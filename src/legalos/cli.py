"""Click CLI — analyze, redline, init, profile, deal, and feedback commands."""

from __future__ import annotations

from pathlib import Path

import click

from legalos.config import resolve_model
from legalos.utils.progress import (
    console,
    print_cost,
    print_error,
    print_header,
    print_success,
    print_warning,
)


@click.group()
@click.version_option(package_name="legalos")
def cli() -> None:
    """LegalOS — AI-powered legal document analyzer for Indian startup founders."""
    pass


# ── Init ────────────────────────────────────────────────────────


@cli.command()
@click.option("--legal-brief", "legal_brief", type=click.Path(exists=True, path_type=Path), default=None, help="Path to a legal team brief file (.txt/.md/.pdf/.docx).")
def init(legal_brief: Path | None) -> None:
    """Set up your founder profile for personalized analysis."""
    from legalos.profile.init_flow import run_init_flow

    run_init_flow(legal_brief_file=legal_brief)


# ── Profile management ──────────────────────────────────────────


@cli.group(invoke_without_command=True)
@click.pass_context
def profile(ctx: click.Context) -> None:
    """View and manage your founder profile."""
    if ctx.invoked_subcommand is not None:
        return
    # Default: show current profile
    from legalos.profile.store import load_profile

    p = load_profile()
    if p is None:
        console.print("[dim]No profile found. Run 'legalos init' to create one.[/]")
        return

    console.print("[bold]Founder Profile[/]\n")
    c = p.company
    if c.name:
        console.print(f"  Company:        {c.name}")
    if c.stage:
        console.print(f"  Stage:          {c.stage.value.replace('_', ' ').title()}")
    if c.sector:
        console.print(f"  Sector:         {c.sector}")
    if c.current_round:
        console.print(f"  Current round:  {c.current_round}")
    if c.previous_rounds:
        console.print(f"  Previous:       {', '.join(c.previous_rounds)}")

    console.print(f"  Risk tolerance: {p.risk_tolerance.value}")

    pri = p.priorities
    if pri.high_priority_areas:
        console.print(f"  Priorities:     {', '.join(pri.high_priority_areas)}")
    if pri.custom_watchlist:
        console.print(f"  Watchlist:      {', '.join(pri.custom_watchlist)}")
    if pri.known_concerns:
        console.print(f"  Concerns:       {pri.known_concerns}")

    if p.priority_overrides:
        console.print("  Doc-type overrides:")
        for dtype, items in p.priority_overrides.items():
            console.print(f"    {dtype}: {', '.join(items)}")

    if p.legal_team_brief:
        preview = p.legal_team_brief[:150]
        if len(p.legal_team_brief) > 150:
            preview += "..."
        console.print(f"  Legal brief:    {preview}")

    d = p.deal_context
    if d.investor_names or d.deal_size or d.pre_money_valuation:
        console.print("\n  [bold]Deal Context[/]")
        if d.investor_names:
            console.print(f"  Investors:      {', '.join(d.investor_names)}")
        if d.lead_investor:
            console.print(f"  Lead:           {d.lead_investor}")
        if d.deal_size:
            console.print(f"  Deal size:      {d.deal_size}")
        if d.pre_money_valuation:
            console.print(f"  Pre-money:      {d.pre_money_valuation}")


