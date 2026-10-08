"""API FastAPI"""

import asyncio
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query, Request
from pydantic import BaseModel
from .model import classifier, MODEL_NAME
from .monitoring import (
    get_history,
    get_summary,
    record_prediction,
    record_request,
    save_snapshot,
    record_text,
    snapshot_loop,
)



@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Avvia il salvataggio periodico degli snapshot insieme all'app"""
    task = asyncio.create_task(snapshot_loop())
    yield
    task.cancel()


app = FastAPI(lifespan=lifespan)
MONITORING_PATHS = {
    "/monitoring/summary",
    "/monitoring/history",
    "/monitoring/snapshot",
    "/health",
}


class InferenceRequest(BaseModel):
    """Payload richiesto dall'endpoint del modello"""

    text: str


@app.middleware("http")
async def monitoring_middleware(request: Request, call_next):
    """Registra numero richieste, errori e tempo di risposta"""
    if request.url.path in MONITORING_PATHS:
        return await call_next(request)

    start = time.time()

    try:
        response = await call_next(request)
    except Exception:
        latency_ms = (time.time() - start) * 1000
        record_request(status_code=500, latency_ms=latency_ms)
        raise

    latency_ms = (time.time() - start) * 1000

    record_request(status_code=response.status_code, latency_ms=latency_ms)

    return response


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
        print("Risultato modello:", result)
        record_text(request.text)
        record_prediction(result["label"], result["confidence"])
        return result
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=422, detail=str(exc)
        ) from exc  # Input non valido -> 422


@app.get("/monitoring/summary")
async def monitoring_summary():
    """Restituisce le metriche aggregate dall'avvio del servizio"""
    return get_summary()


@app.post("/monitoring/snapshot")
async def monitoring_snapshot():
    """Forza il salvataggio di uno snapshot senza attendere il prossimo intervallo"""
    return save_snapshot()


@app.get("/monitoring/history")
async def monitoring_history(minutes: float | None = Query(default=None, gt=0)):
    """Restituisco lo storico a Grafana che lo usera per creare il grafico.
    Con minutes restituisce solo gli snapshot degli ultimi N minuti"""
    return get_history(minutes)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
