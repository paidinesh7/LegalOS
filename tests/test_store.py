"""Tests for store.py — learnings CRUD, search, summary, export, import."""

import json
from pathlib import Path

import pytest

from legalos.profile.schemas import (
    LearningCategory,
    LearningEntry,
    LearningSummary,
    LearningSource,
    LearningsStore,
)
from legalos.profile.store import (
    append_learning,
    clear_learnings,
    compute_learning_summary,
    delete_learning,
    export_learnings_markdown,
    import_learnings,
    load_learnings,
    search_learnings,
    update_learning,
)


@pytest.fixture
def legalos_dir(tmp_path: Path) -> Path:
    d = tmp_path / ".legalos"
    d.mkdir()
    return d


@pytest.fixture
def sample_entry() -> LearningEntry:
    return LearningEntry(
        title="Full ratchet is aggressive",
        insight="Weighted anti-dilution is standard at Series A — full ratchet is aggressive",
        category=LearningCategory.CLAUSE_PATTERN,
        source=LearningSource.AUTO_ANALYSIS,
        tags=["anti-dilution", "series-a"],
        section_ids=["capital_structure"],
        document_name="SHA.pdf",
    )


@pytest.fixture
def populated_store(legalos_dir: Path, sample_entry: LearningEntry) -> LearningsStore:
    """Create a store with 3 entries for search/summary tests."""
    entries = [
        sample_entry,
        LearningEntry(
            title="Pushed back on drag-along threshold",
            insight="Successfully pushed back on drag-along threshold below 75%",
            category=LearningCategory.NEGOTIATION,
            source=LearningSource.MANUAL,
            tags=["drag-along"],
            section_ids=["investor_rights"],
            founder_action="Got threshold raised to 75%",
        ),
        LearningEntry(
            title="Deemed liquidation without consent",
            insight="Deemed liquidation event without founder consent seen in 2 documents",
            category=LearningCategory.RED_FLAG,
            tags=["liquidation"],
            section_ids=["key_events_exit"],
        ),
    ]
    for entry in entries:
        append_learning(entry, legalos_dir)
    return load_learnings(legalos_dir)


# ── Load / Append ──────────────────────────────────────────────


class TestLoadLearnings:
    def test_empty_when_no_file(self, legalos_dir: Path):
        store = load_learnings(legalos_dir)
        assert len(store.entries) == 0

    def test_empty_on_corrupt_file(self, legalos_dir: Path):
        (legalos_dir / "learnings.json").write_text("not json")
        store = load_learnings(legalos_dir)
        assert len(store.entries) == 0


class TestAppendLearning:
    def test_creates_file(self, legalos_dir: Path, sample_entry: LearningEntry):
        path = append_learning(sample_entry, legalos_dir)
        assert path.exists()
        store = load_learnings(legalos_dir)
        assert len(store.entries) == 1
        assert store.entries[0].title == sample_entry.title

    def test_appends_to_existing(self, legalos_dir: Path, sample_entry: LearningEntry):
        append_learning(sample_entry, legalos_dir)
        e2 = LearningEntry(title="Second", insight="Second insight")
        append_learning(e2, legalos_dir)
        store = load_learnings(legalos_dir)
        assert len(store.entries) == 2


# ── Update ─────────────────────────────────────────────────────


class TestUpdateLearning:
    def test_update_existing(self, legalos_dir: Path, sample_entry: LearningEntry):
        append_learning(sample_entry, legalos_dir)
        updated = update_learning(
            sample_entry.id, {"title": "Updated Title", "useful_count": 5}, legalos_dir
        )
        assert updated is not None
        assert updated.title == "Updated Title"
        assert updated.useful_count == 5
        # Verify persisted
        store = load_learnings(legalos_dir)
        assert store.entries[0].title == "Updated Title"

    def test_update_nonexistent(self, legalos_dir: Path, sample_entry: LearningEntry):
        append_learning(sample_entry, legalos_dir)
        result = update_learning("nonexistent", {"title": "X"}, legalos_dir)
        assert result is None

    def test_update_category(self, legalos_dir: Path, sample_entry: LearningEntry):
        append_learning(sample_entry, legalos_dir)
        updated = update_learning(
            sample_entry.id,
            {"category": LearningCategory.RED_FLAG},
            legalos_dir,
        )
        assert updated is not None
        assert updated.category == LearningCategory.RED_FLAG


