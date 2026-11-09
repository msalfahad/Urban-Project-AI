"""T-534: stair marble vs stair bed, and the reconciliation of two stair-marble figures (research/agents_t534).

Fixture villa P534 (not the training villa), by hand:
  one straight flight F1, 12 risers of 0.17, going 0.30, width 1.20; the 12th riser lands on a landing, so 11 treads
  (a tread needs a riser below it and the landing is never a tread); landing LD 1.20 x 1.20; tread marble 0.030.
    treads   11 x 0.30 x 1.20               = 3.9600 m2
    risers   12 x 1.20 x (0.17 - 0.03)      = 2.0160 m2   (visible riser, UP-STAIR-003)
    landing  1.20 x 1.20                    = 1.4400 m2
    marble                                  = 7.4160 m2
  bed with a riser-bed source               = 7.4160 m2 -> 0.22248 m3 (0.03 m) -> 1:3 (UP-STAIR-017):
      cement 0.22248 x 9.576 = 2.13046848 bags, sand 0.22248 x 0.9975 = 0.2219238 m3
  bed with NO riser-bed source              = AT_LEAST 5.4000 m2 (treads + landing), riser bed HELD beside 2.016
  A second figure that counts 'one tread per riser' at the printed 1.25 width and the full rise:
    12 x 0.30 x 1.25 = 4.50 tread, 12 x 0.17 x 1.25 = 2.55 riser, no landing -> 7.05 m2.
    A -> B: tread COUNT (11 - 12) x 1.25 x 0.30 = -0.375, WIDTH 11 x (1.20 - 1.25) x 0.30 = -0.165;
            riser WIDTH 12 x (1.20 - 1.25) x 0.17 = -0.102, HEIGHT 12 x 1.20 x (0.14 - 0.17) = -0.432;
            landing SCOPE +1.44 -> 7.05 - 0.375 - 0.165 - 0.102 - 0.432 + 1.44 = 7.416 (residual 0).
Adverse: a held flight is HELD, never 0; a riser is never bedded without a source; a surface keyed twice; treads >
risers; a visible riser <= 0; mm for m; a difference with no stated cause; an unexplained rest; mirror / rotation of
the landing polygon.
"""

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t534"))

import stair_bed_reconcile as M  # noqa: E402
from engine.source import finish_materials_table_v7 as V7  # noqa: E402

A = lambda x: pytest.approx(x, abs=1e-6)  # noqa: E731
T = 0.03
F1 = dict(id="F1", treads=11, risers=12, going=0.30, width=1.20, rise=0.17)
LD = dict(id="LD", polygon=[(0, 0), (1.2, 0), (1.2, 1.2), (0, 1.2)])


def villa(f=F1, ld=LD):
    return M.check_once(M.flight_parts(f, T) + [M.landing_part(ld)])


def test_marble_by_hand():
    t = M.totals(villa())
    assert t["by_surface"] == {"TREAD": A(3.96), "RISER": A(2.016), "LANDING": A(1.44)}
    assert t["determinate_m2"] == A(7.416) and t["state"] == "COMPLETE"


def test_bed_with_riser_source_and_v7():
    bed = M.bed_parts(villa(), "owner record naming risers in the stair bed")
    t = M.totals(bed)
    assert t["determinate_m2"] == A(7.416) and t["state"] == "COMPLETE"
    v = V7.table([{"id": "P534", "floor": "GF", "kind": V7.STAIR_LANDING, "area_m2": t["determinate_m2"]}])
    r = v["rows"][0]
    assert r["mortar_m3_low"] == A(0.22248)
    assert r["cement_bags_low"] == A(0.22248 * 9.576) == A(2.13046848)
    assert r["sand_m3_low"] == A(0.22248 * 0.9975)


def test_riser_never_bedded_without_source():
    bed = M.bed_parts(villa(), None)
    t = M.totals(bed)
    assert t["determinate_m2"] == A(5.40) and t["state"] == "PARTIAL"
    (h,) = t["held"]
    assert h["surface"] == "RISER" and h["beside"] == A(2.016) and "RISER_BED_SOURCE_NOT_GIVEN" in h["reason"]
    # the riser MARBLE stays measured: marble and bed differ by exactly the riser m2
    assert M.totals(villa())["determinate_m2"] - t["determinate_m2"] == A(2.016)


