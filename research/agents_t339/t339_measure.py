"""T-339 measurement from the architectural DXF (read only): each roof's slab roof zone to the parapet's drawn 0.20 wall
line (outer face), by entity handle, in the SAME local frames as T-321 (origin = each roof's inner south-west corner),
and the plan-overlap checks of R-T339-5.

    python3 -I research/agents_t339/t339_measure.py <P7757.dxf> <out.json>

Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip -> P7757.dxf (sha256 ab54dd55...). Output: handles, local
metres and areas only (no absolute coordinate, no drawing text). The committed MEASURED_T339.json is this script's
output; tests/t339_roof_binding/test_t339_alsenan.py compares the two when the drawing is present.

Outer outline = the inner-face outline of T-321 (face_wall) with every PARAPET edge moved to the parapet's outer 0.20
wall line (the line the parapet top / RC footprint stops on: T-311 / T-324 thickness 0.200); building-wall edges and
divider faces stay where they are (no parapet there). Frame / moulding lines beyond the 0.20 wall line (B2D / B2E,
B27 / B28, 1308 .. 1323, C85 / C86) are the facade frame item (T-305 / T-324), not slab and not parapet: not used.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research" / "agents_t321"))

MM = 0.001

# vertex refs: "H" a handle (x of a vertical / y of a horizontal LINE), "H:xmin" / "H:xmax" / "H:ymin" / "H:ymax" an end
# of a line; ("ARC", handle) an arc of the outline.
OUTER = {
    "ROOF-430": {"origin": ("B37", "B34"),
                 "outer": [("C6F:xmin", "AC7"), ("CEC", "AC7"), ("CEC", "ADF"), ("B3A", "ADF"), ("B3A", "B36"),
                           ("B39", "B36"), ("B39", "ARC:B29:0"), ("ARC", "B29"), ("C6F:xmin", "B26")],
                 "edges": {"south outer (boundary line, T-324 relation AC7 0.200 off B34)": "AC7",
                           "west outer": "C6F (x start)", "north outer": "B36, B39, arc B29 (r 1.300)",
                           "north-west outer": "B26", "divider west face (no parapet)": "CEC",
                           "building wall faces (no parapet)": "ADF, B3A"}},
    "TERRACE-550": {"origin": ("CED", "B25"),
                    "outer": [("CED", "AC7"), ("C7F:xmax", "AC7"), ("C7F:xmax", "BDC"), ("B5D", "BDC"),
                              ("B5D", "AE3"), ("CED", "AE3")],
                    "edges": {"south outer (boundary line)": "AC7", "east outer": "C7F (x end)",
                              "north outer (SW-9 / gate stub)": "BDC", "divider east face (no parapet)": "CED",
                              "building wall faces (no parapet)": "B5D, AE3"}},
    "ROOF-970": {"origin": ("12C9", "1285"),
                 "outer": [("12C7", "127F"), ("12A5", "127F"), ("12A5", "1273"), ("1291", "1273"), ("1291", "1281"),
                           ("1288", "1281"), ("1288", "12A8"), ("12C7", "12A8")],
                 "edges": {"south outer": "127F (+ 131E layer 2, same y)",
                           "sea side 0.20 wall line": "12A5 / 131C / 131B (layer 2)", "north outer": "1273",
                           "west outer": "12C7", "SW-2 outer": "12A8",
                           "building wall faces (no parapet)": "1291, 1281, 1288"}},
}
FINISH = {"ROOF-430": ["D1F", "B2A"], "TERRACE-550": ["AE0", "D1A", "1252"], "ROOF-970": ["2F21"]}
DOMES = {"ROOF-970": ["12EB", "2F33"]}


def _line(doc, h):
    e = doc.entitydb[h]
    assert e.dxftype() == "LINE", (h, e.dxftype())
    return (e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)


def _ref(doc, ref, axis):
    if ref.startswith("ARC:"):
        _, h, k = ref.split(":")
        e = doc.entitydb[h]
        ang = math.radians(e.dxf.start_angle if k == "0" else e.dxf.end_angle)
        if axis == "x":
            return e.dxf.center.x + e.dxf.radius * math.cos(ang)
        return e.dxf.center.y + e.dxf.radius * math.sin(ang)
    h, _, end = ref.partition(":")
    a, b = _line(doc, h)
    if end:
        i = 0 if end[0] == "x" else 1
        return (min if end[1:] == "min" else max)(a[i], b[i])
    if axis == "x":
        assert abs(a[0] - b[0]) < 0.5, f"{h} is not vertical"
        return (a[0] + b[0]) / 2
    assert abs(a[1] - b[1]) < 0.5, f"{h} is not horizontal"
    return (a[1] + b[1]) / 2


def spec(doc, verts, ox, oy):
    out = []
    for v in verts:
        if v[0] == "ARC":
            e = doc.entitydb[v[1]]
            out.append(["ARC", [round((e.dxf.center.x - ox) * MM, 4), round((e.dxf.center.y - oy) * MM, 4)],
                        round(e.dxf.radius * MM, 6), e.dxf.start_angle, e.dxf.end_angle, v[1]])
        else:
            out.append([round((_ref(doc, v[0], "x") - ox) * MM, 4), round((_ref(doc, v[1], "y") - oy) * MM, 4)])
    return out


def poly_of(spec_):
    from shapely.geometry import Polygon
    import roof_buildup as RB
    return Polygon(RB.outline([tuple(v[:2]) if v[0] != "ARC" else ("ARC", tuple(v[1]), v[2], v[3], v[4])
                               for v in spec_]))


def measure(path):
    import ezdxf
    from shapely.geometry import Point, Polygon
    from shapely.ops import unary_union
    import roof_buildup as RB
    import t321_measure as M
    doc = ezdxf.readfile(path)
    t321 = json.loads((ROOT / "research/agents_t321/ALSENAN_ROOF_LAYERS_INPUT.json").read_text(encoding="utf-8"))
    res = {"source": "Drive 'Alsenan chalet project' / P7757_DXF_COMPRESSED.zip -> P7757.dxf", "units": "local m "
           "(T-321 frames)", "roofs": {}}
    for zid, z in OUTER.items():
        ox, oy = _ref(doc, z["origin"][0], "x"), _ref(doc, z["origin"][1], "y")
        o = spec(doc, z["outer"], ox, oy)
        inner_spec = t321["roofs"][zid]["face_wall"]
        outer_p, inner_p = poly_of(o), poly_of(inner_spec)
        strip = outer_p.difference(inner_p)
        outs = []
        for h in FINISH[zid]:
            _, _, outer, _, _ = M._hatch_outer(doc, h)
            outs += outer
        hatch = unary_union([Polygon([((x - ox) * MM, (y - oy) * MM) for x, y in p.exterior.coords]) for p in outs])
        discs = [Point((doc.entitydb[h].dxf.center.x - ox) * MM, (doc.entitydb[h].dxf.center.y - oy) * MM)
                 .buffer(doc.entitydb[h].dxf.radius * MM, quad_segs=2048) for h in DOMES.get(zid, [])]
        disc_u = unary_union(discs) if discs else None
        gap = inner_p.difference(unary_union([hatch] + discs))
        pieces = [gap] if gap.geom_type == "Polygon" else list(gap.geoms)
        res["roofs"][zid] = {
            "outer": o, "outer_edges": z["edges"],
            "outer_m2_exact": round(RB.exact_area([tuple(v[:2]) if v[0] != "ARC" else
                                                   ("ARC", tuple(v[1]), v[2], v[3], v[4]) for v in o]), 6),
            "strip_m2": round(strip.area, 4),
            "inner_outside_outer_m2": round(inner_p.difference(outer_p).area, 6),
            "finish_hatch_m2": round(hatch.area, 4),
            "finish_hatch_in_parapet_strip_m2": round(hatch.intersection(strip).area, 6),
            "finish_hatch_outside_inner_face_m2": round(hatch.difference(inner_p).area, 6),
            "domes_in_parapet_strip_m2": round(disc_u.intersection(strip).area, 6) if disc_u else None,
            "finish_gap_pieces": sorted([{"area_m2": round(g.area, 4),
                                          "bounds": [round(v, 3) for v in g.bounds]}
                                         for g in pieces if g.area > 1e-4], key=lambda d: -d["area_m2"]),
        }
    return res


if __name__ == "__main__":
    out = measure(sys.argv[1])
    Path(sys.argv[2]).write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: {kk: v[kk] for kk in ("outer_m2_exact", "strip_m2", "finish_hatch_m2",
                                                "finish_hatch_in_parapet_strip_m2",
                                                "finish_hatch_outside_inner_face_m2")}
                      for k, v in out["roofs"].items()}, indent=1))
