"""T-493 on the development villa (P7757): census of every landing-like surface of ST-01 (dog-leg, GF -> 2F, with D1),
ST-02 (round stair, GF -> 1F) and ST-03 (E1 entrance flight) with LANDING_CENSUS_V1 (R-T493-1). Research only: no
engine, rule, registry or candidate file changes; the proposed B7-04 lines are UNWIRED (a later stream F row).

    python3 -I research/agents_t493/t493_alsenan.py --extract <P7757.dxf>   (re-read every handle, write EXTRACT_T493.json)
    python3 -I research/agents_t493/t493_alsenan.py --write                 (CENSUS_T493.csv + summary.json from the extract)
    python3 -I research/agents_t493/t493_alsenan.py --check                 (rebuild from the committed extract, byte compare)

Frames (room-local metres, north = +y). SHAFT: the ST-01 stair shaft, origin = its west inner wall face (GF 298, 1F AF0,
2F 12B7: three plans side by side, one x shift each) and the GF south face of the stair room (220); the three plans
share y (north walls 2AB / ADE / 127E all at y 5.000). RS: the ST-02 quarter landing, origin = RS-S last nosing B4D (x)
and its south end (y). Committed: handles, layers, local coordinates, dimension values, line ids and quantities only
(no world coordinate, no name, no drawing text).
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from pathlib import Path

from shapely.geometry import Polygon, box

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import landing_census_v1 as L  # noqa: E402

EXTRACT = HERE / "EXTRACT_T493.json"
CENSUS = HERE / "CENSUS_T493.csv"
SUMMARY = HERE / "summary.json"
DXF_SHA8 = "ab54dd55"
INDEX = ROOT / "research" / "agents_t485" / "out" / "LINE_INDEX_V3_0_46.json"
INDEX_NOTE = ("candidate of record V3.0.47 (T-443) changed FIN.SKIRTING only; every landing / floor line below is "
              "read from the V3.0.46 line index (T-485)")
FLOOR_LEVELS = [0.15, 0.30, 1.00, 5.50, 9.70]   # court, back lobby, GF, 1F, 2F (printed level marks)

# handle -> (frame, what it is). Frames: GF / 1F / 2F (SHAFT, shifted per plan) and RS.
HANDLES = {
    "GF": {"298": "west wall face", "220": "south wall face", "21B": "east wall face (north part)",
           "2AB": "north wall face (west part)", "26F": "north wall face (east part)",
           "DC": "MS1-L first nosing (L5)", "DE": "MS1-L first riser face (L2)",
           "490": "D1 last nosing = hall edge (L5)", "481": "D1 first nosing = lobby edge (L5)",
           "482": "D1 first riser face (L2)", "2C6": "MS1-LD own nosing, above the cut (L2)",
           "49C": "same, duplicate (L2)", "49D": "MS1-T closing riser face below MS1-LD (L2)",
           "154": "divider end at the turn (L2)", "4A6": "divider end at the turn (L5)",
           "485": "MS1-L last nosing / first winder front (L2)", "4A2": "winder radial (L2)",
           "49E": "winder radial (L2)", "4A0": "winder radial (L2)"},
    "1F": {"AF0": "west wall face (north part)", "ADE": "north wall face", "B16": "east wall face",
           "A97": "MS2-L last nosing = MS2-LD west edge (L5)", "A9A": "MS2-L last riser face (L2)",
           "A92": "MS1-U first nosing = MS1-LD south edge seen below (L5)", "A93": "MS1-U first riser face (L2)",
           "BE4": "MS1-LD own nosing seen below / MS2-TR nosing stacked (L5)", "BE5": "the riser face behind it (L2)",
           "A9B": "divider end (L5)", "AC0": "MS2-L first nosing = 1F arrival edge (L5)",
           "AC2": "MS2-L first riser face (L2)", "AC3": "divider band south end (L5)", "ABE": "MS1-U 11th nosing (L5)",
           "10DF": "printed arrival depth", "10D1": "printed flight run", "10C3": "printed half-landing depth",
           "10ED": "printed lane width (west)", "10FB": "printed divider", "110A": "printed lane width (east)"},
    "2F": {"12B7": "west wall face", "1282": "south wall face (west of door)", "1283": "south wall face (east)",
           "129A": "east wall face", "127E": "north wall face", "135B": "MS2-U first nosing (L5)",
           "135C": "MS2-U first riser face (L2)", "1386": "MS2-U 11th nosing (L5)", "1385": "MS2-U 11th riser face (L2)",
           "12B4": "MS2-TR nosing (L5)", "12B5": "MS2-TR riser face (L2)", "138A": "slab / guard edge (L5)",
           "138B": "guard face (L5)", "1363": "divider end (L5)", "2F1F": "unexplained diagonal (L5, Q-ST-11)",
           "2F20": "its companion (L2)", "2F72": "column at the lobby edge (S-COL.BON)",
           "14F1": "printed arrival depth", "14D5": "printed half-landing depth", "152A": "printed lobby length"},
    "RS": {"B4D": "RS-S last nosing = RS-LD west edge (L5)", "B58": "RS-S last riser face (L2)",
           "B59": "RS-A first nosing = RS-LD north edge (L5)", "B6E": "RS-A first riser face (L2)",
           "AF5": "east edge band, inner face (L5)", "AF6": "east edge band, outer face (L5)",
           "3008": "column proud of the south face (S-COL.BON)", "D22": "RS-A floor edge (L5)",
           "1265": "printed width incl. band"},
    "GFRS": {"336": "GF south wall face under the landing (L1)"},
}


def _sha(p, n=8):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:n]


def _r(v):
    return round(float(v), 4)


def extract(dxf):
    import ezdxf
    doc = ezdxf.readfile(str(dxf))
    db = doc.entitydb
    y0 = float(db["220"].dxf.start.y)
    org = {"GF": (float(db["298"].dxf.start.x), y0), "1F": (float(db["AF0"].dxf.start.x), y0),
           "2F": (float(db["12B7"].dxf.start.x), y0),
           "RS": (float(db["B4D"].dxf.start.x), float(db["B4D"].dxf.start.y))}
    shift_gf_1f = org["1F"][0] - org["GF"][0]
    org["GFRS"] = (org["RS"][0] - shift_gf_1f, org["RS"][1])
    out = {}
    for fr, hs in HANDLES.items():
        ox, oy = org[fr]
        rec = {}
        for h, what in hs.items():
            e = db[h]
            t = e.dxftype()
            r = {"type": t, "layer": e.dxf.layer, "what": what}
            if t == "LINE":
                r["pts"] = [[_r((e.dxf.start.x - ox) / 1000), _r((e.dxf.start.y - oy) / 1000)],
                            [_r((e.dxf.end.x - ox) / 1000), _r((e.dxf.end.y - oy) / 1000)]]
            elif t == "LWPOLYLINE":
                r["pts"] = [[_r((p[0] - ox) / 1000), _r((p[1] - oy) / 1000)] for p in e.get_points()]
            elif t == "DIMENSION":
                r["value_mm"] = _r(e.get_measurement())
                r["pts"] = [[_r((e.dxf.defpoint2.x - ox) / 1000), _r((e.dxf.defpoint2.y - oy) / 1000)],
                            [_r((e.dxf.defpoint3.x - ox) / 1000), _r((e.dxf.defpoint3.y - oy) / 1000)]]
            rec[h] = r
        out[fr] = rec
    x = {"drawing": {"P7757.dxf_sha256_8": _sha(dxf)}, "frames": out,
         "frame_note": "SHAFT frames GF / 1F / 2F share y; x per plan from the west wall face; RS from B4D"}
    EXTRACT.write_text(json.dumps(x, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return x


# ------------------------------------------------------------------------------------------------ build (no DXF)
def _seg(x, fr, h):
    return x["frames"][fr][h]["pts"]


def _ys(x, fr, h):
    p = _seg(x, fr, h)
    return p[0][1]


def _xs(x, fr, h):
    p = _seg(x, fr, h)
    return p[0][0]


def _check(cond, msg, fails):
    if not cond:
        fails.append(msg)


def verify(x):
    """Every edge the polygons use is the drawn line it claims to be (local coordinates, 1 mm tolerance)."""
    f = []
    t = 0.001
    g = lambda fr, h: x["frames"][fr][h]  # noqa: E731
    # shaft walls on the three plans
    _check(abs(_xs(x, "GF", "21B") - 2.5) < t and abs(_xs(x, "1F", "B16") - 2.5) < t and abs(_xs(x, "2F", "129A") - 2.5) < t,
           "east wall faces not at x 2.500", f)
    _check(abs(_ys(x, "GF", "2AB") - 5.0) < t and abs(_ys(x, "1F", "ADE") - 5.0) < t and abs(_ys(x, "2F", "127E") - 5.0) < t,
           "north wall faces not at y 5.000", f)
    # nosing pairs (nosing L5 / riser face L2, 0.050 apart)
    for fr, n, rf, d in (("GF", "DC", "DE", 0.05), ("GF", "481", "482", -0.05), ("1F", "A92", "A93", -0.05),
                         ("1F", "AC0", "AC2", 0.05), ("2F", "135B", "135C", -0.05), ("2F", "1386", "1385", -0.05)):
        _check(abs((_ys(x, fr, rf) - _ys(x, fr, n)) - d) < t, f"{fr} {n}/{rf} not a nosing pair", f)
        _check(g(fr, n)["layer"] == "5" and g(fr, rf)["layer"] == "2", f"{fr} {n}/{rf} layers", f)
    for fr, n, rf in (("GF", "2C6", "49D"), ("1F", "BE4", "BE5"), ("2F", "12B4", "12B5")):
        _check(abs(_xs(x, fr, n) - 1.25) < t and abs(_xs(x, fr, rf) - 1.30) < t, f"{fr} {n}/{rf} not at x 1.25 / 1.30", f)
        ys = sorted(p[1] for p in _seg(x, fr, n))
        _check(abs(ys[0] - 3.85) < t and abs(ys[1] - 5.0) < t, f"{fr} {n} not y 3.85 .. 5.00", f)
    _check(abs(_ys(x, "1F", "A97") - 3.80) < t and abs(_ys(x, "1F", "A92") - 3.85) < t, "1F A97 / A92", f)
    _check(abs(_ys(x, "2F", "135B") - 3.85) < t and abs(_ys(x, "1F", "AC0") - 0.50) < t, "2F 135B / 1F AC0", f)
    _check(abs(_ys(x, "GF", "481") - 3.85) < t and abs(_ys(x, "GF", "490") - 2.95) < t, "GF D1 nosings", f)
    _check(abs(_ys(x, "1F", "A9B") - 3.85) < t and abs(_ys(x, "2F", "1363") - 3.85) < t, "divider end y 3.85", f)
    _check(abs(_ys(x, "2F", "138A") - 0.45) < t and abs(_ys(x, "2F", "138B") - 0.50) < t, "2F guard pair", f)
    _check(abs(max(p[0] for p in _seg(x, "2F", "138A")) - 1.35) < t, "2F 138A to x 1.35", f)
    _check(abs(_ys(x, "1F", "AC3") - 0.45) < t, "1F divider south end", f)
    _check(abs(_ys(x, "2F", "1282") + 1.45) < t and abs(_ys(x, "2F", "1283") + 1.45) < t, "2F south wall y -1.45", f)
    # printed dimensions
    for fr, h, v in (("1F", "10DF", 1950), ("1F", "10D1", 3300), ("1F", "10C3", 1200), ("1F", "10ED", 1200),
                     ("1F", "10FB", 100), ("1F", "110A", 1200), ("2F", "14F1", 1950), ("2F", "14D5", 1200),
                     ("2F", "152A", 4500), ("RS", "1265", 1250)):
        _check(abs(g(fr, h)["value_mm"] - v) < 0.5, f"dimension {h} != {v}", f)
    # round-stair quarter landing
    _check(abs(_xs(x, "RS", "B4D")) < t and abs(_xs(x, "RS", "B58") - 0.05) < t, "RS B4D / B58", f)
    _check(abs(_ys(x, "RS", "B59") - 1.15) < t and abs(_ys(x, "RS", "B6E") - 1.20) < t, "RS B59 / B6E", f)
    _check(abs(_xs(x, "RS", "AF5") - 1.20) < t and abs(_xs(x, "RS", "AF6") - 1.25) < t, "RS east band", f)
    _check(abs(_ys(x, "GFRS", "336")) < t and abs(max(p[0] for p in _seg(x, "GFRS", "336")) - 0.65) < t,
           "GF wall 336 not ending at x 0.65 on y 0 under the landing", f)
    col = Polygon(_seg(x, "RS", "3008"))
    _check(abs(col.bounds[1] + 0.20) < t and abs(col.bounds[3] - 0.05) < t and abs(col.bounds[0] - 0.65) < t,
           "RS column 3008 bounds", f)
    return f


def _rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def parts(x):
    """The census parts. Edges by handle (R-T493-1 step 2: arriving flight -> its last nosing is the landing's edge;
    departing flight -> its first nosing line; the 0.050 strip under a departing nosing is reported beside)."""
    col = [tuple(p) for p in _seg(x, "RS", "3008")]
    st01 = [
        {"id": "ST01-GF-HALL", "stair": "ST-01", "level": 1.00, "arriving": ["D1"], "departing": ["MS1-L"],
         "polygon": [(0, 0), (2.5, 0), (2.5, 2.95), (1.35, 2.95), (1.35, 0.45), (1.15, 0.45), (1.15, 1.15),
                     (0, 1.15)], "line": "L-f53d4986", "line_state": "FINISH_HELD 4.805 (B3-01)",
         "claimed_by": ["B3-01"], "edges": "220 / 21B / 490 (D1 last nosing) / divider 47E-4A4 / DE (MS1-L riser "
         "face, T-418) / 298"},
        {"id": "ST01-GF-LOBBY030", "stair": "ST-01", "level": 0.30, "departing": ["D1"],
         "polygon": _rect(1.35, 3.85, 2.5, 5.0), "line": "L-b4441a1b", "line_state": "FINISH_HELD 1.3225 (B3-01)",
         "claimed_by": ["B3-01"], "edges": "481 (D1 first nosing) / 21B / 26F-door OP-013-2AB / divider"},
        {"id": "ST01-MS1-T", "stair": "ST-01", "kind_hint": "WINDER", "level": None, "polygon": None,
         "line": None, "line_state": "tread family (T-412 / Q-51 HELD; S-9)", "edges": "485 / 4A2 / 49E / 4A0"},
        {"id": "ST01-MS1-LD", "stair": "ST-01", "level": 3.50, "arriving": ["MS1-T"], "departing": ["MS1-U"],
         "polygon": _rect(1.25, 3.85, 2.5, 5.0), "line": None, "line_state": "NO LINE (silent omission, F-3)",
         "claimed_by": ["B7-04"], "edges": "2C6 / 49C (GF, hidden) = BE4 (1F, seen below): own nosing x 1.25; "
         "A92 (MS1-U first nosing) y 3.85; 21B / B16 x 2.50; 2AB-26F / ADE y 5.00"},
        {"id": "ST01-1F-ARRIVAL", "stair": "ST-01", "level": 5.50, "arriving": ["MS1-U"], "departing": ["MS2-L"],
         "owner_answer": {"id": "Q-66 B", "condition_met": True},
         "polygon": [(0, -1.45), (2.5, -1.45), (2.5, 0.55), (1.35, 0.55), (1.35, 0.45), (1.15, 0.45), (1.15, 0.5),
                     (0, 0.5)],
         "line": "L-8011889d", "line_state": "RELEASED 4.9225 (B7-04)", "claimed_by": ["B7-04"],
         "edges": "printed 1950 (10DF) to AC0 y 0.50; divider end AC3 y 0.45 (-0.010); MS1-U floor nosing band "
         "y 0.50 .. 0.55 (+0.0575, T-269)"},
        {"id": "ST01-MS2-LD", "stair": "ST-01", "level": 7.516, "arriving": ["MS2-L"], "departing": ["MS2-TR"],
         "polygon": [(0, 3.80), (1.15, 3.80), (1.15, 3.85), (2.5, 3.85), (2.5, 5.0), (0, 5.0)],
         "line": None, "line_state": "only inside HELD bound L-5d2be30d 0 .. 9.225 (no line of its own)",
         "claimed_by": ["B7-04"], "split_level": True,
         "edges": "A97 (MS2-L last nosing, printed 1200 10C3 / 14D5) y 3.80; divider end A9B / 1363 y 3.85; 135B "
         "(MS2-U first nosing) y 3.85; AF0 / 12B8 x 0; B16 / 129A x 2.50; ADE / 127E y 5.00; closing riser "
         "BE4 / 12B4 nosing x 1.25 (face 1.30) splits +7.516 / +7.684"},
        {"id": "ST01-2F-ARRIVAL", "stair": "ST-01", "level": 9.70, "arriving": ["MS2-U"],
         "owner_answer": {"id": "Q-70 A (condition met, T-129)", "condition_met": True},
         "polygon": [(0, -1.45), (2.5, -1.45), (2.5, 0.55), (1.35, 0.55), (1.35, 0.45), (0, 0.45)],
         "line": None, "line_state": "only inside HELD bound L-5d2be30d 0 .. 9.225 (F-1)", "claimed_by": ["B7-04"],
         "edges": "1282 / 1283 y -1.45 (door OP-001 changes no floor area); 12B7 x 0; lobby edge x 2.50 (L-9bd25c0c "
         "beyond); slab / guard edge 138A y 0.45 to x 1.35; MS2-U floor nosing band y 0.50 .. 0.55 (12th riser "
         "face 0.50 by the 0.300 going from 1385 0.80; nosing not drawn, T-412)"},
    ]
    st02 = [
        {"id": "ST02-GF-FOOT", "stair": "ST-02", "level": 1.00, "departing": ["RS-C"], "in_room_floor_line": True,
         "polygon": None, "line": "L-7625f35c", "line_state": "GF open-room porcelain (B3-01)",
         "edges": "RS-C first riser on the room floor; no landing zone drawn"},
        {"id": "ST02-RS-LD", "stair": "ST-02", "level": 4.696, "arriving": ["RS-S"], "departing": ["RS-A"],
         "polygon": _rect(0, 0, 1.2, 1.15), "solids": [col], "line": None,
         "line_state": "NO LINE (F-2; deducted from 1F porcelain as R04 1.352454)", "claimed_by": ["B7-04"],
         "edges": "B4D (RS-S last nosing) x 0; 336 GF wall face y 0 to x 0.65 then column 3008 proud 0.050 "
         "(x 0.65 .. 1.20); AF5 x 1.20 (edge band AF5 / AF6); B59 (RS-A first nosing) y 1.15"},
        {"id": "ST02-1F-TOP", "stair": "ST-02", "level": 5.50, "arriving": ["RS-A"], "in_room_floor_line": True,
         "polygon": None, "line": "L-b06400d4", "line_state": "1F living porcelain (B3-01)",
         "edges": "RS-A floor edge D22; the 1F living floor beyond; no landing zone drawn (nosing D22 lm in B7-05)"},
    ]
    st03 = [
        {"id": "ST03-E1-LANDING", "stair": "ST-03", "level": 1.00, "arriving": ["E1"],
         "owner_answer": {"id": "OWNER_RULE_OUTDOOR_FLOORS (outside stairs marble)", "condition_met": True},
         "polygon": _rect(0, 0, 1.4, 3.7), "line": "L-3dd82a57", "line_state": "RELEASED 5.1794 (B7-04)",
         "claimed_by": ["B7-04"], "edges": "printed 1400 (9A4) x 3700 (9B2), T-490 Checker re-measure"},
    ]
    return st01, st02, st03


def under_nosing():
    """The 0.050 strips under a DEPARTING flight's first nosing (installed, hidden), beside, never added."""
    return [
        {"part": "ST01-GF-HALL", "flight": "MS1-L", "m2": 0.0575, "note": "IN the existing hall part (T-418 runs to "
         "the riser face DE y 1.15; the nosing DC is y 1.10): convention residual of the B3 line, named"},
        {"part": "ST01-GF-LOBBY030", "flight": "D1", "m2": 0.0575, "note": "beside (part ends at nosing 481)"},
        {"part": "ST01-MS1-LD", "flight": "MS1-U", "m2": 0.0575, "note": "beside (A92 / A93)"},
        {"part": "ST01-1F-ARRIVAL", "flight": "MS2-L", "m2": 0.0575, "note": "beside (AC0 / AC2)"},
        {"part": "ST01-MS2-LD", "flight": "MS2-TR + MS2-U", "m2": 0.115, "note": "beside (12B4 / 12B5 and 135B / 135C)"},
        {"part": "ST02-RS-LD", "flight": "RS-A", "m2": 0.0575, "note": "beside (B59 / B6E)"},
    ]


