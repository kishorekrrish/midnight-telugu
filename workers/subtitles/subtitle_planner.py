"""Simple deterministic subtitle cue planner."""

from __future__ import annotations

import re


def split_telugu_cues(text: str, duration_seconds: float) -> list[dict]:
    sentences = [s.strip() for s in re.split(r"(?<=[.!?।])\s+|\n+", text) if s.strip()]
    if not sentences:
        sentences = [text.strip()]
    cues: list[str] = []
    for sentence in sentences:
        words = sentence.split()
        chunk: list[str] = []
        for word in words:
            chunk.append(word)
            if len(chunk) >= 7:
                cues.append(" ".join(chunk))
                chunk = []
        if chunk:
            cues.append(" ".join(chunk))
    cue_count = max(1, len(cues))
    per = duration_seconds / cue_count
    planned = []
    for idx, cue in enumerate(cues):
        start = round(idx * per, 2)
        end = round(duration_seconds if idx == cue_count - 1 else (idx + 1) * per, 2)
        planned.append({"start": start, "end": end, "text": cue})
    return planned
