from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

# ============================================================================
# MODELOS AUXILIARES / ESTRUCTURAS COMPARTIDAS
# ============================================================================

class Lugar(BaseModel):
    """Ubicación desglosada en componentes geográficos."""
    ciudad: Optional[str] = Field(None, description="Ciudad")
    municipio: Optional[str] = Field(None, description="Municipio")
    estado: Optional[str] = Field(None, description="Estado o provincia")
    pais: Optional[str] = Field(None, description="País")

class Persona(BaseModel):
    """Estructura para representar personas (familiares, críticos, etc.)."""
    nombres: Optional[str] = Field(None, description="Nombres de la persona")
    apellidos: Optional[str] = Field(None, description="Apellidos de la persona")
    rol: Optional[str] = Field(None, description="Rol o relación (ej: padre, hermano, crítico)")

class Multimedia(BaseModel):
    """Recurso multimedia: imágenes, audio, video."""
    enlace: str = Field(description="URL o ruta del archivo multimedia")
    tipo: str = Field(description="Tipo de multimedia: imagen, audio, video, pdf")
    restriccion: Optional[str] = Field(None, description="Restricción de acceso: público, privado, restringido")
    embedding: Optional[List[float]] = Field(None, description="Vector de 768 dimensiones para búsqueda semántica")

class PublicacionAgrupacion(BaseModel):
    """Publicación generada por una agrupación literaria."""
    titulo: str = Field(description="Título de la publicación")
    anio: str = Field(description="Año de publicación")
    resumen: Optional[str] = Field(None, description="Resumen de la publicación")

# ============================================================================
# OBRA Y CRÍTICA
# ============================================================================

class ObraSchema(BaseModel):
    """Obra literaria con detalles editoriales y multimedia."""
    titulo: str = Field(description="Título oficial de la obra")
    genero: str = Field(description="Género principal (novela, cuento, poesía, ensayo, etc.)")
    subgenero: Optional[str] = Field(None, description="Subgénero más específico")
    fecha_publicacion: str = Field(description="Año o fecha de publicación (ej: 1883)")
    lugar_publicacion: Optional[Lugar] = Field(None, description="Lugar de publicación desglosado")
    editorial: Optional[str] = Field(None, description="Editorial o imprenta")
    descripcion: Optional[str] = Field(None, description="Descripción, sinopsis o resumen")
    idioma_original: str = Field(default="español", description="Idioma original de la obra")
    multimedia: List[Multimedia] = Field(default=[], description="Multimedia asociada: PDF, portada JPG, MP3, etc.")
    embedding: Optional[List[float]] = Field(None, description="Vector de 768 dimensiones para búsqueda semántica")

class CriticaSchema(BaseModel):
    """Crítica, reseña o interpretación de una obra o autor."""
    tipo: str = Field(description="Tipo de crítica: libro, artículo, reseña, trabajo de grado, etc.")
    autor: str = Field(description="Nombre del crítico o investigador")
    titulo: str = Field(description="Título del artículo o libro de crítica")
    fecha_publicacion: str = Field(description="Año de publicación de la crítica")
    referencia_bibliografica: str = Field(description="Referencia completa: editorial, URL, revista, etc.")
    descripcion_resumen: Optional[str] = Field(None, description="Resumen de hallazgos o conclusiones")
    embedding: Optional[List[float]] = Field(None, description="Vector de 768 dimensiones para búsqueda semántica")

# ============================================================================
# AUTOR
# ============================================================================

class AutorSchema(BaseModel):
    """Autor literario con información biográfica, trayectoria y multimedia."""
    
    # Identidad
    nombres: str = Field(description="Nombres del autor")
    apellidos: str = Field(description="Apellidos del autor")
    nombre_completo: Optional[str] = Field(None, description="Nombre completo formado (nombres + apellidos)")
    sexo: str = Field(description="Género: Femenino, Masculino, Otro, Desconocido")
    seudonimo: Optional[str] = Field(None, description="Seudónimo literario si lo tiene")
    
    # Cronología y Ubicación
    fecha_nacimiento: Optional[str] = Field(None, description="Fecha de nacimiento (ISO YYYY-MM-DD o YYYY)")
    fecha_fallecimiento: Optional[str] = Field(None, description="Fecha de fallecimiento (ISO YYYY-MM-DD o YYYY)")
    lugar_nacimiento: Optional[Lugar] = Field(None, description="Lugar de nacimiento desglosado")
    lugar_fallecimiento: Optional[Lugar] = Field(None, description="Lugar de fallecimiento desglosado")
    
    # Trayectoria y Entorno
    actividad_relevante: Optional[str] = Field(None, description="Texto biográfico: estudios, cargos, profesión, periodos")
    familiares_destacados: List[Persona] = Field(default=[], description="Parientes relevantes: padres, hermanos, hijos")
    contexto_vivio: Optional[str] = Field(None, description="Marco histórico y social en el que vivió")
    
    # Perfil Literario
    tematica_principal: Optional[str] = Field(None, description="Temas centrales en su obra")
    genero_principal: str = Field(description="Género principal cultivado (novela, poesía, ensayo, etc.)")
    
    # Archivos y Multimedia
    imagen_autor: Optional[str] = Field(None, description="URL o ruta de imagen JPG del autor")
    audio_voz: Optional[str] = Field(None, description="URL o ruta de audio MP3 (voz del autor)")
    multimedia: List[Multimedia] = Field(default=[], description="Multimedia adicional: documentos, fotos, videos")
    
    # Relaciones
    obras: List[ObraSchema] = Field(default=[], description="Lista de obras escritas por el autor")
    criticas: List[CriticaSchema] = Field(default=[], description="Críticas y reseñas sobre el autor")

