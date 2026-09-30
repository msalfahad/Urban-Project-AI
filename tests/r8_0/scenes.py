"""R8.0 scenes and their geometric truth.

HOW THE TRUTH IS BUILT (and why it is independent)

Every expected coordinate below is derived by hand from a closed-form point
map written next to the scene, e.g. ``lambda x, y: (-x, y)`` for an X mirror.
The map, the orientation sign and each number were worked out on paper from
the DXF placement rule

    WCS = OCS_to_WCS( insert_point + R(rotation) . S(xscale, yscale) . (p - base_point) )

and, for MINSERT, ``insert_point + R(rotation) . (col*col_spacing, row*row_spacing)``
(spacing is rotated, never scaled). No truth value is produced by
``engine/cad_adapter.py``, by the R8 kernel, or by the test-side reference
realiser. ``test_r8_0_truth.py`` cross-checks every map against ezdxf 1.4.4, an
independent code base, and checks that the stated orientation sign agrees
with the map. Nothing here is taken from, or tuned to, any real project.

THE LOCAL CURVE SET (block ``CURVES``, base point 0,0)

    ARC       centre (1000, 0), radius 500, 0 deg -> 90 deg (CCW in its frame)
              start S = (1500, 0)
              mid   M = (1000 + 500*sqrt(1/2), 500*sqrt(1/2))
              end   E = (1000, 500)
    LWPOLYLINE A = (1500, 0) -> B = (1000, 500), bulge = tan(90/4 deg) = sqrt(2) - 1
              the SAME physical quarter circle: centre (1000, 0), midpoint M,
              the arc lies to the RIGHT of the chord A->B, swept CCW
    LINE      (0, 0) -> (2000, 0)                       a straight reference

A map with orientation sign -1 (a reflection) reverses the sweep: the image
of S->E is traversed CW and the bulge arc lies to the LEFT of its chord.
"""

from __future__ import annotations

import math

R = 500.0
H = 500.0 * math.sqrt(0.5)                 # 353.5533905932738
BULGE_Q = math.sqrt(2.0) - 1.0             # tan(22.5 deg), a quarter circle

LOCAL = {
    "arc": {"CENTER": (1000.0, 0.0), "START_POINT": (1500.0, 0.0),
            "MID_SWEEP_POINT": (1000.0 + H, H), "END_POINT": (1000.0, 500.0),
            "SWEEP_DIRECTION": "CCW", "RADIUS": R},
    "bulge": {"VERTEX_A": (1500.0, 0.0), "ARC_MIDPOINT": (1000.0 + H, H),
              "VERTEX_B": (1000.0, 500.0), "SIDE_OF_CHORD": "RIGHT",
              "SWEEP_DIRECTION": "CCW", "CENTER": (1000.0, 0.0)},
    "line": {"A": (0.0, 0.0), "B": (2000.0, 0.0)},
}

CURVES_BLOCK = {"base": (0.0, 0.0), "entities": [
    {"kind": "ARC", "c": (1000.0, 0.0), "r": R, "a0": 0.0, "a1": 90.0, "layer": "A-DOOR"},
    {"kind": "LWPOLYLINE", "pts": [(1500.0, 0.0), (1000.0, 500.0)],
     "bulges": [BULGE_Q, 0.0], "layer": "A-DOOR"},
    {"kind": "LINE", "a": (0.0, 0.0), "b": (2000.0, 0.0), "layer": "A-WALL"},
]}


def _flip(d):
    return {"CCW": "CW", "CW": "CCW", "RIGHT": "LEFT", "LEFT": "RIGHT"}[d]


