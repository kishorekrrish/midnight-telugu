"""Reusable ffmpeg/ffprobe helpers."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from workers.production_models import MediaInfo


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def ffprobe_available() -> bool:
    return shutil.which("ffprobe") is not None


def _fps(value: str | None) -> float | None:
    if not value or value == "0/0":
        return None
    if "/" in value:
        num, den = value.split("/", 1)
        try:
            return float(num) / float(den)
        except (ValueError, ZeroDivisionError):
            return None
    try:
        return float(value)
    except ValueError:
        return None


def probe_media(path: Path) -> MediaInfo:
    if not path.exists():
        raise FileNotFoundError(path)
    if not ffprobe_available():
        return MediaInfo(path=str(path), warnings=["ffprobe is not installed; metadata unavailable."])

    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels",
        "-of",
        "json",
        str(path),
    ]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    raw = json.loads(result.stdout or "{}")
    info = MediaInfo(path=str(path))
    try:
        info.duration_seconds = float(raw.get("format", {}).get("duration"))
    except (TypeError, ValueError):
        info.duration_seconds = None

    for stream in raw.get("streams", []):
        codec_type = stream.get("codec_type")
        if codec_type == "video" and not info.has_video:
            info.has_video = True
            info.codec = stream.get("codec_name") or info.codec
            info.width = stream.get("width")
            info.height = stream.get("height")
            info.fps = _fps(stream.get("r_frame_rate"))
        elif codec_type == "audio" and not info.has_audio:
            info.has_audio = True
            info.codec = stream.get("codec_name") or info.codec
            try:
                info.sample_rate = int(stream["sample_rate"])
            except (KeyError, TypeError, ValueError):
                info.sample_rate = None
            info.channels = stream.get("channels")
    return info


def get_duration(path: Path) -> float:
    info = probe_media(path)
    if info.duration_seconds is None:
        raise RuntimeError(f"Could not determine duration for {path}")
    return info.duration_seconds


def convert_to_wav_48k_mono(source: Path, target: Path) -> bool:
    if not ffmpeg_available():
        return False
    cmd = ["ffmpeg", "-y", "-i", str(source), "-ar", "48000", "-ac", "1", str(target)]
    subprocess.run(cmd, check=True, capture_output=True)
    return True
