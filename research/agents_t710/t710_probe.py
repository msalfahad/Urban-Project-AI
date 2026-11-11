"""T-710 own probe: the sunken 1F / 2F wet-room panels (ST 'Sunken slab.' hatches, T-213) laid over the architectural
1F / 2F plans, the wet rooms they sit under, and the boundary beams that bound the drop d.

    bash scripts/agent_env.sh run --tree task-T-710 research/agents_t710/t710_probe.py --arch <P7757.dxf> --st <ST7757.dxf> [--stage N]

Prints only RELATIVE geometry (metres), entity handles, lengths and areas; no absolute coordinate and no drawing text.
"""
from __future__ import annotations

import hashlib
import sys
from collections import Counter
from pathlib import Path

import ezdxf
from shapely.geometry import LineString, Polygon, Point
from shapely.ops import polygonize, unary_union

PANELS = ("275", "276", "280", "287", "298", "5BF")


def corners(e):
    p = list(e.get_points("xy"))
    xs, ys = [q[0] for q in p], [q[1] for q in p]
    return min(xs), max(xs), min(ys), max(ys)


def hatch_poly(e):
    polys = []
    for pth in e.paths:
        vs = [tuple(v)[:2] for v in pth.vertices] if hasattr(pth, "vertices") else [tuple(ed.start)[:2] for ed in pth.edges]
        if len(vs) >= 3:
            polys.append(Polygon(vs).buffer(0))
    return unary_union(polys)


def cols(doc):
    return [(e.dxf.handle, corners(e)) for e in doc.modelspace().query('LWPOLYLINE[layer=="S-COL.BON"]')]


def translations(src, dst, tol=2.0):
    """every translation src column -> same-size dst column, scored by how many src columns land on a dst column"""
    size = lambda c: (round(c[1] - c[0]), round(c[3] - c[2]))  # noqa: E731
    by = {}
    for h, c in dst:
        by.setdefault(size(c), []).append(c)
    votes = Counter()
    for _, s in src:
        for d in by.get(size(s), []):
            votes[(round(d[0] - s[0]), round(d[2] - s[2]))] += 1
    return votes.most_common(8)


def main(argv):
    arch, stp = argv[argv.index("--arch") + 1], argv[argv.index("--st") + 1]
    for name, p in (("arch", arch), ("st", stp)):
        print(name, "sha256", hashlib.sha256(Path(p).read_bytes()).hexdigest()[:8])
    ar, st = ezdxf.readfile(arch), ezdxf.readfile(stp)
    ac, sc = cols(ar), cols(st)
    print("columns arch", len(ac), "st", len(sc))
    # anchor: T-702 overlay ST 35C -> arch 2FAE (GF plan)
    a, c = corners(st.entitydb.get("35C")), corners(ar.entitydb.get("2FAE"))
    gdx, gdy = c[0] - a[0], c[2] - a[2]
    # arch plan-to-plan translations (GF plan -> other plans), relative only
    gf = [(h, k) for h, k in ac if abs(k[0] - c[0]) < 30000 and abs(k[2] - c[2]) < 30000]
    print("arch->arch translations from the GF zone (dx, dy mm relative; votes):")
    for t, v in translations(gf, ac):
        print("   ", t, v)
    print("st->st translations near 35C (votes):")
    sz = [(h, k) for h, k in sc if abs(k[0] - a[0]) < 30000 and abs(k[2] - a[2]) < 30000]
    for t, v in translations(sz, sc):
        print("   ", t, v)
    # panels: centroid relative to 35C, area
    for h in PANELS:
        e = st.entitydb.get(h)
        g = hatch_poly(e)
        cx, cy = g.centroid.x - a[0], g.centroid.y - a[2]
        print(f"panel {h} area {g.area/1e6:.4f} m2 centroid rel 35C ({cx/1000:.3f}, {cy/1000:.3f}) bbox "
              f"{(g.bounds[2]-g.bounds[0])/1000:.3f} x {(g.bounds[3]-g.bounds[1])/1000:.3f}")


if __name__ == "__main__" and "--stage" not in sys.argv:
    main(sys.argv)


