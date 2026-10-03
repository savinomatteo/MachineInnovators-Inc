from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .model import classifier, MODEL_NAME

app = FastAPI()

class InferenceRequest(BaseModel): 
    text: str

@app.get("/health")
async def health():
    return {
        "status": "OK",
        "model": MODEL_NAME,
    }


@app.post("/inference")
async def inference(request: InferenceRequest):
    try:
        result = classifier.predict(request.text) 
        return result 
    except (ValueError, TypeError) as exc:
        # Input non valido -> 422
        raise HTTPException(status_code=422, detail=str(exc))   


if __name__ == "__main__":
    import uvicorn 
    uvicorn.run(app, host="0.0.0.0", port=8000)