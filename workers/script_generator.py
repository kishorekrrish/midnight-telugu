"""Script generator — structural variety, anti-AI-pattern Telugu scripts."""

from __future__ import annotations

import random
import uuid

from workers.config import DEFAULT_TEXT_PROVIDER
from workers.models import ContentCategory, StoryIdea, StoryScript

# Script structure variants — each produces a different narrative shape
_STRUCTURES = [
    "cold_open",
    "object_mystery",
    "unreliable_narrator",
    "missing_person_clue",
    "emotional_reveal",
    "reverse_expectation",
    "silent_witness",
    "final_line_twist",
]

# Structure-specific opening templates
_STRUCTURE_OPENINGS: dict[str, list[str]] = {
    "cold_open": [
        "ఆ రాత్రి జరిగింది. ముందు చెప్తాను — అది ఇప్పటికీ నమ్మడానికి కష్టంగా ఉంటుంది.",
        "అది జరిగిన తర్వాత నేను మళ్ళీ ఆ వీధిలో నడవలేదు.",
        "చివరిలో ఏం జరిగిందో ముందు చెప్తాను — ఆ మొదటి మాట వినిన తర్వాత అన్నీ అర్థమవుతాయి.",
    ],
    "object_mystery": [
        "అది ఒక చిన్న వస్తువు. దాని గురించి ఎవరూ మాట్లాడరు — కానీ అందరికీ తెలుసు అది ఎందుకు అక్కడ ఉందో.",
        "ఆ పాత ఫోటో. ఆ పాత ఉత్తరం. ఆ పాత తలుపు. అది ఒక్కటే చాలు — అన్ని ప్రశ్నలకు జవాబు.",
        "ఒక వస్తువు మాట్లాడగలిగితే — ఆ వస్తువు చాలా విషయాలు చెప్పేది.",
    ],
    "unreliable_narrator": [
        "నాకు జ్ఞాపకాలు పూర్తిగా నిజమైనవి కావు అని తెలుసు. కానీ ఆ రోజు — ఆ రోజు మాత్రం నేను చాలా స్పష్టంగా గుర్తు పెట్టుకున్నాను.",
        "అప్పుడు నాకు అర్థమైంది — నేను చూసింది నిజమైతే, ఇక్కడ ఏదో తప్పుగా ఉంది.",
        "అందరూ నన్ను నమ్మలేదు. కానీ నేను చూసింది నేను మర్చిపోలేను.",
    ],
    "missing_person_clue": [
        "ఆ వ్యక్తి ఎక్కడికి వెళ్ళాడో ఎవరికీ తెలియదు. ఒక్క ఒక్క ముక్కే మిగిలింది.",
        "ఒక ఫోన్ నంబర్. ఒక పాత చిరునామా. ఒక unfinished వాక్యం. అంతే — అదే clue.",
        "వాళ్ళు మాయమైన 3 రోజుల తర్వాత ఒక్క గురుతు మిగిలింది.",
    ],
    "emotional_reveal": [
        "నేను అర్థం చేసుకోవడానికి చాలా సమయం పట్టింది. కానీ ఇప్పుడు తెలుసు — అది ప్రేమ. అది త్యాగం.",
        "ఆ మాట వినిన తర్వాత నా కళ్ళు తడిచాయి — కోపంతో కాదు, ప్రేమతో.",
        "ఆ నిజం తెలిసిన తర్వాత నాకు అర్థమైంది — అందులో కోపానికి ఏమీ లేదు. అందులో ఒక గుండె ఉంది.",
    ],
    "reverse_expectation": [
        "అందరూ అనుకున్నారు ఇది ఒక చెడ్డ కథ అని. కానీ అది కాదు.",
        "మొదటిలో చూసినప్పుడు భయమేసింది. తర్వాత అర్థమైంది — ఆ భయం నాది, నిజం వేరే.",
        "దానిని చెడు అని పిలిచారు. నేను తెలుసుకున్నాను — ఇది మనమే సృష్టించిన భయం.",
    ],
    "silent_witness": [
        "ఆ గోడలు మాట్లాడగలిగితే — ఆ పాత ఇల్లు చాలా విషయాలు చెప్పేది.",
        "ఆ కుర్చీ, ఆ తలుపు, ఆ అద్దం — అవి చూశాయి. మనం అడగలేదు.",
        "ఒక్క witness ఉంది ఆ రాత్రికి — కానీ అది మాట్లాడడం లేదు.",
    ],
    "final_line_twist": [
        "ఈ కథ వినడానికి simple గా ఉంటుంది. కానీ చివరి మాటకు వెళ్ళే సరికి — అన్నీ తలకిందులవుతాయి.",
        "మొదటి నుండి ఆఖరు వరకు ఒక్కో మాట చదివారు — ఇప్పుడు మొదటికి వెళ్ళండి. అప్పుడు అర్థమవుతుంది.",
        "అందరూ అనుకున్నారు ముగింపు తెలుసు అని. చివరి వాక్యం చదివే వరకు.",
    ],
}