def curve_truth(f, sign, local=LOCAL, radius_scale=1.0):
    """Apply a HAND-WRITTEN point map to the hand-derived local truth."""
    a, b, ln = local["arc"], local["bulge"], local["line"]
    arc = {k: f(*a[k]) for k in ("CENTER", "START_POINT", "MID_SWEEP_POINT", "END_POINT")}
    arc["SWEEP_DIRECTION"] = a["SWEEP_DIRECTION"] if sign > 0 else _flip(a["SWEEP_DIRECTION"])
    arc["RADIUS"] = a["RADIUS"] * radius_scale
    bul = {k: f(*b[k]) for k in ("VERTEX_A", "ARC_MIDPOINT", "VERTEX_B", "CENTER")}
    bul["SIDE_OF_CHORD"] = b["SIDE_OF_CHORD"] if sign > 0 else _flip(b["SIDE_OF_CHORD"])
    bul["SWEEP_DIRECTION"] = b["SWEEP_DIRECTION"] if sign > 0 else _flip(b["SWEEP_DIRECTION"])
    return {"arc": arc, "bulge": bul, "line": {"A": f(*ln["A"]), "B": f(*ln["B"])},
            "orientation_sign": sign}


def _insert(block, at=(0.0, 0.0), scale=(1.0, 1.0), rot=0.0, extrusion=(0.0, 0.0, 1.0), **kw):
    e = {"kind": "INSERT", "block": block, "at": at, "scale": scale, "rot": rot,
         "extrusion": extrusion}
    e.update(kw)
    return e


# ---------------------------------------------------------------- curves
# (fixture, scene id, what, scene, map, sign, derivation)

