"""
Hybrid retrieval: vector search + BM25-ish full-text, combined with Reciprocal Rank Fusion (RRF).

RRF formula: score(d) = sum(1 / (k + rank_i(d))) for each ranking i.
k=60 is standard (Cormack et al., 2009).
"""
from __future__ import annotations

import asyncpg

from app.db.database import get_pool
from app.services.embedder import embed_query

RRF_K = 60
TOP_N = 20   # candidates per method before RRF
FINAL_K = 5  # results returned to the caller


async def hybrid_search(
    query: str,
    pool: asyncpg.Pool | None = None,
    top_k: int = FINAL_K,
) -> list[dict]:
    """
    Retrieve the top-k chunks most relevant to the query using RRF over:
    - cosine vector search (pgvector)
    - full-text BM25-ish search (tsvector + tsrank)

    Returns list of dicts: {chunk_id, notice_id, text, rrf_score}
    """
    if pool is None:
        pool = await get_pool()

    q_embedding = embed_query(query)
    q_embedding_str = str(q_embedding)

    async with pool.acquire() as conn:
        # 1. Vector search
        vector_rows = await conn.fetch(
            """
            SELECT id, notice_id, text,
                   1 - (embedding <=> $1::vector) AS score
            FROM chunks
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> $1::vector
            LIMIT $2
            """,
            q_embedding_str,
            TOP_N,
        )

        # 2. Full-text search
        fts_rows = await conn.fetch(
            """
            SELECT id, notice_id, text,
                   ts_rank(tsvector, plainto_tsquery('english', $1)) AS score
            FROM chunks
            WHERE tsvector @@ plainto_tsquery('english', $1)
            ORDER BY score DESC
            LIMIT $2
            """,
            query,
            TOP_N,
        )

    # Build rank maps
    vector_rank: dict[str, int] = {r["id"]: i + 1 for i, r in enumerate(vector_rows)}
    fts_rank: dict[str, int] = {r["id"]: i + 1 for i, r in enumerate(fts_rows)}

    # All candidate chunk IDs
    all_ids = set(vector_rank) | set(fts_rank)

    # RRF scoring
    rrf_scores: dict[str, float] = {}
    chunk_meta: dict[str, dict] = {}

    for row in list(vector_rows) + list(fts_rows):
        cid = row["id"]
        chunk_meta[cid] = {"chunk_id": cid, "notice_id": row["notice_id"], "text": row["text"]}

    for cid in all_ids:
        score = 0.0
        if cid in vector_rank:
            score += 1.0 / (RRF_K + vector_rank[cid])
        if cid in fts_rank:
            score += 1.0 / (RRF_K + fts_rank[cid])
        rrf_scores[cid] = score

    # Sort and return top_k
    ranked = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    return [
        {**chunk_meta[cid], "rrf_score": score}
        for cid, score in ranked
        if cid in chunk_meta
    ]
