"""
Parser para fichas de autor en prosa (texto narrativo tipo Wikipedia).

Cubre aperturas como:
  Pepe Alemán, seudónimo de Federico León Madriz
  (Cumaná, Sucre, Venezuela, 1896-Puerto España, Trinidad y Tobago Británica, 1953),
  fue un escritor...
"""

import re
from typing import Optional

from src.ingestion.autor_utils import generar_resumen_autor, normalizar_texto_plano, resolver_sexo
from src.ingestion.mito_parser import es_ficha_mitos
from src.ingestion.revista_parser import es_ficha_revista
from src.ingestion.autor_parser import es_ficha_autor


def es_ficha_narrativa(texto: str) -> bool:
    """Detecta biografía en prosa (no plantilla Word ni mitos/revista)."""
    if es_ficha_mitos(texto) or es_ficha_revista(texto) or es_ficha_autor(texto):
        return False
    t = texto.strip().lower()
    return (
        "seudónimo de" in t
        or "seudonimo de" in t
        or ("nació en" in t and re.search(r"\b(18|19|20)\d{2}\b", texto) is not None)
        or ("fue un" in t[:400] and re.search(r"\(\s*[^)]+,\s*\d{4}\s*-", texto) is not None)
    )


def _limpiar_citas_wikipedia(texto: str) -> str:
    """Elimina referencias tipo [1], [6][7] o citas truncadas [7."""
    return re.sub(r"\[\d*\]?", "", texto)


def _split_nombre(nombre: str) -> tuple[str, str]:
    partes = nombre.strip().split()
    if len(partes) <= 1:
        return partes[0] if partes else "desconocido", "desconocido"
    return partes[0], " ".join(partes[1:])


def _parsear_lugar_fechas(lugar_fechas: str) -> tuple[Optional[str], Optional[dict], Optional[str], Optional[dict]]:
    """
    Parsea 'Cumaná, Sucre, Venezuela, 1896-Puerto España, Trinidad y Tobago Británica, 1953'
    → (fecha_nac, lugar_nac, fecha_fall, lugar_fall)
    """
    m = re.match(
        r"^(.+?),\s*(\d{4})\s*-\s*(.+?),\s*(\d{4})\s*$",
        lugar_fechas.strip(),
        flags=re.DOTALL,
    )
    if not m:
        return None, None, None, None

    def _lugar_desde_partes(parte_lugar: str) -> dict:
        partes = [p.strip() for p in parte_lugar.split(",") if p.strip()]
        if len(partes) >= 3:
            return {"ciudad": partes[0], "estado": partes[1], "pais": partes[2]}
        if len(partes) == 2:
            return {"ciudad": partes[0], "pais": partes[1]}
        return {"ciudad": partes[0]} if partes else {}

    lugar_nac_str, anio_nac, lugar_fall_str, anio_fall = m.groups()
    return anio_nac, _lugar_desde_partes(lugar_nac_str), anio_fall, _lugar_desde_partes(lugar_fall_str)


