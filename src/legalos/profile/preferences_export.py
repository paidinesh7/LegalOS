"""Generate MyPreferences markdown + HTML summary of what LegalOS knows about the founder."""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Optional

from legalos.profile.schemas import (
    FeedbackStore,
    FounderProfile,
    LearningsStore,
    RiskTolerance,
)
from legalos.profile.store import (
    compute_feedback_summary,
    compute_learning_summary,
    list_deals,
    load_feedback,
    load_learnings,
    load_profile,
    _resolve_dir,
)

_ADDITIONAL_NOTES_HEADER = "## Additional Notes"
_ADDITIONAL_NOTES_GUIDANCE = (
    "_This section is yours to edit. Add any custom instructions, preferences, "
    "or context you want LegalOS to consider during every analysis. "
    "Your edits here are preserved when you re-run `legalos preferences`._\n\n"
    "<!-- Write your notes below this line -->\n"
)

_RISK_DESCRIPTIONS = {
    RiskTolerance.CONSERVATIVE: (
        "**Conservative** — LegalOS flags everything that deviates even slightly "
        "from market-standard terms. Errs on the side of over-flagging so nothing slips through."
    ),
    RiskTolerance.BALANCED: (
        "**Balanced** — LegalOS flags aggressive and unusual terms, and notes "
        "standard-but-unfavorable terms briefly without alarm."
    ),
    RiskTolerance.AGGRESSIVE: (
        "**Aggressive** — LegalOS only flags terms that are truly unusual or "
        "materially disadvantageous. Standard-but-unfavorable terms are skipped."
    ),
}


def generate_preferences_markdown(
    profile: Optional[FounderProfile] = None,
    feedback: Optional[FeedbackStore] = None,
    learnings: Optional[LearningsStore] = None,
    deals_dir: Optional[Path] = None,
) -> str:
    """Build the full MyPreferences markdown document."""
    lines: list[str] = ["# My LegalOS Preferences\n"]

    # 1. Company Profile
    lines.append("## Company Profile\n")
    if profile and (profile.company.name or profile.company.stage or profile.company.sector):
        c = profile.company
        if c.name:
            lines.append(f"- **Company:** {c.name}")
        if c.stage:
            lines.append(f"- **Stage:** {c.stage.value.replace('_', ' ').title()}")
        if c.sector:
            lines.append(f"- **Sector:** {c.sector}")
        if c.current_round:
            lines.append(f"- **Current Round:** {c.current_round}")
        if c.previous_rounds:
            lines.append(f"- **Previous Rounds:** {', '.join(c.previous_rounds)}")
    else:
        lines.append("_No profile configured yet. Run `legalos init` to set up._")
    lines.append("")

    # 2. Risk Tolerance & Analysis Style
    lines.append("## Risk Tolerance & Analysis Style\n")
    if profile:
        desc = _RISK_DESCRIPTIONS.get(profile.risk_tolerance, "Balanced")
        lines.append(desc)
    else:
        lines.append("_Default: Balanced_")
    lines.append("")

    # 3. Priority Areas & Watchlist
    lines.append("## Priority Areas & Watchlist\n")
    has_priorities = False
    if profile:
        p = profile.priorities
        if p.high_priority_areas:
            has_priorities = True
            lines.append("**High Priority Areas** (receive extra scrutiny):\n")
            for area in p.high_priority_areas:
                lines.append(f"- {area}")
            lines.append("")
        if p.custom_watchlist:
            has_priorities = True
            lines.append("**Custom Watchlist** (always flagged if found):\n")
            for item in p.custom_watchlist:
                lines.append(f"- {item}")
            lines.append("")
        if p.known_concerns:
            has_priorities = True
            lines.append(f"**Known Concerns:** {p.known_concerns}\n")
    if not has_priorities:
        lines.append("_No priority areas configured. Use `legalos profile set` to add them._\n")

    # 4. Legal Team Brief
    lines.append("## Legal Team Brief\n")
    if profile and profile.legal_team_brief:
        brief = profile.legal_team_brief
        if len(brief) > 2000:
            brief = brief[:2000] + "\n\n_[...truncated — full brief is used during analysis]_"
        lines.append(brief)
    else:
        lines.append("_No legal team brief provided. Add one via `legalos init` or `legalos profile set legal_team_brief \"...\"`._")
    lines.append("")

    # 5. Active Deals
    lines.append("## Active Deals\n")
    deal_names = list_deals()
    if deal_names:
        for name in deal_names:
            lines.append(f"- {name}")
    else:
        lines.append("_No deals configured. Use `legalos deal add <name>` to create one._")
    lines.append("")

    # 6. Feedback Patterns
    lines.append("## Feedback Patterns\n")
    if feedback and feedback.items:
        summary = compute_feedback_summary(feedback)
        lines.append(f"- **Total Sessions:** {summary.total_sessions}")
        if summary.avg_rating is not None:
            lines.append(f"- **Average Rating:** {summary.avg_rating}/5")
        if summary.frequently_missed:
            lines.append("\n**Frequently Missed** (LegalOS gives these extra attention):\n")
            for item, count in summary.frequently_missed.items():
                lines.append(f"- {item} ({count}x)")
        if summary.frequently_over_flagged:
            lines.append("\n**Frequently Over-Flagged** (LegalOS reduces flagging):\n")
            for item, count in summary.frequently_over_flagged.items():
                lines.append(f"- {item} ({count}x)")
    else:
        lines.append("_No feedback collected yet. Feedback is gathered after each analysis._")
    lines.append("")

    # 7. Top Learnings
    lines.append("## Top Learnings\n")
    if learnings and learnings.entries:
        summary = compute_learning_summary(learnings)
        lines.append(f"- **Total Entries:** {summary.total_entries}")
        if summary.by_category:
            cats = ", ".join(
                f"{cat.replace('_', ' ').title()} ({count})"
                for cat, count in summary.by_category.items()
            )
            lines.append(f"- **Categories:** {cats}")
        if summary.most_useful:
            lines.append("\n**Most Referenced:**\n")
            for title in summary.most_useful:
                lines.append(f"- {title}")
        if summary.top_tags:
            lines.append(f"\n**Focus Areas:** {', '.join(summary.top_tags)}")
    else:
        lines.append("_No learnings yet. They are auto-captured during analysis, or add manually with `legalos kb add`._")
    lines.append("")

    # 8. Additional Notes
    lines.append(f"{_ADDITIONAL_NOTES_HEADER}\n")
    lines.append(_ADDITIONAL_NOTES_GUIDANCE)

    return "\n".join(lines)


