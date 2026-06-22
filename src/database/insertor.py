"""
Módulo de inserción en Neo4j.

Toma un objeto FichaLiterariaSchema completamente poblado
(con embeddings ya generados) y lo persiste en el grafo
usando MERGE para evitar duplicados.

Relaciones creadas:
  (Autor)-[:ESCRIBIO]->(Obra)
  (Critica)-[:CRITICA_DE]->(Autor)
  (Multimedia)-[:ASOCIADA_A]->(Autor | Obra | Revista | Antologia | MitoLeyenda)
  (Autor)-[:PERTENECE_A]->(Agrupacion)
  (Revista)-[:PUBLICADA_EN]->(Lugar)
  (Autor)-[:RELACIONADO_CON]->(MitoLeyenda)
"""

import uuid
from typing import Optional
from neo4j import Session

from src.ingestion.schemas import (
    FichaLiterariaSchema,
    AutorSchema,
    ObraSchema,
    CriticaSchema,
    AgrupacionSchema,
    RevistaSchema,
    AntologiaSchema,
    MitoLeyendaSchema,
    Multimedia,
    ChunkSchema,
    Lugar,
    Persona,
)


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def _nuevo_id(prefijo: str = "FICHA") -> str:
    """Genera un id único con UUID corto."""
    return f"{prefijo}_{uuid.uuid4().hex[:8].upper()}"


def _upsert_chunk(session: Session, chunk: ChunkSchema, autor_nombres: str, autor_apellidos: str) -> str:
    """Inserta o actualiza un nodo Chunk y lo vincula al autor."""
    props = _limpiar({
        "chunk_id": chunk.chunk_id,
        "source_file": chunk.source_file,
        "order": chunk.order,
        "texto": chunk.texto,
        "metadata": chunk.metadata,
        "embedding": chunk.embedding,
    })

    session.run(
        """
        MERGE (c:Chunk {chunk_id: $chunk_id})
        ON CREATE SET c += $props
        ON MATCH  SET c += $props
        WITH c
        MATCH (a:Autor {nombres: $nombres, apellidos: $apellidos})
        MERGE (a)-[:TIENE_CHUNK]->(c)
        """,
        chunk_id=chunk.chunk_id,
        props=props,
        nombres=autor_nombres,
        apellidos=autor_apellidos,
    )

    return chunk.chunk_id


def _lugar_a_props(lugar: Optional[Lugar], prefijo: str) -> dict:
    """
    Convierte un objeto Lugar en propiedades planas para Cypher.
    Ej: lugar_nacimiento → lugar_nacimiento_ciudad, ..._estado, etc.
    """
    if lugar is None:
        return {}
    return {
        f"{prefijo}_ciudad":    lugar.ciudad,
        f"{prefijo}_municipio": lugar.municipio,
        f"{prefijo}_estado":    lugar.estado,
        f"{prefijo}_pais":      lugar.pais,
    }


def _limpiar(props: dict) -> dict:
    """Elimina claves con valor None para no sobrescribir datos existentes."""
    return {k: v for k, v in props.items() if v is not None}


# ---------------------------------------------------------------------------
# Inserción de nodos individuales
# ---------------------------------------------------------------------------

def _upsert_autor(session: Session, autor: AutorSchema) -> str:
    """Inserta o actualiza el nodo Autor. Retorna su fichaId."""
    ficha_id = _nuevo_id("AUTOR")

    props = _limpiar({
        "nombres":            autor.nombres,
        "apellidos":          autor.apellidos,
        "nombre_completo":    autor.nombre_completo or f"{autor.nombres} {autor.apellidos}",
        "sexo":               autor.sexo,
        "seudonimo":          autor.seudonimo,
        "fecha_nacimiento":   autor.fecha_nacimiento,
        "fecha_fallecimiento": autor.fecha_fallecimiento,
        "actividad_relevante": autor.actividad_relevante,
        "contexto_vivio":     autor.contexto_vivio,
        "tematica_principal": autor.tematica_principal,
        "genero_principal":   autor.genero_principal,
        "imagen_autor":       autor.imagen_autor,
        "audio_voz":          autor.audio_voz,
        "text":               autor.text,
        **_lugar_a_props(autor.lugar_nacimiento, "lugar_nacimiento"),
        **_lugar_a_props(autor.lugar_fallecimiento, "lugar_fallecimiento"),
    })

    session.run(
        """
        MERGE (a:Autor {nombres: $nombres, apellidos: $apellidos})
        ON CREATE SET a += $props, a.fichaId = $ficha_id
        ON MATCH  SET a += $props
        """,
        nombres=autor.nombres,
        apellidos=autor.apellidos,
        props=props,
        ficha_id=ficha_id,
    )

    # Recuperar el fichaId real (puede ser el existente si ya había un MATCH)
    result = session.run(
        "MATCH (a:Autor {nombres: $nombres, apellidos: $apellidos}) RETURN a.fichaId AS id",
        nombres=autor.nombres,
        apellidos=autor.apellidos,
    )
    return result.single()["id"]


