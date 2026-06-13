"""Perception stage (Stage 1.5): measure screened finalists from Cyvl's 3D scan.

    from perception import perceive, perceive_finalists

See README.md for the output schema and the boundary with screening / the swarm.
"""
from . import config
from .perceive import perceive, perceive_finalists

__all__ = ["perceive", "perceive_finalists", "config"]
