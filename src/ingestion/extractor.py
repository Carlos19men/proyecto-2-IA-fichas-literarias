"""
extractor.py — Extrae datos estructurados de una ficha literaria (Word → Pydantic).

Mejoras respecto a la versión original:
  - Se inyecta `MAPPING_PROMPT_BLOCK` de field_mapping.py en el system-prompt.
  - El LLM recibe una tabla explícita Word-etiqueta → campo Python, eliminando
    ambigüedades en campos críticos (actividad_relevante, tematica_principal,
    audio_voz, imagen_autor, referencia_bibliografica, caracteristica_general).
  - Se añade un segundo nivel de instrucciones para campos compuestos
    (Lugar, Multimedia, listas de Persona).
  - Optimizado para evitar pérdidas de información con instrucciones estrictas de extracción literal.
  - Soporte robusto de fallback para extraer JSON si falla el modo estructurado nativo.
  - Saneamiento y normalización automática de datos JSON antes de la validación Pydantic para evitar excepciones comunes de tipos.
"""

import json
import re
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from src.config import Config
from src.ingestion.schemas import FichaLiterariaSchema
from src.ingestion.field_mapping import get_prompt_mapping_block


def normalizar_lugar(val) -> dict | None:
    """ Convierte valores de lugar en strings a un dict compatible con Lugar. """
    if not val:
        return None
    if isinstance(val, dict):
        return val
    if isinstance(val, str):
        val_clean = val.strip().lower()
        if val_clean in {"desconocido", "no disponible", "n/d", "s/d", "sin dato", "no especificado"}:
            return None
        # Remove trailing periods and spaces
        parts = [p.strip().rstrip(".") for p in val.split(",") if p.strip()]
        if not parts:
            return None
        
        result = {}
        for part in parts:
            part_lower = part.lower()
            if "pais" in part_lower or "venezuela" in part_lower:
                result["pais"] = part
            elif "estado" in part_lower or "provincia" in part_lower or part_lower == "bolivar":
                result["estado"] = part
            elif "municipio" in part_lower:
                result["municipio"] = part
            else:
                # Assign to first empty key in order: ciudad, municipio, estado, pais
                for key in ["ciudad", "municipio", "estado", "pais"]:
                    if key not in result:
                        result[key] = part
                        break
        return result
    return None


def normalizar_persona(p) -> dict | None:
    """ Sanea y mapea un dict de persona para que cumpla con Persona (nombres, apellidos, rol). """
    if not isinstance(p, dict):
        return p
    p = dict(p)
    if "nombre" in p and "nombres" not in p:
        p["nombres"] = p.pop("nombre")
    if "apellido" in p and "apellidos" not in p:
        p["apellidos"] = p.pop("apellido")
    return p


def extraer_string_de_multimedia(val) -> str | None:
    """ Convierte objetos multimedia u otros tipos devueltos por error en un string (ej. enlace/ruta). """
    if not val:
        return None
    if isinstance(val, dict):
        return val.get("enlace") or val.get("ruta") or val.get("url") or str(val)
    return str(val)


def normalizar_multimedia(m) -> dict | None:
    """ Sanea un objeto de multimedia. """
    if not isinstance(m, dict):
        return m
    m = dict(m)
    if "restriccion" in m and not m["restriccion"]:
        m["restriccion"] = None
    return m


def quitar_acentos_dict_keys(d):
    if isinstance(d, list):
        return [quitar_acentos_dict_keys(x) for x in d]
    if isinstance(d, dict):
        new_d = {}
        for k, v in d.items():
            k_clean = k.replace("í", "i").replace("ó", "o").replace("á", "a").replace("é", "e").replace("ú", "u")
            k_clean = k_clean.replace("Í", "I").replace("Ó", "O").replace("Á", "A").replace("É", "E").replace("Ú", "U")
            new_d[k_clean] = quitar_acentos_dict_keys(v)
        return new_d
    return d


