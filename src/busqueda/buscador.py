"""
Motor de búsqueda híbrida GraphRAG para LetraScopio.

Combina búsqueda vectorial (semántica) y full-text (palabras clave)
en Neo4j para encontrar autores, obras, críticas y entidades literarias.
Usa LangChain + Ollama para generar embeddings de consulta y
sintetizar respuestas en lenguaje natural.
"""

import logging
import os
import urllib.request
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Any, Dict, List, Optional

from src.database.connection import db
from src.config import Config
from src.busqueda.enriquecimiento import enriquecer_autor, enriquecer_obra
from src.busqueda.formateador import formatear_contexto, construir_metadata_autor

try:
    # pyrefly: ignore [missing-import]
    from langchain_ollama import OllamaEmbeddings, ChatOllama
    from langchain_core.prompts import ChatPromptTemplate
except ImportError:
    OllamaEmbeddings = None
    ChatOllama = None
    ChatPromptTemplate = None

# Timeout en segundos para comprobar si Ollama está disponible
_OLLAMA_PROBE_TIMEOUT = 3
# Timeout máximo para generar embedding o sintetizar con LLM
_OLLAMA_REQUEST_TIMEOUT = 180
# Timeout duro (ThreadPoolExecutor) para el paso de síntesis LLM
_LLM_HARD_TIMEOUT = 300


def _ollama_disponible() -> bool:
    """Comprueba en ≤3 s si Ollama está escuchando."""
    try:
        url = f"{Config.OLLAMA_BASE_URL.rstrip('/')}/api/tags"
        req = urllib.request.urlopen(url, timeout=_OLLAMA_PROBE_TIMEOUT)  # noqa: S310
        return req.status == 200
    except Exception:
        return False

logger = logging.getLogger(__name__)

# ─── Configuración de índices ─────────────────────────────────────
# Definidos como constantes para facilitar mantenimiento y evitar
# repeticiones de strings mágicos en el código.

INDICES_FULLTEXT = [
    ("fulltext_autor_names", "Autor"),
    ("fulltext_obra_titles", "Obra"),
    ("fulltext_critica_titles", "Critica"),
    ("fulltext_revista_names", "Revista"),
    ("fulltext_antologia_titles", "Antologia"),
    ("fulltext_agrupacion_names", "Agrupacion"),
    ("fulltext_mitleyenda_titles", "MitoLeyenda"),
]

INDICES_VECTORIALES = [
    ("index_autores_vector", "Autor"),
    ("index_obras_vector", "Obra"),
    ("index_criticas_vector", "Critica"),
    ("index_multimedia_vector", "Multimedia"),
]

# Caracteres especiales de Lucene que deben escaparse
_LUCENE_ESPECIALES = set(r'+-&|!(){}[]^"~*?:\/')


def _escapar_lucene(texto: str) -> str:
    """Escapa caracteres especiales de Lucene en la consulta."""
    return "".join(f"\\{c}" if c in _LUCENE_ESPECIALES else c for c in texto)


