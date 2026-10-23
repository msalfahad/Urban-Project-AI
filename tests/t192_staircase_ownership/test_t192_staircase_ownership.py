"""T-192: concrete ownership at stair feet, heads, landings and columns (R-CONC-OWN-1a, proposed; research script
research/agents_t192/t192_staircase_junctions.py on the unwired module engine/source/concrete_overlap_ownership.py).

Synthetic 'Villa S' (not the development villa), metres unless stated. Hand calculations:
  flight: riser r 0.15, going g 0.30, 9 goings, 10 step triangles (the 10th = arrival wedge), width w 1.00, waist t 0.15
    k = r / g = 0.5; cos = 0.30 / hypot(0.30, 0.15) = 0.894427; d = t / cos = 0.167705 (vertical waist depth)
  FOOT in a full-depth band (first riser line a = 0.10 inside the band face, band top = floor level):
    V = (d a - k a^2 / 2) w = 0.0167705 - 0.0025 = 0.0142705  (the steps stand above the floor: never deducted)
  FOOT on a ground slab 0.10 thick running under the flight: the waist below the floor inside the slab:
    soffit k s - d reaches -0.10 at s = 0.135410 and 0 at s = d / k = 0.335410:
    V = 0.10 x 0.135410 + 1/2 x 0.200000 x 0.10 = 0.023541
  TOP KNEE into a landing (top H = 10 r = 1.50, landing t_L 0.15 = r): s_top - L = d / k, height d:
    V = d^2 / (2 k) w = 0.028125
  BOTTOM KNEE leaving a landing t_L 0.15 < d: s_b = (d - t_L) / k = 0.035410, V = 1/2 s_b (d - t_L) w = 0.00031347
  COLUMN projecting 0.05 into the flight over s 1.00 .. 1.30, full storey:
    top of the steps: 0.60 over 1.00 .. 1.20, 0.75 over 1.20 .. 1.30 -> 0.195; soffit integral 0.1725 - 0.0503115
    -> thickness integral 0.0728115; V = 0.05 x 0.0728115 = 0.0036406
"""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import concrete_overlap_ownership as C  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "t192_staircase_junctions", ROOT / "research" / "agents_t192" / "t192_staircase_junctions.py")
J = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(J)

R, G, N_GO, W, T = 0.15, 0.30, 9, 1.00, 0.15
K = R / G
D = T / (G / math.hypot(G, R))
FOOT_BAND = (D * 0.10 - K * 0.10 ** 2 / 2) * W
FOOT_SLAB = (0.10 * ((D - 0.10) / K) + 0.5 * (D / K - (D - 0.10) / K) * 0.10) * W
KNEE_TOP = D * D / (2 * K) * W
KNEE_BOT = 0.5 * ((D - 0.15) / K) * (D - 0.15) * W
COL = 0.05 * ((0.60 * 0.20 + 0.75 * 0.10) - (K * (1.30 ** 2 - 1.00 ** 2) / 2 - D * 0.30))


def test_hand_values():
    assert D == pytest.approx(0.167705, abs=1e-6)
    assert FOOT_BAND == pytest.approx(0.0142705, abs=1e-6)
    assert FOOT_SLAB == pytest.approx(0.023541, abs=1e-6)
    assert KNEE_TOP == pytest.approx(0.028125, abs=1e-6)
    assert KNEE_BOT == pytest.approx(0.00031347, abs=1e-7)
    assert COL == pytest.approx(0.0036406, abs=1e-6)


def _flight(angle_deg=0.0, side=1, unit="m", origin=(0.0, 0.0)):
    f = {"m": 1.0, "cm": 100.0, "mm": 1000.0}[unit]
    a = math.radians(angle_deg)
    return C.Flight("F", (origin[0] * f, origin[1] * f), (math.cos(a), math.sin(a)), W * f, 0.0, R * f, G * f, N_GO,
                    10, T * f, side=side, unit=unit)


def _band_across(fl, s0, s1, z_top, depth, extra=0.5):
    """a full-depth band across the flight between local s0 .. s1 (metres), any rotation / mirror."""
    _, O, d, n = fl.frame()
    sm = 0.5 * (s0 + s1)
    p0 = O + sm * d - extra * n
    p1 = O + sm * d + (W + extra) * n
    return C.beam((p0[0], p0[1]), (p1[0], p1[1]), s1 - s0, z_top, depth, unit="m")


# ------------------------------------------------------------------ foot of a flight in a full-depth band