@profile.command("set")
@click.argument("key")
@click.argument("value")
def profile_set(key: str, value: str) -> None:
    """Set a profile field.

    Scalar examples: risk_tolerance conservative, company.name Acme
    List examples: priorities.high_priority_areas "Board control, Anti-dilution"
                   deal.investor_names "Sequoia, Accel"
                   company.previous_rounds "Seed, Pre-Series A"
    """
    from legalos.profile.schemas import FounderProfile, RiskTolerance
    from legalos.profile.store import load_profile, save_profile

    p = load_profile()
    if p is None:
        p = FounderProfile()

    def _parse_list(val: str) -> list[str]:
        return [v.strip() for v in val.split(",") if v.strip()]

    # Parse dotted keys
    parts = key.split(".")
    try:
        if len(parts) == 1:
            if key == "risk_tolerance":
                p.risk_tolerance = RiskTolerance(value)
            elif key == "legal_team_brief":
                p.legal_team_brief = value
            else:
                raise click.BadParameter(f"Unknown top-level key: {key}")
        elif len(parts) == 2:
            section, field = parts
            if section == "company":
                if field == "name":
                    p.company.name = value
                elif field == "sector":
                    p.company.sector = value
                elif field == "current_round":
                    p.company.current_round = value
                elif field == "stage":
                    from legalos.profile.schemas import FundingStage
                    p.company.stage = FundingStage(value)
                elif field == "previous_rounds":
                    p.company.previous_rounds = _parse_list(value)
                else:
                    raise click.BadParameter(f"Unknown company field: {field}")
            elif section == "deal":
                if field == "deal_size":
                    p.deal_context.deal_size = value
                elif field == "pre_money_valuation":
                    p.deal_context.pre_money_valuation = value
                elif field == "lead_investor":
                    p.deal_context.lead_investor = value
                elif field == "investor_names":
                    p.deal_context.investor_names = _parse_list(value)
                else:
                    raise click.BadParameter(f"Unknown deal field: {field}")
            elif section == "priorities":
                if field == "known_concerns":
                    p.priorities.known_concerns = value
                elif field == "high_priority_areas":
                    p.priorities.high_priority_areas = _parse_list(value)
                elif field == "custom_watchlist":
                    p.priorities.custom_watchlist = _parse_list(value)
                else:
                    raise click.BadParameter(f"Unknown priorities field: {field}")
            else:
                raise click.BadParameter(f"Unknown section: {section}")
        else:
            raise click.BadParameter(f"Key too deeply nested: {key}")
    except ValueError as e:
        print_error(f"Invalid value: {e}")
        raise SystemExit(1)

    path = save_profile(p)
    print_success(f"Set {key} = {value} (saved to {path})")


@profile.command("clear")
def profile_clear() -> None:
    """Delete your founder profile."""
    from legalos.profile.store import delete_profile

    if delete_profile():
        print_success("Profile deleted.")
    else:
        console.print("[dim]No profile to delete.[/]")


@profile.command("export")
@click.argument("file", type=click.Path(path_type=Path))
def profile_export(file: Path) -> None:
    """Export profile to a JSON file for team sharing."""
    from legalos.profile.store import export_profile

    try:
        export_profile(file)
        print_success(f"Profile exported to {file}")
    except FileNotFoundError:
        print_error("No profile found to export. Run 'legalos init' first.")
        raise SystemExit(1)


@profile.command("import")
@click.argument("file", type=click.Path(exists=True, path_type=Path))
def profile_import(file: Path) -> None:
    """Import profile from a JSON file."""
    from legalos.profile.store import import_profile

    try:
        p = import_profile(file)
        name = p.company.name or "imported profile"
        print_success(f"Imported profile: {name}")
    except Exception as e:
        print_error(f"Import failed: {e}")
        raise SystemExit(1)


# ── Deal management ─────────────────────────────────────────────


@cli.group(invoke_without_command=True)
@click.pass_context
def deal(ctx: click.Context) -> None:
    """Manage deal-specific contexts."""
    if ctx.invoked_subcommand is not None:
        return
    # Default: list deals
    from legalos.profile.store import list_deals

    deals = list_deals()
    if not deals:
        console.print("[dim]No deals configured. Use 'legalos deal add <name>' to create one.[/]")
        return
    console.print("[bold]Configured deals:[/]")
    for name in deals:
        console.print(f"  - {name}")


