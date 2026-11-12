"""T-751 exterior paint edge / corner bound closure (R-T751-1 .. -4): synthetic facade V751 by hand (normal +
adverse) and the development villa pinned to the committed outputs (no private input needed).

Facade V751 (synthetic, not the development villa), by hand. Box with a roof at +3.00 (datum of the parapet corners):
  corner A: both faces printed to the parapet top +3.80                         -> 3.80 - 3.00 = 0.80 lm
  corner B: the corner outline drawn to +3.20, an end round r 0.20 to the top +3.40
            -> vertical arris to the tangent point 3.40 - 0.20 - 3.00 = 0.20 lm; the round pi x 0.20 / 2 = 0.314159
               belongs to the top-edge run (shown, not added)
  corner C: parapet height not printed and not drawn                            -> stays HELD 0 .. 0.80, never 0
  corners A + B + C = 1.00 .. 1.80 lm; the group bound 0 .. 2.40 closes to 1.00 when C is read later at +3.00 (0.00)
  arched window: w 1.00, sill +0.50, springing +1.80, semicircular head developed pi x 0.50 = 1.570796
            -> 2 x 1.30 + 1.570796 = 4.170796 lm; the rectangle to the crown +2.30: 2 x 1.80 + 1.00 = 4.60 (refused)
  plane: stones on the front layer over a door drawn beyond -> OFF_FACE (no deduction on the door's face)
  adverse: a top in mm (3800) refused; a top below the datum refused; no top and no bound refused; a closed value
  outside its bound refused; a closure without handles refused; a head in mm refused; a head shorter than its span
  refused; a developed head 0.002 off its ledger refused; rotation 0 / 30 / -121 deg and a mirror give the same head.
"""
import json
import math
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t751"
sys.path.insert(0, str(HERE))
import t751_rules as R  # noqa: E402

OUT = HERE / "out" / "T751_EDGE_BOUNDS.json"
OUT_MD = HERE / "out" / "T751_EDGE_BOUNDS.md"
CENSUS = HERE / "in" / "T751_CENSUS.json"
D = Decimal


# ------------------------------------------------------------------ synthetic V751 (by hand)

def test_corner_printed_both_faces():
    it = R.corner_extra("A", "3.00", top="3.80", source="printed")
    assert it["lm"] == ["0.800000", "0.800000"] and it["state"] == "DRAWN" and it["round_lm"] is None


def test_corner_end_round_stops_at_tangent():
    it = R.corner_extra("B", "3.00", top="3.40", round_r="0.20", source="drawn")
    assert it["lm"] == ["0.200000", "0.200000"]
    assert it["tangent"] == "3.200000" and it["round_lm"] == "0.314159"


def test_unprinted_parapet_keeps_corner_held():
    it = R.corner_extra("C", "3.00", top=None, held=("0", "0.80"), source="parapet height not printed")
    assert it["state"] == "HELD" and it["lm"] == ["0.000000", "0.800000"]


def test_group_sum_and_closure():
    a = R.corner_extra("A", "3.00", top="3.80")
    b = R.corner_extra("B", "3.00", top="3.40", round_r="0.20")
    c = R.corner_extra("C", "3.00", top=None, held=("0", "0.80"))
    assert R.sum_lm([a, b, c])["lm"] == ["1.000000", "1.800000"]
    c2 = R.corner_extra("C", "3.00", top="3.00")
    tot = R.sum_lm([a, b, c2])["lm"]
    assert tot == ["1.000000", "1.000000"]
    cl = R.close_bound("V751 parapet ends", "0", "2.40", tot[0], ["h1", "h2"])
    assert cl["after"] == "1.000000" and cl["narrowed_by"] == "2.400000"


def test_blank_item_never_zero():
    s = R.sum_lm([{"corner": "X", "lm": None}, R.corner_extra("A", "3.00", top="3.80")])
    assert s["blank"] == ["X"] and s["lm"] == ["0.800000", "0.800000"]


@pytest.mark.parametrize("kw", [dict(top="3800"), dict(top="2.90"), dict(top=None), dict(top="3.10", round_r="0.20"),
                                dict(top="3.40", round_r="-0.1"), dict(top=None, held=("0.5", "0.2"))])
def test_corner_adverse_refused(kw):
    with pytest.raises(R.RuleError):
        R.corner_extra("Z", "3.00", **kw)


def test_mm_datum_refused():
    with pytest.raises(R.RuleError):
        R.corner_extra("Z", "3000", top="3.80")


def _semicircle(cx, cy, r, n=64):
    return [(cx - r * math.cos(math.pi * i / n), cy + r * math.sin(math.pi * i / n)) for i in range(n + 1)]


def _rot(pts, deg, mirror=False):
    a = math.radians(deg)
    out = []
    for x, y in pts:
        if mirror:
            x = -x
        out.append((x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)))
    return out


def test_arched_developed_governs():
    head = R.polyline_length(_semicircle(0.0, 1.80, 0.50, n=2000))
    assert abs(head - D("1.570796")) <= D("0.000001")
    it = R.arched_edge("W1", sill="0.50", springing="1.80", head_developed=head, width="1.00", crown="2.30")
    assert it["lm"] == R.s6(D("2.60") + head) and it["rectangle_refused"] == "4.600000"
    assert D(it["rectangle_minus_developed"]) == D("4.60") - D(it["lm"])


@pytest.mark.parametrize("deg,mirror", [(0, False), (30, False), (-121, False), (47, True)])
def test_head_length_rotation_mirror(deg, mirror):
    base = R.polyline_length(_semicircle(0.0, 1.80, 0.50, n=500))
    assert R.polyline_length(_rot(_semicircle(0.0, 1.80, 0.50, n=500), deg, mirror)) == base


