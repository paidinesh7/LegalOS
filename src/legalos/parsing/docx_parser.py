"""DOCX parsing using python-docx, preserving document structure."""

from __future__ import annotations

from pathlib import Path

from docx import Document

from legalos.parsing.base import BaseParser, PageContent, ParsedDocument
from legalos.utils.errors import ParseError


class DOCXParser(BaseParser):
    """Extract text from DOCX files preserving headings and structure."""

    def supported_extensions(self) -> set[str]:
        return {".docx"}

    def parse(self, path: Path) -> ParsedDocument:
        try:
            doc = Document(str(path))
        except Exception as e:
            raise ParseError(f"Cannot open DOCX: {e}") from e

        metadata: dict[str, str] = {}
        if doc.core_properties:
            props = doc.core_properties
            if props.title:
                metadata["title"] = props.title
            if props.author:
                metadata["author"] = props.author

        lines: list[str] = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue
            # Preserve heading structure with markdown-style markers
            style = (para.style.name or "").lower()
            if "heading 1" in style:
                lines.append(f"# {text}")
            elif "heading 2" in style:
                lines.append(f"## {text}")
            elif "heading 3" in style:
                lines.append(f"### {text}")
            elif "heading" in style:
                lines.append(f"#### {text}")
            else:
                lines.append(text)

        # Also extract table content
        for table in doc.tables:
            table_lines: list[str] = []
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells]
                table_lines.append(" | ".join(cells))
            if table_lines:
                lines.append("\n".join(table_lines))

        # Treat entire DOCX as a single page (no inherent page breaks)
        full_text = "\n\n".join(lines)
        pages = [PageContent(page_number=1, text=full_text)] if full_text else []

        return ParsedDocument(
            source_path=path, file_type="docx", pages=pages, metadata=metadata
        )
