"""Test automatici degli endpoint FastAPI"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    """Verifica che l'endpoint health risponda correttamente"""
    resp = client.get("/health")
    assert resp.status_code == 200

    data = resp.json()
    assert data["status"] == "OK"
    assert "model" in data


def test_inference_ok():
    """Verifica una predizione valida"""

    payload = {"text": "I love this!"}
    resp = client.post("/inference", json=payload)
    assert resp.status_code == 200

    data = resp.json()
    assert "text" in data
    assert "label" in data
    assert "confidence" in data
    assert data["label"] in ["positive", "neutral", "negative"]
    assert 0 <= data["confidence"] <= 1


def test_inference_empty_text():
    """Verifica il rifiuto di un testo vuoto"""
    payload = {"text": ""}
    resp = client.post("/inference", json=payload)
    assert resp.status_code == 422


def test_inference_empty_message():
    """Verifica il rifiuto di un payload senza il campo text"""
    response = client.post("/inference", json={})

    assert response.status_code == 422
