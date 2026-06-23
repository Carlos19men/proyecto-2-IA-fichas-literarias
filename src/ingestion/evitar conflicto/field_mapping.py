"""
field_mapping.py — Mapeo semántico Word → Schema (Neo4j)
=========================================================

Este módulo resuelve el problema de que los campos del documento Word
tienen nombres largos y descriptivos, mientras que el schema Pydantic
(y Neo4j) usa nombres cortos en snake_case.

Uso principal:
    from src.ingestion.field_mapping import FIELD_MAP, normalize, get_prompt_mapping_block

El bloque de texto `MAPPING_PROMPT_BLOCK` está diseñado para inyectarse
directamente en el system-prompt del extractor.py, de modo que el LLM
sepa con precisión a qué campo de Pydantic corresponde cada etiqueta
del formulario Word.
"""

import unicodedata
import re
from typing import Optional


# =============================================================================
# UTILIDADES DE NORMALIZACIÓN
# =============================================================================

def normalize(text: str) -> str:
    """
    Normaliza una cadena para hacer matching robusto:
      - Quita tildes (á → a, é → e …)
      - Pasa a minúsculas
      - Elimina signos de puntuación al inicio/final
      - Colapsa espacios múltiples

    Ejemplo:
        normalize("Seudónimo:") → "seudonimo"
        normalize("Título")     → "titulo"
    """
    # 1. Descomponer caracteres Unicode (NFD) y descartar marcas diacríticas
    nfd = unicodedata.normalize("NFD", text)
    sin_tildes = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
    # 2. Minúsculas
    lower = sin_tildes.lower()
    # 3. Quitar puntuación al inicio/final (pero mantener paréntesis internos)
    stripped = lower.strip(":.…,;!¡?¿ \t")
    # 4. Colapsar múltiples espacios
    clean = re.sub(r"\s+", " ", stripped)
    return clean


# =============================================================================
# MAPEO UNO-A-UNO:  Texto del Word → Ruta de campo en el schema
# =============================================================================
# Formato de la ruta:
#   "entidad.campo"          → propiedad directa
#   "entidad.sub_objeto.campo" → campo dentro de un objeto anidado (Lugar, Multimedia)
#   "entidad.lista[]"        → campo que contiene una lista de objetos
#
# La clave es el resultado de normalize() aplicado al texto del Word.
# Se incluyen variantes y formas abreviadas para máxima cobertura.

