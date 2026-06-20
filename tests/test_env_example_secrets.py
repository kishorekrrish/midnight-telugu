"""Guards against committing real credentials in example env files."""

from __future__ import annotations

import re
from pathlib import Path


def test_env_example_does_not_contain_api_key_values():
    content = Path(".env.example").read_text(encoding="utf-8")
    secret_patterns = [
        r"OPENAI_API_KEY=sk-[A-Za-z0-9_-]+",
        r"ELEVENLABS_API_KEY=sk_[A-Za-z0-9]+",
        r"GEMINI_API_KEY=AIza[A-Za-z0-9_-]+",
    ]
    for pattern in secret_patterns:
        assert not re.search(pattern, content)
