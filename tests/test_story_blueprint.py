"""Tests for blueprint generation and validation."""

from __future__ import annotations

from workers.blueprint_validator import validate_blueprint
from workers.models import ContentCategory, StoryIdea
from workers.story_blueprint import build_blueprint


def _make_idea(**kwargs) -> StoryIdea:
    defaults = dict(
        id="idea_bp_1",
        title="అమ్మ చివరి కాల్",
        category=ContentCategory.EMOTIONAL_SUSPENSE,
        hook="అమ్మ చనిపోయిన తర్వాత ఆమె ఫోన్‌లో ఒక వాయిస్ మెమో కనిపించింది.",
        premise="శ్యామ్ పాత చెరువు గట్టు దగ్గర దొరికిన బొమ్మను చూసి తన పుట్టుక గురించే అనుమానపడటం మొదలుపెడతాడు.",
        twist="ఫోటో వెనక రాసిన వాక్యం వల్ల శ్యామ్ తన తండ్రి గురించి విన్నది మొత్తం అబద్ధమని తెలుస్తుంది.",
        tone="emotional suspense",
    )
    defaults.update(kwargs)
    return StoryIdea(**defaults)


def test_valid_blueprint_passes():
    blueprint = build_blueprint(_make_idea())
    result = validate_blueprint(blueprint)
    assert result.passed is True


def test_missing_protagonist_fails():
    blueprint = build_blueprint(_make_idea())
    blueprint.protagonist_name = ""
    result = validate_blueprint(blueprint)
    assert "MISSING_PROTAGONIST" in result.hard_failures


def test_multiple_primary_devices_fail():
    blueprint = build_blueprint(_make_idea())
    blueprint.primary_story_device = "వాయిస్ మెమో, పాత ఫోటో"
    result = validate_blueprint(blueprint)
    assert "MULTIPLE_PRIMARY_DEVICES" in result.hard_failures


def test_unresolved_clue_fails():
    blueprint = build_blueprint(_make_idea())
    blueprint.primary_clue = "పాత ఫోటో"
    blueprint.final_twist = "చివర్లో నిజం బయటపడింది."
    blueprint.final_line = "అంతే."
    result = validate_blueprint(blueprint)
    assert "CLUE_WITHOUT_PAYOFF" in result.hard_failures


def test_unclear_twist_fails():
    blueprint = build_blueprint(_make_idea())
    blueprint.final_twist = ""
    result = validate_blueprint(blueprint)
    assert "MISSING_FINAL_TWIST" in result.hard_failures


def test_too_many_locations_fail():
    blueprint = build_blueprint(_make_idea())
    blueprint.locations = ["పాత ఇల్లు", "చెరువు గట్టు", "ఆసుపత్రి"]
    result = validate_blueprint(blueprint)
    assert "TOO_MANY_LOCATIONS" in result.hard_failures