CURVE_CASES = [
    ("F02", "F02_MIRROR_X", "mirror X: scale (-1, 1)",
     {"blocks": {"CURVES": CURVES_BLOCK}, "entities": [_insert("CURVES", scale=(-1.0, 1.0))]},
     lambda x, y: (-x, y), -1, "S=diag(-1,1): (x,y)->(-x,y); det -1"),
    ("F02", "F02_MIRROR_Y", "mirror Y: scale (1, -1)",
     {"blocks": {"CURVES": CURVES_BLOCK}, "entities": [_insert("CURVES", scale=(1.0, -1.0))]},
     lambda x, y: (x, -y), -1, "S=diag(1,-1): (x,y)->(x,-y); det -1"),
    ("F02", "F02_NEG_SCALE_X", "negative scale X: scale (-2, 2) at (10000, 5000)",
     {"blocks": {"CURVES": CURVES_BLOCK},
      "entities": [_insert("CURVES", at=(10000.0, 5000.0), scale=(-2.0, 2.0))]},
     lambda x, y: (10000.0 - 2.0 * x, 5000.0 + 2.0 * y), -1,
     "(x,y)->(10000-2x, 5000+2y); det -4; radius x2"),
    ("F02", "F02_NEG_SCALE_Y", "negative scale Y: scale (1.5, -1.5) at (-3000, 2000)",
     {"blocks": {"CURVES": CURVES_BLOCK},
      "entities": [_insert("CURVES", at=(-3000.0, 2000.0), scale=(1.5, -1.5))]},
     lambda x, y: (-3000.0 + 1.5 * x, 2000.0 - 1.5 * y), -1,
     "(x,y)->(-3000+1.5x, 2000-1.5y); det -2.25; radius x1.5"),
    ("F02", "F02_ROTATION_REFLECTION", "rotation + reflection: scale (-1, 1), rotation 90",
     {"blocks": {"CURVES": CURVES_BLOCK}, "entities": [_insert("CURVES", scale=(-1.0, 1.0), rot=90.0)]},
     lambda x, y: (-y, -x), -1, "scale: (x,y)->(-x,y); rotate +90: (u,v)->(-v,u) => (-y,-x); det -1"),
    ("F05", "F05_NESTED_ROTATION_REFLECTION",
     "nested rotation + reflection: inner scale (1,-1) at (100,0); outer rotation 90 at (5000,0)",
     {"blocks": {"CURVES": CURVES_BLOCK,
                 "MID": {"base": (0.0, 0.0), "entities": [_insert("CURVES", at=(100.0, 0.0), scale=(1.0, -1.0))]}},
      "entities": [_insert("MID", at=(5000.0, 0.0), rot=90.0)]},
     lambda x, y: (5000.0 + y, x + 100.0), -1,
     "inner (x,y)->(x+100,-y)=(u,v); outer (u,v)->(5000-v, u) => (5000+y, x+100); det -1"),
    ("F05", "F05_DOUBLE_REFLECTION_CANCELS",
     "two reflections that cancel: inner scale (-1,1); outer scale (1,-1)",
     {"blocks": {"CURVES": CURVES_BLOCK,
                 "MIDX": {"base": (0.0, 0.0), "entities": [_insert("CURVES", scale=(-1.0, 1.0))]}},
      "entities": [_insert("MIDX", scale=(1.0, -1.0))]},
     lambda x, y: (-x, -y), +1, "(x,y)->(-x,y)->(-x,-y): a 180 deg rotation; det +1"),
    ("F05", "F05_NESTED_BLOCK_MIRROR",
     "nested block mirror: inner plain at (300,0); outer scale (-1,1) at (7000,1000)",
     {"blocks": {"CURVES": CURVES_BLOCK,
                 "MID": {"base": (0.0, 0.0), "entities": [_insert("CURVES", at=(300.0, 0.0))]}},
      "entities": [_insert("MID", at=(7000.0, 1000.0), scale=(-1.0, 1.0))]},
     lambda x, y: (6700.0 - x, 1000.0 + y), -1,
     "(x,y)->(x+300,y)->(7000-(x+300), 1000+y); det -1"),
    ("F03", "F03_OCS_NEG_Z_INSERT", "OCS -Z reflection on an INSERT at OCS (2000,0)",
     {"blocks": {"CURVES": CURVES_BLOCK},
      "entities": [_insert("CURVES", at=(2000.0, 0.0), extrusion=(0.0, 0.0, -1.0))]},
     lambda x, y: (-x - 2000.0, y), -1,
     "arbitrary axis for N=(0,0,-1): Ax=(-1,0,0), Ay=(0,1,0) => OCS (x,y) -> WCS (-x,y); "
     "block placed at OCS (x+2000, y) => WCS (-x-2000, y)"),
    ("F03", "F03_OCS_NEG_Z_ENTITIES", "ARC and bulged LWPOLYLINE stored in OCS -Z at top level; LINE is WCS-native",
     {"entities": [dict(e, extrusion=(0.0, 0.0, -1.0)) for e in CURVES_BLOCK["entities"]]},
     None, -1,
     "ARC/LWPOLYLINE: OCS (x,y) -> WCS (-x,y). LINE start/end are WCS whatever its extrusion"),
    ("F03", "F03_OCS_POS_Z_CONTROL", "explicit extrusion (0,0,1): identity (control)",
     {"entities": [dict(e, extrusion=(0.0, 0.0, 1.0)) for e in CURVES_BLOCK["entities"]]},
     lambda x, y: (x, y), +1, "identity"),
    ("F02", "F02_ROTATION_ONLY_CONTROL", "rotation only: rotation 90 at (1000,1000) (control, det +1)",
     {"blocks": {"CURVES": CURVES_BLOCK}, "entities": [_insert("CURVES", at=(1000.0, 1000.0), rot=90.0)]},
     lambda x, y: (1000.0 - y, 1000.0 + x), +1, "(x,y)->(1000-y, 1000+x); det +1"),
    ("F02", "F02_SCALED_HALF_TURN_CONTROL", "scale 2 and rotation 180 (control, det +4)",
     {"blocks": {"CURVES": CURVES_BLOCK}, "entities": [_insert("CURVES", scale=(2.0, 2.0), rot=180.0)]},
     lambda x, y: (-2.0 * x, -2.0 * y), +1, "(x,y)->(-2x,-2y); det +4; radius x2"),
]


def curve_case_truth(case):
    fx, sid, what, scene, f, sign, deriv = case
    if sid == "F03_OCS_NEG_Z_ENTITIES":
        # the LINE is WCS-native: identity for the line, OCS map for curves
        t = curve_truth(lambda x, y: (-x, y), -1)
        t["line"] = {"A": (0.0, 0.0), "B": (2000.0, 0.0)}
        return t
    radius_scale = {"F02_NEG_SCALE_X": 2.0, "F02_NEG_SCALE_Y": 1.5,
                    "F02_SCALED_HALF_TURN_CONTROL": 2.0}.get(sid, 1.0)
    return curve_truth(f, sign, radius_scale=radius_scale)


# ------------------------------------------------------------ base point

