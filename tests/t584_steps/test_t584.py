"""T-584 steps (R-T584-1): a non-Alsenan hand fixture (entrance 3 steps x 2.40 m, a 14-tread flight x 1.10 m, door
steps), adverse cases (step lm booked as m2, one step owned twice, a default step, an unprinted level as 0, mirror /
rotation / mm), and the development-villa build pinned (byte-identical rebuild, exact closures, units apart)."""
from __future__ import annotations

import importlib.util
import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t584"
sys.path.insert(0, str(HERE))
R = importlib.import_module("t584_rules")
_spec = importlib.util.spec_from_file_location("t584_alsenan", HERE / "t584_alsenan.py")
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)

D = Decimal


# ---- hand fixture (Villa K584, not Alsenan) --------------------------------------------------------------------------
def test_fixture_entrance_three_steps():
    assert R.flight_steps(3, "2.40") == (D("7.20"), 3)


def test_fixture_flight_fourteen_treads():
    assert R.flight_steps(14, "1.10") == (D("15.40"), 14)


def test_fixture_flight_in_mm_equals_m():
    assert R.flight_steps(14, "1100", unit="mm")[0] == D("15.40")


def test_fixture_threshold_step_on_the_face():
    p = R.step_at_opening("K-D1", "0.90", True, False, "+0.45", "+0.30")
    assert p["kind"] == "THRESHOLD_STEP" and p["lm"] == D("0.90") and p["riser_m"] == D("0.15")
    assert p["m2"] == D("0.1350") and p["nr"] == 1 and p["status"] == "DRAWING-CONFIRMED"


def test_fixture_step_beyond_the_face_is_its_own_element():
    p = R.step_at_opening("K-D2", "1.20", False, True, "+0.30", "+0.15")
    assert p["kind"] == "EXT_STEP" and p["lm"] == D("1.20")


def test_fixture_same_level_no_edge_is_not_applicable():
    p = R.step_at_opening("K-D3", None, False, False, "+1.00", "+1.00")
    assert p["kind"] == "NO_STEP" and p["status"] == "NOT_APPLICABLE" and p["nr"] == 0 and p["lm"] is None


def test_fixture_unprinted_level_holds_the_riser_with_a_bound():
    p = R.step_at_opening("K-D4", "0.90", True, False, "+0.30", None, plan_low="+-0.00")
    assert p["status"] == "HELD" and p["riser_m"] is None and p["m2"] is None
    assert p["bound"]["riser_m"] == (D(0), D("0.30")) and p["bound"]["m2"] == (D(0), D("0.270"))


def test_fixture_piece_per_riser_split_closes():
    held, arr, rem = R.piece_per_riser_split(17, 14, 0, 1)      # his 17 pieces: 14 treads + 1 arrival + 2 more
    assert (held, arr, rem) == (0, 1, 2)


def test_fixture_reconcile_closes_exactly():
    g = R.close("K", "lm", D("15.40"), D("16.80"), [
        R.cause("width 14 x (1.10 - 1.20)", D("-1.40"), "ENGINE_RIGHT", "MEASURE", "drawn")])
    assert g["gap"] == D("-1.40") and g["pct"] == D("-8.33")


@pytest.mark.parametrize("ang", [0, 37, 90, 180, 211])
@pytest.mark.parametrize("mirror", [False, True])
def test_edge_length_rotation_mirror_invariant(ang, mirror):
    import math
    o = (1000.0, -500.0)
    a = math.radians(ang)

    def world(x, y):
        x = -x if mirror else x
        return (o[0] + x * math.cos(a) - y * math.sin(a), o[1] + x * math.sin(a) + y * math.cos(a))
    ln, off = R.edge_in_frame(world(50, 0), world(950, 0), o, ang, mirror)
    assert ln == D("0.900") and off == D("0")
    ln2, off2 = R.edge_in_frame(world(50, 50), world(950, 50), o, ang, mirror)
    assert ln2 == D("0.900") and off2 == D("0.050")


# ---- adverse ---------------------------------------------------------------------------------------------------------
def test_step_lm_booked_as_m2_refused():
    with pytest.raises(R.RuleError):
        R.book("m2", "lm", "7.20")
    assert R.book("lm", "lm", "7.20") == D("7.20")


def test_step_owned_by_threshold_and_outdoor_floor_refused():
    with pytest.raises(R.RuleError):
        R.owners_once({"K-D1": ["THRESHOLD:K-D1", "EXT.FLOOR.OUTDOOR:porch"]})
    assert R.owners_once({"K-D1": ["THRESHOLD:K-D1"]}) == 1


def test_default_step_without_an_edge_refused():
    with pytest.raises(R.RuleError):
        R.step_at_opening("K-D5", None, False, False, "+0.30", "+0.15")


def test_edge_between_equal_levels_is_a_conflict():
    with pytest.raises(R.RuleError):
        R.step_at_opening("K-D6", "0.90", True, False, "+0.30", "+0.30")


def test_edge_on_face_and_beyond_refused_as_one_piece():
    with pytest.raises(R.RuleError):
        R.step_at_opening("K-D7", "0.90", True, True, "+0.45", "+0.15")


def test_unprinted_level_without_bound_refused_and_never_zero():
    with pytest.raises(R.RuleError):
        R.step_at_opening("K-D8", "0.90", True, False, "+0.30", None)
    with pytest.raises(R.RuleError):
        R.D(None)


