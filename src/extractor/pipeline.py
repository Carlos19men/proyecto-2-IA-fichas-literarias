import json
from typing import Optional
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from src.config import Config
from .schemas import FichaLiteraria

class ExtractorPipeline:
    """Pipeline para extraer información estructurada de textos literarios"""
    
    def __init__(self):
        self.llm = ChatOllama(
            base_url=Config.OLLAMA_BASE_URL,
            model=Config.OLLAMA_MODEL,
            temperature=0
        )
        
        # Parser para convertir la salida JSON a objetos Pydantic
        self.parser = JsonOutputParser(pydantic_object=FichaLiteraria)
        
        # Prompt para extraer información
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres un experto en análisis literario y extracción de información estructurada.
            
            Tu tarea es analizar el texto proporcionado y extraer información sobre autores, obras y críticas.
            
            Instrucciones:
            1. Identifica el autor principal del texto
            2. Extrae todas las obras mencionadas
            3. Identifica críticas o artículos sobre el autor
            4. Devuelve la información en formato JSON estructurado
            
            {format_instructions}
            
            Sé preciso y extrae solo la información que aparece en el texto."""),
            ("human", "Texto a analizar:\n{texto}")
        ])
        
        # Cadena completa
        self.chain = self.prompt | self.llm | self.parser
    
    def procesar_texto(self, texto: str) -> Optional[FichaLiteraria]:
        """Procesa un texto y devuelve una ficha literaria estructurada"""
        try:
            # Formatear instrucciones para el parser JSON
            format_instructions = self.parser.get_format_instructions()
            
            # Ejecutar la cadena
            result = self.chain.invoke({
                "texto": texto,
                "format_instructions": format_instructions
            })
            
            return result
        except Exception as e:
            print(f"Error procesando texto: {e}")
            return None
    
    def procesar_archivo(self, ruta_archivo: str) -> Optional[FichaLiteraria]:
        """Procesa un archivo de texto y devuelve una ficha literaria"""
        try:
            with open(ruta_archivo, 'r', encoding='utf-8') as f:
                texto = f.read()
            
            return self.procesar_texto(texto)
        except Exception as e:
            print(f"Error leyendo archivo {ruta_archivo}: {e}")
            return None