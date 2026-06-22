USE_OLLAMA = True
try:
    from langchain_ollama import ChatOllama
    from langchain_core.prompts import ChatPromptTemplate
except Exception:
    ChatOllama = None
    ChatPromptTemplate = None
    USE_OLLAMA = False

from src.config import Config
from src.ingestion.schemas import FichaLiterariaSchema, ObraSchema
import json
from datetime import datetime
import os


def extraer_json_de_ficha(texto_ficha: str) -> FichaLiterariaSchema:
    """
    Envía el texto crudo a Ollama (si está disponible) y fuerza una respuesta estructurada en JSON.

    Si Ollama no está disponible, cae en un extractor heurístico que NUNCA inventa datos:
    sólo extrae coincidencias literales simples del `texto_ficha`.
    """

    # Preparar cadenas/LLM si Ollama está disponible
    cadena = None
    cadena_plain = None
    prompt = None
    if USE_OLLAMA and ChatOllama is not None and ChatPromptTemplate is not None:
        llm = ChatOllama(
            base_url=Config.OLLAMA_BASE_URL,
            model=Config.OLLAMA_MODEL,
            temperature=0,
        )
        llm_estructurado = llm.with_structured_output(FichaLiterariaSchema)
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Eres un experto analista literario e historiador cultural.
Tu tarea es extraer información del texto y estructurarla exactamente como se te pide.

REGLAS INDISPENSABLES:
- Solo extrae información que esté literalmente presente en el texto provisto.
- Para `obras` y `criticas`: solo devuélvelas si puedes señalar un fragmento del texto original
  que las respalde (coincidencia literal de título, autor, o referencia). Si no existe
  evidencia textual en el `texto` suministrado, devuelve la lista vacía `[]` para ese campo.
- Nombres y apellidos: Separar en `nombres` y `apellidos`.
- Fechas: Usar formato `YYYY` o `YYYY-MM-DD`; usar `null`/`None` si no aparece.
- No inventar: Bajo ninguna circunstancia agregues autores, títulos, fechas o referencias
  que no aparezcan en el texto proporcionado. Si dudas, omite el elemento (usa `[]`).
