"""T-325 sills and thresholds: a hand fixture that is NOT the development villa, normal and adverse cases.

Fixture villa R325 (hand calculated):
- bathroom door D1: clear 0.80 m in a 0.15 m wall, bathroom one side -> MARBLE 0.80 x 0.15 = 0.120 m2, 1 pc,
  finish-change edges 2 x 0.80 = 1.600 m.l (wet side + dry side);
- bedroom door D2: clear 0.90 m in a 0.20 m wall, dry both sides -> porcelain strip 0.180 m2, no finish change;
- arch A1: 1.00 m in a 0.20 m wall -> the floor continues 0.200 m2;
- raised window W1: 1.20 m wide, frame 0.05 m from the room face, 0.08 m from the outer face (0.13 + frame 0.07 in a
  0.20 wall): SILL_IN 1.20 x 0.05 = 0.060 m2 / 1.200 m.l, SILL_OUT 1.20 x 0.08 = 0.096 m2 / 1.200 m.l;
- floor-level window W2: 1.50 m wide, frame flush with the room face, 0.08 m outside over outside air:
  THRESHOLD_IN NONE (0), THRESHOLD_OUT = external sill at floor level 0.120 m2 / 1.500 m.l, material UNKNOWN;
- floor-level window W3: 1.00 m, 0.10 m outside onto a terrace floor -> the terrace floor's finish 0.100 m2.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t325"))

import sills_thresholds as S  # noqa: E402


def fixture():
    return [
        {"id": "D1", "kind": "DOOR", "floor": "GF", "clear_width_m": 0.80, "wall_t_m": 0.15,
         "sides": ["BATHROOM", "CORRIDOR"]},
        {"id": "D2", "kind": "DOOR", "floor": "GF", "clear_width_m": 0.90, "wall_t_m": 0.20,
         "sides": ["BEDROOM", "CORRIDOR"]},
        {"id": "A1", "kind": "ARCH", "floor": "GF", "clear_width_m": 1.00, "wall_t_m": 0.20, "sides": ["LIVING"]},
        {"id": "W1", "kind": "WINDOW", "floor": "GF", "width_m": 1.20, "depth_in_m": 0.05, "depth_out_m": 0.08},
        {"id": "W2", "kind": "FLOOR_GLAZING", "floor": "1F", "width_m": 1.50, "depth_in_m": 0.0,
         "depth_out_m": 0.08, "outside": "AIR"},
        {"id": "W3", "kind": "FLOOR_GLAZING", "floor": "1F", "width_m": 1.00, "depth_in_m": 0.0,
         "depth_out_m": 0.10, "outside": "FLOOR"},
    ]


def rows_by(rows):
    return {(r["opening"], r["component"]): r for r in rows}


def test_hand_fixture_every_component_once():
    rows = S.ledger(fixture())
    k = rows_by(rows)
    assert len(k) == len(rows)                                    # every opening x component once
    d1 = k[("D1", "THRESHOLD")]
    assert d1["material"] == "MARBLE" and d1["m2"] == pytest.approx(0.120) and d1["pcs"] == 1
    assert k[("D1", "FINISH_CHANGE_EDGE")]["edge_ml"] == pytest.approx(1.600)
    assert k[("D1", "FINISH_CHANGE_EDGE")]["line_id"] == S.NOT_AN_ITEM
    d2 = k[("D2", "THRESHOLD")]
    assert d2["material"] == "FLOOR PORCELAIN" and d2["m2"] == pytest.approx(0.180)
    assert k[("D2", "FINISH_CHANGE_EDGE")]["edge_ml"] == 0.0
    assert k[("A1", "THRESHOLD")]["m2"] == pytest.approx(0.200)
    assert k[("W1", "SILL_IN")]["m2"] == pytest.approx(0.060) and k[("W1", "SILL_IN")]["edge_ml"] == 1.2
    assert k[("W1", "SILL_OUT")]["m2"] == pytest.approx(0.096)
    assert k[("W1", "SILL_OUT")]["material"] == "UNKNOWN"         # no spec, no owner rule: never a default stone
    assert k[("W2", "THRESHOLD_IN")]["state"] == "NONE" and k[("W2", "THRESHOLD_IN")]["m2"] == 0.0
    w2 = k[("W2", "THRESHOLD_OUT")]
    assert w2["m2"] == pytest.approx(0.120) and w2["edge_ml"] == 1.5 and "external sill" in w2["physical_element"]
    assert w2["material"] == "UNKNOWN"
    assert k[("W3", "THRESHOLD_OUT")]["material"] == "the outdoor floor's finish"
    assert k[("W3", "THRESHOLD_OUT")]["m2"] == pytest.approx(0.100)


def test_totals_by_component_and_material():
    t = S.totals(S.ledger(fixture()))
    assert t["THRESHOLD|MARBLE|MEASURED"] == {"n": 1, "m2": 0.12, "edge_ml": 0.8}
    assert t["SILL_OUT|UNKNOWN|MEASURED"]["m2"] == pytest.approx(0.096)
    assert t["FINISH_CHANGE_EDGE|MEASURED"]["edge_ml"] == pytest.approx(1.6)
    assert S.reconcile(0.120 + 0.180 + 0.200, [0.12, 0.18, 0.2]) == 0.0


def test_spec_sets_the_sill_material_only_where_printed():
    op = dict(fixture()[3], spec={"out": {"material": "MARBLE", "source": "sheet A-501 note 4"}})
    k = rows_by(S.window_rows(op))
    assert k[("W1", "SILL_OUT")]["material"] == "MARBLE"
    assert k[("W1", "SILL_IN")]["material"] == "UNKNOWN"


def test_mirror_and_mm_units_give_the_same_depth():
    d = S.depth_from_plan(S.to_m(0.0, "mm"), S.to_m(80.0, "mm"))
    dm = S.depth_from_plan(-S.to_m(0.0, "mm"), -S.to_m(80.0, "mm"))     # mirrored: both offsets change sign
    assert d == dm == pytest.approx(0.08)
    assert S.to_m(15, "cm") == pytest.approx(0.15)


def test_bind_one_line_per_component_and_per_opening():
    rows = S.ledger(fixture())
    S.bind(rows, {("D1", "THRESHOLD"): "L-a", ("W1", "SILL_OUT"): "L-b"})
    k = rows_by(rows)
    assert k[("D1", "THRESHOLD")]["binding"] == "BOUND" and k[("W2", "THRESHOLD_OUT")]["line_id"] == S.NO_LINE


# ---------------------------------------------------------------- adverse


def test_default_sill_depth_refused():
    with pytest.raises(S.LedgerError, match="default"):
        S.window_rows(dict(fixture()[3], default_depth=0.05))


def test_rise_as_plan_depth_refused():
    with pytest.raises(S.LedgerError, match="vertical"):
        S.door_rows(dict(fixture()[0], wall_t_m=0.02, depth_from_rise=True))


def test_missing_depth_is_unresolved_never_zero():
    k = rows_by(S.window_rows(dict(fixture()[3], depth_out_m=None)))
    r = k[("W1", "SILL_OUT")]
    assert r["state"] == "UNRESOLVED" and r["m2"] is None and r["pcs"] is None
    t = S.totals(list(k.values()))
    assert "SILL_OUT|-|UNRESOLVED" in t and t["SILL_OUT|-|UNRESOLVED"]["m2"] == 0.0 and \
        t["SILL_OUT|-|UNRESOLVED"]["n"] == 1      # counted as one open row, adds no number


def test_outside_not_established_is_held():
    k = rows_by(S.window_rows(dict(fixture()[4], outside=None)))
    assert k[("W2", "THRESHOLD_OUT")]["state"] == "HELD"
    t = S.totals(list(k.values()))
    assert all(v["m2"] == 0.0 for kk, v in t.items() if kk.endswith("|HELD"))


def test_threshold_in_reveal_and_threshold_lines_refused():
    rows = S.ledger(fixture())
    S.bind(rows, {("W2", "THRESHOLD_OUT"): "L-reveal-w2"})
    with pytest.raises(S.LedgerError, match="reveal line and in"):
        S.refuse_double(rows, {"W2": [("ARCH.WINDOW_REVEAL", "L-reveal-w2"), ("FIN.MARBLE.THRESHOLD", "L-thr")]})
    assert S.refuse_double(rows, {"W2": [("ARCH.WINDOW_REVEAL", "L-reveal-w2")]}) is rows


def test_one_component_in_two_lines_and_two_openings_in_one_line_refused():
    rows = S.ledger(fixture())
    S.bind(rows, {("D1", "THRESHOLD"): "L-a"})
    with pytest.raises(S.LedgerError, match="two lines"):
        S.bind(rows, {("D1", "THRESHOLD"): "L-x"})
    with pytest.raises(S.LedgerError, match="two openings"):
        S.bind(S.ledger(fixture()), {("D1", "THRESHOLD"): "L-a", ("D2", "THRESHOLD"): "L-a"})


def test_room_floor_strip_or_edge_bound_to_a_line_refused():
    rows = S.ledger([dict(fixture()[4], depth_in_m=0.05)])
    with pytest.raises(S.LedgerError, match="count it twice"):
        S.bind(rows, {("W2", "THRESHOLD_IN"): "L-thr"})
    with pytest.raises(S.LedgerError, match="count it twice"):
        S.bind(S.ledger(fixture()), {("D1", "FINISH_CHANGE_EDGE"): "L-edge"})


def test_door_sill_duplicate_opening_bad_unit_negative_length_refused():
    with pytest.raises(S.LedgerError, match="no sill"):
        S.door_rows(dict(fixture()[1], sill=True))
    with pytest.raises(S.LedgerError, match="twice"):
        S.ledger([fixture()[0], fixture()[0]])
    with pytest.raises(S.LedgerError, match="unknown unit"):
        S.to_m(1.0, "ft")
    with pytest.raises(S.LedgerError, match="non-negative"):
        S.door_rows(dict(fixture()[1], wall_t_m=-0.2))
    with pytest.raises(S.LedgerError, match="residual"):
        S.reconcile(0.5, [0.12, 0.18])


def test_external_entrance_never_marble_by_the_wet_rule():
    r = rows_by(S.door_rows({"id": "E1", "kind": "DOOR", "clear_width_m": 1.0, "wall_t_m": 0.2,
                             "sides": ["KITCHEN"], "external": True}))[("E1", "THRESHOLD")]
    assert r["material"] != "MARBLE"
