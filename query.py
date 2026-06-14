"""Grounded answer generation (Milestone 5).

Pipeline position: Retrieval (vector_store.py) -> Generation (this file) -> UI (app.py).

`ask()` retrieves the most relevant review chunks, then asks Groq's
llama-3.3-70b-versatile to answer **only** from those chunks. Grounding is
enforced two ways:

  1. A relevance gate: if no retrieved chunk is close enough (cosine distance
     under RELEVANCE_CUTOFF), we skip the LLM entirely and return the
     "not enough information" message. This guarantees out-of-domain questions
     can't be answered from the model's training knowledge.
  2. A strict system prompt: the model is told to use only the provided context
     and to decline if the context is insufficient.

Source attribution is programmatic: the returned `sources` come from the
metadata of the chunks actually passed as context, not from whatever the LLM
chooses to write.

Usage:
    python query.py "What do students say about Professor Narayana?"
"""

from __future__ import annotations

import argparse
import os
import sys

from dotenv import load_dotenv

from vector_store import retrieve

load_dotenv()

MODEL = "llama-3.3-70b-versatile"
TOP_K = 5

# Cosine distance above which a chunk is considered not relevant. In-domain top
# hits observed at 0.27-0.46; if the best hit is worse than this, we decline.
RELEVANCE_CUTOFF = 0.60

NOT_ENOUGH_INFO = "I don't have enough information on that."

SYSTEM_PROMPT = (
    "You are an assistant that answers questions about Rutgers University "
    "Computer Science professors and courses using ONLY the student reviews "
    "provided in the context.\n"
    "Rules:\n"
    "1. Use ONLY the information in the provided reviews. Do not use any outside "
    "or prior knowledge about these professors, courses, or Rutgers.\n"
    f"2. If the reviews do not contain enough information to answer, reply "
    f"EXACTLY with: \"{NOT_ENOUGH_INFO}\" and nothing else.\n"
    "3. When reviews disagree, summarize the range of opinions instead of "
    "picking one side.\n"
    "4. Refer to professors and courses by name as they appear in the reviews. "
    "Do not invent details, numbers, or quotes that are not in the context.\n"
    "5. Keep the answer concise (2-5 sentences)."
)


def _format_context(hits: list[dict]) -> str:
    """Render retrieved chunks into a numbered, source-labeled context block."""
    blocks = []
    for i, hit in enumerate(hits, start=1):
        meta = hit["metadata"]
        blocks.append(
            f"[Review {i}] (source: {meta['source_file']}, "
            f"professor: {meta['professor']}, course: {meta['course']})\n"
            f"{hit['text']}"
        )
    return "\n\n".join(blocks)


def _unique_sources(hits: list[dict]) -> list[str]:
    """Distinct, human-readable source citations from the chunk metadata."""
    seen, sources = set(), []
    for hit in hits:
        meta = hit["metadata"]
        key = meta["source_file"]
        if key not in seen:
            seen.add(key)
            sources.append(
                f"{meta['source_file']} - {meta['professor']} ({meta['source_url']})"
            )
    return sources


def _get_client():
    """Create the Groq client, with a clear error if the key is missing."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key == "your_key_here":
        raise RuntimeError(
            "GROQ_API_KEY is not set. Copy .env.example to .env and add your "
            "free key from https://console.groq.com"
        )
    from groq import Groq

    return Groq(api_key=api_key)


def ask(question: str, k: int = TOP_K) -> dict:
    """Answer a question grounded in retrieved review chunks.

    Returns a dict with: answer (str), sources (list[str]), chunks (list[dict]),
    and grounded (bool, False when we declined for lack of relevant context).
    """
    hits = retrieve(question, k=k)
    relevant = [h for h in hits if h["distance"] <= RELEVANCE_CUTOFF]

    # Grounding gate 1: nothing close enough -> decline without calling the LLM.
    if not relevant:
        return {
            "answer": NOT_ENOUGH_INFO,
            "sources": [],
            "chunks": hits,
            "grounded": False,
        }

    context = _format_context(relevant)
    user_prompt = (
        f"Context (student reviews):\n{context}\n\n"
        f"Question: {question}\n\n"
        "Answer using only the reviews above."
    )

    client = _get_client()
    completion = client.chat.completions.create(
        model=MODEL,
        temperature=0.1,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    answer = completion.choices[0].message.content.strip()

    declined = NOT_ENOUGH_INFO.lower() in answer.lower()
    return {
        "answer": answer,
        "sources": [] if declined else _unique_sources(relevant),
        "chunks": relevant,
        "grounded": not declined,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask a grounded question.")
    parser.add_argument("question", nargs="+", help="the question to ask")
    parser.add_argument("-k", "--top-k", type=int, default=TOP_K)
    args = parser.parse_args()

    result = ask(" ".join(args.question), k=args.top_k)
    print("\nAnswer:")
    print(result["answer"])
    if result["sources"]:
        print("\nRetrieved from:")
        for source in result["sources"]:
            print(f"  - {source}")
    else:
        print("\n(No sources cited - the system declined to answer.)")


if __name__ == "__main__":
    sys.exit(main())
