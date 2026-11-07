"""T-612 / R-T612-1: gross-outline residual by cause (research rule, unwired).

Villa K612 (synthetic, not Alsenan): an open room 12.00 x 8.00 m whose east side is a curved glazing (circle r 5.00,
centre 3.00 west of the east wall) that the room uses only in part (the glazing continues past the north wall), a
boundary column on the south wall (notch), an interior column (solid), a zone line 1.50 north of the south wall (the
'engine face'), two passages in the north wall with 0.20 reveals. Hand calculation (m):
  drawn outline  P = 12 + 1 + arc + 13 + 8 + notch 0.20; arc = 5 x 90 deg = 7.853982 (from -53.130102 to 36.869898 deg)
                 A = 96 + 31.634954 - 21 (circle strip 12.00 .. arc, y 1 .. 8) - column notch 0.06 = 106.574954
  face (zone)    P = 12.570714 + 5 x 81.296924 deg + 13 + 6.5; the arc from asin(-0.7) to asin(0.6)
Written by ezdxf in a temporary folder, read back at 0 / 37 / 90 / 211 deg, mirrored, in mm and m.
"""
from __future__ import annotations

import math
import sys
from decimal import Decimal as D
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research" / "agents_t612"))
sys.path.insert(0, str(ROOT / "research" / "agents_t606"))
import t612_rules as R  # noqa: E402
import t612_extract as X  # noqa: E402
import t606_rules as R6  # noqa: E402

ezdxf = pytest.importorskip("ezdxf")

ARC_LEN = 5 * math.pi / 2
ARC_FACE = 5 * math.radians(math.degrees(math.asin(0.6)) - math.degrees(math.asin(-0.7)))
FACE_S = 9 + math.sqrt(25 - 3.5 ** 2)          # zone line from x 0 to the arc at y 1.5
P_FULL = 12 + 1 + ARC_LEN + 13 + 8 + 0.2
A_FULL = 96 + 31.634954 - 21 - 0.06
P_FACE = FACE_S + ARC_FACE + 13 + 6.5


def _xf(k, ang, mirror, s):
    c, si = math.cos(math.radians(ang)), math.sin(math.radians(ang))

    def f(x, y):
        x = -x if mirror else x
        return ((x * c - y * si) * s + 1234.5 * s, (x * si + y * c) * s - 987.0 * s)
    return f


def _build(tmp, ang=0, mirror=False, unit="mm"):
    s = 1000.0 if unit == "mm" else 1.0
    f = _xf(None, ang, mirror, s)
    doc = ezdxf.new()
    doc.header["$INSUNITS"] = 4 if unit == "mm" else 6
    m = doc.modelspace()
    h = {}

    def line(name, a, b):
        e = m.add_line(f(*a), f(*b), dxfattribs={"layer": "1"})
        h[name] = e.dxf.handle

    line("S", (0, 0), (12, 0))
    line("E1", (12, 0), (12, 1))
    line("N", (6.5, 8), (13, 8))
    line("Nw", (0, 8), (2, 8))                      # north wall west of the passages (not in the chain)
    line("W", (0, 0), (0, 8))
    line("Z", (9.5, 1.5), (12.6, 1.5))               # zone line (drawn piece; its infinite line is used)
    line("J1", (2, 8), (2, 8.2))                     # passage 1 jamb + far face
    line("F1", (2, 8.2), (3, 8.2))
    line("J2", (3, 8), (3, 8.2))
    # curved glazing: ccw from (12, 1) to (5, 8) round (9, 5), r 5 (196.26 deg): bulge tan(theta / 4)
    th = math.radians(196.260205)
    b = math.tan(th / 4) * (-1 if mirror else 1)
    pa, pb = f(12, 1), f(5, 8)
    e = m.add_lwpolyline([(pa[0], pa[1], 0, 0, b), (pb[0], pb[1], 0, 0, 0)], dxfattribs={"layer": "W"})
    h["ARC"] = e.dxf.handle + "#0"
    cols = []
    for name, (x0, y0, x1, y1) in {"C1": (5, -0.2, 5.6, 0.1), "C2": (3, 3, 3.4, 3.4)}.items():
        e = m.add_lwpolyline([f(x0, y0), f(x1, y0), f(x1, y1), f(x0, y1)], close=True,
                             dxfattribs={"layer": "S-COL.BON"})
        h[name] = e.dxf.handle
    p = tmp / f"k612_{ang}_{int(mirror)}_{unit}.dxf"
    doc.saveas(p)
    d2 = ezdxf.readfile(p)
    geom, _ = X._segs(d2.modelspace())
    for e in d2.modelspace().query("LWPOLYLINE"):
        if e.dxf.layer == "S-COL.BON":
            cols.append((e.dxf.handle, [(q[0], q[1]) for q in e.get_points()]))
    um = 0.001 if unit == "mm" else 1.0
    W = "WALL"
    full = [(h["S"], W), (h["E1"], W), (h["ARC"], W), (h["N"], W), (h["W"], W)]
    face = [(h["Z"], "ZONE_EDGE"), (h["ARC"], W), (h["N"], W), (h["W"], W)]
    if mirror:                                       # a mirror reverses the walk direction, not the lengths
        full, face = full[::-1], face[::-1]
    return geom, cols, full, face, h, um


