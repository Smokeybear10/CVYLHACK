"""Disk cache for survey outputs, keyed by site + bundle data + client + prompt.

Identical inputs return the identical cached report, which keeps the demo stable
across reruns and avoids re-paying for tokens during development.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .client import PROMPT_VERSION
from .schema import SiteBundle

DEFAULT_DIR = Path(".survey_cache")


def data_hash(bundle: SiteBundle) -> str:
    blob = json.dumps(bundle.model_dump(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def cache_key(bundle: SiteBundle, client_name: str, prompt_version: str = PROMPT_VERSION) -> str:
    return f"{bundle.site.id}__{client_name}__{prompt_version}__{data_hash(bundle)}"


class CacheStore:
    def __init__(self, directory: Path | str = DEFAULT_DIR):
        self.dir = Path(directory)

    def get(self, key: str) -> dict | None:
        path = self.dir / f"{key}.json"
        if path.exists():
            return json.loads(path.read_text())
        return None

    def set(self, key: str, report_dict: dict) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        (self.dir / f"{key}.json").write_text(json.dumps(report_dict))
