"""Interactive Rich-based init wizard for founder profile setup."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from legalos.profile.schemas import (
    CompanyContext,
    FounderProfile,
    FundingStage,
)
from legalos.profile.store import load_profile, save_profile

console = Console()

_STAGE_OPTIONS = [
    ("1", "Pre-Seed", FundingStage.PRE_SEED),
    ("2", "Seed", FundingStage.SEED),
    ("3", "Series A", FundingStage.SERIES_A),
    ("4", "Series B", FundingStage.SERIES_B),
    ("5", "Series C", FundingStage.SERIES_C),
    ("6", "Series D+", FundingStage.SERIES_D_PLUS),
]


def _read_brief_file(path: Path) -> str:
    """Read a legal brief file and return its text content."""
    suffix = path.suffix.lower()
    if suffix in (".txt", ".md"):
        return path.read_text(encoding="utf-8")
    if suffix in (".pdf", ".docx"):
        from legalos.parsing.router import parse_file_to_text

        return parse_file_to_text(path)
    console.print(f"[yellow]Unsupported brief format '{suffix}'. Use .txt, .md, .pdf, or .docx.[/]")
    return ""


def run_init_flow(directory: Path | None = None, legal_brief_file: Path | None = None) -> FounderProfile:
    """Run the interactive init wizard and save the profile."""
    console.print()
    console.print(Panel(
        "[bold]LegalOS Profile Setup[/bold]\n"
        "This helps LegalOS tailor analysis to your specific situation.\n"
        "All fields are optional — press Enter to skip any question.",
        style="blue",
        expand=False,
    ))
    console.print()

    # Check for existing profile
    existing = load_profile(directory)
    if existing is not None:
        overwrite = Confirm.ask(
            "[yellow]A profile already exists. Overwrite?[/]",
            default=False,
        )
        if not overwrite:
            console.print("[dim]Keeping existing profile.[/]")
            return existing

    # Step 1: Company Background
    console.print("\n[bold cyan]Step 1/2: Company Background[/]")
    console.print("[dim]Tell us about your company.[/]\n")

    name = Prompt.ask("  Company name", default="")
    sector = Prompt.ask("  Sector / industry", default="")

    console.print("  Funding stage:")
    for num, label, _ in _STAGE_OPTIONS:
        console.print(f"    {num}. {label}")
    stage_choice = Prompt.ask("  Select stage (1-6)", default="")
    stage = None
    for num, _, val in _STAGE_OPTIONS:
        if stage_choice == num:
            stage = val
            break

    company = CompanyContext(
        name=name,
        stage=stage,
        sector=sector,
    )

    # Step 2: Legal Team Brief
    console.print("\n[bold cyan]Step 2/2: Legal Team Brief[/]")
    console.print("[dim]Paste guidance from your legal team, or load from a file.[/]\n")

    legal_team_brief = ""

    if legal_brief_file is not None:
        # Pre-loaded via --legal-brief flag
        legal_team_brief = _read_brief_file(legal_brief_file)
        if legal_team_brief:
            preview = legal_team_brief[:150]
            if len(legal_team_brief) > 150:
                preview += "..."
            console.print(f"  [dim]Loaded from {legal_brief_file}:[/]")
            console.print(f"  [dim]{preview}[/]")
    else:
        brief_choice = Prompt.ask(
            "  How to provide legal brief?",
            choices=["type", "file", "skip"],
            default="skip",
        )
        if brief_choice == "type":
            console.print("  [dim]Type your brief (enter an empty line to finish):[/]")
            lines: list[str] = []
            while True:
                line = Prompt.ask("  ", default="")
                if not line:
                    break
                lines.append(line)
            legal_team_brief = "\n".join(lines)
        elif brief_choice == "file":
            file_path_str = Prompt.ask("  Path to brief file (.txt/.md/.pdf/.docx)", default="")
            if file_path_str:
                brief_path = Path(file_path_str).expanduser()
                if brief_path.is_file():
                    legal_team_brief = _read_brief_file(brief_path)
                    if legal_team_brief:
                        preview = legal_team_brief[:150]
                        if len(legal_team_brief) > 150:
                            preview += "..."
                        console.print(f"  [dim]Loaded: {preview}[/]")
                else:
                    console.print(f"  [yellow]File not found: {brief_path}[/]")

    # Build and save
    profile = FounderProfile(
        company=company,
        legal_team_brief=legal_team_brief,
    )

    path = save_profile(profile, directory)
    console.print()
    console.print(f"[bold green]✓[/] Profile saved to {path}")

    # Auto-regenerate MyPreferences (non-fatal)
    try:
        from legalos.profile.preferences_export import write_preferences

        md_path, html_path = write_preferences()
        console.print(f"[dim]MyPreferences updated: {md_path}[/]")
    except Exception:
        pass

    return profile
