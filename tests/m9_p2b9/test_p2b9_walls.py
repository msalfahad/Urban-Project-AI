"""Phase 2B-9 acceptance: wall geometry per face (ARCH_TAKEOFF_V2.8, UP-WALL-GEOM-001) on worked examples 3 and 4.

    example 3     a south wall of collinear stubs (0.20 / 0.25 / 0.25 m) between a door and a window: the stubs were
                  already measured by V2.7.1 (the face lines merge with their cover intervals) - nothing changes
    example 3R    two returns standing into the room at the door jambs, 0.20 m and 0.35 m long: the 0.30 m band rule
                  drops the 0.20 m return from the wall run (12.95 m); V2.8 measures it as wall (13.15 m), its plan
                  strip moved out of the junction pieces (conserved); the room's finishes were already right
    example 4     a quarter-disc room behind a 90-degree curved wall (inner R 3.00, outer R 3.20): the inner face
                  (4.712389 m) carries the room's finishes, the centreline (4.869469 m) the wall run, the outer face
                  (5.026548 m) the external finish - three measures, never one mean radius for a face
    example 4S    a window in the curved wall leaving a 0.20 m curved stub at each end: V2.8 measures both stubs
                  (0.206667 m each on the centreline); the room itself is lost (curved glazing alone is not read as
                  a window, D-P9-01) and V2.8 reports the lost label instead of staying silent

Truth: p2b9_truth (hand arithmetic)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))

pytest.importorskip("ezdxf")

import p2b9_fixtures as F                                     # noqa: E402
import p2b9_run as R                                          # noqa: E402
import p2b9_truth as T                                        # noqa: E402

A = 1e-6
BUILD = {"e3": F.example3, "e3r": F.example3_returns, "e4": F.example4, "e4s": F.example4_curved_stub}


@pytest.fixture(scope="module")
def ex(tmp_path_factory):
    work = tmp_path_factory.mktemp("p2b9_walls")
    cache = {}

    def get(key, method=R.V28):
        if (key, method) not in cache:
            dxf = work / f"{key}.dxf"
            if not dxf.exists():
                BUILD[key](dxf)
            cache[(key, method)] = R.run(dxf, work / f"o_{key}_{method}", method=method)
        return cache[(key, method)]
    return get


def wall_run(out):
    return round(sum(ln["measured_net"] or 0.0 for ln in R.all_of(out, "ARCH.WALL_RUN")), 6)


def test_a_short_return_is_measured_as_wall(ex):
    new, old = ex("e3r"), ex("e3r", R.V271)
    assert wall_run(old) == pytest.approx(T.E3R_WALL_RUN_BANDS_ONLY, abs=A)
    assert wall_run(new) == pytest.approx(T.E3R_WALL_RUN, abs=A)
    g = R.wall_geometry(new)
    assert [(s["kind"], s["length_m"], s["t_m"], s["plan_m2"], s["ends_closed"]) for s in g["stubs"]] == [
        ("RETURN_STUB", T.E3R_RETURNS["short_return"], T.T, pytest.approx(T.E3R_SHORT_RETURN_PLAN_M2, abs=A), 1)]
    # the plan area is conserved: the stub's strip moves from the junction pieces into the wall strips
    c = g["conservation"][0]
    c0 = R.load(old, "ARCH_WALLS.json")["floors"][0]["conservation"]
    assert c["stubs_m2"] == pytest.approx(T.E3R_SHORT_RETURN_PLAN_M2, abs=A)
    assert c["wall_faces_m2"] == c0["wall_faces_m2"] == pytest.approx(c["band_strips_m2"] + c["junction_m2"], abs=A)
    assert c["junction_m2"] == pytest.approx(c0["junction_m2"] - c["stubs_m2"], abs=A)
    # the room's own finishes were right before and are unchanged (every return face is in its boundary)
    for out in (new, old):
        assert R.net(out, "FIN.FLOOR.PORCELAIN", "floor") == pytest.approx(T.E3R_AREA, abs=A)
        assert R.net(out, "FIN.SKIRTING", "skirting") == pytest.approx(T.E3R_SKIRTING, abs=A)
    assert R.net(new, "FIN.PLASTER", "plaster") == pytest.approx(T.E3R_PLASTER, abs=A)


def test_collinear_stubs_were_already_counted(ex):
    new, old = ex("e3"), ex("e3", R.V271)
    assert wall_run(old) == wall_run(new) == pytest.approx(T.E3_WALL_RUN, abs=A)
    assert R.wall_geometry(new)["stubs"] == []
    assert R.net(new, "FIN.PLASTER", "plaster") == pytest.approx(T.E3_NET, abs=A)
    assert R.net(new, "FIN.SKIRTING", "skirting") == pytest.approx(T.E3_SKIRTING, abs=A)


def test_curved_wall_faces_kept_apart(ex):
    out = ex("e4")
    curved = [w for w in R.wall_geometry(out)["walls"] if "arc_inner_m" in w]
    assert len(curved) == 1
    w = curved[0]
    assert (w["r_in_m"], w["r_out_m"], w["run_basis"]) == (T.R_IN, T.R_OUT, "MID_BAND_ARC")
    assert (w["arc_inner_m"], w["arc_mid_m"], w["arc_outer_m"]) == (
        pytest.approx(T.E4_ARC_INNER, abs=1e-5), pytest.approx(T.E4_ARC_MID, abs=1e-5),
        pytest.approx(T.E4_ARC_OUTER, abs=1e-5))
    assert w["centreline_lm"] == pytest.approx(T.E4_ARC_MID, abs=1e-5)
    assert wall_run(out) == pytest.approx(T.E4_WALL_RUN, abs=1e-5)
    # the room's finishes use the inner face, and the floor the inner radius
    assert R.net(out, "FIN.FLOOR.PORCELAIN", "floor") == pytest.approx(T.E4_FLOOR, abs=1e-5)
    assert R.net(out, "FIN.PLASTER", "plaster") == pytest.approx(T.E4_PLASTER, abs=1e-5)
    assert R.net(out, "FIN.SKIRTING", "skirting") == pytest.approx(T.E4_SKIRTING, abs=1e-5)


def test_curved_stubs_beside_a_curved_window_are_measured(ex):
    new, old = ex("e4s"), ex("e4s", R.V271)
    stubs = R.wall_geometry(new)["stubs"]
    assert [s["kind"] for s in stubs] == ["CURVED_STUB", "CURVED_STUB"]
    for s in stubs:
        assert (s["inner_m"], s["run_lm"]) == (pytest.approx(T.E4S_STUB_INNER, abs=1e-5),
                                              pytest.approx(T.E4S_STUB_MID, abs=1e-5))
    assert wall_run(new) - wall_run(old) == pytest.approx(T.E4S_WALL_RUN_CURVED_STUBS, abs=1e-5)


def test_a_room_label_in_no_closed_space_is_reported(ex):
    """D-P9-01 is not fixed: curved glazing alone does not close the room. V2.8 says so instead of losing it."""
    new, old = ex("e4s"), ex("e4s", R.V271)
    assert not R.rooms(new) and not R.rooms(old)
    lost = [u for u in R.unresolved(new) if "ROOM_LABEL_NOT_IN_A_CLOSED_SPACE" in u["reason"]]
    assert [u["item"] for u in lost] == ["ROOM BEDROOM"]
    assert not [u for u in R.unresolved(old) if "ROOM_LABEL_NOT_IN_A_CLOSED_SPACE" in u["reason"]]
    # a measured room's label is never reported as lost
    assert not [u for u in R.unresolved(ex("e4")) if "ROOM_LABEL_NOT_IN_A_CLOSED_SPACE" in u["reason"]]


def test_open_area_labels_are_not_lost_rooms():
    """a garden / roof / pool / void label outside every room is an open area, not a lost room; the Arabic phrase for
    'swimming pool' (it contains the word for 'bath') is a pool, never a bathroom (D-P9-03)."""
    from engine.source import arch_rooms as AR
    from engine.source import arch_v28 as AV
    open_codes = {c[0] for c in AR.LEXICON if c[3] in (AR.EXTERIOR, AR.VOID)}
    pool_ar = "\u062d\u0645\u0627\u0645 \u0633\u0628\u0627\u062d\u0629"
    texts = [{"id": str(i), "layer": "T", "x": 0.0, "y": 0.0, "value": v}
             for i, v in enumerate(("GARDEN", "ROOF", pool_ar, "SWIMMING POOL", "VOID", "BEDROOM"))]
    got = [(x["code"], x["finding"]) for x in AV.lost_labels(texts, [], AR.room_word, "GF", open_codes=open_codes)]
    assert got == [("GARDEN", "OPEN_AREA_LABEL_OUTSIDE_ROOMS"), ("ROOF", "OPEN_AREA_LABEL_OUTSIDE_ROOMS"),
                   ("POOL", "OPEN_AREA_LABEL_OUTSIDE_ROOMS"), ("POOL", "OPEN_AREA_LABEL_OUTSIDE_ROOMS"),
                   ("VOID", "OPEN_AREA_LABEL_OUTSIDE_ROOMS"), ("BEDROOM", "ROOM_LABEL_NOT_IN_A_CLOSED_SPACE")]
    # the room lexicon itself is unchanged (frozen methods read it): the phrase still reads as a bathroom there
    assert AR.room_word(pool_ar)[0] == "BATHROOM"
