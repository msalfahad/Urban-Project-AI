"""T-625 / R-T625-1: open-plan floor boundary and stair footprint (research rule, unwired).

Villa K625 (synthetic, not Alsenan), hand calculation (m):
  L-shaped open plan (0,0) (10,0) (10,4) (6,4) (6,8) (0,8) = 10 x 4 + 6 x 4 = 64.000, split by a printed STEP line at
  x 8 (y 0 .. 4) into the main floor at +1.00 (0,0) (8,0) (8,4) (6,4) (6,8) (0,8) = 8 x 4 + 6 x 4 = 56.000 and a
  sunken lounge at +0.85 (8,0) (10,0) (10,4) (8,4) = 8.000 (the riser face is a vertical item, never plan area).
  South wall: S1 x 0 .. 4 and S2 x 4.90 .. 8, entrance door D090 inserted in the 0.90 gap -> DOOR_ON_FACE 0.90.
  North side y 8: wall N1 x 0 .. 3, stair opening edge V1 x 3 .. 6 (printed VOID_EDGE) -> floor stops on V1, 3.00.
  Perimeter of the main floor: 8 + 4 + 2 + 4 + 6 + 8 = 32.000 = WALL 27.10 - ... (by class below).
  Curved flight: tread band r 1.00 .. 2.20, sweep 90 deg = 1/2 x pi/2 x (4.84 - 1.00) = 3.015929; chord polygon through
  nosings every 15 deg = 6 x 1/2 x sin 15 x 3.84 = 2.981595 (loss 0.034334, never the measure).
  Quarter disc r 3: lines (0,0)-(3,0), arc (3,0)-(0,3), line (0,3)-(0,0) = pi x 9 / 4 = 7.068583.
Read at 0 / 37 / 90 / 211 deg, mirrored, in m and mm. Adverse: the void side closed by the NEAREST WALL prolonged (no
printed line on it) is refused; an undrawn gap with no door / printed line / dimension is refused; a dimension whose end
is off the edge line is refused; two levels in one outline are refused.
"""
from __future__ import annotations

import json
import math
import os
import sys
from decimal import Decimal as D
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research" / "agents_t625"))
import t625_rules as R  # noqa: E402
import t625_extract as X  # noqa: E402
import t625_alsenan as B  # noqa: E402

# ------------------------------------------------------------------ K625 fixture (metres)
SEGS = {
    "S1": ((0, 0), (4, 0)), "S2": ((4.9, 0), (8, 0)), "ST": ((8, 0), (8, 4)), "N3": ((8, 4), (6, 4)),
    "E2": ((6, 4), (6, 8)), "N1": ((0, 8), (3, 8)), "V1": ((3, 8), (6, 8)), "W1": ((0, 8), (0, 0)),
    "S3": ((8, 0), (10, 0)), "E1": ((10, 0), (10, 4)), "N4": ((10, 4), (8, 4)),
}
LAYERS = {"S1": "1", "S2": "1", "ST": "5", "N3": "1", "E2": "1", "N1": "1", "V1": "5", "W1": "1", "S3": "1",
          "E1": "1", "N4": "1"}
ROLES = {"ST": "STEP", "V1": "VOID_EDGE"}
MAIN = [("S1", "WALL"), ("ST", "WALL"), ("N3", "WALL"), ("E2", "WALL"), ("N1", "WALL"), ("W1", "WALL")]
LOUNGE = [("S3", "WALL"), ("E1", "WALL"), ("N4", "WALL"), ("ST", "WALL")]


def _xf(p, ang, mirror, mm):
    x, y = p
    if mirror:
        x = -x
    c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    k = 1000.0 if mm else 1.0
    return ((x * c - y * s) * k + 12345.0 * k / 1000, (x * s + y * c) * k - 6789.0 * k / 1000)


