"""
Parser determinístico para fichas de Mitos y Leyendas (.docx con plantilla fija).

Se usa como fallback cuando el LLM devuelve JSON inválido o vacío (p. ej. con qwen2.5:3b).
"""

import re
import unicodedata
from typing import Optional


def _normalizar_clave(clave: str) -> str:
    clave = unicodedata.normalize("NFKD", clave).encode("ascii", "ignore").decode("ascii")
    return clave.lower().strip().rstrip(":")


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


def _parsear_nombre_recopilador(texto: str) -> tuple[str, str]:
    """Intenta obtener nombres/apellidos del recopilador mencionado en la ficha."""
    m = re.search(
        r"(?:por el |por )\s*(Fray\s+Ces[aá]reo)\s+(de\s+Armellada)",
        texto,
        flags=re.IGNORECASE,
    )
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return "desconocido", "desconocido"


def parsear_ficha_mitos_desde_texto(texto: str) -> Optional[dict]:
    """
    Parsea la plantilla Word de mitos/leyendas y devuelve un dict compatible
    con normalizar_json_antes_de_pydantic / FichaLiterariaSchema.
    """
    if not es_ficha_mitos(texto):
        return None

    titulo = _extraer_campo(texto, ["Título", "Titulo"])
    comunidad = _extraer_campo(texto, ["Comunidad creadora"])
    lugar = _extraer_campo(texto, ["Lugar de difusión", "Lugar de difusion"])
    idioma = _extraer_campo(texto, ["Idioma original"])
    texto_mito = _extraer_campo(
        texto,
        ["Texto completo del mito o leyenda", "Texto completo del mito", "Texto del mito"],
        hasta=r"\n\s*\n\s*(?:Tema principal|Descripción|Multimedia|Obra|Crítica)\b",
    )
    tema = _extraer_campo(
        texto,
        ["Tema principal del mito o leyenda", "Tema principal"],
    )
    descripcion = _extraer_campo(
        texto,
        ["Descripción o resumen", "Descripcion o resumen", "Descripción", "Descripcion"],
        hasta=r"\n\s*\n\s*(?:Multimedia|Obra|Crítica)\b",
    )

    if not titulo and not comunidad:
        return None

    nombres, apellidos = _parsear_nombre_recopilador(texto)
    actividad = ""
    if descripcion:
        m_act = re.search(r"Recogido por vez primera por[^.]+\.", descripcion, flags=re.IGNORECASE)
        if m_act:
            actividad = m_act.group(0).strip()

    critica_desc = _extraer_campo(
        texto,
        ["Descripción o resumen de la crítica", "Descripcion o resumen de la critica"],
    )
    critica_autor = None
    critica_titulo = None
    critica_fecha = None
    critica_ref = None
    m_crit = re.search(
        r"Cr[ií]tica:\s*(.*?)(?:\Z)",
        texto,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if m_crit:
        bloque = m_crit.group(1)
        m_aut = re.search(r"Autor:\s*(.+?)(?:\n\s*\n|\nT[ií]tulo:)", bloque, flags=re.IGNORECASE | re.DOTALL)
        if m_aut:
            critica_autor = m_aut.group(1).strip()
        m_tit = re.search(r"T[ií]tulo:\s*(.+?)(?:\n\s*\n|\nFecha|\nReferencia|\nDescripci)", bloque, flags=re.IGNORECASE | re.DOTALL)
        if m_tit:
            critica_titulo = m_tit.group(1).strip()
        m_fec = re.search(r"Fecha de publicaci[oó]n:\s*(.+?)(?:\n\s*\n|\nReferencia|\nDescripci)", bloque, flags=re.IGNORECASE | re.DOTALL)
        if m_fec:
            critica_fecha = m_fec.group(1).strip()
        m_ref = re.search(r"Referencia bibliogr[aá]fica:\s*(.+?)(?:\n\s*\n|\nDescripci)", bloque, flags=re.IGNORECASE | re.DOTALL)
        if m_ref:
            critica_ref = m_ref.group(1).strip()

    criticas = []
    if critica_titulo or critica_desc:
        criticas.append({
            "tipo": "libro",
            "autor": critica_autor or "desconocido",
            "titulo": critica_titulo or "sin título",
            "fecha_publicacion": str(critica_fecha or "desconocida"),
            "referencia_bibliografica": critica_ref or "no disponible",
            "descripcion_resumen": critica_desc,
        })

    return {
        "autor": {
            "nombres": nombres,
            "apellidos": apellidos,
            "sexo": "desconocido",
            "actividad_relevante": actividad,
            "tematica_principal": tema or "Mitología indígena",
            "genero_principal": "mito/leyenda",
            "criticas": criticas,
            "obras": [],
            "multimedia": [],
        },
        "mitos_leyendas": [{
            "titulo": titulo or "mito sin título",
            "comunidad_creadora": comunidad or "desconocida",
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

    mito = {
        "titulo": str(titulo or "mito sin título"),
        "comunidad_creadora": str(flat.get("comunidad creadora") or flat.get("pueblo de origen") or "desconocida"),
        "lugar_difusion": flat.get("lugar de difusion") or flat.get("lugar de difusion"),
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

    for clave in list(data.keys()):
        if _normalizar_clave(str(clave)) in flat and clave not in reservadas:
            data.pop(clave, None)

    return data
