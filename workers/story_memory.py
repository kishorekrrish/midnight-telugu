"""Story memory — detect repeated patterns across previously generated content."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from workers.config import APPROVED_DIR, IDEAS_DIR, PUBLISHED_DIR, SCRIPTS_DIR
from workers.models import StoryIdea

# Twist type fingerprints — map common Telugu twist patterns to canonical labels
_TWIST_TYPE_PATTERNS: list[tuple[str, str]] = [
    ("పారిపోయింది", "escape_twist"),
    ("పారిపోయాడు", "escape_twist"),
    ("చనిపోయాడు కాదు", "fake_death"),
    ("అది కల", "dream_reveal"),
    ("కలలో", "dream_reveal"),
    ("భూతం", "ghost_reveal"),
    ("దెయ్యం", "ghost_reveal"),
    ("నేనే", "identity_reveal"),
    ("అతనే", "identity_reveal"),
    ("ఆమెే", "identity_reveal"),
    ("పోలీసు", "undercover_reveal"),
    ("అండర్‌కవర్", "undercover_reveal"),
    ("డబ్బు", "money_reveal"),
    ("బ్యాంక్", "money_reveal"),
    ("క్షమాపణ", "forgiveness_reveal"),
    ("రహస్యం", "secret_reveal"),
    ("చదువు", "sacrifice_reveal"),
    ("మోసం", "betrayal_reveal"),
]

_ENDING_PATTERNS: list[tuple[str, str]] = [
    ("అప్పుడు అతనికి నిజం తెలిసింది", "generic_truth_reveal"),
    ("చివరికి నిజం బయటపడింది", "generic_truth_reveal"),
    ("నిజం బయట పడింది", "generic_truth_reveal"),
    ("అందరికీ సత్యం తెలిసింది", "generic_truth_reveal"),
    ("నీతి ఏమిటంటే", "moral_lesson"),
    ("జీవితంలో నేర్చుకున్నది", "moral_lesson"),
    ("Comment లో చెప్పండి", "cta_ending"),
]

_LOCATION_PATTERNS: list[tuple[str, str]] = [
    ("బావి", "well"),
    ("పాత ఇల్లు", "old_house"),
    ("రైలు స్టేషన్", "railway_station"),
    ("గది", "room"),
    ("అడవి", "forest"),
    ("రాత్రి", "night"),
    ("వీధి", "street"),
    ("ఫోన్", "phone"),
    ("ఫోటో", "photograph"),
]

_RELATIONSHIP_PATTERNS: list[tuple[str, str]] = [
    ("భార్య", "spouse"),
    ("భర్త", "spouse"),
    ("అమ్మ", "mother"),
    ("నాన్న", "father"),
    ("కొడుకు", "child"),
    ("కూతురు", "child"),
    ("స్నేహితుడు", "friend"),
    ("స్నేహితురాలు", "friend"),
    ("వ్యాపారస్తుడు", "businessman"),
    ("పోలీసు", "police"),
]


def _extract_twist_type(text: str) -> str:
    for pattern, label in _TWIST_TYPE_PATTERNS:
        if pattern in text:
            return label
    return "unknown_twist"


def _extract_location(text: str) -> str:
    for pattern, label in _LOCATION_PATTERNS:
        if pattern in text:
            return label
    return "unspecified"


def _extract_relationship(text: str) -> str:
    for pattern, label in _RELATIONSHIP_PATTERNS:
        if pattern in text:
            return label
    return "unspecified"


def _extract_ending_type(text: str) -> str:
    for pattern, label in _ENDING_PATTERNS:
        if pattern in text:
            return label
    return "unique"


def _load_existing_content(dirs: list[Path]) -> list[dict]:
    """Load all JSON files from specified directories."""
    records: list[dict] = []
    for d in dirs:
        if not d.exists():
            continue
        for f in d.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                records.append(data)
            except Exception:
                continue
    return records


def check_repeatability(
    idea: StoryIdea,
    scan_dirs: list[Path] | None = None,
) -> list[str]:
    """
    Check a new StoryIdea against existing content for repeated patterns.
    Returns a list of warning strings (empty = no repeats detected).
    """
    if scan_dirs is None:
        scan_dirs = [IDEAS_DIR, SCRIPTS_DIR, APPROVED_DIR, PUBLISHED_DIR]

    existing = _load_existing_content(scan_dirs)
    if not existing:
        return []

    warnings: list[str] = []

    # 1. Title similarity — check for same first word
    idea_first_word = idea.title.split()[0] if idea.title else ""
    title_matches = [
        r.get("title", "") for r in existing
        if r.get("title", "").startswith(idea_first_word) and r.get("title") != idea.title
    ]
    if len(title_matches) >= 2:
        warnings.append(f"Title starts with '{idea_first_word}' — already used {len(title_matches)} time(s).")

    # 2. Category overuse — warn if same category used more than 3 times recently
    categories = [r.get("category", "") for r in existing]
    cat_counts = Counter(categories)
    idea_cat = idea.category if isinstance(idea.category, str) else idea.category.value
    if cat_counts.get(idea_cat, 0) >= 3:
        warnings.append(
            f"Category '{idea_cat}' already used {cat_counts[idea_cat]} time(s). "
            "Consider a different content bucket."
        )

    # 3. Twist type repetition
    idea_twist_type = _extract_twist_type(idea.twist)
    if idea_twist_type != "unknown_twist":
        twist_matches = sum(
            1 for r in existing
            if _extract_twist_type(r.get("twist", "")) == idea_twist_type
        )
        if twist_matches >= 2:
            warnings.append(
                f"Twist type '{idea_twist_type}' already used {twist_matches} time(s). "
                "Try a different reveal mechanic."
            )

    # 4. Same relationship conflict
    idea_rel = _extract_relationship(f"{idea.premise} {idea.twist}")
    if idea_rel != "unspecified":
        rel_matches = sum(
            1 for r in existing
            if _extract_relationship(
                f"{r.get('premise', '')} {r.get('twist', '')}"
            ) == idea_rel
        )
        if rel_matches >= 3:
            warnings.append(
                f"Relationship conflict '{idea_rel}' repeated {rel_matches} time(s). "
                "Vary the character dynamic."
            )

    # 5. Same location
    idea_loc = _extract_location(f"{idea.hook} {idea.premise}")
    if idea_loc != "unspecified":
        loc_matches = sum(
            1 for r in existing
            if _extract_location(
                f"{r.get('hook', '')} {r.get('premise', '')}"
            ) == idea_loc
        )
        if loc_matches >= 3:
            warnings.append(
                f"Location type '{idea_loc}' repeated {loc_matches} time(s). "
                "Use a fresh setting."
            )

    return warnings


def category_distribution(scan_dirs: list[Path] | None = None) -> dict[str, int]:
    """Return category usage counts across all existing content."""
    if scan_dirs is None:
        scan_dirs = [IDEAS_DIR, SCRIPTS_DIR, APPROVED_DIR]
    existing = _load_existing_content(scan_dirs)
    categories = [r.get("category", "unknown") for r in existing]
    return dict(Counter(categories))