def _setup(monkeypatch, ang=0, mirror=False, mm=True, roles=ROLES, door=True, extra=None):
    segs = dict(SEGS, **(extra or {}))
    geom = {h: ("LINE", (_xf(a, ang, mirror, mm), _xf(b, ang, mirror, mm))) for h, (a, b) in segs.items()}
    lines = [(h, g) for h, (_, g) in geom.items()]
    ins = [("I1", "D090", _xf((4.45, -0.1), ang, mirror, mm))] if door else []
    monkeypatch.setattr(X, "PRINTED_ROLE", dict(roles))
    monkeypatch.setattr(R, "LINE_TOL", 1.0 if mm else 0.001)
    return geom, lines, ins


def _gap_tol(monkeypatch, mm):
    # the door search radius in _gap_evidence is in drawing units (600 = 0.60 m in mm)
    if not mm:
        orig = X._gap_evidence

        def scaled(name, h, ab, mid, p, q, inserts, doc, st_doc, shift):
            k = 1000.0
            P = lambda v: (v[0] * k, v[1] * k)  # noqa: E731
            out = orig(name, h, (ab[0] * k, ab[1] * k), P(mid), P(p), P(q),
                       [(a, b, P(c)) for a, b, c in inserts], doc, st_doc, shift)
            for s in out:
                s["length_mm"] /= k
            return out
        monkeypatch.setattr(X, "_gap_evidence", scaled)


def _run(geom, lines, ins, chain, mm=True):
    edges, green = X._edges("K625", "GF", chain, geom, lines, LAYERS, ins, None, None, (0, 0))
    if not mm:
        for e in edges:
            e["length"] = str(R.q6(float(e["length"]) * 1000))
            for s in e["segments"]:
                s["length"] = str(R.q6(float(s["length"]) * 1000))
    return edges, green


@pytest.mark.parametrize("ang,mirror,mm", [(0, False, True), (37, False, True), (90, False, True),
                                           (211, False, True), (0, True, True), (37, True, True), (0, False, False)])
def test_k625_main_floor_hand_calc(monkeypatch, ang, mirror, mm):
    geom, lines, ins = _setup(monkeypatch, ang, mirror, mm)
    _gap_tol(monkeypatch, mm)
    chain = MAIN[::-1] if mirror else MAIN
    edges, green = _run(geom, lines, ins, chain, mm)
    unit = 0.001 if mm else 1.0
    assert R.green_area(green, unit_m=unit) == D("56.0")
    acc = R.account(edges)
    m = {k: D(v) for k, v in acc["metres"].items()}
    assert m["DOOR_ON_FACE"] == D("0.9") and m["PRINTED_LINE"] == D("7.0")   # step 4.00 + void edge 3.00
    assert m["WALL"] == D("24.1") and D(acc["perimeter"]) == D("32.0")
    kinds = sorted((o["class"], o["length"]) for o in acc["open_sides"])
    assert kinds == [("DOOR_ON_FACE", "0.9"), ("PRINTED_LINE", "3.0"), ("PRINTED_LINE", "4.0")]


def test_k625_step_down_splits_into_two_outlines(monkeypatch):
    geom, lines, ins = _setup(monkeypatch)
    _, gm = _run(geom, lines, ins, MAIN)
    _, gl = _run(geom, lines, ins, LOUNGE)
    assert R.green_area(gm) + R.green_area(gl) == D("64.0")
    assert R.green_area(gl) == D("8.0")
    assert R.one_level(["+1.00", "+1.00"]) == "+1.00"
    with pytest.raises(R.RuleError):          # the whole L at two levels in one outline
        R.one_level(["+1.00", "+0.85"])
    with pytest.raises(R.RuleError):
        R.one_level([])


