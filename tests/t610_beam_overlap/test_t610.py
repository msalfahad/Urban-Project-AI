"""T-610: beam band overlap counted once (R-T610-1). Synthetic non-Alsenan fixtures (hand-calculated) + the committed
development-villa census (internal arithmetic and the F-C-P03-2 reproduction)."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pytest
from shapely import affinity
from shapely.geometry import Polygon, box

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t610"))
import t610_rules as R  # noqa: E402

CENSUS = ROOT / "research" / "agents_t610" / "out" / "T610_BEAM_OVERLAP_CENSUS.json"
S2 = math.sqrt(2.0)


# ---- fixture 1: an oblique deep beam B (0.60 x 0.80) starts at a column corner and crosses the strip of a shallow
# beam A (0.25 x 0.50) that runs east from the same column face. Column x -0.80..0, y 0..0.25.
# B's east face starts at the column corner (0, 0.25) and runs at -45 deg; its west face starts on the column's
# bottom edge (y = 0, x = 0.25 - 0.60 x sqrt2 = -0.598528). Common block in A's strip east of the column and west
# of B's east face: triangle (0,0) (0.25,0) (0,0.25) = 0.25 x 0.25 / 2 = 0.03125 m2 (hand).
COL = box(-0.80, 0.0, 0.0, 0.25)
FACE_E = [((0.0, 0.25), (3.0, -2.75))]
X2 = 0.25 - 0.60 * S2
FACE_W = [((X2, 0.0), (X2 + 3.0, -3.0))]
A_DRAWN = box(0.0, 0.0, 4.0, 0.25)
TRI = 0.03125


def b_drawn():
    return R.drawn_outline(FACE_E, FACE_W)


def members(b_billed, a_billed=A_DRAWN, dA=0.50, dB=0.80):
    return {"id": "A", "depth_m": dA, "billed_poly": a_billed}, {"id": "B", "depth_m": dB, "billed_poly": b_billed}


def test_zone_is_the_hand_triangle():
    z = R.zone(A_DRAWN, b_drawn(), [COL])
    assert z.area == pytest.approx(TRI, abs=1e-9)


def test_normal_shallow_beam_bills_block_deeper_stops_at_its_face():
    """Engine like the development villa: A's rectangle bills the whole block at 0.50, B's run stops at A's face."""
    z = R.zone(A_DRAWN, b_drawn(), [COL])
    A, B = members(R.minus(R.minus(b_drawn(), COL), A_DRAWN))
    rec = R.account_zone(z, A, B)
    assert rec["in_A_only_m2"] == pytest.approx(TRI, abs=1e-9) and rec["in_both_m2"] == pytest.approx(0, abs=1e-12)
    assert rec["engine_m3"] == pytest.approx(TRI * 0.50, abs=1e-9)              # 0.015625
    assert rec["physical_m3"] == pytest.approx(TRI * 0.80, abs=1e-9)            # 0.025000
    assert rec["DEPTH_m3"] == pytest.approx(-TRI * 0.30, abs=1e-9)              # -0.009375, the deeper part lost
    assert rec["DOUBLE_m3"] == 0 and rec["verdict"] == "ENGINE_WRONG_UNDER"
    own = R.owner_split(rec, A, B)
    assert own["owner"] == "B"
    assert own["lines"]["A"]["change_m3"] == pytest.approx(-0.015625, abs=1e-9)
    assert own["lines"]["B"]["change_m3"] == pytest.approx(0.025, abs=1e-9)


