from pydantic import BaseModel, Field

class ObraSchema(BaseModel):
    titulo: str = Field(description="El título oficial de la obra literaria")
    genero: str = Field(description="Género específico de la obra (ej: novela, drama de folletín)")
    fecha_publicacion: str = Field(description="Año de publicación (ej: 1883). Usa 'desconocida' si no aparece.")
    lugar_publicacion: str = Field(description="Ciudad o estado donde se publicó la obra")
    idioma_original: str = Field(description="Idioma original de la obra (ej: español)")

class CriticaSchema(BaseModel):
    tipo: str = Field(description="Tipo de crítica: libro, artículo, capítulo de libro, etc.")
    autor: str = Field(description="Nombre del crítico o investigador que escribe")
    titulo: str = Field(description="Título del artículo o libro de crítica")
    fecha_publicacion: str = Field(description="Año de publicación de la crítica")
    referencia_bibliografica: str = Field(description="Cita completa, editorial o URL de la publicación")
    descripcion_resumen: str = Field(description="Resumen corto de los hallazgos o lo que afirma la crítica")

class FichaLiterariaSchema(BaseModel):
    nombre_autor: str = Field(description="Nombre completo del autor (ej: Elisa González de Alegría)")
    sexo: str = Field(description="Femenino, masculino o desconocido")
    seudonimo: str = Field(description="Seudónimo literario utilizado por el autor. Si no tiene, usa 'Ninguno'.")
    fecha_nacimiento: str = Field(default="desconocida")
    fecha_fallecimiento: str = Field(default="desconocida")
    lugar_nacimiento: str = Field(default="desconocido")
    lugar_fallecimiento: str = Field(default="desconocido")
    contexto_vivio: str = Field(description="Ubicación geográfica y época donde residió el autor")
    actividad_relevante: str = Field(description="Texto biográfico extendido que narra la historia y relevancia del autor")
    tematica_principal: str = Field(description="Temas recurrentes en su obra (ej: drama folletinesco)")
    genero_principal: str = Field(description="Género macro que cultivó (ej: novela)")
    obras: list[ObraSchema] = Field(default=[])
    criticas: list[CriticaSchema] = Field(default=[])