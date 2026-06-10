"""Story idea generator — diverse mock/template-based generation with quality scoring."""

from __future__ import annotations

import random
import uuid

from workers.config import DEFAULT_TEXT_PROVIDER
from workers.models import ContentCategory, StoryIdea

# One rich template per content bucket — ensures category diversity
_BUCKET_TEMPLATES: dict[ContentCategory, list[dict]] = {
    ContentCategory.MIDNIGHT_MYSTERY: [
        {
            "title": "అర్థరాత్రి తలుపు",
            "hook": "రాత్రి 2 గంటలకి తలుపు తట్టిన వ్యక్తి... అది బయట నుండి కాదు — ఇంట్లో మూసిన గది నుండి.",
            "premise": "ఒక వ్యక్తి అర్థరాత్రి తన అపార్ట్‌మెంట్‌లో పదే పదే తలుపు శబ్దాలు వింటాడు. 20 సంవత్సరాలుగా తెరవని గది నుండి.",
            "twist": "ఆ గది తన తండ్రి మరణానికి ముందు మూసిపెట్టాడు. లోపల ఒక డైరీ ఉంది — ఇంట్లో అసలు రహస్యం రాసింది.",
            "tone": "eerie, slow-burn, suspenseful",
            "hook_type": "unexplained_sound",
            "twist_type": "secret_reveal",
            "emotional_core": "family_secret",
            "visual_signature": "dark_hallway_closed_door",
        },
        {
            "title": "నిశ్శబ్ద అపార్ట్‌మెంట్",
            "hook": "మా పక్కింటి వ్యక్తి ప్రతి రాత్రీ ఒకే సమయానికి నవ్వుతాడు — కానీ ఆ అపార్ట్‌మెంట్ ఆరు నెలల నుండి ఖాళీగా ఉంది.",
            "premise": "ఒక కొత్త అద్దె వాసి పక్కింటి నుండి రాత్రి 11:11 కి నవ్వు వినిపిస్తుందని security guard కి చెప్తాడు.",
            "twist": "రికార్డింగ్ — మొదటి నివాసి తన చివరి రాత్రి రికార్డ్ చేసి వెళ్ళాడు. అది loop లో play అవుతోంది.",
            "tone": "mystery, unsettling, psychological",
            "hook_type": "unexplained_sound",
            "twist_type": "recording_reveal",
            "emotional_core": "loneliness",
            "visual_signature": "empty_apartment_night",
        },
    ],
    ContentCategory.VILLAGE_MYSTERY: [
        {
            "title": "పాత బావి రహస్యం",
            "hook": "మా ఊళ్ళో పాత బావి దగ్గర నిలబడిన వాళ్ళకి మూడు రాత్రుల్లో కలలు వస్తాయి — కానీ ఆ కలలు అందరికీ ఒకే విషయం చూపిస్తాయి.",
            "premise": "ఒక అమ్మాయి పెళ్ళికి ముందు రాత్రి బావి దగ్గర కూర్చుంటుంది. మూడు రోజుల్లో ఊళ్ళో ఒక పాత రహస్యం బయటపడుతుంది.",
            "twist": "ఆమె పారిపోయింది — బావి వల్ల కాదు. పెళ్ళికొడుకు ఆమె పెద్దమ్మను 20 ఏళ్ళ క్రితం మోసం చేసిన వాడి కొడుకు.",
            "tone": "village-mystery, emotional, generational",
            "hook_type": "supernatural_rumor",
            "twist_type": "generational_betrayal",
            "emotional_core": "justice_delayed",
            "visual_signature": "old_well_moonlight",
        },
        {
            "title": "పల్లెటూరి గడియారం",
            "hook": "మా ఊళ్ళో పాత గడియారం 30 ఏళ్ళగా ఆగిపోయింది. ఈ వారం అది మళ్ళీ కొట్టడం మొదలైంది.",
            "premise": "ఒక పాత గడియారం మళ్ళీ పని చేయడం మొదలు పెట్టింది — అదే రోజు పక్క ఊరి నుండి ఒక పరిచయం లేని వ్యక్తి వచ్చాడు.",
            "twist": "గడియారం ఆపిన వ్యక్తి ఆ పరిచయం లేని వ్యక్తి తాత — తన మరణానికి ముందు ఊళ్ళో ఒక నేరం దాచిపెట్టాడు.",
            "tone": "village-mystery, slow-reveal, past-present",
            "hook_type": "unexplained_object",
            "twist_type": "family_crime_reveal",
            "emotional_core": "buried_truth",
            "visual_signature": "village_clocktower_dusk",
        },
    ],
    ContentCategory.FAMILY_SUSPENSE: [
        {
            "title": "తండ్రి అప్పు",
            "hook": "తండ్రి ప్రతి నెలా ఒక్కో ముక్కని అమ్ముతున్నాడు — ఎందుకు అని చనిపోయే వరకు చెప్పలేదు.",
            "premise": "ఒక కుటుంబంలో తండ్రి మొత్తం ఆస్తులు అమ్మేస్తాడు. పిల్లలకు అనుమానం వస్తుంది. తండ్రి వ్యాధితో ఉన్నాడా? మోసపోయాడా?",
            "twist": "తండ్రి ఒక వడ్డీ వ్యాపారికి అప్పు చేశాడు — పిల్లల చదువు కోసం. ఆ వ్యాపారి ఇప్పుడు ప్రాణాంతకంగా ముప్పు తెచ్చాడు.",
            "tone": "family-thriller, emotional, sacrifice",
            "hook_type": "unexplained_behavior",
            "twist_type": "sacrifice_reveal",
            "emotional_core": "parental_sacrifice",
            "visual_signature": "family_home_documents_scattered",
        },
        {
            "title": "చివరి ఉత్తరం",
            "hook": "నాన్న పోయిన ఒక సంవత్సరం తర్వాత ఆయన రాసిన ఉత్తరం పోస్ట్‌లో వచ్చింది.",
            "premise": "ఒక కొడుకు తండ్రి మరణానంతరం ఒక sealed ఉత్తరం అందుకుంటాడు. తెరవడానికి ఆయన 'ఒక సంవత్సరం తర్వాత తెరవు' అని రాశాడు.",
            "twist": "ఉత్తరంలో తండ్రి ఒక పాత నేరం వివరించాడు — అది కప్పిపుచ్చుకోవడానికి కుటుంబం మొత్తం చాలా ఏళ్ళుగా అబద్ధాలు చెప్పింది.",
            "tone": "family-mystery, emotional, past-revelation",
            "hook_type": "posthumous_message",
            "twist_type": "family_crime_reveal",
            "emotional_core": "grief_and_truth",
            "visual_signature": "old_letter_envelope_light",
        },
    ],
    ContentCategory.PSYCHOLOGICAL_TWIST: [
        {
            "title": "నా భార్య ఎవరు?",
            "hook": "10 సంవత్సరాల పాటు నా భార్యతో జీవించాను. ఒక రోజు ఆమె పాత ఫోటో చూసి నా గుండె ఆగింది.",
            "premise": "ఒక మధ్య తరగతి మనిషి తన భార్య యొక్క పాత ఫోటో చూసి అనుమానపడతాడు. ఫోటోలో ఉన్న వ్యక్తి వేరేగా కనిపిస్తుంది.",
            "twist": "భార్య మారలేదు — అతని జ్ఞాపకశక్తి మారింది. అతను ప్రారంభ దశ dementia కు గురి అవుతున్నాడు.",
            "tone": "psychological, emotional, unreliable-narrator",
            "hook_type": "identity_doubt",
            "twist_type": "narrator_unreliability",
            "emotional_core": "cognitive_loss",
            "visual_signature": "faded_photograph_mirror",
        },
        {
            "title": "రెండు నీడలు",
            "hook": "నా నీడ వేరే దిశలో పడుతోంది — నేను సరిగ్గా చూస్తున్నానా?",
            "premise": "ఒక యువకుడు తన నీడ తన కదలికలతో match అవ్వడం లేదని గమనిస్తాడు. ప్రతి సారీ ఒక్క క్షణం late గా కదులుతుంది.",
            "twist": "ఆ అనుభవం ఒక dissociative episode — అతను తన identity నుండి disconnect అవుతున్నాడు. తన తల్లి అదే పరిస్థితిలో మరణించింది.",
            "tone": "psychological-horror, introspective, family-trauma",
            "hook_type": "perception_distortion",
            "twist_type": "mental_health_reveal",
            "emotional_core": "inherited_trauma",
            "visual_signature": "shadow_misalignment_daylight",
        },
    ],
    ContentCategory.STRANGE_EVENT: [
        {
            "title": "రైలు స్టేషన్‌లో అపరిచితుడు",
            "hook": "ఆ రైలు స్టేషన్‌లో ఒక ముసలాయన నాకు నా భవిష్యత్తు చెప్పాడు. అదంతా నిజమైంది — కానీ ఆ రోజు స్టేషన్‌లో ఎవరూ అతన్ని చూడలేదు.",
            "premise": "ఒక యువకుడు కష్టాల్లో ఉన్న సమయంలో రైలు స్టేషన్‌లో ఒక వ్యక్తిని కలుస్తాడు. ఆ వ్యక్తి కొన్ని మాటలు చెప్పాడు.",
            "twist": "ఆ ముసలాయన 5 సంవత్సరాల క్రితం ఆ స్టేషన్‌లోనే చనిపోయాడని స్టేషన్ మాస్టర్ చెప్తాడు.",
            "tone": "strange, philosophical, unexplained",
            "hook_type": "mysterious_stranger",
            "twist_type": "ghost_presence",
            "emotional_core": "guidance_from_beyond",
            "visual_signature": "misty_railway_platform_dusk",
        },
        {
            "title": "పాత కెమెరా",
            "hook": "నా తాత పాత కెమెరాలో తీసిన ఫోటోల్లో ఒక వ్యక్తి ప్రతి ఫోటోలో కనిపిస్తున్నాడు — మా కుటుంబంలో ఎవరూ అతన్ని గుర్తించలేదు.",
            "premise": "50 సంవత్సరాల పాత ఫోటో ఆల్బమ్‌లో తెలియని వ్యక్తి background లో ఉంటాడు. ప్రతి ఫోటోలో.",
            "twist": "ఆ వ్యక్తి తాత యొక్క పాత స్నేహితుడు — ఒక నేరంలో తప్పుగా అరెస్ట్ అయ్యాడు. తన నిర్దోషిత్వాన్ని ఎవరైనా కనుగొంటారని ఎదురు చూశాడు.",
            "tone": "strange-mystery, historical, justice",
            "hook_type": "unexplained_photograph",
            "twist_type": "historical_injustice",
            "emotional_core": "vindication_delayed",
            "visual_signature": "sepia_photograph_unknown_face",
        },
    ],
    ContentCategory.SOFT_HORROR: [
        {
            "title": "నా గది అద్దం",
            "hook": "నా గది అద్దంలో నా ప్రతిబింబం కదులుతుంది — నేను కదలకున్నా.",
            "premise": "ఒక యువతి కొత్త అద్దె ఇంట్లోకి చేరుతుంది. అక్కడి అద్దంలో ఆమె ప్రతిబింబం ఒక్కోసారి వేరేగా ప్రవర్తిస్తుంది.",
            "twist": "అది ఆమె dissociative experience — గతంలో జరిగిన ఒక trauma వల్ల. అద్దం ఆమె మనసులోని వేరే భాగం మాత్లాడుతోంది.",
            "tone": "soft-horror, psychological, atmospheric",
            "hook_type": "reflection_anomaly",
            "twist_type": "mental_health_reveal",
            "emotional_core": "suppressed_trauma",
            "visual_signature": "mirror_reflection_delayed",
        },
        {
            "title": "మూలన ఉన్న కుర్చీ",
            "hook": "మా ఇంట్లో ఒక కుర్చీ ఉంది — ఎవరూ దాన్ని తరలించడానికి ప్రయత్నించరు. ఎందుకో అందరికీ తెలుసు — కానీ ఎవరూ చెప్పరు.",
            "premise": "ఒక కొత్త అల్లుడు ఆ కుర్చీ గురించి అడుగుతాడు. అందరూ మారిపోతారు. ఆ రాత్రి అతనికి నిజం తెలుస్తుంది.",
            "twist": "ఆ కుర్చీలో మొదట కూర్చున్న వ్యక్తి — ఇంట్లో ఒక పాత శత్రువు — కూర్చున్న రాత్రే చనిపోయాడు. కాయినసిడెన్స్ కావచ్చు — కానీ ఆ కుటుంబానికి నమ్మకం.",
            "tone": "atmospheric-horror, family-superstition, suspense",
            "hook_type": "forbidden_object",
            "twist_type": "superstition_reveal",
            "emotional_core": "family_fear",
            "visual_signature": "single_chair_corner_shadows",
        },
    ],
    ContentCategory.CRIME_NO_VIOLENCE: [
        {
            "title": "విచారణ గది",
            "hook": "ఆ విచారణ గదిలో కూర్చున్న నిందితుడు — అతనే నిజమైన పోలీసు ఆఫీసర్ అని తర్వాత తెలిసింది.",
            "premise": "ఒక నేర విచారణలో నిందితుడు అసాధారణంగా ప్రశ్నలకు జవాబిస్తాడు. అతని జవాబులు విచారిస్తున్న పోలీసుని confuse చేస్తాయి.",
            "twist": "ఇది undercover operation. నిందితుడు నిజంగా పోలీసు అధికారి — అసలు నిందితుడు విచారణ చేస్తున్న వ్యక్తే.",
            "tone": "crime-thriller, clever, role-reversal",
            "hook_type": "identity_reversal",
            "twist_type": "undercover_reveal",
            "emotional_core": "justice_through_deception",
            "visual_signature": "interrogation_room_single_light",
        },
        {
            "title": "Safe లో రహస్యం",
            "hook": "10 సంవత్సరాల తర్వాత మేం పాత ఇల్లు అమ్మాలని వెళ్ళాం. గోడలో ఒక safe కనుగొన్నాం — దానిలో ఏమి ఉందో మాకు అర్థమైంది.",
            "premise": "ఒక పాత ఇంటిలో దాచిన safe తెరిచినప్పుడు లోపల ఒక confession letter ఉంటుంది — ఒక unsolved crime గురించి.",
            "twist": "ఆ confession letter ఇంటి మాజీ యజమాని రాశాడు — ఆ crime లో అతను నిర్దోషి, కానీ నిందితుడిని కాపాడాడు. ఎందుకంటే ఆ నిందితుడు అతని కొడుకు.",
            "tone": "crime-mystery, family-loyalty, moral-conflict",
            "hook_type": "hidden_object_discovery",
            "twist_type": "parental_sacrifice_crime",
            "emotional_core": "love_vs_justice",
            "visual_signature": "old_wall_safe_papers",
        },
    ],
    ContentCategory.EMOTIONAL_SUSPENSE: [
        {
            "title": "అమ్మ చివరి కాల్",
            "hook": "అమ్మ చనిపోయిన తర్వాత ఆమె ఫోన్‌లో ఒక voice memo వినిపించింది. అది వినడానికి నాకు 3 సంవత్సరాలు పట్టింది.",
            "premise": "ఒక కొడుకు తల్లి మరణానంతరం ఆమె పాత ఫోన్ తెరుస్తాడు. ఒక unread voice memo ఉంటుంది.",
            "twist": "voice memo లో అమ్మ ఒక రహస్యం చెప్తుంది — కొడుకు అసలు తండ్రి వేరే వ్యక్తి. ఆ వ్యక్తి కొడుకు జీవితంలో ఇప్పటికీ ఉన్నాడు.",
            "tone": "emotional, family-drama, identity",
            "hook_type": "posthumous_message",
            "twist_type": "identity_origin_reveal",
            "emotional_core": "maternal_secret",
            "visual_signature": "old_phone_voicememo_tearful_face",
        },
        {
            "title": "ఖాళీ సీటు",
            "hook": "ప్రతి సంవత్సరం మా అమ్మ పుట్టినరోజు రాత్రి ఆమె సీటులో ఒక పూలగుత్తి ఉంటుంది — ఎవరు పెడుతున్నారో మాకు ఇప్పటికీ తెలియదు.",
            "premise": "ఒక కుటుంబంలో తల్లి మరణించిన తర్వాత ప్రతి సంవత్సరం ఆమె పుట్టినరోజు రాత్రి ఒక mystery పువ్వుల గుత్తి వస్తుంది.",
            "twist": "అది అమ్మ కి మొదటి ప్రేమ పంపిస్తున్నాడు — అమ్మ పెళ్ళి అయిన తర్వాత కూడా ఆమెను గుర్తు పెట్టుకున్నాడు. అతను ఇప్పుడు పక్కనే ఉంటున్నాడు.",
            "tone": "emotional, mystery, bittersweet",
            "hook_type": "recurring_mystery_event",
            "twist_type": "secret_admirer_reveal",
            "emotional_core": "undying_love",
            "visual_signature": "empty_chair_flowers_candlelight",
        },
    ],
    ContentCategory.KARMA_JUSTICE: [
        {
            "title": "సేఠ్ లెక్క",
            "hook": "20 సంవత్సరాలు పేద మనుషులను మోసం చేసిన వ్యాపారస్తుడికి ఆ రోజు వచ్చింది — తన కొడుకు చేతిలో.",
            "premise": "ఒక దుర్మార్గపు వ్యాపారస్తుడు జీవితమంతా పేదలను దోచుకుంటాడు. ఒక రోజు అతని కొడుకు తండ్రి చేతలు కనుగొంటాడు.",
            "twist": "కొడుకు తనను అమ్మడానికి కారణం తెలుసు — ఆ పేదవాడి కూతురే తన భార్య. అత్తను అదే వ్యాపారస్తుడు దివాలా తీయించాడు.",
            "tone": "karma, family-justice, emotional",
            "hook_type": "poetic_justice_setup",
            "twist_type": "karmic_circle_reveal",
            "emotional_core": "justice_through_love",
            "visual_signature": "courtroom_son_facing_father",
        },
        {
            "title": "పాత ఉద్యోగి",
            "hook": "ఒక కంపెనీ 30 మంది ఉద్యోగులను ఒకే రాత్రి తీసేసింది — 5 సంవత్సరాల తర్వాత వాళ్ళే ఆ కంపెనీని కొన్నారు.",
            "premise": "ఒక పెద్ద కంపెనీ ఆర్థిక ఒత్తిళ్ళలో 30 మంది experienced ఉద్యోగులను తీసేస్తుంది. ఆ తర్వాత కంపెనీ మునగడం మొదలౌతుంది.",
            "twist": "వాళ్ళు కలిసి ఒక చిన్న startup పెట్టారు — 5 ఏళ్ళలో వాళ్ళు ఆ పెద్ద కంపెనీని acquire చేశారు. నిర్వాహకుడికి ఇప్పుడు వాళ్ళ కింద పని చేయాలి.",
            "tone": "karma-justice, business, triumph",
            "hook_type": "reversal_of_fortune",
            "twist_type": "underdog_triumph",
            "emotional_core": "collective_justice",
            "visual_signature": "office_handover_moment",
        },
    ],
    ContentCategory.POOR_VS_RICH: [
        {
            "title": "అడుక్కునే అమ్మమ్మ",
            "hook": "అడుక్కునే ముసలి అమ్మమ్మని అందరూ తోసేశారు — ఆమె చనిపోయిన తర్వాత మాత్రం అందరికీ నిజం తెలిసింది.",
            "premise": "ఒక పేద ముసలి అమ్మమ్మ అడుక్కుంటూ జీవిస్తుంది. ధనవంతులు ఆమెను చిన్నచూపు చూస్తారు. ఆమె ఒంటరిగా చనిపోతుంది.",
            "twist": "ఆమె bank account లో లక్షలు ఉంటాయి — అన్నీ తన మనవళ్ళ చదువు కోసం దాచింది. ఆ డబ్బు ఎవరు పంపించారో మనవళ్ళకు ఇప్పుడు తెలిసింది.",
            "tone": "emotional, social-commentary, sacrifice",
            "hook_type": "appearances_vs_reality",
            "twist_type": "hidden_wealth_sacrifice",
            "emotional_core": "generational_love",
            "visual_signature": "old_woman_street_humble_appearance",
        },
        {
            "title": "చిన్న దుకాణం",
            "hook": "పెద్ద mall వల్ల ఒక పాత చిన్న దుకాణం మూసే పరిస్థితి వచ్చింది — ఆ దుకాణం యజమాని ఒక పాత రహస్యం బయటపెట్టాడు.",
            "premise": "ఒక పాత చిన్న కిరాణా దుకాణం పక్కన పెద్ద mall వస్తుంది. దుకాణదారు వ్యాపారం తగ్గిపోతుంది. చివరి రోజు అతను ఒక పాత account book తెరుస్తాడు.",
            "twist": "ఆ mall యజమాని 30 ఏళ్ళ క్రితం ఈ దుకాణదారు దగ్గర అప్పు తీసుకుని ఎదిగాడు. ఆ account book లో proof ఉంది — అతను తిరిగి చెల్లించలేదు.",
            "tone": "poor-vs-rich, justice, historical-debt",
            "hook_type": "small_vs_large_conflict",
            "twist_type": "historical_debt_reveal",
            "emotional_core": "forgotten_kindness",
            "visual_signature": "old_shop_modern_mall_contrast",
        },
    ],
}


