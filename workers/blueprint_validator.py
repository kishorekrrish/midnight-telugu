"""Validation rules for structured story blueprints."""

from __future__ import annotations

from dataclasses import dataclass, field

from workers.models import StoryBlueprint


@dataclass
class BlueprintValidationResult:
    passed: bool
    score: int
    hard_failures: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)


def validate_blueprint(blueprint: StoryBlueprint) -> BlueprintValidationResult:
    score = 100
    hard_failures: list[str] = []
    issues: list[str] = []
    suggestions: list[str] = []

    if not blueprint.protagonist_name.strip():
        hard_failures.append("MISSING_PROTAGONIST")
    if blueprint.point_of_view not in ("first_person", "third_person"):
        hard_failures.append("MISSING_POV")
    if " మరియు " in blueprint.primary_story_device or "," in blueprint.primary_story_device:
        hard_failures.append("MULTIPLE_PRIMARY_DEVICES")
    if len(blueprint.supporting_clues) > 2:
        hard_failures.append("TOO_MANY_SUPPORTING_CLUES")
    if not blueprint.central_question.strip():
        hard_failures.append("MISSING_CENTRAL_QUESTION")
    if not blueprint.reveal.strip():
        hard_failures.append("MISSING_REVEAL")
    if not blueprint.final_twist.strip():
        hard_failures.append("MISSING_FINAL_TWIST")
    if not blueprint.final_line.strip():
        hard_failures.append("MISSING_FINAL_LINE")
    if len(blueprint.locations) > 2:
        hard_failures.append("TOO_MANY_LOCATIONS")
    if blueprint.primary_clue not in " ".join(
        [blueprint.escalation, blueprint.reveal, blueprint.final_twist, blueprint.final_line]
    ):
        hard_failures.append("CLUE_WITHOUT_PAYOFF")

    question_words = {
        word
        for word in blueprint.central_question.replace("?", "").replace("—", " ").split()
        if len(word) > 2 and word not in {"ఏమిటి", "ఏమిటి?", "నిజం", "ఎమిటి"}
    }
    twist_text = blueprint.final_twist.replace("—", " ")
    answer_signals = question_words | {
        blueprint.primary_story_device,
        blueprint.primary_clue,
        blueprint.protagonist_name,
    }
    if answer_signals and not any(signal and signal in twist_text for signal in answer_signals):
        hard_failures.append("FINAL_TWIST_DOES_NOT_ANSWER_QUESTION")

    if blueprint.primary_story_device == blueprint.primary_clue:
        issues.append("Primary story device and primary clue are identical.")
        suggestions.append("Keep the clue concrete and the device slightly broader.")
        score -= 8

    if len(blueprint.locations) == 0:
        issues.append("No location defined.")
        suggestions.append("Add one anchored location for the whole story.")
        score -= 10

    if len(blueprint.final_line.split()) < 5:
        issues.append("Final line is too short to land emotionally.")
        suggestions.append("Make the final line feel like a spoken cinematic aftershock.")
        score -= 6

    score = max(0, score - 12 * len(hard_failures))
    return BlueprintValidationResult(
        passed=not hard_failures,
        score=score,
        hard_failures=hard_failures,
        issues=issues,
        suggestions=suggestions,
    )
