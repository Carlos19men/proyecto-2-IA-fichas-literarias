"""
Parser determinístico para fichas de Mitos y Leyendas (.docx con plantilla fija).

Lee únicamente la sección del mito (hasta Obra/Crítica) del archivo de ejemplo.
La plantilla vacía «Ficha mitos y leyendas.docx» no se usa como fuente de datos.
"""

import re
import unicodedata
from typing import Optional


def _normalizar_clave(clave: str) -> str:
    clave = unicodedata.normalize("NFKD", clave).encode("ascii", "ignore").decode("ascii")
    return clave.lower().strip().rstrip(":")


def _texto_solo_seccion_mito(texto: str) -> str:
    """Corta el documento antes de las secciones Obra / Crítica (metadatos bibliográficos)."""
    m = re.search(r"\n\s*(?:Obra|Cr[ií]tica)\s*:", texto, flags=re.IGNORECASE)
    if m:
        return texto[: m.start()]
    return texto


def _extraer_campo(texto: str, etiquetas: list[str], hasta: str | None = None) -> Optional[str]:
    """Extrae el valor tras una etiqueta conocida hasta la siguiente sección."""
    etiquetas_pat = "|".join(re.escape(e) for e in etiquetas)
    fin = hasta or r"(?:\n\s*\n|\n(?:Título|Comunidad|Lugar|Idioma|Texto completo|Tema principal|Descripción|Multimedia|Obra|Crítica)\b)"
    patron = rf"(?:{etiquetas_pat})\s*:?\s*(.+?)(?={fin})"
    m = re.search(patron, texto, flags=re.IGNORECASE | re.DOTALL)
    if not m:
        return None
    return re.sub(r"\s+", " ", m.group(1).strip())


def es_ficha_mitos(texto: str) -> bool:
    t = texto.lower()
    return "mitos y leyendas" in t or (
        "titulo:" in t and "comunidad creadora:" in t and "texto completo del mito" in t
    )


def es_plantilla_vacia(texto: str) -> bool:
    """Detecta la plantilla sin datos (solo etiquetas vacías)."""
    if not es_ficha_mitos(texto):
        return False
    titulo = _extraer_campo(texto, ["Título", "Titulo"])
    comunidad = _extraer_campo(texto, ["Comunidad creadora"])
    texto_mito = _extraer_campo(
        texto,
        ["Texto completo del mito o leyenda", "Texto completo del mito", "Texto del mito"],
    )
    return not titulo and not comunidad and (not texto_mito or len(texto_mito) < 80)


