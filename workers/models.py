"""Pydantic data models for the Midnight Telugu pipeline."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, model_validator


def _now() -> datetime:
    return datetime.now(UTC)


class ContentCategory(StrEnum):
    MIDNIGHT_MYSTERY = "midnight_mystery"
    VILLAGE_MYSTERY = "village_mystery"
    FAMILY_SUSPENSE = "family_suspense"
    PSYCHOLOGICAL_TWIST = "psychological_twist"
    STRANGE_EVENT = "strange_event"
    SOFT_HORROR = "soft_horror"
    CRIME_NO_VIOLENCE = "crime_no_violence"
    EMOTIONAL_SUSPENSE = "emotional_suspense"
    KARMA_JUSTICE = "karma_justice"
    POOR_VS_RICH = "poor_vs_rich"


class ReviewStatusEnum(StrEnum):
    NEEDS_REVIEW = "needs_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class StoryIdea(BaseModel):
    id: str
    title: str
    category: ContentCategory
    hook: str = Field(..., description="First 3-second attention grabber")
    premise: str
    twist: str
    tone: str
    estimated_duration_seconds: int = Field(default=55, ge=30, le=90)
    originality_notes: str = ""
    safety_notes: str = ""
    # Quality metadata fields
    hook_type: str = ""
    twist_type: str = ""
    emotional_core: str = ""
    visual_signature: str = ""
    risk_flags: list[str] = Field(default_factory=list)
    story_score: int = 0
    score_breakdown: dict = Field(default_factory=dict)
    repeatability_warnings: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_now)

    model_config = {"use_enum_values": True}


class StoryScript(BaseModel):
    id: str
    idea_id: str
    blueprint_id: str | None = None
    title: str
    category: ContentCategory
    hook_line: str
    full_script_telugu: str
    estimated_duration_seconds: int = Field(default=55, ge=30, le=90)
    youtube_title: str = ""
    youtube_description: str = ""
    youtube_hashtags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)

    model_config = {"use_enum_values": True}


class HumanizedScript(BaseModel):
    id: str
    script_id: str
    title: str
    category: ContentCategory
    hook_line: str
    full_script_telugu: str
    humanization_notes: str = ""
    estimated_duration_seconds: int = Field(default=55, ge=30, le=90)
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)

    model_config = {"use_enum_values": True}


class DirectedScript(BaseModel):
    id: str
    source_script_id: str
    blueprint_id: str = ""
    title: str
    category: ContentCategory
    hook_line: str
    directed_telugu_script: str
    director_provider: str = "mock"
    narrative_score: int = 0
    hard_failures: list[str] = Field(default_factory=list)
    narrative_facts: dict = Field(default_factory=dict)
    quality_score: int = 0
    telugu_authenticity_score: int = 0
    continuity_score: int = 0
    issues_fixed: list[str] = Field(default_factory=list)
    remaining_issues: list[str] = Field(default_factory=list)
    recommendation: str = "needs_rewrite"
    approved_for_scene_planning: bool = False
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)

    model_config = {"use_enum_values": True}


class Scene(BaseModel):
    scene_number: int = Field(..., ge=1)
    timestamp_range: str = Field(..., description="e.g. '00:00-00:07'")
    narration_line: str
    visual_description: str
    characters_present: list[str] = Field(default_factory=list)
    location: str
    mood: str
    camera_angle: str
    motion_direction: str
    image_prompt: str
    negative_prompt: str = ""


class ScenePlan(BaseModel):
    id: str
    script_id: str
    title: str
    total_scenes: int
    scenes: list[Scene]
    created_at: datetime = Field(default_factory=_now)

    @model_validator(mode="after")
    def validate_scene_count(self) -> ScenePlan:
        if not (6 <= len(self.scenes) <= 10):
            raise ValueError(f"ScenePlan must have 6-10 scenes, got {len(self.scenes)}")
        return self


class VoiceAsset(BaseModel):
    id: str
    script_id: str
    provider: str = "mock"
    language: str = "te-IN"
    audio_path: str | None = None
    duration_seconds: float | None = None
    created_at: datetime = Field(default_factory=_now)


class ImageAsset(BaseModel):
    id: str
    scene_number: int
    scene_plan_id: str
    provider: str = "mock"
    image_path: str | None = None
    image_prompt: str = ""
    created_at: datetime = Field(default_factory=_now)


class VideoDraft(BaseModel):
    id: str
    title: str
    category: ContentCategory
    scene_plan_id: str
    voice_asset_id: str | None = None
    image_asset_ids: list[str] = Field(default_factory=list)
    video_path: str | None = None
    thumbnail_path: str | None = None
    width: int = 1080
    height: int = 1920
    fps: int = 30
    duration_seconds: float | None = None
    is_dry_run: bool = False
    ffmpeg_command: str | None = None
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)

    model_config = {"use_enum_values": True}


class ReviewChecklist(BaseModel):
    strong_first_3_seconds: bool = False
    original_story: bool = False
    no_copied_plot: bool = False
    natural_telugu: bool = False
    family_safe: bool = False
    monetization_safe: bool = False
    no_graphic_violence: bool = False
    no_political_or_religious_controversy: bool = False
    no_auto_publish: bool = True
    visual_consistency: bool = False
    audio_quality_ok: bool = False
    subtitles_ok: bool = False
    final_human_review_required: bool = True


class ReviewStatus(BaseModel):
    id: str
    title: str
    category: ContentCategory
    hook: str
    script_path: str | None = None
    scene_plan_path: str | None = None
    audio_path: str | None = None
    image_paths: list[str] = Field(default_factory=list)
    video_path: str | None = None
    status: ReviewStatusEnum = ReviewStatusEnum.NEEDS_REVIEW
    checklist: ReviewChecklist = Field(default_factory=ReviewChecklist)
    reviewer_notes: str = ""
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)

    model_config = {"use_enum_values": True}


class AnalyticsRecord(BaseModel):
    video_id: str
    title: str
    category: ContentCategory
    hook_type: str = ""
    duration_seconds: int = 0
    status: str = "draft"
    created_at: datetime = Field(default_factory=_now)
    published_at: datetime | None = None
    notes: str = ""

    model_config = {"use_enum_values": True}


class PerformanceRecord(BaseModel):
    video_id: str
    date: str
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    average_view_duration: float = 0.0
    retention_percentage: float = 0.0
    subscribers_gained: int = 0
    notes: str = ""


class StoryBlueprint(BaseModel):
    id: str
    idea_id: str
    title: str
    category: ContentCategory
    protagonist_name: str
    protagonist_role: str
    point_of_view: Literal["first_person", "third_person"]
    hook: str
    central_question: str
    primary_story_device: str
    primary_clue: str
    supporting_clues: list[str] = Field(default_factory=list)
    setup: str
    escalation: str
    reveal: str
    final_twist: str
    final_line: str
    locations: list[str] = Field(default_factory=list)
    forbidden_elements: list[str] = Field(default_factory=list)
    opening_image: str = ""
    first_3_seconds_hook: str = ""
    protagonist_desire: str = ""
    hidden_truth: str = ""
    early_clue: str = ""
    misdirection: str = ""
    midpoint_turn: str = ""
    reveal_mechanism: str = ""
    final_recontextualization: str = ""
    replay_value_clue: str = ""
    emotional_aftertaste: str = ""
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)

    model_config = {"use_enum_values": True}


class NarrativeFacts(BaseModel):
    protagonist_names: list[str] = Field(default_factory=list)
    detected_point_of_view: str = "unknown"
    major_objects: list[str] = Field(default_factory=list)
    clues: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    explicit_reveal: str = ""
    final_twist: str = ""
    unresolved_promises: list[str] = Field(default_factory=list)
    meta_narration_hits: list[str] = Field(default_factory=list)
