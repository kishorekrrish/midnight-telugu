"""Story scorer — evaluates idea and script quality for Midnight Telugu."""

from __future__ import annotations

from dataclasses import dataclass, field

from workers.models import StoryIdea, StoryScript


@dataclass
class ScoreBreakdown:
    hook_strength: int = 0          # 0-15
    emotional_pull: int = 0         # 0-12
    suspense_build: int = 0         # 0-12
    twist_quality: int = 0          # 0-15
    originality: int = 0            # 0-15
    telugu_naturalness: int = 0     # 0-10
    visual_potential: int = 0       # 0-10
    monetization_safety: int = 0    # 0-11


@dataclass
class StoryScore:
    overall_score: int
    score_breakdown: ScoreBreakdown
    rejection_reasons: list[str] = field(default_factory=list)
    improvement_suggestions: list[str] = field(default_factory=list)
    repeatability_warnings: list[str] = field(default_factory=list)
    grade: str = "C"

    def to_dict(self) -> dict:
        return {
            "overall_score": self.overall_score,
            "grade": self.grade,
            "score_breakdown": {
                "hook_strength": self.score_breakdown.hook_strength,
                "emotional_pull": self.score_breakdown.emotional_pull,
                "suspense_build": self.score_breakdown.suspense_build,
                "twist_quality": self.score_breakdown.twist_quality,
                "originality": self.score_breakdown.originality,
                "telugu_naturalness": self.score_breakdown.telugu_naturalness,
                "visual_potential": self.score_breakdown.visual_potential,
                "monetization_safety": self.score_breakdown.monetization_safety,
            },
            "rejection_reasons": self.rejection_reasons,
            "improvement_suggestions": self.improvement_suggestions,
            "repeatability_warnings": self.repeatability_warnings,
        }


# Patterns that weaken hook quality
_WEAK_HOOK_PATTERNS = [
    "ఒకానొక రోజు",
    "ఒక రోజు",
    "అప్పుడు",
    "ఇది ఒక కథ",
    "నా కథ",
    "మీకు ఒక విషయం చెప్తాను",
]

# Banned patterns — automatic monetization risk flag
_MONETIZATION_RISK_PATTERNS = [
    "రాజకీయ",
    "మతం",
    "కులం",
    "సెక్స్",
    "నగ్న",
    "రక్తం",
    "హత్య",  # only if graphic context
    "ఆత్మహత్య",
    "celebrity",
]

# Twist types that signal quality
_STRONG_TWIST_SIGNALS = [
    "కాదు",
    "అసలు",
    "నిజం",
    "తెలిసింది",
    "మారిపోయింది",
    "వేరే",
    "రహస్యం",
    "దాచిన",
    "పారిపోయింది",
]

# Textbook Telugu signals
_TEXTBOOK_PATTERNS = [
    "వారు",
    "తాను",
    "ఆయన",
    "ఆమె చెప్పింది",
    "అతను చెప్పాడు",
    "నిష్క్రమించారు",
    "ఆగమించారు",
    "పరిస్థితి",
    "అందువల్ల",
]

# Visually rich signals
_VISUAL_SIGNALS = [
    "రాత్రి",
    "చీకటి",
    "వెలుతురు",
    "నీడ",
    "అద్దం",
    "పాత ఇల్లు",
    "బావి",
    "అడవి",
    "వర్షం",
    "దీపం",
    "ఫోటో",
    "తలుపు",
]


def _grade(score: int) -> str:
    if score >= 85:
        return "A"
    if score >= 70:
        return "B"
    if score >= 55:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def _score_hook(hook: str) -> tuple[int, list[str], list[str]]:
    """Score hook strength (0-15)."""
    score = 10
    rejections: list[str] = []
    suggestions: list[str] = []

    if any(p in hook for p in _WEAK_HOOK_PATTERNS):
        score -= 4
        rejections.append("Hook uses a weak opening pattern ('ఒకానొక రోజు' style).")
        suggestions.append("Start the hook with an immediate mystery or contradiction.")

    if "?" in hook or "..." in hook or "—" in hook:
        score += 2
    else:
        suggestions.append("Add a question mark or em-dash pause to increase hook tension.")

    # Length check — great hooks are punchy (50-120 chars)
    if len(hook) < 30:
        score -= 2
        suggestions.append("Hook is too short — add specificity.")
    elif len(hook) > 200:
        score -= 1
        suggestions.append("Hook is too long — trim to one sharp sentence.")
    else:
        score += 1

    if any(visual in hook for visual in _VISUAL_SIGNALS):
        score += 2

    return max(0, min(15, score)), rejections, suggestions


