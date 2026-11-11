"""
Deterministic eligibility engine (no LLM).

Given a StudentProfile and a Drive, returns eligible/not + reasons.
All logic is table-driven and unit-tested.
"""
from __future__ import annotations

from app.models.drive import Drive, EligibilityResult, StudentProfile


def check_eligibility(profile: StudentProfile, drive: Drive) -> EligibilityResult:
    """
    Check if a student is eligible for a drive.

    Rules (applied in order; all must pass):
    1. CGPA >= min_cgpa (if specified)
    2. Branch in allowed_branches (if specified)
    3. Active backlogs <= max_backlogs
    4. Grad year in allowed grad_years (if specified)
    """
    reasons: list[str] = []
    eligible = True
    rule = drive.eligibility

    # 1. CGPA check
    if rule.min_cgpa is not None:
        if profile.cgpa < rule.min_cgpa:
            eligible = False
            reasons.append(
                f"CGPA {profile.cgpa:.2f} is below the minimum {rule.min_cgpa:.2f} required."
            )
        else:
            reasons.append(
                f"CGPA {profile.cgpa:.2f} meets the minimum {rule.min_cgpa:.2f}."
            )

    # 2. Branch check
    if rule.allowed_branches is not None:
        # Normalize to uppercase for comparison
        allowed = {b.upper().strip() for b in rule.allowed_branches}
        student_branch = profile.branch.upper().strip()
        if student_branch not in allowed:
            eligible = False
            reasons.append(
                f"Branch '{profile.branch}' is not in the allowed list: {', '.join(sorted(allowed))}."
            )
        else:
            reasons.append(f"Branch '{profile.branch}' is eligible.")

    # 3. Backlog check
    if profile.backlogs > rule.max_backlogs:
        eligible = False
        reasons.append(
            f"You have {profile.backlogs} active backlog(s); maximum allowed is {rule.max_backlogs}."
        )
    else:
        if rule.max_backlogs == 0:
            reasons.append("No active backlogs required — you have none.")
        else:
            reasons.append(
                f"Active backlogs ({profile.backlogs}) within the allowed maximum ({rule.max_backlogs})."
            )

    # 4. Grad year check
    if rule.grad_years is not None:
        if profile.grad_year not in rule.grad_years:
            eligible = False
            years_str = ", ".join(str(y) for y in sorted(rule.grad_years))
            reasons.append(
                f"Graduation year {profile.grad_year} is not in the eligible years: {years_str}."
            )
        else:
            reasons.append(f"Graduation year {profile.grad_year} is eligible.")

    # Extra notes from the drive
    if rule.extra_notes:
        reasons.append(f"Note from drive: {rule.extra_notes}")

    return EligibilityResult(eligible=eligible, reasons=reasons)
