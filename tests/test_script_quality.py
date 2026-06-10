"""Tests for script quality validator."""

from __future__ import annotations

from workers.models import ContentCategory, StoryIdea, StoryScript
from workers.script_generator import BANNED_ENDINGS, generate_script
from workers.script_quality import ScriptQualityResult, validate_script


def _make_script(text: str, hook: str = "ఆ రాత్రి గుండె ఆగిపోయింది.") -> StoryScript:
    """Build a minimal StoryScript for testing."""
    return StoryScript(
        id="test_0001",
        idea_id="idea_0001",
        title="Test Story",
        category=ContentCategory.MIDNIGHT_MYSTERY,
        hook_line=hook,
        full_script_telugu=text,
        estimated_duration_seconds=55,
    )


def _make_idea(category: str = "midnight_mystery") -> StoryIdea:
    return StoryIdea(
        id="idea_test",
        title="Test Idea",
        category=ContentCategory(category),
        hook="ఆ రాత్రి గుండె ఆగిపోయింది — లోపల ఏదో ఉంది.",
        premise="రవి ఆ పాత ఇల్లు తెరిచాడు — లోపల ఒక తాళం చెవి ఉంది.",
        twist="ఆ తాళం చెవి రవి తండ్రిది కాదు.",
        tone="dark",
        estimated_duration_seconds=55,
        twist_type="hidden_object_discovery",
        emotional_core="mystery",
        visual_signature="dark_room",
    )


# ── Banned endings ─────────────────────────────────────────────────────────

def test_banned_ending_question_rejected():
    text = (
        "రవి ఆ పాత ఇల్లు తెరిచాడు. గాలి ఆగింది. మూలలో ఒక పాత photograph ఉంది.\n\n"
        "ఆ photograph లో ఉన్న మనిషి — రవి తండ్రి కాదు.\n\n"
        "అలాంటప్పుడు మీరు ఏం చేసేవాళ్ళు?"
    )
    result = validate_script(_make_script(text))
    assert any("Banned ending" in i for i in result.issues)
    assert result.quality_score < 80


def test_banned_ending_moral_rejected():
    text = (
        "రవి ఆ పాత ఇల్లు తెరిచాడు. గాలి ఆగింది. మూలలో ఒక పాత photograph ఉంది.\n\n"
        "ఆ photograph లో ఉన్న మనిషి — రవి తండ్రి కాదు.\n\n"
        "అందుకే మనం అందరినీ నమ్మకూడదు."
    )
    result = validate_script(_make_script(text))
    assert any("Banned ending" in i for i in result.issues)


def test_all_banned_endings_covered():
    """Each banned pattern triggers the validator."""
    base = (
        "రవి ఆ పాత ఇల్లు తెరిచాడు. గాలి ఆగింది.\n\n"
        "ఆ photograph లో ఉన్న మనిషి — రవి తండ్రి కాదు.\n\n"
    )
    for pattern in BANNED_ENDINGS:
        result = validate_script(_make_script(base + pattern))
        assert any("Banned ending" in i for i in result.issues), (
            f"Pattern not caught: {pattern!r}"
        )


# ── Word count ─────────────────────────────────────────────────────────────

def test_too_short_script_rejected():
    text = "రవి ఆ ఇల్లు తెరిచాడు. లోపల ఒక photograph ఉంది. అతను తండ్రి కాదు."
    result = validate_script(_make_script(text))
    assert any("too short" in i.lower() or "below target" in i.lower() for i in result.issues)
    assert result.passed is False


_GOOD_SCRIPT_120W = (
    "ఆ రాత్రి గుండె ఆగిపోయింది — లోపల ఏదో ఉంది.\n\n"
    "రవి ఆ పాత ఇల్లు లోపలికి వెళ్ళినప్పుడు గాలి ఆగింది. "
    "అక్కడ ఎవరూ లేరు అని అనుకున్నాడు. కానీ మూలలో ఒక పాత photograph ఉంది — తాజాగా, ఈరోజే వాడినట్లు. "
    "దాన్ని తీసుకుని చూసాడు. అందులో ఒక మనిషి — అతనికి తెలిసిన మనిషి.\n\n"
    "గుండె ఒక్కసారిగా వేగంగా కొట్టుకుంది. బయట నుండి తలుపు sound వచ్చింది. అది గాలి కాదు. "
    "రవి వెనక్కి తిరిగాడు. అక్కడ ఒక నీడ — ఆ నీడ కదులుతోంది. శ్వాస తగ్గిపోయింది. చేతులు వణికాయి.\n\n"
    "కానీ — ఆ నీడ రవి చనిపోయిన తమ్ముడిది. తమ్ముడు 10 సంవత్సరాల ముందు పోయాడు. "
    "ఆ photograph లో ఉన్న మనిషి — తమ్ముడే. ఈ ఇల్లు తమ్ముడికి తెలుసు అని రవికి తెలియదు.\n\n"
    "ఆ తలుపు మళ్ళీ ఎప్పుడూ తెరవలేదు."
)


def test_target_length_script_passes_word_count():
    result = validate_script(_make_script(_GOOD_SCRIPT_120W))
    assert not any("too short" in i.lower() for i in result.issues)


# ── Good script passes ─────────────────────────────────────────────────────

def test_good_script_passes():
    result = validate_script(_make_script(_GOOD_SCRIPT_120W))
    assert result.passed is True
    assert result.quality_score >= 60