def test_held_flight_is_held_never_zero():
    parts = villa(dict(id="F1", held="WINDERS_NOT_ESTABLISHED", beside_tread=3.0))
    t = M.totals(parts)
    assert t["determinate_m2"] == A(1.44) and t["state"] == "PARTIAL"
    assert {(h["surface"], h["beside"]) for h in t["held"]} == {("TREAD", 3.0), ("RISER", None)}
    assert all(p["m2"] is None for p in parts if p["status"] == M.HELD)
    assert t["print"].startswith("AT_LEAST 1.4400 m2 + HELD (2 parts)")


def test_unknown_rise_holds_riser_only():
    t = M.totals(villa(dict(F1, rise=None)))
    assert t["by_surface"]["TREAD"] == A(3.96) and t["by_surface"]["RISER"] == 0.0
    assert [h["reason"] for h in t["held"]] == ["RISE_NOT_ESTABLISHED"]


def test_material_held_landing_kept_beside():
    t = M.totals(villa(ld=dict(LD, material_held="floor or landing")))
    assert t["determinate_m2"] == A(5.976) and t["held"][0]["beside"] == A(1.44)


def test_held_tread_going_and_closing_riser():
    f = dict(F1, treads=10, treads_held=1, risers=11, risers_held=1)
    t = M.totals(villa(f))
    assert t["by_surface"]["TREAD"] == A(3.60) and t["by_surface"]["RISER"] == A(11 * 1.2 * 0.14)
    assert sorted(h["beside"] for h in t["held"]) == [A(0.168), A(0.36)]


def test_mm_mirror_rotation():
    mm = dict(id="F1", treads=11, risers=12, going=300, width=1200, rise=170, unit_m=0.001)
    ldm = dict(id="LD", polygon=[(0, 0), (1200, 0), (1200, 1200), (0, 1200)], unit_m=0.001)
    base = M.totals(villa())["determinate_m2"]
    assert M.totals(villa(mm, ldm))["determinate_m2"] == A(base)
    c, s = math.cos(0.7), math.sin(0.7)
    rot = [(x * c - y * s + 5, x * s + y * c - 3) for x, y in LD["polygon"]]
    mir = [(-x, y) for x, y in LD["polygon"]]
    for poly in (rot, mir, list(reversed(rot))):
        assert M.totals(villa(ld=dict(id="LD", polygon=poly)))["determinate_m2"] == A(base)


def test_refusals():
    with pytest.raises(M.ReconcileError, match="counted twice"):
        M.check_once(villa() + M.flight_parts(F1, T))
    with pytest.raises(M.ReconcileError, match="treads >"):
        M.flight_parts(dict(F1, treads=13), T)
    with pytest.raises(M.ReconcileError, match="visible riser"):
        M.flight_parts(dict(F1, rise=0.03), T)
    with pytest.raises(M.ReconcileError, match="must be"):
        M.flight_parts(dict(F1, width=0), T)
    with pytest.raises(M.ReconcileError, match="HELD part carries no figure"):
        M.part("X", M.TREAD, 1.0, M.HELD, "b", "r")
    with pytest.raises(M.ReconcileError, match="needs its m2"):
        M.part("X", M.TREAD, None, M.CALCULATED, "b")


def figure_a():
    a = [M.part("F1", M.TREAD, 12 * 0.30 * 1.25, M.CALCULATED, "a", components={"n": 12, "w": 1.25, "d": 0.30}),
         M.part("F1", M.RISER, 12 * 0.17 * 1.25, M.CALCULATED, "a", components={"n": 12, "w": 1.25, "d": 0.17})]
    return M.figure(a)


def test_reconcile_by_hand():
    r = M.reconcile(figure_a(), M.figure(villa()), {("LD", M.LANDING): "landing not in A"})
    assert r["a_m2"] == A(7.05) and r["b_m2"] == A(7.416) and r["unexplained_m2"] == 0.0
    c = {(x["key"], x["surface"]): {k["cause"]: k["m2"] for k in x["causes"]} for x in r["rows"]}
    assert c[("F1", "TREAD")] == {"COUNT": A(-0.375), "WIDTH": A(-0.165)}
    assert c[("F1", "RISER")] == {"WIDTH": A(-0.102), "DEPTH_OR_HEIGHT": A(-0.432)}
    assert c[("LD", "LANDING")] == {"SCOPE": A(1.44)}
    assert sum(r["by_cause"].values()) == A(7.416 - 7.05)