FIELD_MAP: dict[str, str] = {

    # -------------------------------------------------------------------------
    # SECCIÓN AUTOR — Identidad
    # -------------------------------------------------------------------------
    "nombres":                                              "autor.nombres",
    "apellidos":                                            "autor.apellidos",
    "nombre completo":                                      "autor.nombre_completo",
    "sexo":                                                 "autor.sexo",
    "genero":                                               "autor.sexo",           # alias cuando Género = Femenino/Masculino
    "seudonimo":                                            "autor.seudonimo",
    "pseudonimo":                                           "autor.seudonimo",

    # -------------------------------------------------------------------------
    # SECCIÓN AUTOR — Cronología
    # -------------------------------------------------------------------------
    "fecha de nacimiento":                                  "autor.fecha_nacimiento",
    "fecha de fallecimiento":                               "autor.fecha_fallecimiento",
    "fecha de muerte":                                      "autor.fecha_fallecimiento",

    # -------------------------------------------------------------------------
    # SECCIÓN AUTOR — Lugar de nacimiento (campo compuesto → sub-objeto Lugar)
    # -------------------------------------------------------------------------
    "lugar de nacimiento (ciudad, municipio, estado, pais)": "autor.lugar_nacimiento",
    "lugar de nacimiento":                                   "autor.lugar_nacimiento",
    "lugar nacimiento":                                      "autor.lugar_nacimiento",
    # Sub-campos individuales (si el Word los separa)
    "lugar de nacimiento - ciudad":                         "autor.lugar_nacimiento.ciudad",
    "lugar de nacimiento - municipio":                      "autor.lugar_nacimiento.municipio",
    "lugar de nacimiento - estado":                         "autor.lugar_nacimiento.estado",
    "lugar de nacimiento - pais":                           "autor.lugar_nacimiento.pais",

    # -------------------------------------------------------------------------
    # SECCIÓN AUTOR — Lugar de fallecimiento
    # -------------------------------------------------------------------------
    "lugar de fallecimiento (ciudad, municipio, estado, pais)": "autor.lugar_fallecimiento",
    "lugar de fallecimiento":                                    "autor.lugar_fallecimiento",
    "lugar fallecimiento":                                       "autor.lugar_fallecimiento",
    "lugar de muerte":                                           "autor.lugar_fallecimiento",
    # Sub-campos individuales
    "lugar de fallecimiento - ciudad":                      "autor.lugar_fallecimiento.ciudad",
    "lugar de fallecimiento - municipio":                   "autor.lugar_fallecimiento.municipio",
    "lugar de fallecimiento - estado":                      "autor.lugar_fallecimiento.estado",
    "lugar de fallecimiento - pais":                        "autor.lugar_fallecimiento.pais",

    # -------------------------------------------------------------------------
    # SECCIÓN AUTOR — Trayectoria  ← CASOS CRÍTICOS (texto largo → nombre corto)
    # -------------------------------------------------------------------------
    # El Word usa la descripción completa del campo; el schema usa nombre corto.
    "actividad relevante que haya realizado el autor (tipo (estudios realizados, cargos publicos, profesion ejercida, etc.), lugar, periodo)":
        "autor.actividad_relevante",
    "actividad relevante que haya realizado el autor":      "autor.actividad_relevante",
    "actividad relevante realizada por el autor":           "autor.actividad_relevante",
    "actividad relevante realizado el autor":               "autor.actividad_relevante",
    "actividad relevante":                                  "autor.actividad_relevante",
    "actividades relevantes":                               "autor.actividad_relevante",
    "estudios, cargos, profesion":                          "autor.actividad_relevante",

    "familiares destacados (padres, hermanos, hijos)":      "autor.familiares_destacados",
    "familiares destacados":                                "autor.familiares_destacados",
    "familiares":                                           "autor.familiares_destacados",
    "familia destacada":                                    "autor.familiares_destacados",

    "tematica principal desarrollada en el conjunto de su obra": "autor.tematica_principal",
    "tematica principal":                                   "autor.tematica_principal",
    "temas principales":                                    "autor.tematica_principal",
    "tematica":                                             "autor.tematica_principal",

    "genero principal cultivado":                           "autor.genero_principal",
    "genero principal":                                     "autor.genero_principal",
    "genero literario principal":                           "autor.genero_principal",

    "contexto en que vivio":                                "autor.contexto_vivio",
    "contexto historico":                                   "autor.contexto_vivio",
    "contexto":                                             "autor.contexto_vivio",
    "marco historico":                                      "autor.contexto_vivio",

    # -------------------------------------------------------------------------
    # SECCIÓN AUTOR — Multimedia / Archivos  ← CASOS CRÍTICOS
    # -------------------------------------------------------------------------
    "imagen del autor (archivo jpg)":                       "autor.imagen_autor",
    "imagen del autor":                                     "autor.imagen_autor",
    "foto del autor":                                       "autor.imagen_autor",
    "imagen (jpg)":                                         "autor.imagen_autor",

    "audio con la voz del autor (archivo mp3)":             "autor.audio_voz",
    "audio con la voz del autor":                           "autor.audio_voz",
    "audio del autor":                                      "autor.audio_voz",
    "voz del autor":                                        "autor.audio_voz",
    "audio (mp3)":                                          "autor.audio_voz",

    "multimedia (enlace, tipo, restriccion)":               "autor.multimedia",
    "multimedia":                                           "autor.multimedia",
    "recurso multimedia":                                   "autor.multimedia",
    # Sub-campos de Multimedia
    "enlace":                                               "multimedia.enlace",
    "tipo":                                                 "multimedia.tipo",
    "restriccion":                                          "multimedia.restriccion",
    "restriccion de acceso":                                "multimedia.restriccion",

    # -------------------------------------------------------------------------
    # SECCIÓN OBRA
    # -------------------------------------------------------------------------
    "titulo":                                               "obra.titulo",
    "titulo de la obra":                                    "obra.titulo",
    # Género de obra (diferente a género de autor)
    "genero (novela, cuento, poesia, ensayo, revista, antologia. incluir subgeneros)": "obra.genero",
    "genero literario":                                     "obra.genero",
    # El subgénero no tiene campo propio en el Word; se extrae de los paréntesis del campo Género
    "subgenero":                                            "obra.subgenero",

    "fecha de publicacion":                                 "obra.fecha_publicacion",
    "ano de publicacion":                                   "obra.fecha_publicacion",
    "año de publicacion":                                   "obra.fecha_publicacion",

    "lugar de publicacion (ciudad, imprenta, editorial)":   "obra.lugar_publicacion",
    "lugar de publicacion":                                 "obra.lugar_publicacion",
    "lugar publicacion":                                    "obra.lugar_publicacion",
    # Sub-campos de Lugar (Obra)
    "lugar de publicacion - ciudad":                        "obra.lugar_publicacion.ciudad",
    "lugar de publicacion - municipio":                     "obra.lugar_publicacion.municipio",
    "lugar de publicacion - estado":                        "obra.lugar_publicacion.estado",
    "lugar de publicacion - pais":                          "obra.lugar_publicacion.pais",
    "editorial":                                            "obra.editorial",
    "imprenta":                                             "obra.editorial",

    "descripcion o resumen (en caso de revistas o antologias, que exista la posibilidad de mencionar a autores, temas, numeros publicados)": "obra.descripcion",
    "descripcion o resumen":                                "obra.descripcion",
    "descripcion":                                          "obra.descripcion",
    "resumen":                                              "obra.descripcion",
    "sinopsis":                                             "obra.descripcion",

    "idioma original":                                      "obra.idioma_original",

    "obra en archivo pdf, portada en jpg y en mp3 todas para descarga y lectura": "obra.multimedia",
    "obra en archivo pdf, portada en jpg":                  "obra.multimedia",

    # -------------------------------------------------------------------------
    # SECCIÓN CRÍTICA
    # -------------------------------------------------------------------------
    "tipo (libro, articulo, resena, trabajo de grado)":     "critica.tipo",
    "tipo de critica":                                      "critica.tipo",
    # Nota: "Autor" en la sección de Crítica es el crítico, no el autor de la obra
    "autor de la critica":                                  "critica.autor",
    "critico":                                              "critica.autor",
    "titulo de la critica":                                 "critica.titulo",
    "fecha de publicacion de la critica":                   "critica.fecha_publicacion",

    "referencia bibliografica (donde fue publicada la critica, incluir ademas el enlace)": "critica.referencia_bibliografica",
    "referencia bibliografica":                             "critica.referencia_bibliografica",
    "referencia":                                           "critica.referencia_bibliografica",
    "donde fue publicada":                                  "critica.referencia_bibliografica",

    "descripcion o resumen de la critica":                  "critica.descripcion_resumen",
    "resumen de la critica":                                "critica.descripcion_resumen",
    "descripcion de la critica":                            "critica.descripcion_resumen",

    # -------------------------------------------------------------------------
    # SECCIÓN AGRUPACIÓN
    # -------------------------------------------------------------------------
    "nombre de la agrupacion":                              "agrupacion.nombre",
    "nombre":                                               "agrupacion.nombre",

    "lugar de encuentros (ciudad, municipio)":              "agrupacion.lugar_encuentros",
    "lugar de encuentros":                                  "agrupacion.lugar_encuentros",
    "lugar encuentros":                                     "agrupacion.lugar_encuentros",

    "fecha de inicio":                                      "agrupacion.fecha_inicio",
    "fecha inicio":                                         "agrupacion.fecha_inicio",
    "fecha de culminacion":                                 "agrupacion.fecha_culminacion",
    "fecha culminacion":                                    "agrupacion.fecha_culminacion",
    "fecha de fin":                                         "agrupacion.fecha_culminacion",

    "caracteristica general de la agrupacion (tendencia, ideologia)": "agrupacion.caracteristica_general",
    "caracteristica general":                               "agrupacion.caracteristica_general",
    "tendencia":                                            "agrupacion.caracteristica_general",
    "ideologia":                                            "agrupacion.caracteristica_general",

    "integrantes (nombres y apellidos)":                    "agrupacion.integrantes",
    "integrantes":                                          "agrupacion.integrantes",
    "miembros":                                             "agrupacion.integrantes",

    "publicaciones de la agrupacion (titulo, ano, resumen de la obra)": "agrupacion.publicaciones",
    "publicaciones de la agrupacion":                       "agrupacion.publicaciones",
    "publicaciones":                                        "agrupacion.publicaciones",

    "actividades de la agrupacion":                         "agrupacion.actividades",
    "actividades":                                          "agrupacion.actividades",

    # -------------------------------------------------------------------------
    # SECCIÓN REVISTA
    # -------------------------------------------------------------------------
    "titulo de la revista":                                 "revista.titulo",
    "fecha de primer numero":                               "revista.fecha_primer_numero",
    "primer numero":                                        "revista.fecha_primer_numero",
    "fecha de ultimo numero":                               "revista.fecha_ultimo_numero",
    "ultimo numero":                                        "revista.fecha_ultimo_numero",
    "numeros publicados":                                   "revista.numeros_publicados",
    "numero de ejemplares":                                 "revista.numeros_publicados",

    "lugar de publicacion (ciudad, imprenta, editorial) revista": "revista.lugar_publicacion",

    "creadores (director, comite editorial, etc)":          "revista.creadores",
    "creadores":                                            "revista.creadores",
    "director":                                             "revista.creadores",
    "comite editorial":                                     "revista.creadores",

    "secciones de la revista":                              "revista.secciones",
    "secciones":                                            "revista.secciones",

    "descripcion (temas y generos predominantes, autores relevantes)": "revista.descripcion",
    "descripcion de la revista":                            "revista.descripcion",

    "idioma original de la revista":                        "revista.idioma_original",

    "obra en archivo pdf y portada en jpg, todas para descarga y lectura": "revista.multimedia",

    # -------------------------------------------------------------------------
    # SECCIÓN ANTOLOGÍA
    # -------------------------------------------------------------------------
    "autor de la antologia":                                "antologia.autor",
    "compilador":                                           "antologia.autor",
    "editor de la antologia":                               "antologia.autor",

    "titulo de la antologia":                               "antologia.titulo",

    "genero (novela, cuento, poesia, ensayo)":              "antologia.genero",
    "genero de la antologia":                               "antologia.genero",

    "fecha de publicacion de la antologia":                 "antologia.fecha_publicacion",

    "lugar de publicacion (ciudad, imprenta, editorial) antologia": "antologia.lugar_publicacion",

    "editorial de la antologia":                            "antologia.editorial",

    "descripcion o resumen (mencionar autores seleccionados)": "antologia.descripcion",
    "descripcion de la antologia":                          "antologia.descripcion",

    "idioma original de la antologia":                      "antologia.idioma_original",

    "obra en archivo pdf y portada en jpg para descarga y lectura": "antologia.multimedia",

    # -------------------------------------------------------------------------
    # SECCIÓN MITO / LEYENDA  (para Ficha mitos y leyendas.docx)
    # -------------------------------------------------------------------------
    "titulo del mito":                                      "mito_leyenda.titulo",
    "titulo de la leyenda":                                 "mito_leyenda.titulo",

    "comunidad creadora":                                   "mito_leyenda.comunidad_creadora",
    "pueblo de origen":                                     "mito_leyenda.comunidad_creadora",
    "comunidad":                                            "mito_leyenda.comunidad_creadora",

    "lugar de difusion":                                    "mito_leyenda.lugar_difusion",

    "idioma original del mito":                             "mito_leyenda.idioma_original",
    "idioma original de la leyenda":                        "mito_leyenda.idioma_original",

    "texto completo":                                       "mito_leyenda.texto_completo",
    "texto del mito":                                       "mito_leyenda.texto_completo",

    "tema principal":                                       "mito_leyenda.tema_principal",
    "temas principales del mito":                           "mito_leyenda.tema_principal",

    "descripcion del mito":                                 "mito_leyenda.descripcion",
    "descripcion de la leyenda":                            "mito_leyenda.descripcion",
    "analisis":                                             "mito_leyenda.descripcion",
}


