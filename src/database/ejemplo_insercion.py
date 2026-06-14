"""
Ejemplo de inserción de datos literarios en Neo4j con el esquema expandido.
Contiene la sintaxis de Cypher corregida y adaptada al Estado Bolívar, Venezuela.
"""

import os
from datetime import datetime
from typing import Any, Dict
from neo4j import GraphDatabase, Session

# Importación adaptada a tu archivo connection.py creado en el paso anterior
from src.database.connection import db

# ============================================================================
# UTILIDADES
# ============================================================================

def uuid_ficha(prefix: str) -> str:
    """Genera un fichaId único con timestamp."""
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{prefix}_{ts}"


def insertar_autor_con_obras_y_critica(session: Session) -> str:
    """
    Ejemplo: Insertar Autor 'Jean Aristeguieta' con sus obras y críticas.
    Returns: ID del Autor (fichaId)
    """
    ficha_id = uuid_ficha("ARISTEGUIETA")
    
    # Sintaxis corregida: se eliminó el parámetro datetime conflictivo
    cypher = """
    CREATE (a:Autor {
        fichaId: $ficha_id,
        nombres: 'Jean',
        apellidos: 'Aristeguieta',
        nombre_completo: 'Jean Aristeguieta',
        sexo: 'Femenino',
        seudonimo: 'La voz del Orinoco',
        fecha_nacimiento: '1940',
        fecha_fallecimiento: '2015',
        lugar_nacimiento_ciudad: 'Guasipati',
        lugar_nacimiento_municipio: 'Roscio',
        lugar_nacimiento_estado: 'Bolívar',
        lugar_nacimiento_pais: 'Venezuela',
        actividad_relevante: 'Poetisa de la generación del paisaje guayanés. Diplomática y difusora cultural.',
        contexto_vivio: 'Guasipati, Ciudad Bolívar y Caracas. Mediados del siglo XX.',
        tematica_principal: 'El río Orinoco, el oro de Guayana, la selva y el misticismo regional',
        genero_principal: 'Poesía',
        imagen_autor: 'https://letrascopio.gob.ve/media/aristeguieta.jpg',
        audio_voz: 'https://letrascopio.gob.ve/media/aristeguieta_voz.mp3',
        timestamp: datetime()  // Uso nativo de Cypher
    })
    
    // Crear Obra 1
    CREATE (o1:Obra {
        fichaId: $ficha_id_obra1,
        titulo: 'Gemas de Guayana',
        genero: 'Poesía',
        fecha_publicacion: '1964',
        lugar_publicacion_ciudad: 'Ciudad Bolívar',
        editorial: 'Imprenta del Estado Bolívar',
        descripcion: 'Poemario dedicado a las riquezas naturales y leyendas del escudo guayanés',
        idioma_original: 'Español'
    })
    
    // Crear Obra 2
    CREATE (o2:Obra {
        fichaId: $ficha_id_obra2,
        titulo: 'Canto al Orinoco',
        genero: 'Poesía / Épico',
        fecha_publicacion: '1971',
        lugar_publicacion_ciudad: 'Caracas',
        editorial: 'Editorial Arte',
        descripcion: 'Poema extenso que rinde homenaje a la majestuosidad del río padre',
        idioma_original: 'Español'
    })
    
    // Crear Crítica
    CREATE (c:Critica {
        fichaId: $ficha_id_critica,
        tipo: 'Reseña Literaria',
        autor_critica: 'Arturo Uslar Pietri',
        titulo: 'La geografía lírica de Jean Aristeguieta',
        fecha_publicacion: '1975',
        referencia_bibliografica: 'Diario El Nacional, Papel Literario, Caracas.',
        descripcion_resumen: 'Un recorrido por el mapa poético creado por la autora y su conexión con el Estado Bolívar.'
    })
    
    // Relacionar entidades
    CREATE (a)-[:ESCRIBIO]->(o1)
    CREATE (a)-[:ESCRIBIO]->(o2)
    CREATE (c)-[:CRITICA_DE]->(a)
    
    RETURN DISTINCT a.fichaId AS autorId  // Evita la duplicación por relaciones
    """
    
    result = session.run(
        cypher,
        ficha_id=ficha_id,
        ficha_id_obra1=uuid_ficha("GEMAS"),
        ficha_id_obra2=uuid_ficha("CANTO"),
        ficha_id_critica=uuid_ficha("CRITICA_JEAN")
    )
    
    return result.single()["autorId"]