def test_good_script_gets_approve_candidate_or_needs_rewrite():
    text = (
        "ఆ రాత్రి గుండె ఆగిపోయింది — లోపల ఏదో ఉంది.\n\n"
        "రవి ఆ పాత ఇల్లు తెరిచాడు. గాలి ఆగింది. మూలలో పాత photograph — తాజాగా అక్కడ పెట్టినట్లు ఉంది. "
        "దాన్ని తీసుకుని చదివాడు. అందులో ఒక పేరు — అతని తండ్రి పేరు. కానీ photograph లో మనిషి వేరే.\n\n"
        "గుండె వేగంగా కొట్టుకుంది. అకస్మాత్తుగా — తలుపు మూసుకుంది. అది గాలి కాదు.\n\n"
        "కానీ — ఆ గది లో ఎవరూ లేరు. "
        "ఆ photograph లో ఉన్న మనిషి — రవి తండ్రి కాదు. వేరే మనిషి. తండ్రి తెలిసిన మనిషి.\n\n"
        "ఆ తలుపు మళ్ళీ ఎప్పుడూ తెరవలేదు."
    )
    result = validate_script(_make_script(text))
    assert result.publish_recommendation in ("approve_candidate", "needs_rewrite")


# ── Summary-like narration ─────────────────────────────────────────────────

def test_summary_like_script_gets_warning():
    text = (
        "ఒక కొడుకు తండ్రి మరణానంతరం ఒక sealed ఉత్తరం అందుకుంటాడు. "
        "తెరవడానికి 'ఒక సంవత్సరం తర్వాత తెరవు' అని రాశాడు. "
        "ఉత్తరంలో తండ్రి ఒక పాత నేరం వివరించాడు. "
        "అది కప్పిపుచ్చుకోవడానికి కుటుంబం మొత్తం చాలా ఏళ్ళుగా అబద్ధాలు చెప్పింది. "
        "గాలి ఆగింది. కానీ — అది అప్పుడు నిజం అయింది. ఆ ఉత్తరం ఇప్పటికీ అక్కడే ఉంది."
    )
    result = validate_script(_make_script(text))
    assert any("Summary" in i or "summary" in i for i in result.issues)


# ── Monetization safety ────────────────────────────────────────────────────

def test_monetization_risk_fails():
    text = (
        "ఆ రాత్రి గాలి ఆగింది. రవి ఆ ఇల్లు తెరిచాడు. కానీ — "
        "ఆ రాజకీయ విషయం బయటపడింది. ఆ తలుపు మళ్ళీ ఎప్పుడూ తెరవలేదు."
    )
    result = validate_script(_make_script(text))
    assert result.passed is False
    assert any("Monetization risk" in i for i in result.issues)


# ── validate_script returns ScriptQualityResult ───────────────────────────

def test_validate_returns_dataclass():
    script = _make_script("ఆ రాత్రి. గాలి ఆగింది. కానీ — రవి వెళ్ళిపోయాడు.")
    result = validate_script(script)
    assert isinstance(result, ScriptQualityResult)
    assert isinstance(result.quality_score, int)
    assert isinstance(result.issues, list)
    assert isinstance(result.suggestions, list)
    assert result.publish_recommendation in ("approve_candidate", "needs_rewrite", "reject")


def test_validate_to_dict():
    script = _make_script("ఆ రాత్రి. గాలి ఆగింది. కానీ — రవి వెళ్ళిపోయాడు.")
    d = validate_script(script).to_dict()
    assert "passed" in d
    assert "quality_score" in d
    assert "issues" in d
    assert "suggestions" in d
    assert "publish_recommendation" in d


# ── generate_script integration ───────────────────────────────────────────

def test_generated_script_no_banned_endings():
    idea = _make_idea()
    script = generate_script(idea)
    for banned in BANNED_ENDINGS:
        assert banned not in script.full_script_telugu, (
            f"Banned pattern found in generated script: {banned!r}"
        )


def test_generated_script_word_count():
    idea = _make_idea()
    script = generate_script(idea)
    words = script.full_script_telugu.split()
    # Minimum 60 words from the generator; validator enforces 80+ separately
    assert len(words) >= 60, f"Script too short: {len(words)} words"


# ── Review Markdown includes script quality section ───────────────────────

def test_review_markdown_includes_quality_section(tmp_path):
    from workers.review_queue import create_review

    sq_data = {
        "passed": True,
        "quality_score": 78,
        "issues": ["Hook lacks tension."],
        "suggestions": ["Open with a mystery line."],
        "publish_recommendation": "approve_candidate",
    }
    _, md_path = create_review(
        title="Test",
        category="midnight_mystery",
        hook="ఆ రాత్రి —",
        script_text="ఆ రాత్రి గాలి ఆగింది.",
        script_quality=sq_data,
        output_dir=tmp_path,
    )
    content = md_path.read_text(encoding="utf-8")
    assert "Script Quality Validation" in content
    assert "78/100" in content
    assert "approve_candidate" in content.lower() or "Approve Candidate" in content
    assert "Hook lacks tension" in content
    assert "Open with a mystery line" in content


def test_review_markdown_shows_reject_recommendation(tmp_path):
    from workers.review_queue import create_review

    sq_data = {
        "passed": False,
        "quality_score": 30,
        "issues": ["Script too short.", "Banned ending pattern found."],
        "suggestions": ["Expand narration."],
        "publish_recommendation": "reject",
    }
    _, md_path = create_review(
        title="Reject Test",
        category="midnight_mystery",
        hook="hook",
        script_quality=sq_data,
        output_dir=tmp_path,
    )
    content = md_path.read_text(encoding="utf-8")
    assert "Reject" in content
    assert "30/100" in content