def _preserve_additional_notes(existing_path: Path, new_content: str) -> str:
    """If the existing file has custom content in Additional Notes, preserve it."""
    if not existing_path.exists():
        return new_content

    existing = existing_path.read_text(encoding="utf-8")

    # Extract everything after "## Additional Notes" in the existing file
    marker = _ADDITIONAL_NOTES_HEADER
    existing_idx = existing.find(marker)
    if existing_idx == -1:
        return new_content

    existing_notes_section = existing[existing_idx + len(marker):]

    # Strip the guidance template to find actual user content
    # Look for content after the "Write your notes below this line" marker
    user_marker = "<!-- Write your notes below this line -->"
    user_idx = existing_notes_section.find(user_marker)
    if user_idx == -1:
        # No marker found — the user may have removed it; keep what's there
        user_content = existing_notes_section.strip()
        # Check if it's just the default guidance
        if user_content == _ADDITIONAL_NOTES_GUIDANCE.strip():
            return new_content
    else:
        user_content = existing_notes_section[user_idx + len(user_marker):].strip()

    if not user_content:
        return new_content

    # Replace the Additional Notes section in the new content with preserved content
    new_idx = new_content.find(marker)
    if new_idx == -1:
        return new_content

    before_notes = new_content[:new_idx]
    preserved_section = (
        f"{marker}\n\n"
        f"{_ADDITIONAL_NOTES_GUIDANCE}\n"
        f"{user_content}\n"
    )
    return before_notes + preserved_section