class GraphRAGSearcher:
    """
    Realiza búsquedas híbridas (vectorial + full-text) en el grafo
    literario de Neo4j y genera respuestas enriquecidas.
    """

    def __init__(self):
        self.db = db
        self.embeddings: Optional[OllamaEmbeddings] = None
        self.llm: Optional[ChatOllama] = None
        self._conexion_verificada = False

        self._inicializar_embeddings()
        self._inicializar_llm()

    def _inicializar_embeddings(self) -> None:
        """Inicializa el generador de embeddings (Ollama)."""
        if not OllamaEmbeddings:
            logger.warning("langchain_ollama no está instalado; búsqueda vectorial deshabilitada.")
            return
        if not _ollama_disponible():
            logger.warning("Ollama no está disponible en %s; búsqueda vectorial deshabilitada.", Config.OLLAMA_BASE_URL)
            return
        try:
            modelo = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
            # request_timeout no está soportado en todas las versiones de langchain_ollama;
            # se omite para máxima compatibilidad.
            self.embeddings = OllamaEmbeddings(
                model=modelo,
                base_url=Config.OLLAMA_BASE_URL,
            )
            logger.info("Embeddings conectados: %s en %s", modelo, Config.OLLAMA_BASE_URL)
        except Exception as e:
            logger.error("No se pudo inicializar OllamaEmbeddings: %s", e)

    def _inicializar_llm(self) -> None:
        """Inicializa el modelo de chat para síntesis de respuestas."""
        if not ChatOllama:
            logger.warning("langchain_ollama no está instalado; síntesis LLM deshabilitada.")
            return
        if not _ollama_disponible():
            logger.warning("Ollama no está disponible en %s; síntesis LLM deshabilitada.", Config.OLLAMA_BASE_URL)
            return
        try:
            self.llm = ChatOllama(
                base_url=Config.OLLAMA_BASE_URL,
                model=Config.OLLAMA_MODEL,
                temperature=0,
            )
            logger.info("LLM conectado: %s en %s", Config.OLLAMA_MODEL, Config.OLLAMA_BASE_URL)
        except Exception as e:
            logger.error("No se pudo inicializar ChatOllama: %s", e)

    # ─── Verificación de conexión ─────────────────────────────────

    def _verificar_conexion(self) -> bool:
        """
        Verifica la conexión a Neo4j solo una vez (o tras un fallo previo).
        Evita llamar test_connection() en cada request.
        """
        if self._conexion_verificada:
            return True
        if self.db.test_connection():
            self._conexion_verificada = True
            return True
        return False

    # ─── Búsqueda full-text ───────────────────────────────────────

    def _buscar_fulltext(self, session, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Busca en los índices full-text de Neo4j.
        Retorna nodos que coincidan con la consulta por nombre, título, etc.
        """
        query_escaped = _escapar_lucene(query)
        if not query_escaped.strip():
            return []

        resultados = []

        for index_name, label in INDICES_FULLTEXT:
            try:
                cypher = """
                CALL db.index.fulltext.queryNodes($indexName, $texto_buscar)
                YIELD node, score
                RETURN node, score, labels(node) AS labels
                ORDER BY score DESC
                LIMIT $limit
                """
                records = session.run(
                    cypher,
                    indexName=index_name,
                    texto_buscar=query_escaped,
                    limit=limit,
                )
                for record in records:
                    nodo = dict(record["node"])
                    nodo.pop("embedding", None)
                    resultados.append({
                        "nodo": nodo,
                        "tipo": label,
                        "score": record["score"],
                        "fuente": "fulltext",
                    })
            except Exception as e:
                logger.warning("Error en fulltext %s: %s", index_name, e)

        return resultados

    # ─── Búsqueda vectorial ───────────────────────────────────────

    def _buscar_vectorial(self, session, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Genera el embedding de la consulta del usuario y busca
        los nodos más similares en los índices vectoriales de Neo4j.
        """
        if not self.embeddings:
            return []

        try:
            executor = ThreadPoolExecutor(max_workers=1)
            future = executor.submit(self.embeddings.embed_query, query)
            try:
                query_embedding = future.result(timeout=_OLLAMA_REQUEST_TIMEOUT)
            finally:
                executor.shutdown(wait=False)
        except FuturesTimeoutError:
            logger.warning("Generación de embedding superó %ds; omitiendo búsqueda vectorial.", _OLLAMA_REQUEST_TIMEOUT)
            return []
        except Exception as e:
            logger.error("Error al generar embedding de consulta: %s", e)
            return []

        resultados = []

        for index_name, label in INDICES_VECTORIALES:
            try:
                cypher = """
                CALL db.index.vector.queryNodes($indexName, $limit, $embedding)
                YIELD node, score
                RETURN node, score, labels(node) AS labels
                """
                records = session.run(
                    cypher,
                    indexName=index_name,
                    limit=limit,
                    embedding=query_embedding,
                )
                for record in records:
                    nodo = dict(record["node"])
                    nodo.pop("embedding", None)
                    resultados.append({
                        "nodo": nodo,
                        "tipo": label,
                        "score": record["score"],
                        "fuente": "vectorial",
                    })
            except Exception as e:
                logger.warning("Error en vector %s: %s", index_name, e)

        return resultados

    # ─── Síntesis LLM ────────────────────────────────────────────

    def _sintetizar_respuesta(self, query: str, contexto: str, history: Optional[List[Dict]] = None) -> str:
        """
        Usa el LLM (Ollama) para generar una respuesta en lenguaje
        natural a partir del contexto recuperado del grafo.
        """
        if not self.llm or not ChatPromptTemplate:
            return contexto

        historial_texto = ""
        if history:
            for msg in history[-6:]:
                role = "Usuario" if msg.get("role") == "user" else "Asistente"
                historial_texto += f"{role}: {msg.get('content', '')}\n"

        prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres LetraScopio, un agente experto en literatura venezolana, 
especialmente del Estado Bolívar. Respondes preguntas sobre autores, obras, 
corrientes literarias, revistas, agrupaciones y mitos/leyendas de la región.

REGLAS:
- Responde en español, de forma clara y cálida.
- Usa la información del contexto proporcionado como base principal.
- Si el contexto contiene datos de un autor (nombre, fechas, lugar, género), SIEMPRE preséntalo aunque sea brevemente.
- Solo di que "no tienes información" si el contexto está completamente vacío o no contiene ningún dato del tema preguntado.
- Si el contexto tiene datos parciales (por ejemplo, nombre y fechas pero sin obras), preséntalo y menciona que los detalles adicionales (obras, críticas) aún no están disponibles en la base de datos.
- Menciona nombres completos, fechas y lugares cuando estén disponibles en el contexto.
- No repitas la pregunta del usuario en tu respuesta.
- Sé conciso pero informativo (2-4 párrafos máximo)."""),
            ("human", """Historial de conversación:
{historial}

Contexto recuperado del grafo literario:
{contexto}

Pregunta del usuario: {query}"""),
        ])

        try:
            cadena = prompt | self.llm

            def _invocar():
                return cadena.invoke({
                    "historial": historial_texto or "Sin historial previo.",
                    "contexto": contexto,
                    "query": query,
                }).content

            executor = ThreadPoolExecutor(max_workers=1)
            future = executor.submit(_invocar)
            try:
                return future.result(timeout=_LLM_HARD_TIMEOUT)
            except FuturesTimeoutError:
                logger.warning("Síntesis LLM superó %ds; devolviendo contexto directo.", _LLM_HARD_TIMEOUT)
                return contexto
            finally:
                executor.shutdown(wait=False)
        except Exception as e:
            logger.error("Error al sintetizar respuesta: %s", e)
            return contexto

    # ─── Preguntas relacionadas ───────────────────────────────────

    @staticmethod
    def _generar_preguntas_relacionadas(datos: dict) -> List[str]:
        """Genera preguntas de seguimiento basadas en los datos encontrados."""
        preguntas = []
        autor = datos.get("autor") or {}
        nombre = f"{autor.get('nombres', '')} {autor.get('apellidos', '')}".strip()

        if nombre:
            preguntas.append(f"¿Qué obras escribió {nombre}?")
            if datos.get("agrupaciones"):
                ag = datos["agrupaciones"][0]
                preguntas.append(f"¿Qué fue {ag.get('nombre', 'su agrupación literaria')}?")
            if datos.get("criticas"):
                preguntas.append(f"¿Qué críticas existen sobre {nombre}?")
            if datos.get("mitos"):
                mito = datos["mitos"][0]
                preguntas.append(f'¿De qué trata "{mito.get("titulo", "el mito")}"?')

        if not preguntas:
            preguntas = [
                "¿Qué autores hay del Estado Bolívar?",
                "¿Qué es la literatura guayanesa?",
                "¿Qué agrupaciones literarias existen?",
            ]

        return preguntas[:3]

    # ─── Punto de entrada principal ───────────────────────────────

    def buscar(self, query: str, history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Punto de entrada principal. Recibe la consulta del usuario,
        ejecuta búsqueda híbrida y devuelve un JSON listo para el front-end.

        Returns:
            {
                "respuesta_texto": "...",
                "metadata": { ... } | None,
                "relatedQuestions": ["...", "..."]
            }
        """
        if not self._verificar_conexion():
            return {
                "respuesta_texto": "No se pudo conectar a la base de datos Neo4j. Verifica que Docker esté corriendo.",
                "metadata": None,
                "relatedQuestions": [],
            }

        with self.db.driver.session() as session:
            # 1. Ejecutar ambas búsquedas (secuenciales por limitación de driver síncrono)
            print("-> Paso 1: Buscando coincidencias exactas (Full-Text)...")
            resultados_ft = self._buscar_fulltext(session, query, limit=5)
            print("-> Paso 2: Generando Embedding y buscando similitudes (Vectorial)...")
            resultados_vec = self._buscar_vectorial(session, query, limit=5)

            # 2. Combinar y deduplicar resultados por fichaId
            todos = resultados_ft + resultados_vec
            vistos: set = set()
            unicos: List[Dict] = []
            for r in sorted(todos, key=lambda x: x["score"], reverse=True):
                fid = r["nodo"].get("fichaId")
                if fid is None:
                    # Nodos sin fichaId siempre se incluyen (no deduplicables)
                    unicos.append(r)
                elif fid not in vistos:
                    vistos.add(fid)
                    unicos.append(r)

            if not unicos:
                return {
                    "respuesta_texto": "No encontré información sobre ese tema en la base de datos. "
                                       "Intenta con otro autor, obra o tema literario del Estado Bolívar.",
                    "metadata": None,
                    "relatedQuestions": [
                        "¿Qué autores hay del Estado Bolívar?",
                        "¿Qué es el grupo literario Guayana?",
                    ],
                }

            # 3. Tomar el resultado principal (mayor score)
            principal = unicos[0]
            tipo_principal = principal["tipo"]
            nodo_principal = principal["nodo"]

            # 4. Enriquecer según el tipo de nodo
            print("-> Paso 3: Enriqueciendo la información encontrada...")
            datos_enriquecidos = self._enriquecer_por_tipo(session, tipo_principal, nodo_principal)
            metadata = construir_metadata_autor(datos_enriquecidos)

            # 5. Formatear contexto y sintetizar respuesta
            contexto = formatear_contexto(datos_enriquecidos)
            print("-> Paso 4: Redactando respuesta con Inteligencia Artificial (por favor espera)...")
            respuesta_texto = self._sintetizar_respuesta(query, contexto, history)

            # 6. Generar preguntas relacionadas
            preguntas = self._generar_preguntas_relacionadas(datos_enriquecidos)
            
            print("-> Paso 5: ¡Proceso finalizado! Enviando resultados al cliente.")

            return {
                "respuesta_texto": respuesta_texto,
                "metadata": metadata,
                "relatedQuestions": preguntas,
            }

    def _enriquecer_por_tipo(self, session, tipo: str, nodo: dict) -> dict:
        """Despacha el enriquecimiento según el tipo de nodo encontrado."""
        if tipo == "Autor":
            return enriquecer_autor(session, nodo)

        elif tipo == "Obra":
            datos_obra = enriquecer_obra(session, nodo)
            if datos_obra.get("autor"):
                return enriquecer_autor(session, datos_obra["autor"])
            return {"obra": nodo, "obras": [nodo]}

        elif tipo == "Critica":
            return self._enriquecer_desde_critica(session, nodo)

        elif tipo == "Agrupacion":
            return {"agrupaciones": [nodo]}
            
        elif tipo == "MitoLeyenda":
            return {"mitos": [nodo]}
            
        elif tipo == "Multimedia":
            return self._enriquecer_desde_multimedia(session, nodo)

        else:
            # Revista, Antologia, etc.
            return {tipo.lower(): [nodo]}

    def _enriquecer_desde_critica(self, session, nodo_critica: dict) -> dict:
        """Busca el autor relacionado a la crítica y enriquece desde él."""
        try:
            records = session.run(
                """
                MATCH (c:Critica {fichaId: $fichaId})-[:CRITICA_DE]->(a:Autor)
                RETURN a LIMIT 1
                """,
                fichaId=nodo_critica.get("fichaId"),
            )
            record = records.single()
            if record:
                autor_nodo = dict(record["a"])
                autor_nodo.pop("embedding", None)
                return enriquecer_autor(session, autor_nodo)
        except Exception as e:
            logger.warning("Error al enriquecer desde crítica: %s", e)

        return {"criticas": [nodo_critica]}

    def _enriquecer_desde_multimedia(self, session, nodo_multimedia: dict) -> dict:
        """Busca el autor u obra relacionado al nodo multimedia y enriquece desde ahí."""
        try:
            records = session.run(
                """
                MATCH (m:Multimedia {fichaId: $fichaId})-[:ASOCIADA_A]->(a:Autor)
                RETURN a LIMIT 1
                """,
                fichaId=nodo_multimedia.get("fichaId"),
            )
            record = records.single()
            if record:
                autor_nodo = dict(record["a"])
                autor_nodo.pop("embedding", None)
                return enriquecer_autor(session, autor_nodo)
        except Exception as e:
            logger.warning("Error al enriquecer desde multimedia: %s", e)

        return {"multimedia": [nodo_multimedia]}
