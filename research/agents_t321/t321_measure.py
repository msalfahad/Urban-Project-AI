"""T-321 measurement from the architectural DXF (read only): every roof / terrace edge by entity handle, in LOCAL metres.

    python3 -I research/agents_t321/t321_measure.py <P7757.dxf> <out.json>

Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha256 ab54dd55...). Each vertex of each
outline is taken from the coordinates of named entities (x from a vertical edge line, y from a horizontal one, arcs by
their own centre / radius), shifted to a local origin per roof (the inner south-west corner) and converted mm -> m. The
designer's finish hatches (layer 3) are measured by their OUTER boundary paths (annotation islands - labels, level
symbols, rain-water-pipe symbols - are listed, not deducted: they are drafting, not construction). Output: handles,
local metres and areas only (no absolute coordinates, no text of the drawing). The committed
ALSENAN_ROOF_LAYERS_INPUT.json is this script's output; the test compares the two when the drawing is present.
"""
from __future__ import annotations

import json
import math
import sys

import ezdxf
from ezdxf import path as P
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

MM = 0.001


def _line(doc, h):
    e = doc.entitydb[h]
    assert e.dxftype() == "LINE", (h, e.dxftype())
    return (e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y), e.dxf.layer


def _x(doc, h):
    a, b, _ = _line(doc, h)
    assert abs(a[0] - b[0]) < 0.5, f"{h} is not vertical"
    return (a[0] + b[0]) / 2


def _y(doc, h):
    a, b, _ = _line(doc, h)
    assert abs(a[1] - b[1]) < 0.5, f"{h} is not horizontal"
    return (a[1] + b[1]) / 2


def _arc(doc, h):
    e = doc.entitydb[h]
    return (e.dxf.center.x, e.dxf.center.y), e.dxf.radius, e.dxf.start_angle, e.dxf.end_angle, e.dxf.layer


def _is_symbol_box(pts):
    """a label / symbol frame drawn as an EXTERNAL hatch path: a plain rectangle under 1.0 x 1.0 m (drafting)."""
    q = [pts[0]] + [p for i, p in enumerate(pts[1:]) if math.dist(p, pts[i]) > 0.5]
    if math.dist(q[0], q[-1]) < 0.5:
        q.pop()
    xs, ys = [p[0] for p in q], [p[1] for p in q]
    return len(q) == 4 and (max(xs) - min(xs)) < 1000 and (max(ys) - min(ys)) < 1000


def _hatch_outer(doc, h, tol=0.05):
    """(layer, pattern, finish paths, islands, symbol boxes): external paths that are symbol frames are drafting."""
    e = doc.entitydb[h]
    outer, islands, symbols = [], [], []
    for bp in e.paths:
        pts = [(v.x, v.y) for v in P.from_hatch_boundary_path(bp).flattening(tol)]
        poly = Polygon(pts).buffer(0)
        if not bp.path_type_flags & 1:
            islands.append(poly)
        elif _is_symbol_box(pts):
            symbols.append(poly)
        else:
            outer.append(poly)
    return e.dxf.layer, e.dxf.pattern_name, outer, islands, symbols


# Each roof: origin (x handle, y handle) = its inner south-west corner; vertices as (x-ref, y-ref) where a ref is a
# handle (its x or y) or a number of millimetres added to the origin; ARC items name the arc handle.
ROOFS = {
    "ROOF-430": {
        "label": "annex roof, printed +4.30 (1F plan AT220; T-221 ROOF-430)",
        "origin": ("B37", "B34"),
        "face_wall": [("B37", "B34"), ("CEC", "B34"), ("CEC", "ADF"), ("B3A", "ADF"), ("B3A", "B35"), ("B38", "B35"),
                      ("B38", "ARC:B2B:0"), ("ARC", "B2B"), ("B37", "B41")],
        "face_dband": [("B37", "B34"), ("CEC", "B34"), ("CEC", "ADF"), ("B3C", "ADF"), ("B3C", "B35"), ("B38", "B35"),
                       ("B38", "ARC:B2B:0"), ("ARC", "B2B"), ("B37", "B41")],
        "finish_hatches": ["D1F", "B2A"],
        "edges": {"parapet": ["B34", "B37", "B41", "B2B", "B38", "B35"], "divider": ["CEC"],
                  "building_wall": ["B3A", "ADF"], "dband": ["B3C", "C40", "C47"]},
    },
    "TERRACE-550": {
        "label": "GF roof strips at +5.50 south and sea side of the 1F (1F plan AT216; T-221 TERRACE-550)",
        "origin": ("CED", "B25"),
        "face_wall": [("CED", "B25"), ("B33", "B25"), ("B33", "BDB"), ("B5D", "BDB"), ("B5D", "AE3"), ("CED", "AE3")],
        "face_dband": None,
        "finish_hatches": ["AE0", "D1A", "1252"],
        "edges": {"parapet": ["B25", "B33"], "divider": ["CED"], "gate_stub": ["BDB"], "building_wall": ["AE3", "B5D"],
                  "door_closure": ["C9E"]},
    },
    "ROOF-970": {
        "label": "1F roof terraces round the 2F block, printed +9.70 (2F plan AT379 + AT385; T-221 ROOF-970)",
        "origin": ("12C9", "1285"),
        "face_wall": [("12C9", "1285"), ("12A7", "1285"), ("12A7", "1278"), ("1291", "1278"), ("1291", "1281"),
                      ("1288", "1281"), ("1288", "12B9"), ("12C9", "12B9")],
        "face_dband": [("12C9", "1285"), ("12A7", "1285"), ("12A7", "1278"), ("1291", "1278"), ("1291", "1281"),
                       ("12E2", "1281"), ("12E2", "12B9"), ("12C9", "12B9")],
        "finish_hatches": ["2F21"],
        "footprint_circles": {"DOME-W": "12EB", "DOME-E": "2F33"},
        "edges": {"parapet": ["1285", "12C9", "12B9", "12A7", "1278"], "building_wall": ["1288", "1281", "1291"],
                  "dband": ["12E2", "12E6"]},
    },
    "ROOF-1390": {
        "label": "main roof over the 2F block, printed +13.90 (no roof plan; outline from the 2F walls the parapet "
                 "continues, T-172 / T-311 section A-A)",
        "origin": ("12B7", "1283"),
        "face_wall": [("12B7", "1283"), ("1292", "1283"), ("1292", "1279"), ("12B7", "1279")],
        "face_dband": None,
        "finish_hatches": [],
        "footprint_circles": {"DOME-3": "1300"},
        "outer": [("1288", "1281"), ("1291", "1281"), ("1291", "1274"), ("1288", "1274")],
        "edges": {"parapet_inner (2F wall inner faces)": ["12B7", "1292", "1279", "1283"],
                  "parapet_outer (2F wall outer faces)": ["1288", "1291", "1274", "1281"]},
    },
}


