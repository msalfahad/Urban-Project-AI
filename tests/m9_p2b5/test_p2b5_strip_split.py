"""Phase 2B-5 (ARCH_TAKEOFF_V2.6, correction D-V26-07): doorway strips split at the opening boxes (finding D-C2 of
the real-room verification). The expected results come from the fixture geometry by hand, never from the engine:

    a doorway face that runs on past its door's jamb into the wall band - the jamb drawn only with the door symbol,
    the wall's face pieces beside it too short to make a wall band (no wall cap), a wall junction beyond - is split:
        the door's box             width x wall thickness  -> the threshold (UP-THR-001, as any other doorway)
        the rest of the face       (face - boxes)          -> WALL_BAND_REMAINDER, a BLOCKED_RFI strip, no quantity
    only when the face's own boundary proves the reading: its threshold edges are both faces of its openings
    (2 x the sum of the widths), every other edge is a WALL line, the face is no wider across than the wall, the
    openings are on one wall line and the face covers each box whole.

V2.5 (and every earlier method) never splits: the same drawing keeps one unattributed strip there."""

from __future__ import annotations

import csv
import json
import math
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests" / "m9_p2b5_bench"))

from engine.source import arch_completeness as AC             # noqa: E402

ezdxf = pytest.importorskip("ezdxf")

U = 0.001                                                     # drawing mm
T = 150.0                                                     # wall thickness (mm)