def generate_preferences_html(markdown_content: str) -> str:
    """Convert preferences markdown to styled HTML using built-in conversion."""
    # Simple markdown-to-HTML conversion without external dependencies
    body_lines: list[str] = []
    in_list = False

    for line in markdown_content.split("\n"):
        stripped = line.strip()

        # Headings
        if stripped.startswith("# ") and not stripped.startswith("## "):
            if in_list:
                body_lines.append("</ul>")
                in_list = False
            body_lines.append(f"<h1>{html.escape(stripped[2:])}</h1>")
        elif stripped.startswith("## "):
            if in_list:
                body_lines.append("</ul>")
                in_list = False
            body_lines.append(f"<h2>{html.escape(stripped[3:])}</h2>")

        # List items
        elif stripped.startswith("- "):
            if not in_list:
                body_lines.append("<ul>")
                in_list = True
            item_text = _inline_format(stripped[2:])
            body_lines.append(f"  <li>{item_text}</li>")

        # Empty line
        elif not stripped:
            if in_list:
                body_lines.append("</ul>")
                in_list = False

        # HTML comment (skip)
        elif stripped.startswith("<!--"):
            continue

        # Italic-only lines (guidance text)
        elif stripped.startswith("_") and stripped.endswith("_"):
            if in_list:
                body_lines.append("</ul>")
                in_list = False
            body_lines.append(f"<p class=\"hint\">{_inline_format(stripped)}</p>")

        # Regular paragraph
        else:
            if in_list:
                body_lines.append("</ul>")
                in_list = False
            body_lines.append(f"<p>{_inline_format(stripped)}</p>")

    if in_list:
        body_lines.append("</ul>")

    body_html = "\n".join(body_lines)
    return _HTML_TEMPLATE.replace("{{BODY}}", body_html)


def _inline_format(text: str) -> str:
    """Apply inline markdown formatting (bold, italic, code)."""
    escaped = html.escape(text)
    # Bold: **text**
    escaped = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', escaped)
    # Italic: _text_
    escaped = re.sub(r'(?<!\w)_(.+?)_(?!\w)', r'<em>\1</em>', escaped)
    # Inline code: `text`
    escaped = re.sub(r'`(.+?)`', r'<code>\1</code>', escaped)
    return escaped


_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>My LegalOS Preferences</title>
<style>
  :root {
    --bg: #fafafa;
    --fg: #1a1a2e;
    --accent: #2563eb;
    --muted: #6b7280;
    --border: #e5e7eb;
    --card-bg: #ffffff;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: var(--bg);
    color: var(--fg);
    line-height: 1.6;
    max-width: 800px;
    margin: 0 auto;
    padding: 2rem 1.5rem;
  }
  h1 {
    font-size: 1.75rem;
    margin-bottom: 1.5rem;
    color: var(--accent);
    border-bottom: 2px solid var(--accent);
    padding-bottom: 0.5rem;
  }
  h2 {
    font-size: 1.2rem;
    margin: 1.5rem 0 0.75rem;
    color: var(--fg);
  }
  p { margin: 0.5rem 0; }
  ul { margin: 0.5rem 0 0.5rem 1.5rem; }
  li { margin: 0.25rem 0; }
  code {
    background: #f3f4f6;
    padding: 0.125rem 0.375rem;
    border-radius: 3px;
    font-size: 0.9em;
  }
  .hint {
    color: var(--muted);
    font-style: italic;
  }
  strong { color: var(--fg); }
</style>
</head>
<body>
{{BODY}}
<hr style="margin-top:2rem;border:none;border-top:1px solid var(--border);">
<p class="hint">Generated by LegalOS. Re-run <code>legalos preferences</code> to update.</p>
</body>
</html>"""


def write_preferences(output_dir: Path | None = None) -> tuple[Path, Path]:
    """Load all data, generate markdown + HTML, and write to MyPreferences/.

    Returns (markdown_path, html_path).
    """
    profile = load_profile()
    feedback = load_feedback()
    learnings = load_learnings()

    md_content = generate_preferences_markdown(
        profile=profile,
        feedback=feedback,
        learnings=learnings,
    )

    prefs_dir = output_dir or Path("MyPreferences")
    prefs_dir.mkdir(parents=True, exist_ok=True)

    md_path = prefs_dir / "my_preferences.md"

    # Preserve user's Additional Notes from existing file
    md_content = _preserve_additional_notes(md_path, md_content)

    md_path.write_text(md_content, encoding="utf-8")

    html_content = generate_preferences_html(md_content)
    html_path = prefs_dir / "my_preferences.html"
    html_path.write_text(html_content, encoding="utf-8")

    return md_path, html_path


def load_preferences_for_analysis(base_dir: Path | None = None) -> str | None:
    """Read MyPreferences/my_preferences.md if it exists, for injection into analysis.

    Returns the file content as a string, or None if the file doesn't exist.
    """
    search_dirs = []
    if base_dir:
        search_dirs.append(base_dir)
    search_dirs.append(Path("MyPreferences"))
    search_dirs.append(Path.cwd() / "MyPreferences")

    for d in search_dirs:
        md_path = d / "my_preferences.md" if d.name != "my_preferences.md" else d
        if md_path.exists():
            content = md_path.read_text(encoding="utf-8")
            return content if content.strip() else None

    return None
