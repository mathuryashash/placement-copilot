"""
Synthetic placement notice generator.

Generates structured Drive records for FICTIONAL companies
(clearly fake/invented names) and renders them as varied notice text formats.
Used for seeding the development corpus and running evals.

This data is SYNTHETIC — labeled throughout. Never uses real company data.
"""
from __future__ import annotations

import hashlib
import json
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional


# --- Fictional company data ---------------------------------------------------

COMPANIES = [
    {
        "name": "Nexora Systems",
        "domain": "cloud infrastructure",
        "roles": ["Software Engineer", "DevOps Engineer", "Site Reliability Engineer"],
    },
    {
        "name": "Qubitex AI",
        "domain": "AI/ML products",
        "roles": ["ML Engineer", "Data Scientist", "Research Engineer"],
    },
    {
        "name": "Terralogic Solutions",
        "domain": "enterprise software",
        "roles": ["Backend Developer", "Full Stack Developer", "Software Analyst"],
    },
    {
        "name": "Brightwave Tech",
        "domain": "fintech",
        "roles": ["Software Development Engineer", "Platform Engineer"],
    },
    {
        "name": "Helix Robotics",
        "domain": "robotics & embedded",
        "roles": ["Embedded Systems Engineer", "Robotics Software Engineer"],
    },
    {
        "name": "Cloudmapper Inc.",
        "domain": "GIS / mapping",
        "roles": ["Backend Engineer", "Data Engineer"],
    },
    {
        "name": "Veritas Analytics",
        "domain": "business intelligence",
        "roles": ["Data Analyst", "BI Engineer", "Data Engineer"],
    },
    {
        "name": "Orion Cybersec",
        "domain": "cybersecurity",
        "roles": ["Security Engineer", "Penetration Tester"],
    },
]

BRANCHES = ["CSE", "ISE", "ECE", "EEE", "ME", "CV"]
LOCATIONS = ["Bengaluru", "Hyderabad", "Pune", "Chennai", "Mumbai", "Delhi NCR", "Remote"]
IST = timezone(timedelta(hours=5, minutes=30))


def _random_date(days_ahead_min: int = 7, days_ahead_max: int = 60) -> datetime:
    base = datetime.now(tz=IST)
    delta = timedelta(days=random.randint(days_ahead_min, days_ahead_max))
    return base + delta


def _fmt_dt(dt: datetime) -> str:
    return dt.strftime("%d %B %Y, %I:%M %p IST")


def generate_drive_record(seed: int | None = None) -> dict:
    """
    Generate a single synthetic Drive ground-truth record.

    Returns a dict matching the Drive Pydantic model's JSON schema.
    """
    if seed is not None:
        random.seed(seed)

    company_data = random.choice(COMPANIES)
    role = random.choice(company_data["roles"])
    ctc = round(random.uniform(6.0, 32.0), 1)
    min_cgpa = round(random.choice([6.0, 6.5, 7.0, 7.5, 8.0]), 1)
    max_backlogs = random.choice([0, 0, 0, 1, 2])
    branches = random.sample(BRANCHES, random.randint(2, len(BRANCHES)))
    grad_years = random.sample([2025, 2026, 2027], random.randint(1, 2))
    locations = random.sample(LOCATIONS, random.randint(1, 3))
    reg_deadline = _random_date(7, 30)
    test_date = reg_deadline + timedelta(days=random.randint(3, 10))

    # Deterministic ID: content-based hash of company + role + dates (not random UUID)
    # This ensures re-ingestion produces the same notice_id for the same logical drive
    hash_key = f"{company_data['name']}:{role}:{reg_deadline.isoformat()}".encode()
    notice_id = "synthetic_" + hashlib.sha256(hash_key).hexdigest()[:16]

    rounds = [
        {"name": "Online Aptitude Test", "description": "Quant, verbal, logical reasoning", "date_hint": _fmt_dt(test_date)},
        {"name": "Coding Round", "description": "2-3 programming problems", "date_hint": ""},
        {"name": "Technical Interview", "description": "DSA, system design, project discussion", "date_hint": ""},
        {"name": "HR Interview", "description": "Culture fit, compensation discussion", "date_hint": ""},
    ]
    # Randomly drop some rounds
    rounds = rounds[:random.randint(2, 4)]

    return {
        "id": notice_id,
        "company": company_data["name"],
        "role": role,
        "ctc_lpa": ctc,
        "stipend_pm": None,
        "locations": locations,
        "eligibility": {
            "min_cgpa": min_cgpa,
            "allowed_branches": branches,
            "max_backlogs": max_backlogs,
            "grad_years": grad_years,
            "extra_notes": "",
        },
        "registration_deadline": reg_deadline.isoformat(),
        "test_date": test_date.isoformat(),
        "rounds": rounds,
        "links": [f"https://{company_data['name'].lower().replace(' ', '')}.example.com/careers/apply"],
        "notice_ids": [notice_id],
        "amendments": [],
    }


# --- Notice text renderers ----------------------------------------------------

