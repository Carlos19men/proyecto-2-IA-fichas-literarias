from src.database.connection import db
from src.busqueda.buscador import GraphRAGSearcher

def main():
    searcher = GraphRAGSearcher()
    print("Probando busqueda para 'Jean Aristeguieta'...")
    with db.driver.session() as session:
        # Probando busqueda fulltext
        res_ft = searcher._buscar_fulltext(session, "Jean Aristeguieta", limit=5)
        print(f"Resultados Fulltext: {len(res_ft)}")
        for r in res_ft:
            print(f" - Tipo: {r['tipo']}, Score: {r['score']}, Nodo: {r['nodo']}")

        # Probando busqueda vectorial
        res_vec = searcher._buscar_vectorial(session, "Jean Aristeguieta", limit=5)
        print(f"Resultados Vectorial: {len(res_vec)}")
        for r in res_vec:
            print(f" - Tipo: {r['tipo']}, Score: {r['score']}, Nodo: {r['nodo']}")
    db.close()

if __name__ == "__main__":
    main()
