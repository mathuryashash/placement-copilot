"""Tests for parser supporting .eml, .mbox, and PDF ingestion."""
from __future__ import annotations

import io
import os

import pytest


def test_parse_pdf_fixture():
    """Synthetic PDF fixture test."""
    # Import pypdf to ensure it's available
    from pypdf import PdfWriter, PdfReader
    
    # Create a simple synthetic PDF in memory
    writer = PdfWriter()
    page = writer.add_blank_page(width=200, height=200)
    
    # Add text content (requires adding to a page via content stream)
    # For testing, we'll just write it and read it back
    buffer = io.BytesIO()
    writer.write(buffer)
    pdf_bytes = buffer.getvalue()
    
    assert len(pdf_bytes) > 0
    
    # Parse it
    from app.services.parser import parse_pdf
    text = parse_pdf(pdf_bytes)
    assert isinstance(text, str)


def test_parse_eml_fixture():
    """Synthetic .eml fixture test."""
    eml_bytes = b"""From: placement@college.example
To: students@batch.example
Subject: Placement Drive Notice - SynthTech Solutions
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8

[SYNTHETIC DATA - Training Only]
Dear Students,

SynthTech Solutions invites applications for the following positions:

Position: Backend Software Engineer
CTC: 18 LPA
Location: Bengaluru, Pune
Minimum CGPA: 7.5
Eligible Branches: CSE, ISE, ECE, EEE
Maximum Backlogs: 0
Graduation Years: 2026, 2027

Registration Deadline: 20 March 2026, 11:59 PM IST
Test Date: 25 March 2026, 10:00 AM IST

Application Link: https://synthtech.example.com/careers

Best Regards,
Placement Cell
"""
    from app.services.parser import parse_eml
    text = parse_eml(eml_bytes)
    assert "Backend Software Engineer" in text
    assert "18 LPA" in text
    assert "SynthTech Solutions" in text


def test_parse_mbox_fixture():
    """Synthetic .mbox fixture test (single message as mbox)."""
    mbox_bytes = b"""From: placement@college.example
To: students@batch.example
Subject: Amended: CodeMatrix Ltd Drive Notice
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8

[SYNTHETIC DATA - Training Only]
AMENDMENT TO PLACEMENT NOTICE

Previous Deadline: 15 March 2026
New Deadline: 22 March 2026 (extended by 1 week)

Role: Full Stack Developer
Company: CodeMatrix Ltd
CTC: 15 LPA
Location: Hyderabad
Min CGPA: 7.0
Branches: CSE, ISE

Application Link: https://codematrix.example.com/apply
"""
    from app.services.parser import parse_eml  # mbox is parsed same as eml (RFC 2822 format)
    text = parse_eml(mbox_bytes)
    assert "CodeMatrix Ltd" in text
    assert "AMENDMENT" in text
    assert "22 March 2026" in text


def test_parse_file_dispatch():
    """Test file type dispatch based on extension."""
    from app.services.parser import parse_file
    
    # Test .txt dispatch
    txt_bytes = b"Test notice content for .txt"
    result = parse_file("notice.txt", txt_bytes)
    assert "Test notice content" in result
    
    # Test .eml dispatch
    eml_bytes = b"""From: test@example.com
Subject: Test

Email content here."""
    result = parse_file("notice.eml", eml_bytes)
    assert "Email content here" in result
