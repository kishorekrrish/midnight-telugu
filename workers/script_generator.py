"""Script generator — cinematic, narrator-voice Telugu scripts (120–160 words)."""

from __future__ import annotations

import random
import re
import uuid

from workers.blueprint_validator import validate_blueprint
from workers.config import DEFAULT_TEXT_PROVIDER
from workers.models import StoryBlueprint, StoryIdea, StoryScript
from workers.story_blueprint import build_blueprint
from workers.telugu_quality import apply_telugu_replacements

# 8 structure keys
_STRUCTURES = [
    "cold_open_mystery",
    "object_clue_mystery",
    "last_letter_reveal",
    "phone_call_midnight",
    "locked_room_clue",
    "family_secret_reveal",
    "silent_witness",
    "reverse_guilt_twist",
]

# ---------------------------------------------------------------------------
# Banned ending patterns — checked here AND in script_quality.py
# ---------------------------------------------------------------------------
BANNED_ENDINGS: list[str] = [
    "మీరు ఏం చేసేవాళ్ళు?",
    "అలాంటప్పుడు మీరు ఏం చేసేవాళ్ళు?",
    "ఇదే జీవితం",
    "అప్పుడు నిజం తెలిసింది",
    "అందుకే మనం",
    "మనం నేర్చుకోవాలి",
    "ఇది మనకు నేర్పిస్తుంది",
    "నీతి ఏమిటంటే",
    "జీవితం మనకు చెప్తుంది",
    "కదా మరి",
]

# ---------------------------------------------------------------------------
# Cinematic closings — punchy final lines, NOT engagement questions or morals
# ---------------------------------------------------------------------------
_CINEMATIC_CLOSINGS: list[str] = [
    "ఆ ఉత్తరం ఇప్పటికీ అక్కడే ఉంది — unopened.",
    "ఆ తలుపు మళ్ళీ ఎప్పుడూ తెరవలేదు.",
    "ఆ రాత్రి తర్వాత వాళ్ళిద్దరూ మాట్లాడలేదు — ఎందుకో అడగలేదు.",
    "ఆ పాత ఇల్లు ఇప్పటికీ అక్కడే ఉంది. ఎవరూ అందులో ఉండరు.",
    "ఆ మాటలు ఆయన చివరి మాటలు కావు — అవే మొదటి నిజమైన మాటలు.",
    "ఆ ఫోన్ నంబర్ exist అవ్వడం లేదు — అప్పటినుండే.",
    "ఆ photograph లో ఒక్క మనిషి ఉన్నాడు. నేను ఒంటరిగా అక్కడికి వెళ్ళాను.",
    "ఆ అడుగుల చప్పుడు ఇప్పటికీ వినిపిస్తుంది — పైన ఎవరూ లేనప్పుడు.",
    "ఆ number కి call చేసినప్పుడు — నా గొంతే వినిపించింది.",
    "ఆ రాత్రికి ముందు నేను అతన్ని చూశాను. తర్వాత ఎవరూ చూడలేదు.",
    "ఆ గది లో ఒక పేరు రాసి ఉంది. అది నా పేరు.",
    "camera footage లో ఒక్క frame లో మాత్రమే కనిపించాడు. ఆ frame timestamp — నేను అక్కడ లేను.",
]

# ---------------------------------------------------------------------------
# Structure-specific full script builders (120–160 words)
# ---------------------------------------------------------------------------

def _script_cold_open_mystery(
    hook: str, char: str, place: str, object_: str, twist_line: str, closing: str
) -> str:
    return f"""{hook}

{char} ఆ {place} లోపలికి వెళ్ళినప్పుడు — గాలి ఆగింది. అక్కడ ఎవరూ లేరు అని అనుకున్నాడు. కానీ మూలలో ఒక {object_} ఉంది — తాజాగా, ఈరోజే వాడినట్లు. దాన్ని ఎవరు పెట్టారో తెలియదు.

{char} కి చెమట పట్టింది. అడుగులు ఆగాయి. చేతులు వణికాయి. ఆ {object_} అతనికి తెలిసిందే — కానీ అది ఇక్కడ ఉండకూడదు.

గుండె ఒక్కసారిగా వేగంగా కొట్టుకుంది. బయట నుండి తలుపు sound వచ్చింది. అది గాలి కాదు. శ్వాస తగ్గిపోయింది.

{char} వెనక్కి తిరిగాడు. అక్కడ ఒక నీడ — కదులుతోంది.

{twist_line}

{closing}""".strip()


