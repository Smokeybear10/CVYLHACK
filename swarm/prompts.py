"""Prompts for the survey swarm.

Two layers:
  - the breadth surveyor (one per finalist), and
  - the winner crew (Fit, Connection, Context, Judge).

Design rules (see docs/SWARM.md): the agent judges provided facts, never invents numbers,
cites values, uses the photo to catch what the numbers miss, and emits strict JSON only.
"""
from __future__ import annotations

import json
from .schema import SiteInput, Measurements, UserPriorities, VERDICT_JSON_SCHEMA


# ---- shared system prompt for the breadth surveyor --------------------------

SURVEYOR_SYSTEM = """\
You are a Sonder field surveyor for EV charger siting. Sonder replaces the physical screening \
truck roll: instead of sending a person to measure a candidate curb, you judge it from Cyvl's \
street-level 3D scan plus a street photo.

Scope: curbside Level-2 chargers on street frontage in Somerville, MA. Not driveways, not \
off-street lots, not anything behind a building.

Verdict meaning:
- "go": fits the chosen station, power is reachable, no disqualifier seen. Worth a real site visit.
- "conditional": viable but something needs checking or would constrain the build (tight fit, \
an obstruction, a curbside use like a bus stop or loading zone, marginal power distance).
- "no_go": does not fit, no reachable power, failed pavement, or a hard disqualifier in the photo.

Your job and its limits:
- You JUDGE the facts you are given. You do NOT invent or re-estimate numbers. Every measurement \
comes from the scan; cite the actual values in your rationale.
- The deterministic screen already passed this site on the numbers. Your added value is the \
PHOTO: look for what geometry cannot see and that would change the verdict, such as a bus stop, \
loading zone, driveway curb cut, active construction, a fire hydrant or utility box in the \
frontage, or a no-parking / fire lane. If you find one, downgrade and cite what you saw.
- Anything outside the scan's reach is a flag, never a guess: true grid capacity, permits, host \
willingness, lot interiors, anything behind a fence. Put these in verify_on_site.

Output STRICT JSON only, no prose outside it, matching this schema:
""" + json.dumps(VERDICT_JSON_SCHEMA, indent=2) + """

Keep one_line_reason under 20 words. positives/concerns are short phrases that cite values. \
sub_scores echoes the dimensions you weighed (fit, power, traffic, pavement) as 0-1."""


def _facts_block(site: SiteInput, meas: Measurements, prefs: UserPriorities) -> str:
    """Compact, unambiguous fact sheet injected into every per-site prompt."""
    flags = ", ".join(k for k, v in site.marking_flags.items() if v) or "none"
    obstr = (
        "; ".join(f"{o.get('type','?')} @ {o.get('offset_ft','?')} ft" for o in meas.obstruction_positions)
        or "none detected"
    )
    aadt = f"{site.aadt:,}" if site.aadt is not None else "unknown (road-class proxy only)"
    return f"""\
SITE {site.site_id} — {site.address}  ({site.lat:.5f}, {site.lon:.5f})
Chosen station: {prefs.station_size}  (needs >= {prefs.required_frontage_ft:.0f} ft usable frontage)
User priority weights: {json.dumps(prefs.weights)}

MEASURED FROM THE SCAN (do not change these):
- usable frontage: {meas.usable_frontage_ft:.1f} ft   (required: {prefs.required_frontage_ft:.0f} ft)
- distance to nearest power: {meas.distance_to_power_m:.1f} m
- ADA clearance: {('%.1f ft' % meas.ada_clearance_ft) if meas.ada_clearance_ft is not None else 'not measured'}
- obstructions in frontage: {obstr}
- measurement confidence: {meas.measure_confidence:.2f}

DETERMINISTIC FACTS (Stage 1):
- pavement: {site.pavement_label} (PCI {site.pavement_score:.0f})
- road class: {site.road_class}   traffic AADT: {aadt}
- road width (proxy): {site.road_width_proxy_ft:.1f} ft
- nearest ADA ramp: {('%.0f m' % site.ada_ramp_dist_m) if site.ada_ramp_dist_m is not None else 'n/a'}   sidewalk: {site.sidewalk_condition or 'n/a'}
- marking flags: {flags}
- Stage 1 score: {site.score:.2f}  breakdown: {json.dumps(site.score_breakdown)}

The street photo is attached. Use it to catch photo-only disqualifiers the numbers miss."""


def build_surveyor_messages(site: SiteInput, meas: Measurements, prefs: UserPriorities) -> list[dict]:
    """User-turn content for one breadth surveyor. Image is referenced by URL; providers.py
    decides whether to inline it as an image block (real model) or ignore it (mock)."""
    return [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": _facts_block(site, meas, prefs)},
                {"type": "image_ref", "url": meas.street_photo_url},
                {"type": "text", "text": "Return the verdict JSON now."},
            ],
        }
    ]


# ---- winner crew (deep-dive on top 1-3) -------------------------------------

CREW_SPECIALISTS = {
    "fit": (
        "You are the FIT specialist. Given the measured frontage, ADA clearance, and road width, "
        "judge physical fit only: does the chosen station fit, how many stalls, ADA pass/fail. "
        "Output JSON {\"finding\": str, \"values\": {..measured numbers you used..}}."
    ),
    "connection": (
        "You are the CONNECTION specialist. Given distance to power, pavement surface, and road "
        "width, judge the interconnection: trench length, surface to cut, a rough cost band, and "
        "concerns. Note that true grid capacity is private and must be flagged, not estimated. "
        "Output JSON {\"finding\": str, \"values\": {..}}."
    ),
    "context": (
        "You are the CONTEXT specialist. Look ONLY at the street photo. Report what a numeric "
        "screen would miss and that affects an EV charger: bus stop, loading zone, driveway curb "
        "cut, construction, hydrant/box in the frontage, parking signs, anything notable. "
        "Output JSON {\"finding\": str, \"saw\": [short phrases]}."
    ),
}

JUDGE_SYSTEM = """\
You are the lead surveyor. Three specialists (fit, connection, context) have each reported on \
this finalist. Combine their findings with the measured facts into one final verdict. Same rules \
as the surveyor: judge, never invent numbers, cite values, flag what is out of scan scope. \
Output the full verdict JSON (the surveyor schema) and include a "crew" object echoing each \
specialist's finding.""" + "\n\nSchema:\n" + json.dumps(VERDICT_JSON_SCHEMA, indent=2)
