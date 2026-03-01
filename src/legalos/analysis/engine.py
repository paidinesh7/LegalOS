"""Analysis orchestrator — runs 6 sectoral passes + explainer + impact."""

from __future__ import annotations

from typing import Optional

from legalos.analysis.client import AnalysisClient
from legalos.analysis.prompts import (
    EXPLAINER_PROMPT,
    IMPACT_PROMPT,
    REDLINE_PROMPT,
    SECTION_PROMPTS,
    SYSTEM_PROMPT,
)
from legalos.analysis.schemas import (
    AnalysisSection,
    ExplainerOutput,
    FeedbackInsight,
    Finding,
    FullAnalysis,
    ImpactOutput,
    RedlineOutput,
)
from legalos.parsing.base import ParsedDocument
from legalos.parsing.chunker import DocumentChunk, chunk_document
from legalos.profile.prompt_injection import (
    augment_impact_prompt,
    augment_section_prompt,
    build_full_system_prompt,
)
from legalos.profile.schemas import FeedbackStore, FounderProfile, LearningsStore
from legalos.profile.store import compute_feedback_summary
from legalos.utils.progress import make_progress, print_warning


def _merge_findings(all_findings: list[Finding]) -> list[Finding]:
    """Deduplicate findings by clause_reference."""
    seen: set[str] = set()
    merged: list[Finding] = []
    for f in all_findings:
        key = f.clause_reference.strip().lower()
        if key not in seen:
            seen.add(key)
            merged.append(f)
    return merged


def _build_feedback_insights(feedback: Optional[FeedbackStore]) -> list[FeedbackInsight]:
    """Build FeedbackInsight entries from aggregated feedback patterns.

    Uses the same aggregated summary as prompt injection for consistency.
    """
    if feedback is None or not feedback.items:
        return []

    summary = compute_feedback_summary(feedback)
    insights: list[FeedbackInsight] = []

    if summary.frequently_missed:
        items = ", ".join(
            f"{item} ({count}x)" for item, count in summary.frequently_missed.items()
        )
        insights.append(FeedbackInsight(
            source=f"Aggregated from {summary.total_sessions} session(s)",
            action=f"Extra attention given to frequently missed items: {items}",
        ))

    if summary.frequently_over_flagged:
        items = ", ".join(
            f"{item} ({count}x)" for item, count in summary.frequently_over_flagged.items()
        )
        insights.append(FeedbackInsight(
            source=f"Aggregated from {summary.total_sessions} session(s)",
            action=f"Reduced flagging for frequently over-flagged items: {items}",
        ))

    if summary.avg_rating is not None:
        insights.append(FeedbackInsight(
            source=f"Aggregated from {summary.total_sessions} session(s)",
            action=f"Average satisfaction rating: {summary.avg_rating}/5",
        ))

    return insights


def _analyze_section_chunked(
    client: AnalysisClient,
    section_id: str,
    section_name: str,
    prompt: str,
    chunks: list[DocumentChunk],
    system_prompt: str,
) -> AnalysisSection:
    """Run a single section analysis across multiple chunks and merge."""
    all_findings: list[Finding] = []
    last_result: AnalysisSection | None = None

    for chunk in chunks:
        chunk_prompt = prompt
        if chunk.total_chunks > 1:
            chunk_prompt += (
                f"\n\n[This is chunk {chunk.chunk_index + 1} of {chunk.total_chunks}. "
                f"Focus on clauses in this portion of the document.]"
            )

        result = client.analyze(
            system_prompt=system_prompt,
            user_prompt=chunk_prompt,
            response_model=AnalysisSection,
            document_text=chunk.text,
        )
        all_findings.extend(result.findings)
        last_result = result

    if last_result is None:
        return AnalysisSection(
            section_name=section_name,
            section_id=section_id,
            summary="No content found for analysis.",
            risk_level="low",
        )

    # Merge findings across chunks
    merged = _merge_findings(all_findings)
    last_result.findings = merged
    last_result.section_id = section_id
    last_result.section_name = section_name
    return last_result


