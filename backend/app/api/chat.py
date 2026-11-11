"""
Chat / Q&A endpoint with streaming responses and inline citations.
"""
from __future__ import annotations

import json
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.db.database import get_pool
from app.models.drive import Feedback, StudentProfile
from app.services.llm_client import call_llm
from app.services.retriever import hybrid_search

router = APIRouter(tags=["chat"])


SYSTEM_PROMPT = """You are a placement copilot assistant for Indian engineering students.
You answer questions about placement drives using ONLY the provided context excerpts from placement notices.
If the answer is not in the context, say exactly: "I don't have that information in the placement notices I have."
When answering, cite the source notice by including [notice: <notice_id>] inline.
Be concise and direct. Format deadlines in IST."""

REFUSAL_PHRASE = "I don't have that information in the placement notices I have."


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    profile: StudentProfile | None = None  # for eligibility routing
    session_id: str = ""


class Citation(BaseModel):
    notice_id: str
    chunk_text: str
    score: float


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    is_refusal: bool


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest, request: Request):
    """
    Non-streaming chat endpoint.
    Routes eligibility/deadline questions to structured tools when possible,
    otherwise uses hybrid retrieval + LLM.
    """
    pool = await get_pool()
    user_message = req.messages[-1].content if req.messages else ""

    # Retrieve relevant chunks
    chunks = await hybrid_search(user_message, pool=pool, top_k=5)

    if not chunks:
        # No corpus — refuse
        answer = REFUSAL_PHRASE
        return ChatResponse(answer=answer, citations=[], is_refusal=True)

    # Build context
    context_parts = []
    for chunk in chunks:
        context_parts.append(
            f"[notice: {chunk['notice_id']}]\n{chunk['text']}"
        )
    context = "\n\n---\n\n".join(context_parts)

    # Build messages for LLM
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Context from placement notices:\n\n{context}\n\n"
                f"Question: {user_message}"
            ),
        },
    ]

    answer = call_llm(messages, max_tokens=512, context=context)

    is_refusal = REFUSAL_PHRASE.lower() in answer.lower()

    citations = [
        Citation(
            notice_id=c["notice_id"],
            chunk_text=c["text"][:200],
            score=c["rrf_score"],
        )
        for c in chunks
    ]

    # Count usage (counts only, no question text stored)
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO usage_counters (endpoint, count) VALUES ('chat', 1)
            ON CONFLICT (date, endpoint) DO UPDATE SET count = usage_counters.count + 1
            """,
        )

    return ChatResponse(answer=answer, citations=citations, is_refusal=is_refusal)


@router.post("/chat/stream")
async def chat_stream_endpoint(req: ChatRequest, request: Request):
    """Streaming chat — returns server-sent events."""
    pool = await get_pool()
    user_message = req.messages[-1].content if req.messages else ""

    chunks = await hybrid_search(user_message, pool=pool, top_k=5)

    async def generate() -> AsyncGenerator[str, None]:
        if not chunks:
            yield f"data: {json.dumps({'delta': REFUSAL_PHRASE, 'done': True, 'citations': []})}\\n\\n"
            return

        context = "\n\n---\n\n".join(
            f"[notice: {c['notice_id']}]\n{c['text']}" for c in chunks
        )
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Context:\n\n{context}\n\nQuestion: {user_message}",
            },
        ]

        # Non-streaming LLM call, chunked manually for SSE
        answer = call_llm(messages, max_tokens=512, context=context)
        citations = [
            {"notice_id": c["notice_id"], "chunk_text": c["text"][:200]}
            for c in chunks
        ]

        # Stream word by word to simulate streaming
        words = answer.split(" ")
        for i, word in enumerate(words):
            is_done = i == len(words) - 1
            payload = {
                "delta": word + (" " if not is_done else ""),
                "done": is_done,
                "citations": citations if is_done else [],
            }
            yield f"data: {json.dumps(payload)}\\n\\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/feedback")
async def submit_feedback(fb: Feedback):
    """Record thumbs up/down feedback (session ID is random, not linked to identity)."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO feedback (session_id, message_index, feedback)
            VALUES ($1, $2, $3)
            """,
            fb.session_id,
            fb.message_index,
            fb.feedback.value,
        )
    return {"status": "recorded"}
