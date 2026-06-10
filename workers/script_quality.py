"""Script quality validator — checks narrative completeness and safety."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from workers.models import HumanizedScript, StoryScript
from workers.script_generator import BANNED_ENDINGS

# Words that indicate a sensory/cinematic moment
_SENSORY_SIGNALS = [
    "గాలి", "గుండె", "అడుగు", "నిశ్శబ్దం", "వణికాయి",
    "శ్వాస", "చీకటి", "వెలుతురు", "శబ్దం", "వినిపించింది",
    "కళ్ళు", "చేతులు", "మొహం", "గొంతు", "చప్పుడు",
    "మెరిసింది", "చల్లగా", "వేడిగా", "తడిగా",
]

# Midpoint escalation signals — tension rising before twist
_ESCALATION_SIGNALS = [
    "కానీ —", "అప్పుడు —", "ఆ క్షణంలో", "అకస్మాత్తుగా",
    "ఎవరూ అనుకోలేదు", "మళ్ళీ చదివాడు", "వెనక్కి తిరిగాడు",
    "— cut", "line cut", "unknown number",
    "lock", "20 సంవత్సరాలు", "ఒక్కసారిగా",
]

# Final twist signals
_TWIST_SIGNALS = [
    "కాదు", "వేరే", "బతికి ఉంది", "exist అవ్వడం లేదు",
    "లోపల నుండి", "delay", "నా గొంతే", "నా పేరు",
    "నాటి నుండి", "తిరిగి నడుస్తోంది", "ఇప్పటికీ",
]

# Summary-style (not narrator-voice) red flags
_SUMMARY_PATTERNS = [
    r"ఒక కొడుకు\s+తండ్రి",
    r"ఒక అమ్మాయి\s+\w+ని",
    r"ఒక వ్యక్తి\s+\w+కి",
    r"వారు అందుకుంటారు",
    r"వారు వెళ్ళతారు",
    r"వారు చేస్తారు",
]

# Real-person / copyright risk signals
_REAL_PERSON_SIGNALS = [
    "actor", "actress", "minister", "CM ", "PM ", "president",
    "మంత్రి", "ముఖ్యమంత్రి",
]

# Monetization risk terms
_MONETIZATION_RISKS = [
    "రాజకీయ", "మతం", "కులం", "సెక్స్", "నగ్న", "ఆత్మహత్య",
]


@dataclass
class ScriptQualityResult:
    passed: bool
    quality_score: int          # 0-100
    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    publish_recommendation: str = "needs_rewrite"   # approve_candidate | needs_rewrite | reject

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "quality_score": self.quality_score,
            "issues": self.issues,
            "suggestions": self.suggestions,
            "publish_recommendation": self.publish_recommendation,
        }


def validate_script(script: StoryScript | HumanizedScript) -> ScriptQualityResult:
    """Validate a script for narrative quality and safety."""
    text = script.full_script_telugu
    issues: list[str] = []
    suggestions: list[str] = []
    score = 100

    # ── Word count ────────────────────────────────────────────────────────
    words = text.split()
    word_count = len(words)
    if word_count < 80:
        issues.append(f"Script too short: {word_count} words (target 120–160).")
        suggestions.append("Expand narration — add more moment-by-moment detail.")
        score -= 30
    elif word_count < 100:
        issues.append(f"Script below target: {word_count} words (target 120–160).")
        suggestions.append("Add a sensory beat or expand the buildup section.")
        score -= 15
    elif word_count > 220:
        issues.append(f"Script too long: {word_count} words (target 120–160).")
        suggestions.append("Trim summary passages; keep only the key beats.")
        score -= 10

    # ── Hook (first 3 lines) ──────────────────────────────────────────────
    first_lines = "\n".join(text.split("\n")[:3])
    _HOOK_SIGNALS = [
        "?", "—", "కానీ", "రహస్యం", "ఇప్పటికీ", "మోగింది", "వచ్చింది",
        "lock", "Unknown", "ఆగింది", "ఆగిపోయింది", "వణికాయి", "unknown",
        "అకస్మాత్తుగా", "ఎవరూ", "ఎప్పుడూ", "మళ్ళీ", "తెరిచాడు",
    ]
    hook_weak = not any(sig in first_lines for sig in _HOOK_SIGNALS)
    if hook_weak:
        issues.append("Hook lacks tension — first 3 lines don't create a question or mystery.")
        suggestions.append("Open with a surprising fact, a shocking action, or a dangling question.")
        score -= 12

    # ── Sensory detail ────────────────────────────────────────────────────
    has_sensory = any(sig in text for sig in _SENSORY_SIGNALS)
    if not has_sensory:
        issues.append("No sensory detail found (sound, light, silence, physical sensation).")
        suggestions.append("Add one line like 'గాలి ఆగింది' or 'చేతులు వణికాయి' to raise tension.")
        score -= 10

    # ── Midpoint escalation ───────────────────────────────────────────────
    has_escalation = any(sig in text for sig in _ESCALATION_SIGNALS)
    if not has_escalation:
        issues.append("No midpoint escalation detected.")
        suggestions.append("Add a pivot line ('కానీ —' or 'అప్పుడు —') before the twist.")
        score -= 8

    # ── Final twist — scan last 2 paragraphs (cinematic closing follows twist) ──
    paras = [p for p in text.strip().split("\n\n") if p.strip()]
    last_two = "\n\n".join(paras[-2:]) if len(paras) >= 2 else text[-300:]
    # Also add cinematic closing signals as twist indicators
    _CINEMATIC_CLOSING_SIGNALS = [
        "తెరవలేదు", "ఎప్పుడూ", "ఇప్పటికీ అక్కడే", "exist అవ్వడం లేదు",
        "నా గొంతే", "నా పేరు", "ఒంటరిగా అక్కడికి", "ఎవరూ లేనప్పుడు",
    ]
    has_twist = any(sig in last_two for sig in _TWIST_SIGNALS + _CINEMATIC_CLOSING_SIGNALS)
    if not has_twist:
        issues.append("No clear final twist detected.")
        suggestions.append("End with a one-line revelation that recontextualizes the story.")
        score -= 15

    # ── Banned endings ────────────────────────────────────────────────────
    for banned in BANNED_ENDINGS:
        if banned in text:
            issues.append(f"Banned ending pattern found: '{banned}'")
            suggestions.append("Remove generic question/moral endings. Use a cinematic final line instead.")
            score -= 20
            break

    # ── Summary-style narration ───────────────────────────────────────────
    summary_hits = [p for p in _SUMMARY_PATTERNS if re.search(p, text)]
    if summary_hits:
        issues.append("Summary-style narration detected (not narrator-voice).")
        suggestions.append("Replace 'ఒక వ్యక్తి / ఒక కొడుకు' constructions with character-specific scenes.")
        score -= 8

    # ── Safety gates ──────────────────────────────────────────────────────
    for risk in _MONETIZATION_RISKS:
        if risk in text:
            issues.append(f"Monetization risk term found: '{risk}'")
            score -= 25
            break

    for person_ref in _REAL_PERSON_SIGNALS:
        if person_ref.lower() in text.lower():
            issues.append(f"Possible real-person reference: '{person_ref}'")
            suggestions.append("Remove any celebrity, politician, or real-person references.")
            score -= 20
            break

    score = max(0, score)
    passed = score >= 60 and not any("Monetization risk" in i or "real-person" in i.lower() for i in issues)

    if score >= 75:
        rec = "approve_candidate"
    elif score >= 50:
        rec = "needs_rewrite"
    else:
        rec = "reject"

    return ScriptQualityResult(
        passed=passed,
        quality_score=score,
        issues=issues,
        suggestions=suggestions,
        publish_recommendation=rec,
    )
