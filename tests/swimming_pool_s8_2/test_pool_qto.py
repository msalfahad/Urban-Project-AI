"""Generic pool QTO (engine/source/pool_qto.py): synthetic known answers only, no project data.

Only a stated or CAD-established dimension measures; an NTS drawn length never does and a missing one gives no
quantity (None), never 0. Rate bars are rate x width, unrounded, D^2 / 162. A finite group is never a rate. One drawn
bar is one physical bar: its legs in two regions are counted once, by the region holding the larger share."""

from __future__ import annotations

import math

import pytest

from engine.source import ground_slab_qto as GS
from engine.source import pool_qto as PQ


def rect(x0, y0, x1, y1):
    return [GS.line((x0, y0), (x1, y0)), GS.line((x1, y0), (x1, y1)), GS.line((x1, y1), (x0, y1)),
            GS.line((x0, y1), (x0, y0))]


def d_shape(half, depth):
    """Rectangle [0, depth] x [-half, half] closed by a semicircle of radius `half` west of x = 0."""
    return [GS.line((0, -half), (depth, -half)), GS.line((depth, -half), (depth, half)), GS.line((depth, half), (0, half)),
            GS.arc((0, 0), half, math.pi / 2, 3 * math.pi / 2)]


def seg(i, a, b):
    return ("LINE", i, a, b)


def run_of(*segs):
    return {"_segs": list(segs), "run_segments": [s[1] for s in segs]}


# ------------------------------------------------------------------ notation
@pytest.mark.parametrize("text,kind,dia,per_m,count", [
    ("7%%c14/m", PQ.RATE, 14, 7, 7), ("6Ø12/m", PQ.RATE, 12, 6, 6), ("7%%C12/m", PQ.RATE, 12, 7, 7),
    ("%%c12/20cm", PQ.SPACING, 12, 5, None), ("Ø10/20cm", PQ.SPACING, 10, 5, None),
    ("3%%c16", PQ.FINITE_GROUP, 16, None, 3), ("4Ø16", PQ.FINITE_GROUP, 16, None, 4)])
def test_notation_kinds(text, kind, dia, per_m, count):
    n = PQ.parse_notation(text)
    assert (n["kind"], n["dia_mm"], n["per_m"], n["count"]) == (kind, dia, per_m, count)


def test_unparsed_text_is_never_guessed():
    for t in ("AS PER ARCH", "12/20cm", "7 bars", ""):
        n = PQ.parse_notation(t)
        assert n["kind"] == PQ.UNPARSED and n["dia_mm"] is None and n["per_m"] is None


# ------------------------------------------------------------------ plan geometry
def test_d_shape_areas_and_band_are_exact():
    outer, inner = d_shape(1750, 1750), [GS.line((0, -1550), (1750 - 200, -1550))]
    inner = d_shape(1550, 1550)
    a_out = PQ.region_area_m2([outer])
    assert a_out == pytest.approx(3.5 * 1.75 + math.pi * 1.75 ** 2 / 2, abs=1e-12)
    band = PQ.band_area_m2([outer], [inner])
    assert band == pytest.approx(a_out - (3.1 * 1.55 + math.pi * 1.55 ** 2 / 2), abs=1e-12)
    assert PQ.ring_length_m(outer) == pytest.approx(2 * 1.75 + 3.5 + math.pi * 1.75, abs=1e-12)


def test_band_needs_the_water_inside_the_outline():
    with pytest.raises(PQ.PoolQtoError):
        PQ.band_area_m2([rect(0, 0, 1000, 1000)], [rect(0, 0, 2000, 2000)])


def test_tiling_reports_a_gap():
    assert PQ.tiling([1.0, 2.0], 3.0)["exact"]
    t = PQ.tiling([1.0, 1.9], 3.0)
    assert not t["exact"] and t["gap_m2"] == pytest.approx(0.1)


# ------------------------------------------------------------------ concrete
def test_prism_releases_only_established_dimensions():
    assert PQ.prism(10.0, PQ.CAD_GEOMETRY, 0.4, PQ.STATED) == {"lane": PQ.RELEASED, "m3": 4.0, "missing": []}
    nts = PQ.prism(10.0, PQ.CAD_GEOMETRY, 1.2, PQ.NTS_GRAPHIC)
    assert nts["lane"] == PQ.BLOCKED and nts["m3"] is None and nts["missing"] == ["height"]
    none = PQ.prism(None, PQ.NOT_ESTABLISHED, None, PQ.NOT_ESTABLISHED)
    assert none["m3"] is None and none["missing"] == ["height", "plan_area"]


