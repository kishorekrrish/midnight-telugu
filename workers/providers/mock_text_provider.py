"""Mock text provider — works without API keys, applies deterministic improvements."""

from __future__ import annotations

import re

from workers.providers.base import BaseTextProvider

# Fixed sensory beats for deterministic injection
_SENSORY_BEATS = [
    "గాలి ఆగింది.",
    "గుండె వేగంగా కొట్టుకుంది.",
    "అడుగుల చప్పుడు ఆగింది.",
    "నిశ్శబ్దం — భరించలేని నిశ్శబ్దం.",
    "చేతులు వణికాయి.",
    "శ్వాస తగ్గిపోయింది.",
]

_SENSORY_SIGNALS = [
    "గాలి", "గుండె", "అడుగు", "నిశ్శబ్దం",
    "వణికాయి", "శ్వాస", "చీకటి", "వెలుతురు",
]

_CINEMATIC_CLOSINGS = [
    "ఆ రాత్రి నుండి ఆ గది తాళం తెరవలేదు — ఎప్పుడూ.",
    "అప్పటి నుండి ఆ దారిలో ఎవరూ నడవలేదు.",
    "ఇప్పటికీ ఆ నిశ్శబ్దం అక్కడే ఉంది — సమాధానం చెప్పకుండా.",
    "ఆ రాత్రి జరిగింది ఏమిటో — ఇప్పటికీ తెలియదు.",
]

# Textbook → natural spoken Telugu
_WORD_SUBS: list[tuple[str, str]] = [
    ("అతను చెప్పాడు", "అతను అన్నాడు"),
    ("ఆమె చెప్పింది", "ఆమె అంది"),
    ("వారు చెప్పారు", "వాళ్ళు అన్నారు"),
    ("వారు", "వాళ్ళు"),
    ("నిష్క్రమించారు", "వెళ్ళిపోయారు"),
    ("ఆగమించారు", "వచ్చారు"),
    ("ఈ విషయం", "ఈ సంగతి"),
    ("ప్రజలు", "మనుషులు"),
    ("అందువల్ల", "అందుకే"),
    ("వాస్తవం", "నిజం"),
]


def _extract_script_from_prompt(prompt: str) -> str:
    """Extract the Telugu script text from a director prompt."""
    # Try triple-backtick block first
    backtick_match = re.search(r"```(?:telugu)?\s*\n(.*?)```", prompt, re.DOTALL | re.IGNORECASE)
    if backtick_match:
        extracted = backtick_match.group(1).strip()
        if extracted:
            return extracted

    # Try "Current script:" marker
    marker_match = re.search(r"Current script:\s*\n(.*?)(?:\n\n##|\Z)", prompt, re.DOTALL | re.IGNORECASE)
    if marker_match:
        extracted = marker_match.group(1).strip()
        if extracted:
            return extracted

    # Try "Telugu Script:" marker
    marker_match2 = re.search(r"Telugu [Ss]cript:\s*\n(.*?)(?:\n\n##|\Z)", prompt, re.DOTALL | re.IGNORECASE)
    if marker_match2:
        extracted = marker_match2.group(1).strip()
        if extracted:
            return extracted

    # Fall back: look for lines with Telugu Unicode characters
    lines = prompt.split("\n")
    telugu_lines = [
        ln for ln in lines
        if any("ఀ" <= ch <= "౿" for ch in ln)
    ]
    if telugu_lines:
        return "\n".join(telugu_lines).strip()

    return ""


class MockTextProvider(BaseTextProvider):
    """Deterministic mock text provider for testing without API keys."""

    def generate_text(self, prompt: str) -> str:
        """Extract script from prompt, apply improvements, return improved Telugu text."""
        from workers.telugu_quality import apply_telugu_replacements

        script_text = _extract_script_from_prompt(prompt)

        if not script_text:
            # Return a minimal valid Telugu script
            return (
                "అర్ధరాత్రి ఒంటి గంటకు ఆ ఇంట్లో వెలుతురు వచ్చింది.\n\n"
                "గాలి ఆగింది.\n\n"
                "తాళం వేసి ఉన్న గది లోపల నుండి అడుగుల చప్పుడు వినిపించింది.\n\n"
                "కానీ — ఆ ఇంట్లో ఎవరూ లేరు.\n\n"
                "ఇప్పటికీ ఆ నిశ్శబ్దం అక్కడే ఉంది — సమాధానం చెప్పకుండా."
            )

        # Apply Telugu replacements (English → Telugu)
        text = apply_telugu_replacements(script_text)

        # Apply word substitutions
        for old, new in _WORD_SUBS:
            text = text.replace(old, new)

        # Inject sensory beat if missing
        has_sensory = any(sig in text for sig in _SENSORY_SIGNALS)
        if not has_sensory:
            beat = _SENSORY_BEATS[hash(text) % len(_SENSORY_BEATS)]
            parts = text.rsplit("\n\n", 1)
            if len(parts) == 2:
                text = parts[0] + f"\n\n{beat}\n\n" + parts[1]
            else:
                text = text + f"\n\n{beat}"

        # Ensure cinematic closing line
        _closing_signals = [
            "తెరవలేదు", "ఎప్పుడూ", "ఇప్పటికీ అక్కడే", "exist అవ్వడం లేదు",
            "నా గొంతే", "నా పేరు", "సమాధానం", "తెలియదు",
        ]
        last_para = text.strip().split("\n\n")[-1] if "\n\n" in text else text[-100:]
        has_closing = any(sig in last_para for sig in _closing_signals)
        if not has_closing:
            closing = _CINEMATIC_CLOSINGS[hash(text) % len(_CINEMATIC_CLOSINGS)]
            text = text.rstrip() + f"\n\n{closing}"

        return text.strip()
