# Design Notes — Placement Copilot

This document records the main decisions, trade-offs, and alternatives considered.
Intended as interview prep material.

---

## 1. Why pgvector instead of a dedicated vector DB (Pinecone, Qdrant, Weaviate)?

**Decision:** pgvector inside Postgres.

**Reasoning:**
- The corpus is small (hundreds of notices, thousands of chunks). pgvector handles this easily.
- One fewer service to run and explain. Postgres already stores structured drive records; keeping vectors in the same DB avoids dual-write complexity.
- HNSW index in pgvector gives sub-10ms search at this scale.
- If the corpus grew to millions of chunks, Qdrant or Pinecone would be worth the operational cost.

**Alternative rejected:** Qdrant — better at pure vector scale, but adds infra complexity for no gain here.

---

## 2. Why fastembed (ONNX) instead of sentence-transformers (PyTorch)?

**Decision:** fastembed with BAAI/bge-small-en-v1.5.

**Reasoning:**
- No torch means ~200 MB smaller Docker image and faster cold start.
- ONNX Runtime is lighter than PyTorch for inference-only workloads.
- bge-small-en-v1.5 scores well on MTEB benchmarks for retrieval; it's 384-dimensional which is a good trade-off between quality and storage.
- fastembed downloads and caches the ONNX model; no manual model management.

**Alternative rejected:** OpenAI text-embedding-3-small — better quality but costs money and adds latency; not suitable for local/offline use.

---

## 3. Why hybrid retrieval (vector + BM25) with RRF?

**Decision:** Run both cosine vector search and Postgres full-text (tsvector + ts_rank), combine with Reciprocal Rank Fusion (RRF).

**Reasoning:**
- Dense vector retrieval handles semantic similarity ("what companies are hiring for ML roles?") but misses exact keyword matches (company names, specific numbers like "7.5 CGPA").
- Full-text search is exact and fast for keywords but misses paraphrases.
- RRF (score = Σ 1/(k + rank_i)) is parameter-free, easy to implement, and consistently beats either method alone in practice (Cormack et al., 2009).
- k=60 is the standard default; no tuning needed for this scale.

**Alternative rejected:** Cross-encoder reranking — more accurate but adds ~100ms latency and another model dependency.

---

## 4. Why asyncpg instead of SQLAlchemy async?

**Decision:** asyncpg directly.

**Reasoning:**
- Explicit SQL is easier to explain in interviews.
- SQLAlchemy async adds ~300 lines of model definitions that duplicate the Pydantic models.
- asyncpg is fast and handles connection pooling well.
- Downside: no migration tool (we use raw DDL in `init_db()`). For a production system, Alembic would be appropriate.

---

## 5. Student profile in localStorage (privacy trade-off)

**Decision:** Profile stored client-side only; sent per-request; never persisted server-side.

**Reasoning:**
- CGPA and backlog count are sensitive; minimizing server-side storage reduces risk.
- Stateless server simplifies scaling (no session store needed).
- Trade-off: profile is lost when browser data is cleared; users need to re-enter it.
- Alternative: server-side session with a random token. Would enable cross-device sync but requires a session store and raises privacy questions about linking requests.

---

## 6. LLM selection: Groq (primary) with Gemini fallback

**Decision:** Groq llama-3.1-8b-instant as primary, gemini-1.5-flash as fallback.

**Reasoning:**
- Both have free tiers suitable for a portfolio demo.
- Groq offers very low latency (~100ms) for 8B models.
- Fallback ensures the demo works even if one provider has rate limits.
- All responses are disk-cached (SHA-256 of model+messages) to stay within eval budget.

---

## 7. Fake LLM mode

**Decision:** `FAKE_LLM=true` environment variable makes the LLM client return deterministic stubs without network calls.

**Reasoning:**
- All tests can run in CI without API keys.
- Stubs match the expected schema so Pydantic validation is still exercised.
- Eval accuracy numbers are meaningless in fake mode; documented in VERIFY.md.

---

## 8. Chunking strategy

**Decision:** 400-word chunks with 80-word overlap.

**Reasoning:**
- bge-small accepts up to 512 tokens; 400 words ≈ 480-520 tokens, staying safely under the limit.
- Overlap ensures that sentences spanning chunk boundaries are captured by at least one chunk.
- Alternative: sentence-aware chunking (split on `\n\n` or `.`) — better semantically but more complex; word-count is good enough for placement notices which tend to have clear paragraph structure.

---

## 9. Failure modes

| Failure | Behavior |
|---------|----------|
| LLM API down | Returns "I don't have that information" (refusal); no crash |
| Postgres connection fail | 500 error with message; no silent data loss |
| Corrupt notice text | Parser returns empty string; notice stored but with no chunks |
| Embedding model not cached | Downloads on first request (~10s); subsequent requests are fast |
| Rate limit on Groq | Retries twice with backoff, then tries Gemini; falls back to error message |

---

## 10. How to scale further

- **More notices:** pgvector HNSW handles millions of vectors; partition by academic year for faster pruning.
- **Better extraction:** Few-shot prompting with examples from the synthetic corpus improves field accuracy.
- **Multi-tenant:** Add a `corpus_id` column to chunks/notices; filter by it in all queries.
- **Real streaming:** Replace word-split SSE with Groq's streaming API for true token-level streaming.
