"""
Pipeline de ingesta de datos literarios.

Flujo completo para una carpeta de ficha:
  escanear_carpeta_ficha(carpeta)
    → convertir_a_markdown(ruta)             [preprocess.py]
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
    leer_archivo_ficha,
    leer_texto_principal,
    clasificar_archivo,
)
from src.ingestion.extractor import extraer_json_de_ficha
from src.ingestion.embeddings import poblar_embeddings
from src.ingestion.schemas import FichaLiterariaSchema, Multimedia, ChunkSchema, ObraSchema
from src.ingestion.preprocess import convert_to_markdown
from src.ingestion.chunking import chunk_text
from src.ingestion.validator import validate_ficha_evidence


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
        # intentar obtener la ruta principal (usar leer_texto_principal existente para elegir)
        try:
            ruta_principal = leer_texto_principal(carpeta)[1]
        except Exception:
            ruta_principal = None

        ruta_md = None
        if ruta_principal:
            ruta_md = convert_to_markdown(ruta_principal)

        # si conversion exitosa usamos el .md, si no usamos la función de lectura normal
        if ruta_md:
            texto = leer_archivo_ficha(ruta_md)
            ruta_leida = ruta_md
        else:
            texto, ruta_leida = leer_texto_principal(carpeta)
        print(f"   → Archivo leído: {Path(ruta_leida).name} ({len(texto)} caracteres)")

        # Paso intermedio: dividir el Markdown en chunks antes de extraer e insertar.
        print("✂️  Paso 2.1: Dividiendo en chunks para búsquedas vectoriales...")
        ficha_chunks = chunk_text(texto, Path(ruta_leida).name)

        ficha: FichaLiterariaSchema = extraer_json_de_ficha(texto)
        ficha.chunks = [ChunkSchema(**chunk) for chunk in ficha_chunks]

        # Normalizaciones: asegurar nombre_completo y mapear posibles obras encontradas
        try:
            autor = ficha.autor
            if not getattr(autor, "nombre_completo", None):
                n = getattr(autor, "nombres", None)
                a = getattr(autor, "apellidos", None)
                if n and a:
                    autor.nombre_completo = f"{n} {a}"
        except Exception:
            pass

        # Intentar extraer seudónimo del texto si no lo trajo el extractor
        try:
            if not getattr(ficha.autor, "seudonimo", None) and texto:
                import re
                m = re.search(r"pseud[oó]nimo(?:\s+de)?[:\s\"]*([A-Za-zÁÉÍÓÚáéíóúÑñ\-]+)", texto, flags=re.IGNORECASE)
                if m:
                    ficha.autor.seudonimo = m.group(1)
        except Exception:
            pass

        # Si el extractor colocó obras en top-level `mitos_leyendas` o `revistas`, mapearlas a autor.obras
        try:
            if not getattr(ficha.autor, "obras", None):
                obras_mapeadas = []
                for source_name in ("mitos_leyendas", "revistas"):
                    items = getattr(ficha, source_name, None)
                    if not items:
                        continue
                    for m in items:
                        if isinstance(m, dict):
                            titulo = m.get("titulo")
                            descripcion = m.get("descripcion") or m.get("tema_principal") or m.get("genero")
                            fecha_publicacion = m.get("fecha_publicacion") or m.get("fecha_primer_numero") or ""
                            lugar = m.get("lugar_publicacion") or m.get("lugar_difusion")
                            idioma = m.get("idioma_original")
                        else:
                            titulo = getattr(m, "titulo", None)
                            descripcion = getattr(m, "descripcion", None) or getattr(m, "tema_principal", None) or getattr(m, "genero", None)
                            fecha_publicacion = getattr(m, "fecha_publicacion", None) or getattr(m, "fecha_primer_numero", None) or ""
                            lugar = getattr(m, "lugar_publicacion", None) or getattr(m, "lugar_difusion", None)
                            idioma = getattr(m, "idioma_original", None)
                        obras_mapeadas.append(
                            ObraSchema(
                                titulo=titulo or "",
                                genero=descripcion or "desconocido",
                                fecha_publicacion=fecha_publicacion,
                                lugar_publicacion=lugar if isinstance(lugar, dict) else None,
                                editorial=None,
                                descripcion=descripcion,
                                idioma_original=idioma or "español",
                                multimedia=[],
                            )
                        )
                if obras_mapeadas:
                    ficha.autor.obras = obras_mapeadas
        except Exception:
            pass

        # Validar evidencia en obras y críticas antes de proseguir a embeddings/inserción
        try:
            ficha, removed = validate_ficha_evidence(ficha)
        except Exception:
            removed = {"obras": [], "criticas": []}

        print(f"   → Autor detectado: {ficha.autor.nombres} {ficha.autor.apellidos}")
        print(f"   → Obras (verificadas): {len(ficha.autor.obras)} | Críticas (verificadas): {len(ficha.autor.criticas)}")
        print(f"   → Chunks generados: {len(ficha.chunks)}")

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
