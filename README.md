# 📚 GraphRAG Literario: Motor de Búsqueda y Memoria Contextual
Este repositorio contiene un sistema avanzado de **GraphRAG (Retrieval-Augmented Generation basado en Grafos)** diseñado específicamente para la extracción, estructuración y consulta de fichas técnico-literarias e históricas del **Estado Bolívar, Venezuela**. 

El sistema permite procesar textos biográficos y críticos complejos de la región, transformarlos en un modelo de datos estructurado e interconectado (Grafo), y habilitar una interfaz de chat inteligente que comprende lenguaje natural y comandos de voz (Audio) para realizar consultas precisas sobre autores, seudónimos, obras y contextos históricos del sur del Orinoco.

---

## 🏗️ Arquitectura del Sistema

El proyecto está construido sobre una arquitectura modular de tres capas totalmente locales:

1. **Capa de Almacenamiento (Base de Datos Híbrida):** * **Neo4j (Docker):** Mantiene de forma persistente e interconectada los nodos (Autor, Obra, Crítica, Mitos) y sus relaciones conceptuales.
   * **MongoDB (Docker):** Almacena los documentos en formato JSON crudo extraídos directamente de las fichas para auditoría e historial editorial.
2. **Capa Lógica y Orquestación (Backend Python):** Desarrollada con **LangChain** y **Pydantic**. Gobierna la ingesta de datos, la validación estricta de esquemas y moldes literarios, la inyección de la memoria histórica conversacional y la traducción de lenguaje natural a consultas estructuradas en código Cypher.
3. **Capa de Inteligencia y Frontend (LLM e Interfaz):** Ejecutada localmente mediante **Ollama** (*Qwen 2.5* o *Llama 3* para razonamiento y *Nomic-Embed-Text* para vectores de 768 dimensiones) combinada con una interfaz web dinámica en **Chainlit** que incluye soporte Speech-to-Text mediante **Faster-Whisper** para procesar notas de voz.

---

## 📂 Estructura del Repositorio

```text
├── .env.example              # Plantilla de variables de entorno (no subir .env real)
├── .gitignore                # Exclusiones de Git (archivos temporales, venv, .env)
├── Dockerfile                # Receta de Docker para la aplicación web (Opcional)
├── docker-compose.yml        # Orquestador de contenedores (Neo4j + MongoDB)
├── requirements.txt          # Dependencias y librerías del proyecto
├── app_visual.py             # Servidor e interfaz gráfica de usuario (Chainlit)
├── data/
│   └── neo4j_data/           # Volumen persistente para los datos del grafo (ignorado por Git)
└── src/
    ├── __init__.py
    ├── config.py             # Lector centralizado de variables de entorno
    ├── app/
    │   ├── __init__.py
    │   └── main.py           # Lógica del Chat por Consola y memoria contextual
    ├── database/
    │   ├── __init__.py
    │   ├── connection.py     # Inicializador del Driver oficial de Neo4j y validación de red
    │   ├── init_db.py        # Configuración de restricciones, índices fulltext y vectores
    │   └── ejemplo_insercion.py # Script de validación regional con datos del Estado Bolívar
    ├── extractor/
    │   ├── __init__.py
    │   ├── schemas.py        # Moldes estrictos de datos (Pydantic)
    │   └── pipeline.py       # Extractor de texto no estructurado usando el LLM estructurado
    └── rag/
        ├── __init__.py
        └── chain.py          # Motor de traducción Texto-a-Cypher con reglas personalizadas

```

---

## 🚀 Guía de Despliegue: Orden Cronológico de Ejecución

Sigue estos pasos en el orden exacto establecido para levantar los servicios, inyectar tus credenciales seguras, inicializar el esquema del grafo y conectarte visualmente a la base de datos.

### PASO 1: Configurar y Cargar las Credenciales (`.env`)

El sistema utiliza un archivo oculto `.env` para gestionar contraseñas localmente sin exponerlas en Git. El backend en Python (`config.py`) y Docker leerán este archivo automáticamente.

1. Abre tu terminal en la raíz del proyecto y duplica la plantilla de entorno:
```bash
cp .env.example .env

```


*(Si usas Windows PowerShell: `copy .env.example .env`)*
2. Abre el archivo `.env` recién creado en tu editor de código y define las credenciales del sistema:
```text
# Configuración de Neo4j (Base de datos de Grafos)
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=tu_contrasena_segura_aquí  # <-- Elige tu clave local

# Configuración de MongoDB (Base de datos de Documentos)
MONGO_URI=mongodb://admin:otra_contrasena_segura@localhost:27017/

# Configuración de Modelos (Ollama Local)
OLLAMA_BASE_URL=http://localhost:11434

```



### PASO 2: Levantar la Infraestructura en Docker

Con las credenciales listas en el paso anterior, le indicamos a Docker Compose que tome ese archivo de entorno para inicializar las bases de datos con los accesos correctos.

1. Construye y enciende los contenedores en segundo plano (*detached mode*):
```bash
docker compose --env-file .env up -d

```


2. Verifica que ambos motores (`neo4j_literario` y `letrascopio_mongo`) hayan encendido exitosamente:
```bash
docker ps

```



### PASO 3: Inicializar el Esquema del Grafo (Constraints e Índices)

Antes de insertar datos, debes indicarle a Python que prepare las reglas de la base de datos de grafos. Este comando crea las restricciones de unicidad y los índices vectoriales de **768 dimensiones**.

