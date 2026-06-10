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
) -> str:
    """Generate a human-readable Markdown review file."""
    youtube_hashtags = youtube_hashtags or []
    score_breakdown = score_breakdown or {}
    repeatability_warnings = repeatability_warnings or []

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

    repeat_md = ""
    if repeatability_warnings:
        repeat_md = "\n## Repeatability Warnings\n\n"
        for w in repeatability_warnings:
            repeat_md += f"- ⚠️ {w}\n"

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
