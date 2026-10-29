"""T-313 reveal ledger: hand fixture villa R313 (NOT Alsenan), normal and adverse cases.

Villa R313, ground floor, F.F.L. 0.00, room plaster height 3.00 m, walls 0.20 m:
- W1 window 1.20 x 1.50, sill 0.90 (head 2.40); frame band from 0.05 to 0.12 m off the OUTER face, so
  depth_out = 0.05, depth_in = 0.20 - 0.12 = 0.08 (by hand):
  IN  jambs 2 x 0.08 x 1.50 = 0.240 m2 (3.00 m.l), head 0.08 x 1.20 = 0.096 m2, sill 0.096 m2
  OUT jambs 2 x 0.05 x 1.50 = 0.150 m2, head 0.060 m2, sill 0.060 m2; exterior edge 3.00 + 1.20 + 1.20 = 5.40 m.l
- D1 door 0.90 x 2.20 (one reveal through the wall): jambs 2 x 0.20 x 2.20 = 0.880 m2, head 0.20 x 0.90 = 0.180 m2
- A1 segmental arch, chord 1.00, r 0.5673, 28.2 .. 151.8 deg: developed 0.5673 x 2.157226 = 1.223795 m;
  springing 2.20: jambs 0.880 m2, head 0.20 x 1.223795 = 0.244759 m2
"""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("t313_reveal_ledger",
                                               ROOT / "research" / "agents_t313" / "t313_reveal_ledger.py")
L = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(L)

W1 = {"id": "W1", "kind": "WINDOW", "width_m": 1.20, "height_m": 1.50, "sill_m": 0.90,
      "depth_in_m": L.depth_from_plan(0.20, 0.12), "depth_out_m": L.depth_from_plan(0.00, 0.05),
      "plaster_height_m": 3.00, "height_status": "DRAWING-CONFIRMED", "room": "R1"}
D1 = {"id": "D1", "kind": "DOOR", "width_m": 0.90, "height_m": 2.20, "wall_t_m": 0.20,
      "height_status": "ASSUMED — OWNER-APPROVED"}
A1 = {"id": "A1", "kind": "ARCH", "width_m": 1.00, "springing_m": 2.20, "developed_m": 1.223795, "wall_t_m": 0.20,
      "jamb_state": "MEASURED", "head_state": "MEASURED"}


def _by(rows):
    return {(r["opening"], r["side"], r["component"]): r for r in rows}


def test_normal_window_both_sides_by_hand():
    b = _by(L.window_rows(W1))
    assert b[("W1", "IN", "JAMBS")]["m2"] == pytest.approx(0.240)
    assert b[("W1", "IN", "JAMBS")]["ml"] == pytest.approx(3.00)
    assert b[("W1", "IN", "HEAD")]["m2"] == pytest.approx(0.096)
    assert b[("W1", "IN", "SILL")]["m2"] == pytest.approx(0.096)
    assert b[("W1", "OUT", "JAMBS")]["m2"] == pytest.approx(0.150)
    assert b[("W1", "OUT", "HEAD")]["m2"] == pytest.approx(0.060)
    assert b[("W1", "OUT", "SILL")]["m2"] == pytest.approx(0.060)
    assert L.exterior_edge_ml(list(b.values())) == pytest.approx(5.40)
    # the two depths and the frame band close to the wall thickness
    assert W1["depth_in_m"] + W1["depth_out_m"] + 0.07 == pytest.approx(0.20)


def test_normal_head_soffit_only_where_wall_remains_above():
    op = dict(W1, plaster_height_m=2.40)          # band top at the head: no wall above inside the band
    b = _by(L.window_rows(op))
    assert b[("W1", "IN", "HEAD")]["state"] == "NONE" and b[("W1", "IN", "HEAD")]["m2"] == 0.0
    assert b[("W1", "IN", "JAMBS")]["m2"] == pytest.approx(2 * 0.08 * 1.50)


def test_normal_floor_glazing_strip_is_floor_not_sill():
    op = dict(W1, id="FG", kind="FLOOR_GLAZING", sill_m=0.0, height_m=2.40)
    b = _by(L.window_rows(op))
    assert ("FG", "IN", "SILL") not in b and ("FG", "OUT", "SILL") not in b
    assert b[("FG", "IN", "FLOOR_STRIP")]["m2"] == pytest.approx(0.08 * 1.20)
    assert b[("FG", "OUT", "THRESHOLD")]["m2"] == pytest.approx(0.05 * 1.20)
    assert b[("FG", "OUT", "THRESHOLD")]["ml"] == 0.0          # a floor edge, no arris
    assert L.exterior_edge_ml(list(b.values())) == pytest.approx(2 * 2.40 + 1.20)


def test_normal_door_one_reveal_through_the_wall():
    b = _by(L.door_rows(D1))
    assert b[("D1", "THROUGH", "JAMBS")]["m2"] == pytest.approx(0.880)
    assert b[("D1", "THROUGH", "HEAD")]["m2"] == pytest.approx(0.180)
    assert not any(k[1] in ("IN", "OUT") for k in b)