# =============================================================================
# FUNCIÓN DE LOOKUP
# =============================================================================

def get_field(label: str) -> Optional[str]:
    """
    Dado un texto de etiqueta del Word, devuelve la ruta del campo en el
    schema Pydantic, o None si no hay mapeo conocido.

    El matching se hace después de normalizar ambos lados, por lo que es
    robusto a tildes, mayúsculas y puntuación sobrante.

    Ejemplo:
        get_field("Actividad relevante que haya realizado el autor")
        → "autor.actividad_relevante"

        get_field("Seudónimo:")
        → "autor.seudonimo"
    """
    clave = normalize(label)
    return FIELD_MAP.get(clave)


# =============================================================================
# BLOQUE PARA INYECTAR EN EL PROMPT DEL LLM
# =============================================================================

MAPPING_PROMPT_BLOCK = """
MAPEO DE CAMPOS DEL FORMULARIO:
Los campos del documento Word usan etiquetas largas y descriptivas.
Debes traducirlas al campo exacto del schema Python según esta tabla:

AUTOR:
  "Nombres"                                        → autor.nombres
  "Apellidos"                                      → autor.apellidos
  "Sexo"                                           → autor.sexo
  "Seudónimo"                                      → autor.seudonimo
  "Fecha de nacimiento"                            → autor.fecha_nacimiento
  "Fecha de fallecimiento"                         → autor.fecha_fallecimiento
  "Lugar de nacimiento (ciudad, municipio, estado, país)"
                                                   → autor.lugar_nacimiento (objeto: ciudad, municipio, estado, pais)
  "Lugar de fallecimiento (ciudad, municipio, estado, país)"
                                                   → autor.lugar_fallecimiento (objeto: ciudad, municipio, estado, pais)
  "Actividad relevante que haya realizado el autor (Tipo (estudios realizados, cargos públicos, profesión ejercida, etc.), lugar, periodo)."
                                                   → autor.actividad_relevante  ← CAMPO CRÍTICO
  "Familiares destacados (padres, hermanos, hijos…)"
                                                   → autor.familiares_destacados (lista de Persona: nombres, apellidos, rol)
  "Temática principal desarrollada en el conjunto de su obra"
                                                   → autor.tematica_principal  ← CAMPO CRÍTICO
  "Género principal cultivado"                     → autor.genero_principal
  "Contexto en que vivió"                          → autor.contexto_vivio
  "Imagen del autor (archivo jpg)"                 → autor.imagen_autor  ← CAMPO CRÍTICO
  "Audio con la voz del autor (archivo mp3)"       → autor.audio_voz  ← CAMPO CRÍTICO
  "Multimedia (Enlace, Tipo, Restricción)"         → autor.multimedia (lista de Multimedia: enlace, tipo, restriccion)

OBRA:
  "Título"                                         → obra.titulo
  "Género (novela, cuento, poesía, ensayo…)"       → obra.genero (el subgénero va en obra.subgenero)
  "Fecha de publicación"                           → obra.fecha_publicacion
  "Lugar de publicación (ciudad, imprenta, editorial)"
                                                   → obra.lugar_publicacion.ciudad / .editorial
  "Descripción o resumen"                          → obra.descripcion
  "Idioma original"                                → obra.idioma_original

CRÍTICA:
  "Tipo (libro, artículo, reseña, trabajo de grado…)" → critica.tipo
  "Autor"  [en sección Crítica]                    → critica.autor  (nombre del crítico, NO del autor literario)
  "Título" [en sección Crítica]                    → critica.titulo
  "Fecha de publicación" [en sección Crítica]      → critica.fecha_publicacion
  "Referencia bibliográfica (¿dónde fue publicada la crítica?, incluir además el enlace)"
                                                   → critica.referencia_bibliografica  ← CAMPO CRÍTICO
  "Descripción o resumen de la crítica"            → critica.descripcion_resumen

AGRUPACIÓN:
  "Nombre de la agrupación"                        → agrupacion.nombre
  "Lugar de encuentros (ciudad, municipio)"        → agrupacion.lugar_encuentros
  "Fecha de inicio"                                → agrupacion.fecha_inicio
  "Fecha de culminación"                           → agrupacion.fecha_culminacion
  "Característica general de la agrupación (tendencia, ideología)"
                                                   → agrupacion.caracteristica_general  ← CAMPO CRÍTICO
  "Integrantes (Nombres y Apellidos)"              → agrupacion.integrantes
  "Publicaciones de la agrupación (Título, año, resumen de la obra)"
                                                   → agrupacion.publicaciones
  "Actividades de la agrupación"                   → agrupacion.actividades

REVISTA:
  "Título"                                         → revista.titulo
  "Fecha de primer número"                         → revista.fecha_primer_numero
  "Fecha de último número"                         → revista.fecha_ultimo_numero
  "Números publicados"                             → revista.numeros_publicados
  "Lugar de publicación (ciudad, imprenta, editorial)"
                                                   → revista.lugar_publicacion / revista.editorial
  "Creadores (director, comité editorial, etc.)"   → revista.creadores
  "Secciones de la revista"                        → revista.secciones
  "Descripción (temas y géneros predominantes, autores relevantes)"
                                                   → revista.descripcion
  "Idioma original"                                → revista.idioma_original

ANTOLOGÍA:
  "Autor"  [en sección Antología]                  → antologia.autor  (compilador/editor)
  "Título" [en sección Antología]                  → antologia.titulo
  "Género (novela, cuento, poesía, ensayo)"        → antologia.genero
  "Fecha de publicación"                           → antologia.fecha_publicacion
  "Lugar de publicación (ciudad, imprenta, editorial)"
                                                   → antologia.lugar_publicacion / antologia.editorial
  "Descripción o resumen (mencionar autores seleccionados)"
                                                   → antologia.descripcion
  "Idioma original"                                → antologia.idioma_original
"""


def get_prompt_mapping_block() -> str:
    """Devuelve el bloque de texto listo para insertar en el system-prompt del LLM."""
    return MAPPING_PROMPT_BLOCK.strip()
