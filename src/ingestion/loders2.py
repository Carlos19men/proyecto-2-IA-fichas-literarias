from pathlib import Path
from typing import Dict, List, Tuple

from langchain_community.document_loaders import UnstructuredMarkdownLoader, Docx2txtLoader, PyPDFLoader

# ---------------------------------------------------------------------------
# Tipos de extensión por categoría
# ---------------------------------------------------------------------------
EXTENSIONES_TEXTO = {".md", ".docx", ".pdf"}
EXTENSIONES_IMAGEN = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
EXTENSIONES_AUDIO  = {".mp3", ".wav", ".ogg", ".m4a"}
EXTENSIONES_VIDEO  = {".mp4", ".avi", ".mov", ".mkv", ".webm"}

TODAS_LAS_EXTENSIONES = (
    EXTENSIONES_TEXTO | EXTENSIONES_IMAGEN | EXTENSIONES_AUDIO | EXTENSIONES_VIDEO
)


def leer_archivo_ficha(ruta_archivo: str) -> str:
    """
    Lee un archivo y devuelve su contenido como texto plano.

    - .md   → UnstructuredMarkdownLoader
    - .docx → Docx2txtLoader
    - .pdf  → PyPDFLoader (concatena todas las páginas)
    - imágenes / audio / video → retorna cadena vacía
      (estas rutas se manejan como multimedia, no como texto)
    """
    extension = Path(ruta_archivo).suffix.lower()

    if extension == ".md":
        loader = UnstructuredMarkdownLoader(ruta_archivo)
        documentos = loader.load()
        return documentos[0].page_content if documentos else ""

    elif extension == ".docx":
        loader = Docx2txtLoader(ruta_archivo)
        documentos = loader.load()
        return documentos[0].page_content if documentos else ""

    elif extension == ".pdf":
        loader = PyPDFLoader(ruta_archivo)
        documentos = loader.load()
        # Concatenar todas las páginas con salto de línea doble
        return "\n\n".join(doc.page_content for doc in documentos)

    elif extension in EXTENSIONES_IMAGEN | EXTENSIONES_AUDIO | EXTENSIONES_VIDEO:
        # No se extrae texto de multimedia; la ruta se registra como referencia
        return ""

    else:
        raise ValueError(
            f"❌ Formato de archivo no soportado: '{extension}'. "
            f"Formatos aceptados: .md, .docx, .pdf, "
            f".jpg/.png (imagen), .mp3/.wav (audio), .mp4/.mov (video)"
        )


def clasificar_archivo(ruta: str) -> str:
    """
    Devuelve el tipo de un archivo según su extensión.
    Valores posibles: 'texto', 'imagen', 'audio', 'video', 'desconocido'
    """
    ext = Path(ruta).suffix.lower()
    if ext in EXTENSIONES_TEXTO:
        return "texto"
    elif ext in EXTENSIONES_IMAGEN:
        return "imagen"
    elif ext in EXTENSIONES_AUDIO:
        return "audio"
    elif ext in EXTENSIONES_VIDEO:
        return "video"
    return "desconocido"


def escanear_carpeta_ficha(carpeta: str) -> Dict[str, List[str]]:
    """
    Escanea una carpeta y clasifica todos sus archivos por tipo.

    Retorna un diccionario con cuatro listas:
    {
        "texto":   [rutas de .md, .docx, .pdf],
        "imagen":  [rutas de .jpg, .png, ...],
        "audio":   [rutas de .mp3, .wav, ...],
        "video":   [rutas de .mp4, .mov, ...],
    }

    Útil para fichas que tienen archivos hermanos (ej. Montes, Ramón Isidro/
    que contiene .docx + .jpg + .pdf).
    """
    resultado: Dict[str, List[str]] = {
        "texto":  [],
        "imagen": [],
        "audio":  [],
        "video":  [],
    }

    carpeta_path = Path(carpeta)
    if not carpeta_path.is_dir():
        raise ValueError(f"❌ La ruta '{carpeta}' no es un directorio válido.")

    for archivo in sorted(carpeta_path.iterdir()):
        if archivo.is_file():
            tipo = clasificar_archivo(str(archivo))
            if tipo in resultado:
                resultado[tipo].append(str(archivo))

    return resultado


def leer_texto_principal(carpeta: str) -> Tuple[str, str]:
    """
    Dado un directorio de ficha, encuentra el archivo de texto principal
    (.docx preferido sobre .pdf, sobre .md) y lo lee.

    Retorna: (texto_plano, ruta_del_archivo_leído)
    Lanza ValueError si no hay ningún archivo de texto.
    """
    archivos = escanear_carpeta_ficha(carpeta)
    candidatos = archivos["texto"]

    if not candidatos:
        raise ValueError(f"❌ No se encontró ningún archivo de texto en '{carpeta}'.")

    # Orden de preferencia: .docx > .pdf > .md
    def prioridad(ruta: str) -> int:
        ext = Path(ruta).suffix.lower()
        return {".docx": 0, ".pdf": 1, ".md": 2}.get(ext, 99)

    candidatos_ordenados = sorted(candidatos, key=prioridad)
    ruta_principal = candidatos_ordenados[0]

    texto = leer_archivo_ficha(ruta_principal)
    return texto, ruta_principal