"""Tests for story memory and repeatability detection."""

from __future__ import annotations

from workers.io_utils import write_json
from workers.models import ContentCategory, StoryIdea
from workers.story_memory import (
    _extract_location,
    _extract_relationship,
    _extract_twist_type,
    category_distribution,
    check_repeatability,
)


def _make_idea(**kwargs) -> StoryIdea:
    defaults = dict(
        id="idea_test",
        title="Test",
        category=ContentCategory.MIDNIGHT_MYSTERY,
        hook="Hook",
        premise="Premise",
        twist="Twist రహస్యం",
        tone="suspense",
    )
    defaults.update(kwargs)
    return StoryIdea(**defaults)


class TestExtractors:
    def test_extract_twist_type_escape(self):
        assert _extract_twist_type("ఆమె పారిపోయింది") == "escape_twist"

    def test_extract_twist_type_ghost(self):
        assert _extract_twist_type("అది భూతం") == "ghost_reveal"

    def test_extract_twist_unknown(self):
        assert _extract_twist_type("ఏదో జరిగింది") == "unknown_twist"

    def test_extract_location_well(self):
        assert _extract_location("పాత బావి దగ్గర") == "well"

    def test_extract_location_room(self):
        assert _extract_location("ఆ గది లో") == "room"

    def test_extract_relationship_mother(self):
        assert _extract_relationship("అమ్మ చనిపోయింది") == "mother"

    def test_extract_relationship_spouse(self):
        assert _extract_relationship("నా భార్య ఎక్కడ") == "spouse"


class TestRepeatability:
    def test_no_warnings_empty_dir(self, tmp_path):
        idea = _make_idea()
        warnings = check_repeatability(idea, scan_dirs=[tmp_path])
        assert warnings == []

    def test_category_overuse_warning(self, tmp_path):
        # Write 3 existing ideas with same category
        for i in range(3):
            existing = _make_idea(id=f"idea_{i}", title=f"Title {i}")
            p = tmp_path / f"idea_{i}.json"
            write_json(p, existing)

        new_idea = _make_idea(id="idea_new", title="New Story")
        warnings = check_repeatability(new_idea, scan_dirs=[tmp_path])
        assert any("midnight_mystery" in w or "Category" in w for w in warnings)

    def test_twist_type_repetition(self, tmp_path):
        for i in range(2):
            existing = _make_idea(
                id=f"idea_{i}",
                title=f"Title {i}",
                twist="ఆమె పారిపోయింది వేరే ఊరికి",
            )
            write_json(tmp_path / f"idea_{i}.json", existing)

        new_idea = _make_idea(
            id="idea_new",
            title="New",
            twist="అతను కూడా పారిపోయాడు వేరే ఊరికి",
        )
        warnings = check_repeatability(new_idea, scan_dirs=[tmp_path])
        assert any("escape_twist" in w or "Twist" in w for w in warnings)

    def test_no_false_positives_different_categories(self, tmp_path):
        for cat in [ContentCategory.VILLAGE_MYSTERY, ContentCategory.KARMA_JUSTICE]:
            existing = _make_idea(id=f"idea_{cat}", title=f"T {cat}", category=cat)
            write_json(tmp_path / f"idea_{cat}.json", existing)

        new_idea = _make_idea(
            id="idea_new",
            title="New Midnight",
            category=ContentCategory.MIDNIGHT_MYSTERY,
        )
        warnings = check_repeatability(new_idea, scan_dirs=[tmp_path])
        # midnight_mystery only appears once — no overuse warning
        assert not any("midnight_mystery" in w for w in warnings)


class TestCategoryDistribution:
    def test_counts_categories(self, tmp_path):
        for i, cat in enumerate([ContentCategory.MIDNIGHT_MYSTERY, ContentCategory.MIDNIGHT_MYSTERY,
                                  ContentCategory.SOFT_HORROR]):
            idea = _make_idea(id=f"idea_{i}", title=f"T{i}", category=cat)
            write_json(tmp_path / f"idea_{i}.json", idea)

        dist = category_distribution(scan_dirs=[tmp_path])
        assert dist.get("midnight_mystery", 0) == 2
        assert dist.get("soft_horror", 0) == 1

    def test_empty_dir(self, tmp_path):
        dist = category_distribution(scan_dirs=[tmp_path])
        assert dist == {}
