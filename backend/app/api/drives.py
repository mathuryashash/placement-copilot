"""Drives listing and eligibility API."""
from __future__ import annotations

import json
from datetime import UTC

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db.database import get_pool
from app.models.drive import Drive, EligibilityResult, StudentProfile
from app.services.eligibility import check_eligibility

router = APIRouter(tags=["drives"])


@router.get("/drives", response_model=list[dict])
async def list_drives(
    company: str | None = None,
    closing_in_days: int | None = None,
):
    """List all drives with optional filters."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, company, role, data FROM drives ORDER BY updated_at DESC LIMIT 100"
        )

    result = []
    from datetime import datetime, timedelta, timezone
    ist = timezone(timedelta(hours=5, minutes=30))
    now = datetime.now(tz=UTC)

    for row in rows:
        data = row["data"] if isinstance(row["data"], dict) else json.loads(row["data"])
        if company and company.lower() not in row["company"].lower():
            continue
        if closing_in_days is not None:
            dl_str = data.get("registration_deadline")
            if not dl_str:
                continue
            try:
                dl = datetime.fromisoformat(dl_str)
                if dl.tzinfo is None:
                    dl = dl.replace(tzinfo=ist)
                days_left = (dl.astimezone(UTC) - now).days
                if days_left < 0 or days_left > closing_in_days:
                    continue
            except (ValueError, TypeError):
                continue
        result.append({"id": row["id"], "company": row["company"], "role": row["role"], **data})

    return result


@router.get("/drives/{drive_id}", response_model=dict)
async def get_drive(drive_id: str):
    """Get a single drive by ID."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, company, role, data FROM drives WHERE id = $1", drive_id
        )
    if not row:
        raise HTTPException(status_code=404, detail="Drive not found")
    data = row["data"] if isinstance(row["data"], dict) else json.loads(row["data"])
    return {"id": row["id"], "company": row["company"], "role": row["role"], **data}


class EligibilityRequest(BaseModel):
    profile: StudentProfile


@router.post("/drives/{drive_id}/eligibility", response_model=EligibilityResult)
async def check_drive_eligibility(drive_id: str, req: EligibilityRequest):
    """
    Check if a student is eligible for a drive.
    The student profile is NOT stored server-side; it is used only for this request.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT data FROM drives WHERE id = $1", drive_id
        )
    if not row:
        raise HTTPException(status_code=404, detail="Drive not found")

    data = row["data"] if isinstance(row["data"], dict) else json.loads(row["data"])
    drive = Drive(**data)
    return check_eligibility(req.profile, drive)