# ============================================================================
# AGRUPACIONES, REVISTAS, ANTOLOGÍAS
# ============================================================================

class AgrupacionSchema(BaseModel):
    """Agrupación o movimiento literario."""
    nombre: str = Field(description="Nombre de la agrupación")
    lugar_encuentros: Optional[Lugar] = Field(None, description="Lugar de encuentros")
    fecha_inicio: Optional[str] = Field(None, description="Fecha de inicio (YYYY)")
    fecha_culminacion: Optional[str] = Field(None, description="Fecha de fin (YYYY)")
    caracteristica_general: Optional[str] = Field(None, description="Tendencia, ideología, características")
    integrantes: List[Persona] = Field(default=[], description="Miembros de la agrupación")
    publicaciones: List[PublicacionAgrupacion] = Field(default=[], description="Obras publicadas por la agrupación")
    actividades: Optional[str] = Field(None, description="Descripción de actividades y encuentros")

class RevistaSchema(BaseModel):
    """Revista o publicación periódica."""
    titulo: str = Field(description="Título de la revista")
    fecha_primer_numero: Optional[str] = Field(None, description="Fecha del primer número (YYYY-MM)")
    fecha_ultimo_numero: Optional[str] = Field(None, description="Fecha del último número (YYYY-MM)")
    numeros_publicados: Optional[str] = Field(None, description="Descripción de números y volúmenes publicados")
    lugar_publicacion: Optional[Lugar] = Field(None, description="Lugar de publicación")
    editorial: Optional[str] = Field(None, description="Editorial o imprenta")
    creadores: List[Persona] = Field(default=[], description="Director, comité editorial, etc.")
    secciones: Optional[str] = Field(None, description="Secciones o categorías de contenido")
    descripcion: Optional[str] = Field(None, description="Temas, géneros predominantes, autores relevantes")
    idioma_original: str = Field(default="español", description="Idioma original de la revista")
    multimedia: List[Multimedia] = Field(default=[], description="PDF, portada JPG, etc. para descarga")

class AntologiaSchema(BaseModel):
    """Antología o colección de obras."""
    autor: Optional[str] = Field(None, description="Autor o editor de la antología")
    titulo: str = Field(description="Título de la antología")
    genero: str = Field(description="Género dominante: novela, cuento, poesía, ensayo")
    fecha_publicacion: str = Field(description="Año de publicación")
    lugar_publicacion: Optional[Lugar] = Field(None, description="Lugar de publicación")
    editorial: Optional[str] = Field(None, description="Editorial")
    descripcion: Optional[str] = Field(None, description="Descripción y autores seleccionados")
    idioma_original: str = Field(default="español", description="Idioma original")
    multimedia: List[Multimedia] = Field(default=[], description="PDF, portada JPG para descarga")

# ============================================================================
# MITOS Y LEYENDAS
# ============================================================================

class MitoLeyendaSchema(BaseModel):
    """Mito o leyenda tradicional de una comunidad."""
    titulo: str = Field(description="Título del mito o leyenda")
    comunidad_creadora: str = Field(description="Comunidad o pueblo que origina la narrativa")
    lugar_difusion: Optional[Lugar] = Field(None, description="Lugar de difusión principal")
    idioma_original: str = Field(description="Idioma original del mito")
    texto_completo: Optional[str] = Field(None, description="Texto completo del mito o leyenda")
    tema_principal: str = Field(description="Tema principal: cosmogonía, héroes, animales, etc.")
    descripcion: Optional[str] = Field(None, description="Descripción y análisis del mito")
    multimedia: List[Multimedia] = Field(default=[], description="Imágenes JPG, audio, video")

# ============================================================================
# FICHA COMPLETA
# ============================================================================

class FichaLiterariaSchema(BaseModel):
    """Ficha literaria completa que integra autor, obras, crítica y agrupaciones."""
    autor: AutorSchema = Field(description="Información completa del autor")
    
    # Colecciones y agrupaciones
    agrupaciones: List[AgrupacionSchema] = Field(default=[], description="Agrupaciones a las que perteneció")
    revistas: List[RevistaSchema] = Field(default=[], description="Revistas en las que participó")
    antologias: List[AntologiaSchema] = Field(default=[], description="Antologías que editó o en las que aparece")
    
    # Tradiciones culturales
    mitos_leyendas: List[MitoLeyendaSchema] = Field(default=[], description="Mitos o leyendas relacionados")
