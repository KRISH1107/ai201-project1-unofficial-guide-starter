# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->
Rutgers New Brunswick Computer Science course and professor reviews. This guide will make unofficial student feedback searchable across professors, courses, workload, exams, attendance expectations, grading style, lecture quality, and support resources. This knowledge is valuable because official course descriptions say what a class covers, but they usually do not explain how students experience a professor's teaching style, grading, homework load, exam difficulty, or classroom expectations.

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->

| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | Rate My Professors: Ana Paula Centeno | Rutgers CS reviews for CS111/CS112, including notes on exams, assignments, lectures, and study materials. | https://www.ratemyprofessors.com/professor/600296 |
| 2 | Rate My Professors: Lars Sorensen | Rutgers CS111 reviews covering beginner difficulty, homework load, exams, lecture style, and classroom expectations. | https://www.ratemyprofessors.com/professor/2279091 |
| 3 | Rate My Professors: Pedro Pajarillo | Rutgers CS111 reviews focused on introductory programming, feedback, extra credit, and student support. | https://www.ratemyprofessors.com/professor/3025313 |
| 4 | Rate My Professors: John-Austen Francisco | Rutgers CS reviews describing lecture organization, assignments, exams, accessibility, and mixed student experiences. | https://www.ratemyprofessors.com/professor/1833903 |
| 5 | Rate My Professors: Jeffrey Ames | Rutgers CS205 and systems-related reviews covering homework weight, quizzes/exams, lecture clarity, and accommodations. | https://www.ratemyprofessors.com/professor/2256513 |
| 6 | Rate My Professors: Alexander Borgida | Rutgers CS205 reviews covering discrete structures, slide quality, lecture clarity, office hours, and self-study needs. | https://www.ratemyprofessors.com/professor/173951 |
| 7 | Rate My Professors: Uli Kremer | Rutgers CS314/compiler and systems reviews covering projects, exams, office hours, lecture notes, and assignment difficulty. | https://www.ratemyprofessors.com/professor/1815726 |
| 8 | Rate My Professors: Srinivas Narayana | Rutgers CS reviews for systems courses, including projects, quizzes, recordings, lecture quality, and office hours. | https://www.ratemyprofessors.com/professor/2481805 |
| 9 | Rate My Professors: Ahmed Elgammal | Rutgers AI/ML/computer vision reviews covering math intensity, projects, lectures, flexibility, and grading. | https://www.ratemyprofessors.com/professor/184976 |
| 10 | Rate My Professors: Aaron Bernstein | Rutgers upper-level CS reviews covering extra credit, homework, exams, curves, recordings, and lecture attendance. | https://www.ratemyprofessors.com/professor/2447976 |

These documents are mostly short, informal student reviews rather than long official guides. The corpus should be able to answer questions like which professors are described as helpful, which classes have heavy homework or exam pressure, where extra credit is mentioned, whether attendance matters, and what students say about lecture clarity.

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:**

**Overlap:**

**Reasoning:**

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model:**

**Top-k:**

**Production tradeoff reflection:**

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | What do students say about Ana Paula Centeno's CS111 exams and assignments? | Reviews are mixed: some students say assignments are simple but lengthy and exams are code-heavy, while others describe the exams and assignments as unnecessarily hard. Several reviews mention that past exams or study materials are useful. |
| 2 | Which Rutgers CS professor reviews mention extra credit or generous grading support? | Pedro Pajarillo and Aaron Bernstein. Pajarillo reviews mention extra credit and supportive feedback, while Bernstein reviews repeatedly mention extra credit, dropped homework, generous curves, and grading support. |
| 3 | What are the main complaints about John-Austen Francisco's teaching? | Students complain that lectures can be boring, lecture-heavy, disorganized, or hard to follow, and that exams can be tough even when assignments are straightforward. |
| 4 | Which professor is associated with math-heavy AI or machine learning content? | Ahmed Elgammal. Reviews describe his courses as hard, math-heavy, and related to AI, computer vision, or machine learning, while also noting that he is caring and knowledgeable. |
| 5 | What do students say about Srinivas Narayana's lectures and course structure? | Students generally describe him as enthusiastic, clear, well-structured, and helpful, with recorded lectures, available resources, hard but fair assignments/exams, and participation or attendance helping understanding. |

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1. Reviews are noisy and subjective. Different students may describe the same professor in opposite ways, so the system needs to summarize disagreement instead of flattening reviews into a single confident recommendation.

2. Course and professor names can be ambiguous. A query like "who is good for intro CS?" might match CS111 reviews across multiple professors, while a query using only a course number may retrieve reviews that mention the course but do not answer the user's specific concern.

---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->

```mermaid
flowchart LR
    A[Document Ingestion<br/>Python requests/BeautifulSoup or saved HTML/text] --> B[Cleaning<br/>Remove navigation, ads, boilerplate]
    B --> C[Chunking<br/>Review-aware chunks grouped by professor/course]
    C --> D[Embedding + Vector Store<br/>sentence-transformers all-MiniLM-L6-v2 + ChromaDB]
    D --> E[Retrieval<br/>Top-k semantic search with source metadata]
    E --> F[Grounded Generation<br/>Groq llama-3.3-70b-versatile with citations]
```

---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

**Milestone 3 — Ingestion and chunking:**
I will give the AI the Domain, Documents, and Chunking Strategy sections and ask it to implement an ingestion script that saves each review document with metadata such as professor name, source URL, course tags, and review text. I will verify the output by inspecting a few processed documents and checking that boilerplate like navigation links and privacy notices is removed.

**Milestone 4 — Embedding and retrieval:**
I will give the AI the Retrieval Approach section and ask it to implement local embeddings with `sentence-transformers` and persistence with ChromaDB. I will verify retrieval before generation by running the five evaluation questions and checking whether the returned chunks mention the expected professor, course, and topic.

**Milestone 5 — Generation and interface:**
I will give the AI the grounding requirements and evaluation questions and ask it to build a simple CLI or notebook query interface that prints an answer plus cited source documents. I will verify that answers only use retrieved context by testing questions whose answers are not present in the corpus and checking that the system refuses or says the documents do not contain enough information.