def _upsert_obra(session: Session, obra: ObraSchema, autor_nombres: str, autor_apellidos: str) -> str:
    """Inserta o actualiza una Obra y la relaciona con su Autor."""
    ficha_id = _nuevo_id("OBRA")

    props = _limpiar({
        "genero":           obra.genero,
        "subgenero":        obra.subgenero,
        "fecha_publicacion": obra.fecha_publicacion,
        "editorial":        obra.editorial,
        "descripcion":      obra.descripcion,
        "idioma_original":  obra.idioma_original,
        **_lugar_a_props(obra.lugar_publicacion, "lugar_publicacion"),
    })

    session.run(
        """
        MERGE (o:Obra {titulo: $titulo})
        ON CREATE SET o += $props, o.fichaId = $ficha_id
        ON MATCH  SET o += $props
        WITH o
        MATCH (a:Autor {nombres: $nombres, apellidos: $apellidos})
        MERGE (a)-[:ESCRIBIO]->(o)
        """,
        titulo=obra.titulo,
        props=props,
        ficha_id=ficha_id,
        nombres=autor_nombres,
        apellidos=autor_apellidos,
    )

    result = session.run("MATCH (o:Obra {titulo: $titulo}) RETURN o.fichaId AS id", titulo=obra.titulo)
    return result.single()["id"]


def _upsert_critica(session: Session, critica: CriticaSchema, autor_nombres: str, autor_apellidos: str) -> str:
    """Inserta una Crítica y la vincula al Autor."""
    ficha_id = _nuevo_id("CRIT")

    props = _limpiar({
        "tipo":                    critica.tipo,
        "autor_critica":           critica.autor,
        "fecha_publicacion":       critica.fecha_publicacion,
        "referencia_bibliografica": critica.referencia_bibliografica,
        "descripcion_resumen":     critica.descripcion_resumen,
        "embedding":               critica.embedding,
    })

    session.run(
        """
        MERGE (c:Critica {titulo: $titulo})
        ON CREATE SET c += $props, c.fichaId = $ficha_id
        ON MATCH  SET c += $props
        WITH c
        MATCH (a:Autor {nombres: $nombres, apellidos: $apellidos})
        MERGE (c)-[:CRITICA_DE]->(a)
        """,
        titulo=critica.titulo,
        props=props,
        ficha_id=ficha_id,
        nombres=autor_nombres,
        apellidos=autor_apellidos,
    )

    result = session.run("MATCH (c:Critica {titulo: $titulo}) RETURN c.fichaId AS id", titulo=critica.titulo)
    return result.single()["id"]


def _upsert_multimedia(session: Session, media: Multimedia, nodo_label: str, nodo_match: dict) -> None:
    """
    Inserta un nodo Multimedia y lo relaciona con el nodo padre dado.

    Args:
        nodo_label: Etiqueta del nodo padre (ej: 'Autor', 'Obra').
        nodo_match: Dict con la clave de búsqueda del padre (ej: {'nombres': 'Juan', 'apellidos': 'Pérez'}).
    """
    ficha_id = _nuevo_id("MEDIA")
    condicion = " AND ".join(f"n.{k} = ${k}" for k in nodo_match)

    props = _limpiar({
        "tipo":       media.tipo,
        "restriccion": media.restriccion,
        "embedding":  media.embedding,
    })

    session.run(
        f"""
        MERGE (m:Multimedia {{enlace: $enlace}})
        ON CREATE SET m += $props, m.fichaId = $ficha_id
        ON MATCH  SET m += $props
        WITH m
        MATCH (n:{nodo_label}) WHERE {condicion}
        MERGE (m)-[:ASOCIADA_A]->(n)
        """,
        enlace=media.enlace,
        props=props,
        ficha_id=ficha_id,
        **nodo_match,
    )


