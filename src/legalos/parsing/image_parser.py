"""Image OCR parsing using EasyOCR."""

from __future__ import annotations

from pathlib import Path

from legalos.parsing.base import BaseParser, PageContent, ParsedDocument
from legalos.utils.errors import OCRError


class ImageParser(BaseParser):
    """Extract text from scanned document images using EasyOCR."""

    def __init__(self) -> None:
        self._reader = None

    def _get_reader(self):
        if self._reader is None:
            import easyocr
            self._reader = easyocr.Reader(["en"], gpu=False, verbose=False)
        return self._reader

    def supported_extensions(self) -> set[str]:
        return {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp"}

    def parse(self, path: Path) -> ParsedDocument:
        try:
            reader = self._get_reader()
            results = reader.readtext(str(path), detail=0, paragraph=True)
        except Exception as e:
            raise OCRError(f"OCR failed for {path.name}: {e}") from e

        text = "\n".join(results)
        pages = [PageContent(page_number=1, text=text, is_ocr=True)] if text.strip() else []

        return ParsedDocument(
            source_path=path, file_type="image", pages=pages
        )