@deal.command("add")
@click.argument("name")
def deal_add(name: str) -> None:
    """Add a new deal context interactively."""
    from rich.prompt import Prompt

    from legalos.profile.schemas import DealContext, DealProfile
    from legalos.profile.store import save_deal

    console.print(f"\n[bold cyan]Setting up deal: {name}[/]\n")

    investors_input = Prompt.ask("  Investor names (comma-separated)", default="")
    investor_names = [n.strip() for n in investors_input.split(",") if n.strip()] if investors_input else []
    lead = Prompt.ask("  Lead investor", default="")
    size = Prompt.ask("  Deal size (e.g. '$2M', 'INR 15Cr')", default="")
    valuation = Prompt.ask("  Pre-money valuation", default="")
    watchlist_input = Prompt.ask("  Extra watchlist items for this deal (comma-separated)", default="")
    extra_watchlist = [w.strip() for w in watchlist_input.split(",") if w.strip()] if watchlist_input else []

    deal_profile = DealProfile(
        name=name,
        deal_context=DealContext(
            investor_names=investor_names,
            lead_investor=lead,
            deal_size=size,
            pre_money_valuation=valuation,
        ),
        extra_watchlist=extra_watchlist,
    )

    path = save_deal(deal_profile)
    print_success(f"Deal '{name}' saved to {path}")


@deal.command("remove")
@click.argument("name")
def deal_remove(name: str) -> None:
    """Remove a deal context."""
    from legalos.profile.store import delete_deal

    if delete_deal(name):
        print_success(f"Deal '{name}' removed.")
    else:
        print_error(f"Deal '{name}' not found.")


@deal.command("show")
@click.argument("name")
def deal_show(name: str) -> None:
    """Show details of a deal context."""
    from legalos.profile.store import load_deal

    d = load_deal(name)
    if d is None:
        print_error(f"Deal '{name}' not found.")
        raise SystemExit(1)

    console.print(f"\n[bold]Deal: {d.name}[/]")
    dc = d.deal_context
    if dc.investor_names:
        console.print(f"  Investors:   {', '.join(dc.investor_names)}")
    if dc.lead_investor:
        console.print(f"  Lead:        {dc.lead_investor}")
    if dc.deal_size:
        console.print(f"  Deal size:   {dc.deal_size}")
    if dc.pre_money_valuation:
        console.print(f"  Pre-money:   {dc.pre_money_valuation}")
    if d.extra_watchlist:
        console.print(f"  Watchlist:   {', '.join(d.extra_watchlist)}")


# ── Feedback management ─────────────────────────────────────────


@cli.group(name="feedback", invoke_without_command=True)
@click.pass_context
def feedback_group(ctx: click.Context) -> None:
    """View and manage analysis feedback."""
    if ctx.invoked_subcommand is not None:
        return
    # Default: show summary
    from legalos.profile.store import compute_feedback_summary, load_feedback

    store = load_feedback()
    if not store.items:
        console.print("[dim]No feedback collected yet.[/]")
        return

    summary = compute_feedback_summary(store)
    console.print(f"[bold]Feedback Summary[/] ({summary.total_sessions} sessions)\n")

    if summary.avg_rating is not None:
        console.print(f"  Average rating: {summary.avg_rating}/5")

    if summary.frequently_missed:
        console.print("\n  [bold]Frequently missed:[/]")
        for item, count in summary.frequently_missed.items():
            console.print(f"    - {item} ({count}x)")

    if summary.frequently_over_flagged:
        console.print("\n  [bold]Frequently over-flagged:[/]")
        for item, count in summary.frequently_over_flagged.items():
            console.print(f"    - {item} ({count}x)")


@feedback_group.command("import")
@click.argument("file", type=click.Path(exists=True, path_type=Path))
def feedback_import(file: Path) -> None:
    """Import per-finding feedback from an HTML report export."""
    from legalos.profile.store import import_report_feedback

    try:
        item = import_report_feedback(file)
        n_fp = len(item.false_positives)
        print_success(f"Imported feedback: {n_fp} finding(s) marked as not relevant")
    except Exception as e:
        print_error(f"Import failed: {e}")
        raise SystemExit(1)


