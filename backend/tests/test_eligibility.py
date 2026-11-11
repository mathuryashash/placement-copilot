"""
Eligibility engine tests (table-driven, deterministic, no LLM/DB).
"""
from __future__ import annotations

from app.models.drive import Drive, EligibilityRule, StudentProfile
from app.services.eligibility import check_eligibility


def make_drive(**kwargs) -> Drive:
    defaults = {
        "id": "test_drive",
        "company": "AcmeCorp",
        "role": "SWE",
        "eligibility": EligibilityRule(
            min_cgpa=7.0,
            allowed_branches=["CSE", "ISE"],
            max_backlogs=0,
            grad_years=[2025, 2026],
        ),
    }
    if "eligibility" in kwargs and isinstance(kwargs["eligibility"], dict):
        kwargs["eligibility"] = EligibilityRule(**kwargs["eligibility"])
    defaults.update(kwargs)
    return Drive(**defaults)


def make_profile(**kwargs) -> StudentProfile:
    defaults = {
        "cgpa": 8.0,
        "branch": "CSE",
        "backlogs": 0,
        "grad_year": 2026,
    }
    defaults.update(kwargs)
    return StudentProfile(**defaults)


class TestEligibilityEngine:
    def test_fully_eligible(self):
        drive = make_drive()
        profile = make_profile()
        result = check_eligibility(profile, drive)
        assert result.eligible is True
        assert len(result.reasons) > 0

    def test_cgpa_too_low(self):
        drive = make_drive()
        profile = make_profile(cgpa=6.5)
        result = check_eligibility(profile, drive)
        assert result.eligible is False
        assert any("CGPA" in r for r in result.reasons)

    def test_cgpa_exact_minimum(self):
        drive = make_drive()
        profile = make_profile(cgpa=7.0)
        result = check_eligibility(profile, drive)
        assert result.eligible is True

    def test_wrong_branch(self):
        drive = make_drive()
        profile = make_profile(branch="ME")
        result = check_eligibility(profile, drive)
        assert result.eligible is False
        assert any("Branch" in r or "branch" in r.lower() for r in result.reasons)

    def test_branch_case_insensitive(self):
        drive = make_drive()
        profile = make_profile(branch="cse")  # lowercase
        result = check_eligibility(profile, drive)
        assert result.eligible is True

    def test_backlog_exceeds_limit(self):
        drive = make_drive()
        profile = make_profile(backlogs=1)  # max is 0
        result = check_eligibility(profile, drive)
        assert result.eligible is False
        assert any("backlog" in r.lower() for r in result.reasons)

    def test_backlog_within_limit(self):
        drive = make_drive(eligibility=EligibilityRule(
            min_cgpa=7.0, allowed_branches=["CSE"], max_backlogs=2, grad_years=[2026]
        ))
        profile = make_profile(backlogs=2)
        result = check_eligibility(profile, drive)
        assert result.eligible is True

    def test_wrong_grad_year(self):
        drive = make_drive()
        profile = make_profile(grad_year=2024)
        result = check_eligibility(profile, drive)
        assert result.eligible is False
        assert any("year" in r.lower() for r in result.reasons)

    def test_no_cgpa_branch_year_restrictions(self):
        """Drive with no CGPA/branch/year restrictions: only max_backlogs=0 applies."""
        drive = make_drive(eligibility=EligibilityRule())  # max_backlogs defaults to 0
        profile = make_profile(cgpa=5.0, branch="ME", backlogs=0, grad_year=2024)
        result = check_eligibility(profile, drive)
        # No CGPA/branch/year filter -> passes; backlogs=0 satisfies max_backlogs=0
        assert result.eligible is True

    def test_no_restrictions_with_backlogs_fails(self):
        """max_backlogs=0 by default; a student with backlogs is ineligible."""
        drive = make_drive(eligibility=EligibilityRule())
        profile = make_profile(cgpa=5.0, branch="ME", backlogs=3, grad_year=2024)
        result = check_eligibility(profile, drive)
        assert result.eligible is False

    def test_multiple_failures(self):
        """Multiple eligibility failures all reported."""
        drive = make_drive()
        profile = make_profile(cgpa=5.0, branch="EEE", backlogs=2, grad_year=2024)
        result = check_eligibility(profile, drive)
        assert result.eligible is False
        # At least 3 failure reasons
        failures = [r for r in result.reasons if any(
            word in r.lower() for word in ["below", "not in", "backlog", "not in the eligible"]
        )]
        assert len(failures) >= 3

    def test_all_branches_allowed_when_none(self):
        """allowed_branches=None means all branches are allowed."""
        drive = make_drive(eligibility=EligibilityRule(min_cgpa=7.0, allowed_branches=None))
        profile = make_profile(branch="ME")
        result = check_eligibility(profile, drive)
        assert result.eligible is True

    def test_extra_notes_included(self):
        drive = make_drive(eligibility=EligibilityRule(
            extra_notes="Bring original certificates on interview day"
        ))
        profile = make_profile()
        result = check_eligibility(profile, drive)
        assert any("certificate" in r.lower() for r in result.reasons)
