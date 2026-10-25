"""T-299 PART F: footing mesh populations printed as a rate. Hand fixture villa K299F (NOT any real villa).

Hand values (cover 70 mm printed as a MINIMUM against soil, d^2/162 kg/m):
  KF1 300 x 250 cm, BOT '8 ø 12/m' both ways:
    SHORT spread 3000: L_eff = 3000 - 140 - 12 = 2848; 2848 / 125 = 22.784 -> 23 + 1 = 24 (max spacing, e = 0);
      e = 16: 2816 / 125 = 22.528 -> 24; density in zone 8 x 2.86 = 22.88 -> 23  => 23 .. 24 HELD
    LONG  spread 2500: L_eff = 2348 -> 18.784 -> 20; density 8 x 2.36 = 18.88 -> 19 => 19 .. 20 HELD
  KF2 164.5 cm spread, '10 ø 12/m': density ceil(10 x 1.505) = 16; max spacing ceil((1645 - 152 - 2e) / 100) + 1 = 16
    for e = 0 .. 16 => 16 INVARIANT at the minimum cover; first centre 70 + 0 + 6 = 76 mm, last 1645 - 76 = 1569.
  Printed-count trace: 2 footings 100 x 100 cm, 5 + 5 ø12, boxed printed:
    e = 0: 2 x 10 x 0.86 x 144/162 = 15.288889 kg; e = 10: 2 x 10 x 0.84 x 144/162 = 14.933333 kg.
"""
import importlib.util
import os
from fractions import Fraction

import pytest

_P = os.path.join(os.path.dirname(__file__), "..", "..", "research", "agents_t299", "t299_part_f.py")
_s = importlib.util.spec_from_file_location("t299_part_f_under_test", _P)
PF = importlib.util.module_from_spec(_s)
_s.loader.exec_module(PF)

MIN70 = PF.cover_rule("MINIMUM", 70, {"SIDE", "TOP", "BOTTOM"})


def _kf1():
    return {"mark": "KF1", "L": 300, "W": 250, "enclosure": "BOXED_LEG_UNPRINTED",
            "end_detail": {"BOT": "STRAIGHT_DRAWN", "TOP": "NOT_DRAWN"},
            "layers": {"BOT": ["8 ø 12/m", "8 ø 12/m"]}}


# ---------------------------------------------------------------- normal cases
def test_kf1_counts_by_reading_hand_values():
    rows = {r["component"]: r for r in PF.footing_populations(_kf1(), MIN70)}
    s, l = rows["SHORT"], rows["LONG"]
    assert s["readings"]["MAX_SPACING_e0"] == 24 and s["readings"]["MAX_SPACING_e16"] == 24
    assert s["readings"]["DENSITY_IN_ZONE"] == 23
    assert (s["count_low"], s["count_high"], s["count_status"]) == (23, 24, "HELD")
    assert (l["count_low"], l["count_high"]) == (19, 20)
    assert "designer RFI" in s["held_reason"] and "MINIMUM" in s["held_reason"]


def test_invariant_count_and_positions():
    r = PF.population("KF2", "BOT", "SHORT", 1645, 1200, "10 ø 12/m", MIN70, "STRAIGHT_DRAWN", "LEG_UNPRINTED")
    assert r["count_low"] == r["count_high"] == 16 and r["count_status"] == "INVARIANT_AT_MIN_COVER"
    pos = r["max_spacing_positions_e0"]
    assert len(pos) == 16 and pos[0] == 76.0 and pos[-1] == 1569.0
    assert r["length_status"] == "HELD" and r["weight_status"] == "HELD"  # F5: a count never makes a weight


def test_clear_cover_kept_apart_from_centre_offset():
    assert PF.first_centre_offset_mm(70, 12, 0) == Fraction(76)
    assert PF.first_centre_offset_mm(70, 16, 10) == Fraction(88)
    assert PF.first_centre_offset_mm(70, 12, None) is None


def test_cover_effect_by_face_and_kind():
    assert PF.cover_effect("RATE", "SIDE") == {"count": True, "straight_run": True, "bar_level": False}
    assert PF.cover_effect("COUNT", "SIDE") == {"count": False, "straight_run": True, "bar_level": False}
    assert PF.cover_effect("RATE", "BOTTOM") == {"count": False, "straight_run": False, "bar_level": True}


def test_units_and_rotation_give_the_same_population():
    a = PF.footing_populations(_kf1(), MIN70, unit="cm")
    f = _kf1()
    f.update(L=3000, W=2500)
    b = PF.footing_populations(f, MIN70, unit="mm")
    assert [(r["count_low"], r["count_high"]) for r in a] == [(r["count_low"], r["count_high"]) for r in b]
    g = _kf1()
    g.update(L=250, W=300)  # rotated: the SHORT population of one is the LONG population of the other
    c = {r["component"]: r for r in PF.footing_populations(g, MIN70)}
    assert (c["LONG"]["count_low"], c["LONG"]["count_high"]) == (23, 24)


