"""T-606 R-T606-1 room outline causes: a non-Alsenan drawn fixture (villa K606: four rooms, one doorless arch jamb,
one tiled wet face, a column notch, a rounded corner, a stair opening) read from a DXF written by ezdxf (plain, rotated
and mirrored, mm and m), the rule's adverse cases, and the Alsenan rebuild (byte-identical, no private input)."""
from __future__ import annotations

import importlib.util
import json
import math
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t606"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))
import t606_rules as R  # noqa: E402

D = Decimal


def _load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ------------------------------------------------------------------ drawn fixture K606 (not Alsenan), metres
# room A 5.00 x 4.00 (0..5, 0..4); arch 1.00 in the 0.20 wall at x 5.00..5.20 to room B (y 1.00..2.00), doorless
# room B 4.00 x 4.00 (5.20..9.20, 0..4), WET (tiled), column 0.40 x 0.30 protruding 0.05 into B on its south face
# hall C 6.00 x 3.00 (0..6, 4.20..7.20) with a stair opening 2.00 x 1.50 in its SE corner (4..6 x 4.20..5.70)
# room D 4.00 x 3.00 (10..14, 0..3) with an R1.00 rounded NE corner
def _fixture(path, rot_deg=0.0, mirror=False, scale=1000.0):
    import ezdxf

    th = math.radians(rot_deg)

    def P(x, y):
        x = -x if mirror else x
        return ((x * math.cos(th) - y * math.sin(th)) * scale, (x * math.sin(th) + y * math.cos(th)) * scale)

    doc = ezdxf.new()
    doc.header["$INSUNITS"] = 4 if scale == 1000.0 else 6
    m = doc.modelspace()
    H = {}

    def L(name, a, b, layer="1"):
        H[name] = m.add_line(P(*a), P(*b), dxfattribs={"layer": layer}).dxf.handle

    # room A
    L("A_s", (0, 0), (5, 0)); L("A_e1", (5, 0), (5, 1)); L("A_e2", (5, 2), (5, 4)); L("A_n", (5, 4), (0, 4))
    L("A_w", (0, 4), (0, 0))
    # room B
    L("B_s", (5.2, 0), (9.2, 0)); L("B_e", (9.2, 0), (9.2, 4)); L("B_n", (9.2, 4), (5.2, 4))
    L("B_w1", (5.2, 4), (5.2, 2)); L("B_w2", (5.2, 1), (5.2, 0))
    col = [P(6.8, -0.25), P(7.2, -0.25), P(7.2, 0.05), P(6.8, 0.05)]
    m.add_lwpolyline(col, close=True, dxfattribs={"layer": "S-COL.BON"})
    # hall C, walls and the stair-opening edges (layer 5)
    L("C_s", (0, 4.2), (6, 4.2)); L("C_e", (6, 4.2), (6, 7.2)); L("C_n", (6, 7.2), (0, 7.2)); L("C_w", (0, 7.2), (0, 4.2))
    L("V_n", (4, 5.7), (6, 5.7), "5"); L("V_w", (4, 5.7), (4, 4.2), "5")
    # room D with the rounded corner (centre 13, 2, r 1)
    L("D_s", (10, 0), (14, 0)); L("D_e", (14, 0), (14, 2)); L("D_n", (13, 3), (10, 3)); L("D_w", (10, 3), (10, 0))
    c = P(13, 2)
    # arc from 0 to 90 deg in the fixture frame -> rotate / mirror the angles
    def ang(dx, dy):
        q = P(13 + dx, 2 + dy)
        return math.degrees(math.atan2(q[1] - c[1], q[0] - c[0])) % 360.0
    s, e = ang(1, 0), ang(0, 1)
    if mirror:
        s, e = e, s
    H["D_arc"] = m.add_arc(c, 1.0 * scale, s, e, dxfattribs={"layer": "1"}).dxf.handle
    doc.saveas(path)
    return H, col


def _read(path):
    import ezdxf

    ex = _load("t606_extract")
    doc = ezdxf.readfile(path)
    geom, _ = ex._segs(doc.modelspace())
    cols = [[(q[0], q[1]) for q in e.get_points()] for e in doc.modelspace().query("LWPOLYLINE")]
    return geom, cols


CASES = [(0.0, False, 1000.0), (37.0, False, 1000.0), (90.0, True, 1000.0), (211.0, True, 1000.0), (37.0, False, 1.0)]


