import requests

url = "http://localhost:8000/inference"

data = {
    "text": "I love this product"
}

response = requests.post(url, json=data)

if response.status_code == 200:
    print("Risposta:", response.json())
else:
    print(f"Errore {response.status_code}: {response.json()}")