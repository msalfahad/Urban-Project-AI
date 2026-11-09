"""T-626 DRAWING READ (research, unwired): the B8 waterproofing evidence behind the 24 UNKNOWN / HELD rows of the
reconciled-quantities statement (sections T-546/floor, 18 rows, and T-541/membrane, 6 rows), re-measured by HANDLE
on the architectural DXF (Drive "Alsenan chalet project" / P7757_DXF_COMPRESSED.zip, decoded into .work/private only).

Writes T626_DRAWN.json: handles, block names of sanitary symbols, lengths and areas only (no coordinate, no drawing
text, no client name). The evidence builder t626_alsenan.py reads only that JSON. Run through the wrapper's pytest
(tests/t626_wet_roof_wp_evidence re-reads the drawing and compares with the committed JSON when the drawing exists).

Two independent reads per wet room (R-T626-1 step 2):
  A  OUTLINE: an ordered chain of drawn wall-face edges by handle (R-T606-1 geometry, read only: vertices at the
     intersections of consecutive edges, so a door gap closes on its own wall face; S-COL.BON column polygons cut a
     notch). 17 chains are the T-621 chains (MERGED, re-measured here, not copied); the driver's W.C. and the pantry
     chains are new (handles below).
  B  PRINTED: every linear DIMENSION of the plan whose two definition points both lie on the room's own outline
     (within 5 mm) is listed with its handle and measurement; for a rectangular room the product of the printed width
     and depth is the second read. Non-rectangular rooms (wedge, diagonal corner, L-shape) keep the printed sides as
     a check of the chain's edges.
  FIX  sanitary symbols (INSERT block names) inside the outline: the drawing's own wet evidence (UP-WET-001); a room
     label alone is never wet evidence (R-T626-1 step 1).
Roof (T-541 rows): the four roof outlines to the inner parapet / wall faces (T-321 handles, re-measured here with
T-321's exact-arc area, read only), the three dome footprint circles by handle, and the pool-court slab top / ledge
re-run through the merged T-486 / T-529 drawing readers (read only).
"""
from __future__ import annotations

import json
import math
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (ROOT, HERE, ROOT / "research" / "agents_t606", ROOT / "research" / "agents_t612",
          ROOT / "research" / "agents_t621", ROOT / "research" / "agents_t321", ROOT / "research" / "agents_t486",
          ROOT / "research" / "agents_t494", ROOT / "research" / "agents_t522", ROOT / "research" / "agents_t529"):
    sys.path.insert(0, str(p))

OUT = HERE / "T626_DRAWN.json"
W = "WALL"
SCHEMA = "T626_DRAWN_V1"
SANITARY = ("WC", "WASH", "WASH2", "SHOWER", "BATH", "SINK", "FD", "BIDET", "URINAL", "TUB")

# the 18 wet rooms of the candidate's FIN.WP.FLOOR lines -> outline chain (T-621 key or new chain)
ROOMS = {
    "GF lobby wash (2 basins)": ("GF", "T621", "GF-LOBBY-WASH"),
    "GF basin space by the stair": ("GF", "T621", "GF-BASIN-STAIR"),
    "GF master bath": ("GF", "T621", "GF-MASTER-BATH"),
    "GF core W.C. 245 x 167 (wedge)": ("GF", "T621", "GF-WC-CORE-245"),
    "GF core W.C. 289 x 167 (wedge)": ("GF", "T621", "GF-WC-CORE-289"),
    "GF stair-core W.C. 175 x 135": ("GF", "T621", "GF-WC-STAIR"),
    "GF kitchen": ("GF", "T621", "GF-KITCHEN"),
    "GF driver W.C.": ("GF", "NEW", ["112", "134", "14E", "132"]),
    "GF W.C. by the reception room": ("GF", "T621", "GF-WC-REC"),
    "GF wash by the reception room": ("GF", "T621", "GF-WASH-REC"),
    "1F east bath 210 x 225": ("1F", "T621", "1F-EAST-BATH"),
    "1F bath by the laundry": ("1F", "T621", "1F-BATH-LAUNDRY"),
    "1F W.C. by the laundry": ("1F", "T621", "1F-WC-LAUNDRY"),
    "1F west bath A 245 x 205": ("1F", "T621", "1F-WBATH-1"),
    "1F west bath B 245 x 205": ("1F", "T621", "1F-WBATH-2"),
    "1F laundry": ("1F", "T621", "1F-LAUNDRY"),
    "2F roof-floor W.C. 300 x 185": ("2F", "T621", "2F-ROOF-WC"),
    # pantry box: south wall face A6, east edge B3 (layer 5: the open side, no wall), north wall face 158, west wall
    # face AF (window W 3BF in it); column 2FAE cuts its north-west corner (T-310 ruling)
    "GF pantry (wet zone, Q-37 A)": ("GF", "NEW", ["A6", "B3", "158", "AF"]),
}
NEW_NOTES = {
    "GF driver W.C.": "south face 112, east face 134, north face 14E, west face 132 (door D315 19E in the 1900 wall); "
                      "printed 1500 (658) x 1300 (61E)",
    "GF pantry (wet zone, Q-37 A)": "south face A6, open east edge B3 (layer 5), north face 158, west face AF; printed "
                                    "3000 (5D5) x 4500 (5E1); column 2FAE notch",
}
# pieces read as printed sizes
DIMS = {"GF-BASIN-REVEAL": ("GF", ["70F", "672"], "passage reveal of the basin space, printed 1.10 x 0.20")}


