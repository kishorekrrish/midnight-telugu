"""Veo clip generation orchestration."""

from __future__ import annotations

from pathlib import Path

from workers.media.ffmpeg_utils import probe_media
from workers.production_models import now_iso
from workers.video_generation.prompt_manifest import build_veo_prompt
from workers.video_generation.veo_provider import VeoProvider


def generate_veo_clips(
    story_dir: Path,
    manifest: dict,
    model: str,
    resolution: str,
    aspect_ratio: str,
    selected_shots: set[str] | None,
    overwrite: bool,
    dry_run: bool,
) -> list[dict]:
    clips_dir = story_dir / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[dict] = []
    provider = None if dry_run else VeoProvider()
    for shot_data in manifest["shots"]:
        shot_id = shot_data["shot_id"]
        if selected_shots and shot_id not in selected_shots:
            continue
        from workers.production_models import SceneShot

        shot = SceneShot.model_validate(shot_data)
        out = clips_dir / shot.clip_filename
        meta_path = clips_dir / f"{shot_id}.meta.json"
        if out.exists() and not overwrite:
            continue
        prompt = build_veo_prompt(story_dir, shot)
        meta = {
            "shot_id": shot_id,
            "provider": "veo",
            "model": model,
            "prompt": prompt,
            "output_path": str(out),
            "created_at": now_iso(),
            "status": "dry_run" if dry_run else "pending",
        }
        if dry_run:
            meta_path.write_text(__import__("json").dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
            outputs.append(meta)
            continue
        try:
            operation_name = provider.generate_clip(prompt, out, model, aspect_ratio, resolution)  # type: ignore[union-attr]
            info = probe_media(out)
            meta.update(
                {
                    "operation_name": operation_name,
                    "duration_seconds": info.duration_seconds,
                    "width": info.width,
                    "height": info.height,
                    "fps": info.fps,
                    "status": "success",
                }
            )
        except Exception as exc:
            meta.update({"status": "failed", "error": str(exc)})
        meta_path.write_text(__import__("json").dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        outputs.append(meta)
    return outputs
