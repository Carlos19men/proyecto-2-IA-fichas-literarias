"""Complementa la extracción del LLM parseando secciones Markdown estructuradas."""

import re
from typing import List, Optional

from src.ingestion.schemas import (
    CriticaSchema,
    FichaLiterariaSchema,
    Lugar,
    ObraSchema,
)


def _extraer_seccion(texto: str, titulo: str) -> str:
    texto = texto.replace("\r\n", "\n")
    patron = rf"## {re.escape(titulo)}\s*\n(.*?)(?=\n## |\Z)"
    match = re.search(patron, texto, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""


def _parse_lugar(valor: str) -> Optional[Lugar]:
    partes = [p.strip() for p in valor.split(",")]
    if len(partes) >= 4:
        return Lugar(ciudad=partes[0], municipio=partes[1], estado=partes[2], pais=partes[3])
    if len(partes) == 3:
        return Lugar(ciudad=partes[0], estado=partes[1], pais=partes[2])
    if len(partes) == 2:
        return Lugar(ciudad=partes[0], pais=partes[1])
    return Lugar(ciudad=valor) if valor else None


def _parse_campo_bullet(bloque: str, clave: str) -> Optional[str]:
    match = re.search(rf"^-?\s*{re.escape(clave)}:\s*(.+)$", bloque, re.MULTILINE | re.IGNORECASE)
    if not match:
        return None
    valor = match.group(1).strip()
    if valor.lower().startswith("(ninguno") or valor.lower() == "null":
        return None
    return valor


def _parse_obras(seccion: str) -> List[ObraSchema]:
    obras: List[ObraSchema] = []
    bloques = re.split(r"^### ", seccion, flags=re.MULTILINE)
    for bloque in bloques:
        bloque = bloque.strip()
        if not bloque:
            continue
        lineas = bloque.split("\n")
        titulo = lineas[0].strip()
        genero = _parse_campo_bullet(bloque, "Género") or "Poesía"
        fecha = _parse_campo_bullet(bloque, "Fecha de publicación") or ""
        descripcion = _parse_campo_bullet(bloque, "Descripción")
        lugar_txt = _parse_campo_bullet(bloque, "Lugar de publicación")
        obras.append(
            ObraSchema(
                titulo=titulo,
                genero=genero,
                fecha_publicacion=fecha,
                lugar_publicacion=_parse_lugar(lugar_txt) if lugar_txt else None,
                descripcion=descripcion,
                idioma_original="español",
            )
        )
    return obras


def _parse_criticas(seccion: str) -> List[CriticaSchema]:
    criticas: List[CriticaSchema] = []
    bloques = re.split(r"^### ", seccion, flags=re.MULTILINE)
    for bloque in bloques:
        bloque = bloque.strip()
        if not bloque:
            continue
        titulo = bloque.split("\n")[0].strip()
        criticas.append(
            CriticaSchema(
                tipo=_parse_campo_bullet(bloque, "Tipo") or "Reseña",
                autor=_parse_campo_bullet(bloque, "Autor de la crítica") or "",
                titulo=titulo,
                fecha_publicacion=_parse_campo_bullet(bloque, "Fecha de publicación") or "",
                referencia_bibliografica=_parse_campo_bullet(bloque, "Referencia bibliográfica") or "",
                descripcion_resumen=_parse_campo_bullet(bloque, "Descripción"),
            )
        )
    return criticas


def complementar_desde_markdown(ficha: FichaLiterariaSchema, texto: str) -> FichaLiterariaSchema:
    """Rellena campos que el LLM suele omitir cuando la ficha viene en Markdown estructurado."""
    texto = texto.replace("\r\n", "\n")
    tiene_estructura = any(
        h in texto for h in ("## Obras", "## Críticas", "## Identidad", "Obras\n", "Críticas\n")
    )
    if not tiene_estructura:
        return ficha

    autor = ficha.autor
    identidad = _extraer_seccion(texto, "Identidad")
    trayectoria = _extraer_seccion(texto, "Trayectoria")
    perfil = _extraer_seccion(texto, "Perfil literario")

    if identidad:
        autor.nombres = _parse_campo_bullet(identidad, "Nombres") or autor.nombres
        autor.apellidos = _parse_campo_bullet(identidad, "Apellidos") or autor.apellidos
        autor.sexo = _parse_campo_bullet(identidad, "Sexo") or autor.sexo
        autor.seudonimo = _parse_campo_bullet(identidad, "Seudónimo")
        autor.fecha_nacimiento = _parse_campo_bullet(identidad, "Fecha de nacimiento")
        lugar_txt = _parse_campo_bullet(identidad, "Lugar de nacimiento")
        if lugar_txt:
            autor.lugar_nacimiento = _parse_lugar(lugar_txt)

    if trayectoria:
        if "Actividad relevante:" in trayectoria:
            autor.actividad_relevante = trayectoria.split("Actividad relevante:")[1].split("\n\n")[0].strip()
        if "Contexto histórico:" in trayectoria:
            autor.contexto_vivio = trayectoria.split("Contexto histórico:")[1].strip()

    if perfil:
        autor.tematica_principal = _parse_campo_bullet(perfil, "Temática principal") or autor.tematica_principal
        autor.genero_principal = _parse_campo_bullet(perfil, "Género principal") or autor.genero_principal

    obras_md = _parse_obras(_extraer_seccion(texto, "Obras"))
    if obras_md:
        autor.obras = obras_md

    criticas_md = _parse_criticas(_extraer_seccion(texto, "Críticas"))
    if criticas_md:
        autor.criticas = criticas_md

    autor.nombre_completo = f"{autor.nombres} {autor.apellidos}".strip()
    ficha.mitos_leyendas = []
    return ficha
