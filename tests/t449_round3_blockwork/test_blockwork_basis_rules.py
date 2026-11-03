"""T-449 round 3: BLOCKWORK_BASIS_RULES_V1 on a SYNTHETIC villa (VILLA-SYNTH-05), never the training villa.

Fixture (hand-drawn, not from any project): ground storey 3.60 m structural top to structural top, first storey 3.30 m;
declared door fallback 2.10 m (owner decision). Wall SW-1 (0.20 m): 4.00 m under a 0.60 m deep beam (h 3.00) and
2.00 m under a 0.20 m slab with no beam (h 3.40); a drawn window outline 1.50 m2 and a 0.90 m door with no printed
height (0.90 x 2.10 = 1.89 m2, ASSUMED - OWNER-APPROVED). Hand: 4.00 x 3.00 + 2.00 x 3.40 = 18.80 - 1.50 - 1.89 =
15.41 m2; volume 15.41 x 0.20 = 3.082 m3.
Adverse: an undeclared / pending storey or door height (HELD, never 0), a storey in millimetres declared as metres, a
piece with two soffits, a held piece (established PART), an undeductible opening (whole wall HELD), openings inside
the held piece, openings exceeding the closable part, a sunken slab piece (U - L x d), mirrored piece order, a wall
with no drawn piece, parapet block alternatives.
"""

from __future__ import annotations

import pytest

from engine import project_config as pc
from engine.source import blockwork_basis_rules_v1 as R

GF, FF, DOOR, UP = "STOREY_HEIGHT.GF.MAIN", "STOREY_HEIGHT.1F.MAIN", "OPENING.DOOR.FALLBACK_HEIGHT", "PARAPET.UP"


def f(fid, value, unit="m", status="APPROVED", src="DRAWING"):
    d = {"fact_id": fid, "version": 1, "quantity_kind": "LENGTH", "value": value, "unit": unit,
         "source": {"kind": src, "reference": "synthetic section S-03"},
         "approval": {"status": status, "date": "2026-10-01"}, "affected_lines": ["MAS.SYNTH"],
         "confidence": "CONFIRMED" if status == "APPROVED" else "PROVISIONAL"}
    if status == "APPROVED":
        d["approval"]["by"] = "PROJECT_OWNER" if src == "OWNER_DECISION" else "DESIGNER"
    return d


BASE = (f(GF, 3.60), f(FF, 3300, unit="mm"), f(DOOR, 2.10, src="OWNER_DECISION"), f(UP, 0.30))


def cfg(*facts):
    return pc.parse_project_config({"schema": pc.SCHEMA, "project_id": "VILLA-SYNTH-05", "config_version": "0.1.0",
                                    "facts": list(facts or BASE)})


SW1 = (R.Piece("beam", 4.00, depth_m=0.60), R.Piece("slab", 2.00, slab_t_m=0.20))
SW1_OPS = (R.Opening("W1", "WINDOW", outline_m2=1.50), R.Opening("D1", R.DOOR, width_m=0.90))


# ---------------------------------------------------------------- normal

def test_piece_heights_from_storey_and_soffit():
    assert R.piece_height(3.60, SW1[0]) == (3.0, None)
    assert R.piece_height(3.60, SW1[1]) == (3.4, None)


def test_wall_net_hand_value_and_owner_status():
    r = R.wall_net(cfg(), "SW-1", GF, SW1, SW1_OPS, door_fallback_fact=DOOR)
    assert r.state == R.VALUED and r.value == pytest.approx(15.41, abs=1e-9)
    assert r.deducted_m2 == pytest.approx(3.39, abs=1e-9)
    assert r.status == R.ASSUMED_OWNER_APPROVED and r.facts_used == (GF, DOOR)
    assert R.panel_area(r) == r.value and R.volume(r, 0.20) == pytest.approx(3.082, abs=1e-9)


def test_drawing_only_wall_is_drawing_confirmed():
    r = R.wall_net(cfg(), "SW-1", GF, SW1, (R.Opening("W1", "WINDOW", width_m=1.0, height_m=1.5),))
    assert r.value == pytest.approx(17.30, abs=1e-9) and r.status == R.DRAWING_CONFIRMED and r.facts_used == (GF,)


def test_storey_declared_in_millimetres_is_converted():
    r = R.wall_net(cfg(), "FF-1", FF, (R.Piece("b", 2.50, depth_m=0.50),))
    assert r.value == pytest.approx(2.50 * 2.80, abs=1e-9)          # 3300 mm - 0.50 = 2.80 m


def test_mirrored_piece_order_same_result():
    a = R.wall_net(cfg(), "SW-1", GF, SW1, SW1_OPS, door_fallback_fact=DOOR)
    b = R.wall_net(cfg(), "SW-1", GF, tuple(reversed(SW1)), tuple(reversed(SW1_OPS)), door_fallback_fact=DOOR)
    assert a.value == b.value and a.state == b.state


# ---------------------------------------------------------------- adverse: held, never 0

def test_undeclared_storey_is_held_never_zero():
    r = R.wall_net(cfg(), "AX-1", "STOREY_HEIGHT.GF.ANNEX", SW1)
    assert r.state == R.HELD and r.value is None and R.volume(r, 0.2) is None
    assert any("not declared" in h for h in r.held)


def test_pending_storey_is_held():
    r = R.wall_net(cfg(f(GF, 3.60, status="PENDING"), f(DOOR, 2.10, src="OWNER_DECISION")), "SW-1", GF, SW1)
    assert r.state == R.HELD and r.value is None


