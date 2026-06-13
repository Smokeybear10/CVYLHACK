"""Sonder screening stage: region in, ranked candidate curb segments out.

Public API:
    from screening import screen, Filters
    result = screen(region=[-71.108, 42.388, -71.099, 42.397])

See screen() for the result shape and SCREENING.md for the full contract.
"""
from .scoring import Filters
from .screen import screen, to_geojson_str

__all__ = ["screen", "Filters", "to_geojson_str"]
