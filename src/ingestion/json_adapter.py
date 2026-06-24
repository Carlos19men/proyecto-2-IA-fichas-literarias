"""
Adapta respuestas JSON alternativas del LLM al schema FichaLiterariaSchema.

Cubre formatos como {"system": ..., "data": [{type: literaryWork}, ...]}
y extrae revistas mencionadas en el texto plano de la ficha.
"""

import re
from typing import Optional


def _split_nombre(nombre: str) -> tuple[str, str]:
    partes = (nombre or "desconocido").strip().split()
    if len(partes) <= 1:
        return partes[0] if partes else "desconocido", "desconocido"
    return partes[0], " ".join(partes[1:])


def _es_revista_por_item(item: dict) -> bool:
    titulo = (item.get("title") or item.get("titulo") or "").lower()
    item_id = (item.get("id") or "").lower()
    lugar = (item.get("publicationPlace") or item.get("lugar_publicacion") or "").lower()
    tipo_obra = (item.get("typeOfWork") or "").lower()
    texto = f"{titulo} {item_id} {lugar} {tipo_obra}"
    return "revista" in texto


def adaptar_json_alternativo(data: dict) -> Optional[dict]:
    """
    Convierte JSON con lista `data` y tipos literarios
    (person, literaryWork, literaryCriticism, etc.) al dict del schema.
    """
    if not isinstance(data, dict):
        return None

    items = data.get("data")
    if not isinstance(items, list) or not items:
        return None

    resultado: dict = {
        "autor": {},
        "obras": [],
        "criticas": [],
        "agrupaciones": [],
        "revistas": [],
        "antologias": [],
        "mitos_leyendas": [],
    }

    for item in items:
        if not isinstance(item, dict):
            continue
        tipo = (item.get("type") or "").lower()

        if tipo == "person":
            nombre = item.get("name") or item.get("nombre") or ""
            nombres, apellidos = _split_nombre(nombre)
            lugar_nac = item.get("birthPlace") or item.get("lugar_nacimiento")
            resultado["autor"] = {
                "nombres": nombres,
                "apellidos": apellidos,
                "sexo": item.get("sexo") or "desconocido",
                "lugar_nacimiento": lugar_nac,
                "fecha_nacimiento": item.get("birthDate") or item.get("fecha_nacimiento"),
                "fecha_fallecimiento": item.get("deathDate") or item.get("fecha_fallecimiento"),
                "actividad_relevante": item.get("actividad_relevante") or "",
                "genero_principal": item.get("genero_principal") or "desconocido",
                "criticas": [],
                "obras": [],
                "multimedia": [],
            }

        elif tipo in ("literarywork", "obra"):
            resultado["obras"].append({
                "titulo": item.get("title") or item.get("titulo") or "sin título",
                "genero": item.get("genre") or item.get("genero") or "desconocido",
                "fecha_publicacion": str(item.get("publicationDate") or item.get("fecha_publicacion") or "desconocida"),
                "lugar_publicacion": item.get("publicationPlace") or item.get("lugar_publicacion"),
                "editorial": item.get("publisher") or item.get("editorial"),
                "idioma_original": item.get("language") or item.get("idioma_original") or "español",
                "descripcion": item.get("description") or item.get("descripcion"),
                "multimedia": [],
            })

        elif tipo in ("literarycriticism", "critica"):
            resultado["criticas"].append({
                "tipo": item.get("typeOfWork") or item.get("tipo") or "reseña",
                "autor": item.get("author") or item.get("autor") or "desconocido",
                "titulo": item.get("title") or item.get("titulo") or "sin título",
                "fecha_publicacion": str(item.get("publicationDate") or item.get("fecha_publicacion") or "desconocida"),
                "referencia_bibliografica": item.get("publicationPlace") or item.get("referencia_bibliografica") or "no disponible",
                "descripcion_resumen": item.get("description") or item.get("descripcion_resumen"),
            })

        elif tipo in ("literarygroup", "agrupacion"):
            miembros = item.get("members") or item.get("integrantes") or []
            integrantes = []
            for m in miembros:
                if isinstance(m, str):
                    n, a = _split_nombre(m)
                    integrantes.append({"nombres": n, "apellidos": a, "rol": "integrante"})
            resultado["agrupaciones"].append({
                "nombre": item.get("name") or item.get("nombre") or "agrupación sin nombre",
                "integrantes": integrantes,
                "caracteristica_general": item.get("description") or item.get("caracteristica_general"),
            })

        elif tipo in ("literaryanthology", "literarymagazine", "revista", "antologia"):
            if _es_revista_por_item(item):
                resultado["revistas"].append(_item_a_revista(item))
            else:
                resultado["antologias"].append({
                    "titulo": item.get("title") or item.get("titulo") or "antología sin título",
                    "genero": item.get("genre") or item.get("genero") or "desconocido",
                    "fecha_publicacion": str(item.get("publicationDate") or item.get("fecha_publicacion") or "desconocida"),
                    "lugar_publicacion": item.get("publicationPlace") or item.get("lugar_publicacion"),
                    "editorial": item.get("publisher") or item.get("editorial"),
                    "autor": item.get("author") or item.get("autor"),
                    "descripcion": item.get("description") or item.get("descripcion") or item.get("typeOfWork"),
                    "idioma_original": item.get("language") or "español",
                    "multimedia": [],
                })

    if not resultado["autor"] and not resultado["obras"] and not resultado["revistas"]:
        return None

    criticas = resultado.pop("criticas", [])
    obras = resultado.pop("obras", [])
    revistas = resultado.pop("revistas", [])
    agrupaciones = resultado.pop("agrupaciones", [])
    antologias = resultado.pop("antologias", [])
    mitos = resultado.pop("mitos_leyendas", [])

    autor = resultado.get("autor") or {}
    autor.setdefault("nombres", "desconocido")
    autor.setdefault("apellidos", "desconocido")
    autor.setdefault("sexo", "desconocido")
    autor["criticas"] = criticas
    autor["obras"] = obras
    autor.setdefault("multimedia", [])

    return {
        "autor": autor,
        "revistas": revistas,
        "agrupaciones": agrupaciones,
        "antologias": antologias,
        "mitos_leyendas": mitos,
    }