def test_wall_base_intersection_is_counted_once_in_the_base():
    sp = PQ.wall_base_split(10.0, 2.0, 0.4, 1.5, footprint_authority=PQ.CAD_GEOMETRY, band_authority=PQ.CAD_GEOMETRY,
                            base_t_authority=PQ.STATED, wall_h_authority=PQ.STATED)
    assert sp["base"]["m3"] == pytest.approx(4.0) and sp["wall"]["m3"] == pytest.approx(3.0)
    assert sp["shell_m3"] == pytest.approx(7.0) and sp["intersection_owner"] == "BASE"
    blk = PQ.wall_base_split(10.0, 2.0, 0.4, None, footprint_authority=PQ.CAD_GEOMETRY,
                             band_authority=PQ.CAD_GEOMETRY, base_t_authority=PQ.STATED,
                             wall_h_authority=PQ.NOT_ESTABLISHED)
    assert blk["base"]["lane"] == PQ.RELEASED and blk["wall"]["m3"] is None and blk["shell_m3"] is None
    with pytest.raises(PQ.PoolQtoError):
        PQ.wall_base_split(1.0, 2.0, 0.4, 1.0, footprint_authority=PQ.CAD_GEOMETRY, band_authority=PQ.CAD_GEOMETRY,
                           base_t_authority=PQ.STATED, wall_h_authority=PQ.STATED)


def test_sloped_slab_uses_the_true_slope_length():
    assert PQ.sloped_slab_m3(4.0, 0.4, 3.0, 4.0) == pytest.approx(4.0 * 0.4 * 1.25)
    assert PQ.sloped_slab_m3(4.0, 0.4, 0.0, 4.0) == pytest.approx(1.6)


# ------------------------------------------------------------------ reinforcement
def test_rate_bars_are_unrounded_and_use_d2_over_162():
    q = PQ.rate_qty(PQ.parse_notation("7%%c14/m"), 3.33, PQ.STATED, 2.0, PQ.STATED)
    assert q["lane"] == PQ.RELEASED and q["equivalent_count"] == pytest.approx(23.31)
    assert q["length_m"] == pytest.approx(46.62) and q["kg"] == pytest.approx(46.62 * 14 ** 2 / 162)
    s = PQ.rate_qty(PQ.parse_notation("%%c12/20cm"), 2.0, PQ.STATED, 1.0, PQ.CAD_GEOMETRY)
    assert s["equivalent_count"] == pytest.approx(10.0)


def test_an_nts_run_or_width_blocks_the_bars():
    q = PQ.rate_qty(PQ.parse_notation("6Ø12/m"), 3.0, PQ.STATED, 4.2, PQ.NTS_GRAPHIC)
    assert q["lane"] == PQ.BLOCKED and q["kg"] is None and q["length_m"] is None and q["missing"] == ["bar_run"]
    q = PQ.rate_qty(PQ.parse_notation("6Ø12/m"), None, PQ.NOT_ESTABLISHED, None, PQ.NOT_ESTABLISHED)
    assert q["missing"] == ["bar_run", "distribution_width"] and q["equivalent_count"] is None


def test_a_finite_group_is_not_a_rate():
    n = PQ.parse_notation("3%%c16")
    with pytest.raises(PQ.PoolQtoError):
        PQ.rate_qty(n, 1.0, PQ.STATED, 1.0, PQ.STATED)
    q = PQ.finite_qty(n, 3.1, PQ.STATED)
    assert q["count"] == 3 and q["length_m"] == pytest.approx(9.3) and q["kg"] == pytest.approx(9.3 * 256 / 162)
    assert PQ.finite_qty(n, None, PQ.NOT_ESTABLISHED)["kg"] is None
    with pytest.raises(PQ.PoolQtoError):
        PQ.finite_qty(PQ.parse_notation("7%%c14/m"), 1.0, PQ.STATED)


def test_released_total_never_counts_a_blocked_row():
    rows = [{"lane": PQ.RELEASED, "kg": 2.0}, {"lane": PQ.BLOCKED, "kg": None}, {"lane": PQ.RELEASED, "kg": 1.5}]
    assert PQ.released_total(rows, "kg") == 3.5
    with pytest.raises(PQ.PoolQtoError):
        PQ.released_total([{"lane": PQ.BLOCKED, "kg": 0.0}], "kg")
    with pytest.raises(PQ.PoolQtoError):
        PQ.released_total([{"lane": PQ.RELEASED, "kg": None}], "kg")


