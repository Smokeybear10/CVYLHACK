"""Build a SiteBundle from the Stage 1 screening-output contract.

The contract is a screening candidate feature (GeoJSON-style dict with the
properties screening emits). This is the only coupling to Stage 1, and it is by
data shape, not by import, so the survey package is standalone. The bundler also
computes the grounding allow-list: every number a report is permitted to state.
"""
from __future__ import annotations

from . import criteria
from .schema import Derived, Evidence, Measured, Public, SiteBundle, SiteInfo

FCLASS_LABEL = {
    1: "Interstate", 2: "Freeway/Expressway", 3: "Principal arterial",
    4: "Minor arterial", 5: "Major collector", 6: "Minor collector", 7: "Local",
}


def _centroid(geometry: dict) -> tuple[float, float]:
    """Return (lon, lat) for a feature geometry (LineString, Point, or Polygon)."""
    g = geometry or {}
    t = g.get("type")
    coords = g.get("coordinates")
    if t == "Point":
        return float(coords[0]), float(coords[1])
    if t == "LineString":
        pts = coords
    elif t == "Polygon":
        pts = coords[0]
    else:
        raise ValueError(f"unsupported geometry type {t!r}")
    lon = sum(p[0] for p in pts) / len(pts)
    lat = sum(p[1] for p in pts) / len(pts)
    return float(lon), float(lat)


def _r(x, ndigits=1):
    return None if x is None else round(float(x), ndigits)


def _collect_allowed(measured: Measured, derived: Derived, public: Public) -> list[float]:
    """Every number a report may legitimately state. The grounding guard checks
    report numbers against this set (with tolerance)."""
    nums: set[float] = set()

    def add(v, nd=1):
        if v is None:
            return
        try:
            nums.add(round(float(v), nd))
        except (TypeError, ValueError):
            return

    add(measured.usable_frontage_ft); add(measured.road_width_ft)
    add(measured.distance_to_power_m); add(measured.pavement_pci)
    add(measured.obstruction_count, 0)
    add(derived.composite_score); add(derived.rom_cost_usd, 0)
    add(derived.trench_len_ft); add(derived.residential_suit, 2)
    add(derived.traveler_suit, 2); add(derived.functional_class, 0)
    add(derived.ports_that_fit, 0); add(derived.required_frontage_ft)
    for v in derived.component_scores.values():
        add(v, 2)
    add(public.nearby_chargers, 0); add(public.aadt, 0)
    # small integers that legitimately appear as counts / port numbers
    for i in (0, 1, 2, 3, 4):
        nums.add(float(i))
    return sorted(nums)


def bundle_from_feature(feature: dict, region: str | None = None,
                        required_frontage_ft: float = criteria.DEFAULT_REQUIRED_FRONTAGE_FT) -> SiteBundle:
    p = feature["properties"]
    lon, lat = _centroid(feature["geometry"])

    frontage = _r(p.get("length_ft"))
    dist_power = _r(p.get("dist_to_power_m"))
    score = float(p.get("score", 0.0))
    gated = bool(p.get("gated", False))
    fclass = p.get("functional_class")

    ports = int(frontage // required_frontage_ft) if frontage else None
    trench_ft = _r(dist_power * criteria.TRENCH_FT_PER_M) if dist_power is not None else None

    measured = Measured(
        usable_frontage_ft=frontage,
        road_width_ft=_r(p.get("road_width_ft")),
        distance_to_power_m=dist_power,
        pole_type=None,  # screening does not record which power asset was nearest
        obstruction_count=int(p.get("obstruction_count", 0) or 0),
        pavement_pci=_r(p.get("pci"), 0),
        surface=None,  # surface_type not carried by Stage 1 yet
    )
    derived = Derived(
        composite_score=round(score, 1),
        tier_hint=criteria.tier_from(score, gated),
        gated=gated,
        gate_reasons=list(p.get("gate_reasons") or []),
        rom_cost_usd=_r(p.get("est_make_ready_usd"), 0),
        cost_band=p.get("connection_cost_band"),
        trench_len_ft=trench_ft,
        residential_suit=_r(p.get("residential_suit"), 2),
        traveler_suit=_r(p.get("traffic_suit"), 2),
        functional_class=_r(fclass, 0),
        ports_that_fit=ports,
        required_frontage_ft=round(required_frontage_ft, 1),
        component_scores={k: round(float(v), 2) for k, v in (p.get("components") or {}).items()},
    )
    public = Public(
        zoning_allowed=None,
        nearby_chargers=None,
        road_class=FCLASS_LABEL.get(int(fclass)) if fclass is not None else None,
        aadt=None,
    )
    evidence = Evidence(photo_ref=None, cv_findings=[])  # set by Stage 1.5 CV when wired

    return SiteBundle(
        site=SiteInfo(id=str(p.get("cand_id")), lat=lat, lon=lon,
                      street=p.get("address_st"), region=region),
        measured=measured,
        derived=derived,
        public=public,
        evidence=evidence,
        known_unknowns=list(criteria.VERIFY_ON_SITE),
        allowed_numbers=_collect_allowed(measured, derived, public),
    )


def bundles_from_contract(contract: dict,
                          required_frontage_ft: float = criteria.DEFAULT_REQUIRED_FRONTAGE_FT) -> list[SiteBundle]:
    region = contract.get("region")
    region_str = str(region) if region is not None else None
    return [bundle_from_feature(f, region=region_str, required_frontage_ft=required_frontage_ft)
            for f in contract.get("sites", [])]
