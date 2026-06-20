"""ElevenLabs text-to-speech provider."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from workers.media.ffmpeg_utils import convert_to_wav_48k_mono
from workers.production_models import ProviderNotImplementedError
from workers.tts.base import TTSRequest


class ElevenLabsProvider:
    name = "elevenlabs"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("ELEVENLABS_API_KEY", "")
        if not self.api_key:
            raise RuntimeError("ELEVENLABS_API_KEY is required for ElevenLabs voice-over generation.")

    def synthesize(self, request: TTSRequest, output_path: Path) -> None:
        if request.output_format != "wav":
            raise ProviderNotImplementedError("Only WAV output is supported by this pipeline.")
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{request.voice_id}?output_format=mp3_44100_128"
        payload = json.dumps(
            {
                "text": request.text,
                "model_id": request.model,
                "voice_settings": {
                    "stability": float(os.environ.get("ELEVENLABS_STABILITY", "0.45")),
                    "similarity_boost": float(os.environ.get("ELEVENLABS_SIMILARITY_BOOST", "0.75")),
                    "style": float(os.environ.get("ELEVENLABS_STYLE", "0.2")),
                    "speed": request.speed,
                },
            },
            ensure_ascii=False,
        ).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"xi-api-key": self.api_key, "Content-Type": "application/json"},
            method="POST",
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = output_path.with_suffix(".elevenlabs.mp3")
        try:
            with urllib.request.urlopen(req, timeout=180) as response:
                temp_path.write_bytes(response.read())
        except urllib.error.URLError as exc:
            raise RuntimeError(f"ElevenLabs request failed: {exc}") from exc
        try:
            if not convert_to_wav_48k_mono(temp_path, output_path):
                raise RuntimeError("ffmpeg is required to convert ElevenLabs audio to 48kHz mono WAV.")
        finally:
            temp_path.unlink(missing_ok=True)
