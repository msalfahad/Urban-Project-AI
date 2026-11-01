"""T-434 winder-turn reading test on a non-Alsenan hand fixture (Villa K434) with adverse cases.

Villa K434 (hand-made, every figure below computed by hand):
- lower floor FFL +0.15, printed half landing +2.55: rise 2.40 m; straight going 0.300; lane 1.000.
- SECTION draws 9 straight + 6 turn risers = 15 -> riser 0.160 (check 0.150 - 0.170 PASS); its dashed winder treads at
  +1.59 / +1.75 / +1.91 / +2.07 (behind fronts 9 .. 12: 0.15 + 9 x 0.16 = 1.59, ...), drawn with 1 - 2 mm scaling noise.
- ARCH PLAN draws 9 + 5 = 14 -> 0.171429 (FAIL); its tread levels 0.15 + 9 x 0.171429 = 1.692857 vs 1.59 (FAIL).
- STRUCTURAL PLAN draws 11 + 4 = 15 -> 0.160 (PASS) but its foot is a further 2 goings south: -3.000 vs -2.400 (FAIL),
  and its first winder tread sits at 0.15 + 11 x 0.16 = 1.91 vs the drawn 1.59 (FAIL).
- Owner rule (as Q-46 A): the section counts. Governing: SECTION, 6 turn risers.
- The plans draw 4 radial winder fronts (a 5-riser turn): subdivision not drawn for 6 -> fronts and marble HELD (A8).
- Turn region: front of the first winder to the landing edge = 1.000 x 1.000 square + the 0.050 front strip
  = 1.000 + 0.050 = 1.050 m2 (beside, never the quantity while HELD).
"""

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t434"))
import winder_turn as W  # noqa: E402

FFL, LAND = 0.15, 2.55
SEC_LEVELS = (1.591, 1.748, 1.911, 2.072)
REGION = [(-1.0, -0.05), (0.0, -0.05), (0.0, 1.0), (-1.0, 1.0)]


def readings(section=True):
    rs = [W.Reading("ARCH", "arch_plan", 9, 5, foot_s=-2.400, going=0.300),
          W.Reading("ST", "structural_plan", 11, 4, foot_s=-3.000, going=0.300)]
    if section:
        rs.insert(0, W.Reading("SEC", "section", 9, 6, foot_s=-2.380, going=0.300))
    return rs


def fronts(n):
    # n radial fronts from the inner corner of a 1.000 square, fanned evenly over 90 deg; lengths by hand below
    out = []
    for i in range(1, n + 1):
        a = math.radians(90.0 * i / (n + 1))
        ln = 1.0 / max(math.cos(a), math.sin(a))
        out.append((f"R{i}", round(ln, 6), "drawn"))
    return out


def drawing(n_fronts, drawings=("ARCH", "ST")):
    return W.TurnDrawing(winder_fronts=fronts(n_fronts), landing_edge_m=1.0, landing_edge_drawings=drawings,
                         region_polygon=REGION)


# ---------------------------------------------------------------- normal
def test_governing_is_the_owner_named_section_and_consistent():
    g = W.governing(readings(), FFL, LAND, "section", SEC_LEVELS)
    assert g["governing"] == "SEC" and g["turn_risers"] == 6 and g["status"] == W.CONFIRMED
    t = {r["reading"]: r for r in g["table"]}
    assert t["SEC"]["riser_m"] == pytest.approx(0.16) and t["SEC"]["riser_check"] == "PASS"
    assert t["SEC"]["level_check"] == "PASS" and t["SEC"]["level_miss_m"] <= 0.002 + 1e-9
    assert t["ARCH"]["riser_m"] == pytest.approx(2.40 / 14, abs=1e-6) and t["ARCH"]["riser_check"] == "FAIL"
    assert t["ARCH"]["verdict"] == W.REJECTED and "level_check" in t["ARCH"]["rejected_because"]
    assert t["ST"]["riser_check"] == "PASS"                      # a passing riser alone is not a reason to govern
    assert t["ST"]["verdict"] == W.REJECTED and set(t["ST"]["rejected_because"]) == {"level_check", "foot_check"}
    assert t["SEC"]["straight_run_m"] == pytest.approx(2.4) and t["ST"]["straight_run_m"] == pytest.approx(3.0)


def test_turn_quantities_subdivision_not_drawn_held_with_beside():
    q = W.turn_quantities(6, drawing(4))
    assert q["nosing_pieces"] == 6 and q["winder_tread_pieces"] == 6
    assert q["landing_edge"]["status"] == W.CONFIRMED and q["landing_edge"]["lm"] == pytest.approx(1.0)
    assert q["winder_fronts"]["status"] == W.HELD and q["winder_fronts"]["lm"] is None
    assert q["tread_marble"]["status"] == W.HELD and q["tread_marble"]["m2"] is None
    assert q["tread_marble"]["beside_m2"] == pytest.approx(1.05)
    assert "WINDER_SUBDIVISION_NOT_DRAWN" in q["cause"]


