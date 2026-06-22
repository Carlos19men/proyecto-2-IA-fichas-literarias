from pathlib import Path
from typing import List
from uuid import uuid4

from langchain_text_splitters.character import RecursiveCharacterTextSplitter


def _chunk_id(source_file: str, order: int) -> str:
    base = Path(source_file).stem.replace(" ", "_")
    return f"{base}_chunk_{order:04d}"


def chunk_text(texto: str, source_file: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[dict]:
    """Divide un texto en chunks y asigna un ID único a cada fragmento."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    textos = splitter.split_text(texto)

    chunks = []
    for index, contenido in enumerate(textos, start=1):
        chunks.append({
            "chunk_id": _chunk_id(source_file, index),
            "source_file": source_file,
            "order": index,
            "texto": contenido,
            "metadata": {},
        })

    return chunks
