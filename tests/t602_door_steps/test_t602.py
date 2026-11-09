"""T-602 exterior-opening step census (R-T602-1): a non-Alsenan hand fixture (Villa K602: three exterior openings, one
without a level change), adverse cases (equal levels given a step, an edge pair away from the opening, an inverted
companion, a passable level change with no edge, figure matching, units / None), and the development-villa build pinned
(byte-identical rebuild, census, G-01, reconciliation closure, no coordinates, edited input stops the build)."""
from __future__ import annotations

import importlib.util
import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t602"
sys.path.insert(0, str(HERE))
R = importlib.import_module("t602_rules")
_spec = importlib.util.spec_from_file_location("t602_alsenan", HERE / "t602_alsenan.py")
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)

D = Decimal
PAIR = {"high_side": "in", "distance_m": "0.00"}


# ---- hand fixture (Villa K602, not Alsenan) --------------------------------------------------------------------------
# K-D1 house door: +0.45 inside / +0.30 terrace, edge pair on the face, wall gap 1.00 -> 1.00 lm, riser 0.15, 0.150 m2
# K-G1 boundary gate gap 2.00: +0.30 plot / +0.00 street, edge on the plot line -> 2.00 lm, riser 0.30, 0.600 m2
# K-D2 side door: +0.30 / +0.30, no edge -> NO_STEP
def _fixture():
    return [R.decide("K-D1", ["+0.45"], ["+0.30"], edge_pair=PAIR, gap_m="1.00"),
            R.decide("K-G1", ["+0.30"], ["+-0.00"], edge_pair=PAIR, gap_m="2.00"),
            R.decide("K-D2", ["+0.30"], ["+0.30"])]


def test_fixture_three_openings_by_hand():
    d1, g1, d2 = _fixture()
    assert (d1["decision"], d1["payable_lm"], d1["riser_m"], d1["riser_m2"]) == ("STEP", D("1.00"), D("0.15"),
                                                                              D("0.1500"))
    assert (g1["decision"], g1["payable_lm"], g1["riser_m"], g1["riser_m2"]) == ("STEP", D("2.00"), D("0.30"),
                                                                              D("0.6000"))
    assert d2["decision"] == "NO_STEP" and d2["nr"] == 0 and d2["payable_lm"] is None


def test_fixture_reconcile_aggregate_only():
    rc = R.reconcile(["1.00", "2.00", "1.20"], _fixture())
    assert rc["ours_lm"] == D("3.00") and rc["ours_nr"] == 2 and rc["his_lm"] == D("4.20") and rc["his_nr"] == 3
    assert rc["residual_lm_ours_minus_his"] == D("-1.20") and rc["residual_nr_ours_minus_his"] == -1
    assert rc["attribution"].startswith("AGGREGATE_ONLY")


def test_fixture_mm_equals_m():
    r = R.decide("K-D1", ["+0.45"], ["+0.30"], edge_pair=PAIR, gap_m="1000", unit="mm")
    assert r["payable_lm"] == D("1.00") and r["riser_m2"] == D("0.15")


def test_fixture_mirror_sides_same_result():
    a = R.decide("K-D1", ["+0.45"], ["+0.30"], edge_pair={"high_side": "in", "distance_m": "0"}, gap_m="1.00")
    b = R.decide("K-D1", ["+0.30"], ["+0.45"], edge_pair={"high_side": "out", "distance_m": "0"}, gap_m="1.00")
    assert (a["payable_lm"], a["riser_m"], a["riser_m2"]) == (b["payable_lm"], b["riser_m"], b["riser_m2"])


# ---- adverse ----------------------------------------------------------------------------------------------------------
def test_adverse_equal_levels_given_a_step_refused():
    with pytest.raises(R.RuleError, match="equal printed levels"):
        R.decide("K-D2", ["+0.30"], ["+0.30"], given_step=True)


def test_adverse_edge_pair_between_equal_levels_refused():
    with pytest.raises(R.RuleError, match="CONFLICT"):
        R.decide("K-D2", ["+0.30"], ["+0.30"], edge_pair=PAIR, gap_m="0.90")


def test_adverse_pair_away_from_the_opening_is_not_a_door_step():
    with pytest.raises(R.RuleError, match="not at the opening"):
        R.decide("K-D1", ["+0.45"], ["+0.30"], edge_pair={"high_side": "in", "distance_m": "0.45"}, gap_m="1.00")


def test_adverse_inverted_companion_refused():
    with pytest.raises(R.RuleError, match="LOWER side"):
        R.decide("K-D1", ["+0.45"], ["+0.30"], edge_pair={"high_side": "out", "distance_m": "0"}, gap_m="1.00")


