from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_community.graphs import Neo4jGraph
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from src.config import Config
import warnings
warnings.filterwarnings('ignore')

def configurar_cadena_rag():
    """
    Configura la cadena RAG completa que conecta:
    1. Base de datos de grafos Neo4j
    2. Modelo de embeddings para búsqueda semántica
    3. LLM para generación de respuestas
    4. Motor de traducción de preguntas naturales a Cypher
    """
    
    # 1. Conectar a la base de datos Neo4j
    try:
        graph = Neo4jGraph(
            url=Config.NEO4J_URI,
            username=Config.NEO4J_USERNAME,
            password=Config.NEO4J_PASSWORD
        )
        # Test de conexión
        graph.refresh_schema()
        print(f"✅ Conectado a Neo4j en {Config.NEO4J_URI}")
    except Exception as e:
        print(f"❌ Error conectando a Neo4j: {e}")
        print("Asegúrate de que Docker con Neo4j esté corriendo")
        raise
    
    # 2. Configurar embeddings (para búsqueda vectorial si es necesario)
    embeddings = OllamaEmbeddings(
        base_url=Config.OLLAMA_BASE_URL,
        model=getattr(Config, 'OLLAMA_EMBEDDING_MODEL', "nomic-embed-text")
    )
    
    # 3. Configurar el LLM principal
    llm = ChatOllama(
        base_url=Config.OLLAMA_BASE_URL,
        model=Config.OLLAMA_MODEL,
        temperature=0.1
    )
    
    # 4. Crear cadena de QA para grafos
    # Primero, definimos un prompt para traducir preguntas naturales a Cypher
    cypher_generation_prompt = ChatPromptTemplate.from_messages([
        ("system", """Eres un experto en traducir preguntas en lenguaje natural a consultas Cypher para Neo4j.
        Traduce la pregunta del usuario a una consulta Cypher basándote en el esquema del grafo.
        
        Esquema del grafo:
        {schema}
        
        Instrucciones:
        - Usa WHERE para filtrar cuando sea necesario, especialmente para búsquedas de texto parcial
        - Devuelve SOLO la consulta Cypher, sin explicaciones
        - Si no puedes traducir la pregunta, devuelve 'NO_QUERY'
        
        Ejemplos:
        Pregunta: ¿Qué autor escribía bajo el seudónimo de Isael?
        Cypher: MATCH (a:Autor {seudonimo: 'Isael'}) RETURN a.nombre AS nombre
        
        Pregunta: ¿Cuáles fueron las obras que publicó en 1883?
        Cypher: MATCH (a:Autor)-[:ESCRIBIO]->(o:Obra) WHERE o.anio_publicacion = 1883 RETURN o.titulo AS titulo
        
        Pregunta: ¿Hay algún artículo en Prodavinci sobre ella?
        Cypher: MATCH (c:Critica)-[:SOBRE]->(a:Autor) WHERE c.fuente CONTAINS 'Prodavinci' RETURN c.url AS url, c.titulo AS titulo"""),
        ("human", "{question}")
    ])
    
    # Cadena para generar Cypher
    cypher_chain = cypher_generation_prompt | llm
    
    # 5. Función para ejecutar la consulta Cypher y obtener resultados
    def ejecutar_cypher_query(query: str) -> str:
        if query == "NO_QUERY":
            return "No pude generar una consulta para esta pregunta."
        
        try:
            result = graph.query(query)
            return str(result)
        except Exception as e:
            return f"Error ejecutando consulta Cypher: {e}"
    
    # 6. Prompt para formatear la respuesta final
    respuesta_prompt = ChatPromptTemplate.from_messages([
        ("system", """Eres un asistente literario especializado en autores y obras.
        Usa la siguiente información del grafo Neo4j para responder la pregunta.
        Si la información no es suficiente, di que no tienes esa información.
        
        Información del grafo:
        {context}
        
        Responde de manera clara y concisa, citando la información del grafo."""),
        ("human", "{question}")
    ])
    
    # 7. Cadena completa
    full_chain = (
        {"question": RunnablePassthrough()}
        | {
            "context": lambda x: ejecutar_cypher_query(
                cypher_chain.invoke({
                    "schema": graph.get_schema(),
                    "question": x["question"]
                }).content
            ),
            "question": lambda x: x["question"]
        }
        | respuesta_prompt
        | llm
    )
    
    return full_chain