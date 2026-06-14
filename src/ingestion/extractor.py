from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from src.config import Config
from src.ingestion.schemas import FichaLiterariaSchema

def extraer_json_de_ficha(texto_ficha: str) -> FichaLiterariaSchema:
    """
    Envía el texto crudo a Ollama y fuerza una respuesta estructurada en JSON
    siguiendo el esquema detallado y reestructurado de FichaLiterariaSchema.
    """

    # 1. Configurar el modelo (Temperatura 0 para evitar alucinaciones y asegurar consistencia)
    llm = ChatOllama(
        base_url=Config.OLLAMA_BASE_URL,
        model=Config.OLLAMA_MODEL,
        temperature=0 
    )

    # 2. Obligar al modelo a usar el esquema detallado de Pydantic
    llm_estructurado = llm.with_structured_output(FichaLiterariaSchema)

    # 3. Crear el Prompt con instrucciones claras sobre la nueva estructura
    system_instruction = (
        "Eres un analista literario experto de alto nivel. Tu única tarea es extraer "
        "información del texto proporcionado y estructurarla de manera precisa en el formato JSON "
        "solicitado.\n\n"
        "Sigue estas pautas estrictamente:\n"
        "1. **Autor**:\n"
        "   - Separa obligatoriamente el nombre del autor en 'nombres' y 'apellidos'.\n"
        "   - Completa su 'sexo', 'seudonimo' y 'contextoEnQueVivio'.\n"
        "   - Cronología y Ubicación: desglosa fechas y extrae los lugares detallando (ciudad, municipio, estado, país) dentro del objeto de ubicación.\n"
        "   - Trayectoria: extrae actividades relevantes (estudios, cargos, profesión, lugar y período) y familiares destacados en su respectivo listado estructurado.\n"
        "   - Multimedia: identifica referencias a retratos o imágenes (.jpg) del autor, archivos de voz (.mp3) u otros recursos multimedia (enlace, tipo, restriccion).\n"
        "2. **Obras**:\n"
        "   - Lista todas las obras individuales del autor.\n"
        "   - Indica título, género (novela, cuento, poesía, ensayo, etc.), fecha y lugar de publicación.\n"
        "   - Extrae referencias a archivos asociados como PDF de descarga, portadas en JPG o archivos MP3 de audio-lectura si se mencionan.\n"
        "3. **Críticas**:\n"
        "   - Extrae el tipo de crítica, autor, título, fecha, la referencia bibliográfica completa (dónde se publicó) e incluye el enlace o URL si está disponible.\n"
        "4. **Agrupaciones, Revistas y Antologías**:\n"
        "   - Clasifícalas y extráelas en sus respectivas listas dedicadas ('agrupaciones', 'revistas', 'antologias').\n"
        "   - Asegúrate de rellenar los campos específicos de cada tipo, por ejemplo, integrantes y publicaciones para agrupaciones, creadores y secciones para revistas, compilador/autor para antologías.\n"
        "5. **Mitos y Leyendas**:\n"
        "   - Extrae el título, la comunidad creadora, lugar de difusión (estructurado como objeto de ubicación), idioma original, texto completo de la narración, tema y cualquier recurso multimedia asociado.\n\n"
        "Reglas generales de extracción:\n"
        "- Si una sección, listado o campo específico no se encuentra mencionado en el texto, devuélvelo como vacío o null.\n"
        "- No inventes ni alucines información que no aparezca explícitamente en el texto.\n"
        "- Sé sumamente riguroso con la fidelidad de los datos históricos y nombres propios."
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_instruction),
        ("human", "Extrae la información de esta ficha literaria:\n\n{texto}")
    ]) 

    # 4. Unir el prompt y el modelo en una cadena de ejecución (Chain) y ejecutar
    cadena = prompt | llm_estructurado
    resultado = chain_output = cadena.invoke({"texto": texto_ficha})

    return resultado
