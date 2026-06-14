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

**System prompt grounding instruction:** Grounding is enforced in two layers (see `query.py`). First, a **structural relevance gate**: retrieval returns the top-5 chunks by cosine distance, and any question whose best chunk is worse than distance 0.60 is answered with `"I don't have enough information on that."` *without ever calling the LLM* — so an out-of-domain question physically cannot be answered from the model's training knowledge. Second, the system prompt to `llama-3.3-70b-versatile` states the rules explicitly:

> "You are an assistant that answers questions about Rutgers University Computer Science professors and courses using ONLY the student reviews provided in the context. Rules: (1) Use ONLY the information in the provided reviews. Do not use any outside or prior knowledge... (2) If the reviews do not contain enough information to answer, reply EXACTLY with: "I don't have enough information on that." ... (3) When reviews disagree, summarize the range of opinions instead of picking one side. (4) Refer to professors and courses by name as they appear in the reviews. Do not invent details, numbers, or quotes that are not in the context. (5) Keep the answer concise."

The retrieved chunks are passed as a numbered, source-labeled context block, and the temperature is set to 0.1 to minimize improvisation. Verified on the out-of-domain question "What is the best dining hall at Rutgers?" — the system returned the refusal with no sources.

**How source attribution is surfaced in the response:** Attribution is **programmatic, not LLM-generated**. After generation, `ask()` builds the source list from the metadata of the chunks that were actually passed as context (`source_file`, `professor`, `source_url`), de-duplicated by document. This guarantees a citation even if the model forgets to mention one, and the Gradio UI shows it in a separate "Retrieved from (sources)" panel. (Trade-off documented in the Failure Case Analysis: this can over-cite documents the answer didn't actually use.) When the system declines for lack of relevant context, the source list is empty.

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What do students say about Ana Paula Centeno's CS111 exams and assignments? | Mixed: assignments simple but lengthy, 111 exams code-heavy; some call exams unnecessarily hard; past exams are a useful study resource. | Summarized the split: exams manageable if you use past exams, but called "code-heavy" / "unnecessarily hard" by others; assignments "simple but lengthy." All 5 chunks from `centeno.txt` (dist 0.36–0.49). | Relevant | Accurate |
| 2 | Which Rutgers CS professors do students say give a lot of extra credit? | Pedro Pajarillo and Aaron Bernstein. | Correctly named Bernstein and Pajarillo with the specifics (Bernstein for grade recovery, Pajarillo via extracurricular sessions). But the cited source list also included Narayana and Ames, who the answer didn't use. | Partially relevant | Accurate |
| 3 | What are the main complaints about John-Austen Francisco's teaching? | Boring/lecture-heavy/disorganized lectures, tough exams, despite some calling him knowledgeable. | Listed boring/hard-to-follow lectures, disorganization (grades not posted to Canvas), tough exams, and noted opinions vary. All 5 chunks from `francisco.txt` (dist 0.29–0.44). | Relevant | Accurate |
| 4 | Which professor is associated with math-heavy AI or machine learning content? | Ahmed Elgammal (CS334/CS534, AI/vision/ML). | Correctly identified Elgammal and quoted "math-heavy" / "AI researcher." But retrieval was weaker (top 0.486) and pulled in off-topic Pajarillo (CS111) and Borgida (CS336) chunks, which were then over-cited as sources. | Partially relevant | Accurate (answer); over-cited sources |
| 5 | What do students say about Srinivas Narayana's lectures and course structure? | Enthusiastic, clear, well-structured; recorded lectures; hard but fair; attendance helps. | Captured all of it: informative/recorded lectures, well-structured relevant course, hard-but-fair work, attendance helps understanding. All 5 chunks from `narayana.txt` (dist 0.27–0.51). | Relevant | Accurate |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

*Out-of-domain control:* "What is the best dining hall at Rutgers?" — the gate filtered the three weakest chunks, but two borderline Narayana CS352 chunks (0.55, 0.59) still passed under the 0.60 cutoff. The LLM then correctly refused via the system prompt (layer 2), since lecture reviews say nothing about dining, returning "I don't have enough information on that." with no sources. This shows both grounding layers in action.

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:** "Which professor is associated with math-heavy AI or machine learning content?" (Q4). The *answer* was correct, but **source attribution failed** — the failure is in retrieval + citation, not generation.

**What the system returned:** The answer correctly named Ahmed Elgammal and quoted "math-heavy" and "AI researcher." However, the retrieved context included two off-topic chunks — Pedro Pajarillo (CS111, "Prof. Pedro is the goat... turned me into a W programmer") at distance 0.507 and Alexander Borgida (CS336, "isn't the brightest for a CS professor") at 0.531 — and because citations are generated programmatically from every retrieved chunk under the 0.60 cutoff, the system cited `pajarillo.txt` and `borgida.txt` as sources for an answer that drew only from `elgammal.txt`. A user reading the citations would think Pajarillo and Borgida reviews mention AI/ML, which they do not.

**Root cause (tied to a specific pipeline stage):** Two interacting causes. (1) **Embedding/retrieval:** this is an abstract conceptual query with no professor name and few lexical anchors ("math-heavy AI or machine learning"), so `all-MiniLM-L6-v2` produces a flatter similarity distribution — the correct Elgammal chunks only reach ~0.486–0.509, while generic praise/criticism chunks from unrelated professors land just below the 0.60 cutoff. Name-based queries (Q1, Q3, Q5) cluster tightly at 0.27–0.44 and never have this problem. (2) **Attribution design:** `ask()` cites the source of *every* chunk passed as context rather than only the documents the answer actually used, so weak-but-under-cutoff chunks become spurious citations. The same effect appears mildly in Q2 (Narayana and Ames cited but unused).

**What you would change to fix it:** Three options, cheapest first: (a) tighten the relevance cutoff from 0.60 to ~0.48 so borderline off-topic chunks are excluded from context and citations — for Q4 this would drop Pajarillo (0.507) and Borgida (0.531) and cite only Elgammal; (b) add a second-stage citation filter that only lists a source if its professor's name appears in the generated answer; (c) longer term, switch to a stronger embedding model or add hybrid keyword (BM25) re-ranking so conceptual queries get sharper separation between on- and off-topic chunks. Option (b) most directly fixes the attribution honesty problem regardless of retrieval noise.

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:** Writing the Chunking Strategy in `planning.md` before any code forced the "one review per chunk" decision up front, and that decision rippled cleanly through every later stage. Because I had committed to a chunk being a single self-contained opinion, the ingestion parser split on review boundaries instead of a fixed character count, each embedding represented one coherent stance, and the metadata schema (professor, course, grade, source) was obvious. When retrieval worked well on name-based queries (distances 0.27–0.44), it was a direct payoff of that early spec decision — the chunks weren't diluting multiple opinions together. Having the five evaluation questions written in advance also meant I could test retrieval in Milestone 4 against concrete targets before wiring in the LLM.

**One way your implementation diverged from the spec, and why:** My `planning.md` Retrieval Approach only described semantic search and a top-k, but during implementation I added a **relevance-gate grounding layer** (refuse before calling the LLM if no chunk is within distance 0.60) that wasn't in the original plan. I added it after realizing the system prompt alone is a soft guarantee — a clever out-of-domain question could still coax a plausible answer. The gate makes refusal a structural property, not a request. I also diverged on the embedding distance metric: the plan didn't specify one, but I explicitly configured ChromaDB for cosine distance with normalized embeddings so distance scores were interpretable against the milestone's 0.5 threshold. Finally, I pinned Gradio to 5.x instead of the suggested 6.9+ because Gradio 6 requires `huggingface-hub>=1.2`, which conflicts with the `transformers` version `sentence-transformers` depends on.

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1 — Ingestion and chunking**

- *What I gave the AI:* My `planning.md` Documents and Chunking Strategy sections (one-review-per-chunk, ~600-char cap, no cross-review overlap) plus the pipeline diagram, and the raw Rate My Professors review files in `documents/`.
- *What it produced:* `pipeline.py` with `load_documents()` / `clean_text()` / `chunk_document()`, splitting each file on a `=== REVIEW ===` delimiter and emitting one chunk per review with metadata.
- *What I changed or overrode:* I directed it to make the cleaning step actually do work — decode HTML entities (`&#39;`, `&amp;`) and strip RMP boilerplate (rating headers, `Helpful` + vote tallies, `Load More Ratings`, footer) rather than just trim whitespace. I also had it prefix every chunk with `Professor (Course):` so chunks stay self-contained after retrieval, and verified the output by printing 5 random chunks and grepping `chunks.json` to confirm no entities or boilerplate leaked.

**Instance 2 — Grounded generation and source attribution**

- *What I gave the AI:* The grounding requirement (answer only from retrieved context, decline otherwise, cite sources), the Groq `llama-3.3-70b-versatile` target, and my retrieval function from `vector_store.py`.
- *What it produced:* A first version with a strict system prompt that asked the *LLM* to cite its sources in the response text.
- *What I changed or overrode:* I overrode the attribution mechanism to be **programmatic** — citations are built from the metadata of the chunks passed as context (`query.py` `_unique_sources()`), not from whatever the LLM writes, so a citation is guaranteed. I also added a **relevance gate** (refuse before calling the LLM if no chunk is within cosine distance 0.60) that the AI's draft didn't have, making out-of-domain refusal structural rather than prompt-dependent. The evaluation later exposed a downside of my programmatic approach (over-citation on abstract queries), which I documented in the Failure Case Analysis instead of hiding.
