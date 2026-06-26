"""Prueba rápida del endpoint POST /api/generar-ficha."""
import json
import sys
import urllib.request

FICHA = "data/Diccionario/Diccionario/Teresa Coraspe/ficha.md"
API = "http://127.0.0.1:8000/api/generar-ficha"


def main() -> int:
    with open(FICHA, encoding="utf-8") as f:
        texto = f.read()

    payload = json.dumps({"texto": texto, "modelo": "llama3"}).encode("utf-8")
    req = urllib.request.Request(
        API,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    print(f"POST {API} ({len(texto)} chars)...")
    with urllib.request.urlopen(req, timeout=300) as resp:
        data = json.loads(resp.read().decode())

    print(f"modelo_usado: {data.get('modelo_usado')}")
    ficha = data.get("ficha", {})
    autor = ficha.get("autor", {})
    print(f"autor: {autor.get('nombres')} {autor.get('apellidos')}")
    print(f"obras: {len(autor.get('obras', []))}")
    print(f"criticas: {len(autor.get('criticas', []))}")
    print(json.dumps(data, ensure_ascii=False, indent=2)[:2000])
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise SystemExit(1)
