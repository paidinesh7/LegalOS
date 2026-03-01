"""Tests for prompt_injection.py — learnings block and augmented prompts."""

from legalos.profile.schemas import (
    CompanyContext,
    DealContext,
    FeedbackItem,
    FeedbackStore,
    FounderProfile,
    LearningCategory,
    LearningEntry,
    LearningsStore,
    LegalPriorities,
    RiskTolerance,
)
from legalos.profile.prompt_injection import (
    _build_learnings_block,
    augment_section_prompt,
    build_full_system_prompt,
)


def _make_store(*entries: LearningEntry) -> LearningsStore:
    return LearningsStore(entries=list(entries))


def _make_entry(
    title: str = "Test",
    insight: str = "Test insight",
    category: LearningCategory = LearningCategory.GENERAL,
    tags: list[str] | None = None,
    section_ids: list[str] | None = None,
    useful_count: int = 0,
) -> LearningEntry:
    return LearningEntry(
        title=title,
        insight=insight,
        category=category,
        tags=tags or [],
        section_ids=section_ids or [],
        useful_count=useful_count,
    )


# ── _build_learnings_block ─────────────────────────────────────


class TestBuildLearningsBlock:
    def test_empty_store(self):
        assert _build_learnings_block(LearningsStore()) == ""

    def test_single_entry(self):
        store = _make_store(
            _make_entry(
                insight="Full ratchet is aggressive",
                category=LearningCategory.CLAUSE_PATTERN,
            )
        )
        block = _build_learnings_block(store)
        assert "<founder_learnings>" in block
        assert "</founder_learnings>" in block
        assert "1 entries across 1 categories" in block
        assert "Full ratchet is aggressive" in block

    def test_multiple_categories(self):
        store = _make_store(
            _make_entry(category=LearningCategory.CLAUSE_PATTERN, insight="cp"),
            _make_entry(category=LearningCategory.RED_FLAG, insight="rf"),
            _make_entry(category=LearningCategory.NEGOTIATION, insight="neg"),
        )
        block = _build_learnings_block(store)
        assert "3 entries across 3 categories" in block

    def test_top_tags_included(self):
        store = _make_store(
            _make_entry(tags=["anti-dilution", "board"]),
        )
        block = _build_learnings_block(store)
        assert "Top focus areas:" in block
        assert "anti-dilution" in block

    def test_limits_to_10_entries(self):
        entries = [
            _make_entry(title=f"Entry {i}", insight=f"insight {i}")
            for i in range(15)
        ]
        store = LearningsStore(entries=entries)
        block = _build_learnings_block(store)
        # Should only list 10 entries
        insight_lines = [l for l in block.split("\n") if l.strip().startswith("- [")]
        assert len(insight_lines) == 10

    def test_over_20_shows_category_breakdown(self):
        entries = [
            _make_entry(title=f"Entry {i}", insight=f"insight {i}")
            for i in range(25)
        ]
        store = LearningsStore(entries=entries)
        block = _build_learnings_block(store)
        assert "Category breakdown:" in block

    def test_sorts_by_useful_count(self):
        store = _make_store(
            _make_entry(insight="low use", useful_count=0),
            _make_entry(insight="high use", useful_count=10),
        )
        block = _build_learnings_block(store)
        lines = block.split("\n")
        # "high use" should appear before "low use"
        high_idx = next(i for i, l in enumerate(lines) if "high use" in l)
        low_idx = next(i for i, l in enumerate(lines) if "low use" in l)
        assert high_idx < low_idx


# ── build_full_system_prompt ───────────────────────────────────


class TestBuildFullSystemPrompt:
    def test_base_only(self):
        result = build_full_system_prompt("Base prompt")
        assert result == "Base prompt"

    def test_with_learnings(self):
        store = _make_store(
            _make_entry(insight="Test learning"),
        )
        result = build_full_system_prompt("Base prompt", learnings=store)
        assert "Base prompt" in result
        assert "<founder_learnings>" in result
        assert "Test learning" in result

    def test_with_all_three(self):
        profile = FounderProfile(
            company=CompanyContext(name="Acme"),
            risk_tolerance=RiskTolerance.CONSERVATIVE,
        )
        feedback = FeedbackStore(
            items=[FeedbackItem(missed_items=["board control"])]
        )
        learnings = _make_store(_make_entry(insight="learning"))
        result = build_full_system_prompt(
            "Base", profile=profile, feedback=feedback, learnings=learnings
        )
        assert "<founder_context>" in result
        assert "<past_feedback>" in result
        assert "<founder_learnings>" in result

    def test_empty_learnings_no_block(self):
        result = build_full_system_prompt("Base", learnings=LearningsStore())
        assert "<founder_learnings>" not in result

    def test_none_learnings_no_block(self):
        result = build_full_system_prompt("Base", learnings=None)
        assert "<founder_learnings>" not in result


# ── augment_section_prompt ─────────────────────────────────────


class TestAugmentSectionPrompt:
    def test_no_profile_no_learnings(self):
        result = augment_section_prompt("Base", None, "control_provisions")
        assert result == "Base"

    def test_with_learnings_matching_section(self):
        store = _make_store(
            _make_entry(
                insight="Board control is crucial",
                section_ids=["control_provisions"],
            )
        )
        result = augment_section_prompt(
            "Base", None, "control_provisions", learnings=store
        )
        assert "<section_learnings>" in result
        assert "Board control is crucial" in result

    def test_with_learnings_no_match(self):
        store = _make_store(
            _make_entry(
                insight="Board control is crucial",
                section_ids=["control_provisions"],
            )
        )
        result = augment_section_prompt(
            "Base", None, "financial_terms", learnings=store
        )
        # No match by section_id, and no keyword match either
        # (depends on whether "board control" matches financial_terms keywords)
        # financial_terms keywords are: valuation, investment, tranche, etc.
        assert "<section_learnings>" not in result

    def test_learnings_fuzzy_keyword_match(self):
        store = _make_store(
            _make_entry(
                insight="Anti-dilution ratchet protection",
                tags=["anti-dilution", "ratchet"],
                # No direct section_ids match
            )
        )
        result = augment_section_prompt(
            "Base", None, "capital_structure", learnings=store
        )
        # capital_structure keywords include "anti-dilution" and "ratchet"
        assert "<section_learnings>" in result

    def test_max_5_section_learnings(self):
        entries = [
            _make_entry(
                insight=f"Insight {i}",
                section_ids=["control_provisions"],
            )
            for i in range(10)
        ]
        store = LearningsStore(entries=entries)
        result = augment_section_prompt(
            "Base", None, "control_provisions", learnings=store
        )
        insight_lines = [
            l for l in result.split("\n")
            if l.strip().startswith("- ") and "Insight" in l
        ]
        assert len(insight_lines) <= 5

    def test_profile_and_learnings_combined(self):
        profile = FounderProfile(
            priorities=LegalPriorities(
                high_priority_areas=["Board control"],
                custom_watchlist=["Veto rights on fundraising"],
            )
        )
        store = _make_store(
            _make_entry(
                insight="Watch for board majority clauses",
                section_ids=["control_provisions"],
            )
        )
        result = augment_section_prompt(
            "Base", profile, "control_provisions", learnings=store
        )
        assert "<priority_reminder>" in result
        assert "<section_learnings>" in result
        assert "Board control" in result
        assert "Watch for board majority clauses" in result
