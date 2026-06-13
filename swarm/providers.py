"""LLM provider for the swarm.

Real path: Anthropic Messages API (uses ANTHROPIC_API_KEY, model from ANTHROPIC_MODEL).
Mock path: deterministic rule-based verdict from the same inputs, so the whole pipeline runs
end to end today with no key and no CV. Mock mode is for development and as the demo safety net,
never for the verdicts we actually show (see the honesty note in PLAN.md §5.4).
"""
from __future__ import annotations

import json
import os
from typing import Any

from .schema import SiteInput, Measurements, UserPriorities, Verdict
from . import prompts, config


def have_key() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


# ---- real model call --------------------------------------------------------

def _to_anthropic_content(content: list[dict]) -> list[dict]:
    """Convert our message content (text + image_ref) into Anthropic blocks."""
    out: list[dict] = []
    for block in content:
        if block["type"] == "text":
            out.append({"type": "text", "text": block["text"]})
        elif block["type"] == "image_ref":
            out.append({"type": "image", "source": {"type": "url", "url": block["url"]}})
    return out


def _call_model(system: str, messages: list[dict], model: str | None = None,
                temperature: float = 0.1, max_tokens: int = 1024) -> str:
    import anthropic  # imported lazily so mock mode needs no dependency

    client = anthropic.Anthropic()
    model = model or config.BREADTH_MODEL
    api_messages = [{"role": m["role"], "content": _to_anthropic_content(m["content"])} for m in messages]
    resp = client.messages.create(
        model=model, system=system, messages=api_messages,
        temperature=temperature, max_tokens=max_tokens,
    )
    return "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")


def _parse_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1].lstrip("json").strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object found in model output")
    return json.loads(text[start : end + 1])


# required verdict keys -> (default, type). Used to make model output safe to construct a Verdict.
_REQUIRED: dict[str, Any] = {
    "verdict": ("conditional", str),
    "confidence": (0.5, float),
    "one_line_reason": ("", str),
    "rationale": ("", str),
    "positives": ([], list),
    "concerns": ([], list),
    "verify_on_site": ([], list),
    "sub_scores": ({}, dict),
}


def _normalize(data: dict[str, Any]) -> dict[str, Any]:
    """Coerce model/mock output into the exact keys/types a Verdict needs. Never raises."""
    out: dict[str, Any] = {}
    for k, (default, typ) in _REQUIRED.items():
        v = data.get(k, default)
        if typ is float:
            try:
                v = max(0.0, min(1.0, float(v)))
            except (TypeError, ValueError):
                v = default
        elif typ is list:
            v = list(v) if isinstance(v, (list, tuple)) else ([str(v)] if v else [])
        elif typ is dict:
            v = v if isinstance(v, dict) else {}
        elif typ is str:
            v = v if isinstance(v, str) else str(v)
        out[k] = v
    if out["verdict"] not in ("go", "conditional", "no_go"):
        out["verdict"] = "conditional"
    return out


# ---- mock verdict (no key / no CV) ------------------------------------------

def _mock_verdict(site: SiteInput, meas: Measurements, prefs: UserPriorities) -> dict[str, Any]:
    req = prefs.required_frontage_ft
    positives, concerns, flags = [], [], ["final on-site survey"]
    verdict = "go"

    if meas.usable_frontage_ft < req:
        verdict = "no_go"
        concerns.append(f"frontage {meas.usable_frontage_ft:.1f} ft < {req:.0f} ft required")
    else:
        positives.append(f"{meas.usable_frontage_ft:.1f} ft usable frontage")

    if site.pavement_score < 25:
        verdict = "no_go"
        concerns.append(f"pavement {site.pavement_label} (PCI {site.pavement_score:.0f})")
    elif site.pavement_score >= 56:
        positives.append(f"PCI {site.pavement_score:.0f} ({site.pavement_label})")

    if meas.distance_to_power_m > 30:
        verdict = "no_go"
        concerns.append(f"power {meas.distance_to_power_m:.0f} m away")
    else:
        positives.append(f"power {meas.distance_to_power_m:.0f} m")

    blockers = [k for k in ("bus_stop", "loading_zone", "fire_lane", "no_parking") if site.marking_flags.get(k)]
    if meas.obstruction_positions:
        blockers += [o.get("type", "obstruction") for o in meas.obstruction_positions]
    if verdict == "go" and blockers:
        verdict = "conditional"
        concerns.append("photo/markings: " + ", ".join(blockers))
        flags.append("curbside use conflict (" + ", ".join(blockers) + ")")

    flags += ["grid capacity at the pole", "curbside / parking permit"]
    reason = {
        "go": "Fits the stall, power close, nothing in the way.",
        "conditional": "Fits on numbers but the photo shows a curbside conflict.",
        "no_go": "Fails a hard requirement (fit, power, or pavement).",
    }[verdict]
    return {
        "verdict": verdict,
        "confidence": round(0.55 + 0.4 * meas.measure_confidence, 2),
        "one_line_reason": reason,
        "rationale": (
            f"Usable frontage {meas.usable_frontage_ft:.1f} ft vs {req:.0f} ft required; "
            f"power {meas.distance_to_power_m:.0f} m; pavement {site.pavement_label} "
            f"(PCI {site.pavement_score:.0f})." + (f" Concern: {', '.join(blockers)}." if blockers else "")
        ),
        "positives": positives,
        "concerns": concerns,
        "verify_on_site": flags,
        "sub_scores": site.score_breakdown or {"fit": 0.7, "power": 0.7, "traffic": 0.6, "pavement": 0.7},
    }


# ---- public API -------------------------------------------------------------

def surveyor_verdict(site: SiteInput, meas: Measurements, prefs: UserPriorities) -> Verdict:
    if have_key():
        msgs = prompts.build_surveyor_messages(site, meas, prefs)
        data = _parse_json(_call_model(prompts.SURVEYOR_SYSTEM, msgs))
        source = "swarm.breadth"
    else:
        data = _mock_verdict(site, meas, prefs)
        source = "swarm.breadth.mock"
    return Verdict(
        site_id=site.site_id, evidence_image_url=meas.evidence_image_url, source=source,
        lon=site.lon, lat=site.lat, **_normalize(data),
    )
