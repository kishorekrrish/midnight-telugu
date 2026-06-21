"""Tests for Story Lab Phase 1."""

from __future__ import annotations

import json

from typer.testing import CliRunner

from workers.cli import app
from workers.story_lab import (
    RealStorySeed,
    ScriptCritique,
    analyze_source_safety,
    build_advanced_blueprint,
    build_fictionalization_plan,
    default_story_brief,
    evaluate_candidate,
    generate_idea_bank,
    generate_real_story_lab_package,
    generate_story_lab_package,
    run_editorial_gate,
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
    assert "Editorial gate" in review


def test_story_lab_package_caps_candidate_budget(tmp_path):
    story_dir = tmp_path / "stories" / "chandra-last-train"
    result = generate_story_lab_package(
        story_dir,
        default_story_brief("chandra-last-train"),
        provider="mock",
        idea_count=6,
        top_blueprints=3,
        scripts_per_blueprint=3,
        max_candidates=5,
    )
    assert result["candidate_count"] == 5
    assert len(list((story_dir / "script_candidates").glob("*.txt"))) == 5


def test_story_lab_package_removes_stale_candidate_files(tmp_path):
    story_dir = tmp_path / "stories" / "chandra-last-train"
    stale_dir = story_dir / "script_candidates"
    stale_dir.mkdir(parents=True)
    (stale_dir / "old_candidate.txt").write_text("old", encoding="utf-8")
    (stale_dir / "old_candidate.meta.json").write_text("{}", encoding="utf-8")

    result = generate_story_lab_package(
        story_dir,
        default_story_brief("chandra-last-train"),
        provider="mock",
        idea_count=3,
        top_blueprints=1,
        scripts_per_blueprint=3,
        max_candidates=2,
    )
    assert result["candidate_count"] == 2
    assert not (stale_dir / "old_candidate.txt").exists()
    assert not (stale_dir / "old_candidate.meta.json").exists()
    assert len(list(stale_dir.glob("*.txt"))) == 2


def test_editorial_gate_blocks_generic_summary_language():
    idea = generate_idea_bank(default_story_brief("chandra-last-train"), count=1, provider="mock")[0]
    blueprint = build_advanced_blueprint(idea)
    weak_script = (
        "చంద్ర ఒక రోజు స్టేషన్‌కి వెళ్లాడు. ఏదో రహస్యం ఉందని అతనికి అర్థం కాలేదు.\n\n"
        "తర్వాత నిజం తెలిసింది. జీవితం మార్చింది."
    )
    gate = run_editorial_gate(weak_script, blueprint)
    assert gate.total < 88
    assert "WEAK_OR_AWKWARD_LANGUAGE" in gate.blockers


def test_candidate_approval_requires_best_in_class_editorial_gate():
    idea = generate_idea_bank(default_story_brief("chandra-last-train"), count=1, provider="mock")[0]
    blueprint = build_advanced_blueprint(idea)
    weak_script = (
        "చంద్ర ఒక రోజు స్టేషన్‌కి వెళ్లాడు. ఏదో రహస్యం ఉందని అతనికి అర్థం కాలేదు.\n\n"
        "తర్వాత నిజం తెలిసింది. జీవితం మార్చింది."
    )
    critique = ScriptCritique(
        would_stop_scroll=True,
        final_line_strength=9,
        replay_clue=blueprint.primary_clue,
        editor_score=100,
    )
    candidate = evaluate_candidate("weak_candidate", blueprint, weak_script, critique, [])
    assert candidate.recommendation == "needs_rewrite"
    assert "WEAK_OR_AWKWARD_LANGUAGE" in candidate.hard_failures


def test_real_story_safety_blocks_active_case_with_real_person_accusation():
    seed = RealStorySeed(
        story_slug="blocked-case",
        source_type="reported_incident",
        source_summary="A recent allegation involving a named person at an exact apartment.",
        real_names_present=True,
        exact_location_present=True,
        active_case=True,
        accusation_against_real_person=True,
    )
    report = analyze_source_safety(seed)
    assert report.safe_to_dramatize is False
    assert report.risk_level == "blocked"
    assert "ACTIVE_CASE" in report.blocked_reasons
    assert "REAL_PERSON_ACCUSATION" in report.blocked_reasons


def test_fictionalization_plan_preserves_realistic_detail_without_identity():
    seed = RealStorySeed(
        story_slug="hospital-phone",
        source_type="local_rumour",
        source_summary="A closed hospital floor reportedly received the same phone call every night.",
        source_location_type="hospital",
        source_confidence="rumour",
    )
    report = analyze_source_safety(seed)
    plan = build_fictionalization_plan(seed, report)
    assert report.safe_to_dramatize is True
    assert report.claim_style == "fictionalized_realism"
    assert plan.changed_names is True
    assert plan.generalized_location is True
    assert "true story claim" in plan.forbidden_elements


def test_real_story_lab_package_writes_seed_safety_plan_and_three_candidates(tmp_path):
    seed = RealStorySeed(
        story_slug="hospital-phone",
        source_type="local_rumour",
        source_summary="A closed hospital floor reportedly received the same phone call every night.",
        source_location_type="hospital",
        source_confidence="rumour",
    )
    story_dir = tmp_path / "stories" / seed.story_slug
    result = generate_real_story_lab_package(story_dir, seed, provider="mock", idea_count=10)
    assert result["blocked"] is False
    assert result["candidate_count"] == 3
    assert (story_dir / "real_story_seed.json").exists()
    assert (story_dir / "source_safety_report.json").exists()
    assert (story_dir / "fictionalization_plan.json").exists()
    assert (story_dir / "ideas.json").exists()
    assert (story_dir / "top_ideas.json").exists()
    assert len(list((story_dir / "script_candidates").glob("candidate_*.txt"))) == 3
    assert len(list((story_dir / "critic_reviews").glob("candidate_*_review.json"))) == 3
    review = (story_dir / "script_review.md").read_text(encoding="utf-8")
    assert "Real-Story-Inspired Story Lab Review" in review
    assert "Source Safety" in review


def test_real_story_lab_package_stops_when_source_is_blocked(tmp_path):
    seed = RealStorySeed(
        story_slug="blocked-case",
        source_type="reported_incident",
        source_summary="A recent active case with a named person and exact address.",
        real_names_present=True,
        exact_location_present=True,
        active_case=True,
    )
    story_dir = tmp_path / "stories" / seed.story_slug
    result = generate_real_story_lab_package(story_dir, seed, provider="mock", idea_count=10)
    assert result["blocked"] is True
    assert result["candidate_count"] == 0
    assert (story_dir / "source_safety_report.json").exists()
    assert not (story_dir / "ideas.json").exists()


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