@pytest.mark.parametrize("rot,mir,scale", CASES)
def test_fixture_outlines_by_handle(tmp_path, rot, mir, scale):
    H, _ = _fixture(tmp_path / "k606.dxf", rot, mir, scale)
    geom, cols = _read(tmp_path / "k606.dxf")
    u = 0.001 if scale == 1000.0 else 1.0
    W = "WALL"
    a = R.outline(geom, [(H["A_s"], W), (H["A_e1"], W), (H["A_n"], W), (H["A_w"], W)], cols, unit_m=u)
    assert (a["perimeter"], a["area"]) == (D("18.0"), D("20.0"))
    b = R.outline(geom, [(H["B_s"], W), (H["B_e"], W), (H["B_n"], W), (H["B_w1"], W)], cols, unit_m=u)
    assert b["notch_lm"] == D("0.1") and b["perimeter"] == D("16.1") and b["area"] == D("15.98")
    walls = R.outline(geom, [(H["C_s"], W), (H["C_e"], W), (H["C_n"], W), (H["C_w"], W)], cols, unit_m=u)
    edge = R.outline(geom, [(H["C_s"], W), (H["V_w"], "VOID_EDGE"), (H["V_n"], "VOID_EDGE"), (H["C_e"], W),
                            (H["C_n"], W), (H["C_w"], W)], cols, unit_m=u)
    # a rectangular corner cut changes no perimeter: the walls along the opening are a NET question (F-T606-1 kind)
    assert walls["perimeter"] == edge["perimeter"] == D("18.0")
    assert D(walls["wall_lm"]) - D(edge["wall_lm"]) == D("3.5") and edge["virtual_lm"] == D("3.5")
    assert edge["area"] == D("15.0")
    d = R.outline(geom, [(H["D_s"], W), (H["D_e"], W), (H["D_arc"], W), (H["D_n"], W), (H["D_w"], W)], cols, unit_m=u)
    assert d["perimeter"] == R.q6(12.0 + math.pi / 2)
    assert abs(float(d["area"]) - (12.0 - 1.0 + math.pi / 4)) < 2e-4


def test_his_reading_established_ambiguous_and_boundary():
    # room A with the arch reveal returns of its doorless opening (2 x 0.20 depth, 1.00 x 0.20 strip)
    st, both, p, a = R.match_reading(D("18.40"), D("20.20"), {"walls": (D("18"), D("20"))},
                                     {"arch reveals": (D("0.40"), D("0.20")), "other": (D("0.30"), D("0.15"))})
    assert st == "ESTABLISHED" and both[0]["addons"] == ["arch reveals"]
    st, both, _, _ = R.match_reading(D("18.40"), D("20.20"), {"walls": (D("18"), D("20"))},
                                     {"door x": (D("0.40"), D("0.20")), "door y": (D("0.40"), D("0.20"))})
    assert st == "AMBIGUOUS" and len(both) == 2
    # adverse: a reading ON the rounding boundary (7.705 for a typed 7.70) is not a reproduction
    st, both, p, a = R.match_reading(D("13.60"), D("7.70"), {"ours": (D("12.9"), D("7.375"))},
                                     {"m": (D("0.4"), D("0.18")), "r": (D("0.3"), D("0.15"))})
    assert st == "NOT_ESTABLISHED" and p and p[0]["A"] == "7.705"
    # perimeter alone never establishes a reading
    st, both, p, a = R.match_reading(D("18.40"), D("25.00"), {"walls": (D("18"), D("20"))},
                                     {"arch reveals": (D("0.40"), D("0.20"))})
    assert st == "NOT_ESTABLISHED" and len(p) == 1


