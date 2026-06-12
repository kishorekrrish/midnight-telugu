"""Tests for narrative facts extraction and blueprint comparison."""

from __future__ import annotations

import json
from pathlib import Path

from workers.models import ContentCategory, StoryBlueprint, StoryScript
from workers.narrative_facts import extract_narrative_facts
from workers.narrative_validator import validate_narrative

FIXTURES = Path(__file__).parent / "fixtures"


def _make_blueprint() -> StoryBlueprint:
    return StoryBlueprint(
        id="blueprint_1",
        idea_id="idea_1",
        title="అమ్మ చివరి కాల్",
        category=ContentCategory.EMOTIONAL_SUSPENSE,
        protagonist_name="శ్యామ్",
        protagonist_role="కొడుకు",
        point_of_view="third_person",
        hook="అమ్మ చనిపోయిన తర్వాత ఆమె ఫోన్‌లో ఒక వాయిస్ మెమో కనిపించింది.",
        central_question="శ్యామ్ జీవితంలో దాచిన నిజం ఏమిటి?",
        primary_story_device="వాయిస్ మెమో",
        primary_clue="పాత ఫోటో",
        supporting_clues=["పిల్లాడు గీసిన బొమ్మ"],
        setup="శ్యామ్ మూడు సంవత్సరాల తర్వాత ఫోన్ తెరిచాడు.",
        escalation="పెట్టెలో దొరికిన జాడలు అతన్ని ఆపలేదు.",
        reveal="ఫోటోలో ఉన్న మనిషి అతని తండ్రి కాదు.",
        final_twist="రికార్డింగ్‌లో అమ్మ అతన్ని చెరువు దగ్గర నుంచి తీసుకొచ్చానని అంది.",
        final_line="శ్యామ్ ఫోటో వెనక రాసిన వాక్యం చూసి నిలిచిపోయాడు.",
        locations=["పాత ఇల్లు", "చెరువు గట్టు"],
        forbidden_elements=["పాత చీర", "కొత్త పాత్ర"],
    )


def _make_script(text: str, hook: str | None = None) -> StoryScript:
    return StoryScript(
        id="script_nv_1",
        idea_id="idea_1",
        blueprint_id="blueprint_1",
        title="అమ్మ చివరి కాల్",
        category=ContentCategory.EMOTIONAL_SUSPENSE,
        hook_line=hook or "అమ్మ చనిపోయిన తర్వాత ఆమె ఫోన్‌లో ఒక వాయిస్ మెమో కనిపించింది.",
        full_script_telugu=text,
    )


def _load_fixture(relative_path: str) -> StoryScript:
    data = json.loads((FIXTURES / relative_path).read_text(encoding="utf-8"))
    return _make_script(data["full_script_telugu"], hook=data["hook_line"])


def test_extracts_protagonist_names():
    facts = extract_narrative_facts(_load_fixture("passing_scripts/blueprint_aligned_story.json"))
    assert "శ్యామ్" in facts.protagonist_names


def test_detects_first_person():
    script = _make_script("నేను ఆ వాయిస్ మెమో విన్నాను.\n\nనాకు వెంటనే నిజం అర్థమైంది.", hook="నేను ఆ రాత్రి విన్న మాట ఇంకా మర్చిపోలేను.")
    facts = extract_narrative_facts(script)
    assert facts.detected_point_of_view == "first_person"


def test_detects_third_person():
    facts = extract_narrative_facts(_load_fixture("passing_scripts/blueprint_aligned_story.json"))
    assert facts.detected_point_of_view == "third_person"


def test_detects_multiple_protagonist_names():
    facts = extract_narrative_facts(_load_fixture("bad_scripts/character_and_clue_inconsistency.json"))
    assert "కార్తీక్" in facts.protagonist_names
    assert "శ్యామ్" in facts.protagonist_names


def test_detects_major_objects():
    facts = extract_narrative_facts(_load_fixture("passing_scripts/blueprint_aligned_story.json"))
    assert "వాయిస్ మెమో" in facts.major_objects
    assert "ఫోటో" in facts.major_objects


