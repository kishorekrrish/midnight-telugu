"""Story continuity validator — checks POV, character consistency, hook-body-twist connection."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from workers.models import HumanizedScript, StoryScript
from workers.telugu_quality import FIRST_PERSON_MARKERS, THIRD_PERSON_MARKERS


@dataclass
class ContinuityResult:
    continuity_score: int           # 0-100
    passed: bool
    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "continuity_score": self.continuity_score,
            "passed": self.passed,
            "issues": self.issues,
            "suggestions": self.suggestions,
        }


def _count_pov_markers(text: str) -> tuple[int, int]:
    """Return (first_person_count, third_person_count)."""
    fp = sum(text.count(m) for m in FIRST_PERSON_MARKERS)
    tp = sum(text.count(m) for m in THIRD_PERSON_MARKERS)
    return fp, tp


def _extract_character_names(text: str) -> list[str]:
    """
    Extract likely Telugu character names — capitalized-prefix words that
    appear 2+ times and are not common nouns.
    """
    # Match Telugu words that start a sentence or follow a newline/—
    # Simple heuristic: words ending in common Telugu name suffixes
    _NAME_SUFFIXES = [
        "్", "ు", "ి", "ే",          # vowel endings common in Telugu names
        "ష్", "ర్", "న్", "ల్",
    ]
    # Extract words that appear >= 2 times and are likely proper nouns
    # (short, 2-6 chars, start context suggests name)
    words = re.findall(r"[ఀ-౿]{2,8}", text)
    freq: dict[str, int] = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1

    # Common non-name Telugu words to exclude
    _STOP = {
        "అతను", "ఆమె", "అది", "ఇది", "కానీ", "అందులో", "లోపల",
        "అక్కడ", "ఇక్కడ", "అందరూ", "తర్వాత", "ముందు", "వెళ్ళాడు",
        "చూసాడు", "తెలియదు", "ఉంది", "లేదు", "అయింది", "చేసాడు",
        "మళ్ళీ", "ఒక్కసారిగా", "వేగంగా", "నెమ్మదిగా", "తెలిసిన",
        "పట్టింది", "చేతులు", "కళ్ళు", "గుండె", "శ్వాస", "నీడ",
        "గాలి", "తలుపు", "ఇల్లు", "గది", "రాత్రి", "తండ్రి",
        "అమ్మ", "కుటుంబం", "పాత", "తాజా", "వేరే", "నిజం",
    }

    candidates = [
        w for w, cnt in freq.items()
        if cnt >= 2 and w not in _STOP and len(w) >= 3
    ]
    return candidates[:5]  # Top 5 candidates


def _paragraphs(text: str) -> list[str]:
    return [p.strip() for p in text.split("\n\n") if p.strip()]


def check_continuity(script: StoryScript | HumanizedScript) -> ContinuityResult:
    """Validate story continuity for POV, character, hook-body-twist connection."""
    text = script.full_script_telugu
    hook_line = script.hook_line
    issues: list[str] = []
    suggestions: list[str] = []
    score = 100

    paras = _paragraphs(text)
    if not paras:
        return ContinuityResult(
            continuity_score=0, passed=False,
            issues=["Script is empty."], suggestions=["Generate a script first."]
        )

    # ── POV consistency ──────────────────────────────────────────────────
    fp_count, tp_count = _count_pov_markers(text)
    hook_fp = sum(hook_line.count(m) for m in FIRST_PERSON_MARKERS)

    if fp_count > 3 and tp_count > 3:
        # Mixed POV — check if hook matches body
        issues.append(
            f"Mixed POV detected: {fp_count} first-person and {tp_count} third-person markers. "
            "Choose one consistent narrator voice."
        )
        suggestions.append(
            "If the narrator is 'I', remove third-person references to the protagonist. "
            "If third-person, remove 'నేను/నాకు' from the body."
        )
        score -= 20

    if hook_fp > 0 and tp_count > fp_count:
        issues.append(
            "Hook uses first-person ('నేను') but story body is mostly third-person. "
            "POV shifts confuse the listener."
        )
        suggestions.append(
            "Rewrite hook in third-person to match body, or rewrite body in first-person."
        )
        score -= 15

    # ── Character name consistency ────────────────────────────────────────
    names = _extract_character_names(text)
    # If we find 3+ distinct frequent words it might indicate name inconsistency
    # (simple heuristic — not foolproof)
    if len(names) >= 4:
        issues.append(
            f"Multiple prominent names/nouns detected: {', '.join(names[:4])}. "
            "Verify only one protagonist is named."
        )
        suggestions.append("Use a single protagonist name consistently throughout.")
        score -= 10

    # ── Hook connects to body ─────────────────────────────────────────────
    # Hook should share at least one key word with the first 2 paragraphs
    hook_words = set(re.findall(r"[ఀ-౿]{3,}", hook_line))
    body_start = " ".join(paras[:2]) if len(paras) >= 2 else paras[0]
    body_words = set(re.findall(r"[ఀ-౿]{3,}", body_start))
    overlap = hook_words & body_words
    if len(overlap) < 2 and len(hook_words) >= 3:
        issues.append(
            "Hook and story body share few common words — the story may feel disconnected from its opening."
        )
        suggestions.append(
            "Echo the hook's key word or image in the first body paragraph to anchor the listener."
        )
        score -= 12

    # ── Object/clue introduced and resolved ──────────────────────────────
    # Detect if an object is mentioned early and referenced late
    _CLUE_WORDS = [
        "ఉత్తరం", "photograph", "తాళం", "డైరీ", "అద్దం", "రికార్డు",
        "ముద్ర", "ఆధారం", "సాక్ష్యం", "రసీదు", "document",
    ]
    first_half = " ".join(paras[: max(1, len(paras) // 2)])
    second_half = " ".join(paras[len(paras) // 2 :])
    clue_introduced = [w for w in _CLUE_WORDS if w in first_half]
    clue_resolved = [w for w in clue_introduced if w in second_half]

    if clue_introduced and not clue_resolved:
        issues.append(
            f"Clue/object introduced early ('{clue_introduced[0]}') but not referenced in the second half."
        )
        suggestions.append(
            "Bring back the key object in the twist or resolution to close the loop."
        )
        score -= 12

    # ── Hook-to-twist connection ──────────────────────────────────────────
    last_para = paras[-1] if paras else ""
    second_last = paras[-2] if len(paras) >= 2 else ""
    twist_zone = second_last + " " + last_para

    # Check that the final twist contains any word from hook
    twist_overlap = hook_words & set(re.findall(r"[ఀ-౿]{3,}", twist_zone))
    if not twist_overlap and len(hook_words) >= 3:
        issues.append(
            "Final twist does not echo the hook — the story's end feels disconnected from its opening."
        )
        suggestions.append(
            "Add at least one image or word from the hook in the twist to create narrative closure."
        )
        score -= 10

    # ── Final line clarity ────────────────────────────────────────────────
    # A final line that is just a string of English words or very short is suspicious
    final_lines = last_para.split("\n")
    actual_final = final_lines[-1].strip() if final_lines else ""

    if actual_final:
        telugu_chars = len(re.findall(r"[ఀ-౿]", actual_final))
        total_chars = len(actual_final.replace(" ", ""))
        if total_chars > 0 and telugu_chars / total_chars < 0.4:
            issues.append(
                "Final line is mostly English — may be confusing for listeners. "
                f"Found: '{actual_final[:60]}'"
            )
            suggestions.append(
                "Rewrite the final line in Telugu for maximum impact."
            )
            score -= 15

    # ── Setting consistency ───────────────────────────────────────────────
    # Simple check: if multiple distinct locations mentioned without transition
    _LOCATION_MARKERS = [
        "ఇల్లు", "గది", "రోడ్డు", "స్టేషన్", "అడవి", "చెరువు",
        "బావి", "గుడి", "ఆఫీసు", "hospital", "court",
    ]
    mentioned_locations = [loc for loc in _LOCATION_MARKERS if loc in text]
    if len(mentioned_locations) > 3:
        issues.append(
            f"Multiple settings mentioned ({', '.join(mentioned_locations[:4])}). "
            "Verify the story stays in one main location."
        )
        suggestions.append("Focus on one or two locations. Random scene shifts break immersion.")
        score -= 8

    score = max(0, score)
    passed = score >= 60 and not any("POV" in i or "disconnected" in i for i in issues) or score >= 75

    return ContinuityResult(
        continuity_score=score,
        passed=passed,
        issues=issues,
        suggestions=suggestions,
    )
