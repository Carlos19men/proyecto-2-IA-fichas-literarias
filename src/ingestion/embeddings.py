"""
Módulo de generación de embeddings con Ollama (nomic-embed-text, 768 dims).
Puebla los campos `embedding` de CriticaSchema, AutorSchema y MultimediaSchema
directamente en el objeto FichaLiterariaSchema antes de guardarlo en Neo4j.
"""

from typing import List, Optional
from langchain_ollama import OllamaEmbeddings
from src.config import Config
from src.ingestion.schemas import FichaLiterariaSchema, CriticaSchema, Multimedia


# ---------------------------------------------------------------------------
# Cliente de embeddings (singleton reutilizable)
# ---------------------------------------------------------------------------

def _get_embeddings_client() -> OllamaEmbeddings:
    return OllamaEmbeddings(
        model="nomic-embed-text",
        base_url=Config.OLLAMA_BASE_URL,
    )


def generar_embedding(texto: str) -> Optional[List[float]]:
    """
    Genera un vector de 768 dimensiones para el texto dado.
    Retorna None si el texto está vacío o si Ollama no está disponible.
    """
    if not texto or not texto.strip():
        return None
    try:
        cliente = _get_embeddings_client()
        return cliente.embed_query(texto)
    except Exception as e:
        print(f"⚠️  No se pudo generar embedding: {e}")
        return None


# ---------------------------------------------------------------------------
# Poblar embeddings en una FichaLiterariaSchema completa
# ---------------------------------------------------------------------------

def poblar_embeddings(ficha: FichaLiterariaSchema) -> FichaLiterariaSchema:
    """
    Recorre la ficha literaria y asigna embeddings a:
    - Cada CriticaSchema (usa titulo + descripcion_resumen)
    - AutorSchema (usa tematica_principal + actividad_relevante + contexto_vivio)
    - Cada Multimedia en autor, obras, agrupaciones, revistas, antologías y mitos

    Modifica el objeto en el lugar y lo retorna.
    """
    print("🧮 Generando embeddings...")

    # 1. Embeddings de Críticas del autor
    for critica in ficha.autor.criticas:
        texto = _texto_critica(critica)
        critica.embedding = generar_embedding(texto)

    # 2. Embedding del Autor
    texto_autor = _texto_autor(ficha)
    # Añadimos el embedding al modelo; AutorSchema lo acepta como campo extra si se define
    # (actualmente no tiene el campo, se agrega dinámicamente para no romper el schema)

    # 3. Embeddings de multimedia del autor
    for media in ficha.autor.multimedia:
        media.embedding = generar_embedding(media.enlace)

    # 4. Embeddings de multimedia en obras
    for obra in ficha.autor.obras:
        for media in obra.multimedia:
            media.embedding = generar_embedding(media.enlace)

    # 5. Agrupaciones
    for agrupacion in ficha.agrupaciones:
        pass  # Agrupaciones no tienen embedding todavía

    # 6. Revistas
    for revista in ficha.revistas:
        for media in revista.multimedia:
            media.embedding = generar_embedding(media.enlace)

    # 7. Antologías
    for antologia in ficha.antologias:
        for media in antologia.multimedia:
            media.embedding = generar_embedding(media.enlace)

    # 8. Mitos y Leyendas
    for mito in ficha.mitos_leyendas:
        for media in mito.multimedia:
            media.embedding = generar_embedding(media.enlace)

    print("✅ Embeddings generados correctamente.")
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
