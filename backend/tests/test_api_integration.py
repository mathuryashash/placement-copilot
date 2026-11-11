"""
Integration tests: API endpoints with real Postgres/pgvector.
"""
from __future__ import annotations

import os

import httpx
import pytest
import pytest_asyncio

os.environ["FAKE_LLM"] = "true"

DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg://copilot:copilot@localhost:18401/placement_copilot",
)


@pytest.fixture(scope="session", autouse=True)
def set_db_url():
    os.environ.setdefault("DATABASE_URL", DB_URL)
    os.environ["FAKE_LLM"] = "true"


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def app_client(set_db_url):
    import importlib

    import app.core.config
    importlib.reload(app.core.config)

    from app.db import database as db_module
    importlib.reload(db_module)

    from app.db.database import init_db
    from app.main import app

    await init_db()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


NOTICE_TEXT = """
[SYNTHETIC DATA - Training/Demo Only]
Nexora Systems Campus Recruitment Drive
Role: Software Engineer
CTC: 15 LPA
Location: Bengaluru
Minimum CGPA: 7.5
Eligible Branches: CSE, ISE, ECE
Graduation Year: 2026
Max Backlogs: 0
Registration Deadline: 15 March 2026, 11:59 PM IST
Apply at: https://nexora.example.com/careers
"""


@pytest.mark.asyncio(loop_scope="session")
async def test_health(app_client):
    resp = await app_client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio(loop_scope="session")
async def test_ingest_text(app_client):
    resp = await app_client.post(
        "/api/v1/ingest/text",
        json={"text": NOTICE_TEXT, "source_name": "test_notice"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "notice_id" in data
    assert data["notice_id"].startswith("notice_")


@pytest.mark.asyncio(loop_scope="session")
async def test_chat_after_ingest(app_client):
    await app_client.post(
        "/api/v1/ingest/text",
        json={"text": NOTICE_TEXT, "source_name": "test_notice_2"},
    )
    resp = await app_client.post(
        "/api/v1/chat",
        json={
            "messages": [{"role": "user", "content": "What is the minimum CGPA for Nexora Systems?"}],
            "session_id": "test-session-001",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert "citations" in data


@pytest.mark.asyncio(loop_scope="session")
async def test_drives_list(app_client):
    resp = await app_client.get("/api/v1/drives")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio(loop_scope="session")
async def test_deadlines_list(app_client):
    resp = await app_client.get("/api/v1/deadlines")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio(loop_scope="session")
async def test_ingest_text_too_large(app_client):
    big_text = "x" * 200_000
    resp = await app_client.post(
        "/api/v1/ingest/text",
        json={"text": big_text, "source_name": "big"},
    )
    assert resp.status_code == 413


@pytest.mark.asyncio(loop_scope="session")
async def test_feedback_endpoint(app_client):
    resp = await app_client.post(
        "/api/v1/feedback",
        json={"session_id": "sess-abc", "message_index": 0, "feedback": "up"},
    )
    assert resp.status_code == 200


@pytest.mark.asyncio(loop_scope="session")
async def test_eligibility_drive_not_found(app_client):
    resp = await app_client.post(
        "/api/v1/drives/nonexistent_drive_id/eligibility",
        json={"profile": {"cgpa": 8.0, "branch": "CSE", "backlogs": 0, "grad_year": 2026}},
    )
    assert resp.status_code == 404