def _item_a_revista(item: dict) -> dict:
    titulo = item.get("title") or item.get("titulo") or ""
    item_id = item.get("id") or ""
    if "revista_nacional" in item_id.lower() or titulo.lower().startswith("año"):
        titulo = "Revista Nacional de Cultura"
    return {
        "titulo": titulo or "revista sin título",
        "fecha_primer_numero": str(item.get("publicationDate") or item.get("fecha_primer_numero") or ""),
        "numeros_publicados": item.get("typeOfWork") or item.get("numeros_publicados") or item.get("description"),
        "lugar_publicacion": item.get("publicationPlace") or item.get("lugar_publicacion"),
        "editorial": item.get("publisher") or item.get("editorial"),
        "descripcion": item.get("description") or item.get("descripcion") or item.get("typeOfWork"),
        "idioma_original": item.get("language") or "español",
        "creadores": [],
        "multimedia": [],
    }


def extraer_revistas_del_texto(texto: str) -> list[dict]:
    """Extrae revistas mencionadas en biografía o sección de crítica (heurísticas genéricas)."""
    if not texto:
        return []

    revistas: list[dict] = []
    vistos: set[str] = set()

    def _agregar(rev: dict) -> None:
        titulo = (rev.get("titulo") or "").strip().lower()
        if titulo and titulo not in vistos:
            vistos.add(titulo)
            revistas.append(rev)

    # funda (y dirige) la revista X ... año YYYY ... N números / tres números
    m = re.search(
        r"fund[aó]\s+(?:y\s+dirige\s+)?la\s+revista\s+([A-ZÁÉÍÓÚÑa-záéíóúñ]+)"
        r".*?(?:año\s+de\s+)?(\d{4})",
        texto,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if m:
        ventana = texto[m.start() : m.start() + 600]
        nums = re.search(
            r"(\d+|un|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez)\s+n[uú]meros",
            ventana,
            flags=re.IGNORECASE,
        )
        cantidad = nums.group(1) if nums else None
        numeros_txt = f"{cantidad} números publicados" if cantidad else None
        _agregar({
            "titulo": m.group(1).strip(),
            "fecha_primer_numero": m.group(2),
            "numeros_publicados": numeros_txt,
            "descripcion": f"Fundada y dirigida por el autor en {m.group(2)}.",
            "idioma_original": "español",
            "creadores": [],
            "multimedia": [],
        })

    # Revista Nacional de Cultura (2007). Año LXIX, Nº. 335...
    for m in re.finditer(
        r"Revista\s+Nacional\s+de\s+Cultura\s*\((\d{4})\)\.\s*(.+?)(?:\n\s*\n|\Z)",
        texto,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        detalle = re.sub(r"\s+", " ", m.group(2).strip())
        _agregar({
            "titulo": "Revista Nacional de Cultura",
            "fecha_primer_numero": m.group(1),
            "numeros_publicados": detalle,
            "descripcion": detalle,
            "lugar_publicacion": "Ciudad Guayana",
            "idioma_original": "español",
            "creadores": [],
            "multimedia": [],
        })

    # Cárcava. Revista de arte, literatura y pensamiento. Ciudad Guayana. Nº 14...
    for m in re.finditer(
        r"^([A-ZÁÉÍÓÚÑ][^\n.]{1,60})\.\s*Revista\s+de\s+([^\n]+)",
        texto,
        flags=re.IGNORECASE | re.MULTILINE,
    ):
        nombre = m.group(1).strip()
        detalle = m.group(2).strip()
        numero = re.search(r"N[º°o\.]\s*(\d+)", detalle)
        _agregar({
            "titulo": nombre,
            "numeros_publicados": numero.group(0) if numero else detalle,
            "descripcion": f"Revista de {detalle}",
            "lugar_publicacion": "Ciudad Guayana" if "guayana" in detalle.lower() else None,
            "idioma_original": "español",
            "creadores": [],
            "multimedia": [],
        })

    return revistas


def fusionar_revistas(existentes: list, nuevas: list) -> list:
    """Une listas de revistas sin duplicar por título."""
    por_titulo: dict[str, dict] = {}
    for rev in existentes + nuevas:
        if isinstance(rev, dict):
            titulo = (rev.get("titulo") or "").strip().lower()
            if titulo:
                por_titulo[titulo] = {**por_titulo.get(titulo, {}), **rev}
    return list(por_titulo.values())
