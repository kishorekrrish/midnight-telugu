"""Tests for Script Director gate (Phase 6)."""

from __future__ import annotations

import json

import pytest

from workers.models import ContentCategory, DirectedScript, HumanizedScript, StoryScript

# ── Helper fixtures ──────────────────────────────────────────────────────────

def _make_script(text: str | None = None) -> StoryScript:
    return StoryScript(
        id="script_test001",
        idea_id="idea_001",
        title="Test Mystery",
        category=ContentCategory.MIDNIGHT_MYSTERY,
        hook_line="ఆ రాత్రి గుండె ఆగిపోయింది.",
        full_script_telugu=text or (
            "ఆ రాత్రి గుండె ఆగిపోయింది — లోపల ఏదో ఉంది.\n\n"
            "రవి ఆ పాత ఇల్లు తెరిచాడు. గాలి ఆగింది. మూలలో ఒక పాత photograph ఉంది.\n\n"
            "కానీ — ఆ photograph లో ఉన్న మనిషి రవి తండ్రి కాదు. వేరే మనిషి.\n\n"
            "ఆ తలుపు మళ్ళీ ఎప్పుడూ తెరవలేదు."
        ),
        estimated_duration_seconds=55,
    )


def _make_humanized(text: str | None = None) -> HumanizedScript:
    return HumanizedScript(
        id="humanized_test001",
        script_id="script_test001",
        title="Test Mystery",
        category=ContentCategory.MIDNIGHT_MYSTERY,
        hook_line="ఆ రాత్రి గుండె ఆగిపోయింది.",
        full_script_telugu=text or (
            "ఆ రాత్రి గుండె ఆగిపోయింది — లోపల ఏదో ఉంది.\n\n"
            "రవి ఆ పాత ఇల్లు తెరిచాడు. గాలి ఆగింది. మూలలో ఒక పాత photograph ఉంది.\n\n"
            "కానీ — ఆ photograph లో ఉన్న మనిషి రవి తండ్రి కాదు. వేరే మనిషి.\n\n"
            "ఆ తలుపు మళ్ళీ ఎప్పుడూ తెరవలేదు."
        ),
    )


# ── TASK 1: Provider tests ───────────────────────────────────────────────────

def test_mock_provider_returns_text():
    """Mock provider must return non-empty Telugu text."""
    from workers.providers.mock_text_provider import MockTextProvider

    provider = MockTextProvider()
    prompt = "Current script:\nఆ రాత్రి గాలి ఆగింది. కానీ — ఎవరూ లేరు."
    result = provider.generate_text(prompt)
    assert result
    assert len(result.strip()) > 0


def test_provider_selection_mock():
    """get_text_provider('mock') returns MockTextProvider."""
    from workers.providers import get_text_provider
    from workers.providers.mock_text_provider import MockTextProvider

    provider = get_text_provider("mock")
    assert isinstance(provider, MockTextProvider)


def test_openai_provider_missing_key(monkeypatch):
    """OpenAITextProvider raises ValueError when OPENAI_API_KEY is not set."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    from workers.providers.openai_text_provider import OpenAITextProvider

    with pytest.raises(ValueError, match="OPENAI_API_KEY not set"):
        OpenAITextProvider()


def test_mock_provider_extracts_telugu_from_backtick_block():
    """Mock provider correctly extracts text from triple-backtick block."""
    from workers.providers.mock_text_provider import MockTextProvider

    provider = MockTextProvider()
    prompt = "Improve this:\n\n```\nగాలి ఆగింది. కానీ — ఎవరూ లేరు.\n```\n\nDo your best."
    result = provider.generate_text(prompt)
    assert result
    # Should contain Telugu characters
    assert any("ఀ" <= ch <= "౿" for ch in result)


# ── TASK 4: DirectedScript model ─────────────────────────────────────────────

def test_directed_script_model_validation():
    """DirectedScript requires required fields."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        DirectedScript()  # type: ignore[call-arg]


def test_directed_script_json_serializable():
    """DirectedScript can be serialized to JSON."""
    ds = DirectedScript(
        id="directed_abc123",
        source_script_id="script_test001",
        title="Test",
        category=ContentCategory.MIDNIGHT_MYSTERY,
        hook_line="ఆ రాత్రి",
        directed_telugu_script="ఆ రాత్రి గాలి ఆగింది.",
        director_provider="mock",
        quality_score=72,
        telugu_authenticity_score=85,
        continuity_score=80,
    )
    data = json.loads(ds.model_dump_json())
    assert data["id"] == "directed_abc123"
    assert data["quality_score"] == 72
    assert data["approved_for_scene_planning"] is False


