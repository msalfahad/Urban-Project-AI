"""Coverage-recovery round - geometry extracts from the frozen K2 decodes of ST7757.dxf and P7757.dxf.

Writes two registers the blind build reads (so the build and its tests run without the drawings):

  GROUND_SLAB_CELL_EXTRACT.json   cells of the founded footprints on the GROUND BEAMS sheet (generic
                                  ground_slab_recovery.decompose over 300 mm bands of layers 1+2, arcs, columns and
                                  single structural lines), each split into the part already released by V3a / V3b
                                  zones and the unreleased remainder, with the texts inside.
  WALL_FACE_PAIR_EXTRACT.json     Method B of WALL_BAND_RECONCILIATION: parallel-face pairs of the wall layer at 150 /
                                  200 mm per floor plan, plus column outlines and opening-symbol extents for the
                                  classification.

No reference or oracle quantity is read. Inputs are identified by the dxf sha256 carried inside each decode.
    python research/coverage_recovery_round/extract_geometry.py <st7757_k2.pkl> <p7757_k2.pkl>
"""

from __future__ import annotations

import hashlib
import json
import pickle
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
LAB = ROOT / "research" / "external_engine_lab"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(LAB))

from engine.source import canonical_input as CI  # noqa: E402
from engine.source import ground_slab_recovery as GS  # noqa: E402
from engine.source import wall_band_reconciliation as WB  # noqa: E402

# sheet frames (FLOOR_PLAN_REGISTER of phase A, tests/alsenan/registers/FLOOR_PLAN_REGISTER.json)
GROUND_BEAMS_SHEET = (78930.0, 29036.0, 114124.0, 57066.0)
ARCH_PLANS = {"GF": (-164713.0, -811916.0, -124398.0, -783886.0), "1F": (-209565.0, -811916.0, -169251.0, -783886.0),
              "2F": (-254418.0, -811916.0, -214104.0, -783886.0)}
WALL_LAYER, COLUMN_LAYER, DOOR_LAYERS = "1", "S-COL.BON", ("D", "W")
WIDTHS = (150.0, 200.0)


def inb(x, y, b):
    return b[0] <= x <= b[2] and b[1] <= y <= b[3]


def lay(p):
    return CI.effective_layer(p)[0]


def ground_cells(S):
    import alsenan_phase_b2a as B2A
    import alsenan_v3_structure as V3S
    from shapely.geometry import LineString, Point, Polygon
    from shapely.ops import unary_union
    sb = GROUND_BEAMS_SHEET
    segs = [p for p in S["parts"] if p.kind == "SEGMENT" and lay(p) in ("1", "2") and inb(p.geometry[0], p.geometry[1], sb)]
    arcs = [p for p in S["parts"] if p.kind == "ARC" and lay(p) in ("1", "2") and inb(p.geometry[0], p.geometry[1], sb)]
    cols = [Polygon(B2A._rect_poly(r)) for r in B2A._col_rects(S, sb)]
    bands = V3S._pair_bands(segs, width=300.0, tol=12.0) + V3S._arc_bands(arcs, width=300.0, tol=12.0)
    thin = [LineString([(p.geometry[0], p.geometry[1]), (p.geometry[2], p.geometry[3])]).buffer(1.0) for p in segs]
    texts = [(t.x, t.y, t.value.strip()) for t in sorted(S["texts"], key=lambda q: q.identity.key)
             if t.x is not None and t.value and inb(t.x, t.y, sb)]
    cells = GS.decompose([b["poly"] for b in bands] + cols + thin, labels=texts)
    # released regions of the frozen V3a / V3b ground zones (same construction as those rounds)
    seg1 = [p for p in segs if lay(p) == "1"]
    arc1 = [p for p in arcs if lay(p) == "1"]
    b1 = V3S._pair_bands(seg1, width=300.0, tol=12.0) + V3S._arc_bands(arc1, width=300.0, tol=12.0)
    u1 = unary_union([b["poly"] for b in b1] + cols)
    u12 = unary_union([b["poly"] for b in bands] + cols + thin)
    released = []
    for x, y, t in texts:
        if "T=" not in t:
            continue
        pt = Point(x, y)
        hit1 = [Polygon(c.exterior) for c in getattr(u1, "geoms", [u1]) if Polygon(c.exterior).contains(pt)]
        if hit1:                                         # V3a zone (layer 1 only)
            outer = min(hit1, key=lambda p: p.area)
            released.append(("V3A_ZONE", outer.difference(u1)))
            continue
        hit = [Polygon(c.exterior) for c in getattr(u12, "geoms", [u12]) if Polygon(c.exterior).contains(pt)]
        if hit:                                          # V3b cross-layer zone
            outer = min(hit, key=lambda p: p.area)
            rest = outer.difference(u12)
            keep = [q for q in getattr(rest, "geoms", [rest]) if 2 * q.area / q.length >= 450.0]
            released.append(("V3B_ZONE", unary_union(keep)))
    rel = unary_union([g for _, g in released])
    from shapely import wkt as W
    out = []
    for c in cells:
        poly = W.loads(c["wkt"])
        inside = poly.intersection(rel)
        a_in = inside.area / 1e6
        for suffix, geom, part in ((":R", inside, "RELEASED_ZONE_PART"), (":X", poly.difference(rel), "EXTENSION")):
            a = geom.area / 1e6
            if a < 1e-4:
                continue
            g = [q for q in getattr(geom, "geoms", [geom]) if q.area > 0]
            perim = sum(q.length for q in g)
            out.append({"cell_id": c["cell_id"] + suffix, "parent_cell": c["cell_id"], "footprint_id": c["footprint_id"],
                        "footprint_area_m2": round(c["footprint_area_m2"], 4), "part": part, "area_m2": round(a, 4),
                        "eff_width_mm": round(2.0 * geom.area / perim, 1) if perim else 0.0,
                        "labels": [t for (x, y, t) in texts if geom.buffer(1.0).contains(Point(x, y))],
                        "parent_area_m2": round(c["area_m2"], 4), "parent_released_m2": round(a_in, 4)})
    return {"sheet_bounds": GROUND_BEAMS_SHEET, "bands": len(bands), "columns": len(cols),
            "released_zones": [{"kind": k, "area_m2": round(g.area / 1e6, 4)} for k, g in released],
            "cells": out, "rule": "cells = founded footprint - 300 mm bands (layers 1+2, arcs) - columns - single "
                                  "structural lines; RELEASED_ZONE_PART = inside the V3a / V3b T= zones"}


