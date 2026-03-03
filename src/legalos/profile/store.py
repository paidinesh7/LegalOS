"""JSON load/save for profile, deals, and feedback files."""

from __future__ import annotations

import json
import logging
from collections import Counter
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

from legalos.profile.schemas import (
    DealProfile,
    FeedbackItem,
    FeedbackStore,
    FeedbackSummary,
    FounderProfile,
    LearningCategory,
    LearningEntry,
    LearningSummary,
    LearningSource,
    LearningsStore,
    ReportFeedback,
)

PROFILE_FILENAME = "profile.json"
FEEDBACK_FILENAME = "feedback.json"
LEARNINGS_FILENAME = "learnings.json"
DEALS_DIR = "deals"


def _safe_deal_name(name: str) -> str:
    """Sanitize deal name for use as a filename. Prevents path traversal."""
    # Strip path separators and parent references
    safe = name.replace("/", "_").replace("\\", "_").replace("..", "_")
    # Remove any remaining non-alphanumeric chars except - and _
    safe = "".join(c for c in safe if c.isalnum() or c in "-_")
    if not safe:
        raise ValueError(f"Invalid deal name: {name!r}")
    return safe


def _resolve_dir() -> Path:
    """Return the .legalos directory (project-local if exists, else home)."""
    local = Path.cwd() / ".legalos"
    if local.exists():
        return local
    home = Path.home() / ".legalos"
    return home


def _ensure_dir(directory: Optional[Path] = None) -> Path:
    """Ensure the .legalos directory exists and return it."""
    d = directory or _resolve_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d


# ── Profile ─────────────────────────────────────────────────────


def load_profile(directory: Optional[Path] = None) -> Optional[FounderProfile]:
    """Load the founder profile, or None if it doesn't exist."""
    d = directory or _resolve_dir()
    path = d / PROFILE_FILENAME
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return FounderProfile.model_validate(data)
    except Exception as e:
        logger.warning("Failed to load profile from %s: %s", path, e)
        return None


def save_profile(profile: FounderProfile, directory: Optional[Path] = None) -> Path:
    """Save the founder profile and return the file path."""
    d = _ensure_dir(directory)
    path = d / PROFILE_FILENAME
    path.write_text(
        profile.model_dump_json(indent=2),
        encoding="utf-8",
    )
    return path


def delete_profile(directory: Optional[Path] = None) -> bool:
    """Delete the profile file. Returns True if deleted."""
    d = directory or _resolve_dir()
    path = d / PROFILE_FILENAME
    if path.exists():
        path.unlink()
        return True
    return False


def export_profile(output_path: Path, directory: Optional[Path] = None) -> Path:
    """Export profile to a specified path for team sharing."""
    profile = load_profile(directory)
    if profile is None:
        raise FileNotFoundError("No profile found to export.")
    output_path.write_text(
        profile.model_dump_json(indent=2),
        encoding="utf-8",
    )
    return output_path


def import_profile(input_path: Path, directory: Optional[Path] = None) -> FounderProfile:
    """Import profile from a file and save it."""
    data = json.loads(input_path.read_text(encoding="utf-8"))
    profile = FounderProfile.model_validate(data)
    save_profile(profile, directory)
    return profile


# ── Deals ───────────────────────────────────────────────────────


def _deals_dir(directory: Optional[Path] = None) -> Path:
    d = directory or _resolve_dir()
    return d / DEALS_DIR


def list_deals(directory: Optional[Path] = None) -> list[str]:
    """List available deal names."""
    dd = _deals_dir(directory)
    if not dd.exists():
        return []
    return sorted(p.stem for p in dd.glob("*.json"))


def load_deal(name: str, directory: Optional[Path] = None) -> Optional[DealProfile]:
    """Load a deal profile by name."""
    dd = _deals_dir(directory)
    path = dd / f"{_safe_deal_name(name)}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return DealProfile.model_validate(data)
    except Exception as e:
        logger.warning("Failed to load deal from %s: %s", path, e)
        return None


def save_deal(deal: DealProfile, directory: Optional[Path] = None) -> Path:
    """Save a deal profile."""
    dd = _deals_dir(directory)
    dd.mkdir(parents=True, exist_ok=True)
    path = dd / f"{_safe_deal_name(deal.name)}.json"
    path.write_text(
        deal.model_dump_json(indent=2),
        encoding="utf-8",
    )
    return path