def test_adverse_void_side_closed_by_nearest_wall_refused(monkeypatch):
    """The north side closed by the nearest wall N1 prolonged across the stair opening (the printed void edge V1
    not used): 3.00 m of undrawn side with no door, printed line or dimension -> refused, not a boundary."""
    segs_no_v1 = {h: v for h, v in SEGS.items() if h != "V1"}
    geom = {h: ("LINE", (_xf(a, 0, False, True), _xf(b, 0, False, True))) for h, (a, b) in segs_no_v1.items()}
    lines = [(h, g) for h, (_, g) in geom.items()]
    monkeypatch.setattr(X, "PRINTED_ROLE", dict(ROLES))
    ins = [("I1", "D090", _xf((4.45, -0.1), 0, False, True))]
    edges, _ = X._edges("K625", "GF", MAIN, geom, lines, LAYERS, ins, None, None, (0, 0))
    with pytest.raises(R.RuleError, match="refused"):
        R.account(edges)
    with pytest.raises(R.RuleError, match="NEAREST_WALL"):
        R.classify({"length": "3.0", "drawn_by": [], "evidence": {"kind": "NEAREST_WALL"}})
    with pytest.raises(R.RuleError, match="ENGINE_LINE"):
        R.classify({"length": "3.0", "drawn_by": [], "evidence": {"kind": "ENGINE_LINE"}})


def test_door_gap_without_door_block_refused(monkeypatch):
    geom, lines, ins = _setup(monkeypatch, door=False)
    edges, _ = _run(geom, lines, ins, MAIN)
    with pytest.raises(R.RuleError):
        R.account(edges)


def test_printed_line_without_role_refused(monkeypatch):
    geom, lines, ins = _setup(monkeypatch, roles={"ST": "STEP"})      # V1 printed but unnamed
    with pytest.raises(R.RuleError, match="has no role"):
        _run(geom, lines, ins, MAIN)


def test_dimension_gap_status_and_refusal():
    on = {"length": "1.15", "drawn_by": [], "evidence": {"dimension": "DIM1", "on_line": True,
                                                         "corroboration": ["ST:459"]}}
    only = {"length": "0.05", "drawn_by": [], "evidence": {"dimension": "DIM1", "on_line": True, "corroboration": []}}
    off = {"length": "1.15", "drawn_by": [], "evidence": {"dimension": "DIM1", "on_line": False}}
    assert R.classify(on) == "PRINTED_DIMENSION"
    acc = R.account([{"handle": "E", "length": "1.2", "segments": [on, only]}])
    assert [o["status"] for o in acc["open_sides"]] == ["DRAWING_CONFIRMED", "PRINTED_ONLY"]
    with pytest.raises(R.RuleError, match="not on the edge line"):
        R.classify(off)
    with pytest.raises(R.RuleError, match="re-add"):
        R.account([{"handle": "E", "length": "1.3", "segments": [on, only]}])
    with pytest.raises(R.RuleError, match="unknown"):
        R.classify({"length": "1", "drawn_by": [("X", "PRINTED:BANNER")]})


@pytest.mark.parametrize("ang,mirror", [(0, False), (37, False), (211, False), (0, True)])
def test_arc_edge_exact_both_senses(ang, mirror):
    t = lambda p: _xf(p, ang, mirror, True)  # noqa: E731
    c, r = t((0, 0)), 3000.0
    a, b = t((3, 0)), t((0, 3))
    ang_a = math.degrees(math.atan2(a[1] - c[1], a[0] - c[0])) % 360
    ang_b = math.degrees(math.atan2(b[1] - c[1], b[0] - c[0])) % 360
    s0, s1 = (ang_b, ang_a) if mirror else (ang_a, ang_b)     # the drawn arc is ccw from s0 to s1
    fwd = [("LINE", c, a), ("ARC", a, b, c, r, s0, s1), ("LINE", b, c)]
    rev = [("LINE", c, b), ("ARC", b, a, c, r, s0, s1), ("LINE", a, c)]
    assert R.green_area(fwd) == R.green_area(rev) == D("7.068583")


