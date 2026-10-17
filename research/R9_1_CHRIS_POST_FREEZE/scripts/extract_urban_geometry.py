"""R9.1 - Urban-side object geometry for the object-level crosswalk (research only, read-only).

Re-runs the frozen Urban research builders (alsenan_v3_structure._pair_bands / _arc_bands and the span split of
alsenan_v3_structure.ground) on the frozen K2 decode of ST7757.dxf, and writes the geometry the frozen registers do
not store: band face handles, centreline coordinates, span polygons and column boxes. Nothing in engine/ is changed
and no christiannp value is read here (this extract is Urban-only; the crosswalk reads it afterwards).

    python research/R9_1_CHRIS_POST_FREEZE/scripts/extract_urban_geometry.py <st7757_k2.pkl>
"""

from __future__ import annotations

import hashlib
import json
import math
import pickle
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "urban_extract"
ROOT = HERE.parents[2]
LAB = ROOT / "research" / "external_engine_lab"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(LAB))

from engine.source import canonical_input as CI  # noqa: E402

GB_SHEET = (78930.0, 29036.0, 114124.0, 57066.0)          # FLOOR_PLAN_REGISTER (phase A) ground-beams sheet frame


def inb(x, y, b):
    return b[0] <= x <= b[2] and b[1] <= y <= b[3]


def lay(p):
    return CI.effective_layer(p)[0]


def hid(key):
    """'ALSENAN_ST7757_DXF|H248|...' -> 248 (decimal of the DXF hex handle)."""
    return int(key.split("|")[1][1:])


def r1(v):
    return round(float(v), 1)


def ground_geometry(S):
    import alsenan_phase_b2a as B2A
    import alsenan_v3_structure as V3S
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    sb = GB_SHEET
    segs = [p for p in S["parts"] if p.kind == "SEGMENT" and lay(p) == "1" and inb(p.geometry[0], p.geometry[1], sb)]
    arcs = [p for p in S["parts"] if p.kind == "ARC" and lay(p) == "1" and inb(p.geometry[0], p.geometry[1], sb)]
    rects = B2A._col_rects(S, sb)
    cols = [Polygon(B2A._rect_poly(r)) for r in rects]
    bands = V3S._pair_bands(segs, width=300.0, tol=12.0) + V3S._arc_bands(arcs, width=300.0, tol=12.0)
    col_u = unary_union(cols)
    out_b = []
    for b in bands:
        ids = b["id"].replace("ARC:", "").split("+")
        poly = b["poly"]
        rec = {"band_id": b["id"], "face_handles_dec": [int(i[1:]) for i in ids],
               "face_handles_hex": [format(int(i[1:]), "X") for i in ids], "curved": b.get("u") is None,
               "bbox": [r1(v) for v in poly.bounds], "area_m2": round(poly.area / 1e6, 4)}
        if b.get("u") is not None:
            u = b["u"]
            cs = list(poly.exterior.coords)[:4]
            mid0 = ((cs[0][0] + cs[3][0]) / 2, (cs[0][1] + cs[3][1]) / 2)
            mid1 = ((cs[1][0] + cs[2][0]) / 2, (cs[1][1] + cs[2][1]) / 2)
            rec.update(centreline=[[r1(mid0[0]), r1(mid0[1])], [r1(mid1[0]), r1(mid1[1])]],
                       gross_length_m=round(math.hypot(mid1[0] - mid0[0], mid1[1] - mid0[1]) / 1000.0, 4),
                       axis=[round(u[0], 6), round(u[1], 6)])
        else:
            rec.update(gross_length_m=round(b["arc_len"] / 1000.0, 4))
        pieces = poly.difference(col_u)
        sp = []
        for g in getattr(pieces, "geoms", [pieces]):
            if g.is_empty:
                continue
            kept = g.area >= 300 * 300
            sp.append({"bbox": [r1(v) for v in g.bounds], "centroid": [r1(g.centroid.x), r1(g.centroid.y)],
                       "length_m": round(V3S._band_len(g, b) / 1000.0, 6), "kept_as_span": kept,
                       "area_m2": round(g.area / 1e6, 4)})
        rec["pieces"] = sorted(sp, key=lambda z: (z["centroid"][0], z["centroid"][1]))
        rec["inside_columns_m2"] = round(poly.intersection(col_u).area / 1e6, 4)
        out_b.append(rec)
    segs_all = [{"handle_dec": hid(p.identity.key), "layer": lay(p), "p0": [r1(p.geometry[0]), r1(p.geometry[1])],
                 "p1": [r1(p.geometry[2]), r1(p.geometry[3])],
                 "length": r1(math.hypot(p.geometry[2] - p.geometry[0], p.geometry[3] - p.geometry[1]))}
                for p in sorted(segs, key=lambda q: q.identity.key)]
    return {"sheet_bounds": list(sb), "layer": "1", "rule": "_pair_bands(width=300, tol=12) + _arc_bands; spans = band - "
            "column rectangles, piece kept when area >= 300x300 mm", "bands": sorted(out_b, key=lambda z: z["band_id"]),
            "columns": [{"centre": [r1(r[3][0]), r1(r[3][1])], "w": r1(r[1]), "h": r1(r[2])} for r in rects],
            "layer1_segments": segs_all,
            "layer1_arcs": [{"handle_dec": hid(p.identity.key), "centre": [r1(p.geometry[0]), r1(p.geometry[1])],
                             "radius": r1(p.geometry[2])} for p in sorted(arcs, key=lambda q: q.identity.key)]}


