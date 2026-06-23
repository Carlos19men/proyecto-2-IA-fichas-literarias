from pathlib import Path
from typing import List
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter


def _chunk_id(source_file: str, order: int) -> str:
    base = Path(source_file).stem.replace(" ", "_")
    return f"{base}_chunk_{order:04d}"


def chunk_text(texto: str, source_file: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[dict]:
    """
    Divide un texto en chunks estructurados usando primero divisiones por encabezados Markdown
    (para evitar romper la coherencia de obras, críticas o biografías) y luego RecursiveCharacterTextSplitter
    si alguna sección es muy larga.
    """
    # 1. Definir los encabezados estructurados
    headers_to_split_on = [
        ("#", "autor_principal"),
        ("##", "seccion"),
        ("###", "subseccion"),
    ]

    # strip_headers=False mantiene los títulos (# Titulo) dentro del texto indexado
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False
    )
    
    documentos_estructurados = markdown_splitter.split_text(texto)

    # 2. Configurar el sub-segmentador para chunks largos
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )

    chunks = []
    order = 1

    for doc in documentos_estructurados:
        contenido = doc.page_content
        metadata = doc.metadata

        # Si el bloque cabe en un solo chunk, lo guardamos
        if len(contenido) <= chunk_size:
            chunks.append({
                "chunk_id": _chunk_id(source_file, order),
                "source_file": source_file,
                "order": order,
                "texto": contenido,
                "metadata": metadata.copy(),
            })
            order += 1
        else:
            # Si el bloque supera el límite, lo subdividimos preservando la metadata estructural
            sub_textos = text_splitter.split_text(contenido)
            for sub_txt in sub_textos:
                chunks.append({
                    "chunk_id": _chunk_id(source_file, order),
                    "source_file": source_file,
                    "order": order,
                    "texto": sub_txt,
                    "metadata": metadata.copy(),
                })
                order += 1

    return chunks
