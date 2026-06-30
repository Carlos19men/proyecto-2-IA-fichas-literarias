"""Verifica los campos del nodo encontrado por fulltext."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import logging
logging.basicConfig(level=logging.WARNING)

from src.database.connection import db
from src.busqueda.buscador import _escapar_lucene, INDICES_FULLTEXT

QUERY = "Ramon Isidro"
q_escaped = _escapar_lucene(QUERY)

print(f"Query: '{QUERY}' -> escaped: '{q_escaped}'")

with db.driver.session() as session:
    # 1. Probar fulltext
    cypher = """
    CALL db.index.fulltext.queryNodes($indexName, $texto)
    YIELD node, score
    RETURN node, score
    LIMIT 5
    """
    rows = list(session.run(cypher, indexName="fulltext_autor_names", texto=q_escaped))
    print(f"\nResultados fulltext ({len(rows)}):")
    for r in rows:
        nodo = dict(r["node"])
        nodo.pop("embedding", None)
        print(f"  score={r['score']:.4f}")
        print(f"  fichaId = {repr(nodo.get('fichaId'))}")
        print(f"  nombres = {repr(nodo.get('nombres'))}")
        print(f"  apellidos = {repr(nodo.get('apellidos'))}")
        print(f"  campos: {list(nodo.keys())}")
        print()

    # 2. Probar enriquecimiento manual
    if rows:
        nodo = dict(rows[0]["node"])
        nodo.pop("embedding", None)
        ficha_id = nodo.get("fichaId")
        print(f"\nEnriquecimiento con fichaId={repr(ficha_id)}:")

        if ficha_id:
            obras = list(session.run(
                "MATCH (a:Autor {fichaId: $fid})-[:ESCRIBIO]->(o:Obra) RETURN o",
                fid=ficha_id
            ))
            print(f"  Obras encontradas: {len(obras)}")
            for o in obras:
                ov = dict(o["o"])
                ov.pop("embedding", None)
                print(f"    - {ov.get('titulo')}")
        else:
            print("  [!] fichaId es None/vacío — el enriquecimiento retornará datos vacíos")
            # Intentar buscar por nombres
            nombres = nodo.get("nombres", "")
            apellidos = nodo.get("apellidos", "")
            print(f"  Intentando buscar obras por nombres='{nombres}' apellidos='{apellidos}':")
            obras = list(session.run(
                "MATCH (a:Autor {nombres: $n, apellidos: $ap})-[:ESCRIBIO]->(o:Obra) RETURN o",
                n=nombres, ap=apellidos
            ))
            print(f"  Obras encontradas (por nombre/apellido): {len(obras)}")