def delete_deal(name: str, directory: Optional[Path] = None) -> bool:
    """Delete a deal profile. Returns True if deleted."""
    dd = _deals_dir(directory)
    path = dd / f"{_safe_deal_name(name)}.json"
    if path.exists():
        path.unlink()
        return True
    return False


def apply_deal_overlay(
    profile: FounderProfile,
    deal: DealProfile,
) -> FounderProfile:
    """Return a new profile with the deal context and watchlist overlaid."""
    merged = profile.model_copy(deep=True)
    merged.deal_context = deal.deal_context
    if deal.extra_watchlist:
        # Use dict.fromkeys to deduplicate while preserving insertion order
        combined = merged.priorities.custom_watchlist + deal.extra_watchlist
        merged.priorities.custom_watchlist = list(dict.fromkeys(combined))
    return merged


# ── Feedback ────────────────────────────────────────────────────


def load_feedback(directory: Optional[Path] = None) -> FeedbackStore:
    """Load the feedback store (empty if file doesn't exist)."""
    d = directory or _resolve_dir()
    path = d / FEEDBACK_FILENAME
    if not path.exists():
        return FeedbackStore()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return FeedbackStore.model_validate(data)
    except Exception as e:
        logger.warning("Failed to load feedback from %s: %s", path, e)
        return FeedbackStore()


def append_feedback(
    item: FeedbackItem,
    directory: Optional[Path] = None,
) -> Path:
    """Append a feedback item and return the file path."""
    store = load_feedback(directory)
    store.items.append(item)
    d = _ensure_dir(directory)
    path = d / FEEDBACK_FILENAME
    path.write_text(
        store.model_dump_json(indent=2),
        encoding="utf-8",
    )
    return path


def clear_feedback(directory: Optional[Path] = None) -> bool:
    """Delete all feedback. Returns True if file existed."""
    d = directory or _resolve_dir()
    path = d / FEEDBACK_FILENAME
    if path.exists():
        path.unlink()
        return True
    return False


def compute_feedback_summary(
    store: FeedbackStore,
) -> FeedbackSummary:
    """Aggregate raw feedback items into a compact summary."""
    if not store.items:
        return FeedbackSummary()

    missed_counter: Counter[str] = Counter()
    fp_counter: Counter[str] = Counter()
    ratings: list[int] = []

    for item in store.items:
        for m in item.missed_items:
            missed_counter[m] += 1
        for fp in item.false_positives:
            fp_counter[fp] += 1
        if item.overall_rating is not None:
            ratings.append(item.overall_rating)

    return FeedbackSummary(
        frequently_missed=dict(missed_counter.most_common(10)),
        frequently_over_flagged=dict(fp_counter.most_common(10)),
        avg_rating=round(sum(ratings) / len(ratings), 1) if ratings else None,
        total_sessions=len(store.items),
    )


# ── Report (per-finding) feedback ──────────────────────────────


def import_report_feedback(
    input_path: Path,
    directory: Optional[Path] = None,
) -> FeedbackItem:
    """Import per-finding feedback from HTML report export and convert to FeedbackItem.

    Downvoted findings become false_positives. The data is appended to
    the main feedback store so it feeds into future prompts.
    """
    data = json.loads(input_path.read_text(encoding="utf-8"))
    report_fb = ReportFeedback.model_validate(data)

    false_positives = [
        v.finding_title for v in report_fb.votes if v.vote == "down"
    ]

    item = FeedbackItem(
        document_name=report_fb.document_name,
        timestamp=report_fb.timestamp,
        false_positives=false_positives,
    )

    append_feedback(item, directory)
    return item


def submit_feedback_from_titles(
    doc_name: str,
    up_titles: list[str],
    down_titles: list[str],
    directory: Optional[Path] = None,
) -> FeedbackItem:
    """Create a FeedbackItem from explicit up/down title lists (from CLI submit).

    Downvoted titles become false_positives.
    """
    item = FeedbackItem(
        document_name=doc_name,
        false_positives=down_titles,
    )
    append_feedback(item, directory)
    return item


