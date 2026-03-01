"""Post-analysis feedback collection with effectiveness tracking."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from legalos.analysis.schemas import FullAnalysis
from legalos.profile.schemas import FeedbackItem, FeedbackStore
from legalos.profile.store import append_feedback, check_feedback_effectiveness

console = Console()


def _show_effectiveness(feedback: FeedbackStore, analysis: FullAnalysis) -> None:
    """Show which previously-missed items were caught this time."""
    all_titles: list[str] = []
    for section in analysis.sections:
        for f in section.findings:
            all_titles.append(f.title)

    resolved = check_feedback_effectiveness(feedback, all_titles)
    if resolved:
        console.print()
        console.print("[bold green]Feedback loop working:[/]")
        for item in resolved:
            console.print(f"  [green]\u2713[/] Previously missed '{item}' — now caught!")


def run_feedback_flow(
    document_name: str = "",
    model_used: str = "",
    feedback: Optional[FeedbackStore] = None,
    analysis: Optional[FullAnalysis] = None,
    directory: Path | None = None,
) -> Optional[FeedbackItem]:
    """Run the post-analysis feedback collection.

    Returns the FeedbackItem if collected, or None if skipped.
    """
    # Show effectiveness of previous feedback
    if feedback is not None and analysis is not None and feedback.items:
        _show_effectiveness(feedback, analysis)

    console.print()
    console.print(Panel(
        "[bold]Help LegalOS Learn[/bold]\n"
        "Quick feedback to improve future analyses.\n"
        "Type [bold cyan]skip[/] to skip entirely.",
        style="blue",
        expand=False,
    ))
    console.print()

    # Question 1: Missed items
    missed_input = Prompt.ask(
        "[bold]1.[/] Did LegalOS miss anything important? (comma-separated, or 'skip')",
        default="",
    )
    if missed_input.strip().lower() == "skip":
        console.print("[dim]Feedback skipped.[/]")
        return None

    missed_items = [m.strip() for m in missed_input.split(",") if m.strip()] if missed_input else []

    # Question 2: False positives
    fp_input = Prompt.ask(
        "[bold]2.[/] Any findings that were NOT relevant? (comma-separated)",
        default="",
    )
    false_positives = [f.strip() for f in fp_input.split(",") if f.strip()] if fp_input else []

    # Question 3: Additional concerns
    additional = Prompt.ask(
        "[bold]3.[/] Other concerns or comments?",
        default="",
    )

    # Question 4: Rating
    rating: Optional[int] = None
    rating_input = Prompt.ask(
        "[bold]4.[/] Rate this analysis (1-5, or Enter to skip)",
        default="",
    )
    if rating_input.strip().isdigit():
        val = int(rating_input.strip())
        if 1 <= val <= 5:
            rating = val

    item = FeedbackItem(
        document_name=document_name,
        model_used=model_used,
        missed_items=missed_items,
        false_positives=false_positives,
        additional_concerns=additional,
        overall_rating=rating,
    )

    path = append_feedback(item, directory)
    console.print(f"\n[bold green]\u2713[/] Feedback saved to {path}")

    return item
