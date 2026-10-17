"""Phase N10 - curved wall openings (ARCH_TAKEOFF_V2.9; D-P9-01 / D-P9-02), against hand truth (n10_truth.py).

    as found (V2.8)   curved glazing alone is not read as a window: the room is lost (no roles declared), or it is
                      closed at its glazing line and takes the 0.438423 m2 reveal strip as floor (roles declared)
    V2.9              a jambed gap in a curved wall band is an opening closed on both wall faces: the room ends at
                      its own wall face, the window's width on it is that face's arc, the strip to the glazing is the
                      sill surface (or floor at floor-level glazing), the reveals are measured radially
    refused           a gap without jamb lines, a wall arc inside the gap, a furniture / decorative arc (never glazing)
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "m9_p2b9"))

import n10_fixtures as F                                      # noqa: E402
import n10_run as R                                           # noqa: E402
import n10_truth as T                                         # noqa: E402
import p2b9_fixtures as F9                                    # noqa: E402

A = 1e-5          # arc-flattened faces (sagitta <= 1 mm) keep the strip areas to a few square micrometres


@pytest.fixture(scope="module")
def ex(tmp_path_factory):
    cache = {}
    root = tmp_path_factory.mktemp("n10_curved")

    def get(case, method=R.V29, roles=None, extra=(), evidence=F.FULL):
        key = (case, method, bool(roles), tuple(extra), tuple(sorted(evidence)))
        if key not in cache:
            name = "_".join([case, method.replace(".", "_"), "r" if roles else "u", *extra])
            if case == "E4S":
                dxf = F9.example4_curved_stub(root / f"{name}.dxf")
            elif case == "NESTED":
                dxf = F.nested(root / f"{name}.dxf")
            else:
                dxf = F.curved_room(root / f"{name}.dxf", opening=case, extra=extra, evidence=evidence)
            cache[key] = R.run(dxf, root / f"out_{name}", roles=roles, method=method)
        return cache[key]
    return get


def _one_curved(out):
    cv = R.curved(out)["curved_openings"]
    assert len(cv) == 1, cv
    return cv[0]


# --------------------------------------------------------------------------------------------- as found (V2.8)
def test_as_found_v28_loses_or_overcounts_the_curved_window_room(ex):
    assert not R.rooms(ex("E4S", R.V28))                                      # D-P9-01: the room is lost
    assert R.floor_area(ex("E4S", R.V28, F.ROLES)) == pytest.approx(T.FLOOR_IF_CLOSED_AT_GLAZING, abs=A)   # D-P9-02


# --------------------------------------------------------------------------------------------- V2.9 corrections
@pytest.mark.parametrize("roles", [None, F.ROLES], ids=["inferred_roles", "declared_roles"])
def test_curved_window_room_ends_at_its_own_wall_face(ex, roles):
    out = ex("E4S", roles=roles)
    assert R.floor_area(out) == pytest.approx(T.FLOOR, abs=A)
    w = _one_curved(out)
    assert (w["kind"], w["room_side"], w["width_basis"]) == ("WINDOW", "MIN_RADIUS", "MIN_RADIUS_ARC")
    assert w["width_m"] == pytest.approx(T.WIN_INNER, abs=A)
    assert w["bases_m"] == pytest.approx({"MIN_RADIUS_ARC": T.WIN_INNER, "MID_BAND_ARC": T.WIN_GLAZ,
                                          "MAX_RADIUS_ARC": T.WIN_OUTER, "CHORD": T.WIN_CHORD}, abs=A)
    layers = [g["layer"] for g in R.curved(out)["glazing_layers"]]
    assert layers == ([] if roles else ["A-GLAZ"])                            # a declared role is never changed
    assert not [u for u in R.unresolved(out) if "ROOM_LABEL_NOT_IN_A_CLOSED_SPACE" in u["reason"]]


def test_curved_window_without_height_holds_its_deduction(ex):
    out = ex("E4S")                                                          # example 4S: no W4 row, no tag
    rg = R.range_of(out, "FIN.PLASTER", "plaster")
    assert (rg["low"], rg["high"]) == (pytest.approx(T.W4_UNKNOWN_LOW, abs=A), pytest.approx(T.W4_UNKNOWN_HIGH, abs=A))
    assert R.net(out, "FIN.SKIRTING", "skirting") == pytest.approx(T.W4_UNKNOWN_SKIRTING, abs=A)
    sk = R.range_of(out, "FIN.SKIRTING", "skirting, boundary role unresolved")
    assert (sk["low"], sk["high"]) == (0.0, pytest.approx(T.WIN_INNER, abs=A))


def test_curved_sill_window_finishes_and_reveals(ex):
    out = ex("WINDOW")
    assert R.floor_area(out) == pytest.approx(T.FLOOR, abs=A)
    for code in ("FIN.PLASTER", "FIN.PAINT"):
        assert R.net(out, code, "plaster" if code == "FIN.PLASTER" else "paint") == pytest.approx(T.W4_PLASTER, abs=A)
    assert R.net(out, "FIN.SKIRTING", "skirting") == pytest.approx(T.W4_SKIRTING, abs=A)
    assert R.net(out, "ARCH.WINDOW_REVEAL", "window sill surface") == pytest.approx(T.REVEAL_STRIP, abs=A)
    assert R.net(out, "ARCH.WINDOW_REVEAL", "window external strip") == pytest.approx(T.EXTERNAL_STRIP, abs=A)
    assert R.net(out, "FIN.PLASTER", "window reveals") == pytest.approx(T.W4_REVEAL_PLASTER, abs=A)
    rv = [x for x in R.reveals(out) if x["state"] == "MEASURED"]
    assert len(rv) == 1 and rv[0]["depth_m"] == pytest.approx(T.REVEAL_DEPTH, abs=1e-4)
    assert rv[0]["jambs_m2"] == pytest.approx(T.W4_REVEAL_JAMBS, abs=A)
    assert rv[0]["head_m2"] == pytest.approx(T.W4_REVEAL_HEAD, abs=A)


def test_curved_floor_level_glazing(ex):
    out = ex("FLOOR_GLAZING")
    assert R.net(out, "FIN.PLASTER", "plaster") == pytest.approx(T.W5_PLASTER, abs=A)
    assert R.net(out, "FIN.SKIRTING", "skirting") == pytest.approx(T.W5_SKIRTING, abs=A)
    assert R.net(out, "FIN.FLOOR.PORCELAIN", "window floor strip") == pytest.approx(T.W5_FLOOR_STRIP, abs=A)
    assert R.net(out, "FIN.PLASTER", "window reveals") == pytest.approx(T.W5_REVEAL_PLASTER, abs=A)
    assert R.floor_area(out) == pytest.approx(T.FLOOR, abs=A)                # the strip is its own floor line


def test_curved_door(ex):
    out = ex("DOOR")
    d = _one_curved(out)
    assert d["kind"] == "DOOR" and d["door_symbol"]
    assert d["width_m"] == pytest.approx(T.GAP_INNER, abs=A)
    assert R.floor_area(out) == pytest.approx(T.FLOOR, abs=A)
    assert R.net(out, "FIN.PLASTER", "plaster") == pytest.approx(T.D2_PLASTER, abs=A)
    assert R.net(out, "FIN.SKIRTING", "skirting") == pytest.approx(T.GAP_SKIRTING, abs=A)
    strips = sorted(ln["measured_net"] for ln in R.all_of(out, "FIN.FLOOR.PORCELAIN", "doorway strip"))
    assert strips == [pytest.approx(T.DOOR1_W * T.T, abs=A), pytest.approx(T.DOORWAY_STRIP, abs=A)]
    assert not [u for u in R.unresolved(out) if "DOOR_CLOSURE_UNRESOLVED" in u["reason"]]


def test_curved_passage(ex):
    out = ex("PASSAGE")
    assert _one_curved(out)["kind"] == "PASSAGE"
    assert R.net(out, "FIN.PLASTER", "plaster") == pytest.approx(T.PASSAGE_PLASTER, abs=A)
    assert R.net(out, "FIN.SKIRTING", "skirting") == pytest.approx(T.GAP_SKIRTING, abs=A)


def test_splayed_jamb_is_still_an_opening(ex):
    out = ex("SPLAYED")
    w = _one_curved(out)
    assert w["kind"] == "WINDOW" and w["width_m"] == pytest.approx(T.WIN_INNER, abs=A)
    assert R.floor_area(out) == pytest.approx(T.FLOOR, abs=A)
    assert R.net(out, "FIN.PLASTER", "plaster") == pytest.approx(T.W4_PLASTER, abs=A)


# --------------------------------------------------------------------------------------------- refusals
def test_gap_without_jamb_lines_is_not_an_opening(ex):
    out = ex("NO_JAMB")
    assert not R.curved(out)["curved_openings"]
    assert "NO_JAMB_LINE_AT_BOTH_ENDS" in [x["reason"] for x in R.curved(out)["curved_gaps_rejected"]]
    assert not R.rooms(out)
    assert [u["item"] for u in R.unresolved(out) if "ROOM_LABEL_NOT_IN_A_CLOSED_SPACE" in u["reason"]] == ["ROOM BEDROOM"]


def test_wall_arc_inside_the_gap_is_wall(ex):
    out = ex("WINDOW", extra=("WALL_ARC_IN_GAP",))
    assert not R.curved(out)["curved_openings"]
    assert "WALL_ARC_INSIDE_THE_GAP" in [x["reason"] for x in R.curved(out)["curved_gaps_rejected"]]
    # the drawn wall line r 3.10 bounds the room: the quarter disc + the band 3.00 .. 3.10 over the gap
    assert R.floor_area(out) == pytest.approx(T.FLOOR + T.REVEAL_STRIP, abs=A)


@pytest.mark.parametrize("extra", [("FURNITURE",), ("DECOR",)], ids=["furniture_arc", "decor_arcs"])
def test_furniture_and_decor_arcs_change_nothing(ex, extra):
    out, ref = ex("WINDOW", extra=extra), ex("WINDOW")
    assert [g["layer"] for g in R.curved(out)["glazing_layers"]] == ["A-GLAZ"]
    for code, el in (("FIN.FLOOR.PORCELAIN", "floor"), ("FIN.PLASTER", "plaster"), ("FIN.SKIRTING", "skirting"),
                     ("FIN.PLASTER", "window reveals")):
        assert R.net(out, code, el) == pytest.approx(R.net(ref, code, el), abs=A)


# --------------------------------------------------------------------------------------------- invariance
def test_nested_block_turned_30_degrees(ex):
    out = ex("NESTED")
    assert R.floor_area(out) == pytest.approx(T.FLOOR, abs=A)
    assert _one_curved(out)["width_m"] == pytest.approx(T.WIN_INNER, abs=A)
    assert R.net(out, "FIN.PLASTER", "plaster") == pytest.approx(T.W4_PLASTER, abs=A)
    assert R.net(out, "FIN.PLASTER", "window reveals") == pytest.approx(T.W4_REVEAL_PLASTER, abs=A)


def plan_rot(src, dst, deg):
    """the plan sheet's entities turned about the room; the schedule and section sheets stay upright (a turned
    schedule is not read: L-P9-01), as on a real drawing set (tests/m9_p2b9/test_p2b9_invariance.plan_rot30)."""
    import math
    import ezdxf
    from ezdxf.math import Matrix44
    doc = ezdxf.readfile(str(src))
    msp = doc.modelspace()
    c = (1700.0, 1700.0)
    m = Matrix44.chain(Matrix44.translate(-c[0], -c[1], 0), Matrix44.z_rotate(math.radians(deg)),
                       Matrix44.translate(c[0], c[1], 0))
    for e in list(msp):
        p = F.F6._ref(e)
        if e.dxf.layer in F.F6.SHEET or p is None or not (-6000 <= p[0] <= 24000 and -8000 <= p[1] <= 18000):
            continue
        e.transform(m)
    doc.saveas(str(dst))
    return dst


@pytest.mark.parametrize("kind", ["plan_rot30", "plan_rot200", "mirror", "translate", "metres", "reorder"])
def test_transformed_plans_measure_the_same(tmp_path, kind):
    src = F.curved_room(tmp_path / "src.dxf", opening="WINDOW")
    dst = tmp_path / f"{kind}.dxf"
    if kind.startswith("plan_rot"):
        plan_rot(src, dst, float(kind[len("plan_rot"):]))
    else:
        F.variant(src, dst, kind)
    out = R.run(dst, tmp_path / "out", units="m" if kind == "metres" else None)
    assert R.floor_area(out) == pytest.approx(T.FLOOR, abs=A)
    assert _one_curved(out)["width_m"] == pytest.approx(T.WIN_INNER, abs=A)
    assert R.net(out, "FIN.PLASTER", "plaster") == pytest.approx(T.W4_PLASTER, abs=A)
    assert R.net(out, "ARCH.WINDOW_REVEAL", "window sill surface") == pytest.approx(T.REVEAL_STRIP, abs=A)
    assert R.net(out, "FIN.PLASTER", "window reveals") == pytest.approx(T.W4_REVEAL_PLASTER, abs=A)


# --------------------------------------------------------------------------------------------- the gap reader
def test_curved_gap_straddling_zero_degrees():
    """a round room (a full ring wall) with one jambed gap from -20 to +20 degrees (across the 0 / 360 seam)."""
    import math
    from engine.source import arch_v29 as V29
    c, r1, r2 = (0.0, 0.0), 3000.0, 3200.0
    a0, a1 = math.radians(20.0), math.radians(340.0)

    def arc(i, r):
        return {"id": f"A{i}", "layer": "W", "c": c, "r": r, "s": (r * math.cos(a0), r * math.sin(a0)),
                "e": (r * math.cos(a1), r * math.sin(a1)), "dir": "CCW"}
    jamb = [{"id": f"J{k}", "layer": "W", "a": (r1 * math.cos(t), r1 * math.sin(t)),
             "b": (r2 * math.cos(t), r2 * math.sin(t))} for k, t in enumerate((a0, a1))]
    gaps, rej = V29.curved_gaps({"arcs": [arc(0, r1), arc(1, r2)], "segments": jamb}, ["W"], 0.001)
    assert len(gaps) == 1 and not rej
    g = gaps[0]
    assert g["th1"] - g["th0"] == pytest.approx(math.radians(40.0), abs=1e-9)
    assert sorted(g["jambs"]) == ["J0", "J1"]
