"""
Pipeline de ingesta de datos literarios.

Flujo completo para una carpeta de ficha:
  escanear_carpeta_ficha(carpeta)
    → leer_texto_principal(carpeta)          [loaders.py]
    → extraer_json_de_ficha(texto)           [extractor.py]
    → adjuntar_multimedia(ficha, archivos)   [este módulo]
    → poblar_embeddings(ficha)               [embeddings.py]
    → insertar_ficha(ficha, session)         [insertor.py]

También expone `procesar_directorio(raiz)` para lanzar
el pipeline sobre todas las carpetas de un directorio padre.
"""

import os
from pathlib import Path
from typing import Optional

from src.ingestion.loaders import (
    escanear_carpeta_ficha,
    leer_texto_principal,
    clasificar_archivo,
)
from src.ingestion.extractor import extraer_json_de_ficha
from src.ingestion.embeddings import poblar_embeddings
from src.ingestion.schemas import FichaLiterariaSchema, Multimedia


# ---------------------------------------------------------------------------
# Adjuntar multimedia detectada en la carpeta al schema extraído
# ---------------------------------------------------------------------------

def adjuntar_multimedia_carpeta(
    ficha: FichaLiterariaSchema,
    archivos: dict,
    restriccion_defecto: str = "público",
) -> FichaLiterariaSchema:
    """
    Toma los archivos multimedia encontrados en la carpeta de la ficha
    (imágenes, audio, video) y los agrega a `ficha.autor.multimedia`
    si aún no están registrados.

    Esto permite que un .jpg o .pdf encontrado junto al .docx
    quede reflejado automáticamente en el schema.
    """
    enlaces_existentes = {m.enlace for m in ficha.autor.multimedia}

    for tipo_clave, tipo_valor in [("imagen", "imagen"), ("audio", "audio"), ("video", "video")]:
        for ruta in archivos.get(tipo_clave, []):
            if ruta not in enlaces_existentes:
                ficha.autor.multimedia.append(
                    Multimedia(
                        enlace=ruta,
                        tipo=tipo_valor,
                        restriccion=restriccion_defecto,
                    )
                )

    # PDFs de obras se adjuntan también como multimedia de tipo "pdf"
    for ruta in archivos.get("texto", []):
        ext = Path(ruta).suffix.lower()
        if ext == ".pdf" and ruta not in enlaces_existentes:
            ficha.autor.multimedia.append(
                Multimedia(
                    enlace=ruta,
                    tipo="pdf",
                    restriccion=restriccion_defecto,
                )
            )

    return ficha


# ---------------------------------------------------------------------------
# Pipeline principal para una carpeta
# ---------------------------------------------------------------------------

