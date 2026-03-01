"""Auto-capture learnings from analysis results + manual note offering."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from legalos.analysis.schemas import FullAnalysis
from legalos.profile.schemas import (
    FeedbackStore,
    LearningCategory,
    LearningEntry,
    LearningSource,
    LearningsStore,
)
from legalos.profile.store import append_learning, check_feedback_effectiveness


def auto_capture_learnings(
    analysis: FullAnalysis,
    feedback: Optional[FeedbackStore] = None,
    existing: Optional[LearningsStore] = None,
    directory: Optional[Path] = None,
) -> list[LearningEntry]:
    """Extract learnings from analysis results and save them.

    Captures:
    1. High/critical severity findings -> CLAUSE_PATTERN entries
    2. Negotiation items from impact assessment -> NEGOTIATION entries
    3. Previously-missed items now caught (feedback effectiveness) -> AUTO_FEEDBACK entries

    Deduplication: skips if an entry with the same title already exists (case-insensitive).
    """
    existing_titles: set[str] = set()
    if existing:
        existing_titles = {e.title.lower() for e in existing.entries}

    new_entries: list[LearningEntry] = []

    def _add(entry: LearningEntry) -> None:
        if entry.title.lower() not in existing_titles:
            existing_titles.add(entry.title.lower())
            new_entries.append(entry)
            append_learning(entry, directory)

    # 1. High/critical severity findings -> CLAUSE_PATTERN
    for section in analysis.sections:
        if section.risk_level not in ("high", "critical"):
            continue
        for finding in section.findings:
            if finding.severity.value not in ("aggressive", "unusual"):
                continue
            tags = _extract_tags(finding.title)
            _add(LearningEntry(
                title=finding.title,
                insight=f"{finding.explanation} ({finding.severity.value})",
                category=LearningCategory.CLAUSE_PATTERN,
                source=LearningSource.AUTO_ANALYSIS,
                tags=tags,
                section_ids=[section.section_id],
                document_name=analysis.document_name,
            ))

    # 2. Negotiation items from impact assessment -> NEGOTIATION
    if analysis.impact and analysis.impact.top_negotiation_items:
        for item in analysis.impact.top_negotiation_items:
            if item.priority > 7:  # Only high-priority items
                continue
            tags = _extract_tags(item.item)
            _add(LearningEntry(
                title=f"Negotiation priority: {item.item}",
                insight=item.suggested_change,
                category=LearningCategory.NEGOTIATION,
                source=LearningSource.AUTO_ANALYSIS,
                tags=tags,
                founder_action=item.current_language,
                document_name=analysis.document_name,
            ))

    # 3. Previously-missed items now caught -> AUTO_FEEDBACK
    if feedback and feedback.items:
        all_finding_titles = [
            f.title for section in analysis.sections for f in section.findings
        ]
        resolved = check_feedback_effectiveness(feedback, all_finding_titles)
        for item_text in resolved:
            _add(LearningEntry(
                title=f"Now catching: {item_text}",
                insight=f"Previously missed '{item_text}' is now being detected by the analysis",
                category=LearningCategory.CLAUSE_PATTERN,
                source=LearningSource.AUTO_FEEDBACK,
                tags=_extract_tags(item_text),
                document_name=analysis.document_name,
            ))

    return new_entries


def offer_manual_learning(directory: Optional[Path] = None) -> Optional[LearningEntry]:
    """Prompt the founder to optionally record a manual insight.

    Returns the created LearningEntry, or None if skipped.
    """
    from rich.prompt import Prompt

    from legalos.utils.progress import console

    console.print()
    insight_text = Prompt.ask(
        "[bold cyan]Any insight to record from this analysis?[/] (or Enter to skip)",
        default="",
    )
    if not insight_text.strip():
        return None

    title = Prompt.ask("  Short title for this learning", default=insight_text[:60])

    category_choices = [c.value for c in LearningCategory]
    cat_input = Prompt.ask(
        f"  Category ({', '.join(category_choices)})",
        default="general",
    )
    try:
        category = LearningCategory(cat_input)
    except ValueError:
        category = LearningCategory.GENERAL

    tags_input = Prompt.ask("  Tags (comma-separated)", default="")
    tags = [t.strip() for t in tags_input.split(",") if t.strip()] if tags_input else []

    entry = LearningEntry(
        title=title,
        insight=insight_text,
        category=category,
        source=LearningSource.MANUAL,
        tags=tags,
    )
    append_learning(entry, directory)
    return entry


def _extract_tags(text: str) -> list[str]:
    """Extract likely tag keywords from a text string."""
    # Common legal terms that make good tags
    tag_candidates = [
        "anti-dilution", "board", "veto", "drag-along", "tag-along",
        "liquidation", "rofr", "rofo", "esop", "vesting", "non-compete",
        "lock-in", "waterfall", "ratchet", "conversion", "pro-rata",
        "pre-emptive", "indemnification", "valuation", "tranche",
        "protective provisions", "reserved matters", "put option",
        "call option", "pay-to-play", "mfn", "information rights",
        "deemed liquidation", "milestone", "exclusivity",
    ]
    text_lower = text.lower()
    return [tag for tag in tag_candidates if tag in text_lower]