def test_adverse_block_billed_by_both_lines_is_a_double_count():
    """Adverse: B's run also bills the block (its drawn band to the column corner): billed twice."""
    z = R.zone(A_DRAWN, b_drawn(), [COL])
    A, B = members(R.minus(b_drawn(), COL))
    rec = R.account_zone(z, A, B)
    assert rec["in_both_m2"] == pytest.approx(TRI, abs=1e-9)
    assert rec["DOUBLE_m3"] == pytest.approx(TRI * 0.50, abs=1e-9)              # the shallower depth, billed twice
    assert rec["engine_minus_physical_m3"] == pytest.approx(TRI * 0.50, abs=1e-9)
    assert rec["verdict"] == "ENGINE_WRONG_DOUBLE_COUNT"
    with pytest.raises(R.Refused):
        R.refuse_double([{"pair": "A x B", "owner_lines": {"A": rec["in_both_m2"] * 0.5,
                                                           "B": rec["in_both_m2"] * 0.8}}])


def test_owner_rule_once_passes_the_guard_and_total_is_owner_independent():
    z = R.zone(A_DRAWN, b_drawn(), [COL])
    A, B = members(R.minus(R.minus(b_drawn(), COL), A_DRAWN))
    rec = R.account_zone(z, A, B)
    own = R.owner_split(rec, A, B)
    R.refuse_double([{"pair": "A x B", "owner_lines": {k: v["should_m3"] for k, v in own["lines"].items()}}])
    total_should = sum(v["should_m3"] for v in own["lines"].values())
    assert total_should == pytest.approx(rec["physical_m3"], abs=1e-12)


@pytest.mark.parametrize("op", ["mirror", "rotate", "mm_then_m"])
def test_invariant_under_mirror_rotation_and_units(op):
    def f(g):
        if op == "mirror":
            return affinity.scale(g, xfact=-1, origin=(0, 0))
        if op == "rotate":
            return affinity.rotate(g, 33.0, origin=(1.3, -0.7))
        mm = affinity.scale(g, 1000, 1000, origin=(0, 0))              # drawn in mm, converted once to metres
        return affinity.scale(mm, 0.001, 0.001, origin=(0, 0))
    z = R.zone(f(A_DRAWN), f(b_drawn()), [f(COL)])
    A, B = members(f(R.minus(R.minus(b_drawn(), COL), A_DRAWN)), a_billed=f(A_DRAWN))
    rec = R.account_zone(z, A, B)
    assert rec["zone_m2"] == pytest.approx(TRI, abs=1e-7)          # the 1e-7 m snap grid moves an area < 1e-7 m2
    assert rec["DEPTH_m3"] == pytest.approx(-TRI * 0.30, abs=1e-7)


def test_missing_depth_is_held_never_zero():
    z = R.zone(A_DRAWN, b_drawn(), [COL])
    A, B = members(R.minus(b_drawn(), COL), dB=None)
    rec = R.account_zone(z, A, B)
    assert rec["state"] == "HELD" and rec["verdict"] == "HELD"
    assert "engine_m3" not in rec and "physical_m3" not in rec
    assert R.owner_split(rec, A, B) is None


# ---- fixture 2: a T junction. D (0.30 x 0.60) runs along x; C (0.20 x 0.40) frames in from the north and its drawn
# faces stop at D's north face (y = 0.30).
D_RECT = box(-2.0, 0.0, 2.0, 0.30)
C_FACES = ([((-0.10, 0.30), (-0.10, 3.0))], [((0.10, 0.30), (0.10, 3.0))])


def test_t_junction_drawn_face_to_face_has_no_common_block():
    c = R.drawn_outline(*C_FACES)
    z = R.zone(D_RECT, c)
    assert z.area == pytest.approx(0.0, abs=1e-12)
    C = {"id": "C", "depth_m": 0.40, "billed_poly": c}
    D = {"id": "D", "depth_m": 0.60, "billed_poly": D_RECT}
    assert R.billed_outside_zone(z, C, D) is None


