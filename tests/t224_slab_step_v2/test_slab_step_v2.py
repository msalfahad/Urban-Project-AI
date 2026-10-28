"""T-224 hand fixture (NOT the development villa): SLAB_STEP_V2, the step of a sunken panel from its drawn outline and
framing members. Hand truth (metres, by hand before running the code):

Panel P1: x 0 .. 3.0, y 0 .. 4.0 -> A = 12.00 m2, P = 2 x (3.0 + 4.0) = 14.00 m; t = 0.16 printed (fixture note).
Beams 0.20 wide outside its four sides (S, N run x -0.20 .. 3.20; W, E run y 0 .. 4.0); storey slab x -3 .. 6, y -3 .. 7.

 F1 fully framed: P_ext = 14.00 m, L_free = 0, P_shared = 0.
    step concrete = 0 m3 for any d (step = beam side); riser form = +14.0 d m2; beam-side form = -14.0 d m2 (HELD, D-41)
    with d = 0.10 printed (fixture only): +1.400 / -1.400 m2, net 0.
 F2 east beam removed (one free slab edge, 4.00 m): P_ext = 3.0 + 3.0 + 4.0 = 10.00 m, L_free = 4.00 m
    step concrete = 4.00 x d x 0.16 (HELD); with d = 0.10: 4.00 x 0.10 x 0.16 = 0.0640 m3, on that edge only;
    riser free edge = soffit step = 4.00 x 0.10 = 0.400 m2; member riser = 10.0 x 0.10 = 1.000 m2, side -1.000 m2.
 F3 second panel P2 x 3.20 .. 6.20 across the east beam (shared): P1 P_shared = 4.00, P_ext = 10.00; shared riser HELD
    on d AND on the shared beam top level even when d is printed.
 F4 slab extent = the beams' outer faces (x -0.20 .. 3.20, y -0.20 .. 4.20): every beam is a perimeter beam:
    PERIMETER_MEMBER 14.00 m, HELD on the beam top level; step concrete still 0 (member faces only).
 F5 P2 touching P1 with no beam (x 3.00 .. 6.00): ADJACENT_SUNKEN 4.00 m: HELD on the relative drop (never 0).
 F6 free edge with the slab extent not given: 4.00 m UNKNOWN, step concrete HELD.
Legacy V1 bound (scope_quantities SLAB_STEP): 4 sqrt(12) x 0.30 x 0.16 = 13.8564 x 0.048 = 0.66511 m3 high, allowed only
for a finding with no drawn outline and no framing evidence.
T-213 regression (merged geometry, dimensions already public in research/agents_t213/T-213_SUNKEN_PANELS.md s.9):
panels 275 (1.900 x 1.750) and 276 (1.470 x 1.750) 0.20 apart across one beam, 5BF (1.800 x 3.000) framed all round:
P_ext 5.550 / 4.690 / 9.600 m, P_shared 1.750 / 1.750 / 0; 4 sqrt(A) = 7.2938 / 6.4156 / 9.2952 m.
"""
from __future__ import annotations

import math

import pytest

from engine.source import slab_step_v2 as V

T = dict(t_m=0.16, t_source="fixture note: slab 16 cm")
EXT = [(-3, -3), (6, -3), (6, 7), (-3, 7)]


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def beams(east=True, tf=lambda p: p):
    bs = [V.Member("BS", "BEAM", [tf(p) for p in rect(-0.2, -0.2, 3.2, 0)], 0.60, "fixture schedule"),
          V.Member("BN", "BEAM", [tf(p) for p in rect(-0.2, 4.0, 3.2, 4.2)], 0.60, "fixture schedule"),
          V.Member("BW", "BEAM", [tf(p) for p in rect(-0.2, 0, 0, 4.0)], 0.60, "fixture schedule")]
    if east:
        bs.append(V.Member("BE", "BEAM", [tf(p) for p in rect(3.0, 0, 3.2, 4.0)], 0.60, "fixture schedule"))
    return bs


def p1(tf=lambda p: p, **kw):
    return V.SunkenPanel("P1", [tf(p) for p in rect(0, 0, 3.0, 4.0)], **{**T, **kw})


def run(panel, members, others=(), ext=EXT):
    e = V.classify_outline(panel, members, others, ext)
    return e, V.step_quantities(panel, e, members)


