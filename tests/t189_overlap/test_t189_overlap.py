"""T-189: concrete at intersecting structural elements measured exactly once (R-CONC-OWN-1, proposed;
engine/source/concrete_overlap_ownership.py, unwired).

Synthetic 'Villa R' (not the development villa), metres unless stated. Hand calculations:
  flight: risers 0.175, going 0.28, 9 goings, 10 step triangles (the 10th = arrival wedge), width 1.10, waist 0.15
    one triangle 1/2 x 0.175 x 0.28 x 1.10 = 0.02695; steps 10 x 0.02695 = 0.2695
    waist 1.10 x 0.15 x hypot(2.52, 1.575) = 0.490331                              gross 0.759831
  stair head, last riser line 0.20 INSIDE a 0.40 x 0.60 beam billed at full depth (adverse):
    part of the last tread triangle over the last 0.20 of its 0.28 going: 1/2 r g (0.20 / 0.28)^2 x 1.10 = 0.013750
    waist strip: 0.20 x 0.15 / cos (cos = 0.28 / 0.330189) x 1.10 = 0.20 x 0.176886 x 1.10 = 0.038915
    flight solid inside the band 0.052665 m3: billed twice if only the arrival wedge (0.02695) is deducted
  beam 0.30 x 0.60 through a 4 x 4 x 0.20 slab: union 3.20 + 0.30 x 4 x 0.40 = 3.68; slab billed as a full plate
    with the beam at full depth -> 0.30 x 4 x 0.20 = 0.240 twice
  column 0.30 x 0.30 through a 0.25 x 0.60 beam: beam billed gross -> 0.25 x 0.30 x 0.60 = 0.045 twice
  neck 0.40 x 0.40 billed from the footing underside (0.50 thick) -> 0.080 twice and 0.080 outside the neck
  pool 4 x 6, walls 0.20, base 0.30, walls 1.50 above the base top: band 24 - 3.6 x 5.6 = 3.84 m2;
    union 7.20 + 5.76 = 12.96; walls billed from the base underside -> 3.84 x 0.30 = 1.152 twice
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

R, G, N_GO, W, T = 0.175, 0.28, 9, 1.10, 0.15
TRI = 0.5 * R * G * W
WAIST = W * T * math.hypot(N_GO * G, N_GO * R)
IN_BAND = 0.5 * R * G * (0.20 / G) ** 2 * W + 0.20 * T / (G / math.hypot(G, R)) * W


def _rot(p, th):
    c, s = math.cos(th), math.sin(th)
    return (c * p[0] - s * p[1], s * p[0] + c * p[1])


def _stair_head(theta_deg=0.0, inside=0.20, mirror=False, unit="m"):
    """a flight travelling +s from the origin; its last riser line at s = 9 x 0.28 = 2.52, arrival floor at 1.75;
    a 0.40 x 0.60 beam whose stair-side face is `inside` before the last riser line, then a 0.20 slab beyond the beam
    (tops at the arrival level); all rotated by theta, the flight optionally mirrored (width to the right)."""
    th = math.radians(theta_deg)
    d = _rot((1.0, 0.0), th)
    f = 1000.0 if unit == "mm" else 1.0
    fl = C.Flight("F1", (0.0, 0.0), d, W * f, 0.0, R * f, G * f, N_GO, N_GO + 1, T * f,
                  side=-1 if mirror else 1, unit=unit)
    face = 2.52 - inside
    top = (N_GO + 1) * R
    beam = C.beam(_rot((face + 0.20, -3.0), th), _rot((face + 0.20, 3.0), th), 0.40, top, 0.60)
    slab = C.plan_prism([_rot(p, th) for p in ((face + 0.40, -3.0), (face + 2.40, -3.0), (face + 2.40, 3.0),
                                                (face + 0.40, 3.0))], top - 0.20, top)
    phys = fl.pieces(include_arrival_wedge=True)
    rev_q62 = fl.pieces(include_arrival_wedge=False)
    return fl, phys, rev_q62, beam, slab, d, face


def _corrected(rev_q62, d, face):
    # keep the part before the beam face: (x . d) <= face (the flight starts at the origin)
    return C.clip(rev_q62, (d[0], d[1], 0.0), face)


# ---------------------------------------------------------------- kernel


def test_box_and_flight_volumes_equal_the_owner_formulas():
    assert C.total_volume(C.box(0, 2, 0, 3, 0, 0.5)) == pytest.approx(3.0, abs=1e-12)
    fl = C.Flight("F", (0, 0), (1, 0), W, 0.0, R, G, N_GO, N_GO + 1, T)
    led = fl.ledger_m3()
    assert led["steps"] == pytest.approx(10 * TRI, abs=1e-12) == pytest.approx(0.2695, abs=1e-12)
    assert led["waist"] == pytest.approx(0.490331, abs=1e-6)
    assert C.total_volume(fl.pieces()) == pytest.approx(led["steps"] + led["waist"], abs=1e-10)


@pytest.mark.parametrize("theta", [0.0, 30.0, 60.0, 135.0])
@pytest.mark.parametrize("mirror", [False, True])
def test_flight_volume_invariant_under_rotation_mirror_and_units(theta, mirror):
    th = math.radians(theta)
    for unit, f in (("m", 1.0), ("mm", 1000.0), ("cm", 100.0)):
        fl = C.Flight("F", (3.0 * f, -2.0 * f), _rot((1, 0), th), W * f, 1.0 * f, R * f, G * f, N_GO, N_GO + 1,
                      T * f, side=-1 if mirror else 1, unit=unit)
        assert C.total_volume(fl.pieces()) == pytest.approx(10 * TRI + WAIST, abs=1e-9)


def test_unknown_unit_and_non_convex_plan_are_refused():
    with pytest.raises(ValueError):
        C.box(0, 1, 0, 1, 0, 1, unit="ft")
    with pytest.raises(ValueError):
        C.plan_prism([(0, 0), (2, 0), (1, 0.5), (2, 2), (0, 2)], 0, 1)   # an L / dart: split it first


def test_difference_is_exact_and_disjoint():
    a = C.box(0, 2, 0, 2, 0, 2)
    cut = C.box(1, 3, 1, 3, 1, 3)[0]
    rest = C.difference(a, cut)
    assert C.total_volume(rest) == pytest.approx(7.0, abs=1e-12)
    assert C.union_volume([[p] for p in rest]) == pytest.approx(7.0, abs=1e-12)   # pieces do not overlap


# ---------------------------------------------------------------- stair head into a full-depth beam


def _scene(theta=0.0, inside=0.20, mirror=False, unit="m", billed="q62"):
    fl, phys, rev_q62, beam, slab, d, face = _stair_head(theta, inside, mirror, unit)
    corr = _corrected(rev_q62, d, face)
    billed_pieces = {"q62": rev_q62, "corrected": corr, "none": phys}[billed]
    return [C.Element("F1", "STAIR", phys, billed=billed_pieces), C.Element("B1", "BEAM", beam),
            C.Element("S1", "SLAB", slab)], fl


def test_normal_riser_line_at_the_beam_face_only_the_wedge_overlaps():
    els, fl = _scene(inside=0.0)
    rep = C.check_ownership(els)
    assert rep["status"] == "PASS"
    assert len(rep["pairs"]) == 1                                # the slab beyond the beam touches nothing
    pair = rep["pairs"][0]
    assert pair["owner"] == "B1" and pair["m3"] == pytest.approx(TRI, abs=1e-9)   # the arrival wedge, in the beam
    assert rep["owned"]["F1"] == pytest.approx(9 * TRI + WAIST, abs=1e-9)


@pytest.mark.parametrize("theta", [0.0, 30.0, 60.0])
@pytest.mark.parametrize("mirror", [False, True])
def test_adverse_riser_line_inside_the_beam_wedge_only_deduction_double_counts(theta, mirror):
    els, _ = _scene(theta=theta, mirror=mirror, billed="q62")
    rep = C.check_ownership(els)
    assert rep["status"] == "FAIL"
    assert rep["double_m3"] == pytest.approx(IN_BAND, abs=1e-9) == pytest.approx(0.052665, abs=1e-6)
    beam_pair = next(p for p in rep["pairs"] if p["pair"] == ("F1", "B1"))
    assert beam_pair["status"] == "DOUBLE" and beam_pair["owner"] == "B1"
    els2, _ = _scene(theta=theta, mirror=mirror, billed="corrected")
    rep2 = C.check_ownership(els2)
    assert rep2["status"] == "PASS" and rep2["double_m3"] < 1e-9 and rep2["gap_m3"] < 1e-9
    assert rep2["owned"]["F1"] == pytest.approx(10 * TRI + WAIST - TRI - IN_BAND, abs=1e-9)


def test_adverse_units_mm_give_the_same_double():
    rep = C.check_ownership(_scene(unit="mm", billed="q62")[0])
    assert rep["double_m3"] == pytest.approx(IN_BAND, abs=1e-9)


def test_adverse_no_deduction_at_all_counts_wedge_and_band_twice():
    rep = C.check_ownership(_scene(billed="none")[0])
    assert rep["double_m3"] == pytest.approx(TRI + IN_BAND, abs=1e-9)


def test_adverse_both_lines_net_leaves_a_gap_never_zero():
    fl, phys, rev_q62, beam, slab, d, face = _stair_head()
    corr = _corrected(rev_q62, d, face)
    beam_net = C._minus_all(beam, phys)                       # beam ALSO billed net of the flight
    rep = C.check_ownership([C.Element("F1", "STAIR", phys, billed=corr),
                             C.Element("B1", "BEAM", beam, billed=beam_net), C.Element("S1", "SLAB", slab)])
    assert rep["status"] == "FAIL"
    wedge_in_beam = TRI * (1 - (0.08 / G) ** 2)                # the first 0.20 of the wedge's 0.28 lies in the beam
    assert rep["gap_m3"] == pytest.approx(IN_BAND + wedge_in_beam, abs=1e-9)   # counted nowhere: reported


# ---------------------------------------------------------------- beam through a slab, column through a beam


def _slab_beam(full_plate):
    slab_phys = C.box(0, 4, 0, 4, 0.40, 0.60)
    beam = C.box(0, 4, 1.85, 2.15, 0.0, 0.60)
    slab_net = C.box(0, 4, 0, 1.85, 0.40, 0.60) + C.box(0, 4, 2.15, 4, 0.40, 0.60)
    return [C.Element("S1", "SLAB", slab_phys, billed=slab_phys if full_plate else slab_net),
            C.Element("B2", "BEAM", beam)]


def test_beam_through_slab_route_g_basis_counts_once():
    rep = C.check_ownership(_slab_beam(full_plate=False))
    assert rep["status"] == "PASS"
    assert rep["union_m3"] == pytest.approx(3.68, abs=1e-12)
    assert rep["pairs"][0]["owner"] == "B2"


def test_adverse_full_plate_and_full_depth_beam_double():
    rep = C.check_ownership(_slab_beam(full_plate=True))
    assert rep["double_m3"] == pytest.approx(0.24, abs=1e-12)


def test_slab_plate_downstand_basis_needs_its_own_profile():
    slab = C.box(0, 4, 0, 4, 0.40, 0.60)
    beam = C.box(0, 4, 1.85, 2.15, 0.0, 0.60)
    down = C.box(0, 4, 1.85, 2.15, 0.0, 0.40)
    els = [C.Element("S1", "SLAB", slab), C.Element("B2", "BEAM", beam, billed=down)]
    prec = dict(C.PRECEDENCE_ROUTE_G, SLAB=45)                   # URBAN-NON-OVERLAPPING-SLAB-BEAM-MODEL@v1
    rep = C.check_ownership(els, precedence=prec)
    assert rep["status"] == "PASS" and rep["pairs"][0]["owner"] == "S1"
    assert rep["owned"]["B2"] == pytest.approx(0.30 * 4 * 0.40, abs=1e-12)


def test_column_through_beam_route_g_net_plan_and_adverse_gross():
    col = C.box(1.0, 1.3, 0.0, 0.3, 0.0, 3.60)
    beam = C.box(0.0, 5.0, 0.025, 0.275, 3.0, 3.60)
    beam_net = C.box(0.0, 1.0, 0.025, 0.275, 3.0, 3.60) + C.box(1.3, 5.0, 0.025, 0.275, 3.0, 3.60)
    ok = C.check_ownership([C.Element("C1", "COLUMN", col), C.Element("B3", "BEAM", beam, billed=beam_net)])
    assert ok["status"] == "PASS" and ok["pairs"][0]["owner"] == "C1"
    bad = C.check_ownership([C.Element("C1", "COLUMN", col), C.Element("B3", "BEAM", beam)])
    assert bad["double_m3"] == pytest.approx(0.045, abs=1e-12)


# ---------------------------------------------------------------- neck into a footing, pool wall on its base


def test_neck_on_footing_top_and_adverse_neck_from_the_underside():
    footing = C.box(0, 2, 0, 2, -1.5, -1.0)
    neck = C.box(0.8, 1.2, 0.8, 1.2, -1.0, 0.0)
    ok = C.check_ownership([C.Element("F1", "FOOTING", footing), C.Element("N1", "NECK", neck)])
    assert ok["status"] == "PASS" and ok["pairs"] == []        # they touch, no volume shared
    neck_long = C.box(0.8, 1.2, 0.8, 1.2, -1.5, 0.0)
    bad = C.check_ownership([C.Element("F1", "FOOTING", footing), C.Element("N1", "NECK", neck, billed=neck_long)])
    assert bad["status"] == "FAIL"
    assert bad["double_m3"] == pytest.approx(0.08, abs=1e-12)
    assert any(i["kind"] == "OUTSIDE" and i["m3"] == pytest.approx(0.08, abs=1e-12) for i in bad["issues"])


def test_physical_overlap_without_an_established_owner_is_never_guessed():
    footing = C.box(0, 2, 0, 2, -1.5, -1.0)
    neck_drawn_through = C.box(0.8, 1.2, 0.8, 1.2, -1.5, 0.0)
    rep = C.check_ownership([C.Element("F1", "FOOTING", footing),
                             C.Element("N1", "NECK", neck_drawn_through, billed=C.box(0.8, 1.2, 0.8, 1.2, -1.0, 0.0))])
    assert rep["pairs"][0]["status"] == "OWNER_UNDEFINED" and rep["status"] == "FAIL"
    assert rep["owned"]["F1"] == pytest.approx(2.0, abs=1e-12)  # unowned: kept in both, never split silently


def _pool(walls_from_underside=False):
    base = C.box(0, 4, 0, 6, -0.30, 0.0)
    ring = C.box(0, 4, 0, 0.2, 0, 1.5) + C.box(0, 4, 5.8, 6, 0, 1.5) + C.box(0, 0.2, 0.2, 5.8, 0, 1.5) \
        + C.box(3.8, 4, 0.2, 5.8, 0, 1.5)
    z0 = -0.30 if walls_from_underside else 0.0
    billed = C.box(0, 4, 0, 0.2, z0, 1.5) + C.box(0, 4, 5.8, 6, z0, 1.5) + C.box(0, 0.2, 0.2, 5.8, z0, 1.5) \
        + C.box(3.8, 4, 0.2, 5.8, z0, 1.5)
    return [C.Element("PB", "POOL_BASE", base), C.Element("PW", "POOL_WALL", ring, billed=billed)]


def test_pool_walls_on_the_base_counted_once():
    rep = C.check_ownership(_pool())
    assert rep["status"] == "PASS" and rep["union_m3"] == pytest.approx(12.96, abs=1e-12)


def test_adverse_pool_walls_from_the_base_underside_double():
    rep = C.check_ownership(_pool(walls_from_underside=True))
    assert rep["status"] == "FAIL" and rep["double_m3"] == pytest.approx(1.152, abs=1e-12)


# ---------------------------------------------------------------- unknown levels, missing lines, same kind


def test_plan_overlap_with_unprinted_levels_is_held_with_a_bound_never_deducted():
    els = _pool() + [C.Element("FX", "FOOTING", C.plan_prism([(-1, -1), (1, -1), (1, 0.5), (-1, 0.5)], None, None),
                               levels_known=False)]
    rep = C.check_ownership(els)
    assert rep["status"] == "PASS_HELD"
    held = {tuple(h["pair"]): h for h in rep["held"]}
    # plan overlap with the base 1.0 x 0.5 = 0.5 m2 x 0.30 = 0.150; with the walls 0.2 x 0.5 + 0.8 x 0.2 = 0.26 m2 x 1.5
    assert held[("PB", "FX")]["exposure_m3"] == pytest.approx((0.0, 0.15), abs=1e-12)
    assert held[("PW", "FX")]["exposure_m3"] == pytest.approx((0.0, 0.39), abs=1e-12)
    assert rep["owned"]["PB"] == pytest.approx(7.2, abs=1e-12)   # nothing deducted for a held overlap
    assert rep["union_m3"] == pytest.approx(12.96, abs=1e-12)


def test_a_line_that_bills_nothing_is_a_gap_not_zero():
    rep = C.check_ownership([C.Element("S1", "SLAB", C.box(0, 4, 0, 4, 0.40, 0.60), billed=[]),
                             C.Element("B2", "BEAM", C.box(0, 4, 1.85, 2.15, 0.0, 0.60))])
    assert rep["status"] == "FAIL" and rep["gap_m3"] == pytest.approx(3.2 - 0.24, abs=1e-12)


def test_two_beams_crossing_need_a_junction_owner():
    b1 = C.box(0, 4, 1.8, 2.2, 0, 0.6)
    b2 = C.box(1.8, 2.2, 0, 4, 0, 0.6)
    rep = C.check_ownership([C.Element("BX", "BEAM", b1), C.Element("BY", "BEAM", b2)])
    assert rep["pairs"][0]["status"].startswith("DOUBLE") and "OWNER_UNDEFINED" in rep["pairs"][0]["status"]
    assert rep["double_m3"] == pytest.approx(0.4 * 0.4 * 0.6, abs=1e-12)


def test_ledger_figure_is_cross_checked_against_the_geometry():
    rep = C.check_ownership([C.Element("B2", "BEAM", C.box(0, 4, 1.85, 2.15, 0.0, 0.60), ledger_m3=0.80)])
    assert any(i["kind"] == "LEDGER_MISMATCH" for i in rep["issues"])


# ---------------------------------------------------------------- development villa (Alsenan) check


def _alsenan():
    p = ROOT / "research" / "agents_t189" / "t189_alsenan_check.py"
    spec = importlib.util.spec_from_file_location("t189_alsenan_check", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_alsenan_stair_heads_in_b20_b23_and_the_rev2_ledger():
    A = _alsenan()
    res = A.run()
    for fid, rev1, own, chk in (("MS1-U", 1.0548, 0.9976, 0.9976), ("MS2-U", 1.0588, 1.0014, 1.0014)):
        r = res[fid]
        assert r["rev1_ledger_m3"] == pytest.approx(rev1, abs=1e-4)          # T-184 rev1
        assert r["rev1_check"]["status"] == "FAIL" and r["rev1_check"]["double_m3"] > 0.057
        assert r["rev2_check"]["status"] == "PASS"
        assert r["rev2_m3"] == pytest.approx(chk, abs=1e-4)                   # Checker 17:18 own quantity
        assert r["sensitivity"]["margin_up_m"] > 0.16 and r["sensitivity"]["margin_down_m"] > 0.28
    assert res["MS1-U"]["in_band_m3"] + res["MS2-U"]["in_band_m3"] == pytest.approx(0.1147, abs=1e-4)
    led = A.ledger_rev2(res)
    assert led["st01_rev1_m3"] == pytest.approx(4.746, abs=1e-3)
    assert led["st01_change_m3"] == pytest.approx(-0.1147, abs=1e-4)
    assert led["staircase_system_rev2_m3"] == pytest.approx(6.6754, abs=1e-4)
    assert next(r for r in led["st01_rows"] if r["piece"] == "MS1-L")["status"] == "HELD"
    committed = json.loads((ROOT / "research" / "agents_t189" / "T189_STAIR_LEDGER_REV2.json").read_text())
    assert committed == json.loads(json.dumps(led))


def test_alsenan_pool_base_walls_once_and_unprinted_levels_held():
    res = _alsenan().run()["POOL"]
    assert res["status"] == "PASS_HELD" and res["double_m3"] == 0.0 and res["gap_m3"] == 0.0
    assert res["base_m3"] == pytest.approx(4.374, abs=0.005)       # T-183 4.374 (36 chords: -0.002)
    assert res["walls_m3"] == pytest.approx(2.828, abs=0.005)      # T-183 2.828
    assert {tuple(h[0]) for h in res["held"]} >= {("POOL BASE", "F8"), ("POOL WALLS", "B.W band")}
    assert res["adverse_walls_from_base_underside"]["double_m3"] == pytest.approx(2.3565 * 0.40, abs=0.005)