def test_adverse_schedule_rectangle_to_the_axis_is_refused_and_caught():
    """Adverse: C taken as its schedule rectangle to D's axis (y = 0.15) instead of its drawn band."""
    sched = box(-0.10, 0.15, 0.10, 3.0)
    with pytest.raises(R.Refused):
        R.refuse_schedule_rectangle(sched, *C_FACES)
    assert R.refuse_schedule_rectangle(R.drawn_outline(*C_FACES), *C_FACES).area == pytest.approx(0.54, abs=1e-9)
    z = R.zone(D_RECT, R.drawn_outline(*C_FACES))
    C = {"id": "C", "depth_m": 0.40, "billed_poly": sched}
    D = {"id": "D", "depth_m": 0.60, "billed_poly": D_RECT}
    out = R.billed_outside_zone(z, C, D)
    assert out["billed_twice_outside_zone_m2"] == pytest.approx(0.20 * 0.15, abs=1e-9)
    assert out["DOUBLE_m3"] == pytest.approx(0.03 * 0.40, abs=1e-9)


def test_adverse_oblique_drawn_band_replaced_by_perpendicular_rectangle_is_refused():
    rect_b = Polygon([(0.0, 0.25), (3.0, -2.75), (3.0 - 0.6 / S2, -2.75 - 0.6 / S2), (-0.6 / S2, 0.25 - 0.6 / S2)])
    with pytest.raises(R.Refused):
        R.refuse_schedule_rectangle(rect_b, FACE_E, FACE_W)


def test_one_face_alone_is_not_a_band():
    with pytest.raises(R.Refused):
        R.drawn_outline(FACE_E, [])


# ---- the committed development-villa census (arithmetic only; the build needs the private drawing)
@pytest.fixture(scope="module")
def census():
    return json.loads(CENSUS.read_text(encoding="utf-8"))


def test_fcp032_reproduced_to_1e6(census):
    f = census["F_C_P03_2"]
    assert f["zone_m2"] == pytest.approx(0.014761, abs=1e-6)
    assert f["B1_line_excess_vs_net_m3"] == pytest.approx(0.005295, abs=1e-6)
    assert f["B1_bills_m2"] + f["B27_run_bills_m2"] + f["both_m2"] + f["neither_m2"] == pytest.approx(f["zone_m2"],
                                                                                                         abs=2e-6)
    assert f["both_m2"] == 0.0                         # billed once on the candidate, not twice
    assert f["verdict"] == "ENGINE_WRONG_UNDER"
    assert f["physical_m3"] == pytest.approx(0.014761 * 0.85, abs=2e-6)


def test_every_zone_splits_exactly_and_storeys_re_add(census):
    tot = {}
    for z in census["zones"]:
        if z["state"] != "MEASURED":
            assert z["verdict"] == "HELD" and z.get("engine_m3") is None
            continue
        assert z["DOUBLE_m3"] + z["DEPTH_m3"] + z["OMISSION_m3"] == pytest.approx(z["engine_minus_physical_m3"],
                                                                                 abs=3e-6)
        parts = z["in_A_only_m2"] + z["in_B_only_m2"] + z["in_both_m2"] + z["in_neither_m2"]
        assert parts == pytest.approx(z["zone_m2"], abs=4e-6)
        t = tot.setdefault(z["storey"], [0.0, 0.0])
        t[0] += z["engine_minus_physical_m3"]
        t[1] += z["DOUBLE_m3"]
    for st, (diff, dbl) in tot.items():
        assert census["per_storey"][st]["engine_minus_physical_m3"] == pytest.approx(diff, abs=1e-5)
        assert census["per_storey"][st]["DOUBLE_m3"] == pytest.approx(dbl, abs=1e-5)


def test_fix_rows_cover_every_measured_difference(census):
    measured = [z for z in census["zones"] if z["state"] == "MEASURED" and abs(z["engine_minus_physical_m3"]) > 1e-6]
    assert len(census["fix_rows"]) == len(measured)
    for f in census["fix_rows"]:
        assert f["verdict"].startswith("ENGINE_WRONG")
        assert f["id"].startswith("FR-T610-")


def test_no_coordinates_in_the_tracked_output():
    text = CENSUS.read_text(encoding="utf-8")
    assert '"polygon"' not in text and '"pts"' not in text and "origin" not in text
