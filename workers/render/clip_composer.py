"""FFmpeg final clip composer."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from workers.media.ffmpeg_utils import ffmpeg_available, probe_media
from workers.production_models import RenderPlan
from workers.render.audio_mixer import load_music_mix


def build_render_command(story_dir: Path, output_path: Path | None = None) -> RenderPlan:
    output_path = output_path or story_dir / "final.mp4"
    manifest = json.loads((story_dir / "scene_manifest.json").read_text(encoding="utf-8"))
    clips = [story_dir / "clips" / shot["clip_filename"] for shot in manifest["shots"]]
    missing = [str(path) for path in clips if not path.exists()]
    warnings = [f"Missing clip: {path}" for path in missing]
    narration = story_dir / "narration.wav"
    subtitles = story_dir / "subtitles.ass"
    if not narration.exists():
        warnings.append("Missing narration.wav")
    if not subtitles.exists():
        warnings.append("Missing subtitles.ass")

    filter_parts: list[str] = []
    for idx, shot in enumerate(manifest["shots"]):
        duration = float(shot["duration_seconds"])
        filter_parts.append(
            f"[{idx}:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,fps=30,trim=duration={duration:.2f},setpts=PTS-STARTPTS[v{idx}]"
        )
    subtitle_filter_path = str(subtitles).replace("\\", "\\\\").replace(":", "\\:")
    filter_parts.append(
        "".join(f"[v{i}]" for i in range(len(clips)))
        + f"concat=n={len(clips)}:v=1:a=0,ass='{subtitle_filter_path}'[vout]"
    )

    input_args: list[str] = []
    for clip in clips:
        input_args.extend(["-i", str(clip)])
    narration_index = len(clips)
    input_args.extend(["-i", str(narration)])
    music = load_music_mix(story_dir)
    audio_map = f"{narration_index}:a"
    if music:
        for key in ("music_path", "ambience_path"):
            if music.get(key):
                input_args.extend(["-stream_loop", "-1", "-i", str(music[key])])
        # Keep first phase conservative: narration remains primary, optional assets are documented.
        warnings.append("Music/ambience config detected; volume mixing will be added after media validation.")

    command = [
        "ffmpeg",
        "-y",
        *input_args,
        "-filter_complex",
        ";".join(filter_parts),
        "-map",
        "[vout]",
        "-map",
        audio_map,
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-r",
        "30",
        "-c:a",
        "aac",
        "-ar",
        "48000",
        "-shortest",
        str(output_path),
    ]
    return RenderPlan(output_path=str(output_path), ffmpeg_command=command, dry_run=False, warnings=warnings)


def render_final(story_dir: Path, dry_run: bool = False) -> RenderPlan:
    plan = build_render_command(story_dir)
    if dry_run or plan.warnings or not ffmpeg_available():
        plan.dry_run = True
        if not ffmpeg_available():
            plan.warnings.append("ffmpeg is not installed.")
        (story_dir / "render_plan.json").write_text(plan.model_dump_json(indent=2), encoding="utf-8")
        return plan
    subprocess.run(plan.ffmpeg_command, check=True, capture_output=True)
    info = probe_media(Path(plan.output_path))
    (story_dir / "final.meta.json").write_text(info.model_dump_json(indent=2), encoding="utf-8")
    return plan