def test_stair_band_exact_vs_chord():
    assert R.sector_band(1000, 2200, 90) == D("3.015929")
    assert R.chord_band(1000, 2200, [0, 15, 30, 45, 60, 75, 90]) == D("2.981595")
    fp = R.footprint({"band": {"area": "3.015929", "role": "BAND", "handles": ["A1", "A2"]},
                      "curtail": {"area": "0.1", "role": "BESIDE", "handles": ["A3"]}})
    assert fp == {"band": "3.015929", "beside": {"curtail": "0.1"}}
    with pytest.raises(R.RuleError):
        R.footprint({"band": {"area": "3", "role": "BAND", "handles": []}})
    with pytest.raises(R.RuleError):
        R.footprint({"band": {"area": "3", "role": "FLOOR", "handles": ["A"]}})
    for bad in ((2200, 1000, 90), (1000, 2200, 0), (1000, 2200, 360)):
        with pytest.raises(R.RuleError):
            R.sector_band(*bad)
    st, d, _ = R.classify_delta(D("3.015929"), D("2.981595"), "chord flattening")
    assert st == "DIFFERS" and d == D("0.034334")
    with pytest.raises(R.RuleError, match="named"):
        R.classify_delta(D("3.015929"), D("2.981595"), "")
    assert R.classify_delta(D("1.0004"), D("1.0"), "")[0] == "AGREES"


# ------------------------------------------------------------------ Alsenan pins (from the committed JSON only)
def test_alsenan_rebuild_identical():
    o = B.build()
    assert json.dumps(o, indent=1, sort_keys=True) + "\n" == B.OUT_JSON.read_text(encoding="utf-8")
    assert B.md(o) == B.OUT_MD.read_text(encoding="utf-8")


def test_alsenan_row0_and_split():
    r0 = B.build()["row0"]
    assert r0["own"] == "6.137684" and r0["status"] == "DIFFERS" and r0["difference"] == "0.013272"
    assert sum(D(v) for v in r0["difference_split"].values()) == D("0.013272")
    assert D(r0["F1"]) + D(r0["F2"]) == D("6.137684")
    assert r0["beside"]["curtail of the first step (arc 258 to the inner tread arc 239; printed 963 ends on it)"] \
        == "0.157787"
    assert r0["printed"]["963_end_on_curtail_arc_mm"] == "0.0"


def test_alsenan_open_sides_named():
    o = B.build()
    gf = o["outlines"]["GF-OPEN.full"]
    assert gf["status"] == "AGREES" and gf["levels"] == ["+1.00"] and gf["printed_checks_all_agree"]
    assert D(gf["metres_by_class"]["PRINTED_DIMENSION"]) == 0                      # nothing undrawn on GF
    assert sorted(s["by"][0] for s in gf["open_sides"]) == ["22B", "281", "2C7", "2DC", "2F2", "33E"]
    lp = o["outlines"]["1F-LIV.floor_printed"]
    dims = [s for s in lp["open_sides"] if s["class"] == "PRINTED_DIMENSION"]
    assert [(s["length"], s["status"]) for s in dims] == [("1.15", "DRAWING_CONFIRMED"), ("0.05", "PRINTED_ONLY"),
                                                          ("0.05", "PRINTED_ONLY")]
    f = o["first_floor_readings"]
    assert f["restated_floor_at_550"] == "38.6430" and f["engine_minus_restated_split"]["residual"] == "0.000536"


def test_alsenan_drawn_json_has_no_coordinates():
    txt = (ROOT / "research" / "agents_t625" / "T625_DRAWN.json").read_text(encoding="utf-8")
    import re
    assert not re.search(r"-?\d{5,}\.\d", txt)       # no drawing coordinate (mm, five digits and more)
    for word in ("alsenan", "chalet"):
        assert word not in txt.lower().replace("alsenan chalet project", "")


DXF = Path(os.environ.get("T625_DXF", ROOT.parents[1] / ".work" / "private" / "P7757_DXF_COMPRESSED" / "P7757.dxf"))
ST = Path(os.environ.get("T625_ST", ROOT.parents[1] / ".work" / "private" / "ST7757.dxf"))


@pytest.mark.skipif(not (DXF.exists() and ST.exists()), reason="private drawings absent")
def test_alsenan_dxf_reread_identical():
    pytest.importorskip("ezdxf")
    d = X.read(str(DXF), str(ST))
    assert X.dumps(d) == X.OUT.read_text(encoding="utf-8")
