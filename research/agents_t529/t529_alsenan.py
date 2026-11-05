"""T-529 on the development villa: the pool-court ledge (V3.0.58 L-2361d6ec HELD 0 .. 0.639573 m2) classified by
WP_APPLICABILITY_RULES_V2 from the drawn geometry. Reads the private decoded P7757.dxf AT RUN TIME (handles in
t529_inputs.py, no coordinate stored); outputs areas, lengths and decisions. Without the drawing: HELD, bound unchanged.

Run: T486_DXF=<private P7757.dxf> .work/venv/bin/python -I research/agents_t529/t529_alsenan.py
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (ROOT, HERE, ROOT / "research" / "agents_t486", ROOT / "research" / "agents_t494",
          ROOT / "research" / "agents_t522"):
    sys.path.insert(0, str(p))
import t486_alsenan as A                                   # noqa: E402
import t494_alsenan as B                                   # noqa: E402
import t522_alsenan as X                                   # noqa: E402
import t522_inputs as I522                                 # noqa: E402
import t522_ledge_window as L                              # noqa: E402
import t529_exposure_v2 as V                               # noqa: E402
import t529_inputs as I                                    # noqa: E402
from engine.source import wp_applicability_rules_v1 as W   # noqa: E402
from shapely.geometry import LineString, Polygon           # noqa: E402

MM = 0.001


def _hatch_external_rings(dw, handle, dx):
    """external boundary paths of a HATCH (ezdxf path conversion, flattened to 0.1 mm), in 1F-frame local metres."""
    from ezdxf import path as P
    e = dw.d.entitydb[handle]
    ox, oy = dw.o
    rings = []
    for bp in e.paths:
        if not (bp.path_type_flags & 1):            # 1 = external
            continue
        pth = P.from_hatch_boundary_path(bp, e.ocs(), e.dxf.elevation.z)
        rings.append([((v.x - ox) * MM + dx, (v.y - oy) * MM) for v in pth.flattening(0.1)])
    return rings


def cover_outlines(dw):
    dx = I.FRAME_DX_M
    sh = lambda h: [(x + dx, y) for x, y in dw.pts(h)]            # noqa: E731
    hatch = _hatch_external_rings(dw, I.ROOF_HATCH, dx)
    xw, xe = sh(I.BAND_WEST)[0][0], sh(I.BAND_EAST)[0][0]
    ys = sh(I.BAND_SOUTH)[0][1]
    yn = max(p[1] for p in sh(I.BAND_NORTH_STEP))
    band = [(xw, ys), (xe, ys), (xe, yn), (xw, yn)]               # the straight part; the rounded corner lies beyond
    dim = X._dim(dw, I.DIM_PROJECTION)
    return {"hatch_rings": hatch, "band": band, "band_east_x": xe, "band_west_x": xw,
            "projection_dim": {"printed": dim["printed"], "measured_m": dim["measured_m"]},
            "plot_dim_printed": X._dim(dw, I.DIM_TO_PLOT)["printed"]}


def ledge_surface(dw, covers):
    strip, split_line = X.ledge_strip(dw)
    R = A.rings(dw)
    ring = list(strip.exterior.coords)
    runs = []
    for h, kind in I.BAY_RUNS:
        runs.append({"run": f"bay_face:{h}", "kind": kind, "coords": dw.pts(h),
                     "head_drawn": True if kind == "GLAZING" else None,
                     "source": f"1F plan {h} (layer {dw.d.entitydb[h].dxf.layer}); "
                               + (I.BCE_HEAD_SOURCE if kind == "GLAZING" else "wall end (T-522 R-T522-2)")})
    runs.append({"run": "void_edge", "kind": "VOID_EDGE", "coords": R["void"], "source": I.VOID_SOURCE})
    runs.append({"run": "zone_split_wall_line", "kind": "OPEN_EDGE", "coords": list(split_line.coords),
                 "source": I.SPLIT_SOURCE})
    surf = {"zone_id": "POOLCOURT-550-LEDGE", "outline": ring, "boundary": runs,
            "covers": [{"id": "ROOF-970 hatch 2F21", "kind": "ROOF", "outline": r, "source": I.COVER_SOURCE}
                       for r in covers["hatch_rings"]] +
                      [{"id": "2F projection 12A7..1319", "kind": "SLAB", "outline": covers["band"],
                        "source": I.COVER_SOURCE}],
            "screens": []}
    return surf, strip


def own_area_check(dw):
    """an independent construction of the ledge: the bay disk (r 1.935, shapely circle) west of the wall line less
    the void chain polygon (no T-486 outline / pier step)."""
    from shapely.geometry import Point, box
    c = A.Drawing.__dict__  # noqa: F841  (marker: the arc centre is read from the entity, not from T-486)
    e = dw.d.entitydb["BCE"]
    cx, cy = dw._p(e.dxf.center)
    r = e.dxf.radius * MM
    wx = A.rings(dw)["wall_x"]
    disk = Point(cx, cy).buffer(r, quad_segs=2048)
    west = box(-1000, -1000, wx, 1000)
    void = Polygon(dw.chain(A.VOID)).buffer(0)
    own = disk.intersection(west).difference(void)
    return round(own.area, 6)


def build(dxf=None):
    path = dxf or A.default_dxf()
    if path is None:
        return {"drawing_read": False, "note": "drawing absent: the ledge membrane stays HELD 0 .. 0.639573 m2"}
    dw = A.Drawing(path)
    cov = cover_outlines(dw)
    surf, strip = ledge_surface(dw, cov)
    dec = V.classify_surface(surf)
    # V1 rows for the whole ledge zone with the V2 exposure (one part) and the T-522 upturn split
    pc, rn, zs = B.zones(path)
    ledge = zs[1]
    pieces = X.bay_pieces(dw)
    runs, na, rec = L.split_face("bay_face", ledge["upturn_runs"][0]["lm"],
                                 [dict(p, source=I522.BAY_SOURCE) for p in pieces])
    zone = dict(ledge, exposure=V.v1_exposure(dec), upturn_runs=runs)
    zone["evidence"] = dict(ledge["evidence"], FLAT_MEMBRANE=dec["evidence"])
    rows = W.component_rows(zone) + na
    for r in rows:
        if r["component"] == "FLAT_MEMBRANE":
            r["rule_basis"] = "; ".join(dec["basis"]) + " (V2 exposure step) + " + r["rule_basis"]
            r["rule_version_exposure"] = V.RULE_VERSION
    # information: distances behind the cover edges (T-522 took the 1F wall line as the edge)
    edge_e = LineString([(cov["band_east_x"], -1000), (cov["band_east_x"], 1000)])
    edge_w = LineString([(A.rings(dw)["wall_x"], -1000), (A.rings(dw)["wall_x"], 1000)])
    d_e, d_w = V.edge_distances(strip, edge_e), V.edge_distances(strip, edge_w)
    # the open-sky zone under the same projection (T-507 4.906867 m2), information for the Lead
    g = A.poolcourt_geometry(path)
    os_poly = _open_sky_polygon(dw)
    under = os_poly.intersection(Polygon(cov["band"])).area
    return {"drawing_read": True, "decision": {k: v for k, v in dec.items() if k != "parts"},
            "parts": [{k: v for k, v in p.items() if k != "geom"} for p in dec["parts"]],
            "own_area_m2": own_area_check(dw), "t486_area_m2": round(strip.area, 6),
            "cover": {k: v for k, v in cov.items() if k not in ("hatch_rings", "band")},
            "cover_edge_distances_m": {"projection_edge (V2 read)": d_e, "1F wall line (T-522 edge)": d_w},
            "open_sky_under_projection_m2": round(under, 6), "open_sky_net_m2": round(os_poly.area, 6),
            "open_sky_t494_net_m2": g["open_sky"]["net_m2"],
            "rows": rows, "reconciliation_bay": rec, "effect": effect(rows)}


def _open_sky_polygon(dw):
    import t486_terrace_wp as T
    R = A.rings(dw)
    wx, big = R["wall_x"], 1000.0
    whole = T._diff(T._poly(R["outline"]), T.unary_union([T._poly(p) for p in R["piers"].values()]))
    whole = T._diff(whole, T.unary_union([T._poly(R["void"]).buffer(0)]))
    return T._areal(T._inter(whole, T._poly([(wx, -big), (big, -big), (big, big), (wx, big)])))


def effect(rows):
    mem = [r for r in rows if r["component"] == "FLAT_MEMBRANE"][0]
    ups = [r for r in rows if r["component"] == "UPTURN"]
    tr = [r for r in rows if r["component"] == "WINDOW_TRANSITION"]
    m = mem["qty"] if mem["status"] == W.MEASURED else None
    up_lm = sum(r["length_lm"] for r in ups if r["status"] == W.MEASURED)
    r0, u0 = I.V3058_TOTALS["FIN.WP.ROOF"][0], I.V3058_TOTALS["FIN.WP.ROOF_UPTURN"][0]
    return {
        "ledge_membrane": {"line": "L-2361d6ec13c952bd2ae3", "before": "HELD 0 .. 0.639573 m2",
                           "after": f"{mem['status']} {m if m is not None else mem.get('held_bound')} m2"},
        "FIN.WP.ROOF_m2": {"before": r0, "after": round(r0 + (m or 0.0), 6),
                           "change_pct": round(100 * (m or 0.0) / r0, 4)},
        "ledge_upturn": {"line": "L-d7d1bf8c5991ccf69ea2", "before": "HELD 0 .. 3.528277 lm",
                         "after_measured_lm": round(up_lm, 6), "after_m2": round(up_lm * W.UPTURN_H_M, 6),
                         "transition_held_lm": round(sum(r["held_bound"] for r in tr), 6)},
        "FIN.WP.ROOF_UPTURN_lm": {"before": u0, "after_this_piece": round(u0 + up_lm, 6),
                                  "after_with_T522_window": round(u0 + up_lm + I.T522_WINDOW_LM, 6),
                                  "change_pct_this_piece": round(100 * up_lm / u0, 4)},
    }


if __name__ == "__main__":
    r = build(sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--dxf" else None)
    print(json.dumps({k: v for k, v in r.items() if k != "rows"}, indent=1, default=str))
    for x in r.get("rows", []):
        print(x["zone_id"], x["component"], x.get("run", ""), x["unit"], x["qty"], x.get("held_bound"), x["status"],
              "|", x["rule_basis"][:90])