def test_close_room_exact_and_refusals():
    r = R.close_room(D("18.0"), D("18.9"), [{"id": "jamb", "lm": "-0.40", "verdict": "RULE_DIFFERENCE",
                                              "edges": ["A_e1"]}])
    assert D(r["gap"]) == D("-0.9") and D(r["unresolved"]) == D("-0.5")
    assert sum(D(c["lm"]) for c in r["causes"]) == D("-0.9")
    assert r["causes"][-1]["verdict"] == "UNRESOLVED"
    closed = R.close_room(D("18.0"), D("18.4"), [{"id": "jamb", "lm": "-0.40", "verdict": "RULE_DIFFERENCE"}])
    assert D(closed["unresolved"]) == 0 and all(c["verdict"] != "UNRESOLVED" for c in closed["causes"])
    with pytest.raises(R.RuleError, match="counted twice"):
        R.close_room(D("18"), D("19"), [{"id": "a", "lm": "-0.4", "verdict": "RULE_DIFFERENCE"},
                                        {"id": "a", "lm": "-0.4", "verdict": "RULE_DIFFERENCE"}])
    with pytest.raises(R.RuleError, match="counted twice"):
        R.close_room(D("18"), D("19"), [{"id": "a", "lm": "-0.4", "verdict": "RULE_DIFFERENCE", "edges": ["h1"]},
                                        {"id": "b", "lm": "-0.2", "verdict": "ENGINE_RIGHT", "edges": ["h1"]}])
    with pytest.raises(R.RuleError, match="typed"):
        R.close_room(D("18"), D("19"), [{"id": "r", "lm": "0", "verdict": "UNRESOLVED", "residual": True}])
    with pytest.raises(R.RuleError, match="unknown"):
        R.close_room(D("18"), D("19"), [{"id": "x", "lm": "-1", "verdict": "VERIFIED"}])


def test_gross_vs_net_and_tiled_face_refused():
    assert R.check_ours("18.0", "18.0002") == D("-0.0002")
    with pytest.raises(R.RuleError, match="gross vs net"):
        R.check_ours("18.0", "17.6", kind="NET")
    with pytest.raises(R.RuleError, match="not ours"):
        R.check_ours("18.0", "17.6")
    assert R.skirt_face("DRY", "WALL") is True
    assert R.skirt_face("DRY", "VOID_EDGE") is False
    with pytest.raises(R.RuleError, match="tiled face skirted"):
        R.skirt_face("TILED", "WALL")          # room B is wet: its faces never take skirting
    with pytest.raises(R.RuleError, match="HELD"):
        R.skirt_face(None, "WALL")


def test_outline_refusals(tmp_path):
    H, _ = _fixture(tmp_path / "k.dxf")
    geom, cols = _read(tmp_path / "k.dxf")
    with pytest.raises(R.RuleError, match="parallel"):
        R.outline(geom, [(H["A_s"], "WALL"), (H["C_s"], "WALL"), (H["A_w"], "WALL")])
    with pytest.raises(R.RuleError, match="not in the drawing"):
        R.outline(geom, [(H["A_s"], "WALL"), ("ZZZ", "WALL"), (H["A_w"], "WALL")])
    with pytest.raises(R.RuleError, match="role"):
        R.outline(geom, [(H["A_s"], "WALL"), (H["A_e1"], "RAIL"), (H["A_n"], "WALL"), (H["A_w"], "WALL")])
    with pytest.raises(R.RuleError, match="at least 3"):
        R.outline(geom, [(H["A_s"], "WALL"), (H["A_e1"], "WALL")])


# ------------------------------------------------------------------ Alsenan rebuild (committed data only)
def test_alsenan_rebuild_byte_identical():
    b = _load("t606_alsenan")
    assert b.main(["--check"]) == 0


def test_alsenan_split_and_finding():
    d = json.loads((HERE / "out" / "T606_OUTLINE_CAUSES.json").read_text())
    assert d["t574_unresolved"] == "-9.693234"
    assert D(d["split"]["named"]) + D(d["split"]["unresolved"]) == D("-9.693234")
    assert len(d["remeasured"]) >= 8 and all(D(r["diff"]).copy_abs() <= D("0.0005") for r in d["remeasured"])
    liv = next(r for r in d["rooms"] if r["room"].startswith("1F living"))
    assert [(c["id"], c["lm"]) for c in liv["causes"]] == [("LIV-WELL", "8.40"), ("LIV-VOID", "0.20"),
                                                           ("residual", "0.06")]
    assert d["finding"]["lm"] == "11.22" and d["finding"]["verdict_proposal"] == "ENGINE_WRONG"
    for r in d["rooms"]:
        assert sum(D(c["lm"]) for c in r["causes"]) == D(r["gap"])
        if "reading_test" in r:
            assert r["reading_test"]["status"] == "NOT_ESTABLISHED"


def test_drawn_json_has_no_coordinates():
    d = json.loads((HERE / "T606_DRAWN.json").read_text())
    keys = set()

    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                keys.add(k)
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(d)
    assert not keys & {"x", "y", "points", "coords", "start", "end", "centre", "center"}
