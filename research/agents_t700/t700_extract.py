"""T-700 own read (values only): the inputs of the three zones T-695 left open, from the structural DXF.

    .work/venv/bin/python -I research/agents_t700/t700_extract.py <structural.dxf>
    -> research/agents_t700/ZONE_INPUT_T700.json (areas, handles, cell ids, level-mark strings; no coordinates)

1. Z2 (fill above EG under the GF ground slab): the route-G ground sheet (SH08, the run that names the candidate
   GROUND_SLAB cells SITE-...) is read as T-674 reads it; every PANEL face is assigned to the BUILDING BLOCK it lies in
   (connected union of the panel / beam / column / junction faces: the annex block and the main-house block are
   separate networks) and the LEVEL-layer marks printed inside each block are listed. Nothing is typed by hand.
2. Lift pit FF (B1-02 / B1-03 Z1-PIT-FF): the FF outline (route G registered on the foundation plan, as the T-695 /
   T-350 r2 pits reader builds it) at projection 0 and 0.10, its overlap with the pits zone Z, the F10 / F drawn
   outline, the pool envelope and each strap's drawn concrete plan, and the lift ring S-BW 10EB (outer) / 10EA (inner)
   outlines inside it.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research/agents_t350r2"))
sys.path.insert(0, str(ROOT / "research/agents_t391"))
sys.path.insert(0, str(ROOT / "research/agents_t674"))

from shapely.geometry import MultiPoint, Point, Polygon, box  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

DXF_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
STRAPS = {"SB1": ("1689", "1B1C"), "SB2": ("1B08", "1B09"), "SB3": ("1B26", "1B27")}
RING = {"outer": "10EB", "inner": "10EA"}
OUT = HERE / "ZONE_INPUT_T700.json"


def _r(x, n=6):
    return round(x + 0.0, n)


def ground_sheet_blocks(dxf, doc):
    """route-G SH08 faces (T-674 engine_side) -> panel cell -> block, and the LEVEL marks inside each block"""
    import t391_extract as X
    import t674_alsenan as A
    _, rec, u, _, _, faces = A.engine_side(dxf)
    msp = doc.modelspace()
    L = {e.dxf.handle: e for e in msp.query("LINE")}
    ref = faces["SITE-49a7dae5c139aebb"]["polygon"]          # T-674 frame recovery (lines 176 / 180D)
    xs = min(x for x, _ in ref) - L["176"].dxf.start.x
    ys = min(y for _, y in ref) - L["180D"].dxf.start.y
    polys = {k: Polygon([(x - xs, y - ys) for x, y in f["polygon"]]).buffer(0) for k, f in faces.items()}
    net = unary_union([p.buffer(1.0) for p in polys.values()])        # 1 mm closes shared edges only
    blocks = sorted(getattr(net, "geoms", [net]), key=lambda g: g.centroid.x)
    marks = [((t.dxf.text or "").strip(), Point(t.dxf.insert.x, t.dxf.insert.y), t.dxf.handle)
             for t in msp.query("TEXT[layer=='LEVEL']")
             if X.GBP[0] <= t.dxf.insert.x <= X.GBP[2] and X.GBP[1] <= t.dxf.insert.y <= X.GBP[3]]
    bout = []
    for i, g in enumerate(blocks):
        hull = g.convex_hull
        inside = sorted((s, h) for s, p, h in marks if g.buffer(-1.0).contains(p))
        bout.append({"block": i, "faces": sum(1 for p in polys.values() if g.contains(p.representative_point())),
                     "panel_m2": _r(sum(faces[k]["area_m2"] for k, p in polys.items()
                                        if faces[k]["class"] == "PANEL" and g.contains(p.representative_point()))),
                     "level_marks_inside": [s for s, _ in inside], "level_mark_handles": [h for _, h in inside],
                     "level_marks_in_hull_only": sorted(s for s, p, h in marks
                                                        if hull.contains(p) and not g.buffer(-1.0).contains(p))})
    panels = {}
    for k, f in faces.items():
        if f["class"] != "PANEL":
            continue
        p = polys[k]
        bi = next(i for i, g in enumerate(blocks) if g.contains(p.representative_point()))
        panels[k] = {"block": bi, "area_m2": _r(f["area_m2"]),
                     "level_marks_inside": sorted(s for s, q, _ in marks if p.contains(q))}
    other = {}
    for k, f in faces.items():
        if f["class"] != "PANEL":
            c = f["class"]
            other[c] = _r(other.get(c, 0.0) + f["area_m2"])
    return {"blocks": bout, "panels": dict(sorted(panels.items())), "non_panel_faces_m2": other,
            "level_marks_on_sheet": sorted(s for s, _, _ in marks)}


def lift_pit(dxf, doc):
    """FF outline and its neighbours in the route-G foundation frame (the T-695 / T-350 r2 reader's frame)"""
    import t350r2_beam_over_pits as B
    from engine.source import generic_route as GR
    from engine.source import route_g_scope_v1 as SC
    from tools import urban_boq_m2 as M2
    from shapely import affinity
    R = M2.compute([dxf], conventions=str(B.CONV), profile=str(B.M4), route="G", completeness=False)
    D, conv = R["generic"]["D"], R["conv"]
    p = GR._trip(conv, "BLINDING_PROJECTION_M")[1]
    u = D["unit_m"]
    pn, m2 = p / u, u * u
    t170 = json.loads((ROOT / "research/agents_t170/ALSENAN_EXCAVATION_INPUT.json").read_text())["footings"]
    feet = [f for rec in SC._sheets(D, "FOUNDATION_PLAN") for f in rec.get("footings", [])
            if f.get("box") and f.get("drawn_m") and SC._footing_dims(f, conv) and
            list(SC._footing_dims(f, conv)) == list(f["drawn_m"][:2])]
    f8r = next(t for t in t170 if t["type"] == "F8")
    f8g = [f for f in feet if sorted(round(v, 3) for v in f["drawn_m"][:2]) == [3.6, 4.0]]
    assert len(f8g) == 1
    bx = f8g[0]["box"]
    ox = (bx[0] + bx[2]) / 2 - (f8r["x0_mm"] + f8r["dx_mm"] / 2)
    oy = (bx[1] + bx[3]) / 2 - (f8r["y0_mm"] + f8r["dy_mm"] / 2)
    pits, ff0, ffp = [], [], []
    for f in feet:
        bb = f["box"]
        cx, cy = (bb[0] + bb[2]) / 2 - ox, (bb[1] + bb[3]) / 2 - oy
        m = min(t170, key=lambda t: abs(t["x0_mm"] + t["dx_mm"] / 2 - cx) + abs(t["y0_mm"] + t["dy_mm"] / 2 - cy))
        if m["type"] == "FF":
            ff0.append(Polygon(SC._quad(bb, 0.0)))
            ffp.append(Polygon(SC._quad(bb, pn)))
        elif m["type"] != "F10/F":
            pits.append(Polygon(SC._quad(bb, pn)))
    assert len(ff0) == 1, len(ff0)
    FF0, FFP = ff0[0], ffp[0]
    db = doc.entitydb
    plot = Polygon([(x + ox, y + oy) for x, y, *_ in db.get(B.PLOT_HANDLE).get_points()])
    pool = json.loads((ROOT / "research/agents_t189/ALSENAN_OVERLAP_INPUT.json").read_text())["pool"]
    rr, bxp = pool["outline"]["r_outer"], pool["outline"]["back_x"]
    d_ = Point(0, 0).buffer(rr, quad_segs=256).intersection(box(-rr, -rr, 0, rr)).union(box(0, -rr, bxp, rr))
    env = d_.buffer(0.10, quad_segs=256)
    ex_, ey_ = f8r["x0_mm"] / 1000 - pool["F8"]["x"][0], f8r["y0_mm"] / 1000 - pool["F8"]["y"][0]
    env = affinity.translate(affinity.scale(affinity.translate(env, ex_, ey_), 1000, 1000, origin=(0, 0)), ox, oy)
    Z = unary_union(pits).intersection(plot).difference(env)
    f10 = Polygon([(x + ox, y + oy) for x, y, *_ in db.get("1B1B").get_points()]).buffer(0).buffer(pn, join_style=2)

    def poly(h):
        e = db.get(h)
        return Polygon([(x + ox, y + oy) for x, y, *_ in e.get_points()])
    ring_o, ring_i = poly(RING["outer"]), poly(RING["inner"])
    straps = {}
    for mk, (h1, h2) in STRAPS.items():
        e1, e2 = db.get(h1), db.get(h2)
        hull = MultiPoint([(e.dxf.start.x + ox, e.dxf.start.y + oy) for e in (e1, e2)] +
                          [(e.dxf.end.x + ox, e.dxf.end.y + oy) for e in (e1, e2)]).convex_hull
        straps[mk] = {"in_ff_raw_m2": _r(hull.intersection(FF0).area * m2),
                      "in_ff_grown_m2": _r(hull.intersection(FFP).area * m2)}
    out = {}
    for tag, F in (("raw", FF0), ("grown", FFP)):
        out[tag] = {"plan_m2": _r(F.area * m2), "in_pits_zone_m2": _r(F.intersection(Z).area * m2),
                    "in_f10_drawn_m2": _r(F.intersection(f10).area * m2),
                    "in_pool_envelope_m2": _r(F.intersection(env).area * m2),
                    "beyond_plot_m2": _r(F.difference(plot).area * m2)}
    out.update({"projection_m": p, "ring_outer_plan_m2": _r(ring_o.area * m2),
                "ring_inner_plan_m2": _r(ring_i.area * m2),
                "ring_outer_inside_ff_raw_m2": _r(ring_o.intersection(FF0).area * m2),
                "ring_outer_in_pits_zone_m2": _r(ring_o.intersection(Z).area * m2),
                "straps": straps, "pits_zone_plan_m2": _r(Z.area * m2),
                "ring_handles": RING, "ff_outline": "route G FOUNDATION_PLAN box of FF (= S-FOOTINGS 1B2B, T-322)"})
    return out


def main(dxf):
    import ezdxf
    if hashlib.sha256(open(dxf, "rb").read()).hexdigest() != DXF_SHA:
        raise SystemExit("structural DXF sha mismatch")
    doc = ezdxf.readfile(dxf)
    out = {"schema": "URBAN_T700_ZONE_INPUT_V1",
           "source": {"drive": "Alsenan chalet project / ST7757 dxf.dxf", "sha256": DXF_SHA},
           "ground_sheet": ground_sheet_blocks(dxf, doc), "lift_pit": lift_pit(dxf, doc)}
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps(out, indent=1, sort_keys=True))


if __name__ == "__main__":
    main(sys.argv[1])