def procesar_carpeta(
    carpeta: str,
    session=None,
    generar_embeddings: bool = True,
    insertar_neo4j: bool = True,
) -> Optional[FichaLiterariaSchema]:
    """
    Ejecuta el pipeline completo sobre una carpeta de ficha.

    Args:
        carpeta: Ruta al directorio que contiene los archivos de la ficha.
        session: Sesión activa de Neo4j. Si es None, se omite la inserción.
        generar_embeddings: Si True, genera vectores con Ollama antes de insertar.
        insertar_neo4j: Si True y session no es None, inserta en Neo4j.

    Returns:
        El objeto FichaLiterariaSchema procesado, o None si hubo un error.
    """
    print(f"\n{'='*60}")
    print(f"📂 Procesando carpeta: {Path(carpeta).name}")
    print(f"{'='*60}")

    try:
        # Paso 1 — Escanear archivos de la carpeta
        print("📋 Paso 1/4: Escaneando archivos...")
        archivos = escanear_carpeta_ficha(carpeta)
        print(f"   → Texto: {len(archivos['texto'])} archivo(s)")
        print(f"   → Imágenes: {len(archivos['imagen'])} archivo(s)")
        print(f"   → Audio: {len(archivos['audio'])} archivo(s)")
        print(f"   → Video: {len(archivos['video'])} archivo(s)")

        # Paso 2 — Leer texto principal y extraer con LLM
        print("📄 Paso 2/4: Leyendo texto y extrayendo con IA...")
        texto, ruta_leida = leer_texto_principal(carpeta)
        print(f"   → Archivo leído: {Path(ruta_leida).name} ({len(texto)} caracteres)")

        ficha: FichaLiterariaSchema = extraer_json_de_ficha(texto)
        print(f"   → Autor detectado: {ficha.autor.nombres} {ficha.autor.apellidos}")
        print(f"   → Obras: {len(ficha.autor.obras)} | Críticas: {len(ficha.autor.criticas)}")

        # Paso 3 — Adjuntar multimedia de la carpeta
        print("🖼️  Paso 3/4: Adjuntando multimedia de la carpeta...")
        ficha = adjuntar_multimedia_carpeta(ficha, archivos)
        print(f"   → Multimedia total en autor: {len(ficha.autor.multimedia)} elemento(s)")

        # Paso 4 — Embeddings
        if generar_embeddings:
            print("🧮 Paso 4/4: Generando embeddings...")
            ficha = poblar_embeddings(ficha)
        else:
            print("⏭️  Paso 4/4: Embeddings omitidos (generar_embeddings=False)")

        # Paso 5 — Insertar en Neo4j
        if insertar_neo4j and session is not None:
            print("🗄️  Guardando en Neo4j...")
            from src.database.insertor import insertar_ficha
            insertar_ficha(ficha, session)
            print("   ✅ Ficha guardada en el grafo.")
        elif insertar_neo4j and session is None:
            print("⚠️  insertar_neo4j=True pero no se proporcionó session. Omitiendo inserción.")

        print(f"\n✅ Carpeta procesada correctamente: {Path(carpeta).name}")
        return ficha

    except Exception as e:
        print(f"\n❌ Error procesando '{carpeta}': {e}")
        raise


# ---------------------------------------------------------------------------
# Procesar un directorio entero con múltiples fichas
# ---------------------------------------------------------------------------

def procesar_directorio(
    directorio_raiz: str,
    session=None,
    generar_embeddings: bool = True,
    insertar_neo4j: bool = True,
) -> list:
    """
    Escanea un directorio padre y ejecuta `procesar_carpeta` sobre
    cada subdirectorio que contenga al menos un archivo de texto.

    Args:
        directorio_raiz: Ruta padre (ej: "Diccionario/Diccionario/")
        session: Sesión Neo4j compartida para todas las fichas.
        generar_embeddings: Activar/desactivar generación de vectores.
        insertar_neo4j: Activar/desactivar inserción en Neo4j.

    Returns:
        Lista de FichaLiterariaSchema procesadas correctamente.
    """
    raiz = Path(directorio_raiz)
    if not raiz.is_dir():
        raise ValueError(f"❌ El directorio '{directorio_raiz}' no existe.")

    subcarpetas = [p for p in sorted(raiz.iterdir()) if p.is_dir()]
    print(f"\n🚀 Iniciando ingesta de {len(subcarpetas)} carpeta(s) en '{raiz.name}'")

    fichas_ok = []
    fichas_error = []

    for subcarpeta in subcarpetas:
        try:
            ficha = procesar_carpeta(
                str(subcarpeta),
                session=session,
                generar_embeddings=generar_embeddings,
                insertar_neo4j=insertar_neo4j,
            )
            if ficha:
                fichas_ok.append(ficha)
        except Exception:
            fichas_error.append(str(subcarpeta))

    print(f"\n{'='*60}")
    print(f"📊 RESUMEN FINAL")
    print(f"   ✅ Procesadas correctamente: {len(fichas_ok)}")
    print(f"   ❌ Con errores:              {len(fichas_error)}")
    if fichas_error:
        for e in fichas_error:
            print(f"      - {e}")
    print(f"{'='*60}\n")

    return fichas_ok
