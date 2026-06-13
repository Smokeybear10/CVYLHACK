"""Tiny dependency-free .env loader.

Loads KEY=VALUE lines from a .env at the repo root (or cwd) into the environment
without overriding anything already set. Lets you drop ANTHROPIC_API_KEY in a
gitignored .env and have the real agent pick it up automatically.
"""
from __future__ import annotations

import os
from pathlib import Path


def load_dotenv() -> bool:
    candidates = [Path(__file__).resolve().parent.parent / ".env", Path.cwd() / ".env"]
    seen = set()
    loaded = False
    for env_path in candidates:
        if env_path in seen or not env_path.exists():
            continue
        seen.add(env_path)
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))
        loaded = True
    return loaded
