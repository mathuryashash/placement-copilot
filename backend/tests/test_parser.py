"""Tests for parser and chunker utilities."""
from __future__ import annotations

from app.services.parser import chunk_text, parse_eml, parse_text


class TestParseText:
    def test_strips_extra_whitespace(self):
        raw = "Hello   world\n\n\n\nFoo   bar"
        result = parse_text(raw)
        assert "   " not in result
        # More than 2 consecutive newlines collapsed
        assert "\n\n\n" not in result

    def test_crlf_normalized(self):
        raw = "line1\r\nline2\r\nline3"
        result = parse_text(raw)
        assert "\r" not in result
        assert "line1\nline2\nline3" == result

    def test_empty_string(self):
        assert parse_text("") == ""

    def test_preserves_content(self):
        raw = "CGPA requirement: 7.0\nBranches: CSE, ISE"
        result = parse_text(raw)
        assert "7.0" in result
        assert "CSE" in result


class TestParseEml:
    def test_basic_eml(self):
        eml = b"""From: placement@college.example\r\nTo: students@college.example\r\nSubject: Drive Notice\r\nContent-Type: text/plain; charset=utf-8\r\n\r\nThis is a placement notice for Nexora Systems.\r\nMinimum CGPA: 7.0\r\n"""
        result = parse_eml(eml)
        assert "Nexora Systems" in result
        assert "7.0" in result

    def test_multipart_eml(self):
        eml = b"""From: test@example.com\r\nMIME-Version: 1.0\r\nContent-Type: multipart/mixed; boundary="boundary"\r\n\r\n--boundary\r\nContent-Type: text/plain\r\n\r\nPlain text part with CGPA 8.0\r\n--boundary--\r\n"""
        result = parse_eml(eml)
        assert "8.0" in result


class TestChunkText:
    def test_short_text_single_chunk(self):
        text = "Hello world foo bar"
        chunks = chunk_text(text, chunk_size=400, overlap=80)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_long_text_multiple_chunks(self):
        words = ["word"] * 1000
        text = " ".join(words)
        chunks = chunk_text(text, chunk_size=400, overlap=80)
        # Should produce ceil(1000 / (400-80)) ≈ 4 chunks
        assert len(chunks) >= 3

    def test_overlap(self):
        """Last words of chunk n should appear at start of chunk n+1."""
        words = [f"w{i}" for i in range(600)]
        text = " ".join(words)
        chunks = chunk_text(text, chunk_size=100, overlap=20)
        if len(chunks) >= 2:
            # Last 20 words of chunk 0 should be in chunk 1
            last_words = chunks[0].split()[-20:]
            first_words = chunks[1].split()[:20]
            assert last_words == first_words

    def test_empty_text(self):
        assert chunk_text("") == []
