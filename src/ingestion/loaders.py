import os

from langchain_community.document_loaders import (
    UnstructuredMarkdownLoader, 
    Docx2txtLoader, 
    PyPDFLoader
)

def leer_archivo_ficha(ruta_archivo: str) -> str:
    """
    Lee un archivo de Word, Markdown, PDF o identifica metadatos de archivos 
    multimedia (imagen, audio, video) devolviendo una representación en texto plano.
    """
    if not os.path.exists(ruta_archivo):
        raise FileNotFoundError(f"❌ El archivo no existe en la ruta: {ruta_archivo}")

    extension = os.path.splitext(ruta_archivo)[-1].lower()

    # Carga de documentos de texto estructurado/no estructurado
    if extension == '.md':
        loader = UnstructuredMarkdownLoader(ruta_archivo)
        documentos = loader.load()
        texto_plano = "\n".join([doc.page_content for doc in documentos])
    elif extension == '.docx':
        loader = Docx2txtLoader(ruta_archivo)
        documentos = loader.load()
        texto_plano = "\n".join([doc.page_content for doc in documentos])
    elif extension == '.pdf':
        loader = PyPDFLoader(ruta_archivo)
        documentos = loader.load()
        # Concatenar el contenido de todas las páginas del PDF
        texto_plano = "\n".join([doc.page_content for doc in documentos])
    
    # Manejo de formatos multimedia (retornamos una referencia de texto plano)
    elif extension in ['.jpg', '.jpeg', '.png']:
        texto_plano = (
            f"[Archivo de Imagen Encontrado]\n"
            f"Nombre: {os.path.basename(ruta_archivo)}\n"
            f"Ruta: {ruta_archivo}\n"
            f"Tipo: imagen\n"
        )
    elif extension in ['.mp3', '.wav', '.m4a']:
        texto_plano = (
            f"[Archivo de Audio Encontrado]\n"
            f"Nombre: {os.path.basename(ruta_archivo)}\n"
            f"Ruta: {ruta_archivo}\n"
            f"Tipo: audio\n"
        )
    elif extension in ['.mp4', '.avi', '.mkv', '.mov']:
        texto_plano = (
            f"[Archivo de Video Encontrado]\n"
            f"Nombre: {os.path.basename(ruta_archivo)}\n"
            f"Ruta: {ruta_archivo}\n"
            f"Tipo: video\n"
        )
    else:
        raise ValueError(
            f"❌ Formato de archivo no soportado: {extension}. "
            f"Soporta .md, .docx, .pdf, imágenes (.jpg/.png), audio (.mp3/.wav) y video (.mp4)."
        )

    return texto_plano
