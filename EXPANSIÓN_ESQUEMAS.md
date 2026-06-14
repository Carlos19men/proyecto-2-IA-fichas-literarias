# Expansión de Esquemas: Guía de Implementación

**Fecha**: 2024  
**Estado**: ✅ Completado  
**Próximo paso**: Levantar Docker y ejecutar `init_db.py`

---

## 📋 Resumen de Cambios

### 1. **src/ingestion/schemas.py** (EXPANDIDO)

**De**: 4 clases básicas (Obra, Crítica, FichaLiteraria)  
**A**: 14 clases completas + tipos auxiliares

#### Nuevas Clases Auxiliares:
- **`Lugar`**: Desglosar ubicaciones en ciudad, municipio, estado, país
- **`Persona`**: Representar familiares, creadores, críticos (nombres, apellidos, rol)
- **`Multimedia`**: Recursos con enlace, tipo, restricción, embedding (768 dims)
- **`PublicacionAgrupacion`**: Publicaciones generadas por agrupaciones

#### Clases Expandidas:
- **`AutorSchema`** (Nueva): 40+ campos incluyendo nombres/apellidos separados, multimedia, familiaresDestacados, imagenAutor, audioVoz
- **`ObraSchema`**: Ahora con subgénero, editorial, descripción, multimedia list
- **`CriticaSchema`**: Agregado embedding field para búsqueda semántica

#### Nuevas Clases de Entidades:
- **`AgrupacionSchema`**: Movimientos literarios con integrantes y publicaciones
- **`RevistaSchema`**: Publicaciones periódicas con secciones y creadores
- **`AntologiaSchema`**: Colecciones de obras literarias
- **`MitoLeyendaSchema`**: Tradiciones culturales y narrativas comunitarias

#### Actualizado:
- **`FichaLiterariaSchema`**: Ahora usa `AutorSchema` expandido + listas de agrupaciones, revistas, antologías, mitos/leyendas

### 2. **src/database/init_db.py** (ACTUALIZADO)

#### Constraints Actualizados:
```python
# Ahora soporta 8 tipos de entidades con fichaId único
- unique_autor_ficha
- unique_obra_ficha
- unique_critica_ficha
- unique_revista_ficha
- unique_antologia_ficha
- unique_agrupacion_ficha
- unique_multimedia_ficha
- unique_mitleyenda_ficha
```

#### Fulltext Indexes Expandidos:
- ✅ Autor: nombres, apellidos, seudonimo
- ✅ Obra: titulo, descripcion
- ✅ Crítica: titulo, autor, descripcion_resumen
- ✅ Revista: titulo, descripcion
- ✅ Antología: titulo, descripcion
- ✅ Agrupación: nombre, caracteristica_general
- ✅ MitoLeyenda: titulo, tema_principal, descripcion

#### Vector Indexes (Búsqueda Semántica):
- ✅ Crítica.embedding (768 dims, cosine)
- ✅ Autor.embedding (768 dims, cosine)
- ✅ Multimedia.embedding (768 dims, cosine) — **NUEVO**

**Formato de Embedding**: `List[float]` de 768 dimensiones (compatible con nomic-embed-text de Ollama)

### 3. **src/ingestion/extractor.py** (MEJORADO)

**Prompt actualizado** para:
- Separar nombres y apellidos
- Desglosar lugares en componentes geográficos
- Validar formatos de fecha (YYYY o YYYY-MM-DD)
- Extraer multimedia con tipos específicos (imagen, audio, video, pdf)
- No alucinar datos no mencionados
- Rellenar solo campos opcionales que estén en el texto

### 4. **src/database/ejemplo_insercion.py** (NUEVO)

Archivo ejecutable que demuestra:
- Inserción de Autor completo con Obras y Críticas
- Creación de Agrupaciones literarias
- Creación de Revistas literarias
- Creación de Mitos/Leyendas

Uso:
```bash
python src/database/ejemplo_insercion.py
```

---

## 🚀 Instrucciones de Uso

### Paso 1: Verificar Cambios Locales
```bash
# Verificar que schemas.py se expandió correctamente
wc -l src/ingestion/schemas.py  # Debe ser ~359 líneas

# Verificar imports
python -c "from src.ingestion.schemas import AutorSchema, AgrupacionSchema, MitoLeyendaSchema; print('✅ Todos los imports funcionan')"
```

### Paso 2: Levantar Neo4j
```bash
# Con Docker Compose (requiere .env en src/)
docker compose --env-file src/.env up -d

# Verificar estado
docker ps | grep neo4j_literario
```

### Paso 3: Inicializar Esquema en Neo4j
```bash
# Crear constraints e índices
python -m src.database.init_db

# Debe mostrar:
# ✅ Constraints creados
# ✅ Índices fulltext creados
# ✅ Índices vectoriales creados
```