def test_reconcile_refuses_unstated_and_unexplained():
    with pytest.raises(M.ReconcileError, match="no scope cause"):
        M.reconcile(figure_a(), M.figure(villa()), {})
    a = figure_a()
    b = dict(a)
    b[("F1", M.TREAD)] = {"m2": a[("F1", M.TREAD)]["m2"] + 0.05, "components": a[("F1", M.TREAD)]["components"]}
    with pytest.raises(M.ReconcileError, match="no cause stated"):
        M.reconcile(a, b, {})
    r = M.reconcile(a, b, {}, {("F1", M.TREAD): "polygon line"})
    assert r["by_cause"] == {"POLYGON": A(0.05)}
    b2 = dict(a)
    b2[("F1", M.TREAD)] = {"m2": 9.99, "components": None}
    with pytest.raises(M.ReconcileError, match="no cause stated"):
        M.reconcile(a, b2, {})


# ---------------------------------------------------------------- training villa pins (committed merged inputs) ----
def alsenan():
    import t534_alsenan as AL
    return AL, AL.build()


def test_alsenan_figures_and_reconciliation():
    AL, o = alsenan()
    ab = o["reconcile"]["A_to_B"]
    assert ab["a_m2"] == A(39.485) and ab["b_m2"] == A(35.4313) and ab["diff_m2"] == A(-4.0537)
    assert ab["by_cause"] == {"COUNT": A(-3.0), "WIDTH": A(-0.66), "DEPTH_OR_HEIGHT": A(-0.42),
                              "POLYGON": A(-0.0006), "SCOPE": A(0.0269)}
    scope = [c["m2"] for r in ab["rows"] for c in r["causes"] if c["cause"] == "SCOPE"]
    assert sum(x for x in scope if x < 0) == A(-14.905) and sum(x for x in scope if x > 0) == A(14.9319)
    bc = o["reconcile"]["B_to_C"]
    assert bc["b_m2"] == A(56.35861) and bc["by_cause"] == {"POLYGON": A(0.0012), "SCOPE": A(20.92611)}
    # every released candidate key agrees with the drawing (within the two printed-vs-polygon residuals)
    for r in bc["rows"]:
        if r["a_m2"]:
            assert abs(r["diff_m2"]) <= 0.0006 + 1e-9
    tb = o["B_candidate"]["totals"]
    assert tb["state"] == "PARTIAL" and len(tb["held"]) == 20 and tb["print"].startswith("AT_LEAST 35.4313 m2")
    assert len(o["B_candidate"]["held_lines"]) == 23 and len(o["B_candidate"]["lines"]) == 34


def test_alsenan_bed_and_v7():
    AL, o = alsenan()
    c = o["C_drawing"]
    assert c["marble"]["by_surface"] == {"TREAD": A(23.37), "RISER": A(12.29861), "LANDING": A(20.69)}
    assert c["bed_with_q45_riser_source"]["determinate_m2"] == A(56.35861)
    assert c["bed_without_riser_source"]["determinate_m2"] == A(44.06)
    vb = o["v7"]["on_candidate_B"]
    assert vb["area_m2"] == A(35.4313) and vb["mortar_m3_low"] == A(1.062939)
    assert vb["cement_bags_low"] == A(10.178704) and vb["sand_m3_low"] == A(1.06028)
    vc = o["v7"]["on_drawing_C_bed"]
    assert vc["mortar_m3_low"] == pytest.approx(56.35861 * 0.03, abs=1e-5)
    assert vc["cement_bags_low"] == pytest.approx(56.35861 * 0.03 * 9.576, abs=1e-4)  # V7 rounds per row


def test_alsenan_committed_out_reproduces():
    import json
    AL, o = alsenan()
    old = json.loads((AL.OUT / "T534_STAIR_BED_RECONCILE.json").read_text(encoding="utf-8"))
    assert old == json.loads(json.dumps(o, sort_keys=True))