def _script_object_clue(
    hook: str, char: str, place: str, object_: str, twist_line: str, closing: str
) -> str:
    return f"""{hook}

ఆ {object_} చాలా పాతది. ఎవరి దగ్గర ఉందో తెలియదు. {char} దాన్ని తీసుకుని చూసినప్పుడు — లోపల ఒక పేపర్ ఉంది. మడతపెట్టి. పాలిపోయింది.

చదివాడు. మళ్ళీ చదివాడు.

ఆ మాటలు అతనికే రాశారు — పదేళ్ళ ముందు. అతనికి అప్పుడు పుట్టుకే రాలేదు. చేతులు వణికాయి. గుండె వేగంగా కొట్టుకుంది.

{char} పక్కన ఉన్న {place} చూసాడు. అక్కడ ఒక photograph — తాజాగా పెట్టినట్లు. దుమ్ము లేదు. అందులో ఒక మనిషి. నవ్వుతున్నాడు.

కానీ — ఆ మనిషి గది లో ఎవరూ లేరు.

{twist_line}

{closing}""".strip()


def _script_last_letter(
    hook: str, char: str, place: str, object_: str, twist_line: str, closing: str
) -> str:
    return f"""{hook}

{char} ఆ {object_} తీసి చదివాడు. మొదటి మాట చూసినప్పుడే — చేతులు వణికాయి.

"ఈ ఉత్తరం నువ్వు చదివే వరకు నేను పోయి ఒక సంవత్సరం అవుతుంది. కానీ నేను రాసిన విషయం నువ్వు మర్చిపోకూడదు."

{char} కళ్ళు నిండాయి. తర్వాతి మాటలు చదివాడు. మళ్ళీ చదివాడు. ఆ {place} లో కూర్చుని, నిశ్శబ్దంలో — శ్వాస ఆగినట్లు అనిపించింది.

ఆ రహస్యం చాలా సంవత్సరాలు దాగి ఉంది. ఒక్క ఆత్మ తప్ప అందరికీ తెలుసు. అందరూ కాపాడారు. ఒక్కో మాట ఒక్కో బాధ.

{twist_line}

{closing}""".strip()


def _script_phone_call(
    hook: str, char: str, place: str, object_: str, twist_line: str, closing: str
) -> str:
    return f"""{hook}

అర్థరాత్రి 2:47. {char} నిద్రపోతున్నాడు. ఆ {object_} మోగింది.

Unknown number.

తీసుకున్నాడు. అవతల నుండి శ్వాస మాత్రమే వినిపించింది. తర్వాత — ఒక గొంతు. నెమ్మదిగా. అతనికి తెలిసిన గొంతు. చాలాకాలం వినలేదు.

"{char}. ఆ {place} కి వెళ్ళకు. ఎందుకంటే —"

Line cut అయింది.

{char} ఆ number కి call back చేసాడు. Not reachable. మళ్ళీ. మళ్ళీ. లేదు. గుండె చల్లగా అయింది.

తర్వాత తెలిసింది — ఆ number చాలా కాలం క్రితే disconnect అయింది.

{twist_line}

{closing}""".strip()


def _script_locked_room(
    hook: str, char: str, place: str, object_: str, twist_line: str, closing: str
) -> str:
    return f"""{hook}

ఆ {place} లో ఒక గది ఉంది — 20 సంవత్సరాలుగా lock చేసి ఉంది. ఆ తాళం చెవి {char} తండ్రి దగ్గర ఉంది. ఆయన పోయిన తర్వాత వస్తువులలో దొరికింది. పాత పేపర్‌లో చుట్టి.

{char} తలుపు తెరిచాడు. లోపల చీకటి. దుమ్ము వాసన. కానీ అందులో ఒక {object_} — దుమ్ము లేదు. తాజాగా ఉంది. దాని పక్కన — ఒక fresh footprint.

ఎవరు వెళ్ళారు? తలుపు 20 సంవత్సరాలు lock అయి ఉంది. మరో తాళం చెవి లేదు.

{char} footprint కొలిచాడు. తన సైజే.

{twist_line}

{closing}""".strip()


def _script_family_secret(
    hook: str, char: str, place: str, object_: str, twist_line: str, closing: str
) -> str:
    return f"""{hook}

{char} కి తన కుటుంబం గురించి అన్నీ తెలుసు అనుకున్నాడు. కానీ ఆ {place} లో దొరికిన {object_} — అన్నీ తలకిందులు చేసింది.

ఒక photograph. ఒక పేరు. ఒక తేదీ.

ఆ తేదీ {char} పుట్టినరోజు. ఆ పేరు అతని పేరే. కానీ photograph లో మనిషి వేరే. అతనికి తెలియని మనిషి.

{char} అమ్మని అడిగాడు. ఆమె మాట్లాడలేదు. కళ్ళు మూసుకుంది. నిశ్శబ్దం చాలాసేపు.

తర్వాత నెమ్మదిగా — ఒక్క మాట అంది. ఆ మాట విన్న తర్వాత {char} కి అర్థమైంది — ఈ కుటుంబం గురించి అతనికి ఏమీ తెలియదు.

{twist_line}

{closing}""".strip()


