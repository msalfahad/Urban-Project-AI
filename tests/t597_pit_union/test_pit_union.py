"""T-597: PIT_UNION_V1 (R-T597-1 .. 4) on a hand-calculated NON-Alsenan villa E597 (own figures, metres).

Printed blinding projection p = 0.10 each side. Plot 0 .. 6.50 x 0 .. 10.
  A  centre (2.0, 2.0), 1.00 x 1.00 -> neat 1.40 .. 2.60 x 1.40 .. 2.60 = 1.20 x 1.20 = 1.44 m2
  B  centre (3.0, 2.0), 1.00 x 0.80 -> neat 2.40 .. 3.60 x 1.50 .. 2.50 = 1.20 x 1.00 = 1.20 m2
  C  centre (6.0, 2.0), 2.00 x 1.00 -> neat 4.90 .. 7.10 x 1.40 .. 2.60 = 2.20 x 1.20 = 2.64 m2
  A n B = 0.20 x 1.00 = 0.20 m2 (A and B are one dig); sum 5.28, union 5.08, overlap 0.20.
  C beyond the plot line x > 6.50: 0.60 x 1.20 = 0.72 -> in plot 4.36.
  Earlier zone E (dug first) 1.00 .. 2.00 x 2.30 .. 5.00 takes A's 1.40 .. 2.00 x 2.30 .. 2.60 = 0.60 x 0.30 = 0.18
  -> the zone owns 4.36 - 0.18 = 4.18 m2.
  B turned 90 deg about its own centre: neat 2.50 .. 3.50 x 1.40 .. 2.60, A n B = 0.10 x 1.20 = 0.12 -> union 5.16.
"""
from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

import pytest
from shapely import affinity
from shapely.geometry import Point, box

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t597"))

import pit_union_v1 as U  # noqa: E402

P = 0.10
PLOT = box(0, 0, 6.5, 10)
E = box(1.0, 2.3, 2.0, 5.0)


def pits(unit="m", k=1.0, rotB=0.0):
    return [U.Pit("A", 2.0 * k, 2.0 * k, 1.0 * k, 1.0 * k, 0.0, P * k, unit),
            U.Pit("B", 3.0 * k, 2.0 * k, 1.0 * k, 0.8 * k, rotB, P * k, unit),
            U.Pit("C", 6.0 * k, 2.0 * k, 2.0 * k, 1.0 * k, 0.0, P * k, unit)]


def test_normal_union_overlap_clip_ownership():
    r = U.zone_plan("Z", pits(), plot=PLOT, earlier=[("E", E)])
    assert r.per_pit_m2 == {"A": 1.44, "B": 1.2, "C": 2.64}
    assert (r.sum_m2, r.union_m2, r.overlap_m2) == (5.28, 5.08, 0.2)
    assert r.overlap_pairs == [("A", "B", 0.2)]
    assert (r.in_plot_m2, r.beyond_plot_m2) == (4.36, 0.72)
    assert r.given_up_m2 == {"E": 0.18}
    assert r.own_in_plot_m2 == 4.18
    assert r.own_in_plot_m2 + sum(r.given_up_m2.values()) == pytest.approx(r.in_plot_m2, abs=1e-9)


def test_adverse_sum_is_refused_as_zone_plan():
    r = U.zone_plan("Z", pits())
    with pytest.raises(U.PitUnionError):
        U.refuse_sum_as_zone(r.sum_m2, r.union_m2)
    U.refuse_sum_as_zone(r.union_m2, r.union_m2)          # the union itself passes


def test_adverse_pit_rotated_about_its_centre():
    r = U.zone_plan("Z", pits(rotB=90.0))
    assert r.overlap_pairs == [("A", "B", 0.12)]
    assert r.union_m2 == 5.16
    r30 = U.zone_plan("Z", pits(rotB=30.0))
    assert r30.per_pit_m2["B"] == 1.2                    # rotation never changes a pit's own plan


def _moved(f, rot_add):
    ps = []
    for p in pits():
        c = f(Point(p.cx, p.cy))
        ps.append(U.Pit(p.pid, c.x, c.y, p.L, p.W, p.rot_deg + rot_add, p.projection, "m"))
    return U.zone_plan("Z", ps, plot=f(PLOT), earlier=[("E", f(E))])


@pytest.mark.parametrize("f,rot_add", [
    (lambda g: affinity.rotate(g, 37.0, origin=(0, 0)), 37.0),     # whole villa rotated: pits turn with it
    (lambda g: affinity.scale(g, -1, 1, origin=(0, 0)), 0.0),       # mirrored about x = 0
])
def test_adverse_whole_villa_rotated_and_mirrored(f, rot_add):
    base = U.zone_plan("Z", pits(), plot=PLOT, earlier=[("E", E)])
    r = _moved(f, rot_add)
    assert (r.union_m2, r.overlap_m2, r.in_plot_m2, r.own_in_plot_m2) == pytest.approx(
        (base.union_m2, base.overlap_m2, base.in_plot_m2, base.own_in_plot_m2), abs=2e-6)


def test_adverse_mm_units_give_the_same_m2_and_undeclared_unit_refused():
    r = U.zone_plan("Z", pits("mm", 1000.0))
    assert (r.union_m2, r.overlap_m2) == (5.08, 0.2)
    bad = pits()
    bad[0].unit = "cm"
    with pytest.raises(U.PitUnionError):
        U.zone_plan("Z", bad)


