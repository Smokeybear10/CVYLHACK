"""Bundler maps screening output to grounded bundles."""
from survey import criteria


def test_all_sites_bundled(bundles, contract):
    assert len(bundles) == len(contract["sites"])


def test_bundle_core_fields(one_bundle):
    b = one_bundle
    assert b.site.id
    assert -72 < b.site.lon < -70 and 42 < b.site.lat < 43  # Somerville
    assert b.measured.distance_to_power_m is not None
    assert b.derived.composite_score >= 0
    assert b.allowed_numbers, "allow-list must be populated"
    assert b.known_unknowns, "verify-on-site set must be carried"


def test_ports_and_trench_computed(one_bundle):
    b = one_bundle
    if b.measured.usable_frontage_ft:
        expected = int(b.measured.usable_frontage_ft // b.derived.required_frontage_ft)
        assert b.derived.ports_that_fit == expected
    if b.measured.distance_to_power_m is not None:
        assert b.derived.trench_len_ft is not None


def test_gated_site_tier_hint_is_nogo(gated_bundle):
    assert gated_bundle.derived.tier_hint == "No-go"


def test_high_score_is_not_nogo(bundles):
    strong = [b for b in bundles if not b.derived.gated and b.derived.composite_score >= criteria.TIER_3_MIN]
    assert strong, "fixture should include viable sites"
    for b in strong:
        assert b.derived.tier_hint != "No-go"


def test_allowed_numbers_include_key_measurements(one_bundle):
    b = one_bundle
    allowed = b.allowed_numbers
    for v in (b.derived.composite_score, b.measured.distance_to_power_m):
        if v is not None:
            assert any(abs(v - a) <= 0.5 for a in allowed)
