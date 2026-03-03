"""HTML report rendering and browser auto-open."""

from __future__ import annotations

import json
import webbrowser
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader

from legalos.analysis.schemas import FullAnalysis, QuickScanOutput
from legalos.profile.schemas import FounderProfile, LearningEntry
from legalos.utils.errors import ReportError

TEMPLATE_DIR = Path(__file__).parent / "templates"


def generate_report(
    analysis: FullAnalysis,
    output_path: Path | None = None,
    open_browser: bool = True,
    profile: Optional[FounderProfile] = None,
    knowledge_entries: Optional[list[LearningEntry]] = None,
) -> Path:
    """Render analysis to a self-contained HTML report."""
    try:
        env = Environment(
            loader=FileSystemLoader(str(TEMPLATE_DIR)),
            autoescape=True,
        )
        template = env.get_template("report.html")

        # Read CSS to inline
        css_path = TEMPLATE_DIR / "styles.css"
        css = css_path.read_text()

        html = template.render(
            analysis=analysis, css=css, profile=profile,
            knowledge_entries=knowledge_entries or [],
            is_quick_scan=False,
        )
    except Exception as e:
        raise ReportError(f"Failed to render report: {e}") from e

    if output_path is None:
        stem = analysis.document_name.replace(" ", "_").replace(",", "")
        output_path = Path(f"legalos_report_{stem}.html")

    output_path.write_text(html, encoding="utf-8")

    # Write feedback sidecar file alongside report
    _write_feedback_sidecar(output_path, analysis)

    if open_browser:
        webbrowser.open(output_path.resolve().as_uri())

    return output_path


def _write_feedback_sidecar(report_path: Path, analysis: FullAnalysis) -> Path:
    """Write an empty feedback sidecar JSON alongside the HTML report.

    The sidecar file is pre-populated with document metadata and an empty
    votes list.  The 'feedback submit' CLI command or auto-import can later
    populate and consume it.
    """
    sidecar_path = report_path.with_suffix(".feedback.json")
    sidecar = {
        "document_name": analysis.document_name,
        "timestamp": "",
        "votes": [],
        "submitted": False,
    }
    sidecar_path.write_text(json.dumps(sidecar, indent=2), encoding="utf-8")
    return sidecar_path


def generate_quick_report(
    scan: QuickScanOutput,
    output_path: Path | None = None,
    open_browser: bool = True,
    profile: Optional[FounderProfile] = None,
) -> Path:
    """Render a quick scan to a self-contained HTML report."""
    try:
        env = Environment(
            loader=FileSystemLoader(str(TEMPLATE_DIR)),
            autoescape=True,
        )
        template = env.get_template("report.html")

        css_path = TEMPLATE_DIR / "styles.css"
        css = css_path.read_text()

        html = template.render(
            analysis=scan, css=css, profile=profile,
            knowledge_entries=[],
            is_quick_scan=True,
        )
    except Exception as e:
        raise ReportError(f"Failed to render quick scan report: {e}") from e

    if output_path is None:
        stem = scan.document_name.replace(" ", "_").replace(",", "")
        output_path = Path(f"legalos_quickscan_{stem}.html")

    output_path.write_text(html, encoding="utf-8")

    if open_browser:
        webbrowser.open(output_path.resolve().as_uri())

    return output_path
