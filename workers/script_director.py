"""Script Director — blueprint-aware rewrite and strict narrative approval."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path

from workers.models import DirectedScript, HumanizedScript, StoryBlueprint, StoryScript

_QUALITY_THRESHOLD = 88
_AUTH_THRESHOLD = 90
_CONT_THRESHOLD = 90
_NARRATIVE_THRESHOLD = 90


@dataclass
class DirectorResult:
    directed_script: str
    blueprint_id: str
    quality_score: int
    telugu_authenticity_score: int
    continuity_score: int
    narrative_score: int
    hard_failures: list[str] = field(default_factory=list)
    narrative_facts: dict = field(default_factory=dict)
    issues_fixed: list[str] = field(default_factory=list)
    remaining_issues: list[str] = field(default_factory=list)
    recommendation: str = "needs_rewrite"
    approved_for_scene_planning: bool = False
    attempts: int = 1
    provider_name: str = "mock"


def _load_director_prompt() -> str:
    prompt_path = Path(__file__).parent.parent / "prompts" / "script_director.md"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    return ""


def _build_director_prompt(
    blueprint: StoryBlueprint,
    script_text: str,
    issues: list[str],
    system_prompt: str,
) -> str:
    issue_lines = "\n".join(f"- {issue}" for issue in issues[:10])
    return f"""{system_prompt}

## Locked Blueprint

Protagonist: {blueprint.protagonist_name}
POV: {blueprint.point_of_view}
Primary device: {blueprint.primary_story_device}
Primary clue: {blueprint.primary_clue}
Supporting clues: {", ".join(blueprint.supporting_clues)}
Central question: {blueprint.central_question}
Reveal: {blueprint.reveal}
Final twist: {blueprint.final_twist}
Final line: {blueprint.final_line}
Locations: {", ".join(blueprint.locations)}
Forbidden elements: {", ".join(blueprint.forbidden_elements)}

## Current Telugu Script

```
{script_text}
```

## Exact Violations

{issue_lines}

## Instructions

