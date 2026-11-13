"""T-688 R-T688-1 (own panel noding), R-T688-2 (typed reference constant), R-T688-3 (region label vs physical element).
Villa V688 is hand-made (not the development villa); the last tests rebuild the development-villa statement from
committed files only (the own re-measure output is committed as numbers; the drawing never is)."""
from __future__ import annotations

import json
import sys
from decimal import Decimal as X
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t688"))
import t688_rules as R  # noqa: E402


# V688 by hand (mm). Slab 10.30 x 8.30 m: perimeter beams 0.30, one internal beam 0.30 (x 5.00 .. 5.30). Beam faces
# are drawn as continuous lines. Bays: west x 0.30 .. 5.00, east x 5.30 .. 10.00, both y 0.30 .. 8.00:
# 4.70 x 7.70 = 36.19 m2 each. A drawn void 1.00 x 1.00 inside the east bay (outline + X on the opening layer):
# east panel 36.19 - 1.00 = 35.19 m2; panels 71.38 m2; the void 1.00 m2 OPENING; strips and junctions BAND.
def villa(mirror=False, rotate=False, scale=1.0, gap=0.0):
    def P(x, y):
        if mirror:
            x = 10300 - x
        if rotate:
            x, y = -y, x
        return (x * scale, y * scale)
    edges = [[P(0, 0), P(10300, 0), P(10300, 8300), P(0, 8300), P(0, 0)]]
    for y in (300, 8000):
        edges.append([P(0, y), P(10300, y)])
    for x in (300, 5000, 5300, 10000):
        edges.append([P(x, 0), P(x, 8300)])
    # void outline; gap: its last edge stops short of its first corner (an unnoded end)
    edges.append([P(6000, 3000), P(7000, 3000), P(7000, 4000), P(6000, 4000), P(6000, 3000 + gap)])
    openings = [[P(6000, 3000), P(7000, 4000)], [P(7000, 3000), P(6000, 4000)]]
    return edges, openings


def panels(faces):
    return sorted(round(f["area_m2"], 6) for f in faces if f["class"] == "PANEL")


def test_v688_normal_panel_crossed_by_void():
    e, o = villa()
    f = R.classify_faces(e, o)
    assert panels(f) == [35.19, 36.19]
    assert R.panel_total(f) == pytest.approx(71.38, abs=1e-9)
    ops = [x for x in f if x["class"] == "OPENING"]
    assert len(ops) == 1 and ops[0]["area_m2"] == pytest.approx(1.0)
    assert all(x["width_m"] <= 0.3 + 1e-9 for x in f if x["class"] == "BAND")


@pytest.mark.parametrize("kw", [dict(mirror=True), dict(rotate=True), dict(mirror=True, rotate=True)])
def test_v688_mirror_and_rotation_invariant(kw):
    e, o = villa(**kw)
    assert panels(R.classify_faces(e, o)) == [35.19, 36.19]


def test_v688_units_metres_give_the_same_areas():
    e, o = villa(scale=0.001)
    f = R.classify_faces(e, o, unit_m=1.0, ext=0.03)
    assert panels(f) == [35.19, 36.19]


def test_v688_adverse_unnoded_void_end_closed_by_extension_only():
    e, o = villa(gap=0.5)                                  # the void outline stops 0.5 mm short of its corner
    closed = R.classify_faces(e, o, ext=30.0)
    assert panels(closed) == [35.19, 36.19] and sum(x["class"] == "OPENING" for x in closed) == 1
    leaked = R.classify_faces(e, o, ext=0.0)               # without gap closing the void is never deducted
    assert panels(leaked) == [36.19, 36.19] and not any(x["class"] == "OPENING" for x in leaked)


def test_v688_level_mark_keeps_a_narrow_face_as_slab():
    e, o = villa()
    f = R.classify_faces(e, o, level_marks=[(150, 4000)])  # a mark printed inside the west perimeter strip
    strip = [x for x in f if x["polygon"].contains(__import__("shapely.geometry", fromlist=["Point"]).Point(150, 4000))]
    assert strip and strip[0]["class"] == "PANEL"


def test_unit_refused():
    with pytest.raises(R.Refused):
        R.classify_faces([[(0, 0), (1, 0)]], unit_m=0)


# ---------------------------------------------------------------- R-T688-2 typed constant
ENG = {"A": "30", "B": "2.4", "C": "1.1", "D": "0.6"}          # 34.1 m2 by hand


def tcr(ref, own=None, other=()):
    return R.typed_constant_residual(ENG, own or dict(ENG), ref, "0.16", other_storeys=other)


def test_resolution_of_printed_digits():
    assert R.resolution("120") == X(1) and R.resolution("31.84") == X("0.01") and R.resolution("33.5") == X("0.1")
    with pytest.raises(R.Refused):
        R.resolution("12a")


