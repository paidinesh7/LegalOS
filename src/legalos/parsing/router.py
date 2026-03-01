"""MIME detection and parser dispatch."""

from __future__ import annotations

import mimetypes
from pathlib import Path

from legalos.parsing.base import BaseParser, ParsedDocument
from legalos.parsing.docx_parser import DOCXParser
from legalos.parsing.image_parser import ImageParser
from legalos.parsing.pdf_parser import PDFParser
from legalos.utils.errors import UnsupportedFileType

# Map extensions to parser classes
_PARSERS: list[BaseParser] = [
    PDFParser(),
    DOCXParser(),
    ImageParser(),
]

_EXT_MAP: dict[str, BaseParser] = {}
for _p in _PARSERS:
    for _ext in _p.supported_extensions():
        _EXT_MAP[_ext] = _p


def parse_file(path: Path) -> ParsedDocument:
    """Detect file type and dispatch to the appropriate parser."""
    suffix = path.suffix.lower()
    parser = _EXT_MAP.get(suffix)
    if parser is None:
        mime, _ = mimetypes.guess_type(str(path))
        raise UnsupportedFileType(
            f"Unsupported file type '{suffix}' (MIME: {mime}). "
            f"Supported: {', '.join(sorted(_EXT_MAP.keys()))}"
        )
    return parser.parse(path)


def parse_directory(directory: Path) -> list[ParsedDocument]:
    """Parse all supported files in a directory."""
    docs: list[ParsedDocument] = []
    for f in sorted(directory.iterdir()):
        if f.is_file() and f.suffix.lower() in _EXT_MAP:
            docs.append(parse_file(f))
    return docs


def parse_input(path: Path) -> list[ParsedDocument]:
    """Parse a file or all supported files in a directory."""
    if path.is_dir():
        return parse_directory(path)
    return [parse_file(path)]