def _parsear_intro(texto: str) -> Optional[dict]:
    """Extrae seudónimo, nombre real, lugares, fechas y rol del primer párrafo."""
    intro = texto.strip().split("\n\n")[0]

    m = re.search(
        r"^(.+?),\s*seud[oó]nimo de\s+(.+?)\s*\(([^)]+)\)\s*,\s*fue\s+(.+?)(?:\.|$)",
        intro,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not m:
        m = re.search(
            r"^(.+?)\s*\(([^)]+)\)\s*,\s*fue\s+(.+?)(?:\.|$)",
            intro,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if not m:
            return None
        nombre_completo, lugar_fechas, rol = m.groups()
        seudonimo = None
    else:
        seudonimo, nombre_completo, lugar_fechas, rol = m.groups()

    nombres, apellidos = _split_nombre(nombre_completo)
    fecha_nac, lugar_nac, fecha_fall, lugar_fall = _parsear_lugar_fechas(lugar_fechas)

    rol = rol.strip().rstrip(".")
    rol = re.sub(r"^un\s+|^una\s+", "", rol, flags=re.IGNORECASE)
    genero = "desconocido"
    if "ciencia ficción" in rol.lower() or "ciencia ficcion" in rol.lower():
        genero = "novela de ciencia ficción"
    elif "poesía" in rol.lower() or "poeta" in rol.lower():
        genero = "poesía"
    elif "novela" in rol.lower():
        genero = "novela"

    return {
        "nombres": nombres,
        "apellidos": apellidos,
        "seudonimo": seudonimo.strip() if seudonimo else None,
        "fecha_nacimiento": fecha_nac,
        "lugar_nacimiento": lugar_nac,
        "fecha_fallecimiento": fecha_fall,
        "lugar_fallecimiento": lugar_fall,
        "actividad_rol": rol,
        "genero_principal": genero,
    }


def _texto_biografico(texto: str) -> str:
    """Cuerpo biográfico sin la sección final de obras."""
    m = re.search(r"\n\s*obras\s*:?\s*\n", texto, flags=re.IGNORECASE)
    cuerpo = texto[: m.start()] if m else texto
    # Quitar el primer párrafo (ya parseado como intro)
    partes = cuerpo.strip().split("\n\n", 1)
    return partes[1].strip() if len(partes) > 1 else ""


def _parsear_obras(texto: str) -> list[dict]:
    obras: list[dict] = []

    m = re.search(
        r"[UuúÚ]n[ií]ca novela,\s*([^,]+),\s*fue publicada por (?:la\s+)?(?:Editorial\s+)?(.+?)\s+en\s+(\d{4})",
        texto,
    )
    if m:
        editorial = m.group(2).strip().rstrip(".")
        obras.append({
            "titulo": m.group(1).strip(),
            "genero": "novela",
            "fecha_publicacion": m.group(3),
            "editorial": editorial,
            "lugar_publicacion": {"ciudad": "Caracas", "pais": "Venezuela"},
            "idioma_original": "español",
            "multimedia": [],
        })

    m_obras = re.search(r"\n\s*obras\s*:?\s*\n+(.*)", texto, flags=re.IGNORECASE | re.DOTALL)
    if m_obras:
        for linea in m_obras.group(1).strip().split("\n"):
            titulo = linea.strip()
            if not titulo:
                continue
            existente = next(
                (o for o in obras if o["titulo"].lower() == titulo.lower()),
                None,
            )
            if existente:
                continue
            obras.append({
                "titulo": titulo,
                "genero": "novela",
                "fecha_publicacion": "desconocida",
                "idioma_original": "español",
                "multimedia": [],
            })

    return obras


def _parsear_integrantes(miembros_txt: str) -> list[dict]:
    integrantes: list[dict] = []
    miembros_txt = re.split(r",\s*llegado\b", miembros_txt, maxsplit=1)[0]
    for parte in re.split(r"\s+y\s+", miembros_txt):
        parte = parte.strip().rstrip(".")
        if not parte or len(parte) < 3:
            continue
        alias = None
        m_alias = re.search(r"\((?:conocido como|alias)\s+([^)]+)\)", parte, flags=re.I)
        if m_alias:
            alias = m_alias.group(1).strip()
            parte = re.sub(r"\s*\([^)]+\)", "", parte).strip()
        n, a = _split_nombre(parte)
        integrantes.append({
            "nombres": n,
            "apellidos": a,
            "rol": f"integrante ({alias})" if alias else "integrante",
        })
    return integrantes


def _parsear_agrupaciones(texto: str) -> list[dict]:
    agrupaciones: list[dict] = []
    for m in re.finditer(
        r'grupo\s+["\u201c]([^"\u201d]+)["\u201d]\s+encargado de\s+([^,]+(?:,\s*[^,]+)*?),\s*junto con\s+([^.]+?)(?:\.|\[)',
        texto,
        flags=re.IGNORECASE,
    ):
        agrupaciones.append({
            "nombre": m.group(1).strip(),
            "actividades": m.group(2).strip(),
            "integrantes": _parsear_integrantes(m.group(3)),
            "caracteristica_general": None,
        })
    return agrupaciones


def _inferir_tematica(texto: str, rol: str) -> Optional[str]:
    temas = []
    t = texto.lower()
    if "ciencia ficción" in t or "ciencia ficcion" in t:
        temas.append("ciencia ficción")
    if "humor" in t or "humorismo" in t or "humorista" in rol.lower():
        temas.append("humorismo venezolano")
    if "periodismo" in t or "periodista" in rol.lower():
        temas.append("periodismo")
    return ", ".join(temas) if temas else None


def parsear_ficha_narrativa_desde_texto(texto: str) -> Optional[dict]:
    """Construye el dict del schema desde texto biográfico narrativo."""
    if not es_ficha_narrativa(texto):
        return None

    texto = _limpiar_citas_wikipedia(texto)
    intro = _parsear_intro(texto)
    if not intro:
        return None

    biografia = _texto_biografico(texto)
    rol = intro.pop("actividad_rol", "")
    actividad = normalizar_texto_plano(f"{rol}. {biografia}" if biografia else rol)
    obras = _parsear_obras(texto)
    agrupaciones = _parsear_agrupaciones(texto)

    autor = {
        "nombres": intro["nombres"],
        "apellidos": intro["apellidos"],
        "sexo": resolver_sexo(intro["nombres"], intro["apellidos"]),
        "seudonimo": intro.get("seudonimo"),
        "fecha_nacimiento": intro.get("fecha_nacimiento"),
        "fecha_fallecimiento": intro.get("fecha_fallecimiento"),
        "lugar_nacimiento": intro.get("lugar_nacimiento"),
        "lugar_fallecimiento": intro.get("lugar_fallecimiento"),
        "actividad_relevante": actividad,
        "tematica_principal": _inferir_tematica(texto, rol),
        "genero_principal": intro.get("genero_principal") or "desconocido",
        "criticas": [],
        "obras": obras,
        "multimedia": [],
    }
    autor["text"] = generar_resumen_autor(autor)

    return {
        "autor": autor,
        "revistas": [],
        "agrupaciones": agrupaciones,
        "antologias": [],
        "mitos_leyendas": [],
    }