def test_adverse_missing_outline_is_held_never_zero():
    ps = pits() + [U.Pit("D", None, None, None, None, 0.0, P, "m")]
    r = U.zone_plan("Z", ps, plot=PLOT)
    assert r.pits_held == [("D", "outline not drawn")]
    assert "D" not in r.per_pit_m2
    assert r.union_m2 == 5.08                             # the others are unchanged, D is never a 0 inside them
    only = U.zone_plan("Z", [U.Pit("D", None, None, None, None, 0.0, P, "m")], plot=PLOT)
    assert only.union_m2 is None and only.in_plot_m2 is None and only.own_in_plot_m2 is None


def test_adverse_unprinted_projection_is_held_not_zero_projection():
    ps = pits()
    ps[2].projection = None
    r = U.zone_plan("Z", ps)
    assert r.pits_held == [("C", "projection not printed")]
    assert r.union_m2 == 2.44                             # A u B only; C never enters at its bare footprint


def test_adverse_pit_listed_twice_and_non_physical_size():
    with pytest.raises(U.PitUnionError):
        U.zone_plan("Z", pits() + [pits()[0]])
    with pytest.raises(U.PitUnionError):
        U.zone_plan("Z", [U.Pit("X", 0, 0, -1.0, 1.0, 0.0, P, "m")])


def test_adverse_repeated_earlier_zone_takes_nothing_twice():
    r = U.zone_plan("Z", pits(), plot=PLOT, earlier=[("E", E), ("E again", E)])
    assert r.given_up_m2 == {"E": 0.18, "E again": 0.0}
    assert r.own_in_plot_m2 == 4.18


def test_convex_offset_area_matches_a_fine_buffer():
    sq = box(0, 0, 1, 1)
    exact = U.convex_offset_area(1.0, 4.0, 0.1)
    assert exact == pytest.approx(1.0 + 0.4 + math.pi * 0.01, abs=1e-12)
    assert sq.buffer(0.1, quad_segs=4096).area == pytest.approx(exact, abs=1e-7)
    assert sq.buffer(0.1, quad_segs=4).area < exact - 1e-4    # a coarse buffer is short: never used as the value


# ---------------------------------------------------------------- development villa (committed output, no private data)
OUT = ROOT / "research" / "agents_t597" / "out" / "T597_PLAN_SIDE.json"


@pytest.fixture(scope="module")
def dev():
    return json.loads(OUT.read_text())


def test_dev_villa_24_pits_union_and_schedule(dev):
    assert dev["size_vs_schedule"] == {"agree": 24, "of": 24}
    z = dev["pits_zone"]
    assert (z["sum_m2"], z["union_m2"], z["overlap_m2"]) == (129.57, 129.234375, 0.335625)
    assert sorted(tuple(x) for x in z["overlap_pairs"]) == [("10F0", "1B24", 0.005625), ("180C", "180F", 0.33)]
    assert (z["in_plot_m2"], z["beyond_plot_m2"]) == (127.344375, 1.89)
    assert z["own_in_plot_m2"] == 124.648614
    assert len([p for p in dev["pits"] if not p["checked_before"]]) == 16


def test_dev_villa_pool_envelope_exact_and_converged(dev):
    pool = dev["pool"]
    exact = 10.935563 + (12.497787 - 3.5) * 0.10 + math.pi / 2 * 0.01
    assert pool["envelope_in_plot_m2_exact"] == pytest.approx(exact, abs=2e-6)
    c = dev["envelope_convergence"]
    assert c["4096"]["pits_given_up_m2"] == 2.695761
    assert c["16"]["pits_given_up_m2"] < c["4096"]["pits_given_up_m2"]


def test_dev_villa_rows_restated_with_cause(dev):
    rows = {r["id"]: r for r in dev["b1_rows"]}
    p = rows["B1-02 valued excavation: Z1-PITS-24"]
    assert p["plan_delta_m2"] == -0.000941 and p["m3_delta_at_S01"] == -0.001572
    assert "S01" in p["depth"] and "HELD" in p["depth"]
    t = rows["EW-T350:B1-02:Z1-TRENCH-EXT-GB-MAIN"]
    assert t["m3_at_blinding_0.10"] == pytest.approx(t["engine_m3"], abs=5e-6)
    for k in ("EW-T350:B1-02:Z1-PIT-FF", "EW-T350:B1-02:Z1-PIT-F10F"):
        assert rows[k]["plan_m2"] is None and "HELD" in rows[k]["plan_status"]


def test_dev_villa_trench_insensitive_to_junction_extent(dev):
    a, b = dev["ext_gb_trench"], dev["ext_gb_trench_either_face_extent"]
    assert (a["own_in_plot_m2"], a["own_beyond_plot_m2"]) == (b["own_in_plot_m2"], b["own_beyond_plot_m2"])


PRIV = ROOT.parent / "private" / "st7757.dxf"   # .work/private (git-excluded)


@pytest.mark.skipif(not PRIV.exists(), reason="private drawing not present (decoded only into .work/private)")
def test_private_reread_reproduces_committed_output(dev):
    sys.path.insert(0, str(ROOT / "research" / "agents_t597"))
    import t597_alsenan as A
    out = A.run(str(PRIV))
    assert out["pits_zone"]["own_in_plot_m2"] == dev["pits_zone"]["own_in_plot_m2"]
    assert out["pool"] == dev["pool"]
