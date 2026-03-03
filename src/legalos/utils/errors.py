"""Exception hierarchy for LegalOS."""

from __future__ import annotations


class LegalOSError(Exception):
    """Base exception for LegalOS."""


class ParseError(LegalOSError):
    """Failed to parse a document."""


class UnsupportedFileType(ParseError):
    """File type not supported."""


class OCRError(ParseError):
    """OCR processing failed."""


class AnalysisError(LegalOSError):
    """Analysis step failed."""


class APIError(AnalysisError):
    """Anthropic API call failed."""


class ChunkingError(LegalOSError):
    """Document chunking failed."""


class RedlineError(LegalOSError):
    """Redline generation failed."""


class ReportError(LegalOSError):
    """Report generation failed."""
