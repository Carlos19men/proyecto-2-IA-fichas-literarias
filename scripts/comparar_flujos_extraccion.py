"""
Comparativa de flujos de extracción: PRO-27 vs rama Fichas_JSON.

PRO-27: endpoint / drag-and-drop → extraer_ficha_desde_texto + markdown_parser
Fichas_JSON: preprocess → chunking → extractor → validator → field_mapping

Uso:
    python scripts/comparar_flujos_extraccion.py
    python scripts/comparar_flujos_extraccion.py --carpeta "data/Diccionario/Diccionario/Teresa Coraspe"
    python scripts/comparar_flujos_extraccion.py --worktree ../IA-fichas-json-worktree
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
CARPETAS_CANDIDATAS = [
    "data/Diccionario/Diccionario/Montes, Ramón Isidro",
    "Diccionario/Diccionario/Montes, Ramón Isidro",
    "data/Diccionario/Diccionario/Teresa Coraspe",
]
WORKTREE_DEFAULT = ROOT.parent / "IA-fichas-json-worktree"
SALIDA_DIR = ROOT / "data" / "cargar"


def resolver_carpeta(explicita: str | None) -> Path:
    if explicita:
        p = Path(explicita)
        if not p.is_absolute():
            p = ROOT / p
        if not p.exists():
            raise FileNotFoundError(f"Carpeta no encontrada: {p}")
        return p

    for rel in CARPETAS_CANDIDATAS:
        p = ROOT / rel
        if p.exists():
            return p

    raise FileNotFoundError(
        "No hay carpeta de ficha disponible. Coloca Montes en "
        "data/Diccionario/Diccionario/Montes, Ramón Isidro o pasa --carpeta."
    )


def leer_texto_carpeta(carpeta: Path) -> str:
    try:
        from src.ingestion.loders2 import leer_texto_principal

        texto, _ = leer_texto_principal(str(carpeta))
        return texto
    except (ImportError, ValueError):
        pass

    from src.ingestion.loaders import leer_archivo_ficha

    for pattern in ("ficha.md", "*.md", "*.docx", "*.pdf"):
        matches = sorted(carpeta.glob(pattern))
        if matches:
            return leer_archivo_ficha(str(matches[0]))

    raise FileNotFoundError(f"No hay archivo de texto en {carpeta}")


def puntuar(ficha: dict) -> dict:
    autor = ficha.get("autor", {})
    puntos = 0
    campos_basicos = ["nombres", "apellidos", "sexo", "fecha_nacimiento", "genero_principal"]
    puntos += sum(1 for c in campos_basicos if autor.get(c))
    lugar = autor.get("lugar_nacimiento") or {}
    puntos += sum(1 for k in ("ciudad", "estado", "pais") if lugar.get(k))
    puntos += min(len(autor.get("obras", [])), 1)
    puntos += min(len(autor.get("criticas", [])), 1)
    if ficha.get("mitos_leyendas"):
        puntos -= 1
    return {
        "puntos": f"{puntos}/10",
        "obras": len(autor.get("obras", [])),
        "criticas": len(autor.get("criticas", [])),
        "chunks": len(ficha.get("chunks", [])),
        "multimedia": len(autor.get("multimedia", [])),
        "mitos_mal": len(ficha.get("mitos_leyendas", [])),
    }


def flujo_pro27(texto: str, modelo: str) -> tuple[dict, float]:
    from src.busqueda.api import extraer_ficha_desde_texto

    inicio = time.time()
    ficha = extraer_ficha_desde_texto(texto, modelo=modelo)
    return ficha, round(time.time() - inicio, 2)


def flujo_fichas_json(carpeta: Path, worktree: Path) -> tuple[dict | None, float, str]:
    if not worktree.exists():
        return None, 0.0, f"Worktree no encontrado: {worktree}"

    script = r"""
import json, sys
from pathlib import Path
from src.ingestion.pipeline import procesar_carpeta

carpeta = sys.argv[1]
ficha = procesar_carpeta(
    carpeta,
    session=None,
    generar_embeddings=False,
    insertar_neo4j=False,
)
if ficha is None:
    raise SystemExit(1)
