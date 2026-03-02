"""Dynamic prompt composition — augments prompts with profile + feedback."""

from __future__ import annotations

from typing import Optional

from legalos.profile.schemas import (
    FeedbackStore,
    FeedbackSummary,
    FounderProfile,
    LearningsStore,
    RiskTolerance,
)
from legalos.profile.store import compute_feedback_summary, compute_learning_summary, search_learnings

# Keyword mapping: section_id -> relevant priority keywords
_SECTION_KEYWORDS: dict[str, list[str]] = {
    "control_provisions": [
        "board", "control", "veto", "voting", "reserved matters",
        "protective provisions", "quorum", "deadlock",
    ],
    "capital_structure": [
        "dilution", "anti-dilution", "esop", "conversion", "capital",
        "pro-rata", "preference shares", "ratchet",
    ],
    "investor_rights": [
        "tag-along", "drag-along", "rofr", "rofo", "pre-emptive",
        "information rights", "mfn", "transfer",
    ],
    "key_events_exit": [
        "liquidation", "exit", "ipo", "put option", "call option",
        "deemed liquidation", "waterfall",
    ],
    "founder_obligations": [
        "non-compete", "lock-in", "vesting", "indemnification",
        "representation", "warranty", "exclusivity", "non-solicitation",
    ],
    "financial_terms": [
        "valuation", "investment", "tranche", "conditions precedent",
        "use of proceeds", "milestone", "closing",
    ],
}


def _build_founder_context(profile: FounderProfile) -> str:
    """Build the <founder_context> XML block from profile data."""
    parts: list[str] = ["<founder_context>"]

    # Company info
    c = profile.company
    if c.name or c.stage or c.sector:
        parts.append("Company:")
        if c.name:
            parts.append(f"  Name: {c.name}")
        if c.stage:
            parts.append(f"  Stage: {c.stage.value.replace('_', ' ').title()}")
        if c.sector:
            parts.append(f"  Sector: {c.sector}")
        if c.current_round:
            parts.append(f"  Current round: {c.current_round}")
        if c.previous_rounds:
            parts.append(f"  Previous rounds: {', '.join(c.previous_rounds)}")

    # Risk tolerance directive
    rt = profile.risk_tolerance
    if rt == RiskTolerance.CONSERVATIVE:
        parts.append(
            "\nRisk tolerance: CONSERVATIVE — Flag everything that deviates even slightly "
            "from market-standard terms. Err on the side of over-flagging."
        )
    elif rt == RiskTolerance.AGGRESSIVE:
        parts.append(
            "\nRisk tolerance: AGGRESSIVE — Only flag terms that are truly unusual or "
            "materially disadvantageous. Skip standard-but-unfavorable terms."
        )
    else:
        parts.append(
            "\nRisk tolerance: BALANCED — Flag aggressive and unusual terms. "
            "Note standard terms briefly without alarm."
        )

    # Priority areas
    p = profile.priorities
    if p.high_priority_areas:
        parts.append(
            "\nHigh-priority areas (give extra scrutiny):"
        )
        for area in p.high_priority_areas:
            parts.append(f"  - {area}")

    if p.custom_watchlist:
        parts.append(
            "\nCustom watchlist (ALWAYS flag if found, regardless of severity):"
        )
        for item in p.custom_watchlist:
            parts.append(f"  - {item}")

    if p.known_concerns:
        parts.append(f"\nKnown concerns: {p.known_concerns}")

    # Deal context
    d = profile.deal_context
    if d.investor_names or d.deal_size or d.pre_money_valuation:
        parts.append("\nDeal context:")
        if d.investor_names:
            parts.append(f"  Investors: {', '.join(d.investor_names)}")
        if d.lead_investor:
            parts.append(f"  Lead investor: {d.lead_investor}")
        if d.deal_size:
            parts.append(f"  Deal size: {d.deal_size}")
        if d.pre_money_valuation:
            parts.append(f"  Pre-money valuation: {d.pre_money_valuation}")

    # Legal team brief
    if profile.legal_team_brief:
        brief = profile.legal_team_brief
        if len(brief) > 10_000:
            brief = brief[:10_000] + "\n[...truncated to 10,000 characters]"
        parts.append("")
        parts.append("<legal_team_guidance>")
        parts.append(brief)
        parts.append("</legal_team_guidance>")

    parts.append("</founder_context>")
    return "\n".join(parts)