@feedback_group.command("submit")
@click.option("--up", "up_titles", default="", help="Comma-separated titles of helpful findings.")
@click.option("--down", "down_titles", default="", help="Comma-separated titles of not-relevant findings.")
@click.option("--doc", "doc_name", default="", help="Document name the feedback is for.")
def feedback_submit(up_titles: str, down_titles: str, doc_name: str) -> None:
    """Submit per-finding feedback directly (paste from report)."""
    from legalos.profile.store import submit_feedback_from_titles

    up_list = [t.strip() for t in up_titles.split(",") if t.strip()] if up_titles else []
    down_list = [t.strip() for t in down_titles.split(",") if t.strip()] if down_titles else []

    if not up_list and not down_list:
        print_error("No feedback provided. Use --up and/or --down with finding titles.")
        raise SystemExit(1)

    item = submit_feedback_from_titles(doc_name, up_list, down_list)
    n_fp = len(item.false_positives)
    total = len(up_list) + len(down_list)
    print_success(f"Feedback saved: {total} finding(s) rated ({n_fp} marked not relevant)")


@feedback_group.command("clear")
def feedback_clear() -> None:
    """Delete all collected feedback."""
    from legalos.profile.store import clear_feedback

    if clear_feedback():
        print_success("All feedback cleared.")
    else:
        console.print("[dim]No feedback to clear.[/]")


# ── Knowledge base management ──────────────────────────────────


@cli.group(name="kb", invoke_without_command=True)
@click.pass_context
def kb_group(ctx: click.Context) -> None:
    """View and manage your learnings knowledge base."""
    if ctx.invoked_subcommand is not None:
        return
    # Default: show summary
    from legalos.profile.store import compute_learning_summary, load_learnings

    store = load_learnings()
    if not store.entries:
        console.print("[dim]No learnings yet. They'll be auto-captured during analysis, or use 'legalos kb add'.[/]")
        return

    summary = compute_learning_summary(store)
    console.print(f"[bold]Knowledge Base[/] ({summary.total_entries} entries)\n")

    if summary.by_category:
        console.print("  [bold]By category:[/]")
        for cat, count in summary.by_category.items():
            label = cat.replace("_", " ").title()
            console.print(f"    {label}: {count}")

    if summary.top_tags:
        console.print(f"\n  [bold]Top tags:[/] {', '.join(summary.top_tags)}")

    if summary.most_useful:
        console.print("\n  [bold]Most referenced:[/]")
        for title in summary.most_useful[:5]:
            console.print(f"    - {title}")


@kb_group.command("show")
def kb_show() -> None:
    """List all knowledge base entries."""
    from legalos.profile.store import load_learnings

    store = load_learnings()
    if not store.entries:
        console.print("[dim]No learnings yet.[/]")
        return

    for entry in store.entries:
        cat_label = entry.category.value.replace("_", " ").title()
        tags = ", ".join(entry.tags) if entry.tags else ""
        date_str = entry.created_at[:10] if entry.created_at else ""
        console.print(
            f"  [bold]{entry.id}[/]  [{cat_label}]  {entry.title}"
        )
        console.print(f"         {entry.insight}")
        meta_parts = []
        if tags:
            meta_parts.append(f"tags: {tags}")
        if entry.document_name:
            meta_parts.append(f"from: {entry.document_name}")
        if date_str:
            meta_parts.append(date_str)
        if entry.useful_count:
            meta_parts.append(f"used {entry.useful_count}x")
        if meta_parts:
            console.print(f"         [dim]{' | '.join(meta_parts)}[/]")
        console.print()


@kb_group.command("add")
def kb_add() -> None:
    """Add a learning entry interactively."""
    from legalos.profile.learning_capture import offer_manual_learning

    entry = offer_manual_learning()
    if entry:
        print_success(f"Learning '{entry.title}' saved (ID: {entry.id})")
    else:
        console.print("[dim]No learning added.[/]")


@kb_group.command("search")
@click.argument("query")
@click.option("--category", "-c", default="", help="Filter by category.")
@click.option("--section", "-s", default="", help="Filter by section ID.")
def kb_search(query: str, category: str, section: str) -> None:
    """Search the knowledge base by keyword."""
    from legalos.profile.store import load_learnings, search_learnings

    store = load_learnings()
    results = search_learnings(store, query=query, section_id=section, category=category)

    if not results:
        console.print(f"[dim]No learnings matching '{query}'.[/]")
        return

    console.print(f"[bold]{len(results)} result(s):[/]\n")
    for entry in results:
        cat_label = entry.category.value.replace("_", " ").title()
        console.print(f"  [bold]{entry.id}[/]  [{cat_label}]  {entry.title}")
        console.print(f"         {entry.insight}")
        console.print()


