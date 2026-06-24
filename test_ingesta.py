"""
Script de prueba del pipeline de ingesta literaria.

Modos de uso:
  1. Prueba rápida (sin Neo4j) — solo lectura + extracción:
       python test_ingesta.py

  2. Prueba completa (con Neo4j):
       python test_ingesta.py --neo4j

  3. Prueba sobre una carpeta específica:
       python test_ingesta.py --carpeta "data/raw/Montes, Ramón Isidro"
"""

import sys
import json
from pathlib import Path

# Fichas de prueba disponibles en el data
FICHAS_DISPONIBLES = {
    "montes": "data/raw/Montes, Ramón Isidro",
    "gonzalez": "data/raw/González de Alegría, Elisa",
    "pirrongeli": "data/raw/Pirrongeli, Oscar",
    "teresa": "data/raw/Teresa Coraspe",
    "horizontes": "data/raw/Revista Horizontes",
    "salloum": "data/raw/Salloum Bitar, Abraham",
    "peraza": "data/raw/Peraza, Celestino",
    "mistos": "data/raw/Mitos y leyendas",
}


def prueba_loaders():
    """Verifica que el loader multiarchivo funciona correctamente."""
    print("\n" + "="*60)
    print("🧪 TEST 1: Loaders multiarchivo")
    print("="*60)

    from src.ingestion.loaders import (
        leer_archivo_ficha, clasificar_archivo, escanear_carpeta_ficha
    )

    # Test clasificador
    assert clasificar_archivo("foto.jpg") == "imagen"
    assert clasificar_archivo("voz.mp3") == "audio"
    assert clasificar_archivo("libro.pdf") == "texto"
    assert clasificar_archivo("ficha.docx") == "texto"
    print("   ✅ clasificar_archivo() funciona correctamente")

    # Test escanear carpeta Montes (tiene .docx + .jpg + .pdf)
    carpeta_montes = FICHAS_DISPONIBLES["montes"]
    if Path(carpeta_montes).exists():
        archivos = escanear_carpeta_ficha(carpeta_montes)
        print(f"   📂 Montes, Ramón Isidro:")
        print(f"      Texto:   {archivos['texto']}")
        print(f"      Imágenes: {archivos['imagen']}")
        print(f"      PDFs en texto: {[f for f in archivos['texto'] if f.endswith('.pdf')]}")
        assert len(archivos["texto"]) > 0, "Debe haber al menos un archivo de texto"
        assert len(archivos["imagen"]) > 0, "Debe haber al menos una imagen"
        print("   ✅ escanear_carpeta_ficha() funciona correctamente")
    else:
        print(f"   ⚠️  Carpeta no encontrada: {carpeta_montes}")

    print("\n✅ TEST 1 completado")


