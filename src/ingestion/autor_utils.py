"""
Utilidades compartidas para fichas de autor: campos múltiples y resumen biográfico.
"""

import re
import unicodedata
from typing import Any, Optional


def _sin_tildes(texto: str) -> str:
    nfd = unicodedata.normalize("NFD", texto)
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn").lower()


# Estados de Venezuela (normalizados sin tildes)
_ESTADOS_VENEZUELA = {
    "amazonas", "anzoategui", "apure", "aragua", "barinas", "bolivar",
    "carabobo", "cojedes", "delta amacuro", "falcon", "guarico", "lara",
    "merida", "miranda", "monagas", "nueva esparta", "portuguesa", "sucre",
    "tachira", "trujillo", "vargas", "yaracuy", "zulia", "distrito capital",
    "guayana",
}

# Ciudades y localidades venezolanas frecuentes en las fichas
_CIUDADES_VENEZUELA = {
    "ciudad bolivar", "ciudad guayana", "puerto ordaz", "san felix", "upata",
    "caracas", "maracaibo", "valencia", "barquisimeto", "merida", "angostura",
    "coro", "cumana", "maturin", "el tigre", "anaco", "guanare",
    "san cristobal", "la victoria", "los teques", "barcelona", "heres",
}

# País explícito en cualquier componente del lugar
_PAISES_POR_TEXTO = {
    "venezuela": "Venezuela",
    "siria": "Siria",
    "syria": "Siria",
    "mexico": "México",
    "colombia": "Colombia",
    "brasil": "Brasil",
    "argentina": "Argentina",
    "chile": "Chile",
    "peru": "Perú",
    "cuba": "Cuba",
    "espana": "España",
    "spain": "España",
    "francia": "Francia",
    "italia": "Italia",
    "republica dominicana": "República Dominicana",
    "santo domingo": "República Dominicana",
    "estados unidos": "Estados Unidos",
    "eeuu": "Estados Unidos",
    "usa": "Estados Unidos",
}


def completar_pais_en_lugar(lugar: dict | None) -> dict | None:
    """
    Infiere `pais` cuando falta, a partir de ciudad, municipio o estado.
    Prioriza países explícitos en el texto; luego heurísticas venezolanas.
    """
    if not lugar or not isinstance(lugar, dict):
        return lugar
    if lugar.get("pais"):
        return lugar

    componentes = [
        lugar.get("ciudad"),
        lugar.get("municipio"),
        lugar.get("estado"),
    ]
    texto_completo = _sin_tildes(" ".join(str(c) for c in componentes if c))

    # País mencionado explícitamente en algún componente
    for clave, pais in _PAISES_POR_TEXTO.items():
        if clave in texto_completo:
            lugar["pais"] = pais
            return lugar

    # Estado venezolano (ej. "estado Bolívar" → bolivar)
    estado_raw = lugar.get("estado") or ""
    estado = _sin_tildes(str(estado_raw)).replace("estado ", "").strip()
    if estado in _ESTADOS_VENEZUELA or any(e in estado for e in _ESTADOS_VENEZUELA):
        lugar["pais"] = "Venezuela"
        return lugar

    # Ciudad o municipio venezolano
    for campo in componentes:
        if not campo:
            continue
        campo_norm = _sin_tildes(str(campo))
        for ciudad in _CIUDADES_VENEZUELA:
            if ciudad in campo_norm:
                lugar["pais"] = "Venezuela"
                return lugar

    # Siria: abreviatura "Siri" o nombres árabes frecuentes en fichas sirio-venezolanas
    if re.search(r"\bsiri\b", texto_completo) or "ayoum" in texto_completo:
        lugar["pais"] = "Siria"
        return lugar

    return lugar


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
