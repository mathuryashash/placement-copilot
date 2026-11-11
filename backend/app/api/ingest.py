"""Ingestion API endpoint."""
from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from pydantic import BaseModel

from app.db.database import get_pool
from app.services.extractor import extract_drive
from app.services.ingestion import ingest_file, ingest_text

router = APIRouter(tags=["ingest"])

MAX_TEXT_BYTES = 100_000  # 100 KB limit for pasted text
MAX_FILE_BYTES = 5_000_000  # 5 MB limit for uploaded files


class IngestTextRequest(BaseModel):
    text: str
    source_name: str = "pasted"


class IngestResponse(BaseModel):
    notice_id: str
    drive_id: str | None = None
    message: str


@router.post("/ingest/text", response_model=IngestResponse)
async def ingest_text_endpoint(req: IngestTextRequest, request: Request):
    """Ingest pasted notice text."""
    if len(req.text.encode()) > MAX_TEXT_BYTES:
        raise HTTPException(status_code=413, detail="Text too large (max 100 KB)")

    pool = await get_pool()
    notice_id = await ingest_text(req.text, source_name=req.source_name, pool=pool)

    # Extract structured drive info
    drive = None
    drive_id = None
    try:
        drive = extract_drive(notice_id, req.text)
        # Persist drive
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO drives (id, company, role, data, notice_ids)
                VALUES ($1, $2, $3, $4::jsonb, $5)
                ON CONFLICT (id) DO UPDATE
                    SET data = EXCLUDED.data, updated_at = NOW()
                """,
                drive.id,
                drive.company,
                drive.role,
                drive.model_dump_json(),
                drive.notice_ids,
            )
        drive_id = drive.id
    except Exception:
        # Extraction failure is non-fatal; notice is still indexed
        pass

    # Increment usage counter (counts only)
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO usage_counters (endpoint, count) VALUES ('ingest', 1)
            ON CONFLICT (date, endpoint) DO UPDATE SET count = usage_counters.count + 1
            """,
        )

    return IngestResponse(
        notice_id=notice_id,
        drive_id=drive_id,
        message="Ingested and indexed successfully",
    )


@router.post("/ingest/file", response_model=IngestResponse)
async def ingest_file_endpoint(request: Request, file: UploadFile = File(...)):
    """Ingest a PDF or .eml file."""
    data = await file.read()
    if len(data) > MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 5 MB)")

    allowed_exts = {".pdf", ".eml", ".mbox", ".txt"}
    from pathlib import Path
    ext = Path(file.filename or "").suffix.lower()
    if ext not in allowed_exts:
        raise HTTPException(status_code=415, detail=f"Unsupported file type: {ext}")

    pool = await get_pool()
    notice_id = await ingest_file(file.filename or "upload", data, pool=pool)

    return IngestResponse(
        notice_id=notice_id,
        drive_id=None,
        message="File ingested and indexed successfully",
    )
