"""Tests for store.py — profile, deal, and feedback CRUD + _safe_deal_name."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from legalos.profile.schemas import (
    DealContext,
    DealProfile,
    FeedbackItem,
    FeedbackStore,
    FounderProfile,
    LearningEntry,
)
from legalos.profile.store import (
    _safe_deal_name,
    append_feedback,
    apply_deal_overlay,
    batch_append_learnings,
    clear_feedback,
    compute_feedback_summary,
    delete_deal,
    delete_profile,
    export_profile,
    import_profile,
    list_deals,
    load_deal,
    load_feedback,
    load_profile,
    save_deal,
    save_profile,
)


@pytest.fixture
def legalos_dir(tmp_path: Path) -> Path:
    d = tmp_path / ".legalos"
    d.mkdir()
    return d


@pytest.fixture
def sample_profile() -> FounderProfile:
    p = FounderProfile()
    p.company.name = "TestCo"
    p.company.sector = "SaaS"
    return p


@pytest.fixture
def sample_deal() -> DealProfile:
    return DealProfile(
        name="series-a",
        deal_context=DealContext(
            investor_names=["Sequoia", "Accel"],
            lead_investor="Sequoia",
            deal_size="$5M",
        ),
        extra_watchlist=["board control"],
    )


# ── _safe_deal_name ────────────────────────────────────────────


class TestSafeDealName:
    def test_normal_name(self):
        assert _safe_deal_name("series-a") == "series-a"

    def test_path_traversal_dots(self):
        result = _safe_deal_name("../etc")
        assert ".." not in result
        assert "/" not in result

    def test_path_traversal_slashes(self):
        result = _safe_deal_name("foo/bar")
        assert "/" not in result

    def test_backslash_traversal(self):
        result = _safe_deal_name("foo\\bar")
        assert "\\" not in result

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="Invalid deal name"):
            _safe_deal_name("")

    def test_special_chars_only(self):
        # "..." becomes "___" after sanitization (dots stripped by .replace)
        # This is valid since non-empty alphanumeric-like chars remain
        result = _safe_deal_name("...")
        assert "/" not in result
        assert "\\" not in result

    def test_only_nonalnum_raises(self):
        with pytest.raises(ValueError, match="Invalid deal name"):
            _safe_deal_name("@#$%")

    def test_preserves_alphanumeric(self):
        assert _safe_deal_name("Deal_2024-Q1") == "Deal_2024-Q1"


# ── Profile CRUD ──────────────────────────────────────────────


class TestProfileCRUD:
    def test_load_returns_none_when_missing(self, legalos_dir: Path):
        assert load_profile(legalos_dir) is None

    def test_save_and_load(self, legalos_dir: Path, sample_profile: FounderProfile):
        save_profile(sample_profile, legalos_dir)
        loaded = load_profile(legalos_dir)
        assert loaded is not None
        assert loaded.company.name == "TestCo"

    def test_delete_existing(self, legalos_dir: Path, sample_profile: FounderProfile):
        save_profile(sample_profile, legalos_dir)
        assert delete_profile(legalos_dir) is True
        assert load_profile(legalos_dir) is None

    def test_delete_nonexistent(self, legalos_dir: Path):
        assert delete_profile(legalos_dir) is False

    def test_export_and_import(self, legalos_dir: Path, tmp_path: Path, sample_profile: FounderProfile):
        save_profile(sample_profile, legalos_dir)
        export_path = tmp_path / "exported.json"
        export_profile(export_path, legalos_dir)
        assert export_path.exists()

        # Import into a fresh directory
        fresh_dir = tmp_path / ".legalos_fresh"
        fresh_dir.mkdir()
        imported = import_profile(export_path, fresh_dir)
        assert imported.company.name == "TestCo"

    def test_export_missing_profile_raises(self, legalos_dir: Path, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            export_profile(tmp_path / "out.json", legalos_dir)


# ── Deal CRUD ─────────────────────────────────────────────────


class TestDealCRUD:
    def test_list_empty(self, legalos_dir: Path):
        assert list_deals(legalos_dir) == []

    def test_save_and_list(self, legalos_dir: Path, sample_deal: DealProfile):
        save_deal(sample_deal, legalos_dir)
        deals = list_deals(legalos_dir)
        assert "series-a" in deals

    def test_load_existing(self, legalos_dir: Path, sample_deal: DealProfile):
        save_deal(sample_deal, legalos_dir)
        loaded = load_deal("series-a", legalos_dir)
        assert loaded is not None
        assert loaded.deal_context.lead_investor == "Sequoia"

    def test_load_nonexistent(self, legalos_dir: Path):
        assert load_deal("nonexistent", legalos_dir) is None

    def test_delete_existing(self, legalos_dir: Path, sample_deal: DealProfile):
        save_deal(sample_deal, legalos_dir)
        assert delete_deal("series-a", legalos_dir) is True
        assert load_deal("series-a", legalos_dir) is None

    def test_delete_nonexistent(self, legalos_dir: Path):
        assert delete_deal("nope", legalos_dir) is False

    def test_apply_deal_overlay(self, sample_profile: FounderProfile, sample_deal: DealProfile):
        merged = apply_deal_overlay(sample_profile, sample_deal)
        assert merged.deal_context.lead_investor == "Sequoia"
        assert "board control" in merged.priorities.custom_watchlist


# ── Feedback CRUD ─────────────────────────────────────────────


class TestFeedbackCRUD:
    def test_load_empty(self, legalos_dir: Path):
        store = load_feedback(legalos_dir)
        assert len(store.items) == 0

    def test_append_and_load(self, legalos_dir: Path):
        item = FeedbackItem(document_name="test.pdf", false_positives=["Board control"])
        append_feedback(item, legalos_dir)
        store = load_feedback(legalos_dir)
        assert len(store.items) == 1
        assert store.items[0].document_name == "test.pdf"

    def test_clear_existing(self, legalos_dir: Path):
        item = FeedbackItem(document_name="test.pdf")
        append_feedback(item, legalos_dir)
        assert clear_feedback(legalos_dir) is True
        store = load_feedback(legalos_dir)
        assert len(store.items) == 0

    def test_clear_nonexistent(self, legalos_dir: Path):
        assert clear_feedback(legalos_dir) is False

    def test_compute_summary_empty(self):
        summary = compute_feedback_summary(FeedbackStore())
        assert summary.total_sessions == 0

    def test_compute_summary_with_data(self, legalos_dir: Path):
        items = [
            FeedbackItem(
                document_name="a.pdf",
                missed_items=["anti-dilution", "board"],
                false_positives=["vesting"],
                overall_rating=4,
            ),
            FeedbackItem(
                document_name="b.pdf",
                missed_items=["anti-dilution"],
                false_positives=[],
                overall_rating=3,
            ),
        ]
        store = FeedbackStore(items=items)
        summary = compute_feedback_summary(store)
        assert summary.total_sessions == 2
        assert summary.avg_rating == 3.5
        assert "anti-dilution" in summary.frequently_missed


# ── Batch append learnings ────────────────────────────────────


class TestBatchAppendLearnings:
    def test_batch_empty(self, legalos_dir: Path):
        result = batch_append_learnings([], legalos_dir)
        assert result is None

    def test_batch_multiple(self, legalos_dir: Path):
        entries = [
            LearningEntry(title="A", insight="a"),
            LearningEntry(title="B", insight="b"),
        ]
        path = batch_append_learnings(entries, legalos_dir)
        assert path is not None
        assert path.exists()
        from legalos.profile.store import load_learnings
        store = load_learnings(legalos_dir)
        assert len(store.entries) == 2