def test_typed_constant_ambiguous_is_unresolved_never_closest():
    s = tcr("31")                                   # scope 34.1 - 31.5 .. 34.1 - 30.5 = 2.6 .. 3.6: B+C 3.5, B+D 3.0
    assert s["scope_band_m2"] == (X("2.6"), X("3.6")) and s["fitting_subsets"] == 2
    assert s["status"] == "UNRESOLVED_AMBIGUOUS"
    assert s["difference_m3"] == X("-0.496")         # (31 - 34.1) x 0.16
    lo, hi = s["split_m3"]["rounding_band"]
    slo, shi = s["split_m3"]["scope_band"]
    assert (lo, hi) == (X("-0.08"), X("0.08")) and slo + hi == s["difference_m3"] and shi + lo == s["difference_m3"]


def test_typed_constant_unique_candidate_and_none():
    assert tcr("33.5")["status"] == "UNIQUE_CANDIDATE"   # scope 0.55 .. 0.65: D only
    assert R.unique_subset(ENG, "0.55", "0.65") == ("D",)
    assert tcr("33.4")["status"] == "NOT_WHOLE_PANELS"   # 0.65 .. 0.75: no whole panel
    assert tcr("34.1")["status"] == "ROUNDING_ONLY"
    assert tcr("35")["status"] == "REFERENCE_LARGER"


def test_our_error_named_first():
    own = dict(ENG, A="30.02")
    s = tcr("31", own=own)
    assert s["our_error"] and s["split_m3"]["our_error"] == X("-0.0032")
    s2 = tcr("31", own=dict(ENG, A="30.001"))
    assert not s2["our_error"] and s2["split_m3"]["our_error"] == 0


def test_own_must_locate_every_engine_panel():
    with pytest.raises(R.Refused):
        tcr("31", own={"A": "30", "B": "2.4", "C": "1.1"})


def test_convention_check_other_storey():
    assert tcr("31", other=[("GF", "206.68", "207")])["same_convention"] is True
    assert tcr("31", other=[("GF", "205.9", "207")])["same_convention"] is False


# ---------------------------------------------------------------- R-T688-3 region label vs physical element
def test_member_strip_normal():
    r = R.face_owner(0.30, 4.25, own_level_mark=False, member_sections_m=[0.30])
    assert r["owner"] == "MEMBER_STRIP" and r["line_family"] == "B10-04"


def test_panel_with_own_level_mark_adverse():
    r = R.face_owner(0.95, 1.20, own_level_mark=True, member_sections_m=[0.30])
    assert r["owner"] == "GROUND_SLAB" and r["line_family"] == "B10-05"
    assert R.face_owner(1.20, 0.95, own_level_mark=False, member_sections_m=[0.30])["owner"] == "GROUND_SLAB"
    assert R.face_owner(0.25, 2.0, own_level_mark=False, member_sections_m=[0.30])["owner"] == "UNRESOLVED"
    assert R.band_refused(0.95, [0.30]) and not R.band_refused(0.30, [0.30])
    with pytest.raises(R.Refused):
        R.face_owner(0, 1, own_level_mark=False, member_sections_m=[0.3])


# ---------------------------------------------------------------- development villa (committed files only)
def test_development_villa_statement_reproduces():
    import t688_alsenan as A
    s = A.build()
    js = json.dumps(s, indent=1, default=str) + "\n"
    assert (ROOT / "research/agents_t688/out/T688_STATEMENT.json").read_text(encoding="utf-8") == js
    assert (ROOT / "research/agents_t688/out/T688_STATEMENT.md").read_text(encoding="utf-8") == A.render(s)


def test_development_villa_numbers():
    import t688_alsenan as A
    a = A.build()["slab_1f"]
    assert a["difference_m3"] == "-0.556333" and a["located"] == 22 and a["our_error"] is False
    assert abs(X(a["own_minus_engine_m2"])) <= X("0.005")
    d = X(a["difference_m3"])
    rlo, rhi = (X(v) for v in a["split_m3"]["reference rounding band"])
    slo, shi = (X(v) for v in a["split_m3"]["reference scope band"])
    assert slo + rhi == d and shi + rlo == d                 # every m3 of the difference sits in the two bands
    assert a["status"] == "UNRESOLVED_AMBIGUOUS" and a["fitting_subsets"] > 1
    assert a["same_convention"] is True
    assert all(c["fits"] for c in a["candidates"])


def test_development_villa_f_v_p18_2():
    import t688_alsenan as A
    f = A.build()["f_v_p18_2"]
    assert f["owner"]["owner"] == "GROUND_SLAB" and f["band_pairing_refused"] is True
    assert f["own"]["m3_at_0.10"] == "0.114000" and f["engine"]["m3"] == 0.114
    assert f["own"]["neighbour_widths_m"] == [0.3] and f["own"]["neighbours"] == 4