def _ref(doc, ref, axis):
    if ref.startswith("ARC:"):
        _, h, k = ref.split(":")
        c, r, a0, a1, _ = _arc(doc, h)
        ang = math.radians(a0 if k == "0" else a1)
        return (c[0] + r * math.cos(ang)) if axis == "x" else (c[1] + r * math.sin(ang))
    return _x(doc, ref) if axis == "x" else _y(doc, ref)


def _spec(doc, verts, ox, oy):
    out = []
    for v in verts:
        if v[0] == "ARC":
            c, r, a0, a1, _ = _arc(doc, v[1])
            out.append(["ARC", [round((c[0] - ox) * MM, 4), round((c[1] - oy) * MM, 4)], round(r * MM, 6), a0, a1,
                        v[1]])
        else:
            out.append([round((_ref(doc, v[0], "x") - ox) * MM, 4), round((_ref(doc, v[1], "y") - oy) * MM, 4)])
    return out


def measure(path):
    doc = ezdxf.readfile(path)
    res = {"source": "Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip -> P7757.dxf", "units": "local m",
           "roofs": {}}
    for zid, z in ROOFS.items():
        ox, oy = _x(doc, z["origin"][0]), _y(doc, z["origin"][1])
        r = {"label": z["label"], "origin_handles": list(z["origin"]),
             "face_wall": _spec(doc, z["face_wall"], ox, oy),
             "face_dband": _spec(doc, z["face_dband"], ox, oy) if z.get("face_dband") else None,
             "edges": z["edges"]}
        if z.get("outer"):
            r["outer_wall"] = _spec(doc, z["outer"], ox, oy)
        fins = []
        for h in z["finish_hatches"]:
            layer, pat, outer, islands, symbols = _hatch_outer(doc, h)
            main = unary_union(outer)
            fins.append({"handle": h, "layer": layer, "pattern": pat,
                         "outer_m2": round(main.area * MM * MM, 4),
                         "outer_paths": len(outer),
                         "symbol_box_paths": [{"area_m2": round(p.area * MM * MM, 4),
                                               "outside_finish_paths_m2": round(p.difference(main).area * MM * MM, 4)}
                                              for p in symbols],
                         "islands": [round(p.area * MM * MM, 4) for p in islands]})
        r["finish_hatches"] = fins
        circ = {}
        for name, h in z.get("footprint_circles", {}).items():
            e = doc.entitydb[h]
            circ[name] = {"handle": h, "layer": e.dxf.layer,
                          "centre": [round((e.dxf.center.x - ox) * MM, 4), round((e.dxf.center.y - oy) * MM, 4)],
                          "r": round(e.dxf.radius * MM, 6)}
        r["footprint_circles"] = circ
        if zid == "ROOF-970":
            r["hatch_vs_outline"] = _hatch_gap(doc, z, ox, oy)
        res["roofs"][zid] = r
    return res


def _hatch_gap(doc, z, ox, oy):
    """the pieces of the D-band outline (less the dome discs) that the finish hatch does not cover: each piece's area
    and local centroid, so the report can name it (door swing, dome tangency cusp)."""
    from roof_buildup import outline  # noqa: E402
    spec = _spec(doc, z["face_dband"], ox, oy)
    poly = Polygon(outline([tuple(v[:2]) if v[0] != "ARC" else ("ARC", tuple(v[1]), v[2], v[3], v[4]) for v in spec]))
    _, _, outer, _, _ = _hatch_outer(doc, z["finish_hatches"][0])
    hatch = unary_union([Polygon([((x - ox) * MM, (y - oy) * MM) for x, y in p.exterior.coords]) for p in outer])
    discs = [Point((doc.entitydb[h].dxf.center.x - ox) * MM, (doc.entitydb[h].dxf.center.y - oy) * MM)
             .buffer(doc.entitydb[h].dxf.radius * MM, quad_segs=2048) for h in z["footprint_circles"].values()]
    gap = poly.difference(unary_union([hatch] + discs))
    pieces = [gap] if gap.geom_type == "Polygon" else list(gap.geoms)
    return sorted([{"area_m2": round(g.area, 4), "centroid": [round(g.centroid.x, 3), round(g.centroid.y, 3)]}
                   for g in pieces if g.area > 1e-4], key=lambda d: -d["area_m2"])


if __name__ == "__main__":
    sys.path.insert(0, __file__.rsplit("/", 1)[0])
    out = measure(sys.argv[1])
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, sort_keys=True)
        f.write("\n")
    print(json.dumps({k: {"finish": v["finish_hatches"]} for k, v in out["roofs"].items()}, indent=0)[:3000])