# ── Delete ─────────────────────────────────────────────────────


class TestDeleteLearning:
    def test_delete_existing(self, legalos_dir: Path, sample_entry: LearningEntry):
        append_learning(sample_entry, legalos_dir)
        assert delete_learning(sample_entry.id, legalos_dir) is True
        store = load_learnings(legalos_dir)
        assert len(store.entries) == 0

    def test_delete_nonexistent(self, legalos_dir: Path, sample_entry: LearningEntry):
        append_learning(sample_entry, legalos_dir)
        assert delete_learning("nonexistent", legalos_dir) is False
        store = load_learnings(legalos_dir)
        assert len(store.entries) == 1

    def test_delete_one_of_many(self, legalos_dir: Path):
        e1 = LearningEntry(title="A", insight="a")
        e2 = LearningEntry(title="B", insight="b")
        append_learning(e1, legalos_dir)
        append_learning(e2, legalos_dir)
        delete_learning(e1.id, legalos_dir)
        store = load_learnings(legalos_dir)
        assert len(store.entries) == 1
        assert store.entries[0].id == e2.id


# ── Clear ──────────────────────────────────────────────────────


class TestClearLearnings:
    def test_clear_existing(self, legalos_dir: Path, sample_entry: LearningEntry):
        append_learning(sample_entry, legalos_dir)
        assert clear_learnings(legalos_dir) is True
        store = load_learnings(legalos_dir)
        assert len(store.entries) == 0

    def test_clear_nonexistent(self, legalos_dir: Path):
        assert clear_learnings(legalos_dir) is False


# ── Search ─────────────────────────────────────────────────────


class TestSearchLearnings:
    def test_search_by_query(self, populated_store: LearningsStore):
        results = search_learnings(populated_store, query="anti-dilution")
        assert len(results) == 1
        assert "anti-dilution" in results[0].title.lower() or "anti-dilution" in results[0].insight.lower()

    def test_search_by_category(self, populated_store: LearningsStore):
        results = search_learnings(populated_store, category="negotiation")
        assert len(results) == 1
        assert results[0].category == LearningCategory.NEGOTIATION

    def test_search_by_section_id_direct(self, populated_store: LearningsStore):
        results = search_learnings(populated_store, section_id="capital_structure")
        assert len(results) >= 1
        # The sample entry has capital_structure in section_ids
        titles = [r.title for r in results]
        assert "Full ratchet is aggressive" in titles

    def test_search_by_section_id_fuzzy(self, populated_store: LearningsStore):
        """Section keyword matching should find entries by tag/content even without direct section_ids."""
        results = search_learnings(populated_store, section_id="investor_rights")
        assert len(results) >= 1

    def test_search_no_results(self, populated_store: LearningsStore):
        results = search_learnings(populated_store, query="nonexistent_term_xyz")
        assert len(results) == 0

    def test_search_combined_filters(self, populated_store: LearningsStore):
        results = search_learnings(
            populated_store, query="drag", category="negotiation"
        )
        assert len(results) == 1

    def test_search_empty_store(self):
        store = LearningsStore()
        results = search_learnings(store, query="anything")
        assert len(results) == 0

    def test_search_all(self, populated_store: LearningsStore):
        results = search_learnings(populated_store)
        assert len(results) == 3


# ── Summary ────────────────────────────────────────────────────