def test_unknown_authority_is_an_error():
    with pytest.raises(PQ.PoolQtoError):
        PQ.established("SCALED_FROM_DRAWING")
    with pytest.raises(PQ.PoolQtoError):
        PQ.prism(1.0, "GUESS", 1.0, PQ.STATED)


# ------------------------------------------------------------------ drawn bar runs
def test_an_l_bar_chains_and_a_t_contact_does_not():
    l_bar = [seg("v", (0, 1000), (0, 0)), seg("h", (0, 0), (800, 0))]
    tee = seg("t", (400, 0), (400, 300))                   # touches the middle of h
    out = PQ.chain_runs(l_bar + [tee])
    runs = {tuple(r["run_segments"]) for r in out["runs"]}
    assert ("v", "h") in runs or ("h", "v") in runs
    assert ("t",) in runs
    lr = next(r for r in out["runs"] if len(r["run_segments"]) == 2)
    assert PQ.run_shape(lr, hook_max_units=150)["shape"] == PQ.L_SHAPE


def test_duplicate_segments_collapse():
    out = PQ.chain_runs([seg("a", (0, 0), (100, 0)), seg("b", (100, 0), (0, 0))])
    assert out["duplicates"] == [("b", "a")] and len(out["runs"]) == 1


def test_hairpin_is_u_and_crank_is_cranked_with_hooks():
    u = PQ.chain_runs([seg("o", (0, 0), (0, 2000)), seg("t", (0, 2000), (300, 2000)), seg("i", (300, 2000), (300, 0))])
    assert PQ.run_shape(u["runs"][0], hook_max_units=150)["shape"] == PQ.U_SHAPE
    c = PQ.chain_runs([seg("k0", (-90, 90), (0, 0)), seg("h", (0, 0), (2000, 0)), seg("s", (2000, 0), (3000, 600)),
                       seg("k1", (3000, 600), (3000, 720))])
    sh = PQ.run_shape(c["runs"][0], hook_max_units=150)
    assert sh["shape"] == PQ.CRANKED and sh["hooks"] == 2 and sh["core_legs"] == 2


# ------------------------------------------------------------------ label binding
def test_leader_tips_bind_what_they_touch():
    targets = [("s1", ("SEG", (0, 0), (1000, 0))), ("d1", ("DOT", (500, 500), 20.0))]
    b = PQ.bind_leaders([("L1", [(300, 10)]), ("L2", [(510, 530)]), ("L3", [(5000, 0)])], targets, tol=20)
    assert b["L1"] == {"targets": ["s1"], "state": "BOUND"}
    assert b["L2"]["targets"] == ["d1"] and b["L3"]["state"] == "UNBOUND"


def test_nearest_binding_needs_a_clear_margin_and_groups_pieces():
    targets = [("A", ("SEG", (0, 0), (100, 0))), ("A", ("SEG", (100, 0), (100, 100))), ("B", ("SEG", (0, 300), (100, 300)))]
    b = PQ.bind_nearest([("near", (50, 40)), ("tie", (0, 160)), ("far", (5000, 5000))], targets, max_d=350)
    assert b["near"]["state"] == "BOUND" and b["near"]["targets"] == ["A"]
    assert b["tie"]["state"] == "AMBIGUOUS" and sorted(b["tie"]["targets"]) == ["A", "B"]
    assert b["far"]["state"] == "UNBOUND"


def test_two_diameters_on_one_drawn_run_are_a_conflict():
    nots = {"a": PQ.parse_notation("7%%c14/m"), "b": PQ.parse_notation("7%%c12/m"), "c": PQ.parse_notation("7Ø14/m")}
    assert PQ.run_diameters(["a", "c"], nots)["state"] == "CONSISTENT"
    assert PQ.run_diameters(["a", "b"], nots) == {"diameters": [12.0, 14.0], "state": PQ.CONFLICT}
    assert PQ.run_diameters([], nots)["state"] == "UNLABELLED"


# ------------------------------------------------------------------ wall / base interfaces
WALL = [(0, 400), (200, 400), (200, 3000), (0, 3000)]
BASE = [(0, 0), (3000, 0), (3000, 400), (0, 400)]
REGIONS = {"WALL": [WALL], "BASE": [BASE]}