def q9(x) -> str:
    return str(Decimal(repr(float(x))).quantize(Decimal("0.000000001")))


def q6(x) -> str:
    return str(Decimal(repr(float(x))).quantize(Decimal("0.000001")))


def _poly_from_chain(geom, chain):
    import t606_rules as R6
    from shapely.geometry import Polygon
    n = len(chain)
    pts = []
    for i in range(n):
        ga, gb = geom[chain[i - 1]], geom[chain[i]]
        if ga[0] != "LINE" or gb[0] != "LINE":
            return None
        pts.append(R6._line_line(ga[1], gb[1]))
    return Polygon(pts)


def _dims_on(msp, poly, tol=5.0):
    """linear DIMENSIONs whose two definition points lie on the outline (within tol mm)."""
    from shapely.geometry import Point
    out = []
    ring = poly.exterior
    for e in msp.query("DIMENSION"):
        if not (e.dxf.hasattr("defpoint2") and e.dxf.hasattr("defpoint3")):
            continue
        a, b = e.dxf.defpoint2, e.dxf.defpoint3
        pa, pb = Point(a.x, a.y), Point(b.x, b.y)
        if ring.distance(pa) <= tol and ring.distance(pb) <= tol and pa.distance(pb) > 100:
            dx, dy = abs(a.x - b.x), abs(a.y - b.y)
            out.append({"handle": e.dxf.handle, "m": q6(e.get_measurement() / 1000),
                        "dir": "X" if dx >= dy else "Y"})
    return sorted(out, key=lambda d: d["handle"])


def _printed_rect(poly, dims):
    """width x depth from the printed dims when the outline is a rectangle and both sides are printed."""
    import shapely
    mrr = poly.minimum_rotated_rectangle
    if abs(mrr.area - poly.area) > 1.0 or len(shapely.get_coordinates(poly.exterior)) != 5:
        return None
    x0, y0, x1, y1 = poly.bounds
    w, d = (x1 - x0) / 1000, (y1 - y0) / 1000
    pw = [x for x in dims if x["dir"] == "X" and abs(float(x["m"]) - w) < 0.0015]
    pd = [x for x in dims if x["dir"] == "Y" and abs(float(x["m"]) - d) < 0.0015]
    if not pw or not pd:
        return None
    a, b = Decimal(pw[0]["m"]), Decimal(pd[0]["m"])
    return {"handles": [pw[0]["handle"], pd[0]["handle"]], "values": [str(a), str(b)], "area": str((a * b).quantize(Decimal("0.000001")))}


