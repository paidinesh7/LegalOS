"""Interactive terminal Q&A with conversation history."""

from __future__ import annotations

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from legalos.analysis.client import AnalysisClient
from legalos.analysis.prompts import SYSTEM_PROMPT
from legalos.analysis.schemas import FullAnalysis

console = Console()

QA_SYSTEM_ADDENDUM = """

You are now in an interactive Q&A session with a startup founder. They have just reviewed \
your analysis of their legal document. Answer their questions precisely, referencing specific \
clauses and your earlier analysis where relevant. Keep answers concise but thorough. \
If they ask about something not covered in the document, say so clearly."""


def run_qa_session(
    client: AnalysisClient,
    document_text: str,
    analysis: FullAnalysis,
) -> None:
    """Run an interactive Q&A REPL in the terminal."""
    system = SYSTEM_PROMPT + QA_SYSTEM_ADDENDUM

    # Seed context with analysis summary
    analysis_summary = _build_analysis_context(analysis)
    full_doc_context = f"{document_text}\n\n---\n\nPrevious analysis summary:\n{analysis_summary}"

    messages: list[dict] = []

    console.print()
    console.print(Panel(
        "[bold]Q&A Session[/bold]\n"
        "Ask questions about the document and analysis.\n"
        "Type [bold cyan]quit[/] or [bold cyan]exit[/] to end.",
        style="blue",
        expand=False,
    ))
    console.print()

    while True:
        try:
            question = console.input("[bold green]You:[/] ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not question:
            continue
        if question.lower() in ("quit", "exit", "q"):
            break

        messages.append({"role": "user", "content": question})

        try:
            answer = client.chat(
                system_prompt=system,
                messages=messages,
                document_text=full_doc_context,
            )
        except Exception as e:
            console.print(f"[bold red]Error:[/] {e}")
            messages.pop()  # Remove failed question
            continue

        messages.append({"role": "assistant", "content": answer})

        console.print()
        console.print("[bold blue]LegalOS:[/]")
        console.print(Markdown(answer))
        console.print()

    console.print("[dim]Q&A session ended.[/]")


def _build_analysis_context(analysis: FullAnalysis) -> str:
    """Build a compact summary of analysis for Q&A context."""
    parts: list[str] = []
    for section in analysis.sections:
        parts.append(f"## {section.section_name} (Risk: {section.risk_level})")
        parts.append(section.summary)
        for f in section.findings[:5]:  # Top 5 per section to save tokens
            parts.append(f"- [{f.severity.value}] {f.title}: {f.explanation}")
    return "\n".join(parts)
