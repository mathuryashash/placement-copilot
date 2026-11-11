"""pytest configuration and shared fixtures."""
from __future__ import annotations

import os
import sys

# Ensure backend is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Force fake LLM mode for all tests
os.environ["FAKE_LLM"] = "true"
os.environ["DATABASE_URL"] = "postgresql+psycopg://copilot:copilot@localhost:18401/placement_copilot"