def test_detects_meta_narration():
    facts = extract_narrative_facts(_load_fixture("bad_scripts/character_and_clue_inconsistency.json"))
    assert facts.meta_narration_hits


def test_detects_unresolved_promise():
    blueprint = _make_blueprint()
    script = _make_script(
        "అమ్మ చనిపోయిన తర్వాత ఆమె ఫోన్‌లో ఒక వాయిస్ మెమో కనిపించింది.\n\nశ్యామ్ పాత ఇంటికి వెళ్లాడు.\n\nచివరికి ఏమీ దొరకలేదు."
    )
    facts = extract_narrative_facts(script, blueprint)
    assert "వాయిస్ మెమో" in facts.unresolved_promises


def test_detects_pov_mismatch():
    blueprint = _make_blueprint()
    script = _load_fixture("bad_scripts/character_and_clue_inconsistency.json")
    facts = extract_narrative_facts(script, blueprint)
    result = validate_narrative(blueprint, facts, script.hook_line)
    assert "POV_MISMATCH" in result.hard_failures


def test_detects_karthik_to_shyam_name_change():
    blueprint = _make_blueprint()
    blueprint.protagonist_name = "కార్తీక్"
    script = _load_fixture("bad_scripts/character_and_clue_inconsistency.json")
    facts = extract_narrative_facts(script, blueprint)
    result = validate_narrative(blueprint, facts, script.hook_line)
    assert "PROTAGONIST_NAME_CHANGED" in result.hard_failures


def test_detects_missing_voice_memo_payoff():
    blueprint = _make_blueprint()
    script = _make_script(
        "అమ్మ చనిపోయిన తర్వాత ఆమె ఫోన్‌లో ఒక వాయిస్ మెమో కనిపించింది.\n\nశ్యామ్ పాత గదిలో ఫోటో మాత్రమే చూశాడు.\n\nచివరికి ఫోటోలో ఉన్న మనిషి వేరే అని తెలిసింది."
    )
    facts = extract_narrative_facts(script, blueprint)
    result = validate_narrative(blueprint, facts, script.hook_line)
    assert "PRIMARY_DEVICE_NOT_RESOLVED" in result.hard_failures


def test_detects_unplanned_saree_clue():
    blueprint = _make_blueprint()
    script = _load_fixture("bad_scripts/character_and_clue_inconsistency.json")
    facts = extract_narrative_facts(script, blueprint)
    result = validate_narrative(blueprint, facts, script.hook_line)
    assert "UNPLANNED_MAJOR_OBJECT" in result.hard_failures


def test_detects_vague_reveal():
    blueprint = _make_blueprint()
    script = _make_script(
        "అమ్మ చనిపోయిన తర్వాత ఆమె ఫోన్‌లో ఒక వాయిస్ మెమో కనిపించింది.\n\nశ్యామ్ ఫోటో చూశాడు.\n\nచివరికి తండ్రి గురించి ఏదో విషయం ఉందని మాత్రమే అనిపించింది."
    )
    facts = extract_narrative_facts(script, blueprint)
    result = validate_narrative(blueprint, facts, script.hook_line)
    assert "FINAL_TWIST_UNCLEAR" in result.hard_failures or "REVEAL_NOT_EXPLICIT" in result.hard_failures


def test_detects_summary_narration():
    blueprint = _make_blueprint()
    script = _load_fixture("bad_scripts/character_and_clue_inconsistency.json")
    facts = extract_narrative_facts(script, blueprint)
    result = validate_narrative(blueprint, facts, script.hook_line)
    assert "META_OR_SUMMARY_NARRATION" in result.hard_failures


def test_passing_script_has_no_hard_failures():
    blueprint = _make_blueprint()
    script = _load_fixture("passing_scripts/blueprint_aligned_story.json")
    facts = extract_narrative_facts(script, blueprint)
    result = validate_narrative(blueprint, facts, script.hook_line)
    assert result.hard_failures == []