BP_H = 500.0 * math.sqrt(0.5)
BP_BLOCK = {"base": (500.0, 250.0), "entities": [
    {"kind": "ARC", "c": (1000.0, 250.0), "r": R, "a0": 0.0, "a1": 90.0},
    {"kind": "LWPOLYLINE", "pts": [(1500.0, 250.0), (1000.0, 750.0)], "bulges": [BULGE_Q, 0.0]},
    {"kind": "LINE", "a": (500.0, 250.0), "b": (1500.0, 250.0)},
]}
BP_LOCAL = {
    "arc": {"CENTER": (1000.0, 250.0), "START_POINT": (1500.0, 250.0),
            "MID_SWEEP_POINT": (1000.0 + BP_H, 250.0 + BP_H), "END_POINT": (1000.0, 750.0),
            "SWEEP_DIRECTION": "CCW", "RADIUS": R},
    "bulge": {"VERTEX_A": (1500.0, 250.0), "ARC_MIDPOINT": (1000.0 + BP_H, 250.0 + BP_H),
              "VERTEX_B": (1000.0, 750.0), "SIDE_OF_CHORD": "RIGHT", "SWEEP_DIRECTION": "CCW",
              "CENTER": (1000.0, 250.0)},
    "line": {"A": (500.0, 250.0), "B": (1500.0, 250.0)},
}

BASE_POINT_CASES = [
    ("F01", "F01_BASE_POINT_PLAIN", "base (500,250); INSERT at (10000,20000)",
     {"blocks": {"BP": BP_BLOCK}, "entities": [_insert("BP", at=(10000.0, 20000.0))]},
     lambda x, y: (x - 500.0 + 10000.0, y - 250.0 + 20000.0), +1, 1.0,
     "(x,y)->(x-500+10000, y-250+20000)"),
    ("F01", "F01_BASE_POINT_ROTATED", "base (500,250); rotation 90",
     {"blocks": {"BP": BP_BLOCK}, "entities": [_insert("BP", rot=90.0)]},
     lambda x, y: (250.0 - y, x - 500.0), +1, 1.0, "(x-500, y-250) rotated +90 => (250-y, x-500)"),
    ("F01", "F01_BASE_POINT_SCALED", "base (500,250); scale 2",
     {"blocks": {"BP": BP_BLOCK}, "entities": [_insert("BP", scale=(2.0, 2.0))]},
     lambda x, y: (2.0 * x - 1000.0, 2.0 * y - 500.0), +1, 2.0, "2*(x-500, y-250)"),
    ("F01", "F01_BASE_POINT_MIRRORED", "base (500,250); scale (-1,1)",
     {"blocks": {"BP": BP_BLOCK}, "entities": [_insert("BP", scale=(-1.0, 1.0))]},
     lambda x, y: (500.0 - x, y - 250.0), -1, 1.0, "(-(x-500), y-250); det -1"),
    ("F01", "F01_BASE_POINT_NESTED", "inner base (500,250) at (100,100) inside OUT with base (50,50)",
     {"blocks": {"BP": BP_BLOCK,
                 "OUT": {"base": (50.0, 50.0), "entities": [_insert("BP", at=(100.0, 100.0))]}},
      "entities": [_insert("OUT")]},
     lambda x, y: (x - 450.0, y - 200.0), +1, 1.0,
     "inner (x-500+100, y-250+100)=(x-400,y-150); outer minus (50,50) => (x-450, y-200)"),
]


def base_point_truth(case):
    fx, sid, what, scene, f, sign, rs, deriv = case
    return curve_truth(f, sign, local=BP_LOCAL, radius_scale=rs)


# --------------------------------------------------------------- MINSERT

CELL = {"base": (0.0, 0.0), "entities": [{"kind": "LINE", "a": (0.0, 0.0), "b": (100.0, 0.0)}]}


def _minsert(at=(0.0, 0.0), scale=(1.0, 1.0), rot=0.0, cols=3, rows=2, col_sp=1000.0, row_sp=500.0):
    return {"kind": "MINSERT", "block": "CELL", "at": at, "scale": scale, "rot": rot,
            "cols": cols, "rows": rows, "col_sp": col_sp, "row_sp": row_sp}


def _grid(seg):
    return sorted(seg(c, r) for c in range(3) for r in range(2))


