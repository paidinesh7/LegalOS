"""MIME detection and parser dispatch."""

from __future__ import annotations

import mimetypes
from pathlib import Path

from legalos.parsing.base import BaseParser, ParsedDocument
from legalos.utils.errors import UnsupportedFileType

# Lazy-loaded extension → parser map (avoids ~333ms import overhead on every command)
_EXT_MAP: dict[str, BaseParser] | None = None


def _get_ext_map() -> dict[str, BaseParser]:
    """Build and cache the extension → parser map on first use."""
    global _EXT_MAP
    if _EXT_MAP is None:
        from legalos.parsing.docx_parser import DOCXParser
        from legalos.parsing.image_parser import ImageParser
        from legalos.parsing.pdf_parser import PDFParser

        parsers: list[BaseParser] = [PDFParser(), DOCXParser(), ImageParser()]
        _EXT_MAP = {}
        for p in parsers:
            for ext in p.supported_extensions():
                _EXT_MAP[ext] = p
    return _EXT_MAP


def parse_file(path: Path) -> ParsedDocument:
    """Detect file type and dispatch to the appropriate parser."""
    ext_map = _get_ext_map()
    suffix = path.suffix.lower()
    parser = ext_map.get(suffix)
    if parser is None:
        mime, _ = mimetypes.guess_type(str(path))
        raise UnsupportedFileType(
            f"Unsupported file type '{suffix}' (MIME: {mime}). "
            f"Supported: {', '.join(sorted(ext_map.keys()))}"
        )
    return parser.parse(path)


def parse_file_to_text(path: Path) -> str:
    """Parse a file and return its full text content.

    Convenience wrapper used by init flow and CLI for reading
    legal brief files (.pdf, .docx, .txt, .md).
    """
    suffix = path.suffix.lower()
    if suffix in (".txt", ".md"):
        return path.read_text(encoding="utf-8")
    doc = parse_file(path)
    return doc.full_text


def parse_directory(directory: Path) -> list[ParsedDocument]:
    """Parse all supported files in a directory."""
    ext_map = _get_ext_map()
    docs: list[ParsedDocument] = []
    for f in sorted(directory.iterdir()):
        if f.is_file() and f.suffix.lower() in ext_map:
            docs.append(parse_file(f))
    return docs


def parse_input(path: Path) -> list[ParsedDocument]:
    """Parse a file or all supported files in a directory."""
    if path.is_dir():
        return parse_directory(path)
    return [parse_file(path)]