print(json.dumps(ficha.model_dump(exclude_none=True), ensure_ascii=False))
"""
    inicio = time.time()
    proc = subprocess.run(
        [sys.executable, "-c", script, str(carpeta)],
        cwd=worktree,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=600,
        env={
            **os.environ,
            "PYTHONPATH": str(worktree),
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUTF8": "1",
        },
    )
    elapsed = round(time.time() - inicio, 2)
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "error desconocido")[-2000:]
        return None, elapsed, err

    lineas = [ln for ln in proc.stdout.splitlines() if ln.strip().startswith("{")]
    if not lineas:
        return None, elapsed, "Sin JSON en stdout del pipeline Fichas_JSON"
    return json.loads(lineas[-1]), elapsed, ""


def tabla_comparativa(pro27: dict, fichas_json: dict | None) -> str:
    filas = [
        ("Aspecto", "PRO-27", "Fichas_JSON"),
        ("---", "---", "---"),
        ("Entrada", "Texto plano (web/API)", "Carpeta con preprocess + loaders"),
        ("Post-proceso LLM", "markdown_parser (obras/críticas)", "validator + field_mapping + autor_parser"),
        ("Chunks vectoriales", "No", "Sí (chunking.py)"),
        ("Multimedia en schema", "No (stub frontend PRO-22)", "Sí (adjuntar_multimedia_carpeta)"),
        ("Embeddings / Neo4j", "No en este flujo", "Opcional en pipeline"),
        ("Tiempo (s)", str(pro27.get("tiempo", "?")), str(fichas_json.get("tiempo", "?") if fichas_json else "N/A")),
        ("Puntuación", pro27.get("puntuacion", {}).get("puntos", "?"), fichas_json.get("puntuacion", {}).get("puntos", "?") if fichas_json else "N/A"),
        ("Obras", str(pro27.get("puntuacion", {}).get("obras", "?")), str(fichas_json.get("puntuacion", {}).get("obras", "?") if fichas_json else "N/A")),
        ("Críticas", str(pro27.get("puntuacion", {}).get("criticas", "?")), str(fichas_json.get("puntuacion", {}).get("criticas", "?") if fichas_json else "N/A")),
    ]
    lineas = ["| " + " | ".join(c) + " |" for c in filas]
    return "\n".join(lineas)


def main() -> int:
    parser = argparse.ArgumentParser(description="Comparar flujos PRO-27 vs Fichas_JSON")
    parser.add_argument("--carpeta", help="Ruta a carpeta de ficha")
    parser.add_argument("--modelo", default="llama3")
    parser.add_argument("--worktree", default=str(WORKTREE_DEFAULT))
    parser.add_argument("--salida", default=str(SALIDA_DIR))
    args = parser.parse_args()

    carpeta = resolver_carpeta(args.carpeta)
    worktree = Path(args.worktree)
    salida = Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print("  Comparativa de flujos — PRO-27 vs Fichas_JSON")
    print(f"  Carpeta: {carpeta.name}")
    print(f"{'='*60}\n")

    texto = leer_texto_carpeta(carpeta)
    print(f"[PRO-27] Extrayendo ({len(texto)} chars, modelo={args.modelo})...")
    ficha_pro27, t_pro27 = flujo_pro27(texto, args.modelo)
    score_pro27 = puntuar(ficha_pro27)
    print(f"  Tiempo: {t_pro27}s | {score_pro27}\n")

    print(f"[Fichas_JSON] Pipeline en {worktree}...")
    ficha_json, t_json, err_json = flujo_fichas_json(carpeta, worktree)
    if ficha_json:
        score_json = puntuar(ficha_json)
        print(f"  Tiempo: {t_json}s | {score_json}\n")
    else:
        score_json = None
        print(f"  ERROR: {err_json}\n")

    slug = carpeta.name.replace(" ", "_").replace(",", "")
    path_pro27 = salida / f"{slug}_pro27.json"
    path_json = salida / f"{slug}_fichas_json.json"
    path_tabla = salida / f"{slug}_comparativa.md"

    path_pro27.write_text(json.dumps(ficha_pro27, ensure_ascii=False, indent=2), encoding="utf-8")
    if ficha_json:
        path_json.write_text(json.dumps(ficha_json, ensure_ascii=False, indent=2), encoding="utf-8")

    resumen_pro27 = {"tiempo": t_pro27, "puntuacion": score_pro27}
    resumen_json = {"tiempo": t_json, "puntuacion": score_json} if ficha_json else None
    tabla = tabla_comparativa(resumen_pro27, resumen_json)
    path_tabla.write_text(
        f"# Comparativa: {carpeta.name}\n\n{tabla}\n\n"
        f"## Recomendación\n\n"
        f"- **PRO-27**: ideal para carga manual desde el front (drag-and-drop) y pruebas rápidas vía API.\n"
        f"- **Fichas_JSON**: pipeline batch completo (preprocess, chunks, multimedia, validación) para ingesta a Neo4j.\n"
        f"- **Combinar**: usar preprocess + loaders de Fichas_JSON en el front; post-LLM aplicar markdown_parser de PRO-27.\n",
        encoding="utf-8",
    )

    print(tabla)
    print(f"\nJSON PRO-27:     {path_pro27}")
    if ficha_json:
        print(f"JSON Fichas_JSON: {path_json}")
    print(f"Tabla:           {path_tabla}")

    return 0 if ficha_json else 1


if __name__ == "__main__":
    raise SystemExit(main())