def test_head_in_mm_refused():
    with pytest.raises(R.RuleError):
        R.polyline_length([(0, 0), (1000, 0)], unit="mm")


@pytest.mark.parametrize("kw", [dict(head_developed="0.90"), dict(sill="1.90"), dict(width="0"),
                                dict(ledger="4.172800")])
def test_arched_adverse_refused(kw):
    base = dict(sill="0.50", springing="1.80", head_developed="1.570796", width="1.00", crown="2.30")
    base.update(kw)
    with pytest.raises(R.RuleError):
        R.arched_edge("W1", **base)


def test_arched_ledger_within_tolerance():
    it = R.arched_edge("W1", sill="0.50", springing="1.80", head_developed="1.570796", width="1.00", crown="2.30",
                       ledger="4.1712")
    assert it["ledger_diff"] == "-0.000404"


def test_plane_attribution():
    assert R.plane_attribution("1", "1") == "ON_FACE"
    assert R.plane_attribution("1", "5") == "OFF_FACE"
    with pytest.raises(R.RuleError):
        R.plane_attribution("5", "1")


@pytest.mark.parametrize("args", [("x", "0", "1", "1.2", ["h"]), ("x", "0", "1", "0.5", []), ("x", "1", "0", "0.5",
                                                                                                ["h"])])
def test_close_bound_refusals(args):
    with pytest.raises(R.RuleError):
        R.close_bound(*args)


# ------------------------------------------------------------------ development villa (committed outputs)

@pytest.fixture(scope="module")
def out():
    return json.loads(OUT.read_text(encoding="utf-8"))


def test_rebuild_equals_committed():
    sys.path.insert(0, str(HERE))
    import t751_alsenan as A
    d = A.build()
    assert json.dumps(d, ensure_ascii=False, indent=1, sort_keys=True) + "\n" == OUT.read_text(encoding="utf-8")
    assert A.md(d) == OUT_MD.read_text(encoding="utf-8")


def test_parapet_end_corners(out):
    got = {it["corner"]: it["lm"][0] for it in out["corners"]["parapet_ends"]}
    assert got == {"NE-2/SE-1": "1.600000", "NW-1/NW-2": "1.300000", "NW-2/NW-3": "1.300000",
                   "NW-3/NE-1": "1.300000", "NW-5/NE-2": "0.900000", "SE-1/SW-2": "0.185812",
                   "SW-1/NW-5": "1.300000", "SW-3/NW-1": "1.300000"}
    assert out["corners"]["parapet_ends_lm"] == ["9.185812", "9.185812"]
    above = [it["corner"] for it in out["corners"]["parapet_ends"] if it["cap_check"].startswith("ABOVE")]
    assert above == ["NE-2/SE-1"]


def test_corner_totals(out):
    c = out["corners"]
    assert c["before_lm"] == ["168.500000", "182.050000"] and c["fixed_part_lm"] == "166.400000"
    assert c["plinth_lm"] == ["2.550000", "2.550000"]
    assert c["after_lm"] == ["178.135812", "179.335812"]
    assert c["after_physical_lm"] == ["179.535812", "180.735812"]
    assert c["stop_end"]["lm"] == ["0.000000", "1.200000"] and c["stop_end"]["state"] == "HELD"
    for cl in c["closures"]:
        assert D(cl["before"][0]) <= D(cl["after"]) <= D(cl["before"][1])


def test_windows(out):
    w = out["windows"]
    assert {it["opening"]: it["lm"] for it in w["arched"]} == {"W15": "6.845844", "W16": "6.845844",
                                                               "W26": "4.070563"}
    assert w["before_lm"] == "103.683100" and w["after_lm"] == "103.682251"
    assert w["t746_minus_after"] == "2.337749" and w["residual"] == "0.000000"
    assert all(abs(D(it["ledger_diff"])) <= D("0.001") for it in w["arched"])


def test_surround(out):
    s = out["surround"]
    assert s["plane"]["attribution"] == "OFF_FACE"
    assert s["t747_zone_m2"] == "1.298383" and s["t360_visible_m2"] == "1.514884"
    assert s["explained"]["residual_m2"] == "0.000000"
    assert s["keystone"]["face_m2"] == "0.134936"
    assert D(s["split_at_ffl_m2"]["below_+1.00"]) == D("0.222500")


def test_paint_lines(out):
    p = out["paint"]
    moved = {ln["line_key"]: ln["paint_after"] for ln in p["lines_moved"]}
    assert moved == {"L-b05f70c92405dbcfbe62": ["376.694149", "410.179149"],
                     "NEW FIN.EXT.FINISH PARAPET-OUTER 1F +9.70": ["54.651307", "60.029307"],
                     "NEW FIN.EXT.FINISH PLINTH GF": ["71.688590", "72.749795"]}
    assert p["total_after"]["paint"] == ["1009.110254", "1087.619176"]
    assert p["total_after"]["render_minus_paint"] == ["0.000000", "0.000000"]
    assert len(p["blank_faces"]) == 6


def test_no_coordinates_in_committed_files():
    import re
    for path in (CENSUS, OUT):
        nums = [abs(float(x)) for x in re.findall(r"-?\d+\.\d+", path.read_text(encoding="utf-8"))]
        assert max(nums) < 2000, path
    assert max(abs(float(x)) for x in re.findall(r"-?\d+\.\d+", CENSUS.read_text(encoding="utf-8"))) < 20
