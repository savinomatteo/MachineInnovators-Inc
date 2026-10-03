"""API FastAPI"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .model import classifier, MODEL_NAME

app = FastAPI()


class InferenceRequest(BaseModel):
    """Payload richiesto dall'endpoint del modello"""

    text: str


@app.get("/health")
async def health():
    """Restituisce lo stato del servizio e il nome del  modello"""
    return {
        "status": "OK",
        "model": MODEL_NAME,
    }


@app.post("/inference")
async def inference(request: InferenceRequest):
    """Classifica il sentiment del testo ricevuto"""
    try:
        result = classifier.predict(request.text)
        return result
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=422, detail=str(exc)
        ) from exc  # Input non valido -> 422


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