def _script_silent_witness(
    hook: str, char: str, place: str, object_: str, twist_line: str, closing: str
) -> str:
    return f"""{hook}

ఆ {place} ని అందరూ ignore చేశారు. కానీ {char} ఒక్కడే గమనించాడు — అక్కడ ఏదో తప్పుగా ఉంది. రోజూ. ప్రతి రాత్రి.

రోజూ సాయంత్రం ఆ {object_} మారుతుంది. ఎవరూ తాకలేదు — కానీ మారుతుంది. {char} దాన్ని గురించి అడిగాడు. ఎవరూ నమ్మలేదు.

{char} ఒక camera పెట్టాడు. అందరికీ చెప్పలేదు. రాత్రి footage చూసాడు. 3:12 AM కి —

ఆ {object_} దగ్గర ఒక figure వచ్చింది. స్పష్టంగా కనపడింది. ముఖం కనిపించింది.

{char} screenshot తీసాడు. zoom చేసాడు. గుండె ఆగిపోయింది.

{twist_line}

{closing}""".strip()


def _script_reverse_guilt(
    hook: str, char: str, place: str, object_: str, twist_line: str, closing: str
) -> str:
    return f"""{hook}

అందరూ అనుకున్నారు — {char} తప్పు చేశాడు అని. పోలీసులు, పొరుగువాళ్ళు, కుటుంబం — అందరూ. {char} మాట్లాడలేదు. మాట్లాడలేకపోయాడు.

{char} ఆ {place} లో ఒంటరిగా కూర్చున్నాడు. పక్కన ఒక {object_}. తన దగ్గర ఒక్కటే proof ఉంది — ఒక్కటే.

కానీ దాన్ని చూపిస్తే — నిజంగా తప్పు చేసిన వ్యక్తి బయటపడతాడు. ఆ వ్యక్తి {char} ని నమ్మిన వ్యక్తి. ఆ వ్యక్తి ని {char} నమ్మాడు.

ఆ వ్యక్తి —

{twist_line}

{closing}""".strip()


_STRUCTURE_BUILDERS = {
    "cold_open_mystery": _script_cold_open_mystery,
    "object_clue_mystery": _script_object_clue,
    "last_letter_reveal": _script_last_letter,
    "phone_call_midnight": _script_phone_call,
    "locked_room_clue": _script_locked_room,
    "family_secret_reveal": _script_family_secret,
    "silent_witness": _script_silent_witness,
    "reverse_guilt_twist": _script_reverse_guilt,
}

# ---------------------------------------------------------------------------
# Category-specific characters, places, objects, twist lines
# ---------------------------------------------------------------------------

