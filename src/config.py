"""Runtime configuration, read from environment with sane defaults."""
import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    kb_dir: Path = ROOT / "data" / "kb"
    index_dir: Path = ROOT / "data" / "index"

    # Chunking. 700/120 chosen from the eval sweep in evals/README.md:
    # 400 split procedures across chunks and broke step-ordering answers;
    # 1200 pulled unrelated sections into context and raised off-topic citations.
    chunk_size: int = int(os.getenv("CHUNK_SIZE", 700))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", 120))

    embedding_model: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

    top_k: int = int(os.getenv("TOP_K", 4))
    # Relevance ceiling on the retrieval score. FAISS IndexFlatL2 returns SQUARED
    # L2 distance; the embeddings are L2-normalised, so squared_l2 = 2 - 2*cos_sim
    # and the score ranges 0..4. The 1.05 default is therefore a cosine-similarity
    # floor of 1 - 1.05/2 = 0.475. Above the ceiling a passage is treated as not
    # relevant, which is what makes "I don't know" reachable instead of always
    # answering. Tuned on the eval suite: 0.8 caused false refusals on paraphrased
    # questions, 1.4 let unrelated articles through.
    max_distance: float = float(os.getenv("MAX_DISTANCE", 1.05))

    # Generation backend: "anthropic", "openai", or "extractive" (no API key needed).
    llm_backend: str = os.getenv("LLM_BACKEND", "extractive")
    llm_model: str = os.getenv("LLM_MODEL", "claude-sonnet-4-20250514")


settings = Settings()
