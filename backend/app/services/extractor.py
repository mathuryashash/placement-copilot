"""
Structured extraction: LLM + Pydantic validation.

Given raw notice text, extracts a Drive record with JSON schema enforcement.
Amendments (updated notices) patch the existing Drive record and append to history.
"""
from __future__ import annotations

import json
import re
from datetime import datetime

from app.models.drive import Drive, DriveAmendment
from app.services.llm_client import call_llm

SYSTEM_PROMPT = """You are a placement drive data extractor for an Indian engineering college placement cell.
Given raw text from a placement notice, extract the structured fields in JSON format exactly matching this schema.
If a field is not mentioned, use null.
All deadlines must be in ISO 8601 format with IST offset (+05:30).
Output ONLY valid JSON, no extra text.

Schema:
{
  "company": "string",
  "role": "string",
  "ctc_lpa": number | null,
  "stipend_pm": number | null,
  "locations": ["string"],
  "eligibility": {
    "min_cgpa": number | null,
    "allowed_branches": ["string"] | null,
    "max_backlogs": integer,
    "grad_years": [integer] | null,
    "extra_notes": "string"
  },
  "registration_deadline": "ISO8601 string" | null,
  "test_date": "ISO8601 string" | null,
  "rounds": [{"name": "string", "description": "string", "date_hint": "string"}],
  "links": ["string"]
}"""


def _parse_json_response(text: str) -> dict:
    """Extract JSON from LLM response (may have extra prose)."""
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Try extracting a JSON block
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        return json.loads(match.group())
    raise ValueError(f"Could not parse JSON from LLM response: {text[:200]}")


def extract_drive(notice_id: str, text: str) -> Drive:
    """
    Extract a Drive record from notice text.
    Uses LLM (cached) + Pydantic validation.
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Extract the placement drive data from this notice:\n\n{text[:6000]}"},
    ]
    raw = call_llm(messages, max_tokens=1024)
    data = _parse_json_response(raw)

    # Validate and coerce with Pydantic
    drive = Drive(
        id=notice_id,
        notice_ids=[notice_id],
        **{k: v for k, v in data.items() if v is not None},
    )
    return drive


def apply_amendment(existing: Drive, notice_id: str, amendment_text: str) -> Drive:
    """
    Apply an amendment notice to an existing Drive record.
    Keeps amendment history.
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"This is an AMENDMENT to the placement drive for {existing.company} - {existing.role}.\n"
                f"Current record:\n{existing.model_dump_json()}\n\n"
                f"Amendment notice:\n{amendment_text[:4000]}\n\n"
                "Output ONLY the updated fields that changed, as JSON."
            ),
        },
    ]
    raw = call_llm(messages, max_tokens=512)
    try:
        changes = _parse_json_response(raw)
    except ValueError:
        changes = {}

    amendment = DriveAmendment(
        notice_id=notice_id,
        changed_at=datetime.utcnow(),
        description=f"Amendment from notice {notice_id}: {str(changes)[:200]}",
    )

    updated_data = existing.model_dump()
    updated_data.update({k: v for k, v in changes.items() if v is not None})
    updated_data["notice_ids"] = list(set(existing.notice_ids + [notice_id]))
    updated_data["amendments"] = [a.model_dump() for a in existing.amendments] + [amendment.model_dump()]
    updated_data["updated_at"] = datetime.utcnow()

    return Drive(**updated_data)
