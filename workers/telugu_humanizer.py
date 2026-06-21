"""Telugu humanizer — converts generated scripts to natural spoken narration."""

from __future__ import annotations

import re
import uuid

from workers.config import DEFAULT_TEXT_PROVIDER
from workers.models import HumanizedScript, StoryScript
from workers.script_generator import BANNED_ENDINGS
from workers.telugu_quality import apply_telugu_replacements

# Textbook → natural spoken Telugu substitutions
_WORD_SUBS: list[tuple[str, str]] = [
    ("అతను చెప్పాడు", "అతను అన్నాడు"),
    ("ఆమె చెప్పింది", "ఆమె అంది"),
    ("వారు చెప్పారు", "వాళ్ళు అన్నారు"),
    ("వారు", "వాళ్ళు"),
    ("తాను వెళ్ళాడు", "వెళ్ళాడు"),
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

# Summary-to-spoken regex patterns (multiline)
_SUMMARY_TO_SPOKEN: list[tuple[str, str]] = [
    (r"ఒక కొడుకు\s+(\S+)", r"ఆ కొడుకు — \1"),
    (r"ఒక అమ్మాయి\s+(\S+)", r"ఆ అమ్మాయి — \1"),
    (r"ఒక వ్యక్తి\s+(\S+)", r"ఆ వ్యక్తి — \1"),
    (r"ఒక మనిషి\s+(\S+)", r"ఆ మనిషి — \1"),
    (r"^అప్పుడు\s+", ""),
]

# Phrases that weaken suspense
_OVER_EXPLANATIONS: list[str] = [
    "అంటే అతను అర్థం చేసుకున్నాడు",
    "అంటే ఆమె అర్థం చేసుకుంది",
    "దీనివల్ల అతనికి తెలిసింది",
    "ఇది చాలా ముఖ్యమైన విషయం",
    "మీకు అర్థమైందా అంటే",
    "సరిగ్గా చెప్పాలంటే",
]

# Sensory beats to inject when missing
_SENSORY_BEATS: list[str] = [
    "గాలి ఆగింది.",
    "గుండె వేగంగా కొట్టుకుంది.",
    "అడుగుల చప్పుడు ఆగింది.",
    "నిశ్శబ్దం — భరించలేని నిశ్శబ్దం.",
    "చేతులు వణికాయి.",
    "శ్వాస తగ్గిపోయింది.",
]

# Reveal trigger words — add em-dash pause before them
_REVEAL_TRIGGERS = [
    "నిజం", "రహస్యం", "తెలిసింది", "అర్థమైంది",
    "బయటపడింది", "కనుగొన్నాడు",
]


def _apply_word_subs(text: str) -> str:
    for old, new in _WORD_SUBS:
        text = text.replace(old, new)
    return text


def _convert_summary_to_spoken(text: str) -> str:
    for pattern, replacement in _SUMMARY_TO_SPOKEN:
        text = re.sub(pattern, replacement, text, flags=re.MULTILINE)
    return text


def _remove_over_explanations(text: str) -> str:
    for phrase in _OVER_EXPLANATIONS:
        text = text.replace(phrase, "")
    return text


def _remove_banned_endings(text: str) -> str:
    for pattern in BANNED_ENDINGS:
        if text.rstrip().endswith(pattern):
            text = text[: text.rstrip().rfind(pattern)].rstrip()
    return text


def _add_em_dash_pauses(text: str) -> str:
    for trigger in _REVEAL_TRIGGERS:
        text = re.sub(rf"(?<!—\s)(?<!—)({trigger})", r"— \1", text)
    return text


def _ensure_voiceover_beats(text: str) -> str:
    """Split paragraphs >3 sentences into 2-sentence breath chunks."""
    paragraphs = text.split("\n\n")
    result = []
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        sentences = re.split(r"(?<=[।.!?])\s+", para)
        sentences = [s.strip() for s in sentences if s.strip()]
        if len(sentences) > 3:
            chunks = [sentences[i : i + 2] for i in range(0, len(sentences), 2)]
            result.append("\n\n".join(" ".join(c) for c in chunks if c))
        else:
            result.append(para)
    return "\n\n".join(result)


def _inject_sensory_detail(text: str) -> str:
    """Inject a sensory beat before the last paragraph if none exist."""
    sensory_signals = [
        "గాలి", "గుండె", "అడుగు", "నిశ్శబ్దం",
        "వణికాయి", "శ్వాస", "చీకటి", "వెలుతురు",
    ]
    has_sensory = any(sig in text for sig in sensory_signals)
    if not has_sensory:
        beat = _SENSORY_BEATS[hash(text) % len(_SENSORY_BEATS)]
        parts = text.rsplit("\n\n", 1)
        if len(parts) == 2:
            text = parts[0] + f"\n\n{beat}\n\n" + parts[1]
    return text


def humanize_script(script: StoryScript, provider: str | None = None) -> HumanizedScript:
    """Apply full naturalness and pacing pass to a Telugu script."""
    provider = provider or DEFAULT_TEXT_PROVIDER

    text = script.full_script_telugu
    if provider != "mock":
        from workers.providers import get_text_provider

        prompt = f"""You are the Telugu humanization editor for Midnight Telugu.

Rewrite this Telugu Shorts narration to sound naturally spoken by a mature Indian Telugu male narrator.

Hard requirements:
- Output only the final Telugu narration text.
- Preserve the exact story, protagonist, clues, reveal, and final twist.
- Do not translate, summarize, add new characters, or change the ending.
- Remove unnecessary English words.
- Keep it around 45-60 seconds.
- Add suspenseful breathing rhythm with short paragraphs.
- No moral lecture, no engagement question.
- Keep concrete cinematic details and suspense beats.
- Replace flat summary language with moment-by-moment narration.
- Keep the hook sharp and the final line chilling.

Script:
```
{text}
```
"""
        text = get_text_provider(provider).generate_text(prompt).strip()
        if not text:
            raise RuntimeError(f"Text provider '{provider}' returned an empty humanized script.")

    text = apply_telugu_replacements(text)   # English → Telugu equivalents first
    text = _apply_word_subs(text)
    text = _convert_summary_to_spoken(text)
    text = _remove_over_explanations(text)
    text = _remove_banned_endings(text)
    text = _add_em_dash_pauses(text)
    text = _inject_sensory_detail(text)
    text = _ensure_voiceover_beats(text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    notes = (
        "English→Telugu replacements applied. "
        "Textbook→spoken substitutions. "
        "Summary-style lines converted to narrator-voice. "
        "Banned endings removed. "
        "Em-dash reveal pauses added. "
        "Sensory beats injected where missing. "
        "Long paragraphs split for voiceover rhythm."
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