ROOF_SHEETS = {"GF": (40205.0, 29036.0, 75400.0, 57066.0), "1F": (1481.0, 29036.0, 36675.0, 57066.0),
               "2F": (-37243.0, 29036.0, -2049.0, 57066.0)}   # FLOOR_PLAN_REGISTER STRU-S06 / S05 / S04


def slab_openings(S):
    """Re-runs engine.source.slab_region.regions with the frozen B2A inputs (element layers 1 + S-BEAM, S-OPENING,
    stair layers 2 / 5 / ST, VOID labels, stacked 'T' / 'nn' thickness tags) and keeps the opening rings, which the
    frozen SLAB_REGION_REGISTER does not store. band_points (plan-component selection) are approximated by the beam
    mark text points (B<n> / CB<n>); the reproduction check against the frozen register is recorded per floor."""
    import re
    import alsenan_phase_b2a as B2A
    from engine.source import slab_region as SR
    out = {}
    for fl, sb in ROOF_SHEETS.items():
        inb = lambda p: inb_(p, sb)
        segs = [(p.identity.key,) + tuple(p.geometry) for p in S["parts"] if p.kind == "SEGMENT" and lay(p) in ("1", "S-BEAM") and inb(p)]
        arcs = [(p.identity.key,) + tuple(p.geometry[:5]) for p in S["parts"] if p.kind == "ARC" and lay(p) in ("1", "S-BEAM") and inb(p)]
        rects = B2A._col_rects(S, sb)
        cols = [{"id": "COL:" + "+".join(sorted(r[0])[:2]), "polygon": B2A._rect_poly(r)} for r in rects]
        tx = sorted([t for t in S["texts"] if t.x is not None and t.value and inb_xy(t.x, t.y, sb)], key=lambda t: t.identity.key)
        ops = [(p.identity.key,) + tuple(p.geometry) for p in S["parts"] if p.kind == "SEGMENT" and lay(p) == "S-OPENING" and inb(p)]
        sts = [(p.identity.key,) + tuple(p.geometry) for p in S["parts"] if p.kind == "SEGMENT" and lay(p) in ("2", "5", "ST") and inb(p)]
        voids = [(t.x, t.y) for t in tx if t.value.strip().upper() == "VOID"]
        tags = []
        for t in tx:
            if t.value.strip() == "T":
                below = [u for u in tx if u is not t and re.fullmatch(r"\d{2}", u.value.strip()) and abs(u.x - t.x) < 300
                         and 0 < t.y - u.y < 500]
                if len(below) == 1:
                    tags.append({"t_cm": int(below[0].value.strip()), "x": t.x, "y": t.y,
                                 "handles": [hid(t.identity.key), hid(below[0].identity.key)]})
        bp = [(t.identity.key, t.x, t.y) for t in tx if re.fullmatch(r"C?B\d+", t.value.strip())]
        res = SR.regions(segments=segs, arcs=arcs, columns=cols, void_labels=voids, opening_segments=ops, stair_segments=sts,
                         thickness_tags=[{k: v for k, v in g.items() if k != "handles"} for g in tags], band_points=bp,
                         umm=1.0, eps=1.0)
        rings = res.pop("_rings")
        res.pop("_dangles", None)
        opn = [f for f in res["faces"] if f["role"] != "PLATE"]
        recs = []
        for f, ring in zip(opn, rings["openings"]):
            xs, ys = [q[0] for q in ring], [q[1] for q in ring]
            recs.append({"face": f["face"], "role": f["role"], "why": f.get("why"), "area_m2": round(f["area_m2"], 4),
                         "tags_cm": f.get("tags_cm") or [], "bbox": [r1(min(xs)), r1(min(ys)), r1(max(xs)), r1(max(ys))],
                         "bbox_local": [r1(min(xs) - sb[0]), r1(min(ys) - sb[1]), r1(max(xs) - sb[0]), r1(max(ys) - sb[1])]})
        frozen = json.loads((ROOT / "tests/alsenan/registers_b2a1/SLAB_REGION_REGISTER.json").read_text())["sheets"][fl]
        repro = {"gross": [round(res["gross_outline_area_m2"], 4), round(frozen["gross_outline_area_m2"], 4)],
                 "openings": [round(res["openings_area_m2"], 4), round(frozen["openings_area_m2"], 4)]}
        repro["REPRODUCES_FROZEN_B2A1"] = all(abs(a - b) < 1e-3 for a, b in repro.values())
        out[fl] = {"bounds": list(sb), "reproduction": repro, "gross_outline_area_m2": round(res["gross_outline_area_m2"], 4),
                   "net_plate_area_m2": round(res["net_plate_area_m2"], 4), "sheet_thickness_tags_cm": res["sheet_thickness_tags_cm"],
                   "thickness_tags": [{"t_cm": g["t_cm"], "handles_hex": [format(h, "X") for h in g["handles"]],
                                       "xy_local": [r1(g["x"] - sb[0]), r1(g["y"] - sb[1])]} for g in tags],
                   "void_labels_local": [[r1(x - sb[0]), r1(y - sb[1])] for x, y in voids],
                   "opening_segments_hex": sorted(format(hid(k[0]), "X") for k in ops),
                   "openings": sorted(recs, key=lambda z: z["bbox"])}
    return out


