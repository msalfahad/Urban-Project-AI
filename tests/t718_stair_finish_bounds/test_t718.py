"""T-718: skirting piece datum (R-T718-1), stopper-to-stopper ceilings (R-T718-2) and drawn floors (R-T718-3).
Villa V718 is hand-made (not the development villa): a straight flight of 8 risers / 7 goings 0.28 with a drawn nosing
projection 0.04, a column 0.50 .. 0.90 and a window jamb at 1.50 on its wall; a round flight with outline radii
0.12 / 0.41 and a front at offset 0.09 (Pythagorean 9-12-15 / 9-40-41: chord 0.28 exactly) and a curtail arc 0.10;
a winder square 0.75 x 1.00 (diameter 1.25). The last tests rebuild the development-villa ledger from committed files."""
from __future__ import annotations

import json
import math
import subprocess
import sys
from decimal import Decimal as X
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t718"))
import t718_rules as R  # noqa: E402

DW = R.DRAWN
FR = [X("0.28") * k for k in range(8)]                  # front edges 0 .. 1.96
FA = [v + X("0.04") for v in FR]                          # riser faces 0.04 uphill
CUTS = ["0.50", "0.90", "1.50"]


def P(**kw):
    a = dict(fronts=[str(v) for v in FR], faces=[str(v) for v in FA], cuts=CUTS)
    a.update(kw)
    return R.pieces(**a)


# ------------------------------------------------------------------ R-T718-1 normal (hand)
def test_pieces_front_edge_datum_hand():
    r = P()
    assert r["projection_m"] == X("0.04") and r["run_m"] == X("1.96")
    assert r["front_edge"]["plans_m"] == [X("0.50"), X("0.40"), X("0.60"), X("0.46")]
    assert r["riser_face"]["plans_m"] == [X("0.46"), X("0.40"), X("0.60"), X("0.50")]
    assert r["risers"] == [2, 2, 2, 2] and r["risers_by_front"] == [2, 2, 2, 2] and not r["cut_inside_projection"]
    assert r["datum_shift_first_last_m"] == (X("0.04"), X("-0.04"))
    assert sum(r["front_edge"]["plans_m"]) == sum(r["riser_face"]["plans_m"]) == X("1.96")


def test_jamb_on_a_face_keeps_the_riser_downhill():
    r = P(cuts=["0.60"])                                  # the face of riser 3
    assert r["risers"] == [3, 5] and r["risers_by_front"] == [3, 5]


def test_cut_inside_projection_face_governs_and_flags():
    r = P(cuts=["0.58"])                                  # front 3 at 0.56 < cut < face 3 at 0.60
    assert r["cut_inside_projection"] and r["risers"] == [2, 6] and r["risers_by_front"] == [3, 5]


def test_mirror_and_rotation_give_the_same_pieces():
    base = P()
    # mirrored flight (walks toward -y): stations measured uphill from the first front edge are the same
    ys = [X("10") - v for v in FR]
    fr = [ys[0] - y for y in ys]
    assert R.pieces(fronts=[str(v) for v in fr], faces=[str(v + X("0.04")) for v in fr], cuts=CUTS)["front_edge"] == \
        base["front_edge"]
    # rotated 37 deg: project rotated points on the rotated axis
    c, s = math.cos(math.radians(37)), math.sin(math.radians(37))
    pts = [(float(v) * c, float(v) * s) for v in FR]
    st = [round(x * c + y * s, 9) for x, y in pts]
    rr = R.pieces(fronts=[str(v) for v in st], faces=[str(round(v + 0.04, 9)) for v in st], cuts=CUTS)
    assert [round(float(v), 6) for v in rr["front_edge"]["plans_m"]] == [0.5, 0.4, 0.6, 0.46]


# ------------------------------------------------------------------ R-T718-1 adverse
@pytest.mark.parametrize("kw, msg", [
    (dict(faces=[None] * 8), "no drawn pair"),
    (dict(faces=[str(FA[0]), "0.33"] + [None] * 6), "projections differ"),
    (dict(faces=[str(v - X("0.08")) for v in FA]), "not uphill"),
    (dict(cuts=["2.10"]), "outside the flight"),
    (dict(cuts=["0.90", "0.50"]), "strictly increasing"),
    (dict(fronts=[str(v) for v in reversed(FR)]), "strictly increasing"),
    (dict(fronts=[None] + [str(v) for v in FR[1:]]), "missing"),
    (dict(cuts=["0.02"]), "projection of the end edge"),
])
def test_pieces_refusals(kw, msg):
    with pytest.raises(R.Refused, match=msg):
        P(**kw)


def test_pieces_units_refused():
    with pytest.raises(R.Refused, match="metres only"):
        P(unit="mm")


# ------------------------------------------------------------------ R-T718-2 normal (hand)
def test_round_chord_hand():
    c = R.round_front_at_most(offset=(X("0.09"), DW), r_in=(X("0.15"), DW), r_out=(X("0.41"), DW))
    assert c == X("0.28")                                 # 0.40 - 0.12
    assert R.round_front_at_most(offset=(X("0"), DW), r_in=(X("0.15"), DW), r_out=(X("0.41"), DW)) == X("0.26")


def test_curtail_front_hand():
    v = R.curtail_front_at_most(start_r=(X("0.15"), DW), offset=(X("0.09"), DW), r_out=(X("0.41"), DW),
                                curtail_arc=(X("0.10"), DW))
    assert v == X("0.38")