MINSERT_CASES = [
    ("F06", "F06_MINSERT_GRID", "3 columns x 2 rows, spacing 1000 x 500",
     {"blocks": {"CELL": CELL}, "entities": [_minsert()]},
     _grid(lambda c, r: ((1000.0 * c, 500.0 * r), (1000.0 * c + 100.0, 500.0 * r))),
     "cell (c,r) at (1000c, 500r); line +100 in x"),
    ("F06", "F06_MINSERT_ROTATED", "grid rotated 90",
     {"blocks": {"CELL": CELL}, "entities": [_minsert(rot=90.0)]},
     _grid(lambda c, r: ((-500.0 * r, 1000.0 * c), (-500.0 * r, 1000.0 * c + 100.0))),
     "offset (1000c,500r) rotated +90 = (-500r, 1000c); line becomes +100 in y"),
    ("F06", "F06_MINSERT_SCALED", "content scaled 2, spacing NOT scaled",
     {"blocks": {"CELL": CELL}, "entities": [_minsert(scale=(2.0, 2.0))]},
     _grid(lambda c, r: ((1000.0 * c, 500.0 * r), (1000.0 * c + 200.0, 500.0 * r))),
     "spacing is in parent units and is rotated, not scaled"),
    ("F06", "F06_MINSERT_NESTED", "grid inside HOLDER; HOLDER at (5000,5000)",
     {"blocks": {"CELL": CELL, "HOLDER": {"base": (0.0, 0.0), "entities": [_minsert()]}},
      "entities": [_insert("HOLDER", at=(5000.0, 5000.0))]},
     _grid(lambda c, r: ((5000.0 + 1000.0 * c, 5000.0 + 500.0 * r),
                         (5100.0 + 1000.0 * c, 5000.0 + 500.0 * r))),
     "+ (5000,5000)"),
    ("F06", "F06_MINSERT_MIRRORED_PARENT", "grid inside HOLDER; HOLDER scale (-1,1)",
     {"blocks": {"CELL": CELL, "HOLDER": {"base": (0.0, 0.0), "entities": [_minsert()]}},
      "entities": [_insert("HOLDER", scale=(-1.0, 1.0))]},
     _grid(lambda c, r: ((-1000.0 * c, 500.0 * r), (-1000.0 * c - 100.0, 500.0 * r))),
     "(x,y)->(-x,y)"),
]


def norm_segments(segs):
    """Order-free form of a segment multiset (each segment's ends sorted)."""
    return sorted(tuple(sorted((tuple(a), tuple(b)))) for a, b in segs)


# ------------------------------------------------------------------ XREF

XREF_CASES = [
    ("F08", "F08_XREF_RESOLVED", "attached xref, resolved at authoring time; content lives in another file",
     {"blocks": {"XR": {"entities": [], "xref": {"path": "ext_resolved.dwg", "resolved": True}}},
      "entities": [_insert("XR")]},
     {"finding": "XREF_CONTENT_NOT_IN_SOURCE", "attachment": "ATTACH", "blocks_final": True}),
    ("F08", "F08_XREF_MISSING", "attached xref that did not resolve",
     {"blocks": {"XR": {"entities": [], "xref": {"path": "missing.dwg", "resolved": False}}},
      "entities": [_insert("XR")]},
     {"finding": "XREF_NOT_RESOLVED", "attachment": "ATTACH", "blocks_final": True}),
    ("F08", "F08_XREF_NESTED", "xref placed inside an ordinary block",
     {"blocks": {"XR": {"entities": [], "xref": {"path": "nested.dwg", "resolved": False}},
                 "HOLDER": {"entities": [_insert("XR", at=(100.0, 0.0))]}},
      "entities": [_insert("HOLDER", at=(1000.0, 0.0))]},
     {"finding": "XREF_NOT_RESOLVED", "attachment": "ATTACH", "blocks_final": True, "nested": True}),
    ("F08", "F08_XREF_UNLOADED", "xref present but unloaded",
     {"blocks": {"XR": {"entities": [], "xref": {"path": "unloaded.dwg", "resolved": True, "unloaded": True}}},
      "entities": [_insert("XR")]},
     {"finding": "XREF_UNLOADED", "attachment": "ATTACH", "blocks_final": True}),
    ("F08", "F08_XREF_OVERLAY", "overlay attachment (does not propagate to host's hosts)",
     {"blocks": {"XR": {"entities": [], "xref": {"path": "overlay.dwg", "resolved": False, "overlay": True}}},
      "entities": [_insert("XR")]},
     {"finding": "XREF_NOT_RESOLVED", "attachment": "OVERLAY", "blocks_final": True}),
]


