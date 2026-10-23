"""T-198: census revision and downstream deltas on a NON-Alsenan hand fixture (villa T198-B).

Hand truth (metres, m2):
  Wall W-A: outer white block 0.20 m, measured run 6.00 m, height to the beam soffit 3.00 -> gross 18.000 m2.
  The old opening list carries only window WA1 1.50 x 1.20 (sill 0.90, printed) -> net 18.000 - 1.800 = 16.200.
  The plan also draws PA1, a doorless 1.20 m opening inside the same run, head printed 2.40 above the floor, frameless,
  with a schedule lintel bearing 0.20 m each side. The revision adds it:
    block deduction 1.20 x 2.40 = 2.880 -> net 16.200 - 2.880 = 13.320 (delta -2.880 m2 = -0.576 m3 at 0.20 m)
    lintel length 1.20 + 2 x 0.20 = 1.600 m;  reveal 2 x 2.40 + 1.20 = 6.000 m.l (no sill: not a window), depth 0.20
    head soffit 1.20 x 0.20 = 0.240 m2;  threshold 1.20 m.l;  finish deduction 2.880 m2 on each face
  WA1 reveal 2 x 1.20 + 1.50 + 1.50 (sill) = 5.400 m.l.
  Adverse: PA1 with no printed head -> deduction HELD (never 0), net None with bounds 16.200 - 1.20 x 3.00 = 12.600 ..
  16.200; an opening drawn only on an elevation -> reported, never measured; a list sill holding a raw chain part (1.85
  from a +0.15 chain base, floor +1.00) re-datums to 1.00 only with its chain base; millimetres refused; an opening
  outside the run is not deducted again, but the masonry above its lintel is a scope gap: 1.30 x (3.00 - 2.20 - 0.20) =
  0.780 m2."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t198"))

import census_r3 as C                                           # noqa: E402

GROSS = 18.000


def wa1():
    return C.Opening("WA1", "WINDOW", 1.50, 1.20, "BLOCK", True, 0.20, faces=("INTERNAL", "EXTERNAL"),
                     clear_height_m=3.00, edge="SILL")


def pa1(h=2.40):
    return C.Opening("PA1", "PASSAGE", 1.20, h, "BLOCK", True, 0.20, faces=("INTERNAL", "EXTERNAL"),
                     lintel_bearing_m=0.20, lintel_status=C.DC, clear_height_m=3.00, lintel_depth_m=0.20,
                     edge="THRESHOLD")


def test_omitted_opening_hand_deltas():
    d = C.wall_delta(GROSS, [wa1()], pa1())
    assert d["before"][0] == pytest.approx(16.200) and d["before"][1] == C.DC
    assert d["after"][0] == pytest.approx(13.320) and d["after"][1] == C.DC
    assert d["delta_m2"] == pytest.approx(-2.880)
    assert d["delta_m2"] * 0.20 == pytest.approx(-0.576)
    c = C.consequences(pa1())
    assert c["OPENING_M2"] == (2.88, C.DC)
    assert c["BLOCK_DEDUCTION_M2"] == (2.88, C.DC)
    assert c["LINTEL_LENGTH_M"] == (1.6, C.DC)
    assert c["REVEAL_LM"] == (6.0, C.DC)
    assert c["REVEAL_DEPTH_M"] == (0.20, C.DC)
    assert c["HEAD_SOFFIT_M2"] == (0.24, C.DC)
    assert c["THRESHOLD_LM"] == (1.20, C.DC)
    assert c["FINISH_FACE_1_M2:INTERNAL"] == (2.88, C.DC) and c["FINISH_FACE_2_M2:EXTERNAL"] == (2.88, C.DC)
    assert "MASONRY_ABOVE_HEAD_M2" not in c          # inside the run: the masonry above is already in the gross


def test_window_reveal_includes_sill():
    c = C.consequences(wa1())
    assert c["REVEAL_LM"] == (5.4, C.DC)
    assert c["SILL_LM"] == (1.50, C.DC)


def test_adverse_head_not_printed_is_held_never_zero():
    op = pa1(h=None)
    c = C.consequences(op)
    assert c["OPENING_M2"] == (None, C.HELD)
    assert c["BLOCK_DEDUCTION_M2"] == (None, C.HELD)
    assert c["REVEAL_LM"] == (None, C.HELD)
    # extent-only lines do not need the head
    assert c["HEAD_SOFFIT_M2"] == (0.24, C.DC) and c["THRESHOLD_LM"] == (1.20, C.DC)
    d = C.wall_delta(GROSS, [wa1()], op)
    assert d["after"][0] is None and d["after"][1] == C.HELD
    assert d["after"][2] == (pytest.approx(12.600), pytest.approx(16.200))
    assert d["delta_m2"] is None


def test_adverse_opening_on_elevation_only_is_reported_not_measured():
    ghost = C.Opening("EX1", "OPENING", 0.10, 0.10, "BLOCK", True, 0.20, on_plan=False)
    assert C.consequences(ghost) == {"REPORT": ("ELEVATION_ONLY", C.UNKNOWN)}
    net = C.wall_net(GROSS, [wa1(), ghost])
    assert net[0] == pytest.approx(16.200)


def test_adverse_list_level_on_a_raw_chain_part():
    # the list wrote 1.85 (a chain part from +0.15) as if it were the sill above the +1.00 floor
    s, h, basis = C.redatum(ffl_m=1.00, chain_base_m=0.15, chain_parts_m=[1.85, 2.00])
    assert (s, h, basis) == (1.0, 3.0, "CHAIN")
    s2, h2, basis2 = C.redatum(ffl_m=1.00, sill_level_m=2.00, head_level_m=4.00, chain_base_m=0.15,
                               chain_parts_m=[1.85, 2.00])
    assert (s2, h2, basis2) == (1.0, 3.0, "LEVEL+CHAIN")
    with pytest.raises(ValueError, match="without its chain base"):
        C.redatum(ffl_m=1.00, chain_parts_m=[1.85, 2.00])
    with pytest.raises(ValueError, match="disagree"):
        C.redatum(ffl_m=1.00, sill_level_m=1.85, head_level_m=3.85, chain_base_m=0.15, chain_parts_m=[1.85, 2.00])
    with pytest.raises(ValueError, match="FFL"):
        C.redatum(ffl_m=None, sill_level_m=2.0, head_level_m=4.0)
    # a level equal to the floor gives a floor-level sill (curved glazing to the floor)
    assert C.redatum(ffl_m=1.00, sill_level_m=1.00, head_level_m=5.30)[:2] == (0.0, 4.3)


def test_adverse_millimetres_refused():
    with pytest.raises(ValueError, match="millimetres"):
        C.Opening("PA1", "PASSAGE", 1200, 2400, "BLOCK", True, 200)


def test_adverse_head_above_member_soffit_refused():
    with pytest.raises(ValueError, match="soffit"):
        C.Opening("PA1", "PASSAGE", 1.20, 3.10, "BLOCK", True, 0.20, clear_height_m=3.00)


def test_outside_run_not_deducted_but_masonry_above_is_a_scope_gap():
    op = C.Opening("PB1", "PASSAGE", 1.30, 2.20, "BLOCK", False, 0.15, lintel_bearing_m=0.40, lintel_status=C.DC,
                   clear_height_m=3.00, lintel_depth_m=0.20, edge="THRESHOLD")
    c = C.consequences(op)
    assert c["BLOCK_DEDUCTION_M2"] == (None, C.NA)
    assert c["MASONRY_ABOVE_HEAD_M2"] == (0.78, C.DC)
    assert C.wall_net(GROSS, [wa1(), op])[0] == pytest.approx(16.200)
    held = C.with_height(op, None)
    assert C.consequences(held)["MASONRY_ABOVE_HEAD_M2"] == (None, C.HELD)
    assert C.masonry_above_head_bounds(held) == (0.0, 3.64)       # 1.30 x (3.00 - 0.20) = 1.30 x 2.80


def test_glazed_line_and_open_side_build_before_deduct():
    gl = C.Opening("GL1", "WINDOW", 4.00, 2.50, "GLAZED", False, 0.20)
    c = C.consequences(gl)
    assert c["BLOCK_DEDUCTION_M2"] == (None, C.NA) and c["FINISH_FACE_1_M2"] == (None, C.NA)
    mouth = C.Opening("PM1", "PASSAGE", 1.20, None, "NONE", False, 0.20, faces=(None, None), edge="UNKNOWN")
    c = C.consequences(mouth)
    assert c["BLOCK_DEDUCTION_M2"] == (None, C.NA)
    assert c["EDGE_LM"] == (None, C.UNKNOWN)          # no door, no level change: no threshold established
    assert c["HEAD_SOFFIT_M2"] == (0.24, C.DC)


def test_census_revision_keeps_old_rows_and_refuses_bad_input():
    old = [{"ID": "WA1", "BOQ_LINE": "WINDOW.ALUMINIUM", "SILL_M": "1.85"},
           {"ID": "WA2", "BOQ_LINE": "WINDOW.ALUMINIUM", "SILL_M": "0.90"}]
    snapshot = [dict(r) for r in old]
    extra = ("PCS_STATUS", "PCS_REASON", "R3_CHANGE")
    rev = C.Revision(additions=[{"ID": "PA1", "BOQ_LINE": "OPENING.PASSAGE_NO_LEAF"}],
                     redatums={"WA1": {"SILL_M": "1.00"}},
                     pcs={"WA1": ("SETTLED", ""), "WA2": ("HELD", "count not settled")},
                     notes={"WA1": "re-datum"})
    new = C.revise(old, rev, extra)
    assert old == snapshot                                        # the old version is never edited
    assert [r["ID"] for r in new] == ["WA1", "WA2", "PA1"]
    assert new[0]["SILL_M"] == "1.00" and new[1]["SILL_M"] == "0.90"
    assert C.pcs_summary(new, "WINDOW.ALUMINIUM") == (1, ["WA2"])
    with pytest.raises(ValueError, match="already in the census"):
        C.revise(old, C.Revision(additions=[{"ID": "WA2"}]), extra)
    with pytest.raises(ValueError, match="not in the census"):
        C.revise(old, C.Revision(redatums={"ZZ9": {"SILL_M": "0"}}), extra)
    with pytest.raises(ValueError, match="unknown column"):
        C.revise(old, C.Revision(redatums={"WA1": {"NOPE": "0"}}), extra)
    with pytest.raises(ValueError, match="already in the list"):
        C.wall_delta(GROSS, [wa1(), pa1()], pa1())


def test_status_and_deduction_guards():
    with pytest.raises(ValueError, match="s.5"):
        C.Opening("PA1", "PASSAGE", 1.2, 2.4, "BLOCK", True, 0.2, height_status="ESTIMATED")
    big = C.Opening("BIG", "OPENING", 6.0, 3.0, "BLOCK", True, 0.2, clear_height_m=3.0)
    with pytest.raises(ValueError, match="exceed the gross"):
        C.wall_net(GROSS - 1.0, [big])
    assumed = C.Opening("D1", "DOOR", 0.90, 2.20, "BLOCK", True, 0.15, height_status=C.AOA)
    assert C.wall_net(GROSS, [assumed])[1] == C.AOA        # the weakest established status governs the net