def normalizar_json_antes_de_pydantic(data: dict) -> dict:
    """
    Sanea y normaliza la estructura del JSON devuelto por el LLM
    antes de instanciarlo con Pydantic, previniendo fallas de validación.
    """
    if not isinstance(data, dict):
        return data

    # Remover acentos de todas las claves (ej: críticas -> criticas, título -> titulo)
    data = quitar_acentos_dict_keys(data)

    # 1. Corregir claves de primer nivel con acentos o formas incorrectas
    mapeo_claves_raiz = {
        "criticas": "criticas",
        "antologias": "antologias",
        "agrupacion": "agrupaciones",
        "mitos_y_leyendas": "mitos_leyendas"
    }
    for k_inc, k_corr in mapeo_claves_raiz.items():
        if k_inc in data and k_corr not in data:
            data[k_corr] = data.pop(k_inc)

    autor = data.get("autor")
    if not isinstance(autor, dict):
        autor = {}
        data["autor"] = autor

    if isinstance(autor, dict):
        # Mover posibles campos de autor que el LLM haya puesto erróneamente en la raíz
        for c_key in ["contexto_vivio", "lugar_vivio", "contexto", "marco_historico", "contexto_historico", 
                      "imagen_autor", "imagen_del_autor", "foto_autor", "audio_voz", "audio_del_autor",
                      "seudonimo", "pseudonimo", "genero_principal", "genero_principal_cultivado", "genero_cultivado"]:
            if c_key in data:
                val = data.pop(c_key)
                target_key = c_key
                if c_key in ["lugar_vivio", "contexto", "marco_historico", "contexto_historico"]:
                    target_key = "contexto_vivio"
                elif c_key == "pseudonimo":
                    target_key = "seudonimo"
                elif c_key in ["genero_principal_cultivado", "genero_cultivado"]:
                    target_key = "genero_principal"
                elif c_key in ["imagen_del_autor", "foto_autor"]:
                    target_key = "imagen_autor"
                elif c_key == "audio_del_autor":
                    target_key = "audio_voz"
                
                if target_key not in autor or autor[target_key] is None:
                    autor[target_key] = val

        # Corregir claves dentro de autor
        if "criticas" in autor and "criticas" not in autor:
            autor["criticas"] = autor.pop("criticas")
            
        for c_key in ["lugar_vivio", "contexto", "marco_historico", "contexto_historico"]:
            if c_key in autor and ("contexto_vivio" not in autor or autor["contexto_vivio"] is None):
                autor["contexto_vivio"] = autor.pop(c_key)

        if "pseudonimo" in autor and ("seudonimo" not in autor or autor["seudonimo"] is None):
            autor["seudonimo"] = autor.pop("pseudonimo")
            
        # Corregir genero_principal / genero_principal_cultivado / genero_cultivado
        if "genero_principal" not in autor or autor["genero_principal"] is None:
            for g_key in ["genero_principal_cultivado", "genero_cultivado", "genero"]:
                if g_key in autor:
                    autor["genero_principal"] = autor.pop(g_key)
                    break
            else:
                autor["genero_principal"] = "desconocido"

        # Asegurar que genero_principal sea string y no list
        gp = autor.get("genero_principal")
        if isinstance(gp, list):
            autor["genero_principal"] = ", ".join(str(g) for g in gp)
        elif gp is not None:
            autor["genero_principal"] = str(gp)

        # Asegurar que tematica_principal sea string y no list
        tp = autor.get("tematica_principal")
        if isinstance(tp, list):
            autor["tematica_principal"] = ", ".join(str(t) for t in tp)
        elif tp is not None:
            autor["tematica_principal"] = str(tp)
        
        # Validaciones defensivas de campos obligatorios de Autor
        if "nombres" not in autor or not autor["nombres"]:
            autor["nombres"] = "desconocido"
        if "apellidos" not in autor or not autor["apellidos"]:
            autor["apellidos"] = "desconocido"
        if "sexo" not in autor or not autor["sexo"]:
            autor["sexo"] = "desconocido"
        if not autor.get("genero_principal"):
            autor["genero_principal"] = "desconocido"

        # Corregir fechas en autor (deben ser string)
        for f_key in ["fecha_nacimiento", "fecha_fallecimiento"]:
            if f_key in autor and autor[f_key] is not None:
                autor[f_key] = str(autor[f_key])
        
        # Corregir lugares en Autor
        if "lugar_nacimiento" in autor:
            autor["lugar_nacimiento"] = normalizar_lugar(autor["lugar_nacimiento"])
        if "lugar_fallecimiento" in autor:
            autor["lugar_fallecimiento"] = normalizar_lugar(autor["lugar_fallecimiento"])
                
        # Corregir actividad_relevante (debe ser un string, no una lista)
        act = autor.get("actividad_relevante")
        if isinstance(act, list):
            lineas = []
            for item in act:
                if isinstance(item, dict):
                    tipo = item.get("tipo") or item.get("actividad") or item.get("cargo") or item.get("puesto") or item.get("funcion") or ""
                    lugar = item.get("lugar") or ""
                    periodo = item.get("periodo") or item.get("fecha") or item.get("fecha_inicio") or item.get("fecha_fin") or item.get("anio") or ""
                    partes = []
                    if tipo: partes.append(str(tipo))
                    if lugar: partes.append(f"en {lugar}")
                    if periodo: partes.append(f"({periodo})")
                    if partes:
                        lineas.append(" ".join(partes))
                else:
                    lineas.append(str(item))
            autor["actividad_relevante"] = "; ".join(lineas)
        elif act is None:
            autor["actividad_relevante"] = ""

        # Corregir contexto_vivio (debe ser un string, no un dict)
        ctx = autor.get("contexto_vivio")
        if isinstance(ctx, dict):
            partes = []
            for k, v in ctx.items():
                if v:
                    partes.append(f"{k}: {v}")
            autor["contexto_vivio"] = ", ".join(partes)

        # Corregir familiares_destacados
        fams = autor.get("familiares_destacados")
        if isinstance(fams, list):
            autor["familiares_destacados"] = [normalizar_persona(f) for f in fams if f]

        # Corregir imagen_autor y audio_voz
        if "imagen_autor" in autor:
            autor["imagen_autor"] = extraer_string_de_multimedia(autor["imagen_autor"])
        if "audio_voz" in autor:
            autor["audio_voz"] = extraer_string_de_multimedia(autor["audio_voz"])

        # Corregir multimedia del autor
        mult = autor.get("multimedia")
        if isinstance(mult, list):
            autor["multimedia"] = [normalizar_multimedia(item) for item in mult if item]
        elif isinstance(mult, dict):
            autor["multimedia"] = [normalizar_multimedia(mult)]

        # Corregir obras del autor
        obras = autor.get("obras")
        if isinstance(obras, list):
            for o in obras:
                if isinstance(o, dict):
                    if "nombres" in o and "titulo" not in o:
                        o["titulo"] = o.pop("nombres")
                    if "nombre" in o and "titulo" not in o:
                        o["titulo"] = o.pop("nombre")
                    # Campos requeridos para Obra
                    if "titulo" not in o or not o["titulo"]:
                        o["titulo"] = "sin título"
                    if "genero" not in o or not o["genero"]:
                        o["genero"] = "desconocido"
                    else:
                        gen = o.get("genero")
                        if isinstance(gen, list):
                            o["genero"] = ", ".join(str(g) for g in gen)
                    if "fecha_publicacion" not in o or o["fecha_publicacion"] is None:
                        o["fecha_publicacion"] = "desconocida"
                    else:
                        o["fecha_publicacion"] = str(o["fecha_publicacion"])
                    if "idioma_original" not in o or not o["idioma_original"]:
                        o["idioma_original"] = "español"
                    if "lugar_publicacion" in o:
                        o["lugar_publicacion"] = normalizar_lugar(o["lugar_publicacion"])

        # Corregir críticas del autor
        criticas = autor.get("criticas")
        if isinstance(criticas, list):
            for c in criticas:
                if isinstance(c, dict):
                    if "nombre" in c and "titulo" not in c:
                        c["titulo"] = c.pop("nombre")
                    if "nombres" in c and "titulo" not in c:
                        c["titulo"] = c.pop("nombres")
                    # Campos requeridos para Crítica
                    if "tipo" not in c or not c["tipo"]:
                        c["tipo"] = "reseña"
                    if "autor" not in c or not c["autor"]:
                        c["autor"] = "desconocido"
                    if "titulo" not in c or not c["titulo"]:
                        c["titulo"] = "sin título"
                    if "fecha_publicacion" not in c or c["fecha_publicacion"] is None:
                        c["fecha_publicacion"] = "desconocida"
                    else:
                        c["fecha_publicacion"] = str(c["fecha_publicacion"])
                    if "referencia_bibliografica" not in c or not c["referencia_bibliografica"]:
                        c["referencia_bibliografica"] = "no disponible"

    # Corregir agrupaciones
    agrupaciones = data.get("agrupaciones")
    if isinstance(agrupaciones, list):
        for ag in agrupaciones:
            if isinstance(ag, dict):
                if "nombres" in ag and "nombre" not in ag:
                    ag["nombre"] = ag.pop("nombres")
                if "titulo" in ag and "nombre" not in ag:
                    ag["nombre"] = ag.pop("titulo")
                if "nombre" not in ag or not ag["nombre"]:
                    ag["nombre"] = "agrupación sin nombre"
                if "lugar_encuentros" in ag:
                    ag["lugar_encuentros"] = normalizar_lugar(ag["lugar_encuentros"])
                for f_key in ["fecha_inicio", "fecha_culminacion"]:
                    if f_key in ag and ag[f_key] is not None:
                        ag[f_key] = str(ag[f_key])
                # Corregir integrantes
                ints = ag.get("integrantes")
                if isinstance(ints, list):
                    ag["integrantes"] = [normalizar_persona(i) for i in ints if i]

    # Corregir revistas
    revistas = data.get("revistas")
    if isinstance(revistas, list):
        for r in revistas:
            if isinstance(r, dict):
                if "nombre" in r and "titulo" not in r:
                    r["titulo"] = r.pop("nombre")
                if "nombres" in r and "titulo" not in r:
                    r["titulo"] = r.pop("nombres")
                if "titulo" not in r or not r["titulo"]:
                    r["titulo"] = "revista sin título"
                if "lugar_publicacion" in r:
                    r["lugar_publicacion"] = normalizar_lugar(r["lugar_publicacion"])
                if "fecha_primer_numero" in r and r["fecha_primer_numero"] is not None:
                    r["fecha_primer_numero"] = str(r["fecha_primer_numero"])
                if "fecha_ultimo_numero" in r and r["fecha_ultimo_numero"] is not None:
                    r["fecha_ultimo_numero"] = str(r["fecha_ultimo_numero"])
                # Corregir creadores
                creads = r.get("creadores")
                if isinstance(creads, list):
                    r["creadores"] = [normalizar_persona(cr) for cr in creads if cr]

    # Corregir antologias
    antologias = data.get("antologias")
    if isinstance(antologias, list):
        for an in antologias:
            if isinstance(an, dict):
                if "nombre" in an and "titulo" not in an:
                    an["titulo"] = an.pop("nombre")
                if "nombres" in an and "titulo" not in an:
                    an["titulo"] = an.pop("nombres")
                if "titulo" not in an or not an["titulo"]:
                    an["titulo"] = "antología sin título"
                if "genero" not in an or not an["genero"]:
                    an["genero"] = "desconocido"
                if "fecha_publicacion" not in an or not an["fecha_publicacion"]:
                    an["fecha_publicacion"] = "desconocida"
                else:
                    an["fecha_publicacion"] = str(an["fecha_publicacion"])
                if "lugar_publicacion" in an:
                    an["lugar_publicacion"] = normalizar_lugar(an["lugar_publicacion"])

    # Corregir mitos y leyendas
    mitos_leyendas = data.get("mitos_leyendas")
    if isinstance(mitos_leyendas, list):
        for ml in mitos_leyendas:
            if isinstance(ml, dict):
                if "nombre" in ml and "titulo" not in ml:
                    ml["titulo"] = ml.pop("nombre")
                if "nombres" in ml and "titulo" not in ml:
                    ml["titulo"] = ml.pop("nombres")
                if "titulo" not in ml or not ml["titulo"]:
                    ml["titulo"] = "mito sin título"
                if "comunidad_creadora" not in ml or not ml["comunidad_creadora"]:
                    ml["comunidad_creadora"] = "desconocida"
                if "idioma_original" not in ml or not ml["idioma_original"]:
                    ml["idioma_original"] = "español"
                if "tema_principal" not in ml or not ml["tema_principal"]:
                    ml["tema_principal"] = "desconocido"
                if "lugar_difusion" in ml:
                    ml["lugar_difusion"] = normalizar_lugar(ml["lugar_difusion"])

    # Mover obras, críticas y multimedia de la raíz al autor si es necesario
    for key in ["obra", "obras"]:
        if key in data:
            val = data.get(key)
            if isinstance(val, dict):
                val = [val]
            if isinstance(val, list):
                if isinstance(autor, dict) and not autor.get("obras"):
                    for o in val:
                        if isinstance(o, dict):
                            if "nombres" in o and "titulo" not in o:
                                o["titulo"] = o.pop("nombres")
                            if "nombre" in o and "titulo" not in o:
                                o["titulo"] = o.pop("nombre")
                            if "titulo" not in o or not o["titulo"]:
                                o["titulo"] = "sin título"
                            if "genero" not in o or not o["genero"]:
                                o["genero"] = "desconocido"
                            else:
                                gen = o.get("genero")
                                if isinstance(gen, list):
                                    o["genero"] = ", ".join(str(g) for g in gen)
                            if "fecha_publicacion" not in o or o["fecha_publicacion"] is None:
                                o["fecha_publicacion"] = "desconocida"
                            else:
                                o["fecha_publicacion"] = str(o["fecha_publicacion"])
                            if "idioma_original" not in o or not o["idioma_original"]:
                                o["idioma_original"] = "español"
                            if "lugar_publicacion" in o:
                                o["lugar_publicacion"] = normalizar_lugar(o["lugar_publicacion"])
                    autor["obras"] = val

    for key in ["obra", "obras"]:
        if key in data:
            val = data.get(key)
            if isinstance(val, dict):
                val = [val]
            if isinstance(val, list):
                if isinstance(autor, dict) and not autor.get("obras"):
                    for o in val:
                        if isinstance(o, dict):
                            if "nombres" in o and "titulo" not in o:
                                o["titulo"] = o.pop("nombres")
                            if "nombre" in o and "titulo" not in o:
                                o["titulo"] = o.pop("nombre")
                            if "titulo" not in o or not o["titulo"]:
                                o["titulo"] = "sin título"
                            if "genero" not in o or not o["genero"]:
                                o["genero"] = "desconocido"
                            else:
                                gen = o.get("genero")
                                if isinstance(gen, list):
                                    o["genero"] = ", ".join(str(g) for g in gen)
                            if "fecha_publicacion" not in o or o["fecha_publicacion"] is None:
                                o["fecha_publicacion"] = "desconocida"
                            else:
                                o["fecha_publicacion"] = str(o["fecha_publicacion"])
                            if "idioma_original" not in o or not o["idioma_original"]:
                                o["idioma_original"] = "español"
                            if "lugar_publicacion" in o:
                                o["lugar_publicacion"] = normalizar_lugar(o["lugar_publicacion"])
                    autor["obras"] = val

    for key in ["critica", "criticas"]:
        if key in data:
            val = data.get(key)
            if isinstance(val, dict):
                val = [val]
            if isinstance(val, list):
                if isinstance(autor, dict) and not autor.get("criticas"):
                    for c in val:
                        if isinstance(c, dict):
                            if "nombre" in c and "titulo" not in c:
                                c["titulo"] = c.pop("nombre")
                            if "nombres" in c and "titulo" not in c:
                                c["titulo"] = c.pop("nombres")
                            if "tipo" not in c or not c["tipo"]:
                                c["tipo"] = "reseña"
                            if "autor" not in c or not c["autor"]:
                                c["autor"] = "desconocido"
                            if "titulo" not in c or not c["titulo"]:
                                c["titulo"] = "sin título"
                            if "fecha_publicacion" not in c or c["fecha_publicacion"] is None:
                                c["fecha_publicacion"] = "desconocida"
                            else:
                                c["fecha_publicacion"] = str(c["fecha_publicacion"])
                            if "referencia_bibliografica" not in c or not c["referencia_bibliografica"]:
                                c["referencia_bibliografica"] = "no disponible"
                    autor["criticas"] = val

    if "multimedia" in data:
        val = data.pop("multimedia")
        if isinstance(val, dict):
            val = [val]
        if isinstance(val, list):
            if isinstance(autor, dict) and not autor.get("multimedia"):
                autor["multimedia"] = [normalizar_multimedia(item) for item in val if item]
    return data


