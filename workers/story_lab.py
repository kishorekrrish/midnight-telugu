"""Story Lab Phase 1: best-in-class story/script development loop."""

from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from workers.config import DEFAULT_TEXT_PROVIDER
from workers.io_utils import write_json
from workers.models import ContentCategory, HumanizedScript, StoryBlueprint, StoryIdea
from workers.narrative_facts import extract_narrative_facts
from workers.narrative_validator import validate_narrative
from workers.script_generator import generate_script
from workers.script_quality import validate_script
from workers.story_blueprint import build_blueprint
from workers.story_continuity import check_continuity
from workers.telugu_humanizer import humanize_script
from workers.telugu_quality import check_telugu_quality


class StoryBrief(BaseModel):
    story_slug: str
    category: str = "supernatural_suspense"
    target_duration_seconds: int = 50
    audience: str = "Telugu YouTube Shorts audience"
    tone: str = "restrained supernatural suspense"
    location_preference: str = "railway station"
    emotion: str = "fear + grief"
    twist_type: str = "earned ghost reveal"
    avoid: list[str] = Field(
        default_factory=lambda: [
            "moral lecture",
            "generic dream ending",
            "copied movie plot",
            "random ghost appearance",
            "old photo explains everything without setup",
        ]
    )


class ViralScore(BaseModel):
    scroll_stop_hook: int = 0
    freshness: int = 0
    emotional_punch: int = 0
    twist_surprise: int = 0
    twist_fairness: int = 0
    replay_clue: int = 0
    visual_simplicity: int = 0
    production_feasibility: int = 0
    shareability: int = 0
    comment_potential: int = 0
    total: int = 0
    rejection_reasons: list[str] = Field(default_factory=list)
    improvement_suggestions: list[str] = Field(default_factory=list)


class ScriptCritique(BaseModel):
    would_stop_scroll: bool = False
    predicted_drop_points: list[str] = Field(default_factory=list)
    predictable_twist: bool = False
    final_line_strength: int = 0
    comment_potential: str = ""
    replay_clue: str = ""
    boring_sentences: list[str] = Field(default_factory=list)
    required_fixes: list[str] = Field(default_factory=list)
    editor_score: int = 0


class StoryLabCandidate(BaseModel):
    candidate_id: str
    blueprint_id: str
    idea_id: str
    script_text: str
    critique: ScriptCritique
    rewrite_notes: list[str] = Field(default_factory=list)
    narrative_score: int = 0
    quality_score: int = 0
    telugu_authenticity_score: int = 0
    continuity_score: int = 0
    hard_failures: list[str] = Field(default_factory=list)
    recommendation: str = "needs_rewrite"


