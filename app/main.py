from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .agent import answer_question
from .tools import get_schema_metadata

app = FastAPI(title="NL-SQL Agent", version="0.1.0")


class AskRequest(BaseModel):
    question: str


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.get("/schema")
def schema():
    return get_schema_metadata()


@app.post("/ask")
def ask(req: AskRequest):
    try:
        result = answer_question(req.question)
        return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
