"""Tests for Pydantic data models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from workers.models import (
    AnalyticsRecord,
    ContentCategory,
    ReviewStatus,
    Scene,
    ScenePlan,
    StoryIdea,
    StoryScript,
    VideoDraft,
)


def _make_idea(**kwargs) -> StoryIdea:
    defaults = dict(
        id="idea_abc123",
        title="Test Title",
        category=ContentCategory.MIDNIGHT_MYSTERY,
        hook="Hook line",
        premise="Some premise",
        twist="Twist ending",
        tone="suspenseful",
    )
    defaults.update(kwargs)
    return StoryIdea(**defaults)


def _make_script(**kwargs) -> StoryScript:
    defaults = dict(
        id="script_abc",
        idea_id="idea_abc123",
        title="Test Script",
        category=ContentCategory.MIDNIGHT_MYSTERY,
        hook_line="Hook",
        full_script_telugu="Telugu script content here...",
    )
    defaults.update(kwargs)
    return StoryScript(**defaults)


def _make_scene(n: int) -> Scene:
    return Scene(
        scene_number=n,
        timestamp_range=f"00:{(n-1)*8:02d}-00:{n*8:02d}",
        narration_line="narration",
        visual_description="visual",
        location="place",
        mood="tense",
        camera_angle="close-up",
        motion_direction="zoom in",
        image_prompt="prompt",
    )


class TestStoryIdea:
    def test_valid_creation(self):
        idea = _make_idea()
        assert idea.id == "idea_abc123"
        assert idea.category == "midnight_mystery"

    def test_duration_default(self):
        idea = _make_idea()
        assert idea.estimated_duration_seconds == 55

    def test_duration_bounds(self):
        with pytest.raises(ValidationError):
            _make_idea(estimated_duration_seconds=10)
        with pytest.raises(ValidationError):
            _make_idea(estimated_duration_seconds=200)

    def test_json_serialization(self):
        idea = _make_idea()
        data = idea.model_dump_json()
        assert "midnight_mystery" in data


class TestStoryScript:
    def test_valid_creation(self):
        s = _make_script()
        assert s.id == "script_abc"

    def test_created_at_set(self):
        s = _make_script()
        assert s.created_at is not None

    def test_json_round_trip(self):
        s = _make_script()
        restored = StoryScript.model_validate_json(s.model_dump_json())
        assert restored.id == s.id


class TestScenePlan:
    def test_valid_scene_count(self):
        scenes = [_make_scene(i) for i in range(1, 8)]
        plan = ScenePlan(id="sp1", script_id="s1", title="T", total_scenes=7, scenes=scenes)
        assert plan.total_scenes == 7

    def test_too_few_scenes_raises(self):
        scenes = [_make_scene(i) for i in range(1, 4)]
        with pytest.raises(ValidationError):
            ScenePlan(id="sp1", script_id="s1", title="T", total_scenes=3, scenes=scenes)

    def test_too_many_scenes_raises(self):
        scenes = [_make_scene(i) for i in range(1, 12)]
        with pytest.raises(ValidationError):
            ScenePlan(id="sp1", script_id="s1", title="T", total_scenes=11, scenes=scenes)


class TestReviewStatus:
    def test_default_status(self):
        r = ReviewStatus(id="r1", title="T", category="midnight_mystery", hook="h")
        assert r.status == "needs_review"

    def test_checklist_defaults(self):
        r = ReviewStatus(id="r1", title="T", category="midnight_mystery", hook="h")
        assert r.checklist.no_auto_publish is True
        assert r.checklist.final_human_review_required is True
        assert r.checklist.strong_first_3_seconds is False


class TestVideoDraft:
    def test_defaults(self):
        d = VideoDraft(
            id="v1", title="T", category="midnight_mystery",
            scene_plan_id="sp1",
        )
        assert d.width == 1080
        assert d.height == 1920
        assert d.fps == 30
        assert d.is_dry_run is False


class TestAnalyticsRecord:
    def test_valid(self):
        r = AnalyticsRecord(video_id="v1", title="T", category="midnight_mystery")
        assert r.status == "draft"
