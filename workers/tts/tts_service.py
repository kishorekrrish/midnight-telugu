"""Voice-over orchestration."""

from __future__ import annotations

import os
from pathlib import Path

from workers.media.ffmpeg_utils import probe_media
from workers.production_models import ProviderNotImplementedError, now_iso
from workers.tts.base import TTSRequest
from workers.tts.elevenlabs_provider import ElevenLabsProvider

DEFAULT_VOICE_DIRECTION = (
    "Mature Indian male Telugu narrator. Calm, intimate, restrained suspense. "
    "Natural Telugu pronunciation. Avoid exaggerated horror or movie-trailer delivery. "
    "Slow down slightly for the final reveal. Do not translate or paraphrase the Telugu script."
)


def generate_voiceover(
    text: str,
    output_path: Path,
    provider_name: str,
    voice_id: str | None,
    model: str | None,
    dry_run: bool = False,
) -> dict:
    provider_name = provider_name or os.environ.get("TTS_PROVIDER", "elevenlabs")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    voice_id = voice_id or os.environ.get("ELEVENLABS_VOICE_ID", "")
    model = model or os.environ.get("ELEVENLABS_MODEL", "eleven_v3")
    direction = DEFAULT_VOICE_DIRECTION

    if provider_name != "elevenlabs":
        raise ProviderNotImplementedError(f"TTS provider '{provider_name}' is not implemented.")
    if dry_run:
        return {
            "provider": provider_name,
            "model": model,
            "voice_id": voice_id,
            "output_path": str(output_path),
            "created_at": now_iso(),
            "status": "dry_run",
            "voice_direction": direction,
            "text_preview": text[:240],
        }
    if not voice_id:
        raise RuntimeError("ELEVENLABS_VOICE_ID or --voice-id is required.")

    request = TTSRequest(
        text=text,
        voice_id=voice_id,
        model=model,
        output_format=os.environ.get("TTS_OUTPUT_FORMAT", "wav"),
        speed=float(os.environ.get("ELEVENLABS_SPEED", "0.92")),
        voice_direction=direction,
    )
    ElevenLabsProvider().synthesize(request, output_path)
    info = probe_media(output_path)
    return {
        "provider": provider_name,
        "model": model,
        "voice_id": voice_id,
        "output_path": str(output_path),
        "duration_seconds": info.duration_seconds,
        "sample_rate": info.sample_rate,
        "channels": info.channels,
        "codec": info.codec,
        "created_at": now_iso(),
        "status": "success",
        "voice_direction": direction,
    }
