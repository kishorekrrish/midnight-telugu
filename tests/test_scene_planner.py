"""Tests for scene planner."""

from __future__ import annotations

from workers.models import ContentCategory, HumanizedScript, StoryScript
from workers.scene_planner import plan_scenes


def _make_script() -> StoryScript:
    return StoryScript(
        id="s1",
        idea_id="i1",
        title="Test Script",
        category=ContentCategory.MIDNIGHT_MYSTERY,
        hook_line="Hook line here",
        full_script_telugu=(
            "పేరా 1 — ఒక పరిచయం.\n\n"
            "పేరా 2 — నేపథ్యం.\n\n"
            "పేరా 3 — సమస్య.\n\n"
            "పేరా 4 — సంఘర్షణ.\n\n"
            "పేరా 5 — మలుపు.\n\n"
            "పేరా 6 — ముగింపు.\n\n"
            "పేరా 7 — చివరి వాక్యం."
        ),
        estimated_duration_seconds=55,
    )


def _make_humanized() -> HumanizedScript:
    return HumanizedScript(
        id="h1",
        script_id="s1",
        title="Humanized Script",
        category=ContentCategory.PSYCHOLOGICAL_TWIST,
        hook_line="Hook",
        full_script_telugu=(
            "భాగం 1.\n\nభాగం 2.\n\nభాగం 3.\n\nభాగం 4.\n\nభాగం 5.\n\nభాగం 6.\n\nభాగం 7."
        ),
        estimated_duration_seconds=55,
    )


class TestPlanScenes:
    def test_default_scene_count(self):
        script = _make_script()
        plan = plan_scenes(script)
        assert 6 <= len(plan.scenes) <= 10
        assert plan.total_scenes == len(plan.scenes)

    def test_min_scenes(self):
        script = _make_script()
        plan = plan_scenes(script, num_scenes=6)
        assert len(plan.scenes) == 6

    def test_max_scenes(self):
        script = _make_script()
        plan = plan_scenes(script, num_scenes=10)
        assert len(plan.scenes) == 10

    def test_clamps_below_min(self):
        script = _make_script()
        plan = plan_scenes(script, num_scenes=3)
        assert len(plan.scenes) == 6

    def test_clamps_above_max(self):
        script = _make_script()
        plan = plan_scenes(script, num_scenes=15)
        assert len(plan.scenes) == 10

    def test_scene_has_required_fields(self):
        script = _make_script()
        plan = plan_scenes(script)
        for scene in plan.scenes:
            assert scene.scene_number >= 1
            assert scene.timestamp_range
            assert scene.narration_line
            assert scene.visual_description
            assert scene.location
            assert scene.mood
            assert scene.camera_angle
            assert scene.motion_direction
            assert scene.image_prompt
            assert scene.negative_prompt

    def test_scene_numbers_sequential(self):
        script = _make_script()
        plan = plan_scenes(script, num_scenes=7)
        for i, scene in enumerate(plan.scenes):
            assert scene.scene_number == i + 1

    def test_accepts_humanized_script(self):
        humanized = _make_humanized()
        plan = plan_scenes(humanized)
        assert plan.total_scenes >= 6

    def test_plan_has_id_and_title(self):
        script = _make_script()
        plan = plan_scenes(script)
        assert plan.id.startswith("scenes_")
        assert plan.title == script.title