def test_bad_units_and_counts_refused():
    with pytest.raises(R.RuleError):
        R.flight_steps(14, "110", unit="cm")
    with pytest.raises(R.RuleError):
        R.flight_steps(13.5, "1.10")
    with pytest.raises(R.RuleError):
        R.flight_steps(3, "0")


def test_unnamed_residual_and_open_gap_refused():
    with pytest.raises(R.RuleError):
        R.cause(" ", 1, "UNRESOLVED", "MEASURE", "x")
    with pytest.raises(R.RuleError):
        R.close("K", "lm", D("15.40"), D("16.80"), [R.cause("width", D("-1.00"), "ENGINE_RIGHT", "MEASURE", "x")])


def test_held_cause_needs_its_bound_and_verified_refused():
    with pytest.raises(R.RuleError):
        R.cause("held", D("-2.4"), "HELD", "HELD", "x")
    with pytest.raises(R.RuleError):
        R.status_ok("VERIFIED")


def test_held_and_omission_withhold_pct():
    g = R.close("K", "lm", D(0), D("7.20"), [R.cause("no line", D("-7.20"), "ENGINE_OMISSION", "MEASURE", "x")])
    assert g["pct"] is None


# ---- development villa (pinned) ---------------------------------------------------------------------------------------
OUT = HERE / "out" / "T584_STEPS.json"


def _built():
    return json.loads(OUT.read_text(encoding="utf-8"))


def test_alsenan_rebuild_byte_identical():
    assert A.dump(A.build()) == OUT.read_text(encoding="utf-8")


def test_alsenan_edited_input_stops_the_build(monkeypatch):
    monkeypatch.setitem(A.PINS, A.LINE_INDEX, "0000000000000000")
    with pytest.raises(R.RuleError):
        A.build()


def test_alsenan_door_steps():
    o = _built()["openings"]
    assert {k for k, v in o.items() if v["piece"]["kind"] == "THRESHOLD_STEP"} == {
        "D-GF-01", "D-GF-03", "D-GF-05", "D-GF-09", "D-GF-15"}
    assert {k for k, v in o.items() if v["piece"]["kind"] == "NO_STEP"} == {"D-GF-06", "D-GF-07", "D-2F-01"}
    assert not any(v["piece"]["kind"] == "EXT_STEP" for v in o.values())
    assert o["D-GF-09"]["piece"]["status"] == "HELD" and o["D-GF-09"]["piece"]["m2"] is None
    # hand check: 0.90 + 0.80 + 0.90 + 0.90 = 3.50 lm at house doors; risers 0.15 x (0.90 + 0.80 + 0.90) = 0.390 m2
    house = [D(v["piece"]["lm"]) for k, v in o.items() if v["piece"]["lm"] and k != "D-GF-15"]
    assert sum(house) == D("3.5")
    assert sum(D(v["piece"]["m2"]) for k, v in o.items() if v["piece"]["m2"] and k != "D-GF-15") == D("0.390")


def test_alsenan_stair_tables_close_and_hand_check():
    t = {(u, g["id"]): g for u, gs in _built()["tables"]["stairs"].items() for g in gs}
    # ST-01: 9 + 3 + 11 + 11 + 11 = 45 treads x 1.150 = 51.75 vs 63 x 1.20 = 75.60
    assert (t[("lm", "ST-01")]["ours"], t[("lm", "ST-01")]["his"]) == ("51.750", "75.6")
    assert sum(D(c["amount"]) for c in t[("lm", "ST-01")]["causes"]) == D("-23.85")
    # ST-02: 10 + 4 = 14 x 1.150 = 16.10 vs 28 x 1.20 = 33.60
    assert t[("lm", "ST-02")]["ours"] == "16.100" and D(t[("lm", "ST-02")]["gap"]) == D("-17.5")
    # E1: no line; 4 x 2.80 = 11.20 omission + 1 x 2.80 platform edge
    e1 = [c for c in t[("lm", "ST-03")]["causes"] if c["verdict"] == "ENGINE_OMISSION"]
    assert len(e1) == 1 and D(e1[0]["amount"]) == D("-11.2") and t[("lm", "ST-03")]["pct"] is None
    assert [c["kind"] for c in t[("m2", "STAIR_STEPS")]["causes"]] == ["UNIT"]
    for (u, gid), g in t.items():
        assert sum(D(c["amount"]) for c in g["causes"]) == D(g["gap"]), (u, gid)


def test_alsenan_units_never_meet_and_nothing_released():
    b = _built()
    for part in b["tables"].values():
        for u, gs in part.items():
            for g in gs:
                assert g["id"] and u in ("lm", "m2", "nr")
                assert sum(D(c["amount"]) for c in g["causes"]) == D(g["gap"])
    assert b["released"].startswith("NOTHING RELEASED")
    assert b["fix_rows"][0]["id"] == "FR-T584-1" and "11.200" in b["fix_rows"][0]["proposal"]


def test_alsenan_outputs_carry_no_coordinates():
    drawn = (HERE / "T584_DRAWN.json").read_text(encoding="utf-8")
    assert '"x"' not in drawn and '"y"' not in drawn and "insert_point" not in drawn
