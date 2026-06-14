import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Asegurar que se carguen las variables del archivo .env en la carpeta src/
load_dotenv(dotenv_path="src/.env")

class Neo4jConnection:
    def __init__(self):
        # Leer variables de entorno con los valores por defecto que ya probamos
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "password123")
        self.driver = None
        
        try:
            # Inicializar el driver oficial de Neo4j
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        except Exception as e:
            print(f"❌ Error crítico al inicializar el Driver de Neo4j: {e}")

    def close(self):
        if self.driver:
            self.driver.close()

    def test_connection(self) -> bool:
        """Verifica si el contenedor de Docker responde correctamente"""
        if not self.driver:
            print("❌ No se ha inicializado el driver de la base de datos.")
            return False
        try:
            # Intentamos una consulta ultra rápida para validar credenciales y estado
            self.driver.verify_connectivity()
            print(f"🔌 Conexión exitosa con Neo4j Docker en {self.uri}")
            return True
        except Exception as e:
            print("\n❌ error de conexión: El contenedor Neo4j no está listo o las credenciales fallaron.")
            print(f"Detalle técnico del error: {e}")
            print("\n💡 SOLUCIÓN RECOMENDADA:")
            print("1. Verifica que tu docker esté corriendo ejecutando: docker ps")
            print("2. Revisa que tu archivo src/.env tenga las claves correctas.")
            return False

# Instanciar el objeto global 'db' que importa tu script init_db.py
db = Neo4jConnection()