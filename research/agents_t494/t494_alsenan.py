"""T-494 on the development villa: B8-06 component rows of the pool-court slab (POOLCOURT-550) under
WP_APPLICABILITY_RULES_V1 (engine/source/wp_applicability_rules_v1.py), from the T-486 geometry (merged e8ee22f0).

Drawings by Drive title and entity handle only (Drive "Alsenan chalet project": P7757_DXF_COMPRESSED.zip -> P7757.dxf
sha256 ab54dd55...; sanitary-7757.pdf sheet 2). The geometry is read AT RUN TIME from the private decoded drawing
(git-excluded); this file holds handles, no coordinate; outputs are areas and lengths. Without the drawing every
measured row is HELD (never 0).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t486"))
import t486_alsenan as A                                   # noqa: E402
import t486_terrace_wp as T                                # noqa: E402
from engine.source import wp_applicability_rules_v1 as W   # noqa: E402

WINDOW_FACE = "C35"          # the 1F bath window's outer line at the wall line (layer 5), glazing C33 .. C3E (layer W)
PARAPET_FACE = A.SOUTH       # BDC: the north face of the 0.20 m parapet pair BDC / BDB to the SE strip
PARAPET_END = A.PARAPET_END  # C7F / B32


def runs(dxf=None):
    """the open-sky boundary split into its upturn runs, each measured on the drawn entity it lies on."""
    path = dxf or A.default_dxf()
    if path is None:
        return None
    from shapely.geometry import LineString, Polygon
    dw = A.Drawing(path)
    R = A.rings(dw)
    wx, ny, ex = R["wall_x"], R["north_y"], R["east_x"]
    big = 1000.0
    clip = Polygon([(wx, -big), (big, -big), (big, big), (wx, big)])
    # the same snapped boolean operations as T-486 zone_geometry (1 micrometre grid: no slivers along shared faces)
    whole = T._diff(T._poly(R["outline"]), T.unary_union([T._poly(p) for p in R["piers"].values()]))
    whole = T._diff(whole, T.unary_union([T._poly(R["void"]).buffer(0)]))
    net = T._areal(T._inter(whole, T._poly(list(clip.exterior.coords))))
    rest = net.boundary
    total = rest.length
    tol = 1.1e-6                 # just above the 1 micrometre snap grid
    out = {}

    def take(key, geom):
        nonlocal rest
        piece = rest.intersection(geom.buffer(tol, cap_style="flat"))
        out[key] = round(out.get(key, 0.0) + piece.length, 6)
        rest = rest.difference(geom.buffer(tol, cap_style="flat"))
    # each boundary piece goes to exactly one run (first match), so the runs partition the perimeter
    take("parapet_face", LineString(dw.pts(PARAPET_FACE)))
    for h in PARAPET_END:
        take("parapet_end", LineString(dw.pts(h)))
    take("window_face", LineString(dw.pts(WINDOW_FACE)))
    take("open_edge", LineString([(wx, ny), (ex, ny), (ex, R["pe_y"])]))
    take("void_edge", Polygon(R["void"]).buffer(0).boundary)
    take("continuation", LineString([(wx, -big), (wx, big)]))
    for k, v in R["piers"].items():
        take(k, Polygon(v).boundary)
    out["unassigned"] = round(rest.length, 6)
    out["perimeter"] = round(total, 6)
    out["net_m2"] = round(net.area, 6)
    return out


def zones(dxf=None):
    pc = A.poolcourt_geometry(dxf)
    rn = runs(dxf)
    os_ = (pc or {}).get("open_sky") or {}
    oh = (pc or {}).get("overhang") or {}
    g = (lambda d, k: None if not d else d.get(k))
    up = []
    for k, label in (("north_pier", "N pier faces (CAA .. CA4)"), ("south_pier", "S pier faces (CB2 .. CA2)"),
                     ("southwest_pier", "SW pier faces (CA1 / CA3 / C9E)")):
        up.append({"run": k, "lm": g(rn, k), "kind": "SOLID"})
    up.append({"run": "parapet_face", "lm": g(rn, "parapet_face"), "kind": "PARAPET"})
    up.append({"run": "parapet_end", "lm": g(rn, "parapet_end"), "kind": "PARAPET"})
    up.append({"run": "window_face", "lm": g(rn, "window_face"), "kind": "UNDER_WINDOW", "sill_above_slab_m": None})
    ev = {
        "FLAT_MEMBRANE": ["slab top round the oval VOID (label BBF), printed +5.50 (LEVEL 1251), no ROOF label: exposed "
                          "by the 2F plan (nothing drawn east of the 2F parapet at the 1F wall line)",
                          "T-486 own measure 8.3537 gross - piers 0.5837 - void 2.8632 = 4.9069 m2; Checker re-measure "
                          "4.9069 AGREE (T-486 Gate A, own polygonisation)",
                          "below: the GF pool court (exterior); slab by the GF roof-slab sheet (T-127 / T-154, Q-68)"],
        "north_pier": ["bay-frame pier, layer D on 1F, same outline layer 5 on 2F; elevation: rises from the slab"],
        "south_pier": ["bay-frame pier, layer D on 1F / layer 5 on 2F"],
        "southwest_pier": ["bay-frame pier CA1 / CA3 / C9E, cut at the parapet face BDC"],
        "parapet_face": ["BDC north face of the 0.20 m parapet pair BDC / BDB (layer 5); the SE strip (TERRACE-550, "
                         "L-2f7502be) owns the BDB south face: distinct faces, no shared upturn"],
        "parapet_end": ["C7F / B32: end of the SE-strip parapet on the plot line"],
        "window_face": ["C35 (layer 5) closes the wall line across the 1F bath window (glazing C33 .. C3E, layer W); "
                        "the window sill height above the slab top is printed in no view read this run"],
        "SLAB_EDGE_TERMINATION": ["C7D north edge 1.500 + B30 east edge 5.368: single layer-5 lines, no parapet (the "
                                  "parallel C7E / C80 / B31 are layer 2 = GF walls below)"],
        "VOID_EDGE_TERMINATION": ["void BCF / 2F1C / C7A / 2F1B east of the wall line (C7A = the GF pool water edge)"],
        "DRAINAGE_FALLS": ["sanitary-7757.pdf sheet 2 (1F drainage): no gully, no RWP and no slope arrow on this "
                           "area; the other three roofs print them"],
    }
    open_sky = {"zone_id": "POOLCOURT-550", "exposure": W.EXPOSED if pc else None, "doors": 0,
                "membrane_m2": g(os_, "net_m2"), "upturn_runs": up, "doorways": [],
                "open_edge_lm": g(rn, "open_edge"), "void_edge_lm": g(rn, "void_edge"), "carried": [],
                "outlet_printed": False, "evidence": ev}
    ledge = {"zone_id": "POOLCOURT-550-LEDGE", "exposure": W.COVERED_OPEN_SIDE if pc else None, "doors": 0,
             "membrane_m2": g(oh, "net_m2"),
             "upturn_runs": [{"run": "bay_face", "lm": g(oh, "upturn_lm"), "kind": "WALL"}],
             "void_edge_lm": g(oh, "opening_edge_lm"), "carried": [], "outlet_printed": False,
             "evidence": {"FLAT_MEMBRANE": ["0.20 m ledge between the bay's outer face (BCD / BCE / BD0, r 1.935) and the "
                                            "void edge (BCF, r 1.735), west of the wall line, under the 2F roof slab "
                                            "4.20 m above (+5.50 to +9.70), open on the void side (T-486; Checker "
                                            "0.6396 AGREE)"],
                          "bay_face": ["bay outer face BCD / BCE / BD0 (glazing BD2 .. BD5 inside it)"]}}
    return pc, rn, [open_sky, ledge]


def overlap_with_roof_lines():
    """the zone vs every FIN.WP.ROOF line of the candidate (T-486 census rows): physical surface, level and plan."""
    return [
        {"line_id": "L-d57d2dc2", "zone": "ROOF-430 1F west", "level": "+4.30", "overlap_m2": 0.0,
         "evidence": "label B8D 25.7 m west of the 1F wall line, 1.20 m below the pool-court slab top: another slab"},
        {"line_id": "L-2f7502be", "zone": "TERRACE-550 1F SE strip", "level": "+5.50", "overlap_m2": 0.0,
         "evidence": "label B81 4.70 m south of BDC; separated by the 0.20 m parapet BDC / BDB; the strip measures to "
                     "the BDB face, POOLCOURT-550 to the BDC face (outline south edge = BDC)"},
        {"line_id": "L-636fd3ff", "zone": "ROOF-970 2F roof terrace", "level": "+9.70", "overlap_m2": 0.0,
         "evidence": "4.20 m above; its straight east edge on the 2F parapet at the 1F wall line, so in plan it covers "
                     "only the ledge west of that line (the HELD row), not the open-sky part"},
        {"line_id": "L-3e8fe55d", "zone": "ROOF-1390 2F block roof (HELD)", "level": "+13.90", "overlap_m2": 0.0,
         "evidence": "the 2F block's own roof, west of the 2F parapet: not over the court"},
    ]


def build(dxf=None):
    pc, rn, zs = zones(dxf)
    rows = [r for z in zs for r in W.component_rows(z)]
    return {"rule_version": W.RULE_VERSION, "runs": rn, "rows": rows, "totals": W.totals(rows),
            "overlap": overlap_with_roof_lines(), "drawing_read": pc is not None}


if __name__ == "__main__":
    r = build(sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--dxf" else None)
    print(json.dumps({k: r[k] for k in ("runs", "totals", "drawing_read")}, indent=1))
    for x in r["rows"]:
        print(x["zone_id"], x["component"], x.get("run", ""), x["unit"], x["qty"], x.get("held_bound"), x["status"])