def test_normal_arch_developed_head():
    b = _by(L.arch_rows(A1))
    assert b[("A1", "THROUGH", "HEAD")]["m2"] == pytest.approx(0.244759, abs=1e-6)
    assert b[("A1", "THROUGH", "JAMBS")]["m2"] == pytest.approx(0.880)


def test_normal_mirror_and_mm_units_give_the_same_depths():
    mirrored_in = L.depth_from_plan(-0.20, -0.12)
    mm_in = L.depth_from_plan(L.to_m(200, "mm"), L.to_m(120, "mm"))
    assert mirrored_in == pytest.approx(W1["depth_in_m"]) and mm_in == pytest.approx(W1["depth_in_m"])
    op = dict(W1, width_m=L.to_m(1200, "mm"), height_m=L.to_m(1500, "mm"), sill_m=L.to_m(900, "mm"))
    assert _by(L.window_rows(op))[("W1", "IN", "JAMBS")]["m2"] == pytest.approx(0.240)


def test_normal_flush_frame_is_none_with_evidence():
    op = dict(W1, depth_out_m=0.0, depth_out_source="frame line on the outer face line")
    b = _by(L.window_rows(op))
    assert all(b[("W1", "OUT", c)]["state"] == "NONE" for c in ("JAMBS", "HEAD", "SILL"))


def test_normal_binding_each_row_one_line_or_no_line():
    rows = L.ledger([W1, D1, A1])
    bound = L.bind_lines(rows, {("W1", "IN", "SILL"): "L-1", ("W1", "OUT", "SILL"): "L-1"})
    assert {r["line_id"] for r in bound if r["opening"] == "W1" and r["component"] == "SILL"} == {"L-1"}
    assert all(r["line_id"] == L.NO_LINE for r in bound if r["opening"] != "W1")


def test_normal_totals_keep_unresolved_by_name():
    op = dict(W1, id="W2", depth_in_m=None)
    t = L.totals(L.ledger([W1, op]))
    assert t[("IN", "JAMBS")]["unresolved"] == ["W2"]
    assert t[("IN", "JAMBS")]["m2"] == pytest.approx(0.240)


def test_normal_sill_unknown_room_side_held_outside_measured():
    b = _by(L.window_rows(dict(W1, sill_m=None)))
    assert b[("W1", "IN", "JAMBS")]["state"] == "HELD" and b[("W1", "IN", "JAMBS")]["m2"] is None
    assert b[("W1", "OUT", "JAMBS")]["m2"] == pytest.approx(0.150)


def test_normal_height_unknown_jambs_held_head_and_sill_measured():
    b = _by(L.window_rows(dict(W1, height_m=None)))
    assert b[("W1", "OUT", "JAMBS")]["state"] == "HELD"
    assert b[("W1", "OUT", "HEAD")]["m2"] == pytest.approx(0.060)
    assert b[("W1", "IN", "SILL")]["m2"] == pytest.approx(0.096)


def test_normal_held_arch_carries_no_quantity_only_its_candidate():
    b = _by(L.arch_rows(dict(A1, jamb_state="HELD", head_state="HELD")))
    assert b[("A1", "THROUGH", "HEAD")]["m2"] is None and "0.244759 m2 candidate" in b[("A1", "THROUGH", "HEAD")]["basis"]


# ------------------------------------------------------------------ adverse
def test_adverse_default_depth_refused():
    with pytest.raises(L.LedgerError, match="default"):
        L.window_rows(dict(W1, default_depth=True))


def test_adverse_missing_depth_is_unresolved_never_zero():
    rows = L.window_rows(dict(W1, depth_in_m=None, depth_out_m=None))
    assert all(r["state"] == "UNRESOLVED" and r["m2"] is None for r in rows)


def test_adverse_door_sill_reveal_refused():
    with pytest.raises(L.LedgerError, match="no sill reveal"):
        L.door_rows(dict(D1, sill_reveal=True))


def test_adverse_reveal_counted_in_facade_face_refused():
    rows = L.window_rows(W1)
    with pytest.raises(L.LedgerError, match="facade"):
        L.refuse_facade_overlap(rows, {"W1:JAMBS"})
    assert L.refuse_facade_overlap(rows, {"FACE-NE-1"})


def test_adverse_opening_in_two_lines_refused():
    rows = L.ledger([W1])
    with pytest.raises(L.LedgerError, match="two lines"):
        L.bind_lines(rows, {("W1", "IN", "SILL"): "L-1", ("W1", "OUT", "SILL"): "L-2"})


def test_adverse_two_openings_in_one_line_refused():
    rows = L.ledger([W1, dict(W1, id="W9")])
    with pytest.raises(L.LedgerError, match="two openings"):
        L.bind_lines(rows, {("W1", "IN", "SILL"): "L-1", ("W9", "IN", "SILL"): "L-1"})


def test_adverse_binding_to_nonexistent_row_refused():
    with pytest.raises(L.LedgerError, match="does not exist"):
        L.bind_lines(L.ledger([D1]), {("D1", "THROUGH", "SILL"): "L-1"})


