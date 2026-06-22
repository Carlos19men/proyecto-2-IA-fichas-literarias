import os
import json
from datetime import datetime
from typing import Tuple

from src.ingestion.schemas import FichaLiterariaSchema, CriticaSchema, ObraSchema


def _text_corpus_from_chunks(chunks) -> str:
    parts = []
    for c in chunks:
        texto = getattr(c, "texto", None) if not isinstance(c, dict) else c.get("texto", "")
        if texto:
            parts.append(texto.lower())
    return "\n".join(parts)


def validate_ficha_evidence(ficha: FichaLiterariaSchema) -> Tuple[FichaLiterariaSchema, dict]:
    """Valida que obras y críticas extraídas tengan evidencia en los chunks.

    - Busca coincidencias simples (case-insensitive) del título, autor o fragmentos
      de la referencia dentro del corpus de chunks.
    - Elimina las entradas que no muestran evidencia y guarda un reporte en `logs/`.

    Devuelve la ficha (posiblemente modificada) y un diccionario resumen.
    """
    corpus = _text_corpus_from_chunks(ficha.chunks)
    removed = {"obras": [], "criticas": []}

    # Validar obras
    obras_final = []
    for obra in ficha.autor.obras:
        titulo = (obra.titulo or "").lower()
        descripcion = (obra.descripcion or "").lower()
        found = False
        if titulo and titulo in corpus:
            found = True
        elif descripcion and descripcion[:40] and descripcion[:40] in corpus:
            found = True

        if found:
            obras_final.append(obra)
        else:
            removed["obras"].append({"titulo": obra.titulo, "motivo": "sin evidencia en chunks"})

    # Validar críticas
    criticas_final = []
    for critica in ficha.autor.criticas:
        autor = (critica.autor or "").lower()
        titulo = (critica.titulo or "").lower()
        referencia = (critica.referencia_bibliografica or "").lower()
        descripcion = (critica.descripcion_resumen or "").lower()
        found = False
        for term in (autor, titulo, referencia, descripcion[:60] if descripcion else ""):
            if term and term in corpus:
                found = True
                break

        if found:
            criticas_final.append(critica)
        else:
            removed["criticas"].append({"titulo": critica.titulo, "autor": critica.autor, "motivo": "sin evidencia en chunks"})

    ficha.autor.obras = obras_final
    ficha.autor.criticas = criticas_final

    # Volcar reporte
    try:
        logs_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        fname = f"validation_report_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.json"
        path = os.path.join(logs_dir, fname)
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "ficha_autor": f"{ficha.autor.nombres} {ficha.autor.apellidos}",
            "removed": removed,
        }
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(report, ensure_ascii=False, indent=2))
        print(f"⚠️  Validation report written to: {path}")
    except Exception as e:
        print(f"⚠️  No se pudo escribir el reporte de validación: {e}")

    return ficha, removed
