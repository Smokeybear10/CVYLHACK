"""LLM provider for the swarm.

Real path: Anthropic Messages API (uses ANTHROPIC_API_KEY, model from ANTHROPIC_MODEL).
Mock path: deterministic rule-based verdict from the same inputs, so the whole pipeline runs
end to end today with no key and no CV. Mock mode is for development and as the demo safety net,
never for the verdicts we actually show (see the honesty note in PLAN.md §5.4).
"""
from __future__ import annotations

import base64
import json
import os
import re
import urllib.request
from typing import Any

from .schema import SiteInput, Measurements, UserPriorities, Verdict, VERDICT_JSON_SCHEMA
from . import prompts, config


def have_key() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


# ---- real model call --------------------------------------------------------

_IMG_CACHE: dict[str, Any] = {}


def _fetch_image_b64(url: str):
    """Download an image and return (media_type, base64_data). Anthropic refuses URL image
    sources blocked by robots.txt (the Cyvl CDN is), so we inline the bytes. Cached per URL.
    Returns None on any failure so the call falls back to text-only."""
    if url in _IMG_CACHE:
        return _IMG_CACHE[url]
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "sonder-swarm/0.1"})
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read()
            ct = r.headers.get("Content-Type", "").split(";")[0].strip()
        media = ct if ct.startswith("image/") else ("image/png" if url.lower().endswith(".png") else "image/jpeg")
        out = (media, base64.standard_b64encode(raw).decode("ascii"))
    except Exception:
        out = None
    _IMG_CACHE[url] = out
    return out


def _to_anthropic_content(content: list[dict]) -> list[dict]:
    """Convert our message content (text + image_ref) into Anthropic blocks. Images are fetched
    and inlined as base64 because the Cyvl CDN disallows Anthropic's URL fetch via robots.txt."""
    out: list[dict] = []
    for block in content:
        if block["type"] == "text":
            out.append({"type": "text", "text": block["text"]})
        elif block["type"] == "image_ref":
            img = _fetch_image_b64(block["url"])
            if img:
                out.append({"type": "image", "source": {"type": "base64", "media_type": img[0], "data": img[1]}})
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


# Tool-call schemas (force schema-valid JSON; no fragile free-text parsing).
_VERDICT_TOOL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": VERDICT_JSON_SCHEMA["required"],
    "properties": {**VERDICT_JSON_SCHEMA["properties"],
                   "verdict": {"type": "string", "enum": ["go", "conditional", "no_go"]}},
}
JUDGE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": VERDICT_JSON_SCHEMA["required"],
    "properties": {**_VERDICT_TOOL_SCHEMA["properties"], "crew": {"type": "object"}},
}
SPECIALIST_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["finding"],
    "properties": {
        "finding": {"type": "string"},
        "values": {"type": "object"},
        "saw": {"type": "array", "items": {"type": "string"}},
    },
}


# Strip control + line/paragraph separators the browser's JSON.parse rejects (U+2028/U+2029)
# and C0 controls Python's strict json rejects. Models occasionally emit these in free text.
_CTRL_RE = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\u2028\u2029]")


def _clean(obj):
    if isinstance(obj, str):
        return _CTRL_RE.sub(" ", obj)
    if isinstance(obj, list):
        return [_clean(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    return obj


def _call_tool(system: str, messages: list[dict], schema: dict, model: str | None = None,
               temperature: float = 0.1, max_tokens: int = 1024, tool_name: str = "emit") -> dict:
    """Force the model to return schema-valid JSON via a single tool call. Eliminates the
    free-text JSON parsing that breaks on unescaped quotes or token-cap truncation."""
    import anthropic  # lazy, mock mode needs no dependency

    client = anthropic.Anthropic()
    model = model or config.BREADTH_MODEL
    api_messages = [{"role": m["role"], "content": _to_anthropic_content(m["content"])} for m in messages]
    tool = {"name": tool_name, "description": "Return the structured result.", "input_schema": schema}
    resp = client.messages.create(
        model=model, system=system, messages=api_messages,
        temperature=temperature, max_tokens=max_tokens,
        tools=[tool], tool_choice={"type": "tool", "name": tool_name},
    )
    for b in resp.content:
        if getattr(b, "type", None) == "tool_use":
            return _clean(dict(b.input))
    text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
    return _clean(_parse_json(text))


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
        data = _call_tool(prompts.SURVEYOR_SYSTEM, msgs, _VERDICT_TOOL_SCHEMA,
                          model=config.BREADTH_MODEL, tool_name="emit_verdict")
        source = "swarm.breadth"
    else:
        data = _mock_verdict(site, meas, prefs)
        source = "swarm.breadth.mock"
    return Verdict(
        site_id=site.site_id, evidence_image_url=meas.evidence_image_url, source=source,
        lon=site.lon, lat=site.lat, **_normalize(data),
    )
