"""HTML report rendering and browser auto-open."""

from __future__ import annotations

import webbrowser
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from legalos.analysis.schemas import FullAnalysis
from legalos.utils.errors import ReportError

TEMPLATE_DIR = Path(__file__).parent / "templates"


def generate_report(
    analysis: FullAnalysis,
    output_path: Path | None = None,
    open_browser: bool = True,
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

        html = template.render(analysis=analysis, css=css)
    except Exception as e:
        raise ReportError(f"Failed to render report: {e}") from e

    if output_path is None:
        stem = analysis.document_name.replace(" ", "_").replace(",", "")
        output_path = Path(f"legalos_report_{stem}.html")

    output_path.write_text(html, encoding="utf-8")

    if open_browser:
        webbrowser.open(output_path.resolve().as_uri())

    return output_path
