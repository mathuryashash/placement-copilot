"""
Golden question set generator for retrieval and answer evals.

Generates questions from the synthetic corpus with:
- Answerable questions (with expected answer ground truth)
- Unanswerable questions (should trigger refusal)
"""
from __future__ import annotations

import json
import random
from datetime import datetime
from pathlib import Path


def generate_golden_questions(corpus: list[dict], seed: int = 42) -> list[dict]:
    """
    Generate >= 40 golden questions from a synthetic corpus.
    Each question has: id, question, expected_answer_contains (keywords),
    notice_ids (which notices should be retrieved), type (answerable/unanswerable).
    """
    random.seed(seed)
    questions = []
    q_id = 0

    for item in corpus:
        record = item["record"]
        company = record["company"]
        role = record["role"]
        el = record["eligibility"]
        notices = [n["text"][:50] for n in item["notices"]]

        # Q1: Eligibility criteria
        questions.append({
            "id": f"q{q_id:03d}",
            "question": f"What is the minimum CGPA required for {company}?",
            "expected_contains": [str(el["min_cgpa"])],
            "notice_ids": [record["id"]],
            "type": "answerable",
            "category": "eligibility",
        })
        q_id += 1

        # Q2: CTC
        questions.append({
            "id": f"q{q_id:03d}",
            "question": f"What is the package offered by {company} for the {role} role?",
            "expected_contains": [str(record["ctc_lpa"]), "LPA"],
            "notice_ids": [record["id"]],
            "type": "answerable",
            "category": "ctc",
        })
        q_id += 1

        # Q3: Deadline
        dl = record.get("registration_deadline", "")
        if dl:
            dl_dt = datetime.fromisoformat(dl)
            questions.append({
                "id": f"q{q_id:03d}",
                "question": f"When is the registration deadline for {company}?",
                "expected_contains": [str(dl_dt.year)],
                "notice_ids": [record["id"]],
                "type": "answerable",
                "category": "deadline",
            })
            q_id += 1

        # Q4: Locations
        if record["locations"]:
            questions.append({
                "id": f"q{q_id:03d}",
                "question": f"Where are the job locations for {company} {role}?",
                "expected_contains": record["locations"][:1],
                "notice_ids": [record["id"]],
                "type": "answerable",
                "category": "location",
            })
            q_id += 1

        # Q5: Branches
        questions.append({
            "id": f"q{q_id:03d}",
            "question": f"Which branches are eligible for the {company} drive?",
            "expected_contains": el["allowed_branches"][:1],
            "notice_ids": [record["id"]],
            "type": "answerable",
            "category": "eligibility",
        })
        q_id += 1

    # Unanswerable questions (fictional topics not in corpus)
    unanswerable = [
        "What is the bond period for TechDragon Corp?",
        "Does QuantumLeap Industries offer relocation assistance?",
        "What is the interview date for StellarMind Technologies?",
        "Are there any openings at GalaxyCraft for mechanical engineers?",
        "What is the dress code for the Vortex Systems interview?",
        "Does NovaStar Inc provide laptop to new hires?",
        "What is the joining date for Prism Analytics?",
        "Are lateral entries allowed for the Blueshift Capital drive?",
    ]
    for uq in unanswerable:
        questions.append({
            "id": f"q{q_id:03d}",
            "question": uq,
            "expected_contains": [],
            "notice_ids": [],
            "type": "unanswerable",
            "category": "refusal",
        })
        q_id += 1

    return questions


if __name__ == "__main__":
    import sys
    from generator import generate_corpus

    output_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/synthetic/golden_questions.json")
    corpus = generate_corpus(n=10, seed=42)
    questions = generate_golden_questions(corpus, seed=42)
    output_path.write_text(json.dumps(questions, indent=2))
    print(f"Generated {len(questions)} golden questions -> {output_path}")
    answerable = sum(1 for q in questions if q["type"] == "answerable")
    unanswerable = sum(1 for q in questions if q["type"] == "unanswerable")
    print(f"  Answerable: {answerable}, Unanswerable: {unanswerable}")