def inb_(p, b):
    return inb(p.geometry[0], p.geometry[1], b)


def inb_xy(x, y, b):
    return inb(x, y, b)


def ground_cell_polygons(S):
    """The coverage-round ground-slab cells (extract_geometry.ground_cells) with their polygons, which the frozen
    GROUND_SLAB_CELL_EXTRACT does not store; ids and areas are checked against that extract."""
    sys.path.insert(0, str(ROOT / "research" / "coverage_recovery_round"))
    import alsenan_phase_b2a as B2A
    import alsenan_v3_structure as V3S
    from shapely.geometry import LineString, Polygon
    from engine.source import ground_slab_recovery as GS
    sb = GB_SHEET
    segs = [p for p in S["parts"] if p.kind == "SEGMENT" and lay(p) in ("1", "2") and inb(p.geometry[0], p.geometry[1], sb)]
    arcs = [p for p in S["parts"] if p.kind == "ARC" and lay(p) in ("1", "2") and inb(p.geometry[0], p.geometry[1], sb)]
    cols = [Polygon(B2A._rect_poly(r)) for r in B2A._col_rects(S, sb)]
    bands = V3S._pair_bands(segs, width=300.0, tol=12.0) + V3S._arc_bands(arcs, width=300.0, tol=12.0)
    thin = [LineString([(p.geometry[0], p.geometry[1]), (p.geometry[2], p.geometry[3])]).buffer(1.0) for p in segs]
    cells = GS.decompose([b["poly"] for b in bands] + cols + thin)
    frozen = {c["parent_cell"]: c["parent_area_m2"]
              for c in json.loads((ROOT / "research/coverage_recovery_round/GROUND_SLAB_CELL_EXTRACT.json").read_text())["cells"]}
    from shapely import wkt as W
    out = []
    for c in cells:
        g = W.loads(c["wkt"])
        out.append({"cell_id": c["cell_id"], "area_m2": round(c["area_m2"], 4),
                    "frozen_area_m2": frozen.get(c["cell_id"]),
                    "exterior": [[r1(x), r1(y)] for x, y in g.exterior.coords],
                    "holes": [[[r1(x), r1(y)] for x, y in h.coords] for h in g.interiors]})
    degenerate = sorted(c["cell_id"] for c in out if c["frozen_area_m2"] is None and c["area_m2"] < 1e-3)
    out = [c for c in out if c["cell_id"] not in degenerate]
    return {"cells": out, "bands_layers_1_2": len(bands), "degenerate_cells_not_in_frozen_extract": degenerate,
            "REPRODUCES_FROZEN_EXTRACT": sorted(frozen) == sorted(c["cell_id"] for c in out) and all(
                abs(c["area_m2"] - c["frozen_area_m2"]) < 1e-3 for c in out)}


def dumps(o):
    return json.dumps(o, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def main(st_pkl):
    S = pickle.load(open(st_pkl, "rb"))
    OUT.mkdir(exist_ok=True)
    doc = dict(ground_geometry(S), source={"ST7757.dxf": S.get("dxf_sha256")})
    (OUT / "URBAN_GB_GEOMETRY_EXTRACT.json").write_text(dumps(doc), encoding="utf-8")
    print("URBAN_GB_GEOMETRY_EXTRACT.json", hashlib.sha256(dumps(doc).encode()).hexdigest()[:16], len(doc["bands"]))
    doc = dict(floors=slab_openings(S), source={"ST7757.dxf": S.get("dxf_sha256")},
               rule="engine.source.slab_region.regions re-run with the frozen B2A inputs; opening rings kept")
    (OUT / "URBAN_SLAB_OPENING_GEOMETRY_EXTRACT.json").write_text(dumps(doc), encoding="utf-8")
    print("URBAN_SLAB_OPENING_GEOMETRY_EXTRACT.json", hashlib.sha256(dumps(doc).encode()).hexdigest()[:16])
    doc = dict(ground_cell_polygons(S), source={"ST7757.dxf": S.get("dxf_sha256")})
    (OUT / "URBAN_GROUND_CELL_GEOMETRY_EXTRACT.json").write_text(dumps(doc), encoding="utf-8")
    print("URBAN_GROUND_CELL_GEOMETRY_EXTRACT.json", hashlib.sha256(dumps(doc).encode()).hexdigest()[:16],
          doc["REPRODUCES_FROZEN_EXTRACT"])


if __name__ == "__main__":
    main(sys.argv[1])
