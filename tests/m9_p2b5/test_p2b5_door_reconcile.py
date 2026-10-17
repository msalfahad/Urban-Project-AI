"""Phase 2B-5 (ARCH_TAKEOFF_V2.6, correction D-V26-06): door symbol reconciliation (finding D-C1 of the real-room
verification). The expected results come from the rule text and the fixture geometry, never from the engine:

    review fit (arch_rooms.match_swings_review), for a swing whose leaf closes no gap and a passage with no door:
        hinge within 0.30 m of a jamb (strict) .. 0.45 m (review); leaf >= 25 % / 0.15 m off the width (strict) down to
        60 % of the width (review); the closed leaf must lie along the opening's wall line
    closure fit (arch_rooms.closure_in_passage), for a leaf-closed swing: its closure parallel to the passage's wall
    (2 degrees), its middle between the jambs and within 50 mm of the wall band, no longer than the gap + 0.15 m
    either fit -> the passage is a DOOR held from every released total (DOOR_SYMBOL_FIT_REVIEW), both widths recorded
    beyond the review limits, within 1.0 m -> the passage stays a PASSAGE with a note

V2.5 (and every earlier method) never calls either fit: the same drawing keeps its passage there."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests" / "m9_p2b5_bench"))

from engine.source import arch_rooms as AR                    # noqa: E402

ezdxf = pytest.importorskip("ezdxf")

U = 0.001                                                     # drawing mm


def _opening(oid="OP-1", s0=1000.0, s1=1800.0, kind="PASSAGE"):
    """a gap in a horizontal wall band y 0 .. 200 (mm): along x from s0 to s1."""
    return {"opening_id": oid, "s0": s0, "s1": s1, "o0": 0.0, "o1": 200.0, "u": (1.0, 0.0), "n": (0.0, 1.0),
            "kind": kind, "width_m": (s1 - s0) * U}


def _swing(hx, r, closed_along=True):
    """a swing hinged on the room face (y 200): open leaf up (+y), closed leaf along the wall towards -x."""
    ends = [(hx, 200.0 + r), (hx - r, 200.0)] if closed_along else [(hx, 200.0 + r), (hx - 0.7 * r, 200.0 + 0.7 * r)]
    return {"hinge": (hx, 200.0), "radius": r, "ends": ends}


def _review(ops, swings):
    return AR.match_swings_review(ops, swings, U, {})


# ---- the review fit: boundaries ---------------------------------------------------------------------------------

def test_a_strict_fit_is_not_a_review_fit():
    got, notes = _review([_opening()], {"S": _swing(1800, 800)})
    assert got == {} and notes == {}


@pytest.mark.parametrize("hx,expect", [(2099.0, False), (2150.0, True), (2250.0, True), (2251.0, False)])
def test_the_hinge_limits(hx, expect):
    """dj = hx - 1800: 299 strict (left to match_swings), 350 / 450 review, 451 beyond -> a note."""
    got, notes = _review([_opening()], {"S": _swing(hx, 800)})
    assert ("OP-1" in got) == expect
    if expect:
        assert got["OP-1"][0] == "S" and f"hinge {(hx - 1800) / 1000:.3f} m from the jamb" in got["OP-1"][1]
    elif hx > 2250:
        assert notes["OP-1"]["hinge_from_jamb_m"] == round((hx - 1800) / 1000, 3)
        assert notes["OP-1"]["why_not_a_door"].startswith("hinge 0.451 m from the nearest jamb (review limit 0.45 m)")
    else:
        assert notes == {}                                  # a strict fit is never noted


@pytest.mark.parametrize("r,expect", [(690.0, True), (600.0, True), (599.0, False)])
def test_the_leaf_share_limit(r, expect):
    """a 1.00 m gap: strict needs the leaf within 0.25 m (or a half leaf of 0.35 - 0.65 m); review takes 60 %."""
    got, notes = _review([_opening(s1=2000.0)], {"S": _swing(2000.0, r)})
    assert ("OP-1" in got) == expect
    if expect:
        assert f"= {100 * r / 1000:.0f} % of the 1.000 m opening" in got["OP-1"][1]
    else:
        assert notes["OP-1"]["why_not_a_door"].startswith("leaf 0.599 m under 60 % of the 1.000 m opening")


def test_a_leaf_not_closing_along_the_wall_is_never_fitted():
    got, notes = _review([_opening()], {"S": _swing(2150.0, 800, closed_along=False)})
    assert got == {} and "the closed leaf does not lie along the opening's wall line" in notes["OP-1"]["why_not_a_door"]


def test_one_swing_serves_one_opening_the_nearest():
    ops = [_opening("OP-A", 1000, 1800), _opening("OP-B", 2600, 3400)]
    got, _ = _review(ops, {"S": _swing(2150.0, 800)})      # 0.35 m from OP-A's jamb, 0.45 m from OP-B's
    assert list(got) == ["OP-A"]


# ---- the closure fit ----------------------------------------------------------------------------------------------

@pytest.mark.parametrize("seg,expect", [
    ((1100.0, 100.0, 1900.0, 100.0), True),                 # 0.80 m along the wall line inside a 1.00 m gap
    ((1100.0, 240.0, 1900.0, 240.0), True),                 # 40 mm beside the room face: within the 50 mm band margin
    ((1100.0, 260.0, 1900.0, 260.0), False),                # 60 mm beside it
    ((1500.0, 300.0, 1500.0, 1100.0), False),               # perpendicular: a door into a room beyond the passage
    ((2300.0, 100.0, 3100.0, 100.0), False),                # parallel, its middle past the jamb
    ((1000.0, 100.0, 2160.0, 100.0), False),                # longer than the gap + 0.15 m
])
def test_the_closure_limits(seg, expect):
    o = _opening(s1=2000.0)
    hit = AR.closure_in_passage(seg, [o], U)
    assert (hit is not None) == expect
    if expect:
        assert hit[0] is o and abs(hit[1] - 800.0) < 1e-9


# ---- through the command line: V2.5 against V2.6 on the same drawing ------------------------------------------------

DECLARED = ("A-WALL=WALL", "A-COL=COLUMN", "A-GLAZ=WINDOW", "A-DOOR=DOOR")


def _drawing(path, *, gap=(1000, 1800), hinge_x=1800.0, scale=None):
    """B01 of the room-reader benchmark (a 4.00 x 3.00 m bathroom, door in the south wall, a 0.60 m window) with
    its door gap and its door block placed / scaled as given."""
    import bench_cases as BC
    import bench_drawings as BD
    s0, s1 = gap
    case = dict(BC.BY_ID["B01"], openings=[("DOOR", "y", 0, 200, s0, s1, (s1, 200, 90, 1, 1)),
                                           ("WINDOW", "x", 4200, 4400, 1000, 1600, None)])
    BD.dxf(case, path)
    doc = ezdxf.readfile(str(path))
    for e in doc.modelspace().query("INSERT[layer=='A-DOOR']"):
        e.dxf.insert = (hinge_x, 200.0)
        k = scale if scale is not None else (s1 - s0) / 1000.0
        e.dxf.xscale, e.dxf.yscale = k, k
    doc.saveas(str(path))
    return path


def _run(dxf, out, method):
    r = subprocess.run([sys.executable, "-I", str(ROOT / "tools" / "urban_boq_m9.py"), "arch", "--drawings", str(dxf),
                        "--out", str(out), "--method", method, "--layer-roles", *DECLARED],
                       capture_output=True, text=True, cwd=str(out.parent))
    assert r.returncode == 0, r.stderr[-2000:]
    ops = json.loads((out / "ARCH_OPENINGS.json").read_text(encoding="utf-8"))["openings"]
    lines = list(csv.DictReader((out / "BOQ_LINES.csv").open(encoding="utf-8")))
    doors = json.loads((out / "DOOR_SCHEDULE.json").read_text(encoding="utf-8"))["doors"]
    rooms = json.loads((out / "ARCH_ROOMS.json").read_text(encoding="utf-8"))["rooms"]
    run = json.loads((out / "RUN_RULES.json").read_text(encoding="utf-8"))["arch"]
    return {"door": next(o for o in ops if o["width_m"] > 0.7), "lines": lines, "doors": doors, "rooms": rooms,
            "run": run}


def _code(res, code):
    return [x for x in res["lines"] if x["item_code"] == code]


@pytest.fixture(scope="module")
def runs(tmp_path_factory):
    base = tmp_path_factory.mktemp("doorfit")
    cases = {"strict": {}, "hinge_035": {"hinge_x": 2150.0}, "hinge_050": {"hinge_x": 2300.0},
             "leaf_069": {"gap": (1000, 2000), "hinge_x": 2000.0, "scale": 0.69}}
    out = {}
    for name, kw in cases.items():
        dxf = _drawing(base / f"{name}.dxf", **kw)
        for m in ("ARCH_TAKEOFF_V2.5", "ARCH_TAKEOFF_V2.6"):
            out[(name, m[-3:])] = _run(dxf, base / f"{name}_{m[-3:]}", m)
    return out


def test_a_strict_door_is_the_same_in_both_methods(runs):
    for m in ("2.5", "2.6"):
        r = runs[("strict", m)]
        assert r["door"]["kind"] == "DOOR" and "door_fit_review" not in r["door"]
        assert [x["measured_net"] for x in _code(r, "DOOR.EXTERNAL.ALUMINIUM")] == ["1"]
        assert [x["evidence_state"] for x in _code(r, "FIN.WP.DOORWAY")] == ["SOURCE_DERIVED"]


@pytest.mark.parametrize("name,why", [("hinge_035", "hinge 0.350 m from the jamb (strict 0.30 m)"),
                                      ("leaf_069", "leaf 0.690 m = 69 % of the 1.000 m opening")])
def test_a_review_fit_makes_a_held_door(runs, name, why):
    old, new = runs[(name, "2.5")], runs[(name, "2.6")]
    assert old["door"]["kind"] == "PASSAGE" and new["door"]["kind"] == "DOOR"
    assert why in new["door"]["door_fit_review"]
    el = next(e for e in new["doors"]["elements"] if e.get("fit_review"))
    assert el["state"] == "CONFIRMED" and el["released"] is False and el["section"] == "PROVISIONAL_NOT_RELEASED"
    assert any(f["code"] == "DOOR_SYMBOL_FIT_REVIEW" for f in new["doors"]["findings"])
    assert not _code(new, "DOOR.EXTERNAL.ALUMINIUM") and not _code(new, "DOOR.INTERNAL.PVC")
    w = new["door"]["width_m"]
    # the doorway piece exists now: door width x wall thickness 0.20 m - PROVISIONAL while the door is held
    wp = _code(new, "FIN.WP.DOORWAY")
    assert [round(float(x["measured_net"]), 6) for x in wp] == [round(w * 0.2, 6)]
    assert [x["evidence_state"] for x in wp] == ["PROVISIONAL"] and "DOOR_SYMBOL_FIT_REVIEW" in wp[0]["notes"]
    assert not _code(old, "FIN.WP.DOORWAY")
    thr = _code(new, "FIN.MARBLE.THRESHOLD")
    assert [x["evidence_state"] for x in thr] == ["PROVISIONAL"]
    # the floor never changes: 4.00 x 3.00 m
    assert [round(r["area_m2"], 6) for r in new["rooms"]] == [round(r["area_m2"], 6) for r in old["rooms"]] == [12.0]
    assert new["run"]["v2_6"]["door_reconciliation"]["reconciled"] == [f"GF:{new['door']['opening_id']}"]


def test_beyond_the_limits_a_passage_with_a_note(runs):
    old, new = runs[("hinge_050", "2.5")], runs[("hinge_050", "2.6")]
    assert old["door"]["kind"] == new["door"]["kind"] == "PASSAGE"
    assert new["door"]["door_symbol_note"]["hinge_from_jamb_m"] == 0.5 and "door_symbol_note" not in old["door"]
    assert new["run"]["v2_6"]["door_reconciliation"]["noted"] == [f"GF:{new['door']['opening_id']}"]