@pytest.mark.parametrize("ang", [0, 37, 90, 211])
@pytest.mark.parametrize("mirror", [False, True])
@pytest.mark.parametrize("unit", ["mm", "m"])
def test_normal_outline_partial_arc(tmp_path, ang, mirror, unit):
    geom, cols, full, face, h, um = _build(tmp_path, ang, mirror, unit)
    r = R.outline_gross(geom, full, cols, unit_m=um)
    assert abs(float(r["perimeter"]) - P_FULL) < 1e-5
    assert abs(float(r["area"]) - A_FULL) < 1e-3     # the arc is flattened at 0.5 deg for the area only
    arc = next(e for e in r["edges"] if e["handle"] == h["ARC"])
    assert abs(float(arc["lm"]) - ARC_LEN) < 1e-5     # on the arc, never its chord
    assert [x["handle"] for x in r["notches"]] == [h["C1"]] and D(r["notches"][0]["lm"]) == D("0.2")
    assert [x["handle"] for x in r["interior_solids"]] == [h["C2"]]
    assert r["interior_solids"][0]["perimeter"] == "1.6" and r["interior_solids"][0]["area"] == "0.16"
    f = R.outline_gross(geom, face, cols, unit_m=um)
    assert abs(float(f["perimeter"]) - P_FACE) < 1e-5 and f["notches"] == []


def test_face_vs_outline_cause_and_residual(tmp_path):
    geom, cols, full, face, h, um = _build(tmp_path)
    r = R.outline_gross(geom, full, cols)
    f = R.outline_gross(geom, face, cols)
    his_p, his_a = D("49.88"), D("107.90")          # two rows of his summed: an undrawn split counted twice
    room = R.close_room(f["perimeter"], his_p, [
        {"id": "FACE-VS-OUTLINE", "lm": str(D(f["perimeter"]) - D(r["perimeter"])), "verdict": "ENGINE_RIGHT"}])
    assert D(room["unresolved"]) == D(r["perimeter"]) - his_p
    s = R.split_bound(his_p, r["perimeter"])
    assert s == (his_p - D(r["perimeter"])) / 2 and s > 0
    st, both, p_only, a_only = R.match_reading(his_p, his_a, {"outline": (r["perimeter"], r["area"])},
                                               {"P1 reveals": (D("0.4"), D("0.2")), "P2 reveals": (D("0.4"), D("0.2"))})
    assert st == "NOT_ESTABLISHED"                   # an undrawn split is never an add-on, never ESTABLISHED


def test_passage_reveals_by_handle(tmp_path):
    geom, cols, full, face, h, um = _build(tmp_path, 37, True)
    w = X._gap(geom, h["J1"], h["J2"]) * um
    d = X._depth(geom, h["N"], h["F1"]) * um
    assert abs(w - 1.0) < 1e-9 and abs(d - 0.2) < 1e-9


# ---- adverse ---------------------------------------------------------------------------------------------------------
def test_mid_angle_rule_fails_on_partial_arc(tmp_path):
    """R-T606-1's 'through the entity's mid-angle' takes the long way (270 deg) round a partly used arc: the old rule
    cannot even close the outline (pinned); R-T612-1.5 takes the 90 deg inside the drawn range."""
    geom, cols, full, face, h, um = _build(tmp_path)
    with pytest.raises(R6.RuleError, match="simple polygon"):
        R6.outline(geom, full, [])
    new = R.outline(geom, full, [])
    assert abs(float(next(e for e in new["edges"] if e["handle"] == h["ARC"])["lm"]) - ARC_LEN) < 1e-5


