"""T-482: BLOCKWORK_CONDITIONS_V1 on a SYNTHETIC villa (VILLA-SYNTH-482), never the training villa.

Fixture (hand-drawn, not from any project): ground slab FFL +0.60 with a drawn 0.08 build-up (top +0.52); first plate
carries the first-floor FFL +4.10 (drawn build-up 0.08) AND a roof terrace printed +4.10: one plate, top +4.02; the
penthouse roof is a roof-only plate printed +7.40 (finished), build-up unprinted. Storeys: ground 3.50 (structural),
penthouse U-storey 7.40 - 4.02 = 3.38 at b_r = 0 (the architectural chain 7.40 - 4.10 = 3.30 is refused).
Penthouse wall PW-1 (0.15): 3.00 m under a 0.50 beam, 1.50 m under a 0.15 slab, a 0.90 door with no printed height
(declared fallback 2.10). Hand: U = 3.00 x 2.88 + 1.50 x 3.23 - 1.89 = 11.595 m2, L = 4.50 m;
at b_r = 0.10: 11.595 - 0.45 = 11.145 m2 = V1 at storey 3.28 (3 x 2.78 + 1.5 x 3.13 - 1.89).
Width conflict: wall X-7 4.00 m, last 0.05 m under a band drawn 0.30 (depth 0.60) vs scheduled 0.25 on the outer face
(no cover): readings 4.00 x 3.35 = 13.40 (schedule) and 3.95 x 3.35 + 0.05 x 2.90 = 13.3775 (drawn): range
[13.3775, 13.40], width 0.0225 = 0.05 x (3.35 - 2.90).
Parapet run R-2: drawn at roof level 4.00 m, height 1.10, upstand 0.30 -> [0, 3.20]; the floor outline below carried
4.40 -> delta (4.00 - 4.40) x 0.80 = -0.32 m2.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from engine import project_config as pc
from engine.source import blockwork_basis_rules_v1 as R

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("blockwork_conditions_v1_t482",
                                               ROOT / "research/agents_t482/blockwork_conditions_v1.py")
C = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = C
_spec.loader.exec_module(C)

PH, DOOR, UP = "STOREY_HEIGHT.PH.MAIN", "OPENING.DOOR.FALLBACK_HEIGHT", "PARAPET.UP"


def f(fid, value, src="DRAWING"):
    return {"fact_id": fid, "version": 1, "quantity_kind": "LENGTH", "value": value, "unit": "m",
            "source": {"kind": src, "reference": "synthetic section S-482"},
            "approval": {"status": "APPROVED", "date": "2026-10-01",
                         "by": "PROJECT_OWNER" if src == "OWNER_DECISION" else "DESIGNER"},
            "affected_lines": ["MAS.SYNTH"], "confidence": "CONFIRMED"}


def cfg(*facts):
    return pc.parse_project_config({"schema": pc.SCHEMA, "project_id": "VILLA-SYNTH-482", "config_version": "0.1.0",
                                    "facts": list(facts or (f(PH, 3.30), f(DOOR, 2.10, "OWNER_DECISION"),
                                                            f(UP, 0.30)))})


GROUND = C.Plate("G", (C.Zone("G-FLOOR", C.FLOOR, 0.60, 0.08),))
P1 = C.Plate("P1", (C.Zone("1F", C.FLOOR, 4.10, 0.08), C.Zone("TERRACE", C.ROOF, 4.10)))
P2 = C.Plate("P2", (C.Zone("PH-ROOF", C.ROOF, 7.40),))
PW1 = (R.Piece("beam", 3.00, depth_m=0.50), R.Piece("slab", 1.50, slab_t_m=0.15))
PW1_OPS = (R.Opening("D1", R.DOOR, width_m=0.90),)


# ------------------------------------------------------------------ R-MAS-ROOF-DATUM-1 normal
def test_plate_with_floor_zone_takes_ffl_minus_buildup():
    d = C.plate_top(P1)
    assert d.state == R.VALUED and d.top_m == pytest.approx(4.02)
    assert C.plate_top(GROUND).top_m == pytest.approx(0.52)


def test_roof_only_plate_is_roof_datum_with_upper_mark():
    d = C.plate_top(P2, "a printed bound, named beside")
    assert d.state == C.ROOF_DATUM and d.top_m is None and d.upper_m == pytest.approx(7.40)
    assert d.beside == ("a printed bound, named beside",)


def test_structural_storeys():
    g, p1, p2 = C.plate_top(GROUND), C.plate_top(P1), C.plate_top(P2)
    assert C.structural_storey(g, p1) == (pytest.approx(3.50), None)
    assert C.structural_storey(p1, p2) == (None, pytest.approx(3.38))
    assert C.refuse_finished_chain(3.50, g, p1) is True


def test_wall_under_roof_hand_value():
    p1, p2 = C.plate_top(P1), C.plate_top(P2)
    w = C.wall_under_roof(cfg(), "PW-1", PH, p1, p2, PW1, PW1_OPS, DOOR, what_if_storey_m=3.28)
    assert w.state == C.ROOF_DATUM and not w.part
    assert w.upper_m2 == pytest.approx(11.595, abs=1e-9) and w.datum_length_m == pytest.approx(4.50)
    assert w.v1_at_storey == pytest.approx(11.145, abs=1e-9)
    assert w.upper_m2 - 0.10 * w.datum_length_m == pytest.approx(w.v1_at_storey, abs=1e-9)


def test_mirrored_piece_order_same_result():
    p1, p2 = C.plate_top(P1), C.plate_top(P2)
    a = C.wall_under_roof(cfg(), "PW-1", PH, p1, p2, PW1, PW1_OPS, DOOR)
    b = C.wall_under_roof(cfg(), "PW-1", PH, p1, p2, tuple(reversed(PW1)), PW1_OPS, DOOR)
    assert (a.upper_m2, a.datum_length_m) == (b.upper_m2, b.datum_length_m)


def test_held_piece_gives_part_bound_and_held_wall_stays_held():
    p1, p2 = C.plate_top(P1), C.plate_top(P2)
    pcs = PW1 + (R.Piece("unsized", 1.00, held_reason="depth not printed"),)
    w = C.wall_under_roof(cfg(), "PW-2", PH, p1, p2, pcs, PW1_OPS, DOOR)
    assert w.part and w.datum_length_m == pytest.approx(4.50)          # the held piece is not in L
    assert any("depth not printed" in h for h in w.held)
    h = C.wall_under_roof(cfg(), "PW-3", PH, p1, p2, (R.Piece("x", 2.0, held_reason="dome opening"),))
    assert h.state == R.HELD and h.upper_m2 is None and h.datum_length_m is None   # never 0


# ------------------------------------------------------------------ R-MAS-ROOF-DATUM-1 adverse
def test_architectural_chain_under_a_roof_refused():
    with pytest.raises(C.ConditionError, match="FINISHED_AS_STRUCTURAL"):
        C.refuse_finished_chain(3.30, C.plate_top(P1), C.plate_top(P2))     # 7.40 - 4.10 from the FFL chain


def test_wrong_declared_storey_refused():
    with pytest.raises(C.ConditionError, match="STOREY_MISMATCH"):
        C.refuse_finished_chain(3.58, C.plate_top(GROUND), C.plate_top(P1))  # FFL 4.10 - 0.52 mixes datums


def test_roof_buildup_constant_refused():
    with pytest.raises(C.ConditionError, match="ROOF_BUILDUP_CONSTANT"):
        C.plate_top(C.Plate("P2x", (C.Zone("PH-ROOF", C.ROOF, 7.40, 0.05),)))


def test_one_plate_two_tops_refused():
    with pytest.raises(C.ConditionError, match="PLATE_CONFLICT"):
        C.plate_top(C.Plate("Px", (C.Zone("a", C.FLOOR, 4.10, 0.08), C.Zone("b", C.FLOOR, 4.30, 0.08))))
    with pytest.raises(C.ConditionError, match="PLATE_CONFLICT"):
        C.plate_top(C.Plate("Py", (C.Zone("a", C.ROOF, 7.40), C.Zone("b", C.ROOF, 7.60))))


def test_units_and_kinds_refused():
    with pytest.raises(C.ConditionError, match="BAD_UNITS"):
        C.plate_top(C.Plate("mm", (C.Zone("PH-ROOF", C.ROOF, 7400.0),)))       # millimetres read as metres
    with pytest.raises(C.ConditionError, match="BAD_ZONE"):
        C.plate_top(C.Plate("k", (C.Zone("z", "BALCONY", 4.10),)))
    with pytest.raises(C.ConditionError, match="NO_ZONE"):
        C.plate_top(C.Plate("e", ()))


def test_floor_zone_without_drawn_buildup_is_held_not_default():
    d = C.plate_top(C.Plate("Pn", (C.Zone("1F", C.FLOOR, 4.10),)))
    assert d.state == R.HELD and d.top_m is None


def test_wall_rule_refuses_a_known_top_and_a_held_base():
    with pytest.raises(C.ConditionError, match="NOT_ROOF_ONLY"):
        C.wall_under_roof(cfg(), "PW-1", PH, C.plate_top(GROUND), C.plate_top(P1), PW1)
    held = C.plate_top(C.Plate("Pn", (C.Zone("1F", C.FLOOR, 4.10),)))
    with pytest.raises(C.ConditionError, match="BASE_HELD"):
        C.wall_under_roof(cfg(), "PW-1", PH, held, C.plate_top(P2), PW1)


# ------------------------------------------------------------------ R-MAS-WIDTH-CONFLICT-1
READ = {"band drawn 0.30": 3.95 * 3.35 + 0.05 * 2.90, "band schedule 0.25": 4.00 * 3.35}


def test_width_conflict_range_hand_value():
    r = C.width_conflict("X-7", "D-SYN-1", READ)
    assert r.state == C.CONFLICT and (r.low, r.high) == (pytest.approx(13.3775), pytest.approx(13.40))
    assert r.low_reading == "band drawn 0.30" and r.high - r.low == pytest.approx(0.05 * (3.35 - 2.90))


def test_width_conflict_one_end_as_confirmed_refused():
    for end in (13.3775, 13.40):
        with pytest.raises(C.ConditionError, match="CONFLICT_ONE_END"):
            C.width_conflict("X-7", "D-SYN-1", READ, carried=end, carried_status=R.DRAWING_CONFIRMED)
    assert C.width_conflict("X-7", "D-SYN-1", READ, carried=13.3775, carried_status="CONFLICT").low == \
        pytest.approx(13.3775)


def test_width_conflict_needs_both_readings_and_an_item():
    with pytest.raises(C.ConditionError, match="ONE_READING"):
        C.width_conflict("X-7", "D-SYN-1", {"band drawn 0.30": 13.3775})
    with pytest.raises(C.ConditionError, match="NO_CONFLICT_ID"):
        C.width_conflict("X-7", "", READ)


def test_drop_upper_is_max_over_readings():
    assert C.drop_upper_over_readings("Y-2", {"drawn": 10.0, "schedule": 10.02}) == (pytest.approx(10.02),
                                                                                       "schedule")
    with pytest.raises(C.ConditionError, match="ONE_READING"):
        C.drop_upper_over_readings("Y-2", {"drawn": 10.0})


# ------------------------------------------------------------------ R-MAS-PARAPET-RUN-1
def test_parapet_on_roof_level_run_and_delta():
    r, delta = C.parapet_alternative(cfg(), C.ParapetRun("R-2", 4.00, 1.10, "ROOF_LEVEL"), UP,
                                     previous_centreline_m=4.40)
    assert (r.low, r.high) == (0.0, pytest.approx(3.20)) and delta == pytest.approx(-0.32)


def test_parapet_floor_outline_run_refused():
    with pytest.raises(C.ConditionError, match="FLOOR_OUTLINE_RUN"):
        C.parapet_alternative(cfg(), C.ParapetRun("R-2", 4.40, 1.10, "FLOOR_OUTLINE"), UP)


def test_parapet_undeclared_upstand_stays_blank():
    r, delta = C.parapet_alternative(cfg(f(PH, 3.30)), C.ParapetRun("R-2", 4.00, 1.10, "ROOF_LEVEL"), UP,
                                     previous_centreline_m=4.40)
    assert r.high is None and r.low is None and delta is None
