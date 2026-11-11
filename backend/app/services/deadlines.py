"""
Deadlines service: upcoming deadlines and .ics export.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta, timezone

import asyncpg
from icalendar import Calendar, Event

from app.db.database import get_pool

IST = timezone(timedelta(hours=5, minutes=30))


async def get_upcoming_deadlines(
    days_ahead: int = 30,
    pool: asyncpg.Pool | None = None,
) -> list[dict]:
    """Return drives with registration deadlines in the next `days_ahead` days."""
    if pool is None:
        pool = await get_pool()

    now = datetime.now(tz=UTC)
    cutoff = now + timedelta(days=days_ahead)

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, company, role, data
            FROM drives
            WHERE (data->>'registration_deadline') IS NOT NULL
            ORDER BY data->>'registration_deadline' ASC
            """
        )

    results = []
    for row in rows:
        data = row["data"] if isinstance(row["data"], dict) else json.loads(row["data"])
        dl_str = data.get("registration_deadline")
        if not dl_str:
            continue
        try:
            dl = datetime.fromisoformat(dl_str)
            if dl.tzinfo is None:
                dl = dl.replace(tzinfo=IST)
            dl_utc = dl.astimezone(UTC)
            if now <= dl_utc <= cutoff:
                results.append({
                    "drive_id": row["id"],
                    "company": row["company"],
                    "role": row["role"],
                    "deadline": dl.isoformat(),
                    "days_left": (dl_utc - now).days,
                })
        except (ValueError, TypeError):
            continue

    return results


def build_ics(deadlines: list[dict]) -> bytes:
    """Build an iCalendar (.ics) file from a list of deadline dicts."""
    cal = Calendar()
    cal.add("prodid", "-//Placement Copilot//placement-copilot//EN")
    cal.add("version", "2.0")

    for dl in deadlines:
        event = Event()
        event.add("summary", f"[Placement] {dl['company']} – {dl['role']} deadline")
        try:
            dt = datetime.fromisoformat(dl["deadline"])
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=IST)
        except (ValueError, KeyError):
            continue
        event.add("dtstart", dt.date())  # all-day event
        event.add("dtend", dt.date())
        event.add("description", f"Registration deadline for {dl['company']} – {dl['role']}")
        cal.add_component(event)

    return cal.to_ical()
