from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    resp = client.get("/health") 
    assert resp.status_code == 200

    data = resp.json() 
    assert data["status"] ==  "OK"
    assert "model" in data


def test_inference_ok():
    
    payload = {"text":"I love this!"}
    resp = client.post("/inference", json=payload)
    assert resp.status_code == 200 

    data = resp.json()
    assert "text" in data 
    assert "label" in data 
    assert "confidence" in data 
    assert data["label"] in ["positive","neutral","negative"]
    assert 0 <= data["confidence"]<= 1


def test_inference_empty_text():
    payload = {"text": ""}
    resp = client.post("/inference", json=payload) 
    assert resp.status_code == 422

