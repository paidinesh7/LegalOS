"""PDF parsing using pymupdf4llm with OCR fallback."""

from __future__ import annotations

from pathlib import Path

import pymupdf
import pymupdf4llm

from legalos.parsing.base import BaseParser, PageContent, ParsedDocument
from legalos.utils.errors import ParseError


class PDFParser(BaseParser):
    """Extract text from PDF files using pymupdf4llm."""

    def supported_extensions(self) -> set[str]:
        return {".pdf"}

    def parse(self, path: Path) -> ParsedDocument:
        try:
            doc = pymupdf.open(str(path))
        except Exception as e:
            raise ParseError(f"Cannot open PDF: {e}") from e

        pages: list[PageContent] = []
        metadata = {k: str(v) for k, v in (doc.metadata or {}).items() if v}

        try:
            # Try pymupdf4llm markdown extraction (best for structured text)
            try:
                md_pages = pymupdf4llm.to_markdown(
                    str(path), page_chunks=True, show_progress=False
                )
                for chunk in md_pages:
                    page_num = chunk.get("metadata", {}).get("page", len(pages) + 1)
                    text = chunk.get("text", "").strip()
                    if text:
                        pages.append(PageContent(page_number=page_num, text=text))
            except Exception:
                # Fallback to basic pymupdf extraction
                for i, page in enumerate(doc):
                    text = page.get_text("text").strip()
                    if text:
                        pages.append(PageContent(page_number=i + 1, text=text))

            # If no text found, pages might be scanned — flag for OCR
            if not pages or all(len(p.text) < 50 for p in pages):
                pages = self._ocr_fallback(doc)
        finally:
            doc.close()

        return ParsedDocument(
            source_path=path, file_type="pdf", pages=pages, metadata=metadata
        )

    def _ocr_fallback(self, doc: pymupdf.Document) -> list[PageContent]:
        """Use pymupdf's built-in OCR via Tesseract if available, else return empty."""
        pages: list[PageContent] = []
        for i, page in enumerate(doc):
            try:
                tp = page.get_textpage_ocr(flags=pymupdf.TEXT_PRESERVE_WHITESPACE)
                text = page.get_text("text", textpage=tp).strip()
            except Exception:
                text = ""
            if text:
                pages.append(PageContent(page_number=i + 1, text=text, is_ocr=True))
        return pages
