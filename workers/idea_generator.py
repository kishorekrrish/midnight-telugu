"""Story idea generator — mock/template-based for v1."""

from __future__ import annotations

import random
import uuid

from workers.config import DEFAULT_TEXT_PROVIDER
from workers.models import ContentCategory, StoryIdea

_IDEA_TEMPLATES: list[dict] = [
    {
        "category": ContentCategory.MIDNIGHT_MYSTERY,
        "title": "అర్థరాత్రి తలుపు",
        "hook": "రాత్రి 2 గంటలకి తలుపు తట్టిన వ్యక్తి... బయట నిల్చున్నది ఎవరో కాదు, 10 సంవత్సరాల క్రితం చనిపోయిన నా స్నేహితుడు.",
        "premise": "ఒక వ్యక్తి అర్థరాత్రి తన అపార్ట్‌మెంట్‌లో అనుమానాస్పద తలుపు శబ్దాలు వినడం మొదలు పెడతాడు. ప్రతి రాత్రీ అదే సమయానికి. కానీ తెరిస్తే ఎవరూ కనపడరు.",
        "twist": "తలుపు తట్టేది బయటి నుండి కాదు — ఇంట్లో నే ఉన్న మూసిన గదిలో నుండి. ఆ గది 20 సంవత్సరాల నుండి తెరవలేదు.",
        "tone": "suspenseful, eerie, slow-burn",
        "estimated_duration_seconds": 55,
        "originality_notes": "Original story — no real events or known plots referenced.",
        "safety_notes": "No graphic violence. Family-safe suspense.",
    },
    {
        "category": ContentCategory.VILLAGE_MYSTERY,
        "title": "పాత బావి రహస్యం",
        "hook": "మా ఊళ్ళో పాత బావి దగ్గర ఎవరైనా నిలబడితే... అది వాళ్ళ చివరి రాత్రి అవుతుందని పెద్దలు చెప్పేవారు.",
        "premise": "ఒక అమ్మాయి పెళ్ళి నిశ్చయమైన రాత్రి పాత బావి దగ్గర ఒంటరిగా కూర్చుంటుంది. తెల్లవారి ఆమె కనపడదు.",
        "twist": "ఆమె పారిపోయింది — బావి వల్ల కాదు, ఆ పెళ్ళి నుండి. పెళ్ళికొడుకు ఆమె కుటుంబాన్ని మోసం చేసినట్టు ఆమెకు తెలుసు.",
        "tone": "mystery, emotional, village-drama",
        "estimated_duration_seconds": 58,
        "originality_notes": "Original village mystery. No copied folk tale or film plot.",
        "safety_notes": "Family-safe. No violence.",
    },
    {
        "category": ContentCategory.PSYCHOLOGICAL_TWIST,
        "title": "నా భార్య ఎవరు?",
        "hook": "10 సంవత్సరాల పాటు నా భార్యతో జీవించాను. ఒక రోజు ఆమె పాత ఫోటో చూసి నా గుండె ఆగింది.",
        "premise": "ఒక మధ్య తరగతి మనిషి తన భార్య గురించి ఒక పాత ఫోటో చూసి అనుమానపడతాడు. ఫోటోలో ఉన్న వ్యక్తి అదే మనిషా కాదా అని.",
        "twist": "భార్య మారలేదు — అతని జ్ఞాపకశక్తి మారింది. అతను ప్రారంభ దశలో మతిమరపు వ్యాధికి గురి అవుతున్నాడు.",
        "tone": "psychological, emotional, slow-reveal",
        "estimated_duration_seconds": 57,
        "originality_notes": "Original psychological story. No film or book references.",
        "safety_notes": "Sensitive — mental health theme handled respectfully. No medical advice given.",
    },
    {
        "category": ContentCategory.STRANGE_EVENT,
        "title": "రైలు స్టేషన్‌లో అపరిచితుడు",
        "hook": "ఆ రైలు స్టేషన్‌లో ఒక ముసలాయన నాకు నా భవిష్యత్తు చెప్పాడు. అదంతా నిజమైంది — కానీ ఆ రోజు ఆ స్టేషన్‌లో అతన్ని ఎవరూ చూడలేదు.",
        "premise": "ఒక యువకుడు తన కష్టాల్లో ఉన్న సమయంలో రైలు స్టేషన్‌లో ఒక వ్యక్తిని కలుస్తాడు. ఆ వ్యక్తి కొన్ని మాటలు చెప్పాడు.",
        "twist": "ఆ ముసలాయన 5 సంవత్సరాల క్రితం ఆ స్టేషన్‌లోనే చనిపోయాడని స్టేషన్ మాస్టర్ చెప్తాడు.",
        "tone": "strange, philosophical, emotional",
        "estimated_duration_seconds": 53,
        "originality_notes": "Original supernatural-adjacent story.",
        "safety_notes": "No graphic content. Family-safe.",
    },
    {
        "category": ContentCategory.KARMA_JUSTICE,
        "title": "సేఠ్ లెక్క",
        "hook": "20 సంవత్సరాలు పేద మనుషులను మోసం చేసిన వ్యాపారస్తుడికి — ఆ రోజు వచ్చింది.",
        "premise": "ఒక దుర్మార్గపు వ్యాపారస్తుడు తన జీవితాంతం పేదలను దోచుకుంటాడు. చివరికి తన కొడుకే అతని మోసాలను బయటపెడతాడు.",
        "twist": "కొడుకు తనను అమ్మకేమని తెలుసుకున్నాడు — ఆ పేదవాడి కూతురే తన భార్య అని.",
        "tone": "justice, emotional, karma",
        "estimated_duration_seconds": 56,
        "originality_notes": "Original karma/justice story. Fictional characters.",
        "safety_notes": "No violence. Positive moral resolution.",
    },
    {
        "category": ContentCategory.EMOTIONAL_SUSPENSE,
        "title": "అమ్మ చివరి కాల్",
        "hook": "అమ్మ చనిపోయిన తర్వాత ఆమె ఫోన్‌లో ఒక రికార్డ్ వినిపించింది. అది వినడానికి నాకు 3 సంవత్సరాలు పట్టింది.",
        "premise": "ఒక కొడుకు తల్లి చనిపోయిన తర్వాత ఆమె పాత ఫోన్ తెరుస్తాడు. ఒక అన్‌రీడ్ వాయిస్ మెమో ఉంటుంది.",
        "twist": "వాయిస్ మెమోలో అమ్మ అతనికి క్షమాపణ చెప్తుంది — ఒక రహస్యం చెప్తుంది. ఆ రహస్యం వినేంత వరకు అతను ఆమెను అర్థం చేసుకోలేదు.",
        "tone": "emotional, family, suspense-drama",
        "estimated_duration_seconds": 58,
        "originality_notes": "Original emotional story. No real events.",
        "safety_notes": "Grief theme — handled with care. No harmful content.",
    },
    {
        "category": ContentCategory.SOFT_HORROR,
        "title": "నా గది అద్దం",
        "hook": "నా గది అద్దంలో నా ప్రతిబింబం కదులుతుంది — నేను కదలకున్నా.",
        "premise": "ఒక యువతి కొత్త అద్దె ఇంట్లోకి చేరుతుంది. అక్కడి అద్దంలో ఆమె ప్రతిబింబం ఒక్కోసారి వేరేగా ప్రవర్తిస్తుంది.",
        "twist": "అది ఆమె డిసోసియేటివ్ అనుభవం — గతంలో జరిగిన ఒక ట్రామా వల్ల. అద్దం ఆమె మనసులోని వేరే భాగం.",
        "tone": "soft-horror, psychological, character-driven",
        "estimated_duration_seconds": 54,
        "originality_notes": "Original. Psychological horror without supernatural claim.",
        "safety_notes": "Mental health portrayed responsibly. No graphic horror.",
    },
    {
        "category": ContentCategory.POOR_VS_RICH,
        "title": "అడుక్కునే అమ్మమ్మ",
        "hook": "అడుక్కునే ముసలి అమ్మమ్మని అందరూ తోసేశారు — ఆమె చనిపోయిన తర్వాత మాత్రం అందరికీ సత్యం తెలిసింది.",
        "premise": "ఒక పేద ముసలి అమ్మమ్మ అడుక్కుంటూ జీవిస్తుంది. ధనవంతులు ఆమెను చిన్నచూపు చూస్తారు. ఆమె ఒంటరిగా చనిపోతుంది.",
        "twist": "ఆమె బ్యాంక్ అకౌంట్‌లో లక్షలు ఉంటాయి — అన్నీ తన మనవళ్ళ చదువు కోసం దాచింది.",
        "tone": "emotional, social-commentary, twist-ending",
        "estimated_duration_seconds": 55,
        "originality_notes": "Original character story. No real person referenced.",
        "safety_notes": "No graphic content. Positive moral.",
    },
    {
        "category": ContentCategory.FAMILY_SUSPENSE,
        "title": "తండ్రి అప్పు",
        "hook": "తండ్రి ప్రతి నెలా ఒక్కో ముక్కని అమ్ముతున్నాడు. ఎందుకు అని ఎవరికీ చెప్పలేదు — చనిపోయే వరకు.",
        "premise": "ఒక కుటుంబంలో తండ్రి అకస్మాత్తుగా ఆస్తులు అమ్మడం మొదలు పెడతాడు. పిల్లలకు అనుమానం వస్తుంది.",
        "twist": "తండ్రి చేసిన అప్పు పిల్లల చదువు కోసమే. కానీ ఆ అప్పు చేసిన వ్యక్తి ఇప్పుడు ఇంటికి వస్తున్నాడు — వడ్డీ వసూలు చేయడానికి కాదు, తండ్రి ప్రాణాలు తీయడానికి.",
        "tone": "family-suspense, thriller, emotional",
        "estimated_duration_seconds": 58,
        "originality_notes": "Original family suspense. No film plot copied.",
        "safety_notes": "Threat depicted without graphic violence.",
    },
    {
        "category": ContentCategory.CRIME_NO_VIOLENCE,
        "title": "విచారణ గది",
        "hook": "ఆ విచారణ గదిలో కూర్చున్న నిందితుడు — అతనే నిజమైన పోలీసు ఆఫీసర్ అని తర్వాత తెలిసింది.",
        "premise": "ఒక నేర విచారణలో ఒక నిందితుడు అసాధారణంగా ప్రశ్నలకు జవాబిస్తాడు. అతని జవాబులు చాలా తెలివైనవి.",
        "twist": "ఇది ఒక అండర్‌కవర్ ఆపరేషన్. నిందితుడు నిజంగా పోలీసు అధికారి — అసలు నిందితుడు విచారణ చేస్తున్న పోలీసు.",
        "tone": "crime-thriller, clever-twist, suspense",
        "estimated_duration_seconds": 56,
        "originality_notes": "Original crime story. No real case referenced.",
        "safety_notes": "No graphic crime depiction.",
    },
]


def generate_ideas(count: int = 5, provider: str | None = None) -> list[StoryIdea]:
    """Generate story ideas using mock templates or a real provider."""
    provider = provider or DEFAULT_TEXT_PROVIDER

    if provider != "mock":
        import warnings
        warnings.warn(
            f"Provider '{provider}' is not implemented in v1. Falling back to mock.",
            stacklevel=2,
        )

    # Shuffle and pick; cycle if count > available templates
    pool = _IDEA_TEMPLATES * (count // len(_IDEA_TEMPLATES) + 1)
    random.shuffle(pool)
    selected = pool[:count]

    ideas: list[StoryIdea] = []
    for template in selected:
        idea = StoryIdea(
            id=f"idea_{uuid.uuid4().hex[:8]}",
            **template,
        )
        ideas.append(idea)
    return ideas