_CATEGORY_DETAILS: dict[str, dict[str, list[str]]] = {
    "midnight_mystery": {
        "chars": ["రవి", "అర్జున్", "కిరణ్", "సంతోష్"],
        "places": ["పాత ఇల్లు", "అర్ధరాత్రి దారి", "బస్ నిలయం", "రైల్వే స్టేషన్"],
        "objects": ["పాత ఉత్తరం", "పాత ఫోటో", "తాళం చెవి", "పాత డైరీ"],
        "twists": [
            "ఆ నీడ — {char} చనిపోయిన తమ్ముడిది.",
            "ఆ గది లో ఉన్న వ్యక్తి — {char} యే. పది సంవత్సరాల ముందు.",
            "ఆ అడుగు ముద్ర సైజు {char} సైజే. తాను రాలేదు. కానీ ముద్ర ఉంది.",
        ],
    },
    "village_mystery": {
        "chars": ["రాము", "లక్ష్మి", "వెంకట్", "సుభద్ర"],
        "places": ["పాత బావి దగ్గర", "చెరువు గట్టు", "పాత గుడి", "ఊరి చివర ఇల్లు"],
        "objects": ["పాత రాయి", "మట్టి కుండ", "తాళం", "పాత తలుపు"],
        "twists": [
            "బావిలో పడ్డాడని అందరూ అన్నారు. బావిలో నీళ్ళు లేవు — నాటి నుండి.",
            "ఆ చెరువులో యాభై సంవత్సరాలుగా ఎవరూ దిగలేదు. కానీ ఆ రాత్రి — అడుగుల ముద్రలు నీళ్ళ నుండి బయటకు వచ్చాయి.",
            "పాత గుడి తలుపు లోపల నుండి తాళం వేసి ఉంది. లోపల ఎవరూ లేరు.",
        ],
    },
    "family_suspense": {
        "chars": ["ప్రవీణ్", "సుమ", "మహేష్", "అనిత"],
        "places": ["పాత ఇల్లు", "అటక", "పాత అలమర", "పాత గది"],
        "objects": ["మూసి పెట్టిన ఉత్తరం", "పాత ఫోటో", "పాత పాస్‌పోర్టు", "పాత కాగితం"],
        "twists": [
            "ఆ ఫోటోలో ఉన్న మనిషి — {char} తండ్రి కాదు.",
            "ఆ ఉత్తరం చిరునామా — {char} పేరు కాదు. కానీ {char} సంతకం ఉంది.",
            "ఆ పాస్‌పోర్టులో ఫోటో — {char} అమ్మది. తేదీ — {char} పుట్టిన రోజుకు ఇరవై సంవత్సరాల ముందు. వేరే పేరు.",
        ],
    },
    "psychological_twist": {
        "chars": ["ఆదిత్య", "శ్రేయ", "విక్రమ్", "రంజిత్"],
        "places": ["అపార్టుమెంట్", "పాత నేల గది", "నడవ చివర", "వెలుతురు లేని దారి"],
        "objects": ["పాత డైరీ", "గది అద్దం", "పాత ఫోటో", "వాయిస్ మెసేజ్"],
        "twists": [
            "ఆ డైరీలో రాసింది {char} చేతిరాత — కానీ {char} దాన్ని రాయలేదు.",
            "ఆ అద్దంలో ప్రతిబింబం ఒక్క క్షణం ఆలస్యంగా కదిలింది.",
            "ఆ వాయిస్ మెసేజ్ — {char} గొంతు. కానీ {char} ఆ మాటలు ఎప్పుడూ అనలేదు.",
        ],
    },
    "strange_event": {
        "chars": ["నాగేశ్వర్", "పద్మ", "చంద్ర", "భాస్కర్"],
        "places": ["చిన్న అడవి", "పాత దారి", "వంతెన దగ్గర", "రైలు పట్టాల దగ్గర"],
        "objects": ["పాత బైక్", "ఆగిపోయిన గడియారం", "తడి అడుగుల ముద్రలు", "పాప చెప్పు"],
        "twists": [
            "ఆ గడియారం — {char} చనిపోయిన రోజు ఆగిపోయింది. ఈ రోజు మళ్ళీ నడుస్తోంది.",
            "ఆ అడుగుల ముద్రలు నీళ్ళలో నుండి బయటకు వచ్చాయి. లోపలికి వెళ్ళలేదు.",
            "ఆ చెప్పు — {char} పాపది. పాప ఇంట్లో ఉంది. చెప్పు ఇక్కడ ఉంది.",
        ],
    },
    "soft_horror": {
        "chars": ["రమేశ్", "నళిని", "దినేశ్", "కావ్య"],
        "places": ["పాత అపార్టుమెంట్", "అర్ధరాత్రి నడవ", "పై అంతస్తు", "నేల గది"],
        "objects": ["పాత రేడియో", "మైనపు వత్తి", "గోకిన గీతలు", "చేతి ముద్ర"],
        "twists": [
            "ఆ గోకిన గీతలు — లోపల నుండి చేశారు.",
            "ఆ చేతి ముద్ర — పైకప్పు మీద ఉంది. నిలబడి చేయలేరు.",
            "ఆ రేడియోకు ప్లగ్ పెట్టలేదు. కానీ ఆ పాట వినిపిస్తోంది.",
        ],
    },
    "crime_no_violence": {
        "chars": ["అభిషేక్", "ప్రియ", "రాహుల్", "నీతూ"],
        "places": ["కార్యాలయం", "బ్యాంకు", "న్యాయస్థానం", "పోలీసు స్టేషన్"],
        "objects": ["నిఘా దృశ్యం", "బ్యాంక్ వివరాలు", "ఉత్తరం", "రసీదు"],
        "twists": [
            "ఆ నిఘా దృశ్యంలో నేరం చేసిన వ్యక్తి — {char} తండ్రి.",
            "ఆ బ్యాంక్ ఖాతా — {char} పేరు మీద ఉంది. {char} తెరవలేదు.",
            "ఆ రసీదు తేదీ — నేరం జరిగిన రోజు. {char} సంతకం ఉంది. కానీ {char} అప్పుడు ఊళ్ళో లేడు.",
        ],
    },
    "emotional_suspense": {
        "chars": ["శ్యామ్", "గీత", "కార్తీక్", "మాలతి"],
        "places": ["ఆసుపత్రి", "పాత ఇల్లు", "రైలు స్టేషన్", "పాత చెరువు గట్టు"],
        "objects": ["మూసి పెట్టిన ఉత్తరం", "పాత చీర", "విరిగిన గాజు", "పాప గీచిన బొమ్మ"],
        "twists": [
            "ఆ బొమ్మలో ఇల్లు — {char} పుట్టిన ఇల్లు. పాప దాన్ని ఎప్పుడూ చూడలేదు.",
            "ఆ ఉత్తరం — అమ్మ రాసింది. ఇరవై సంవత్సరాల ముందు. {char} కి.",
            "ఆ గాజు — {char} అమ్మది. అమ్మ చనిపోయినప్పుడు వేసి పంపారు. కానీ అమ్మ బతికి ఉంది.",
        ],
    },
    "karma_justice": {
        "chars": ["వెంకటేష్", "సరళ", "గోపాల్", "రేఖ"],
        "places": ["పాత కర్మాగారం", "న్యాయస్థానం", "ఊరు", "బస్సు"],
        "objects": ["పాత ఫైలు", "చిరిగిన కాగితం", "రికార్డు", "సాక్షి ఉత్తరం"],
        "twists": [
            "ఆ రికార్డులో గొంతు — న్యాయమూర్తి గొంతు.",
            "ఆ సాక్షి ఉత్తరంపై సంతకం — {char}ని నష్టపరచాలని చూసిన వ్యక్తిది.",
            "ఆ కాగితం చించిన వ్యక్తి — {char} తండ్రి. తన కొడుకుని కాపాడటానికి.",
        ],
    },
    "poor_vs_rich": {
        "chars": ["రంగారావు", "సుమిత్ర", "నాగభూషణ్", "జ్యోతి"],
        "places": ["పెద్ద బంగళా", "కర్మాగారం", "న్యాయస్థానం", "గ్రామ సరిహద్దు"],
        "objects": ["భూ పత్రం", "పాత ఫోటో", "రసీదు", "హక్కు పత్రం"],
        "twists": [
            "ఆ భూ పత్రంపై సంతకం — {char} తాతది. డెబ్బై సంవత్సరాల ముందు. అది అసలైనది.",
            "ఆ కర్మాగారం — {char} తాత కట్టించాడు. లోపల పాత రాయి మీద పేరు ఉంది.",
            "ఆ రసీదు — సేఠ్ ఇచ్చింది. మొత్తం వేరే. {char} దగ్గర అసలైనది ఉంది.",
        ],
    },
}

