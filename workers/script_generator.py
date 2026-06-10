"""Script generator — mock/template-based for v1."""

from __future__ import annotations

import uuid

from workers.config import DEFAULT_TEXT_PROVIDER
from workers.models import ContentCategory, StoryIdea, StoryScript

_SCRIPT_TEMPLATE = """\
{hook_line}

అందరూ అనుకున్నారు ఇది సాధారణ విషయమని. కానీ అది కాదు.

{premise_expanded}

ఆ రాత్రి అన్నీ మారిపోయాయి.

{build_up}

చివరికి సత్యం బయటపడింది —

{twist_reveal}

మీరు ఇలాంటి విషయాలు నమ్ముతారా? Comment లో చెప్పండి.
"""

_PREMISE_EXPANSIONS: dict[str, str] = {
    ContentCategory.MIDNIGHT_MYSTERY: (
        "అర్థరాత్రి తర్వాత మాత్రమే కొన్ని రహస్యాలు తెరుచుకుంటాయి. "
        "ఆ వ్యక్తికి తెలుసు — ప్రతి రాత్రి ఆ గంటకు ఏదో జరుగుతుంది."
    ),
    ContentCategory.VILLAGE_MYSTERY: (
        "మా ఊళ్ళో పెద్దలు అన్ని విషయాలు చెప్పరు. కొన్ని నిజాలు తరాల పాటు మూసి పెడతారు."
    ),
    ContentCategory.PSYCHOLOGICAL_TWIST: (
        "మన మనస్సే మనకు శత్రువు అవుతుంది కొన్నిసార్లు. "
        "నిజం అనుకున్నది అబద్ధమో, కలలో చూసింది నిజమో తెలియని స్థితి."
    ),
    ContentCategory.STRANGE_EVENT: (
        "జీవితంలో కొన్ని సంఘటనలు వివరణకు అందవు. అవి జరుగుతాయి — మనం నమ్మినా నమ్మకపోయినా."
    ),
    ContentCategory.KARMA_JUSTICE: (
        "అన్యాయంగా చేసే ప్రతిది తిరిగి వస్తుంది. కాలానికి మనసు ఉంది."
    ),
    ContentCategory.EMOTIONAL_SUSPENSE: (
        "కొన్ని మాటలు జీవితకాలం చెప్పలేకపోతాం. "
        "వాటిని తర్వాత వింటే గుండె ఆగిపోతుంది."
    ),
    ContentCategory.SOFT_HORROR: (
        "మనకు అర్థంకాని అనుభవాలు మనలో ఒక భాగం నుండే వస్తాయి. "
        "ఆ భాగాన్ని మనం చాలాసార్లు పట్టించుకోం."
    ),
    ContentCategory.CRIME_NO_VIOLENCE: (
        "నేరాలు అన్నీ బయటనుండి జరగవు — కొన్ని మనకు చాలా దగ్గరగా ఉంటాయి."
    ),
    ContentCategory.FAMILY_SUSPENSE: (
        "కుటుంబంలో అందరికీ చెప్పుకోలేని రహస్యాలు ఉంటాయి. "
        "వాటి భారం ఒక్కళ్ళే మోస్తారు."
    ),
    ContentCategory.POOR_VS_RICH: (
        "డబ్బుకి ఎదురు తిరిగిన వాళ్ళని అందరూ పిచ్చివాళ్ళు అంటారు. "
        "కానీ వాళ్ళకే నిజమైన శక్తి ఉంటుంది."
    ),
}


def generate_script(idea: StoryIdea, provider: str | None = None) -> StoryScript:
    """Generate a Telugu script from a StoryIdea using mock templates."""
    provider = provider or DEFAULT_TEXT_PROVIDER

    if provider != "mock":
        import warnings
        warnings.warn(
            f"Provider '{provider}' not implemented in v1. Falling back to mock.",
            stacklevel=2,
        )

    category_key = idea.category if isinstance(idea.category, str) else idea.category.value
    premise_expansion = _PREMISE_EXPANSIONS.get(
        category_key,
        _PREMISE_EXPANSIONS[ContentCategory.MIDNIGHT_MYSTERY],
    )

    build_up = (
        f"{idea.premise}\n\n"
        "క్రమక్రమంగా అన్ని ముక్కలు కలిసాయి. "
        "ఆ పజిల్ పూర్తయేసరికి అందరికీ నోట మాట రాలేదు."
    )

    twist_reveal = (
        f"{idea.twist}\n\n"
        "అది తెలిసిన తర్వాత, ఆ వ్యక్తి జీవితం మళ్ళీ మొదలైంది — వేరే కోణంలో."
    )

    full_script = _SCRIPT_TEMPLATE.format(
        hook_line=idea.hook,
        premise_expanded=premise_expansion,
        build_up=build_up,
        twist_reveal=twist_reveal,
    ).strip()

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
        youtube_hashtags=["MidnightTelugu", "TeluguShorts", "TeluguMystery", "TeluguStories", "TeluguSuspense"],
    )
