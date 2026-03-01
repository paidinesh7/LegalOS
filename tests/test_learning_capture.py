"""Tests for learning_capture.py — auto-capture and tag extraction."""

from pathlib import Path

import pytest

from legalos.analysis.schemas import (
    AnalysisSection,
    ExplainerOutput,
    Finding,
    FullAnalysis,
    ImpactOutput,
    ImpactScores,
    NegotiationItem,
    Severity,
    WaterfallRow,
)
from legalos.profile.schemas import (
    FeedbackItem,
    FeedbackStore,
    LearningCategory,
    LearningEntry,
    LearningSource,
    LearningsStore,
)
from legalos.profile.learning_capture import (
    _extract_tags,
    auto_capture_learnings,
)
from legalos.profile.store import load_learnings


@pytest.fixture
def legalos_dir(tmp_path: Path) -> Path:
    d = tmp_path / ".legalos"
    d.mkdir()
    return d


@pytest.fixture
def aggressive_analysis() -> FullAnalysis:
    """Analysis with aggressive findings in a high-risk section."""
    return FullAnalysis(
        document_name="test_sha.pdf",
        document_type="SHA",
        sections=[
            AnalysisSection(
                section_name="Capital Structure",
                section_id="capital_structure",
                summary="Several aggressive clauses found.",
                risk_level="high",
                findings=[
                    Finding(
                        clause_reference="Clause 5.1",
                        quoted_text="Full ratchet anti-dilution protection.",
                        title="Full Ratchet Anti-Dilution",
                        severity=Severity.AGGRESSIVE,
                        explanation="Full ratchet is more aggressive than weighted average.",
                        founder_impact="Significant founder dilution in down rounds.",
                        recommendation="Negotiate for weighted average.",
                    ),
                    Finding(
                        clause_reference="Clause 5.2",
                        quoted_text="Standard conversion ratio.",
                        title="Standard Conversion",
                        severity=Severity.STANDARD,
                        explanation="Normal conversion terms.",
                        founder_impact="Minimal impact.",
                        recommendation="No action needed.",
                    ),
                ],
            ),
            AnalysisSection(
                section_name="Control Provisions",
                section_id="control_provisions",
                summary="Standard board provisions.",
                risk_level="medium",
                findings=[
                    Finding(
                        clause_reference="Clause 3.1",
                        quoted_text="Board of 5 directors.",
                        title="Board Composition",
                        severity=Severity.AGGRESSIVE,
                        explanation="Investor-heavy board.",
                        founder_impact="Loss of board control.",
                        recommendation="Negotiate equal representation.",
                    ),
                ],
            ),
        ],
        explainer=ExplainerOutput(),
        impact=ImpactOutput(
            scores=ImpactScores(
                control_score=7,
                economics_score=5,
                flexibility_score=6,
                control_rationale="High investor control",
                economics_rationale="Standard economics",
                flexibility_rationale="Moderate restrictions",
            ),
            waterfall=[],
            top_negotiation_items=[
                NegotiationItem(
                    priority=1,
                    item="Board Composition",
                    current_language="3 investor, 2 founder",
                    suggested_change="2 investor, 2 founder, 1 independent",
                    reasoning="Founders should retain board influence.",
                ),
                NegotiationItem(
                    priority=5,
                    item="Anti-Dilution Mechanism",
                    current_language="Full ratchet",
                    suggested_change="Weighted average",
                    reasoning="Full ratchet is unusually punitive.",
                ),
                NegotiationItem(
                    priority=9,
                    item="Minor Reporting",
                    current_language="Quarterly reports",
                    suggested_change="Semi-annual reports",
                    reasoning="Reduce reporting burden.",
                ),
            ],
        ),
    )


# ── Auto-Capture ───────────────────────────────────────────────


