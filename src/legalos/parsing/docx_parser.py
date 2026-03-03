"""DOCX parsing using python-docx, preserving document structure."""

from __future__ import annotations

from pathlib import Path

from docx import Document
from lxml import etree

from legalos.parsing.base import BaseParser, PageContent, ParsedDocument
from legalos.utils.errors import ParseError

# Word XML namespace
_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


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

        # Walk body children in order to interleave paragraphs and tables
        body = doc.element.body
        for child in body:
            tag = etree.QName(child.tag).localname
            if tag == "p":
                text = child.text or ""
                # Collect all run text within the paragraph
                text = "".join(
                    node.text or ""
                    for node in child.iter(f"{{{_W_NS}}}t")
                )
                text = text.strip()
                if not text:
                    continue
                # Determine heading level from style
                style_name = self._get_para_style(child, doc)
                if "heading 1" in style_name:
                    lines.append(f"# {text}")
                elif "heading 2" in style_name:
                    lines.append(f"## {text}")
                elif "heading 3" in style_name:
                    lines.append(f"### {text}")
                elif "heading" in style_name:
                    lines.append(f"#### {text}")
                else:
                    lines.append(text)
            elif tag == "tbl":
                table_lines = self._extract_table(child)
                if table_lines:
                    lines.append("\n".join(table_lines))

        # Extract footnotes if available
        footnote_texts = self._extract_footnotes(doc)
        if footnote_texts:
            lines.append("\n--- Footnotes ---")
            for i, fn in enumerate(footnote_texts, 1):
                lines.append(f"[{i}] {fn}")

        # Treat entire DOCX as a single page (no inherent page breaks)
        full_text = "\n\n".join(lines)
        pages = [PageContent(page_number=1, text=full_text)] if full_text else []

        return ParsedDocument(
            source_path=path, file_type="docx", pages=pages, metadata=metadata
        )

    @staticmethod
    def _get_para_style(para_elem: etree._Element, doc: Document) -> str:
        """Get the style name for a paragraph element, guarding against None."""
        pPr = para_elem.find(f"{{{_W_NS}}}pPr")
        if pPr is None:
            return ""
        pStyle = pPr.find(f"{{{_W_NS}}}pStyle")
        if pStyle is None:
            return ""
        style_id = pStyle.get(f"{{{_W_NS}}}val", "")
        # Look up style name from style_id
        try:
            style = doc.styles.get_by_id(style_id, "paragraph")
            return (style.name or "").lower() if style else ""
        except Exception:
            return style_id.lower()

    @staticmethod
    def _extract_table(tbl_elem: etree._Element) -> list[str]:
        """Extract text from a table element as pipe-separated rows."""
        table_lines: list[str] = []
        for tr in tbl_elem.iter(f"{{{_W_NS}}}tr"):
            cells: list[str] = []
            for tc in tr.iter(f"{{{_W_NS}}}tc"):
                cell_text = "".join(
                    node.text or ""
                    for node in tc.iter(f"{{{_W_NS}}}t")
                ).strip()
                cells.append(cell_text)
            if cells:
                table_lines.append(" | ".join(cells))
        return table_lines

    @staticmethod
    def _extract_footnotes(doc: Document) -> list[str]:
        """Extract footnote text from the DOCX package if available."""
        footnotes: list[str] = []
        try:
            # python-docx doesn't expose footnotes directly; access via package parts
            for rel in doc.part.rels.values():
                if "footnotes" in (rel.reltype or ""):
                    fn_part = rel.target_part
                    fn_xml = etree.fromstring(fn_part.blob)
                    for footnote in fn_xml.iter(f"{{{_W_NS}}}footnote"):
                        fn_id = footnote.get(f"{{{_W_NS}}}id", "")
                        # Skip separator footnotes (id 0 and -1)
                        if fn_id in ("0", "-1"):
                            continue
                        text = "".join(
                            node.text or ""
                            for node in footnote.iter(f"{{{_W_NS}}}t")
                        ).strip()
                        if text:
                            footnotes.append(text)
                    break
        except Exception:
            pass  # Footnotes are optional; don't fail if unavailable
        return footnotes