def auto_import_sidecar_feedback(directory: Optional[Path] = None) -> int:
    """Scan CWD for *.feedback.json sidecar files and import pending ones.

    Returns the number of sidecar files imported.
    """
    scan_dir = directory or Path.cwd()
    imported = 0

    for sidecar_path in scan_dir.glob("*.feedback.json"):
        try:
            data = json.loads(sidecar_path.read_text(encoding="utf-8"))
        except Exception:
            continue

        # Skip already-submitted or empty-vote sidecars
        if data.get("submitted", False):
            continue
        votes = data.get("votes", [])
        if not votes:
            continue

        # Convert to ReportFeedback and import
        report_fb = ReportFeedback.model_validate(data)
        false_positives = [
            v.finding_title for v in report_fb.votes if v.vote == "down"
        ]
        if not false_positives and not any(v.vote == "up" for v in report_fb.votes):
            continue

        item = FeedbackItem(
            document_name=report_fb.document_name,
            timestamp=report_fb.timestamp,
            false_positives=false_positives,
        )
        append_feedback(item)

        # Mark sidecar as submitted
        data["submitted"] = True
        sidecar_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        imported += 1

    return imported


def check_feedback_effectiveness(
    store: FeedbackStore,
    current_finding_titles: list[str],
) -> list[str]:
    """Check which previously-missed items are now caught.

    Returns a list of resolved items (items that were previously reported as
    missed but appear in the current analysis findings).
    """
    if not store.items:
        return []

    all_missed: set[str] = set()
    for item in store.items:
        for m in item.missed_items:
            all_missed.add(m.lower())

    current_lower = {t.lower() for t in current_finding_titles}

    resolved: list[str] = []
    for missed in all_missed:
        # Check if any current finding title contains the missed item keyword
        if any(missed in title for title in current_lower):
            resolved.append(missed)

    return resolved


# ── Learnings / Knowledge Base ─────────────────────────────────


def load_learnings(directory: Optional[Path] = None) -> LearningsStore:
    """Load the learnings store (empty if file doesn't exist)."""
    d = directory or _resolve_dir()
    path = d / LEARNINGS_FILENAME
    if not path.exists():
        return LearningsStore()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return LearningsStore.model_validate(data)
    except Exception as e:
        logger.warning("Failed to load learnings from %s: %s", path, e)
        return LearningsStore()


def _save_learnings(store: LearningsStore, directory: Optional[Path] = None) -> Path:
    """Write the full learnings store to disk."""
    d = _ensure_dir(directory)
    path = d / LEARNINGS_FILENAME
    path.write_text(store.model_dump_json(indent=2), encoding="utf-8")
    return path


def append_learning(
    entry: LearningEntry,
    directory: Optional[Path] = None,
) -> Path:
    """Append a learning entry and return the file path."""
    store = load_learnings(directory)
    store.entries.append(entry)
    return _save_learnings(store, directory)


def update_learning(
    entry_id: str,
    updates: dict,
    directory: Optional[Path] = None,
) -> Optional[LearningEntry]:
    """Update fields on an existing learning entry. Returns updated entry or None."""
    store = load_learnings(directory)
    for entry in store.entries:
        if entry.id == entry_id:
            for key, value in updates.items():
                if hasattr(entry, key):
                    setattr(entry, key, value)
            _save_learnings(store, directory)
            return entry
    return None


def delete_learning(entry_id: str, directory: Optional[Path] = None) -> bool:
    """Delete a learning entry by ID. Returns True if found and deleted."""
    store = load_learnings(directory)
    original_len = len(store.entries)
    store.entries = [e for e in store.entries if e.id != entry_id]
    if len(store.entries) < original_len:
        _save_learnings(store, directory)
        return True
    return False


def clear_learnings(directory: Optional[Path] = None) -> bool:
    """Delete all learnings. Returns True if file existed."""
    d = directory or _resolve_dir()
    path = d / LEARNINGS_FILENAME
    if path.exists():
        path.unlink()
        return True
    return False


