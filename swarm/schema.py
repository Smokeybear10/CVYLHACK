"""Data contracts for the Sonder survey swarm.

These are the shapes we consume (SiteInput from Saim, Measurements from Max, UserPriorities
from the UI) and the shape we emit (Verdict to Thomas). Keep this file the single source of
truth for field names so the forked teams stay aligned.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Literal, Optional

VerdictLabel = Literal["go", "conditional", "no_go"]


# ---- inputs -----------------------------------------------------------------

@dataclass
class SiteInput:
    """One finalist curb segment, from Saim's Stage 1 screen."""
    site_id: str
    address: str
    lon: float
    lat: float
    score: float                       # 0-1, Stage 1 weighted score
    score_breakdown: dict[str, float]  # e.g. {"fit":0.8,"power":0.9,...}
    pavement_label: str                # Good / Fair / ...
    pavement_score: float              # PCI 0-100
    road_class: str                    # functional class / hierarchy
    aadt: Optional[int]                # traffic volume, may be None (proxy elsewhere)
    power_distance_m: float            # nearest pole/luminaire (Stage 1 estimate)
    ada_ramp_dist_m: Optional[float]
    sidewalk_condition: Optional[str]
    obstruction_count: int
    marking_flags: dict[str, bool]     # {"fire_lane":False,"no_parking":True,"bus_stop":...}
    road_width_proxy_ft: float


@dataclass
class Measurements:
    """Measured truth for one finalist, from Max's CV + SDK projection."""
    site_id: str
    usable_frontage_ft: float
    distance_to_power_m: float
    obstruction_positions: list[dict[str, Any]]   # [{"type":"hydrant","offset_ft":3.2}, ...]
    ada_clearance_ft: Optional[float]
    evidence_image_url: str            # photo with SAM3 masks drawn
    street_photo_url: str              # raw frame, for the agent's own vision pass
    measure_confidence: float          # 0-1


@dataclass
class UserPriorities:
    """Live UI settings for a run."""
    station_size: str = "curbside_l2"
    required_frontage_ft: float = 18.0          # ~5.5 m for a curbside L2 stall
    weights: dict[str, float] = field(default_factory=lambda: {"power": 1.0, "traffic": 1.0, "fit": 1.0})


# ---- output -----------------------------------------------------------------

@dataclass
class Verdict:
    """What we hand Thomas, per site."""
    site_id: str
    verdict: VerdictLabel
    confidence: float
    one_line_reason: str
    rationale: str
    positives: list[str]
    concerns: list[str]
    verify_on_site: list[str]
    evidence_image_url: str
    sub_scores: dict[str, float]
    source: str = "swarm.breadth"               # or swarm.crew.judge
    crew: Optional[dict[str, Any]] = None        # populated only on the winner deep-dive
    error: Optional[str] = None                  # set when an agent failed; frontend shows it distinctly

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# JSON schema we ask the model to fill (kept in sync with Verdict). Used in the prompt and for
# validation. Crew sub-findings reuse a smaller {finding, values/saw} shape (see prompts.py).
VERDICT_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": [
        "verdict", "confidence", "one_line_reason", "rationale",
        "positives", "concerns", "verify_on_site", "sub_scores",
    ],
    "properties": {
        "verdict": {"enum": ["go", "conditional", "no_go"]},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "one_line_reason": {"type": "string"},
        "rationale": {"type": "string"},
        "positives": {"type": "array", "items": {"type": "string"}},
        "concerns": {"type": "array", "items": {"type": "string"}},
        "verify_on_site": {"type": "array", "items": {"type": "string"}},
        "sub_scores": {"type": "object"},
    },
}
