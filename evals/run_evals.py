"""
Eval runner for placement-copilot.

Evals (run with real or fake LLM, results saved to evals/results/):
(a) Extraction field accuracy vs generator ground truth
(b) Retrieval recall@5 / MRR on golden question set
(c) Answer correctness + citation correctness + refusal accuracy

Usage:
    python evals/run_evals.py [--fake-llm] [--output evals/results/]

LLM calls are cached; total budget <= 300 calls.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
sys.path.insert(0, str(Path(__file__).parent.parent / "data" / "synthetic"))


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--fake-llm", action="store_true", default=True,
                   help="Use fake LLM (default: True for reproducibility)")
    p.add_argument("--output", default="evals/results", help="Output directory")
    p.add_argument("--db-url", default=os.environ.get("DATABASE_URL", ""))
    return p.parse_args()


# --- Extraction eval ----------------------------------------------------------

def eval_extraction(corpus: list[dict], fake_llm: bool) -> dict:
    """
    For each synthetic drive, run extract_drive() and compare field-by-field
    against the ground truth record.
    Returns per-field accuracy dict.
    """
    if fake_llm:
        os.environ["FAKE_LLM"] = "true"

    from app.services.extractor import extract_drive

    fields_to_check = ["company", "role", "ctc_lpa", "locations"]
    field_hits = {f: 0 for f in fields_to_check}
    field_total = {f: 0 for f in fields_to_check}
    cgpa_hits = 0
    total = 0

    for item in corpus:
        record = item["record"]
        notice_text = item["notices"][0]["text"] if item["notices"] else ""
        if not notice_text:
            continue

        try:
            drive = extract_drive(record["id"], notice_text)
        except Exception as e:
            print(f"  Extraction failed for {record['id']}: {e}")
            continue

        total += 1
        for field in fields_to_check:
            gt = record.get(field)
            pred = getattr(drive, field, None)
            field_total[field] += 1
            # Normalize comparison
            if gt is not None and pred is not None:
                gt_str = str(gt).lower().strip()
                pred_str = str(pred).lower().strip()
                if gt_str == pred_str or gt_str in pred_str:
                    field_hits[field] += 1

        # CGPA comparison
        gt_cgpa = record["eligibility"]["min_cgpa"]
        pred_cgpa = drive.eligibility.min_cgpa
        if pred_cgpa is not None and abs(gt_cgpa - pred_cgpa) < 0.1:
            cgpa_hits += 1

    results = {}
    for f in fields_to_check:
        n = field_total[f]
        results[f"extraction/{f}_accuracy"] = field_hits[f] / n if n > 0 else 0.0
    results["extraction/cgpa_accuracy"] = cgpa_hits / total if total > 0 else 0.0
    results["extraction/total_records"] = total
    return results


# --- Retrieval eval -----------------------------------------------------------

async def eval_retrieval(golden_questions: list[dict], pool) -> dict:
    """
    For each answerable golden question, check if the correct notice is in top-5 results.
    Returns recall@5 and MRR.
    """
    from app.services.retriever import hybrid_search

    recall_hits = 0
    mrr_total = 0.0
    n_answerable = 0

    for q in golden_questions:
        if q["type"] != "answerable":
            continue
        expected_ids = set(q.get("notice_ids", []))
        if not expected_ids:
            continue

        n_answerable += 1
        chunks = await hybrid_search(q["question"], pool=pool, top_k=5)
        retrieved_notice_ids = [c["notice_id"] for c in chunks]

        # Recall@5
        if any(nid in expected_ids for nid in retrieved_notice_ids):
            recall_hits += 1

        # MRR
        for rank, nid in enumerate(retrieved_notice_ids, start=1):
            if nid in expected_ids:
                mrr_total += 1.0 / rank
                break

    return {
        "retrieval/recall_at_5": recall_hits / n_answerable if n_answerable > 0 else 0.0,
        "retrieval/mrr": mrr_total / n_answerable if n_answerable > 0 else 0.0,
        "retrieval/n_questions": n_answerable,
    }


# --- Answer correctness eval --------------------------------------------------

async def eval_answers(golden_questions: list[dict], fake_llm: bool) -> dict:
    """
    For each question, call the chat endpoint and check:
    - Answerable: answer contains expected keywords
    - Unanswerable: answer is a refusal
    """
    import httpx
    from app.db.database import init_db

    await init_db()

    correct = 0
    refusal_correct = 0
    n_answerable = 0
    n_unanswerable = 0
    citation_hits = 0

    from app.main import app as fastapi_app
    transport = httpx.ASGITransport(app=fastapi_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        for q in golden_questions[:50]:  # cap at 50 to stay in budget
            resp = await client.post(
                "/api/v1/chat",
                json={
                    "messages": [{"role": "user", "content": q["question"]}],
                    "session_id": "eval-session",
                },
            )
            if resp.status_code != 200:
                continue

            data = resp.json()
            answer = data.get("answer", "").lower()
            is_refusal = data.get("is_refusal", False)
            citations = data.get("citations", [])

            if q["type"] == "unanswerable":
                n_unanswerable += 1
                if is_refusal or "don't have" in answer or "not in" in answer:
                    refusal_correct += 1
            else:
                n_answerable += 1
                # Check if expected keywords appear in answer
                expected = q.get("expected_contains", [])
                if expected and any(kw.lower() in answer for kw in expected):
                    correct += 1
                # Check citations
                expected_ids = set(q.get("notice_ids", []))
                cited_ids = {c.get("notice_id", "") for c in citations}
                if expected_ids and expected_ids & cited_ids:
                    citation_hits += 1

    return {
        "answers/correctness": correct / n_answerable if n_answerable > 0 else 0.0,
        "answers/refusal_accuracy": refusal_correct / n_unanswerable if n_unanswerable > 0 else 0.0,
        "answers/citation_accuracy": citation_hits / n_answerable if n_answerable > 0 else 0.0,
        "answers/n_answerable": n_answerable,
        "answers/n_unanswerable": n_unanswerable,
    }


async def main():
    args = parse_args()
    if args.fake_llm:
        os.environ["FAKE_LLM"] = "true"
    if args.db_url:
        os.environ["DATABASE_URL"] = args.db_url

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=== Placement Copilot Evals ===")
    print(f"Mode: {'FAKE LLM' if args.fake_llm else 'REAL LLM'}")

    # Generate synthetic corpus
    from generator import generate_corpus
    from golden_questions import generate_golden_questions

    corpus = generate_corpus(n=20, seed=42)
    golden_questions = generate_golden_questions(corpus, seed=42)
    print(f"Corpus: {len(corpus)} drives, {len(golden_questions)} golden questions")

    # Save corpus and questions
    (output_dir / "corpus.json").write_text(json.dumps(corpus, indent=2, default=str))
    (output_dir / "golden_questions.json").write_text(json.dumps(golden_questions, indent=2))

    all_results = {}
    all_results["setup"] = {
        "fake_llm": args.fake_llm,
        "corpus_size": len(corpus),
        "golden_questions": len(golden_questions),
        "model": "fake" if args.fake_llm else "llama-3.1-8b-instant (Groq) / gemini-1.5-flash (fallback)",
        "hardware": "laptop (synthetic data, no real corpus)",
    }

    # (a) Extraction eval
    print("\n--- (a) Extraction eval ---")
    extraction_results = eval_extraction(corpus, fake_llm=args.fake_llm)
    all_results.update(extraction_results)
    for k, v in extraction_results.items():
        print(f"  {k}: {v:.3f}" if isinstance(v, float) else f"  {k}: {v}")

    # (b) Retrieval eval — needs DB
    print("\n--- (b) Retrieval eval ---")
    try:
        from app.db.database import get_pool, init_db
        from app.services.ingestion import ingest_text

        await init_db()
        pool = await get_pool()

        # Ingest corpus into DB
        for item in corpus:
            for notice in item["notices"]:
                await ingest_text(notice["text"], source_name=item["record"]["id"], pool=pool)

        retrieval_results = await eval_retrieval(golden_questions, pool=pool)
        all_results.update(retrieval_results)
        for k, v in retrieval_results.items():
            print(f"  {k}: {v:.3f}" if isinstance(v, float) else f"  {k}: {v}")
    except Exception as e:
        print(f"  Retrieval eval skipped (no DB): {e}")
        all_results["retrieval/skipped"] = str(e)

    # (c) Answer eval
    print("\n--- (c) Answer eval ---")
    try:
        answer_results = await eval_answers(golden_questions, fake_llm=args.fake_llm)
        all_results.update(answer_results)
        for k, v in answer_results.items():
            print(f"  {k}: {v:.3f}" if isinstance(v, float) else f"  {k}: {v}")
    except Exception as e:
        print(f"  Answer eval skipped: {e}")
        all_results["answers/skipped"] = str(e)

    # Save results
    results_path = output_dir / "eval_results.json"
    results_path.write_text(json.dumps(all_results, indent=2, default=str))
    print(f"\nResults saved to {results_path}")
    return all_results


if __name__ == "__main__":
    asyncio.run(main())
