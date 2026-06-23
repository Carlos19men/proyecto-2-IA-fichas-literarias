"""
Módulo de inserción en Neo4j.

Toma un objeto FichaLiterariaSchema completamente poblado
(con embeddings ya generados) y lo persiste en el grafo
usando MERGE para evitar duplicados.

Relaciones creadas:
  (Autor)-[:ESCRIBIO]->(Obra)
  (Critica)-[:CRITICA_DE]->(Autor)
  (Critica)-[:CRITICA_DE]->(Obra) [si la crítica menciona la obra]
  (Multimedia)-[:ASOCIADA_A]->(Autor | Obra | Revista | Antologia | MitoLeyenda)
  (Autor)-[:PERTENECE_A]->(Agrupacion)
  (Persona)-[:PERTENECE_A]->(Agrupacion)
  (Agrupacion)-[:PUBLICO]->(PublicacionAgrupacion)
  (Autor)-[:PARTICIPO_EN]->(Revista)
  (Persona)-[:CREO]->(Revista)
  (Revista)-[:PUBLICA]->(Obra)
  (Autor)-[:INCLUIDO_EN]->(Antologia)
  (Antologia)-[:CONTIENE]->(Obra)
  (Autor)-[:RELACIONADO_CON]->(MitoLeyenda)
  (Autor)-[:TIENE_FAMILIAR]->(Persona)
  (Autor)-[:TIENE_CHUNK]->(Chunk)
"""

import hashlib
from typing import Optional, List
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

def generar_id(prefijo: str, texto: str) -> str:
    """Genera un identificador único determinista a partir de un texto."""
    texto_limpio = "".join(c for c in texto if c.isalnum() or c == "_").lower()
    hash_val = hashlib.md5(texto.encode("utf-8")).hexdigest()[:8]
    return f"{prefijo}_{texto_limpio[:20]}_{hash_val}".upper()


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
    autor_id = generar_id("AUTOR", f"{autor.nombres}_{autor.apellidos}")

    # Generar texto biográfico para el vector de búsqueda semántica si no está definido
    if not autor.text:
        bio_texto = f"{autor.nombres} {autor.apellidos}. "
        if autor.seudonimo:
            bio_texto += f"Conocido como {autor.seudonimo}. "
        if autor.actividad_relevante:
            bio_texto += f"{autor.actividad_relevante} "
        if autor.contexto_vivio:
            bio_texto += f"Vivió en el contexto: {autor.contexto_vivio} "
        if autor.tematica_principal:
            bio_texto += f"Temas principales: {autor.tematica_principal} "
        autor.text = bio_texto.strip()

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
        "embedding":          autor.embedding,
        **_lugar_a_props(autor.lugar_nacimiento, "lugar_nacimiento"),
        **_lugar_a_props(autor.lugar_fallecimiento, "lugar_fallecimiento"),
    })

    session.run(
        """
        MERGE (a:Autor {nombres: $nombres, apellidos: $apellidos})
        ON CREATE SET a += $props, a.fichaId = $fichaId, a.timestamp = datetime()
        ON MATCH  SET a += $props, a.timestamp = datetime()
        """,
        nombres=autor.nombres,
        apellidos=autor.apellidos,
        props=props,
        fichaId=autor_id,
    )
    return autor_id


def _upsert_familiar(session: Session, autor_id: str, fam: Persona) -> None:
    """Crea nodos de Persona para familiares y los relaciona con el Autor."""
    if not fam.nombres:
        return

    nombre_completo = f"{fam.nombres} {fam.apellidos or ''}".strip()
    session.run(
        """
        MATCH (a:Autor {fichaId: $autorId})
        MERGE (p:Persona {nombre_completo: $nombre_completo})
        ON CREATE SET
            p.nombres = $nombres,
            p.apellidos = $apellidos
        MERGE (a)-[r:TIENE_FAMILIAR]->(p)
        SET r.rol = $rol
        """,
        autorId=autor_id,
        nombre_completo=nombre_completo,
        nombres=fam.nombres,
        apellidos=fam.apellidos,
        rol=fam.rol or "Familiar"
    )


