"""Pydantic models for founder profile and feedback."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


# ── Profile models ──────────────────────────────────────────────


class FundingStage(str, Enum):
    PRE_SEED = "pre_seed"
    SEED = "seed"
    SERIES_A = "series_a"
    SERIES_B = "series_b"
    SERIES_C = "series_c"
    SERIES_D_PLUS = "series_d_plus"


class RiskTolerance(str, Enum):
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"


class CompanyContext(BaseModel):
    name: str = ""
    stage: Optional[FundingStage] = None
    sector: str = ""
    current_round: str = ""
    previous_rounds: list[str] = Field(default_factory=list)


class LegalPriorities(BaseModel):
    high_priority_areas: list[str] = Field(default_factory=list)
    custom_watchlist: list[str] = Field(default_factory=list)
    known_concerns: str = ""


class DealContext(BaseModel):
    investor_names: list[str] = Field(default_factory=list)
    lead_investor: str = ""
    deal_size: str = ""
    pre_money_valuation: str = ""


class DealProfile(BaseModel):
    """Deal-specific context that overlays the base profile."""

    name: str
    deal_context: DealContext = Field(default_factory=DealContext)
    extra_watchlist: list[str] = Field(default_factory=list)


class FounderProfile(BaseModel):
    company: CompanyContext = Field(default_factory=CompanyContext)
    priorities: LegalPriorities = Field(default_factory=LegalPriorities)
    risk_tolerance: RiskTolerance = RiskTolerance.BALANCED
    deal_context: DealContext = Field(default_factory=DealContext)
    priority_overrides: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Document-type-specific priority overrides (e.g. 'term_sheet': ['valuation basis'])",
    )


# ── Feedback models ─────────────────────────────────────────────


class FeedbackItem(BaseModel):
    document_name: str = ""
    model_used: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    missed_items: list[str] = Field(default_factory=list)
    false_positives: list[str] = Field(default_factory=list)
    additional_concerns: str = ""
    overall_rating: Optional[int] = Field(default=None, ge=1, le=5)


class FeedbackStore(BaseModel):
    items: list[FeedbackItem] = Field(default_factory=list)


class FeedbackSummary(BaseModel):
    """Aggregated feedback patterns computed from FeedbackStore."""

    frequently_missed: dict[str, int] = Field(default_factory=dict)
    frequently_over_flagged: dict[str, int] = Field(default_factory=dict)
    avg_rating: Optional[float] = None
    total_sessions: int = 0


# ── Per-finding feedback from HTML report ───────────────────────


class FindingVote(BaseModel):
    """A single thumbs-up/down vote on a finding from the HTML report."""

    section_id: str
    finding_index: int
    finding_title: str
    vote: Literal["up", "down"] = Field(description="'up' or 'down'")


class ReportFeedback(BaseModel):
    """Feedback exported from the HTML report's per-finding buttons."""

    document_name: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    votes: list[FindingVote] = Field(default_factory=list)


# ── Learning / Knowledge Base models ──────────────────────────


class LearningCategory(str, Enum):
    CLAUSE_PATTERN = "clause_pattern"
    NEGOTIATION = "negotiation"
    RED_FLAG = "red_flag"
    DECISION = "decision"
    MARKET_INSIGHT = "market_insight"
    GENERAL = "general"


class LearningSource(str, Enum):
    AUTO_ANALYSIS = "auto_analysis"
    AUTO_FEEDBACK = "auto_feedback"
    MANUAL = "manual"
    IMPORT = "import"


class LearningEntry(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex[:8])
    title: str
    insight: str
    category: LearningCategory = LearningCategory.GENERAL
    source: LearningSource = LearningSource.MANUAL
    tags: list[str] = Field(default_factory=list)
    section_ids: list[str] = Field(default_factory=list)
    founder_action: str = ""
    document_name: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    useful_count: int = 0


class LearningsStore(BaseModel):
    entries: list[LearningEntry] = Field(default_factory=list)


class LearningSummary(BaseModel):
    """Compact summary for prompt injection and sharing."""

    total_entries: int = 0
    by_category: dict[str, int] = Field(default_factory=dict)
    top_tags: list[str] = Field(default_factory=list)
    most_useful: list[str] = Field(default_factory=list)