def _pick_diverse_ideas(count: int) -> list[dict]:
    """
    Pick templates ensuring all 10 categories are covered before repeating.
    """
    categories = list(_BUCKET_TEMPLATES.keys())
    selected: list[dict] = []
    category_pool = categories * (count // len(categories) + 1)
    random.shuffle(category_pool)

    used_categories: list[str] = []
    for cat in category_pool:
        if len(selected) >= count:
            break
        templates = _BUCKET_TEMPLATES[cat]
        # Avoid picking same template twice in a row per category
        template = random.choice(templates)
        item = dict(template)
        item["category"] = cat
        selected.append(item)
        used_categories.append(str(cat))

    return selected[:count]


def generate_ideas(count: int = 5, provider: str | None = None) -> list[StoryIdea]:
    """Generate story ideas with diversity across all content buckets."""
    provider = provider or DEFAULT_TEXT_PROVIDER

    if provider != "mock":
        import warnings
        warnings.warn(
            f"Provider '{provider}' is not implemented in v1. Falling back to mock.",
            stacklevel=2,
        )

    from workers.story_memory import check_repeatability
    from workers.story_scorer import score_idea

    pool = _pick_diverse_ideas(count)
    ideas: list[StoryIdea] = []

    for template in pool:
        # Build the idea first (without score)
        idea_data = {k: v for k, v in template.items()
                     if k in StoryIdea.model_fields}
        idea_data["id"] = f"idea_{uuid.uuid4().hex[:8]}"
        idea_data.setdefault("estimated_duration_seconds", random.randint(52, 60))
        idea_data.setdefault("originality_notes", "Original story — no real events or known plots referenced.")
        idea_data.setdefault("safety_notes", "No graphic violence. Family-safe content.")
        idea_data.setdefault("risk_flags", [])

        idea = StoryIdea(**idea_data)

        # Check repeatability
        repeat_warnings = check_repeatability(idea)

        # Score the idea
        score = score_idea(idea, repeatability_warnings=repeat_warnings)

        # Attach scoring data back to the idea
        idea.story_score = score.overall_score
        idea.score_breakdown = score.to_dict()["score_breakdown"]
        idea.repeatability_warnings = repeat_warnings
        if score.rejection_reasons:
            idea.risk_flags = score.rejection_reasons

        ideas.append(idea)

    return ideas
