"""R-T336-WP-BIND-1 on villa W336 (hand fixture, not the development villa).

Villa W336, ground floor: bath B1 3.00 x 2.00 (boundary 10.00 lm) and W.C. B2 1.50 x 1.20 (boundary 5.40 lm) share
door DA (0.80 jamb to jamb in a 0.15 wall); B1 has door DB 0.90 to the hall (0.20 wall) and a window W1 0.60 wide,
sill 0.90 printed; B2 has a full-height glazed door G1 0.70 wide, sill 0.00. A column 0.40 x 0.30 stands 0.05 proud
of B1's north face over 0.40 (footprint in the room 0.020 m2). Hand results:

  B1 floor 3.00 x 2.00 - 0.40 x 0.05 = 5.980 m2
  B1 upturn (10.00 - 0.80 DA - 0.90 DB) x 0.20 = 8.30 x 0.20 = 1.660 m2   (W1 sill 0.90 > 0.20: not deducted)
  B2 upturn (5.40 - 0.80 DA - 0.70 G1) x 0.20 = 3.90 x 0.20 = 0.780 m2     (G1 sill 0.00 <= 0.20: deducted)
  thresholds DA 0.80 x 0.15 = 0.120 m2, DB 0.90 x 0.20 = 0.180 m2
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t336"))
import t336_wp_binding as B  # noqa: E402

WET = "WP.WET_AREA"
LINES = {"L-F1", "L-F2", "L-U1", "L-U2", "L-TA1", "L-TA2", "L-DA", "L-DB", "L-TB", "L-T1"}


def _pieces():
    p = B.piece
    return [
        p("F/B1", WET, "FLOOR", "m2", "B1", B.floor_net_m2(3.00 * 2.00, [0.40 * 0.05]), "DRAWING-CONFIRMED",
          line_id="L-F1", action="CORRECT", before=6.00, before_state="SOURCE_DERIVED", evidence="box + column"),
        p("F/B2", WET, "FLOOR", "m2", "B2", 1.80, "DRAWING-CONFIRMED", line_id="L-F2", before=1.80,
          before_state="SOURCE_DERIVED", evidence="box"),
        p("U/B1", WET, "WALL_UPTURN", "m2", "B1",
          B.upturn_m2(10.00, doors=[0.80, 0.90], windows=[(0.60, 0.90)])[0], "DRAWING-CONFIRMED", line_id="L-U1",
          action="CORRECT", before=1.540, before_state="SOURCE_DERIVED", evidence="sill 0.90 printed"),
        p("U/B2", WET, "WALL_UPTURN", "m2", "B2",
          B.upturn_m2(5.40, doors=[0.80], windows=[(0.70, 0.00)])[0], "DRAWING-CONFIRMED", line_id="L-U2",
          before=0.780, before_state="SOURCE_DERIVED", evidence="sill 0.00 printed"),
        p("D[m2]/DOOR:DA/THRESHOLD", WET, "THRESHOLD", "m2", "B1|B2", B.threshold_m2(0.80, 0.15),
          "DRAWING-CONFIRMED", line_id="L-DA", before=0.12, before_state="SOURCE_DERIVED", evidence="jambs"),
        p("D[m2]/DOOR:DB/THRESHOLD", WET, "THRESHOLD", "m2", "B1", B.threshold_m2(0.90, 0.20),
          "DRAWING-CONFIRMED", line_id="L-DB", before=0.18, before_state="SOURCE_DERIVED", evidence="jambs"),
        # door DA carried by a line in each room -> both replaced by one door row
        p("T[m2]/DOOR:DA/TRANSITION|RETIRED:L-TA1", WET, "TRANSITION", "m2", "B1", None, "HELD", line_id="L-TA1",
          action="REPLACE_BY_DOOR_ROW", evidence="Q-35 C"),
        p("T[m2]/DOOR:DA/TRANSITION|RETIRED:L-TA2", WET, "TRANSITION", "m2", "B2", None, "HELD", line_id="L-TA2",
          action="REPLACE_BY_DOOR_ROW", evidence="Q-35 C"),
        p("T[m2]/DOOR:DA/TRANSITION", WET, "TRANSITION", "m2", "B1|B2", None, "HELD",
          new_row="T[m2]/DOOR:DA/TRANSITION", action="ADD_ROW", evidence="Q-35 C"),
        p("T[m2]/DOOR:DB/TRANSITION", WET, "TRANSITION", "m2", "B1", None, "HELD", line_id="L-TB",
          evidence="held"),
        p("TERM/LINE:L-T1", WET, "TERMINATION", "lm", "B1", None, "NOT_APPLICABLE_WITH_EVIDENCE", line_id="L-T1",
          action="SET_NOT_APPLICABLE", evidence="window W1 sill 0.90 above the upturn"),
        p("POOL/M", "WP.POOL_TANK", "POOL_MEMBRANE", "m2", "P1", 12.5, "DRAWING-CONFIRMED", new_row="POOL/M",
          action="ADD_ROW", evidence="hatch", bound="+ HELD 0 .. 0.6"),
    ]


# ------------------------------------------------------------------------------------------------ normal
def test_hand_values():
    assert B.floor_net_m2(6.0, [0.02]) == pytest.approx(5.98, abs=1e-9)
    assert B.upturn_m2(10.00, doors=[0.80, 0.90], windows=[(0.60, 0.90)]) == (pytest.approx(1.66), pytest.approx(8.3))
    assert B.upturn_m2(5.40, doors=[0.80], windows=[(0.70, 0.00)]) == (pytest.approx(0.78), pytest.approx(3.9))
    assert B.threshold_m2(0.80, 0.15) == pytest.approx(0.12) and B.threshold_m2(0.90, 0.20) == pytest.approx(0.18)
    assert B.threshold_m2(1.00, None) is None


def test_binding_and_fill():
    ps = _pieces()
    assert B.validate_pieces(ps, LINES)
    rows = B.fill_rows(ps)
    assert B.check_fill(rows)
    by = {r["piece"]: r for r in rows}
    assert by["U/B1"]["change"] == pytest.approx(0.12)            # 1.540 deducted the window below its sill
    assert by["F/B1"]["change"] == pytest.approx(-0.02)
    assert by["T[m2]/DOOR:DA/TRANSITION|RETIRED:L-TA1"]["after"] is None
    t = B.totals(rows, "m2", families=(WET,))
    assert t["FLOOR"]["after"] == pytest.approx(7.78) and t["TRANSITION"]["held_rows"] == 4


def test_door_transitions_classes():
    d = B.door_transitions({"DA": ("B1", "B2"), "DB": ("B1",), "DC": ("B2",)},
                           {"L-TA1": "DA", "L-TA2": "DA", "L-TB": "DB"})
    assert (d["DA"]["class"], d["DB"]["class"], d["DC"]["class"]) == ("DOUBLE", "ONE", "NONE")


def test_mirror_invariant():
    # a mirrored room keeps its boundary, door and window widths: same upturn
    assert B.upturn_m2(10.0, [0.9, 0.8], windows=[(0.6, 0.9)]) == B.upturn_m2(10.0, [0.8, 0.9], windows=[(0.6, 0.9)])


# ------------------------------------------------------------------------------------------------ adverse
def test_door_transition_in_two_rooms_refused():
    ps = _pieces()
    for p in ps:                                   # keep both room-side lines live: a double count
        if "RETIRED" in p["key"]:
            p["action"], p["key"] = "KEEP", p["key"].replace("|RETIRED", "/ROOMSIDE")
    rows = B.fill_rows(ps)
    with pytest.raises(B.BindingError, match="door pieces carried twice"):
        B.check_fill(rows + [dict(rows[0], row="L-TA3", piece="T[m2]/DOOR:DA/TRANSITION", kind="TRANSITION",
                                  action="KEEP", after_status="HELD", after=None)])


def test_door_piece_keyed_by_room_refused():
    ps = _pieces() + [B.piece("T[m2]/B2/TRANSITION", WET, "TRANSITION", "m2", "B2", None, "HELD",
                              new_row="T[m2]/B2/TRANSITION", action="ADD_ROW", evidence="room side")]
    with pytest.raises(B.BindingError, match="keyed by its physical door"):
        B.validate_pieces(ps, LINES)


def test_window_below_sill_deducted_refused():
    # the engine's reading: W1 deducted from B1's upturn although its sill is 0.90
    wrong = round((10.00 - 0.80 - 0.90 - 0.60) * 0.20, 6)
    right = B.upturn_m2(10.00, doors=[0.80, 0.90], windows=[(0.60, 0.90)])[0]
    assert wrong == pytest.approx(1.54) and right != pytest.approx(wrong)
    assert B.opening_interrupts(0.90) is False and B.opening_interrupts(0.20) is True
    with pytest.raises(B.BindingError, match="sill not printed"):
        B.upturn_m2(10.00, doors=[0.80], windows=[(0.60, None)])


def test_held_as_zero_refused():
    ps = _pieces()
    ps[9]["qty"] = 0.0
    with pytest.raises(B.BindingError, match="blank quantity"):
        B.validate_pieces(ps, LINES)
    rows = B.fill_rows(_pieces())
    rows[0] = dict(rows[0], after_status="HELD", after=0)
    with pytest.raises(B.BindingError, match="held"):
        B.check_fill(rows)


def test_piece_in_two_lines_refused():
    ps = _pieces()
    ps[1]["line_id"] = "L-F1"                      # B2 floor on B1's line
    with pytest.raises(B.BindingError, match="one piece per line"):
        B.validate_pieces(ps, LINES)


def test_unknown_line_and_new_row_rules():
    ps = _pieces()
    ps[0]["line_id"] = "L-XX"
    with pytest.raises(B.BindingError, match="not a line of the candidate"):
        B.validate_pieces(ps, LINES)
    ps = _pieces()
    ps[-1]["action"] = "KEEP"
    with pytest.raises(B.BindingError, match="NEW row"):
        B.validate_pieces(ps, LINES)


def test_not_applicable_without_evidence_refused():
    ps = _pieces()
    ps[10]["evidence"] = None
    with pytest.raises(B.BindingError, match="without evidence"):
        B.validate_pieces(ps, LINES)


def test_units_and_millimetres_refused():
    with pytest.raises(B.BindingError):
        B.threshold_m2(800, 150)
    with pytest.raises(B.BindingError):
        B.upturn_m2(10000, doors=[800])
    ps = _pieces()
    ps[0]["unit"] = "sqm"
    with pytest.raises(B.BindingError, match="unit"):
        B.validate_pieces(ps, LINES)


def test_column_bigger_than_box_refused():
    with pytest.raises(B.BindingError):
        B.floor_net_m2(0.5, [0.6])
