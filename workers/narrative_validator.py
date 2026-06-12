"""Compare generated narrative facts against an approved blueprint."""

from __future__ import annotations

from dataclasses import dataclass, field

from workers.models import NarrativeFacts, StoryBlueprint

_OBJECT_ALIASES = {
    "వాయిస్ మెమో": {"వాయిస్ మెమో", "రికార్డింగ్", "గొంతు"},
    "పాత ఫోటో": {"పాత ఫోటో", "ఫోటో", "photograph"},
    "పిల్లాడు గీసిన బొమ్మ": {"పిల్లాడు గీసిన బొమ్మ", "పాప గీసిన బొమ్మ", "బొమ్మ"},
    "పెట్టె": {"పెట్టె", "పాత పెట్టె"},
}
_VAGUE_TWIST_MARKERS = {"ఏదో విషయం", "అనిపించింది", "పూర్తిగా చెప్పలేదు", "రహస్యం చెప్తుంది"}


@dataclass
class NarrativeValidationResult:
    passed: bool
    score: int
    hard_failures: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)


def _alias_set(value: str) -> set[str]:
    if not value:
        return set()
    aliases = {value}
    aliases.update(_OBJECT_ALIASES.get(value, set()))
    return {alias for alias in aliases if alias}


def _matches_expected(expected: str, candidates: list[str]) -> bool:
    aliases = _alias_set(expected)
    if not aliases:
        return False
    for candidate in candidates:
        if candidate in aliases:
            return True
        if any(alias in candidate or candidate in alias for alias in aliases):
            return True
    return False


def _location_matches(expected: str, actual: str) -> bool:
    expected_root = expected.replace(" గట్టు", "").replace(" దగ్గర", "").strip()
    actual_root = actual.replace(" గట్టు", "").replace(" దగ్గర", "").strip()
    return (
        expected == actual
        or expected in actual
        or actual in expected
        or (expected_root and expected_root == actual_root)
    )


def validate_narrative(
    blueprint: StoryBlueprint,
    facts: NarrativeFacts,
    hook_line: str,
) -> NarrativeValidationResult:
    score = 100
    hard_failures: list[str] = []
    issues: list[str] = []
    suggestions: list[str] = []

    hook_first_person = "నేను" in hook_line or "నాకు" in hook_line
    if facts.detected_point_of_view != "unknown" and facts.detected_point_of_view != blueprint.point_of_view:
        hard_failures.append("POV_MISMATCH")
    elif hook_first_person and blueprint.point_of_view == "third_person":
        hard_failures.append("POV_MISMATCH")
    if blueprint.protagonist_name not in facts.protagonist_names and facts.protagonist_names:
        hard_failures.append("PROTAGONIST_NAME_CHANGED")
    if len(facts.protagonist_names) > 1:
        hard_failures.append("MULTIPLE_PROTAGONISTS")
    if not (
        any(alias in hook_line for alias in _alias_set(blueprint.primary_story_device))
        or _matches_expected(blueprint.primary_story_device, facts.major_objects)
    ):
        hard_failures.append("PRIMARY_DEVICE_MISSING")
    if blueprint.primary_story_device in hook_line and blueprint.primary_story_device in facts.unresolved_promises:
        hard_failures.append("PRIMARY_DEVICE_NOT_RESOLVED")
    if blueprint.primary_clue and not (
        _matches_expected(blueprint.primary_clue, facts.clues)
        or _matches_expected(blueprint.primary_clue, facts.major_objects)
    ):
        hard_failures.append("PRIMARY_CLUE_MISSING")
    if blueprint.primary_clue in facts.unresolved_promises:
        hard_failures.append("PRIMARY_CLUE_NOT_RESOLVED")

    allowed_aliases: set[str] = set()
    for item in [blueprint.primary_story_device, blueprint.primary_clue, *blueprint.supporting_clues]:
        allowed_aliases.update(_alias_set(item))
    blueprint_text = " ".join(
        [
            blueprint.hook,
            blueprint.setup,
            blueprint.escalation,
            blueprint.reveal,
            blueprint.final_twist,
            blueprint.final_line,
        ]
    )
    for alias, variants in _OBJECT_ALIASES.items():
        if alias in blueprint_text or any(variant in blueprint_text for variant in variants):
            allowed_aliases.update({alias, *variants})
    unexpected_objects = [obj for obj in facts.major_objects if not any(_matches_expected(alias, [obj]) for alias in allowed_aliases)]
    if unexpected_objects:
        hard_failures.append("UNPLANNED_MAJOR_OBJECT")
        issues.append(f"Unexpected objects found: {', '.join(unexpected_objects[:3])}")

    unexpected_names = [name for name in facts.protagonist_names if name != blueprint.protagonist_name]
    if unexpected_names:
        hard_failures.append("PROTAGONIST_NAME_CHANGED")
        hard_failures.append("UNPLANNED_CHARACTER")
        issues.append(f"Unexpected character names found: {', '.join(unexpected_names[:3])}")

    unexpected_locations = [
        loc for loc in facts.locations
        if not any(_location_matches(expected, loc) for expected in blueprint.locations)
    ]
    if unexpected_locations:
        hard_failures.append("UNPLANNED_LOCATION")
        issues.append(f"Unexpected locations found: {', '.join(unexpected_locations[:3])}")

    if blueprint.central_question and not facts.explicit_reveal:
        hard_failures.append("PROMISED_REVEAL_NOT_SHOWN")
    if not facts.explicit_reveal:
        hard_failures.append("REVEAL_NOT_EXPLICIT")
    if (
        not facts.final_twist.strip()
        or len(facts.final_twist.split()) < 4
        or any(marker in facts.final_twist for marker in _VAGUE_TWIST_MARKERS)
    ):
        hard_failures.append("FINAL_TWIST_UNCLEAR")
    key_signals = {blueprint.protagonist_name, blueprint.primary_story_device, blueprint.primary_clue}
    hook_words = blueprint.hook.replace("—", " ").replace(".", " ").split()
    stopwords = {"అమ్మ", "తర్వాత", "ఆమె", "ఒక", "లో", "లోపల", "కనిపించింది"}
    key_signals.update(word for word in hook_words if len(word) > 2 and word not in stopwords)
    if not any(word in facts.final_twist for word in key_signals):
        hard_failures.append("FINAL_TWIST_NOT_CONNECTED_TO_HOOK")
    if facts.meta_narration_hits:
        hard_failures.append("META_OR_SUMMARY_NARRATION")
        issues.append(f"Meta/summary narration detected: {', '.join(facts.meta_narration_hits[:3])}")

    if any(obj in facts.final_twist for obj in ["అది", "అదిే", "అది అదే"]):
        hard_failures.append("AMBIGUOUS_OBJECT_REFERENCE")

    suggestions.extend([
        "Keep the same protagonist name from hook to final line.",
        "Resolve the primary device explicitly in the reveal or final twist.",
    ])
    score = max(0, score - (12 * len(hard_failures)) - (4 * len(issues)))

    return NarrativeValidationResult(
        passed=not hard_failures,
        score=score,
        hard_failures=hard_failures,
        issues=issues,
        suggestions=suggestions,
    )
