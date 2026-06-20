"""Pytest configuration.

Tests always run in mock/test mode. Production defaults remain AI-backed.
"""

from __future__ import annotations

import os

os.environ.setdefault("MIDNIGHT_TELUGU_TEST_MODE", "1")
os.environ.setdefault("DEFAULT_TEXT_PROVIDER", "mock")
os.environ.setdefault("SCRIPT_DIRECTOR_PROVIDER", "mock")
