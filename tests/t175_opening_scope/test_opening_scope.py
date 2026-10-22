"""T-175 OPENING_SCOPE_V1: hand fixtures, NOT the development villa.

Villa "T175-A" (metres), hand truth:
  W1  block wall 0.20, run 8.00 m x clear height 2.50 m (beam soffit) = 20.00 m2 gross, DRAWING-CONFIRMED.
      window N1 1.50 x 2.00 = 3.00 m2 printed, sill 0.50 -> net 17.00 m2. Reveal 2 x 2.00 + 1.50 + 1.50 = 7.00 m.l;
      sill 1.50 m.l; lintel row 0.20 deep, min bearing 0.40: head room 2.50 - 2.50 = 0 -> the beam is the lintel.
  W2  block wall 0.15 (internal), 4.00 x 3.00 = 12.00 m2; door D1 0.90 x 2.20 (owner fallback height, ASSUMED —
      OWNER-APPROVED) = 1.98 m2 -> net 10.02 m2, status ASSUMED — OWNER-APPROVED. Wet side B: upturn not deducted,
      threshold 0.90 m.l. Lintel: room 3.00 - 2.20 = 0.80 >= 0.20: candidate face 0.20 x (0.90 + 0.80) = 0.34 m2, HELD.
  W3  full-height glazed bay, 3.60 m: construction GLAZED -> no masonry, no masonry deduction, no finish face.
  W4  RC wall 0.25 with a 1.00 x 2.10 opening: no masonry deduction; both faces' finish deduction 2.10 m2 each.
  W5  block wall 0.20, 6.00 x 3.20 = 19.20 m2 with window N2 width 1.20 printed, height NOT printed (HELD):
      net None (never 0); bounds [19.20 - 1.20 x (3.20 - 0.00), 19.20] = [15.36, 19.20].
  W6  block wall 0.20, gross 10.00, door D2 1.00 x 2.20 lying in the free-end gap OUTSIDE the run: not deducted
      (it is not in the gross): net 10.00.
Adverse: units in millimetres; a status outside section 5; one opening twice; one opening on two walls; a head above
the soffit (capped, flagged); deductions larger than the gross; mirror (side A <-> B) changes nothing but the faces."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import opening_scope_v1 as OS               # noqa: E402

DC, AOA, HELD = "DRAWING-CONFIRMED", "ASSUMED — OWNER-APPROVED", "HELD"
LINTEL = {"row": "L1", "depth_m": 0.20, "min_bearing_m": 0.40}


def _wall(i, cons="BLOCK", t=0.20, gross=None, gs=DC, clear=None):
    return {"id": i, "construction": cons, "t_m": t, "gross_m2": gross, "gross_status": gs, "clear_h_min_m": clear}


def _op(i, kind="WINDOW", w=1.5, ws=DC, h=2.0, hs=DC, sill=0.0, in_gross=True, frame=True,
        faces=("INTERNAL_PLASTER_PAINT", "EXTERNAL_PLASTER_PAINT"), wet=False, lintel=LINTEL):
    return {"id": i, "kind": kind, "width_m": w, "width_status": ws, "height_m": h, "height_status": hs,
            "sill_m": sill, "in_gross": in_gross, "frame": frame, "faces": faces, "wet_side": wet, "lintel": lintel}


def test_normal_window_20_minus_3_is_17():
    r = OS.wall_net(_wall("W1", gross=20.0, clear=2.5), [_op("N1", sill=0.5)])
    assert r["net_m2"] == pytest.approx(17.0)
    assert r["net_status"] == DC
    c = r["openings"][0]
    assert c["block_deduction"]["m2"] == pytest.approx(3.0)
    assert [f["m2"] for f in c["finish_deduction"]] == [pytest.approx(3.0), pytest.approx(3.0)]
    assert c["reveal_lm"]["m"] == pytest.approx(7.0)
    assert c["edge"] == {"kind": "SILL", "m": 1.5, "status": DC}
    assert c["reveal_depth"]["status"] == HELD            # framed: frame position not drawn
    assert c["lintel"]["status"] == "NOT_APPLICABLE"      # head at the soffit: the beam is the lintel
    assert c["flags"] == []


def test_door_owner_fallback_height_wet_side_and_lintel_candidate():
    r = OS.wall_net(_wall("W2", t=0.15, gross=12.0, clear=3.0),
                    [_op("D1", kind="DOOR", w=0.9, h=2.2, hs=AOA,
                         faces=("INTERNAL_PLASTER_PAINT", "WALL_TILE"), wet=True)])
    assert r["net_m2"] == pytest.approx(10.02)
    assert r["net_status"] == AOA
    c = r["openings"][0]
    assert c["waterproofing"]["upturn_deducted"] is False
    assert c["waterproofing"]["threshold_lm"] == pytest.approx(0.9)
    assert c["edge"]["kind"] == "THRESHOLD"
    assert c["reveal_lm"]["m"] == pytest.approx(2 * 2.2 + 0.9)
    lt = c["lintel"]
    assert lt["status"] == HELD and lt["face_m2_candidate_at_min_bearing"] == pytest.approx(0.34)
    assert c["finish_deduction"][1]["family"] == "WALL_TILE"


def test_adverse_full_height_glazed_bay_no_block_no_deduction():
    r = OS.wall_net(_wall("W3", cons="GLAZED", gross=None, gs=HELD),
                    [_op("G1", w=3.6, h=3.5)])
    c = r["openings"][0]
    assert c["block_deduction"]["status"] == "NOT_APPLICABLE" and c["block_deduction"]["m2"] is None
    assert all(f["status"] == "NOT_APPLICABLE" for f in c["finish_deduction"])
    assert r["deducted_m2"] == 0.0
    assert r["net_m2"] is None                             # no masonry is measured here, never invented


def test_adverse_opening_in_rc_wall_no_block_deduction_finishes_still_deducted():
    r = OS.wall_net(_wall("W4", cons="RC", t=0.25, gross=None, gs=HELD),
                    [_op("R1", kind="PASSAGE", w=1.0, h=2.1, frame=False)])
    c = r["openings"][0]
    assert c["block_deduction"]["status"] == "NOT_APPLICABLE"
    assert [f["m2"] for f in c["finish_deduction"]] == [pytest.approx(2.1), pytest.approx(2.1)]
    assert c["reveal_depth"] == {"m": 0.25, "status": DC}  # frameless: the full wall thickness
    assert c["lintel"]["status"] == "NOT_APPLICABLE"


def test_adverse_held_height_never_zero_with_bounds():
    r = OS.wall_net(_wall("W5", gross=19.2, clear=3.2), [_op("N2", w=1.2, h=None, hs=HELD)])
    assert r["net_m2"] is None and r["net_status"] == HELD
    assert r["held_openings"] == ["N2"]
    lo, hi = r["net_bounds_m2"]
    assert lo == pytest.approx(15.36) and hi == pytest.approx(19.2)
    c = r["openings"][0]
    assert c["block_deduction"]["m2"] is None and c["opening_m2"] is None
    assert c["reveal_lm"]["m"] is None and c["lintel"]["status"] == HELD
    assert c["edge"]["m"] == pytest.approx(1.2)            # the width is still known


def test_opening_outside_the_gross_run_is_not_deducted_again():
    r = OS.wall_net(_wall("W6", gross=10.0, clear=3.0), [_op("D2", kind="DOOR", w=1.0, h=2.2, hs=AOA, in_gross=False)])
    assert r["net_m2"] == pytest.approx(10.0)
    assert r["openings"][0]["block_deduction"]["status"] == "NOT_APPLICABLE"
    assert r["net_status"] == DC                           # nothing deducted: the gross status stands


def test_head_above_soffit_is_capped_and_flagged():
    r = OS.wall_net(_wall("W7", gross=12.0, clear=3.0), [_op("N3", w=1.0, h=2.5, sill=1.0)])
    c = r["openings"][0]
    assert "HEAD_ABOVE_SOFFIT" in c["flags"]
    assert c["block_deduction"]["m2"] == pytest.approx(2.0)
    assert c["block_deduction"]["beyond_masonry_m2"] == pytest.approx(0.5)
    assert r["net_m2"] == pytest.approx(10.0)


def test_finish_band_cap_up_open_sched_001():
    # window 1.20 x 2.00, sill 1.00 (head 3.00); internal finish top 2.80 (false ceiling), external to the beam 3.50
    op = _op("N4", w=1.2, h=2.0, sill=1.0)
    op["finish_top_m"] = (2.8, 3.5)
    c = OS.opening_consequences(op, _wall("W9", clear=3.5))
    assert c["finish_deduction"][0]["m2"] == pytest.approx(1.2 * 1.8)     # min(3.0, 2.8) - 1.0
    assert c["finish_deduction"][1]["m2"] == pytest.approx(2.4)           # full opening
    assert c["block_deduction"]["m2"] == pytest.approx(2.4)               # masonry: full opening, no band


def test_mirror_swaps_faces_only():
    a = OS.wall_net(_wall("W1", gross=20.0, clear=2.5), [_op("N1", sill=0.5, faces=("A_FAM", "B_FAM"))])
    b = OS.wall_net(_wall("W1", gross=20.0, clear=2.5), [_op("N1", sill=0.5, faces=("B_FAM", "A_FAM"))])
    assert a["net_m2"] == b["net_m2"]
    assert [f["family"] for f in a["openings"][0]["finish_deduction"]] == ["A_FAM", "B_FAM"]
    assert [f["family"] for f in b["openings"][0]["finish_deduction"]] == ["B_FAM", "A_FAM"]


@pytest.mark.parametrize("kw", [{"w": 1500.0}, {"h": 2200.0}])
def test_adverse_millimetres_refused(kw):
    with pytest.raises(ValueError, match="millimetres"):
        OS.wall_net(_wall("W1", gross=20.0, clear=2.5), [_op("N1", **kw)])


def test_adverse_status_outside_section_5_refused():
    with pytest.raises(ValueError, match="section-5"):
        OS.wall_net(_wall("W1", gross=20.0), [_op("N1", hs="INFERRED")])
    with pytest.raises(ValueError, match="section-5"):
        OS.wall_net(_wall("W1", gross=20.0, gs="PROVISIONAL"), [])


def test_adverse_double_count_refused():
    with pytest.raises(ValueError, match="twice"):
        OS.wall_net(_wall("W1", gross=20.0), [_op("N1"), _op("N1")])
    w1 = dict(_wall("W1", gross=20.0), openings=[_op("N1")])
    w2 = dict(_wall("W2", gross=20.0), openings=[_op("N1")])
    with pytest.raises(ValueError, match="two walls"):
        OS.walls_net([w1, w2])
    w3 = dict(_wall("W3", gross=20.0), openings=[_op("N1", in_gross=False)])
    assert len(OS.walls_net([w1, w3])) == 2                # listed on its neighbour, deducted once


def test_adverse_deductions_larger_than_gross_refused():
    with pytest.raises(ValueError, match="exceed"):
        OS.wall_net(_wall("W1", gross=2.0, clear=3.0), [_op("N1", w=1.5, h=2.0)])


def test_held_gross_keeps_net_held_even_with_known_openings():
    r = OS.wall_net(_wall("W8", gross=15.0, gs=HELD, clear=3.0), [_op("N1")])
    assert r["net_m2"] is None and r["net_status"] == HELD
    assert r["deducted_m2"] == pytest.approx(3.0)          # the consequence stays listed


def test_policy_not_wired():
    p = OS.policy_record()
    assert p["wired"] is False and "Q-73 (owner, CONFIRMED 2026-10-22)" in p["rules"]