def test_adverse_level_change_without_edge_is_held_never_zero():
    r = R.decide("K-P1", ["+0.30"], ["+0.15"])
    assert r["decision"] == "HELD" and r["nr"] is None and r["payable_lm"] is None
    assert r["riser_bound"] == (D(0), D("0.15"))


def test_adverse_edge_with_unreadable_side_held_with_bound():
    r = R.decide("K-D1", ["+0.45"], ["+0.30", "+0.15"], edge_pair=PAIR, gap_m="1.00", fallback_out="+0.30")
    assert r["decision"] == "HELD" and r["riser_m"] is None and r["payable_lm"] == D("1.00")


def test_adverse_fallback_never_sets_a_riser():
    r = R.decide("K-D1", ["+0.45"], [], edge_pair=PAIR, gap_m="1.00", fallback_out="+0.30")
    assert r["decision"] == "HELD" and r["riser_m"] is None


def test_adverse_not_passable_with_a_step_refused():
    assert R.decide("K-X1", ["+0.15"], ["+-0.00"], passable=False)["decision"] == "NO_STEP"
    with pytest.raises(R.RuleError, match="not passable"):
        R.decide("K-X1", ["+0.15"], ["+-0.00"], passable=False, given_step=True)


def test_adverse_figure_matching_refused():
    with pytest.raises(R.RuleError, match="refused"):
        R.attribute_by_figure("1.00", "K-D1")


def test_adverse_units_and_none():
    with pytest.raises(R.RuleError):
        R.length("1.0", "cm")
    with pytest.raises(R.RuleError):
        R.D(None)
    with pytest.raises(R.RuleError, match="no measured wall gap"):
        R.decide("K-D1", ["+0.45"], ["+0.30"], edge_pair=PAIR, gap_m=None)
    with pytest.raises(R.RuleError):
        R.book("lm", "m2")


# ---- development villa (pinned) ---------------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def built():
    return A.build()


def test_alsenan_rebuild_byte_identical(built):
    out = json.dumps(built, indent=1, sort_keys=True, ensure_ascii=True) + "\n"
    assert (HERE / "out" / "T602_DOOR_STEPS.json").read_text(encoding="utf-8") == out


def test_alsenan_census_every_exterior_opening_decided(built):
    got = {r["opening"]: r["decision"] for r in built["openings"]}
    assert set(got) == set(A.EXTERIOR_CENSUS) | {"G-01"}
    steps = sorted(k for k, v in got.items() if v == "STEP")
    assert steps == ["D-GF-01", "D-GF-03", "D-GF-05", "D-GF-09", "D-GF-15", "G-01"]
    assert all(v in ("STEP", "NO_STEP") for v in got.values())          # nothing HELD on this villa


def test_alsenan_g01_step(built):
    g = next(r for r in built["openings"] if r["opening"] == "G-01")
    assert (g["payable_lm"], g["riser_m"], g["riser_m2"], g["nr"]) == ("2.5", "0.15", "0.375", 1)
    assert g["levels_in"] == ["+0.15"] and g["levels_out"] == ["+-0.00"]
    assert g["edge_pair"]["edge"] == "10F" and g["edge_pair"]["companion"] == "110#0"


def test_alsenan_reconciliation_closes(built):
    rc = built["reconciliation"]
    assert (rc["ours_lm"], rc["ours_nr"], rc["residual_lm"], rc["residual_nr"]) == ("7.3", 6, "-0.4", 0)
    assert built["his"]["lm"] == "7.7" and built["his"]["nr"] == 6
    v8 = rc["v8_before"]
    parts = rc["v8_unresolved_split"]
    assert v8["unresolved_lm"] == "2.9" and sum(D(p["lm"]) for p in parts) == D("2.9")
    assert [p["status"] for p in parts] == ["DRAWING-CONFIRMED", "UNRESOLVED"]


def test_alsenan_pairs_away_are_not_door_steps(built):
    pc = built["pair_census"]
    assert pc["pairs"] == 128 and len(pc["at_exterior_openings"]) == 6
    assert pc["away_reaching_an_outdoor_figure"] == []
    assert D(pc["min_distance_away_pair_to_an_exterior_opening_m"]) > R.AT_OPENING_M


def test_alsenan_changed_input_stops_the_build(monkeypatch):
    real = A._sha
    monkeypatch.setattr(A, "_sha", lambda p: "0000000000000000" if p == A.DRAWN else real(p))
    with pytest.raises(R.RuleError, match="changed"):
        A.build()


def test_alsenan_drawn_json_has_no_coordinates():
    d = json.loads((HERE / "T602_DRAWN.json").read_text(encoding="utf-8"))

    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                assert k not in ("x", "y", "insert_point", "coords", "position")
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
        elif isinstance(x, (int, float)) and not isinstance(x, bool):
            assert abs(x) < 25, x
    walk(d)
