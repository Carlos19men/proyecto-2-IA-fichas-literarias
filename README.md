# 📚 GraphRAG Literario: Motor de Búsqueda y Memoria Contextual

Este repositorio contiene un sistema avanzado de **GraphRAG (Retrieval-Augmented Generation basado en Grafos)** diseñado específicamente para la extracción, estructuración y consulta de fichas técnico-literarias e históricas. 

El sistema permite procesar textos biográficos y críticos complejos, transformarlos en un modelo de datos estructurado e interconectado (Grafo), y habilitar una interfaz de chat inteligente que comprende lenguaje natural y comandos de voz (Audio) para realizar consultas precisas sobre autores, seudónimos, obras y contextos.

---

## 🏗️ Arquitectura del Sistema

El proyecto está construido sobre una arquitectura modular de tres capas totalmente locales:

1. **Capa de Almacenamiento (Base de Datos de Grafos):** Una instancia de **Neo4j** corriendo de manera aislada dentro de un contenedor de **Docker**. Mantiene de forma persistente e interconectada los nodos (Autor, Obra, Crítica) y sus relaciones.
2. **Capa Lógica y Orquestación (Backend Python):** Desarrollada con **LangChain** y **Pydantic**. Gobierna la ingesta de datos, la validación de esquemas, la inyección de la memoria histórica conversacional y la traducción de lenguaje natural a consultas estructuradas en código Cypher.
3. **Capa de Inteligencia y Frontend (LLM e Interfaz):** Ejecutada localmente mediante **Ollama** (Llama 3 para razonamiento y Nomic-Embed-Text para vectores) combinada con una interfaz web dinámica en **Chainlit** que incluye soporte Speech-to-Text mediante **Faster-Whisper** para procesar notas de voz.

---

## 📂 Estructura del Repositorio

```text
├── .env.example             # Plantilla de variables de entorno (no subir .env real)
├── .gitignore               # Exclusiones de Git (archivos temporales, venv, .env)
├── Dockerfile               # Receta de Docker para la aplicación web (Opcional)
├── docker-compose.yml       # Orquestador del contenedor Neo4j y la App
├── requirements.txt         # Dependencias del proyecto
├── app_visual.py            # Servidor e interfaz gráfica de usuario (Chainlit)
├── data/
│   └── neo4j_data/          # Volumen persistente para los datos del grafo (ignorado por Git)
└── src/
    ├── __init__.py
    ├── config.py            # Lector centralizado de variables de entorno
    ├── app/
    │   ├── __init__.py
    │   └── main.py          # Lógica del Chat por Consola y memoria contextual
    ├── extractor/
    │   ├── __init__.py
    │   ├── schemas.py       # Moldes estrictos de datos (Pydantic)
    │   └── pipeline.py      # Extractor de texto no estructurado usando el LLM
    └── rag/
        ├── __init__.py
        └── chain.py         # Motor de traducción Texto-a-Cypher con reglas personalizadas