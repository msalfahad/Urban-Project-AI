"""T-788 Checker aid (research only, no quantity change): the wall pieces of each open cornice zone by DXF handle.

For every zone of the T-788 fix row (GF-08 open room, 1F-13 living zone, GF-14 wash lobby, GF-07 pantry, 2F-01 stair
lobby, ST-2F shaft-box top) it walks the zone's share of its parent plan face boundary (R-T788-2 partition, same
sampling as t788_rules.partition_perimeter) and gives every boundary piece to the nearest drawn DXF entity:
  - a barrier entity of layer 1 (wall lines), S-COL.BON (columns) or W (windows): its handle, layer and type;
  - otherwise a closure line of rooms.py (door closed on a wall face, or a collinear face-line gap): the nearest door
    INSERT handle within 1.5 m, else GAP-CLOSURE / PLAN-BOX.
Printed: per zone, handle | layer | type | drawn length of the entity | length of it on the zone boundary; the zone
sum (= the partition length t788_fill.py uses before the hand-classified cuts); then the cut lines and the zone run.
No coordinates are printed or written; the face files stay in the private folder.

Usage (inside the wrapper allow-list, from the checkout root):
  bash scripts/agent_env.sh run --tree task-T-788 research/agents_t788/t788_zone_pieces.py <P7757.dxf> <private dir>
The three floor face files (gf_rooms.json, f1_rooms.json, f2_rooms.json) are made in <private dir> with the T-147
polygoniser when they are absent (same boxes as t788_fill.py).
"""
from __future__ import annotations

import collections
import json
import math
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import t788_fill as F  # noqa: E402
import t788_rules as R  # noqa: E402

ROOMS = HERE.parent / "agents_t147/scripts/rooms.py"
FLOORS = {"gf_rooms.json": (-163, -124), "f1_rooms.json": (-208, -169), "f2_rooms.json": (-253, -214)}
Y0, Y1 = -811, -784
BARRIER_LAYERS = ("1", "S-COL.BON", "W")
NEAR_M = 0.035          # a face sits on its drawn line after the BUF grow-back (0.015): match within 3.5 cm
STEP = 0.005


def ensure_faces(dxf, priv):
    for name, (x0, x1) in FLOORS.items():
        if not (priv / name).exists():
            subprocess.run([sys.executable, "-I", str(ROOMS), str(dxf), str(x0), str(x1), str(Y0), str(Y1),
                            str(priv / name)], check=True, stdout=subprocess.DEVNULL)


def entities(dxf):
    import ezdxf
    from ezdxf import path as zpath
    from shapely.geometry import LineString, Point, box

    doc = ezdxf.readfile(str(dxf))
    msp = doc.modelspace()
    plan = box(min(v[0] for v in FLOORS.values()), Y0, max(v[1] for v in FLOORS.values()), Y1)
    ents, doors = [], []
    for e in msp:
        if e.dxftype() == "RTEXT":
            continue                         # no layer attribute (rooms.py skips it the same way)
        if e.dxf.layer in BARRIER_LAYERS and e.dxftype() in ("LINE", "LWPOLYLINE", "ARC", "POLYLINE", "CIRCLE"):
            try:
                v = [(q.x / 1000, q.y / 1000) for q in zpath.make_path(e).flattening(5)]
            except Exception:
                continue
            if len(v) >= 2 and any(plan.contains(Point(q)) for q in v):
                g = LineString(v)
                ents.append((e.dxf.handle, e.dxf.layer, e.dxftype(), g))
        elif e.dxftype() == "INSERT":
            p = Point(e.dxf.insert.x / 1000, e.dxf.insert.y / 1000)
            if plan.contains(p):
                doors.append((e.dxf.handle, e.dxf.name, p))
    return ents, doors


