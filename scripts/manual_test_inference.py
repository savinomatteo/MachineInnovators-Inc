"""Esegue manualmente una richiesta di inferenza alle API in locale"""

import requests

INFERENCE_URL = "http://localhost:8000/inference"

data = {"text": "I love this product"}

response = requests.post(INFERENCE_URL, json=data)

if response.status_code == 200:
    print("Risposta:", response.json())
else:
    print(f"Errore {response.status_code}: {response.json()}")