def segs(doc, layers):
    out = []
    for e in doc.modelspace().query("LINE"):
        if e.dxf.layer in layers:
            out.append((e.dxf.handle, e.dxf.layer, LineString([tuple(e.dxf.start)[:2], tuple(e.dxf.end)[:2]])))
    for e in doc.modelspace().query("LWPOLYLINE"):
        if e.dxf.layer in layers:
            pts = [tuple(p)[:2] for p in e.get_points("xy")]
            if e.closed:
                pts.append(pts[0])
            if len(pts) >= 2:
                out.append((e.dxf.handle, e.dxf.layer, LineString(pts)))
    return out


def rays(pt, S, reach=8000):
    res = {}
    for name, (ux, uy) in (("E", (1, 0)), ("W", (-1, 0)), ("N", (0, 1)), ("S", (0, -1))):
        r = LineString([pt, (pt[0] + ux * reach, pt[1] + uy * reach)])
        best = None
        for h, lay, g in S:
            x = r.intersection(g)
            if x.is_empty:
                continue
            d = Point(pt).distance(x)
            if best is None or d < best[0]:
                best = (d, h, lay)
        res[name] = best
    return res


def stage2(ar, st):
    a, c = corners(st.entitydb.get("35C")), corners(ar.entitydb.get("2FAE"))
    gdx, gdy = c[0] - a[0], c[2] - a[2]
    lay = Counter(e.dxf.layer for e in ar.modelspace().query("LINE LWPOLYLINE"))
    print("arch layers (LINE/LWPOLYLINE):", lay.most_common(25))
    S = segs(ar, {"1", "S-COL.BON", "W", "5", "2"})
    for h in PANELS:
        g = hatch_poly(st.entitydb.get(h))
        if h == "5BF":
            sx, plan = 38724, -89705  # 1F-roof ST sheet -> GF-roof sheet frame, then GF arch -> 2F arch plan
        else:
            sx, plan = 0, -44853      # GF-roof ST sheet = 1F floor -> 1F arch plan
        pt = (g.centroid.x + sx + gdx + plan, g.centroid.y + gdy)
        bx = g.bounds
        print(f"panel {h}: hatch bbox {(bx[2]-bx[0])/1000:.3f} x {(bx[3]-bx[1])/1000:.3f}; rays from its centroid on the plan:")
        R = rays(pt, S)
        for k, v in R.items():
            print(f"    {k}: {'none' if v is None else f'{v[0]/1000:.4f} m to {v[1]} (layer {v[2]})'}")
        # panel edges to the hit faces (centroid offsets)
        print(f"    panel half-widths: E/W {(bx[2]-g.centroid.x)/1000:.4f} / {(g.centroid.x-bx[0])/1000:.4f}, "
              f"N/S {(bx[3]-g.centroid.y)/1000:.4f} / {(g.centroid.y-bx[1])/1000:.4f}")


if __name__ == "__main__" and "--stage" in sys.argv:
    _ar = ezdxf.readfile(sys.argv[sys.argv.index("--arch") + 1])
    _st = ezdxf.readfile(sys.argv[sys.argv.index("--st") + 1])
    if sys.argv[sys.argv.index("--stage") + 1] == "2":
        stage2(_ar, _st)


def stage3(ar, st):
    """grid-sample each panel; group samples by the 4 faces their rays hit (= the room cell); cell box and overlap"""
    from shapely.geometry import box
    a, c = corners(st.entitydb.get("35C")), corners(ar.entitydb.get("2FAE"))
    gdx, gdy = c[0] - a[0], c[2] - a[2]
    S = segs(ar, {"1", "S-COL.BON", "W", "5", "2", "D"})
    for h in PANELS:
        g = hatch_poly(st.entitydb.get(h))
        sx, plan = (38724, -89705) if h == "5BF" else (0, -44853)
        from shapely.affinity import translate
        gp = translate(g, sx + gdx + plan, gdy)
        x0, y0, x1, y1 = gp.bounds
        near = gp.buffer(6500)
        SS = [t for t in S if t[2].intersects(near)]
        cells = {}
        n = 0
        step = 100.0
        yy = y0 + step / 2
        while yy < y1:
            xx = x0 + step / 2
            while xx < x1:
                if gp.contains(Point(xx, yy)):
                    n += 1
                    R = rays((xx, yy), SS, reach=6000)
                    if None in R.values():
                        key = ("OPEN",) + tuple((k, v[1] if v else None) for k, v in R.items())
                        bx = None
                    else:
                        key = tuple(R[k][1] for k in ("W", "E", "S", "N"))
                        bx = (xx - R["W"][0], xx + R["E"][0], yy - R["S"][0], yy + R["N"][0])
                    cells.setdefault(key, [0, bx])[0] += 1
                xx += step
            yy += step
        print(f"panel {h}: area {gp.area/1e6:.4f} m2, {n} samples at {step:.0f} mm")
        for key, (cnt, bx) in sorted(cells.items(), key=lambda kv: -kv[1][0]):
            if cnt < 3:
                continue
            if bx is None:
                print(f"    {cnt:4d} samples OPEN ray: {key}")
                continue
            B = box(bx[0], bx[2], bx[1], bx[3])
            ov = gp.intersection(B).area
            ex = gp.exterior if gp.geom_type == "Polygon" else None
            print(f"    {cnt:4d} samples cell W/E/S/N {key}: box {(bx[1]-bx[0])/1000:.4f} x {(bx[3]-bx[2])/1000:.4f} = "
                  f"{B.area/1e6:.4f} m2; panel in it {ov/1e6:.4f} m2; panel offset from box W/E/S/N "
                  f"{(gp.intersection(B).bounds[0]-bx[0])/1000:.3f} {(bx[1]-gp.intersection(B).bounds[2])/1000:.3f} "
                  f"{(gp.intersection(B).bounds[1]-bx[2])/1000:.3f} {(bx[3]-gp.intersection(B).bounds[3])/1000:.3f}")