_CHANDRA_IDEAS = [
    {
        "title": "చంద్ర చివరి రైలు",
        "hook": "రాత్రి 12:17కి చివరి రైలు వెళ్లిపోయింది. కానీ ఖాళీ ప్లాట్‌ఫామ్ మీద ఒక ముసలాయన చంద్రని చూసి, “ఇంకా ఎక్కకు” అన్నాడు.",
        "premise": "వర్షంలో చిక్కుకున్న చంద్రకి ఫోన్ సిగ్నల్ ఉండదు. స్టేషన్ గడియారం 12:17 దగ్గర ఆగిపోతుంది. బెంచ్ మీదున్న ముసలాయన చంద్ర పేరు ముందే తెలిసినట్టుగా మాట్లాడుతాడు.",
        "twist": "స్టేషన్ మాస్టర్ గదిలోని పాత ఫోటోలో అదే బెంచ్, అదే ముసలాయన, అదే 12:17 గడియారం ఉంటాయి. చంద్ర వెనక్కి చూసేసరికి బెంచ్ ఖాళీగా ఉంటుంది; ఫోటోలో ఖాళీ చోట ఇప్పుడు చంద్ర నీడ కనిపిస్తుంది.",
        "tone": "restrained supernatural suspense, fear + grief",
        "hook_type": "stopped_clock_warning",
        "twist_type": "earned_ghost_recontextualization",
        "emotional_core": "a warning from someone trapped in the station's last moment",
        "visual_signature": "rainy empty platform, stopped clock, old bench, old photo",
    },
    {
        "title": "12:17 ప్లాట్‌ఫామ్",
        "hook": "చంద్ర గడియారం చూసాడు — 12:17. స్టేషన్ గడియారం కూడా 12:17. కానీ అతని ఫోన్‌లో తేదీ ఐదు సంవత్సరాల వెనక్కి వెళ్లిపోయింది.",
        "premise": "చివరి రైలు మిస్ అయిన చంద్ర స్టేషన్‌లో రాత్రి ఆగాల్సి వస్తుంది. ఒక ముసలాయన అతని దగ్గర కూర్చుని, ఈ ప్లాట్‌ఫామ్ మీద ఎవరూ ఉదయం వరకు ఒంటరిగా ఉండరని చెప్తాడు.",
        "twist": "స్టేషన్ రిజిస్టర్‌లో ఐదు సంవత్సరాల క్రితం 12:17కి కనిపించకుండా పోయిన ప్రయాణికుడి పేరు చంద్రే అని ఉంటుంది. ముసలాయన అతన్ని కాపాడటం కాదు, నిజం గుర్తు చేస్తున్నాడు.",
        "tone": "psychological supernatural suspense",
        "hook_type": "time_anomaly",
        "twist_type": "identity_reveal",
        "emotional_core": "fear of realizing you may already belong to the place",
        "visual_signature": "same time on every clock",
    },
    {
        "title": "ఖాళీ బెంచ్",
        "hook": "వర్షం ఆగిన తర్వాత కూడా చంద్ర పక్క బెంచ్ తడిగా లేదు. ఎందుకంటే అక్కడ కూర్చున్న ముసలాయనకు వర్షం తగలలేదు.",
        "premise": "చంద్ర స్టేషన్‌లో రాత్రి ఆగుతాడు. అతని పక్కన కూర్చున్న ముసలాయన మాటలు సాధారణంగా మొదలై, చంద్ర గతాన్ని తాకేలా మారుతాయి.",
        "twist": "పాత ఫోటోలో ముసలాయన కనిపిస్తాడు, కానీ అతని పక్కన మొదట ఖాళీగా ఉన్న చోట చివరికి చంద్రే కనిపిస్తాడు.",
        "tone": "slow-burn supernatural suspense",
        "hook_type": "impossible_rain_detail",
        "twist_type": "photo_changes_payoff",
        "emotional_core": "a stranger who knows where the protagonist is headed",
        "visual_signature": "dry bench in rain",
    },
    {
        "title": "మూడో టికెట్",
        "hook": "చంద్ర జేబులో రెండు టికెట్లు మాత్రమే ఉన్నాయి. కానీ టికెట్ చెకర్ అతని చేతిలో మూడో టికెట్ చూసి వణికిపోయాడు.",
        "premise": "చంద్ర చివరి రైలు మిస్ అయి ప్లాట్‌ఫామ్ మీద ఆగుతాడు. ముసలాయన ఒక టికెట్ అతని చేతిలో పెట్టి, దాన్ని ఎవరికి చూపొద్దని హెచ్చరిస్తాడు.",
        "twist": "ఆ మూడో టికెట్ మీద ఐదు సంవత్సరాల క్రితం చనిపోయిన ముసలాయన పేరు ఉంటుంది. చివరికి టికెట్ వెనుక చంద్ర పేరు కొత్తగా కనిపిస్తుంది.",
        "tone": "restrained supernatural suspense",
        "hook_type": "impossible_object",
        "twist_type": "ticket_name_reveal",
        "emotional_core": "a stranger trying to pass on a warning",
        "visual_signature": "wet platform ticket, trembling hand, stopped clock",
    },
    {
        "title": "ఆగిపోయిన గడియారం",
        "hook": "స్టేషన్‌లోని అన్ని గడియారాలు 12:17 చూపిస్తున్నాయి. చంద్ర ఫోన్ మాత్రం ఒక్క మాట చూపించింది — ‘ఇక్కడినుంచి వెళ్లిపో.’",
        "premise": "చంద్ర వర్షంలో చివరి రైలు కోసం నిలబడుతాడు. ప్లాట్‌ఫామ్ ఖాళీగా ఉన్నా, లౌడ్‌స్పీకర్‌లో అతని పేరు వినిపిస్తుంది.",
        "twist": "స్టేషన్ మాస్టర్ రిజిస్టర్‌లో ఐదు సంవత్సరాల క్రితం 12:17కి అదృశ్యమైన ప్రయాణికుడి పక్కన ఇప్పుడు చంద్ర సంతకం కనిపిస్తుంది.",
        "tone": "time-loop supernatural suspense",
        "hook_type": "time_anomaly",
        "twist_type": "register_signature_payoff",
        "emotional_core": "fear of becoming part of a place",
        "visual_signature": "all clocks stopped at 12:17",
    },
    {
        "title": "ఖాళీ ప్రకటన",
        "hook": "ఖాళీ స్టేషన్‌లో లౌడ్‌స్పీకర్ ఒక్కసారిగా మోగింది — ‘చంద్ర, చివరి రైలు ఎక్కకండి.’",
        "premise": "చంద్ర తప్ప ఇంకెవరూ లేని స్టేషన్‌లో అతని పేరు ప్రకటనలో వినిపిస్తుంది. బెంచ్ మీదున్న ముసలాయన ఆ ప్రకటనను పట్టించుకోనట్టు కూర్చుంటాడు.",
        "twist": "ఆ ప్రకటన ఐదు సంవత్సరాల క్రితం రికార్డ్ అయినదని తెలుస్తుంది. రికార్డింగ్ చేసిన స్టేషన్ మాస్టర్ అప్పటికే చనిపోయి ఉంటాడు.",
        "tone": "audio-clue supernatural suspense",
        "hook_type": "impossible_announcement",
        "twist_type": "old_recording_reveal",
        "emotional_core": "a warning that waited years",
        "visual_signature": "rusted speaker, empty platform, rain",
    },
    {
        "title": "నీడల బెంచ్",
        "hook": "చంద్ర బెంచ్ మీద ఒంటరిగా కూర్చున్నాడు. కానీ ప్లాట్‌ఫామ్ లైట్ కింద నేలపై రెండు నీడలు కనిపించాయి.",
        "premise": "వర్షం, చీకటి, చివరి రైలు తర్వాతి నిశ్శబ్దం. చంద్ర పక్కన ఎవరూ కనిపించరు, కానీ రెండో నీడ అతని కదలికలకు ముందే కదులుతుంది.",
        "twist": "పాత ఫోటోలో చంద్ర కూర్చున్న అదే బెంచ్ మీద ముసలాయన కనిపిస్తాడు. ఫోటో దిగువన తేదీ ఐదు సంవత్సరాల క్రితం అదే రాత్రి.",
        "tone": "visual supernatural suspense",
        "hook_type": "impossible_shadow",
        "twist_type": "shadow_photo_payoff",
        "emotional_core": "being accompanied by someone unseen",
        "visual_signature": "two shadows under one flickering tube light",
    },
    {
        "title": "చివరి సీటు",
        "hook": "చివరి రైలు ఖాళీగా వెళ్లిపోయింది. కానీ కిటికీ పక్క సీటులో చంద్ర పేరుతో ఒక రిజర్వేషన్ ఇంకా వెలిగుతోంది.",
        "premise": "చంద్ర రైలును మిస్ అయ్యానని అనుకుంటాడు. ముసలాయన మాత్రం ఆ రైలులో ఎక్కాల్సింది చంద్ర కాదని చెప్తాడు.",
        "twist": "రిజర్వేషన్ జాబితాలో చంద్ర పేరు ఐదు సంవత్సరాల క్రితం చనిపోయిన ప్రయాణికుడి సీటుకు ఎదురుగా ఉంటుంది.",
        "tone": "fate-driven railway suspense",
        "hook_type": "impossible_reservation",
        "twist_type": "seat_manifest_reveal",
        "emotional_core": "escaping a fate by understanding a warning",
        "visual_signature": "empty train window, glowing reservation chart",
    },
    {
        "title": "తడి అడుగుల ముద్రలు",
        "hook": "చంద్ర అడుగుల ముద్రలు ప్లాట్‌ఫామ్ మీద ముందుకు వెళ్లాయి. కానీ తిరిగి వచ్చిన ముద్రలు అతనివి కావు.",
        "premise": "చంద్ర వర్షంలో స్టేషన్ మాస్టర్ గదికి నడుస్తాడు. వెనక్కి చూసిన ప్రతిసారి అతని వెనక ఇంకొకరి తడి ముద్రలు దగ్గరపడుతుంటాయి.",
        "twist": "పాత రిజిస్టర్‌లో ఆ ముద్రల దగ్గర చనిపోయిన ముసలాయన సంతకం ఉంటుంది; చివరికి చంద్ర ముద్రలు అదే పేజీపై తడి అవుతాయి.",
        "tone": "pursuit-style supernatural suspense",
        "hook_type": "footprint_mystery",
        "twist_type": "register_footprint_payoff",
        "emotional_core": "fear of being followed by a past death",
        "visual_signature": "wet footprints on platform concrete",
    },
    {
        "title": "స్టేషన్ మాస్టర్ తాళం",
        "hook": "స్టేషన్ మాస్టర్ గది తాళం వేసి ఉంది. కానీ లోపల నుంచి ఎవరో చంద్ర పేరుని నెమ్మదిగా పిలిచారు.",
        "premise": "చంద్ర సహాయం కోసం స్టేషన్ మాస్టర్ గది దగ్గరకు వెళ్తాడు. తలుపు మూసి ఉంటుంది. ముసలాయన తాళం తన దగ్గర ఉందని చెప్తాడు.",
        "twist": "ఆ తాళం ఐదు సంవత్సరాల క్రితం చనిపోయిన స్టేషన్ మాస్టర్ దగ్గరే పూడ్చిపెట్టారని రిజిస్టర్‌లో ఉంటుంది.",
        "tone": "locked-room railway suspense",
        "hook_type": "locked_room_voice",
        "twist_type": "dead_key_holder",
        "emotional_core": "help coming from the dead",
        "visual_signature": "locked station master room, rusted key",
    },
    {
        "title": "రేపటి వార్త",
        "hook": "ప్లాట్‌ఫామ్ మీద పడి ఉన్న పాత పేపర్‌లో రేపటి తేదీ ఉంది. వార్త శీర్షిక — ‘చివరి రైలులో యువకుడు మాయం.’",
        "premise": "చంద్ర దాన్ని జోక్ అనుకుంటాడు. కానీ పేపర్‌లోని ఫోటోలో అతని చొక్కా, అతని బ్యాగ్, అదే తడి ప్లాట్‌ఫామ్ కనిపిస్తాయి.",
        "twist": "ముసలాయన ఆ పేపర్‌ను ఐదు సంవత్సరాలుగా ప్రతి రాత్రి ఎవరో ఒకరికి చూపిస్తున్నాడని తెలుస్తుంది.",
        "tone": "prophetic supernatural suspense",
        "hook_type": "future_newspaper",
        "twist_type": "repeating_warning",
        "emotional_core": "a trapped soul trying to change one ending",
        "visual_signature": "wet newspaper with tomorrow's date",
    },
]


