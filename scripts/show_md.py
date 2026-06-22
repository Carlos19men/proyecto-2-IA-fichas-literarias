import sys
import os
from pathlib import Path

# Ensure workspace root on path for imports
sys.path.insert(0, os.getcwd())
from src.ingestion.preprocess import convert_to_markdown
from src.ingestion.loaders import leer_archivo_ficha

docx_rel = os.path.join('Diccionario','Diccionario','González de Alegría, Elisa','González de Alegría, Elisa.docx')
docx = os.path.join(os.getcwd(), docx_rel)
print('DOCX:', docx)
md = convert_to_markdown(docx)
print('MD PATH:', md)
print('\n---BEGIN TRANSCRIPTION (leer_archivo_ficha)---\n')
try:
    txt = leer_archivo_ficha(docx)
    print(txt)
except Exception as e:
    print('Error reading with leer_archivo_ficha:', e)
print('\n---END TRANSCRIPTION---\n')
