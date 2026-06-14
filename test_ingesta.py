from src.ingestion.loaders import leer_archivo_ficha
from src.ingestion.extractor import extraer_json_de_ficha

def ejecutar_prueba():

    # 1. Define la ruta de una ficha real que tengas en tu computadora
    # Asegúrate de poner un archivo de prueba en esta ruta
    ruta_prueba = "data/raw/Iot comparacion y aplicacion.docx" 

    try:
        print("📄 Leyendo documento...")
        texto = leer_archivo_ficha(ruta_prueba)
        print(f"✅ Documento leído. Longitud: {len(texto)} caracteres.")   

        print("🧠 Enviando a la IA local para extracción (Esto puede tomar unos segundos)...")
        # El resultado será un objeto de Python (Pydantic) con la estructura perfecta
        resultado_estructurado = extraer_json_de_ficha(texto)

        print("\n🎉 ¡Extracción Exitosa! Aquí está el JSON validado:\n")
        # .model_dump_json() convierte el objeto Pydantic a un JSON real formateado
        print(resultado_estructurado.model_dump_json(indent=4))

    except Exception as e:
        print(f"\n❌ Ocurrió un error en la prueba: {e}")

if __name__ == "__main__":
    ejecutar_prueba()