Rewrite ONLY within the blueprint. Do not invent new characters, objects, clues, locations, or twists.
Output ONLY the final Telugu narration.
"""


def _evaluate_attempt(
    text: str,
    source_script: StoryScript | HumanizedScript,
    blueprint: StoryBlueprint,
) -> tuple[int, int, int, int, list[str], dict]:
    from workers.narrative_facts import extract_narrative_facts
    from workers.narrative_validator import validate_narrative
    from workers.script_quality import validate_script
    from workers.story_continuity import check_continuity
    from workers.telugu_quality import check_telugu_quality

    wrapped = HumanizedScript(
        id=f"tmp_{uuid.uuid4().hex[:6]}",
        script_id=source_script.id,
        title=source_script.title,
        category=source_script.category,
        hook_line=source_script.hook_line,
        full_script_telugu=text,
        estimated_duration_seconds=getattr(source_script, "estimated_duration_seconds", 55),
    )
    facts = extract_narrative_facts(wrapped, blueprint)
    narrative = validate_narrative(blueprint, facts, wrapped.hook_line)
    quality = validate_script(wrapped)
    telugu = check_telugu_quality(text)
    continuity = check_continuity(wrapped)

    combined_issues = narrative.hard_failures + narrative.issues + quality.issues[:3]
    return (
        quality.quality_score,
        telugu.telugu_authenticity_score,
        continuity.continuity_score,
        narrative.score,
        combined_issues,
        facts.model_dump(),
    )


def _approval(
    blueprint_passed: bool,
    recommendation: str,
    narrative_score: int,
    hard_failures: list[str],
    quality_score: int,
    auth_score: int,
    continuity_score: int,
) -> bool:
    return (
        blueprint_passed
        and not hard_failures
        and narrative_score >= _NARRATIVE_THRESHOLD
        and quality_score >= _QUALITY_THRESHOLD
        and auth_score >= _AUTH_THRESHOLD
        and continuity_score >= _CONT_THRESHOLD
        and recommendation == "approve_candidate"
    )


def _attempt_rank(result: DirectorResult) -> tuple[int, int, int, int, int, int]:
    minimum_quality = min(
        result.quality_score,
        result.telugu_authenticity_score,
        result.continuity_score,
    )
    combined = (
        result.quality_score + result.telugu_authenticity_score + result.continuity_score + result.narrative_score
    )
    return (
        1 if not result.hard_failures else 0,
        1 if result.approved_for_scene_planning else 0,
        result.narrative_score,
        minimum_quality,
        combined,
        -len(result.remaining_issues),
    )


def direct_script(
    script: StoryScript | HumanizedScript,
    blueprint: StoryBlueprint,
    provider_name: str | None = None,
    max_attempts: int = 3,
) -> DirectorResult:
    from workers.blueprint_validator import validate_blueprint
    from workers.config import SCRIPT_DIRECTOR_PROVIDER
    from workers.narrative_facts import extract_narrative_facts
    from workers.narrative_validator import validate_narrative
    from workers.providers import get_text_provider
    from workers.script_generator import generate_script
    from workers.script_quality import validate_script
    from workers.story_continuity import check_continuity
    from workers.telugu_quality import check_telugu_quality

    provider_name = provider_name or SCRIPT_DIRECTOR_PROVIDER
    provider = get_text_provider(provider_name)
    blueprint_validation = validate_blueprint(blueprint)
    if not blueprint_validation.passed:
        raise ValueError(
            f"Blueprint failed validation: {', '.join(blueprint_validation.hard_failures)}"
        )

    system_prompt = _load_director_prompt()
    current_text = script.full_script_telugu
    source_facts = extract_narrative_facts(script, blueprint)
    source_narrative = validate_narrative(blueprint, source_facts, script.hook_line)
    source_quality = validate_script(script)
    source_telugu = check_telugu_quality(script.full_script_telugu)
    source_continuity = check_continuity(script)
    source_issues = (
        source_narrative.hard_failures
        + source_narrative.issues
        + source_quality.issues[:3]
        + source_telugu.english_word_issues[:2]
    )

    initial_recommendation = (
        "approve_candidate" if not source_narrative.hard_failures and source_quality.publish_recommendation == "approve_candidate"
        else source_quality.publish_recommendation
    )
    best = DirectorResult(
        directed_script=current_text,
        blueprint_id=blueprint.id,
        quality_score=source_quality.quality_score,
        telugu_authenticity_score=source_telugu.telugu_authenticity_score,
        continuity_score=source_continuity.continuity_score,
        narrative_score=source_narrative.score,
        hard_failures=source_narrative.hard_failures[:],
        narrative_facts=source_facts.model_dump(),
        issues_fixed=[],
        remaining_issues=source_issues[:],
        recommendation=initial_recommendation if not source_narrative.hard_failures else "needs_rewrite",
        approved_for_scene_planning=False,
        attempts=0,
        provider_name=provider_name,
    )
    best.approved_for_scene_planning = _approval(
        blueprint_passed=blueprint_validation.passed,
        recommendation=best.recommendation,
        narrative_score=best.narrative_score,
        hard_failures=best.hard_failures,
        quality_score=best.quality_score,
        auth_score=best.telugu_authenticity_score,
        continuity_score=best.continuity_score,
    )

    original_issue_set = set(source_issues)

    for attempt in range(1, max_attempts + 1):
        if provider_name == "mock":
            candidate_text = generate_script(blueprint, provider="mock").full_script_telugu
        else:
            prompt = _build_director_prompt(blueprint, current_text, source_issues, system_prompt)
            candidate_text = provider.generate_text(prompt)
        if not candidate_text.strip():
            continue

        q, auth, cont, narrative_score, issues, facts = _evaluate_attempt(candidate_text, script, blueprint)
        recommendation = "approve_candidate" if not any(code in issues for code in source_narrative.hard_failures) and q >= _QUALITY_THRESHOLD else "needs_rewrite"
        hard_failures = [issue for issue in issues if issue.isupper() and "_" in issue]
        approved = _approval(
            blueprint_passed=blueprint_validation.passed,
            recommendation=recommendation,
            narrative_score=narrative_score,
            hard_failures=hard_failures,
            quality_score=q,
            auth_score=auth,
            continuity_score=cont,
        )
        candidate = DirectorResult(
            directed_script=candidate_text,
            blueprint_id=blueprint.id,
            quality_score=q,
            telugu_authenticity_score=auth,
            continuity_score=cont,
            narrative_score=narrative_score,
            hard_failures=hard_failures,
            narrative_facts=facts,
            issues_fixed=sorted(original_issue_set - set(issues)),
            remaining_issues=issues,
            recommendation="approve_candidate" if approved else "needs_rewrite",
            approved_for_scene_planning=approved,
            attempts=attempt,
            provider_name=provider_name,
        )

        if _attempt_rank(candidate) > _attempt_rank(best):
            best = candidate

        current_text = candidate_text
        source_issues = issues
        if approved:
            break

    return best


def save_directed_script(
    result: DirectorResult,
    script: StoryScript | HumanizedScript,
    output_dir: Path,
) -> tuple[DirectedScript, Path]:
    from workers.io_utils import write_json

    output_dir.mkdir(parents=True, exist_ok=True)

    ds = DirectedScript(
        id=f"directed_{uuid.uuid4().hex[:8]}",
        source_script_id=script.id,
        blueprint_id=result.blueprint_id,
        title=script.title,
        category=script.category,
        hook_line=script.hook_line,
        directed_telugu_script=result.directed_script,
        director_provider=result.provider_name,
        narrative_score=result.narrative_score,
        hard_failures=result.hard_failures,
        narrative_facts=result.narrative_facts,
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
