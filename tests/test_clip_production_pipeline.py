"""Tests for the clip-based production pipeline."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from workers.cli import app
from workers.production_models import SceneManifest, SceneShot
from workers.render.clip_composer import build_render_command
from workers.script_generator import generate_script
from workers.story_workspace import APPROVAL_ERROR, StoryWorkspace
from workers.subtitles.ass_renderer import render_ass
from workers.subtitles.subtitle_planner import split_telugu_cues

runner = CliRunner()


def _workspace(tmp_path: Path) -> StoryWorkspace:
    ws = StoryWorkspace.from_arg(tmp_path / "stories" / "chandra-last-train", create=True)
    return ws


def _approved_workspace(tmp_path: Path) -> StoryWorkspace:
    ws = _workspace(tmp_path)
    ws.path("script_candidates", "candidate_02.txt").write_text(
        "చంద్ర చివరి రైలు కోసం ఎదురు చూశాడు. ముసలాయన చెప్పిన మాట చివరికి నిజమైంది.",
        encoding="utf-8",
    )
    result = runner.invoke(
        app,
        [
            "approve-script",
            str(ws.root),
            "--candidate",
            "candidate_02",
            "--notes",
            "Approved for pilot",
        ],
    )
    assert result.exit_code == 0, result.output
    return ws


def _manifest(ws: StoryWorkspace, shots: int = 8) -> None:
    shot_models = [
        SceneShot(
            shot_id=f"shot_{idx:02d}",
            scene_number=idx,
            start_seconds=float(idx - 1),
            end_seconds=float(idx),
            duration_seconds=1.0,
            narration_text=f"లైన్ {idx}",
            clip_filename=f"shot_{idx:02d}.mp4",
            visual_prompt=f"షాట్ {idx}",
            camera_notes="Vertical locked camera.",
            subtitle_text=f"లైన్ {idx}",
        )
        for idx in range(1, shots + 1)
    ]
    ws.write_json(
        "scene_manifest.json",
        SceneManifest(
            story_slug=ws.slug,
            title="చంద్ర చివరి రైలు",
            total_duration_seconds=float(shots),
            shots=shot_models,
            global_style="style",
            negative_prompt="negative",
            character_bible_path=str(ws.path("character_bible.json")),
            location_bible_path=str(ws.path("location_bible.json")),
        ),
    )


def test_story_workspace_creation(tmp_path):
    ws = _workspace(tmp_path)
    assert ws.path("script_candidates").is_dir()
    assert ws.path("clips").is_dir()


def test_script_package_generation_creates_candidates_and_review(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MIDNIGHT_TELUGU_TEST_MODE", "1")
    monkeypatch.setattr("workers.config.ALLOW_MOCK_PRODUCTION", True)
    result = runner.invoke(
        app,
        ["generate-story-package", "chandra-last-train", "--variants", "2", "--provider", "mock"],
    )
    assert result.exit_code == 0, result.output
    ws = StoryWorkspace.from_arg("chandra-last-train")
    assert ws.path("script_candidates", "candidate_01.txt").exists()
    assert ws.path("script_candidates", "candidate_02.meta.json").exists()
    assert "Approval Command" in ws.path("script_review.md").read_text(encoding="utf-8")


def test_production_rejects_mock_story_package_provider(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("MIDNIGHT_TELUGU_TEST_MODE", raising=False)
    monkeypatch.setattr("workers.config.ALLOW_MOCK_PRODUCTION", False)
    result = runner.invoke(
        app,
        ["generate-story-package", "chandra-last-train", "--provider", "mock"],
    )
    assert result.exit_code == 1
    assert "Mock script provider is disabled for production" in result.output


def test_script_generation_uses_text_provider_for_non_mock(monkeypatch):
    from tests.test_cli_blueprint_flow import _make_blueprint

    class FakeProvider:
        def generate_text(self, prompt: str) -> str:
            assert "Locked blueprint" in prompt
            return "చంద్ర స్టేషన్‌లో ఒంటరిగా నిలబడ్డాడు. చివరికి ముసలాయన మాటే నిజమైంది."

    monkeypatch.setattr("workers.providers.get_text_provider", lambda provider: FakeProvider())
    script = generate_script(_make_blueprint(), provider="openai")
    assert "చంద్ర స్టేషన్" in script.full_script_telugu


def test_approval_command_creates_script_and_approval_json(tmp_path):
    ws = _approved_workspace(tmp_path)
    approval = json.loads(ws.path("script_approval.json").read_text(encoding="utf-8"))
    assert ws.path("script.txt").exists()
    assert approval["approved"] is True
    assert approval["script_version"] == "candidate_02"


def test_production_commands_fail_without_approved_script(tmp_path):
    ws = _workspace(tmp_path)
    result = runner.invoke(app, ["generate-voiceover", str(ws.root), "--dry-run"])
    assert result.exit_code == 1
    assert APPROVAL_ERROR in result.output


def test_tts_command_dry_run_does_not_fake_audio(tmp_path):
    ws = _approved_workspace(tmp_path)
    result = runner.invoke(app, ["generate-voiceover", str(ws.root), "--dry-run", "--voice-id", "voice"])
    assert result.exit_code == 0, result.output
    meta = json.loads(ws.path("narration.meta.json").read_text(encoding="utf-8"))
    assert meta["status"] == "dry_run"
    assert not ws.path("narration.wav").exists()


def test_scene_manifest_validates_shot_count_and_total_duration(tmp_path):
    ws = _approved_workspace(tmp_path)
    ws.write_json("narration.meta.json", {"duration_seconds": 48})
    result = runner.invoke(app, ["create-scene-manifest", str(ws.root), "--shots", "8"])
    assert result.exit_code == 0, result.output
    manifest = json.loads(ws.path("scene_manifest.json").read_text(encoding="utf-8"))
    assert len(manifest["shots"]) == 8
    assert manifest["total_duration_seconds"] == 48


def test_subtitle_cue_generation_creates_valid_ass_content():
    cues = split_telugu_cues("చంద్ర రైలు కోసం ఎదురు చూశాడు. చివరికి నిజం తెలిసింది.", 10)
    ass = render_ass(cues, title="test")
    assert "[Events]" in ass
    assert "Style: Telugu" in ass
    assert "Dialogue:" in ass


def test_clip_import_validation_catches_missing_clips(tmp_path):
    ws = _approved_workspace(tmp_path)
    _manifest(ws, shots=2)
    source = tmp_path / "clips"
    source.mkdir()
    (source / "shot_01.mp4").write_bytes(b"not-real")
    result = runner.invoke(app, ["import-clips", str(ws.root), str(source)])
    assert result.exit_code == 1
    assert "Missing clips: shot_02.mp4" in result.output


def test_ffmpeg_command_builder_includes_core_render_steps(tmp_path):
    ws = _approved_workspace(tmp_path)
    _manifest(ws, shots=2)
    ws.path("clips", "shot_01.mp4").write_bytes(b"")
    ws.path("clips", "shot_02.mp4").write_bytes(b"")
    ws.path("narration.wav").write_bytes(b"")
    ws.path("subtitles.ass").write_text("[Script Info]\n", encoding="utf-8")
    plan = build_render_command(ws.root)
    command = " ".join(plan.ffmpeg_command)
    assert "scale=1080:1920" in command
    assert "crop=1080:1920" in command
    assert "concat=n=2" in command
    assert "-c:a aac -ar 48000" in command
    assert "ass=" in command


def test_render_command_supports_dry_run_without_real_media(tmp_path):
    ws = _approved_workspace(tmp_path)
    _manifest(ws, shots=1)
    ws.path("subtitles.ass").write_text("[Script Info]\n", encoding="utf-8")
    result = runner.invoke(app, ["render-final", str(ws.root), "--dry-run"])
    assert result.exit_code == 0, result.output
    assert ws.path("render_plan.json").exists()


def test_veo_generation_dry_run_writes_prompts_and_metadata(tmp_path):
    ws = _approved_workspace(tmp_path)
    _manifest(ws, shots=1)
    result = runner.invoke(app, ["generate-veo-clips", str(ws.root), "--dry-run"])
    assert result.exit_code == 0, result.output
    meta = json.loads(ws.path("clips", "shot_01.meta.json").read_text(encoding="utf-8"))
    assert meta["status"] == "dry_run"
    assert "Cinematic vertical 9:16" in meta["prompt"]