_DEFAULT_CATEGORY = "midnight_mystery"
_LOCATION_HINTS = [
    "ఇల్లు", "గది", "చెరువు", "బావి", "స్టేషన్", "దారి", "ఆసుపత్రి",
    "అలమర", "అద్దం", "వంతెన", "న్యాయస్థానం", "కార్యాలయం",
]
_CLUE_HINTS = [
    "ఉత్తరం", "ఫోటో", "తాళం", "డైరీ", "బొమ్మ", "రికార్డింగ్",
    "గాజు", "రసీదు", "పెట్టె", "చెవి", "గడియారం", "ముద్ర",
]
_CATEGORY_MOODS: dict[str, tuple[str, str, str]] = {
    "midnight_mystery": (
        "ఆ రాత్రి చిన్న శబ్దం కూడా పెద్ద హెచ్చరికలా అనిపించింది.",
        "కానీ — ఆ చిన్న సూచనే అసలు తలుపు తెరిచింది.",
        "ఆ నిజం బయటికి వచ్చిన తర్వాత ఆ తలుపు మళ్లీ ఎవరూ తట్టలేదు.",
    ),
    "village_mystery": (
        "ఆ ఊరి నిశ్శబ్దం వెనక చాలా కాలంగా దాచిన మాట ఉంది.",
        "కానీ — ఆ జాడ మట్టిలో కాదు, మనుషుల జ్ఞాపకాల్లో ఉంది.",
        "ఆ రహస్యం బయటపడిన రాత్రి నుంచి ఆ చోటు గురించి ఎవరూ సరదాగా మాట్లాడలేదు.",
    ),
    "family_suspense": (
        "ఆ ఇంట్లో దాచింది వస్తువు కాదు, ఒక జీవితాన్ని మార్చే మాట.",
        "కానీ — ఆ జ్ఞాపకాన్ని కాపాడటానికి వాళ్లు నిజాన్నే బంధించారు.",
        "ఆ నిజం తెలిసిన తర్వాత కుటుంబ ఫోటోలు కూడా అలాగే కనిపించలేదు.",
    ),
    "psychological_twist": (
        "చూసింది ఒక్కటే అయినా, అర్థమవుతున్న నిజం వేరేలా ఉంది.",
        "కానీ — ఆ సందేహం బయట ప్రపంచం గురించి కాదు, తన గురించే.",
        "ఆ రాత్రి తర్వాత అతను అద్దంలో ముందుగా తన కళ్లనే చూశాడు.",
    ),
    "strange_event": (
        "ఏం జరిగిందో అర్థం కాలేదు. కానీ అది కేవలం యాదృచ్ఛికం కాదు.",
        "కానీ — ఆ జాడకు కారణం దొరికినప్పుడు ప్రశ్నలు ఇంకా పెరిగాయి.",
        "ఆ సంఘటనకి సాక్ష్యంగా మిగిలింది ఒక వస్తువే. అదే చివరి జవాబు అయింది.",
    ),
    "soft_horror": (
        "ఆ గాలి చల్లదనం కంటే, అక్కడి నిశ్శబ్దమే భయపెట్టింది.",
        "కానీ — భయానికి రూపం ఇచ్చింది ఆ ఒక్క చిన్న సూచనే.",
        "ఆ రాత్రి తర్వాత చీకటి కంటే ఆ గుర్తే ఎక్కువగా గుర్తొచ్చింది.",
    ),
    "crime_no_violence": (
        "కాగితం మీద ఉన్న నిజం, మనిషి ముఖం మీద ఉన్న నిజానికి సరిపోలలేదు.",
        "కానీ — ఆ చిన్న తేడానే కేసు మొత్తం తలకిందులు చేసింది.",
        "ఆ సాక్ష్యం బయటపడిన తర్వాత వాళ్లు మాట్లాడింది చట్టం గురించి కాదు, మోసం గురించి.",
    ),
    "emotional_suspense": (
        "ఆ జ్ఞాపకం మొదట ఓదార్పులా అనిపించింది. తర్వాత అదే గాయం అయింది.",
        "కానీ — ఆ వస్తువు వెనక ఉన్న నిజం ప్రేమకన్నా భయంకరంగా ఉంది.",
        "ఆ మాట విన్న తర్వాత శ్యామ్ పాత జ్ఞాపకాలను కూడా కొత్తగా అనుమానించాడు.",
    ),
    "karma_justice": (
        "ఏళ్లుగా మునిగిపోయిన అన్యాయం, ఒక్క చిన్న ఆధారంతో మళ్లీ పైకి వచ్చింది.",
        "కానీ — దాచిన నిజం తిరిగి వచ్చినప్పుడు బాధపడింది తప్పు చేసినవాడే.",
        "ఆ రోజుకు తర్వాత వాళ్లు దాన్ని అదృష్టం అనలేదు. ఆలస్యమైన న్యాయం అన్నారు.",
    ),
    "poor_vs_rich": (
        "చిన్నదిగా కనిపించిన వస్తువు వెనక పెద్ద జీవిత కథ దాగి ఉంది.",
        "కానీ — దాన్ని చదివిన క్షణంలో గౌరవం ఎవరిదో తేలిపోయింది.",
        "ఆ నిజం బయటపడిన తర్వాత ధనం గురించి మాట్లాడిన వాళ్లే తల వంచారు.",
    ),
}