def zone_pieces(parent, regions, default, ents, doors):
    """{zone: {key: length}} with the R-T788-2 sample-to-zone rule and nearest-entity attribution."""
    from shapely import STRtree
    from shapely.geometry import Point

    tree = STRtree([g for *_, g in ents])
    grown = {k: r.buffer(0.002) for k, r in regions.items()}
    out = collections.defaultdict(lambda: collections.defaultdict(float))
    polys = [parent] if parent.geom_type == "Polygon" else list(parent.geoms)
    for poly in polys:
        for ring in [poly.exterior, *poly.interiors]:
            c = list(ring.coords)
            for a, b in zip(c, c[1:]):
                seg = math.dist(a, b)
                n = max(1, int(seg / STEP))
                for k in range(n):
                    t = (k + 0.5) / n
                    p = Point(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
                    zone = next((kk for kk, g in grown.items() if g.contains(p)), default)
                    i = tree.query_nearest(p, max_distance=NEAR_M)
                    if len(i):
                        h, lay, typ, g = ents[int(i[0])]
                        key = (h, lay, typ, round(g.length, 3))
                    else:
                        near = [(p.distance(q), h, nm) for h, nm, q in doors if p.distance(q) < 1.5]
                        key = (("DOOR-CLOSURE " + min(near)[1]), "INSERT", min(near)[2], None) if near else \
                              ("GAP-CLOSURE/PLAN-BOX", "-", "-", None)
                    out[zone][key] += seg / n
    return out


def main(dxf, priv):
    from shapely.geometry import box

    ensure_faces(dxf, priv)
    ents, doors = entities(dxf)
    runs, parts = F.open_zones(priv, [g for *_, g in ents])
    # the same parent faces and cut regions as t788_fill.open_zones (re-picked here; areas are the identifiers)
    from shapely import wkt
    from shapely.geometry import Polygon

    def faces(name):
        return [wkt.loads(o["wkt"]) for o in json.load(open(priv / name))["faces"]]

    def pick(Fs, area, tol=0.02):
        m = [g for g in Fs if abs(g.area - area) < tol]
        assert len(m) == 1, f"face of {area} m2 not unique ({len(m)})"
        return m[0]

    gf, f1, f2 = faces("gf_rooms.json"), faces("f1_rooms.json"), faces("f2_rooms.json")
    gclip = Polygon([(-148.2, -805.094), (-129.07, -805.094), (-129.07, -797.594), (-131.0, -797.594),
                     (-131.0, -795.9), (-145.05, -795.9), (-145.05, -800.45), (-148.2, -800.45)])
    LB, PB = box(-140.6, -796.0, -137.85, -793.0), box(-148.2, -805.2, -145.05, -800.45)
    G0 = max(gf, key=lambda g: g.area)
    _, pockets = R.split_outdoor(G0.difference(LB).difference(PB), gclip, [g for *_, g in ents])   # R-T788-3
    gregs = {"GF-14": LB, "GF-07": PB.intersection(gclip)}
    gregs.update({f"OUTDOOR-{i}": q for i, q in enumerate(pockets)})
    gregs["GF-08"] = gclip
    sets = [
        ("GF", G0, gregs, "OUTSIDE"),
        ("1F", pick(f1, 75.983), {"ST-1F": box(-189.893, -797.194, -187.393, -791.994)}, "1F-13"),
        ("2F", pick(f2, 18.600), {"ST-2F": box(-234.745, -797.194, -232.245, -791.994)}, "2F-01"),
    ]
    report = {}
    for floor, parent, regions, default in sets:
        pieces = zone_pieces(parent, regions, default, ents, doors)
        for zone, d in pieces.items():
            if zone in ("OUTSIDE", "ST-1F") or zone.startswith("OUTDOOR-"):
                continue                     # not a cornice zone (yard leak / open stair well, R-T788-1)
            tot = sum(d.values())
            print(f"\n== {floor} {zone}: boundary {tot:.3f} m (partition {parts[floor][zone]:.3f})")
            print("handle | layer | type | drawn length m | on zone boundary m")
            for (h, lay, typ, ln), v in sorted(d.items(), key=lambda kv: -kv[1]):
                if v >= 0.005:
                    print(f"{h} | {lay} | {typ} | {'' if ln is None else f'{ln:.3f}'} | {v:.3f}")
            report[zone] = {"boundary_m": round(tot, 3), "partition_m": parts[floor][zone],
                            "pieces": len([v for v in d.values() if v >= 0.005])}
    print("\n== hand-classified cut lines (t788_fill.open_zones): GF-07 +2.79 OPENING, +4.5 OPEN_SIDE; GF-08 openings"
          " 0.285 + 1.271; 1.475 + 0.891 (outdoor pocket, R-T788-3) and 4.5 OPEN_SIDE; GF-14 opening 1.271 + niche WALL; 1F-13 2.5 OPEN_SIDE")
    print("== zone runs (lm):", json.dumps(runs))
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main(pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]))