def test_door_without_declared_fallback_holds_the_wall():
    r = R.wall_net(cfg(f(GF, 3.60)), "SW-1", GF, SW1, SW1_OPS, door_fallback_fact=DOOR)
    assert r.state == R.HELD and r.value is None and any("D1" in h for h in r.held)


def test_window_without_printed_height_holds_the_wall_no_fallback():
    r = R.wall_net(cfg(), "SW-1", GF, SW1, (R.Opening("W2", "WINDOW", width_m=1.2),), door_fallback_fact=DOOR)
    assert r.state == R.HELD and r.value is None


def test_held_piece_gives_established_part_only():
    pcs = SW1 + (R.Piece("dome", 1.10, held_reason="dome opening: nothing drawn over it"),)
    r = R.wall_net(cfg(), "SW-1", GF, pcs, (R.Opening("W1", "WINDOW", outline_m2=1.50),
                                            R.Opening("D9", R.DOOR, in_held_piece=True)))
    assert r.state == R.PART and r.value == pytest.approx(18.80 - 1.50, abs=1e-9)
    assert any("dome" in h for h in r.held)


def test_undrawn_member_depth_holds_the_piece():
    r = R.wall_net(cfg(), "SW-1", GF, (R.Piece("unlabelled", 2.0),))
    assert r.state == R.HELD and r.value is None


def test_held_note_holds_the_whole_wall():
    r = R.wall_net(cfg(), "SW-1", GF, SW1, held_notes=("tie beam called for, size not printed",))
    assert r.state == R.HELD and r.value is None


def test_openings_exceeding_the_closable_part_with_held_pieces_hold_the_wall():
    pcs = (R.Piece("b", 0.30, depth_m=0.60), R.Piece("h", 3.0, held_reason="nothing drawn"))
    r = R.wall_net(cfg(), "SW-2", GF, pcs, (R.Opening("D2", "DOOR", outline_m2=1.89),))
    assert r.state == R.HELD and r.value is None


def test_openings_exceeding_a_fully_drawn_wall_are_refused():
    with pytest.raises(R.BlockworkRuleError, match="NON_POSITIVE"):
        R.wall_net(cfg(), "SW-2", GF, (R.Piece("b", 0.30, depth_m=0.60),), (R.Opening("D2", "DOOR", outline_m2=1.89),))


def test_no_drawn_piece_is_held():
    r = R.wall_net(cfg(), "GL-1", GF, ())
    assert r.state == R.HELD and r.value is None


def test_sunken_piece_gives_upper_bound_and_drop_length():
    pcs = (R.Piece("b", 1.0, depth_m=0.60), R.Piece("wet", 1.5, slab_t_m=0.20, sunken=True))
    r = R.wall_net(cfg(), "SW-3", GF, pcs)
    assert r.state == R.DROP and r.value is None
    assert r.upper_m2 == pytest.approx(3.0 + 1.5 * 3.4, abs=1e-9) and r.drop_length_m == pytest.approx(1.5)
    assert R.volume(r, 0.2) is None


def test_unit_errors_refused():
    with pytest.raises(R.BlockworkRuleError, match="BAD_UNITS"):
        R.wall_net(cfg(f(GF, 3600), f(DOOR, 2.1, src="OWNER_DECISION")), "SW-1", GF, SW1)   # mm declared as m
    with pytest.raises(R.BlockworkRuleError, match="BAD_UNITS"):
        R.wall_net(cfg(), "SW-1", GF, (R.Piece("b", 4000, depth_m=0.6),))                    # piece in mm
    with pytest.raises(R.BlockworkRuleError, match="BAD_UNITS"):
        R.wall_net(cfg(), "SW-1", GF, (R.Piece("b", 4.0, depth_m=600),))                     # depth in mm
    with pytest.raises(R.BlockworkRuleError, match="TWO_SOFFITS"):
        R.wall_net(cfg(), "SW-1", GF, (R.Piece("b", 4.0, depth_m=0.6, slab_t_m=0.2),))
    with pytest.raises(R.BlockworkRuleError, match="DUPLICATE_PIECE"):
        R.wall_net(cfg(), "SW-1", GF, (SW1[0], SW1[0]))


def test_soffit_deeper_than_the_storey_refused():
    with pytest.raises(R.BlockworkRuleError, match="BAD_LEVEL"):
        R.wall_net(cfg(f(GF, 2.5), f(DOOR, 2.1, src="OWNER_DECISION")), "SW-1", GF, (R.Piece("b", 4.0, depth_m=2.9),))


# ---------------------------------------------------------------- parapet block alternative

def test_parapet_block_alternative_hand_range():
    r = R.parapet_block_alternative(cfg(), "P1", 10.0, 1.30, UP)
    assert (r.low, r.high) == (0.0, pytest.approx(10.0, abs=1e-9)) and r.state == R.HELD and r.facts_used == (UP,)


def test_parapet_lower_than_upstand_has_no_block_and_rc_decided_is_zero_range():
    assert R.parapet_block_alternative(cfg(), "P2", 5.0, 0.25, UP).high == 0.0
    r = R.parapet_block_alternative(cfg(), "P3", 5.0, 1.0, UP, material_decided_rc=True)
    assert (r.low, r.high) == (0.0, 0.0)


def test_parapet_without_declared_upstand_is_blank():
    r = R.parapet_block_alternative(cfg(f(GF, 3.6)), "P1", 10.0, 1.30, UP)
    assert r.low is None and r.high is None and "HELD" in r.held_reason
