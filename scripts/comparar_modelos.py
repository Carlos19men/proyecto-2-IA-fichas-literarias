"""
Comparativa de modelos Ollama para extracción de fichas literarias.
Corre la misma ficha contra los modelos indicados y reporta:
  - Tiempo de respuesta
  - Campos extraídos (obras, críticas, datos biográficos)
  - Puntuación simple de completitud

Uso:
    python scripts/comparar_modelos.py
    python scripts/comparar_modelos.py --ficha "data/Diccionario/Diccionario/Teresa Coraspe/ficha.md"
    python scripts/comparar_modelos.py --modelos llama3 qwen2.5:3b
"""

import argparse
import json
import sys
import time
import urllib.request

FICHA_DEFAULT = "data/Diccionario/Diccionario/Teresa Coraspe/ficha.md"
API = "http://127.0.0.1:8000/api/generar-ficha"
MODELOS_DEFAULT = ["llama3", "qwen2.5:3b"]


def llamar_api(texto: str, modelo: str) -> tuple[dict | None, float]:
    payload = json.dumps({"texto": texto, "modelo": modelo}).encode("utf-8")
    req = urllib.request.Request(
        API,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    inicio = time.time()
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read().decode())
        return data, round(time.time() - inicio, 2)
    except Exception as e:
        print(f"  ERROR con {modelo}: {e}")
        return None, round(time.time() - inicio, 2)


def puntuar(ficha: dict) -> dict:
    """Puntuación de completitud sobre 10 puntos."""
    autor = ficha.get("autor", {})
    puntos = 0
    detalles = {}

    campos_basicos = ["nombres", "apellidos", "sexo", "fecha_nacimiento", "genero_principal"]
    for c in campos_basicos:
        if autor.get(c):
            puntos += 1
    detalles["campos_basicos"] = f"{sum(1 for c in campos_basicos if autor.get(c))}/{len(campos_basicos)}"

    lugar = autor.get("lugar_nacimiento") or {}
    lugar_ok = sum(1 for k in ["ciudad", "estado", "pais"] if lugar.get(k))
    puntos += lugar_ok
    detalles["lugar_nacimiento"] = f"{lugar_ok}/3 campos"

    obras = autor.get("obras", [])
    puntos += min(len(obras), 1)
    detalles["obras"] = len(obras)

    criticas = autor.get("criticas", [])
    puntos += min(len(criticas), 1)
    detalles["criticas"] = len(criticas)

    mitos_mal = len(ficha.get("mitos_leyendas", []))
    detalles["mitos_mal_clasificados"] = mitos_mal
    if mitos_mal > 0:
        puntos -= 1

    detalles["total"] = f"{puntos}/10"
    return detalles


def main() -> int:
    parser = argparse.ArgumentParser(description="Comparar modelos Ollama en extracción de fichas")
    parser.add_argument("--ficha", default=FICHA_DEFAULT)
    parser.add_argument("--modelos", nargs="+", default=MODELOS_DEFAULT)
    args = parser.parse_args()

    with open(args.ficha, encoding="utf-8") as f:
        texto = f.read()

    print(f"\n{'='*60}")
    print(f"  Comparativa de modelos — LetraScopio PRO-27")
    print(f"  Ficha: {args.ficha}")
    print(f"{'='*60}\n")

    resultados = []
    for modelo in args.modelos:
        print(f"[{modelo}] Enviando ficha...")
        data, elapsed = llamar_api(texto, modelo)
        if data is None:
            resultados.append({"modelo": modelo, "tiempo": elapsed, "error": True})
            continue
        ficha = data.get("ficha", {})
        puntuacion = puntuar(ficha)
        resultados.append({"modelo": modelo, "tiempo": elapsed, "puntuacion": puntuacion})
        print(f"  Tiempo:  {elapsed}s")
        print(f"  Obras:   {puntuacion['obras']}")
        print(f"  Críticas:{puntuacion['criticas']}")
        print(f"  Campos:  {puntuacion['campos_basicos']}")
        print(f"  Lugar:   {puntuacion['lugar_nacimiento']}")
        print(f"  Mitos mal clasificados: {puntuacion['mitos_mal_clasificados']}")
        print(f"  PUNTUACION: {puntuacion['total']}\n")

    print(f"\n{'='*60}")
    print("  RESUMEN")
    print(f"{'='*60}")
    print(f"{'Modelo':<20} {'Tiempo':>8} {'Puntuación':>12}")
    print("-" * 44)
    for r in resultados:
        if r.get("error"):
            print(f"{r['modelo']:<20} {'ERROR':>8} {'--':>12}")
        else:
            print(f"{r['modelo']:<20} {r['tiempo']:>7}s {r['puntuacion']['total']:>12}")

    mejor = min(
        (r for r in resultados if not r.get("error")),
        key=lambda r: r["tiempo"],
        default=None,
    )
    if mejor:
        print(f"\n  Modelo más rápido: {mejor['modelo']} ({mejor['tiempo']}s)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
