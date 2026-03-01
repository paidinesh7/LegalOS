"""Click CLI — analyze and redline commands."""

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
@click.option("--verbose", "-v", is_flag=True, help="Show token usage details.")
def analyze(
    path: Path,
    model: str,
    output: Path | None,
    no_qa: bool,
    no_browser: bool,
    verbose: bool,
) -> None:
    """Analyze legal documents and generate an interactive report.

    PATH can be a single file (PDF/DOCX/image) or a directory of files.
    """
    from legalos.analysis.client import AnalysisClient
    from legalos.analysis.engine import run_analysis
    from legalos.parsing.router import parse_input
    from legalos.qa.session import run_qa_session
    from legalos.report.generator import generate_report

    model_id = resolve_model(model)
    print_header(f"LegalOS — Analyzing with {model}")

    # Parse
    console.print(f"[dim]Parsing {path}…[/]")
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
    try:
        analysis = run_analysis(client, documents)
    except Exception as e:
        print_error(f"Analysis failed: {e}")
        raise SystemExit(1)

    print_success(f"Analysis complete — {sum(len(s.findings) for s in analysis.sections)} findings across {len(analysis.sections)} sections")

    if verbose:
        print_cost(client.usage.summary(model_id))

    # Generate report
    try:
        report_path = generate_report(analysis, output_path=output, open_browser=not no_browser)
    except Exception as e:
        print_error(f"Report generation failed: {e}")
        raise SystemExit(1)

    print_success(f"Report saved to {report_path}")
    if not no_browser:
        console.print("[dim]Report opened in browser.[/]")

    # Q&A session
    if not no_qa:
        combined_text = "\n\n---\n\n".join(doc.full_text for doc in documents)
        run_qa_session(client, combined_text, analysis)
        if verbose:
            print_cost(client.usage.summary(model_id))


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
@click.option("--verbose", "-v", is_flag=True, help="Show token usage details.")
def redline(
    path: Path,
    model: str,
    output: Path | None,
    author: str,
    verbose: bool,
) -> None:
    """Generate a redlined DOCX with margin comments.

    PATH must be a DOCX file.
    """
    from legalos.analysis.client import AnalysisClient
    from legalos.analysis.engine import run_redline_analysis
    from legalos.parsing.router import parse_input
    from legalos.redline.generator import generate_redline

    if path.suffix.lower() != ".docx":
        print_error("Redline command requires a .docx file.")
        raise SystemExit(1)

    model_id = resolve_model(model)
    print_header(f"LegalOS Redline — Using {model}")

    # Parse
    console.print(f"[dim]Parsing {path}…[/]")
    try:
        documents = parse_input(path)
    except Exception as e:
        print_error(f"Parsing failed: {e}")
        raise SystemExit(1)

    print_success(f"Parsed {sum(d.page_count for d in documents)} page(s)")

    # Analyze for redline
    client = AnalysisClient(model_id=model_id, verbose=verbose)
    try:
        redline_output = run_redline_analysis(client, documents)
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