def test_adverse_duplicate_opening_refused():
    with pytest.raises(L.LedgerError, match="twice"):
        L.ledger([W1, W1])


def test_adverse_unknown_unit_and_negative_length_refused():
    with pytest.raises(L.LedgerError):
        L.to_m(1200, "in")
    with pytest.raises(L.LedgerError):
        L.window_rows(dict(W1, width_m=-1.2))


def test_adverse_arch_at_chord_or_undeveloped():
    with pytest.raises(L.LedgerError, match="chord"):
        L.arch_rows(dict(A1, developed_m=0.90))
    b = _by(L.arch_rows(dict(A1, developed_m=None)))
    assert b[("A1", "THROUGH", "HEAD")]["state"] == "UNRESOLVED" and b[("A1", "THROUGH", "HEAD")]["m2"] is None


# ------------------------------------------------------------------ r2: cross-family binding (door reveals in plaster)
# Villa R313: the candidate carries D1's reveal in a plaster line 'door jambs and head' = 2 x 0.20 x 2.20 + 0.20 x 0.90
# = 0.880 + 0.180 = 1.060 m2 (by hand); a second door D2 (0.80 in a 0.15 wall) has no line anywhere:
# 2 x 0.15 x 2.20 + 0.15 x 0.80 = 0.660 + 0.120 = 0.780 m2 missing.
D2 = {"id": "D2", "kind": "DOOR", "width_m": 0.80, "height_m": 2.20, "wall_t_m": 0.15}
PL = {"line_id": "L-PL-D1", "family": "FIN.PLASTER", "measured": 1.06, "range": None}


def test_normal_door_bound_to_its_plaster_line_and_reconciled():
    rows = L.bind_lines(L.ledger([W1, D1, D2]), {("D1", "THROUGH", "JAMBS"): "L-PL-D1",
                                                 ("D1", "THROUGH", "HEAD"): "L-PL-D1"})
    rec = L.reconcile_line(rows, "D1", ("JAMBS", "HEAD"), PL)
    assert rec["verdict"] == "EQUAL" and rec["ledger_m2"] == pytest.approx(1.060) and rec["residual_m2"] == 0.0
    carried = {("D1", "THROUGH", "JAMBS"): ("FIN.PLASTER", "L-PL-D1"),
               ("D1", "THROUGH", "HEAD"): ("FIN.PLASTER", "L-PL-D1")}
    miss = L.book_missing(rows, carried)
    assert miss[("DOOR", "THROUGH", "JAMBS")]["openings"] == ["D2"]
    assert miss[("DOOR", "THROUGH", "JAMBS")]["m2"] + miss[("DOOR", "THROUGH", "HEAD")]["m2"] == pytest.approx(0.780)


def test_normal_bounded_line_within_bound_names_both_residuals():
    rows = L.ledger([dict(D1, height_m=2.50, width_m=2.00)])      # printed 2.50: 1.000 + 0.400 = 1.400 m2
    rec = L.reconcile_line(rows, "D1", ("JAMBS", "HEAD"), dict(PL, measured=None, range=[1.28, 1.40]))
    assert rec["verdict"] == "WITHIN_BOUND" and rec["residual_m2"] == pytest.approx([0.12, 0.0])
    rec = L.reconcile_line(rows, "D1", ("JAMBS", "HEAD"), dict(PL, measured=1.28))
    assert rec["verdict"] == "DIFFERS" and rec["residual_m2"] == pytest.approx(0.12)


def test_adverse_door_reveal_already_in_a_plaster_line_booked_again_refused():
    rows = L.ledger([D1])                                 # left NO_LINE although FIN.PLASTER carries it
    with pytest.raises(L.LedgerError, match="second count"):
        L.book_missing(rows, {("D1", "THROUGH", "JAMBS"): ("FIN.PLASTER", "L-PL-D1")})
    with pytest.raises(L.LedgerError, match="two lines"):   # and bound to a reveal line beside its plaster line
        L.bind_lines(rows, {("D1", "THROUGH", "JAMBS"): "L-PL-D1", ("D1", "THROUGH", "HEAD"): "L-REVEAL-9"})


def test_adverse_held_component_never_reconciled_as_zero():
    rows = L.ledger([dict(D1, height_m=None)])
    rec = L.reconcile_line(rows, "D1", ("JAMBS", "HEAD"), PL)
    assert rec["verdict"] == "LEDGER_OPEN" and rec["ledger_m2"] is None and rec["residual_m2"] is None
    with pytest.raises(L.LedgerError, match="not all"):
        L.reconcile_line(rows, "D1", ("JAMBS", "SILL"), PL)


def test_adverse_reconciliation_names_the_residual():
    assert L.reconcile(189.630, {"r2": 137.110, "jambs counted twice in r1": 52.520}) == pytest.approx(0.0)
    with pytest.raises(L.LedgerError, match="residual"):
        L.reconcile(189.630, {"r2": 137.110})
