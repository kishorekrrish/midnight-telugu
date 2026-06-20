"""Audio metadata helpers."""

from __future__ import annotations

from pathlib import Path

from workers.media.ffmpeg_utils import probe_media


def narration_metadata(path: Path) -> dict:
    info = probe_media(path)
    warnings = list(info.warnings)
    if path.suffix.lower() != ".wav":
        warnings.append("Narration is not WAV.")
    if info.sample_rate and info.sample_rate != 48000:
        warnings.append("Narration is not 48kHz.")
    if info.channels and info.channels != 1:
        warnings.append("Narration is not mono.")
    payload = info.model_dump()
    payload["warnings"] = warnings
    return payload