class TestAutoCaptureFromAnalysis:
    def test_captures_aggressive_findings_in_high_risk_sections(
        self, aggressive_analysis: FullAnalysis, legalos_dir: Path
    ):
        entries = auto_capture_learnings(
            aggressive_analysis, directory=legalos_dir
        )
        # Should capture "Full Ratchet Anti-Dilution" (aggressive in high-risk section)
        # Should NOT capture "Standard Conversion" (standard severity)
        # Should NOT capture "Board Composition" (aggressive but in medium-risk section)
        titles = [e.title for e in entries]
        assert "Full Ratchet Anti-Dilution" in titles
        assert "Standard Conversion" not in titles

    def test_captures_high_priority_negotiation_items(
        self, aggressive_analysis: FullAnalysis, legalos_dir: Path
    ):
        entries = auto_capture_learnings(
            aggressive_analysis, directory=legalos_dir
        )
        titles = [e.title for e in entries]
        # Priority 1 and 5 should be captured (<=7)
        assert any("Board Composition" in t for t in titles)
        assert any("Anti-Dilution" in t for t in titles)
        # Priority 9 should NOT be captured (>7)
        assert not any("Minor Reporting" in t for t in titles)

    def test_negotiation_entries_have_correct_category(
        self, aggressive_analysis: FullAnalysis, legalos_dir: Path
    ):
        entries = auto_capture_learnings(
            aggressive_analysis, directory=legalos_dir
        )
        negotiation_entries = [
            e for e in entries if e.category == LearningCategory.NEGOTIATION
        ]
        assert len(negotiation_entries) >= 1

    def test_clause_entries_have_correct_source(
        self, aggressive_analysis: FullAnalysis, legalos_dir: Path
    ):
        entries = auto_capture_learnings(
            aggressive_analysis, directory=legalos_dir
        )
        clause_entries = [
            e for e in entries if e.category == LearningCategory.CLAUSE_PATTERN
        ]
        for e in clause_entries:
            assert e.source == LearningSource.AUTO_ANALYSIS

    def test_entries_persisted(
        self, aggressive_analysis: FullAnalysis, legalos_dir: Path
    ):
        auto_capture_learnings(aggressive_analysis, directory=legalos_dir)
        store = load_learnings(legalos_dir)
        assert len(store.entries) > 0

    def test_document_name_captured(
        self, aggressive_analysis: FullAnalysis, legalos_dir: Path
    ):
        entries = auto_capture_learnings(
            aggressive_analysis, directory=legalos_dir
        )
        for entry in entries:
            assert entry.document_name == "test_sha.pdf"


class TestAutoCaptureDeduplication:
    def test_skips_existing_titles(
        self, aggressive_analysis: FullAnalysis, legalos_dir: Path
    ):
        existing = LearningsStore(
            entries=[
                LearningEntry(
                    title="Full Ratchet Anti-Dilution",
                    insight="Already known",
                )
            ]
        )
        entries = auto_capture_learnings(
            aggressive_analysis, existing=existing, directory=legalos_dir
        )
        titles = [e.title for e in entries]
        assert "Full Ratchet Anti-Dilution" not in titles

    def test_case_insensitive_dedup(
        self, aggressive_analysis: FullAnalysis, legalos_dir: Path
    ):
        existing = LearningsStore(
            entries=[
                LearningEntry(
                    title="full ratchet anti-dilution",
                    insight="Already known",
                )
            ]
        )
        entries = auto_capture_learnings(
            aggressive_analysis, existing=existing, directory=legalos_dir
        )
        titles = [e.title for e in entries]
        assert "Full Ratchet Anti-Dilution" not in titles

    def test_no_duplicates_across_same_run(
        self, aggressive_analysis: FullAnalysis, legalos_dir: Path
    ):
        entries = auto_capture_learnings(
            aggressive_analysis, directory=legalos_dir
        )
        titles = [e.title for e in entries]
        assert len(titles) == len(set(titles))


class TestAutoCaptureFromFeedback:
    def test_captures_resolved_feedback_items(self, legalos_dir: Path):
        feedback = FeedbackStore(
            items=[
                FeedbackItem(missed_items=["board composition"]),
            ]
        )
        # Analysis with a finding matching the missed item
        analysis = FullAnalysis(
            document_name="doc.pdf",
            document_type="SHA",
            sections=[
                AnalysisSection(
                    section_name="Control",
                    section_id="control_provisions",
                    summary="Board issues found.",
                    risk_level="low",
                    findings=[
                        Finding(
                            clause_reference="1.1",
                            quoted_text="Board shall have 5 members.",
                            title="Board Composition",
                            severity=Severity.STANDARD,
                            explanation="Standard board.",
                            founder_impact="Minimal.",
                            recommendation="OK.",
                        )
                    ],
                )
            ],
        )
        entries = auto_capture_learnings(
            analysis, feedback=feedback, directory=legalos_dir
        )
        feedback_entries = [
            e for e in entries if e.source == LearningSource.AUTO_FEEDBACK
        ]
        assert len(feedback_entries) >= 1
        assert any("board composition" in e.title.lower() for e in feedback_entries)


# ── Tag Extraction ─────────────────────────────────────────────


class TestExtractTags:
    def test_extracts_known_terms(self):
        tags = _extract_tags("Full ratchet anti-dilution protection clause")
        assert "anti-dilution" in tags
        assert "ratchet" in tags

    def test_extracts_multiple(self):
        tags = _extract_tags("Board veto rights with drag-along and tag-along")
        assert "board" in tags
        assert "veto" in tags
        assert "drag-along" in tags
        assert "tag-along" in tags

    def test_empty_for_no_matches(self):
        tags = _extract_tags("This is a generic sentence about nothing legal")
        assert tags == []

    def test_case_insensitive(self):
        tags = _extract_tags("ANTI-DILUTION and BOARD control")
        assert "anti-dilution" in tags
        assert "board" in tags
