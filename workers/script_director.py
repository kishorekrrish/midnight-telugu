"""Script Director — automated Telugu narration improvement gate."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path

from workers.models import DirectedScript, HumanizedScript, StoryScript

# Thresholds for auto-approval
_QUALITY_THRESHOLD = 88
_AUTH_THRESHOLD = 90
_CONT_THRESHOLD = 90


@dataclass
class DirectorResult:
    directed_script: str
    quality_score: int
    telugu_authenticity_score: int
    continuity_score: int
    issues_fixed: list[str] = field(default_factory=list)
    remaining_issues: list[str] = field(default_factory=list)
    recommendation: str = "needs_rewrite"
    approved_for_scene_planning: bool = False
    attempts: int = 1
    provider_name: str = "mock"


def _load_director_prompt() -> str:
    """Load the script director system prompt from prompts/script_director.md."""
    prompt_path = Path(__file__).parent.parent / "prompts" / "script_director.md"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    return ""


def _build_director_prompt(
    script_text: str,
    hook_line: str,
    issues: list[str],
    suggestions: list[str],
    system_prompt: str,
) -> str:
    """Build the full prompt sent to the text provider."""
    issues_block = ""
    if issues:
        issues_block = "\n## Issues to Fix\n\n" + "\n".join(f"- {i}" for i in issues[:8]) + "\n"

    suggestions_block = ""
    if suggestions:
        suggestions_block = "\n## Suggestions\n\n" + "\n".join(f"- {s}" for s in suggestions[:5]) + "\n"

    return f"""{system_prompt}

---

## Original Hook Line

{hook_line}

## Current Telugu Script

```
{script_text}
```
{issues_block}{suggestions_block}
## Instructions

Rewrite the above Telugu script, fixing the listed issues.
Output ONLY the improved Telugu narration — no commentary, no headers.
"""


def _score_text(text: str, script: StoryScript | HumanizedScript) -> tuple[int, int, int, list[str]]:
    """Run all three validators on `text` wrapped in a script-like object and return scores + issues."""
    from workers.script_quality import validate_script
    from workers.story_continuity import check_continuity
    from workers.telugu_quality import check_telugu_quality

    # Wrap text in a HumanizedScript-like object to reuse validators
    wrapped = HumanizedScript(
        id=f"tmp_{uuid.uuid4().hex[:6]}",
        script_id=script.id,
        title=script.title,
        category=script.category,
        hook_line=script.hook_line,
        full_script_telugu=text,
        estimated_duration_seconds=getattr(script, "estimated_duration_seconds", 55),
    )

    sq = validate_script(wrapped)
    tq = check_telugu_quality(text)
    cont = check_continuity(wrapped)

    all_issues = sq.issues[:]
    return sq.quality_score, tq.telugu_authenticity_score, cont.continuity_score, all_issues


def direct_script(
    script: StoryScript | HumanizedScript,
    provider_name: str | None = None,
    max_attempts: int = 3,
) -> DirectorResult:
    """Run Script Director to improve and validate a Telugu script.

    Retries up to max_attempts, picking the best result.
    """
    from workers.config import SCRIPT_DIRECTOR_PROVIDER
    from workers.providers import get_text_provider
    from workers.script_quality import validate_script
    from workers.story_continuity import check_continuity
    from workers.telugu_quality import check_telugu_quality

    provider_name = provider_name or SCRIPT_DIRECTOR_PROVIDER
    provider = get_text_provider(provider_name)
    system_prompt = _load_director_prompt()

    # Initial validation of the input script
    sq0 = validate_script(script)
    tq0 = check_telugu_quality(script.full_script_telugu)
    cont0 = check_continuity(script)
    original_issues = sq0.issues + (tq0.english_word_issues if tq0.english_word_issues else [])

    best_text = script.full_script_telugu
    best_q = sq0.quality_score
    best_auth = tq0.telugu_authenticity_score
    best_cont = cont0.continuity_score
    best_issues = sq0.issues[:]
    best_suggestions = sq0.suggestions[:]
    best_approved = False

    current_issues = sq0.issues + sq0.suggestions
    current_text = script.full_script_telugu

    attempt = 0
    for attempt in range(1, max_attempts + 1):  # noqa: B007
        prompt = _build_director_prompt(
            script_text=current_text,
            hook_line=script.hook_line,
            issues=current_issues[:8],
            suggestions=best_suggestions[:5],
            system_prompt=system_prompt,
        )

        improved = provider.generate_text(prompt)
        if not improved or not improved.strip():
            continue

        q, auth, cont_score, issues = _score_text(improved, script)
        approved = (
            q >= _QUALITY_THRESHOLD
            and auth >= _AUTH_THRESHOLD
            and cont_score >= _CONT_THRESHOLD
            and not any("Monetization risk" in i or "real-person" in i.lower() for i in issues)
        )

        # Keep best attempt
        if q > best_q or (q == best_q and auth > best_auth):
            best_text = improved
            best_q = q
            best_auth = auth
            best_cont = cont_score
            best_issues = issues
            best_approved = approved

        if approved:
            break

        # Next iteration: feed back the remaining issues
        current_text = improved
        current_issues = issues

    # Compute issues_fixed
    issues_fixed = [i for i in original_issues if i not in best_issues]

    # Final recommendation
    if best_approved:
        rec = "approve_candidate"
    elif best_q >= 50:
        rec = "needs_rewrite"
    else:
        rec = "reject"

    return DirectorResult(
        directed_script=best_text,
        quality_score=best_q,
        telugu_authenticity_score=best_auth,
        continuity_score=best_cont,
        issues_fixed=issues_fixed,
        remaining_issues=best_issues,
        recommendation=rec,
        approved_for_scene_planning=best_approved,
        attempts=min(attempt, max_attempts),
        provider_name=provider_name,
    )


def save_directed_script(
    result: DirectorResult,
    script: StoryScript | HumanizedScript,
    output_dir: Path,
) -> tuple[DirectedScript, Path]:
    """Persist a DirectorResult as a DirectedScript JSON file."""
    from workers.io_utils import write_json

    output_dir.mkdir(parents=True, exist_ok=True)

    ds = DirectedScript(
        id=f"directed_{uuid.uuid4().hex[:8]}",
        source_script_id=script.id,
        title=script.title,
        category=script.category,
        hook_line=script.hook_line,
        directed_telugu_script=result.directed_script,
        director_provider=result.provider_name,
        quality_score=result.quality_score,
        telugu_authenticity_score=result.telugu_authenticity_score,
        continuity_score=result.continuity_score,
        issues_fixed=result.issues_fixed,
        remaining_issues=result.remaining_issues,
        recommendation=result.recommendation,
        approved_for_scene_planning=result.approved_for_scene_planning,
    )

    json_path = output_dir / f"{ds.id}.json"
    write_json(json_path, ds)
    return ds, json_path
