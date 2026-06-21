"""Tests for Story Lab Phase 1."""

from __future__ import annotations

import json

from typer.testing import CliRunner

from workers.cli import app
from workers.story_lab import (
    build_advanced_blueprint,
    default_story_brief,
    generate_idea_bank,
    generate_story_lab_package,
    score_idea_viral,
)

runner = CliRunner()


def test_story_lab_generates_idea_bank_with_viral_scores():
    brief = default_story_brief("chandra-last-train")
    ideas = generate_idea_bank(brief, count=10, provider="mock")
    scores = [score_idea_viral(idea) for idea in ideas]
    assert len(ideas) == 10
    assert max(score.total for score in scores) > 70
    assert any(score.replay_clue >= 7 for score in scores)


def test_advanced_blueprint_has_story_design_fields():
    idea = generate_idea_bank(default_story_brief("chandra-last-train"), count=1, provider="mock")[0]
    blueprint = build_advanced_blueprint(idea)
    assert blueprint.first_3_seconds_hook
    assert blueprint.protagonist_desire
    assert blueprint.hidden_truth
    assert blueprint.replay_value_clue
    assert blueprint.emotional_aftertaste


def test_story_lab_package_creates_review_and_candidates(tmp_path):
    story_dir = tmp_path / "stories" / "chandra-last-train"
    result = generate_story_lab_package(
        story_dir,
        default_story_brief("chandra-last-train"),
        provider="mock",
        idea_count=4,
        top_blueprints=2,
        scripts_per_blueprint=2,
    )
    assert result["candidate_count"] == 4
    assert (story_dir / "story_brief.json").exists()
    assert (story_dir / "idea_bank" / "ideas.json").exists()
    assert (story_dir / "blueprints" / "blueprint_01.json").exists()
    assert (story_dir / "script_review.md").exists()
    assert len(list((story_dir / "script_candidates").glob("*.txt"))) == 4
    review = (story_dir / "script_review.md").read_text(encoding="utf-8")
    assert "Story Lab Review" in review
    assert "Editor score" in review


def test_story_lab_cli_uses_mock_only_in_test_mode(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("MIDNIGHT_TELUGU_TEST_MODE", "1")
    monkeypatch.setattr("workers.config.ALLOW_MOCK_PRODUCTION", True)
    result = runner.invoke(
        app,
        [
            "generate-story-lab-package",
            "chandra-last-train",
            "--provider",
            "mock",
            "--ideas",
            "3",
            "--top-blueprints",
            "1",
            "--scripts-per-blueprint",
            "1",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Story Lab package created" in result.output
    metadata = json.loads(
        (tmp_path / "stories" / "chandra-last-train" / "script_candidates" / "bp01_candidate_01.meta.json").read_text(
            encoding="utf-8"
        )
    )
    assert "critique" in metadata


def test_story_lab_cli_rejects_mock_outside_test_mode(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("MIDNIGHT_TELUGU_TEST_MODE", raising=False)
    monkeypatch.setattr("workers.config.ALLOW_MOCK_PRODUCTION", False)
    result = runner.invoke(
        app,
        ["generate-story-lab-package", "chandra-last-train", "--provider", "mock"],
    )
    assert result.exit_code == 1
    assert "Mock Story Lab provider is disabled for production" in result.output
