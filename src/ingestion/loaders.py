import os
from pathlib import Path
from typing import Dict, List, Tuple

try:
    from langchain_community.document_loaders import (
        UnstructuredMarkdownLoader,
        Docx2txtLoader,
        PyPDFLoader,
    )
except Exception:
    # Light-weight fallbacks when langchain_community isn't installed.
    class _SimpleDoc:
        def __init__(self, content: str):
            self.page_content = content

    class UnstructuredMarkdownLoader:
        def __init__(self, path):
            self.path = path

        def load(self):
            with open(self.path, "r", encoding="utf-8") as fh:
                return [_SimpleDoc(fh.read())]

    class Docx2txtLoader:
        def __init__(self, path):
            self.path = path

        def load(self):
            # fallback: try to read as text if docx2txt not available
            try:
                import docx
                doc = docx.Document(self.path)
                texts = [p.text for p in doc.paragraphs]
                return [_SimpleDoc("\n".join(texts))]
            except Exception:
                # last resort, return empty
                return [_SimpleDoc("")]

    class PyPDFLoader:
        def __init__(self, path):
            self.path = path

        def load(self):
            # fallback: try pdftotext via subprocess
            try:
                import subprocess, tempfile
                tmp = tempfile.mktemp(suffix=".txt")
                subprocess.run(["pdftotext", self.path, tmp], check=True)
                with open(tmp, "r", encoding="utf-8") as fh:
                    text = fh.read()
                return [_SimpleDoc(text)]
            except Exception:
                return [_SimpleDoc("")]

# ---------------------------------------------------------------------------
# Tipos de extensión por categoría
# ---------------------------------------------------------------------------
EXTENSIONES_TEXTO = {".md", ".docx", ".pdf"}
EXTENSIONES_IMAGEN = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
EXTENSIONES_AUDIO = {".mp3", ".wav", ".ogg", ".m4a"}
EXTENSIONES_VIDEO = {".mp4", ".avi", ".mov", ".mkv", ".webm"}


def leer_archivo_ficha(ruta_archivo: str) -> str:
    """
    Lee un archivo y devuelve su contenido como texto plano.

    - .md   → UnstructuredMarkdownLoader
    - .docx → Docx2txtLoader
    - .pdf  → PyPDFLoader (concatena todas las páginas)
    - imágenes / audio / video → retorna cadena vacía
      (estas rutas se manejan como multimedia, no como texto)
    """
    if not os.path.exists(ruta_archivo):
        raise FileNotFoundError(f"❌ El archivo no existe en la ruta: {ruta_archivo}")

    extension = Path(ruta_archivo).suffix.lower()

    if extension == ".md":
        loader = UnstructuredMarkdownLoader(ruta_archivo)
        documentos = loader.load()
        return "\n".join([doc.page_content for doc in documentos])

    elif extension == ".docx":
        loader = Docx2txtLoader(ruta_archivo)
        documentos = loader.load()
        return "\n".join([doc.page_content for doc in documentos])

    elif extension == ".pdf":
        loader = PyPDFLoader(ruta_archivo)
        documentos = loader.load()
        return "\n\n".join(doc.page_content for doc in documentos)

    elif extension in EXTENSIONES_IMAGEN | EXTENSIONES_AUDIO | EXTENSIONES_VIDEO:
        # No se extrae texto de multimedia; la ruta se registra como referencia
        return ""

    else:
        raise ValueError(
            f"❌ Formato de archivo no soportado: '{extension}'. "
            f"Formatos aceptados: .md, .docx, .pdf, "
            f"imagenes (.jpg/.png), audio (.mp3/.wav) y video (.mp4)."
        )


def clasificar_archivo(ruta: str) -> str:
    """
    Devuelve el tipo de un archivo según su extensión.
    Valores posibles: 'texto', 'imagen', 'audio', 'video', 'desconocido'
    """
    ext = Path(ruta).suffix.lower()
    if ext in EXTENSIONES_TEXTO:
        return "texto"
    elif ext in EXTENSIONES_IMAGEN:
        return "imagen"
    elif ext in EXTENSIONES_AUDIO:
        return "audio"
    elif ext in EXTENSIONES_VIDEO:
        return "video"
    return "desconocido"


def escanear_carpeta_ficha(carpeta: str, recursivo: bool = True) -> Dict[str, List[str]]:
    """
    Escanea una carpeta y clasifica todos sus archivos por tipo.

    Por defecto incluye subcarpetas (p. ej. números de una revista).

    Retorna un diccionario con cuatro listas:
    {
        "texto":   [rutas de .md, .docx, .pdf],
        "imagen":  [rutas de .jpg, .png, ...],
        "audio":   [rutas de .mp3, .wav, ...],
        "video":   [rutas de .mp4, .mov, ...],
    }
    """
    resultado: Dict[str, List[str]] = {
        "texto": [],
        "imagen": [],
        "audio": [],
        "video": [],
    }

    carpeta_path = Path(carpeta)
    if not carpeta_path.is_dir():
        raise ValueError(f"❌ La ruta '{carpeta}' no es un directorio válido.")

    iterador = carpeta_path.rglob("*") if recursivo else carpeta_path.iterdir()
    for archivo in sorted(iterador):
        if archivo.is_file():
            tipo = clasificar_archivo(str(archivo))
            if tipo in resultado:
                resultado[tipo].append(str(archivo))

    return resultado


def leer_texto_principal(carpeta: str) -> Tuple[str, str]:
    """
    Dado un directorio de ficha, encuentra el archivo de texto principal
    (.docx preferido sobre .pdf, sobre .md) y lo lee.

    Retorna: (texto_plano, ruta_del_archivo_leído)
    Lanza ValueError si no hay ningún archivo de texto.
    """
    archivos = escanear_carpeta_ficha(carpeta)
    carpeta_path = Path(carpeta).resolve()
    # El texto principal suele estar en la raíz de la carpeta (ficha .docx)
    candidatos = [
        c for c in archivos["texto"]
        if Path(c).parent.resolve() == carpeta_path
    ] or archivos["texto"]

    if not candidatos:
        raise ValueError(f"❌ No se encontró ningún archivo de texto en '{carpeta}'.")

    def prioridad(ruta: str) -> tuple:
        ext = Path(ruta).suffix.lower()
        ext_ord = {".docx": 0, ".pdf": 1, ".md": 2}.get(ext, 99)
        nombre = Path(ruta).name.lower()
        # Plantilla vacía al final; ficha de ejemplo con datos primero
        if ext == ".docx" and "ejemplo" in nombre:
            ejemplo_ord = 0
        elif ext == ".docx" and "ficha mitos" in nombre and "ejemplo" not in nombre:
            ejemplo_ord = 2
        else:
            ejemplo_ord = 1
        return (ext_ord, ejemplo_ord, nombre)

    candidatos_ordenados = sorted(candidatos, key=prioridad)
    ruta_principal = candidatos_ordenados[0]
    texto = leer_archivo_ficha(ruta_principal)
    return texto, ruta_principal
