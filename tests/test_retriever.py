import pytest

from src.generate import answer
from src.retriever import retrieve


@pytest.mark.parametrize(
    "question,expected_article",
    [
        ("How long does an agent portal account stay locked?", "KB-001"),
        ("What does the PENDING_DOCS claim status mean?", "KB-002"),
        ("Advisor Pro will not launch", "KB-003"),
        ("Can I backdate an endorsement?", "KB-004"),
        ("My autopay failed, what happens next?", "KB-005"),
    ],
)
def test_retrieves_correct_article(question, expected_article):
    passages = retrieve(question)
    assert passages, f"no passages retrieved for {question!r}"
    assert expected_article in {p.article_id for p in passages}


@pytest.mark.parametrize(
    "question",
    [
        "What is the capital of France?",
        "How do I cancel my Netflix subscription?",
        "Write me a poem about the sea.",
    ],
)
def test_refuses_out_of_scope(question):
    result = answer(question)
    assert result.refused, f"should have refused: {question!r}"
    assert not result.citations, "a refusal must not carry citations"


def test_answer_carries_citations():
    result = answer("How long does an agent portal account stay locked?")
    assert not result.refused
    assert result.citations
    assert result.grounded
