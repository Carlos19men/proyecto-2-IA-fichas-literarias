"""
API REST de LetraScopio — Backend FastAPI.

Expone el endpoint POST /api/chat para que el front-end en Next.js
envíe la pregunta del usuario y reciba la respuesta enriquecida
con datos del grafo literario en Neo4j.
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from src.busqueda.buscador import GraphRAGSearcher

logger = logging.getLogger(__name__)

# ─── Aplicación FastAPI ───────────────────────────────────────────

app = FastAPI(
    title="LetraScopio API",
    description="API del motor de búsqueda GraphRAG para literatura venezolana",
    version="0.1.0",
)

# Habilitar CORS para permitir peticiones desde el front-end Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instancia global del buscador (se inicializa una sola vez al arrancar)
searcher = GraphRAGSearcher()


# ─── Modelos de Request / Response ────────────────────────────────

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    query: str
    history: List[ChatMessage] = []

class ChatMetadata(BaseModel):
    nombre: str
    disciplina: str
    periodo: str
    lugar: str
    imagenes: Optional[List[str]] = None
    audios: Optional[List[str]] = None
    pdfs: Optional[List[str]] = None

class ChatResponse(BaseModel):
    respuesta_texto: str
    metadata: Optional[ChatMetadata] = None
    relatedQuestions: List[str] = []


# ─── Endpoints ────────────────────────────────────────────────────

@app.get("/")
def root():
    """Health check — verifica que el servidor está vivo."""
    return {"status": "ok", "service": "LetraScopio API", "version": "0.1.0"}


@app.get("/api/debug")
def debug_search(q: str = "Ramon Isidro"):
    """
    Endpoint de diagnóstico: ejecuta la búsqueda paso a paso y muestra
    qué encuentra en cada etapa (fulltext, vectorial, enriquecimiento).
    """
    import logging
    from src.database.connection import db

    log = []
    log.append(f"Query recibida: '{q}'")

    # 1. Conexión
    ok = db.test_connection()
    log.append(f"Conexión Neo4j: {'OK' if ok else 'FALLO'}")
    if not ok:
        return {"log": log, "error": "Sin conexión Neo4j"}

    from src.busqueda.buscador import _escapar_lucene, INDICES_FULLTEXT

    q_escaped = _escapar_lucene(q)
    log.append(f"Query escapada: '{q_escaped}'")

    resultados_ft = []
    with db.driver.session() as session:
        # 2. Test fulltext por cada índice
        for index_name, label in INDICES_FULLTEXT:
            try:
                records = session.run(
                    """
                    CALL db.index.fulltext.queryNodes($indexName, $texto)
                    YIELD node, score
                    RETURN node, score
                    LIMIT 3
                    """,
                    indexName=index_name,
                    texto=q_escaped,
                )
                rows = list(records)
                if rows:
                    for r in rows:
                        nodo = dict(r["node"])
                        nodo.pop("embedding", None)
                        resultados_ft.append({
                            "indice": index_name,
                            "label": label,
                            "score": r["score"],
                            "nodo": nodo,
                        })
                    log.append(f"  Índice {index_name} ({label}): {len(rows)} resultado(s)")
                else:
                    log.append(f"  Índice {index_name} ({label}): sin resultados")
            except Exception as e:
                log.append(f"  Índice {index_name} ERROR: {e}")

        # 3. Contar nodos Autor
        try:
            total = session.run("MATCH (a:Autor) RETURN count(a) AS total").single()
            log.append(f"Total nodos Autor en BD: {total['total'] if total else '?'}")
        except Exception as e:
            log.append(f"Error contando autores: {e}")

    return {
        "log": log,
        "resultados_fulltext": resultados_ft,
        "total_encontrados": len(resultados_ft),
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Endpoint principal del chat. Recibe la consulta del usuario
    y opcionalmente el historial de mensajes previos.
    """
    history_dicts = [{"role": m.role, "content": m.content} for m in request.history]

    resultado = searcher.buscar(
        query=request.query,
        history=history_dicts,
    )

    return ChatResponse(
        respuesta_texto=resultado["respuesta_texto"],
        metadata=ChatMetadata(**resultado["metadata"]) if resultado.get("metadata") else None,
        relatedQuestions=resultado.get("relatedQuestions", []),
    )