# ---------------------------------------------------------------- normal cases
def test_f1_fully_framed_no_step_concrete_formwork_held():
    e, q = run(p1(), beams())
    assert math.isclose(e["EXTERNAL_MEMBER"], 14.0, abs_tol=1e-9)
    assert e["FREE_SLAB_EDGE"] == 0 and e["SHARED_MEMBER"] == 0 and e["UNKNOWN"] == 0
    assert q["step_concrete_m3"]["value"] == 0.0 and q["step_concrete_m3"]["status"] == V.DC
    for k, sign in (("riser_form_member_m2", "+"), ("member_side_form_adjust_m2", "-")):
        assert q[k]["value"] is None and q[k]["status"] == V.HELD
        assert f"{sign} P_ext x d = {sign} 14.0000 x d" == q[k]["formula"]
        assert q[k]["missing"] == ["drop d (D-41)"]
    assert math.isclose(q["panel_slab_concrete_m3_record"]["value"], 1.92)
    assert q["net_member_form_change_m2"]["value"] == 0.0


def test_f1_with_printed_drop():
    _, q = run(p1(d_m=0.10, d_source="fixture section S-1"), beams())
    assert q["riser_form_member_m2"]["value"] == 1.4
    assert q["member_side_form_adjust_m2"]["value"] == -1.4
    assert q["step_concrete_m3"]["value"] == 0.0


def test_f2_one_free_edge_step_concrete_on_that_edge_only():
    e, q = run(p1(), beams(east=False))
    assert math.isclose(e["EXTERNAL_MEMBER"], 10.0, abs_tol=1e-9)
    assert math.isclose(e["FREE_SLAB_EDGE"], 4.0, abs_tol=1e-9)
    assert q["step_concrete_m3"]["value"] is None and "4.0000 x d x t" in q["step_concrete_m3"]["formula"]
    _, q = run(p1(d_m=0.10, d_source="fixture section S-1"), beams(east=False))
    assert q["step_concrete_m3"]["value"] == 0.064 and q["step_concrete_m3"]["status"] == V.DC
    assert q["riser_form_free_edge_m2"]["value"] == 0.4
    assert q["soffit_step_form_free_edge_m2"]["value"] == 0.4
    assert q["riser_form_member_m2"]["value"] == 1.0
    assert q["member_side_form_adjust_m2"]["value"] == -1.0


def test_f3_shared_beam_held_on_beam_top_level_even_with_d():
    p2 = V.SunkenPanel("P2", rect(3.2, 0, 6.2, 4.0), **T)
    e, q = run(p1(d_m=0.10, d_source="fixture section S-1"), beams(), [p2])
    assert math.isclose(e["SHARED_MEMBER"], 4.0, abs_tol=1e-9) and math.isclose(e["EXTERNAL_MEMBER"], 10.0)
    assert e["shared_with"] == {"P2": pytest.approx(4.0)}
    assert q["shared_member_riser_m2"]["value"] is None
    assert "shared beam top level" in q["shared_member_riser_m2"]["missing"]
    assert q["step_concrete_m3"]["value"] == 0.0


def test_f4_perimeter_beams_held_on_beam_top():
    e, q = run(p1(), beams(), ext=rect(-0.2, -0.2, 3.2, 4.2))
    assert math.isclose(e["PERIMETER_MEMBER"], 14.0, abs_tol=1e-9) and e["EXTERNAL_MEMBER"] == 0
    assert q["shared_member_riser_m2"]["value"] is None
    assert q["step_concrete_m3"]["value"] == 0.0


def test_totals_list_held_never_zero():
    _, a = run(p1(), beams())
    _, b = run(V.SunkenPanel("Q", rect(10, 0, 12, 2), **T),
               [V.Member("X", "BEAM", rect(9.8, -0.2, 12.2, 0)), V.Member("Y", "BEAM", rect(9.8, 2, 12.2, 2.2)),
                V.Member("Z", "BEAM", rect(9.8, 0, 10, 2)), V.Member("W", "BEAM", rect(12, 0, 12.2, 2))],
               ext=[(-3, -3), (20, -3), (20, 7), (-3, 7)])
    tot = V.totals([a, b])
    assert tot["P_ext_m"] == 22.0
    assert tot["riser_form_member_m2"]["complete"] is False and len(tot["riser_form_member_m2"]["held"]) == 2
    assert tot["step_concrete_m3"]["complete"] is True and tot["step_concrete_m3"]["known"] == 0.0


# ---------------------------------------------------------------- adverse cases
def test_legacy_square_bound_refused_where_outline_drawn():
    with pytest.raises(V.SlabStepError, match="outline is drawn"):
        V.legacy_bound(12.0, 0.30, 0.16, outline_drawn=True, framing_evidence=False)
    with pytest.raises(V.SlabStepError, match="framing members"):
        V.legacy_bound(12.0, 0.30, 0.16, outline_drawn=False, framing_evidence=True)


def test_legacy_bound_still_selectable_and_flagged():
    r = V.legacy_bound(12.0, 0.30, 0.16, outline_drawn=False, framing_evidence=False)
    assert r["low"] == 0.0 and math.isclose(r["high"], 4 * math.sqrt(12.0) * 0.30 * 0.16, rel_tol=1e-6)
    assert math.isclose(r["high"], 0.66511, abs_tol=1e-5)
    assert r["flag"] == "LEGACY_SQUARE_EQUIVALENT_BOUND" and r["status"] == V.HELD


