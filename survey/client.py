"""LLM clients behind one interface.

StubClient is the deterministic offline judgment (development, tests, demo
fallback). AnthropicClient is the real agent, wired with forced structured output
so the model must return the report schema. Both return a raw report dict that the
agent then validates.
"""
from __future__ import annotations

import json
import os
from typing import Protocol

from . import deterministic
from .schema import SiteBundle, SiteReport

PROMPT_VERSION = "survey-v1"
DEFAULT_MODEL = os.environ.get("SURVEY_MODEL", "claude-sonnet-4-6")


class LLMClient(Protocol):
    name: str

    def generate(self, bundle: SiteBundle, skills: str) -> dict:
        ...


class StubClient:
    """Deterministic, no network. Grounded by construction."""
    name = "stub"

    def generate(self, bundle: SiteBundle, skills: str) -> dict:
        return deterministic.build_report(bundle, generated_by="stub").model_dump()


def have_key() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


class AnthropicClient:
    """Real agent. Forces the model to emit the report schema via a tool call.

    Requires ANTHROPIC_API_KEY. Not exercised in offline tests; the stub path is
    the verified one. The agent layer revalidates and falls back if this errors.
    """
    name = "anthropic"

    def __init__(self, model: str = DEFAULT_MODEL, max_tokens: int = 4096, temperature: float = 0.0):
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    def generate(self, bundle: SiteBundle, skills: str) -> dict:
        import anthropic

        client = anthropic.Anthropic()
        tool = {
            "name": "emit_site_report",
            "description": "Emit the curbside EV site assessment as the required schema. "
                           "Use only the values in the bundle; defer everything else to "
                           "to_be_verified. Never invent a number.",
            "input_schema": SiteReport.model_json_schema(),
        }
        user = (
            "Assess this curbside EV charging candidate. Judge the provided facts, do not "
            "compute or invent numbers, and emit the report via emit_site_report.\n\n"
            "SITE BUNDLE (your only source of facts):\n"
            + json.dumps(bundle.model_dump(), indent=2)
        )
        msg = client.messages.create(
            model=self.model, max_tokens=self.max_tokens, temperature=self.temperature,
            system=skills, tools=[tool],
            tool_choice={"type": "tool", "name": "emit_site_report"},
            messages=[{"role": "user", "content": user}],
        )
        data = None
        for block in msg.content:
            if getattr(block, "type", None) == "tool_use":
                data = dict(block.input)
                break
        if data is None:
            raise RuntimeError("model did not return a tool_use report block")
        data["generated_by"] = "anthropic"
        return data
