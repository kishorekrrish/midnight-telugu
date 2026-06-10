"""Video composer — FFmpeg-based composition layer with dry-run support."""

from __future__ import annotations

import shutil
import subprocess
import uuid
from pathlib import Path

from workers.config import (
    BACKGROUND_MUSIC_PATH,
    OUTPUT_VIDEO_FPS,
    OUTPUT_VIDEO_HEIGHT,
    OUTPUT_VIDEO_WIDTH,
    VIDEOS_OUT_DIR,
)
from workers.models import ImageAsset, ScenePlan, VideoDraft, VoiceAsset


def _ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def _build_ffmpeg_command(
    image_paths: list[str],
    audio_path: str | None,
    output_path: str,
    width: int,
    height: int,
    fps: int,
    music_path: str | None = None,
    duration_seconds: float = 55.0,
) -> str:
    """Build the FFmpeg command string for a YouTube Shorts vertical video."""
    # Each image shown for (duration / num_images) seconds with zoom/pan filter
    num_images = max(1, len(image_paths))
    per_image_duration = duration_seconds / num_images

    input_args = []
    filter_parts = []

    for i, img in enumerate(image_paths):
        input_args.append(f"-loop 1 -t {per_image_duration:.2f} -i \"{img}\"")
        # Ken-Burns zoom-pan effect
        zoom_dir = "in" if i % 2 == 0 else "out"
        if zoom_dir == "in":
            zoom_filter = f"zoompan=z='min(zoom+0.0015,1.5)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={int(per_image_duration * fps)}:s={width}x{height}:fps={fps}"
        else:
            zoom_filter = f"zoompan=z='if(lte(zoom,1.0),1.5,max(1.0,zoom-0.0015))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={int(per_image_duration * fps)}:s={width}x{height}:fps={fps}"
        filter_parts.append(f"[{i}:v]{zoom_filter},setsar=1[v{i}]")

    concat_inputs = "".join(f"[v{i}]" for i in range(num_images))
    filter_parts.append(f"{concat_inputs}concat=n={num_images}:v=1:a=0[outv]")

    inputs_str = " ".join(input_args)
    filter_str = "; ".join(filter_parts)

    audio_args = f"-i \"{audio_path}\"" if audio_path else ""
    music_args = f"-i \"{music_path}\"" if music_path else ""

    # Audio mixing
    if audio_path and music_path:
        audio_filter = f"-filter_complex \"{filter_str}; [voice]amix=inputs=2:duration=first[outa]\" -map \"[outv]\" -map \"[outa]\""
    elif audio_path:
        audio_filter = f"-filter_complex \"{filter_str}\" -map \"[outv]\" -map \"{num_images}:a\""
    else:
        audio_filter = f"-filter_complex \"{filter_str}\" -map \"[outv]\""

    cmd = (
        f"ffmpeg -y {inputs_str} {audio_args} {music_args} "
        f"{audio_filter} "
        f"-c:v libx264 -preset fast -crf 22 -pix_fmt yuv420p "
        f"-c:a aac -b:a 192k "
        f"-r {fps} -s {width}x{height} "
        f"\"{output_path}\""
    )
    return cmd


def compose_video(
    scene_plan: ScenePlan,
    image_assets: list[ImageAsset],
    voice_asset: VoiceAsset | None = None,
    output_dir: Path | None = None,
    dry_run: bool = False,
) -> VideoDraft:
    """Compose a vertical MP4 from scenes and audio. Dry-run if assets missing or FFmpeg absent."""
    output_dir = output_dir or VIDEOS_OUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    draft_id = f"video_{uuid.uuid4().hex[:8]}"
    output_path = str(output_dir / f"{draft_id}.mp4")

    # Collect real image paths
    real_images = [
        a.image_path for a in image_assets
        if a.image_path and Path(a.image_path).exists()
    ]
    audio_path = (
        voice_asset.audio_path
        if voice_asset and voice_asset.audio_path and Path(voice_asset.audio_path).exists()
        else None
    )
    music_path = BACKGROUND_MUSIC_PATH if BACKGROUND_MUSIC_PATH and Path(BACKGROUND_MUSIC_PATH).exists() else None

    has_assets = bool(real_images)
    has_ffmpeg = _ffmpeg_available()
    is_dry_run = dry_run or not has_assets or not has_ffmpeg

    duration = float(voice_asset.duration_seconds) if voice_asset and voice_asset.duration_seconds else 55.0

    ffmpeg_cmd: str | None = None
    if real_images:
        ffmpeg_cmd = _build_ffmpeg_command(
            image_paths=real_images,
            audio_path=audio_path,
            output_path=output_path,
            width=OUTPUT_VIDEO_WIDTH,
            height=OUTPUT_VIDEO_HEIGHT,
            fps=OUTPUT_VIDEO_FPS,
            music_path=music_path,
            duration_seconds=duration,
        )

    if not is_dry_run and ffmpeg_cmd:
        try:
            subprocess.run(ffmpeg_cmd, shell=True, check=True, capture_output=True)
            video_path = output_path
        except subprocess.CalledProcessError:
            is_dry_run = True
            video_path = None
    else:
        video_path = None

    return VideoDraft(
        id=draft_id,
        title=scene_plan.title,
        category="midnight_mystery",  # default; real value from scene_plan if available
        scene_plan_id=scene_plan.id,
        voice_asset_id=voice_asset.id if voice_asset else None,
        image_asset_ids=[a.id for a in image_assets],
        video_path=video_path,
        width=OUTPUT_VIDEO_WIDTH,
        height=OUTPUT_VIDEO_HEIGHT,
        fps=OUTPUT_VIDEO_FPS,
        duration_seconds=duration,
        is_dry_run=is_dry_run,
        ffmpeg_command=ffmpeg_cmd,
    )
