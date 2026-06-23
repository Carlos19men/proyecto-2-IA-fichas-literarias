from src.busqueda.buscador import GraphRAGSearcher
import json

def main():
    searcher = GraphRAGSearcher()
    print("Buscando 'Jean Aristeguieta'...")
    res = searcher.buscar("Jean Aristeguieta")
    print("\n--- RESPUESTA ---")
    print(res["respuesta_texto"])
    print("\n--- METADATA ---")
    print(json.dumps(res["metadata"], indent=2, ensure_ascii=False))
    print("\n--- PREGUNTAS RELACIONADAS ---")
    print(res["relatedQuestions"])

if __name__ == "__main__":
    main()
