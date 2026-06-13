from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

class Autor(BaseModel):
    nombre: str = Field(description="Nombre completo del autor")
    seudonimo: Optional[str] = Field(None, description="Seudónimo literario si lo tiene")
    fecha_nacimiento: Optional[date] = Field(None, description="Fecha de nacimiento")
    fecha_muerte: Optional[date] = Field(None, description="Fecha de muerte")
    nacionalidad: Optional[str] = Field(None, description="Nacionalidad del autor")
    
class Obra(BaseModel):
    titulo: str = Field(description="Título de la obra")
    anio_publicacion: Optional[int] = Field(None, description="Año de publicación")
    genero: Optional[str] = Field(None, description="Género literario")
    idioma: Optional[str] = Field("español", description="Idioma de la obra")
    
class Critica(BaseModel):
    titulo: str = Field(description="Título del artículo o crítica")
    fuente: str = Field(description="Fuente de la crítica (ej: Prodavinci, revista, etc.)")
    url: Optional[str] = Field(None, description="URL del artículo")
    fecha_publicacion: Optional[date] = Field(None, description="Fecha de publicación")
    autor_critica: Optional[str] = Field(None, description="Autor de la crítica")
    
class FichaLiteraria(BaseModel):
    """Ficha completa que contiene autor, obras y críticas relacionadas"""
    autor: Autor = Field(description="Información del autor")
    obras: List[Obra] = Field(default_factory=list, description="Lista de obras del autor")
    criticas: List[Critica] = Field(default_factory=list, description="Críticas sobre el autor")