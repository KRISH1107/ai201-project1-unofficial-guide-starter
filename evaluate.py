"""Evaluation harness (Milestone 6).

Runs the five evaluation-plan questions (plus one out-of-domain question that the
system should refuse) end-to-end and prints, for each:

  - the question
  - the retrieved chunks with their cosine distances and source files
  - the grounded answer
  - the programmatic source citations

Run:
    python evaluate.py
"""

from __future__ import annotations

from query import ask

# Five evaluation questions (see planning.md > Evaluation Plan) plus one
# deliberately out-of-domain question to test the refusal path.
QUESTIONS = [
    "What do students say about Ana Paula Centeno's CS111 exams and assignments?",
    "Which Rutgers CS professors do students say give a lot of extra credit?",
    "What are the main complaints about John-Austen Francisco's teaching?",
    "Which professor is associated with math-heavy AI or machine learning content?",
    "What do students say about Srinivas Narayana's lectures and course structure?",
    "What is the best dining hall at Rutgers?",  # out-of-domain -> should decline
]


def run() -> None:
    for n, question in enumerate(QUESTIONS, start=1):
        result = ask(question)
        print("#" * 90)
        print(f"Q{n}: {question}")
        print("-" * 90)
        print("Retrieved chunks (distance | source | professor):")
        for hit in result["chunks"]:
            meta = hit["metadata"]
            print(
                f"  {hit['distance']:.3f} | {meta['source_file']:16} | "
                f"{meta['professor']} ({meta['course']})"
            )
        if not result["chunks"]:
            print("  (none within the relevance cutoff)")
        print(f"\nGrounded: {result['grounded']}")
        print("Answer:")
        print(f"  {result['answer']}")
        print("Sources cited:")
        for source in result["sources"]:
            print(f"  - {source}")
        if not result["sources"]:
            print("  (none)")
        print()


if __name__ == "__main__":
    run()
