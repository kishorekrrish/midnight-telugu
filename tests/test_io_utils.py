"""Tests for I/O utilities."""

from __future__ import annotations

import csv

from workers.io_utils import (
    append_csv_row,
    ensure_csv,
    latest_file,
    read_json,
    update_csv_field,
    write_json,
)
from workers.models import ContentCategory, StoryIdea


def _make_idea(id_: str = "idea_test") -> StoryIdea:
    return StoryIdea(
        id=id_,
        title="Test",
        category=ContentCategory.MIDNIGHT_MYSTERY,
        hook="Hook",
        premise="Premise",
        twist="Twist",
        tone="suspense",
    )


class TestWriteReadJson:
    def test_round_trip(self, tmp_path):
        idea = _make_idea()
        p = tmp_path / "idea.json"
        write_json(p, idea)
        assert p.exists()
        restored = read_json(p, StoryIdea)
        assert restored.id == idea.id
        assert restored.title == idea.title

    def test_creates_parent_dirs(self, tmp_path):
        idea = _make_idea()
        p = tmp_path / "a" / "b" / "idea.json"
        write_json(p, idea)
        assert p.exists()


class TestLatestFile:
    def test_returns_none_on_empty_dir(self, tmp_path):
        assert latest_file(tmp_path) is None

    def test_returns_most_recent(self, tmp_path):
        import time
        p1 = tmp_path / "a.json"
        p1.write_text("{}")
        time.sleep(0.01)
        p2 = tmp_path / "b.json"
        p2.write_text("{}")
        result = latest_file(tmp_path)
        assert result == p2


class TestCsv:
    HEADERS = ["id", "name", "value"]

    def test_ensure_csv_creates_file(self, tmp_path):
        p = tmp_path / "test.csv"
        ensure_csv(p, self.HEADERS)
        assert p.exists()
        rows = list(csv.DictReader(p.open()))
        assert rows == []

    def test_ensure_csv_does_not_overwrite(self, tmp_path):
        p = tmp_path / "test.csv"
        ensure_csv(p, self.HEADERS)
        append_csv_row(p, {"id": "1", "name": "foo", "value": "bar"}, self.HEADERS)
        ensure_csv(p, self.HEADERS)  # should not wipe existing data
        rows = list(csv.DictReader(p.open()))
        assert len(rows) == 1

    def test_append_row(self, tmp_path):
        p = tmp_path / "test.csv"
        ensure_csv(p, self.HEADERS)
        append_csv_row(p, {"id": "1", "name": "foo", "value": "bar"}, self.HEADERS)
        rows = list(csv.DictReader(p.open()))
        assert rows[0]["name"] == "foo"

    def test_update_csv_field(self, tmp_path):
        p = tmp_path / "test.csv"
        ensure_csv(p, self.HEADERS)
        append_csv_row(p, {"id": "1", "name": "foo", "value": "bar"}, self.HEADERS)
        found = update_csv_field(p, "id", "1", {"value": "updated"}, self.HEADERS)
        assert found
        rows = list(csv.DictReader(p.open()))
        assert rows[0]["value"] == "updated"

    def test_update_csv_field_not_found(self, tmp_path):
        p = tmp_path / "test.csv"
        ensure_csv(p, self.HEADERS)
        found = update_csv_field(p, "id", "999", {"value": "x"}, self.HEADERS)
        assert not found
