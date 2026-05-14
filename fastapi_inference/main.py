from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="AEAIOS Inference Service")


class InferenceRequest(BaseModel):
    task: str
    text: str | None = None


@app.get("/health")
def health():
    return {"status": "ok", "service": "fastapi-inference"}


@app.post("/infer")
def infer(request: InferenceRequest):
    return {"task": request.task, "result": {"summary": (request.text or "")[:500], "confidence": 0.75}}