def _upsert_obra(session: Session, obra: ObraSchema, autor_id: str) -> str:
    """Inserta o actualiza una Obra y la relaciona con su Autor."""
    obra_id = generar_id("OBRA", obra.titulo)

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
        MATCH (a:Autor {fichaId: $autorId})
        MERGE (o:Obra {titulo: $titulo})
        ON CREATE SET o += $props, o.fichaId = $fichaId
        ON MATCH  SET o += $props
        WITH a, o
        MERGE (a)-[:ESCRIBIO]->(o)
        """,
        autorId=autor_id,
        titulo=obra.titulo,
        props=props,
        fichaId=obra_id,
    )
    return obra_id


def _upsert_critica(session: Session, critica: CriticaSchema, autor_id: str, obras_ids: List[str]) -> str:
    """Inserta una Crítica y la vincula al Autor y opcionalmente a Obras."""
    critica_id = generar_id("CRITICA", critica.titulo)

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
        MATCH (a:Autor {fichaId: $autorId})
        MERGE (c:Critica {titulo: $titulo})
        ON CREATE SET c += $props, c.fichaId = $fichaId
        ON MATCH  SET c += $props
        WITH a, c
        MERGE (c)-[:CRITICA_DE]->(a)
        """,
        autorId=autor_id,
        titulo=critica.titulo,
        props=props,
        fichaId=critica_id,
    )

    # Conexión dinámica con obras
    for obra_id in obras_ids:
        session.run(
            """
            MATCH (c:Critica {fichaId: $criticaId})
            MATCH (o:Obra {fichaId: $obraId})
            WHERE toLower(c.titulo) CONTAINS toLower(o.titulo) 
               OR toLower(c.descripcion_resumen) CONTAINS toLower(o.titulo)
               OR toLower(c.referencia_bibliografica) CONTAINS toLower(o.titulo)
            MERGE (c)-[:CRITICA_DE]->(o)
            """,
            criticaId=critica_id,
            obraId=obra_id,
        )

    return critica_id


def _upsert_multimedia(session: Session, media: Multimedia, label_padre: str, match_padre: dict) -> None:
    """Inserta un nodo Multimedia y lo relaciona con el nodo padre."""
    if not media.enlace:
        return
    media_id = generar_id("MULTIMEDIA", media.enlace)

    props = _limpiar({
        "tipo":       media.tipo,
        "restriccion": media.restriccion,
        "embedding":  media.embedding,
    })

    condicion = " AND ".join(f"n.{k} = ${k}" for k in match_padre)

    session.run(
        f"""
        MERGE (m:Multimedia {{enlace: $enlace}})
        ON CREATE SET m += $props, m.fichaId = $fichaId
        ON MATCH  SET m += $props
        WITH m
        MATCH (n:{label_padre}) WHERE {condicion}
        MERGE (m)-[:ASOCIADA_A]->(n)
        """,
        enlace=media.enlace,
        props=props,
        fichaId=media_id,
        **match_padre,
    )


