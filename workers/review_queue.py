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
) -> ReviewStatus:
    """Create a review metadata file for a draft."""
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

    out_path = output_dir / f"{review_id}.json"
    write_json(out_path, review)

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

    return review


def approve_review(review_path: Path, notes: str = "", approved_dir: Path | None = None) -> ReviewStatus:
    """Mark a review as approved and copy to approved directory."""
    from workers.io_utils import read_json

    approved_dir = approved_dir or APPROVED_DIR
    approved_dir.mkdir(parents=True, exist_ok=True)

    review = read_json(review_path, ReviewStatus)
    review.status = ReviewStatusEnum.APPROVED
    review.reviewer_notes = notes
    review.updated_at = datetime.now(UTC)

    # Save updated review in place
    write_json(review_path, review)

    # Copy to approved dir
    dest = approved_dir / review_path.name
    shutil.copy2(review_path, dest)

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