def _score_twist(twist: str) -> tuple[int, list[str], list[str]]:
    """Score twist quality (0-15)."""
    score = 8
    rejections: list[str] = []
    suggestions: list[str] = []

    strong_signals = sum(1 for s in _STRONG_TWIST_SIGNALS if s in twist)
    score += min(4, strong_signals)

    # Predictable twist patterns
    predictable = [
        "అది కల",
        "కలలో",
        "భూతం",
        "దెయ్యం",
        "చనిపోయాడు కాదు",
        "జీవించి ఉన్నాడు",
    ]
    if any(p in twist for p in predictable):
        score -= 3
        suggestions.append("Twist is predictable. Subvert the expectation more sharply.")

    if len(twist) < 20:
        score -= 2
        suggestions.append("Twist is underdeveloped — add context for why it's surprising.")

    return max(0, min(15, score)), rejections, suggestions


def _score_telugu(text: str) -> tuple[int, list[str], list[str]]:
    """Score Telugu naturalness (0-10)."""
    score = 8
    suggestions: list[str] = []

    textbook_count = sum(1 for p in _TEXTBOOK_PATTERNS if p in text)
    penalty = min(4, textbook_count)
    score -= penalty
    if penalty > 0:
        suggestions.append(
            f"Found {textbook_count} textbook Telugu pattern(s). "
            "Replace with natural spoken forms (e.g. 'వారు' → 'వాళ్ళు')."
        )

    if "—" in text:
        score += 1  # good pacing
    if "?" in text:
        score += 1  # audience engagement

    return max(0, min(10, score)), [], suggestions


def _score_monetization(hook: str, premise: str, twist: str) -> tuple[int, list[str]]:
    """Score monetization safety (0-11)."""
    combined = f"{hook} {premise} {twist}"
    score = 11
    rejections: list[str] = []

    for pattern in _MONETIZATION_RISK_PATTERNS:
        if pattern in combined:
            score -= 3
            rejections.append(f"Monetization risk: contains '{pattern}'.")

    return max(0, min(11, score)), rejections


def _score_visual(premise: str, hook: str) -> tuple[int, list[str]]:
    """Score visual potential (0-10)."""
    combined = f"{hook} {premise}"
    visual_count = sum(1 for v in _VISUAL_SIGNALS if v in combined)
    score = min(10, 4 + visual_count * 2)
    suggestions: list[str] = []
    if score < 6:
        suggestions.append("Add a strong visual element (location, object, lighting) to make scenes richer.")
    return score, suggestions


def score_idea(idea: StoryIdea, repeatability_warnings: list[str] | None = None) -> StoryScore:
    """Score a StoryIdea and return a StoryScore."""
    repeatability_warnings = repeatability_warnings or []
    breakdown = ScoreBreakdown()
    all_rejections: list[str] = []
    all_suggestions: list[str] = []

    # Hook strength
    breakdown.hook_strength, r, s = _score_hook(idea.hook)
    all_rejections.extend(r)
    all_suggestions.extend(s)

    # Emotional pull — inferred from tone
    emotional_tones = ["emotional", "family", "grief", "love", "loss", "karma", "justice"]
    breakdown.emotional_pull = 8 if any(t in idea.tone.lower() for t in emotional_tones) else 6

    # Suspense build — inferred from category
    suspense_cats = ["midnight_mystery", "soft_horror", "psychological_twist", "crime_no_violence", "strange_event"]
    breakdown.suspense_build = 9 if idea.category in suspense_cats else 7

    # Twist quality
    breakdown.twist_quality, r, s = _score_twist(idea.twist)
    all_rejections.extend(r)
    all_suggestions.extend(s)

    # Originality — reduced if repeatability warnings exist
    breakdown.originality = max(5, 13 - len(repeatability_warnings) * 2)
    if repeatability_warnings:
        all_suggestions.append("Story shares patterns with existing content — differentiate further.")

    # Telugu naturalness (score hook and premise)
    breakdown.telugu_naturalness, _, s = _score_telugu(f"{idea.hook} {idea.premise}")
    all_suggestions.extend(s)

    # Visual potential
    breakdown.visual_potential, s = _score_visual(idea.premise, idea.hook)
    all_suggestions.extend(s)

    # Monetization safety
    breakdown.monetization_safety, r = _score_monetization(idea.hook, idea.premise, idea.twist)
    all_rejections.extend(r)

    total = (
        breakdown.hook_strength
        + breakdown.emotional_pull
        + breakdown.suspense_build
        + breakdown.twist_quality
        + breakdown.originality
        + breakdown.telugu_naturalness
        + breakdown.visual_potential
        + breakdown.monetization_safety
    )

    return StoryScore(
        overall_score=max(0, min(100, total)),
        score_breakdown=breakdown,
        rejection_reasons=all_rejections,
        improvement_suggestions=list(dict.fromkeys(all_suggestions)),  # deduplicate
        repeatability_warnings=repeatability_warnings,
        grade=_grade(total),
    )