def _upsert_agrupacion(session: Session, ag: AgrupacionSchema, autor_id: str) -> str:
    """Inserta una Agrupación y relaciona al Autor con ella."""
    agrupacion_id = generar_id("AGRUPACION", ag.nombre)

    props = _limpiar({
        "fecha_inicio":        ag.fecha_inicio,
        "fecha_culminacion":   ag.fecha_culminacion,
        "caracteristica_general": ag.caracteristica_general,
        "actividades":         ag.actividades,
        **_lugar_a_props(ag.lugar_encuentros, "lugar_encuentros"),
    })

    session.run(
        """
        MATCH (a:Autor {fichaId: $autorId})
        MERGE (ag:Agrupacion {nombre: $nombre})
        ON CREATE SET ag += $props, ag.fichaId = $fichaId
        ON MATCH  SET ag += $props
        WITH a, ag
        MERGE (a)-[:PERTENECE_A]->(ag)
        """,
        autorId=autor_id,
        nombre=ag.nombre,
        props=props,
        fichaId=agrupacion_id,
    )

    # Integrantes
    for intg in ag.integrantes:
        if not intg.nombres:
            continue
        nombre_completo = f"{intg.nombres} {intg.apellidos or ''}".strip()
        session.run(
            """
            MATCH (ag:Agrupacion {fichaId: $agrupacionId})
            MERGE (p:Persona {nombre_completo: $nombre_completo})
            ON CREATE SET
                p.nombres = $nombres,
                p.apellidos = $apellidos
            WITH ag, p
            MERGE (p)-[r:PERTENECE_A]->(ag)
            SET r.rol = $rol
            """,
            agrupacionId=agrupacion_id,
            nombre_completo=nombre_completo,
            nombres=intg.nombres,
            apellidos=intg.apellidos,
            rol=intg.rol or "Integrante"
        )

    # Publicaciones
    for pub in ag.publicaciones:
        session.run(
            """
            MATCH (ag:Agrupacion {fichaId: $agrupacionId})
            MERGE (p:PublicacionAgrupacion {titulo: $titulo, anio: $anio})
            ON CREATE SET
                p.resumen = $resumen
            WITH ag, p
            MERGE (ag)-[:PUBLICO]->(p)
            """,
            agrupacionId=agrupacion_id,
            titulo=pub.titulo,
            anio=pub.anio,
            resumen=pub.resumen
        )

    return agrupacion_id


def _upsert_revista(session: Session, revista: RevistaSchema, autor_id: str, obras_ids: List[str]) -> str:
    """Inserta una Revista y la relaciona con el Autor."""
    revista_id = generar_id("REVISTA", revista.titulo)

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
        MATCH (a:Autor {fichaId: $autorId})
        MERGE (r:Revista {titulo: $titulo})
        ON CREATE SET r += $props, r.fichaId = $fichaId
        ON MATCH  SET r += $props
        WITH a, r
        MERGE (a)-[:PARTICIPO_EN]->(r)
        """,
        autorId=autor_id,
        titulo=revista.titulo,
        props=props,
        fichaId=revista_id,
    )

    # Creadores
    for creador in revista.creadores:
        if not creador.nombres:
            continue
        nombre_completo = f"{creador.nombres} {creador.apellidos or ''}".strip()
        session.run(
            """
            MATCH (r:Revista {fichaId: $revistaId})
            MERGE (p:Persona {nombre_completo: $nombre_completo})
            ON CREATE SET
                p.nombres = $nombres,
                p.apellidos = $apellidos
            WITH r, p
            MERGE (p)-[rel:CREO]->(r)
            SET rel.rol = $rol
            """,
            revistaId=revista_id,
            nombre_completo=nombre_completo,
            nombres=creador.nombres,
            apellidos=creador.apellidos,
            rol=creador.rol or "Creador"
        )

    # Relación Revista -> Obra
    for obra_id in obras_ids:
        session.run(
            """
            MATCH (r:Revista {fichaId: $revistaId})
            MATCH (o:Obra {fichaId: $obraId})
            WHERE toLower(r.descripcion) CONTAINS toLower(o.titulo) 
               OR toLower(r.secciones) CONTAINS toLower(o.titulo)
            MERGE (r)-[:PUBLICA]->(o)
            """,
            revistaId=revista_id,
            obraId=obra_id,
        )

    return revista_id


def _upsert_antologia(session: Session, antologia: AntologiaSchema, autor_id: str, obras_ids: List[str]) -> str:
    """Inserta una Antología y la relaciona con el Autor."""
    antologia_id = generar_id("ANTOLOGIA", antologia.titulo)

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
        MATCH (a:Autor {fichaId: $autorId})
        MERGE (an:Antologia {titulo: $titulo})
        ON CREATE SET an += $props, an.fichaId = $fichaId
        ON MATCH  SET an += $props
        WITH a, an
        MERGE (an)-[:CONTIENE_OBRAS_DE]->(a)
        """,
        autorId=autor_id,
        titulo=antologia.titulo,
        props=props,
        fichaId=antologia_id,
    )

    # Relación Antología -> Obra
    for obra_id in obras_ids:
        session.run(
            """
            MATCH (an:Antologia {fichaId: $antologiaId})
            MATCH (o:Obra {fichaId: $obraId})
            WHERE toLower(an.descripcion) CONTAINS toLower(o.titulo)
            MERGE (an)-[:CONTIENE]->(o)
            """,
            antologiaId=antologia_id,
            obraId=obra_id,
        )

    return antologia_id


