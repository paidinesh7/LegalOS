"""Auto-populate profile from analysis results."""

from __future__ import annotations

import re
from typing import Optional

from rich.console import Console
from rich.prompt import Confirm

from legalos.analysis.schemas import FullAnalysis
from legalos.profile.schemas import FounderProfile, FundingStage
from legalos.profile.store import load_profile, save_profile

console = Console()

# Patterns to extract deal info from finding text
_AMOUNT_PATTERN = re.compile(
    r"""
    (?:                         # Currency prefix
        (?:INR|Rs\.?|USD|\$|US\$)\s*
    )?
    (\d[\d,]*\.?\d*)            # Number
    \s*
    (?:                         # Suffix
        (?:Cr|Crore|Crores|Lac|Lacs|Lakhs?|Mn|Million|Bn|Billion|M|K)
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)

_ROUND_KEYWORDS = [
    # Longer/more-specific matches first to avoid "seed" matching "pre-seed"
    ("pre-seed", FundingStage.PRE_SEED),
    ("pre seed", FundingStage.PRE_SEED),
    ("series e", FundingStage.SERIES_D_PLUS),
    ("series d", FundingStage.SERIES_D_PLUS),
    ("series c", FundingStage.SERIES_C),
    ("series b", FundingStage.SERIES_B),
    ("series a", FundingStage.SERIES_A),
    ("seed", FundingStage.SEED),
]

_DOC_TYPE_KEYWORDS = [
    # Longer phrases first to match most-specific; use word-boundary regex
    (re.compile(r"\bshareholder\s+agreement\b", re.IGNORECASE), "sha"),
    (re.compile(r"\bshare\s+subscription\s+agreement\b", re.IGNORECASE), "ssa"),
    (re.compile(r"\bshare\s+purchase\s+agreement\b", re.IGNORECASE), "spa"),
    (re.compile(r"\bterm\s+sheet\b", re.IGNORECASE), "term_sheet"),
    # Abbreviations only as standalone words (avoids "shall" matching "sha")
    (re.compile(r"\bSHA\b"), "sha"),
    (re.compile(r"\bSSA\b"), "ssa"),
    (re.compile(r"\bSPA\b"), "spa"),
]


def _detect_round(text: str) -> Optional[FundingStage]:
    """Try to detect funding round from analysis text."""
    lower = text.lower()
    for keyword, stage in _ROUND_KEYWORDS:
        if keyword in lower:
            return stage
    return None


def _detect_document_type(text: str) -> str:
    """Try to detect document type from analysis text."""
    for pattern, dtype in _DOC_TYPE_KEYWORDS:
        if pattern.search(text):
            return dtype
    return ""


def _extract_amounts(text: str) -> list[str]:
    """Extract monetary amounts from text."""
    results: list[str] = []
    for match in _AMOUNT_PATTERN.finditer(text):
        results.append(match.group(0).strip())
    return results[:5]  # Cap at 5


def extract_suggestions(analysis: FullAnalysis) -> dict:
    """Extract profile suggestions from analysis results.

    Returns a dict with detected fields:
      - document_type, stage, amounts, investor_mentions
    """
    suggestions: dict = {}

    # Combine all text sources for detection
    all_text_parts: list[str] = [
        analysis.document_name,
        analysis.document_type,
    ]
    for section in analysis.sections:
        all_text_parts.append(section.summary)
        for f in section.findings:
            all_text_parts.append(f.explanation)
            all_text_parts.append(f.founder_impact)

    combined = " ".join(all_text_parts)

    # Detect document type
    doc_type = _detect_document_type(combined)
    if doc_type:
        suggestions["document_type"] = doc_type

    # Detect round
    stage = _detect_round(combined)
    if stage:
        suggestions["stage"] = stage

    # Detect amounts (potential deal size / valuation)
    amounts = _extract_amounts(combined)
    if amounts:
        suggestions["amounts"] = amounts

    return suggestions


def offer_auto_populate(
    analysis: FullAnalysis,
) -> Optional[FounderProfile]:
    """After analysis, offer to create/update profile from detected info.

    Returns the updated profile if the user accepts, None otherwise.
    """
    existing = load_profile()
    suggestions = extract_suggestions(analysis)

    if not suggestions:
        return None

    # Build a description of what we found
    parts: list[str] = []
    if "stage" in suggestions:
        stage_label = suggestions["stage"].value.replace("_", " ").title()
        parts.append(f"Stage: {stage_label}")
    if "document_type" in suggestions:
        parts.append(f"Document type: {suggestions['document_type']}")
    if "amounts" in suggestions:
        parts.append(f"Amounts found: {', '.join(suggestions['amounts'])}")

    if not parts:
        return None

    console.print()
    console.print(f"[bold cyan]Detected from document:[/] {'; '.join(parts)}")

    if existing is None:
        proceed = Confirm.ask(
            "No profile found. Create one from these details?",
            default=True,
        )
        if not proceed:
            return None
        profile = FounderProfile()
    else:
        proceed = Confirm.ask(
            "Update your profile with these details?",
            default=False,
        )
        if not proceed:
            return existing
        profile = existing.model_copy(deep=True)

    # Apply suggestions
    if "stage" in suggestions and not profile.company.stage:
        profile.company.stage = suggestions["stage"]
        current_round = suggestions["stage"].value.replace("_", " ").title()
        if not profile.company.current_round:
            profile.company.current_round = current_round

    path = save_profile(profile)
    console.print(f"[bold green]\u2713[/] Profile updated at {path}")
    return profile
