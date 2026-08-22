from src.guardrails import check_groundedness


def test_fully_grounded_answer_passes():
    context = "An agent portal account locks after five consecutive failed sign-in attempts."
    answer = "The account locks after five failed sign-in attempts."
    result = check_groundedness(answer, context)
    assert result.grounded
    assert result.coverage == 1.0


def test_invented_detail_is_caught():
    context = "An agent portal account locks after five failed sign-in attempts."
    answer = "The account locks after five attempts and requires biometric reverification by a supervisor."
    result = check_groundedness(answer, context)
    assert not result.grounded
    assert "biometric" in result.unsupported_terms


def test_empty_answer_is_not_grounded():
    assert not check_groundedness("", "some context").grounded
