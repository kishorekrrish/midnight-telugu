"""Blueprint-first story planner for deterministic Telugu short stories."""

from __future__ import annotations

import re
import uuid

from workers.models import StoryBlueprint, StoryIdea
from workers.telugu_quality import apply_telugu_replacements

_CATEGORY_DEFAULTS: dict[str, dict[str, list[str] | str]] = {
    "midnight_mystery": {
        "names": ["రవి", "అర్జున్", "కిరణ్"],
        "role": "యువకుడు",
        "devices": ["మూసి ఉన్న గది", "అర్థరాత్రి శబ్దం", "పాత డైరీ"],
        "clues": ["పాత ఫోటో", "తాళం చెవి", "డైరీ పేజీ"],
        "locations": ["పాత ఇల్లు", "మూసి ఉన్న గది"],
    },
    "emotional_suspense": {
        "names": ["శ్యామ్", "కార్తీక్", "మాలతి"],
        "role": "కొడుకు",
        "devices": ["వాయిస్ మెమో", "మూసి పెట్టిన పెట్టె", "పాత ఫోటో"],
        "clues": ["పిల్లాడు గీసిన బొమ్మ", "పాత ఫోటో", "రికార్డింగ్ తేదీ"],
        "locations": ["పాత ఇల్లు", "చెరువు గట్టు"],
    },
    "family_suspense": {
        "names": ["ప్రవీణ్", "సుమ", "అనిత"],
        "role": "కుటుంబ సభ్యుడు",
        "devices": ["చివరి ఉత్తరం", "పాత ఫోటో", "అలమరలో దాచిన పత్రం"],
        "clues": ["ఉత్తరం", "పాత ఫోటో", "తేదీ రాసిన కాగితం"],
        "locations": ["పాత ఇల్లు", "అలమర దగ్గర"],
    },
    "strange_event": {
        "names": ["చంద్ర"],
        "role": "యువకుడు",
        "devices": ["చివరి రైలు హెచ్చరిక", "ముసలాయన మాట", "ఖాళీ ప్లాట్‌ఫామ్"],
        "clues": ["పాత ఫోటో", "స్టేషన్ మాస్టర్ రిజిస్టర్", "చివరి రైలు సమయం"],
        "locations": ["రైల్వే స్టేషన్", "ప్లాట్‌ఫామ్"],
    },
}
_GENERIC_DEFAULT = {
    "names": ["రవి", "లక్ష్మి", "శ్యామ్"],
    "role": "ప్రధాన పాత్ర",
    "devices": ["పాత ఉత్తరం", "పాత ఫోటో", "రికార్డింగ్"],
    "clues": ["పాత ఫోటో", "తేదీ", "చిన్న జాడ"],
    "locations": ["పాత ఇల్లు", "లోపలి గది"],
}
_NAME_CANDIDATES = [
    "చంద్ర", "శ్యామ్", "కార్తీక్", "రవి", "అర్జున్", "కిరణ్", "మాలతి", "గీత", "అనిత", "లక్ష్మి",
]
_DEVICE_HINTS = [
    "చివరి రైలు", "హెచ్చరిక", "వాయిస్ మెమో", "రికార్డింగ్", "ఉత్తరం", "ఫోటో", "డైరీ", "పెట్టె", "తాళం", "బొమ్మ",
]
_LOCATION_HINTS = [
    "ప్లాట్‌ఫామ్", "రైల్వే స్టేషన్", "చెరువు గట్టు", "పాత ఇల్లు", "గది", "అలమర", "ఆసుపత్రి", "స్టేషన్", "బావి",
]
_FORBIDDEN_POOL = [
    "కొత్త పాత్ర", "సంబంధం లేని వస్తువు", "యాదృచ్ఛికంగా వచ్చిన పాత చీర", "చివర్లో కొత్త రహస్యం",
]
_CHANDRA_RAILWAY_SIGNALS = [
    "చంద్ర", "చివరి రైలు", "రైలు", "రైల్వే", "స్టేషన్", "ప్లాట్‌ఫామ్", "12:17",
]


def _category_key(idea: StoryIdea) -> str:
    return idea.category if isinstance(idea.category, str) else idea.category.value


