"""Retrieval over the FAISS index, with a distance floor so irrelevant hits are dropped."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

from .config import settings


@dataclass
class Passage:
    text: str
    article_id: str
    title: str
    chunk_id: str
    distance: float

    def citation(self) -> str:
        return f"[{self.article_id}] {self.title}"


@lru_cache(maxsize=1)
def _store() -> FAISS:
    embeddings = HuggingFaceEmbeddings(model_name=settings.embedding_model)
    return FAISS.load_local(
        str(settings.index_dir), embeddings, allow_dangerous_deserialization=True
    )


def retrieve(question: str, top_k: int | None = None, category: str | None = None) -> list[Passage]:
    """Return passages above the relevance threshold, closest first.

    An empty list is a valid, meaningful result: it means the knowledge base
    does not cover the question, and the generator must refuse rather than guess.
    """
    top_k = top_k or settings.top_k
    # Over-fetch when filtering so the filter does not starve the result set.
    fetch = top_k * 4 if category else top_k
    hits = _store().similarity_search_with_score(question, k=fetch)

    passages: list[Passage] = []
    for doc, distance in hits:
        if distance > settings.max_distance:
            continue
        if category and doc.metadata.get("category") != category:
            continue
        passages.append(
            Passage(
                text=doc.page_content.strip(),
                article_id=doc.metadata.get("article_id", "unknown"),
                title=doc.metadata.get("title", "untitled"),
                chunk_id=doc.metadata.get("chunk_id", ""),
                distance=float(distance),
            )
        )
    return passages[:top_k]
