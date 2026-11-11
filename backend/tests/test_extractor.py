"""Tests for LLM client fake mode and extractor."""
from __future__ import annotations

import json
import os

os.environ["FAKE_LLM"] = "true"

from app.services.extractor import extract_drive
from app.services.llm_client import call_llm, fake_llm_call


class TestFakeLLM:
    def test_fake_extraction_returns_json(self):
        messages = [
            {"role": "system", "content": "You extract placement data."},
            {"role": "user", "content": "Extract the drive data from this notice text."},
        ]
        response = fake_llm_call(messages)
        # Should be valid JSON
        data = json.loads(response)
        assert "company" in data
        assert "eligibility" in data

    def test_call_llm_uses_fake_mode(self):
        """When FAKE_LLM=true, call_llm should not make network calls."""
        response = call_llm([{"role": "user", "content": "Extract drive data from notice text."}])
        assert response  # non-empty


class TestExtractor:
    def test_extract_drive_returns_drive_model(self):
        from app.models.drive import Drive
        notice_text = """
        AcmeCorp is hiring Software Engineers.
        CGPA: 7.0 minimum. Branches: CSE, ISE.
        CTC: 12 LPA. Location: Bengaluru.
        Deadline: 28 February 2025.
        """
        drive = extract_drive("test_notice_001", notice_text)
        assert isinstance(drive, Drive)
        assert drive.id == "test_notice_001"
        assert drive.company  # non-empty

    def test_extract_drive_has_eligibility(self):
        drive = extract_drive("test_notice_002", "Some placement notice text.")
        assert drive.eligibility is not None

    def test_extract_drive_notice_id_in_list(self):
        drive = extract_drive("test_notice_003", "Notice text.")
        assert "test_notice_003" in drive.notice_ids
