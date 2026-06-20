"""Music/ambience config helpers."""

from __future__ import annotations

import json
from pathlib import Path


def load_music_mix(story_dir: Path) -> dict | None:
    path = story_dir / "music_mix.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
