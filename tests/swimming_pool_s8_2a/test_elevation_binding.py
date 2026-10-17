"""Generic elevation binding and source identity: synthetic known answers only, no project data.

A dimension on an elevation binds to an object only on a plan identity label plus dimension and feature matches with
nothing failed or contradicted. A cylinder seen side-on shows its radius as the silhouette half-width. A dimension
drawn on one flat floor does not apply to a pool another source draws with a level change. A re-saved PDF that only
gained /Info entries is the same source once those entries are removed and the offsets restored."""

from __future__ import annotations

import io
import math

import pytest

from engine.source import elevation_binding as EB
from engine.source import source_identity as SI


# ------------------------------------------------------------------ levels
def test_levels_from_a_datum_dimension():
    assert EB.level_at(-804246, -805246, 0.0) == pytest.approx(1.0)
    s = EB.dimension_span(-806096, -804946, -805246, 0.0)
    assert (s["low_m"], s["high_m"], s["span_m"]) == (pytest.approx(-0.85), pytest.approx(0.30), pytest.approx(1.15))
    with pytest.raises(EB.ElevationBindingError):
        EB.level_at(0, 0, 0, units_per_m=0)


# ------------------------------------------------------------------ cylinders and arcs
def test_a_cylinder_seen_side_on():
    R = 1550.0
    offs = [R * math.cos(math.radians(a)) for a in (12, 18, 31, 45, 72)]
    c = EB.cylinder_from_generators(R, offs + [-o for o in offs])
    assert c["consistent"] and [round(a) for a in c["angles_deg"]] == [72, 45, 31, 18, 12]
    assert not EB.cylinder_from_generators(R, offs)["consistent"]                         # one side only
    assert not EB.cylinder_from_generators(1000.0, offs + [-o for o in offs])["consistent"]   # lines outside


def test_arc_projected_half_width():
    assert EB.arc_projected_half_width(2250, 96.4, 263.6, "y") == pytest.approx(2250 * math.sin(math.radians(96.4)))
    assert EB.arc_projected_half_width(1750, 90, 270, "y") == pytest.approx(1750)
    assert EB.arc_projected_half_width(1750, 90, 270, "x") == pytest.approx(1750)       # the apex at 180 degrees
    assert EB.arc_projected_half_width(1000, 10, 20, "x") == pytest.approx(1000 * math.cos(math.radians(10)))
    assert EB.arc_projected_half_width(1000, 350, 10, "y") == pytest.approx(1000 * math.sin(math.radians(10)))


# ------------------------------------------------------------------ binding
def C(kind, ok, detail=""):
    return {"kind": kind, "ok": ok, "detail": detail or kind}


def test_bound_needs_label_dimension_and_feature():
    full = [C(EB.IDENTITY_LABEL, True), C(EB.DIMENSION_MATCH, True), C(EB.FEATURE_MATCH, True), C(EB.LEVEL_MATCH, True)]
    assert EB.binding_verdict(full)["state"] == EB.BOUND
    for drop in (EB.IDENTITY_LABEL, EB.DIMENSION_MATCH, EB.FEATURE_MATCH):
        v = EB.binding_verdict([c for c in full if c["kind"] != drop])
        assert v["state"] == EB.NOT_BOUND and v["missing"] == [drop]


def test_resemblance_alone_is_not_binding():
    # a sunken box the right size but no plan label at that place (it could be a lift pit or a planter)
    v = EB.binding_verdict([C(EB.DIMENSION_MATCH, True), C(EB.LEVEL_MATCH, True)])
    assert v["state"] == EB.NOT_BOUND and set(v["missing"]) == {EB.IDENTITY_LABEL, EB.FEATURE_MATCH}


def test_a_failed_match_or_a_contradiction_unbinds():
    base = [C(EB.IDENTITY_LABEL, True), C(EB.DIMENSION_MATCH, True), C(EB.FEATURE_MATCH, True)]
    assert EB.binding_verdict(base + [C(EB.DIMENSION_MATCH, False, "width 2.8 vs 3.5")])["failed"] == ["width 2.8 vs 3.5"]
    assert EB.binding_verdict(base + [C(EB.LEVEL_MATCH, False)])["state"] == EB.NOT_BOUND
    v = EB.binding_verdict(base + [C(EB.CONTRADICTION, True, "a lift pit is drawn here")])
    assert v["state"] == EB.NOT_BOUND and v["contradictions"] == ["a lift pit is drawn here"]
    assert EB.binding_verdict(base + [C(EB.CONTRADICTION, False)])["state"] == EB.BOUND
    with pytest.raises(EB.ElevationBindingError):
        EB.binding_verdict([C("LOOKS_LIKE_A_POOL", True)])


# ------------------------------------------------------------------ floor profile
def test_one_flat_floor_against_a_level_change_is_a_conflict():
    p = EB.floor_profile([{"source": "arch elevation", "levels": [-0.85]},
                          {"source": "structural section", "levels": ["DEEP", "SLOPE", "SHALLOW"]}])
    assert p["state"] == EB.PROFILE_CONFLICT and p["uniform_dimension_allowed"] is False
    assert EB.floor_profile([{"source": "a", "levels": [-0.85]}, {"source": "b", "levels": [-0.85]}])["state"] == EB.UNIFORM
    assert EB.floor_profile([{"source": "a", "levels": [-0.85]}, {"source": "b", "levels": [-0.80]}])["state"] == \
        EB.PROFILE_CONFLICT
    assert EB.floor_profile([{"source": "a", "levels": []}])["state"] == EB.NOT_SHOWN


# ------------------------------------------------------------------ source identity
def _pdf(meta):
    from pypdf import PdfWriter
    w = PdfWriter()
    w.add_blank_page(100, 100)
    w.add_metadata(meta)
    b = io.BytesIO()
    w.write(b)
    return b.getvalue()


def test_added_info_entries_are_wrapper_metadata_only():
    base = _pdf({"/Producer": "pypdf"})
    plus = _pdf({"/Producer": "pypdf", "/Title": "Part 1, pages (01-06)", "/Subject": "split for upload"})
    r = SI.relation(plus, SI.sha256(base))
    assert r["relation"] == SI.WRAPPER_METADATA_ONLY and r["reconstructed_sha256"] == SI.sha256(base)
    assert r["removed_bytes"] == len(plus) - len(base)
    assert SI.relation(base, SI.sha256(base))["relation"] == SI.IDENTICAL


def test_a_changed_page_is_a_different_source():
    from pypdf import PdfWriter
    base = _pdf({"/Producer": "pypdf"})
    w = PdfWriter()
    w.add_blank_page(100, 120)                              # different page, same metadata change
    w.add_metadata({"/Producer": "pypdf", "/Title": "Part 1"})
    b = io.BytesIO()
    w.write(b)
    assert SI.relation(b.getvalue(), SI.sha256(base))["relation"] == SI.DIFFERENT
    assert SI.relation(b"not a pdf", SI.sha256(base))["relation"] == SI.DIFFERENT


def test_arc_projected_interval_tells_the_view_direction():
    lo, hi = EB.arc_projected_interval(2250, 96.4, 263.6, "y")
    assert lo == pytest.approx(-hi) and hi == pytest.approx(2250 * math.sin(math.radians(96.4)))
    lo, hi = EB.arc_projected_interval(2250, 96.4, 263.6, "x")
    assert lo == pytest.approx(-2250) and hi == pytest.approx(2250 * math.cos(math.radians(96.4)))
    assert abs(lo + hi) > 100                                           # asymmetric: not the view axis
