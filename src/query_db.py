from src.database.connection import db

def main():
    if not db.test_connection():
        print("No se pudo conectar a Neo4j")
        return
    with db.driver.session() as session:
        result = session.run("MATCH (n) RETURN labels(n) as labels, keys(n) as keys, n.nombres as nombres, n.nombre as nombre, n.titulo as titulo, n.fichaId as fichaId LIMIT 50")
        print("Nodos en la base de datos:")
        for record in result:
            print(f"Etiquetas: {record['labels']}, fichaId: {record['fichaId']}, nombres: {record['nombres']}, nombre: {record['nombre']}, titulo: {record['titulo']}")
    db.close()

if __name__ == "__main__":
    main()
