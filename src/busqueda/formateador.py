"""
Funciones de formateo de datos para el front-end.

Convierte los datos enriquecidos del grafo en texto legible para el LLM
y en objetos metadata compatibles con el componente LiteraryCard.
"""

from typing import Dict, List, Optional


def formatear_contexto(datos_enriquecidos: dict) -> str:
    """Convierte los datos enriquecidos en texto legible para el LLM."""
    partes: List[str] = []

    autor = datos_enriquecidos.get("autor")
    if autor:
        nombre = f"{autor.get('nombres', '')} {autor.get('apellidos', '')}".strip()
        partes.append(f"AUTOR: {nombre}")
        # nombre_completo puede ser diferente al compuesto
        nc = autor.get("nombre_completo", "")
        if nc and nc.strip() != nombre:
            partes.append(f"  Nombre completo: {nc}")
        _agregar_si_existe(partes, autor, "seudonimo", "Seudónimo")
        _agregar_si_existe(partes, autor, "sexo", "Sexo")
        _agregar_si_existe(partes, autor, "fecha_nacimiento", "Nacimiento")
        _agregar_si_existe(partes, autor, "fecha_fallecimiento", "Fallecimiento")

        # Lugar de nacimiento compuesto
        lugar_nac = _construir_lugar(autor, prefijo="lugar_nacimiento")
        if lugar_nac:
            partes.append(f"  Lugar de nacimiento: {lugar_nac}")

        # Lugar de fallecimiento compuesto
        lugar_fall = _construir_lugar(autor, prefijo="lugar_fallecimiento")
        if lugar_fall:
            partes.append(f"  Lugar de fallecimiento: {lugar_fall}")

        _agregar_si_existe(partes, autor, "actividad_relevante", "Actividad")
        _agregar_si_existe(partes, autor, "contexto_vivio", "Contexto")
        _agregar_si_existe(partes, autor, "tematica_principal", "Temática principal")
        _agregar_si_existe(partes, autor, "genero_principal", "Género principal")

    for o in datos_enriquecidos.get("obras", []):
        partes.append(f"\nOBRA: {o.get('titulo', 'Sin título')}")
        _agregar_si_existe(partes, o, "genero", "Género")
        _agregar_si_existe(partes, o, "fecha_publicacion", "Publicación")
        _agregar_si_existe(partes, o, "editorial", "Editorial")
        _agregar_si_existe(partes, o, "descripcion", "Descripción")

    for c in datos_enriquecidos.get("criticas", []):
        partes.append(f"\nCRÍTICA: {c.get('titulo', 'Sin título')}")
        _agregar_si_existe(partes, c, "autor_critica", "Autor de la crítica")
        _agregar_si_existe(partes, c, "descripcion_resumen", "Resumen")

    for ag in datos_enriquecidos.get("agrupaciones", []):
        partes.append(f"\nAGRUPACIÓN: {ag.get('nombre', 'Sin nombre')}")
        _agregar_si_existe(partes, ag, "caracteristica_general", "Característica")

    for m in datos_enriquecidos.get("mitos", []):
        partes.append(f"\nMITO/LEYENDA: {m.get('titulo', 'Sin título')}")
        _agregar_si_existe(partes, m, "descripcion", "Descripción")
        _agregar_si_existe(partes, m, "tema_principal", "Tema")

    return "\n".join(partes) if partes else "No se encontró información relevante en la base de datos."


def construir_metadata_autor(datos: dict) -> Optional[dict]:
    """Construye el objeto metadata compatible con LiteraryCard del front-end."""
    autor = datos.get("autor")
    if not autor:
        return None

    nombre = f"{autor.get('nombres', '')} {autor.get('apellidos', '')}".strip()
    if not nombre:
        return None

    lugar = _construir_lugar(autor, prefijo="lugar_nacimiento") or "Venezuela"

    # Periodo
    periodo_partes = []
    if autor.get("fecha_nacimiento"):
        periodo_partes.append(str(autor["fecha_nacimiento"]))
    if autor.get("fecha_fallecimiento"):
        periodo_partes.append(str(autor["fecha_fallecimiento"]))
    periodo = "–".join(periodo_partes)

    disciplina = autor.get("genero_principal", "Literatura")

    # Multimedia clasificada
    imagenes, audios, pdfs = _clasificar_multimedia(autor, datos.get("multimedia", []))

    return {
        "nombre": nombre,
        "disciplina": disciplina,
        "periodo": periodo,
        "lugar": lugar,
        "imagenes": imagenes or None,
        "audios": audios or None,
        "pdfs": pdfs or None,
    }


# ─── Funciones auxiliares privadas ────────────────────────────────

def _agregar_si_existe(partes: List[str], nodo: dict, campo: str, etiqueta: str) -> None:
    """Agrega una línea al contexto solo si el campo existe y no está vacío."""
    valor = nodo.get(campo)
    if valor:
        partes.append(f"  {etiqueta}: {valor}")


def _construir_lugar(nodo: dict, prefijo: str) -> str:
    """Construye una cadena de lugar a partir de campos ciudad/estado/país."""
    partes = []
    for sufijo in ["_ciudad", "_estado", "_pais"]:
        valor = nodo.get(f"{prefijo}{sufijo}")
        if valor:
            partes.append(valor)
    return ", ".join(partes)


def _clasificar_multimedia(autor: dict, multimedia_nodos: list) -> tuple:
    """
    Clasifica los archivos multimedia en imagenes, audios y pdfs.
    Toma datos tanto del propio nodo Autor como de nodos Multimedia relacionados.
    """
    imagenes: List[str] = []
    audios: List[str] = []
    pdfs: List[str] = []

    # Multimedia directa del nodo Autor
    if autor.get("imagen_autor"):
        imagenes.append(autor["imagen_autor"])
    if autor.get("audio_voz"):
        audios.append(autor["audio_voz"])

    # Multimedia de nodos relacionados
    for m in multimedia_nodos:
        tipo = (m.get("tipo") or "").lower()
        enlace = m.get("enlace", "")
        if not enlace:
            continue
        if tipo == "imagen":
            imagenes.append(enlace)
        elif tipo == "audio":
            audios.append(enlace)
        elif tipo == "pdf":
            pdfs.append(enlace)

    return imagenes, audios, pdfs