@kb_group.command("update")
@click.argument("entry_id")
def kb_update(entry_id: str) -> None:
    """Edit an existing knowledge base entry interactively."""
    from rich.prompt import Prompt

    from legalos.profile.schemas import LearningCategory
    from legalos.profile.store import load_learnings, update_learning

    store = load_learnings()
    target = None
    for e in store.entries:
        if e.id == entry_id:
            target = e
            break

    if target is None:
        print_error(f"Entry '{entry_id}' not found.")
        raise SystemExit(1)

    console.print(f"[bold]Editing: {target.title}[/]\n")

    title = Prompt.ask("  Title", default=target.title)
    insight = Prompt.ask("  Insight", default=target.insight)
    cat_input = Prompt.ask("  Category", default=target.category.value)
    tags_input = Prompt.ask("  Tags (comma-separated)", default=", ".join(target.tags))
    tags = [t.strip() for t in tags_input.split(",") if t.strip()] if tags_input else []

    try:
        category = LearningCategory(cat_input)
    except ValueError:
        category = target.category

    updates = {
        "title": title,
        "insight": insight,
        "category": category,
        "tags": tags,
    }
    updated = update_learning(entry_id, updates)
    if updated:
        print_success(f"Entry '{entry_id}' updated.")
    else:
        print_error("Update failed.")


@kb_group.command("remove")
@click.argument("entry_id")
def kb_remove(entry_id: str) -> None:
    """Delete a knowledge base entry by ID."""
    from legalos.profile.store import delete_learning

    if delete_learning(entry_id):
        print_success(f"Entry '{entry_id}' removed.")
    else:
        print_error(f"Entry '{entry_id}' not found.")


@kb_group.command("export")
@click.option("--output", "-o", type=click.Path(path_type=Path), default=None, help="Output file path.")
def kb_export(output: Path | None) -> None:
    """Export knowledge base as Markdown."""
    from legalos.profile.store import export_learnings_markdown, load_learnings

    store = load_learnings()
    if not store.entries:
        console.print("[dim]No learnings to export.[/]")
        return

    md = export_learnings_markdown(store)

    if output:
        output.write_text(md, encoding="utf-8")
        print_success(f"Exported to {output}")
    else:
        console.print(md)


@kb_group.command("import")
@click.argument("file", type=click.Path(exists=True, path_type=Path))
def kb_import(file: Path) -> None:
    """Import learnings from another founder's JSON export."""
    from legalos.profile.store import import_learnings

    try:
        count = import_learnings(file)
        print_success(f"Imported {count} new learning(s)")
    except Exception as e:
        print_error(f"Import failed: {e}")
        raise SystemExit(1)


@kb_group.command("clear")
def kb_clear() -> None:
    """Delete all learnings (with confirmation)."""
    from rich.prompt import Confirm

    from legalos.profile.store import clear_learnings

    if not Confirm.ask("Delete all learnings?", default=False):
        console.print("[dim]Cancelled.[/]")
        return

    if clear_learnings():
        print_success("All learnings cleared.")
    else:
        console.print("[dim]No learnings to clear.[/]")


# ── Shared helpers ─────────────────────────────────────────────


def _apply_deal_context(
    deal_name: str | None,
    profile: "FounderProfile | None",
    verbose: bool,
) -> "FounderProfile | None":
    """Load a deal overlay and merge into profile. Shared by analyze and redline."""
    if not deal_name:
        return profile

    from legalos.profile.store import apply_deal_overlay, load_deal

    deal_profile = load_deal(deal_name)
    if deal_profile is None:
        print_error(f"Deal '{deal_name}' not found. Run 'legalos deal add {deal_name}' first.")
        raise SystemExit(1)
    if profile is None:
        from legalos.profile.schemas import FounderProfile
        profile = FounderProfile()
    profile = apply_deal_overlay(profile, deal_profile)
    if verbose:
        console.print(f"[dim]Using deal context: {deal_name}[/]")
    return profile


