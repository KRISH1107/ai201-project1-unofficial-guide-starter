"""Gradio query interface for the Unofficial Guide (Milestone 5).

Run:
    python app.py
then open http://localhost:7860

Type a question about a Rutgers CS professor or course, click Ask (or press
Enter), and the app shows a grounded answer plus the source documents the
answer was drawn from.
"""

from __future__ import annotations

import gradio as gr

from query import ask

EXAMPLES = [
    "What do students say about Ana Paula Centeno's CS111 exams?",
    "Which professors give a lot of extra credit?",
    "What are the main complaints about John-Austen Francisco's teaching?",
    "Which professor teaches math-heavy AI or machine learning content?",
    "What is the best dining hall on campus?",  # out-of-domain: should decline
]


def handle_query(question: str):
    question = (question or "").strip()
    if not question:
        return "Please enter a question.", ""

    result = ask(question)

    if result["sources"]:
        sources = "\n".join(f"- {s}" for s in result["sources"])
    else:
        sources = "(No sources - the system did not find enough relevant context.)"
    return result["answer"], sources


with gr.Blocks(title="The Unofficial Guide - Rutgers CS Reviews") as demo:
    gr.Markdown(
        "# The Unofficial Guide: Rutgers CS Professor Reviews\n"
        "Ask about teaching style, workload, exams, grading, or extra credit. "
        "Answers are grounded only in collected student reviews and cite their sources."
    )
    question = gr.Textbox(
        label="Your question",
        placeholder="e.g. What do students say about Professor Narayana's lectures?",
    )
    ask_btn = gr.Button("Ask", variant="primary")
    answer = gr.Textbox(label="Answer", lines=8)
    sources = gr.Textbox(label="Retrieved from (sources)", lines=4)

    gr.Examples(examples=EXAMPLES, inputs=question)

    ask_btn.click(handle_query, inputs=question, outputs=[answer, sources])
    question.submit(handle_query, inputs=question, outputs=[answer, sources])


if __name__ == "__main__":
    demo.launch()
