"""
Funciones de enriquecimiento de nodos del grafo literario.

Dado un nodo encontrado por la búsqueda, estas funciones traen
las relaciones asociadas (obras, críticas, agrupaciones, etc.)
para construir una ficha completa.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def _limpiar_nodo(record_value) -> dict:
    """Convierte un nodo de Neo4j en dict y elimina el campo embedding."""
    nodo = dict(record_value)
    nodo.pop("embedding", None)
    return nodo


def _consultar_relacion(session, cypher: str, ficha_id: str, clave_retorno: str) -> List[dict]:
    """
    Ejecuta una consulta Cypher parametrizada y retorna una lista de dicts.
    Centraliza el manejo de errores para evitar except:pass silenciosos.
    """
    try:
        records = session.run(cypher, fichaId=ficha_id)
        return [_limpiar_nodo(r[clave_retorno]) for r in records]
    except Exception as e:
        logger.warning("Error en consulta de relación (%s): %s", clave_retorno, e)
        return []


def enriquecer_autor(session, autor_nodo: dict) -> Dict[str, Any]:
    """
    Dado un nodo Autor, trae sus obras, críticas, agrupaciones,
    multimedia y mitos/leyendas relacionados.
    """
    ficha_id = autor_nodo.get("fichaId")
    resultado_base = {
        "autor": autor_nodo,
        "obras": [],
        "criticas": [],
        "agrupaciones": [],
        "mitos": [],
        "multimedia": [],
    }

    if not ficha_id:
        return resultado_base

    resultado_base["obras"] = _consultar_relacion(
        session,
        "MATCH (a:Autor {fichaId: $fichaId})-[:ESCRIBIO]->(o:Obra) RETURN o",
        ficha_id, "o",
    )

    resultado_base["criticas"] = _consultar_relacion(
        session,
        "MATCH (c:Critica)-[:CRITICA_DE]->(a:Autor {fichaId: $fichaId}) RETURN c",
        ficha_id, "c",
    )

    resultado_base["agrupaciones"] = _consultar_relacion(
        session,
        "MATCH (a:Autor {fichaId: $fichaId})-[:PERTENECE_A]->(ag:Agrupacion) RETURN ag",
        ficha_id, "ag",
    )

    resultado_base["mitos"] = _consultar_relacion(
        session,
        "MATCH (a:Autor {fichaId: $fichaId})-[:RELACIONADO_CON]->(ml:MitoLeyenda) RETURN ml",
        ficha_id, "ml",
    )

    resultado_base["multimedia"] = _consultar_relacion(
        session,
        "MATCH (m:Multimedia)-[:ASOCIADA_A]->(a:Autor {fichaId: $fichaId}) RETURN m",
        ficha_id, "m",
    )

    return resultado_base


def enriquecer_obra(session, obra_nodo: dict) -> Dict[str, Any]:
    """
    Dado un nodo Obra, trae el autor asociado y sus multimedia.
    """
    ficha_id = obra_nodo.get("fichaId")
    autor = None
    multimedia = []

    if ficha_id:
        try:
            records = session.run(
                """
                MATCH (a:Autor)-[:ESCRIBIO]->(o:Obra {fichaId: $fichaId})
                RETURN a
                LIMIT 1
                """,
                fichaId=ficha_id,
            )
            record = records.single()
            if record:
                autor = _limpiar_nodo(record["a"])
        except Exception as e:
            logger.warning("Error al buscar autor de obra %s: %s", ficha_id, e)

        multimedia = _consultar_relacion(
            session,
            "MATCH (m:Multimedia)-[:ASOCIADA_A]->(o:Obra {fichaId: $fichaId}) RETURN m",
            ficha_id, "m",
        )

    return {
        "obra": obra_nodo,
        "autor": autor,
        "multimedia": multimedia,
    }