def _build_feedback_block_aggregated(summary: FeedbackSummary) -> str:
    """Build a compact <past_feedback> block from aggregated patterns."""
    if summary.total_sessions == 0:
        return ""

    parts: list[str] = ["<past_feedback>"]
    parts.append(
        f"Aggregated from {summary.total_sessions} previous analysis session(s)."
    )

    if summary.frequently_missed:
        parts.append(
            "\nFrequently missed items (give EXTRA attention to these):"
        )
        for item, count in summary.frequently_missed.items():
            parts.append(f"  - {item} (reported {count}x)")

    if summary.frequently_over_flagged:
        parts.append(
            "\nFrequently over-flagged items (reduce flagging unless truly unusual):"
        )
        for item, count in summary.frequently_over_flagged.items():
            parts.append(f"  - {item} (reported {count}x)")

    if summary.avg_rating is not None:
        parts.append(f"\nAverage satisfaction rating: {summary.avg_rating}/5")

    parts.append("</past_feedback>")
    return "\n".join(parts)


def _build_learnings_block(store: LearningsStore) -> str:
    """Build a compact <founder_learnings> XML block from the knowledge base."""
    if not store.entries:
        return ""

    summary = compute_learning_summary(store)
    parts: list[str] = ["<founder_learnings>"]
    parts.append(
        f"Knowledge base: {summary.total_entries} entries across "
        f"{len(summary.by_category)} categories."
    )

    # Include top entries by useful_count then recency
    sorted_entries = sorted(
        store.entries,
        key=lambda e: (e.useful_count, e.created_at),
        reverse=True,
    )
    top_entries = sorted_entries[:10]

    if summary.total_entries > 20:
        # Summarize counts instead of listing all
        parts.append("\nCategory breakdown:")
        for cat, count in summary.by_category.items():
            parts.append(f"  - {cat}: {count} entries")
        parts.append("\nKey learnings to apply:")
    else:
        parts.append("\nKey learnings to apply:")

    for entry in top_entries:
        parts.append(f"  - [{entry.category.value}] {entry.insight}")

    if summary.top_tags:
        parts.append(
            f"\nTop focus areas: {', '.join(summary.top_tags[:8])}"
        )

    parts.append("</founder_learnings>")
    return "\n".join(parts)


def build_full_system_prompt(
    base: str,
    profile: Optional[FounderProfile] = None,
    feedback: Optional[FeedbackStore] = None,
    learnings: Optional[LearningsStore] = None,
) -> str:
    """Augment the system prompt with founder context, past feedback, and learnings.

    Uses aggregated feedback patterns instead of raw items for
    token efficiency and prompt cache stability.

    Returns base prompt unchanged if no profile/feedback/learnings exists.
    """
    parts = [base]

    if profile is not None:
        parts.append("")
        parts.append(_build_founder_context(profile))

    if feedback is not None and feedback.items:
        summary = compute_feedback_summary(feedback)
        block = _build_feedback_block_aggregated(summary)
        if block:
            parts.append("")
            parts.append(block)

    if learnings is not None and learnings.entries:
        block = _build_learnings_block(learnings)
        if block:
            parts.append("")
            parts.append(block)

    return "\n".join(parts)


def _build_section_learnings_block(
    store: LearningsStore,
    section_id: str,
) -> str:
    """Build a compact <section_learnings> block for a specific analysis section."""
    matches = search_learnings(store, section_id=section_id)
    if not matches:
        return ""

    # Sort by useful_count (descending), limit to 5
    matches.sort(key=lambda e: e.useful_count, reverse=True)
    top = matches[:5]

    parts: list[str] = ["<section_learnings>"]
    parts.append("Relevant past insights for this section:")
    for entry in top:
        parts.append(f"  - {entry.insight}")
    parts.append("</section_learnings>")
    return "\n".join(parts)


