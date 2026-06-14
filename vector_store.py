"""Embedding and retrieval over the review chunks (Milestone 4).

Pipeline position: Chunking (pipeline.py) -> Embedding + Vector Store (this file)
-> Retrieval (this file) -> Generation (Milestone 5).

  - Embeddings: sentence-transformers `all-MiniLM-L6-v2` (local, 384-dim, normalized)
  - Vector store: ChromaDB PersistentClient, cosine distance
  - Each vector keeps its source metadata (professor, course, grade, source file/URL)
    so retrieved chunks can be attributed back to their document.

Because embeddings are L2-normalized and the collection uses cosine space, the
distance Chroma returns is `1 - cosine_similarity`: ~0 is identical, lower is
more relevant. On-topic matches in this corpus land roughly in the 0.2-0.5 range.

Usage:
    python vector_store.py --build         # (re)build the vector store from chunks.json
    python vector_store.py                  # build + run the evaluation-plan queries
    python vector_store.py --query "..."    # ad hoc query against the existing store
    python vector_store.py --query "..." -k 5
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

EMBED_MODEL_NAME = "all-MiniLM-L6-v2"
COLLECTION_NAME = "rutgers_cs_reviews"
CHUNKS_PATH = Path(__file__).parent / "chunks.json"
CHROMA_DIR = Path(__file__).parent / "chroma_db"

# Evaluation-plan queries (mirrors planning.md > Evaluation Plan).
EVAL_QUERIES = [
    "What do students say about Ana Paula Centeno's CS111 exams and assignments?",
    "Which professors give a lot of extra credit or generous grading?",
    "What are the main complaints about John-Austen Francisco's teaching?",
    "Which professor teaches math-heavy AI or machine learning content?",
    "What do students say about Srinivas Narayana's lectures and course structure?",
]

_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    """Load the embedding model once and reuse it (downloads on first run)."""
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBED_MODEL_NAME)
    return _model


def _client() -> chromadb.ClientAPI:
    return chromadb.PersistentClient(
        path=str(CHROMA_DIR),
        settings=Settings(anonymized_telemetry=False),
    )


def embed(texts: list[str]) -> list[list[float]]:
    """Embed text with all-MiniLM-L6-v2, L2-normalized for cosine distance."""
    vectors = get_model().encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return vectors.tolist()


def build_vector_store(rebuild: bool = True):
    """Load chunks.json, embed every chunk, and store it in ChromaDB."""
    if not CHUNKS_PATH.exists():
        raise FileNotFoundError(
            f"{CHUNKS_PATH} not found. Run `python pipeline.py` first."
        )
    chunks = json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))

    client = _client()
    if rebuild:
        try:
            client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass  # collection didn't exist yet

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    texts = [c["text"] for c in chunks]
    collection.add(
        ids=[c["id"] for c in chunks],
        embeddings=embed(texts),
        documents=texts,
        metadatas=[c["metadata"] for c in chunks],
    )
    print(f"Embedded and stored {collection.count()} chunks in '{COLLECTION_NAME}'.")
    return collection


def get_collection():
    """Return the existing collection, or build it if it isn't there yet."""
    client = _client()
    try:
        return client.get_collection(COLLECTION_NAME)
    except Exception:
        print("Vector store not found; building it now...")
        return build_vector_store()


def retrieve(query: str, k: int = 5, collection=None) -> list[dict]:
    """Return the top-k most relevant chunks with metadata and distance."""
    collection = collection or get_collection()
    result = collection.query(
        query_embeddings=embed([query]),
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )
    hits = []
    for doc, meta, dist in zip(
        result["documents"][0], result["metadatas"][0], result["distances"][0]
    ):
        hits.append({"text": doc, "metadata": meta, "distance": dist})
    return hits


def _print_hits(query: str, hits: list[dict]) -> None:
    print(f"\nQuery: {query}")
    print("=" * 88)
    for rank, hit in enumerate(hits, start=1):
        meta = hit["metadata"]
        flag = "" if hit["distance"] < 0.5 else "   <-- weak match (>= 0.5)"
        print(
            f"[{rank}] distance={hit['distance']:.3f}  "
            f"{meta['professor']} | {meta['course']} | {meta['source_file']}{flag}"
        )
        print(f"    {hit['text']}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Build/query the review vector store.")
    parser.add_argument("--build", action="store_true", help="rebuild the vector store")
    parser.add_argument("--query", type=str, help="run a single ad hoc query")
    parser.add_argument("-k", "--top-k", type=int, default=5, help="chunks to retrieve")
    args = parser.parse_args()

    if args.query:
        hits = retrieve(args.query, k=args.top_k)
        _print_hits(args.query, hits)
        return

    # Default / --build path: (re)build, then sanity-check with the eval queries.
    collection = build_vector_store()
    for query in EVAL_QUERIES:
        _print_hits(query, retrieve(query, k=args.top_k, collection=collection))


if __name__ == "__main__":
    main()