def line_states():
    idx = json.loads(INDEX.read_text(encoding="utf-8"))
    want = {"L-1983e89d", "L-5d2be30d", "L-8011889d", "L-3dd82a57", "L-f53d4986", "L-b4441a1b", "L-9bd25c0c",
            "L-b06400d4", "L-7625f35c"}
    out = {}
    for ln in idx["lines"]:
        k = ln["line_id"][:10]
        if k in want:
            out[k] = {"item": ln["item_code"], "class": ln["class"], "net": ln["measured_net"],
                      "held": [ln["held_low"], ln["held_high"]], "element": ln["element_id"]}
    return {"index": "research/agents_t485/out/LINE_INDEX_V3_0_46.json", "note": INDEX_NOTE, "lines": out}


def build(x):
    if x["drawing"]["P7757.dxf_sha256_8"] != DXF_SHA8:
        raise SystemExit("drawing hash differs from the training-villa manifest")
    fails = verify(x)
    if fails:
        raise SystemExit("drawn-line checks failed: " + "; ".join(fails))
    st01, st02, st03 = parts(x)
    res = {k: L.census(p, FLOOR_LEVELS) for k, p in (("ST-01", st01), ("ST-02", st02), ("ST-03", st03))}
    ms2 = next(p for p in st01 if p["id"] == "ST01-MS2-LD")
    split = L.split_level([{"id": "MS2-LD-W", "level": 7.516,
                            "polygon": [(0, 3.80), (1.15, 3.80), (1.15, 3.85), (1.25, 3.85), (1.25, 5.0), (0, 5.0)]},
                           {"id": "MS2-LD-E", "level": 7.684, "polygon": _rect(1.25, 3.85, 2.5, 5.0)}],
                          ms2["polygon"])
    # bound content (step 6); itemised from T-418 face parts and this census
    gf_bound = L.bound_check(2.9225, [
        {"id": "MS1-L treads beyond the candidate tread figure", "m2": round(3.080 + 1.035 - 3.425, 4), "kind": "TREAD"},
        {"id": "MS1-T winders (NW quarter, T-418)", "m2": 1.3225, "kind": "WINDER"},
        {"id": "central divider", "m2": 0.680, "kind": "SOLID"},
        {"id": "strip north of the divider end (unread)", "m2": 0.230, "kind": "UNREAD"}])
    arr2 = next(r for r in res["ST-01"]["rows"] if r["id"] == "ST01-2F-ARRIVAL")["area_m2"]
    ld2 = next(r for r in res["ST-01"]["rows"] if r["id"] == "ST01-MS2-LD")["area_m2"]
    f2_bound = L.bound_check(9.225, [
        {"id": "2F arrival (F-1)", "m2": arr2, "kind": "LANDING"},
        {"id": "2F guard / slab-edge band y 0.45 .. 0.50, x 0 .. 1.35", "m2": 0.0675, "kind": "SOLID"},
        {"id": "MS2-U top tread y 0.55 .. 0.85 (B7 tread)", "m2": 0.345, "kind": "TREAD"},
        {"id": "MS2-LD (in plan inside the 2F void)", "m2": ld2, "kind": "LANDING"},
        {"id": "rest of the void residual (divider, well, flight parts not deducted)",
         "m2": round(9.225 - arr2 - 0.0675 - 0.345 - ld2, 6), "kind": "VOID"}])
    # 2F arrival vs 2F lobby porcelain: shared edge only
    lobby = box(2.5, -1.45, 4.5, -0.2)
    arr_poly = Polygon(next(p for p in st01 if p["id"] == "ST01-2F-ARRIVAL")["polygon"])
    adj = {"ST01-2F-ARRIVAL vs 2F lobby L-9bd25c0c (x 2.50 .. 4.50, y -1.45 .. -0.20)":
           round(arr_poly.intersection(lobby).area, 6)}
    rows = [dict(r, **{"edges": p.get("edges")}) for k, st in (("ST-01", st01), ("ST-02", st02), ("ST-03", st03))
            for r, p in zip(res[k]["rows"], st)]
    new = [r for r in rows if r["line"] is None and r["trade"] == "B7-04"]
    new_m2 = round(sum(r["area_m2"] for r in new), 6)
    cl = line_states()
    existing_b7 = round(sum(cl["lines"][r["line"]]["net"] for r in rows if r["line"] and r["trade"] == "B7-04"), 6)
    drawn_vs_line = {r["id"]: round(r["area_m2"] - cl["lines"][r["line"]]["net"], 6)
                     for r in rows if r["line"] and r["area_m2"] is not None}
    s = {"task": "T-493", "method": L.METHOD, "rule": L.RULE, "drawing_sha256_8": DXF_SHA8,
         "floor_levels": FLOOR_LEVELS, "rows": rows, "stacked": {k: v["stacked"] for k, v in res.items()},
         "b3_b7_shared_m2": 0.0, "ms2_ld_split": split,
         "ms2_ld_split_status": ("HELD as a split (W / E): the closing riser is drawn as the pair BE4 / 12B4 + BE5 / "
                                 "12B5 at x 1.25 / 1.30 (structural 5E2 at 1.30), but the 2F plan also draws the "
                                 "diagonal pair 2F1F / 2F20 across the east half (Q-ST-11, no stated meaning); the "
                                 "section A-A has one closing riser, so the total is established either way"),
         "bounds": {"L-1983e89d GF-R31F8AE:landings 0 .. 2.9225": gf_bound,
                    "L-5d2be30d 2F-R4D1B62:landings 0 .. 9.225": f2_bound},
         "adjacency_overlap_m2": adj, "under_nosing_beside": under_nosing(),
         "proposed_b7_04_lines": [{"part": r["id"], "m2": r["area_m2"], "level": r["level"],
                                   "material": r["material"], "basis": r["material_basis"]} for r in new],
         "proposed_new_b7_04_m2": new_m2, "existing_b7_04_landing_lines_m2": existing_b7,
         "b7_04_after_m2": round(new_m2 + existing_b7, 6),
         "held_high_retired_m2": round(2.9225 + 9.225, 6),
         "drawn_minus_line_m2": drawn_vs_line, "candidate_lines": cl, "drawn_line_checks": "PASS"}
    return s


def write_outputs(s):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    cols = ["id", "stair", "element", "level", "area_m2", "solid_cut_m2", "material", "material_basis", "trade",
            "status", "line", "line_state", "edges"]
    w.writerow(cols)
    for r in s["rows"]:
        w.writerow(["" if r[c] is None else r[c] for c in cols])
    return buf.getvalue(), json.dumps(s, indent=1, sort_keys=True) + "\n"


def main(argv):
    if argv[:1] == ["--extract"]:
        extract(argv[1])
        argv = ["--write"]
    x = json.loads(EXTRACT.read_text(encoding="utf-8"))
    c, j = write_outputs(build(x))
    if argv[:1] == ["--write"]:
        CENSUS.write_text(c, encoding="utf-8")
        SUMMARY.write_text(j, encoding="utf-8")
        print("written")
        return 0
    if argv[:1] == ["--check"]:
        ok = CENSUS.read_text(encoding="utf-8") == c and SUMMARY.read_text(encoding="utf-8") == j
        print("check", "PASS" if ok else "FAIL")
        return 0 if ok else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
