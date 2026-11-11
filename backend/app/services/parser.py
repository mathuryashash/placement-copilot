"""
Text parsing utilities for placement notices.

Supports:
- Plain text
- Simple HTML/email text extraction
- PDF via pypdf
- .eml (RFC 2822) messages
"""
from __future__ import annotations

import email
import io
import re
from pathlib import Path


def parse_text(raw: str) -> str:
    """Clean and normalize plain text."""
    # Collapse excessive whitespace but preserve paragraph breaks
    raw = re.sub(r"\r\n", "\n", raw)
    raw = re.sub(r"[ \t]+", " ", raw)
    raw = re.sub(r"\n{3,}", "\n\n", raw)
    return raw.strip()


def parse_pdf(data: bytes) -> str:
    """Extract text from a PDF file (bytes)."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))
        pages = [page.extract_text() or "" for page in reader.pages]
        return parse_text("\n\n".join(pages))
    except Exception as exc:
        raise ValueError(f"PDF parse failed: {exc}") from exc


def parse_eml(data: bytes) -> str:
    """Extract plain text from an .eml file."""
    msg = email.message_from_bytes(data)
    parts: list[str] = []

    def _walk(m: email.message.Message) -> None:
        ct = m.get_content_type()
        if ct == "text/plain":
            payload = m.get_payload(decode=True)
            if payload:
                charset = m.get_content_charset() or "utf-8"
                parts.append(payload.decode(charset, errors="replace"))
        elif m.is_multipart():
            for sub in m.walk():
                if sub is not m:
                    _walk(sub)

    _walk(msg)
    text = "\n\n".join(parts)
    return parse_text(text)


def parse_file(path: str | Path, data: bytes) -> str:
    """Dispatch to the right parser based on file extension."""
    ext = Path(path).suffix.lower()
    if ext == ".pdf":
        return parse_pdf(data)
    elif ext in (".eml", ".mbox"):
        return parse_eml(data)
    else:
        return parse_text(data.decode("utf-8", errors="replace"))


# --- Chunking -------------------------------------------------------------------

def chunk_text(text: str, chunk_size: int = 400, overlap: int = 80) -> list[str]:
    """
    Split text into overlapping chunks by word count.

    Why word count instead of tokens: avoids a tokenizer dependency.
    400 words ~ 500-600 tokens for the embedding model (bge-small accepts up to 512 tokens).
    """
    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start += chunk_size - overlap
    return chunks