def test_printed_count_trace_hand_values():
    rows = [{"mark": "K1", "occurrences": 2, "L": 1000, "W": 1000, "short": (5, 12), "long": (5, 12),
             "boxed_printed": True}]
    t = PF.printed_count_straight_trace(rows, 70, (0, 10))
    assert abs(float(t[0]) - 15.288889) < 1e-6 and abs(float(t[10]) - 14.933333) < 1e-6
    rows[0]["boxed_printed"] = False  # nothing drawn between the bar end and the face: no deduction
    t = PF.printed_count_straight_trace(rows, 70, (0, 10))
    assert t[0] == t[10]


def test_printed_count_never_recounted():
    r = PF.population("KF3", "BOT", "SHORT", 2000, 1500, "9 ø 12", MIN70, "STRAIGHT_DRAWN", None)
    assert r["count_status"] == "PRINTED" and r["count_low"] == r["count_high"] == 9


# ---------------------------------------------------------------- adverse cases
def test_fractional_count_refused():
    with pytest.raises(PF.RefusedError):
        PF._whole(Fraction(3474, 100))
    with pytest.raises(PF.RefusedError):
        PF._whole(34.74)


@pytest.mark.parametrize("name", ["N_TIMES_L_PLUS_1", "BEAM_FIRST_LINK_OFFSET_75"])
def test_beam_reading_and_n_l_plus_1_refused_for_footings(name):
    with pytest.raises(PF.RefusedError):
        PF.refuse_reading(name)


def test_no_automatic_enclosing_subtraction_and_no_length_from_a_minimum_cover():
    r = PF.population("KF1", "TOP", "SHORT", 3000, 2500, "5 ø 12/m", MIN70, "NOT_DRAWN", "LEG_UNPRINTED")
    assert r["developed_length_m"] is None and r["length_status"] == "HELD"
    assert "not drawn" in r["held_reason"]
    r = PF.population("KF1", "BOT", "SHORT", 3000, 2500, "8 ø 12/m", MIN70, "STRAIGHT_DRAWN", None)
    assert r["developed_length_m"] is None  # side - 2 x minimum cover is a longest run, not a length
    exact = PF.cover_rule("EXACT", 70, {"SIDE"})
    r = PF.population("KF1", "BOT", "SHORT", 3000, 2500, "8 ø 12/m", exact, "STRAIGHT_DRAWN", None)
    assert r["developed_length_m"] == 2.36 and r["length_status"] == "INVARIANT_AT_MIN_COVER"


def test_weight_claim_refused_while_count_or_length_held():
    r = PF.footing_populations(_kf1(), MIN70)[0]
    for claim in ("VERIFIED", "DRAWING-CONFIRMED"):
        with pytest.raises(PF.RefusedError):
            PF.check_status_claim(r, claim)


def test_held_never_zero_and_scenario_never_summed():
    rows = PF.footing_populations(_kf1(), MIN70)
    assert PF.measured_total_kg(rows) is None  # HELD, never 0
    env = PF.scenario_envelope_kg(rows)
    assert env["status"] == "AUDIT_SCENARIO" and env["low_kg"] < env["high_kg"]
    with pytest.raises(PF.RefusedError):
        PF.measured_total_kg([{"weight_status": "AUDIT_SCENARIO", "kg": 1.0}])
    with pytest.raises(PF.RefusedError):
        PF.measured_total_kg([{"weight_status": "INVARIANT_AT_MIN_COVER", "kg": None}])


def test_missing_cover_or_unreadable_cell_held():
    with pytest.raises(PF.RefusedError):
        PF.cover_rule("MINIMUM", None, {"SIDE"})
    with pytest.raises(PF.RefusedError):
        PF.cover_rule("ABOUT", 70, {"SIDE"})
    bottom_only = PF.cover_rule("MINIMUM", 70, {"BOTTOM"})  # a bottom-face note does not give the side cover
    r = PF.population("KF1", "BOT", "SHORT", 3000, 2500, "8 ø 12/m", bottom_only, "STRAIGHT_DRAWN", None)
    assert r["count_status"] == "HELD" and r["count_low"] is None
    r = PF.population("KF1", "BOT", "SHORT", 3000, 2500, "8 x 12 per m", MIN70, "STRAIGHT_DRAWN", None)
    assert r["count_status"] == "HELD" and r["diameter_mm"] is None


def test_larger_actual_cover_only_lowers_counts():
    p = PF.T171.parse("8 ø 12/m")
    base = PF.count_max_spacing(3000, 70, 12, p["spacing_mm"], 0)
    for extra in range(0, 120, 5):
        assert PF.count_max_spacing(3000, 70 + extra, 12, p["spacing_mm"], 0) <= base
        assert PF.count_density_in_zone(3000, 70 + extra, p["rate"]) <= PF.count_density_in_zone(3000, 70, p["rate"])


def test_f_t299_01_q71_hold_restated_by_designer_item():
    p = os.path.join(os.path.dirname(__file__), "..", "..", "research", "agents_t299", "t299_alsenan.py")
    s = importlib.util.spec_from_file_location("t299_alsenan_for_part_f", p)
    a = importlib.util.module_from_spec(s)
    s.loader.exec_module(a)
    out = a._restate_q71("HELD: count Q-71; hooks not printed")
    assert "open Q-71" in out and "S21" in out and "answered" in out and out.endswith("; hooks not printed")
    assert a._restate_q71("HELD: hooks not printed") == "HELD: hooks not printed"
