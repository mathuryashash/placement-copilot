"""Deadlines API: upcoming deadlines + .ics export."""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import Response

from app.services.deadlines import build_ics, get_upcoming_deadlines

router = APIRouter(tags=["deadlines"])


@router.get("/deadlines")
async def list_deadlines(days_ahead: int = 30):
    """List upcoming registration deadlines."""
    deadlines = await get_upcoming_deadlines(days_ahead=days_ahead)
    return deadlines


@router.get("/deadlines/calendar.ics")
async def deadlines_ics(days_ahead: int = 30):
    """Download upcoming deadlines as a .ics calendar file."""
    deadlines = await get_upcoming_deadlines(days_ahead=days_ahead)
    ics_data = build_ics(deadlines)
    return Response(
        content=ics_data,
        media_type="text/calendar",
        headers={"Content-Disposition": "attachment; filename=placement-deadlines.ics"},
    )
