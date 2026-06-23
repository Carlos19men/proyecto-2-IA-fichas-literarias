import os
import subprocess
from shutil import which

try:
    import pypandoc
except Exception:
    pypandoc = None

try:
    import mammoth
except Exception:
    mammoth = None

try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None


def _md_path(ruta: str) -> str:
    base = os.path.splitext(ruta)[0]
    return base + ".md"


def _extract_media_with_marker_pdf(ruta: str, out_dir: str) -> bool:
    """Try to run `marker-pdf` CLI to extract media into out_dir.
    Returns True if command ran successfully.
    """
    cmd = ["marker-pdf", "extract", ruta, "--out", out_dir]
    try:
        subprocess.run(cmd, check=True)
        return True
    except Exception:
        return False


def _extract_media_with_pymupdf(ruta: str, out_dir: str) -> bool:
    """Fallback media extraction using PyMuPDF (fitz).
    Extracts images found in PDF pages into out_dir.
    """
    if fitz is None:
        return False

    try:
        doc = fitz.open(ruta)
        img_count = 0
        for page_index in range(len(doc)):
            page = doc[page_index]
            images = page.get_images(full=True)
            for img_index, img in enumerate(images):
                xref = img[0]
                pix = fitz.Pixmap(doc, xref)
                ext = "png" if pix.n < 4 else "png"
                out_path = os.path.join(out_dir, f"extracted_{page_index+1}_{img_index+1}.{ext}")
                if pix.n < 4:
                    pix.save(out_path)
                else:
                    pix.save(out_path)
                pix = None
                img_count += 1
        return img_count > 0
    except Exception:
        return False


def clean_markdown_text(text: str) -> str:
    """
    Limpia el texto Markdown generado para eliminar ruido común de la conversión:
    - Colapsa saltos de línea excesivos (más de 2 consecutivos a 2).
    - Colapsa espacios horizontales múltiples a uno solo.
    - Elimina líneas que contienen únicamente números de página (ej: 'Pág. 12', '12').
    - Limpia espacios al inicio y final de las líneas.
    """
    import re
    if not text:
        return ""
    # 1. Eliminar números de página y líneas de numeración solitaria (ej: "Pág. 5", "5")
    text = re.sub(r"(?m)^\s*(?:p[aá]g\.|p[aá]gina|pagina)?\s*\d+\s*$", "", text)
    
    # 2. Limpiar espacios en blanco al inicio/final de cada línea y colapsar espacios internos
    lines = [line.strip() for line in text.splitlines()]
    
    # 3. Eliminar líneas vacías duplicadas consecutivas y colapsar espacios
    cleaned_lines = []
    for line in lines:
        if line:
            # Colapsar espacios múltiples en la misma línea
            line = re.sub(r"[ \t]+", " ", line)
            cleaned_lines.append(line)
        else:
            if not cleaned_lines or cleaned_lines[-1] != "":
                cleaned_lines.append("")
                
    cleaned_text = "\n".join(cleaned_lines)
    
    # 4. Asegurar que no queden más de 2 saltos de línea consecutivos
    cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)
    
    return cleaned_text.strip()


def convert_to_markdown(ruta: str) -> str | None:
    """Convert a source file to Markdown and try to extract multimedia.

    Behavior:
    - If `ruta` already ends with .md returns it.
    - If a .md sibling exists, returns it (cache).
    - Tries pypandoc (requires pandoc installed). Falls back to mammoth for .docx
      and to plain text for PDFs if necessary.
    - For PDFs, attempts to extract embedded images using `marker-pdf` CLI
      if available, otherwise falls back to PyMuPDF (fitz) if installed.

    Returns path to generated .md on success, or None on failure.
    """
    md = _md_path(ruta)
    if os.path.exists(md):
        return md

    ext = os.path.splitext(ruta)[1].lower()
    if ext == ".md":
        return ruta

    # Ensure output directory exists
    out_dir = os.path.dirname(ruta) or "."

    # Try pypandoc first (requires system pandoc)
    if pypandoc is not None:
        try:
            pypandoc.convert_file(ruta, "md", outputfile=md)
            # Apply cleaning to the pandoc output
            try:
                with open(md, "r", encoding="utf-8") as f:
                    content = f.read()
                cleaned = clean_markdown_text(content)
                with open(md, "w", encoding="utf-8") as f:
                    f.write(cleaned)
            except Exception:
                pass
            # For PDFs, also attempt media extraction below
            if ext == ".pdf":
                # try marker-pdf then pymupdf
                if which("marker-pdf"):
                    _extract_media_with_marker_pdf(ruta, out_dir)
                else:
                    _extract_media_with_pymupdf(ruta, out_dir)
            return md
        except Exception:
            pass

    # Fallback for .docx using mammoth
    if ext == ".docx" and mammoth is not None:
        try:
            with open(ruta, "rb") as f:
                html = mammoth.convert_to_html(f).value
            if pypandoc is not None:
                md_text = pypandoc.convert_text(html, "md", format="html")
            else:
                md_text = html
            # Clean text before writing
            md_text = clean_markdown_text(md_text)
            with open(md, "w", encoding="utf-8") as out:
                out.write(md_text)
            return md
        except Exception:
            return None

    # Fallback for PDF: try pdftotext -> use as simple markdown, and try extract images
    if ext == ".pdf":
        txt_tmp = md + ".txt"
        try:
            subprocess.run(["pdftotext", ruta, txt_tmp], check=True)
            # convert txt to md (plain) and clean it
            with open(txt_tmp, "r", encoding="utf-8") as f_in:
                txt_content = f_in.read()
            cleaned = clean_markdown_text(txt_content)
            with open(md, "w", encoding="utf-8") as f_out:
                f_out.write(cleaned)
            try:
                os.remove(txt_tmp)
            except Exception:
                pass
            # extract media
            if which("marker-pdf"):
                _extract_media_with_marker_pdf(ruta, out_dir)
            else:
                _extract_media_with_pymupdf(ruta, out_dir)
            return md
        except Exception:
            try:
                if os.path.exists(txt_tmp):
                    os.remove(txt_tmp)
            except Exception:
                pass
            return None

    return None