if __name__ == "__main__" and "--stage" in sys.argv and sys.argv[sys.argv.index("--stage") + 1] == "3":
    stage3(_ar, _st)


# room cells by their four face lines (W, E, S, N), as found by stage 3; ids by floor area match (T-691 for the twins)
CELLS = {
    "1F-RED23B8": ("B09", "B01", "AD6", "B1F", "275"),
    "1F-R52AC05": ("B05", "B0E", "AD7", "CC5", "276"),
    "1F-R48AA46": ("B3E", "C23", "AE4", "C28", "280"),
    "1F-R8BDA49": ("C22", "C1C", "C25", "C26", "280 287"),
    "1F-R48CDA5": ("C0D", "B69", "B1B", "C0C", "298"),
    "2F-RE83BED": ("1296", "128F", "1298", "127B", "5BF"),
    "1F-DRY-NORTH": ("B3F", "C1F", "C29", "C24", "280 287"),
}


def coord(doc, h, axis):
    e = doc.entitydb.get(h)
    if e.dxftype() == "LINE":
        p, q = e.dxf.start, e.dxf.end
    else:
        pts = list(e.get_points("xy"))
        p, q = pts[0], pts[-1]
    return (p[0] + q[0]) / 2 if axis == "x" else (p[1] + q[1]) / 2, e.dxftype(), e.dxf.layer