def score_script(script: StoryScript, repeatability_warnings: list[str] | None = None) -> StoryScore:
    """Score a StoryScript."""
    repeatability_warnings = repeatability_warnings or []
    breakdown = ScoreBreakdown()
    all_rejections: list[str] = []
    all_suggestions: list[str] = []

    full = script.full_script_telugu

    # Hook
    breakdown.hook_strength, r, s = _score_hook(script.hook_line)
    all_rejections.extend(r)
    all_suggestions.extend(s)

    # Emotional pull — check for emotional Telugu words
    emotional_words = ["గుండె", "కన్నీళ్ళు", "ప్రేమ", "అమ్మ", "నాన్న", "క్షమాపణ", "విషాదం"]
    emotional_count = sum(1 for w in emotional_words if w in full)
    breakdown.emotional_pull = min(12, 5 + emotional_count * 2)

    # Suspense build — look for tension markers
    tension_markers = ["—", "...", "ఆగిపోయింది", "వణికిపోయింది", "నోరు", "గుండె"]
    tension_count = sum(1 for m in tension_markers if m in full)
    breakdown.suspense_build = min(12, 5 + tension_count)

    # Twist quality — look for reveal patterns in last third
    last_third = full[len(full) * 2 // 3:]
    breakdown.twist_quality, r, s = _score_twist(last_third)
    all_rejections.extend(r)
    all_suggestions.extend(s)

    # Originality
    breakdown.originality = max(5, 13 - len(repeatability_warnings) * 2)

    # Telugu naturalness
    breakdown.telugu_naturalness, _, s = _score_telugu(full)
    all_suggestions.extend(s)

    # Visual potential
    breakdown.visual_potential, s = _score_visual(full, script.hook_line)
    all_suggestions.extend(s)

    # Monetization safety
    breakdown.monetization_safety, r = _score_monetization(script.hook_line, full, "")
    all_rejections.extend(r)

    # Penalty for repeated AI endings
    ai_endings = [
        "అప్పుడు అతనికి నిజం తెలిసింది",
        "నీతి ఏమిటంటే",
        "ఇది మనకు నేర్పిస్తుంది",
        "జీవితం మనకు చెప్తుంది",
    ]
    for ending in ai_endings:
        if ending in full:
            breakdown.telugu_naturalness = max(0, breakdown.telugu_naturalness - 2)
            all_suggestions.append(f"Remove AI-pattern ending: '{ending}'.")

    total = (
        breakdown.hook_strength
        + breakdown.emotional_pull
        + breakdown.suspense_build
        + breakdown.twist_quality
        + breakdown.originality
        + breakdown.telugu_naturalness
        + breakdown.visual_potential
        + breakdown.monetization_safety
    )

    return StoryScore(
        overall_score=max(0, min(100, total)),
        score_breakdown=breakdown,
        rejection_reasons=all_rejections,
        improvement_suggestions=list(dict.fromkeys(all_suggestions)),
        repeatability_warnings=repeatability_warnings,
        grade=_grade(total),
    )
