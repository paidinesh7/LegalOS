"""Tests for profile schemas — especially learnings models."""

from legalos.profile.schemas import (
    LearningCategory,
    LearningEntry,
    LearningSummary,
    LearningSource,
    LearningsStore,
)


class TestLearningCategory:
    def test_all_values(self):
        assert LearningCategory.CLAUSE_PATTERN == "clause_pattern"
        assert LearningCategory.NEGOTIATION == "negotiation"
        assert LearningCategory.RED_FLAG == "red_flag"
        assert LearningCategory.DECISION == "decision"
        assert LearningCategory.MARKET_INSIGHT == "market_insight"
        assert LearningCategory.GENERAL == "general"

    def test_from_string(self):
        assert LearningCategory("clause_pattern") == LearningCategory.CLAUSE_PATTERN


class TestLearningSource:
    def test_all_values(self):
        assert LearningSource.AUTO_ANALYSIS == "auto_analysis"
        assert LearningSource.AUTO_FEEDBACK == "auto_feedback"
        assert LearningSource.MANUAL == "manual"
        assert LearningSource.IMPORT == "import"


class TestLearningEntry:
    def test_defaults(self):
        entry = LearningEntry(title="Test", insight="Test insight")
        assert entry.category == LearningCategory.GENERAL
        assert entry.source == LearningSource.MANUAL
        assert entry.tags == []
        assert entry.section_ids == []
        assert entry.founder_action == ""
        assert entry.document_name == ""
        assert entry.useful_count == 0
        assert len(entry.id) == 8
        assert entry.created_at  # non-empty

    def test_auto_generated_id(self):
        e1 = LearningEntry(title="A", insight="a")
        e2 = LearningEntry(title="B", insight="b")
        assert e1.id != e2.id

    def test_full_entry(self):
        entry = LearningEntry(
            title="Full ratchet is aggressive",
            insight="Weighted anti-dilution is standard at Series A",
            category=LearningCategory.CLAUSE_PATTERN,
            source=LearningSource.AUTO_ANALYSIS,
            tags=["anti-dilution", "series-a"],
            section_ids=["capital_structure"],
            founder_action="Pushed back successfully",
            document_name="SHA.pdf",
            useful_count=3,
        )
        assert entry.category == LearningCategory.CLAUSE_PATTERN
        assert entry.source == LearningSource.AUTO_ANALYSIS
        assert len(entry.tags) == 2
        assert entry.useful_count == 3


class TestLearningsStore:
    def test_empty(self):
        store = LearningsStore()
        assert store.entries == []

    def test_with_entries(self):
        entries = [
            LearningEntry(title="A", insight="a"),
            LearningEntry(title="B", insight="b"),
        ]
        store = LearningsStore(entries=entries)
        assert len(store.entries) == 2

    def test_serialization_roundtrip(self):
        entry = LearningEntry(
            title="Test",
            insight="Test insight",
            category=LearningCategory.RED_FLAG,
            tags=["tag1"],
        )
        store = LearningsStore(entries=[entry])
        json_str = store.model_dump_json()
        restored = LearningsStore.model_validate_json(json_str)
        assert len(restored.entries) == 1
        assert restored.entries[0].title == "Test"
        assert restored.entries[0].category == LearningCategory.RED_FLAG
        assert restored.entries[0].tags == ["tag1"]


class TestLearningSummary:
    def test_defaults(self):
        summary = LearningSummary()
        assert summary.total_entries == 0
        assert summary.by_category == {}
        assert summary.top_tags == []
        assert summary.most_useful == []