def _upsert_agrupacion(session: Session, ag: AgrupacionSchema, autor_nombres: str, autor_apellidos: str) -> str:
    """Inserta una Agrupación y relaciona al Autor con ella."""
    ficha_id = _nuevo_id("AGRUP")

    props = _limpiar({
        "fecha_inicio":        ag.fecha_inicio,
        "fecha_culminacion":   ag.fecha_culminacion,
        "caracteristica_general": ag.caracteristica_general,
        "actividades":         ag.actividades,
        **_lugar_a_props(ag.lugar_encuentros, "lugar_encuentros"),
    })

    session.run(
        """
        MERGE (ag:Agrupacion {nombre: $nombre})
        ON CREATE SET ag += $props, ag.fichaId = $ficha_id
        ON MATCH  SET ag += $props
        WITH ag
        MATCH (a:Autor {nombres: $nombres, apellidos: $apellidos})
        MERGE (a)-[:PERTENECE_A]->(ag)
        """,
        nombre=ag.nombre,
        props=props,
        ficha_id=ficha_id,
        nombres=autor_nombres,
        apellidos=autor_apellidos,
    )

    result = session.run("MATCH (ag:Agrupacion {nombre: $nombre}) RETURN ag.fichaId AS id", nombre=ag.nombre)
    return result.single()["id"]


def _upsert_revista(session: Session, revista: RevistaSchema, autor_nombres: str, autor_apellidos: str) -> str:
    """Inserta una Revista y la relaciona con el Autor."""
    ficha_id = _nuevo_id("REV")

    props = _limpiar({
        "fecha_primer_numero": revista.fecha_primer_numero,
        "fecha_ultimo_numero": revista.fecha_ultimo_numero,
        "numeros_publicados":  revista.numeros_publicados,
        "editorial":           revista.editorial,
        "secciones":           revista.secciones,
        "descripcion":         revista.descripcion,
        "idioma_original":     revista.idioma_original,
        **_lugar_a_props(revista.lugar_publicacion, "lugar_publicacion"),
    })

    session.run(
        """
        MERGE (r:Revista {titulo: $titulo})
        ON CREATE SET r += $props, r.fichaId = $ficha_id
        ON MATCH  SET r += $props
        WITH r
        MATCH (a:Autor {nombres: $nombres, apellidos: $apellidos})
        MERGE (a)-[:PARTICIPO_EN]->(r)
        """,
        titulo=revista.titulo,
        props=props,
        ficha_id=ficha_id,
        nombres=autor_nombres,
        apellidos=autor_apellidos,
    )

    result = session.run("MATCH (r:Revista {titulo: $titulo}) RETURN r.fichaId AS id", titulo=revista.titulo)
    return result.single()["id"]


def _upsert_antologia(session: Session, antologia: AntologiaSchema, autor_nombres: str, autor_apellidos: str) -> str:
    """Inserta una Antología y la relaciona con el Autor."""
    ficha_id = _nuevo_id("ANTOL")

    props = _limpiar({
        "autor_antologia":    antologia.autor,
        "genero":             antologia.genero,
        "fecha_publicacion":  antologia.fecha_publicacion,
        "editorial":          antologia.editorial,
        "descripcion":        antologia.descripcion,
        "idioma_original":    antologia.idioma_original,
        **_lugar_a_props(antologia.lugar_publicacion, "lugar_publicacion"),
    })

    session.run(
        """
        MERGE (ant:Antologia {titulo: $titulo})
        ON CREATE SET ant += $props, ant.fichaId = $ficha_id
        ON MATCH  SET ant += $props
        WITH ant
        MATCH (a:Autor {nombres: $nombres, apellidos: $apellidos})
        MERGE (a)-[:INCLUIDO_EN]->(ant)
        """,
        titulo=antologia.titulo,
        props=props,
        ficha_id=ficha_id,
        nombres=autor_nombres,
        apellidos=autor_apellidos,
    )

    result = session.run("MATCH (ant:Antologia {titulo: $titulo}) RETURN ant.fichaId AS id", titulo=antologia.titulo)
    return result.single()["id"]