class TestComputeLearningSummary:
    def test_empty_store(self):
        summary = compute_learning_summary(LearningsStore())
        assert summary.total_entries == 0
        assert summary.by_category == {}

    def test_populated_store(self, populated_store: LearningsStore):
        summary = compute_learning_summary(populated_store)
        assert summary.total_entries == 3
        assert "clause_pattern" in summary.by_category
        assert "negotiation" in summary.by_category
        assert "red_flag" in summary.by_category
        assert len(summary.top_tags) > 0
        assert len(summary.most_useful) > 0

    def test_top_tags(self, populated_store: LearningsStore):
        summary = compute_learning_summary(populated_store)
        # All three entries have different tags
        assert "anti-dilution" in summary.top_tags
        assert "drag-along" in summary.top_tags
        assert "liquidation" in summary.top_tags


# ── Markdown Export ────────────────────────────────────────────


class TestExportLearningsMarkdown:
    def test_empty_store(self):
        md = export_learnings_markdown(LearningsStore())
        assert "# Legal Knowledge Base" in md

    def test_populated_store(self, populated_store: LearningsStore):
        md = export_learnings_markdown(populated_store)
        assert "# Legal Knowledge Base" in md
        assert "## Clause Patterns" in md
        assert "## Negotiation Outcomes" in md
        assert "## Red Flags" in md
        assert "anti-dilution" in md
        assert "Exported from LegalOS" in md

    def test_negotiation_table_format(self, populated_store: LearningsStore):
        md = export_learnings_markdown(populated_store)
        # Negotiation section uses table format
        assert "What We Pushed Back On" in md
        assert "Result" in md
        assert "Document" in md


# ── Import ─────────────────────────────────────────────────────


class TestImportLearnings:
    def test_import_new(self, legalos_dir: Path, tmp_path: Path):
        entries = [
            LearningEntry(title="Imported A", insight="insight A"),
            LearningEntry(title="Imported B", insight="insight B"),
        ]
        import_store = LearningsStore(entries=entries)
        import_file = tmp_path / "import.json"
        import_file.write_text(import_store.model_dump_json(indent=2))

        count = import_learnings(import_file, legalos_dir)
        assert count == 2
        store = load_learnings(legalos_dir)
        assert len(store.entries) == 2

    def test_import_deduplicates(self, legalos_dir: Path, tmp_path: Path):
        # Pre-populate
        append_learning(
            LearningEntry(title="Existing Entry", insight="already here"),
            legalos_dir,
        )

        # Import with one duplicate and one new
        entries = [
            LearningEntry(title="Existing Entry", insight="duplicate"),
            LearningEntry(title="New Entry", insight="new"),
        ]
        import_store = LearningsStore(entries=entries)
        import_file = tmp_path / "import.json"
        import_file.write_text(import_store.model_dump_json(indent=2))

        count = import_learnings(import_file, legalos_dir)
        assert count == 1  # Only the new one
        store = load_learnings(legalos_dir)
        assert len(store.entries) == 2

    def test_import_sets_source(self, legalos_dir: Path, tmp_path: Path):
        entries = [
            LearningEntry(
                title="From Friend",
                insight="friend's insight",
                source=LearningSource.MANUAL,
            )
        ]
        import_store = LearningsStore(entries=entries)
        import_file = tmp_path / "import.json"
        import_file.write_text(import_store.model_dump_json(indent=2))

        import_learnings(import_file, legalos_dir)
        store = load_learnings(legalos_dir)
        assert store.entries[0].source == LearningSource.IMPORT

    def test_import_case_insensitive_dedup(self, legalos_dir: Path, tmp_path: Path):
        append_learning(
            LearningEntry(title="Board Control", insight="x"),
            legalos_dir,
        )
        entries = [LearningEntry(title="board control", insight="y")]
        import_store = LearningsStore(entries=entries)
        import_file = tmp_path / "import.json"
        import_file.write_text(import_store.model_dump_json(indent=2))

        count = import_learnings(import_file, legalos_dir)
        assert count == 0
