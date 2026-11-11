"""T-695 own read (values only): the STRAP trench zone (B1-02 Z1-TRENCH-STRAPS) on the structural DXF.

    .work/venv/bin/python -I research/agents_t695/t695_extract.py <structural.dxf>
    -> research/agents_t695/STRAP_TRENCH_INPUT_T695.json (areas, handles, run keys; no coordinates, no drawing text)

What is read (same frames and calls as the merged T-350 r2 / T-356 readers, nothing typed by hand):
  * the pits zone Z (24 outlined footings + the p.13 projection 0.10, inside the plot, minus the pool envelope) exactly
    as research/agents_t350r2/t350r2_beam_over_pits.py builds it (route G registered on the foundation plan);
  * the F10 / F (1B1B) and FF outlines route G registers (their own zone lines PIT-F10F / PIT-FF);
  * the three straps by their edge LINE handles (T-174 / T-230 / T-356: SB1 1689 / 1B1C, SB2 1B08 / 1B09, SB3 1B26 /
    1B27), moved raw foundation frame -> route G by the frame offset the pits reader proves on every footing;
  * every ground-beam piece of the GROUND BEAMS PLAN (route G strips, the T-350 r2 piece keys) against the strap trench.

Two neat trench plans per strap (D-15 open: blinding under a strap printed nowhere):
  NEAT_B   the strap concrete plan (drawn edges) outside every pit / F10F / FF excavation plan;
  NEAT_BP  the strap grown 0.10 on its two SIDES (the p.13 projection, the T-356 'own layer' reading) outside them.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research/agents_t350r2"))

from shapely.geometry import LineString, MultiPoint, Point, Polygon, box  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

DXF_SHA = "9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079"
STRAPS = {"SB1": ("1689", "1B1C"), "SB2": ("1B08", "1B09"), "SB3": ("1B26", "1B27")}
OUT = HERE / "STRAP_TRENCH_INPUT_T695.json"


def _r(x, n=6):
    return round(x + 0.0, n)


def side_strip(hull, axis_line, pn):
    """the strap grown pn on its two sides only (not past its drawn ends): the T-356 strap_strip geometry"""
    (x0, y0), (x1, y1) = axis_line.coords[0], axis_line.coords[1]
    L = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
    ux, uy, nx, ny = (x1 - x0) / L, (y1 - y0) / L, -(y1 - y0) / L, (x1 - x0) / L
    ts = [c[0] * ux + c[1] * uy for c in hull.exterior.coords]
    t0, t1, big = min(ts), max(ts), 1e9
    slab = Polygon([(ux * t0 + nx * big, uy * t0 + ny * big), (ux * t1 + nx * big, uy * t1 + ny * big),
                    (ux * t1 - nx * big, uy * t1 - ny * big), (ux * t0 - nx * big, uy * t0 - ny * big)])
    return hull.buffer(pn, join_style=2).intersection(slab)


def gf_drop_evidence(msp, gbp, fpx0):
    """Is a sunken / dropped slab drawn on the GROUND BEAMS PLAN? Counts, per sheet frame, the hatches by layer and
    pattern (the 1F / 2F sunken wet panels are S-HAT.BAT ANSI31, T-214 / T-221) and lists the level marks (layer
    LEVEL) printed inside the ground-beam frame. Values only."""
    from collections import Counter
    from ezdxf import bbox
    fp = (fpx0, gbp[1], fpx0 + (gbp[2] - gbp[0]), gbp[3])
    cnt = Counter()
    for e in msp.query("HATCH"):
        b = bbox.extents([e])
        if not b.has_data:
            continue
        x, y = b.extmin.x, b.extmin.y
        fr = ("GROUND_BEAMS_PLAN" if gbp[0] <= x <= gbp[2] and gbp[1] <= y <= gbp[3] else
              "FOUNDATION_PLAN" if fp[0] <= x <= fp[2] and fp[1] <= y <= fp[3] else "OTHER_SHEETS")
        cnt[f"{fr}|{e.dxf.layer}|{e.dxf.pattern_name}"] += 1
    marks = sorted({(t.dxf.text or "").strip() for t in msp.query("TEXT[layer=='LEVEL']")
                    if gbp[0] <= t.dxf.insert.x <= gbp[2] and gbp[1] <= t.dxf.insert.y <= gbp[3]})
    return {"hatches": dict(sorted(cnt.items())), "ground_beam_plan_level_marks": marks}


def main(dxf):
    import hashlib

    import ezdxf
    import t350r2_beam_over_pits as B  # noqa: F401  (frames, plot handle, key function)
    from engine.source import generic_route as GR
    from engine.source import route_g_scope_v1 as SC
    from tools import urban_boq_m2 as M2

    if hashlib.sha256(open(dxf, "rb").read()).hexdigest() != DXF_SHA:
        raise SystemExit("structural DXF sha mismatch")
    R = M2.compute([dxf], conventions=str(B.CONV), profile=str(B.M4), route="G", completeness=False)
    D, conv = R["generic"]["D"], R["conv"]
    p = GR._trip(conv, "BLINDING_PROJECTION_M")[1]
    u = D["unit_m"]
    pn = p / u
    m2 = u * u
    state, shift, _ = GR._register_on_foundation(D)
    assert state == "REGISTERED", state
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
    pits, other, res_mm = [], {}, []
    for f in feet:
        bb = f["box"]
        cx, cy = (bb[0] + bb[2]) / 2 - ox, (bb[1] + bb[3]) / 2 - oy
        dist = lambda t: abs(t["x0_mm"] + t["dx_mm"] / 2 - cx) + abs(t["y0_mm"] + t["dy_mm"] / 2 - cy)  # noqa: E731
        m = min(t170, key=dist)
        res_mm.append(dist(m))
        q = Polygon(SC._quad(bb, pn))
        if m["type"] in ("FF", "F10/F"):
            other.setdefault(m["type"], []).append(q)
        else:
            pits.append(q)
    PU = unary_union(pits)
    doc = ezdxf.readfile(dxf)
    db, msp = doc.entitydb, doc.modelspace()
    plot = Polygon([(x + ox, y + oy) for x, y, *_ in db.get(B.PLOT_HANDLE).get_points()])
    assert abs(plot.area * m2 - 470.55) < 0.01
    # pool envelope, as the pits reader builds it
    pool = json.loads((ROOT / "research/agents_t189/ALSENAN_OVERLAP_INPUT.json").read_text())["pool"]
    from shapely import affinity
    rr, bxp = pool["outline"]["r_outer"], pool["outline"]["back_x"]
    d_ = Point(0, 0).buffer(rr, quad_segs=256).intersection(box(-rr, -rr, 0, rr)).union(box(0, -rr, bxp, rr))
    env = d_.buffer(0.10, quad_segs=256)
    ex_, ey_ = f8r["x0_mm"] / 1000 - pool["F8"]["x"][0], f8r["y0_mm"] / 1000 - pool["F8"]["y"][0]
    env = affinity.translate(affinity.scale(affinity.translate(env, ex_, ey_), 1000, 1000, origin=(0, 0)), ox, oy)
    Z = PU.intersection(plot).difference(env)
    zone_check = _r(Z.area * m2)
    F10F = unary_union(other.get("F10/F", []))
    FF = unary_union(other.get("FF", []))
    # F10 / F drawn open outline 1B1B (S02 'drawn outline' scenario; route G registers only its box)
    e1b = db.get("1B1B")
    f10_drawn = Polygon([(x + ox, y + oy) for x, y, *_ in e1b.get_points()]).buffer(0).buffer(pn, join_style=2)
    EXCL = unary_union([Z, F10F, FF])
    EXCL_DRAWN = unary_union([Z, f10_drawn, FF])

    inner = Polygon([(x + ox, y + oy) for x, y, *_ in db.get("1659").get_points()])
    band = plot.difference(inner)
    straps = {}
    trench_b, trench_bp, trench_bd, trench_bpd = [], [], [], []
    for mark, (h1, h2) in STRAPS.items():
        e1, e2 = db.get(h1), db.get(h2)
        L1 = LineString([(e1.dxf.start.x + ox, e1.dxf.start.y + oy), (e1.dxf.end.x + ox, e1.dxf.end.y + oy)])
        L2 = LineString([(e2.dxf.start.x + ox, e2.dxf.start.y + oy), (e2.dxf.end.x + ox, e2.dxf.end.y + oy)])
        hull = MultiPoint(list(L1.coords) + list(L2.coords)).convex_hull
        sp = side_strip(hull, L1, pn)
        nb = hull.difference(EXCL).intersection(plot)
        nbp = sp.difference(EXCL).intersection(plot)
        nb_d = hull.difference(EXCL_DRAWN).intersection(plot)
        nbp_d = sp.difference(EXCL_DRAWN).intersection(plot)
        widths = [L2.distance(Point(L1.coords[0])) * u, L2.distance(Point(L1.coords[1])) * u]
        straps[mark] = {
            "edge_handles": [h1, h2],
            "drawn_width_m": [_r(w, 4) for w in widths],
            "concrete_plan_outside_zones_m2": _r(nb.area * m2),
            "side_strip_plan_outside_zones_m2": _r(nbp.area * m2),
            "concrete_plan_outside_zones_f10_drawn_m2": _r(nb_d.area * m2),
            "side_strip_plan_outside_zones_f10_drawn_m2": _r(nbp_d.area * m2),
            "concrete_plan_inside_pits_zone_m2": _r(hull.intersection(Z).area * m2),
            "concrete_plan_inside_f10f_box_m2": _r(hull.intersection(F10F).area * m2),
            "beyond_plot_m2": _r(sp.difference(plot).area * m2),
            "side_strip_over_boundary_band_m2": _r(nbp.intersection(band).area * m2),
            "centre_axis_outside_zones_m": _r(LineString([
                ((L1.coords[0][0] + L2.coords[0][0]) / 2, (L1.coords[0][1] + L2.coords[0][1]) / 2),
                ((L1.coords[1][0] + L2.coords[1][0]) / 2, (L1.coords[1][1] + L2.coords[1][1]) / 2)]).difference(EXCL).length * u, 4),
        }
        trench_b.append((mark, nb))
        trench_bp.append((mark, nbp))
        trench_bd.append((mark, nb_d))
        trench_bpd.append((mark, nbp_d))
    TB = unary_union([g for _, g in trench_b])
    TBP = unary_union([g for _, g in trench_bp])
    # deeper zones a ground-beam trench never owns: pits, F10 / F (route G box and drawn outline), FF, the pool
    # envelope, the strap trench (widest reading) and the foundation-plan boundary band (S-BOUN 1658 - 1659, its
    # depth runs to the foundation level, ST p.1 note 2): the free strip is what a GB trench line alone can own.
    DEEP = unary_union([Z, F10F, f10_drawn, FF, env, TBP, band])

    # ground-beam pieces over the strap trench (route G strips, T-350 r2 piece keys)
    rows = []
    for rec in sorted(D["sheets"].values(), key=lambda r: r["sheet"]["sheet_id"]):
        if rec["sheet"]["role"] != "GROUND_BEAM_PLAN":
            continue
        sid = rec["sheet"]["sheet_id"]
        bpoly = {x["band_id"]: x for x in rec.get("bands", [])}
        seq = {}
        for b in rec.get("beams", []):
            k = B._key(b)
            seq[k] = seq.get(k, 0) + 1
            q = GR._strip_outline(b, bpoly.get(b["band_id"]), pn, *shift[sid])
            if q is None:
                if not b.get("polygon"):
                    continue
                dx, dy = shift[sid]
                Bm = Polygon([(x + dx, y + dy) for x, y in b["polygon"]])
                Bm = Bm if Bm.is_valid else Bm.buffer(0)
                S = Bm.buffer(pn, join_style=2)
            else:
                S = Polygon(q)
                Bm = Polygon(GR._strip_outline(b, bpoly.get(b["band_id"]), 0.0, *shift[sid]))
            row = {"piece": f"{k}#{seq[k]}", "L_routeG_m": _r(b["length_m"], 4),
                   "strip_m2": _r(S.intersection(plot).area * m2),
                   "strip_free_m2": _r(S.intersection(plot).difference(DEEP).area * m2),
                   "beam_free_m2": _r(Bm.intersection(plot).difference(DEEP).area * m2),
                   "strip_over_B_m2": _r(S.intersection(TB).area * m2),
                   "strip_over_BP_m2": _r(S.intersection(TBP).area * m2),
                   "beam_over_B_m2": _r(Bm.intersection(TB).area * m2),
                   "beam_over_BP_m2": _r(Bm.intersection(TBP).area * m2),
                   # per strap, per F10F end reading (BOX = route G box, DRAWN = 1B1B outline): [strip over B,
                   # strip over BP, beam over B, beam over BP] m2
                   "by_strap": {f"{mk}|{tag}": [_r(S.intersection(g).area * m2), _r(S.intersection(gp).area * m2),
                                                _r(Bm.intersection(g).area * m2), _r(Bm.intersection(gp).area * m2)]
                                for tag, TBl, TBPl in (("BOX", trench_b, trench_bp), ("DRAWN", trench_bd, trench_bpd))
                                for (mk, g), (_, gp) in zip(TBl, TBPl)
                                if S.intersection(gp).area * m2 > 1e-9}}
            rows.append(row)
    out = {
        "schema": "URBAN_T695_STRAP_TRENCH_INPUT_V1",
        "source": {"drive": "Alsenan chalet project / ST7757 dxf.dxf", "sha256": DXF_SHA,
                   "frame": "route G registered on FOUNDATION PLAN", "projection_m": p,
                   "projection_source": "ST7757.pdf p.13 typical footing / ground-beam details"},
        "pits_zone_plan_m2": zone_check,
        "pit_match_residual_mm_max": _r(max(res_mm), 1),
        "frame_offset_mm": [_r(ox, 3), _r(oy, 3)],
        "f10f_box_plan_m2": _r(F10F.area * m2),
        "f10f_drawn_grown_plan_m2": _r(f10_drawn.area * m2),
        "ff_box_plan_m2": _r(FF.area * m2),
        "straps": straps,
        "trench_union_B_m2": _r(TB.area * m2),
        "trench_union_BP_m2": _r(TBP.area * m2),
        "gb_pieces": rows,
        "gf_drop_evidence": gf_drop_evidence(msp, B.GBP, B.FPX0),
    }
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps(out, indent=1, sort_keys=True))


if __name__ == "__main__":
    main(sys.argv[1])
