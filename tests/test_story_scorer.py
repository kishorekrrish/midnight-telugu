"""Tests for story scorer."""

from __future__ import annotations

from workers.models import ContentCategory, StoryIdea, StoryScript
from workers.story_scorer import ScoreBreakdown, StoryScore, _grade, score_idea, score_script


def _make_idea(**kwargs) -> StoryIdea:
    defaults = dict(
        id="idea_test",
        title="Test Idea",
        category=ContentCategory.MIDNIGHT_MYSTERY,
        hook="రాత్రి 2 గంటలకి తలుపు తట్టిన వ్యక్తి — అది బయట నుండి కాదు.",
        premise="ఒక వ్యక్తి మూసిన గది నుండి శబ్దాలు వింటాడు.",
        twist="ఆ గదిలో తండ్రి రహస్యం దాచిపెట్టాడు.",
        tone="eerie, suspenseful",
    )
    defaults.update(kwargs)
    return StoryIdea(**defaults)


def _make_script(**kwargs) -> StoryScript:
    defaults = dict(
        id="script_test",
        idea_id="idea_test",
        title="Test Script",
        category=ContentCategory.MIDNIGHT_MYSTERY,
        hook_line="రాత్రి 2 గంటలకి తలుపు తట్టిన వ్యక్తి — అది బయట నుండి కాదు.",
        full_script_telugu=(
            "రాత్రి 2 గంటలకి తలుపు తట్టిన వ్యక్తి —\n\n"
            "ఒక వ్యక్తి మూసిన గది నుండి శబ్దాలు వింటాడు. ప్రతి రాత్రీ.\n\n"
            "ఆ గది 20 సంవత్సరాల నుండి తెరవలేదు.\n\n"
            "చివరికి తెరిచాడు — లోపల ఒక డైరీ ఉంది.\n\n"
            "ఆ డైరీలో — నిజం రాసి ఉంది."
        ),
    )
    defaults.update(kwargs)
    return StoryScript(**defaults)


class TestScoring:
    def test_score_idea_returns_score(self):
        idea = _make_idea()
        result = score_idea(idea)
        assert isinstance(result, StoryScore)
        assert 0 <= result.overall_score <= 100

    def test_score_has_breakdown(self):
        idea = _make_idea()
        result = score_idea(idea)
        bd = result.score_breakdown
        assert isinstance(bd, ScoreBreakdown)
        assert bd.hook_strength >= 0
        assert bd.monetization_safety >= 0

    def test_weak_hook_reduces_score(self):
        weak = _make_idea(hook="ఒకానొక రోజు ఒక వ్యక్తి ఉన్నాడు")
        strong = _make_idea(hook="రాత్రి 2 గంటలకి తలుపు తట్టిన వ్యక్తి — అది బయట నుండి కాదు.")
        assert score_idea(weak).score_breakdown.hook_strength < score_idea(strong).score_breakdown.hook_strength

    def test_monetization_risk_reduces_score(self):
        risky = _make_idea(hook="రాజకీయ నాయకుడి రహస్యం", premise="రాజకీయ పార్టీ మోసం", twist="రహస్యం")
        clean = _make_idea()
        assert score_idea(risky).score_breakdown.monetization_safety < score_idea(clean).score_breakdown.monetization_safety

    def test_repeatability_warnings_reduce_originality(self):
        idea = _make_idea()
        no_warn = score_idea(idea, repeatability_warnings=[])
        with_warn = score_idea(idea, repeatability_warnings=["Twist repeated 3x", "Category overused"])
        assert with_warn.score_breakdown.originality < no_warn.score_breakdown.originality

    def test_grade_assignment(self):
        assert _grade(90) == "A"
        assert _grade(75) == "B"
        assert _grade(60) == "C"
        assert _grade(45) == "D"
        assert _grade(30) == "F"

    def test_score_idea_to_dict(self):
        idea = _make_idea()
        result = score_idea(idea)
        d = result.to_dict()
        assert "overall_score" in d
        assert "grade" in d
        assert "score_breakdown" in d
        assert "rejection_reasons" in d
        assert "improvement_suggestions" in d

    def test_score_script_returns_score(self):
        script = _make_script()
        result = score_script(script)
        assert isinstance(result, StoryScore)
        assert 0 <= result.overall_score <= 100

    def test_ai_ending_reduces_naturalness(self):
        clean = _make_script()
        ai_ending = _make_script(
            full_script_telugu=clean.full_script_telugu + "\nనీతి ఏమిటంటే మంచిగా ఉండాలి."
        )
        clean_score = score_script(clean).score_breakdown.telugu_naturalness
        ai_score = score_script(ai_ending).score_breakdown.telugu_naturalness
        assert ai_score <= clean_score
