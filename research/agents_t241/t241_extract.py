"""T-241 extractor: plan partition of the three roof-slab sheets against the beam bands and the column outlines.

Reads the private copy of Drive "Alsenan chalet project" / 'ST7757 dxf.dxf' (sha256 9f9d1179...38079) from .work/private,
the T-139 face polygons (research/agents_t139/slab_faces.py run on the same file) and the route G band polygons
(research/agents_t110/scripts/bands.py on the committed route G run, fit <= 0.6 mm). Writes ALSENAN_PARTITION_INPUT.json:
per face of every slab sheet its T-139 id, class and area, and the plan areas (m2) it shares with each route G band piece
and with each column outline of that sheet (S-COL.BON handle, hatch SOLID = column under the slab / PATTERN = member
starting on it). No coordinates and no drawing content are written: ids, handles, areas only.

    python3 -I research/agents_t139/slab_faces.py <ST7757 dxf> <scratch>/faces.json
    python3 -I research/agents_t110/scripts/bands.py research/urban_engine_m4_correctness/st7757_route_g <scratch>/bands.json
    python3 -I research/agents_t241/t241_extract.py <ST7757 dxf> <scratch>/faces.json <scratch>/bands.json [--write]
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
# slab-sheet windows in drawing mm (= research/agents_t139/slab_faces.py SHEETS)
SHEETS = {"GF": (40500, 74500, 35500, 51000), "1F": (11500, 36000, 35500, 51000), "2F": (-27000, -2000, 35500, 51000)}
MIN_M2 = 1e-5


def columns(path):
    import ezdxf
    from ezdxf import bbox
    from shapely.geometry import Polygon
    msp = ezdxf.readfile(str(path)).modelspace()
    hatches = []
    for e in msp.query('HATCH[layer=="S-COL.HAT"]'):
        b = bbox.extents([e])
        if b.has_data:
            hatches.append((b.center.x, b.center.y, b.size.x, b.size.y, e.dxf.pattern_name))
    out = {k: [] for k in SHEETS}
    for e in msp.query('LWPOLYLINE[layer=="S-COL.BON"]'):
        pts = [(p[0], p[1]) for p in e.get_points("xy")]
        if len(pts) < 3:
            continue
        b = bbox.extents([e])
        for sh, (x0, x1, y0, y1) in SHEETS.items():
            if x0 <= b.center.x <= x1 and y0 <= b.center.y <= y1:
                pats = {h[4] for h in hatches if abs(h[0] - b.center.x) <= b.size.x / 2 + 5
                        and abs(h[1] - b.center.y) <= b.size.y / 2 + 5 and h[2] <= b.size.x + 10 and h[3] <= b.size.y + 10}
                hatch = "SOLID" if pats == {"SOLID"} else ("PATTERN" if pats and "SOLID" not in pats else
                                                           ("NONE" if not pats else "MIXED"))
                poly = Polygon([(x / 1000.0, y / 1000.0) for x, y in pts]).buffer(0)
                out[sh].append({"h": e.dxf.handle, "hatch": hatch, "poly": poly})
    return out


def build(dxf, faces_json, bands_json):
    from shapely import wkt
    from shapely.geometry import Polygon
    if hashlib.sha256(Path(dxf).read_bytes()).hexdigest() != SHA:
        raise SystemExit("not the route G input (sha256 differs)")
    faces = json.load(open(faces_json, encoding="utf-8"))
    bands = json.load(open(bands_json, encoding="utf-8"))
    cls = {r["id"]: r["cls"] for r in csv.DictReader(open(ROOT / "research/agents_t139/PANELS.csv", encoding="utf-8"))}
    cols = columns(dxf)
    bpoly = {}
    for k, v in bands.items():
        bid, st = k.split("@")
        bpoly.setdefault(st, []).append((bid, v["title"], Polygon(v["pts"]).buffer(0)))
    out = {"schema": "T241_PARTITION_INPUT_V1", "source_dxf_sha256": SHA, "faces": [], "bands": [], "columns": []}
    for st in ("GF", "1F", "2F"):
        for bid, title, p in bpoly.get(st, []):
            out["bands"].append({"storey": st, "band": bid, "title": title, "area_m2": round(p.area, 5)})
        for c in cols[st]:
            out["columns"].append({"storey": st, "h": c["h"], "hatch": c["hatch"], "area_m2": round(c["poly"].area, 5)})
        for f in faces[st]:
            g = wkt.loads(f["wkt"]).buffer(0)
            row = {"storey": st, "id": f["id"], "cls": cls.get(f["id"]), "area_m2": round(g.area, 5), "bands": [],
                   "columns": []}
            for bid, _t, p in bpoly.get(st, []):
                a = g.intersection(p).area
                if a > MIN_M2:
                    row["bands"].append([bid, round(a, 5)])
            for c in cols[st]:
                a = g.intersection(c["poly"]).area
                if a > MIN_M2:
                    row["columns"].append([c["h"], c["hatch"], round(a, 5)])
            # plan area of the face covered by no band and no column (union, so a band over a column is not counted twice)
            cover = [p for _b, _t, p in bpoly.get(st, []) if g.intersects(p)] + [c["poly"] for c in cols[st]
                                                                               if g.intersects(c["poly"])]
            if cover:
                from shapely.ops import unary_union
                rest = g.difference(unary_union(cover))
            else:
                rest = g
            row["uncovered_m2"] = round(rest.area, 5)
            # each uncovered part >= 1e-3 m2 with the band piece it touches (nearest, distance in m): the receiving beam
            parts = []
            for q in getattr(rest, "geoms", [rest]):
                if q.is_empty or q.area < 1e-3:
                    continue
                near = sorted((q.distance(p), bid) for bid, _t, p in bpoly.get(st, []))
                parts.append([near[0][1] if near and near[0][0] < 0.01 else None, round(q.area, 5)])
            row["gaps"] = parts
            out["faces"].append(row)
    return out


def main(argv):
    if len(argv) < 3:
        raise SystemExit(__doc__)
    data = build(*argv[:3])
    n = {st: sum(1 for f in data["faces"] if f["storey"] == st) for st in SHEETS}
    print("faces", n, "bands", len(data["bands"]), "columns", len(data["columns"]))
    if "--write" in argv:
        (HERE / "ALSENAN_PARTITION_INPUT.json").write_text(json.dumps(data, indent=0), encoding="utf-8")
        print("written", HERE / "ALSENAN_PARTITION_INPUT.json")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