def prueba_extraccion(carpeta: str = None, con_neo4j: bool = False):
    """Ejecuta el pipeline completo sobre una ficha real."""
    if carpeta is None:
        carpeta = FICHAS_DISPONIBLES["mistos"]

    print("\n" + "="*60)
    print(f"🧪 TEST 2: Pipeline completo")
    print(f"   Carpeta: {carpeta}")
    print(f"   Neo4j:   {'Sí' if con_neo4j else 'No (dry run)'}")
    print("="*60)

    from src.ingestion.pipeline import procesar_carpeta

    if not Path(carpeta).exists():
        print(f"❌ La carpeta no existe: {carpeta}")
        return

    if con_neo4j:
        from src.database.connection import db
        if not db.test_connection():
            print("❌ No se pudo conectar a Neo4j. Ejecuta Docker primero.")
            return
        with db.driver.session() as session:
            ficha = procesar_carpeta(
                carpeta,
                session=session,
                generar_embeddings=True,
                insertar_neo4j=True,
            )
    else:
        ficha = procesar_carpeta(
            carpeta,
            session=None,
            generar_embeddings=False,   # Ollama puede no estar corriendo
            insertar_neo4j=False,
        )

    if ficha:
        from src.ingestion.revista_parser import es_resultado_ficha_revista

        es_mitos = bool(ficha.mitos_leyendas) or "mitos" in str(carpeta).lower()
        es_revista = es_resultado_ficha_revista(ficha) or "revista" in str(carpeta).lower()

        if es_mitos and ficha.mitos_leyendas:
            print("\n📋 JSON extraído (mito/leyenda):")
            for m in ficha.mitos_leyendas:
                datos_mito = m.model_dump(exclude={"multimedia", "embedding"})
                print(json.dumps(datos_mito, ensure_ascii=False, indent=2))
        elif es_revista and ficha.revistas:
            print("\n📋 JSON extraído (revista):")
            for r in ficha.revistas:
                datos_rev = r.model_dump(exclude={"multimedia", "embedding"})
                print(json.dumps(datos_rev, ensure_ascii=False, indent=2))
            if ficha.autor.criticas:
                print("\n📋 Críticas asociadas:")
                print(json.dumps(
                    [c.model_dump(exclude={"embedding"}) for c in ficha.autor.criticas],
                    ensure_ascii=False,
                    indent=2,
                ))
        else:
            print("\n📋 JSON extraído (autor):")
            datos = ficha.autor.model_dump(exclude={"obras", "criticas", "multimedia"})
            print(json.dumps(datos, ensure_ascii=False, indent=2))

        if not es_revista:
            print(f"\n📚 Obras encontradas: {len(ficha.autor.obras)}")
            for o in ficha.autor.obras:
                print(f"   - {o.titulo} ({o.fecha_publicacion})")

        print(f"\n📝 Críticas encontradas: {len(ficha.autor.criticas)}")
        for c in ficha.autor.criticas:
            print(f"   - {c.titulo} — {c.autor}")

        if not es_revista:
            print(f"\n📰 Revistas encontradas: {len(ficha.revistas)}")
            for r in ficha.revistas:
                nums = f" — {r.numeros_publicados}" if r.numeros_publicados else ""
                fecha = f" ({r.fecha_primer_numero})" if r.fecha_primer_numero else ""
                print(f"   - {r.titulo}{fecha}{nums}")
        elif ficha.revistas:
            r = ficha.revistas[0]
            print(f"\n📰 Revista: {r.titulo} ({r.fecha_primer_numero} – {r.fecha_ultimo_numero})")

        if ficha.antologias:
            print(f"\n📖 Antologías encontradas: {len(ficha.antologias)}")
            for a in ficha.antologias:
                print(f"   - {a.titulo} ({a.fecha_publicacion})")

        if ficha.agrupaciones:
            print(f"\n👥 Agrupaciones: {len(ficha.agrupaciones)}")
            for g in ficha.agrupaciones:
                print(f"   - {g.nombre}")

        if ficha.mitos_leyendas:
            print(f"\n🌿 Mitos y leyendas: {len(ficha.mitos_leyendas)}")
            for m in ficha.mitos_leyendas:
                print(f"   - {m.titulo} ({m.comunidad_creadora}) — {m.tema_principal}")

        if es_revista and ficha.revistas:
            print(f"\n🖼️  Multimedia adjuntada: {len(ficha.revistas[0].multimedia)}")
            for m in ficha.revistas[0].multimedia[:5]:
                print(f"   - [{m.tipo}] {Path(m.enlace).name}")
            if len(ficha.revistas[0].multimedia) > 5:
                print(f"   - ... y {len(ficha.revistas[0].multimedia) - 5} más")
        else:
            print(f"\n🖼️  Multimedia adjuntada: {len(ficha.autor.multimedia)}")
            for m in ficha.autor.multimedia:
                print(f"   - [{m.tipo}] {Path(m.enlace).name}")


def main():
    args = sys.argv[1:]
    carpeta = None
    con_neo4j = "--neo4j" in args

    # Buscar argumento --carpeta
    if "--carpeta" in args:
        idx = args.index("--carpeta")
        if idx + 1 < len(args):
            carpeta = args[idx + 1]

    # Ejecutar tests
    prueba_loaders()
    prueba_extraccion(carpeta=carpeta, con_neo4j=con_neo4j)

    print("\n🎉 Todos los tests completados.\n")


if __name__ == "__main__":
    main()
