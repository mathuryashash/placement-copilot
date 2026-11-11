"""
LLM client with Groq primary, Gemini fallback, disk-based response cache,
and a deterministic fake mode for tests.

Cache key: SHA-256(model + sorted messages JSON).  Response stored as JSON.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from app.core.config import settings


def _cache_path(key: str) -> Path:
    cache_dir = Path(settings.llm_cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"{key}.json"


def _cache_key(model: str, messages: list[dict]) -> str:
    payload = json.dumps({"model": model, "messages": messages}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def _load_cache(key: str) -> dict | None:
    p = _cache_path(key)
    if p.exists():
        return json.loads(p.read_text())
    return None


def _save_cache(key: str, response: dict) -> None:
    _cache_path(key).write_text(json.dumps(response))


# --- Fake / stub LLM for tests ------------------------------------------------

FAKE_DRIVE_JSON = {
    "company": "AcmeCorp",
    "role": "Software Engineer",
    "ctc_lpa": 12.0,
    "stipend_pm": None,
    "locations": ["Bengaluru"],
    "eligibility": {
        "min_cgpa": 7.0,
        "allowed_branches": ["CSE", "ISE", "ECE"],
        "max_backlogs": 0,
        "grad_years": [2025, 2026],
        "extra_notes": "",
    },
    "registration_deadline": "2025-02-28T23:59:00+05:30",
    "test_date": "2025-03-05T10:00:00+05:30",
    "rounds": [
        {"name": "Online Test", "description": "Aptitude + Coding", "date_hint": "5 March"},
        {"name": "Technical Interview", "description": "DSA + System Design", "date_hint": ""},
        {"name": "HR", "description": "", "date_hint": ""},
    ],
    "links": ["https://acmecorp.example.com/careers/apply"],
}


def fake_llm_call(messages: list[dict], context: str = "") -> str:
    """
    Return a deterministic stub response for tests.
    Routes based on message content and can refuse when context is empty.
    """
    # Look for a "user" message that asks for JSON extraction
    for msg in messages:
        if msg.get("role") == "user" and "extract" in msg.get("content", "").lower():
            return json.dumps(FAKE_DRIVE_JSON)

    # Check if context is empty (no relevant corpus results)
    # This makes the refusal behavior testable
    if "[notice:" not in context and "[NOTICE:" not in context:
        return "I don't have that information in the placement notices I have."

    # Default: a generic answer using context
    return "Based on the placement notices in the corpus, I can answer your question."


# --- Real LLM calls -----------------------------------------------------------

def _call_groq(messages: list[dict], max_tokens: int = 1024) -> str:
    import groq  # type: ignore
    client = groq.Groq(api_key=settings.groq_api_key)
    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,  # type: ignore
        max_tokens=max_tokens,
        temperature=0.0,
    )
    return resp.choices[0].message.content or ""


def _call_gemini(messages: list[dict], max_tokens: int = 1024) -> str:
    import google.generativeai as genai  # type: ignore
    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    # Convert OpenAI-style messages to a single prompt
    prompt = "\n\n".join(
        f"[{m['role'].upper()}]: {m['content']}" for m in messages
    )
    resp = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            max_output_tokens=max_tokens, temperature=0.0
        ),
    )
    return resp.text


def call_llm(
    messages: list[dict],
    max_tokens: int = 1024,
    use_cache: bool = True,
    context: str = "",
) -> str:
    """
    Call LLM: fake mode -> Groq -> Gemini fallback.
    Responses are cached to disk to stay within the 300-call eval budget.
    context: optional context string for fake mode to detect refusal scenarios
    """
    if settings.fake_llm:
        return fake_llm_call(messages, context=context)

    cache_key = _cache_key("llm", messages)
    if use_cache:
        cached = _load_cache(cache_key)
        if cached:
            return cached["response"]

    # Try Groq first
    response = ""
    for attempt in range(2):
        try:
            response = _call_groq(messages, max_tokens=max_tokens)
            break
        except Exception as exc:
            if "429" in str(exc) or "rate" in str(exc).lower():
                time.sleep(2 ** attempt)
            else:
                # Fall through to Gemini
                break
    else:
        # Exhausted retries on Groq
        pass

    if not response and settings.gemini_api_key:
        try:
            response = _call_gemini(messages, max_tokens=max_tokens)
        except Exception:
            pass

    if not response:
        raise RuntimeError("All LLM providers failed or no keys configured")

    if use_cache:
        _save_cache(cache_key, {"response": response})
    return response
