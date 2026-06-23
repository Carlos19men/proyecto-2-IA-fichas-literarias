"""
Diagnóstico completo para depurar búsquedas que no devuelven resultados.

Ejecutar desde la raíz del proyecto:
    python -m src.diagnostico_busqueda
"""

import logging
import json
import os
import sys

# Configurar logging verbose
logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s | %(name)s | %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("diagnostico")

from src.database.connection import db
from src.busqueda.buscador import _escapar_lucene

QUERY_NOMBRE = "Ramón Isidro"


def diagnostico_conexion():
    print("\n" + "=" * 60)
    print("1. VERIFICANDO CONEXIÓN A NEO4J")
    print("=" * 60)
    ok = db.test_connection()
    print(f"   Conexion Neo4j: {'OK' if ok else 'FALLO'}")
    return ok


def diagnostico_nodos(session):
    print("\n" + "=" * 60)
    print("2. NODOS AUTOR EN LA BASE DE DATOS")
    print("=" * 60)
    records = session.run("MATCH (a:Autor) RETURN a.nombres, a.apellidos, a.fichaId LIMIT 20")
    rows = list(records)
    if not rows:
        print("   [!] No hay nodos Autor en la base de datos")
        return
    for r in rows:
        print(f"   - {r['a.nombres']} {r['a.apellidos']} | fichaId={r['a.fichaId']}")
    print(f"\n   Total mostrado: {len(rows)} (max 20)")


def diagnostico_indices_fulltext(session):
    print("\n" + "=" * 60)
    print("3. INDICES FULLTEXT EXISTENTES")
    print("=" * 60)
    try:
        records = session.run("SHOW FULLTEXT INDEXES")
        rows = list(records)
        if not rows:
            print("   [!] No hay indices fulltext creados")
        for r in rows:
            print(f"   - {r['name']} | state={r.get('state', '?')} | labels={r.get('labelsOrTypes', [])}")
    except Exception as e:
        print(f"   [ERR] Error listando indices: {e}")


def diagnostico_busqueda_directa(session):
    print("\n" + "=" * 60)
    print("4. BUSQUEDA DIRECTA CYPHER (sin indice)")
    print("=" * 60)
    queries = [
        ("Exacto nombres=Ramon Isidro", "MATCH (a:Autor) WHERE a.nombres = 'Ram\u00f3n Isidro' RETURN a LIMIT 5"),
        ("CONTAINS Ramon (con tilde)", "MATCH (a:Autor) WHERE a.nombres CONTAINS 'Ram\u00f3n' OR a.apellidos CONTAINS 'Ram\u00f3n' RETURN a LIMIT 5"),
        ("CONTAINS ramon (sin tilde, toLower)", "MATCH (a:Autor) WHERE toLower(a.nombres) CONTAINS 'ramon' OR toLower(a.apellidos) CONTAINS 'ramon' RETURN a LIMIT 5"),
        ("CONTAINS Isidro", "MATCH (a:Autor) WHERE a.nombres CONTAINS 'Isidro' OR a.apellidos CONTAINS 'Isidro' RETURN a LIMIT 5"),
    ]
    for desc, cypher in queries:
        try:
            rows = list(session.run(cypher))
            if rows:
                print(f"   [OK] '{desc}': {len(rows)} resultado(s)")
                for r in rows:
                    nodo = dict(r["a"])
                    nodo.pop("embedding", None)
                    print(f"     -> nombres={nodo.get('nombres')}, apellidos={nodo.get('apellidos')}, fichaId={nodo.get('fichaId')}")
            else:
                print(f"   [NO] '{desc}': sin resultados")
        except Exception as e:
            print(f"   [ERR] '{desc}': ERROR -> {e}")


def diagnostico_fulltext_query(session):
    print("\n" + "=" * 60)
    print("5. BUSQUEDA FULLTEXT (como lo hace el buscador)")
    print("=" * 60)

    query_original = QUERY_NOMBRE
    query_escapada = _escapar_lucene(query_original)

    print(f"   Query original  : '{query_original}'")
    print(f"   Query escapada  : '{query_escapada}'")

    variantes = [
        ("Query escapada", query_escapada),
        ("Sin escape / literal", query_original),
        ("Solo primer nombre", query_original.split()[0]),
        ("Solo segundo nombre", query_original.split()[1] if len(query_original.split()) > 1 else ""),
        ("Con wildcard *", f"{query_original.split()[0]}*"),
        ("Sin tilde Ramon", "Ramon Isidro"),
    ]

    INDEX_NAME = "fulltext_autor_names"

    for desc, texto in variantes:
        if not texto:
            continue
        try:
            records = session.run(
                """
                CALL db.index.fulltext.queryNodes($indexName, $texto)
                YIELD node, score
                RETURN node, score
                LIMIT 5
                """,
                indexName=INDEX_NAME,
                texto=texto,
            )
            rows = list(records)
            if rows:
                print(f"\n   [OK] '{desc}' (texto='{texto}'): {len(rows)} resultado(s)")
                for r in rows:
                    nodo = dict(r["node"])
                    nodo.pop("embedding", None)
                    print(f"     -> score={r['score']:.4f} | {nodo.get('nombres')} {nodo.get('apellidos')}")
            else:
                print(f"   [NO] '{desc}' (texto='{texto}'): sin resultados")
        except Exception as e:
            print(f"   [ERR] '{desc}' (texto='{texto}'): ERROR -> {e}")


def diagnostico_embeddings():
    print("\n" + "=" * 60)
    print("6. ESTADO DE EMBEDDINGS Y LLM")
    print("=" * 60)
    try:
        from src.busqueda.buscador import GraphRAGSearcher
        s = GraphRAGSearcher()
        print(f"   Embeddings activos: {'SI' if s.embeddings else 'NO (busqueda vectorial deshabilitada)'}")
        print(f"   LLM activo        : {'SI' if s.llm else 'NO (sintesis deshabilitada)'}")
    except Exception as e:
        print(f"   [ERR] Error inicializando GraphRAGSearcher: {e}")


def main():
    print("=" * 60)
    print(f"  DIAGNOSTICO DE BUSQUEDA: '{QUERY_NOMBRE}'")
    print("=" * 60)

    if not diagnostico_conexion():
        print("\n✗ No se puede continuar sin conexión a Neo4j.")
        return

    with db.driver.session() as session:
        diagnostico_nodos(session)
        diagnostico_indices_fulltext(session)
        diagnostico_busqueda_directa(session)
        diagnostico_fulltext_query(session)

    diagnostico_embeddings()

    print("\n" + "=" * 60)
    print("  FIN DEL DIAGNÓSTICO")
    print("=" * 60)


if __name__ == "__main__":
    main()
