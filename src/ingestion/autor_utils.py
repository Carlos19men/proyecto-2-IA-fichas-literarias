"""
Utilidades compartidas para fichas de autor: campos múltiples y resumen biográfico.
"""

import re
from typing import Any, Optional


def normalizar_texto_plano(texto: Any) -> str:
    """Colapsa saltos de línea y espacios múltiples en un párrafo continuo."""
    if texto is None:
        return ""
    return re.sub(r"\s+", " ", str(texto).strip())


def unir_valores_multiples(val: Any, separador: str = ", ") -> Optional[str]:
    """Normaliza listas o cadenas con varios valores en un solo string."""
    if val is None:
        return None
    if isinstance(val, list):
        partes = [str(v).strip() for v in val if v and str(v).strip()]
        return separador.join(partes) if partes else None
    texto = str(val).strip()
    if not texto:
        return None
    # Unificar separadores habituales en plantillas Word
    partes = re.split(r"\s*[,;/]\s*|\s+y\s+", texto)
    partes = [p.strip().rstrip(".") for p in partes if p.strip()]
    if len(partes) <= 1:
        return texto.rstrip(".")
    return separador.join(partes)


def generar_resumen_autor(autor: Any) -> str:
    """Construye el campo `text` con un resumen biográfico del autor."""
    if isinstance(autor, dict):
        get = autor.get
    else:
        get = lambda k, d=None: getattr(autor, k, d)

    def _frase(texto: str) -> str:
        t = texto.strip()
        if t and t[-1] not in ".!?":
            t += "."
        return t

    partes: list[str] = []
    nombre = f"{get('nombres', '') or ''} {get('apellidos', '') or ''}".strip()
    if nombre and nombre != "desconocido desconocido":
        partes.append(_frase(nombre))

    seudonimo = get("seudonimo")
    if seudonimo:
        partes.append(_frase(f"Conocido como {seudonimo}"))

    actividad = get("actividad_relevante")
    if actividad:
        partes.append(normalizar_texto_plano(actividad))

    contexto = get("contexto_vivio")
    if contexto:
        partes.append(_frase(f"Vivió en el contexto: {contexto}"))

    tematica = get("tematica_principal")
    if tematica:
        partes.append(_frase(f"Temas principales: {tematica}"))

    genero = get("genero_principal")
    if genero and genero != "desconocido":
        partes.append(_frase(f"Géneros cultivados: {genero}"))

    return normalizar_texto_plano(" ".join(p for p in partes if p))


def extraer_perfil_literario(texto: str) -> dict[str, Optional[str]]:
    """Extrae campos de perfil literario desde etiquetas de la plantilla Word."""
    resultado: dict[str, Optional[str]] = {
        "genero_principal": None,
        "tematica_principal": None,
        "contexto_vivio": None,
        "seudonimo": None,
    }

    m = re.search(
        r"G[eé]nero principal cultivado:\s*(.+?)(?=\n\s*\n|\nObras\s*:|\n\s*Cr[ií]tica\s*:|\Z)",
        texto,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if m:
        resultado["genero_principal"] = unir_valores_multiples(m.group(1))

    m = re.search(
        r"Tem[aá]tica principal desarrollada[^:]*:\s*(.+?)(?=\n\s*\n|\nG[eé]nero principal|\nObras\s*:|\Z)",
        texto,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if m:
        resultado["tematica_principal"] = m.group(1).strip().rstrip(".")

    m = re.search(
        r"Contexto en que viv[ióó]:\s*(.+?)(?=\n\s*\n|\nTem[aá]tica|\nG[eé]nero principal|\nActividad|\Z)",
        texto,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if m:
        resultado["contexto_vivio"] = m.group(1).strip().rstrip(".")

    m = re.search(
        r"Seud[oó]nimo:\s*(.+?)(?=\n\s*\n|\n(?:Nombres|Apellidos|Fecha|Sexo|Actividad|Contexto|Tem[aá]tica|G[eé]nero)\b)",
        texto,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if m:
        resultado["seudonimo"] = unir_valores_multiples(m.group(1))

    return resultado


def extraer_actividad_relevante(texto: str) -> Optional[str]:
    """Extrae la biografía completa hasta Temática/Género/Obras."""
    m = re.search(
        r"Actividad relevante[^:]*:\s*(.+?)(?=\n\s*Tem[aá]tica principal|\n\s*G[eé]nero principal|\n\s*Obras\s*:|\n\s*Cr[ií]tica\s*:|\Z)",
        texto,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not m:
        return None
    return normalizar_texto_plano(m.group(1))