### Paso 4: Insertar Datos de Ejemplo (Opcional)
```bash
python src/database/ejemplo_insercion.py

# Debe mostrar:
# 🚀 Insertando datos de ejemplo en Neo4j...
# ✅ Autor creado
# ✅ Agrupación creada
# ... etc
```

### Paso 5: Usar Schemas en Ingesta Real
```python
from src.ingestion.schemas import FichaLiterariaSchema, AutorSchema
from src.ingestion.extractor import extraer_json_de_ficha

# Extraer de documento
ficha = extraer_json_de_ficha(texto_documento)

# Ahora ficha.autor es AutorSchema con todos los campos
print(ficha.autor.nombres)  # "Juan"
print(ficha.autor.apellidos)  # "Montalvo"
print(ficha.autor.lugar_nacimiento.ciudad)  # "Ambato"
print(ficha.autor.multimedia)  # List[Multimedia]
```

---

## 🔄 Flujo Completo de Ingesta

```
Documento (.docx, .md)
        ↓
Loader (UnstructuredMarkdownLoader, Docx2txtLoader)
        ↓
Extractor (LLM + Pydantic) → FichaLiterariaSchema
        ↓
Validación (Pydantic automática)
        ↓
Normalización (formatos de fecha, lugares desglosados)
        ↓
Generación de Embeddings (Ollama nomic-embed-text)
        ↓
Inserción en Neo4j (CREATE nodos, relaciones)
        ↓
Vector Index Store (búsqueda semántica por embedding)
```

---

## 📊 Métricas del Esquema Actualizado

| Métrica | Valor |
|---------|-------|
| **Clases de Esquema** | 14 (Autor, Obra, Crítica, Revista, Antología, Agrupación, MitoLeyenda + auxiliares) |
| **Campos en AutorSchema** | 40+ |
| **Tipos de Multimedia** | imagen, audio, video, pdf |
| **Dimensiones de Embedding** | 768 (nomic-embed-text) |
| **Índices Vectoriales** | 3 (Crítica, Autor, Multimedia) |
| **Índices Fulltext** | 7 (una por entidad principal) |
| **Constraints Únicos** | 14 (fichaId + legacy names) |

---

## ⚙️ Configuración de Embeddings

### Generación en Ingesta:
```python
from langchain_ollama import OllamaEmbeddings

embeddings = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url="http://localhost:11434"
)

# Para cada texto (descripción de obra, crítica, etc.):
vector = embeddings.embed_query("Texto del que extraer embedding")
# Retorna: List[float] de 768 dimensiones
```

### Almacenamiento en Neo4j:
```cypher
CREATE (c:Critica {
    titulo: "Análisis de Obra",
    embedding: [0.123, 0.456, ..., 0.789]  // 768 valores
})
```

### Búsqueda Semántica:
```cypher
WITH $query_embedding AS query_vec
MATCH (c:Critica)
WITH c, 
     gds.similarity.cosine(c.embedding, query_vec) AS score
WHERE score > 0.7
RETURN c, score
ORDER BY score DESC
LIMIT 5
```

---

## 🐛 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'src.ingestion.schemas'"
**Solución**: Ejecutar desde la raíz del proyecto
```bash
cd /path/to/proyecto-2-IA-fichas-literarias
python -m src.database.init_db
```

### Error: "Neo4j server not available"
**Solución**: Verificar que Docker está corriendo y Neo4j inició
```bash
docker logs neo4j_literario  # Ver logs del contenedor
docker compose --env-file src/.env up -d  # Reiniciar
```

### Error: "FULLTEXT INDEX already exists"
**Solución**: Es esperado en ejecuciones repetidas. El script usa `IF NOT EXISTS`.

### Error: "VECTOR INDEX not supported"
**Solución**: Verificar versión de Neo4j (requiere v5.13+)
```bash
docker run neo4j:5.15 --version
```

---

## 📚 Referencias

- **Pydantic v2 Docs**: https://docs.pydantic.dev/
- **Neo4j Vector Index**: https://neo4j.com/docs/cypher-manual/current/administration/indexes-search-native-vector/
- **Ollama Embeddings**: https://ollama.ai/library/nomic-embed-text
- **LangChain Pydantic**: https://python.langchain.com/docs/modules/model_io/output_parsers/pydantic

---

## ✅ Checklist de Verificación

- [x] Schemas.py expandido con todas las clases
- [x] init_db.py actualizado con constraints e índices para nuevas entidades
- [x] Extractor mejorado con prompt actualizado
- [x] Archivo ejemplo_insercion.py creado
- [ ] Docker levantado (`docker compose --env-file src/.env up -d`)
- [ ] Schema inicializado (`python -m src.database.init_db`)
- [ ] Datos de ejemplo insertados (`python src/database/ejemplo_insercion.py`)
- [ ] Prompts RAG optimizados (Opción A pendiente)
- [ ] Ingesta completa de documento de prueba

---

**Última actualización**: Sesión actual  
**Responsable**: Sistema de Ingesta Literaria GraphRAG
