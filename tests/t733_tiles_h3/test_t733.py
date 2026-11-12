"""T-733: one step-line set before footprints are summed or unioned, a closed slab is no void, census against the live
record (R-T733-1 .. -4).

Villa K733 is hand-made (not the development villa). Two straight flights in line, 1.00 wide, every step drawn as a
pair of lines 0.05 apart (set N = nosing lines, set R = riser lines, R = N + 0.05). Flight A: 10 goings of 0.30, set N
x 0 .. 3.00, set R 0.05 .. 3.05. Flight B continues: 7 goings of 0.30, set N 3.00 .. 5.10, set R 3.05 .. 5.15. The
stair outline (stringer end / void edge) is at x 5.15 (the R set's last line).
Hand: one set (N or R): A 3.00 + B 2.10 = 5.10 = union, overlap 0. Mixed (A on R, B on N): A 0.05 .. 3.05 = 3.00,
B 3.00 .. 5.10 = 2.10, overlap 0.05 x 1.00 = 0.05, union 5.05, sum 5.10: a SET_MIX, flight lines kept (3.00 / 2.10).
Adverse: B truly starts at 2.95 on both sets: the overlap 0.05 survives every one-set reading: PHYSICAL_OVERLAP.
The last tests rebuild the development-villa outputs from committed files."""
from __future__ import annotations

import json
import subprocess
import sys
from decimal import Decimal as X
from pathlib import Path

import pytest
from shapely import affinity
from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t733"))
import t733_rules as R  # noqa: E402


def _tf(g, deg=0.0, mirror=False, scale=1.0):
    if mirror:
        g = affinity.scale(g, xfact=-1, yfact=1, origin=(0, 0))
    g = affinity.rotate(g, deg, origin=(0, 0))
    return affinity.scale(g, xfact=scale, yfact=scale, origin=(0, 0))


def _reading(a, b, **kw):
    s = kw.get("scale", 1.0)
    A, B = _tf(a, **kw), _tf(b, **kw)
    k = 1.0 / (s * s)                                         # back to m2 (scale 1000 = millimetres)
    return (round(A.area * k, 6), round(B.area * k, 6), round(A.intersection(B).area * k, 6),
            round(A.union(B).area * k, 6))


A_N, A_R = box(0, 0, 3.00, 1), box(0.05, 0, 3.05, 1)
B_N, B_R = box(3.00, 0, 5.10, 1), box(3.05, 0, 5.15, 1)


def _pairs(**kw):
    return {"mixed": _reading(A_R, B_N, **kw), "set_a": _reading(A_N, B_N, **kw), "set_b": _reading(A_R, B_R, **kw)}


def test_normal_hand_set_mix_keeps_flight_lines():
    p = _pairs()
    assert p["mixed"] == (3.0, 2.1, 0.05, 5.05)
    assert p["set_a"] == (3.0, 2.1, 0.0, 5.1) and p["set_b"] == (3.0, 2.1, 0.0, 5.1)
    v = R.one_set_reading(p)
    assert v["result"] == "SET_MIX" and v["overlap_m2"] == X("0.050000")
    assert v["union_understated_by_m2"] == X("0.050000") and v["clean_sets"] == ["set_a", "set_b"]
    assert v["flight_lines"].startswith("KEEP")


@pytest.mark.parametrize("kw", [dict(deg=90), dict(deg=37.5), dict(mirror=True), dict(mirror=True, deg=-120),
                                dict(scale=1000.0)])
def test_mirror_rotation_mm_same_verdict(kw):
    v = R.one_set_reading(_pairs(**kw))
    assert v["result"] == "SET_MIX" and v["overlap_m2"] == X("0.050000")


def test_adverse_physical_overlap_survives_one_set():
    b_n, b_r = box(2.95, 0, 5.05, 1), box(3.00, 0, 5.10, 1)          # B really starts 0.05 inside A on both sets
    p = {"mixed": _reading(A_R, b_n), "set_a": _reading(A_N, b_n), "set_b": _reading(A_R, b_r)}
    v = R.one_set_reading(p)
    assert v["result"] == "PHYSICAL_OVERLAP" and v["overlap_m2"] == X("0.050000")
    assert v["flight_lines"].startswith("UNION INCREMENT")


def test_adverse_missing_reading_is_held_never_zero():
    p = _pairs()
    p["set_b"] = (3.0, None, 0.0, 5.1)
    v = R.one_set_reading(p)
    assert v["result"] == "HELD" and "never 0" in v["cause"]
    del p["set_b"]
    assert R.one_set_reading(p)["result"] == "HELD"


def test_no_overlap_no_finding():
    p = {k: _reading(A_N, B_N) for k in ("mixed", "set_a", "set_b")}
    assert R.one_set_reading(p)["result"] == "NO_OVERLAP"


def test_governing_set_from_outline_and_named_range():
    assert R.governing_set({"set_a": False, "set_b": True}) == {"set": "set_b", "basis": "end lines on the drawn outline"}
    for case in ({"set_a": False, "set_b": False}, {"set_a": True, "set_b": True}):
        g = R.governing_set(case)
        assert g["set"] is None and "named range" in g["basis"]          # never chosen by size


def test_ceiling_void_closed_slab_open_slab_and_no_slab():
    closed = R.ceiling_void(slab_drawing=True, opening_drawn=False, beams_cross=True)
    assert closed["result"] == "NOT_A_VOID" and closed["m2"] == X("0") and "beams cross" in closed["cause"]
    assert R.ceiling_void(True, True)["result"] == "DRAWN_OPENING"
    held = R.ceiling_void(slab_drawing=False, opening_drawn=None)
    assert held["status"] == "HELD" and held["m2"] is None                 # no drawing: never 0
    with pytest.raises(R.RuleError):
        R.ceiling_void(slab_drawing=True, opening_drawn=None)               # unread is not 'closed'


def test_stale_entries_normal_and_adverse():
    old = {"L-1": {"class": "HELD", "held_high": 1.0}, "L-2": {"class": "RELEASED", "measured_net": 2.0}}
    assert R.stale_entries(old, dict(old)) == ([], [])
    live = {"L-1": {"class": "HELD", "held_high": 1.1}}
    assert R.stale_entries(old, live) == (["L-1"], ["L-2"])


# ---------------------------------------------------------------- development villa (committed files only)

OUTD = ROOT / "research" / "agents_t733" / "out" / "T733_H3_READINESS.json"


def test_development_villa_rebuild_is_identical():
    r = subprocess.run([sys.executable, "-I", str(ROOT / "research" / "agents_t733" / "t733_alsenan.py"), "--check"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_development_villa_results_pinned():
    d = json.loads(OUTD.read_text())
    a, b, c = d["a_tread_highs"], d["b_v07"], d["c_census"]
    assert a["verdict"]["result"] == "SET_MIX" and a["governing_set"]["set"] == "set_layer2"
    assert all(l["verdict"] == "ENGINE_RIGHT" and l["change"] == "none" for l in a["lines"])
    assert a["own_readings"]["set_layer2"]["union_m2"] == a["own_readings"]["set_layer2"]["sum_m2"] == 7.544412
    assert a["own_readings"]["mixed_engine"]["union_m2"] == 7.486974
    assert b["after"]["result"] == "NOT_A_VOID" and b["evidence"]["s_opening_entities_on_sheet"] == 0
    assert b["evidence"]["overlay"]["matched_st"] == 9
    assert c["stale_vs_v3069"] == {"stale": 0, "missing": 0, "added": 0} and c["wiring"]["stale_hosts"] == []
    assert c["lines"] == 321 and c["held"] == 127
