"""Telugu language quality checker — detects avoidable English and rates authenticity."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Avoidable English words → preferred Telugu equivalents
# These are words that appear in Midnight Telugu scripts but have good
# Telugu equivalents that feel more natural in narration.
# ---------------------------------------------------------------------------
ENGLISH_TO_TELUGU: dict[str, str] = {
    # Physical objects / evidence
    "wet footprints": "తడి అడుగుల ముద్రలు",
    "footprints": "అడుగుల ముద్రలు",
    "footprint": "అడుగు ముద్ర",
    "sealed letter": "మూసి పెట్టిన ఉత్తరం",
    "sealed": "మూసి పెట్టిన",
    "clue": "ఆధారం",
    "proof": "సాక్ష్యం",
    "evidence": "సాక్ష్యం",
    # Actions and states
    "sound": "శబ్దం",
    "noise": "శబ్దం",
    "shadow": "నీడ",
    "midnight": "అర్ధరాత్రి",
    "old road": "పాత దారి",
    "unknown number": "తెలియని నంబర్",
    "not reachable": "అందుబాటులో లేరు",
    "fresh footprint": "తాజా అడుగు ముద్ర",
    "fresh": "తాజా",
    # Locations / places
    "bus stand": "బస్ నిలయం",
    "bridge": "వంతెన",
    "basement": "నేల గది",
    "terrace": "పై అంతస్తు",
    "corridor": "నడవ",
    "apartment": "అపార్టుమెంట్",
    "flat": "అపార్టుమెంట్",
    "office": "కార్యాలయం",
    "factory": "కర్మాగారం",
    "court": "న్యాయస్థానం",
    "village boundary": "గ్రామ సరిహద్దు",
    # Objects
    "diary": "డైరీ",
    "mirror": "అద్దం",
    "candle": "మైనపు వత్తి",
    "camera": "కెమెరా",
    "footage": "దృశ్యం",
    "receipt": "రసీదు",
    "recording": "రికార్డింగ్",
    "screenshot": "స్క్రీన్‌షాట్",
    "zoom": "దగ్గరగా చూసాడు",
    "figure": "ఆకృతి",
    "handprint": "చేతి ముద్ర",
    "scratch marks": "గోకిన గీతలు",
    # Actions
    "line cut": "లైన్ తెగిపోయింది",
    "call back": "తిరిగి call చేసాడు",
    "unreachable": "అందుబాటులో లేరు",
    "lock": "తాళం వేసి",
    "locked": "తాళం వేసి ఉంది",
    "unlock": "తాళం తీసాడు",
    "plug": "ప్లగ్",
    "ignore": "పట్టించుకోలేదు",
    "zoom in": "దగ్గరగా చూసాడు",
}

# Words that are ACCEPTABLE even in narration (commonly used in spoken Telugu)
_ACCEPTABLE_ENGLISH = {
    "డైరీ", "కెమెరా", "అపార్టుమెంట్", "రికార్డింగ్",
    # Numbers and common words
    "photo", "CCTV",
}

# Avoidable English word patterns to detect in script text
# These are the raw English forms that should ideally be replaced
_AVOIDABLE_PATTERNS: list[tuple[str, str]] = [
    ("wet footprints", "తడి అడుగుల ముద్రలు"),
    ("footprints", "అడుగుల ముద్రలు"),
    ("footprint", "అడుగు ముద్ర"),
    ("sealed letter", "మూసి పెట్టిన ఉత్తరం"),
    (r"\bsealed\b", "మూసి పెట్టిన"),
    (r"\bsound\b", "శబ్దం"),
    (r"\bclue\b", "ఆధారం"),
    (r"\bproof\b", "సాక్ష్యం"),
    (r"\bshadow\b", "నీడ"),
    (r"\bmidnight\b", "అర్ధరాత్రి"),
    ("old road", "పాత దారి"),
    ("unknown number", "తెలియని నంబర్"),
    ("not reachable", "అందుబాటులో లేరు"),
    ("fresh footprint", "తాజా అడుగు ముద్ర"),
    (r"\bbridge\b", "వంతెన"),
    (r"\bbasement\b", "నేల గది"),
    (r"\bcorridor\b", "నడవ"),
    (r"\bfigure\b", "ఆకృతి"),
    ("handprint", "చేతి ముద్ర"),
    ("scratch marks", "గోకిన గీతలు"),
    ("line cut", "లైన్ తెగిపోయింది"),
    (r"\bignore\b", "పట్టించుకోలేదు"),
    (r"\bfootage\b", "దృశ్యం"),
    (r"\breceipt\b", "రసీదు"),
    (r"\brecording\b", "రికార్డు"),
]

# POV markers — used by continuity checker
FIRST_PERSON_MARKERS = ["నేను", "నాకు", "నా ", "నన్ను", "నాతో", "నాలో"]
THIRD_PERSON_MARKERS = ["అతను", "ఆమె", "అతనికి", "ఆయన", "వాళ్ళు"]


@dataclass
class TeluguQualityResult:
    telugu_authenticity_score: int          # 0-100
    english_word_issues: list[str] = field(default_factory=list)
    suggested_replacements: list[tuple[str, str]] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "telugu_authenticity_score": self.telugu_authenticity_score,
            "english_word_issues": self.english_word_issues,
            "suggested_replacements": [
                {"found": f, "replace_with": r} for f, r in self.suggested_replacements
            ],
            "suggestions": self.suggestions,
        }


def check_telugu_quality(text: str) -> TeluguQualityResult:
    """Detect avoidable English words and compute a Telugu authenticity score."""
    issues: list[str] = []
    replacements: list[tuple[str, str]] = []
    suggestions: list[str] = []
    penalty = 0

    text_lower = text.lower()

    for pattern, replacement in _AVOIDABLE_PATTERNS:
        # Check as plain substring (case-insensitive) or regex
        try:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
        except re.error:
            matches = [pattern] if pattern.lower() in text_lower else []

        if matches:
            # De-duplicate
            unique_match = matches[0]
            issues.append(f"Avoidable English: '{unique_match}' → suggest '{replacement}'")
            replacements.append((unique_match, replacement))
            penalty += 8

    # Cap penalty at 40 (5 or more English words = -40 max)
    penalty = min(penalty, 40)
    score = max(0, 100 - penalty)

    if replacements:
        suggestions.append(
            f"Replace {len(replacements)} avoidable English word(s) with Telugu equivalents."
        )
    if score >= 85:
        pass  # Good
    elif score >= 65:
        suggestions.append("A few English words remain — replace for more authentic narration.")
    else:
        suggestions.append(
            "Too many English words in narration. Rewrite using Telugu equivalents."
        )

    return TeluguQualityResult(
        telugu_authenticity_score=score,
        english_word_issues=issues,
        suggested_replacements=replacements,
        suggestions=suggestions,
    )


def apply_telugu_replacements(text: str) -> str:
    """Replace avoidable English words with Telugu equivalents in-place."""
    for pattern, replacement in _AVOIDABLE_PATTERNS:
        try:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        except re.error:
            text = text.replace(pattern, replacement)
    return text
