"""
Parser determinístico para fichas de Revista con plantilla Word estándar.
"""

import re
from typing import Optional

from src.ingestion.autor_utils import normalizar_texto_plano


def es_ficha_revista(texto: str) -> bool:
    """Detecta plantilla de ficha de revista (no autor ni mitos)."""
    t = texto.strip().lower()
    if "comunidad creadora:" in t or "texto completo del mito" in t:
        return False
    if "nombres:" in t and "apellidos:" in t and "autor:" in t:
        return False
    return t.startswith("revista:") or (
        "revista:" in t[:80] and "fecha de primer" in t and "título:" in t
    )


def es_resultado_ficha_revista(ficha) -> bool:
    """True si la ficha procesada es de revista (no de autor)."""
    if not getattr(ficha, "revistas", None):
        return False
    autor = ficha.autor
    return (
        getattr(autor, "nombres", "") == "desconocido"
        and getattr(autor, "apellidos", "") == "desconocido"
        and not getattr(autor, "obras", None)
    )


def generar_resumen_revista(revista: dict) -> str:
    """Construye el campo `text` con un resumen de la revista."""
    partes: list[str] = []
    titulo = revista.get("titulo")
    if titulo:
        partes.append(f"Revista {titulo}.")
    if revista.get("fecha_primer_numero"):
        partes.append(f"Primer número: {revista['fecha_primer_numero']}.")
    if revista.get("fecha_ultimo_numero"):
        partes.append(f"Último número: {revista['fecha_ultimo_numero']}.")
    if revista.get("numeros_publicados"):
        partes.append(f"Números publicados: {revista['numeros_publicados']}.")
    if revista.get("lugar_publicacion"):
        lugar = revista["lugar_publicacion"]
        if isinstance(lugar, dict):
            lugar = ", ".join(v for v in lugar.values() if v)
        partes.append(f"Lugar de publicación: {lugar}.")
    editorial = revista.get("editorial")
    if editorial:
        lugar_txt = str(revista.get("lugar_publicacion") or "")
        if editorial != lugar_txt and editorial not in lugar_txt:
            partes.append(f"Editorial: {editorial}.")
    if revista.get("secciones"):
        partes.append(f"Secciones: {revista['secciones']}")
    creadores = revista.get("creadores") or []
    if creadores:
        nombres = []
        for c in creadores:
            if isinstance(c, dict):
                nombre = f"{c.get('nombres', '')} {c.get('apellidos', '')}".strip()
                rol = c.get("rol")
                nombres.append(f"{nombre} ({rol})" if rol else nombre)
        if nombres:
            partes.append(f"Creadores: {', '.join(nombres)}.")
    return normalizar_texto_plano(" ".join(partes))


def _extraer_campo(texto: str, etiquetas: list[str], hasta: str | None = None) -> Optional[str]:
    etiquetas_pat = "|".join(re.escape(e) for e in etiquetas)
    fin = hasta or (
        r"(?:\n\s*\n|\n(?:Título|Fecha|Números|N[uú]meros|Lugar|Creadores|Secciones|"
        r"Idioma|Multimedia|Obra|Cr[ií]tica|Tipo)\b)"
    )
    patron = rf"(?:{etiquetas_pat})\s*:?\s*(.+?)(?={fin})"
    m = re.search(patron, texto, flags=re.IGNORECASE | re.DOTALL)
    if not m:
        return None
    return re.sub(r"\s+", " ", m.group(1).strip())


def _parsear_creadores(linea: str) -> list[dict]:
    if not linea:
        return []
    creadores: list[dict] = []
    for m in re.finditer(
        r"([^:,]+?):\s*([^,]+?)(?=,\s*[^:,]+:|\.?\s*$)",
        linea,
        flags=re.DOTALL,
    ):
        rol = m.group(1).strip()
        nombre = m.group(2).strip().rstrip(".")
        partes = nombre.split()
        creadores.append({
            "nombres": partes[0] if partes else nombre,
            "apellidos": " ".join(partes[1:]) if len(partes) > 1 else "",
            "rol": rol,
        })
    return creadores


def _parsear_criticas(texto: str) -> list[dict]:
    m = re.search(r"Cr[ií]tica:\s*(.*)", texto, flags=re.IGNORECASE | re.DOTALL)
    if not m:
        return []

    criticas: list[dict] = []
    patron = (
        r"Tipo\s*\(([^)]+)\)\s*\n\s*Autor:\s*(.+?)\s*\n\s*"
        r"T[ií]tulo:\s*(.+?)\s*\n\s*"
        r"Fecha de publicaci[oó]n:\s*(.+?)\s*\n\s*"
        r"Referencia bibliogr[aá]fica[:\s]*(.+?)(?=\n\s*\n|\n\s*Tipo\s*\(|\Z)"
    )
    for m in re.finditer(patron, m.group(1), flags=re.IGNORECASE | re.DOTALL):
        criticas.append({
            "tipo": m.group(1).strip(),
            "autor": m.group(2).strip(),
            "titulo": m.group(3).strip().rstrip("."),
            "fecha_publicacion": m.group(4).strip(),
            "referencia_bibliografica": m.group(5).strip(),
        })
    return criticas


def parsear_ficha_revista_desde_texto(texto: str) -> Optional[dict]:
    """Construye el dict del schema a partir de la plantilla Word de revista."""
    if not es_ficha_revista(texto):
        return None

    titulo = _extraer_campo(texto, ["Título", "Titulo"])
    if not titulo:
        return None

    creadores_linea = _extraer_campo(texto, ["Creadores"]) or ""
    secciones = _extraer_campo(
        texto,
        ["Secciones de la revista", "Secciones"],
    )

    lugar_raw = _extraer_campo(texto, ["Lugar de publicación", "Lugar de publicacion"])
    editorial = None
    if lugar_raw and re.search(r"tipograf[ií]a|editorial|editado por", lugar_raw, re.I):
        editorial = lugar_raw

    revista = {
        "titulo": titulo,
        "fecha_primer_numero": _extraer_campo(texto, ["Fecha de primer número", "Fecha de primer numero"]),
        "fecha_ultimo_numero": _extraer_campo(texto, ["Fecha de último número", "Fecha de ultimo numero"]),
        "numeros_publicados": _extraer_campo(texto, ["Números publicados", "Numeros publicados"]),
        "lugar_publicacion": lugar_raw,
        "editorial": editorial,
        "creadores": _parsear_creadores(creadores_linea),
        "secciones": secciones,
        "descripcion": secciones,
        "idioma_original": (_extraer_campo(texto, ["Idioma original"]) or "español").rstrip("."),
        "multimedia": [],
    }
    revista["text"] = generar_resumen_revista(revista)

    return {
        "autor": {
            "nombres": "desconocido",
            "apellidos": "desconocido",
            "sexo": "desconocido",
            "genero_principal": "desconocido",
            "criticas": _parsear_criticas(texto),
            "obras": [],
            "multimedia": [],
        },
        "revistas": [revista],
        "agrupaciones": [],
        "antologias": [],
        "mitos_leyendas": [],
    }
