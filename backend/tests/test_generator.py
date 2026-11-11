"""Tests for the synthetic data generator."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../data/synthetic"))

from generator import (
    generate_corpus,
    generate_drive_record,
    render_formal_notice,
    render_informal_notice,
)


class TestGenerator:
    def test_generate_drive_record_fields(self):
        record = generate_drive_record(seed=1)
        assert "company" in record
        assert "role" in record
        assert "ctc_lpa" in record
        assert "eligibility" in record
        el = record["eligibility"]
        assert "min_cgpa" in el
        assert "allowed_branches" in el
        assert "max_backlogs" in el
        assert "grad_years" in el

    def test_generate_drive_record_deterministic(self):
        r1 = generate_drive_record(seed=42)
        r2 = generate_drive_record(seed=42)
        assert r1["company"] == r2["company"]
        assert r1["ctc_lpa"] == r2["ctc_lpa"]

    def test_generate_corpus_count(self):
        corpus = generate_corpus(n=5, seed=42)
        assert len(corpus) == 5

    def test_corpus_has_notices(self):
        corpus = generate_corpus(n=3, seed=42)
        for item in corpus:
            assert len(item["notices"]) >= 1
            for notice in item["notices"]:
                assert "text" in notice
                assert len(notice["text"]) > 50

    def test_formal_notice_contains_company(self):
        record = generate_drive_record(seed=10)
        text = render_formal_notice(record)
        assert record["company"] in text
        assert "SYNTHETIC" in text.upper()

    def test_informal_notice_contains_ctc(self):
        record = generate_drive_record(seed=10)
        text = render_informal_notice(record)
        assert str(record["ctc_lpa"]) in text

    def test_notice_contains_cgpa(self):
        record = generate_drive_record(seed=5)
        text = render_formal_notice(record)
        assert str(record["eligibility"]["min_cgpa"]) in text
