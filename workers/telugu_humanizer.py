"""Telugu humanizer — converts generated scripts to natural spoken Telugu."""

from __future__ import annotations

import random
import re
import uuid

from workers.config import DEFAULT_TEXT_PROVIDER
from workers.models import HumanizedScript, StoryScript

# Lexical substitutions: textbook → natural spoken Telugu
_WORD_SUBS: list[tuple[str, str]] = [
    ("అతను చెప్పాడు", "అతను అన్నాడు"),
    ("ఆమె చెప్పింది", "ఆమె అంది"),
    ("వారు చెప్పారు", "వాళ్ళు అన్నారు"),
    ("వారు", "వాళ్ళు"),
    ("తాను వెళ్ళాడు", "వెళ్ళాడు"),
    ("ఆయన", "అతను"),  # unless religious context
    ("నిష్క్రమించారు", "వెళ్ళిపోయారు"),
    ("ఆగమించారు", "వచ్చారు"),
    ("ఈ విషయం", "ఈ సంగతి"),
    ("పరిస్థితి", "సంగతి"),
    ("ప్రజలు", "మనుషులు"),
    ("సమాచారం", "విషయం"),
    ("అందువల్ల", "అందుకే"),
    ("వాస్తవం", "నిజం"),
    ("ఆశ్చర్యపడ్డాడు", "నోరు తెరుచుకుపోయింది"),
    ("భయపడ్డాడు", "గుండె ఆగిపోయింది"),
    ("ప్రయత్నించాడు", "చూసాడు"),
    ("నిర్ణయించాడు", "అనుకున్నాడు"),
    ("అనుభవించాడు", "అనిపించింది"),
    ("అతను అనుకున్నాడు", "అతనికి అనిపించింది"),
    ("సంఘటన", "విషయం"),
    ("పరిశీలించాడు", "చూసాడు"),
    ("నిశ్శబ్దంగా", "మెల్లగా"),
]

# AI-pattern endings to remove
_AI_ENDINGS: list[str] = [
    "అప్పుడు అతనికి నిజం తెలిసింది",
    "నీతి ఏమిటంటే",
    "జీవితం మనకు చెప్తుంది",
    "ఇది మనకు నేర్పిస్తుంది",
    "ఈ కథ నుండి నేర్చుకున్నది",
    "జీవితంలో నేర్చుకున్నది",
]

# Suspense transition phrases (add natural pacing)
_SUSPENSE_TRANSITIONS = [
    "కానీ —",
    "అప్పుడు —",
    "అకస్మాత్తుగా —",
    "ఆ క్షణంలో —",
    "ఎవరూ అనుకోలేదు —",
]

# Spoken rhythm: em-dash before reveals
_REVEAL_TRIGGERS = ["నిజం", "రహస్యం", "తెలిసింది", "అర్థమైంది", "బయటపడింది", "కనుగొన్నాడు"]


def _apply_word_subs(text: str) -> str:
    for old, new in _WORD_SUBS:
        text = text.replace(old, new)
    return text


def _remove_ai_endings(text: str) -> str:
    for pattern in _AI_ENDINGS:
        if pattern in text:
            text = text.replace(pattern, "")
    return text


def _add_pacing(text: str) -> str:
    """
    - Split long lines at natural pause points
    - Add em-dash before reveals
    - Avoid double em-dashes
    """
    lines = text.split("\n")
    result = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            result.append("")
            continue

        # Add em-dash before reveal trigger words if not already present
        for trigger in _REVEAL_TRIGGERS:
            pattern = rf"(?<!—\s)({trigger})"
            replacement = r"— \1"
            stripped = re.sub(pattern, replacement, stripped, count=1)

        # Split very long lines (>90 chars) at a comma or space near midpoint
        if len(stripped) > 90 and stripped.count("—") < 2:
            mid = len(stripped) // 2
            # Try to split at a comma first
            split_pos = stripped.rfind(",", 0, mid + 20)
            if split_pos == -1:
                split_pos = stripped.rfind(" ", 0, mid + 15)
            if split_pos > 20:
                stripped = stripped[:split_pos + 1] + "\n" + stripped[split_pos + 1:].lstrip()

        result.append(stripped)

    return "\n".join(result)


def _shorten_over_explanation(text: str) -> str:
    """Remove redundant explanatory phrases that weaken suspense."""
    redundant = [
        "అంటే అతను అర్థం చేసుకున్నాడు",
        "అంటే ఆమె అర్థం చేసుకుంది",
        "దీనివల్ల అతనికి తెలిసింది",
        "ఇది చాలా ముఖ్యమైన విషయం",
        "మీకు అర్థమైందా అంటే",
        "సరిగ్గా చెప్పాలంటే",
    ]
    for phrase in redundant:
        text = text.replace(phrase, "")
    return text


def _ensure_voiceover_rhythm(text: str) -> str:
    """
    Ensure the text has breath pauses — no paragraph longer than 3 sentences.
    """
    paragraphs = text.split("\n\n")
    result = []
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        # Count sentence endings
        sentences = re.split(r"[।.!?]", para)
        sentences = [s.strip() for s in sentences if s.strip()]
        if len(sentences) > 3:
            # Break into sub-paragraphs of max 2 sentences
            chunks = [sentences[i:i + 2] for i in range(0, len(sentences), 2)]
            result.append("\n\n".join(". ".join(c) + "." for c in chunks if c))
        else:
            result.append(para)
    return "\n\n".join(result)


_CLOSING_LINES = [
    "మీకు ఇలాంటి అనుభవం ఉందా? Comment లో చెప్పండి.",
    "ఇది నిజంగా జరిగింది అని మీరు నమ్ముతారా?",
    "ఈ కథలో నిజమేమిటో మీరే చెప్పండి.",
    "అలాంటప్పుడు మీరు ఏం చేసేవారు?",
    "మీకు ఏమనిపించింది — వినాలని ఉంది.",
]


def humanize_script(script: StoryScript, provider: str | None = None) -> HumanizedScript:
    """Apply full naturalness pass to a generated Telugu script."""
    provider = provider or DEFAULT_TEXT_PROVIDER

    if provider != "mock":
        import warnings
        warnings.warn(
            f"Provider '{provider}' not implemented in v1. Falling back to mock.",
            stacklevel=2,
        )

    text = script.full_script_telugu

    # Pipeline
    text = _apply_word_subs(text)
    text = _remove_ai_endings(text)
    text = _shorten_over_explanation(text)
    text = _add_pacing(text)
    text = _ensure_voiceover_rhythm(text)

    # Ensure closing is conversational
    has_closing = any(m in text for m in ["Comment", "Subscribe", "అనుభవం", "చెప్పండి", "Follow"])
    if not has_closing:
        text = text.rstrip() + f"\n\n{random.choice(_CLOSING_LINES)}"

    # Clean up extra blank lines
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    notes = (
        "Word-level substitutions applied (textbook→spoken). "
        "AI-pattern endings removed. "
        "Long sentences split for voiceover pacing. "
        "Em-dash reveal markers added. "
        "Neutral Andhra + Telangana mix maintained."
    )

    return HumanizedScript(
        id=f"humanized_{uuid.uuid4().hex[:8]}",
        script_id=script.id,
        title=script.title,
        category=script.category,
        hook_line=script.hook_line,
        full_script_telugu=text,
        humanization_notes=notes,
        estimated_duration_seconds=script.estimated_duration_seconds,
    )