def search_learnings(
    store: LearningsStore,
    query: str = "",
    section_id: str = "",
    category: str = "",
) -> list[LearningEntry]:
    """Filter learnings by keyword, section, and/or category."""
    results = list(store.entries)

    if category:
        results = [e for e in results if e.category.value == category]

    if section_id:
        # Use _SECTION_KEYWORDS for fuzzy matching
        from legalos.profile.prompt_injection import _SECTION_KEYWORDS

        keywords = _SECTION_KEYWORDS.get(section_id, [])
        filtered: list[LearningEntry] = []
        for entry in results:
            # Direct section_ids match
            if section_id in entry.section_ids:
                filtered.append(entry)
                continue
            # Fuzzy: check if entry tags/title/insight match section keywords
            combined = " ".join([entry.title, entry.insight] + entry.tags).lower()
            if any(kw in combined for kw in keywords):
                filtered.append(entry)
        results = filtered

    if query:
        q_lower = query.lower()
        filtered = []
        for entry in results:
            searchable = " ".join(
                [entry.title, entry.insight] + entry.tags
            ).lower()
            if q_lower in searchable:
                filtered.append(entry)
        results = filtered

    return results


def compute_learning_summary(store: LearningsStore) -> LearningSummary:
    """Compute a compact summary of the learnings store."""
    if not store.entries:
        return LearningSummary()

    by_category: Counter[str] = Counter()
    tag_counter: Counter[str] = Counter()
    for entry in store.entries:
        by_category[entry.category.value] += 1
        for tag in entry.tags:
            tag_counter[tag] += 1

    # Top entries by useful_count then recency
    sorted_entries = sorted(
        store.entries,
        key=lambda e: (e.useful_count, e.created_at),
        reverse=True,
    )
    most_useful = [e.title for e in sorted_entries[:5]]

    return LearningSummary(
        total_entries=len(store.entries),
        by_category=dict(by_category),
        top_tags=[tag for tag, _ in tag_counter.most_common(10)],
        most_useful=most_useful,
    )


def export_learnings_markdown(store: LearningsStore) -> str:
    """Export learnings as a Markdown document grouped by category."""
    lines: list[str] = ["# Legal Knowledge Base\n"]

    grouped: dict[str, list[LearningEntry]] = {}
    for entry in store.entries:
        grouped.setdefault(entry.category.value, []).append(entry)

    category_labels = {
        "clause_pattern": "Clause Patterns",
        "negotiation": "Negotiation Outcomes",
        "red_flag": "Red Flags",
        "decision": "Decisions Made",
        "market_insight": "Market Insights",
        "general": "General Notes",
    }

    for cat_value, label in category_labels.items():
        entries = grouped.get(cat_value, [])
        if not entries:
            continue

        lines.append(f"## {label}\n")

        if cat_value == "negotiation":
            lines.append("| What We Pushed Back On | Result | Document |")
            lines.append("|------------------------|--------|----------|")
            for e in entries:
                action = e.founder_action or "-"
                doc = e.document_name or "-"
                lines.append(f"| {e.title} | {action} | {doc} |")
        elif cat_value in ("red_flag", "decision", "general", "market_insight"):
            for e in entries:
                lines.append(f"- {e.insight}")
        else:
            # clause_pattern — table format
            lines.append("| Insight | Tags | Source |")
            lines.append("|---------|------|--------|")
            for e in entries:
                tags = ", ".join(e.tags) if e.tags else "-"
                source_label = e.source.value.replace("_", " ").title()
                if e.document_name:
                    source_label += f" ({e.document_name})"
                lines.append(f"| {e.insight} | {tags} | {source_label} |")

        lines.append("")

    summary = compute_learning_summary(store)
    lines.append("---")
    lines.append(
        f"*Exported from LegalOS. "
        f"{summary.total_entries} entries across "
        f"{len(summary.by_category)} categories.*"
    )

    return "\n".join(lines)


def import_learnings(input_path: Path, directory: Optional[Path] = None) -> int:
    """Import learnings from a JSON file. Returns count of entries imported."""
    data = json.loads(input_path.read_text(encoding="utf-8"))
    incoming = LearningsStore.model_validate(data)

    store = load_learnings(directory)
    existing_titles = {e.title.lower() for e in store.entries}

    added = 0
    for entry in incoming.entries:
        if entry.title.lower() not in existing_titles:
            entry.source = LearningSource.IMPORT
            store.entries.append(entry)
            existing_titles.add(entry.title.lower())
            added += 1

    if added:
        _save_learnings(store, directory)
    return added
