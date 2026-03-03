"""Generate personalized Claude Project files for using LegalOS on claude.ai."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

from legalos.profile.prompt_injection import build_full_system_prompt
from legalos.profile.schemas import FeedbackStore, FounderProfile, LearningsStore
from legalos.profile.store import load_feedback, load_learnings, load_profile


def _find_claude_project_dir() -> Path:
    """Locate the claude-project/ static files directory.

    Walks up from this file to find the repo root (has pyproject.toml),
    then returns claude-project/ under it.  Falls back to importlib.resources
    for installed packages.
    """
    # Walk up from this file's location
    current = Path(__file__).resolve().parent
    for _ in range(10):
        candidate = current / "claude-project"
        if candidate.is_dir() and (candidate / "instructions.md").exists():
            return candidate
        # Check if pyproject.toml is here (repo root)
        if (current / "pyproject.toml").exists():
            cp = current / "claude-project"
            if cp.is_dir():
                return cp
        current = current.parent

    # Fallback: importlib.resources for installed package
    try:
        import importlib.resources as pkg_resources

        ref = pkg_resources.files("legalos") / "claude_project"
        # Traverse into the package data
        pkg_path = Path(str(ref))
        if pkg_path.is_dir() and (pkg_path / "instructions.md").exists():
            return pkg_path
    except Exception:
        pass

    raise FileNotFoundError(
        "Could not find claude-project/ directory. "
        "Ensure you're running from the LegalOS repo or that the package "
        "was installed with static files included."
    )


def generate_personalized_instructions(
    profile: Optional[FounderProfile] = None,
    feedback: Optional[FeedbackStore] = None,
    learnings: Optional[LearningsStore] = None,
    preferences_doc: Optional[str] = None,
) -> str:
    """Generate personalized Claude Project instructions.

    Reads the static instructions.md template and replaces the generic
    system prompt section with a personalized version that includes
    founder context, feedback patterns, and learnings.

    Returns the complete instructions markdown.
    """
    static_dir = _find_claude_project_dir()
    template = (static_dir / "instructions.md").read_text(encoding="utf-8")

    if profile is None and feedback is None and learnings is None and preferences_doc is None:
        return template

    # Build the personalized system prompt using the same machinery as CLI
    from legalos.analysis.prompts.system import SYSTEM_PROMPT

    personalized_prompt = build_full_system_prompt(
        base=SYSTEM_PROMPT,
        profile=profile,
        feedback=feedback,
        learnings=learnings,
        preferences_doc=preferences_doc,
    )

    # Replace the generic system prompt block in the template with
    # the personalized version.  The generic prompt starts after the
    # "---" separator and runs until "## Analysis Workflow".
    separator = "---\n\n"
    workflow_header = "## Analysis Workflow"

    sep_idx = template.find(separator)
    workflow_idx = template.find(workflow_header)

    if sep_idx == -1 or workflow_idx == -1:
        # Template structure unexpected — append personalization at end
        return template + "\n\n" + personalized_prompt

    # The persona block is between the first separator and the workflow header
    before = template[: sep_idx + len(separator)]
    after = template[workflow_idx:]

    return before + personalized_prompt + "\n\n" + after


def export_claude_project(output_dir: Path | None = None) -> list[Path]:
    """Generate Claude Project files, personalized if a profile exists.

    Copies the 3 knowledge files (analysis_checklist, doc_type_guidance,
    scoring_rubric) and writes personalized instructions.

    Args:
        output_dir: Where to write files. Defaults to MyPreferences/claude-project/.

    Returns:
        List of generated file paths.
    """
    profile = load_profile()
    feedback = load_feedback()
    learnings = load_learnings()

    # Load preferences doc if it exists
    preferences_doc: str | None = None
    try:
        from legalos.profile.preferences_export import load_preferences_for_analysis

        preferences_doc = load_preferences_for_analysis()
    except Exception:
        pass

    # Generate personalized instructions
    instructions = generate_personalized_instructions(
        profile=profile,
        feedback=feedback if feedback and feedback.items else None,
        learnings=learnings if learnings and learnings.entries else None,
        preferences_doc=preferences_doc,
    )

    # Determine output directory
    dest = output_dir or Path("MyPreferences") / "claude-project"
    dest.mkdir(parents=True, exist_ok=True)

    generated: list[Path] = []

    # Write personalized instructions
    instructions_path = dest / "instructions.md"
    instructions_path.write_text(instructions, encoding="utf-8")
    generated.append(instructions_path)

    # Copy the 3 knowledge files from the static directory
    static_dir = _find_claude_project_dir()
    knowledge_files = [
        "analysis_checklist.md",
        "doc_type_guidance.md",
        "scoring_rubric.md",
    ]

    for filename in knowledge_files:
        src = static_dir / filename
        dst = dest / filename
        shutil.copy2(src, dst)
        generated.append(dst)

    return generated
