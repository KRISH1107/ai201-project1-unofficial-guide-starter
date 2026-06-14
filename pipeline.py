"""Document ingestion and chunking pipeline (Milestone 3).

Stages:
  1. load_documents   -- read every raw .txt file from documents/ into memory
  2. clean_text       -- strip Rate My Professors boilerplate, HTML, and entities
  3. chunk_document   -- split a cleaned document into one-review-per-chunk records

Each chunk is a single, self-contained student review tagged with the professor,
course, grade, and source URL so attribution survives into retrieval.

This stage uses only the Python standard library; embedding (sentence-transformers)
and the vector store (ChromaDB) are added in Milestone 4.

Run directly to build chunks.json and inspect the output:

    python pipeline.py                 # build + print 5 random chunks
    python pipeline.py --show-raw      # also print a raw vs. cleaned comparison
    python pipeline.py --sample 8      # print 8 random chunks instead of 5
"""

from __future__ import annotations

import argparse
import html
import json
import random
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

# --- Configuration -----------------------------------------------------------

DOCUMENTS_DIR = Path(__file__).parent / "documents"
CHUNKS_PATH = Path(__file__).parent / "chunks.json"

REVIEW_DELIMITER = "=== REVIEW ==="

# Soft maximum chunk length, in characters. See planning.md > Chunking Strategy.
# Almost every review is one chunk; only an unusually long review is split.
MAX_CHUNK_CHARS = 600
SPLIT_OVERLAP_CHARS = 50

# Lines that are site boilerplate, not review content. Removed during cleaning.
BOILERPLATE_PREFIXES = (
    "I'm Professor",
    "Tags:",
    "Load More",
    "Overall Quality:",
    "Would Take Again:",
    "Level of Difficulty:",
    "Department:",
    "University:",
    "Online Class:",
)
BOILERPLATE_EXACT = {
    "Helpful",
    "CA Notice at Collection",
    "Do Not Sell My Personal Information",
}

HTML_TAG_RE = re.compile(r"<[^>]+>")
VOTE_COUNT_RE = re.compile(r"^\d+$")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


# --- Data model --------------------------------------------------------------


@dataclass
class Chunk:
    """A single retrievable review plus the metadata needed for attribution."""

    id: str
    text: str
    metadata: dict = field(default_factory=dict)


# --- Stage 1: load -----------------------------------------------------------


def load_documents(documents_dir: Path = DOCUMENTS_DIR) -> list[dict]:
    """Load every raw .txt document from disk into memory, unmodified."""
    if not documents_dir.exists():
        raise FileNotFoundError(f"Documents directory not found: {documents_dir}")

    documents = []
    for path in sorted(documents_dir.glob("*.txt")):
        raw_text = path.read_text(encoding="utf-8")
        documents.append({"filename": path.name, "raw_text": raw_text})

    if not documents:
        raise ValueError(f"No .txt documents found in {documents_dir}")
    return documents


# --- Stage 2: clean ----------------------------------------------------------


def _is_boilerplate(line: str) -> bool:
    stripped = line.strip()
    if stripped in BOILERPLATE_EXACT:
        return True
    if VOTE_COUNT_RE.match(stripped):  # standalone "Helpful" vote tallies
        return True
    if stripped.startswith("©"):
        return True
    return any(stripped.startswith(prefix) for prefix in BOILERPLATE_PREFIXES)


