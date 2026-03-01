"""Section-aware document chunking with overlap."""

from __future__ import annotations

import re
from dataclasses import dataclass

from legalos.config import CHUNK_OVERLAP, MAX_DOCUMENT_TOKENS, SINGLE_PASS_LIMIT
from legalos.utils.errors import ChunkingError


@dataclass
class DocumentChunk:
    """A chunk of document text with metadata."""

    text: str
    chunk_index: int
    total_chunks: int
    has_overlap: bool = False


# Patterns that typically mark clause/section boundaries in legal docs
_SECTION_BREAK = re.compile(
    r"\n(?="
    r"(?:\d+\.[\d.]*\s)|"       # 1.  1.1  1.1.2
    r"(?:ARTICLE\s)|"           # ARTICLE I
    r"(?:SCHEDULE\s)|"          # SCHEDULE
    r"(?:ANNEXURE\s)|"          # ANNEXURE
    r"(?:CLAUSE\s)|"            # CLAUSE
    r"(?:SECTION\s)|"           # SECTION
    r"(?:#{1,4}\s)"             # Markdown headings
    r")",
    re.IGNORECASE,
)


def chunk_document(text: str, max_chunk_tokens: int = SINGLE_PASS_LIMIT) -> list[DocumentChunk]:
    """Split document text into section-aware chunks.

    Documents under max_chunk_tokens are returned as a single chunk.
    Larger documents are split at clause/section boundaries with overlap.
    """
    est_tokens = len(text) // 4
    if est_tokens <= max_chunk_tokens:
        return [DocumentChunk(text=text, chunk_index=0, total_chunks=1)]

    if est_tokens > MAX_DOCUMENT_TOKENS:
        raise ChunkingError(
            f"Document too large (~{est_tokens:,} tokens). "
            f"Maximum supported: {MAX_DOCUMENT_TOKENS:,} tokens."
        )

    # Split at section boundaries
    sections = _SECTION_BREAK.split(text)
    # Re-attach the split markers (lookahead doesn't consume)
    # Actually the pattern uses lookahead so sections keeps full text
    # But split with lookahead can be tricky, let's use findall approach
    boundaries = list(_SECTION_BREAK.finditer(text))
    if not boundaries:
        # No section boundaries found — split at paragraph breaks
        return _split_at_paragraphs(text, max_chunk_tokens)

    # Build sections from boundary positions
    parts: list[str] = []
    prev = 0
    for m in boundaries:
        part = text[prev : m.start()].strip()
        if part:
            parts.append(part)
        prev = m.start()
    # Last section
    tail = text[prev:].strip()
    if tail:
        parts.append(tail)

    # Merge sections into chunks under token limit
    return _merge_sections(parts, max_chunk_tokens)


def _merge_sections(parts: list[str], max_tokens: int) -> list[DocumentChunk]:
    """Merge sections into chunks that fit within token limit, with overlap."""
    chunks: list[DocumentChunk] = []
    current_parts: list[str] = []
    current_tokens = 0
    overlap_chars = CHUNK_OVERLAP * 4  # Convert token overlap to char estimate

    for part in parts:
        part_tokens = len(part) // 4
        if current_tokens + part_tokens > max_tokens and current_parts:
            # Finalize current chunk
            chunk_text = "\n\n".join(current_parts)
            chunks.append(DocumentChunk(
                text=chunk_text,
                chunk_index=len(chunks),
                total_chunks=0,  # Will fix after
                has_overlap=len(chunks) > 0,
            ))
            # Start new chunk with overlap from end of previous
            overlap_text = chunk_text[-overlap_chars:] if len(chunk_text) > overlap_chars else ""
            if overlap_text:
                current_parts = [f"[CONTEXT FROM PREVIOUS SECTION]\n{overlap_text}"]
                current_tokens = len(overlap_text) // 4
            else:
                current_parts = []
                current_tokens = 0

        current_parts.append(part)
        current_tokens += part_tokens

    # Last chunk
    if current_parts:
        chunks.append(DocumentChunk(
            text="\n\n".join(current_parts),
            chunk_index=len(chunks),
            total_chunks=0,
            has_overlap=len(chunks) > 0,
        ))

    # Fix total_chunks
    total = len(chunks)
    for c in chunks:
        c.total_chunks = total

    return chunks


def _split_at_paragraphs(text: str, max_tokens: int) -> list[DocumentChunk]:
    """Fallback: split at double-newlines."""
    paragraphs = text.split("\n\n")
    return _merge_sections(paragraphs, max_tokens)