# ------------------------------------------------ frames that cannot be plan

FRAME_CASES = [
    ("F34", "F34_TILTED_EXTRUSION", "ARC on a tilted plane N=(0,0.6,0.8)", [0.0, 0.6, 0.8], "UNSUPPORTED_FRAME"),
    ("F34", "F34_UNREADABLE_ZERO", "extrusion (0,0,0): not a direction", [0.0, 0.0, 0.0], "FRAME_UNREADABLE"),
    ("F34", "F34_UNREADABLE_NULL", "extrusion present but null", "NULL", "FRAME_UNREADABLE"),
    ("F34", "F34_UNREADABLE_SHORT", "extrusion with two components", [0.0, 1.0], "FRAME_UNREADABLE"),
    ("F34", "F34_UNREADABLE_TEXT", "extrusion with a non-numeric component", ["z", 0.0, 1.0], "FRAME_UNREADABLE"),
]


def frame_scene(extrusion):
    return {"entities": [{"kind": "ARC", "c": (1000.0, 0.0), "r": R, "a0": 0.0, "a1": 90.0,
                          "extrusion": extrusion}]}


# ------------------------------------------ objects a decoder may not realise

SKIP_CASES = [
    ("F35", "F35_OLE2FRAME_IN_BLOCK", "OLE2FRAME inside a placed block",
     {"blocks": {"OLEBLK": {"entities": [{"kind": "OLE2FRAME"}, {"kind": "LINE", "a": (0, 0), "b": (100, 0)}]}},
      "entities": [_insert("OLEBLK")]}, "74"),
    ("F36", "F36_PROXY_ENTITY", "ACAD_PROXY_ENTITY at top level",
     {"entities": [{"kind": "ACAD_PROXY_ENTITY", "layer": "A-WALL"}]}, "498"),
    ("F19", "F19_CUSTOM_ON_WALL_LAYER", "custom-class entity (type 512) on a wall layer",
     {"entities": [{"kind": "CUSTOM", "type_code": 512, "name": "AEC_WALL", "layer": "A-WALL"},
                   {"kind": "LINE", "a": (0, 0), "b": (3000, 0), "layer": "A-WALL"}]}, "512"),
]


# ------------------------------------------------- non-uniform scale (F04)

F04_SCENE = {"blocks": {"CURVES": CURVES_BLOCK}, "entities": [_insert("CURVES", scale=(2.0, 1.0))]}
F04_MAP = (lambda x, y: (2.0 * x, y))
F04_TRUTH_POINTS = {"START_POINT": F04_MAP(1500.0, 0.0), "MID_SWEEP_POINT": F04_MAP(1000.0 + H, H),
                    "END_POINT": F04_MAP(1000.0, 500.0)}   # an elliptical arc; no circle passes these with centre (2000,0)


# ------------------------------------------- rotated linear dimension (F10)
# DIMENSION_LINEAR (type 21) measures the PROJECTION of the extension-line
# origins onto the dimension direction. Horizontal dimension (rotation 0),
# origins (0,0) and (3000,400): projected measurement = |3000 - 0| = 3000.
F10_ORIGINS = ((0.0, 0.0), (3000.0, 400.0))
F10_PROJECTED_MM = 3000.0


# ------------------------------------------------- MTEXT literal decode (F11)
# Contract (fixed here, from the MTEXT format codes, not from any donor):
# \A<n>; alignment -> removed; {\f<font>|...;TEXT} -> TEXT; \P -> newline;
# %%c -> U+2300 DIAMETER SIGN; %%d -> U+00B0; %%p -> U+00B1; \~ -> no-break space
F11_RAW = "\\A1;{\\fArial|b0|i0;DOOR}\\PD01 %%c50 %%d %%p"
F11_LITERAL = "DOOR\nD01 ⌀50 ° ±"