def insertar_agrupacion_literaria(session: Session) -> str:
    ficha_id = uuid_ficha("GRUPO_GUAYANA")
    
    cypher = """
    CREATE (ag:Agrupacion {
        fichaId: $ficha_id,
        nombre: 'Grupo Literario Guayana',
        lugar_encuentros_ciudad: 'Ciudad Bolívar',
        lugar_encuentros_municipio: 'Angostura del Orinoco',
        fecha_inicio: '1970',
        fecha_culminacion: '1985',
        caracteristica_general: 'Colectivo enfocado en revitalizar la identidad poética e histórica del sur de Venezuela',
        actividades: 'Tertulias a orillas del Orinoco, talleres de escritura en la Casa de las Doce Ventanas'
    })
    
    CREATE (ag)-[:PUBLICO]->(pub:PublicacionAgrupacion {
        titulo: 'Cuadernos del Sur',
        anio: '1974',
        resumen: 'Folleto colaborativo de crónicas regionales y versos antológicos'
    })
    
    RETURN ag.fichaId AS agrupacionId
    """
    
    result = session.run(cypher, ficha_id=ficha_id)
    return result.single()["agrupacionId"]


def insertar_revista_literaria(session: Session) -> str:
    ficha_id = uuid_ficha("REV_ORINOCO")
    
    cypher = """
    CREATE (r:Revista {
        fichaId: $ficha_id,
        titulo: 'Orinoco Cultural',
        fecha_primer_numero: '1952-05',
        fecha_ultimo_numero: '1965-12',
        numeros_publicados: 'Números 1 al 24',
        lugar_publicacion_ciudad: 'Ciudad Bolívar',
        editorial: 'Imprenta Regional',
        secciones: 'Crónica, Poesía de la Selva, Reseñas Históricas',
        descripcion: 'Revista clave para entender el movimiento intelectual del Estado Bolívar a mediados de siglo',
        idioma_original: 'Español'
    })
    
    RETURN r.fichaId AS revistaId
    """
    
    result = session.run(cypher, ficha_id=ficha_id)
    return result.single()["revistaId"]


def insertar_mito_leyenda(session: Session) -> str:
    ficha_id = uuid_ficha("SERPIENTE")
    
    cypher = """
    CREATE (ml:MitoLeyenda {
        fichaId: $ficha_id,
        titulo: 'La Serpiente de Siete Cabezas',
        comunidad_creadora: 'Tradición oral popular de Ciudad Bolívar',
        lugar_difusion_ciudad: 'Ciudad Bolívar',
        lugar_difusion_estado: 'Bolívar',
        lugar_difusion_pais: 'Venezuela',
        idioma_original: 'Español',
        tema_principal: 'Mitos del río Orinoco y la Piedra del Medio',
        descripcion: 'Leyenda urbana que afirma que una colosal serpiente duerme bajo la Piedra del Medio y controla las crecidas del río.',
        texto_completo: 'Dicen los viejos lancheros del Orinoco que debajo de la Piedra del Medio habita una criatura gigantesca...'
    })
    
    RETURN ml.fichaId AS mitoId
    """
    
    result = session.run(cypher, ficha_id=ficha_id)
    return result.single()["mitoId"]


def main():
    # Usamos la conexión reutilizable global 'db' que creamos en el paso anterior
    if not db.test_connection():
        return
        
    try:
        with db.driver.session() as session:
            print("🚀 Insertando datos reales del Estado Bolívar en Neo4j...")
            print("-" * 50)
            
            autor_id = insertar_autor_con_obras_y_critica(session)
            print(f"   ✅ Autor Creado (Jean Aristeguieta): {autor_id}")
            
            agrupacion_id = insertar_agrupacion_literaria(session)
            print(f"   ✅ Agrupación Creada (Grupo Guayana): {agrupacion_id}")
            
            revista_id = insertar_revista_literaria(session)
            print(f"   ✅ Revista Creada (Orinoco Cultural): {revista_id}")
            
            mito_id = insertar_mito_leyenda(session)
            print(f"   ✅ Mito Creado (Serpiente 7 Cabezas): {mito_id}")
            
            # --- VERIFICACIÓN DE CONTEO ---
            print("\n📊 Resumen actual de la Base de Datos:")
            resultado = session.run("""
                MATCH (n) 
                RETURN labels(n)[0] as etiqueta, count(n) as total
            """)
            for registro in resultado:
                print(f"   - {registro['etiqueta']}: {registro['total']} nodos.")
                
            print("\n🎉 ¡Inserción completada con éxito y sin errores de sintaxis!")
            
    except Exception as e:
        print(f"❌ Falló la inserción de datos: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()