def _upsert_mito_leyenda(session: Session, mito: MitoLeyendaSchema, autor_nombres: str, autor_apellidos: str) -> str:
    """Inserta un Mito/Leyenda y lo relaciona con el Autor."""
    ficha_id = _nuevo_id("MITO")

    props = _limpiar({
        "comunidad_creadora": mito.comunidad_creadora,
        "idioma_original":    mito.idioma_original,
        "texto_completo":     mito.texto_completo,
        "tema_principal":     mito.tema_principal,
        "descripcion":        mito.descripcion,
        **_lugar_a_props(mito.lugar_difusion, "lugar_difusion"),
    })

    session.run(
        """
        MERGE (ml:MitoLeyenda {titulo: $titulo})
        ON CREATE SET ml += $props, ml.fichaId = $ficha_id
        ON MATCH  SET ml += $props
        WITH ml
        MATCH (a:Autor {nombres: $nombres, apellidos: $apellidos})
        MERGE (a)-[:RELACIONADO_CON]->(ml)
        """,
        titulo=mito.titulo,
        props=props,
        ficha_id=ficha_id,
        nombres=autor_nombres,
        apellidos=autor_apellidos,
    )

    result = session.run("MATCH (ml:MitoLeyenda {titulo: $titulo}) RETURN ml.fichaId AS id", titulo=mito.titulo)
    return result.single()["id"]


# ---------------------------------------------------------------------------
# Función principal pública
# ---------------------------------------------------------------------------

def insertar_ficha(ficha: FichaLiterariaSchema, session: Session) -> None:
    """
    Persiste una FichaLiterariaSchema completa en Neo4j.

    Orden de inserción:
    1. Autor (nodo raíz)
    2. Obras del autor + relación ESCRIBIO
    3. Críticas del autor + relación CRITICA_DE
    4. Multimedia del autor + obras
    5. Chunks del documento + relación TIENE_CHUNK
    6. Agrupaciones + relación PERTENECE_A
    7. Revistas + relación PARTICIPO_EN
    8. Antologías + relación INCLUIDO_EN
    9. Mitos y Leyendas + relación RELACIONADO_CON
    """
    autor = ficha.autor
    n = autor.nombres
    ap = autor.apellidos

    print(f"   📌 Insertando autor: {n} {ap}")
    _upsert_autor(session, autor)

    # Obras
    for obra in autor.obras:
        _upsert_obra(session, obra, n, ap)
        for media in obra.multimedia:
            _upsert_multimedia(session, media, "Obra", {"titulo": obra.titulo})

    # Críticas
    for critica in autor.criticas:
        _upsert_critica(session, critica, n, ap)

    # Multimedia del autor
    for media in autor.multimedia:
        _upsert_multimedia(session, media, "Autor", {"nombres": n, "apellidos": ap})

    # Chunks
    for chunk in ficha.chunks:
        _upsert_chunk(session, chunk, n, ap)

    # Agrupaciones
    for ag in ficha.agrupaciones:
        _upsert_agrupacion(session, ag, n, ap)

    # Revistas
    for revista in ficha.revistas:
        _upsert_revista(session, revista, n, ap)
        for media in revista.multimedia:
            _upsert_multimedia(session, media, "Revista", {"titulo": revista.titulo})

    # Antologías
    for antologia in ficha.antologias:
        _upsert_antologia(session, antologia, n, ap)
        for media in antologia.multimedia:
            _upsert_multimedia(session, media, "Antologia", {"titulo": antologia.titulo})

    # Mitos y Leyendas
    for mito in ficha.mitos_leyendas:
        _upsert_mito_leyenda(session, mito, n, ap)
        for media in mito.multimedia:
            _upsert_multimedia(session, media, "MitoLeyenda", {"titulo": mito.titulo})

    print(f"   ✅ Ficha guardada: {n} {ap} | Obras: {len(autor.obras)} | Críticas: {len(autor.criticas)} | Chunks: {len(ficha.chunks)}")