def read_rooms(doc, msp):
    import t606_extract as X6
    import t606_rules as R6
    import t621_extract as X21
    from shapely.geometry import Point
    geom, mids = X21.segs(msp)
    st = X6._storeys(msp, mids)
    cols = {k: [] for k in st}
    for e in msp.query("LWPOLYLINE"):
        if e.dxf.layer == "S-COL.BON" and e.closed:
            p = [(q[0], q[1]) for q in e.get_points()]
            for k, (a0, b0) in st.items():
                if a0 < p[0][0] < b0:
                    cols[k].append((e.dxf.handle, p))
    inserts = [(e.dxf.name, Point(e.dxf.insert.x, e.dxf.insert.y)) for e in msp.query("INSERT")]
    out = {}
    for room, (s, src, ref) in ROOMS.items():
        chain = X21.OUTLINES[ref][1] if src == "T621" else ref
        a0, b0 = st[s]
        for h in chain:
            if h not in geom:
                raise ValueError(f"{room}: handle {h} not in the drawing")
            x = geom[h][1][0][0]
            if not a0 < x < b0:
                raise ValueError(f"{room}: {h} is not on the {s} plan")
        res = R6.outline(geom, [(h, W) for h in chain], [p for _, p in cols[s]])
        poly = _poly_from_chain(geom, chain)
        rec = {"storey": s, "kind": "OUTLINE", "source": "DRAWING", "handles": list(chain),
               "chain_from": "T-621 " + ref if src == "T621" else "new (T-626)",
               "area": str(res["area"]), "perimeter": str(res["perimeter"]), "notch_m2": str(res["notch_m2"]),
               "note": X21.OUTLINES[ref][2] if src == "T621" else NEW_NOTES[room]}
        if poly is not None:
            notch_cols = [h for h, p in cols[s] if poly.intersects(_P(p)) and poly.intersection(_P(p)).area > 1e-6]
            rec["notch_columns"] = notch_cols
            dims = _dims_on(msp, poly)
            rec["printed_dims"] = dims
            pr = _printed_rect(poly, dims)
            if pr is not None:
                notch = Decimal(rec["notch_m2"])
                pr["area_less_notch"] = str((Decimal(pr["area"]) + notch).quantize(Decimal("0.000001")))
            rec["printed_rect"] = pr
            inner = poly.buffer(-20)
            rec["symbols_inside"] = sorted(n for n, pt in inserts if inner.contains(pt))
            rec["fixtures"] = sorted(n for n in rec["symbols_inside"] if n.upper() in SANITARY)
        else:
            rec["printed_dims"], rec["printed_rect"], rec["fixtures"], rec["symbols_inside"] = [], None, [], []
        out[room] = rec
    db = doc.entitydb
    for oid, (s, hs, note) in DIMS.items():
        vals = [Decimal(q6(db[h].get_measurement() / 1000)) for h in hs]
        a = vals[0]
        for v in vals[1:]:
            a = a * v
        out[oid] = {"storey": s, "kind": "DIM", "source": "DRAWING", "handles": hs, "values": [str(v) for v in vals],
                    "area": str(a.quantize(Decimal("0.000001"))), "note": note}
    return out


def _P(p):
    from shapely.geometry import Polygon
    return Polygon(p)


def read_roof(path):
    import t321_measure as M
    import roof_buildup as RB
    raw = M.measure(path)
    doc = M.ezdxf.readfile(path)
    db = doc.entitydb
    out = {}
    for zid, r in raw["roofs"].items():
        spec = [("ARC", tuple(v[1]), v[2], v[3], v[4]) if v[0] == "ARC" else tuple(v) for v in r["face_wall"]]
        hs = sorted({h for pair in M.ROOFS[zid]["face_wall"] for h in pair if not h.startswith("ARC")} |
                    {pair[1] for pair in M.ROOFS[zid]["face_wall"] if pair[0] == "ARC"})
        rec = {"kind": "OUTLINE", "source": "DRAWING", "handles": hs, "area": q6(RB.exact_area(spec)),
               "note": M.ROOFS[zid]["label"]}
        circ = {}
        for name, c in r["footprint_circles"].items():
            rr = Decimal(repr(db[c["handle"]].dxf.radius / 1000))   # full precision (T-321 rounds to 6 dp)
            circ[name] = {"handle": c["handle"], "layer": c["layer"], "r": q9(rr),
                          "area": q6(math.pi * float(rr) ** 2), "circumference": q6(2 * math.pi * float(rr))}
        rec["circles"] = circ
        if zid == "ROOF-1390":
            sp = M._spec(doc, M.ROOFS[zid]["face_wall"], 0, 0)
            xs = sorted({v[0] for v in sp})
            ys = sorted({v[1] for v in sp})
            rec["inner_sides"] = [q6(xs[-1] - xs[0]), q6(ys[-1] - ys[0])]
        out[zid] = rec
    return out


def read_poolcourt(path):
    import t486_alsenan as A
    import t529_alsenan as L29
    g = A.poolcourt_geometry(path)
    dw = A.Drawing(path)
    return {"POOLCOURT-550-OPEN-SKY": {"kind": "OUTLINE", "source": "DRAWING", "handles": ["T-486 / T-494 named set"],
                                       "area": q6(g["open_sky"]["net_m2"]),
                                       "note": "slab top +5.50 east of the wall line less piers and the void "
                                               "(merged T-486 / T-494 reader re-run this session, read only)"},
            "POOLCOURT-550-LEDGE": {"kind": "OUTLINE", "source": "DRAWING", "handles": ["BCE", "T-486 void chain"],
                                    "area": q6(L29.own_area_check(dw)),
                                    "note": "T-529 own construction: bay disk r of arc BCE west of the wall line less "
                                            "the void chain (re-run this session, read only)"}}


def read(path):
    import ezdxf
    doc = ezdxf.readfile(path)
    if doc.header.get("$INSUNITS") != 4:
        raise ValueError("drawing units are not mm")
    msp = doc.modelspace()
    return {"schema": SCHEMA, "source": "Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip (P7757.dxf)",
            "units": "m / m2", "rooms": read_rooms(doc, msp), "roof": read_roof(path),
            "poolcourt": read_poolcourt(path)}


def dumps(d) -> str:
    return json.dumps(d, indent=1, sort_keys=True, ensure_ascii=True) + "\n"
