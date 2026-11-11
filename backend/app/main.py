"""
Main FastAPI application.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api import chat, deadlines, drives, ingest
from app.core.config import settings
from app.db.database import close_db, init_db

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title="Placement Copilot API",
    description="RAG-powered Q&A over synthetic placement notices",
    version="0.1.0",
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — locked to configured origins; never wildcard in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# Routers
app.include_router(ingest.router, prefix="/api/v1")
app.include_router(drives.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(deadlines.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
