"""
Parser determinístico para fichas de Autor con plantilla Word estándar.

Cubre campos etiquetados (Nombres, Apellidos, Título, Género, Crítica, etc.)
y complementa revistas con heurísticas del texto plano.
"""

import re
from typing import Optional

from src.ingestion.json_adapter import extraer_revistas_del_texto
from src.ingestion.autor_utils import (
    extraer_actividad_relevante,
    extraer_perfil_literario,
    generar_resumen_autor,
)


def es_ficha_autor(texto: str) -> bool:
    """Detecta plantilla de ficha de autor (no mitos/leyendas)."""
    t = texto.lower()
    if "comunidad creadora:" in t or "texto completo del mito" in t:
        return False
    return "nombres:" in t and "apellidos:" in t and "autor:" in t


def _extraer_campo(texto: str, etiquetas: list[str], hasta: str | None = None) -> Optional[str]:
    etiquetas_pat = "|".join(re.escape(e) for e in etiquetas)
    fin = hasta or r"(?:\n\s*\n|\n(?:Nombres|Apellidos|Fecha|Título|Género|Crítica|Obra|Sexo|Lugar|Actividad)\b)"
    patron = rf"(?:{etiquetas_pat})\s*:?\s*(.+?)(?={fin})"
    m = re.search(patron, texto, flags=re.IGNORECASE | re.DOTALL)
    if not m:
        return None
    return re.sub(r"\s+", " ", m.group(1).strip())


def _parsear_obras(texto: str) -> list[dict]:
    m_critica = re.search(r"\n\s*Cr[ií]tica\s*:", texto, flags=re.IGNORECASE)
    seccion = texto[: m_critica.start()] if m_critica else texto

    obras: list[dict] = []
    patron = (
        r"T[ií]tulo:\s*(.+?)\s*\n\s*G[eé]nero:\s*(.+?)\s*\n\s*"
        r"Fecha de publicaci[oó]n:\s*(.+?)\s*\n\s*"
        r"Lugar de publicaci[oó]n:\s*(.+?)\s*\n\s*"
        r"(?:Editorial|Imprenta):\s*(.+?)\s*\n\s*"
        r"Idioma original:\s*(.+?)(?=\n\s*\n|\n\s*T[ií]tulo:|\Z)"
    )
    for m in re.finditer(patron, seccion, flags=re.IGNORECASE | re.DOTALL):
        obras.append({
            "titulo": m.group(1).strip(),
            "genero": m.group(2).strip().rstrip("."),
            "fecha_publicacion": m.group(3).strip(),
            "lugar_publicacion": m.group(4).strip(),
            "editorial": m.group(5).strip(),
            "idioma_original": m.group(6).strip(),
            "multimedia": [],
        })
    return obras


def _parsear_criticas(texto: str) -> list[dict]:
    m = re.search(r"Cr[ií]tica:\s*(.*)", texto, flags=re.IGNORECASE | re.DOTALL)
    if not m:
        return []

    criticas: list[dict] = []
    bloque = m.group(1).strip()
    parrafos = re.split(r"\n\s*\n+", bloque)

    for p in parrafos:
        p = p.strip()
        if not p:
            continue
        if re.match(r"Revista\s+", p, flags=re.IGNORECASE):
            continue

        m_bib = re.match(
            r"^([^(]+?)\s*\((\d{4})\)\.\s*(.+)$",
            p,
            flags=re.DOTALL,
        )
        if m_bib:
            autor = m_bib.group(1).strip().rstrip(",")
            titulo = m_bib.group(3).strip()
            titulo = re.sub(r"^[«\"](.+?)[»\"]\.?\s*", r"\1. ", titulo).strip()
            criticas.append({
                "tipo": "reseña",
                "autor": autor,
                "titulo": titulo.split(".")[0].strip() if titulo else "sin título",
                "fecha_publicacion": m_bib.group(2),
                "referencia_bibliografica": titulo,
            })
            continue

        if re.match(r"^[A-ZÁÉÍÓÚÑ][^\n.]+\.\s*Revista\s+de\s+", p, flags=re.IGNORECASE):
            continue

    return criticas


def _parsear_agrupaciones(texto: str) -> list[dict]:
    agrupaciones: list[dict] = []
    for m in re.finditer(
        r"grupo\s+literario\s+([^(\n]+)\s*\(\s*integrado\s+por\s+([^)]+)\)",
        texto,
        flags=re.IGNORECASE,
    ):
        nombre = m.group(1).strip()
        miembros_raw = m.group(2)
        integrantes = []
        for nombre_miembro in re.split(r",\s*y\s+|,\s*", miembros_raw):
            nombre_miembro = nombre_miembro.strip()
            if not nombre_miembro:
                continue
            partes = nombre_miembro.split()
            integrantes.append({
                "nombres": partes[0] if partes else nombre_miembro,
                "apellidos": " ".join(partes[1:]) if len(partes) > 1 else "",
                "rol": "integrante",
            })
        agrupaciones.append({
            "nombre": nombre,
            "integrantes": integrantes,
            "caracteristica_general": None,
        })
    return agrupaciones


def parsear_ficha_autor_desde_texto(texto: str) -> Optional[dict]:
    """Construye el dict del schema a partir de la plantilla Word de autor."""
    if not es_ficha_autor(texto):
        return None

    nombres = _extraer_campo(texto, ["Nombres"]) or "desconocido"
    apellidos = _extraer_campo(texto, ["Apellidos"]) or "desconocido"
    if nombres == "desconocido" and apellidos == "desconocido":
        return None

    obras = _parsear_obras(texto)
    criticas = _parsear_criticas(texto)
    agrupaciones = _parsear_agrupaciones(texto)
    revistas = extraer_revistas_del_texto(texto)
    perfil = extraer_perfil_literario(texto)
    actividad = extraer_actividad_relevante(texto) or _extraer_campo(
        texto,
        ["Actividad relevante que haya realizado el autor", "Actividad relevante"],
    ) or ""

    autor = {
        "nombres": nombres,
        "apellidos": apellidos,
        "sexo": _extraer_campo(texto, ["Sexo"]) or "desconocido",
        "fecha_nacimiento": _extraer_campo(texto, ["Fecha de nacimiento"]),
        "fecha_fallecimiento": _extraer_campo(texto, ["Fecha de fallecimiento", "Fecha de muerte"]),
        "lugar_nacimiento": _extraer_campo(texto, ["Lugar de nacimiento"]),
        "lugar_fallecimiento": _extraer_campo(texto, ["Lugar de fallecimiento"]),
        "actividad_relevante": actividad,
        "contexto_vivio": perfil.get("contexto_vivio"),
        "tematica_principal": perfil.get("tematica_principal"),
        "genero_principal": perfil.get("genero_principal") or "desconocido",
        "seudonimo": perfil.get("seudonimo"),
        "criticas": criticas,
        "obras": obras,
        "multimedia": [],
    }
    autor["text"] = generar_resumen_autor(autor)

    return {
        "autor": autor,
        "revistas": revistas,
        "agrupaciones": agrupaciones,
        "antologias": [],
        "mitos_leyendas": [],
    }
