"""
Ejemplo de inserción de datos literarios en Neo4j con el esquema expandido.
Demuestra cómo crear nodos Autor, Obra, Crítica, Agrupación, etc. con todas sus relaciones.

Ejecutar después de:
1. docker compose --env-file src/.env up -d
2. python -m src.database.init_db
3. Tener LLM Ollama ejecutándose en localhost:11434
"""

import os
import json
from datetime import datetime
from typing import Any, Dict

from neo4j import GraphDatabase, Session
from src.config import load_config

# ============================================================================
# UTILIDADES
# ============================================================================

def uuid_ficha(prefix: str) -> str:
    """Genera un fichaId único con timestamp."""
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{prefix}_{ts}"


def insertar_autor_con_obras_y_critica(session: Session, config: Dict[str, Any]) -> str:
    """
    Ejemplo: Insertar Autor 'Juan Montalvo' con obras y críticas.
    Returns: ID del Autor (fichaId)
    """
    ficha_id = uuid_ficha("MONTALVO")
    
    # Cypher para crear Autor con propiedades anidadas (Lugar como propiedades, Multimedia como nodos)
    cypher = """
    CREATE (a:Autor {
        fichaId: $ficha_id,
        nombres: 'Juan',
        apellidos: 'Montalvo y Fajardo',
        nombre_completo: 'Juan Montalvo y Fajardo',
        sexo: 'Masculino',
        seudonimo: 'Catón',
        fecha_nacimiento: '1832',
        fecha_fallecimiento: '1889',
        lugar_nacimiento_ciudad: 'Ambato',
        lugar_nacimiento_pais: 'Ecuador',
        lugar_fallecimiento_ciudad: 'París',
        lugar_fallecimiento_pais: 'Francia',
        actividad_relevante: 'Escritor ecuatoriano del siglo XIX. Famoso por sus ensayos políticos y su participación en luchas contra la tiranía. Exiliado múltiples veces.',
        contexto_vivio: 'Ecuador, Perú, Colombia, París. Época del Romanticismo latinoamericano.',
        tematica_principal: 'Libertad, tiranía, justicia social, política',
        genero_principal: 'Ensayo, novela',
        imagen_autor: 'https://example.com/montalvo.jpg',
        audio_voz: 'https://example.com/montalvo_voz.mp3',
        timestamp: datetime()
    })
    
    // Crear Obra 1: 'Siete Tratados'
    CREATE (o1:Obra {
        fichaId: $ficha_id_obra1,
        titulo: 'Siete Tratados',
        genero: 'Ensayo',
        fecha_publicacion: '1882',
        lugar_publicacion_ciudad: 'París',
        lugar_publicacion_pais: 'Francia',
        editorial: 'Imprenta de A. Lahure',
        descripcion: 'Colección de ensayos políticos y sociales que critican la tiranía',
        idioma_original: 'español'
    })
    
    // Crear Obra 2: 'Numas'
    CREATE (o2:Obra {
        fichaId: $ficha_id_obra2,
        titulo: 'Numas',
        genero: 'Novela',
        fecha_publicacion: '1884',
        lugar_publicacion_ciudad: 'París',
        lugar_publicacion_pais: 'Francia',
        editorial: 'Imprenta de A. Lahure',
        descripcion: 'Novela utópica que describe una sociedad ideal',
        idioma_original: 'español'
    })
    
    // Crear Crítica sobre Montalvo
    CREATE (c:Critica {
        fichaId: $ficha_id_critica,
        tipo: 'Artículo académico',
        autor: 'Ángel Rama',
        titulo: 'Juan Montalvo: El ensayista como ideólogo',
        fecha_publicacion: '1975',
        referencia_bibliografica: 'Rama, A. Ensayos sobre la literatura de América. Montevideo: Biblioteca de Marcha.',
        descripcion_resumen: 'Análisis de la función del ensayo montaviano en la construcción de la identidad latinoamericana'
    })
    
    // Relacionar Autor → Obras
    CREATE (a)-[:ESCRIBIO]->(o1)
    CREATE (a)-[:ESCRIBIO]->(o2)
    
    // Relacionar Autor ← Crítica
    CREATE (c)-[:CRITICA_DE]->(a)
    
    RETURN a.fichaId AS autorId
    """
    
    result = session.run(
        cypher,
        ficha_id=ficha_id,
        ficha_id_obra1=uuid_ficha("SIETETRATADOS"),
        ficha_id_obra2=uuid_ficha("NUMAS"),
        ficha_id_critica=uuid_ficha("CRITICA_MONTALVO"),
        datetime=datetime.now()
    )
    
    return result.single()["autorId"]