- Responde SOLO en la estructura JSON/Pydantic solicitada; no incluyas explicaciones adicionales.
"""),
            ("human", "Extrae la información de esta ficha literaria:\n\n{texto}"),
        ])
        cadena = prompt | llm_estructurado
        llm_plain = ChatOllama(base_url=Config.OLLAMA_BASE_URL, model=Config.OLLAMA_MODEL, temperature=0)
        cadena_plain = prompt | llm_plain


    def _dump_raw_output(raw_text: str) -> None:
        logs_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        fname = f"extractor_raw_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.txt"
        path = os.path.join(logs_dir, fname)
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(raw_text)
            print(f"⚠️  Raw model output written to: {path}")
        except Exception as e:
            print(f"⚠️  No se pudo escribir raw output: {e}")


    def _dump_structured_output(obj) -> None:
        logs_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(logs_dir, exist_ok=True)
        fname = f"extractor_structured_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.json"
        path = os.path.join(logs_dir, fname)
        try:
            try:
                payload = obj.model_dump()
            except Exception:
                payload = obj
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(json.dumps(payload, ensure_ascii=False, indent=2))
            print(f"⚠️  Structured model output written to: {path}")
        except Exception as e:
            print(f"⚠️  No se pudo escribir structured output: {e}")


    def _serialize_raw(raw) -> str:
        try:
            if raw is None:
                return ""
            if isinstance(raw, str):
                return raw
            content = getattr(raw, "content", None)
            if content:
                return content if isinstance(content, str) else str(content)
            if isinstance(raw, (list, tuple)):
                parts = []
                for item in raw:
                    c = getattr(item, "content", None)
                    parts.append(c if isinstance(c, str) else str(item))
                return "\n---\n".join(parts)
            if isinstance(raw, dict):
                return json.dumps(raw, ensure_ascii=False, indent=2)
            return str(raw)
        except Exception as e:
            return f"(error serializing raw: {e})"


    try:
        # Invocar al LLM estructurado si está disponible
        if cadena is not None:
            resultado = cadena.invoke({"texto": texto_ficha})
        else:
            # Fallback heurístico que evita inventar datos: solo captura patrones literales
            import re

            texto_lower = (texto_ficha or "").strip()
            m = re.search(r"^(?:Autor|Autor:|Autor\.|Autor\s)\s*(.+)$", texto_ficha, flags=re.IGNORECASE | re.MULTILINE)
            if m:
                nombre_completo = m.group(1).strip()
                parts = nombre_completo.split()
                nombres = " ".join(parts[:-1]) if len(parts) > 1 else parts[0]
                apellidos = parts[-1] if len(parts) > 1 else ""
            else:
                nombres = ""
                apellidos = ""

            autor = {
                "nombres": nombres,
                "apellidos": apellidos,
                "nombre_completo": f"{nombres} {apellidos}".strip(),
                "sexo": "Desconocido",
                "genero_principal": "desconocido",
                "familiares_destacados": [],
                "multimedia": [],
                "obras": [],
                "criticas": [],
            }
            resultado = FichaLiterariaSchema(autor=autor)

        # Post-procesamiento estricto: eliminar obras/criticas que no tengan evidencia literal
        try:
            texto_lower = (texto_ficha or "").lower()
            removed_local = {"obras": [], "criticas": []}

            obras_keep = []
            for obra in getattr(resultado.autor, "obras", []) or []:
                titulo = (getattr(obra, "titulo", "") or "").lower()
                descripcion = (getattr(obra, "descripcion", "") or "").lower()
                if titulo and titulo in texto_lower:
                    obras_keep.append(obra)
                elif descripcion and descripcion[:40] and descripcion[:40] in texto_lower:
                    obras_keep.append(obra)
                else:
                    removed_local["obras"].append({"titulo": getattr(obra, "titulo", None)})
            resultado.autor.obras = obras_keep

            crit_keep = []
            for critica in getattr(resultado.autor, "criticas", []) or []:
                autor_c = (getattr(critica, "autor", "") or "").lower()
                titulo_c = (getattr(critica, "titulo", "") or "").lower()
                referencia = (getattr(critica, "referencia_bibliografica", "") or "").lower()
                descripcion = (getattr(critica, "descripcion_resumen", "") or "").lower()
                if any(t and t in texto_lower for t in (autor_c, titulo_c, referencia)):
                    crit_keep.append(critica)
                elif descripcion and descripcion[:60] and descripcion[:60] in texto_lower:
                    crit_keep.append(critica)
                else:
                    removed_local["criticas"].append({"titulo": getattr(critica, "titulo", None), "autor": getattr(critica, "autor", None)})
            resultado.autor.criticas = crit_keep

            if removed_local["obras"] or removed_local["criticas"]:
                try:
                    logs_dir = os.path.join(os.getcwd(), "logs")
                    os.makedirs(logs_dir, exist_ok=True)
                    fname = f"extractor_pruned_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.json"
                    path = os.path.join(logs_dir, fname)
                    with open(path, "w", encoding="utf-8") as fh:
                        fh.write(json.dumps({"removed": removed_local}, ensure_ascii=False, indent=2))
                    print(f"⚠️  Extractor pruned items; report: {path}")
                except Exception:
                    pass
        except Exception:
            pass

        # Heurística de verificación básica: asegurarnos que el autor y el nombre existan
        try:
            autor = resultado.autor
            nombres = getattr(autor, "nombres", None)
            apellidos = getattr(autor, "apellidos", None)
        except Exception:
            nombres = apellidos = None

        # Generar y adjuntar resumen biográfico (`text`) para persistencia y búsquedas
        try:
            autor_obj = resultado.autor
            parts = []
            name = f"{getattr(autor_obj, 'nombres', '') or ''} {getattr(autor_obj, 'apellidos', '') or ''}".strip()
            if name:
                parts.append(f"{name}.")
            if getattr(autor_obj, 'seudonimo', None):
                parts.append(f"Conocido como {autor_obj.seudonimo}.")
            if getattr(autor_obj, 'actividad_relevante', None):
                parts.append(str(autor_obj.actividad_relevante))
            if getattr(autor_obj, 'contexto_vivio', None):
                parts.append(f"Vivio en el contexto: {autor_obj.contexto_vivio}")
            if getattr(autor_obj, 'tematica_principal', None):
                parts.append(f"Temas principales: {autor_obj.tematica_principal}")

            bio_texto = " ".join(p for p in parts if p).strip()
            resultado.autor.text = bio_texto or None

        except Exception:
            pass

        # Si faltan `actividad_relevante` o `contexto_vivio`, intentar heurística segura
        try:
            import re

            act = getattr(resultado.autor, "actividad_relevante", None)
            ctx = getattr(resultado.autor, "contexto_vivio", None)

            # Normalizar listas devueltas por el modelo
            if isinstance(act, (list, tuple)):
                act = ", ".join(str(x) for x in act if x)
            if isinstance(ctx, (list, tuple)):
                ctx = ", ".join(str(x) for x in ctx if x)

            text_src = (texto_ficha or "").strip()
            sentences = re.split(r'(?<=[\.!?])\s+', text_src)

            activity_keywords = [
                "fue", "trabajó", "trabajo", "se desempeñó", "ocupó", "director", "profesor",
                "periodista", "diplomat", "estudió", "graduado", "ejerció", "colaboró", "editor",
            ]
            context_keywords = ["vivió en", "residió en", "nació en", "en el contexto", "vivio en", "residio en", "durante"]

            if not act:
                # Prioridad: buscar encabezado explícito como 'Actividad relevante que haya realizado el autor'
                m_header = re.search(r"actividad\s+relevante(?:\s+que\s+haya\s+realizado\s+el\s+autor)?\s*[:\-–]?\s*(.+?)(?:\n\s*\n|$)", texto_ficha, flags=re.IGNORECASE | re.DOTALL)
                if m_header:
                    resultado.autor.actividad_relevante = m_header.group(1).strip()
                else:
                    found_act = []
                    for s in sentences:
                        sl = s.lower()
                        if any(k in sl for k in activity_keywords):
                            found_act.append(s.strip())
                    if found_act:
                        resultado.autor.actividad_relevante = " ".join(found_act).strip()

            if not ctx:
                found_ctx = []
                for s in sentences:
                    sl = s.lower()
                    if any(k in sl for k in context_keywords) or re.search(r'naci[oó] en|residi[oó] en|vivio en|vivió en', sl):
                        found_ctx.append(s.strip())
                if found_ctx:
                    resultado.autor.contexto_vivio = " ".join(found_ctx).strip()
        except Exception:
            pass
        except Exception:
            pass

        # Además, capturamos siempre la salida cruda del modelo y la salida estructurada
        try:
            if cadena_plain is not None:
                raw = cadena_plain.invoke({"texto": texto_ficha})
                raw_text = _serialize_raw(raw)
                _dump_raw_output(raw_text)
            else:
                _dump_raw_output("(raw output not available; no LLM present)")
        except Exception as e:
            print(f"⚠️  No se pudo obtener la salida cruda del modelo: {e}")

        try:
            _dump_structured_output(resultado)
        except Exception as e:
            print(f"⚠️  No se pudo volcar la salida estructurada: {e}")

        return resultado

    except Exception as exc:
        mensaje = str(exc).lower()
        if "not found" in mensaje and "model" in mensaje and prompt is not None and ChatOllama is not None:
            fallback_models = ["llama3", "qwen2.5", "qwen2.5:3b"]
            for fallback in fallback_models:
                if fallback == Config.OLLAMA_MODEL:
                    continue
                try:
                    print(f"⚠️  Modelo '{Config.OLLAMA_MODEL}' no encontrado; intentando fallback '{fallback}'.")
                    llm_f = ChatOllama(
                        base_url=Config.OLLAMA_BASE_URL,
                        model=fallback,
                        temperature=0,
                    )
                    llm_f_estruct = llm_f.with_structured_output(FichaLiterariaSchema)
                    cadena_f = prompt | llm_f_estruct
                    resultado = cadena_f.invoke({"texto": texto_ficha})
                    return resultado
                except Exception:
                    continue
        # En caso de otro error, intentar capturar la salida cruda para diagnóstico
        try:
            if 'cadena_plain' in locals() and cadena_plain is not None:
                raw = cadena_plain.invoke({"texto": texto_ficha})
                raw_text = json.dumps(raw, ensure_ascii=False, indent=2) if not isinstance(raw, str) else raw
            else:
                raw_text = f"(error obtaining raw response: {exc})"
        except Exception as e:
            raw_text = f"(error obtaining raw response: {e})"
        print("⚠️  Error durante la extracción estructurada. Guardando salida cruda para inspección.")
        _dump_raw_output(raw_text)
        raise