# ── Analyze ─────────────────────────────────────────────────────


@cli.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--model", "-m",
    type=click.Choice(["opus", "sonnet", "haiku"], case_sensitive=False),
    default="sonnet",
    show_default=True,
    help="Claude model to use.",
)
@click.option("--output", "-o", type=click.Path(path_type=Path), default=None, help="Output HTML path.")
@click.option("--no-qa", is_flag=True, help="Skip the interactive Q&A session.")
@click.option("--no-browser", is_flag=True, help="Don't auto-open the report in browser.")
@click.option("--no-feedback", is_flag=True, help="Skip feedback prompts entirely.")
@click.option("--deal", "deal_name", default=None, help="Use a named deal context.")
@click.option(
    "--type", "document_type",
    type=click.Choice(
        ["term_sheet", "sha", "ssa", "spa", "convertible_note", "safe"],
        case_sensitive=False,
    ),
    default=None,
    help="Document type (auto-detected if omitted).",
)
@click.option("--deep", is_flag=True, help="Full section-by-section analysis (default: quick scan).")
@click.option("--legal-brief", "legal_brief", type=click.Path(exists=True, path_type=Path), default=None, help="Override legal team brief for this session (.txt/.md/.pdf/.docx).")
@click.option("--verbose", "-v", is_flag=True, help="Show token usage details.")
def analyze(
    path: Path,
    model: str,
    output: Path | None,
    no_qa: bool,
    no_browser: bool,
    no_feedback: bool,
    deal_name: str | None,
    document_type: str | None,
    deep: bool,
    legal_brief: Path | None,
    verbose: bool,
) -> None:
    """Analyze legal documents and generate an interactive report.

    PATH can be a single file (PDF/DOCX/image) or a directory of files.
    """
    from legalos.analysis.client import AnalysisClient
    from legalos.analysis.engine import run_analysis
    from legalos.parsing.router import parse_input
    from legalos.profile.auto_populate import offer_auto_populate
    from legalos.profile.feedback_flow import run_feedback_flow
    from legalos.profile.store import load_feedback, load_learnings, load_profile
    from legalos.qa.session import run_qa_session
    from legalos.report.generator import generate_report

    model_id = resolve_model(model)
    print_header(f"LegalOS — Analyzing with {model}")

    # Load profile, feedback, and learnings
    profile = load_profile()
    feedback_store = load_feedback()
    learnings_store = load_learnings()

    # Auto-import any sidecar feedback files from CWD
    from legalos.profile.store import auto_import_sidecar_feedback
    sidecar_count = auto_import_sidecar_feedback()
    if sidecar_count > 0:
        print_success(f"Auto-imported feedback from {sidecar_count} sidecar file(s)")
        feedback_store = load_feedback()  # Reload with new feedback

    # Apply deal overlay if specified
    profile = _apply_deal_context(deal_name, profile, verbose)

    # Apply --legal-brief session overlay if specified
    if legal_brief is not None:
        from legalos.parsing.router import parse_file_to_text

        brief_suffix = legal_brief.suffix.lower()
        if brief_suffix in (".txt", ".md"):
            brief_text = legal_brief.read_text(encoding="utf-8")
        else:
            brief_text = parse_file_to_text(legal_brief)
        if brief_text:
            if profile is None:
                from legalos.profile.schemas import FounderProfile as _FP
                profile = _FP()
            profile = profile.model_copy(deep=True)
            profile.legal_team_brief = brief_text
            if verbose:
                console.print(f"[dim]Legal brief loaded from {legal_brief} ({len(brief_text)} chars)[/]")

    if profile is not None:
        label = profile.company.name or "founder"
        if verbose:
            console.print(f"[dim]Using profile: {label} ({profile.risk_tolerance.value})[/]")
    else:
        console.print("[dim]No profile found. Run 'legalos init' to personalize analysis.[/]")

    if feedback_store.items and verbose:
        console.print(f"[dim]Loaded {len(feedback_store.items)} feedback item(s) from previous sessions.[/]")

    if learnings_store.entries and verbose:
        console.print(f"[dim]Loaded {len(learnings_store.entries)} learning(s) from knowledge base.[/]")

    # Parse
    console.print(f"[dim]Parsing {path}\u2026[/]")
    try:
        documents = parse_input(path)
    except Exception as e:
        print_error(f"Parsing failed: {e}")
        raise SystemExit(1)

    if not documents:
        print_error("No supported files found.")
        raise SystemExit(1)

    total_pages = sum(d.page_count for d in documents)
    total_tokens = sum(d.estimated_tokens() for d in documents)
    print_success(f"Parsed {len(documents)} file(s), {total_pages} page(s), ~{total_tokens:,} tokens")

    if total_tokens < 100:
        print_warning("Very little text extracted. The document might be scanned — try an image file.")

    # Analyze
    client = AnalysisClient(model_id=model_id, verbose=verbose)

    if deep:
        # Full 9-pass analysis (existing behavior)
        try:
            analysis = run_analysis(
                client, documents, profile=profile, feedback=feedback_store,
                document_type=document_type or "", learnings=learnings_store,
            )
        except Exception as e:
            print_error(f"Analysis failed: {e}")
            raise SystemExit(1)

        print_success(f"Analysis complete — {sum(len(s.findings) for s in analysis.sections)} findings across {len(analysis.sections)} sections")

        if verbose:
            print_cost(client.usage.summary(model_id))

        # Auto-populate profile from analysis if no profile exists
        if profile is None:
            profile = offer_auto_populate(analysis)

        # Collect relevant knowledge entries for the report
        from legalos.profile.store import search_learnings as _search_learnings

        knowledge_for_report = []
        if learnings_store.entries:
            for section in analysis.sections:
                matches = _search_learnings(learnings_store, section_id=section.section_id)
                for m in matches:
                    if m not in knowledge_for_report:
                        knowledge_for_report.append(m)

        # Generate report
        try:
            report_path = generate_report(
                analysis, output_path=output, open_browser=not no_browser, profile=profile,
                knowledge_entries=knowledge_for_report or None,
            )
        except Exception as e:
            print_error(f"Report generation failed: {e}")
            raise SystemExit(1)

        print_success(f"Report saved to {report_path}")
        if not no_browser:
            console.print("[dim]Report opened in browser.[/]")

        # Q&A session
        if not no_qa:
            combined_text = "\n\n---\n\n".join(doc.full_text for doc in documents)
            run_qa_session(
                client, combined_text, analysis,
                profile=profile, feedback=feedback_store, no_feedback=no_feedback,
            )
            if verbose:
                print_cost(client.usage.summary(model_id))

        # Feedback collection
        if not no_feedback:
            doc_name = ", ".join(doc.source_path.name for doc in documents)
            run_feedback_flow(
                document_name=doc_name,
                model_used=model_id,
                feedback=feedback_store,
                analysis=analysis,
            )

            from legalos.profile.learning_capture import (
                auto_capture_learnings,
                offer_manual_learning,
            )

            new_entries = auto_capture_learnings(
                analysis, feedback_store, learnings_store,
            )
            if new_entries:
                console.print(
                    f"[bold green]{len(new_entries)} new learning(s) captured.[/]"
                )
            manual = offer_manual_learning()

    else:
        # Quick scan (default) — 1 API call
        from legalos.analysis.engine import run_quick_analysis
        from legalos.analysis.schemas import ExecutiveSummary, FullAnalysis
        from legalos.report.generator import generate_quick_report

        try:
            quick_result = run_quick_analysis(
                client, documents, profile=profile, feedback=feedback_store,
                document_type=document_type or "", learnings=learnings_store,
            )
        except Exception as e:
            print_error(f"Quick scan failed: {e}")
            raise SystemExit(1)

        n_flags = len(quick_result.red_flags)
        print_success(f"Quick scan complete — {n_flags} red flag(s) found")

        if verbose:
            print_cost(client.usage.summary(model_id))

        # Generate quick scan report
        try:
            report_path = generate_quick_report(
                quick_result, output_path=output, open_browser=not no_browser,
                profile=profile,
            )
        except Exception as e:
            print_error(f"Report generation failed: {e}")
            raise SystemExit(1)

        print_success(f"Report saved to {report_path}")
        if not no_browser:
            console.print("[dim]Report opened in browser.[/]")

        # Q&A session with lightweight FullAnalysis shell
        if not no_qa:
            combined_text = "\n\n---\n\n".join(doc.full_text for doc in documents)
            qa_analysis = FullAnalysis(
                document_name=quick_result.document_name,
                document_type=quick_result.document_type,
                executive_summary=ExecutiveSummary(
                    overall_risk=quick_result.overall_risk,
                    bottom_line=quick_result.bottom_line,
                    must_negotiate=quick_result.must_negotiate,
                ),
            )
            run_qa_session(
                client, combined_text, qa_analysis,
                profile=profile, feedback=feedback_store, no_feedback=no_feedback,
            )
            if verbose:
                print_cost(client.usage.summary(model_id))

        # Suggest deep dive
        console.print()
        console.print(
            "[bold cyan]Want the full picture?[/] "
            f"Run [bold]legalos analyze {path} --deep[/] for detailed analysis."
        )


