# Eval suite

## Running

```bash
python -m src.ingest                              # build the index first
npx promptfoo@latest eval -c evals/promptfooconfig.yaml
npx promptfoo@latest view                         # browse results
```

## What is scored

| Failure mode | What it means | Where the fix goes |
|---|---|---|
| wrong-intent | retrieved the wrong article | chunking strategy, `MAX_DISTANCE` |
| ungrounded | answered beyond the context | system prompt, coverage threshold |
| false-refusal | refused something the KB covers | `MAX_DISTANCE` too tight |
| phantom citation | cited an article it did not use | citation assembly in `generate.py` |

Separating these matters: an aggregate pass rate tells you the assistant is
worse, not which knob moved it.

## Chunk size sweep

`CHUNK_SIZE` was chosen empirically, not by default:

| chunk_size | overlap | in-scope pass | false-refusal | note |
|---|---|---|---|---|
| 400 | 80 | 6/9 | 1 | procedures split mid-list, step order lost |
| 700 | 120 | 9/9 | 0 | selected |
| 1200 | 200 | 8/9 | 0 | unrelated sections pulled into context |

Reproduce with `CHUNK_SIZE=400 python -m src.ingest && npx promptfoo eval -c evals/promptfooconfig.yaml`.