def augment_section_prompt(
    base: str,
    profile: Optional[FounderProfile],
    section_id: str,
    document_type: str = "",
    learnings: Optional[LearningsStore] = None,
) -> str:
    """Add priority/watchlist reminders relevant to a specific section.

    Includes document-type-specific priority overrides and relevant learnings
    when available.

    Returns base prompt unchanged if no profile exists.
    """
    result = base

    if profile is not None:
        keywords = _SECTION_KEYWORDS.get(section_id, [])
        if keywords:
            # Collect priorities: base + document-type-specific overrides
            all_priority_areas = list(profile.priorities.high_priority_areas)
            if document_type and profile.priority_overrides:
                doc_key = document_type.lower().replace(" ", "_").replace("-", "_")
                override_priorities = profile.priority_overrides.get(doc_key, [])
                all_priority_areas.extend(override_priorities)

            # Find matching priority areas
            matching_priorities: list[str] = []
            for area in all_priority_areas:
                area_lower = area.lower()
                if any(kw in area_lower for kw in keywords):
                    matching_priorities.append(area)
            # Deduplicate while preserving order
            seen: set[str] = set()
            deduped: list[str] = []
            for p in matching_priorities:
                if p not in seen:
                    seen.add(p)
                    deduped.append(p)
            matching_priorities = deduped

            # Find matching watchlist items
            matching_watchlist: list[str] = []
            for item in profile.priorities.custom_watchlist:
                item_lower = item.lower()
                if any(kw in item_lower for kw in keywords):
                    matching_watchlist.append(item)

            if matching_priorities or matching_watchlist:
                addendum_parts: list[str] = ["\n\n<priority_reminder>"]
                if matching_priorities:
                    addendum_parts.append(
                        "The founder has flagged these as HIGH PRIORITY for this section:"
                    )
                    for p in matching_priorities:
                        addendum_parts.append(f"  - {p}")
                if matching_watchlist:
                    addendum_parts.append(
                        "WATCHLIST — always flag if found:"
                    )
                    for w in matching_watchlist:
                        addendum_parts.append(f"  - {w}")
                addendum_parts.append("</priority_reminder>")
                result += "\n".join(addendum_parts)

    # Append section-specific learnings
    if learnings is not None and learnings.entries:
        block = _build_section_learnings_block(learnings, section_id)
        if block:
            result += "\n\n" + block

    return result


def augment_impact_prompt(
    base: str,
    profile: Optional[FounderProfile],
) -> str:
    """Weight negotiation priorities by stated focus areas; use deal size for waterfall.

    Returns base prompt unchanged if no profile exists.
    """
    if profile is None:
        return base

    addendum_parts: list[str] = []

    # Deal size for waterfall calculations
    d = profile.deal_context
    if d.deal_size or d.pre_money_valuation:
        addendum_parts.append("\n\n<deal_parameters>")
        if d.deal_size:
            addendum_parts.append(f"Deal size: {d.deal_size}")
        if d.pre_money_valuation:
            addendum_parts.append(f"Pre-money valuation: {d.pre_money_valuation}")
        addendum_parts.append(
            "Use these figures for the exit waterfall calculations if "
            "they are consistent with the document terms."
        )
        addendum_parts.append("</deal_parameters>")

    # Priority weighting for negotiation items
    p = profile.priorities
    if p.high_priority_areas:
        addendum_parts.append("\n\n<negotiation_focus>")
        addendum_parts.append(
            "The founder considers these areas most important — "
            "weight negotiation priorities accordingly:"
        )
        for area in p.high_priority_areas:
            addendum_parts.append(f"  - {area}")
        addendum_parts.append("</negotiation_focus>")

    if not addendum_parts:
        return base

    return base + "\n".join(addendum_parts)
