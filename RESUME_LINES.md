# Resume Lines — Placement Copilot

Bullets based on verified numbers from VERIFY.md only.

---

## Resume bullets

- Built full-stack RAG app (Next.js + FastAPI + pgvector): 43 backend tests and 10 frontend unit tests pass; hybrid vector+BM25 retrieval with RRF; deterministic eligibility engine with 13 table-driven tests
- Implemented fastembed ONNX inference (BAAI/bge-small-en-v1.5) with asyncpg pool, pgvector HNSW index, and streaming SSE chat; Groq/Gemini LLM with disk cache and fallback chain
- Shipped TypeScript-clean Next.js frontend with ruff-clean FastAPI backend, CI workflow, Dockerfile, render.yaml, and synthetic data generator with 25 fictional drive records

---

## Honest keyword list (what this codebase actually uses and tests)

**Backend:** Python 3.12, FastAPI, asyncpg, pgvector, PostgreSQL, fastembed, ONNX, BAAI/bge-small-en-v1.5, Groq API, Gemini API, RRF (Reciprocal Rank Fusion), BM25, vector search, hybrid retrieval, pydantic, pytest, testcontainers, ruff

**Frontend:** Next.js 15, TypeScript, Tailwind CSS, App Router, vitest, localStorage

**Infrastructure:** Docker, pgvector/pgvector:pg17, Render (config only), Vercel (config notes), GitHub Actions CI

**Concepts:** RAG (Retrieval-Augmented Generation), hybrid search, eligibility rule engine, SSE streaming, rate limiting, CORS, LLM fallback chain, disk-based LLM cache, synthetic data generation

---

## Keywords NOT claimed (not in this codebase)

- Kubernetes, AWS, GCP, Azure, Terraform (not deployed)
- Real user data or production usage (synthetic only)
- Playwright e2e (not completed)
- Reranking, cross-encoders (not implemented)