def default_story_brief(story_slug: str) -> StoryBrief:
    if story_slug == "chandra-last-train":
        return StoryBrief(
            story_slug=story_slug,
            location_preference="deserted railway station at night",
            emotion="fear + grief + fate",
            twist_type="earned ghost reveal with replay clue",
        )
    return StoryBrief(story_slug=story_slug)


def _extract_json(text: str) -> Any:
    cleaned = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", cleaned, flags=re.DOTALL)
    if fenced:
        cleaned = fenced.group(1).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        array_start = cleaned.find("[")
        array_end = cleaned.rfind("]")
        if array_start != -1 and array_end != -1 and array_end > array_start:
            return json.loads(cleaned[array_start : array_end + 1])
        object_start = cleaned.find("{")
        object_end = cleaned.rfind("}")
        if object_start != -1 and object_end != -1 and object_end > object_start:
            return json.loads(cleaned[object_start : object_end + 1])
        preview = cleaned[:240].replace("\n", " ")
        raise ValueError(f"Provider did not return parseable JSON. Preview: {preview}") from None


def _provider_generate_json(prompt: str, provider_name: str) -> Any:
    from workers.providers import get_text_provider

    return _extract_json(get_text_provider(provider_name).generate_text(prompt))


def generate_idea_bank(brief: StoryBrief, count: int = 10, provider: str | None = None) -> list[StoryIdea]:
    provider = provider or DEFAULT_TEXT_PROVIDER
    if provider == "mock" or brief.story_slug == "chandra-last-train":
        seeds = _CHANDRA_IDEAS if brief.story_slug == "chandra-last-train" else _CHANDRA_IDEAS[:1]
        ideas = []
        while len(ideas) < count:
            seed = dict(seeds[len(ideas) % len(seeds)])
            suffix = len(ideas) + 1
            if suffix > len(seeds):
                seed["title"] = f"{seed['title']} - వేరియంట్ {suffix}"
                seed["hook"] = seed["hook"].replace("చంద్ర", "చంద్ర")
            ideas.append(
                StoryIdea(
                    id=f"idea_lab_{suffix:02d}_{uuid.uuid4().hex[:6]}",
                    category=ContentCategory.STRANGE_EVENT,
                    estimated_duration_seconds=brief.target_duration_seconds,
                    originality_notes="Story Lab generated candidate.",
                    safety_notes="Family-safe supernatural suspense; no gore.",
                    **seed,
                )
            )
        return ideas[:count]

    prompt = f"""Generate {count} original Telugu YouTube Shorts story ideas as JSON.

Return ONLY a valid JSON array. Start with [ and end with ]. No markdown. No explanation.
Each item must have:
title, hook, premise, twist, tone, hook_type, twist_type, emotional_core, visual_signature.

Brief:
{brief.model_dump_json(indent=2)}

Rules:
- Telugu mystery/suspense/soft-horror, no gore.
- Every idea needs a scroll-stopping first 3 seconds.
- Every twist needs an early replay clue and emotional aftertaste.
- Avoid generic old-photo/diary-only reveals unless the execution is fresh.
"""
    raw_items = _provider_generate_json(prompt, provider)
    ideas: list[StoryIdea] = []
    for idx, item in enumerate(raw_items[:count], start=1):
        ideas.append(
            StoryIdea(
                id=f"idea_lab_{idx:02d}_{uuid.uuid4().hex[:6]}",
                category=ContentCategory.STRANGE_EVENT,
                estimated_duration_seconds=brief.target_duration_seconds,
                originality_notes="AI Story Lab generated candidate.",
                safety_notes="Family-safe supernatural suspense; no gore.",
                **item,
            )
        )
    return ideas


