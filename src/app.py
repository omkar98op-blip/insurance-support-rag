"""FastAPI service exposing the grounded support assistant."""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .config import settings
from .generate import answer as generate_answer
from .ingest import build_index

app = FastAPI(
    title="Insurance Support RAG",
    description="Retrieval-grounded support assistant over a knowledge base, with groundedness guardrails.",
    version="1.0.0",
)


class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    top_k: int | None = Field(default=None, ge=1, le=10)
    category: str | None = None


class Citation(BaseModel):
    article_id: str
    title: str
    chunk_id: str
    distance: float


class QueryResponse(BaseModel):
    answer: str
    refused: bool
    grounded: bool
    coverage: float
    backend: str
    citations: list[Citation]


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "backend": settings.llm_backend, "top_k": settings.top_k}


@app.post("/ingest")
def ingest() -> dict:
    count = build_index()
    return {"indexed_chunks": count}


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    try:
        result = generate_answer(request.question, top_k=request.top_k, category=request.category)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return QueryResponse(
        answer=result.text,
        refused=result.refused,
        grounded=result.grounded,
        coverage=result.coverage,
        backend=result.backend,
        citations=[
            Citation(article_id=p.article_id, title=p.title, chunk_id=p.chunk_id,
                     distance=round(p.distance, 4))
            for p in result.passages
        ],
    )
