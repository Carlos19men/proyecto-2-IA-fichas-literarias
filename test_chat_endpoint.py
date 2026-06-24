import requests
import time
import sys

def test_chat():
    print("Testing /api/chat...")
    start = time.time()
    try:
        res = requests.post("http://127.0.0.1:8000/api/chat", json={"query": "Teresa", "history": []}, timeout=60)
        end = time.time()
        print(f"Status Code: {res.status_code}")
        print(f"Time taken: {end - start:.2f} seconds")
        print(res.json())
    except Exception as e:
        end = time.time()
        print(f"Error after {end - start:.2f} seconds: {e}")

if __name__ == "__main__":
    test_chat()