@pytest.mark.parametrize("kw", [dict(d_m=0.10), dict(d_m=0.10, d_source="")])
def test_drop_defaulted_refused(kw):
    with pytest.raises(V.SlabStepError, match="default"):
        p1(**kw)


def test_zero_drop_refused_missing_is_none():
    with pytest.raises(V.SlabStepError, match="never 0"):
        p1(d_m=0.0, d_source="x")


def test_thickness_without_source_refused():
    with pytest.raises(V.SlabStepError, match="thickness without a printed source"):
        V.SunkenPanel("P1", rect(0, 0, 3, 4), t_m=0.16)


@pytest.mark.parametrize("bad", ["mm_outline", "mm_t", "mm_d", "mm_member"])
def test_millimetres_refused(bad):
    with pytest.raises(V.SlabStepError):
        if bad == "mm_outline":
            V.SunkenPanel("P1", rect(0, 0, 3000, 4000))
        elif bad == "mm_t":
            V.SunkenPanel("P1", rect(0, 0, 3, 4), t_m=160, t_source="x")
        elif bad == "mm_d":
            V.SunkenPanel("P1", rect(0, 0, 3, 4), d_m=100, d_source="x")
        else:
            V.Member("B", "BEAM", rect(0, 0, 3000, 200))


def test_mirror_and_rotation_give_the_same_lengths():
    base, qb = run(p1(), beams(east=False))
    th = math.radians(33.0)

    def rot(p):
        return (p[0] * math.cos(th) - p[1] * math.sin(th), p[0] * math.sin(th) + p[1] * math.cos(th))

    def mir(p):
        return (-p[0], p[1])

    for tf in (rot, mir):
        e, q = run(p1(tf), beams(east=False, tf=tf), ext=[tf(p) for p in EXT])
        for k in V.EDGE_KINDS:
            assert math.isclose(e[k], base[k], abs_tol=1e-6), (tf.__name__, k)
        assert q["step_concrete_m3"]["formula"] == qb["step_concrete_m3"]["formula"]


def test_adjacent_sunken_without_member_held_not_zero():
    p2 = V.SunkenPanel("P2", rect(3.0, 0, 6.0, 4.0), **T)
    e, q = run(p1(d_m=0.10, d_source="fixture section S-1"), beams(east=False), [p2])
    assert math.isclose(e["ADJACENT_SUNKEN"], 4.0, abs_tol=1e-9)
    assert q["adjacent_sunken_step"]["value"] is None
    assert q["step_concrete_m3"]["value"] is None and q["step_concrete_m3"]["status"] == V.HELD


def test_unknown_edge_without_slab_extent_held():
    e, q = run(p1(d_m=0.10, d_source="fixture section S-1"), beams(east=False), ext=None)
    assert math.isclose(e["UNKNOWN"], 4.0 + 10.0, abs_tol=1e-9)   # far side of the beams is unknown too
    assert q["step_concrete_m3"]["value"] is None and q["unknown_edge"]["value"] is None
    assert q["area_status"] == V.HELD


def test_beam_depth_conflict_refused():
    shallow = [V.Member("BS", "BEAM", rect(-0.2, -0.2, 3.2, 0), 0.30, "fixture schedule")] + beams()[1:]
    panel = p1(d_m=0.15, d_source="fixture section S-1")
    e = V.classify_outline(panel, shallow, (), EXT)
    with pytest.raises(V.SlabStepError, match="BEAM DEPTH CONFLICT"):
        V.step_quantities(panel, e, shallow)


def test_overlapping_panels_refused_and_bad_outline_refused():
    with pytest.raises(V.SlabStepError, match="overlap"):
        V.classify_outline(p1(), beams(), [V.SunkenPanel("P2", rect(2.0, 0, 5.0, 4.0))], EXT)
    with pytest.raises(V.SlabStepError, match="self-intersecting"):
        V.SunkenPanel("BOW", [(0, 0), (3, 4), (3, 0), (0, 4)])
    with pytest.raises(V.SlabStepError, match="depth without a printed source"):
        V.Member("B", "BEAM", rect(0, 0, 3, 0.2), 0.6)
    with pytest.raises(V.SlabStepError, match="kind"):
        V.Member("B", "WALL", rect(0, 0, 3, 0.2))


