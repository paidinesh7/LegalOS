"""DOCX comment annotation with text-to-run mapping and fuzzy matching."""

from __future__ import annotations

import difflib
from pathlib import Path

from docx import Document
from docx.shared import Pt as docx_pt, RGBColor

from legalos.analysis.schemas import RedlineComment, RedlineOutput
from legalos.utils.errors import RedlineError


def _find_text_in_paragraphs(
    doc: Document,
    target_text: str,
    threshold: float = 0.85,
) -> tuple[int, int, int] | None:
    """Find target text in document paragraphs.

    Returns (paragraph_index, start_char, end_char) or None.
    Uses exact match first, then fuzzy fallback.
    """
    target_clean = target_text.strip()

    # Exact substring match
    for i, para in enumerate(doc.paragraphs):
        para_text = para.text
        idx = para_text.find(target_clean)
        if idx >= 0:
            return (i, idx, idx + len(target_clean))

    # Fuzzy match fallback
    best_ratio = 0.0
    best_match = None
    for i, para in enumerate(doc.paragraphs):
        para_text = para.text
        if not para_text.strip():
            continue
        # Try matching against sliding windows of similar length
        target_len = len(target_clean)
        for start in range(0, max(1, len(para_text) - target_len // 2)):
            end = min(start + target_len + target_len // 4, len(para_text))
            window = para_text[start:end]
            ratio = difflib.SequenceMatcher(None, target_clean, window).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = (i, start, end)

    if best_ratio >= threshold and best_match is not None:
        return best_match
    return None


def _add_comment_to_paragraph(
    doc: Document,
    para_index: int,
    comment_text: str,
    author: str,
) -> None:
    """Add a comment as a simple annotation on a paragraph.

    Uses a pragmatic approach: appends the comment text as a footnote-style
    annotation since python-docx comment API varies by version.
    """
    para = doc.paragraphs[para_index]
    # Add a visible annotation marker at end of paragraph
    run = para.add_run(f"  [{author}: {comment_text[:100]}…]" if len(comment_text) > 100 else f"  [{author}: {comment_text}]")
    run.font.size = docx_pt(8)
    run.font.color.rgb = RGBColor(0x99, 0x33, 0x33)
    run.font.italic = True


def _format_comment(comment: RedlineComment) -> str:
    """Format a redline comment for display."""
    parts = [
        f"[{comment.severity.value.upper()}]",
        f"Issue: {comment.issue}",
        f"Suggestion: {comment.suggestion}",
    ]
    if comment.alternative_language:
        parts.append(f"Alternative language: {comment.alternative_language}")
    parts.append(f"Reasoning: {comment.reasoning}")
    return " | ".join(parts)


def generate_redline(
    source_path: Path,
    redline_output: RedlineOutput,
    output_path: Path | None = None,
    author: str = "LegalOS",
) -> Path:
    """Generate an annotated DOCX with redline comments."""
    if source_path.suffix.lower() != ".docx":
        raise RedlineError(
            f"Redline requires a DOCX file, got '{source_path.suffix}'. "
            "Convert PDF to DOCX first."
        )

    try:
        doc = Document(str(source_path))
    except Exception as e:
        raise RedlineError(f"Cannot open DOCX: {e}") from e

    matched_count = 0
    unmatched_comments: list[str] = []

    for comment in redline_output.comments:
        location = _find_text_in_paragraphs(doc, comment.target_text)
        comment_text = _format_comment(comment)

        if location is not None:
            para_idx, _, _ = location
            _add_comment_to_paragraph(doc, para_idx, comment_text, author)
            matched_count += 1
        else:
            unmatched_comments.append(comment_text)

    # Add unmatched comments as a summary at the start
    if unmatched_comments:
        # Insert summary paragraph at beginning
        summary_para = doc.paragraphs[0].insert_paragraph_before(
            f"[{author} — UNMATCHED COMMENTS]\n" + "\n\n".join(unmatched_comments)
        )

    if output_path is None:
        output_path = source_path.parent / f"{source_path.stem}_redlined.docx"

    doc.save(str(output_path))
    return output_path
