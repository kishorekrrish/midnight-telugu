"""TTS provider base types."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TTSRequest:
    text: str
    voice_id: str
    model: str
    output_format: str = "wav"
    speed: float = 0.92
    voice_direction: str = ""
