"""
Script de prueba del pipeline de ingesta literaria.

Modos de uso:
  1. Prueba rápida (sin Neo4j) — solo lectura + extracción:
       python test_ingesta.py

  2. Prueba completa (con Neo4j):
       python test_ingesta.py --neo4j

  3. Prueba sobre una carpeta específica:
       python test_ingesta.py --carpeta "Diccionario/Diccionario/Montes, Ramón Isidro"
"""

import sys
import json
from pathlib import Path

# Fichas de prueba disponibles en el Diccionario
FICHAS_DISPONIBLES = {
    "montes": "Diccionario/Diccionario/Montes, Ramón Isidro",
    "gonzalez": "Diccionario/Diccionario/González de Alegría, Elisa",
    "pirrongeli": "Diccionario/Diccionario/Pirrongeli, Oscar",
    "teresa": "Diccionario/Diccionario/Teresa Coraspe",
    "horizontes": "Diccionario/Diccionario/Revista Horizontes",
    "salloum": "Diccionario/Salloum Bitar, Abraham",
    "peraza": "Diccionario/Peraza, Celestino",
    "mistos": "Diccionario/Mitos y leyendas",
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
        carpeta = FICHAS_DISPONIBLES["teresa"]

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
        print("\n📋 JSON extraído (autor):")
        datos = ficha.autor.model_dump(exclude={"obras", "criticas", "multimedia"})
        print(json.dumps(datos, ensure_ascii=False, indent=2))

        print(f"\n📚 Obras encontradas: {len(ficha.autor.obras)}")
        for o in ficha.autor.obras:
            print(f"   - {o.titulo} ({o.fecha_publicacion})")

        print(f"\n📝 Críticas encontradas: {len(ficha.autor.criticas)}")
        for c in ficha.autor.criticas:
            print(f"   - {c.titulo} — {c.autor}")

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
