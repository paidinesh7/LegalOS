"""Base types and abstract parser for document parsing."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class PageContent:
    """Content from a single page of a document."""

    page_number: int
    text: str
    is_ocr: bool = False


@dataclass
class ParsedDocument:
    """Parsed document ready for analysis."""

    source_path: Path
    file_type: str  # "pdf", "docx", "image"
    pages: list[PageContent] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)

    @property
    def full_text(self) -> str:
        return "\n\n".join(p.text for p in self.pages if p.text.strip())

    @property
    def page_count(self) -> int:
        return len(self.pages)

    def estimated_tokens(self) -> int:
        """Rough token estimate (~4 chars per token)."""
        return len(self.full_text) // 4


class BaseParser(ABC):
    """Abstract base class for document parsers."""

    @abstractmethod
    def parse(self, path: Path) -> ParsedDocument:
        """Parse a document file and return structured content."""
        ...

    @abstractmethod
    def supported_extensions(self) -> set[str]:
        """Return set of supported file extensions (e.g. {'.pdf'})."""
        ...
