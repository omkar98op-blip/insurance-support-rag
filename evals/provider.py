"""Promptfoo custom provider: calls the RAG pipeline in-process."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.generate import answer  # noqa: E402


def call_api(prompt, options, context):
    result = answer(prompt)
    return {
        "output": result.text,
        "metadata": {
            "refused": result.refused,
            "grounded": result.grounded,
            "coverage": result.coverage,
            "citations": result.citations,
            "backend": result.backend,
        },
    }