def clean_text(raw_text: str) -> str:
    """Remove HTML, decode entities, and drop site boilerplate lines.

    Keeps only the structural keys we need downstream (Professor, Source,
    the === REVIEW === delimiter, Course, Grade, Review).
    """
    # Decode HTML entities (&#39; -> ', &amp; -> &) and strip any stray tags.
    text = html.unescape(raw_text)
    text = HTML_TAG_RE.sub("", text)
    text = text.replace("\xa0", " ")  # non-breaking spaces left by &nbsp;

    cleaned_lines = []
    for line in text.splitlines():
        if _is_boilerplate(line):
            continue
        # Collapse runs of internal whitespace but keep the line's content.
        normalized = re.sub(r"[ \t]+", " ", line).rstrip()
        cleaned_lines.append(normalized)

    # Collapse 3+ blank lines down to a single blank line.
    cleaned = "\n".join(cleaned_lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


# --- Stage 3: chunk ----------------------------------------------------------


def _parse_header(header_block: str) -> dict:
    """Pull document-level metadata (professor, source URL) from the header."""
    meta = {}
    for line in header_block.splitlines():
        if line.startswith("Professor:"):
            meta["professor"] = line.split(":", 1)[1].strip()
        elif line.startswith("Source:"):
            meta["source_url"] = line.split(":", 1)[1].strip()
    return meta


def _parse_review_block(block: str) -> dict | None:
    """Parse one review block into its course, grade, and review text."""
    fields = {"course": "Unknown", "grade": "Not listed", "review": ""}
    for line in block.splitlines():
        if line.startswith("Course:"):
            fields["course"] = line.split(":", 1)[1].strip()
        elif line.startswith("Grade:"):
            fields["grade"] = line.split(":", 1)[1].strip()
        elif line.startswith("Review:"):
            fields["review"] = line.split(":", 1)[1].strip()

    if not fields["review"]:
        return None
    return fields


def _split_long_review(text: str) -> list[str]:
    """Split an over-long review on sentence boundaries with small overlap."""
    if len(text) <= MAX_CHUNK_CHARS:
        return [text]

    sentences = SENTENCE_SPLIT_RE.split(text)
    pieces, current = [], ""
    for sentence in sentences:
        if current and len(current) + len(sentence) + 1 > MAX_CHUNK_CHARS:
            pieces.append(current.strip())
            tail = current[-SPLIT_OVERLAP_CHARS:]
            current = (tail + " " + sentence).strip()
        else:
            current = (current + " " + sentence).strip()
    if current:
        pieces.append(current.strip())
    return pieces


def chunk_document(cleaned_text: str, filename: str) -> list[Chunk]:
    """Turn one cleaned document into a list of one-review-per-chunk records."""
    segments = cleaned_text.split(REVIEW_DELIMITER)
    header_meta = _parse_header(segments[0])
    professor = header_meta.get("professor", "Unknown Professor")

    chunks: list[Chunk] = []
    review_index = 0
    for block in segments[1:]:
        parsed = _parse_review_block(block)
        if parsed is None:
            continue  # filters out empty / malformed blocks

        review_index += 1
        course = parsed["course"]
        for part_no, piece in enumerate(_split_long_review(parsed["review"])):
            if not piece.strip():
                continue
            # Prefix the professor + course so each chunk stands on its own.
            chunk_text = f"{professor} ({course}): {piece}"
            stem = Path(filename).stem
            suffix = f"-{part_no}" if part_no else ""
            chunks.append(
                Chunk(
                    id=f"{stem}-r{review_index}{suffix}",
                    text=chunk_text,
                    metadata={
                        "professor": professor,
                        "course": course,
                        "grade": parsed["grade"],
                        "source_url": header_meta.get("source_url", ""),
                        "source_file": filename,
                    },
                )
            )
    return chunks


def build_chunks(documents_dir: Path = DOCUMENTS_DIR) -> list[Chunk]:
    """Run the full pipeline: load -> clean -> chunk across all documents."""
    all_chunks: list[Chunk] = []
    for doc in load_documents(documents_dir):
        cleaned = clean_text(doc["raw_text"])
        all_chunks.extend(chunk_document(cleaned, doc["filename"]))
    return all_chunks


def save_chunks(chunks: list[Chunk], path: Path = CHUNKS_PATH) -> None:
    payload = [asdict(c) for c in chunks]
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


# --- Inspection / CLI --------------------------------------------------------


def _print_chunk(chunk: Chunk) -> None:
    meta = chunk.metadata
    print(f"  id:     {chunk.id}")
    print(f"  source: {meta['source_file']} | {meta['source_url']}")
    print(f"  course: {meta['course']} | grade: {meta['grade']} | chars: {len(chunk.text)}")
    print(f"  text:   {chunk.text}")
    print("-" * 80)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build and inspect review chunks.")
    parser.add_argument("--sample", type=int, default=5, help="random chunks to print")
    parser.add_argument("--seed", type=int, default=42, help="random seed for sampling")
    parser.add_argument("--show-raw", action="store_true", help="print raw vs cleaned")
    args = parser.parse_args()

    documents = load_documents()
    print(f"Loaded {len(documents)} documents from {DOCUMENTS_DIR}/")

    if args.show_raw:
        sample_doc = documents[0]
        print("\n=== RAW (first 600 chars) ===")
        print(sample_doc["raw_text"][:600])
        print("\n=== CLEANED (first 600 chars) ===")
        print(clean_text(sample_doc["raw_text"])[:600])
        print("=" * 80)

    chunks = build_chunks()
    save_chunks(chunks)

    lengths = [len(c.text) for c in chunks]
    print(f"\nTotal chunks: {len(chunks)}")
    print(
        f"Chunk length (chars) -> min {min(lengths)}, "
        f"avg {sum(lengths) // len(lengths)}, max {max(lengths)}"
    )
    print(f"Saved chunks to {CHUNKS_PATH}")

    n = min(args.sample, len(chunks))
    print(f"\n=== {n} RANDOM CHUNKS (seed={args.seed}) ===")
    print("-" * 80)
    for chunk in random.Random(args.seed).sample(chunks, n):
        _print_chunk(chunk)


if __name__ == "__main__":
    main()