def test_turn_diameter_hand():
    assert R.turn_front_at_most(side_a=(X("0.75"), DW), side_b=(X("1.00"), DW)) == X("1.25")
    assert R.turn_front_at_most(side_b=(X("0.75"), DW), side_a=(X("1.00"), DW)) == X("1.25")   # mirror


# ------------------------------------------------------------------ R-T718-2 adverse: never from a schedule value
@pytest.mark.parametrize("bad", [X("0.41"), ("0.41", "SCHEDULE"), ("0.41", "NOMINAL"), (None, DW), ("0.41",)])
def test_at_most_refuses_non_drawn_inputs(bad):
    with pytest.raises(R.Refused):
        R.round_front_at_most(offset=(X("0.09"), DW), r_in=(X("0.15"), DW), r_out=bad)
    with pytest.raises(R.Refused):
        R.turn_front_at_most(side_a=bad, side_b=(X("1.00"), DW))


def test_at_most_refuses_drawn_end_plus_schedule_width():
    # a drawn inner end with a 'lane width from the schedule' as the outer stopper is refused
    with pytest.raises(R.Refused, match="drawn source"):
        R.curtail_front_at_most(start_r=(X("0.15"), DW), offset=(X("0.09"), DW), r_out=(X("0.41"), "SCHEDULE"),
                                curtail_arc=(X("0.10"), DW))


@pytest.mark.parametrize("off, ri, ro", [("0.20", "0.15", "0.41"), ("0.09", "0.41", "0.15"), ("-0.01", "0.15", "0.41")])
def test_chord_geometry_refusals(off, ri, ro):
    with pytest.raises(R.Refused):
        R.round_front_at_most(offset=(X(off), DW), r_in=(X(ri), DW), r_out=(X(ro), DW))


# ------------------------------------------------------------------ R-T718-3
def test_drawn_floor_and_lane_cap():
    assert R.drawn_floor([("a", "1.20"), ("b", "1.15")]) == X("2.35")
    assert R.drawn_floor([("a", "1.20"), ("b", "1.15")], lane=(X("1.15"), DW)) == X("2.30")
    with pytest.raises(R.Refused):
        R.drawn_floor([("", "1.20")])
    with pytest.raises(R.Refused):
        R.drawn_floor([("a", None)])
    with pytest.raises(R.Refused):
        R.drawn_floor([("a", "1.20")], lane=(X("1.15"), "SCHEDULE"))


# ------------------------------------------------------------------ development villa (committed files only)
LED = ROOT / "research" / "agents_t718" / "out" / "T718_LEDGER.json"


def test_ledger_reproduces():
    p = subprocess.run([sys.executable, "-I", str(ROOT / "research" / "agents_t718" / "t718_alsenan.py"), "--check"],
                       capture_output=True, text=True, cwd=ROOT)
    assert p.returncode == 0, p.stderr
    assert "REPRODUCED" in p.stdout


def test_fv715_1_closed_to_the_datum():
    d = json.loads(LED.read_text())["f_v715_1"]
    assert (d["walled_plan_front_edge_m"], d["walled_plan_riser_face_m"]) == ("2.250000", "2.200000")
    assert d["difference_m"] == d["nosing_projection_m"] == "0.050000"
    assert (d["window_plan_front_edge_m"], d["window_plan_riser_face_m"]) == ("1.050000", "1.100000")


def test_cut_pieces_agree_with_t410():
    rows = json.loads(LED.read_text())["cut_pieces"]
    assert len(rows) == 14 and all(r["t410_agrees_front_edge"] for r in rows)
    ms2 = {r["piece"]: (r["plan_front_edge_m"], r["risers"]) for r in rows if r["flight"] == "MS2-L"}
    assert ms2 == {"MS2-L.W1": ("1.000000", 4), "MS2-L.W1C": ("0.500000", 1), "MS2-L.W1B": ("0.750000", 3),
                   "MS2-L.W2": ("1.050000", 4)}


def test_bounds_pins_and_never_zero():
    led = json.loads(LED.read_text())
    got = {(r["element_id"], r["item_code"]): r["after"] for r in led["lines"]}
    pins = {("1F-R78C367:flight 5", "FIN.MARBLE.RISER"): ("RANGE", "0.785833", "1.111337"),
            ("1F-R78C367:flight 5", "FIN.STAIR.STEP_LM"): ("RANGE", "5.750000", "8.131728"),
            ("GF-RC99C2A:flight 1", "FIN.MARBLE.RISER"): ("RANGE", "1.803598", "2.131176"),
            ("GF-RC99C2A:flight 1", "FIN.STAIR.STEP_LM"): ("RANGE", "13.800000", "16.521440"),
            ("STAIR:ST-01:soffit", "FIN.STAIR.SOFFIT"): ("AT_LEAST", "20.423364", None),
            ("STAIR:ST-02:soffit", "FIN.STAIR.SOFFIT"): ("AT_LEAST", "4.460946", None)}
    assert {k: (v["class"], v["low"], v["high"]) for k, v in got.items()} == pins
    for r in led["lines"]:
        a, b = r["after"], r["before"]
        assert X(a["low"]) > 0 and X(a["low"]) >= X(b["low"])             # a floor never drops
        assert a["high"] is None or X(a["high"]) >= X(a["low"])
        assert a["value"] is None                                          # no point value invented
