"""
Módulo de generación de embeddings con LangChain + Ollama (nomic-embed-text, 768 dims).

Puebla los campos `embedding` de CriticaSchema, AutorSchema y MultimediaSchema
directamente en el objeto FichaLiterariaSchema antes de guardarlo en Neo4j.

Cambios vs versión anterior:
- Usa un singleton de OllamaEmbeddings (LangChain) para evitar recrear el cliente
  en cada llamada.
- Usa `embed_documents()` en lote cuando hay múltiples textos del mismo tipo,
  reduciendo el overhead de conexión HTTP con Ollama.
- Usa `embed_query()` para textos individuales de consulta (semánticamente distinto).
"""

import logging
from typing import List, Optional

from langchain_ollama import OllamaEmbeddings

from src.config import Config
from src.ingestion.schemas import FichaLiterariaSchema, CriticaSchema, Multimedia

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Singleton de OllamaEmbeddings (LangChain)
# ---------------------------------------------------------------------------

_embeddings_client: Optional[OllamaEmbeddings] = None


def get_embeddings_client() -> OllamaEmbeddings:
    """
    Retorna (o crea) el cliente singleton de OllamaEmbeddings.
    Se inicializa con lazy-loading para no fallar al importar si Ollama no está up.
    """
    global _embeddings_client
    if _embeddings_client is None:
        import os
        modelo = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
        _embeddings_client = OllamaEmbeddings(
            model=modelo,
            base_url=Config.OLLAMA_BASE_URL,
        )
        logger.info("OllamaEmbeddings (LangChain) inicializado: %s en %s", modelo, Config.OLLAMA_BASE_URL)
    return _embeddings_client


# ---------------------------------------------------------------------------
# Funciones de generación individual
# ---------------------------------------------------------------------------

def generar_embedding(texto: str) -> Optional[List[float]]:
    """
    Genera un vector de 768 dimensiones para el texto dado usando LangChain.
    Usa `embed_query()` — apropiado para textos individuales de descripción.
    Retorna None si el texto está vacío o si Ollama no está disponible.
    """
    if not texto or not texto.strip():
        return None
    try:
        cliente = get_embeddings_client()
        return cliente.embed_query(texto)
    except Exception as e:
        logger.warning("No se pudo generar embedding: %s", e)
        print(f"⚠️  No se pudo generar embedding: {e}")
        return None


def generar_embeddings_batch(textos: List[str]) -> List[Optional[List[float]]]:
    """
    Genera embeddings en lote (batch) usando `embed_documents()` de LangChain.
    Más eficiente que llamar `generar_embedding()` N veces cuando hay múltiples
    textos del mismo tipo (ej.: todas las críticas de un autor).

    Args:
        textos: Lista de strings. Los vacíos o None se omiten y devuelven None.

    Returns:
        Lista de vectores en el mismo orden que `textos`.
        Las posiciones con texto vacío retornan None.
    """
    if not textos:
        return []

    # Índices con texto válido
    indices_validos = [(i, t) for i, t in enumerate(textos) if t and t.strip()]
    resultado: List[Optional[List[float]]] = [None] * len(textos)

    if not indices_validos:
        return resultado

    try:
        cliente = get_embeddings_client()
        textos_validos = [t for _, t in indices_validos]
        vectores = cliente.embed_documents(textos_validos)
        for (i, _), vector in zip(indices_validos, vectores):
            resultado[i] = vector
    except Exception as e:
        logger.warning("Error en embed_documents batch: %s", e)
        print(f"⚠️  Error en generación de embeddings en lote: {e}")

    return resultado


# ---------------------------------------------------------------------------
# Poblar embeddings en una FichaLiterariaSchema completa
# ---------------------------------------------------------------------------

def poblar_embeddings(ficha: FichaLiterariaSchema) -> FichaLiterariaSchema:
    """
    Recorre la ficha literaria y asigna embeddings a:
    - Cada CriticaSchema (usa titulo + descripcion_resumen) — en batch
    - AutorSchema (usa tematica_principal + actividad_relevante + contexto_vivio)
    - Cada Multimedia en autor, obras, agrupaciones, revistas, antologías y mitos

    Modifica el objeto en el lugar y lo retorna.
    Usa `embed_documents()` (LangChain) en batch para críticas y obras,
    reduciendo el número de llamadas HTTP a Ollama.
    """
    print("🧮 Generando embeddings con LangChain + Ollama...")

    # 1. Embeddings de Críticas del autor — BATCH
    if ficha.autor.criticas:
        textos_criticas = [_texto_critica(c) for c in ficha.autor.criticas]
        vectores_criticas = generar_embeddings_batch(textos_criticas)
        for critica, vector in zip(ficha.autor.criticas, vectores_criticas):
            critica.embedding = vector

    # 2. Embedding del Autor — individual
    texto_autor = _texto_autor(ficha)
    if texto_autor.strip():
        ficha.autor.embedding = generar_embedding(texto_autor)  # type: ignore[attr-defined]

    # 3. Embeddings de multimedia del autor — individual (URLs de enlace)
    for media in ficha.autor.multimedia:
        media.embedding = generar_embedding(media.enlace)

    # 4. Embeddings de Obras y su multimedia — BATCH para obras
    if ficha.autor.obras:
        textos_obras = [
            f"{obra.titulo}. {obra.descripcion or ''}".strip()
            for obra in ficha.autor.obras
        ]
        vectores_obras = generar_embeddings_batch(textos_obras)
        for obra, vector in zip(ficha.autor.obras, vectores_obras):
            obra.embedding = vector
            for media in obra.multimedia:
                media.embedding = generar_embedding(media.enlace)

    # 5. Agrupaciones — sin embedding por ahora
    for agrupacion in ficha.agrupaciones:
        pass

    # 6. Revistas — multimedia
    for revista in ficha.revistas:
        for media in revista.multimedia:
            media.embedding = generar_embedding(media.enlace)

    # 7. Antologías — multimedia
    for antologia in ficha.antologias:
        for media in antologia.multimedia:
            media.embedding = generar_embedding(media.enlace)

    # 8. Mitos y Leyendas — multimedia
    for mito in ficha.mitos_leyendas:
        for media in mito.multimedia:
            media.embedding = generar_embedding(media.enlace)

    print("✅ Embeddings generados correctamente con LangChain.")
    return ficha


# ---------------------------------------------------------------------------
# Helpers para construir el texto de cada entidad
# ---------------------------------------------------------------------------

def _texto_critica(critica: CriticaSchema) -> str:
    partes = [critica.titulo, critica.descripcion_resumen or ""]
    return " ".join(p for p in partes if p)


def _texto_autor(ficha: FichaLiterariaSchema) -> str:
    a = ficha.autor
    partes = [
        a.tematica_principal or "",
        a.actividad_relevante or "",
        a.contexto_vivio or "",
    ]
    return " ".join(p for p in partes if p)