def score_idea_viral(idea: StoryIdea) -> ViralScore:
    combined = f"{idea.hook} {idea.premise} {idea.twist} {idea.visual_signature}"
    weak = ["ఒక రోజు", "రహస్యం", "అర్థం కాలేదు", "జీవితం మార్చింది"]
    strong_visuals = ["గడియారం", "ప్లాట్‌ఫామ్", "వర్షం", "బెంచ్", "ఫోటో", "నీడ", "తలుపు", "అద్దం"]
    replay = ["ముందే", "మళ్లీ", "ఫోటో", "గడియారం", "రిజిస్టర్", "తేదీ", "నీడ"]
    twist_fair = any(token in idea.premise for token in replay) and any(token in idea.twist for token in replay)
    rejection_reasons = []
    if any(pattern in idea.hook for pattern in weak):
        rejection_reasons.append("Hook uses weak/generic phrasing.")
    if "కల" in idea.twist:
        rejection_reasons.append("Dream ending is not allowed.")

    score = ViralScore(
        scroll_stop_hook=min(10, 4 + int("?" in idea.hook) + int("—" in idea.hook) + sum(v in idea.hook for v in strong_visuals) * 2),
        freshness=max(1, 10 - sum(pattern in combined for pattern in ["డైరీ", "పాత ఫోటో", "భూతం"]) * 2),
        emotional_punch=8 if any(token in combined for token in ["భయం", "దుఃఖం", "గ్రief", "అమ్మ", "తండ్రి", "ఒంటరిగా"]) else 6,
        twist_surprise=min(10, 5 + sum(token in idea.twist for token in ["కానీ", "ఇప్పుడు", "అదే", "వెనక్కి", "నీడ"])),
        twist_fairness=9 if twist_fair else 5,
        replay_clue=min(10, 3 + sum(token in combined for token in replay)),
        visual_simplicity=9 if sum(v in combined for v in strong_visuals) >= 2 else 6,
        production_feasibility=8 if any(loc in combined for loc in ["స్టేషన్", "ఇల్లు", "గది", "ప్లాట్‌ఫామ్"]) else 6,
        shareability=8 if any(token in idea.twist for token in ["ఇప్పుడు", "నీడ", "అదే"]) else 6,
        comment_potential=8 if any(token in idea.hook + idea.twist for token in ["ఎందుకు", "ఎవరు", "నిజంగా", "?"]) else 6,
        rejection_reasons=rejection_reasons,
    )
    score.total = (
        score.scroll_stop_hook
        + score.freshness
        + score.emotional_punch
        + score.twist_surprise
        + score.twist_fairness
        + score.replay_clue
        + score.visual_simplicity
        + score.production_feasibility
        + score.shareability
        + score.comment_potential
    )
    if score.replay_clue < 7:
        score.improvement_suggestions.append("Add a replay clue that appears before the reveal.")
    if score.twist_fairness < 7:
        score.improvement_suggestions.append("Make the twist feel earned by planting the clue earlier.")
    return score


