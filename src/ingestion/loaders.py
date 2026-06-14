import os
from langchain_community.document_loaders import UnstructuredMarkdownLoader, Docx2txtLoader

def leer_archivo_ficha(ruta_archivo: str) -> str:
    """
    Lee un archivo de Word o Markdown y devuelve su contenido como texto plano.
    """
    extension = os.path.splitext(ruta_archivo)[-1].lower()

    if extension == '.md':
        loader = UnstructuredMarkdownLoader(ruta_archivo)
    elif extension == '.docx':
        loader = Docx2txtLoader(ruta_archivo)
    else:
        raise ValueError(f"❌ Formato de archivo no soportado: {extension}. Usa .md o .docx")

    # LangChain carga el documento como una lista de objetos "Document"
    documentos = loader.load()

    # Extraemos solo el texto del primer documento
    texto_plano = documentos[0].page_content
    return texto_plano

