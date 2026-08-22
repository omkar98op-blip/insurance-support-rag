# Insurance Support RAG

A retrieval-grounded support assistant over a technical-support knowledge base, with
groundedness guardrails, citation enforcement, and an eval suite that scores retrieval
and generation failures separately.

Built as a working reference for the pattern I deployed in production at Allstate:
a GenAI virtual agent on Amazon Connect grounded on the ServiceNow knowledge base,
which cut technical support demand by 16.77%.

## The problem this solves

A support assistant that answers confidently and wrongly costs more than one that
escalates. Most of the engineering here is spent on making **"I don't know" reachable**:

- a cosine-distance ceiling on retrieval, so an irrelevant nearest neighbour is
  discarded rather than answered from
- a system prompt that constrains generation to retrieved context and mandates
  article-level citation
- a cheap lexical groundedness check on every response, in the request path
- an eval suite that separates *wrong-intent*, *ungrounded*, and *false-refusal*
  failures, because they have different fixes

## Architecture

```
data/kb/*.md
    │  frontmatter -> metadata (article_id, category, product, last_reviewed)
    ▼
ingest.py ── markdown-header split ──▶ recursive char split (700/120)
    │                                        │
    │                                        ▼
    │                              all-MiniLM-L6-v2 embeddings
    │                                        │
    ▼                                        ▼
                                       FAISS index
                                             │
query ──▶ retriever.py ── distance ceiling + optional category filter
                                             │
                                       top-k passages
                                             │
                     ┌───────────────────────┴─── no passages ──▶ refuse
                     ▼
              generate.py ── grounded prompt ──▶ LLM (or extractive fallback)
                     │
                     ▼
              guardrails.py ── coverage check ──▶ response + citations
```

## Quick start

```bash
pip install -r requirements.txt
python -m src.ingest                  # build the FAISS index
uvicorn src.app:app --reload
```

```bash
curl -X POST localhost:8000/query -H 'content-type: application/json' \
  -d '{"question":"How long is the grace period after a failed payment?"}'
```

```json
{
  "answer": "... After the third failure the policy enters GRACE status for 10 days ... [KB-005]",
  "refused": false,
  "grounded": true,
  "coverage": 1.0,
  "citations": [{"article_id": "KB-005", "title": "Recurring payment failures", "distance": 0.7285}]
}
```

Out-of-scope questions refuse rather than improvise:

```json
{
  "answer": "I don't have a knowledge base article covering that. Escalating rather than guessing.",
  "refused": true,
  "citations": []
}
```

### Docker

```bash
docker compose up --build
```

The index is baked into the image at build time, so the container starts cold
without network access.

## Generation backends

| `LLM_BACKEND` | Behaviour | Needs a key |
|---|---|---|
| `extractive` (default) | returns the top passage verbatim with its citation | no |
| `anthropic` | grounded generation via Claude | `ANTHROPIC_API_KEY` |
| `openai` | grounded generation via GPT | `OPENAI_API_KEY` |

The extractive backend is not a toy — it is the groundedness baseline the LLM
backends are scored against in the eval suite. A generative answer that scores
below extractive on citation accuracy is a regression.

## Evaluation

```bash
npx promptfoo@latest eval -c evals/promptfooconfig.yaml
npx promptfoo@latest view
```

12 cases across three groups:

- **in-scope** — must answer, must cite the correct article, must preserve stated limits
- **out-of-scope** — must refuse, must carry no citations
- **adversarial** — prompt injection, false premises embedded in the question,
  and authority pressure ("my manager says backdating is unlimited")

The false-premise cases matter most. A support assistant that accepts "since claims
auto-close after 3 days" and answers around it has already failed, even if the rest
of the answer is correctly retrieved.

See `evals/README.md` for the chunk-size sweep behind the 700/120 default.

## Tests

```bash
pytest -q     # 12 passed
```

Covers retrieval correctness per article, refusal on out-of-scope input, citation
presence, and the groundedness checker's ability to catch an invented detail.

## Design notes

**Why lexical groundedness in the request path and LLM-as-judge only in CI.**
The in-path check must be deterministic and sub-millisecond; it catches invented
proper nouns, numbers, and product names, which is the bulk of real hallucination
in a support context. Semantic judging is slower and non-deterministic, so it runs
in the eval suite where its cost is paid once per change, not once per request.

**Why chunks split on markdown headers first.** Support articles are procedures.
A character splitter alone cuts numbered steps in half, and a retrieved half-procedure
produces an answer that is grounded and still wrong. Splitting on headings keeps a
procedure intact and the character splitter only handles overflow.

**Why metadata carries `last_reviewed`.** Stale knowledge base articles are the
most common source of confidently wrong support answers in a real deployment. The
field is surfaced in retrieval metadata so a staleness filter is a config change
rather than a re-architecture.
