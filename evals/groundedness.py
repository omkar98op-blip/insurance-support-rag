"""Custom promptfoo assertion: every factual claim must be supported by retrieved context.

Runs as a graded assertion over the service response. The service already
returns its own lexical coverage score and citation list, so this assertion
checks the contract rather than recomputing it:

  - a non-refusal answer must carry at least one citation
  - a non-refusal answer must clear the coverage threshold
  - a refusal must carry no citations (no phantom sourcing)
"""
COVERAGE_THRESHOLD = 0.75


def get_assert(output, context):
    meta = (context or {}).get("metadata") or {}
    refused = meta.get("refused", False)
    grounded = meta.get("grounded", False)
    coverage = meta.get("coverage", 0.0)
    citations = meta.get("citations", [])

    if refused:
        if citations:
            return {"pass": False, "score": 0.0,
                    "reason": f"refusal carried citations: {citations}"}
        return {"pass": True, "score": 1.0, "reason": "clean refusal"}

    if not citations:
        return {"pass": False, "score": 0.0, "reason": "answer returned with no citation"}

    if not grounded or coverage < COVERAGE_THRESHOLD:
        return {"pass": False, "score": coverage,
                "reason": f"coverage {coverage} below {COVERAGE_THRESHOLD}"}

    return {"pass": True, "score": coverage, "reason": f"grounded, coverage {coverage}"}
