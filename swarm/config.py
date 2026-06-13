"""Swarm config: load .env, pick models, hold cost knobs.

Frugality matters here (shared $200 credit). Defaults:
  - breadth pass uses a cheap fast model (haiku) — it is high-volume, one call per finalist.
  - winner crew + judge use a stronger model (sonnet) — only 1-3 sites, worth the spend.
Override any of these in .env. If a model id is wrong for your account, set it explicitly.
"""
from __future__ import annotations

import os
from pathlib import Path

# repo root = parent of this file's package dir
_ROOT = Path(__file__).resolve().parent.parent


def load_env() -> None:
    """Minimal .env loader (no dependency). Does not overwrite already-set vars."""
    env = _ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        os.environ.setdefault(k, v)


load_env()

# Model tiers (override in .env). Confirm the exact ids your key can call.
BREADTH_MODEL = os.environ.get("SWARM_BREADTH_MODEL", "claude-haiku-4-5")
CREW_MODEL = os.environ.get("SWARM_CREW_MODEL", "claude-sonnet-4-5")

# Cost guardrails.
WAVE_SIZE = int(os.environ.get("SWARM_WAVE_SIZE", "6"))
MAX_BREADTH_SITES = int(os.environ.get("SWARM_MAX_BREADTH", "0"))  # 0 = no cap
CREW_WINNERS = int(os.environ.get("SWARM_CREW_WINNERS", "1"))      # how many winners get the deep-dive