def run_analysis(
    client: AnalysisClient,
    documents: list[ParsedDocument],
    profile: Optional[FounderProfile] = None,
    feedback: Optional[FeedbackStore] = None,
    document_type: str = "",
    learnings: Optional[LearningsStore] = None,
) -> FullAnalysis:
    """Run full analysis pipeline across all documents."""
    # Combine all document text
    combined_text = "\n\n---\n\n".join(doc.full_text for doc in documents)
    doc_name = ", ".join(doc.source_path.name for doc in documents)

    chunks = chunk_document(combined_text)

    # Build augmented system prompt (cached across all passes)
    system_prompt = build_full_system_prompt(SYSTEM_PROMPT, profile, feedback, learnings)

    sections: list[AnalysisSection] = []
    total_steps = len(SECTION_PROMPTS) + 2  # +2 for explainer and impact

    with make_progress() as progress:
        task = progress.add_task("Analyzing document\u2026", total=total_steps)

        # 6 sectoral passes
        for section_id, section_name, prompt in SECTION_PROMPTS:
            progress.update(task, description=f"Analyzing {section_name}\u2026")
            # Augment section prompt with priority reminders, doc-type overrides, and learnings
            augmented_prompt = augment_section_prompt(
                prompt, profile, section_id, document_type=document_type,
                learnings=learnings,
            )
            section = _analyze_section_chunked(
                client, section_id, section_name, augmented_prompt, chunks,
                system_prompt=system_prompt,
            )
            sections.append(section)
            progress.advance(task)

        # Explainer pass (uses full text, single pass — it's a synthesis)
        progress.update(task, description="Generating plain English guide\u2026")
        try:
            explainer = client.analyze(
                system_prompt=system_prompt,
                user_prompt=EXPLAINER_PROMPT,
                response_model=ExplainerOutput,
                document_text=combined_text[:500_000],  # Truncate if huge
            )
        except Exception as e:
            print_warning(f"Explainer pass failed: {e}")
            explainer = ExplainerOutput()
        progress.advance(task)

        # Impact assessment pass
        progress.update(task, description="Assessing founder impact\u2026")
        try:
            impact_prompt = augment_impact_prompt(IMPACT_PROMPT, profile)
            impact = client.analyze(
                system_prompt=system_prompt,
                user_prompt=impact_prompt,
                response_model=ImpactOutput,
                document_text=combined_text[:500_000],
            )
        except Exception as e:
            print_warning(f"Impact assessment failed: {e}")
            impact = None
        progress.advance(task)

    # Build feedback insights
    feedback_insights = _build_feedback_insights(feedback)

    return FullAnalysis(
        document_name=doc_name,
        document_type=document_type or "Legal Document",
        sections=sections,
        explainer=explainer,
        impact=impact,
        feedback_insights=feedback_insights,
    )


def run_redline_analysis(
    client: AnalysisClient,
    documents: list[ParsedDocument],
    profile: Optional[FounderProfile] = None,
    feedback: Optional[FeedbackStore] = None,
    learnings: Optional[LearningsStore] = None,
) -> RedlineOutput:
    """Run redline-focused analysis for DOCX annotation."""
    combined_text = "\n\n---\n\n".join(doc.full_text for doc in documents)
    chunks = chunk_document(combined_text)

    system_prompt = build_full_system_prompt(SYSTEM_PROMPT, profile, feedback, learnings)

    all_comments = []
    with make_progress() as progress:
        task = progress.add_task("Generating redline comments\u2026", total=len(chunks))
        for chunk in chunks:
            result = client.analyze(
                system_prompt=system_prompt,
                user_prompt=REDLINE_PROMPT,
                response_model=RedlineOutput,
                document_text=chunk.text,
            )
            all_comments.extend(result.comments)
            progress.advance(task)

    return RedlineOutput(comments=all_comments)