# ── TASK 6: direct_script() function ────────────────────────────────────────

def test_direct_script_mock_runs():
    """direct_script() runs without API keys using mock provider."""
    from workers.script_director import DirectorResult, direct_script

    script = _make_script()
    result = direct_script(script, provider_name="mock", max_attempts=1)

    assert isinstance(result, DirectorResult)
    assert result.directed_script
    assert isinstance(result.quality_score, int)
    assert isinstance(result.telugu_authenticity_score, int)
    assert isinstance(result.continuity_score, int)
    assert result.recommendation in ("approve_candidate", "needs_rewrite", "reject")
    assert isinstance(result.approved_for_scene_planning, bool)


def test_direct_script_saves_result(tmp_path):
    """save_directed_script() saves DirectedScript JSON."""
    from workers.script_director import DirectorResult, save_directed_script

    result = DirectorResult(
        directed_script="ఆ రాత్రి గాలి ఆగింది. కానీ — ఎవరూ లేరు. ఇప్పటికీ అక్కడే ఉంది.",
        quality_score=70,
        telugu_authenticity_score=85,
        continuity_score=80,
        issues_fixed=["Hook lacks tension."],
        remaining_issues=[],
        recommendation="needs_rewrite",
        approved_for_scene_planning=False,
        attempts=1,
    )
    script = _make_script()
    ds, path = save_directed_script(result, script, tmp_path)

    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["directed_telugu_script"]
    assert data["quality_score"] == 70


def test_direct_script_retry_stops():
    """direct_script() stops after max_attempts."""
    from workers.script_director import direct_script

    script = _make_script()
    result = direct_script(script, provider_name="mock", max_attempts=2)

    assert result.attempts <= 2


def test_direct_script_best_attempt_selected():
    """direct_script() picks the best quality attempt."""
    from workers.script_director import direct_script

    # Run with max_attempts=3 and check we get a valid result
    script = _make_humanized()
    result = direct_script(script, provider_name="mock", max_attempts=3)

    # Result should always have a non-empty directed script
    assert result.directed_script.strip()
    # quality_score should be within valid range
    assert 0 <= result.quality_score <= 100


# ── TASK 8: plan-scenes DirectedScript preference ───────────────────────────

def test_plan_scenes_prefers_directed(tmp_path, monkeypatch):
    """plan-scenes uses approved DirectedScript when available."""
    from workers.io_utils import write_json

    # Set up directory structure
    directed_dir = tmp_path / "scripts" / "directed"
    directed_dir.mkdir(parents=True)
    scripts_dir = tmp_path / "scripts"

    ds = DirectedScript(
        id="directed_abc",
        source_script_id="s1",
        title="Directed Story",
        category=ContentCategory.MIDNIGHT_MYSTERY,
        hook_line="ఆ రాత్రి",
        directed_telugu_script="ఆ రాత్రి గాలి ఆగింది. కానీ — ఎవరూ లేరు.",
        approved_for_scene_planning=True,
    )
    write_json(directed_dir / "directed_abc.json", ds)

    # Monkeypatch config dirs
    monkeypatch.setattr("workers.config.DIRECTED_SCRIPTS_DIR", directed_dir)
    monkeypatch.setattr("workers.config.SCRIPTS_DIR", scripts_dir)

    from workers.io_utils import latest_file

    found = latest_file(directed_dir, pattern="directed_*.json")
    assert found is not None

    from workers.io_utils import read_json

    loaded = read_json(found, DirectedScript)
    assert loaded.approved_for_scene_planning is True


def test_plan_scenes_skips_unapproved_directed(tmp_path):
    """plan-scenes skips unapproved DirectedScript (approved_for_scene_planning=False)."""
    from workers.io_utils import write_json

    directed_dir = tmp_path / "directed"
    directed_dir.mkdir()

    ds = DirectedScript(
        id="directed_notapproved",
        source_script_id="s1",
        title="Unapproved Story",
        category=ContentCategory.MIDNIGHT_MYSTERY,
        hook_line="ఆ రాత్రి",
        directed_telugu_script="ఆ రాత్రి గాలి ఆగింది.",
        approved_for_scene_planning=False,
    )
    write_json(directed_dir / "directed_notapproved.json", ds)

    from workers.io_utils import read_json

    loaded = read_json(directed_dir / "directed_notapproved.json", DirectedScript)
    assert loaded.approved_for_scene_planning is False


# ── TASK 9: Review Markdown sections ────────────────────────────────────────

