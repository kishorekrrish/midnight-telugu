"""Prompt construction for Veo scene clips."""

from __future__ import annotations

import json
from pathlib import Path

from workers.production_models import SceneShot

GLOBAL_STYLE = (
    "Cinematic vertical 9:16 Telugu supernatural suspense short. Realistic South Indian atmosphere, "
    "muted colours, deep shadows, subtle film grain, restrained horror, no gore, no exaggerated acting."
)
NEGATIVE_PROMPT = (
    "No subtitles, no captions, no logos, no readable signs, no extra random people, no Western-looking "
    "characters, no distorted faces, no extra limbs, no cartoon/anime style, no gore, no monsters unless "
    "explicitly requested, no sudden camera orbit."
)


def ensure_default_bibles(story_dir: Path) -> tuple[Path, Path]:
    character_path = story_dir / "character_bible.json"
    location_path = story_dir / "location_bible.json"
    if not character_path.exists() and story_dir.name == "chandra-last-train":
        character_path.write_text(
            json.dumps(
                {
                    "characters": [
                        {
                            "name": "Chandra",
                            "description": "South Indian Telugu man, Indian nationality, around 30 years old, lean build, medium-brown skin, angular face, short slightly untidy black hair, light stubble, tired intense eyes.",
                            "clothing": "Faded blue long-sleeved cotton shirt, dark charcoal trousers, simple dark sandals.",
                            "continuity_rules": [
                                "Do not change his ethnicity, age, skin tone, face, hairstyle, body type or clothing.",
                                "Do not make him look American, European or foreign.",
                            ],
                        },
                        {
                            "name": "Old man",
                            "description": "Elderly South Indian man, Indian nationality, around 70 years old, very thin build, weathered medium-brown skin, narrow face, visible cheekbones, deep-set eyes, short grey hair, faint grey stubble, calm unsettling expression.",
                            "clothing": "Worn off-white cotton shirt, dark charcoal shawl draped over shoulders, plain white dhoti, old brown sandals.",
                            "continuity_rules": [
                                "Do not change his ethnicity, age, skin tone, face, hairstyle, body type or clothing.",
                                "Do not make him look American, European or foreign.",
                            ],
                        },
                    ]
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    if not location_path.exists() and story_dir.name == "chandra-last-train":
        location_path.write_text(
            json.dumps(
                {
                    "locations": [
                        {
                            "name": "deserted_railway_station",
                            "description": "Deserted South Indian railway station late at night. Old metal bench, wet platform, thin mist, one flickering fluorescent tube light, empty railway tracks, deep shadows.",
                            "camera_lock": "Camera stays on the track side of the bench at chest height with a 35mm cinematic medium-lens look. Do not cross to the opposite side. Do not reverse character left-right positions.",
                            "blocking": "From camera view, Chandra sits on the left side of the bench and the old man sits on the right. Both face diagonally toward screen-right.",
                        }
                    ]
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    return character_path, location_path


def build_veo_prompt(story_dir: Path, shot: SceneShot) -> str:
    character_path, location_path = ensure_default_bibles(story_dir)
    character_bible = json.loads(character_path.read_text(encoding="utf-8")) if character_path.exists() else {}
    location_bible = json.loads(location_path.read_text(encoding="utf-8")) if location_path.exists() else {}
    return "\n".join(
        [
            GLOBAL_STYLE,
            f"Character identity lock: {json.dumps(character_bible, ensure_ascii=False)}",
            f"Location lock: {json.dumps(location_bible, ensure_ascii=False)}",
            f"Shot action: {shot.visual_prompt}",
            f"Camera notes: {shot.camera_notes}",
            "Motion restriction: subtle human movement, restrained camera movement, no abrupt cuts inside the clip.",
            f"Negative instructions: {NEGATIVE_PROMPT}",
        ]
    )
