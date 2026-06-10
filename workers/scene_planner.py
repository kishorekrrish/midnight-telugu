"""Scene planner — converts a script into 6-10 production-ready scenes."""

from __future__ import annotations

import uuid

from workers.models import HumanizedScript, Scene, ScenePlan, StoryScript

_CAMERA_ANGLES = [
    "close-up", "medium shot", "wide shot", "over-the-shoulder",
    "low angle", "high angle", "dutch angle",
]

_MOTIONS = [
    "slow zoom in", "slow zoom out", "pan left", "pan right",
    "static", "gentle push in", "subtle pull back",
]

_NEGATIVE_PROMPT = (
    "blurry, low quality, distorted face, extra limbs, watermark, "
    "text overlay, anime style, cartoon, Western appearance, "
    "copyrighted characters, celebrity likeness"
)


def _split_script_to_segments(script_text: str, num_scenes: int) -> list[str]:
    """Split script text into roughly equal segments for each scene."""
    paragraphs = [p.strip() for p in script_text.split("\n\n") if p.strip()]
    if len(paragraphs) >= num_scenes:
        # Merge extras into last segment
        result = paragraphs[:num_scenes - 1]
        result.append(" ".join(paragraphs[num_scenes - 1:]))
        return result

    # Pad with empty strings if too few paragraphs
    while len(paragraphs) < num_scenes:
        paragraphs.append("...")
    return paragraphs[:num_scenes]


def _timestamp_range(scene_idx: int, total_scenes: int, total_seconds: int) -> str:
    seconds_per_scene = total_seconds / total_scenes
    start = int(scene_idx * seconds_per_scene)
    end = int((scene_idx + 1) * seconds_per_scene)
    def fmt(s: int) -> str:
        return f"{s // 60:02d}:{s % 60:02d}"
    return f"{fmt(start)}-{fmt(end)}"


_SCENE_VISUAL_TEMPLATES = [
    # (visual_description template, location, mood, camera_angle, motion)
    (
        "చీకటి వాతావరణంలో ఒక వ్యక్తి ఒంటరిగా నిల్చున్నాడు, వెలుతురు మసకగా పడుతుంది",
        "రాత్రి వీధి / అపార్ట్‌మెంట్",
        "eerie, tense",
        "low angle",
        "slow zoom in",
    ),
    (
        "పాత ఇంట్లో కిటికీ లోంచి వెలుతురు పడుతుంది, దుమ్ము తేలుతోంది",
        "పాత ఇల్లు — ఇంటిలోపల",
        "mysterious, suspenseful",
        "wide shot",
        "gentle push in",
    ),
    (
        "ముఖంపై భావాలు స్పష్టంగా కనపడుతున్నాయి, నేపథ్యం మసకగా ఉంది",
        "ఇంటి లోపల / గది",
        "intense, emotional",
        "close-up",
        "static",
    ),
    (
        "గ్రామ వీధిలో సాయంత్రపు వెలుతురులో నీడలు పడుతున్నాయి",
        "గ్రామ వాతావరణం",
        "nostalgic, foreboding",
        "medium shot",
        "pan left",
    ),
    (
        "పాత ఆల్బమ్ లేదా ఫోటో క్లోజ్‌గా కనిపిస్తుంది",
        "గది లోపల",
        "melancholy, revealing",
        "close-up",
        "slow zoom in",
    ),
    (
        "రాత్రి ఆకాశం నేపథ్యంలో ఒంటరి వ్యక్తి నిల్చుని ఉన్నాడు",
        "బయట — రాత్రి",
        "isolated, atmospheric",
        "wide shot",
        "subtle pull back",
    ),
    (
        "ఇంటి తలుపు, తెరవబడబోతున్న సన్నివేశం",
        "ఇల్లు / ప్రవేశం",
        "anticipation, dread",
        "over-the-shoulder",
        "slow zoom in",
    ),
    (
        "ముఖంపై సంఘర్షణ భావాలు, కళ్ళలో సత్యం కనుగొన్న ఆనందమూ బాధా కలిసి",
        "ఇంటి లోపల",
        "revelation, emotional",
        "close-up",
        "static",
    ),
]


def _build_image_prompt(visual_desc: str, mood: str, location: str) -> str:
    return (
        f"Cinematic Indian Telugu scene, {visual_desc.lower()}, "
        f"location: {location}, mood: {mood}, "
        "photorealistic style, warm cinematic color grading, "
        "vertical 9:16 frame, soft dramatic lighting, "
        "authentic South Indian setting, no text, no watermark"
    )


def plan_scenes(
    script: HumanizedScript | StoryScript,
    num_scenes: int = 7,
) -> ScenePlan:
    """Convert a script into a ScenePlan with 6-10 scenes."""
    num_scenes = max(6, min(10, num_scenes))

    script_text = script.full_script_telugu
    total_seconds = getattr(script, "estimated_duration_seconds", 55)
    segments = _split_script_to_segments(script_text, num_scenes)

    scenes: list[Scene] = []
    for i, segment in enumerate(segments):
        template_idx = i % len(_SCENE_VISUAL_TEMPLATES)
        vis_desc, location, mood, camera, motion = _SCENE_VISUAL_TEMPLATES[template_idx]
        # Vary camera/motion slightly
        if i > 0:
            camera = _CAMERA_ANGLES[i % len(_CAMERA_ANGLES)]
            motion = _MOTIONS[i % len(_MOTIONS)]

        image_prompt = _build_image_prompt(vis_desc, mood, location)

        scene = Scene(
            scene_number=i + 1,
            timestamp_range=_timestamp_range(i, num_scenes, total_seconds),
            narration_line=segment[:200],  # cap for display
            visual_description=vis_desc,
            characters_present=["ప్రధాన పాత్ర"],
            location=location,
            mood=mood,
            camera_angle=camera,
            motion_direction=motion,
            image_prompt=image_prompt,
            negative_prompt=_NEGATIVE_PROMPT,
        )
        scenes.append(scene)

    script_id = getattr(script, "script_id", None) or script.id

    return ScenePlan(
        id=f"scenes_{uuid.uuid4().hex[:8]}",
        script_id=script_id,
        title=script.title,
        total_scenes=len(scenes),
        scenes=scenes,
    )
