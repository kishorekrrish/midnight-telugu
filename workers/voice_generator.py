"""Voice generator — mock provider for v1; real providers pluggable later."""

from __future__ import annotations

import uuid
from pathlib import Path

from workers.config import AUDIO_OUT_DIR, DEFAULT_VOICE_PROVIDER
from workers.models import HumanizedScript, StoryScript, VoiceAsset


def generate_voice(
    script: HumanizedScript | StoryScript,
    provider: str | None = None,
    output_dir: Path | None = None,
) -> VoiceAsset:
    """Generate a voice asset for the script. Returns mock metadata in v1."""
    provider = provider or DEFAULT_VOICE_PROVIDER
    output_dir = output_dir or AUDIO_OUT_DIR

    if provider != "mock":
        import warnings
        warnings.warn(
            f"Voice provider '{provider}' not implemented in v1. Using mock.",
            stacklevel=2,
        )

    asset_id = f"voice_{uuid.uuid4().hex[:8]}"
    # In mock mode, we don't create a real audio file
    audio_path = str(output_dir / f"{asset_id}.mp3") if provider != "mock" else None

    return VoiceAsset(
        id=asset_id,
        script_id=script.id,
        provider=provider,
        language="te-IN",
        audio_path=audio_path,
        duration_seconds=float(script.estimated_duration_seconds),
    )