def stage4(ar, st):
    from shapely.affinity import translate
    from shapely.geometry import box
    a, c = corners(st.entitydb.get("35C")), corners(ar.entitydb.get("2FAE"))
    gdx, gdy = c[0] - a[0], c[2] - a[2]
    # overlay check on the 1F and 2F plans: ST columns of each sheet within 12 m of the panels -> arch columns
    acs = [k for _, k in cols(ar)]
    for label, sx, plan, hs in (("GF-roof sheet -> 1F plan", 0, -44853, PANELS[:5]), ("1F-roof sheet -> 2F plan", 38724, -89705, ("5BF",))):
        cen = unary_union([hatch_poly(st.entitydb.get(h)) for h in hs]).centroid
        n = m = 0
        worst = 0.0
        for _, s in cols(st):
            if abs((s[0] + s[1]) / 2 - cen.x) > 12000 or abs((s[2] + s[3]) / 2 - cen.y) > 12000:
                continue
            m += 1
            t = (s[0] + sx + gdx + plan, s[1] + sx + gdx + plan, s[2] + gdy, s[3] + gdy)
            r = min(acs, key=lambda q: sum(abs(q[i] - t[i]) for i in range(4)))
            err = max(abs(r[i] - t[i]) for i in range(4))
            if err <= 2.0:
                n += 1
                worst = max(worst, err)
        print(f"overlay {label}: {n} of {m} ST column outlines within 12 m land on an arch column, worst {worst:.1f} mm")
    P = {}
    for h in PANELS:
        sx, plan = (38724, -89705) if h == "5BF" else (0, -44853)
        P[h] = translate(hatch_poly(st.entitydb.get(h)), sx + gdx + plan, gdy)
        ext = max(P[h].geoms, key=lambda g: g.area) if P[h].geom_type == "MultiPolygon" else P[h]
        print(f"panel {h}: union of loops {P[h].area/1e6:.4f} m2, outer loop {Polygon(ext.exterior).area/1e6:.4f} m2, perimeter of union {P[h].length/1000:.4f} m")
    for rid, (w, e_, s, n, ph) in CELLS.items():
        x0, t0, l0 = coord(ar, w, "x"); x1, t1, l1 = coord(ar, e_, "x"); y0, t2, l2 = coord(ar, s, "y"); y1, t3, l3 = coord(ar, n, "y")
        B = box(x0, y0, x1, y1)
        print(f"{rid}: faces {w}/{e_}/{s}/{n} layers {l0}/{l1}/{l2}/{l3}: {abs(x1-x0)/1000:.4f} x {abs(y1-y0)/1000:.4f} = {B.area/1e6:.4f} m2, perimeter {B.length/1000:.4f}")
        for h in ph.split():
            # use the outer loops only (annotation islands are not voids: T-213 rule a)
            g = P[h]
            outer = unary_union([Polygon(q.exterior) for q in (g.geoms if g.geom_type == "MultiPolygon" else [g])])
            I = outer.intersection(B)
            if I.area < 1e3:
                continue
            on_face = I.boundary.intersection(B.boundary.buffer(1.0)).length
            print(f"    panel {h}: in the room {I.area/1e6:.4f} m2 ({I.area/B.area*100:.1f} % of the floor); recess loop "
                  f"{I.length/1000:.4f} m = along the room faces {on_face/1000:.4f} + free step inside the room {(I.length-on_face)/1000:.4f}")


if __name__ == "__main__" and "--stage" in sys.argv and sys.argv[sys.argv.index("--stage") + 1] == "4":
    stage4(_ar, _st)


def stage5(ar, st):
    """face walk of each wet-room cell: covered by wall lines (layer 1) or a column outline; gaps classed by what is in them"""
    from shapely.geometry import box
    S = segs(ar, {"1", "S-COL.BON"})
    Wl = segs(ar, {"W"})
    Dl = segs(ar, {"D"})
    for rid, (w, e_, s, n, _) in CELLS.items():
        if rid.startswith("1F-DRY"):
            continue
        x0 = coord(ar, w, "x")[0]; x1 = coord(ar, e_, "x")[0]; y0 = coord(ar, s, "y")[0]; y1 = coord(ar, n, "y")[0]
        B = box(x0, y0, x1, y1)
        near = [g for _, _, g in S if g.distance(B.boundary) < 5]
        wn = [g for _, _, g in Wl if g.distance(B.boundary) < 400]
        dn = [g for _, _, g in Dl if g.distance(B) < 1200]
        cs = [g for h_, l_, g in S if l_ == "S-COL.BON" and len(g.coords) >= 4 and g.is_closed and Polygon(g.coords).buffer(-1).intersects(B)]
        notch = sum(Polygon(g.coords).intersection(B).area for g in cs if g.is_closed) / 1e6
        cov = unary_union([g.buffer(1.5) for g in near])
        print(f"{rid}: box {abs(x1-x0)/1000:.4f} x {abs(y1-y0)/1000:.4f}; column area inside the box {notch:.4f} m2")
        sides = {"W": ((x0, y0), (x0, y1)), "E": ((x1, y0), (x1, y1)), "S": ((x0, y0), (x1, y0)), "N": ((x0, y1), (x1, y1))}
        for k, (p, q) in sides.items():
            L = LineString([p, q])
            gap = L.difference(cov)
            parts = [] if gap.is_empty else (list(gap.geoms) if hasattr(gap, "geoms") else [gap])
            out = []
            for g in parts:
                if g.length < 20:
                    continue
                kind = "window" if any(x.distance(g) < 350 for x in wn) else ("door" if any(x.distance(g) < 1100 for x in dn) else "open")
                st0 = L.project(Point(g.coords[0])) / 1000
                out.append(f"{kind} {g.length/1000:.4f} at {st0:.3f}")
            print(f"    {k} side {L.length/1000:.4f} m: gaps {out if out else 'none'}")


if __name__ == "__main__" and "--stage" in sys.argv and sys.argv[sys.argv.index("--stage") + 1] == "5":
    stage5(_ar, _st)
