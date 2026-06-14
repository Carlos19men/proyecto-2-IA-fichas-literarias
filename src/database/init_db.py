from src.database.connection import db


def _crear_constraints(session):
    """
    Restricciones de unicidad por fichaId para todos los nodos principales.
    Se mantienen también los constraints legacy por nombre/titulo para
    compatibilidad con el pipeline de ingesta existente.
    """
    constraints = [
        # --- Constraints por fichaId (identificador único de ficha) ---
        ("unique_autor_ficha",       "Autor",            "fichaId"),
        ("unique_obra_ficha",        "Obra",             "fichaId"),
        ("unique_critica_ficha",     "Critica",          "fichaId"),
        ("unique_revista_ficha",     "Revista",          "fichaId"),
        ("unique_antologia_ficha",   "Antologia",        "fichaId"),
        ("unique_agrupacion_ficha",  "Agrupacion",       "fichaId"),
        ("unique_multimedia_ficha",  "Multimedia",       "fichaId"),
        ("unique_mitleyenda_ficha",  "MitoLeyenda",      "fichaId"),

        # --- Constraints legacy por nombre/titulo (nombres en español) ---
        ("unique_autor_nombre",      "Autor",            "nombres"),
        ("unique_obra_titulo",       "Obra",             "titulo"),
        ("unique_revista_titulo",    "Revista",          "titulo"),
        ("unique_antologia_titulo",  "Antologia",        "titulo"),
        ("unique_agrupacion_nombre", "Agrupacion",       "nombre"),
        ("unique_mitleyenda_titulo", "MitoLeyenda",      "titulo"),
    ]

    for name, label, prop in constraints:
        session.run(f"""
            CREATE CONSTRAINT {name} IF NOT EXISTS
            FOR (n:{label}) REQUIRE n.{prop} IS UNIQUE
        """)

    print("✅ Restricciones de unicidad creadas (fichaId + nombre/titulo).")


def _crear_indices_fulltext(session):
    """
    Índices de texto completo para búsquedas exactas por nombre y título.
    Permiten que el agente de IA genere consultas Cypher rápidas cuando
    el usuario pregunta por un nombre o título específico.
    """
    # Usamos nombres de propiedad en español para coincidir con la capa de ingesta
    try:
        session.run("""
            CREATE FULLTEXT INDEX fulltext_autor_names IF NOT EXISTS
            FOR (a:Autor)
            ON EACH [a.nombres, a.apellidos, a.seudonimo]
        """)

        session.run("""
            CREATE FULLTEXT INDEX fulltext_obra_titles IF NOT EXISTS
            FOR (o:Obra)
            ON EACH [o.titulo, o.descripcion]
        """)

        session.run("""
            CREATE FULLTEXT INDEX fulltext_critica_titles IF NOT EXISTS
            FOR (c:Critica)
            ON EACH [c.titulo, c.autor, c.descripcion_resumen]
        """)

        session.run("""
            CREATE FULLTEXT INDEX fulltext_revista_names IF NOT EXISTS
            FOR (r:Revista)
            ON EACH [r.titulo, r.descripcion]
        """)

        session.run("""
            CREATE FULLTEXT INDEX fulltext_antologia_titles IF NOT EXISTS
            FOR (a:Antologia)
            ON EACH [a.titulo, a.descripcion]
        """)

        session.run("""
            CREATE FULLTEXT INDEX fulltext_agrupacion_names IF NOT EXISTS
            FOR (ag:Agrupacion)
            ON EACH [ag.nombre, ag.caracteristica_general]
        """)

        session.run("""
            CREATE FULLTEXT INDEX fulltext_mitleyenda_titles IF NOT EXISTS
            FOR (ml:MitoLeyenda)
            ON EACH [ml.titulo, ml.tema_principal, ml.descripcion]
        """)
    except Exception as e:
        print(f"⚠️  No se pudieron crear algunos índices fulltext: {e}")


def _crear_indices_vectoriales(session):
    """
    Índice vectorial para búsqueda semántica con embeddings de Ollama.
    Usa 768 dimensiones (nomic-embed-text) con similitud coseno.
    Sintaxis corregida y optimizada para Neo4j v5.15+.
    """
    try:
        # 1. Índice para Críticas
        session.run("""
            CREATE VECTOR INDEX index_criticas_vector IF NOT EXISTS
            FOR (c:Critica) ON (c.embedding)
            OPTIONS {
              indexConfig: {
                `vector.dimensions`: 768,
                `vector.similarity_function`: "cosine"
              }
            }
        """)

        # 2. Índice para Autores
        session.run("""
            CREATE VECTOR INDEX index_autores_vector IF NOT EXISTS
            FOR (a:Autor) ON (a.embedding)
            OPTIONS {
              indexConfig: {
                `vector.dimensions`: 768,
                `vector.similarity_function`: "cosine"
              }
            }
        """)

        # 3. Índice para Multimedia
        session.run("""
            CREATE VECTOR INDEX index_multimedia_vector IF NOT EXISTS
            FOR (m:Multimedia) ON (m.embedding)
            OPTIONS {
              indexConfig: {
                `vector.dimensions`: 768,
                `vector.similarity_function`: "cosine"
              }
            }
        """)

        print("✅ Índices vectoriales creados con éxito (Critica, Autor, Multimedia — 768 dims, cosine).")
    except Exception as e:
        print(f"⚠️  No se pudieron crear índices vectoriales (ver versión Neo4j / configuración): {e}")

def configurar_base_de_datos():
    """
    Función principal de inicialización.
    Crea constraints, índices fulltext e índices vectoriales.
    
    Relaciones esperadas post-inserción:
    ──────────────────────────────────────
    (Autor)-[:ESCRIBIO]->(Obra)
    (Critica)-[:CRITICA_DE]->(Autor | Obra)
    (Autor)-[:PERTENECE_A]->(Agrupacion)
    (Revista)-[:PUBLICA]->(Obra | Critica)
    (Antologia)-[:CONTIENE]->(Obra)
    (Autor)-[:RELACIONADO_CON]->(MitoLeyenda)
    (Multimedia)-[:ASOCIADA_A]->(Autor | Obra | Revista | Antologia | MitoLeyenda)
    """
    if not db.test_connection():
        return

    with db.driver.session() as session:
        print("🔧 Configurando esquema del grafo literario...")
        print("-" * 50)

        _crear_constraints(session)
        _crear_indices_fulltext(session)
        _crear_indices_vectoriales(session)

        print("-" * 50)
        print("🎉 ¡Base de datos preparada para recibir el grafo literario completo!")


if __name__ == "__main__":
    configurar_base_de_datos()