def build_advanced_blueprint(idea: StoryIdea) -> StoryBlueprint:
    blueprint = build_blueprint(idea)
    blueprint.opening_image = idea.visual_signature or idea.hook
    blueprint.first_3_seconds_hook = idea.hook
    blueprint.protagonist_desire = "అక్కడి నుంచి సురక్షితంగా బయటపడాలి."
    blueprint.hidden_truth = idea.twist
    blueprint.early_clue = blueprint.primary_clue
    blueprint.misdirection = "ప్రేక్షకుడు మొదట దీనిని సాధారణ భయం అనుకోవాలి."
    blueprint.midpoint_turn = blueprint.escalation
    blueprint.reveal_mechanism = "ప్రోటాగనిస్ట్ చూసిన ఆధారం revealని నిర్ధారిస్తుంది."
    blueprint.final_recontextualization = blueprint.final_twist
    blueprint.replay_value_clue = blueprint.primary_clue
    blueprint.emotional_aftertaste = idea.emotional_core
    return blueprint


def critique_script(script_text: str, blueprint: StoryBlueprint, provider: str | None = None) -> ScriptCritique:
    provider = provider or DEFAULT_TEXT_PROVIDER
    if provider != "mock":
        prompt = f"""Act as a ruthless Telugu YouTube Shorts editor.

Return ONLY JSON with keys:
would_stop_scroll, predicted_drop_points, predictable_twist, final_line_strength,
comment_potential, replay_clue, boring_sentences, required_fixes, editor_score.

Judge this against the blueprint. Be strict.

Blueprint:
{blueprint.model_dump_json(indent=2)}

Script:
```
{script_text}
```
"""
        try:
            return ScriptCritique.model_validate(_provider_generate_json(prompt, provider))
        except Exception:
            pass

    boring = []
    for sentence in re.split(r"(?<=[.!?।])\s+|\n+", script_text):
        if any(weak in sentence for weak in ["ఆసక్తి", "అర్థం కాలేదు", "రహస్యం", "జీవితం మార్చిన"]):
            boring.append(sentence.strip())
    final_line = script_text.strip().splitlines()[-1] if script_text.strip() else ""
    replay_clue = blueprint.replay_value_clue or blueprint.primary_clue
    score = 70
    if blueprint.hook.split()[0] in script_text[:160]:
        score += 8
    if replay_clue and replay_clue in script_text:
        score += 8
    if any(token in final_line for token in ["ఆగిపోయింది", "నీడ", "ఖాళీ"]):
        score += 8
    score -= min(20, len(boring) * 5)
    return ScriptCritique(
        would_stop_scroll=score >= 78,
        predicted_drop_points=boring[:3],
        predictable_twist="కల" in script_text or "దెయ్యం" in script_text,
        final_line_strength=min(10, max(1, score // 10)),
        comment_potential="Viewer may comment about the clock/photo clue." if replay_clue else "",
        replay_clue=replay_clue,
        boring_sentences=boring[:5],
        required_fixes=[
            "Remove flat summary sentences.",
            "Make final line more chilling.",
        ][: 0 if score >= 85 else 2],
        editor_score=min(100, max(0, score)),
    )


def rewrite_with_critique(
    script_text: str,
    blueprint: StoryBlueprint,
    critique: ScriptCritique,
    provider: str | None = None,
) -> tuple[str, list[str]]:
    provider = provider or DEFAULT_TEXT_PROVIDER
    if provider == "mock" or not critique.required_fixes:
        return script_text, critique.required_fixes
    prompt = f"""Rewrite this Telugu Shorts narration using the editor critique.

Output ONLY the rewritten Telugu narration.

Blueprint:
{blueprint.model_dump_json(indent=2)}

Critique:
{critique.model_dump_json(indent=2)}

Current script:
```
{script_text}
```

Rules:
- Keep 45-60 seconds.
- Strong first line, spoken Telugu, short paragraphs.
- Keep the exact reveal and replay clue.
- No moral, no generic ending.
"""
    from workers.providers import get_text_provider

    rewritten = get_text_provider(provider).generate_text(prompt).strip()
    return rewritten or script_text, critique.required_fixes


def evaluate_candidate(candidate_id: str, blueprint: StoryBlueprint, script_text: str, critique: ScriptCritique, rewrite_notes: list[str]) -> StoryLabCandidate:
    wrapped = HumanizedScript(
        id=candidate_id,
        script_id=candidate_id,
        title=blueprint.title,
        category=blueprint.category,
        hook_line=blueprint.hook,
        full_script_telugu=script_text,
    )
    narrative = validate_narrative(blueprint, extract_narrative_facts(wrapped, blueprint), wrapped.hook_line)
    quality = validate_script(wrapped)
    telugu = check_telugu_quality(script_text)
    continuity = check_continuity(wrapped)
    approved = (
        not narrative.hard_failures
        and quality.quality_score >= 88
        and telugu.telugu_authenticity_score >= 90
        and continuity.continuity_score >= 90
        and critique.editor_score >= 80
    )
    return StoryLabCandidate(
        candidate_id=candidate_id,
        blueprint_id=blueprint.id,
        idea_id=blueprint.idea_id,
        script_text=script_text,
        critique=critique,
        rewrite_notes=rewrite_notes,
        narrative_score=narrative.score,
        quality_score=quality.quality_score,
        telugu_authenticity_score=telugu.telugu_authenticity_score,
        continuity_score=continuity.continuity_score,
        hard_failures=narrative.hard_failures,
        recommendation="approve_candidate" if approved else "needs_rewrite",
    )


def generate_story_lab_package(
    story_dir: Path,
    brief: StoryBrief,
    provider: str | None = None,
    idea_count: int = 10,
    top_blueprints: int = 3,
    scripts_per_blueprint: int = 3,
) -> dict[str, Any]:
    provider = provider or DEFAULT_TEXT_PROVIDER
    story_dir.mkdir(parents=True, exist_ok=True)
    (story_dir / "idea_bank").mkdir(exist_ok=True)
    (story_dir / "blueprints").mkdir(exist_ok=True)
    (story_dir / "script_candidates").mkdir(exist_ok=True)

    ideas = generate_idea_bank(brief, count=idea_count, provider=provider)
    scored = [(idea, score_idea_viral(idea)) for idea in ideas]
    scored.sort(key=lambda item: item[1].total, reverse=True)
    selected = scored[:top_blueprints]

    write_json(story_dir / "story_brief.json", brief)
    (story_dir / "idea_bank" / "ideas.json").write_text(
        json.dumps(
            [{"idea": idea.model_dump(mode="json"), "viral_score": score.model_dump()} for idea, score in scored],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    candidates: list[StoryLabCandidate] = []
    for blueprint_idx, (idea, _score) in enumerate(selected, start=1):
        blueprint = build_advanced_blueprint(idea)
        write_json(story_dir / "blueprints" / f"blueprint_{blueprint_idx:02d}.json", blueprint)
        if blueprint_idx == 1:
            write_json(story_dir / "idea.json", idea)
            write_json(story_dir / "blueprint.json", blueprint)
        for script_idx in range(1, scripts_per_blueprint + 1):
            raw = generate_script(blueprint, provider=provider)
            humanized = humanize_script(raw, provider=provider)
            critique = critique_script(humanized.full_script_telugu, blueprint, provider=provider)
            rewritten, notes = rewrite_with_critique(humanized.full_script_telugu, blueprint, critique, provider=provider)
            final_critique = critique_script(rewritten, blueprint, provider=provider)
            candidate_id = f"bp{blueprint_idx:02d}_candidate_{script_idx:02d}"
            candidate = evaluate_candidate(candidate_id, blueprint, rewritten, final_critique, notes)
            candidates.append(candidate)
            (story_dir / "script_candidates" / f"{candidate_id}.txt").write_text(rewritten, encoding="utf-8")
            (story_dir / "script_candidates" / f"{candidate_id}.meta.json").write_text(
                candidate.model_dump_json(indent=2),
                encoding="utf-8",
            )

    candidates.sort(
        key=lambda c: (
            1 if c.recommendation == "approve_candidate" else 0,
            c.critique.editor_score,
            c.narrative_score,
            c.quality_score,
            c.continuity_score,
        ),
        reverse=True,
    )
    best = candidates[0] if candidates else None
    if best:
        (story_dir / "script.txt").write_text(best.script_text, encoding="utf-8")
    review_path = write_story_lab_review(story_dir, brief, scored, selected, candidates, best)
    return {
        "story_dir": story_dir,
        "review_path": review_path,
        "best_candidate": best.candidate_id if best else None,
        "candidate_count": len(candidates),
    }


def write_story_lab_review(
    story_dir: Path,
    brief: StoryBrief,
    scored_ideas: list[tuple[StoryIdea, ViralScore]],
    selected: list[tuple[StoryIdea, ViralScore]],
    candidates: list[StoryLabCandidate],
    best: StoryLabCandidate | None,
) -> Path:
    lines = [
        f"# Story Lab Review: {brief.story_slug}",
        "",
        "## Story Brief",
        "",
        "```json",
        brief.model_dump_json(indent=2),
        "```",
        "",
        "## Top Ideas",
        "",
    ]
    for idx, (idea, score) in enumerate(scored_ideas[:10], start=1):
        marker = "selected" if any(idea.id == selected_idea.id for selected_idea, _ in selected) else "banked"
        lines.extend(
            [
                f"### {idx}. {idea.title} ({marker})",
                f"- Viral score: {score.total}/100",
                f"- Hook: {idea.hook}",
                f"- Twist: {idea.twist}",
                f"- Replay clue score: {score.replay_clue}/10",
                f"- Comment potential: {score.comment_potential}/10",
                "",
            ]
        )

    lines.extend(["## Script Candidates", ""])
    for candidate in candidates:
        lines.extend(
            [
                f"### {candidate.candidate_id}",
                f"- Recommendation: {candidate.recommendation}",
                f"- Editor score: {candidate.critique.editor_score}/100",
                f"- Narrative score: {candidate.narrative_score}/100",
                f"- Quality score: {candidate.quality_score}/100",
                f"- Telugu authenticity: {candidate.telugu_authenticity_score}/100",
                f"- Continuity: {candidate.continuity_score}/100",
                f"- Hard failures: {', '.join(candidate.hard_failures) or 'None'}",
                f"- Would stop scroll: {candidate.critique.would_stop_scroll}",
                f"- Replay clue: {candidate.critique.replay_clue or 'None'}",
                f"- Comment potential: {candidate.critique.comment_potential or 'None'}",
                "",
                candidate.script_text,
                "",
            ]
        )

    if best:
        lines.extend(
            [
                "## Best Candidate",
                "",
                best.candidate_id,
                "",
                "## Approval Command",
                "",
                f"```bash\npython -m workers.cli approve-script {story_dir} --candidate {best.candidate_id} --notes \"Approved from Story Lab\"\n```",
                "",
            ]
        )
    path = story_dir / "script_review.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
