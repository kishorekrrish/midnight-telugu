"""Tests for review markdown generation."""

from __future__ import annotations

from workers.models import ReviewChecklist, ReviewStatus, ReviewStatusEnum
from workers.review_queue import _build_review_markdown, create_review


def _make_review(**kwargs) -> ReviewStatus:
    defaults = dict(
        id="review_test123",
        title="Test Story",
        category="midnight_mystery",
        hook="రాత్రి 2 గంటలకి తలుపు తట్టింది.",
        status=ReviewStatusEnum.NEEDS_REVIEW,
        checklist=ReviewChecklist(),
    )
    defaults.update(kwargs)
    return ReviewStatus(**defaults)


class TestReviewMarkdown:
    def test_markdown_contains_title(self):
        review = _make_review()
        md = _build_review_markdown(review)
        assert "Test Story" in md

    def test_markdown_contains_hook(self):
        review = _make_review()
        md = _build_review_markdown(review)
        assert review.hook in md

    def test_markdown_contains_review_id(self):
        review = _make_review()
        md = _build_review_markdown(review)
        assert review.id in md

    def test_markdown_contains_approve_command(self):
        review = _make_review()
        md = _build_review_markdown(review)
        assert "approve" in md
        assert "reject" in md

    def test_markdown_contains_no_upload_warning(self):
        review = _make_review()
        md = _build_review_markdown(review)
        assert "upload" in md.lower() or "YouTube" in md

    def test_markdown_contains_checklist(self):
        review = _make_review()
        md = _build_review_markdown(review)
        assert "final_human_review_required" in md.lower() or "Final human review" in md

    def test_markdown_with_script_text(self):
        review = _make_review()
        md = _build_review_markdown(review, script_text="ఒక రహస్య కథ.")
        assert "ఒక రహస్య కథ." in md

    def test_markdown_with_scene_table(self):
        review = _make_review()
        table = "| # | Timestamp |\n|---|---|\n| 1 | 00:00-00:08 |"
        md = _build_review_markdown(review, scene_table=table)
        assert "Scene Table" in md
        assert "00:00-00:08" in md

    def test_markdown_with_youtube_metadata(self):
        review = _make_review()
        md = _build_review_markdown(
            review,
            youtube_title="Test Title | Midnight Telugu",
            youtube_hashtags=["MidnightTelugu", "TeluguShorts"],
        )
        assert "YouTube Metadata" in md
        assert "#MidnightTelugu" in md

    def test_markdown_with_score_breakdown(self):
        review = _make_review()
        md = _build_review_markdown(
            review,
            score_breakdown={"hook_strength": 12, "originality": 10},
        )
        assert "Quality Score" in md
        assert "12" in md

    def test_markdown_with_repeatability_warnings(self):
        review = _make_review()
        md = _build_review_markdown(
            review,
            repeatability_warnings=["Category repeated 4 times."],
        )
        assert "Repeatability" in md
        assert "Category repeated 4 times." in md

    def test_directed_script_failure_never_marks_review_ready(self):
        review = _make_review()
        md = _build_review_markdown(
            review,
            script_quality={
                "passed": True,
                "quality_score": 92,
                "issues": [],
                "suggestions": [],
                "publish_recommendation": "approve_candidate",
            },
            telugu_quality={
                "telugu_authenticity_score": 100,
                "english_word_issues": [],
                "suggested_replacements": [],
                "suggestions": [],
            },
            continuity={
                "continuity_score": 92,
                "issues": [],
                "suggestions": [],
            },
            directed_script_info={
                "provider": "mock",
                "blueprint_id": "blueprint_1",
                "narrative_score": 68,
                "hard_failures": ["FINAL_TWIST_UNCLEAR"],
                "quality_score": 92,
                "telugu_authenticity_score": 100,
                "continuity_score": 68,
                "issues_fixed": [],
                "remaining_issues": ["Final twist does not echo the hook."],
                "recommendation": "needs_rewrite",
                "approved_for_scene_planning": False,
            },
        )
        assert "needs_script_rewrite" in md
        assert "draft_ready_for_human_review" not in md

    def test_directed_script_success_marks_review_ready(self):
        review = _make_review()
        md = _build_review_markdown(
            review,
            script_quality={
                "passed": True,
                "quality_score": 91,
                "issues": [],
                "suggestions": [],
                "publish_recommendation": "approve_candidate",
            },
            telugu_quality={
                "telugu_authenticity_score": 95,
                "english_word_issues": [],
                "suggested_replacements": [],
                "suggestions": [],
            },
            continuity={
                "continuity_score": 94,
                "issues": [],
                "suggestions": [],
            },
            directed_script_info={
                "provider": "mock",
                "blueprint_id": "blueprint_1",
                "narrative_score": 94,
                "hard_failures": [],
                "quality_score": 91,
                "telugu_authenticity_score": 95,
                "continuity_score": 94,
                "issues_fixed": ["Hook now connects to the clue."],
                "remaining_issues": [],
                "recommendation": "approve_candidate",
                "approved_for_scene_planning": True,
            },
        )
        assert "draft_ready_for_human_review" in md


class TestCreateReview:
    def test_creates_json_and_markdown(self, tmp_path):
        review, md_path = create_review(
            title="Test Story",
            category="midnight_mystery",
            hook="Hook line",
            output_dir=tmp_path,
        )
        json_path = tmp_path / f"{review.id}.json"
        assert json_path.exists()
        assert md_path.exists()
        assert md_path.suffix == ".md"

    def test_review_status_is_needs_review(self, tmp_path):
        review, _ = create_review(
            title="Test",
            category="midnight_mystery",
            hook="Hook",
            output_dir=tmp_path,
        )
        assert review.status == "needs_review"

    def test_markdown_includes_story_data(self, tmp_path):
        review, md_path = create_review(
            title="Test Story",
            category="midnight_mystery",
            hook="ఆ రాత్రి —",
            script_text="Full script here",
            output_dir=tmp_path,
        )
        content = md_path.read_text(encoding="utf-8")
        assert "Test Story" in content
        assert "Full script here" in content
