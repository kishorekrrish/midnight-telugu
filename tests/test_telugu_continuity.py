"""Tests for Telugu authenticity and story continuity validators."""

from __future__ import annotations

from workers.models import ContentCategory, StoryIdea, StoryScript
from workers.story_continuity import check_continuity
from workers.telugu_quality import apply_telugu_replacements, check_telugu_quality


def _make_script(text: str, hook: str = "ఆ రాత్రి తలుపు తెరుచుకుంది.") -> StoryScript:
    idea = StoryIdea(
        id="idea_test",
        title="Test",
        category=ContentCategory.MIDNIGHT_MYSTERY,
        hook=hook,
        premise="test premise",
        twist="test twist",
        tone="dark",
    )
    return StoryScript(
        id="script_test",
        idea_id="idea_test",
        title="Test",
        category=ContentCategory.MIDNIGHT_MYSTERY,
        hook_line=hook,
        full_script_telugu=text,
        estimated_duration_seconds=60,
        story_idea=idea,
    )


# ── Telugu quality tests ─────────────────────────────────────────────────────

def test_avoidable_english_detected():
    result = check_telugu_quality("అతను wet footprints చూసాడు.")
    assert result.telugu_authenticity_score < 100
    assert len(result.english_word_issues) > 0


def test_english_replacements_suggested():
    result = check_telugu_quality("అతను shadow చూసాడు midnight లో.")
    replacements = result.suggested_replacements
    found_words = [r[0] for r in replacements]
    assert any("shadow" in w or "midnight" in w for w in found_words)


def test_clean_telugu_passes_authenticity():
    text = (
        "అర్ధరాత్రి తలుపు తెరుచుకుంది.\n\n"
        "గాలి ఆగింది. నిశ్శబ్దం అలుముకుంది.\n\n"
        "చేతులు వణికాయి — నీడ కదిలింది."
    )
    result = check_telugu_quality(text)
    assert result.telugu_authenticity_score >= 80


def test_apply_telugu_replacements_fixes_english():
    text = "అతను shadow చూసాడు."
    fixed = apply_telugu_replacements(text)
    assert "shadow" not in fixed
    assert "నీడ" in fixed


def test_apply_telugu_replacements_multi():
    text = "wet footprints మరియు handprint కనుగొన్నారు."
    fixed = apply_telugu_replacements(text)
    assert "wet footprints" not in fixed
    assert "handprint" not in fixed


# ── Continuity tests ─────────────────────────────────────────────────────────

def test_pov_mismatch_detected():
    # First-person hook, third-person body
    hook = "నేను ఆ రోజు మరచిపోలేను."
    text = (
        "అతను ఆఫీసుకి వెళ్ళాడు.\n\n"
        "అతను పాత ఉత్తరం చూసాడు.\n\n"
        "అతను తిరిగి చూసాడు — ఎవరూ లేరు."
    )
    script = _make_script(text, hook=hook)
    result = check_continuity(script)
    pov_issues = [i for i in result.issues if "POV" in i or "first-person" in i]
    assert len(pov_issues) > 0


def test_hook_body_disconnect_detected():
    hook = "అర్ధరాత్రి ఆ పాత భవనం తలుపు తెరుచుకుంది."
    text = (
        "రాముడు రోజూ బజారుకి వెళ్ళేవాడు.\n\n"
        "ఒకరోజు అతనికి పాత పుస్తకం దొరికింది.\n\n"
        "పుస్తకంలో రహస్యం — అతను నోరు తెరుచుకుపోయింది."
    )
    script = _make_script(text, hook=hook)
    result = check_continuity(script)
    assert result.continuity_score < 100


def test_good_script_continuity_passes():
    hook = "ఆ రాత్రి తలుపు తెరుచుకుంది — లోపల నుండి."
    text = (
        "ఆ రాత్రి రాముడు ఇంట్లో ఒంటరిగా ఉన్నాడు.\n\n"
        "తలుపు శబ్దం వినిపించింది. గాలి ఆగింది.\n\n"
        "అతను లేచి తలుపు దగ్గరకి వెళ్ళాడు — కానీ —\n\n"
        "తలుపు లోపల నుండి లాక్ అయి ఉంది. అతను బయటకే రాలేకపోయాడు.\n\n"
        "ఇప్పటికీ అక్కడే ఉన్నాడు."
    )
    script = _make_script(text, hook=hook)
    result = check_continuity(script)
    assert result.continuity_score >= 65


def test_mostly_english_final_line_flagged():
    hook = "ఆ రాత్రి ఏదో జరిగింది."
    text = (
        "రాముడు ఇంట్లో ఉన్నాడు.\n\n"
        "చీకటి అలుముకుంది. గుండె వేగంగా కొట్టుకుంది.\n\n"
        "The truth was finally revealed and he could not believe it."
    )
    script = _make_script(text, hook=hook)
    result = check_continuity(script)
    english_issues = [i for i in result.issues if "English" in i or "final line" in i.lower()]
    assert len(english_issues) > 0


def test_review_markdown_includes_authenticity_section():
    from workers.models import ReviewChecklist, ReviewStatus, ReviewStatusEnum
    from workers.review_queue import _build_review_markdown

    review = ReviewStatus(
        id="review_test",
        title="Test",
        category="midnight_mystery",
        hook="test hook",
        status=ReviewStatusEnum.NEEDS_REVIEW,
        checklist=ReviewChecklist(),
    )
    md = _build_review_markdown(
        review=review,
        telugu_quality={
            "telugu_authenticity_score": 85,
            "suggested_replacements": [{"found": "shadow", "replace_with": "నీడ"}],
            "suggestions": ["Replace shadow with నీడ"],
        },
        continuity={
            "continuity_score": 90,
            "issues": [],
            "suggestions": [],
        },
    )
    assert "Telugu Authenticity Check" in md
    assert "85/100" in md
    assert "Continuity Check" in md
    assert "90/100" in md
