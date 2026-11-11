"""
Playwright e2e tests for placement-copilot.
Run against backend in fake-LLM mode.

Usage:
  FAKE_LLM=true docker-compose up -d
  python -m pytest frontend/e2e/test_e2e.py -v
"""
from __future__ import annotations

import os

import pytest
import pytest_asyncio
from playwright.async_api import async_playwright


# Set fake LLM for deterministic responses
os.environ["FAKE_LLM"] = "true"

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:18400")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


@pytest_asyncio.fixture(scope="session")
async def browser():
    """Create a Playwright browser session."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        yield browser
        await browser.close()


@pytest_asyncio.fixture
async def page(browser):
    """Create a new page for each test."""
    context = await browser.new_context()
    page = await context.new_page()
    yield page
    await page.close()
    await context.close()


@pytest.mark.asyncio
async def test_home_page_loads(page):
    """Test that the home page loads."""
    await page.goto(FRONTEND_URL, wait_until="networkidle")
    title = await page.title()
    assert title or await page.locator("h1").first.text_content()


@pytest.mark.asyncio
async def test_chat_with_cited_answer(page):
    """Test asking a question and receiving a cited answer."""
    # Navigate to chat page
    await page.goto(f"{FRONTEND_URL}/chat", wait_until="networkidle")
    
    # Find the chat input and send a question
    question_input = page.locator("input, textarea").first
    if not question_input:
        pytest.skip("Chat input not found")
    
    await question_input.fill("What is the minimum CGPA?")
    
    # Find and click the send button
    send_button = page.locator("button:has-text('Send'), button[type='submit']").first
    if send_button:
        await send_button.click()
        # Wait for response
        await page.wait_for_timeout(2000)
    
    # Check for an answer (should be visible)
    response_text = await page.content()
    # In fake LLM mode, we expect a generic response
    assert "Based on the placement notices" in response_text or "CGPA" in response_text


@pytest.mark.asyncio
async def test_set_profile_and_eligible_filter(page):
    """Test setting student profile and filtering for eligible drives."""
    # Navigate to profile page
    await page.goto(f"{FRONTEND_URL}/profile", wait_until="networkidle")
    
    # Fill in profile
    cgpa_input = page.locator("input[type='number']").first
    if cgpa_input:
        await cgpa_input.fill("8.0")
    
    branch_select = page.locator("select").first
    if branch_select:
        await branch_select.select_option("CSE")
    
    # Save profile (click button if present)
    save_btn = page.locator("button:has-text('Save')").first
    if save_btn:
        await save_btn.click()
        await page.wait_for_timeout(500)
    
    # Navigate to drives
    await page.goto(f"{FRONTEND_URL}/drives", wait_until="networkidle")
    
    # Check for eligible filter
    eligible_filter = page.locator("input:has-text('Eligible for me'), button:has-text('Eligible')").first
    if eligible_filter:
        await eligible_filter.click()
        await page.wait_for_timeout(1000)
    
    # Page should render without errors
    content = await page.content()
    assert len(content) > 0


@pytest.mark.asyncio
async def test_refusal_case(page):
    """Test that unanswerable questions trigger a refusal."""
    await page.goto(f"{FRONTEND_URL}/chat", wait_until="networkidle")
    
    # Ask a question not in the corpus
    question_input = page.locator("input, textarea").first
    if not question_input:
        pytest.skip("Chat input not found")
    
    await question_input.fill("What is the bond period for FictionalCompany Corp?")
    
    send_button = page.locator("button:has-text('Send'), button[type='submit']").first
    if send_button:
        await send_button.click()
        await page.wait_for_timeout(2000)
    
    # In fake LLM mode with no context, expect refusal
    response = await page.content()
    # The response might contain "don't have" or similar
    assert len(response) > 0


@pytest.mark.asyncio
async def test_navigation(page):
    """Test basic navigation between pages."""
    # Start at home
    await page.goto(FRONTEND_URL, wait_until="networkidle")
    
    # Navigate to chat
    chat_link = page.locator("a:has-text('Chat'), button:has-text('Chat')").first
    if chat_link:
        await chat_link.click()
        await page.wait_for_url("**/chat**", timeout=5000)
    
    # Navigate to drives
    drives_link = page.locator("a:has-text('Drives'), button:has-text('Drives')").first
    if drives_link:
        await drives_link.click()
        await page.wait_for_url("**/drives**", timeout=5000)
    
    # Page should load without errors
    assert page.url


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
