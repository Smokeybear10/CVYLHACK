"""Pydantic contracts for the survey swarm (Stage 2), per the research synthesis.

The bundle is the single source of truth and the grounding allow-list: nothing
outside it may appear in a report. The report is the strict structured output an
agent must emit. Strict models are what let the validators reject hallucinated or
malformed output.
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

Tier = Literal["Tier 1", "Tier 2", "Tier 3", "No-go"]
Rating = Literal["GO", "CAUTION", "NO-GO"]
Source = Literal["have", "partial", "verify"]


# --- shared ------------------------------------------------------------------

class SiteInfo(BaseModel):
    id: str
    lat: float
    lon: float
    street: Optional[str] = None
    region: Optional[str] = None


class Evidence(BaseModel):
    photo_ref: Optional[str] = None
    cv_findings: list[str] = Field(default_factory=list)


# --- input bundle ------------------------------------------------------------

class Measured(BaseModel):
    usable_frontage_ft: Optional[float] = None  # proxy = segment length; true value is SDK-measured
    road_width_ft: Optional[float] = None
    distance_to_power_m: Optional[float] = None
    pole_type: Optional[str] = None
    obstruction_count: int = 0
    pavement_pci: Optional[float] = None
    surface: Optional[str] = None


class Derived(BaseModel):
    composite_score: float
    tier_hint: Tier
    gated: bool = False
    gate_reasons: list[str] = Field(default_factory=list)
    rom_cost_usd: Optional[float] = None
    cost_band: Optional[str] = None
    trench_len_ft: Optional[float] = None
    residential_suit: Optional[float] = None
    traveler_suit: Optional[float] = None
    functional_class: Optional[float] = None
    ports_that_fit: Optional[int] = None
    required_frontage_ft: Optional[float] = None
    component_scores: dict[str, float] = Field(default_factory=dict)


class Public(BaseModel):
    zoning_allowed: Optional[bool] = None
    nearby_chargers: Optional[int] = None
    road_class: Optional[str] = None
    aadt: Optional[float] = None


class SiteBundle(BaseModel):
    """Everything an agent may use for one site. allowed_numbers is the grounding
    allow-list the guard checks the report against."""
    site: SiteInfo
    measured: Measured
    derived: Derived
    public: Public = Field(default_factory=Public)
    evidence: Evidence = Field(default_factory=Evidence)
    known_unknowns: list[str] = Field(default_factory=list)
    allowed_numbers: list[float] = Field(default_factory=list)


# --- output report -----------------------------------------------------------

class Verdict(BaseModel):
    tier: Tier
    composite_score: float
    one_line_reason: str


class ScoreRow(BaseModel):
    criterion: str
    value: str
    rating: Rating
    source: Source


class PhysicalFit(BaseModel):
    usable_frontage_ft: Optional[float] = None
    ports_that_fit: Optional[int] = None
    road_width_ft: Optional[float] = None
    notes: list[str] = Field(default_factory=list)


class Connection(BaseModel):
    distance_to_power_m: Optional[float] = None
    pole_type: Optional[str] = None
    trench_len_ft: Optional[float] = None
    surface: Optional[str] = None
    rom_cost_usd: Optional[float] = None
    cost_band: Optional[str] = None
    exclusions: list[str] = Field(default_factory=list)


class Demand(BaseModel):
    residential_suit: Optional[float] = None
    traveler_suit: Optional[float] = None
    functional_class: Optional[float] = None
    nearby_chargers: Optional[int] = None
    notes: list[str] = Field(default_factory=list)


class SiteConditions(BaseModel):
    pavement_pci: Optional[float] = None
    surface: Optional[str] = None
    obstruction_count: int = 0
    clearance_notes: list[str] = Field(default_factory=list)


class Accessibility(BaseModel):
    near_curb_ramp: Optional[bool] = None
    notes: list[str] = Field(default_factory=list)


class SiteReport(BaseModel):
    site: SiteInfo
    verdict: Verdict
    executive_summary: list[str] = Field(default_factory=list)
    scorecard: list[ScoreRow] = Field(default_factory=list)
    physical_fit: PhysicalFit
    connection: Connection
    demand: Demand
    site_conditions: SiteConditions
    accessibility: Accessibility
    risks_and_constraints: list[str] = Field(default_factory=list)
    to_be_verified: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    evidence: Evidence = Field(default_factory=Evidence)
    generated_by: str = "stub"  # "anthropic" | "stub" | "fallback"