def _boxes(geoms, grow=0.0):
    from shapely.ops import unary_union
    u = unary_union([g.buffer(grow) for g in geoms]) if geoms else None
    if u is None or u.is_empty:
        return []
    return [tuple(round(v, 1) for v in g.bounds) for g in getattr(u, "geoms", [u])]


def wall_pairs(P):
    from shapely.geometry import LineString, Point
    out = {}
    for fl, sb in ARCH_PLANS.items():
        segs = [(p.identity.key,) + tuple(p.geometry[:4]) for p in sorted(P["parts"], key=lambda q: q.identity.key)
                if p.kind == "SEGMENT" and lay(p) == WALL_LAYER and inb(p.geometry[0], p.geometry[1], sb)]
        cols = [LineString([(p.geometry[0], p.geometry[1]), (p.geometry[2], p.geometry[3])])
                for p in P["parts"] if p.kind == "SEGMENT" and lay(p) == COLUMN_LAYER and inb(p.geometry[0], p.geometry[1], sb)]
        opn = []
        for p in P["parts"]:
            if lay(p) not in DOOR_LAYERS or not inb(p.geometry[0], p.geometry[1], sb):
                continue
            if p.kind == "SEGMENT":
                opn.append(LineString([(p.geometry[0], p.geometry[1]), (p.geometry[2], p.geometry[3])]))
            elif p.kind == "ARC":
                opn.append(Point(p.geometry[0], p.geometry[1]).buffer(abs(p.geometry[2])))
        col_boxes = _boxes([c.buffer(0.5) for c in cols], grow=5.0)
        opn_boxes = _boxes(opn, grow=25.0)
        fl_out = {"segments": len(segs), "column_boxes": col_boxes, "opening_boxes": opn_boxes, "pairs": {}}
        for w in WIDTHS:
            iv = WB.pair_parallel_faces(segs, w, tol=15.0, min_overlap=200.0)
            fl_out["pairs"][str(int(w))] = [{"a": x["a"], "b": x["b"], "width": x["width"], "length": round(x["length"], 1),
                                             "p0": [round(v, 1) for v in x["p0"]], "p1": [round(v, 1) for v in x["p1"]],
                                             "axis": [round(v, 6) for v in x["axis"]]} for x in iv]
        out[fl] = fl_out
    return {"layer": WALL_LAYER, "column_layer": COLUMN_LAYER, "opening_layers": list(DOOR_LAYERS),
            "widths_mm": list(WIDTHS), "floors": out,
            "rule": "Method B: nearest parallel faces of the wall layer at the nominal width +/- 15 mm, overlap > 200 mm"}


def dumps(o):
    return json.dumps(o, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def main(st_pkl, ar_pkl):
    S = pickle.load(open(st_pkl, "rb"))
    P = pickle.load(open(ar_pkl, "rb"))
    src = {"ST7757.dxf": S.get("dxf_sha256"), "P7757.dxf": P.get("dxf_sha256")}
    files = {"GROUND_SLAB_CELL_EXTRACT.json": dict(ground_cells(S), source=src),
             "WALL_FACE_PAIR_EXTRACT.json": dict(wall_pairs(P), source=src)}
    for k, v in files.items():
        (HERE / k).write_text(dumps(v), encoding="utf-8")
        print(k, hashlib.sha256(dumps(v).encode()).hexdigest()[:16])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