def test_turn_quantities_subdivision_drawn_for_the_governing_count():
    # 5 drawn fronts for a 6-riser turn: measured. Hand: fan at 15/30/45/60/75 deg over a 1.000 square:
    # 1/cos15 + 1/cos30 + 1/cos45 + 1/sin60 + 1/sin75 = 1.035276 + 1.154701 + 1.414214 + 1.154701 + 1.035276 = 5.794168
    q = W.turn_quantities(6, drawing(5))
    assert q["winder_fronts"]["status"] == W.CONFIRMED
    assert q["winder_fronts"]["lm"] == pytest.approx(5.794168, abs=2e-6)
    assert q["tread_marble"]["status"] == W.CONFIRMED and q["tread_marble"]["m2"] == pytest.approx(1.05)


# ---------------------------------------------------------------- adverse
def test_adverse_best_fit_without_governing_reason_is_held():
    """'winder count taken from the drawing that fits best without a governing reason' must be refused: the section
    fits every check, yet with no owner rule naming a source nothing governs and every turn quantity stays blank."""
    g = W.governing(readings(), FFL, LAND, None, SEC_LEVELS)
    assert g["governing"] is None and g["turn_risers"] is None and g["status"] == W.HELD
    assert g["reason"].startswith("NO_GOVERNING_REASON")
    assert all(r["verdict"] == W.CONFLICT for r in g["table"])
    q = W.turn_quantities(g["turn_risers"], drawing(5))
    assert q["nosing_pieces"] is None and q["winder_tread_pieces"] is None
    assert q["landing_edge"]["lm"] is None and q["winder_fronts"]["lm"] is None and q["tread_marble"]["m2"] is None


def test_adverse_rule_source_absent_is_held_not_next_best():
    g = W.governing(readings(section=False), FFL, LAND, "section", SEC_LEVELS)
    assert g["governing"] is None and g["status"] == W.HELD     # never falls back to the passing ST riser


def test_adverse_governing_source_inconsistent_is_conflict():
    bad_levels = (1.70, 1.87, 2.04)                              # drawn treads not on the section's own risers
    g = W.governing(readings(), FFL, LAND, "section", bad_levels)
    assert g["status"] == W.HELD and g["reason"].startswith("CONFLICT")
    far = [W.Reading("SEC", "section", 9, 6, foot_s=-3.600, going=0.300)] + readings(section=False)
    g2 = W.governing(far, FFL, LAND, "section", SEC_LEVELS)
    assert g2["status"] == W.HELD and "foot_check" in g2["reason"]


def test_adverse_generated_winders_refused():
    d = drawing(5)
    d.winder_fronts.append(("G1", 1.2, "generated"))
    with pytest.raises(W.ReadingError):
        W.turn_quantities(6, d)


def test_adverse_units_and_missing():
    with pytest.raises(W.ReadingError):
        W.Reading("X", "section", 9, 6, going=300)              # mm as m
    with pytest.raises(W.ReadingError):
        W.governing([W.Reading("X", "section", 9, 6)], 150, 2550, "section")
    with pytest.raises(W.ReadingError):
        W.turn_quantities(6, W.TurnDrawing(fronts(5), 1000.0, ("A", "B"), REGION))
    with pytest.raises(W.ReadingError):
        W.governing(readings() + [W.Reading("SEC", "section", 9, 6)], FFL, LAND, "section")
    with pytest.raises(W.ReadingError):
        W.Reading("X", "section", 0, 6)


def test_adverse_landing_edge_on_one_drawing_held_never_zero():
    q = W.turn_quantities(6, drawing(4, drawings=("ARCH", "ARCH")))
    assert q["landing_edge"]["status"] == W.HELD and q["landing_edge"]["lm"] is None
    assert q["landing_edge"]["beside_lm"] == pytest.approx(1.0)


def test_rotation_mirror_invariance_of_region_and_fronts():
    base = W.shoelace(REGION)
    for deg in (0, 37.5, 90, 211):
        for mir in (False, True):
            assert W.shoelace(W.rotate(REGION, deg, mir)) == pytest.approx(base, abs=1e-12)
    ends = [(0.0, 0.0), (-1.0, 0.267949)]
    ln = math.dist(*ends)
    r = W.rotate(ends, 123.0, True)
    assert math.dist(*r) == pytest.approx(ln, abs=1e-12)


def test_reach_of_drawn_readings():
    assert W.reach({"a": (25, 28), "b": (24, 27), "c": (4, 4)}) == (53, 59)
