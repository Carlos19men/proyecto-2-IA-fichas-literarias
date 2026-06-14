from pydantic import BaseModel, Field
from typing import List, Optional

class LugarSchema(BaseModel):
    ciudad: Optional[str] = Field(None, description="Ciudad o municipio menor")
    municipio: Optional[str] = Field(None, description="Municipio político-territorial")
    estado: Optional[str] = Field(None, description="Estado o provincia")
    pais: Optional[str] = Field(None, description="País")

class ActividadRelevanteSchema(BaseModel):
    tipo: str = Field(description="Tipo de actividad (estudios, cargos, profesión)")
    lugar: Optional[str] = Field(None, description="Lugar donde se realizó la actividad")
    periodo: Optional[str] = Field(None, description="Periodo de tiempo en el que se realizó la actividad")

class FamiliarDestacadoSchema(BaseModel):
    nombre: str = Field(description="Nombre y apellido del familiar")
    parentesco: str = Field(description="Relación de parentesco (padre, madre, hermano, hijo, etc.)")

class MultimediaSchema(BaseModel):
    enlace: str = Field(description="Ruta, nombre de archivo o URL del recurso multimedia")
    tipo: str = Field(description="Tipo de archivo (imagen, audio, video, pdf, jpg, mp3)")
    restriccion: Optional[str] = Field(None, description="Restricción de acceso o derechos de autor")

class ObraSchema(BaseModel):
    titulo: str = Field(description="El título oficial de la obra literaria")
    genero: str = Field(description="Género de la obra (novela, cuento, poesía, ensayo, revista, antología). Incluir subgéneros.")
    fecha_publicacion: Optional[str] = Field(None, description="Fecha de publicación de la obra")
    lugar_publicacion: Optional[str] = Field(None, description="Lugar de publicación (ciudad, imprenta, editorial)")
    descripcion_resumen: Optional[str] = Field(None, description="Descripción o resumen de la obra. Para revistas o antologías, mencionar autores, temas, números...")
    idioma_original: str = Field(default="español", description="Idioma original de la obra")
    multimedia: List[MultimediaSchema] = Field(default=[], description="Lista de elementos multimedia asociados")
    archivo_pdf: Optional[str] = Field(None, description="Referencia o enlace al archivo PDF de la obra para descarga y lectura")
    portada_jpg: Optional[str] = Field(None, description="Referencia o enlace a la portada en JPG")
    audio_mp3: Optional[str] = Field(None, description="Referencia o enlace al archivo de audio en MP3")

class CriticaSchema(BaseModel):
    tipo: str = Field(description="Tipo de crítica (libro, artículo, reseña, trabajo de grado, etc.)")
    autor: str = Field(description="Nombre del crítico o investigador")
    titulo: str = Field(description="Título del trabajo de crítica")
    fecha_publicacion: Optional[str] = Field(None, description="Fecha de publicación de la crítica")
    referencia_bibliografica: str = Field(description="Referencia completa de dónde fue publicada (revista, libro, etc.) e incluye enlace si existe")
    enlace: Optional[str] = Field(None, description="Enlace directo a la crítica")
    descripcion_resumen: str = Field(description="Resumen o valoración principal que realiza la crítica")

class PublicacionAgrupacionSchema(BaseModel):
    titulo: str = Field(description="Título de la publicación")
    ano: Optional[str] = Field(None, description="Año de publicación")
    resumen: Optional[str] = Field(None, description="Resumen de la obra")

class AgrupacionSchema(BaseModel):
    nombre_agrupacion: str = Field(description="Nombre oficial de la agrupación literaria")
    lugar_encuentros: Optional[LugarSchema] = Field(None, description="Lugar geográfico donde se reunía la agrupación")
    fecha_inicio: Optional[str] = Field(None, description="Fecha de inicio o fundación")
    fecha_culminacion: Optional[str] = Field(None, description="Fecha de culminación o disolución")
    caracteristica_general: Optional[str] = Field(None, description="Tendencia ideológica, literaria o características generales")
    integrantes: List[str] = Field(default=[], description="Nombres y apellidos de los integrantes")
    publicaciones: List[PublicacionAgrupacionSchema] = Field(default=[], description="Lista de publicaciones de la agrupación")
    actividades: List[str] = Field(default=[], description="Actividades o eventos principales organizados por la agrupación")

