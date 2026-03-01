"""Pydantic models for analysis structured output."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Severity(str, Enum):
    STANDARD = "standard"
    AGGRESSIVE = "aggressive"
    UNUSUAL = "unusual"
    MISSING = "missing"


class Finding(BaseModel):
    """A single finding from document analysis."""

    clause_reference: str = Field(description="Clause number or section reference")
    quoted_text: str = Field(description="Exact text from the document")
    title: str = Field(description="Short title for the finding")
    severity: Severity = Field(description="How concerning this clause is for founders")
    explanation: str = Field(description="Plain English explanation of what this means")
    founder_impact: str = Field(description="Specific impact on the founder's position")
    recommendation: str = Field(description="What the founder should negotiate or watch for")


class AnalysisSection(BaseModel):
    """Analysis results for one section (e.g., Control Provisions)."""

    section_name: str
    section_id: str = Field(description="URL-safe identifier for the section")
    summary: str = Field(description="2-3 sentence summary of this section's findings")
    risk_level: str = Field(description="Overall risk: low / medium / high / critical")
    findings: list[Finding] = Field(default_factory=list)


class TermExplanation(BaseModel):
    """Plain English explanation of a legal term."""

    term: str
    definition: str = Field(description="Plain English definition")
    real_world_example: str = Field(description="Concrete example relevant to Indian startups")
    why_it_matters: str = Field(description="Why this matters for a founder")


class ExplainerOutput(BaseModel):
    """Output from the Plain English explainer pass."""

    terms: list[TermExplanation] = Field(default_factory=list)


class ImpactScores(BaseModel):
    """Founder impact scores across three dimensions."""

    control_score: int = Field(ge=1, le=10, description="1=full founder control, 10=investor dominance")
    economics_score: int = Field(ge=1, le=10, description="1=founder-friendly, 10=investor-heavy economics")
    flexibility_score: int = Field(ge=1, le=10, description="1=full flexibility, 10=heavily restricted")
    control_rationale: str
    economics_rationale: str
    flexibility_rationale: str


class WaterfallRow(BaseModel):
    """Exit waterfall at a specific multiple."""

    exit_multiple: str = Field(description="e.g., '2x', '5x', '10x'")
    exit_valuation: str
    investor_gets: str
    founder_gets: str
    notes: str = ""


class NegotiationItem(BaseModel):
    """A top negotiation priority item."""

    priority: int = Field(ge=1, le=10)
    item: str
    current_language: str
    suggested_change: str
    reasoning: str


class ImpactOutput(BaseModel):
    """Output from the impact assessment pass."""

    scores: ImpactScores
    waterfall: list[WaterfallRow] = Field(default_factory=list)
    top_negotiation_items: list[NegotiationItem] = Field(default_factory=list)


class RedlineComment(BaseModel):
    """A single redline comment to anchor to the document."""

    target_text: str = Field(description="Exact text in the document to anchor the comment to")
    severity: Severity
    issue: str
    suggestion: str
    alternative_language: Optional[str] = None
    reasoning: str


class RedlineOutput(BaseModel):
    """Output from the redline generation pass."""

    comments: list[RedlineComment] = Field(default_factory=list)


class FullAnalysis(BaseModel):
    """Complete analysis result combining all passes."""

    document_name: str
    document_type: str = Field(description="e.g., 'Term Sheet', 'SHA', 'SSA'")
    sections: list[AnalysisSection] = Field(default_factory=list)
    explainer: ExplainerOutput = Field(default_factory=ExplainerOutput)
    impact: Optional[ImpactOutput] = None
