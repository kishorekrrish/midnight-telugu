"""Review queue — create, approve, and reject draft review packages."""

from __future__ import annotations

import shutil
import uuid
from datetime import UTC, datetime
from pathlib import Path

from workers.config import APPROVED_DIR, REVIEW_DIR, VIDEOS_CSV, VIDEOS_CSV_HEADERS
from workers.io_utils import append_csv_row, update_csv_field, write_json
from workers.models import (
    ReviewChecklist,
    ReviewStatus,
    ReviewStatusEnum,
)


def _has_hard_safety_issue(script_quality: dict) -> bool:
    return any(
        "Monetization risk" in issue or "real-person" in issue.lower()
        for issue in script_quality.get("issues", [])
    )


def _has_banned_ending(script_quality: dict) -> bool:
    return any("Banned ending pattern found" in issue for issue in script_quality.get("issues", []))


def _has_blocking_english_issues(telugu_quality: dict) -> bool:
    return bool(telugu_quality.get("english_word_issues") or telugu_quality.get("suggested_replacements"))


def _final_publish_recommendation(
    script_quality: dict,
    telugu_quality: dict,
    continuity: dict,
    directed_script_info: dict | None,
) -> tuple[str, str]:
    hard_block = _has_hard_safety_issue(script_quality)
    banned_ending = _has_banned_ending(script_quality)
    english_block = _has_blocking_english_issues(telugu_quality)

    if directed_script_info:
        strict_failures = [
            directed_script_info.get("recommendation") != "approve_candidate",
            not bool(directed_script_info.get("approved_for_scene_planning")),
            directed_script_info.get("quality_score", 0) < 88,
            directed_script_info.get("telugu_authenticity_score", 0) < 90,
            directed_script_info.get("continuity_score", 0) < 90,
            english_block,
            banned_ending,
            hard_block,
        ]
        if any(strict_failures):
            return (
                "needs_script_rewrite",
                "🟡 **NEEDS SCRIPT REWRITE** — DirectedScript failed the strict Script Director gate.",
            )
        return (
            "draft_ready_for_human_review",
            "🟢 **DRAFT READY FOR HUMAN REVIEW** — DirectedScript passed the strict Script Director gate.",
        )

    if hard_block:
        return ("reject", "🔴 **REJECT** — Hard safety block found. Do not publish.")

    final_quality = script_quality.get("quality_score", 0)
    final_continuity = continuity.get("continuity_score", 0)
    if final_quality >= 75 and final_continuity >= 65 and not banned_ending and not english_block:
        return (
            "draft_ready_for_human_review",
            "🟢 **DRAFT READY FOR HUMAN REVIEW** — Human review is still mandatory.",
        )

    return (
        "needs_script_rewrite",
        "🟡 **NEEDS SCRIPT REWRITE** — Improve the script and re-run the pipeline.",
    )


