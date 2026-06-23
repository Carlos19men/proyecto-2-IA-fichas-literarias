"""
Verifica el estado de las relaciones en la base de datos para el autor Ramón Isidro.
Ejecutar: .venv\Scripts\python.exe -m src.check_relaciones
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import logging
logging.basicConfig(level=logging.WARNING)

from src.database.connection import db

FICHA_ID = "AUTOR_CED91957"

print(f"Verificando relaciones para fichaId={FICHA_ID}")
print("=" * 60)

with db.driver.session() as session:
    # 1. Datos del nodo autor
    r = session.run("MATCH (a:Autor {fichaId: $fid}) RETURN a", fid=FICHA_ID).single()
    if r:
        nodo = dict(r["a"])
        nodo.pop("embedding", None)
        print("NODO AUTOR:")
        for k, v in nodo.items():
            print(f"  {k} = {repr(v)}")
    else:
        print(f"[!] No se encontró Autor con fichaId={FICHA_ID}")

    print()

    # 2. Obras
    obras = list(session.run(
        "MATCH (a:Autor {fichaId: $fid})-[:ESCRIBIO]->(o:Obra) RETURN o",
        fid=FICHA_ID
    ))
    print(f"Obras (ESCRIBIO): {len(obras)}")
    for o in obras:
        ov = dict(o["o"])
        ov.pop("embedding", None)
        print(f"  - {ov.get('titulo')} ({ov.get('fichaId')})")

    # 3. Críticas
    criticas = list(session.run(
        "MATCH (c:Critica)-[:CRITICA_DE]->(a:Autor {fichaId: $fid}) RETURN c",
        fid=FICHA_ID
    ))
    print(f"Criticas (CRITICA_DE): {len(criticas)}")

    # 4. Agrupaciones
    agrupaciones = list(session.run(
        "MATCH (a:Autor {fichaId: $fid})-[:PERTENECE_A]->(ag:Agrupacion) RETURN ag",
        fid=FICHA_ID
    ))
    print(f"Agrupaciones (PERTENECE_A): {len(agrupaciones)}")
    for ag in agrupaciones:
        agv = dict(ag["ag"])
        print(f"  - {agv.get('nombre')}")

    # 5. Resumen general de la BD
    print()
    print("=" * 60)
    print("RESUMEN DE LA BASE DE DATOS:")
    for label in ["Autor", "Obra", "Critica", "Agrupacion", "Revista", "Antologia", "MitoLeyenda"]:
        count = session.run(f"MATCH (n:{label}) RETURN count(n) AS c").single()["c"]
        print(f"  {label}: {count} nodos")

    # Relaciones
    print()
    print("RELACIONES:")
    for rel in ["ESCRIBIO", "CRITICA_DE", "PERTENECE_A", "RELACIONADO_CON", "PUBLICA", "CONTIENE"]:
        count = session.run(f"MATCH ()-[r:{rel}]->() RETURN count(r) AS c").single()["c"]
        print(f"  :{rel}: {count}")
