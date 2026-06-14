import sys
import traceback
from src.ingestion.loaders import leer_archivo_ficha
from src.ingestion.extractor import extraer_json_de_ficha
from src.database.uploader import FichaUploader
from src.ingestion.schemas import (
    FichaLiterariaSchema,
    AutorSchema,
    ObraSchema,
    CriticaSchema,
    AgrupacionSchema,
    MitoLeyendaSchema,
    Lugar
)

def obtener_datos_mock() -> FichaLiterariaSchema:
    """Retorna una ficha estructurada de prueba para validar Neo4j si Ollama no está corriendo."""
    return FichaLiterariaSchema(
        autor=AutorSchema(
            nombres="Jean",
            apellidos="Aristeguieta",
            nombre_completo="Jean Aristeguieta",
            sexo="Femenino",
            seudonimo="La voz del Orinoco",
            fecha_nacimiento="1940",
            fecha_fallecimiento="2015",
            lugar_nacimiento=Lugar(ciudad="Guasipati", estado="Bolívar", pais="Venezuela"),
            actividad_relevante="Poetisa de la generacion del paisaje guayanes. Diplomatica y difusora cultural.",
            contexto_vivio="Guasipati y Ciudad Bolivar a mediados del siglo XX.",
            tematica_principal="El rio Orinoco, la selva y el misticismo regional.",
            genero_principal="Poesia",
            obras=[
                ObraSchema(
                    titulo="Gemas de Guayana",
                    genero="Poesia",
                    fecha_publicacion="1964",
                    lugar_publicacion=Lugar(ciudad="Ciudad Bolivar", estado="Bolívar"),
                    editorial="Imprenta del Estado Bolivar",
                    descripcion="Poemario dedicado a las riquezas naturales del escudo guayanes.",
                    idioma_original="Español"
                ),
                ObraSchema(
                    titulo="Canto al Orinoco",
                    genero="Poesia",
                    fecha_publicacion="1971",
                    lugar_publicacion=Lugar(ciudad="Caracas", pais="Venezuela"),
                    editorial="Editorial Arte",
                    descripcion="Poema extenso que rinde homenaje a la majestuosidad del rio.",
                    idioma_original="Español"
                )
            ],
            criticas=[
                CriticaSchema(
                    tipo="Resena Literaria",
                    autor="Arturo Uslar Pietri",
                    titulo="La geografia lirica de Jean Aristeguieta",
                    fecha_publicacion="1975",
                    referencia_bibliografica="Diario El Nacional, Papel Literario, Caracas.",
                    descripcion_resumen="Un recorrido por el mapa poetico creado por la autora."
                )
            ]
        ),
        agrupaciones=[
            AgrupacionSchema(
                nombre="Grupo Literario Guayana",
                lugar_encuentros=Lugar(ciudad="Ciudad Bolivar"),
                fecha_inicio="1970",
                fecha_culminacion="1985",
                caracteristica_general="Colectivo enfocado en revitalizar la identidad poetica del sur de Venezuela."
            )
        ],
        mitos_leyendas=[
            MitoLeyendaSchema(
                titulo="La Serpiente de Siete Cabezas",
                comunidad_creadora="Tradicion oral popular de Ciudad Bolivar",
                lugar_difusion=Lugar(ciudad="Ciudad Bolivar", estado="Bolívar"),
                idioma_original="Español",
                tema_principal="Mitos del rio Orinoco y la Piedra del Medio",
                descripcion="Leyenda urbana que afirma que una colosal serpiente duerme bajo la Piedra del Medio."
            )
        ]
    )

def ejecutar_ingesta_completa():
    ruta_prueba = "data/raw/Iot comparacion y aplicacion.docx"

    print("==============================================================")
    print(" INICIANDO PIPELINE GRAPHRAG: INGESTA DE FICHA A NEO4J")
    print("==============================================================")

    try:
        # Paso 1: Leer documento crudo
        print("[-] 1. Leyendo documento Word de prueba...")
        texto = leer_archivo_ficha(ruta_prueba)
        print("    -> Documento leido con exito. (Longitud: {} caracteres)".format(len(texto)))

        # Paso 2: Extraer JSON estructurado mediante IA Local
        print("\n[-] 2. Extrayendo informacion estructurada con Ollama...")
        print("      (Este paso puede tomar unos segundos, por favor espera...)")
        
        try:
            resultado_estructurado = extraer_json_de_ficha(texto)
            print("    -> Informacion extraida y validada con Pydantic.")
        except Exception as ollama_err:
            print("\n[!] AVISO: Hubo un inconveniente al comunicarse con Ollama ({}).".format(ollama_err))
            print("    -> Activando modo SIMULACION con datos de la ficha real del Estado Bolivar...")
            resultado_estructurado = obtener_datos_mock()

        # Imprimir resumen de lo extraído para control del usuario
        print("\n[-] Resumen de la Informacion a Cargar:")
        autor = resultado_estructurado.autor
        print("   * Autor: {} {}".format(autor.nombres, autor.apellidos))
        print("   * Cantidad de Obras: {}".format(len(autor.obras)))
        print("   * Cantidad de Criticas: {}".format(len(autor.criticas)))
        print("   * Cantidad de Agrupaciones: {}".format(len(resultado_estructurado.agrupaciones)))
        print("   * Cantidad de Mitos/Leyendas: {}".format(len(resultado_estructurado.mitos_leyendas)))

        # Paso 3: Conectar y subir a la base de datos de grafos Neo4j
        print("\n[-] 3. Conectando a Neo4j y subiendo grafo literario...")
        uploader = FichaUploader()
        exito = uploader.subir_ficha(resultado_estructurado)

        if exito:
            print("\n==============================================================")
            print(" PIPELINE COMPLETADO CON EXITO")
            print("==============================================================")
            print(" -> Puedes abrir Neo4j Browser en http://localhost:7474")
            print(" -> Ejecuta esta consulta Cypher para ver el grafo:")
            print("    MATCH (a:Autor)-[r]->(o) RETURN a, r, o LIMIT 20")
        else:
            print("\n[!] El pipeline fallo en la etapa de subida a la base de datos.")

    except Exception as e:
        print("\n[!] Error critico durante la ejecucion del pipeline: {}".format(e))
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    ejecutar_ingesta_completa()