def _rot(p, deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return (p[0] * c - p[1] * s, p[0] * s + p[1] * c)


def _op(oid, s0, s1, kind="DOOR", deg=0.0, t=T):
    return {"opening_id": oid, "kind": kind, "s0": s0, "s1": s1, "o0": 0.0, "o1": t, "u": _rot((1.0, 0.0), deg),
            "n": _rot((0.0, 1.0), deg), "width_m": (s1 - s0) * U, "wall_t_m": t * U}


def _plan(ops, poly, roles, deg=0.0):
    """one DOORWAY face (polygon in the wall's frame, turned by deg) bounded by its openings' thresholds."""
    pts = [_rot(p, deg) for p in poly]
    a = abs(sum(pts[i - 1][0] * pts[i][1] - pts[i][0] * pts[i - 1][1] for i in range(len(pts)))) / 2 * U * U
    face = {"face_id": "F1", "class": "DOORWAY", "opening_ids": [o["opening_id"] for o in ops], "closure_ids": [],
            "outer_role_lm": roles, "area_m2": a, "polygon": pts}
    return {"unit_m": U, "faces": [face], "openings_by_id": {o["opening_id"]: o for o in ops}}


def _split(S):
    strips = AC.strip_register(S, "GF")
    return AC.split_strips(S, strips, "GF")


# two 0.80 m doors and the 0.2383 m wall between them (the real W.C. pair): face 1.8383 x 0.15 m
NIB = [(0.0, 0.0), (1838.3, 0.0), (1838.3, T), (0.0, T)]
NIB_ROLES = {"DOOR_THRESHOLD": 3.2, "WALL": round(2 * 0.2383 + 2 * 0.15, 4)}


@pytest.mark.parametrize("deg", [0.0, 45.0, 117.0])
def test_two_doors_and_the_wall_between_them(deg):
    ops = [_op("OP-A", 0.0, 800.0, deg=deg), _op("OP-B", 1038.3, 1838.3, deg=deg)]
    out, recs = _split(_plan(ops, NIB, NIB_ROLES, deg))
    by = {(tuple(s["opening_ids"]), s["class"]): s for s in out}
    # hand: each door 0.80 x 0.15 = 0.12 m2; between them 0.2383 x 0.15 = 0.035745 m2; the face 0.275745 m2
    assert by[(("OP-A",), "THRESHOLD")]["area_m2"] == pytest.approx(0.12, abs=1e-6)
    assert by[(("OP-B",), "THRESHOLD")]["area_m2"] == pytest.approx(0.12, abs=1e-6)
    rem = by[((), "UNATTRIBUTED")]
    assert rem["area_m2"] == pytest.approx(0.035745, abs=1e-6)
    assert rem["question"].startswith("WALL_BAND_REMAINDER") and rem["beside_openings"] == ["OP-A", "OP-B"]
    assert sum(s["area_m2"] for s in out) == pytest.approx(0.275745, abs=1e-6)        # conserved
    for oid in ("OP-A", "OP-B"):
        s = by[((oid,), "THRESHOLD")]
        assert s["geometry_verified"] and s["geometry"]["failed_checks"] == [] and s["split_from"]["rule"] == "D-V26-07"
        assert s["geometry"]["depth_m"] == pytest.approx(0.15, abs=1e-6)
        # the piece's polygon is the door's box, back in the drawing frame (0.1 mm rounding)
        o = ops[0] if oid == "OP-A" else ops[1]
        (ux, uy), (nx, ny) = o["u"], o["n"]
        loc = [((x * ux + y * uy) / U, (x * nx + y * ny) / U) for x, y in s["polygon_m"]]
        assert all(o["s0"] - 0.5 <= a <= o["s1"] + 0.5 and -0.5 <= b <= T + 0.5 for a, b in loc)
        assert min(a for a, _ in loc) == pytest.approx(o["s0"], abs=0.5)
        assert max(a for a, _ in loc) == pytest.approx(o["s1"], abs=0.5)
    assert recs == [{"floor": "GF", "strip_id": "F1", "openings": ["OP-A", "OP-B"], "face_m2": round(0.275745, 6),
                     "split": True, "pieces_m2": {"OP-A": 0.12, "OP-B": 0.12}, "remainder_m2": 0.035745}]


def test_a_door_and_a_passage_split_each_into_its_own_kind():
    ops = [_op("OP-A", 0.0, 800.0), _op("OP-B", 1038.3, 1838.3, kind="PASSAGE")]
    roles = {"DOOR_THRESHOLD": 1.6, "PASSAGE_THRESHOLD": 1.6, "WALL": NIB_ROLES["WALL"]}
    out, recs = _split(_plan(ops, NIB, roles))
    assert recs[0]["split"] is True
    assert sorted((s["opening_ids"], s["opening_kinds"]) for s in out if s["class"] == "THRESHOLD") == \
        [(["OP-A"], ["DOOR"]), (["OP-B"], ["PASSAGE"])]


@pytest.mark.parametrize("name,ops,poly,roles,reason", [
    ("a column bounds it", [_op("OP-A", 0.0, 800.0), _op("OP-B", 1038.3, 1838.3)], NIB,
     {"DOOR_THRESHOLD": 3.2, "WALL": 0.6266, "COLUMN": 0.15}, "bounded by COLUMN"),
    ("thresholds on one face only", [_op("OP-A", 0.0, 800.0), _op("OP-B", 1038.3, 1838.3)], NIB,
     {"DOOR_THRESHOLD": 1.6, "WALL": 2.3766}, "its threshold edges are not both faces of its openings"),
    ("wider across than the wall", [_op("OP-A", 0.0, 800.0)], [(0, 0), (1027, 0), (1027, 200), (0, 200)],
     {"DOOR_THRESHOLD": 1.6, "WALL": 0.854}, "wider across than the wall"),
    ("a notch in the door's box", [_op("OP-A", 0.0, 800.0)],
     [(0, 0), (1027, 0), (1027, T), (400, T), (400, 100), (300, 100), (300, T), (0, T)],
     {"DOOR_THRESHOLD": 1.6, "WALL": 0.854}, "it does not cover the box of OP-A"),
    ("openings on two wall lines", [_op("OP-A", 0.0, 800.0), _op("OP-B", 1038.3, 1838.3, deg=90.0)], NIB,
     NIB_ROLES, "its openings are not on one wall line"),
])
def test_what_is_not_split(name, ops, poly, roles, reason):
    S = _plan(ops, poly, roles)
    strips = AC.strip_register(S, "GF")
    out, recs = AC.split_strips(S, strips, "GF")
    assert out == strips                                      # unchanged, one unattributed strip
    assert [r["split"] for r in recs] == [False] and recs[0]["reason"] == reason


def test_a_strip_that_fits_its_box_and_a_window_are_never_candidates():
    door = _plan([_op("OP-A", 0.0, 800.0)], [(0, 0), (800, 0), (800, T), (0, T)], {"DOOR_THRESHOLD": 1.6, "WALL": 0.3})
    win = _plan([_op("OP-W", 0.0, 800.0, kind="WINDOW")], [(0, 0), (1027, 0), (1027, T), (0, T)],
                {"WINDOW_THRESHOLD": 1.6, "WALL": 0.754})
    for S in (door, win):
        strips = AC.strip_register(S, "GF")
        assert AC.split_strips(S, strips, "GF") == (strips, [])


# ---- the doorway piece of a door closed by its leaf (closure A) and the wall's other face (closure B) -------------

def _leaf_face(poly, roles, a=((0.0, 0.0), (800.0, 0.0)), b=((800.0, T), (0.0, T)), deg=0.0):
    pts = [_rot(p, deg) for p in poly]
    area = abs(sum(pts[i - 1][0] * pts[i][1] - pts[i][0] * pts[i - 1][1] for i in range(len(pts)))) / 2 * U * U
    rep = [{"kind": "DOOR_CLOSURE", "id": "CLOSURE|D", "a": _rot(a[0], deg), "b": _rot(a[1], deg)},
           {"kind": "DOOR_CLOSURE", "id": "CLOSURE|D|B", "a": _rot(b[0], deg), "b": _rot(b[1], deg)}]
    return {"face_id": "F1", "closure_ids": ["CLOSURE|D", "CLOSURE|D|B"], "outer_role_lm": roles, "area_m2": area,
            "polygon": pts}, rep


LEAF = [(0.0, 0.0), (1027.0, 0.0), (1027.0, T), (0.0, T)]
LEAF_ROLES = {"DOOR_CLOSURE": 1.6, "WALL": round(2 * 0.227 + 2 * 0.15, 4)}


@pytest.mark.parametrize("deg", [0.0, 45.0, 200.0])
def test_a_leaf_closed_doorway_piece_is_the_box_between_its_closures(deg):
    f, rep = _leaf_face(LEAF, LEAF_ROLES, deg=deg)
    # hand: 0.80 x 0.15 = 0.12 m2 between the closures; 0.227 x 0.15 = 0.03405 m2 beyond them
    assert AC.closure_box(f, rep, U) == (0.12, 0.03405, 0.15)


@pytest.mark.parametrize("poly,roles,kw,reason", [
    (LEAF, {"DOOR_CLOSURE": 1.6, "WALL": 0.604, "COLUMN": 0.15}, {}, "bounded by COLUMN"),
    (LEAF, {"DOOR_CLOSURE": 0.8, "WALL": 1.554}, {}, "its closure edges are not the two closures"),
    (LEAF, LEAF_ROLES, {"b": ((800.0, T), (0.0, T + 40.0))}, "its closures are not parallel"),
    ([(0, 0), (1027, 0), (1027, 200), (0, 200)], LEAF_ROLES, {}, "wider across than the wall"),
    ([(0, 0), (1027, 0), (1027, T), (400, T), (400, 100), (300, 100), (300, T), (0, T)], LEAF_ROLES, {},
     "it does not cover the box between its closures"),
    ([(0, 0), (800, 0), (800, T), (0, T)], {"DOOR_CLOSURE": 1.6, "WALL": 0.3}, {}, "nothing lies beyond the closures"),
])
def test_what_keeps_its_whole_face(poly, roles, kw, reason):
    f, rep = _leaf_face(poly, roles, **kw)
    assert AC.closure_box(f, rep, U) == reason
    f["closure_ids"] = f["closure_ids"][:1]
    assert AC.closure_box(f, rep, U) == "not closed by two closures"


# ---- through the command line: V2.5 against V2.6 on the same drawing ------------------------------------------------

DECLARED = ("A-WALL=WALL", "A-COL=COLUMN", "A-GLAZ=WINDOW", "A-DOOR=DOOR")


def _drawing(path, junction, door_jambs=True):
    """B01 of the room-reader benchmark (a 4.00 x 3.00 m bathroom, 0.20 m walls, a 0.80 m door in the south wall
    at x 1.00 - 1.80 m). junction: the door's east jamb is drawn only with the door symbol (A-DOOR); beyond it the
    outer face runs 77 mm and then meets a perpendicular wall (x 1.877 - 2.027 m, going 2.45 m south, closed),
    after which the outer face resumes - the real plan's pattern. door_jambs=False: no jamb line at x 1.80 m on any
    layer, so the door is not a band opening and is closed by its leaf (closure A) and the other face (closure B)."""
    import bench_cases as BC
    import bench_drawings as BD
    BD.dxf(dict(BC.BY_ID["B01"]), path)
    doc = ezdxf.readfile(str(path))
    msp = doc.modelspace()
    for e in msp.query("INSERT[layer=='A-DOOR']"):
        e.dxf.xscale = e.dxf.yscale = 0.8
    if junction:
        for e in list(msp.query("LINE[layer=='A-WALL']")):
            a, b = e.dxf.start, e.dxf.end
            if (a.x, a.y, b.x, b.y) in ((1800, 0, 1800, 200), (1800, 0, 4400, 0)):
                msp.delete_entity(e)
        W = {"layer": "A-WALL"}
        for a, b in (((1800, 0), (1877, 0)), ((2027, 0), (4400, 0)), ((1877, 0), (1877, -2450)),
                     ((2027, 0), (2027, -2450)), ((1877, -2450), (2027, -2450))):
            msp.add_line(a, b, dxfattribs=W)
        for x in ((1000, 1800) if door_jambs else ()):
            msp.add_line((x, 0), (x, 200), dxfattribs={"layer": "A-DOOR"})
    doc.saveas(str(path))
    return path


def _run(dxf, out, method):
    r = subprocess.run([sys.executable, "-I", str(ROOT / "tools" / "urban_boq_m9.py"), "arch", "--drawings", str(dxf),
                        "--out", str(out), "--method", method, "--layer-roles", *DECLARED],
                       capture_output=True, text=True, cwd=str(out.parent))
    assert r.returncode == 0, r.stderr[-2000:]
    rd = lambda n: json.loads((out / n).read_text(encoding="utf-8"))          # noqa: E731
    return {"lines": list(csv.DictReader((out / "BOQ_LINES.csv").open(encoding="utf-8"))),
            "json_lines": rd("BOQ_LINES.json"), "floors": rd("ARCH_FLOOR_AREAS.json"),
            "unresolved": rd("UNRESOLVED.json"), "run": rd("RUN_RULES.json")["arch"]}


def _floor(res):
    fa = res["floors"]
    return (fa["floors"] if "floors" in fa else fa)[0]


@pytest.fixture(scope="module")
def runs(tmp_path_factory):
    base = tmp_path_factory.mktemp("stripsplit")
    out = {}
    for name, junction, jambs in (("plain", False, True), ("junction", True, True), ("leaf", True, False)):
        dxf = _drawing(base / f"{name}.dxf", junction, jambs)
        for m in ("ARCH_TAKEOFF_V2.5", "ARCH_TAKEOFF_V2.6"):
            out[(name, m[-3:])] = _run(dxf, base / f"{name}_{m[-3:]}", m)
    return out


def _codes(res, code):
    return [x for x in res["lines"] if x["item_code"] == code]


def test_v25_withholds_the_whole_face(runs):
    old = runs[("junction", "2.5")]
    assert not _codes(old, "FIN.MARBLE.THRESHOLD")
    [s] = [s for s in _floor(old)["strips"] if s["class"] != "WINDOW_REVEAL"]
    # hand: the door's box 0.80 x 0.20 + the 77 mm return and the 150 mm junction x 0.20 = 0.2054 m2
    assert s["area_m2"] == pytest.approx(0.2054, abs=1e-6) and s["class"] == "UNATTRIBUTED"
    assert set(s["geometry"]["failed_checks"]) == {"OUTSIDE_OPENING_BOX", "DEPTH_OVER_WALL"}
    assert s["bounded_by_lm"] == {"DOOR_THRESHOLD": 1.6, "WALL": pytest.approx(0.2 + 0.077 + 0.15 + 0.227 + 0.2)}
    assert "strip_split" not in _floor(old) and "strip_split" not in (old["run"].get("v2_6") or {})


def test_v26_takes_the_door_box_and_leaves_the_wall(runs):
    new = runs[("junction", "2.6")]
    [thr] = _codes(new, "FIN.MARBLE.THRESHOLD")
    assert float(thr["measured_net"]) == pytest.approx(0.16, abs=1e-6)              # 0.80 x 0.20
    # the rule's own state for an external doorway (UP-THR-001): PROVISIONAL, with the split named
    assert thr["evidence_state"] == "PROVISIONAL" and "STRIP_SPLIT_AT_OPENING_BOX (D-V26-07)" in thr["notes"]
    [j] = [x for x in new["json_lines"] if x["item_code"] == "FIN.MARBLE.THRESHOLD"]
    assert j["calculation"]["inputs"]["split_from"]["remainder_m2"] == pytest.approx(0.0454, abs=1e-6)
    rest = [x for x in new["lines"] if x["item_code"] == "ARCH.THRESHOLD"]
    assert len(rest) == 1 and rest[0]["measured_net"] == "" and rest[0]["evidence_state"] == "BLOCKED_RFI"
    [u] = [x for x in new["unresolved"]["unresolved"] if x["reason"].startswith("WALL_BAND_REMAINDER")]
    assert u["cause"] == "SOURCE" and u["module_function"] == "arch_completeness.split_strips"
    assert "[0.045 m2]" in u["reason"]
    assert _floor(new)["strip_split"] == [{"face_m2": 0.2054, "floor": "GF", "openings": ["OP-001"],
                                           "pieces_m2": {"OP-001": 0.16}, "remainder_m2": 0.0454, "split": True,
                                           "strip_id": _floor(new)["strip_split"][0]["strip_id"]}]
    assert new["run"]["v2_6"]["strip_split"]["split"] == ["GF:OP-001"]
    assert any(c.startswith("D-V26-07") for c in new["run"]["v2_6"]["corrections"])


def test_the_face_floor_and_coverage_do_not_change(runs):
    old, new = runs[("junction", "2.5")], runs[("junction", "2.6")]
    for k in ("internal_physical_floor_m2", "gross_floor_plate_m2"):
        assert _floor(new)[k] == _floor(old)[k]
    assert [s["area_m2"] for s in _floor(new)["strips"]] == [s["area_m2"] for s in _floor(old)["strips"]]
    assert [float(x["measured_net"]) for x in _codes(new, "FIN.WP.FLOOR")] == [12.0]
    assert _floor(new)["coverage"] == _floor(old)["coverage"]                       # gate, nothing unaccounted
    assert _floor(new)["coverage"]["unaccounted"] == 0


def test_a_door_with_its_jambs_drawn_is_the_same_in_both_methods(runs):
    old, new = runs[("plain", "2.5")], runs[("plain", "2.6")]
    key = lambda r: [(x["item_code"], x["room_id"], x["measured_net"], x["evidence_state"]) for x in r["lines"]  # noqa: E731
                     if "THRESHOLD" in x["item_code"] or x["item_code"] == "FIN.WP.DOORWAY"]
    assert key(new) == key(old) and [x[2] for x in key(new) if x[0] == "FIN.MARBLE.THRESHOLD"] == ["0.16"]
    assert _floor(new)["strip_split"] == []


def test_a_leaf_closed_door_takes_the_box_between_its_closures(runs):
    old, new = runs[("leaf", "2.5")], runs[("leaf", "2.6")]
    # V2.5 takes the whole face for the doorway piece: 0.2054 m2 (the door's 0.16 m2 + 0.0454 m2 of wall, +28 %)
    assert [float(x["measured_net"]) for x in _codes(old, "FIN.WP.DOORWAY")] == [pytest.approx(0.2054, abs=1e-6)]
    [wp] = _codes(new, "FIN.WP.DOORWAY")
    assert float(wp["measured_net"]) == pytest.approx(0.16, abs=1e-6) and wp["evidence_state"] == "SOURCE_DERIVED"
    assert "STRIP_SPLIT_AT_OPENING_BOX (D-V26-07)" in wp["notes"]
    [j] = [x for x in new["json_lines"] if x["item_code"] == "FIN.WP.DOORWAY"]
    assert j["calculation"]["inputs"]["face_m2"] == pytest.approx(0.2054, abs=1e-6)
    assert j["calculation"]["inputs"]["remainder_m2"] == pytest.approx(0.0454, abs=1e-6)
    assert j["calculation"]["inputs"]["depth_m"] == pytest.approx(0.2, abs=1e-6)
    [rec] = new["run"]["v2_6"]["strip_split"]["doorway_pieces"]
    assert rec["split"] is True and rec["box_m2"] == pytest.approx(0.16) and rec["face_m2"] == pytest.approx(0.2054)
    # the threshold of a leaf-closed door stays withheld (its opening is not established): unchanged by D-V26-07
    assert not _codes(new, "FIN.MARBLE.THRESHOLD") and not _codes(old, "FIN.MARBLE.THRESHOLD")
    assert [float(x["measured_net"]) for x in _codes(new, "FIN.WP.FLOOR")] == [12.0]