@pytest.mark.parametrize("angle,side", [(0, 1), (30, 1), (60, -1), (135, -1)])
def test_foot_inside_band_adverse_double_and_corrected(angle, side):
    fl = _flight(angle, side)
    band = _band_across(fl, -0.20, 0.10, 0.0, 0.50)           # stair-side face 0.10 beyond the first riser line
    assert J.foot_in_member(fl, band) == pytest.approx(FOOT_BAND, abs=1e-7)
    stair = fl.pieces(include_arrival_wedge=False)
    adverse = C.check_ownership([C.Element("F", "STAIR", stair), C.Element("BAND", "BEAM", band)])
    assert adverse["status"] == "FAIL" and adverse["double_m3"] == pytest.approx(FOOT_BAND, abs=1e-7)
    net = C._minus_all(stair, band)
    ok = C.check_ownership([C.Element("F", "STAIR", stair, billed=net), C.Element("BAND", "BEAM", band)])
    assert ok["status"] == "PASS"
    assert C.total_volume(stair) - C.total_volume(net) == pytest.approx(FOOT_BAND, abs=1e-7)


def test_foot_at_band_face_normal_nothing_to_deduct():
    fl = _flight()
    band = _band_across(fl, -0.30, 0.0, 0.0, 0.50)             # first riser line ON the band face
    assert J.foot_in_member(fl, band) == pytest.approx(0.0, abs=1e-9)
    chk = C.check_ownership([C.Element("F", "STAIR", fl.pieces(include_arrival_wedge=False)),
                             C.Element("BAND", "BEAM", band)])
    assert chk["status"] == "PASS"


def test_foot_band_in_millimetres_same_volume():
    fl = _flight(unit="mm")
    band = _band_across(fl, -0.20, 0.10, 0.0, 0.50)
    assert J.foot_in_member(fl, band) == pytest.approx(FOOT_BAND, abs=1e-7)


def test_unknown_unit_refused():
    with pytest.raises(ValueError):
        C.Flight("F", (0, 0), (1, 0), W, 0.0, R, G, N_GO, 10, T, unit="ft").pieces()


# ------------------------------------------------------------------ foot on a ground slab

def test_foot_on_ground_slab_running_under_the_flight_slab_owns():
    fl = _flight()
    slab = C.box(-2.0, 0.40, -0.5, 1.5, -0.10, 0.0)            # slab on grade continuing 0.40 under the flight
    stair = fl.pieces(include_arrival_wedge=False)
    v = C.intersection_volume(stair, slab)
    assert v == pytest.approx(FOOT_SLAB, abs=1e-7)
    adverse = C.check_ownership([C.Element("F", "STAIR", stair), C.Element("GS", "SLAB", slab)])
    assert adverse["status"] == "FAIL" and adverse["double_m3"] == pytest.approx(FOOT_SLAB, abs=1e-7)
    pair = adverse["pairs"][0]
    assert pair["owner"] == "GS"                               # Q-62 A cond: slab owns
    ok = C.check_ownership([C.Element("F", "STAIR", stair, billed=C._minus_all(stair, slab)),
                            C.Element("GS", "SLAB", slab)])
    assert ok["status"] == "PASS"
    own = C.owned_volumes([C.Element("F", "STAIR", stair), C.Element("GS", "SLAB", slab)])
    assert sum(own.values()) == pytest.approx(ok["union_m3"], abs=1e-9)


def test_foot_on_slab_stopping_at_first_riser_line_normal():
    fl = _flight()
    slab = C.box(-2.0, 0.0, -0.5, 1.5, -0.10, 0.0)
    chk = C.check_ownership([C.Element("F", "STAIR", fl.pieces(include_arrival_wedge=False)),
                             C.Element("GS", "SLAB", slab)])
    assert chk["status"] == "PASS" and not chk["pairs"]


def test_foot_on_unbilled_floor_is_undetermined_never_deducted():
    fl = _flight()
    floor = C.plan_prism([(-2.0, -0.5), (0.4, -0.5), (0.4, 1.5), (-2.0, 1.5)], None, None)
    chk = C.check_ownership([C.Element("F", "STAIR", fl.pieces(include_arrival_wedge=False)),
                             C.Element("SHAFT FLOOR", "SLAB", floor, levels_known=False)])
    assert chk["status"] == "PASS_HELD"
    lo, hi = chk["held"][0]["exposure_m3"]
    assert lo == 0.0 and hi > FOOT_SLAB                         # bounded, not a deduction
    assert chk["billed_sum_m3"] == pytest.approx(C.total_volume(fl.pieces(include_arrival_wedge=False)))


# ------------------------------------------------------------------ landings

def test_landing_poured_with_slab_not_counted_in_stair_adverse():
    slab = C.box(2.70, 5.00, 0.0, 1.0, 1.35, 1.50)
    landing_in_stair = C.box(2.70, 3.90, 0.0, 1.0, 1.35, 1.50)  # the same concrete, billed again as a landing
    chk = C.check_ownership([C.Element("SLAB", "SLAB", slab), C.Element("LD", "LANDING", landing_in_stair)])
    assert chk["status"] == "FAIL" and chk["double_m3"] == pytest.approx(1.2 * 1.0 * 0.15, abs=1e-9)
    assert "OWNER_UNDEFINED" in chk["pairs"][0]["status"]     # never split silently


