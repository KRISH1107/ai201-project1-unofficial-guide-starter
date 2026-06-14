# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

<!-- What topic or category of knowledge does your system cover?
     Why is this knowledge valuable, and why is it hard to find through official channels?
     Example: "Student reviews of CS professors at [university] — useful because official
     course descriptions don't reflect teaching style, exam difficulty, or workload." -->
This project covers Rutgers New Brunswick Computer Science course and professor reviews. The goal is to make unofficial student feedback searchable across questions about teaching style, workload, exam difficulty, grading, attendance expectations, office hours, and course support. This knowledge is valuable because official course descriptions explain curriculum requirements, but they usually do not capture what students actually experience when choosing a professor or preparing for a class.

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | Ana Paula Centeno, Rutgers CS reviews | Rate My Professors page | https://www.ratemyprofessors.com/professor/600296 |
| 2 | Lars Sorensen, Rutgers CS reviews | Rate My Professors page | https://www.ratemyprofessors.com/professor/2279091 |
| 3 | Pedro Pajarillo, Rutgers CS reviews | Rate My Professors page | https://www.ratemyprofessors.com/professor/3025313 |
| 4 | John-Austen Francisco, Rutgers CS reviews | Rate My Professors page | https://www.ratemyprofessors.com/professor/1833903 |
| 5 | Jeffrey Ames, Rutgers CS reviews | Rate My Professors page | https://www.ratemyprofessors.com/professor/2256513 |
| 6 | Alexander Borgida, Rutgers CS reviews | Rate My Professors page | https://www.ratemyprofessors.com/professor/173951 |
| 7 | Uli Kremer, Rutgers CS reviews | Rate My Professors page | https://www.ratemyprofessors.com/professor/1815726 |
| 8 | Srinivas Narayana, Rutgers CS reviews | Rate My Professors page | https://www.ratemyprofessors.com/professor/2481805 |
| 9 | Ahmed Elgammal, Rutgers CS reviews | Rate My Professors page | https://www.ratemyprofessors.com/professor/184976 |
| 10 | Aaron Bernstein, Rutgers CS reviews | Rate My Professors page | https://www.ratemyprofessors.com/professor/2447976 |

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:** One student review per chunk (review-aware chunking), soft-capped at 600 characters. In practice every review fell under the cap, so each chunk is exactly one complete review (37–382 characters; average ~286). Each chunk text is prefixed with the professor name and course (e.g., `Jeffrey Ames (CS336): ...`) so it stays self-contained after retrieval.

**Overlap:** None across reviews (0 characters). Overlap (~50 characters on sentence boundaries) is only applied if a single review exceeds the 600-character cap and must be split — which did not occur in the current corpus.

**Why these choices fit your documents:** Rate My Professors pages are stacks of short, self-contained opinions, so a single review is the natural unit of meaning. Fixed-character splitting would merge the tail of one student's verdict with the head of another's and embed to a muddy average; keeping one review per chunk means each embedding represents one coherent stance. Preprocessing before chunking: HTML entities are decoded (`&#39;` → `'`, `&amp;` → `&`), stray HTML tags are stripped, and site boilerplate is removed (rating headers, `I'm Professor X`, `Tags:` lines, `Helpful` + vote tallies, `Load More Ratings`, and the page footer). See `pipeline.py` (`clean_text`).

**Final chunk count:** 50 chunks across 10 documents (4–6 per professor). This sits comfortably above the 50-chunk floor and well below the 2,000-chunk ceiling, which fits a corpus of ~50 short reviews.

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers`, with embeddings stored in a local ChromaDB collection (`rutgers_cs_reviews`) using cosine distance. Embeddings are L2-normalized, so ChromaDB returns `1 - cosine_similarity` as the distance (lower = more relevant). I chose it because it runs locally with no API key or rate limits, is fast on CPU, and is tuned for short sentence-level text — which fits my one-review-per-chunk strategy. Retrieval uses top-k = 5. Across all five evaluation queries, the top-ranked chunk scored between 0.27 and 0.46 and came from the correct professor, confirming retrieval quality before adding generation.

**Production tradeoff reflection:** If I were deploying for real users and cost weren't a constraint, I'd weigh a stronger hosted embedding model (e.g., OpenAI `text-embedding-3-large` or Cohere) for better accuracy on slangy, sarcastic review text where MiniLM can miss implied sentiment (e.g., "his lectures put me to sleep" has no explicit negative keyword). The tradeoffs: (1) accuracy on domain-specific text — larger models capture more nuance but with diminishing returns on already-short reviews; (2) latency and dependency — an API adds network round-trips and an external point of failure versus a fully local model; (3) cost at scale — per-token billing for every chunk and query; (4) context length — irrelevant for short reviews but important if I expanded to long-form guides or Reddit megathreads; (5) multilingual support — unnecessary for an English-only Rutgers corpus, but a multilingual model would matter for an international deployment; (6) privacy — local embedding keeps student opinions off third-party servers. For this project, the local model's zero cost, low latency, and strong retrieval scores make it the right default.

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**

**How source attribution is surfaced in the response:**

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:**

**What the system returned:**

**Root cause (tied to a specific pipeline stage):**

**What you would change to fix it:**

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**

**One way your implementation diverged from the spec, and why:**

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*

**Instance 2**

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*
