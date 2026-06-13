import sys
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from src.rag.chain import configurar_cadena_rag
from src.config import Config

def reformular_pregunta_con_memoria(pregunta_usuario: str, historial_chat: str, llm_ligero) -> str:
    """
    Toma el historial de la conversación y la nueva pregunta, y redacta 
    una pregunta autoconclusiva para que la base de datos no pierda el contexto.
    """
    if not historial_chat.strip():
        return pregunta_usuario # Si es la primera pregunta, no hay nada que reformular
    
    prompt_memoria = ChatPromptTemplate.from_messages([
        ("system", "Dada la siguiente conversación y una pregunta de seguimiento, "
                   "reformula la pregunta de seguimiento para que sea una pregunta independiente "
                   "(standalone question) que se entienda sin necesidad del historial. "
                   "No respondas a la pregunta, SOLO reformúlala."),
        ("human", "Historial:\n{historial}\n\nPregunta de seguimiento: {pregunta}")
    ])
    
    cadena_reformular = prompt_memoria | llm_ligero
    respuesta = cadena_reformular.invoke({
        "historial": historial_chat, 
        "pregunta": pregunta_usuario
    })
    
    return respuesta.content

def iniciar_interfaz_chat():
    print("========================================================")
    print("📚 Iniciando Asistente Literario GraphRAG...")
    print("⚙️  Conectando motores y leyendo base de datos de grafos...")
    print("========================================================\n")
    
    try:
        motor_rag = configurar_cadena_rag()
        # Usamos el LLM para reformular preguntas de forma rápida
        llm_ligero = ChatOllama(base_url=Config.OLLAMA_BASE_URL, model=Config.OLLAMA_MODEL, temperature=0)
    except Exception as e:
        print(f"❌ Error crítico al iniciar los motores: {e}")
        sys.exit(1)

    # Aquí vivirá la memoria de la sesión actual
    historial_chat = ""
    
    print("✅ ¡Sistema listo! Escribe tu pregunta (o escribe 'salir' para terminar).")
    print("-" * 56)

    # Bucle infinito del chat
    while True:
        try:
            # 1. Leer entrada del usuario
            pregunta_usuario = input("\n👤 Tú: ")
            
            if pregunta_usuario.lower() in ['salir', 'exit', 'quit']:
                print("\n👋 ¡Hasta pronto! Cerrando el asistente...")
                break
            
            if not pregunta_usuario.strip():
                continue

            # 2. Inyectar Memoria (Reformular pregunta si hay historial)
            pregunta_contextualizada = reformular_pregunta_con_memoria(
                pregunta_usuario, 
                historial_chat, 
                llm_ligero
            )
            
            if historial_chat:
                print(f"   [IA entendió la pregunta como: '{pregunta_contextualizada}']")

            print("🧠 Pensando y consultando el grafo...")

            # 3. Consultar la base de datos con la pregunta completa
            respuesta_cruda = motor_rag.invoke({"query": pregunta_contextualizada})
            respuesta_final = respuesta_cruda["result"]
            
            # 4. Imprimir la respuesta de la IA
            print(f"\n🤖 Asistente: {respuesta_final}\n")
            print("-" * 56)

            # 5. Actualizar la memoria para el próximo turno
            historial_chat += f"Usuario: {pregunta_usuario}\nAsistente: {respuesta_final}\n\n"
            
            # (Opcional) Limitar el historial a las últimas 4 interacciones para no saturar la memoria
            lineas_historial = historial_chat.strip().split('\n\n')
            if len(lineas_historial) > 4:
                historial_chat = "\n\n".join(lineas_historial[-4:]) + "\n\n"

        except KeyboardInterrupt:
            # Captura si el usuario presiona Ctrl+C
            print("\n\n👋 Interrupción forzada. ¡Hasta pronto!")
            break
        except Exception as e:
            print(f"\n❌ Ocurrió un error procesando tu solicitud: {e}")

if __name__ == "__main__":
    iniciar_interfaz_chat()