def _normalize(text: str) -> str:
    cleaned = apply_telugu_replacements(text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _pick_first_match(text: str, candidates: list[str]) -> str | None:
    for candidate in candidates:
        if candidate in text:
            return candidate
    return None


def _is_chandra_railway_idea(idea: StoryIdea) -> bool:
    corpus = " ".join([idea.id, idea.title, idea.hook, idea.premise, idea.twist])
    return "చంద్ర" in corpus and any(signal in corpus for signal in _CHANDRA_RAILWAY_SIGNALS[1:])


def build_blueprint(idea: StoryIdea) -> StoryBlueprint:
    category_key = _category_key(idea)
    if idea.id == "idea_chandra_last_train" or _is_chandra_railway_idea(idea):
        normalized_hook = _normalize(idea.hook)
        normalized_setup = _normalize(idea.premise)
        normalized_reveal = _normalize(idea.twist)
        return StoryBlueprint(
            id=f"blueprint_{uuid.uuid4().hex[:8]}",
            idea_id=idea.id,
            title=idea.title,
            category=idea.category,
            protagonist_name="చంద్ర",
            protagonist_role="రాత్రి రైల్వే స్టేషన్‌లో చిక్కుకున్న యువకుడు",
            point_of_view="third_person",
            hook=normalized_hook,
            central_question="చంద్రని చివరి రైలు ఎక్కొద్దని హెచ్చరించిన ముసలాయన నిజంగా ఎవరు?",
            primary_story_device="చివరి రైలు",
            primary_clue="పాత ఫోటో",
            supporting_clues=["ఆగిపోయిన గడియారం", "స్టేషన్ మాస్టర్ రిజిస్టర్"],
            setup=normalized_setup,
            escalation=(
                f"{normalized_setup} ముసలాయన చంద్ర పేరు చెప్పకముందే తెలుసుకుంటాడు; "
                "గడియారం 12:17 దగ్గరే ఆగిపోతుంది; చివరి రైలు గురించి అతని హెచ్చరిక మరింత వ్యక్తిగతంగా మారుతుంది."
            ),
            reveal=(
                f"{normalized_reveal} స్టేషన్ మాస్టర్ పాత ఫోటో చూపించి, అదే ముసలాయన ఐదు సంవత్సరాల క్రితం "
                "ఇదే బెంచ్ మీద చివరి రైలు కోసం ఎదురు చూస్తూ చనిపోయాడని చెప్తాడు."
            ),
            final_twist=(
                "చంద్ర వెనక్కి చూసేసరికి బెంచ్ ఖాళీగా ఉంటుంది; కానీ పాత ఫోటోలో ముసలాయన పక్కన ఖాళీగా ఉన్న చోట "
                "ఇప్పుడు చంద్ర నీడ కనిపిస్తుంది."
            ),
            final_line="గడియారం మళ్లీ 12:17 దగ్గరే ఆగిపోయింది.",
            locations=["ప్లాట్‌ఫామ్", "రైల్వే స్టేషన్"],
            forbidden_elements=["కొత్త పాత్ర", "వేరే నగరం", "మోరల్ లెక్చర్", "యాదృచ్ఛిక కల"],
        )

    defaults = _CATEGORY_DEFAULTS.get(category_key, _GENERIC_DEFAULT)
    corpus = " ".join([idea.title, idea.hook, idea.premise, idea.twist])

    protagonist_name = _pick_first_match(corpus, _NAME_CANDIDATES) or str(defaults["names"][0])
    point_of_view = "first_person" if "నేను" in idea.hook or "నాకు" in idea.hook else "third_person"
    primary_story_device = _pick_first_match(corpus, _DEVICE_HINTS) or str(defaults["devices"][0])
    primary_clue = _pick_first_match(corpus, list(defaults["clues"])) or str(defaults["clues"][0])

    supporting_clues: list[str] = []
    for clue in defaults["clues"]:
        clue_str = str(clue)
        if clue_str != primary_clue and (clue_str in corpus or len(supporting_clues) < 1):
            supporting_clues.append(clue_str)
        if len(supporting_clues) == 2:
            break

    locations: list[str] = []
    for hint in _LOCATION_HINTS + [str(item) for item in defaults["locations"]]:
        if hint in corpus and hint not in locations:
            locations.append(hint)
        if len(locations) == 2:
            break
    if not locations:
        locations = [str(defaults["locations"][0])]
    elif len(locations) == 1 and len(defaults["locations"]) > 1 and str(defaults["locations"][1]) != locations[0]:
        locations.append(str(defaults["locations"][1]))

    central_question = (
        f"{protagonist_name}‌కి కనిపించిన {primary_story_device} వెనక దాచిన నిజం ఏమిటి?"
    )
    reveal = _normalize(idea.twist)
    final_twist = (
        f"{primary_clue}నే చివరికి {reveal.rstrip('.')} అని నిర్ధారించే జాడగా మారుతుంది."
    )
    final_line = (
        f"{protagonist_name} చేతిలో ఇంకా {primary_clue}నే ఉంది. అదే అతని జీవితాన్ని మార్చిన చివరి సాక్ష్యం."
    )

    forbidden_elements = [primary_story_device]
    for element in _FORBIDDEN_POOL:
        if element not in forbidden_elements:
            forbidden_elements.append(element)
        if len(forbidden_elements) == 4:
            break

    return StoryBlueprint(
        id=f"blueprint_{uuid.uuid4().hex[:8]}",
        idea_id=idea.id,
        title=idea.title,
        category=idea.category,
        protagonist_name=protagonist_name,
        protagonist_role=str(defaults["role"]),
        point_of_view=point_of_view,
        hook=_normalize(idea.hook),
        central_question=central_question,
        primary_story_device=primary_story_device,
        primary_clue=primary_clue,
        supporting_clues=supporting_clues[:2],
        setup=_normalize(idea.premise),
        escalation=f"{protagonist_name}‌కి కనిపించిన ప్రతి చిన్న జాడ అదే ప్రశ్నను మరింత గట్టిగా నిలబెడుతుంది.",
        reveal=reveal,
        final_twist=final_twist,
        final_line=final_line,
        locations=locations[:2],
        forbidden_elements=forbidden_elements,
    )