1. Con tu entorno virtual activo (`.venv`), ejecuta el inicializador estructurado como módulo:
```bash
python -m src.database.init_db

```



### PASO 4: Validar el Pipeline con Datos de Prueba (Estado Bolívar)

Inserta un árbol de conocimiento real del Estado Bolívar (vía Python) para comprobar la latencia, la comunicación y las credenciales entre el backend y Docker.

1. Ejecuta el script de siembra:
```bash
python -m src.database.ejemplo_insercion

```



---

## 🕵️‍♂️ Cómo Conectarse a Neo4j Browser (Inspección Visual)

Una vez completado el orden de ejecución anterior, puedes abrir la consola de administración nativa de Neo4j en tu navegador web para ver los datos del Estado Bolívar interconectados en tiempo real.

1. Abre tu navegador web e ingresa a la siguiente dirección local:
```text
http://localhost:7474

```


2. La pantalla te solicitará el formulario de autenticación. Configura los campos utilizando **las mismas credenciales exactas** que definiste en el **PASO 1** de tu archivo `.env`:
* **Connection URL:** `bolt://localhost:7687`
* **Authentication type:** `Username / Password`
* **Username:** `neo4j`
* **Password:** *[La contraseña que escribiste en NEO4J_PASSWORD]*


3. Haz clic en el botón **Connect**.
4. **Tu primera consulta:** En la barra de comandos Cypher ubicada en la parte superior del navegador (marcada con un símbolo `>`), pega la siguiente línea y presiona `Ctrl + Enter` o haz clic en el botón azul de `Play`:
```cypher
MATCH (n) RETURN n LIMIT 25

```



Aparecerán esferas interconectadas flotando en la pantalla que representan al grupo lírico guayanés, las obras de la autora *Jean Aristeguieta* y la leyenda de la *Serpiente de Siete Cabezas*.

---

## 🛠️ Comandos de Mantenimiento de Docker

Si necesitas pausar el desarrollo o limpiar tu entorno, utiliza estos comandos en la raíz del proyecto:

* **Detener los servicios (Liberar memoria RAM):** Apaga los contenedores de forma segura sin perder los datos guardados en tus grafos:
```bash
docker compose down

```


* **Reiniciar el entorno desde cero:** Si cambias alguna clave en tu `.env` y necesitas que Docker la aplique inmediatamente:
```bash
docker compose --env-file .env restart

```


## 🎓 Créditos y Referencias Académicas

Este proyecto se desarrolla tomando como base fundamental la investigación, el diseño conceptual y el marco metodológico del siguiente Trabajo de Grado:

### 1. Referencia Principal (Tesis de Grado)
* **Guevara Torres, Á. R., & Lorenzo Arias, C. A.** (2024). *Diccionario de la Literatura del Estado Bolívar Basado en Procesamiento de Lenguaje Natural* [Trabajo de Grado de Licenciatura, Universidad Católica Andrés Bello]. Facultad de Ingeniería, Escuela de Ingeniería Informática - Guayana. Tutor: Ing. Jesús José Lárez Mata.

---

### 2. Fuentes Bibliográficas Técnicas y Regionales

El sustento científico de la arquitectura híbrida (Documental-Grafo), el procesamiento lingüístico y el contexto histórico de Guayana se basan en las siguientes publicaciones indexadas:

#### 🧠 Inteligencia Artificial, RAG y GraphRAG
* **Lewis, P., Perez, E., Piktus, A., Petroni, F., Lewis, M., Riedel, S., & Kiela, D.** (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. *Advances in Neural Information Processing Systems*, 33, 9459-9474.
* **Magham, R. K.** (2024). GraphRAG and role of graph databases in advancing AI. *International Journal of Research in Computer Applications and Information Technology*, 12(1).
* **Es, S., James, J., Espinosa, J., & Ragas Authors.** (2023). *Ragas: Automated evaluation of retrieval augmented generation*. arXiv preprint arXiv:2309.15217.

#### 🗣️ Procesamiento de Lenguaje Natural (NLP) y Text-to-SQL/Cypher
* **Chowdhary, K. R.** (2020). Natural language processing. En *Fundamentals of Artificial Intelligence* (pp. 411-443). Springer, New Delhi.
* **Zhong, V., Xiong, C., & Socher, R.** (2017). *Seq2sql: Generating structured queries from natural language using reinforcement learning*. arXiv preprint arXiv:1709.00103.

#### 🗄️ Bases de Datos de Grafos y Almacenamiento Vectorial
* **Han, Y., Liu, C., & Wang, P.** (2023). *A comprehensive survey on vector database: Storage and retrieval technique*. arXiv preprint arXiv:2310.14021.
* **Robinson, J., Webber, J., & Eifrem, E.** (2021). *Graph Databases: New Opportunities for Connected Data* (2nd ed.). O'Reilly Media, Inc.

#### 🇻🇪 Contexto Literario e Historiográfico Regional
* **Leal, H. B., Gómez, Y. R., & Ajmad, D. R.** (2022). Un diccionario de lo nuestro. Reflexión metalexicográfica para la elaboración de un diccionario de literatura del estado Bolívar. *Revista Guayana Moderna*, (11), 45-58. Universidad Católica Andrés Bello - Núcleo Guayana.

---

## 🏷️ Palabras Clave (Keywords)
`Diccionario en Línea` • `GraphRAG` • `Procesamiento de Lenguaje Natural (PLN)` • `Sistemas de Búsqueda de Respuestas (QA Systems)` • `Neo4j` • `Ollama` • `Estado Bolívar` • `Literatura Guayanesa`