"""Models for the clip-based production pipeline."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


class ProviderNotImplementedError(RuntimeError):
    """Raised when a requested production provider is not implemented."""


class MediaInfo(BaseModel):
    path: str
    duration_seconds: float | None = None
    sample_rate: int | None = None
    channels: int | None = None
    codec: str | None = None
    width: int | None = None
    height: int | None = None
    fps: float | None = None
    has_video: bool = False
    has_audio: bool = False
    warnings: list[str] = Field(default_factory=list)


class ScriptApproval(BaseModel):
    story_slug: str
    script_path: str
    approved: bool
    approved_by: str = "Kishore"
    approved_at: str
    notes: str = ""
    script_version: str


class SceneShot(BaseModel):
    shot_id: str
    scene_number: int
    start_seconds: float
    end_seconds: float
    duration_seconds: float
    narration_text: str
    clip_filename: str
    visual_prompt: str
    camera_notes: str
    subtitle_text: str


class SceneManifest(BaseModel):
    story_slug: str
    title: str
    total_duration_seconds: float
    shots: list[SceneShot]
    global_style: str
    negative_prompt: str
    character_bible_path: str
    location_bible_path: str
    created_at: str = Field(default_factory=now_iso)


class RenderPlan(BaseModel):
    output_path: str
    ffmpeg_command: list[str]
    dry_run: bool = False
    warnings: list[str] = Field(default_factory=list)


def relative_to_cwd(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)