def _upsert_mito_leyenda(session: Session, mito: MitoLeyendaSchema, autor_id: str) -> str:
    """Inserta un Mito/Leyenda y lo relaciona con el Autor."""
    mito_id = generar_id("MITO", mito.titulo)

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
        MATCH (a:Autor {fichaId: $autorId})
        MERGE (ml:MitoLeyenda {titulo: $titulo})
        ON CREATE SET ml += $props, ml.fichaId = $fichaId
        ON MATCH  SET ml += $props
        WITH a, ml
        MERGE (a)-[:RELACIONADO_CON]->(ml)
        """,
        autorId=autor_id,
        titulo=mito.titulo,
        props=props,
        fichaId=mito_id,
    )
    return mito_id


def _upsert_chunk(session: Session, chunk: ChunkSchema, autor_id: str) -> str:
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
        MATCH (a:Autor {fichaId: $autorId})
        MERGE (c:Chunk {chunk_id: $chunk_id})
        ON CREATE SET c += $props
        ON MATCH  SET c += $props
        WITH a, c
        MERGE (a)-[:TIENE_CHUNK]->(c)
        """,
        autorId=autor_id,
        chunk_id=chunk.chunk_id,
        props=props,
    )
    return chunk.chunk_id


# ---------------------------------------------------------------------------
# Función principal pública
# ---------------------------------------------------------------------------

def insertar_ficha(ficha: FichaLiterariaSchema, session: Session) -> None:
    """
    Persiste una FichaLiterariaSchema completa en Neo4j.
    """
    autor = ficha.autor

    # 1. Autor
    print(f"   📌 Insertando autor: {autor.nombres} {autor.apellidos}")
    autor_id = _upsert_autor(session, autor)

    # 2. Familiares destacados
    for fam in autor.familiares_destacados:
        _upsert_familiar(session, autor_id, fam)

    # 3. Obras
    obras_ids = []
    for obra in autor.obras:
        obra_id = _upsert_obra(session, obra, autor_id)
        obras_ids.append(obra_id)
        for media in obra.multimedia:
            _upsert_multimedia(session, media, "Obra", {"titulo": obra.titulo})

    # 4. Críticas
    for critica in autor.criticas:
        _upsert_critica(session, critica, autor_id, obras_ids)

    # 5. Multimedia del autor
    for media in autor.multimedia:
        _upsert_multimedia(session, media, "Autor", {"fichaId": autor_id})

    # 6. Chunks
    for chunk in ficha.chunks:
        _upsert_chunk(session, chunk, autor_id)

    # 7. Agrupaciones
    for ag in ficha.agrupaciones:
        _upsert_agrupacion(session, ag, autor_id)

    # 8. Revistas
    for revista in ficha.revistas:
        _upsert_revista(session, revista, autor_id, obras_ids)
        for media in revista.multimedia:
            _upsert_multimedia(session, media, "Revista", {"titulo": revista.titulo})

    # 9. Antologías
    for antologia in ficha.antologias:
        _upsert_antologia(session, antologia, autor_id, obras_ids)
        for media in antologia.multimedia:
            _upsert_multimedia(session, media, "Antologia", {"titulo": antologia.titulo})

    # 10. Mitos y Leyendas
    for mito in ficha.mitos_leyendas:
        _upsert_mito_leyenda(session, mito, autor_id)
        for media in mito.multimedia:
            _upsert_multimedia(session, media, "MitoLeyenda", {"titulo": mito.titulo})

    print(f"   ✅ Ficha guardada: {autor.nombres} {autor.apellidos} | Obras: {len(autor.obras)} | Críticas: {len(autor.criticas)} | Chunks: {len(ficha.chunks)}")
