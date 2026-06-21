"""Extract deterministic narrative facts from a generated Telugu script."""

from __future__ import annotations

from workers.models import HumanizedScript, NarrativeFacts, StoryBlueprint, StoryScript
from workers.telugu_quality import FIRST_PERSON_MARKERS, THIRD_PERSON_MARKERS

_NAME_CANDIDATES = [
    "చంద్ర", "శ్యామ్", "కార్తీక్", "రవి", "అర్జున్", "కిరణ్", "మాలతి", "గీత", "అనిత", "లక్ష్మి",
]
_OBJECT_CANDIDATES = [
    "చివరి రైలు", "పాత ఫోటో", "స్టేషన్ మాస్టర్ రిజిస్టర్",
    "వాయిస్ మెమో", "రికార్డింగ్", "ఉత్తరం", "ఫోటో", "డైరీ", "పెట్టె", "తాళం", "బొమ్మ", "చీర",
]
_LOCATION_CANDIDATES = [
    "ప్లాట్‌ఫామ్", "రైల్వే స్టేషన్",
    "చెరువు", "చెరువు గట్టు", "చెరువు దగ్గర", "పాత ఇల్లు", "గది", "అలమర", "ఆసుపత్రి", "స్టేషన్", "బావి",
]
_META_PATTERNS = [
    "ఒక కొడుకు", "ఒక వ్యక్తి", "ఒక అమ్మాయి", "అనే భావనే", "ఈ కథలో",
    "చివర్లో తెలుస్తుంది", "రహస్యం చెప్తుంది", "నిజం అతని ముందే నిలబడ్డట్టు",
    "అతనికి అర్థమవుతూ వచ్చింది",
]
_DEVICE_ALIASES = {
    "చివరి రైలు": ["చివరి రైలు", "రైలు"],
    "వాయిస్ మెమో": ["వాయిస్ మెమో", "రికార్డింగ్", "గొంతు"],
    "పాత ఫోటో": ["పాత ఫోటో", "ఫోటో"],
    "పిల్లాడు గీసిన బొమ్మ": ["పిల్లాడు గీసిన బొమ్మ", "పాప గీసిన బొమ్మ", "బొమ్మ"],
    "స్టేషన్ మాస్టర్ రిజిస్టర్": ["స్టేషన్ మాస్టర్ రిజిస్టర్", "రిజిస్టర్"],
}


def _paragraphs(text: str) -> list[str]:
    return [p.strip() for p in text.split("\n\n") if p.strip()]


def extract_narrative_facts(
    script: StoryScript | HumanizedScript,
    blueprint: StoryBlueprint | None = None,
) -> NarrativeFacts:
    text = script.full_script_telugu
    paragraphs = _paragraphs(text)

    protagonist_names = [name for name in _NAME_CANDIDATES if name in text]
    fp = sum(text.count(marker) for marker in FIRST_PERSON_MARKERS)
    tp = sum(text.count(marker) for marker in THIRD_PERSON_MARKERS)
    if fp > tp and fp > 0:
        pov = "first_person"
    elif tp > 0:
        pov = "third_person"
    else:
        pov = "unknown"

    major_objects = [obj for obj in _OBJECT_CANDIDATES if obj in text]
    clues = [obj for obj in major_objects if obj in " ".join(paragraphs[: max(1, len(paragraphs) // 2)])]
    locations = [loc for loc in _LOCATION_CANDIDATES if loc in text]

    explicit_reveal = ""
    for para in paragraphs[-3:]:
        if any(token in para for token in ["కాదు", "తెలిసింది", "కనలేదు", "అంది", "అన్నాడు", "చెప్పాడు", "చెప్తాడు", "చనిపోయాడు", "చనిపోయారు", "తీసుకొచ్చాను", "వెనక ఒక్క వాక్యం ఉంది"]):
            explicit_reveal = para
            break

    final_twist = paragraphs[-1] if paragraphs else ""
    unresolved_promises: list[str] = []
    if blueprint:
        device_aliases = _DEVICE_ALIASES.get(blueprint.primary_story_device, [blueprint.primary_story_device])
        later_text = " ".join(paragraphs[1:])
        if blueprint.primary_story_device in script.hook_line and not any(alias in later_text for alias in device_aliases):
            unresolved_promises.append(blueprint.primary_story_device)
        clue_aliases = _DEVICE_ALIASES.get(blueprint.primary_clue, [blueprint.primary_clue])
        second_half = " ".join(paragraphs[len(paragraphs) // 2 :])
        if blueprint.primary_clue and not any(alias in second_half for alias in clue_aliases):
            unresolved_promises.append(blueprint.primary_clue)

    meta_hits = [pattern for pattern in _META_PATTERNS if pattern in text]

    return NarrativeFacts(
        protagonist_names=protagonist_names,
        detected_point_of_view=pov,
        major_objects=major_objects,
        clues=clues,
        locations=locations,
        explicit_reveal=explicit_reveal,
        final_twist=final_twist,
        unresolved_promises=unresolved_promises,
        meta_narration_hits=meta_hits,
    )