def _build_review_markdown(
    review: ReviewStatus,
    script_text: str = "",
    scene_table: str = "",
    english_summary: str = "",
    thumbnail_idea: str = "",
    youtube_title: str = "",
    youtube_description: str = "",
    youtube_hashtags: list[str] | None = None,
    score_breakdown: dict | None = None,
    repeatability_warnings: list[str] | None = None,
    script_quality: dict | None = None,
    telugu_quality: dict | None = None,
    continuity: dict | None = None,
    directed_script_info: dict | None = None,
    script_source: str = "generated",
) -> str:
    """Generate a human-readable Markdown review file."""
    youtube_hashtags = youtube_hashtags or []
    score_breakdown = score_breakdown or {}
    repeatability_warnings = repeatability_warnings or []
    script_quality = script_quality or {}
    telugu_quality = telugu_quality or {}
    continuity = continuity or {}

    checklist = review.checklist
    safety_items = [
        ("strong_first_3_seconds", "Strong first 3 seconds", checklist.strong_first_3_seconds),
        ("original_story", "Original story", checklist.original_story),
        ("no_copied_plot", "No copied plot", checklist.no_copied_plot),
        ("natural_telugu", "Natural Telugu", checklist.natural_telugu),
        ("family_safe", "Family safe", checklist.family_safe),
        ("monetization_safe", "Monetization safe", checklist.monetization_safe),
        ("no_graphic_violence", "No graphic violence", checklist.no_graphic_violence),
        ("no_political_or_religious_controversy", "No political/religious controversy",
         checklist.no_political_or_religious_controversy),
        ("no_auto_publish", "No auto-publish", checklist.no_auto_publish),
        ("visual_consistency", "Visual consistency", checklist.visual_consistency),
        ("audio_quality_ok", "Audio quality OK", checklist.audio_quality_ok),
        ("subtitles_ok", "Subtitles OK", checklist.subtitles_ok),
        ("final_human_review_required", "Final human review required",
         checklist.final_human_review_required),
    ]

    checklist_md = "\n".join(
        f"- [{'x' if val else ' '}] {label}" for _, label, val in safety_items
    )

    score_md = ""
    if score_breakdown:
        score_md = "\n## Quality Score\n\n"
        for k, v in score_breakdown.items():
            score_md += f"- **{k.replace('_', ' ').title()}**: {v}\n"

    sq_md = ""
    if script_quality:
        sq = script_quality
        passed_icon = "✅" if sq.get("passed") else "❌"
        rec = sq.get("publish_recommendation", "needs_rewrite")
        rec_icons = {
            "approve_candidate": "🟢 Approve Candidate",
            "needs_rewrite": "🟡 Needs Rewrite",
            "reject": "🔴 Reject",
        }
        sq_md = "\n## Script Quality Validation\n\n"
        sq_md += f"**Result:** {passed_icon} {'PASS' if sq.get('passed') else 'FAIL'} — Score: {sq.get('quality_score', 0)}/100\n\n"
        sq_md += f"**Publish Recommendation:** {rec_icons.get(rec, rec)}\n\n"
        if sq.get("issues"):
            sq_md += "**Issues:**\n"
            for issue in sq["issues"]:
                sq_md += f"- ⚠️ {issue}\n"
            sq_md += "\n"
        if sq.get("suggestions"):
            sq_md += "**Suggestions:**\n"
            for s in sq["suggestions"]:
                sq_md += f"- 💡 {s}\n"
            sq_md += "\n"

    # ── Telugu Authenticity section ───────────────────────────────────────
    auth_md = ""
    if telugu_quality:
        auth_score = telugu_quality.get("telugu_authenticity_score", 100)
        auth_icon = "✅" if auth_score >= 70 else "⚠️"
        auth_md = "\n## Telugu Authenticity Check\n\n"
        auth_md += f"**Score:** {auth_icon} {auth_score}/100\n\n"
        replacements = telugu_quality.get("suggested_replacements", [])
        if replacements:
            auth_md += "**English Word Replacements:**\n\n"
            auth_md += "| Found | Suggested Telugu |\n|-------|------------------|\n"
            for rep in replacements[:8]:
                auth_md += f"| `{rep.get('found', '')}` | {rep.get('replace_with', '')} |\n"
            auth_md += "\n"
        if telugu_quality.get("suggestions"):
            for s in telugu_quality["suggestions"][:2]:
                auth_md += f"- 💡 {s}\n"
            auth_md += "\n"

    # ── Continuity section ────────────────────────────────────────────────
    cont_md = ""
    if continuity:
        cont_score = continuity.get("continuity_score", 100)
        cont_icon = "✅" if cont_score >= 65 else "⚠️"
        cont_md = "\n## Continuity Check\n\n"
        cont_md += f"**Score:** {cont_icon} {cont_score}/100\n\n"
        if continuity.get("issues"):
            cont_md += "**Issues:**\n"
            for issue in continuity["issues"]:
                cont_md += f"- ⚠️ {issue}\n"
            cont_md += "\n"
        if continuity.get("suggestions"):
            cont_md += "**Suggestions:**\n"
            for s in continuity["suggestions"]:
                cont_md += f"- 💡 {s}\n"
            cont_md += "\n"

    repeat_md = ""
    if repeatability_warnings:
        repeat_md = "\n## Repeatability Warnings\n\n"
        for w in repeatability_warnings:
            repeat_md += f"- ⚠️ {w}\n"

    # ── Script Director section ───────────────────────────────────────────────
    director_md = ""
    if directed_script_info:
        di = directed_script_info
        approved_icon = "✅ Yes" if di.get("approved_for_scene_planning") else "❌ No"
        rec = di.get("recommendation", "needs_rewrite")
        rec_icons = {
            "approve_candidate": "🟢 Approve Candidate",
            "needs_rewrite": "🟡 Needs Rewrite",
            "reject": "🔴 Reject",
        }
        director_md = "\n## Script Director\n\n"
        director_md += f"**Provider:** {di.get('provider', 'mock')}\n\n"
        director_md += (
            f"**Scores:** Quality {di.get('quality_score', 0)}/100 | "
            f"Authenticity {di.get('telugu_authenticity_score', 0)}/100 | "
            f"Continuity {di.get('continuity_score', 0)}/100\n\n"
        )
        director_md += f"**Recommendation:** {rec_icons.get(rec, rec)}\n\n"
        director_md += f"**Approved for scene planning:** {approved_icon}\n\n"
        if di.get("issues_fixed"):
            director_md += "**Issues Fixed:**\n"
            for issue in di["issues_fixed"][:5]:
                director_md += f"- ✅ {issue}\n"
            director_md += "\n"
        if di.get("remaining_issues"):
            director_md += "**Remaining Issues:**\n"
            for issue in di["remaining_issues"][:5]:
                director_md += f"- ⚠️ {issue}\n"
            director_md += "\n"

    # ── Script Source section ─────────────────────────────────────────────────
    source_md = f"\n## Script Source\n\nScript used for this review: **{script_source}**\n"

    final_rec, final_rec_label = _final_publish_recommendation(
        script_quality=script_quality,
        telugu_quality=telugu_quality,
        continuity=continuity,
        directed_script_info=directed_script_info,
    )

    final_rec_md = f"\n## Final Publish Recommendation\n\n{final_rec_label}\n\n> `{final_rec}`\n"

    scene_section = f"\n## Scene Table\n\n{scene_table}" if scene_table else ""
    summary_section = f"\n## English Summary\n\n{english_summary}" if english_summary else ""
    thumbnail_section = f"\n## Thumbnail Idea\n\n{thumbnail_idea}" if thumbnail_idea else ""

    youtube_section = ""
    if youtube_title or youtube_description:
        youtube_section = "\n## YouTube Metadata\n\n"
        if youtube_title:
            youtube_section += f"**Title:** {youtube_title}\n\n"
        if youtube_description:
            youtube_section += f"**Description:**\n```\n{youtube_description}\n```\n\n"
        if youtube_hashtags:
            youtube_section += f"**Hashtags:** {' '.join('#' + h for h in youtube_hashtags)}\n"

    script_section = f"\n## Full Telugu Script\n\n```\n{script_text}\n```" if script_text else ""

    approve_cmd = f"python -m workers.cli approve content/review/{review.id}.json --notes \"Approved after review\""
    reject_cmd = f"python -m workers.cli reject content/review/{review.id}.json --notes \"Reason here\""

    return f"""# Review Package: {review.title}

**Review ID:** `{review.id}`
**Category:** {review.category}
**Status:** {review.status}
**Created:** {review.created_at.strftime('%Y-%m-%d %H:%M UTC')}

---

## Hook

> {review.hook}
{summary_section}
{script_section}
{scene_section}
{thumbnail_section}
{youtube_section}
{score_md}
{director_md}
{source_md}
{sq_md}
{auth_md}
{cont_md}
{repeat_md}
## Safety & Quality Checklist

{checklist_md}

---

## Asset Paths

- **Script:** `{review.script_path or 'N/A'}`
- **Scene Plan:** `{review.scene_plan_path or 'N/A'}`
- **Audio:** `{review.audio_path or 'N/A (mock)'}`
- **Video:** `{review.video_path or 'N/A (dry-run)'}`

---
{final_rec_md}

---

## Approve / Reject Commands

```bash
# Approve:
{approve_cmd}

# Reject:
{reject_cmd}
```

> ⚠️ **Approval does NOT upload to YouTube. Upload manually via YouTube Studio after approval.**
""".strip()