def test_landing_at_slab_edge_touch_only_normal():
    slab = C.box(3.90, 6.00, 0.0, 1.0, 1.35, 1.50)
    landing = C.box(2.70, 3.90, 0.0, 1.0, 1.35, 1.50)
    chk = C.check_ownership([C.Element("SLAB", "SLAB", slab), C.Element("LD", "LANDING", landing)])
    assert chk["status"] == "PASS" and not chk["pairs"]


# ------------------------------------------------------------------ knees (owner method vs drawing-derived)

@pytest.mark.parametrize("angle,side", [(0, 1), (90, -1), (200, 1)])
def test_top_knee_hand_value_any_rotation(angle, side):
    fl = _flight(angle, side)
    p, hand, s_top = J.knee_top(fl, 1.50, 0.15)
    assert hand == pytest.approx(KNEE_TOP, abs=1e-9)
    assert C.volume(p) == pytest.approx(KNEE_TOP, abs=1e-7)
    assert s_top == pytest.approx(2.70 + D / K, abs=1e-9)


def test_top_knee_is_gap_in_owner_method_and_closed_in_drawing_derived():
    fl = _flight()
    _, O, d, n = fl.frame()
    landing = C.box(2.70, 3.90, 0.0, 1.0, 1.35, 1.50)          # top landing beyond the last riser line (s 2.70)
    knee, _, _ = J.knee_top(fl, 1.50, 0.15)
    wedge = [p for p in fl.pieces(include_arrival_wedge=True) if "arrival wedge" in p.label]
    knee_net = C._minus_all([knee], wedge)
    phys = fl.pieces(include_arrival_wedge=True) + knee_net
    owner = fl.pieces(include_arrival_wedge=False)
    gap = C.check_ownership([C.Element("F", "STAIR", phys, billed=owner), C.Element("LD", "LANDING", landing)])
    assert gap["status"] == "FAIL" and gap["double_m3"] == pytest.approx(0.0, abs=1e-9)
    assert gap["gap_m3"] == pytest.approx(KNEE_TOP, abs=1e-6)  # r = t_L: the wedge lies wholly inside the landing
    dd = C.check_ownership([C.Element("F", "STAIR", phys, billed=owner + knee_net),
                            C.Element("LD", "LANDING", landing)])
    assert dd["status"] == "PASS"


def test_bottom_knee_not_built_owner_method_outside():
    fl = _flight()
    p, hand = J.knee_bottom(fl, 0.15)
    assert hand == pytest.approx(KNEE_BOT, abs=1e-10)
    assert C.volume(p) == pytest.approx(KNEE_BOT, abs=1e-8)
    owner = fl.pieces(include_arrival_wedge=False)
    phys = C._minus_all(owner, [p])
    chk = C.check_ownership([C.Element("F", "STAIR", phys, billed=owner)])
    assert any(i["kind"] == "OUTSIDE" and i["m3"] == pytest.approx(KNEE_BOT, abs=1e-8) for i in chk["issues"])


def test_no_bottom_knee_when_landing_thicker_than_waist_depth():
    fl = _flight()
    p, hand = J.knee_bottom(fl, 0.20)
    assert p is None and hand == 0.0


# ------------------------------------------------------------------ column through a flight

def test_column_through_flight_owner_column_when_billed():
    fl = _flight()
    col = C.box(1.00, 1.30, -0.25, 0.05, -1.0, 3.0)           # 0.05 projection into the flight width
    stair = fl.pieces(include_arrival_wedge=False)
    assert C.intersection_volume(stair, col) == pytest.approx(COL, abs=1e-7)
    adverse = C.check_ownership([C.Element("F", "STAIR", stair), C.Element("COL", "COLUMN", col)],
                                established=J.ESTABLISHED)
    assert adverse["status"] == "FAIL" and adverse["pairs"][0]["owner"] == "COL"
    ok = C.check_ownership([C.Element("F", "STAIR", stair, billed=C._minus_all(stair, col)),
                            C.Element("COL", "COLUMN", col)], established=J.ESTABLISHED)
    assert ok["status"] == "PASS"


def test_column_stair_pair_not_in_the_module_profile_stays_undefined():
    fl = _flight()
    col = C.box(1.00, 1.30, -0.25, 0.05, -1.0, 3.0)
    chk = C.check_ownership([C.Element("F", "STAIR", fl.pieces(include_arrival_wedge=False)),
                             C.Element("COL", "COLUMN", col)])
    assert "OWNER_UNDEFINED" in chk["pairs"][0]["status"]     # the module's own table is not edited by T-192