# ---------------------------------------------------------------- T-213 regression (merged geometry)
def test_t213_three_rectangular_panels_reproduce_merged_edges():
    # 275 at x 0 .. 1.900, 276 at x 2.100 .. 3.570 (one 0.20 beam between), 5BF elsewhere framed all round
    p275 = V.SunkenPanel("275", rect(0, 0, 1.9, 1.75), **T)
    p276 = V.SunkenPanel("276", rect(2.1, 0, 3.57, 1.75), **T)
    p5bf = V.SunkenPanel("5BF", rect(10, 0, 11.8, 3.0), **T)
    ms = [V.Member("b1", "BEAM", rect(-0.2, -0.2, 3.77, 0)), V.Member("b2", "BEAM", rect(-0.2, 1.75, 3.77, 1.95)),
          V.Member("b3", "BEAM", rect(-0.2, 0, 0, 1.75)), V.Member("b4", "BEAM", rect(1.9, 0, 2.1, 1.75)),
          V.Member("b5", "BEAM", rect(3.57, 0, 3.77, 1.75)),
          V.Member("c1", "BEAM", rect(9.8, -0.2, 12.0, 0)), V.Member("c2", "BEAM", rect(9.8, 3.0, 12.0, 3.2)),
          V.Member("c3", "BEAM", rect(9.8, 0, 10, 3.0)), V.Member("c4", "BEAM", rect(11.8, 0, 12.0, 3.0))]
    ext = rect(-5, -5, 20, 10)
    ps = [p275, p276, p5bf]
    got = {p.pid: V.classify_outline(p, ms, ps, ext) for p in ps}
    want = {"275": (5.55, 1.75), "276": (4.69, 1.75), "5BF": (9.6, 0.0)}
    for pid, (pe, psh) in want.items():
        assert math.isclose(got[pid]["EXTERNAL_MEMBER"], pe, abs_tol=1e-6), pid
        assert math.isclose(got[pid]["SHARED_MEMBER"], psh, abs_tol=1e-6), pid
    # the V1 square-equivalent perimeter differs from the drawn step perimeter on every panel
    sq = {p.pid: 4 * math.sqrt(p.area) for p in ps}
    assert round(sq["275"], 4) == 7.2938 and round(sq["276"], 4) == 6.4156 and round(sq["5BF"], 4) == 9.2952
    for p in ps:
        q = V.step_quantities(p, got[p.pid], ms)
        assert q["step_concrete_m3"]["value"] == 0.0          # framed: 0 for any d (T-213 s.6)
        assert q["riser_form_member_m2"]["value"] is None    # D-41 open


def test_module_declares_its_default_guard_class_and_is_unwired():
    assert V.DEFAULT_GUARD_CLASS == "UNWIRED_PRODUCER"
    assert V.METHOD == "SLAB_STEP_V2"


def test_l_panel_member_on_part_of_a_side_only():
    """L panel (0,0) (3,0) (3,1.2) (1.5,1.2) (1.5,2.5) (0,2.5): A = 5.55, P = 11.00 m. Beam S (3.00 m), beam W (2.50 m),
    column 0.30 x 0.30 at the east side's foot (0.30 m of that side); the other 5.20 m are free slab edge.
    d = 0.10, t = 0.16 printed (fixture): step concrete = 5.20 x 0.10 x 0.16 = 0.0832 m3; member riser 5.80 x 0.10."""
    L = V.SunkenPanel("L1", [(0, 0), (3, 0), (3, 1.2), (1.5, 1.2), (1.5, 2.5), (0, 2.5)], d_m=0.10,
                      d_source="fixture section S-2", **T)
    ms = [V.Member("BS", "BEAM", rect(-0.2, -0.2, 3.2, 0), 0.60, "fixture schedule"),
          V.Member("BW", "BEAM", rect(-0.2, 0, 0, 2.5), 0.60, "fixture schedule"),
          V.Member("C1", "COLUMN", rect(3.0, 0, 3.3, 0.3))]
    e, q = run(L, ms)
    assert math.isclose(L.area, 5.55) and math.isclose(L.perimeter, 11.0)
    assert math.isclose(e["EXTERNAL_MEMBER"], 5.8, abs_tol=1e-9)
    assert math.isclose(e["FREE_SLAB_EDGE"], 5.2, abs_tol=1e-9)
    assert math.isclose(e["members"]["C1"], 0.3, abs_tol=1e-9)
    assert q["step_concrete_m3"]["value"] == 0.0832
    assert q["riser_form_member_m2"]["value"] == 0.58 and q["riser_form_free_edge_m2"]["value"] == 0.52


def test_touching_panels_are_not_an_overlap_identical_ones_are():
    a = V.SunkenPanel("A", rect(0, 0, 3, 4))
    assert V.classify_outline(a, [], [V.SunkenPanel("B", rect(3, 0, 6, 4))], EXT)["ADJACENT_SUNKEN"] == \
        pytest.approx(4.0)
    with pytest.raises(V.SlabStepError, match="overlap"):
        V.classify_outline(a, [], [V.SunkenPanel("B", rect(0, 0, 3, 4))], EXT)
