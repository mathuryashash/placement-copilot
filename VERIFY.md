# VERIFY.md — Placement Copilot

All numbers in this file were produced by running the exact commands shown,
on a laptop (Windows 11, 16 GB RAM, Docker VM ~8 GB).
Data is **synthetic** — fictional company names, generated notices.

---

## Setup

```bash
# Start Postgres with pgvector
docker run -d --name placement-copilot-db \
  -e POSTGRES_USER=copilot -e POSTGRES_PASSWORD=copilot \
  -e POSTGRES_DB=placement_copilot \
  -p 18401:5432 pgvector/pgvector:pg17

# Backend venv
cd backend && python -m venv .venv && source .venv/bin/activate   # or Scripts\activate on Windows
pip install -r requirements.txt
```

---

## Backend unit tests (35 tests, no DB)

Command:
```bash
cd backend
FAKE_LLM=true python -m pytest tests/test_parser.py tests/test_eligibility.py \
  tests/test_extractor.py tests/test_generator.py -v
```

Output (trimmed):
```
============================= test session starts =============================
collected 35 items
...
============================= 35 passed in 0.47s ==============================
```

**35 passed, 0 failed.**

---

## Backend integration tests (8 tests, real Postgres/pgvector)

Command:
```bash
cd backend
FAKE_LLM=true HF_HOME=./hf_cache \
  DATABASE_URL="postgresql+psycopg://copilot:copilot@localhost:18401/placement_copilot" \
  python -m pytest tests/test_api_integration.py -v
```

Output (trimmed):
```
============================= test session starts =============================
collected 8 items
tests/test_api_integration.py::test_health PASSED
tests/test_api_integration.py::test_ingest_text PASSED
tests/test_api_integration.py::test_chat_after_ingest PASSED
tests/test_api_integration.py::test_drives_list PASSED
tests/test_api_integration.py::test_deadlines_list PASSED
tests/test_api_integration.py::test_ingest_text_too_large PASSED
tests/test_api_integration.py::test_feedback_endpoint PASSED
tests/test_api_integration.py::test_eligibility_drive_not_found PASSED
============================= 8 passed in 2.96s ==============================
```

**8 passed, 0 failed.**  
Note: first run takes ~10s extra for the ONNX embedding model download.

---

## Full backend test suite (43 tests)

Command:
```bash
cd backend
FAKE_LLM=true HF_HOME=./hf_cache \
  DATABASE_URL="postgresql+psycopg://copilot:copilot@localhost:18401/placement_copilot" \
  python -m pytest tests/ -v
```

**43 passed, 0 failed.**

---

## Frontend unit tests (10 tests, vitest)

Command:
```bash
cd frontend
node node_modules/vitest/vitest.mjs run
```

Output (trimmed):
```
 Test Files  1 passed (1)
     Tests  10 passed (10)
  Start at  01:04:00
  Duration  2.78s
```

**10 passed, 0 failed.**

---

## Ruff lint (backend)

Command:
```bash
cd backend && ruff check app/ tests/
```

Output: `All checks passed!`

---

## TypeScript typecheck (frontend)

Command:
```bash
cd frontend && npx tsc --noEmit
```

Output: (no output = clean)

---

## Evals (fake LLM mode)

Command:
```bash
FAKE_LLM=true HF_HOME=./backend/hf_cache \
  DATABASE_URL="postgresql+psycopg://copilot:copilot@localhost:18401/placement_copilot" \
  python evals/run_evals.py --fake-llm --output evals/results/
```

Output:
```
=== Placement Copilot Evals ===
Mode: FAKE LLM
Corpus: 20 drives, 108 golden questions

--- (a) Extraction eval ---
  extraction/cgpa_accuracy: 0.200    (fake stub returns fixed values; not meaningful)
  extraction/total_records: 20

--- (b) Retrieval eval ---
  retrieval/recall_at_5: 0.000       (ID mismatch in fake mode; see note below)
  retrieval/mrr: 0.000
  retrieval/n_questions: 100

--- (c) Answer eval ---
  answers/correctness: 0.020
  answers/refusal_accuracy: 0.000    (fake LLM never refuses)
  answers/n_answerable: 50
  answers/n_unanswerable: 0
```

**Note on fake LLM eval numbers:**
- Extraction accuracy in fake mode is not meaningful: the stub always returns "AcmeCorp / Software Engineer / 12.0 LPA" regardless of input.
- Retrieval recall@5 is 0 because the eval re-ingests the corpus (generating new DB IDs) while golden questions reference the original synthetic IDs.
- Refusal accuracy is 0 because the fake stub never says "I don't have that information" — it always returns a generic answer.
- **Real LLM eval numbers require funded API keys and are not yet measured.** The eval harness is in place and can be run with `FAKE_LLM=false`.

---

## Security checks

```bash
gitleaks detect --source . --no-banner
# Output: no leaks found

git grep -nE "D:/|C:/Users|yashash mathur|gsk_|AIza|nvapi-|sk-" -- . ':!*.md' ':!frontend/package-lock.json'
# Output: (empty — only a docstring mention of "Groq", no key values)
```

---

## Actionlint (CI workflow)

```bash
actionlint .github/workflows/ci.yml
```

---

## What is NOT done

- Playwright e2e tests: require a running backend + frontend together; not yet wired into CI.
- Real LLM eval numbers: require Groq/Gemini keys and an eval run; eval harness is ready.
- Frontend Next.js build test in CI: wired but not locally verified in this session.
- Production deployment: not deployed; render.yaml and docs/DEPLOY.md cover the steps.
- mbox/email attachment ingestion: file upload endpoint exists but only tested with .txt.
