"""Shared test fixtures for LegalOS."""

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
    TermExplanation,
    WaterfallRow,
)
from legalos.parsing.base import PageContent, ParsedDocument


@pytest.fixture
def sample_page() -> PageContent:
    return PageContent(page_number=1, text="This is a test legal document.")


@pytest.fixture
def sample_document(tmp_path: Path) -> ParsedDocument:
    fake_path = tmp_path / "test.pdf"
    fake_path.touch()
    return ParsedDocument(
        source_path=fake_path,
        file_type="pdf",
        pages=[
            PageContent(page_number=1, text="1. DEFINITIONS\n\n1.1 'Company' means XYZ Pvt Ltd."),
            PageContent(page_number=2, text="2. INVESTMENT\n\n2.1 The Investor shall invest INR 5,00,00,000."),
        ],
    )


@pytest.fixture
def sample_finding() -> Finding:
    return Finding(
        clause_reference="Clause 4.1",
        quoted_text="The Board shall consist of 5 directors, of which 3 shall be nominated by the Investor.",
        title="Investor-Heavy Board Composition",
        severity=Severity.AGGRESSIVE,
        explanation="Investors control the majority of board seats.",
        founder_impact="Founders lose board control from day one.",
        recommendation="Negotiate for equal or founder-majority board composition at this stage.",
    )


@pytest.fixture
def sample_analysis(sample_finding: Finding) -> FullAnalysis:
    return FullAnalysis(
        document_name="test_termsheet.pdf",
        document_type="Term Sheet",
        sections=[
            AnalysisSection(
                section_name="Control Provisions",
                section_id="control_provisions",
                summary="The term sheet gives investors significant board control.",
                risk_level="high",
                findings=[sample_finding],
            )
        ],
        explainer=ExplainerOutput(
            terms=[
                TermExplanation(
                    term="Board Composition",
                    definition="How many seats each side gets on the company's board of directors.",
                    real_world_example="If investors get 3 of 5 seats, they can outvote founders on every board decision.",
                    why_it_matters="The board approves budgets, hires CXOs, and makes strategic decisions.",
                )
            ]
        ),
        impact=ImpactOutput(
            scores=ImpactScores(
                control_score=7,
                economics_score=5,
                flexibility_score=6,
                control_rationale="Investor board majority with broad veto rights.",
                economics_rationale="Standard 1x non-participating liquidation preference.",
                flexibility_rationale="Moderate restrictions on founder transfers and outside activities.",
            ),
            waterfall=[
                WaterfallRow(
                    exit_multiple="2x",
                    exit_valuation="INR 100 Cr",
                    investor_gets="INR 50 Cr",
                    founder_gets="INR 50 Cr",
                )
            ],
            top_negotiation_items=[
                NegotiationItem(
                    priority=1,
                    item="Board Composition",
                    current_language="3 investor nominees, 2 founder nominees",
                    suggested_change="2 investor, 2 founder, 1 independent",
                    reasoning="Founders should not lose board control at early stage.",
                )
            ],
        ),
    )
