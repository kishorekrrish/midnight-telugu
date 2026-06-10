"""Telugu humanizer — makes AI-generated scripts sound like natural storytelling."""

from __future__ import annotations

import uuid

from workers.config import DEFAULT_TEXT_PROVIDER
from workers.models import HumanizedScript, StoryScript

# Substitutions: robotic / textbook Telugu -> natural conversational Telugu
_REPLACEMENTS: list[tuple[str, str]] = [
    ("అతను చెప్పాడు", "అతను అన్నాడు"),
    ("ఆమె చెప్పింది", "ఆమె అంది"),
    ("వారు చెప్పారు", "వాళ్ళు అన్నారు"),
    ("ఈ విషయం", "ఈ సంగతి"),
    ("పరిస్థితి", "సంగతి"),
    ("ప్రజలు", "మనుషులు"),
    ("సమాచారం", "విషయం"),
    ("అందువల్ల", "అందుకే"),
    ("కానీ", "కానీ"),
    ("మాత్రమే", "మాత్రమే"),
    ("వాస్తవం", "నిజం"),
    ("ఆశ్చర్యపడ్డాడు", "నోరు తెరుచుకుపోయింది"),
    ("భయపడ్డాడు", "గుండె ఆగిపోయింది"),
    ("ప్రయత్నించాడు", "చూసాడు"),
]

_CONVERSATIONAL_OPENERS = [
    "చూడండి —",
    "వినండి —",
    "అర్థమైందా? —",
    "ఒక్క నిమిషం ఆగండి —",
]

_CLOSING_LINES = [
    "మీకు ఇలాంటి అనుభవం ఉందా? Comment లో చెప్పండి.",
    "ఇది నిజంగా జరిగింది అని మీరు నమ్ముతారా?",
    "ఇలాంటి కథలు మరిన్ని చూడాలంటే Subscribe చేయండి.",
    "ఈ కథ మీకు ఎలా అనిపించింది — comment చేయండి.",
]


def _apply_replacements(text: str) -> str:
    for old, new in _REPLACEMENTS:
        text = text.replace(old, new)
    return text


def _add_natural_rhythm(text: str) -> str:
    """Add pauses, em-dashes and natural Telugu spoken rhythm markers."""
    lines = text.split("\n")
    result = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            result.append("")
            continue
        # Shorten very long sentences with a pause marker
        if len(stripped) > 80 and "—" not in stripped:
            mid = len(stripped) // 2
            # Find nearest space to split
            split_pos = stripped.rfind(" ", 0, mid)
            if split_pos > 0:
                stripped = stripped[:split_pos] + " —\n" + stripped[split_pos + 1:]
        result.append(stripped)
    return "\n".join(result)


def humanize_script(script: StoryScript, provider: str | None = None) -> HumanizedScript:
    """Apply naturalness improvements to a generated Telugu script."""
    provider = provider or DEFAULT_TEXT_PROVIDER

    if provider != "mock":
        import warnings
        warnings.warn(
            f"Provider '{provider}' not implemented in v1. Falling back to mock.",
            stacklevel=2,
        )

    humanized_text = _apply_replacements(script.full_script_telugu)
    humanized_text = _add_natural_rhythm(humanized_text)

    # Ensure closing line is conversational
    import random
    closing = random.choice(_CLOSING_LINES)
    if not any(marker in humanized_text for marker in ["Comment", "Subscribe", "అనుభవం"]):
        humanized_text = humanized_text.rstrip() + f"\n\n{closing}"

    notes = (
        "Applied lexical substitutions for natural spoken Telugu. "
        "Added rhythm pauses. "
        "Ensured closing line is conversational. "
        "Neutral Andhra + Telangana mix preserved."
    )

    return HumanizedScript(
        id=f"humanized_{uuid.uuid4().hex[:8]}",
        script_id=script.id,
        title=script.title,
        category=script.category,
        hook_line=script.hook_line,
        full_script_telugu=humanized_text,
        humanization_notes=notes,
        estimated_duration_seconds=script.estimated_duration_seconds,
    )