# Category-specific premise expansion templates
_PREMISE_VOICE: dict[str, str] = {
    ContentCategory.MIDNIGHT_MYSTERY: (
        "అర్థరాత్రి తర్వాత మాత్రమే కొన్ని రహస్యాలు తెరుచుకుంటాయి. "
        "ఆ సమయానికి మనసు రక్షణ తగ్గిపోతుంది — నిజాలు దగ్గరకు వస్తాయి."
    ),
    ContentCategory.VILLAGE_MYSTERY: (
        "మా ఊళ్ళో పెద్దలు అన్ని విషయాలు చెప్పరు. "
        "కొన్ని నిజాలు తరాల పాటు మూసి పెడతారు — "
        "ఒక్కోసారి ఆ మూత ఒక్కసారిగా తెరుచుకుంటుంది."
    ),
    ContentCategory.PSYCHOLOGICAL_TWIST: (
        "మన మనస్సే మనకు శత్రువు అవుతుంది కొన్నిసార్లు. "
        "నిజం అనుకున్నది అబద్ధమో — "
        "కలలో చూసింది నిజమో తెలియని స్థితి."
    ),
    ContentCategory.STRANGE_EVENT: (
        "జీవితంలో కొన్ని సంఘటనలు వివరణకు అందవు. "
        "అవి జరుగుతాయి — మనం నమ్మినా నమ్మకపోయినా."
    ),
    ContentCategory.KARMA_JUSTICE: (
        "అన్యాయంగా చేసే ప్రతిది తిరిగి వస్తుంది. "
        "కాలానికి మనసు ఉంది — "
        "జ్ఞాపకం ఉంది."
    ),
    ContentCategory.EMOTIONAL_SUSPENSE: (
        "కొన్ని మాటలు జీవితకాలం చెప్పలేకపోతాం. "
        "వాటిని తర్వాత వింటే — "
        "గుండె మూగబోతుంది."
    ),
    ContentCategory.SOFT_HORROR: (
        "మనకు అర్థంకాని అనుభవాలు మనలో ఒక భాగం నుండే వస్తాయి. "
        "ఆ భాగాన్ని మనం చాలాసార్లు పట్టించుకోం — "
        "అది మనల్ని పట్టించుకుంటుంది."
    ),
    ContentCategory.CRIME_NO_VIOLENCE: (
        "నేరాలు అన్నీ బయటనుండి జరగవు — "
        "కొన్ని మనకు చాలా దగ్గరగా ఉంటాయి, "
        "మనం గమనించే వరకు."
    ),
    ContentCategory.FAMILY_SUSPENSE: (
        "కుటుంబంలో అందరికీ చెప్పుకోలేని రహస్యాలు ఉంటాయి. "
        "వాటి భారం ఒక్కళ్ళే మోస్తారు — "
        "ఎవరికీ చెప్పకుండా."
    ),
    ContentCategory.POOR_VS_RICH: (
        "డబ్బు లేదు అని అర్థం కాదు శక్తి లేదు అని. "
        "అసలు శక్తి ఎక్కడ ఉంటుందో "
        "అది తెలుసుకోవడానికి సమయం పడుతుంది."
    ),
}

# Varied closing lines — avoids same CTA every time
_CLOSING_VARIANTS = [
    "మీకు ఇలాంటి అనుభవం ఉందా? Comment లో చెప్పండి.",
    "ఇది నిజంగా జరిగింది అని మీరు నమ్ముతారా?",
    "ఈ కథలో నిజమేమిటో — మీరే నిర్ణయించండి.",
    "అలాంటప్పుడు మీరు ఏం చేసేవారు?",
    "మీకు ఏమనిపించింది? వినాలని ఉంది.",
    "ఇలాంటి కథలు మరిన్ని కావాలంటే — Follow చేయండి.",
]