# ------------------------------------------------------------------ development villa (Alsenan) regression

@pytest.fixture(scope="module")
def alsenan():
    return J.run()


def test_alsenan_ms2l_foot_inside_b20(alsenan):
    s = alsenan["st01"]
    assert s["MS2L_foot_band_strip_m"] == pytest.approx(0.15, abs=1e-9)
    assert s["MS2L_foot_in_B20_m3"] == pytest.approx(s["MS2L_foot_hand_m3"], abs=1e-9)
    assert s["MS2L_foot_in_B20_m3"] == pytest.approx(0.025448, abs=1e-6)
    assert list(s["MS2L_foot_parts"]) == ["MS2-L waist"]       # steps above the floor: never deducted
    assert s["MS2L_rev2_geometry_m3"] == pytest.approx(1.058893, abs=1e-6)   # geometry = the verified ledger rev2


def test_alsenan_checks_owner_method_and_drawing_derived(alsenan):
    s = alsenan["st01"]
    assert s["check_rev2"]["status"] == "FAIL" and s["check_rev2"]["double_m3"] == pytest.approx(0.025448, abs=1e-6)
    assert s["check_rev3"]["double_m3"] == pytest.approx(0.0, abs=1e-8)
    knee_gap = s["knee_top_MS2L"]["m3"] - s["MS2L_wedge_sliver_m3"]
    assert s["check_rev3"]["gap_m3"] == pytest.approx(
        knee_gap - s["knee_bottom_MS1U"]["m3"] - s["knee_bottom_MS2U"]["m3"], abs=C.TOL_M3)  # sliver billed (T-184)
    assert s["check_drawing_derived"]["status"] == "PASS"
    assert s["sum_owned_m3"] == pytest.approx(s["union_m3"], abs=1e-7)


def test_alsenan_knees_hand(alsenan):
    s, r2 = alsenan["st01"], alsenan["st02"]
    assert s["knee_top_MS2L"]["m3"] == pytest.approx(s["knee_top_MS2L"]["hand_m3"], abs=1e-8)
    assert s["knee_top_MS2L"]["m3"] == pytest.approx(0.039242, abs=1e-6)
    assert r2["knee_top_RSS"]["m3"] == pytest.approx(0.037169, abs=1e-6)
    assert r2["knee_top_RSA"]["m3"] == pytest.approx(0.038754, abs=1e-6)


def test_alsenan_e1_wedge_into_released_ground_slab(alsenan):
    e = alsenan["st03"]
    hand = 0.5 * 0.05 * (0.85 - (0.17 / 0.30) * 1.45) * 2.80   # last 0.05 of the wedge run, x 94.718 .. 94.768
    assert e["wedge_in_ground_slab_m3"] == pytest.approx(hand, abs=1e-8)
    assert e["check_before"]["status"] == "FAIL" and e["check_after"]["status"] == "PASS_HELD"
    assert e["sum_owned_m3"] == pytest.approx(e["union_m3"], abs=1e-8)


def test_alsenan_released_stair_head_inside_b20(alsenan):
    r = alsenan["released_GF_stair"]
    assert r["base"]["flight_m3"] == pytest.approx(1.071, abs=5e-4)   # the line's own run base (1.071)
    assert r["base"]["in_band_m3"] == pytest.approx(0.058586, abs=1e-6)
    lo, hi = r["range_correction_m3"]
    assert lo < r["base"]["in_band_m3"] < hi


def test_alsenan_ledger_rev3_regenerates_byte_identical(tmp_path, alsenan):
    out = tmp_path / "rev3.json"
    out.write_text(json.dumps(J.ledger_rev3(alsenan), indent=1) + "\n", encoding="utf-8")
    committed = ROOT / "research" / "agents_t192" / "T192_STAIR_LEDGER_REV3.json"
    assert out.read_bytes() == committed.read_bytes()
    led = json.loads(committed.read_text(encoding="utf-8"))
    assert led["st01_rev3_m3"] == pytest.approx(4.6058, abs=1e-4)
    assert led["staircase_system_rev3_m3"] == pytest.approx(6.6479, abs=1e-4)
    held = {r["piece"]: r for r in led["st01_rows"]}["MS1-L"]
    assert held["status"] == "HELD" and held["held_range_m3"] == [0.863, 1.055]   # held never 0, never moved


def test_alsenan_rev2_file_unchanged():
    rev2 = json.loads((ROOT / "research" / "agents_t189" / "T189_STAIR_LEDGER_REV2.json").read_text(encoding="utf-8"))
    assert rev2["staircase_system_rev2_m3"] == 6.6754