class RevistaSchema(BaseModel):
    titulo: str = Field(description="Título de la revista")
    fecha_primer_numero: Optional[str] = Field(None, description="Fecha del primer número publicado")
    fecha_ultimo_numero: Optional[str] = Field(None, description="Fecha del último número publicado")
    numeros_publicados: Optional[str] = Field(None, description="Detalle de los números o cantidad publicados")
    lugar_publicacion: Optional[str] = Field(None, description="Lugar de publicación (ciudad, imprenta, editorial)")
    creadores: List[str] = Field(default=[], description="Listado de directores, comité editorial, fundadores, etc.")
    secciones_revista: List[str] = Field(default=[], description="Secciones principales de la revista")
    descripcion: Optional[str] = Field(None, description="Temas y géneros predominantes, autores relevantes")
    idioma_original: str = Field(default="español")
    multimedia: List[MultimediaSchema] = Field(default=[])
    archivo_pdf: Optional[str] = Field(None, description="Obra en archivo PDF para descarga y lectura")
    portada_jpg: Optional[str] = Field(None, description="Portada en JPG para descarga y lectura")

class AntologiaSchema(BaseModel):
    autor: Optional[str] = Field(None, description="Compilador o autor principal de la antología")
    titulo: str = Field(description="Título de la antología")
    genero: str = Field(description="Género predominante (novela, cuento, poesía, ensayo)")
    fecha_publicacion: Optional[str] = Field(None, description="Fecha de publicación")
    lugar_publicacion: Optional[str] = Field(None, description="Lugar de publicación (ciudad, imprenta, editorial)")
    descripcion_resumen: Optional[str] = Field(None, description="Descripción o resumen de la antología, mencionando autores seleccionados")
    idioma_original: str = Field(default="español")
    multimedia: List[MultimediaSchema] = Field(default=[])
    archivo_pdf: Optional[str] = Field(None, description="Obra en archivo PDF para descarga y lectura")
    portada_jpg: Optional[str] = Field(None, description="Portada en JPG")

class MitoLeyendaSchema(BaseModel):
    titulo: str = Field(description="Título del mito o leyenda")
    comunidad_creadora: Optional[str] = Field(None, description="Comunidad indígena, afrodescendiente o local creadora")
    lugar_difusion: Optional[LugarSchema] = Field(None, description="Lugares donde se difunde (pueblo, municipio, ciudad, estado)")
    idioma_original: Optional[str] = Field(None, description="Idioma original del mito o leyenda")
    texto_completo: str = Field(description="Texto completo narrativo del mito o leyenda")
    tema_principal: Optional[str] = Field(None, description="Tema o enseñanza principal")
    descripcion_resumen: Optional[str] = Field(None, description="Resumen o descripción breve del mito/leyenda")
    multimedia: List[MultimediaSchema] = Field(default=[], description="Obra en archivo JPG, audio o video")

class AutorSchema(BaseModel):
    # Identidad
    nombres: str = Field(description="Nombres del autor")
    apellidos: str = Field(description="Apellidos del autor")
    sexo: str = Field(description="Género o sexo del autor")
    seudonimo: Optional[str] = Field(None, description="Seudónimo literario")
    
    # Cronología y Ubicación
    fechaDeNacimiento: Optional[str] = Field(None, description="Fecha de nacimiento completa o aproximada")
    fechaDeFallecimiento: Optional[str] = Field(None, description="Fecha de fallecimiento completa (si aplica)")
    lugarDeNacimiento: Optional[LugarSchema] = Field(None, description="Ubicación detallada de nacimiento")
    lugarDeFallecimiento: Optional[LugarSchema] = Field(None, description="Ubicación detallada de fallecimiento")
    
    # Trayectoria y Entorno
    actividadRelevante: List[ActividadRelevanteSchema] = Field(default=[], description="Listado de estudios, cargos, profesiones, etc.")
    familiaresDestacados: List[FamiliarDestacadoSchema] = Field(default=[], description="Listado de parientes destacados")
    contextoEnQueVivio: Optional[str] = Field(None, description="Contexto histórico, social y geográfico")
    
    # Perfil Literario
    tematicaPrincipal: List[str] = Field(default=[], description="Temas centrales de su obra")
    generoPrincipal: str = Field(description="Género literario principal cultivado")
    
    # Archivos y Multimedia
    imagenAutor: Optional[str] = Field(None, description="Enlace o referencia a la imagen en JPG del autor")
    audioVoz: Optional[str] = Field(None, description="Enlace o referencia al audio en MP3 de la voz del autor")
    multimedia: List[MultimediaSchema] = Field(default=[], description="Otras referencias multimedia")

class FichaLiterariaSchema(BaseModel):
    autor: Optional[AutorSchema] = Field(None, description="Información completa del autor de la ficha")
    obras: List[ObraSchema] = Field(default=[], description="Obras creadas por el autor")
    criticas: List[CriticaSchema] = Field(default=[], description="Críticas recibidas sobre el autor o sus obras")
    agrupaciones: List[AgrupacionSchema] = Field(default=[], description="Agrupaciones literarias asociadas")
    revistas: List[RevistaSchema] = Field(default=[], description="Revistas asociadas")
    antologias: List[AntologiaSchema] = Field(default=[], description="Antologías asociadas")
    mitos_y_leyendas: List[MitoLeyendaSchema] = Field(default=[], description="Mitos y leyendas asociados")