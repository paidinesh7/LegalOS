"""Interactive Rich-based init wizard for founder profile setup."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from legalos.profile.schemas import (
    CompanyContext,
    DealContext,
    FounderProfile,
    FundingStage,
    LegalPriorities,
    RiskTolerance,
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

_PRIORITY_SUGGESTIONS = [
    "Board control & composition",
    "Liquidation preference terms",
    "Anti-dilution protection",
    "Founder vesting & lock-in",
    "Non-compete scope",
    "Drag-along rights",
    "ESOP pool dilution",
    "Reserved matters / veto rights",
    "Exit & IPO terms",
    "Indemnification caps",
]

_RISK_OPTIONS = [
    ("1", "Conservative — flag everything", RiskTolerance.CONSERVATIVE),
    ("2", "Balanced — flag aggressive & unusual (recommended)", RiskTolerance.BALANCED),
    ("3", "Aggressive — only flag truly unusual terms", RiskTolerance.AGGRESSIVE),
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

    # Step 1: Company Context
    console.print("\n[bold cyan]Step 1/5: Company Context[/]")
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

    current_round = Prompt.ask("  Current round name (e.g. 'Series A')", default="")
    prev_input = Prompt.ask("  Previous rounds (comma-separated)", default="")
    previous_rounds = [r.strip() for r in prev_input.split(",") if r.strip()] if prev_input else []

    company = CompanyContext(
        name=name,
        stage=stage,
        sector=sector,
        current_round=current_round,
        previous_rounds=previous_rounds,
    )

    # Step 2: Legal Priorities
    console.print("\n[bold cyan]Step 2/5: Legal Priorities[/]")
    console.print("[dim]What should LegalOS pay extra attention to?[/]\n")

    console.print("  Suggested priority areas:")
    for i, suggestion in enumerate(_PRIORITY_SUGGESTIONS, 1):
        console.print(f"    {i:2}. {suggestion}")
    console.print()

    priority_input = Prompt.ask(
        "  Select numbers (comma-separated) and/or type custom items",
        default="",
    )
    high_priority_areas: list[str] = []
    if priority_input:
        for part in priority_input.split(","):
            part = part.strip()
            if part.isdigit():
                idx = int(part) - 1
                if 0 <= idx < len(_PRIORITY_SUGGESTIONS):
                    high_priority_areas.append(_PRIORITY_SUGGESTIONS[idx])
            elif part:
                high_priority_areas.append(part)

    watchlist_input = Prompt.ask(
        "  Custom watchlist items — specific terms to always flag (comma-separated)",
        default="",
    )
    custom_watchlist = [w.strip() for w in watchlist_input.split(",") if w.strip()] if watchlist_input else []

    known_concerns = Prompt.ask("  Any known concerns about this deal?", default="")

    # Document-type-specific priority overrides
    console.print("\n  [dim]Optional: set extra priorities for specific document types.[/]")
    console.print("  [dim]Types: term_sheet, sha, ssa, spa, convertible_note, safe[/]")
    priority_overrides: dict[str, list[str]] = {}
    override_input = Prompt.ask(
        "  Doc-type overrides (format: type=item1,item2; or Enter to skip)",
        default="",
    )
    if override_input:
        for pair in override_input.split(";"):
            pair = pair.strip()
            if "=" in pair:
                dtype, items_str = pair.split("=", 1)
                items = [i.strip() for i in items_str.split(",") if i.strip()]
                if dtype.strip() and items:
                    priority_overrides[dtype.strip()] = items

    priorities = LegalPriorities(
        high_priority_areas=high_priority_areas,
        custom_watchlist=custom_watchlist,
        known_concerns=known_concerns,
    )

    # Step 3: Risk Tolerance
    console.print("\n[bold cyan]Step 3/5: Risk Tolerance[/]")
    console.print("[dim]How aggressively should LegalOS flag issues?[/]\n")

    for num, label, _ in _RISK_OPTIONS:
        console.print(f"    {num}. {label}")
    risk_choice = Prompt.ask("  Select (1-3)", default="2")
    risk_tolerance = RiskTolerance.BALANCED
    for num, _, val in _RISK_OPTIONS:
        if risk_choice == num:
            risk_tolerance = val
            break

    # Step 4: Deal Context
    console.print("\n[bold cyan]Step 4/5: Deal Context[/]")
    console.print("[dim]Details about the current deal (all optional).[/]\n")

    investors_input = Prompt.ask("  Investor names (comma-separated)", default="")
    investor_names = [n.strip() for n in investors_input.split(",") if n.strip()] if investors_input else []

    lead_investor = Prompt.ask("  Lead investor", default="")
    deal_size = Prompt.ask("  Deal size (e.g. '$2M', 'INR 15Cr')", default="")
    pre_money = Prompt.ask("  Pre-money valuation", default="")

    deal_context = DealContext(
        investor_names=investor_names,
        lead_investor=lead_investor,
        deal_size=deal_size,
        pre_money_valuation=pre_money,
    )

    # Step 5: Legal Team Brief
    console.print("\n[bold cyan]Step 5/5: Legal Team Brief[/]")
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
        priorities=priorities,
        risk_tolerance=risk_tolerance,
        deal_context=deal_context,
        priority_overrides=priority_overrides,
        legal_team_brief=legal_team_brief,
    )

    path = save_profile(profile, directory)
    console.print()
    console.print(f"[bold green]\u2713[/] Profile saved to {path}")

    return profile
