"""Analytics tracker — manual CSV-based performance recording for v1."""

from __future__ import annotations

from workers.config import PERFORMANCE_CSV, PERFORMANCE_CSV_HEADERS
from workers.io_utils import append_csv_row, ensure_csv
from workers.models import PerformanceRecord


def record_performance(record: PerformanceRecord) -> None:
    """Append a manual performance record to analytics/performance.csv."""
    ensure_csv(PERFORMANCE_CSV, PERFORMANCE_CSV_HEADERS)
    append_csv_row(
        PERFORMANCE_CSV,
        {
            "video_id": record.video_id,
            "date": record.date,
            "views": record.views,
            "likes": record.likes,
            "comments": record.comments,
            "shares": record.shares,
            "average_view_duration": record.average_view_duration,
            "retention_percentage": record.retention_percentage,
            "subscribers_gained": record.subscribers_gained,
            "notes": record.notes,
        },
        PERFORMANCE_CSV_HEADERS,
    )