def extraer_json_de_ficha(texto_ficha: str) -> FichaLiterariaSchema:
    """
    Envía el texto crudo a Ollama y fuerza una respuesta estructurada en JSON.

    Extrae información completa incluyendo:
    - Datos biográficos del autor (nombres, apellidos, fechas, lugares desglosados)
    - Multimedia (imágenes, audio, videos)
    - Relaciones (obras, críticas, agrupaciones, revistas, antologías, mitos/leyendas)

    El sistema-prompt incluye el mapeo semántico completo (field_mapping.py) para
    que el LLM traduzca correctamente los campos del Word al schema de Pydantic.
    """

    # 1. Obtener el bloque de mapeo semántico Word → schema
    mapping_block = get_prompt_mapping_block()

    # 2. Crear el Prompt con el mapeo inyectado en el system-prompt
    system_prompt = f"""Eres un experto analista literario e historiador cultural.
Tu tarea es extraer información del texto y estructurarla exactamente como se te pide.

{mapping_block}

REGLAS DE EXTRACCIÓN LITERAL Y PREVENCIÓN DE PÉRDIDAS (CRÍTICAS):
- TÍTULOS Y NOMBRES EXACTOS: Extrae los títulos de las obras, críticas, revistas y nombres de personas EXACTAMENTE como aparecen en el texto original, carácter por carácter. No parafrasees, resumas ni corrijas los títulos, ya que el sistema realiza validaciones cruzadas literales y descartará cualquier título alterado.
- EXTRAE SIN OMISIONES: No omitas ningún libro, obra, artículo de crítica, revista o antología que se mencione en la ficha. Todos los elementos deben incluirse.
- MULTIMEDIA Y ARCHIVOS: Si en alguna parte del texto se mencionan nombres de archivos de imagen (.jpg, .png), audio (.mp3) o documentos (.pdf) de descarga, regístralos obligatoriamente en la lista de `multimedia` o en los campos correspondientes (`imagen_autor`, `audio_voz`, etc.).

REGLAS GENERALES:
- Nombres y apellidos: Separa en campos `nombres` y `apellidos` (NO uses nombre_completo para rellenar)
- Lugares: Desglosa en ciudad, municipio, estado, pais (cada uno Optional). Si el texto solo da ciudad, pon ciudad y deja el resto en null
- Fechas: Formato YYYY o YYYY-MM-DD; usar null si no aparece en el texto
- Multimedia: Incluir enlace (URL o ruta), tipo (imagen|audio|video|pdf), restriccion (público|privado|restringido)
- Listas vacías: Si no hay críticas/obras/agrupaciones/etc, devolver []
- NO inventar datos: No alucines valores que no estén en el texto
- Campos opcionales: Solo rellenar si el dato aparece explícitamente en el texto
- Sección activa: Identifica si el texto describe un Autor, Obra, Crítica, Agrupación, Revista, Antología o Mito/Leyenda

INSTRUCCIONES ESPECIALES para campos críticos:
- `autor.actividad_relevante`: Extrae TODO el texto que describe estudios, cargos públicos, profesiones, lugares y periodos del autor (debe ser un texto plano continuo, NO una lista)
- `autor.contexto_vivio`: Extrae de forma literal el texto asociado a la etiqueta "Contexto en que vivió:" (por ejemplo: "Municipio Heres, segunda mitad del siglo XIX.") y asígnalo a este campo. No lo dejes en null si existe esta sección en la ficha.
- `autor.genero_principal`: Asigna aquí el género principal cultivado por el autor (ej: "novela", "poesía"). Asegúrate de usar exactamente la clave `genero_principal` en el JSON.
- `autor.imagen_autor`: Extrae la ruta o URL del archivo .jpg de la foto del autor
- `autor.audio_voz`: Extrae la ruta o URL del archivo .mp3 de la voz del autor
- `critica.referencia_bibliografica`: Extrae el LUGAR DE PUBLICACIÓN de la crítica (editorial, revista, URL donde apareció)
- `critica.autor`: Es el CRÍTICO o investigador que escribió la reseña, NO el autor literario del que se habla
- `agrupacion.caracteristica_general`: Extrae la tendencia literaria, ideología o características generales del grupo
- `autor.familiares_destacados`: Lista de familiares; cada uno con nombres, apellidos y rol (padre, madre, hijo/a, hermano/a, etc.)
- `agrupacion.integrantes`: Lista de miembros; cada uno con nombres, apellidos y rol (fundador, integrante, etc.)
- `revista.creadores`: Lista de personas; cada uno con nombres, apellidos y rol (director, editor, etc.)"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Extrae la información de esta ficha literaria:\n\n{texto}")
    ])

    # 3. Configurar el modelo (Temperatura 0 para evitar alucinaciones)
    llm = ChatOllama(
        base_url=Config.OLLAMA_BASE_URL,
        model=Config.OLLAMA_MODEL,
        temperature=0
    )

    # Intentar con json_mode (mucho más robusto para modelos locales como Qwen/Llama)
    try:
        llm_estructurado = llm.with_structured_output(FichaLiterariaSchema, method="json_mode")
        cadena = prompt | llm_estructurado
        resultado = cadena.invoke({"texto": texto_ficha})
        return resultado
    except Exception as e:
        print(f"⚠️  Fallo la extracción estructurada nativa con json_mode: {e}")
        
        # Intentar recuperar el JSON generado de la excepción para no repetir la llamada al LLM
        raw_text = None
        err_msg = str(e)
        
        # Buscar el JSON en la cadena del error de manera robusta
        start_idx = err_msg.find('{"autor"')
        if start_idx == -1:
            start_idx = err_msg.find('{"')
            
        if start_idx != -1:
            raw_text = err_msg[start_idx:]
            # Cortar en el primer ". Got:" que indica el final del JSON
            got_idx = raw_text.find(". Got:")
            if got_idx != -1:
                raw_text = raw_text[:got_idx]
                
        if raw_text:
            try:
                print("    -> Intentando recuperar y normalizar JSON desde la salida previa...")
                start = raw_text.find("{")
                end = raw_text.rfind("}")
                if start != -1 and end != -1:
                    json_str = raw_text[start:end+1]
                    data = json.loads(json_str)
                    
                    # Saneamiento de datos antes de Pydantic
                    data = normalizar_json_antes_de_pydantic(data)
                    
                    # Validar con Pydantic
                    return FichaLiterariaSchema(**data)
            except Exception as e_recovery:
                print(f"    -> No se pudo recuperar de la salida previa: {e_recovery}")
        
        print("    -> Iniciando fallback de extracción y parseo manual de JSON...")
        try:
            # Re-invocar de forma estándar y forzar JSON en las instrucciones
            system_prompt_fallback = system_prompt + "\nDebes responder UNICAMENTE con un objeto JSON válido que cumpla estrictamente con el esquema solicitado. No agregues texto adicional ni explicaciones."
            prompt_fallback = ChatPromptTemplate.from_messages([
                ("system", system_prompt_fallback),
                ("human", "Extrae la información de esta ficha literaria:\n\n{texto}")
            ])
            cadena_fallback = prompt_fallback | llm
            raw_response = cadena_fallback.invoke({"texto": texto_ficha})
            
            raw_text = raw_response.content if hasattr(raw_response, "content") else str(raw_response)
            
            # Buscar formato markdown ```json ... ```
            match = re.search(r"```json\s*(.*?)\s*```", raw_text, re.DOTALL)
            if match:
                json_str = match.group(1)
            else:
                # Buscar entre el primer { y el último }
                start = raw_text.find("{")
                end = raw_text.rfind("}")
                if start != -1 and end != -1:
                    json_str = raw_text[start:end+1]
                else:
                    json_str = raw_text
            
            data = json.loads(json_str)
            # Saneamiento de datos antes de Pydantic
            data = normalizar_json_antes_de_pydantic(data)
            
            return FichaLiterariaSchema(**data)
        except Exception as e_inner:
            print(f"❌ Falló el fallback de extracción manual: {e_inner}")
            raise e
