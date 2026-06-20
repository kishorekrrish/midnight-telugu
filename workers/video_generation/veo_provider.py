"""Official Gemini/Veo API provider wrapper."""

from __future__ import annotations

import os
import time
from pathlib import Path


class VeoProvider:
    """Thin placeholder for official Veo API calls.

    The pipeline intentionally does not automate browser UIs. Network calls are kept behind this
    provider so dry-run and manual import remain useful without fake generated videos.
    """

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is required for automated Veo clip generation.")

    def generate_clip(self, prompt: str, output_path: Path, model: str, aspect_ratio: str, resolution: str) -> str:
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise RuntimeError(
                "The official google-genai SDK is required for automated Veo generation. "
                "Install project dependencies or use --dry-run/import-clips."
            ) from exc

        client = genai.Client(api_key=self.api_key)
        operation = client.models.generate_videos(
            model=model,
            prompt=prompt,
            config=types.GenerateVideosConfig(
                aspect_ratio=aspect_ratio,
                number_of_videos=int(os.environ.get("VEO_NUMBER_OF_VIDEOS", "1")),
                resolution=resolution,
            ),
        )
        operation_name = getattr(operation, "name", "")
        poll_interval = float(os.environ.get("VEO_POLL_INTERVAL_SECONDS", "10"))
        max_wait = float(os.environ.get("VEO_MAX_WAIT_SECONDS", "900"))
        waited = 0.0
        while not getattr(operation, "done", False):
            if waited >= max_wait:
                raise TimeoutError(f"Veo operation timed out after {max_wait} seconds: {operation_name}")
            time.sleep(poll_interval)
            waited += poll_interval
            operation = client.operations.get(operation)

        response = getattr(operation, "response", None)
        videos = getattr(response, "generated_videos", None) if response else None
        if not videos:
            raise RuntimeError(f"Veo operation completed without generated videos: {operation_name}")
        video = videos[0].video
        client.files.download(file=video)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        video.save(str(output_path))
        return operation_name