def _pick(lst: list[str]) -> str:
    return random.choice(lst)


def _fill_twist(twist_template: str, char: str) -> str:
    return twist_template.replace("{char}", char)


def _normalize_sentence(text: str) -> str:
    text = apply_telugu_replacements(text)
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace(" కి ", "‌కి ").replace(" లో ", "లో ")
    if text and text[-1] not in ".?!":
        text += "."
    return text


def _normalize_hook(text: str) -> str:
    hook = _normalize_sentence(text)
    hook = hook.replace("వాయిస్ memo", "వాయిస్ మెమో").replace("voice memo", "వాయిస్ మెమో")
    hook = hook.replace("3 ", "మూడు ")
    return hook


def _extract_named_character(text: str, candidates: list[str]) -> str | None:
    for name in candidates:
        if name in text:
            return name
    return None


def _extract_location(text: str, fallbacks: list[str]) -> str:
    for hint in _LOCATION_HINTS + fallbacks:
        if hint in text:
            return hint
    return _pick(fallbacks)


def _extract_clue(text: str, fallbacks: list[str]) -> str:
    for hint in _CLUE_HINTS:
        if hint in text:
            return hint
    for fallback in fallbacks:
        if fallback in text:
            return fallback
    return _pick(fallbacks)


def _short_phrase(text: str) -> str:
    phrase = re.sub(r"[\"“”]", "", apply_telugu_replacements(text)).strip()
    phrase = re.sub(r"\s+", " ", phrase)
    return phrase.rstrip(".!? ")


