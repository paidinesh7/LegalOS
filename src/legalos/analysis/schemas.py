"""Pydantic models for analysis structured output."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class Severity(str, Enum):
    STANDARD = "standard"
    AGGRESSIVE = "aggressive"
    UNUSUAL = "unusual"
    MISSING = "missing"


class Finding(BaseModel):
    """A single finding from document analysis."""

    clause_reference: str = Field(description="Clause number or section reference")
    quoted_text: str = Field(default="", description="Source text for reference")
    title: str = Field(description="Short title for the finding")
    severity: Severity = Field(default=Severity.UNUSUAL, description="How concerning this clause is for founders")
    why_it_matters: str = Field(default="", description="What this means and how it affects the founder")
    action: str = Field(default="", description="What to negotiate or do about it")

    @model_validator(mode="before")
    @classmethod
    def _migrate_old_fields(cls, values: object) -> object:
        """Backward compat: merge old field names into new ones."""
        if isinstance(values, dict):
            if "explanation" in values and "why_it_matters" not in values:
                values["why_it_matters"] = f"{values.pop('explanation', '')} {values.pop('founder_impact', '')}".strip()
            elif "explanation" in values:
                values.pop("explanation", None)
                values.pop("founder_impact", None)
            if "recommendation" in values and "action" not in values:
                values["action"] = values.pop("recommendation", "")
            elif "recommendation" in values:
                values.pop("recommendation", None)
        return values

    @field_validator("severity", mode="before")
    @classmethod
    def _coerce_severity(cls, v: object) -> str:
        """Accept partial/unknown severity strings from truncated JSON."""
        if isinstance(v, str):
            v_lower = v.strip().lower()
            for member in Severity:
                if v_lower.startswith(member.value[:3]):
                    return member.value
        return "unusual"  # Safe fallback


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


class FeedbackInsight(BaseModel):
    """An insight derived from past founder feedback."""

    source: str = Field(description="What feedback this came from")
    action: str = Field(description="What extra attention was given as a result")


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


class ExecutiveSummary(BaseModel):
    """Top-level summary for quick founder decision-making."""

    overall_risk: str = Field(description="low / medium / high / critical")
    bottom_line: str = Field(description="One paragraph: what kind of deal, biggest concern, recommendation")
    must_negotiate: list[str] = Field(default_factory=list, description="Top 3 action items")


class RedFlag(BaseModel):
    """A red flag from quick scan."""

    clause_reference: str = Field(description="Clause number")
    title: str = Field(description="Short title")
    severity: Severity = Field(default=Severity.UNUSUAL)
    what_it_says: str = Field(default="", description="1-sentence clause summary")
    why_its_a_problem: str = Field(default="", description="Why this concerns the founder")
    pushback: str = Field(default="", description="Specific counter-argument or negotiation angle")

    @field_validator("severity", mode="before")
    @classmethod
    def _coerce_severity(cls, v: object) -> str:
        """Accept partial/unknown severity strings from truncated JSON."""
        if isinstance(v, str):
            v_lower = v.strip().lower()
            for member in Severity:
                if v_lower.startswith(member.value[:3]):
                    return member.value
        return "unusual"  # Safe fallback


class QuickScanOutput(BaseModel):
    """Output from quick scan (1-2 API calls)."""

    document_name: str
    document_type: str
    overall_risk: str = Field(description="low/medium/high/critical")
    bottom_line: str = Field(description="2-3 sentences: deal posture, biggest concern, recommendation")
    red_flags: list[RedFlag] = Field(default_factory=list)
    investor_asks: list[str] = Field(default_factory=list, description="Key things investor is requesting")
    must_negotiate: list[str] = Field(default_factory=list, description="Top 3-5 pushback items")


class FullAnalysis(BaseModel):
    """Complete analysis result combining all passes."""

    document_name: str
    document_type: str = Field(description="e.g., 'Term Sheet', 'SHA', 'SSA'")
    executive_summary: Optional[ExecutiveSummary] = None
    sections: list[AnalysisSection] = Field(default_factory=list)
    explainer: ExplainerOutput = Field(default_factory=ExplainerOutput)
    impact: Optional[ImpactOutput] = None
    feedback_insights: list[FeedbackInsight] = Field(default_factory=list)
