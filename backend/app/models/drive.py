"""Pydantic models for placement drive data."""
from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class EligibilityRule(BaseModel):
    min_cgpa: float | None = None
    allowed_branches: list[str] | None = None  # None = all branches
    max_backlogs: int = 0
    grad_years: list[int] | None = None  # None = any year
    extra_notes: str = ""


class Round(BaseModel):
    name: str
    description: str = ""
    date_hint: str = ""  # free text from notice


class DriveAmendment(BaseModel):
    notice_id: str
    changed_at: datetime
    description: str  # human-readable diff


class Drive(BaseModel):
    """Structured record extracted from placement notices."""
    id: str
    company: str
    role: str
    ctc_lpa: float | None = None  # CTC in LPA; None if not stated
    stipend_pm: int | None = None  # Monthly stipend in INR; for internships
    locations: list[str] = Field(default_factory=list)
    eligibility: EligibilityRule = Field(default_factory=EligibilityRule)
    registration_deadline: datetime | None = None
    test_date: datetime | None = None
    rounds: list[Round] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)
    notice_ids: list[str] = Field(default_factory=list)  # source notices
    amendments: list[DriveAmendment] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class StudentProfile(BaseModel):
    """Student profile for eligibility checks (sent per-request; not stored server-side)."""
    cgpa: float = Field(..., ge=0.0, le=10.0)
    branch: str
    backlogs: int = Field(default=0, ge=0)
    grad_year: int


class EligibilityResult(BaseModel):
    eligible: bool
    reasons: list[str]  # always populated; explains why eligible or not


class FeedbackType(StrEnum):
    up = "up"
    down = "down"


class Feedback(BaseModel):
    session_id: str  # random client-generated ID; not linked to identity
    message_index: int
    feedback: FeedbackType
