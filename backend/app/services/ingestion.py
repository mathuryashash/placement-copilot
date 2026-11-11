"""
Ingestion pipeline: file/text -> parse -> chunk -> embed -> store in Postgres.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import asyncpg

from app.db.database import get_pool
from app.services.embedder import embed_texts
from app.services.parser import chunk_text, parse_file, parse_text


def _notice_id(source_path: str, text: str) -> str:
    """Deterministic ID: hash of source path + first 500 chars of text."""
    key = f"{source_path}:{text[:500]}"
    return "notice_" + hashlib.sha256(key.encode()).hexdigest()[:16]


async def ingest_text(
    text: str,
    source_name: str = "pasted",
    pool: asyncpg.Pool | None = None,
) -> str:
    """Ingest plain text. Returns notice_id."""
    if pool is None:
        pool = await get_pool()

    cleaned = parse_text(text)
    notice_id = _notice_id(source_name, cleaned)

    async with pool.acquire() as conn:
        # Upsert notice
        await conn.execute(
            """
            INSERT INTO notices (id, source_path, raw_text)
            VALUES ($1, $2, $3)
            ON CONFLICT (id) DO UPDATE SET raw_text = EXCLUDED.raw_text
            """,
            notice_id,
            source_name,
            cleaned,
        )

        # Delete old chunks (re-ingest)
        await conn.execute("DELETE FROM chunks WHERE notice_id = $1", notice_id)

        # Chunk + embed
        chunks = chunk_text(cleaned)
        if not chunks:
            return notice_id

        embeddings = embed_texts(chunks)

        # Batch insert
        rows = [
            (
                f"{notice_id}_chunk_{i}",
                notice_id,
                i,
                chunk,
                str(emb),  # asyncpg requires string for vector type
            )
            for i, (chunk, emb) in enumerate(zip(chunks, embeddings))
        ]
        await conn.executemany(
            """
            INSERT INTO chunks (id, notice_id, chunk_index, text, embedding)
            VALUES ($1, $2, $3, $4, $5::vector)
            ON CONFLICT (id) DO UPDATE
                SET text = EXCLUDED.text, embedding = EXCLUDED.embedding
            """,
            rows,
        )

    return notice_id


async def ingest_file(
    path: str | Path,
    data: bytes,
    pool: asyncpg.Pool | None = None,
) -> str:
    """Ingest a file (PDF, .eml, .txt). Returns notice_id."""
    text = parse_file(path, data)
    return await ingest_text(text, source_name=str(Path(path).name), pool=pool)
