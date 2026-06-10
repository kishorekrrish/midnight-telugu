"""Tests for video composer dry-run behavior."""

from __future__ import annotations

from workers.models import ImageAsset, Scene, ScenePlan
from workers.video_composer import _build_ffmpeg_command, compose_video


def _make_scene_plan() -> ScenePlan:
    scenes = [
        Scene(
            scene_number=i,
            timestamp_range=f"00:{(i-1)*8:02d}-00:{i*8:02d}",
            narration_line=f"narration {i}",
            visual_description="visual",
            location="place",
            mood="tense",
            camera_angle="close-up",
            motion_direction="zoom in",
            image_prompt="prompt",
        )
        for i in range(1, 8)
    ]
    return ScenePlan(id="sp1", script_id="s1", title="Test", total_scenes=7, scenes=scenes)


def _make_image_assets(scene_plan: ScenePlan) -> list[ImageAsset]:
    return [
        ImageAsset(
            id=f"img_{i}",
            scene_number=i,
            scene_plan_id=scene_plan.id,
            image_path=None,  # missing — forces dry run
        )
        for i in range(1, 8)
    ]


class TestDryRun:
    def test_dry_run_when_no_images(self, tmp_path):
        plan = _make_scene_plan()
        images = _make_image_assets(plan)
        draft = compose_video(plan, images, output_dir=tmp_path)
        assert draft.is_dry_run is True
        assert draft.video_path is None

    def test_dry_run_explicit_flag(self, tmp_path):
        plan = _make_scene_plan()
        images = _make_image_assets(plan)
        draft = compose_video(plan, images, dry_run=True, output_dir=tmp_path)
        assert draft.is_dry_run is True

    def test_draft_has_correct_dimensions(self, tmp_path):
        plan = _make_scene_plan()
        images = _make_image_assets(plan)
        draft = compose_video(plan, images, output_dir=tmp_path)
        assert draft.width == 1080
        assert draft.height == 1920
        assert draft.fps == 30

    def test_draft_has_id(self, tmp_path):
        plan = _make_scene_plan()
        images = _make_image_assets(plan)
        draft = compose_video(plan, images, output_dir=tmp_path)
        assert draft.id.startswith("video_")

    def test_metadata_saved_not_video_file(self, tmp_path):
        plan = _make_scene_plan()
        images = _make_image_assets(plan)
        draft = compose_video(plan, images, output_dir=tmp_path)
        assert draft.video_path is None


class TestFfmpegCommandGeneration:
    def test_command_contains_dimensions(self):
        cmd = _build_ffmpeg_command(
            image_paths=["/tmp/a.png", "/tmp/b.png"],
            audio_path=None,
            output_path="/tmp/out.mp4",
            width=1080,
            height=1920,
            fps=30,
            duration_seconds=55.0,
        )
        assert "1080x1920" in cmd
        assert "30" in cmd

    def test_command_contains_output(self):
        cmd = _build_ffmpeg_command(
            image_paths=["/tmp/a.png"],
            audio_path=None,
            output_path="/tmp/out.mp4",
            width=1080,
            height=1920,
            fps=30,
        )
        assert "/tmp/out.mp4" in cmd

    def test_command_contains_audio_when_provided(self):
        cmd = _build_ffmpeg_command(
            image_paths=["/tmp/a.png"],
            audio_path="/tmp/audio.mp3",
            output_path="/tmp/out.mp4",
            width=1080,
            height=1920,
            fps=30,
        )
        assert "/tmp/audio.mp3" in cmd

    def test_command_has_codec(self):
        cmd = _build_ffmpeg_command(
            image_paths=["/tmp/a.png"],
            audio_path=None,
            output_path="/tmp/out.mp4",
            width=1080,
            height=1920,
            fps=30,
        )
        assert "libx264" in cmd
