"""
Script de prueba para la API de LetraScopio.

Envía consultas de ejemplo al endpoint POST /api/chat
y valida que el JSON de respuesta cumpla con el formato esperado.

Uso:
    python test_api.py
"""

import json
import sys

try:
    import requests
except ImportError:
    print("Instalando 'requests' para las pruebas...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests


API_URL = "http://localhost:8000"


def test_health():
    """Verifica que el servidor esté corriendo."""
    print("\n" + "=" * 60)
    print("🧪 TEST 1: Health check")
    print("=" * 60)

    try:
        r = requests.get(f"{API_URL}/", timeout=5)
        assert r.status_code == 200, f"Status inesperado: {r.status_code}"
        data = r.json()
        assert data.get("status") == "ok"
        print(f"   ✅ Servidor respondió: {data}")
    except requests.ConnectionError:
        print("   ❌ No se pudo conectar al servidor.")
        print("      → ¿Está corriendo? Ejecuta: uvicorn src.api:app --reload --port 8000")
        sys.exit(1)


def test_chat_query(query: str, expect_metadata: bool = False):
    """Envía una consulta al endpoint /api/chat y valida la respuesta."""
    print(f"\n{'─' * 60}")
    print(f"📝 Query: \"{query}\"")
    print(f"{'─' * 60}")

    payload = {
        "query": query,
        "history": [],
    }

    r = requests.post(f"{API_URL}/api/chat", json=payload, timeout=120)
    assert r.status_code == 200, f"Status inesperado: {r.status_code}"

    data = r.json()

    # Validar campos requeridos
    assert "respuesta_texto" in data, "Falta 'respuesta_texto' en la respuesta"
    assert "relatedQuestions" in data, "Falta 'relatedQuestions' en la respuesta"
    assert isinstance(data["relatedQuestions"], list), "'relatedQuestions' debe ser una lista"

    print(f"   📄 Respuesta: {data['respuesta_texto'][:150]}...")
    print(f"   🔗 Preguntas relacionadas: {data['relatedQuestions']}")

    if data.get("metadata"):
        m = data["metadata"]
        print(f"   🎴 Metadata encontrada:")
        print(f"      Nombre: {m.get('nombre')}")
        print(f"      Disciplina: {m.get('disciplina')}")
        print(f"      Periodo: {m.get('periodo')}")
        print(f"      Lugar: {m.get('lugar')}")
        print(f"      Imágenes: {len(m.get('imagenes') or [])}")
        print(f"      Audios: {len(m.get('audios') or [])}")
        print(f"      PDFs: {len(m.get('pdfs') or [])}")
    else:
        print("   🎴 Sin metadata (respuesta solo texto)")

    if expect_metadata:
        assert data.get("metadata") is not None, "Se esperaba metadata pero no vino"
        print("   ✅ Metadata validada correctamente")

    return data


def test_chat_with_history():
    """Verifica que el historial de conversación se envíe correctamente."""
    print(f"\n{'=' * 60}")
    print("🧪 TEST 3: Chat con historial")
    print("=" * 60)

    payload = {
        "query": "¿Qué obras escribió?",
        "history": [
            {"role": "user", "content": "¿Quién fue Jean Aristeguieta?"},
            {"role": "assistant", "content": "Jean Aristeguieta fue una poetisa del Estado Bolívar..."},
        ],
    }

    r = requests.post(f"{API_URL}/api/chat", json=payload, timeout=120)
    assert r.status_code == 200, f"Status inesperado: {r.status_code}"

    data = r.json()
    assert "respuesta_texto" in data
    print(f"   📄 Respuesta con contexto: {data['respuesta_texto'][:150]}...")
    print("   ✅ Historial procesado correctamente")


def main():
    print("\n🚀 Iniciando pruebas de la API de LetraScopio")
    print(f"   Servidor: {API_URL}\n")

    # Test 1: Health
    test_health()

    # Test 2: Consultas de ejemplo
    print(f"\n{'=' * 60}")
    print("🧪 TEST 2: Consultas al chat")
    print("=" * 60)

    consultas = [
        ("Jean Aristeguieta", True),
        ("Gemas de Guayana", False),
        ("Serpiente de Siete Cabezas", False),
        ("poesía del Orinoco", False),
    ]

    for query, expect_meta in consultas:
        try:
            test_chat_query(query, expect_metadata=expect_meta)
        except AssertionError as e:
            print(f"   ⚠️  Assertion fallida: {e}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

    # Test 3: Historial
    try:
        test_chat_with_history()
    except Exception as e:
        print(f"   ❌ Error en test de historial: {e}")

    print(f"\n{'=' * 60}")
    print("🎉 Pruebas completadas.")
    print("=" * 60)


if __name__ == "__main__":
    main()
