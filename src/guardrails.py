"""Groundedness checks applied to a generated answer before it is returned."""
from __future__ import annotations

import re
from dataclasses import dataclass

STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "is", "are", "for", "on",
    "it", "that", "this", "with", "as", "be", "by", "at", "from", "you", "your",
    "can", "will", "not", "if", "after", "before", "when", "must", "may",
}

REFUSAL = (
    "I don't have a knowledge base article covering that. "
    "Escalating rather than guessing."
)


@dataclass
class GroundednessResult:
    grounded: bool
    coverage: float
    unsupported_terms: list[str]


def _content_terms(text: str) -> set[str]:
    tokens = re.findall(r"[a-z0-9_%\\\\]+", text.lower())
    return {t for t in tokens if t not in STOPWORDS and len(t) > 2}


def check_groundedness(answer: str, context: str, threshold: float = 0.75) -> GroundednessResult:
    """Lexical groundedness: what share of the answer's content terms appear in
    the retrieved context.

    This is deliberately cheap and deterministic — it runs on every request as a
    pre-filter. The LLM-as-judge assertion in evals/ is the slower, semantic
    check and runs in CI, not in the hot path.
    """
    answer_terms = _content_terms(answer)
    if not answer_terms:
        return GroundednessResult(False, 0.0, [])

    context_terms = _content_terms(context)
    unsupported = sorted(answer_terms - context_terms)
    coverage = 1 - (len(unsupported) / len(answer_terms))
    return GroundednessResult(coverage >= threshold, round(coverage, 3), unsupported)