def render_formal_notice(record: dict) -> str:
    """Render as a formal placement cell email."""
    el = record["eligibility"]
    branches_str = ", ".join(el["allowed_branches"])
    years_str = ", ".join(str(y) for y in el["grad_years"])
    deadline_str = _fmt_dt(datetime.fromisoformat(record["registration_deadline"]))

    rounds_text = "\n".join(
        f"  {i+1}. {r['name']}: {r['description']}" +
        (f" ({r['date_hint']})" if r.get("date_hint") else "")
        for i, r in enumerate(record["rounds"])
    )

    return f"""
[SYNTHETIC DATA - Training/Demo Only]
Subject: Placement Drive Notification - {record['company']} | {record['role']}

Dear Students,

We are pleased to inform you that {record['company']}, a leading company in the
{record.get('domain', 'technology')} sector, will be conducting campus recruitment.

COMPANY: {record['company']}
ROLE: {record['role']}
CTC: {record['ctc_lpa']} LPA
LOCATION(S): {', '.join(record['locations'])}

ELIGIBILITY CRITERIA:
- Minimum CGPA: {el['min_cgpa']}
- Eligible Branches: {branches_str}
- Active Backlogs: Maximum {el['max_backlogs']} allowed
- Graduation Year: {years_str}

SELECTION PROCESS:
{rounds_text}

REGISTRATION DEADLINE: {deadline_str}
Apply here: {record['links'][0] if record['links'] else 'Visit placement portal'}

Interested students must register through the placement portal before the deadline.
This is SYNTHETIC data generated for demonstration purposes only.

Regards,
Placement Cell (Fictional)
""".strip()


def render_informal_notice(record: dict) -> str:
    """Render as a forwarded informal message (with typos, casual tone)."""
    el = record["eligibility"]
    branches_str = " / ".join(el["allowed_branches"])
    deadline_str = _fmt_dt(datetime.fromisoformat(record["registration_deadline"]))

    # Introduce minor typos
    company = record["company"]
    if random.random() < 0.3:
        idx = random.randint(0, len(company) - 1)
        company = company[:idx] + company[idx:]  # keep same but simulate

    return f"""
[SYNTHETIC DATA]
---------- Forwarded message ----------

guys {company} drive is here!!

role - {record['role']}
package - {record['ctc_lpa']} lpa
cities - {', '.join(record['locations'])}

eligiblity (important plz read):
cgpa >= {el['min_cgpa']} (no relaxation)
branches: {branches_str}
backlogs: max {el['max_backlogs']}
batch: {', '.join(str(y) for y in el['grad_years'])}

rounds: {' -> '.join(r['name'] for r in record['rounds'])}

REGISTER BY: {deadline_str}
link: {record['links'][0] if record['links'] else 'placement portal'}

dont miss it, deadline is strict!!
""".strip()


def render_amendment(original: dict, changed_field: str) -> tuple[dict, str]:
    """
    Generate an amendment to an existing drive record.
    Returns (updated_record, amendment_text).
    """
    updated = json.loads(json.dumps(original))  # deep copy
    amendment_text = ""

    if changed_field == "deadline":
        old_dl = datetime.fromisoformat(updated["registration_deadline"])
        new_dl = old_dl + timedelta(days=random.randint(3, 7))
        updated["registration_deadline"] = new_dl.isoformat()
        amendment_text = (
            f"[SYNTHETIC AMENDMENT]\n"
            f"IMPORTANT: The registration deadline for {original['company']} - {original['role']} "
            f"has been EXTENDED.\n"
            f"Old deadline: {_fmt_dt(old_dl)}\n"
            f"New deadline: {_fmt_dt(new_dl)}\n"
            f"All other details remain unchanged."
        )
    elif changed_field == "cgpa":
        old_cgpa = updated["eligibility"]["min_cgpa"]
        new_cgpa = max(5.0, old_cgpa - 0.5)
        updated["eligibility"]["min_cgpa"] = new_cgpa
        amendment_text = (
            f"[SYNTHETIC AMENDMENT]\n"
            f"CORRIGENDUM: Minimum CGPA requirement for {original['company']} - {original['role']} "
            f"has been revised.\n"
            f"Revised CGPA: {new_cgpa} (was {old_cgpa})\n"
            f"Registration deadline remains {_fmt_dt(datetime.fromisoformat(updated['registration_deadline']))}."
        )

    return updated, amendment_text


# --- Corpus generator ---------------------------------------------------------

def generate_corpus(n: int = 20, seed: int = 42) -> list[dict]:
    """
    Generate a corpus of n synthetic drive records with associated notice texts.

    Returns list of dicts:
      {record (ground truth), notices: [{text, format}], amendments: [{record, text}]}
    """
    random.seed(seed)
    corpus = []

    for i in range(n):
        record = generate_drive_record(seed=seed + i)

        # Each drive gets 1-3 notices (different formats)
        formats = random.sample(["formal", "informal"], random.randint(1, 2))
        notices = []
        for fmt in formats:
            if fmt == "formal":
                text = render_formal_notice(record)
            else:
                text = render_informal_notice(record)
            notices.append({"text": text, "format": fmt})

        # ~30% chance of an amendment
        amendments = []
        if random.random() < 0.3:
            field = random.choice(["deadline", "cgpa"])
            updated_record, amend_text = render_amendment(record, field)
            amendments.append({"record": updated_record, "text": amend_text, "field": field})

        corpus.append({
            "record": record,
            "notices": notices,
            "amendments": amendments,
        })

    return corpus


if __name__ == "__main__":
    import sys

    output_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/synthetic")
    output_dir.mkdir(parents=True, exist_ok=True)

    corpus = generate_corpus(n=25, seed=42)

    # Save ground truth
    records = [item["record"] for item in corpus]
    (output_dir / "drives_ground_truth.json").write_text(
        json.dumps(records, indent=2, default=str)
    )

    # Save notices (all text files)
    notices_dir = output_dir / "notices"
    notices_dir.mkdir(exist_ok=True)
    for item in corpus:
        for j, notice in enumerate(item["notices"]):
            fname = f"{item['record']['id']}_{j}.txt"
            (notices_dir / fname).write_text(notice["text"])
        for j, amend in enumerate(item["amendments"]):
            fname = f"{item['record']['id']}_amendment_{j}.txt"
            (notices_dir / fname).write_text(amend["text"])

    print(f"Generated {len(corpus)} synthetic drive records")
    print(f"Output: {output_dir}")
    print("NOTE: This is SYNTHETIC data only. No real company or college data used.")
