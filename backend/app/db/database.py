"""Database connection and schema management."""
from __future__ import annotations

import asyncpg

from app.core.config import settings

# --- Schema DDL -----------------------------------------------------------

SCHEMA_SQL = """
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- for full-text similarity

CREATE TABLE IF NOT EXISTS notices (
    id          TEXT PRIMARY KEY,
    source_path TEXT NOT NULL,
    raw_text    TEXT NOT NULL,
    parsed_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    tsvector    TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', raw_text)) STORED
);
CREATE INDEX IF NOT EXISTS notices_fts ON notices USING GIN(tsvector);

CREATE TABLE IF NOT EXISTS chunks (
    id          TEXT PRIMARY KEY,
    notice_id   TEXT NOT NULL REFERENCES notices(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    text        TEXT NOT NULL,
    embedding   VECTOR(384),
    tsvector    TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', text)) STORED
);
CREATE INDEX IF NOT EXISTS chunks_embedding ON chunks USING hnsw(embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS chunks_fts       ON chunks USING GIN(tsvector);

CREATE TABLE IF NOT EXISTS drives (
    id              TEXT PRIMARY KEY,
    company         TEXT NOT NULL,
    role            TEXT NOT NULL,
    data            JSONB NOT NULL,
    notice_ids      TEXT[] NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS usage_counters (
    -- Privacy-preserving: counts only, no question text stored
    date            DATE NOT NULL DEFAULT CURRENT_DATE,
    endpoint        TEXT NOT NULL,
    count           INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (date, endpoint)
);

CREATE TABLE IF NOT EXISTS feedback (
    id              BIGSERIAL PRIMARY KEY,
    session_id      TEXT NOT NULL,  -- random client ID; not linked to identity
    message_index   INTEGER NOT NULL,
    feedback        TEXT NOT NULL CHECK (feedback IN ('up','down')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


_pool: asyncpg.Pool | None = None


def _dsn_to_asyncpg(url: str) -> str:
    """Convert SQLAlchemy-style URL to asyncpg DSN."""
    # postgresql+psycopg://... -> postgresql://...
    return url.replace("postgresql+psycopg://", "postgresql://")


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            _dsn_to_asyncpg(settings.database_url),
            min_size=2,
            max_size=10,
            command_timeout=30,
        )
    return _pool


async def init_db() -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(SCHEMA_SQL)


async def close_db() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