def test_arc_as_chord_refused():
    chord = 2 * 5 * math.sin(math.radians(45))
    with pytest.raises(R.RuleError, match="chord"):
        R.arc_len(5, 90, repr(round(chord, 6)))
    assert R.arc_len(5, 90, repr(round(ARC_LEN, 6))) == D(repr(round(ARC_LEN, 6)))
    with pytest.raises(R.RuleError):
        R.arc_len(5, 90, "7.5")


def test_net_residual_as_one_cause_refused():
    with pytest.raises(R.RuleError, match="net"):
        R.refuse_single_cause([{"id": "x", "lm": "-9.69", "parts": ["8.66", "-18.35"]}])
    R.refuse_single_cause([{"id": "a", "lm": "8.66"}, {"id": "b", "lm": "-18.35"}])


def test_interior_column_never_a_hole(tmp_path):
    geom, cols, full, face, h, um = _build(tmp_path)
    c2 = dict(cols)[h["C2"]]
    with pytest.raises(R.RuleError, match="interior solid"):
        R.outline(geom, full, [c2])
    rect = [(h["S"], "WALL"), (h["E1"], "WALL"), (h["N"], "WALL"), (h["W"], "WALL")]
    old = R6.outline(geom, rect, [c2])                # the old rule folds the ring into the perimeter: + 1.6 lm
    assert abs(float(old["perimeter"]) - 40.0 - 1.6) < 1e-5
    assert R.outline_gross(geom, rect, [(h["C2"], c2)])["perimeter"] == D("40.0")


def test_refusals(tmp_path):
    geom, cols, full, face, h, um = _build(tmp_path)
    with pytest.raises(R.RuleError):
        R.outline_gross(geom, full[:-1] + [("NOPE", "WALL")], cols)
    with pytest.raises(R.RuleError):
        R.check_ours("41.0", "41.0", kind="NET")
    with pytest.raises(R.RuleError):
        R.close_room("10", "9", [{"id": "a", "lm": "1", "verdict": "UNRESOLVED", "residual": True}])
    assert R.rect_from_pp("10", "7") is None          # p^2 < 16 a: no rectangle
    a, b = R.rect_from_pp("14.76", "10.46")
    assert abs(a + b - D("7.38")) < D("0.000002") and abs(a * b - D("10.46")) < D("0.00001")
    with pytest.raises(R.RuleError):
        R._sweep_in_range(10.0, 300.0, 0.0, 90.0)     # a vertex outside the drawn range


def test_alsenan_rebuild_and_privacy():
    import json
    import subprocess

    out = subprocess.run([sys.executable, "-I", str(ROOT / "research/agents_t612/t612_alsenan.py"), "--check"],
                         capture_output=True, text=True)
    assert "byte-identical" in out.stdout, out.stdout + out.stderr
    d = json.loads((ROOT / "research/agents_t612/out/T612_REMAINDER_CAUSES.json").read_text())
    assert D(d["split"]["named"]) + D(d["split"]["unresolved"]) == D(d["t606_remainder_total"]) == D("-18.353234")
    gf = d["rooms"][0]
    assert gf["remeasured"]["engine face"][0] == "56.006096"
    assert gf["remeasured"]["drawn gross outline"][:2] == ["55.906096", "147.657717"]
    assert gf["reading_test"]["status"] == "NOT_ESTABLISHED"
    assert gf["split_bound"]["grid_test"]["reproducing_both"] == 0
    assert D(gf["unresolved"]) == D("-17.013904")
    import re
    drawn = json.loads((ROOT / "research/agents_t612/T612_DRAWN.json").read_text())
    drawn.pop("grid_test")                            # counts only
    drawn.pop("source")                               # the Drive title
    drawn.pop("rule")
    drawn.pop("schema")
    vals = re.findall(r"-?\d+(?:\.\d+)?", json.dumps(drawn))
    assert vals and max(abs(float(v)) for v in vals) < 500   # lengths / areas only: no drawing coordinate