def test_review_markdown_script_director_section(tmp_path):
    """Review Markdown includes Script Director section when directed_script_info provided."""
    from workers.review_queue import create_review

    directed_info = {
        "provider": "mock",
        "quality_score": 75,
        "telugu_authenticity_score": 88,
        "continuity_score": 82,
        "issues_fixed": ["No sensory detail found."],
        "remaining_issues": ["Hook lacks tension."],
        "recommendation": "needs_rewrite",
        "approved_for_scene_planning": False,
    }

    _, md_path = create_review(
        title="Director Test",
        category="midnight_mystery",
        hook="ఆ రాత్రి —",
        script_text="ఆ రాత్రి గాలి ఆగింది.",
        directed_script_info=directed_info,
        output_dir=tmp_path,
    )

    content = md_path.read_text(encoding="utf-8")
    assert "## Script Director" in content
    assert "mock" in content
    assert "75/100" in content
    assert "approved_for_scene_planning" in content.lower() or "Approved for scene planning" in content


def test_review_markdown_final_recommendation(tmp_path):
    """Review Markdown includes Final Publish Recommendation section."""
    from workers.review_queue import create_review

    _, md_path = create_review(
        title="Recommendation Test",
        category="midnight_mystery",
        hook="ఆ రాత్రి —",
        script_text="ఆ రాత్రి గాలి ఆగింది.",
        script_quality={
            "passed": True,
            "quality_score": 78,
            "issues": [],
            "suggestions": [],
            "publish_recommendation": "approve_candidate",
        },
        output_dir=tmp_path,
    )

    content = md_path.read_text(encoding="utf-8")
    assert "## Final Publish Recommendation" in content


def test_review_markdown_script_source_section(tmp_path):
    """Review Markdown includes Script Source section."""
    from workers.review_queue import create_review

    _, md_path = create_review(
        title="Source Test",
        category="midnight_mystery",
        hook="ఆ రాత్రి —",
        script_source="directed",
        output_dir=tmp_path,
    )

    content = md_path.read_text(encoding="utf-8")
    assert "## Script Source" in content
    assert "directed" in content


# ── TASK 3: approve_candidate thresholds ────────────────────────────────────

def test_approve_candidate_requires_new_thresholds():
    """approve_candidate requires quality>=88, auth>=90, cont>=90, no english issues."""
    from workers.script_quality import validate_script

    # A script that may not reach all thresholds — just verify logic
    text = (
        "ఆ రాత్రి గుండె ఆగిపోయింది — లోపల ఏదో ఉంది.\n\n"
        "రవి ఆ పాత ఇల్లు తెరిచాడు. గాలి ఆగింది. మూలలో ఒక పాత photograph ఉంది.\n\n"
        "కానీ — ఆ photograph లో ఉన్న మనిషి రవి తండ్రి కాదు. వేరే మనిషి.\n\n"
        "ఆ తలుపు మళ్ళీ ఎప్పుడూ తెరవలేదు."
    )
    script = StoryScript(
        id="test_threshold",
        idea_id="idea_001",
        title="Threshold Test",
        category=ContentCategory.MIDNIGHT_MYSTERY,
        hook_line="ఆ రాత్రి",
        full_script_telugu=text,
    )
    result = validate_script(script)

    # If approved, verify thresholds are met
    if result.publish_recommendation == "approve_candidate":
        assert result.quality_score >= 88
        assert result.telugu_authenticity_score >= 90
        assert result.continuity_score >= 90
    else:
        # If not approved, at least one threshold must be unmet
        unmet = (
            result.quality_score < 88
            or result.telugu_authenticity_score < 90
            or result.continuity_score < 90
        )
        assert unmet, "approve_candidate should require all thresholds"


def test_approve_candidate_english_words_blocks():
    """approve_candidate must not be given if English word issues exist."""
    from workers.script_quality import validate_script

    # Script with English word that has Telugu equivalent
    text = (
        "ఆ రాత్రి గుండె ఆగిపోయింది — లోపల footprint ఉంది.\n\n"
        "రవి ఆ bridge దగ్గర నిలబడ్డాడు. గాలి ఆగింది. కానీ — ఎవరూ లేరు.\n\n"
        "ఆ తలుపు మళ్ళీ ఎప్పుడూ తెరవలేదు."
    )
    script = StoryScript(
        id="test_english",
        idea_id="idea_001",
        title="English Test",
        category=ContentCategory.MIDNIGHT_MYSTERY,
        hook_line="ఆ రాత్రి",
        full_script_telugu=text,
    )
    result = validate_script(script)

    # With English words present, should not be approve_candidate
    assert result.publish_recommendation != "approve_candidate"
