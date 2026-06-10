"""Configuration loading from .env / environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).parent.parent


def _get(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


# Provider selection
DEFAULT_TEXT_PROVIDER: str = _get("DEFAULT_TEXT_PROVIDER", "mock")
DEFAULT_VOICE_PROVIDER: str = _get("DEFAULT_VOICE_PROVIDER", "mock")
DEFAULT_IMAGE_PROVIDER: str = _get("DEFAULT_IMAGE_PROVIDER", "mock")

# API keys (optional in v1)
OPENAI_API_KEY: str = _get("OPENAI_API_KEY")
ANTHROPIC_API_KEY: str = _get("ANTHROPIC_API_KEY")
GEMINI_API_KEY: str = _get("GEMINI_API_KEY")
ELEVENLABS_API_KEY: str = _get("ELEVENLABS_API_KEY")
IMAGE_PROVIDER_API_KEY: str = _get("IMAGE_PROVIDER_API_KEY")
VIDEO_PROVIDER_API_KEY: str = _get("VIDEO_PROVIDER_API_KEY")

# Video output settings
OUTPUT_VIDEO_WIDTH: int = int(_get("OUTPUT_VIDEO_WIDTH", "1080"))
OUTPUT_VIDEO_HEIGHT: int = int(_get("OUTPUT_VIDEO_HEIGHT", "1920"))
OUTPUT_VIDEO_FPS: int = int(_get("OUTPUT_VIDEO_FPS", "30"))

# Audio/Language
DEFAULT_LANGUAGE: str = _get("DEFAULT_LANGUAGE", "te-IN")
BACKGROUND_MUSIC_PATH: str = _get("BACKGROUND_MUSIC_PATH", "")

# Directories
CONTENT_DIR = ROOT / "content"
IDEAS_DIR = CONTENT_DIR / "ideas"
SCRIPTS_DIR = CONTENT_DIR / "scripts"
SCENES_DIR = CONTENT_DIR / "scenes"
REVIEW_DIR = CONTENT_DIR / "review"
APPROVED_DIR = CONTENT_DIR / "approved"
PUBLISHED_DIR = CONTENT_DIR / "published"

ASSETS_DIR = ROOT / "assets"
OUTPUTS_DIR = ROOT / "outputs"
ANALYTICS_DIR = ROOT / "analytics"

AUDIO_OUT_DIR = OUTPUTS_DIR / "audio"
IMAGES_OUT_DIR = OUTPUTS_DIR / "images"
VIDEOS_OUT_DIR = OUTPUTS_DIR / "videos"
THUMBNAILS_OUT_DIR = OUTPUTS_DIR / "thumbnails"

ALL_DIRS = [
    IDEAS_DIR, SCRIPTS_DIR, SCENES_DIR, REVIEW_DIR, APPROVED_DIR, PUBLISHED_DIR,
    ASSETS_DIR / "music", ASSETS_DIR / "sfx", ASSETS_DIR / "fonts", ASSETS_DIR / "brand",
    AUDIO_OUT_DIR, IMAGES_OUT_DIR, VIDEOS_OUT_DIR, THUMBNAILS_OUT_DIR,
    ANALYTICS_DIR,
]

VIDEOS_CSV = ANALYTICS_DIR / "videos.csv"
PERFORMANCE_CSV = ANALYTICS_DIR / "performance.csv"

VIDEOS_CSV_HEADERS = [
    "video_id", "title", "category", "hook_type", "duration_seconds",
    "status", "created_at", "published_at", "notes",
]

PERFORMANCE_CSV_HEADERS = [
    "video_id", "date", "views", "likes", "comments", "shares",
    "average_view_duration", "retention_percentage", "subscribers_gained", "notes",
]
