"""Load knowledge base articles, chunk them, embed, and persist a FAISS index."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

from .config import settings

FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Pull YAML-ish frontmatter off an article. Metadata drives citation and filtering."""
    match = FRONTMATTER.match(text)
    if not match:
        return {}, text
    meta = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    return meta, text[match.end():]


def load_articles(kb_dir: Path) -> list[Document]:
    docs: list[Document] = []
    for path in sorted(kb_dir.glob("*.md")):
        meta, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        meta.setdefault("article_id", path.stem)
        meta["source"] = path.name
        docs.append(Document(page_content=body, metadata=meta))
    return docs


def chunk(docs: list[Document]) -> list[Document]:
    """Split on markdown headings first so a chunk stays inside one procedure,
    then fall back to character splitting for long sections."""
    header_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[("#", "h1"), ("##", "h2")],
        strip_headers=False,
    )
    char_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " "],
    )

    chunks: list[Document] = []
    for doc in docs:
        for section in header_splitter.split_text(doc.page_content):
            section.metadata = {**doc.metadata, **section.metadata}
            chunks.extend(char_splitter.split_documents([section]))

    for i, c in enumerate(chunks):
        c.metadata["chunk_id"] = f"{c.metadata.get('article_id', 'unknown')}#{i}"
    return chunks


def build_index(kb_dir: Path | None = None, index_dir: Path | None = None) -> int:
    kb_dir = kb_dir or settings.kb_dir
    index_dir = index_dir or settings.index_dir

    docs = load_articles(kb_dir)
    if not docs:
        raise SystemExit(f"no articles found in {kb_dir}")
    chunks = chunk(docs)

    embeddings = HuggingFaceEmbeddings(model_name=settings.embedding_model)
    store = FAISS.from_documents(chunks, embeddings)
    index_dir.mkdir(parents=True, exist_ok=True)
    store.save_local(str(index_dir))
    return len(chunks)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build the FAISS index from the knowledge base.")
    parser.add_argument("--kb-dir", type=Path, default=settings.kb_dir)
    parser.add_argument("--index-dir", type=Path, default=settings.index_dir)
    args = parser.parse_args()
    count = build_index(args.kb_dir, args.index_dir)
    print(f"indexed {count} chunks -> {args.index_dir}")