def create_review(
    title: str,
    category: str,
    hook: str,
    script_path: str | None = None,
    scene_plan_path: str | None = None,
    audio_path: str | None = None,
    image_paths: list[str] | None = None,
    video_path: str | None = None,
    output_dir: Path | None = None,
    # Optional enrichment data
    script_text: str = "",
    scene_table: str = "",
    english_summary: str = "",
    thumbnail_idea: str = "",
    youtube_title: str = "",
    youtube_description: str = "",
    youtube_hashtags: list[str] | None = None,
    score_breakdown: dict | None = None,
    repeatability_warnings: list[str] | None = None,
    script_quality: dict | None = None,
    telugu_quality: dict | None = None,
    continuity: dict | None = None,
    directed_script_info: dict | None = None,
    script_source: str = "generated",
) -> tuple[ReviewStatus, Path]:
    """Create a review JSON + Markdown file for a draft. Returns (ReviewStatus, markdown_path)."""
    output_dir = output_dir or REVIEW_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    review_id = f"review_{uuid.uuid4().hex[:8]}"
    review = ReviewStatus(
        id=review_id,
        title=title,
        category=category,
        hook=hook,
        script_path=script_path,
        scene_plan_path=scene_plan_path,
        audio_path=audio_path,
        image_paths=image_paths or [],
        video_path=video_path,
        status=ReviewStatusEnum.NEEDS_REVIEW,
        checklist=ReviewChecklist(),
    )

    # Save JSON
    json_path = output_dir / f"{review_id}.json"
    write_json(json_path, review)

    # Save Markdown
    md_content = _build_review_markdown(
        review=review,
        script_text=script_text,
        scene_table=scene_table,
        english_summary=english_summary,
        thumbnail_idea=thumbnail_idea,
        youtube_title=youtube_title,
        youtube_description=youtube_description,
        youtube_hashtags=youtube_hashtags or [],
        score_breakdown=score_breakdown or {},
        repeatability_warnings=repeatability_warnings or [],
        script_quality=script_quality or {},
        telugu_quality=telugu_quality or {},
        continuity=continuity or {},
        directed_script_info=directed_script_info,
        script_source=script_source,
    )
    md_path = output_dir / f"{review_id}.md"
    md_path.write_text(md_content, encoding="utf-8")

    # Register in analytics/videos.csv
    append_csv_row(
        VIDEOS_CSV,
        {
            "video_id": review_id,
            "title": title,
            "category": category,
            "hook_type": hook[:50],
            "duration_seconds": 0,
            "status": "needs_review",
            "created_at": review.created_at.isoformat(),
            "published_at": "",
            "notes": "",
        },
        VIDEOS_CSV_HEADERS,
    )

    return review, md_path