def _combine_paragraphs(paragraphs: list[str]) -> str:
    cleaned = [p.strip() for p in paragraphs if p.strip()]
    return "\n\n".join(cleaned)


def _word_count(text: str) -> int:
    return len(text.split())


def _fit_story_length(paragraphs: list[str], category_key: str) -> list[str]:
    text = _combine_paragraphs(paragraphs)
    count = _word_count(text)
    mood_line, escalation_line, closing_line = _CATEGORY_MOODS.get(category_key, _CATEGORY_MOODS[_DEFAULT_CATEGORY])

    if count < 110:
        paragraphs.insert(2, mood_line)
        text = _combine_paragraphs(paragraphs)
        count = _word_count(text)
    if count < 120:
        paragraphs.insert(-1, escalation_line)
        text = _combine_paragraphs(paragraphs)
        count = _word_count(text)
    if count > 165:
        paragraphs = [p.replace("చిన్న ", "").replace("పాత ", "", 1) for p in paragraphs]
    if _word_count(_combine_paragraphs(paragraphs)) > 175:
        paragraphs = paragraphs[:]
        paragraphs[2] = paragraphs[2].split(" కానీ ", 1)[0].strip() + "."
    if _word_count(_combine_paragraphs(paragraphs)) < 120:
        paragraphs.append(closing_line)
    return paragraphs


def _build_story_from_blueprint(
    blueprint: StoryBlueprint,
    category_key: str,
) -> str:
    hook = _normalize_hook(blueprint.hook)
    premise = _short_phrase(blueprint.setup)
    twist = _short_phrase(blueprint.reveal)
    mood_line, escalation_line, closing_line = _CATEGORY_MOODS.get(category_key, _CATEGORY_MOODS[_DEFAULT_CATEGORY])
    char = blueprint.protagonist_name
    location = blueprint.locations[0] if blueprint.locations else "పాత ఇల్లు"
    clue = blueprint.primary_clue
    device = blueprint.primary_story_device
    pov_prefix = "నాకు" if blueprint.point_of_view == "first_person" else f"{char}‌కి"
    actor = "నేను" if blueprint.point_of_view == "first_person" else char

    para1 = hook
    para2 = (
        f"{pov_prefix} మొదట అది ఒక చిన్న అనుమానం మాత్రమే. కానీ {premise} "
        f"అని అనిపించిన క్షణం నుంచి అతను వెనక్కి తగ్గలేదు."
    )
    para3 = (
        f"{location} దగ్గర కనిపించిన {device}తో పాటు {clue}నే మొదటి నిజమైన జాడ. {actor} దాన్ని మళ్లీ చూసిన కొద్దీ, "
        f"దాచింది ఒక వస్తువు కాదు, ఇంట్లో ఎవరూ పలకకూడదనుకున్న నిజమని అతనికి స్పష్టంగా అనిపించింది."
    )
    para4 = (
        f"{mood_line} {escalation_line} {blueprint.escalation} {twist}."
    )
    para5 = (
        f"{blueprint.final_twist} {blueprint.final_line} {device} గురించిన ప్రశ్నకు అదే చివరి జవాబైంది. {closing_line}"
    )

    paragraphs = _fit_story_length([para1, para2, para3, para4, para5], category_key)
    return _combine_paragraphs(paragraphs)


