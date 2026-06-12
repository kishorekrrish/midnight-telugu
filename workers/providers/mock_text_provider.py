"""Mock text provider — deterministic Script Director rewrite for tests."""

from __future__ import annotations

import re

from workers.providers.base import BaseTextProvider

_DEFAULT_HOOK = "ఆ రాత్రి తలుపు లోపల నుండి తెరుచుకుంది."
_FIRST_PERSON_MARKERS = ("నేను", "నాకు", "నా ", "నన్ను", "నాతో", "నాలో")
_KNOWN_NAMES = ("రవి", "అర్జున్", "కిరణ్", "సుమ", "లక్ష్మి", "మహేష్", "అనిత", "వెంకట్")
_CLUE_OPTIONS = ("ఉత్తరం", "తాళం", "డైరీ", "అద్దం", "ఫోటో", "ముద్ర")


def _extract_section(prompt: str, heading: str) -> str:
    pattern = rf"## {re.escape(heading)}\s*\n\n(.*?)(?:\n## |\Z)"
    match = re.search(pattern, prompt, re.DOTALL)
    return match.group(1).strip() if match else ""


def _extract_script_from_prompt(prompt: str) -> str:
    backtick_match = re.search(r"```(?:telugu)?\s*\n(.*?)```", prompt, re.DOTALL | re.IGNORECASE)
    if backtick_match:
        extracted = backtick_match.group(1).strip()
        if extracted:
            return extracted
    return _extract_section(prompt, "Current Telugu Script")


def _normalize_hook(hook_line: str) -> str:
    hook = " ".join(hook_line.split()).strip()
    hook = hook.replace("...", ".").replace("..", ".")
    if not hook:
        return _DEFAULT_HOOK
    if hook[-1] not in ".?!":
        hook += "."
    return hook


def _extract_name(text: str, first_person: bool) -> str:
    if first_person:
        return "నేను"
    for name in _KNOWN_NAMES:
        if name in text:
            return name
    words = re.findall(r"[ఀ-౿]{3,8}", text)
    for word in words:
        if word not in {"అతను", "ఆమె", "ఇంటి", "తలుపు", "రాత్రి", "గది", "ఉత్తరం"}:
            return word
    return "రవి"


def _extract_clue(text: str) -> str:
    for clue in _CLUE_OPTIONS:
        if clue in text:
            return clue
    return "ఉత్తరం"


def _first_person_story(hook: str, clue: str) -> str:
    return (
        f"{hook}\n\n"
        f"ఆ శబ్దం విన్న క్షణంలోనే నేను మంచం మీద నుంచి లేచాను. ముందు గదిలో వెలిగిన చిన్న దీపం మాత్రమే ఉంది. "
        f"తలుపు దగ్గరకు వెళ్లినప్పుడు నేల మీద {clue} పక్కన ఒక మడిచిన కాగితం కనిపించింది. ఆ కాగితంపై నా ఇంటి పాత చిరునామా, "
        "ఈ రోజే రాసిన తేదీ, నా చేతిరాతలా కనిపించిన అక్షరాలు ఉన్నాయి.\n\n"
        f"నేను ఆ కాగితం తెరిచి చదివాను. అందులో ఒకే వాక్యం ఉంది: ఆ తలుపు పూర్తిగా తెరవకముందే అద్దం వెనుక చూడు. "
        f"అక్కడే నిజం ఉంటుంది. ఆ మాట చదివిన వెంటనే తలుపు మళ్లీ మెల్లగా కదిలింది. గది అంతా నిశ్శబ్దంగా ఉన్నా, "
        f"{clue} మాత్రం కాసేపటి క్రితమే ఎవరో పట్టినట్టుగా వెచ్చగా అనిపించింది.\n\n"
        "నేను అద్దం వెనుక భాగాన్ని తట్టాను. పలుచని పలక కదిలి చిన్న ఖాళీ తెరుచుకుంది. లోపల మరో కాగితం, పాత తాళం, "
        "మరియు నా పేరు ఉన్న లిఫాఫా ఉన్నాయి. రెండో కాగితంలో చిన్నప్పుడు ఈ గది తాళం వేసింది నేనేనని, కానీ ఆ జ్ఞాపకాన్ని భయంతో దాచేశానని రాసి ఉంది.\n\n"
        f"అప్పుడు నాకు అర్థమైంది. {hook[:-1]} అని నేను చిన్నప్పుడు అరిచిన మాటనే ఈ రాత్రి మళ్లీ విన్నాను. "
        f"ఆ తలుపు లోపల నుంచి తెరుచుకున్నది ఎవరో కాదు; నా చేతే దాచిన నిజాన్ని గుర్తు చేయడానికి నేను వదిలిన {clue}."
    )


def _third_person_story(hook: str, protagonist: str, clue: str) -> str:
    return (
        f"{hook}\n\n"
        f"{protagonist} ఆ ఇంట్లో ఒంటరిగా ఉన్న రాత్రి అదే మొదటిసారి కాదు. కానీ ఆ శబ్దం తర్వాత అతను నేరుగా ముందు గది తలుపు దగ్గరకు వెళ్లాడు. "
        f"తలుపు కింద నుంచి జారిన {clue} పక్కన మడిచిన కాగితం కనిపించింది. కాగితంపై ఇంటి పాత చిరునామా, ఈ రాత్రి తేదీ, "
        f"మరియు {protagonist} పేరే రాసి ఉన్నాయి.\n\n"
        f"{protagonist} కాగితం విప్పి చదివాడు. అందులో ఒకే మాట మళ్లీ మళ్లీ ఉంది: తలుపు తెరుచుకునే ముందు అద్దం వెనుక చూడు. "
        f"అతను ఆ గదిలో ఉన్న పాత అద్దాన్ని తిప్పి చూసినప్పుడు వెనుక భాగంలో చిన్న గీత కనిపించింది. అదే గీతను {clue} అంచుపై కూడా చూశాడు. "
        "అప్పుడు ఈ రెండూ ఒకే కథలో భాగాలని అతనికి అర్థమైంది.\n\n"
        f"అతను అద్దం వెనుక పలకను నెమ్మదిగా పైకి ఎత్తాడు. లోపల చిన్న సంచి, పాత తాళం, మరో కాగితం ఉన్నాయి. "
        f"రెండో కాగితంలో తన తండ్రి రాసిన నిజం ఉంది: ఈ గదిని తాళం వేసింది దొంగ కాదు, {protagonist} చిన్నప్పుడు చూసిన సంఘటనను కాపాడాలని ఆయన చేసిన నిర్ణయం. "
        f"ఆ రాత్రి తలుపు లోపల నుంచి తెరుచుకున్నది ఆ గదిలో దాక్కున్న మనిషి కోసం కాదు; {clue} చూపించిన నిజం బయటికి రావడానికి."
    )


class MockTextProvider(BaseTextProvider):
    """Deterministic mock text provider for testing without API keys."""

    def generate_text(self, prompt: str) -> str:
        script_text = _extract_script_from_prompt(prompt)
        hook_line = _extract_section(prompt, "Original Hook Line") or _DEFAULT_HOOK
        hook = _normalize_hook(hook_line)
        first_person = any(marker in hook for marker in _FIRST_PERSON_MARKERS)

        if first_person:
            clue = _extract_clue(script_text or hook)
            return _first_person_story(hook, clue).strip()

        protagonist = _extract_name(script_text or hook, first_person=False)
        clue = _extract_clue(script_text or hook)
        return _third_person_story(hook, protagonist, clue).strip()