def test_one_bent_bar_is_one_bar_owned_by_the_larger_share():
    r = run_of(seg("v", (50, 2900), (50, 50)), seg("h", (50, 50), (2950, 50)))
    r["shape"] = PQ.L_SHAPE
    lens = PQ.leg_lengths_in(r, REGIONS)
    assert lens["WALL"] == pytest.approx(2500) and lens["BASE"] == pytest.approx(350 + 2900)
    rows = PQ.classify_interface({"R1": r}, REGIONS, "WALL", "BASE", eps_units=1, parallel_tol_units=40)
    assert len(rows) == 1 and rows[0]["class"] == PQ.SINGLE_BENT_BAR and rows[0]["component_owner_id"] == "BASE"
    assert PQ.owner_of({"WALL": 5.0, "BASE": 5.0}, priority=("WALL", "BASE")) == "WALL"
    assert PQ.owner_of({"WALL": 0.0}) is None


def test_lap_starter_anchored_and_base_only():
    wall_bar = run_of(seg("w", (150, 2900), (150, 300)))
    wall_bar["shape"] = PQ.STRAIGHT
    starter = run_of(seg("sv", (170, 1200), (170, 50)), seg("sh", (170, 50), (1200, 50)))
    starter["shape"] = PQ.L_SHAPE
    base_bar = run_of(seg("b", (100, 300), (2900, 300)))
    base_bar["shape"] = PQ.STRAIGHT
    rows = {x["run_id"]: x["class"] for x in PQ.classify_interface(
        {"W": wall_bar, "S": starter, "B": base_bar}, REGIONS, "WALL", "BASE", eps_units=1, parallel_tol_units=40)}
    assert rows["S"] == PQ.SEPARATE_STARTER and rows["W"] == PQ.LAP_BETWEEN_DISTINCT_BARS and rows["B"] == PQ.BASE_ONLY
    alone = run_of(seg("a", (150, 2900), (150, 100)))
    alone["shape"] = PQ.STRAIGHT
    assert PQ.classify_interface({"A": alone}, REGIONS, "WALL", "BASE", eps_units=1,
                                 parallel_tol_units=40)[0]["class"] == PQ.ANCHORED_STRAIGHT


def test_a_wall_bar_stopping_above_the_base_is_unresolved():
    r = run_of(seg("w", (150, 2900), (150, 800)))
    r["shape"] = PQ.STRAIGHT
    rows = PQ.classify_interface({"W": r}, REGIONS, "WALL", "BASE", eps_units=1, parallel_tol_units=40)
    assert rows[0]["class"] == PQ.UNRESOLVED and rows[0]["component_owner_id"] == "WALL"


# ------------------------------------------------------------------ arc conventions (found on the real drawing)
def test_an_arc_distance_is_to_the_drawn_sweep_not_the_circle():
    quarter = ("ARC", (0.0, 0.0), 100.0, 0.0, math.pi / 2)              # CCW from (100, 0) to (0, 100)
    assert PQ.target_distance((110, 0), quarter) == pytest.approx(10)    # off the arc, foot on the sweep
    assert PQ.target_distance((-100, 0), quarter) == pytest.approx(math.dist((-100, 0), (0, 100)))   # opposite side
    cw = ("ARC", (0.0, 0.0), 100.0, math.pi / 2, 0.0)                    # the same arc traversed clockwise
    assert PQ.target_distance((-100, 0), cw) == pytest.approx(PQ.target_distance((-100, 0), quarter))
    assert PQ.target_distance((70.0, 70.0), quarter) == pytest.approx(abs(math.hypot(70, 70) - 100))


def test_a_zero_or_oversized_sweep_is_rejected_and_an_unwrapped_arc_measures_its_sweep():
    unwrapped = ("ARC", "a", (0.0, 0.0), 10.0, 3 * math.pi / 2, 2 * math.pi)
    assert PQ._seg_len(unwrapped) == pytest.approx(10 * math.pi / 2)
    with pytest.raises(PQ.PoolQtoError):
        PQ.chain_runs([("ARC", "z", (0.0, 0.0), 10.0, 1.0, 1.0)])
    with pytest.raises(PQ.PoolQtoError):
        PQ.chain_runs([("ARC", "w", (0.0, 0.0), 10.0, 0.0, 7.0)])
    assert len(PQ.chain_runs([unwrapped])["runs"]) == 1
