"""File I/O utilities for JSON read/write and file selection."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def write_json(path: Path, data: BaseModel) -> None:
    """Serialize a Pydantic model to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        data.model_dump_json(indent=2, exclude_none=False),
        encoding="utf-8",
    )


def read_json(path: Path, model: type[T]) -> T:
    """Deserialize a JSON file into a Pydantic model."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    return model.model_validate(raw)


def latest_file(directory: Path, pattern: str = "*.json") -> Path | None:
    """Return the most recently modified file matching pattern in directory."""
    files = sorted(directory.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def ensure_csv(path: Path, headers: list[str]) -> None:
    """Create CSV with headers if it does not exist."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)


def append_csv_row(path: Path, row: dict[str, Any], headers: list[str]) -> None:
    """Append a row to a CSV file, writing headers if file is new."""
    ensure_csv(path, headers)
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        writer.writerow(row)


def update_csv_field(path: Path, id_field: str, id_value: str, updates: dict[str, Any], headers: list[str]) -> bool:
    """Update fields in a CSV row matching id_field == id_value. Returns True if found."""
    if not path.exists():
        return False
    rows: list[dict[str, str]] = []
    found = False
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get(id_field) == id_value:
                row.update({k: str(v) for k, v in updates.items()})
                found = True
            rows.append(row)
    if found:
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
    return found


def format_datetime(dt: datetime) -> str:
    return dt.strftime("%Y%m%d_%H%M%S")