def insertar_agrupacion_literaria(session: Session) -> str:
    """
    Ejemplo: Insertar agrupación literaria 'Generación de 1930'
    Returns: ID de la Agrupación
    """
    ficha_id = uuid_ficha("GEN1930")
    
    cypher = """
    CREATE (ag:Agrupacion {
        fichaId: $ficha_id,
        nombre: 'Generación de 1930',
        lugar_encuentros_ciudad: 'Quito',
        lugar_encuentros_pais: 'Ecuador',
        fecha_inicio: '1930',
        fecha_culminacion: '1945',
        caracteristica_general: 'Movimiento literario ecuatoriano enfocado en la narrativa social y realismo',
        actividades: 'Tertulias en cafés de Quito, lecturas públicas, colaboraciones en revistas culturales'
    })
    
    // Crear publicación de la agrupación
    CREATE (ag)-[:PUBLICO]->(pub:PublicacionAgrupacion {
        titulo: 'Revista de las Letras',
        anio: '1935',
        resumen: 'Revista colaborativa de poesía y ensayo'
    })
    
    RETURN ag.fichaId AS agrupacionId
    """
    
    result = session.run(cypher, ficha_id=ficha_id)
    return result.single()["agrupacionId"]


def insertar_revista_literaria(session: Session) -> str:
    """
    Ejemplo: Insertar revista literaria 'El Telégrafo Literario'
    Returns: ID de la Revista
    """
    ficha_id = uuid_ficha("TELEGRAFO")
    
    cypher = """
    CREATE (r:Revista {
        fichaId: $ficha_id,
        titulo: 'El Telégrafo Literario',
        fecha_primer_numero: '1885-01',
        fecha_ultimo_numero: '1900-12',
        numeros_publicados: 'Volumes 1-15, números mensuales',
        lugar_publicacion_ciudad: 'Guayaquil',
        lugar_publicacion_pais: 'Ecuador',
        editorial: 'Imprenta Nacional',
        secciones: 'Prosa, Poesía, Crítica Literaria, Noticias',
        descripcion: 'Revista de difusión literaria ecuatoriana con colaboraciones de autores reconocidos',
        idioma_original: 'español'
    })
    
    RETURN r.fichaId AS revistaId
    """
    
    result = session.run(cypher, ficha_id=ficha_id)
    return result.single()["revistaId"]


def insertar_mito_leyenda(session: Session) -> str:
    """
    Ejemplo: Insertar mito/leyenda 'La Laguna de Yambo' (Tungurahua, Ecuador)
    Returns: ID del MitoLeyenda
    """
    ficha_id = uuid_ficha("YAMBO")
    
    cypher = """
    CREATE (ml:MitoLeyenda {
        fichaId: $ficha_id,
        titulo: 'La Laguna de Yambo',
        comunidad_creadora: 'Comunidades indígenas de Tungurahua',
        lugar_difusion_ciudad: 'Ambato',
        lugar_difusion_provincia: 'Tungurahua',
        lugar_difusion_pais: 'Ecuador',
        idioma_original: 'kichwa',
        tema_principal: 'Cosmogonía andina, espíritus de agua',
        descripcion: 'Leyenda sobre una laguna encantada que guarda tesoros y castiga a los avaros',
        texto_completo: 'Hace muchos años, en la laguna de Yambo vivía una hermosa doncella que era la guardiana del agua...'
    })
    
    RETURN ml.fichaId AS mitoId
    """
    
    result = session.run(cypher, ficha_id=ficha_id)
    return result.single()["mitoId"]


def main():
    """Ejecutar ejemplos de inserción."""
    config = load_config()
    
    # Conectar a Neo4j
    driver = GraphDatabase.driver(
        config["neo4j_uri"],
        auth=(config["neo4j_username"], config["neo4j_password"])
    )
    
    try:
        with driver.session() as session:
            print("🚀 Insertando datos de ejemplo en Neo4j...")
            
            # Ejemplo 1: Autor con obras y crítica
            print("\n1️⃣  Insertando Autor 'Juan Montalvo'...")
            autor_id = insertar_autor_con_obras_y_critica(session, config)
            print(f"   ✅ Autor creado: {autor_id}")
            
            # Ejemplo 2: Agrupación literaria
            print("\n2️⃣  Insertando Agrupación 'Generación de 1930'...")
            agrupacion_id = insertar_agrupacion_literaria(session)
            print(f"   ✅ Agrupación creada: {agrupacion_id}")
            
            # Ejemplo 3: Revista literaria
            print("\n3️⃣  Insertando Revista 'El Telégrafo Literario'...")
            revista_id = insertar_revista_literaria(session)
            print(f"   ✅ Revista creada: {revista_id}")
            
            # Ejemplo 4: Mito/Leyenda
            print("\n4️⃣  Insertando Mito 'La Laguna de Yambo'...")
            mito_id = insertar_mito_leyenda(session)
            print(f"   ✅ Mito/Leyenda creado: {mito_id}")
            
            # Verificar datos insertados
            print("\n📊 Verificando datos insertados...")
            resultado = session.run("""
                MATCH (a:Autor), (o:Obra), (c:Critica), (ag:Agrupacion), (r:Revista), (ml:MitoLeyenda)
                RETURN count(a) as autores, count(o) as obras, count(c) as criticas, 
                       count(ag) as agrupaciones, count(r) as revistas, count(ml) as mitos
            """)
            stats = resultado.single()
            print(f"   Autores: {stats['autores']}")
            print(f"   Obras: {stats['obras']}")
            print(f"   Críticas: {stats['criticas']}")
            print(f"   Agrupaciones: {stats['agrupaciones']}")
            print(f"   Revistas: {stats['revistas']}")
            print(f"   Mitos/Leyendas: {stats['mitos']}")
            
            print("\n✅ Inserción de ejemplo completada.")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