# ── Redline ─────────────────────────────────────────────────────


@cli.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--model", "-m",
    type=click.Choice(["opus", "sonnet", "haiku"], case_sensitive=False),
    default="sonnet",
    show_default=True,
    help="Claude model to use.",
)
@click.option("--output", "-o", type=click.Path(path_type=Path), default=None, help="Output DOCX path.")
@click.option("--author", "-a", default="LegalOS", show_default=True, help="Author name for comments.")
@click.option("--deal", "deal_name", default=None, help="Use a named deal context.")
@click.option("--verbose", "-v", is_flag=True, help="Show token usage details.")
def redline(
    path: Path,
    model: str,
    output: Path | None,
    author: str,
    deal_name: str | None,
    verbose: bool,
) -> None:
    """Generate a redlined DOCX with margin comments.

    PATH must be a DOCX file.
    """
    from legalos.analysis.client import AnalysisClient
    from legalos.analysis.engine import run_redline_analysis
    from legalos.parsing.router import parse_input
    from legalos.profile.store import load_feedback, load_learnings as _load_learnings, load_profile
    from legalos.redline.generator import generate_redline

    if path.suffix.lower() != ".docx":
        print_error("Redline command requires a .docx file.")
        raise SystemExit(1)

    model_id = resolve_model(model)
    print_header(f"LegalOS Redline — Using {model}")

    # Load profile, feedback, and learnings
    profile = load_profile()
    feedback_store = load_feedback()
    learnings_store = _load_learnings()

    # Apply deal overlay if specified
    profile = _apply_deal_context(deal_name, profile, verbose)

    if profile is not None and verbose:
        label = profile.company.name or "founder"
        console.print(f"[dim]Using profile: {label} ({profile.risk_tolerance.value})[/]")

    # Parse
    console.print(f"[dim]Parsing {path}\u2026[/]")
    try:
        documents = parse_input(path)
    except Exception as e:
        print_error(f"Parsing failed: {e}")
        raise SystemExit(1)

    print_success(f"Parsed {sum(d.page_count for d in documents)} page(s)")

    # Analyze for redline
    client = AnalysisClient(model_id=model_id, verbose=verbose)
    try:
        redline_output = run_redline_analysis(
            client, documents, profile=profile, feedback=feedback_store,
            learnings=learnings_store,
        )
    except Exception as e:
        print_error(f"Redline analysis failed: {e}")
        raise SystemExit(1)

    print_success(f"Generated {len(redline_output.comments)} redline comments")

    # Generate annotated DOCX
    try:
        output_path = generate_redline(
            source_path=path,
            redline_output=redline_output,
            output_path=output,
            author=author,
        )
    except Exception as e:
        print_error(f"DOCX generation failed: {e}")
        raise SystemExit(1)

    print_success(f"Redlined document saved to {output_path}")

    if verbose:
        print_cost(client.usage.summary(model_id))
