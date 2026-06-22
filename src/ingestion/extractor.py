"""
extractor.py — Extrae datos estructurados de una ficha literaria (Word → Pydantic).

Mejoras respecto a la versión original:
  - Se inyecta `MAPPING_PROMPT_BLOCK` de field_mapping.py en el system-prompt.
  - El LLM recibe una tabla explícita Word-etiqueta → campo Python, eliminando
    ambigüedades en campos críticos (actividad_relevante, tematica_principal,
    audio_voz, imagen_autor, referencia_bibliografica, caracteristica_general).
  - Se añade un segundo nivel de instrucciones para campos compuestos
    (Lugar, Multimedia, listas de Persona).
"""

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from src.config import Config
from src.ingestion.schemas import FichaLiterariaSchema
from src.ingestion.field_mapping import get_prompt_mapping_block


def extraer_json_de_ficha(texto_ficha: str) -> FichaLiterariaSchema:
    """
    Envía el texto crudo a Ollama y fuerza una respuesta estructurada en JSON.

    Extrae información completa incluyendo:
    - Datos biográficos del autor (nombres, apellidos, fechas, lugares desglosados)
    - Multimedia (imágenes, audio, videos)
    - Relaciones (obras, críticas, agrupaciones, revistas, antologías, mitos/leyendas)

    El sistema-prompt incluye el mapeo semántico completo (field_mapping.py) para
    que el LLM traduzca correctamente los campos del Word al schema de Pydantic,
    incluso cuando los nombres difieren significativamente.
    """

    # 1. Configurar el modelo (Temperatura 0 para evitar alucinaciones)
    llm = ChatOllama(
        base_url=Config.OLLAMA_BASE_URL,
        model=Config.OLLAMA_MODEL,
        temperature=0
    )

    # 2. Obligar al modelo a usar el esquema de Pydantic
    llm_estructurado = llm.with_structured_output(FichaLiterariaSchema)

    # 3. Obtener el bloque de mapeo semántico Word → schema
    mapping_block = get_prompt_mapping_block()

    # 4. Crear el Prompt con el mapeo inyectado en el system-prompt
    system_prompt = f"""Eres un experto analista literario e historiador cultural.
Tu tarea es extraer información del texto y estructurarla exactamente como se te pide.

{mapping_block}

REGLAS GENERALES:
- Nombres y apellidos: Separa en campos `nombres` y `apellidos` (NO uses nombre_completo para rellenar)
- Lugares: Desglosa en ciudad, municipio, estado, pais (cada uno Optional). Si el texto solo da ciudad, pon ciudad y deja el resto en null
- Fechas: Formato YYYY o YYYY-MM-DD; usar null si no aparece en el texto
- Multimedia: Incluir enlace (URL o ruta), tipo (imagen|audio|video|pdf), restriccion (público|privado|restringido)
- Listas vacías: Si no hay críticas/obras/agrupaciones/etc, devolver []
- NO inventar datos: No alucines valores que no estén en el texto
- Campos opcionales: Solo rellenar si el dato aparece explícitamente en el texto
- Sección activa: Identifica si el texto describe un Autor, Obra, Crítica, Agrupación, Revista, Antología o Mito/Leyenda

INSTRUCCIONES ESPECIALES para campos críticos:
- `autor.actividad_relevante`: Extrae TODO el texto que describe estudios, cargos públicos, profesiones, lugares y periodos del autor
- `autor.tematica_principal`: Extrae los temas literarios centrales de su obra (ej: identidad, historia, violencia)
- `autor.imagen_autor`: Extrae la ruta o URL del archivo .jpg de la foto del autor
- `autor.audio_voz`: Extrae la ruta o URL del archivo .mp3 de la voz del autor
- `critica.referencia_bibliografica`: Extrae el LUGAR DE PUBLICACIÓN de la crítica (editorial, revista, URL donde apareció)
- `critica.autor`: Es el CRÍTICO o investigador que escribió la reseña, NO el autor literario del que se habla
- `agrupacion.caracteristica_general`: Extrae la tendencia literaria, ideología o características generales del grupo
- `autor.familiares_destacados`: Lista de familiares; cada uno con nombres, apellidos y rol (padre, madre, hijo/a, hermano/a, etc.)
- `agrupacion.integrantes`: Lista de miembros; cada uno con nombres, apellidos y rol (fundador, integrante, etc.)
- `revista.creadores`: Lista de personas; cada uno con nombres, apellidos y rol (director, editor, etc.)"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Extrae la información de esta ficha literaria:\n\n{texto}")
    ])

    # 5. Unir el prompt y el modelo en una cadena (Chain) y ejecutar
    cadena = prompt | llm_estructurado
    resultado = cadena.invoke({"texto": texto_ficha})

    return resultado