def approve_review(review_path: Path, notes: str = "", approved_dir: Path | None = None) -> ReviewStatus:
    """Mark a review as approved and copy to approved directory."""
    from workers.io_utils import read_json

    approved_dir = approved_dir or APPROVED_DIR
    approved_dir.mkdir(parents=True, exist_ok=True)

    review = read_json(review_path, ReviewStatus)
    review.status = ReviewStatusEnum.APPROVED
    review.reviewer_notes = notes
    review.updated_at = datetime.now(UTC)

    write_json(review_path, review)

    dest = approved_dir / review_path.name
    shutil.copy2(review_path, dest)

    # Also copy markdown if it exists
    md_path = review_path.with_suffix(".md")
    if md_path.exists():
        shutil.copy2(md_path, approved_dir / md_path.name)

    update_csv_field(VIDEOS_CSV, "video_id", review.id, {"status": "approved"}, VIDEOS_CSV_HEADERS)

    return review


def reject_review(review_path: Path, notes: str = "") -> ReviewStatus:
    """Mark a review as rejected."""
    from workers.io_utils import read_json

    review = read_json(review_path, ReviewStatus)
    review.status = ReviewStatusEnum.REJECTED
    review.reviewer_notes = notes
    review.updated_at = datetime.now(UTC)

    write_json(review_path, review)

    update_csv_field(VIDEOS_CSV, "video_id", review.id, {"status": "rejected"}, VIDEOS_CSV_HEADERS)

    return review