def _build_ai_script_prompt(blueprint: StoryBlueprint, category_key: str) -> str:
    supporting = ", ".join(blueprint.supporting_clues) or "None"
    locations = ", ".join(blueprint.locations) or "single locked location"
    forbidden = ", ".join(blueprint.forbidden_elements) or "new characters, vague twists"
    return f"""You are the lead Telugu scriptwriter for Midnight Telugu, a YouTube Shorts channel for mystery, suspense, and soft-horror stories.

Write ONE production-ready Telugu voice-over narration script from this locked blueprint.

Hard requirements:
- Output only the final Telugu narration text. No headings, notes, markdown, translations, or explanations.
- Natural spoken Telugu, mature Indian narrator tone. It should sound like a human Telugu narrator, not a plot summary.
- 45-60 seconds when narrated, around 115-145 Telugu words.
- Viral hook in the first 2-3 seconds: one strange concrete image, not generic suspense.
- One protagonist only; do not change the protagonist name.
- No POV confusion.
- No unnecessary English words.
- No moral lecture, no generic AI ending, no engagement question.
- The final twist must be specific, clear, and pay off an earlier clue.
- End with a strong final line.
- Stay family-safe: no gore, no graphic violence.
- Use 5 short breath-friendly paragraphs.
- Build suspense through concrete details: rain, empty platform, stopped clock, old bench, flickering light, quiet tracks.
- The reveal must explicitly connect the old man, the old photo, the stopped clock, and the final train.
- The final line must be cinematic and chilling, not explanatory.
- Avoid these weak phrases: "ఏదో రహస్యం", "అర్థం కాలేదు", "అంచనా వేయలేనిది", "జీవితం మార్చింది", "ఆసక్తి చూపించాడు".
- Avoid awkward Telugu such as "అవినీతి అనుభవాలు", "సర్దుబాటు చేసుకోవడం", "పుట్టిమనసులో".
- Do not say the protagonist is curious; show what he sees, hears, and does.
- Paragraph 1: cold-open hook at 12:17.
- Paragraph 2: context and atmosphere: rain, empty platform, phone dead, stopped clock.
- Paragraph 3: old man's warning becomes personal; one replay clue appears.
- Paragraph 4: station master/photo/register reveal.
- Paragraph 5: final twist with the empty bench/photo shadow and the stopped clock.

Locked blueprint:
Title: {blueprint.title}
Category: {category_key}
Protagonist: {blueprint.protagonist_name}
Role: {blueprint.protagonist_role}
POV: {blueprint.point_of_view}
Hook: {blueprint.hook}
Central question: {blueprint.central_question}
Primary story device: {blueprint.primary_story_device}
Primary clue: {blueprint.primary_clue}
Supporting clues: {supporting}
Setup: {blueprint.setup}
Escalation: {blueprint.escalation}
Reveal: {blueprint.reveal}
Final twist: {blueprint.final_twist}
Required final line idea: {blueprint.final_line}
Locations: {locations}
Forbidden elements: {forbidden}
"""


def generate_script(source: StoryBlueprint | StoryIdea, provider: str | None = None) -> StoryScript:
    """Generate a cinematic Telugu script from an approved StoryBlueprint."""
    provider = provider or DEFAULT_TEXT_PROVIDER

    if isinstance(source, StoryIdea):
        blueprint = build_blueprint(source)
    else:
        blueprint = source

    validation = validate_blueprint(blueprint)
    if not validation.passed:
        raise ValueError(
            f"Blueprint failed validation: {', '.join(validation.hard_failures)}"
        )

    category_key = blueprint.category if isinstance(blueprint.category, str) else blueprint.category.value
    if provider == "mock":
        full_script = _build_story_from_blueprint(
            blueprint=blueprint,
            category_key=category_key,
        )
    else:
        from workers.providers import get_text_provider

        ai_provider = get_text_provider(provider)
        full_script = ai_provider.generate_text(_build_ai_script_prompt(blueprint, category_key)).strip()
        if not full_script:
            raise RuntimeError(f"Text provider '{provider}' returned an empty script.")
        full_script = apply_telugu_replacements(full_script)

    youtube_title = f"{blueprint.title} | Midnight Telugu | Telugu Short Story"
    youtube_desc = (
        f"{_normalize_hook(blueprint.hook)}\n\n"
        f"Category: {category_key}\n\n"
        "Midnight Telugu — మిస్టరీ, హారర్, సస్పెన్స్ Telugu Short Stories.\n"
        "Subscribe చేయండి మరిన్ని కథలకు.\n\n"
        "#MidnightTelugu #TeluguShorts #TeluguMystery #TeluguStories"
    )

    # ~2.5 words/second for Telugu narration
    word_count = len(full_script.split())
    duration = max(45, min(65, int(word_count / 2.5)))

    return StoryScript(
        id=f"script_{uuid.uuid4().hex[:8]}",
        idea_id=blueprint.idea_id,
        blueprint_id=blueprint.id,
        title=blueprint.title,
        category=blueprint.category,
        hook_line=_normalize_hook(blueprint.hook),
        full_script_telugu=full_script,
        estimated_duration_seconds=duration,
        youtube_title=youtube_title,
        youtube_description=youtube_desc,
        youtube_hashtags=[
            "MidnightTelugu", "TeluguShorts", "TeluguMystery",
            "TeluguStories", "TeluguSuspense",
        ],
    )
