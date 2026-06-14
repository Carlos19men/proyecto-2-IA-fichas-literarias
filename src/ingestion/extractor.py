from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from src.config import Config
from src.ingestion.schemas import FichaLiterariaSchema

def extraer_json_de_ficha(texto_ficha: str) -> FichaLiterariaSchema:

    """
    Envía el texto crudo a Ollama y fuerza una respuesta estructurada en JSON.
    
    Extrae información completa incluyendo:
    - Datos biográficos del autor (nombres, apellidos, fechas, lugares desglosados)
    - Multimedia (imágenes, audio, videos)
    - Relaciones (obras, críticas, agrupaciones, revistas, antologías, mitos/leyendas)
    """

    # 1. Configurar el modelo (Temperatura 0 para evitar alucinaciones)
    llm = ChatOllama(
        base_url=Config.OLLAMA_BASE_URL,
        model=Config.OLLAMA_MODEL,
        temperature=0 
    )

    # 2. Obligar al modelo a usar el esquema de Pydantic
    llm_estructurado = llm.with_structured_output(FichaLiterariaSchema)

    # 3. Crear el Prompt (Instrucciones claras para la IA)
    prompt = ChatPromptTemplate.from_messages([
        ("system", """Eres un experto analista literario e historiador cultural. 
Tu tarea es extraer información del texto y estructurarla exactamente como se te pide.

REGLAS:
- Nombres y apellidos: Separa en campos nombres y apellidos (no nombres_completos)
- Lugares: Desglosar en ciudad, municipio, estado, pais (cada uno Optional)
- Fechas: Formato YYYY o YYYY-MM-DD; usar None si no aparece
- Multimedia: Incluir enlace, tipo (imagen|audio|video|pdf), restriccion (público|privado|restringido)
- Listas vacías: Si no hay críticas/obras/agrupaciones/etc, devolver []
- No inventar: No alucines datos no mencionados
- Campos opcionales: Solo rellenar si están en el texto"""),
        ("human", "Extrae la información de esta ficha literaria:\n\n{texto}")
    ]) 

    # 4. Unir el prompt y el modelo en una "Cadena" (Chain) y ejecutar
    cadena = prompt | llm_estructurado
    resultado = cadena.invoke({"texto": texto_ficha})

    return resultado