def _build_script(
    hook: str,
    premise: str,
    twist: str,
    category_voice: str,
    structure: str,
    opening: str,
) -> str:
    """Assemble a script using the chosen structure."""

    if structure == "cold_open":
        return (
            f"{hook}\n\n"
            f"{opening}\n\n"
            f"{category_voice}\n\n"
            f"{premise}\n\n"
            f"అన్ని ముక్కలు కలిసాయి —\n\n"
            f"{twist}"
        )
    elif structure == "object_mystery":
        return (
            f"{opening}\n\n"
            f"{hook}\n\n"
            f"{premise}\n\n"
            f"ఆ వస్తువు నిజం చెప్పింది —\n\n"
            f"{twist}"
        )
    elif structure == "unreliable_narrator":
        return (
            f"{opening}\n\n"
            f"{hook}\n\n"
            f"{category_voice}\n\n"
            f"{premise}\n\n"
            f"కానీ నిజం — ఇది:\n\n"
            f"{twist}"
        )
    elif structure in ("missing_person_clue", "silent_witness"):
        return (
            f"{hook}\n\n"
            f"{opening}\n\n"
            f"{premise}\n\n"
            f"ఆ clue దారి చూపించింది —\n\n"
            f"{twist}"
        )
    elif structure == "emotional_reveal":
        return (
            f"{hook}\n\n"
            f"{premise}\n\n"
            f"{category_voice}\n\n"
            f"{opening}\n\n"
            f"{twist}"
        )
    elif structure == "reverse_expectation":
        return (
            f"{opening}\n\n"
            f"{hook}\n\n"
            f"{premise}\n\n"
            f"అందరూ తప్పు అర్థం చేసుకున్నారు —\n\n"
            f"{twist}"
        )
    else:  # final_line_twist
        return (
            f"{hook}\n\n"
            f"{premise}\n\n"
            f"{category_voice}\n\n"
            f"అన్నీ సాధారణంగా కనపడతాయి — \n\n"
            f"{twist}"
        )


def generate_script(idea: StoryIdea, provider: str | None = None) -> StoryScript:
    """Generate a Telugu script from a StoryIdea using structural variety."""
    provider = provider or DEFAULT_TEXT_PROVIDER

    if provider != "mock":
        import warnings
        warnings.warn(
            f"Provider '{provider}' not implemented in v1. Falling back to mock.",
            stacklevel=2,
        )

    category_key = idea.category if isinstance(idea.category, str) else idea.category.value
    category_voice = _PREMISE_VOICE.get(category_key, _PREMISE_VOICE[ContentCategory.MIDNIGHT_MYSTERY])

    # Pick structure based on twist_type or random
    twist_type = getattr(idea, "twist_type", "") or ""
    if twist_type in ("emotional_reveal", "sacrifice_reveal", "maternal_secret"):
        structure = "emotional_reveal"
    elif twist_type in ("narrator_unreliability", "mental_health_reveal"):
        structure = "unreliable_narrator"
    elif twist_type in ("posthumous_message", "hidden_object_discovery"):
        structure = "object_mystery"
    elif twist_type in ("identity_reversal", "undercover_reveal"):
        structure = "cold_open"
    else:
        structure = random.choice(_STRUCTURES)

    opening = random.choice(_STRUCTURE_OPENINGS[structure])
    closing = random.choice(_CLOSING_VARIANTS)

    full_script = (
        _build_script(
            hook=idea.hook,
            premise=idea.premise,
            twist=idea.twist,
            category_voice=category_voice,
            structure=structure,
            opening=opening,
        ).strip()
        + f"\n\n{closing}"
    )

    youtube_title = f"{idea.title} | Midnight Telugu | Telugu Short Story"
    youtube_desc = (
        f"{idea.hook}\n\n"
        f"Category: {category_key}\n\n"
        "Midnight Telugu — మిస్టరీ, హారర్, సస్పెన్స్ Telugu Short Stories.\n"
        "Subscribe చేయండి మరిన్ని కథలకు.\n\n"
        "#MidnightTelugu #TeluguShorts #TeluguMystery #TeluguStories"
    )

    return StoryScript(
        id=f"script_{uuid.uuid4().hex[:8]}",
        idea_id=idea.id,
        title=idea.title,
        category=idea.category,
        hook_line=idea.hook,
        full_script_telugu=full_script,
        estimated_duration_seconds=idea.estimated_duration_seconds,
        youtube_title=youtube_title,
        youtube_description=youtube_desc,
        youtube_hashtags=[
            "MidnightTelugu", "TeluguShorts", "TeluguMystery",
            "TeluguStories", "TeluguSuspense",
        ],
    )
