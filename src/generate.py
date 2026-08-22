"""Grounded answer generation with citations and a refusal path."""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from .config import settings
from .guardrails import REFUSAL, check_groundedness
from .retriever import Passage, retrieve

SYSTEM_PROMPT = """You are a technical support assistant for an insurance carrier.

Rules, in priority order:
1. Answer ONLY from the CONTEXT passages provided. Never use outside knowledge.
2. If the context does not contain the answer, reply exactly: "{refusal}"
3. Cite the article id in square brackets after each claim, e.g. [KB-002].
4. Preserve procedures step by step and in order. Do not reorder or merge steps.
5. Do not soften or omit stated limits, timeouts, or escalation criteria.
6. Be concise. No preamble.""".format(refusal=REFUSAL)

USER_TEMPLATE = """CONTEXT:
{context}

QUESTION: {question}

Answer using only the context above."""


@dataclass
class Answer:
    text: str
    citations: list[str] = field(default_factory=list)
    passages: list[Passage] = field(default_factory=list)
    grounded: bool = True
    coverage: float = 1.0
    refused: bool = False
    backend: str = "extractive"


def _format_context(passages: list[Passage]) -> str:
    return "\n\n".join(f"[{p.article_id}] {p.title}\n{p.text}" for p in passages)


def _extractive(question: str, passages: list[Passage]) -> str:
    """Zero-dependency fallback: return the top passage with its citation.

    Keeps the service demoable and the eval suite runnable without an API key,
    and gives the eval harness a baseline to score the LLM backends against.
    """
    top = passages[0]
    return f"{top.text}\n\n[{top.article_id}]"


def _anthropic(question: str, context: str) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model=settings.llm_model,
        max_tokens=700,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": USER_TEMPLATE.format(context=context, question=question)}],
    )
    return message.content[0].text.strip()


def _openai(question: str, context: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    completion = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_TEMPLATE.format(context=context, question=question)},
        ],
    )
    return completion.choices[0].message.content.strip()


def answer(question: str, top_k: int | None = None, category: str | None = None) -> Answer:
    passages = retrieve(question, top_k=top_k, category=category)

    # No passage cleared the relevance threshold: refuse. This is the single
    # most valuable behaviour in a support assistant — a confident wrong answer
    # costs more than an escalation.
    if not passages:
        return Answer(text=REFUSAL, refused=True, grounded=True, coverage=1.0,
                      backend=settings.llm_backend)

    context = _format_context(passages)
    backend = settings.llm_backend

    if backend == "anthropic":
        text = _anthropic(question, context)
    elif backend == "openai":
        text = _openai(question, context)
    else:
        text = _extractive(question, passages)

    if text.strip() == REFUSAL:
        return Answer(text=REFUSAL, refused=True, passages=passages, backend=backend)

    check = check_groundedness(text, context)
    return Answer(
        text=text,
        citations=sorted({p.article_id for p in passages}),
        passages=passages,
        grounded=check.grounded,
        coverage=check.coverage,
        backend=backend,
    )