def _parsear_obra_bibliografica(texto: str) -> Optional[dict]:
    """Extrae la línea Obra: (referencia bibliográfica del relato)."""
    m = re.search(
        r"Obra:\s*(.+?)(?=\n\s*\n|\n\s*Cr[ií]tica\s*:|\Z)",
        texto,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not m:
        return None
    linea = re.sub(r"\s+", " ", m.group(1).strip())
    fecha = None
    m_fecha = re.search(r"\b(19|20)\d{2}\b", linea)
    if m_fecha:
        fecha = m_fecha.group(0)
    return {"linea": linea, "fecha_publicacion": fecha or "desconocida"}


def _parsear_critica_bibliografica(texto: str) -> Optional[dict]:
    """Extrae la sección Crítica: del Word (reseña bibliográfica, no el mito)."""
    m = re.search(r"Cr[ií]tica:\s*(.*?)(?:\Z)", texto, flags=re.IGNORECASE | re.DOTALL)
    if not m:
        return None
    bloque = m.group(1)
    critica_autor = None
    critica_titulo = None
    critica_fecha = None
    critica_ref = None
    critica_desc = None

    m_aut = re.search(r"Autor:\s*(.+?)(?:\n\s*\n|\nT[ií]tulo:)", bloque, flags=re.IGNORECASE | re.DOTALL)
    if m_aut:
        critica_autor = m_aut.group(1).strip()
    m_tit = re.search(
        r"T[ií]tulo:\s*(.+?)(?:\n\s*\n|\nFecha|\nReferencia|\nDescripci)",
        bloque,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if m_tit:
        critica_titulo = m_tit.group(1).strip()
    m_fec = re.search(
        r"Fecha de publicaci[oó]n:\s*(.+?)(?:\n\s*\n|\nReferencia|\nDescripci)",
        bloque,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if m_fec:
        critica_fecha = m_fec.group(1).strip()
    m_ref = re.search(
        r"Referencia bibliogr[aá]fica:\s*(.+?)(?:\n\s*\n|\nDescripci)",
        bloque,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if m_ref:
        critica_ref = m_ref.group(1).strip()
    m_desc = re.search(
        r"Descripci[oó]n o resumen de la cr[ií]tica:\s*(.+?)(?:\Z)",
        bloque,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if m_desc:
        critica_desc = re.sub(r"\s+", " ", m_desc.group(1).strip())

    if not critica_titulo and not critica_desc:
        return None

    return {
        "tipo": "libro",
        "autor": critica_autor or "desconocido",
        "titulo": critica_titulo or "sin título",
        "fecha_publicacion": str(critica_fecha or "desconocida"),
        "referencia_bibliografica": critica_ref or "no disponible",
        "descripcion_resumen": critica_desc,
    }


def parsear_ficha_mitos_desde_texto(texto: str) -> Optional[dict]:
    """
    Parsea la plantilla Word de mitos/leyendas y devuelve un dict compatible
    con normalizar_json_antes_de_pydantic / FichaLiterariaSchema.

    Solo extrae campos del mito en mitos_leyendas.
    Además rellena autor.obras (título del mito) y autor.criticas (sección Crítica del Word).
    """
    if not es_ficha_mitos(texto) or es_plantilla_vacia(texto):
        return None

    seccion = _texto_solo_seccion_mito(texto)

    titulo = _extraer_campo(seccion, ["Título", "Titulo"])
    comunidad = _extraer_campo(seccion, ["Comunidad creadora"])
    lugar = _extraer_campo(seccion, ["Lugar de difusión", "Lugar de difusion"])
    idioma = _extraer_campo(seccion, ["Idioma original"])
    texto_mito = _extraer_campo(
        seccion,
        ["Texto completo del mito o leyenda", "Texto completo del mito", "Texto del mito"],
        hasta=r"\n\s*\n\s*(?:Tema principal|Descripción|Multimedia)\b",
    )
    tema = _extraer_campo(
        seccion,
        ["Tema principal del mito o leyenda", "Tema principal"],
    )
    descripcion = _extraer_campo(
        seccion,
        ["Descripción o resumen", "Descripcion o resumen"],
        hasta=r"\n\s*\n\s*(?:Multimedia)\b",
    )

    if not titulo and not comunidad:
        return None

    # Autor mínimo requerido por el schema: representa la comunidad creadora
    comunidad_str = (comunidad or "desconocida").strip()
    titulo_mito = titulo or "mito sin título"

    obra_bib = _parsear_obra_bibliografica(texto)
    critica = _parsear_critica_bibliografica(texto)

    obras = [{
        "titulo": titulo_mito,
        "genero": "mito/leyenda",
        "fecha_publicacion": (obra_bib or {}).get("fecha_publicacion", "desconocida"),
        "descripcion": descripcion,
        "idioma_original": idioma or "español",
        "multimedia": [],
    }]

    criticas = [critica] if critica else []

    return {
        "autor": {
            "nombres": comunidad_str,
            "apellidos": "comunidad creadora",
            "sexo": "no aplica",
            "actividad_relevante": "",
            "tematica_principal": tema or "Mitología y tradición oral",
            "genero_principal": "mito/leyenda",
            "criticas": criticas,
            "obras": obras,
            "multimedia": [],
        },
        "mitos_leyendas": [{
            "titulo": titulo_mito,
            "comunidad_creadora": comunidad_str,
            "lugar_difusion": lugar,
            "idioma_original": idioma or "español",
            "texto_completo": texto_mito,
            "tema_principal": tema or "desconocido",
            "descripcion": descripcion,
            "multimedia": [],
        }],
    }


def mapear_claves_planas_mito(data: dict) -> dict:
    """
    Convierte claves planas del LLM (Título, Comunidad creadora, etc.)
    en la lista mitos_leyendas del schema.
    """
    if not isinstance(data, dict) or data.get("mitos_leyendas"):
        return data

    flat: dict[str, object] = {}
    reservadas = {
        "autor", "obra", "obras", "critica", "criticas",
        "agrupaciones", "revistas", "antologias", "mitos_leyendas", "chunks",
    }
    for clave, valor in data.items():
        if clave in reservadas or valor is None:
            continue
        nk = _normalizar_clave(str(clave))
        if nk not in reservadas:
            flat[nk] = valor

    titulo = flat.get("titulo") or flat.get("titulo del mito") or flat.get("titulo de la leyenda")
    if not titulo and "comunidad creadora" not in flat:
        return data

    comunidad = str(flat.get("comunidad creadora") or flat.get("pueblo de origen") or "desconocida")
    mito = {
        "titulo": str(titulo or "mito sin título"),
        "comunidad_creadora": comunidad,
        "lugar_difusion": flat.get("lugar de difusion"),
        "idioma_original": str(flat.get("idioma original") or flat.get("idioma original del mito") or "español"),
        "texto_completo": flat.get("texto completo del mito o leyenda") or flat.get("texto completo") or flat.get("texto del mito"),
        "tema_principal": str(
            flat.get("tema principal del mito o leyenda")
            or flat.get("tema principal")
            or flat.get("temas principales del mito")
            or "desconocido"
        ),
        "descripcion": flat.get("descripcion o resumen") or flat.get("descripcion del mito") or flat.get("descripcion"),
        "multimedia": [],
    }
    data["mitos_leyendas"] = [mito]

    if "autor" not in data or not isinstance(data.get("autor"), dict):
        data["autor"] = {
            "nombres": comunidad,
            "apellidos": "comunidad creadora",
            "sexo": "no aplica",
            "criticas": [],
            "obras": [],
            "multimedia": [],
        }
    data["autor"]["criticas"] = []

    for clave in list(data.keys()):
        if _normalizar_clave(str(clave)) in flat and clave not in reservadas:
            data.pop(clave, None)

    return data
