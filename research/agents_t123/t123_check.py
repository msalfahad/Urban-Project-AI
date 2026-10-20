"""T-123 reproduction (research only, not a method): GF facade run vs billable run vs reveal returns, and the slab over
the GF side passage read from the structural slab sheet by raw entities (no route G, no engine faces).

    python3 -I research/agents_t123/t123_check.py <plan.dxf> <structural.dxf> <V2.12 run dir>

<V2.12 run dir> is the output of
    python3 -I -c "from tools import urban_boq_m9 as M; M.main(['arch','--drawings','<plan.dxf>','--out','<dir>',
        '--method','ARCH_TAKEOFF_V2.12','--no-svg','--no-m9-xlsx','--facts','research/urban_m9_s2/SYNTHETIC_FACTS_S2.json'])"
The drawings stay outside the repository (Drive, read-only). The script prints lengths, areas, counts, entity handles,
line ids and coordinates LOCAL to two drawn anchors (metres): N = the corner of the GF column whose face meets the pool
glazing frame (column handle given), P = the passage corner where the annex face meets the boundary wall's inner face.
No absolute drawing coordinates, no names.
"""
import json
import math
import sys
from collections import Counter
from pathlib import Path

import ezdxf
from ezdxf import bbox, path as dxfpath
from shapely.affinity import translate
from shapely.geometry import Polygon, box

U = 0.001                                   # both drawings are in mm (INSUNITS 4)
COL_NOTCH = "2F87"                          # GF column at the north end of the curved pool glazing (layer S-COL.BON)


def poly_of_hatch(doc, handle):
    e = doc.entitydb.get(handle)
    g = None
    for pp in dxfpath.from_hatch(e):
        p = Polygon([(v.x, v.y) for v in pp.flattening(10)]).buffer(0)
        g = p if g is None else g.symmetric_difference(p)
    return g, e


def ents_in(doc, x0, y0, x1, y1, max_span=25000):
    out = []

    def walk(ents, blk=""):
        for e in ents:
            t = e.dxftype()
            if t == "INSERT":
                try:
                    walk(e.virtual_entities(), e.dxf.name)
                except Exception:              # noqa: BLE001
                    out.append(("INSERT_NOT_EXPLODED", e.dxf.name, None, None))
                continue
            try:
                b = bbox.extents([e])
                lay = e.dxf.layer
            except Exception:                  # noqa: BLE001
                continue
            if not b.has_data or b.extmax.x < x0 or b.extmin.x > x1 or b.extmax.y < y0 or b.extmin.y > y1:
                continue
            if b.extmax.x - b.extmin.x > max_span or b.extmax.y - b.extmin.y > max_span:
                continue
            out.append((t, lay, blk, (b.extmin.x, b.extmin.y, b.extmax.x, b.extmax.y), e))
    walk(doc.modelspace())
    return out


def main():
    arch_p, st_p, run = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    A = ezdxf.readfile(str(arch_p))
    B = ezdxf.readfile(str(st_p))
    plan = json.loads((run / "ARCH_PLAN.json").read_text())
    gf_box = [v for r in plan["regions"] if r["floor"] == "GF" for v in r["box"]]
    f1_box = [v for r in plan["regions"] if r["floor"] == "1F" for v in r["box"]]
    off_1f = f1_box[0] - gf_box[0]

    # ---------- 1. the notch: walked vs closed vs returns (GF outline of the V2.12 run) ----------
    fac = json.loads((run / "FACADE.json").read_text())
    gf = [f for f in fac["floors"] if f["floor"] == "GF"][0]["outlines"][0]
    ring = gf["ring_m"]
    col = A.entitydb.get(COL_NOTCH)
    cx = [p[0] * U for p in col.get_points("xy")]
    cy = [p[1] * U for p in col.get_points("xy")]
    N = (min(cx), min(cy))                                   # column corner nearest the glazing
    k = min(range(len(ring)), key=lambda i: math.dist(ring[i], N))
    print(f"GF released run (V2.12) {gf['perimeter_m']:.6f} m; by role {gf['by_role']}")
    print(f"notch at column {COL_NOTCH} ({(max(cx) - min(cx)):.3f} x {(max(cy) - min(cy)):.3f} m); ring walk from its "
          "corner N (local m):")
    walk = 0.0
    for i in range(k, k + 4):
        a, b = ring[i], ring[i + 1]
        d = math.dist(a, b)
        print(f"   v{i - k}: ({a[0] - N[0]:+.4f}, {a[1] - N[1]:+.4f}) -> ({b[0] - N[0]:+.4f}, {b[1] - N[1]:+.4f})"
              f"  {d:.4f} m")
        if i < k + 3:
            walk += d
    chord = math.dist(ring[k], ring[k + 3])
    print(f"   walked round the notch {walk:.4f} m; straight across at the column face line {chord:.4f} m; "
          f"returns {walk - chord:.4f} m")

    # ---------- 2. which BOQ line measures those faces? ----------
    lines = json.loads((run / "BOQ_LINES.json").read_text())
    lines = lines["lines"] if isinstance(lines, dict) else lines
    ops = {o["opening_id"]: o for o in json.loads((run / "ARCH_OPENINGS.json").read_text())["openings"]
           if o["floor"] == "GF"}
    rev = [ln for ln in lines if ln["item_code"] == "ARCH.WINDOW_REVEAL" and ln["location"]["floor"] == "GF"]
    print(f"GF ARCH.WINDOW_REVEAL lines in V2.12: {len(rev)}")
    for ln in rev:
        oid = ln["calculation"]["inputs"]["opening_ids"][0]
        c = ops[oid]["position"]["centre_m"]
        print(f"   {ln['line_id']} {oid} {ops[oid]['width_m']} m, value {ln['measured_net']} "
              f"({ln['evidence_state']}), {math.dist(c, N):.2f} m from the notch")
    cur = json.loads((run / "CURVED_OPENINGS.json").read_text())
    print(f"curved openings in V2.12: {[(c['floor'], c['opening_id']) for c in cur['curved_openings']]}; "
          f"GF curved gaps rejected: {[(g['r1_m'], g['r2_m'], g['reason']) for g in cur['curved_gaps_rejected'] if g['floor'] == 'GF']}")
    gfwin = [ln for ln in lines if ln["item_code"] == "ARCH.WINDOW" and ln["location"]["floor"] == "GF"]
    print(f"GF ARCH.WINDOW lines: {len(gfwin)} ({sorted(ln['location']['element_id'].split(':')[1] for ln in gfwin)}); "
          f"GF outline length walked on window frames (role WINDOW): {gf['by_role'].get('WINDOW', 0):.6f} m")

    # ---------- 3. the side passage on the GF plan ----------
    P0 = None
    for i in range(len(ring) - 1):                           # the 1.20 m of the outline walked over the boundary wall
        a, b = ring[i], ring[i + 1]
        if abs(a[1] - b[1]) < 1e-6 and abs(math.dist(a, b) - 1.2) < 1e-6 and a[0] > b[0] and a[1] < ring[k][1] - 10:
            P0 = (b[0], a[1])
    mouth = [(i, ring[i], ring[i + 1]) for i in range(len(ring) - 1)
             if abs(ring[i][1] - ring[i + 1][1]) < 1e-6 and abs(math.dist(ring[i], ring[i + 1]) - 1.2) < 1e-6
             and abs(ring[i][0] - P0[0]) < 1e-6]
    ym = mouth[0][1][1]
    # boundary wall inner face: the layer-5 line pair across the strip
    xs0, xs1 = P0[0], P0[0] + 1.2
    across = [e for e in ents_in(A, xs0 / U - 50, P0[1] / U - 50, xs1 / U + 50, ym / U + 400)
              if e[0] == "LINE" and abs(e[4].dxf.start.y - e[4].dxf.end.y) < 1 and
              min(e[4].dxf.start.x, e[4].dxf.end.x) <= xs0 / U + 1 and max(e[4].dxf.start.x, e[4].dxf.end.x) >= xs1 / U - 1]
    ys = []
    for y in sorted(e[4].dxf.start.y * U for e in across):        # raw values, duplicates within 1 mm merged
        if not ys or y - ys[-1] > 1e-3:
            ys.append(y)
    print(f"passage: outline walks the boundary wall at local y 0 and crosses the mouth at {ym - P0[1]:+.4f} m; lines "
          f"drawn across the full 1.20 m width at local y {[round(y - P0[1], 4) for y in ys]} "
          f"(layers {sorted({e[1] for e in across})})")
    yin = [y for y in ys if y > P0[1] + 1e-3 and y < ym - 1e-3]
    inner = min(yin) if yin else None
    L = ym - inner
    print(f"   boundary wall {inner - P0[1]:.3f} m thick (two lines, no opening in it); clear passage length "
          f"{L:.3f} m x width {xs1 - xs0:.3f} m = {L * (xs1 - xs0):.3f} m2")
    near = ents_in(A, xs0 / U - 10, ym / U - 10, xs1 / U + 10, ym / U + 10)
    cross_mouth = [e for e in near if e[3][0] < xs1 / U - 5 and e[3][2] > xs0 / U + 5 and e[3][1] < ym / U + 5
                   and e[3][3] > ym / U - 5 and e[1] not in ("4",)]
    print(f"   entities crossing the mouth (any layer except dimensions): {len(cross_mouth)} "
          f"{Counter((e[0], e[1]) for e in cross_mouth)}")
    inside = ents_in(A, xs0 / U + 5, inner / U + 5, xs1 / U - 5, ym / U - 5)
    print(f"   inside the strip: {Counter((e[0], e[1], e[2]) for e in inside)}; level texts "
          f"{[e[4].dxf.text for e in inside if e[0] == 'TEXT' and e[1] == 'LEVEL']}")
    beyond = ents_in(A, xs0 / U - 1000, ym / U + 10, xs1 / U + 1600, ym / U + 4000)
    print(f"   beyond the mouth (4.0 m): doors {sum(1 for e in beyond if e[1] == 'D')}, windows "
          f"{sum(1 for e in beyond if e[1] == 'W')}, level texts "
          f"{[e[4].dxf.text for e in beyond if e[0] == 'TEXT' and e[1] == 'LEVEL']}")
    walls = 0.0
    for x in (xs0, xs1):
        walls += L
    print(f"   run under Q-67 A: released {gf['perimeter_m']:.6f} - mouth 1.200 - boundary 1.200 + annex face {L:.3f} + "
          f"house face {L:.3f} = {gf['perimeter_m'] - 2.4 + walls:.6f} m")

    # ---------- 4. the GF roof slab sheet over the passage (raw entities) ----------
    def cols(doc, bx):
        r = []
        for e in doc.modelspace().query('LWPOLYLINE[layer=="S-COL.BON"]'):
            p = list(e.get_points("xy"))
            q = (min(a[0] for a in p), min(a[1] for a in p), max(a[0] for a in p), max(a[1] for a in p))
            if bx[0] <= q[0] <= bx[2] and bx[1] <= q[1] <= bx[3]:
                r.append(q)
        return r
    titles = [e for e in ents_in(B, -1e9, -1e9, 1e9, 1e9) if e[0] in ("TEXT", "MTEXT")
              and "GROUND FLOOR ROOF SLAB" in (e[4].dxf.text if e[0] == "TEXT" else e[4].plain_text())]
    tx = titles[0][3][0]
    sheet = (tx - 22000, 30000, tx + 17000, 56000)            # the sheet band round its title (title x -/+)
    ca, cb = cols(A, [v for v in gf_box]), cols(B, sheet)
    votes = Counter()
    for a in ca:
        for b in cb:
            if abs((a[2] - a[0]) - (b[2] - b[0])) < 2 and abs((a[3] - a[1]) - (b[3] - b[1])) < 2:
                votes[(round(b[0] - a[0], 1), round(b[1] - a[1], 1))] += 1
    (dx, dy), n = votes.most_common(1)[0]
    print(f"GF roof slab sheet registered on the GF plan by column outlines: {n} of {len(ca)} GF columns coincide "
          f"(next best offset {votes.most_common(2)[1][1]} votes); translation only")
    sx0, sx1, sy0, sy1 = xs0 / U + dx, xs1 / U + dx, inner / U + dy, ym / U + dy
    over = ents_in(B, sx0 + 5, sy0 + 5, sx1 - 5, sy1 - 5)
    hz = sorted({(round(e[4].dxf.start.y - dy - inner / U), e[1], e[4].dxf.handle) for e in over
                 if e[0] == "LINE" and abs(e[4].dxf.start.y - e[4].dxf.end.y) < 1
                 and min(e[4].dxf.start.x, e[4].dxf.end.x) <= sx0 + 1 and max(e[4].dxf.start.x, e[4].dxf.end.x) >= sx1 - 1})
    edge = ents_in(B, sx0 - 5, sy0 - 5, sx1 + 5, sy0 + 5)
    edge_l = [e for e in edge if e[0] == "LINE" and abs(e[4].dxf.start.y - e[4].dxf.end.y) < 1 and abs(e[4].dxf.start.y - sy0) < 2]
    print(f"   slab edge at the boundary wall's inner face: {[(e[1], e[4].dxf.handle) for e in edge_l]}")
    print(f"   lines across the whole passage width on the slab sheet (mm from the boundary inner face, layer, handle): {hz}")
    labels = [e for e in ents_in(B, sx0 - 600, sy0 - 300, sx1 + 900, sy1 + 300) if e[0] == "TEXT"
              and e[1] in ("S-TEXT", "S-TEXT-SLAB")]
    print(f"   beam and bar labels near: {sorted((e[4].dxf.text, e[4].dxf.handle or e[2]) for e in labels)}")
    rein = [e for e in over if e[1] == "S-REIN-SLAB"]
    print(f"   slab bars drawn inside the passage: {len(rein)} lines {sorted(e[4].dxf.handle for e in rein)}")
    hat = [e for e in over if e[0] == "HATCH" and e[1] == "S-HAT.BAT"]
    pas_s = box(sx0, sy0, sx1, sy1)
    for e in hat:
        g, he = poly_of_hatch(B, e[4].dxf.handle)
        print(f"   hatch {he.dxf.handle} ({he.dxf.pattern_name}, layer S-HAT.BAT) over the passage "
              f"{g.intersection(pas_s).area * U * U:.4f} m2, local y {g.intersection(pas_s).bounds[1] - sy0:.0f} .. "
              f"{g.intersection(pas_s).bounds[3] - sy0:.0f} mm")
    # bands from the lines across: beams are the 0.20 pairs, panels the rest
    yy = sorted({h[0] for h in hz} | {0, round(L / U)})
    print(f"   band edges along the passage (mm from the boundary inner face): {yy}")
    w = xs1 - xs0
    for a, b in zip(yy, yy[1:]):
        print(f"      {a:5d} .. {b:5d}: {(b - a) / 1000:.3f} m x {w:.3f} = {(b - a) / 1000 * w:.3f} m2")

    # ---------- 5. the 1F plan over the passage: the roof hatch and the 1F walls ----------
    roof = [e for e in ents_in(A, xs0 / U + off_1f, P0[1] / U, xs1 / U + off_1f, ym / U)
            if e[0] == "HATCH" and e[1] == "3"]
    pas = box(xs0 / U, inner / U, xs1 / U, ym / U)
    for e in roof:
        g, he = poly_of_hatch(A, e[4].dxf.handle)
        loops = list(dxfpath.from_hatch(he))
        outer = max((Polygon([(v.x, v.y) for v in pp.flattening(10)]).buffer(0) for pp in loops), key=lambda p: p.area)
        outer = translate(outer, -off_1f, 0)
        ib = outer.intersection(pas)
        print(f"1F plan hatch {he.dxf.handle} ({he.dxf.pattern_name}, layer 3): its outer loop covers "
              f"{ib.area * U * U:.4f} m2 of the passage, local y {(ib.bounds[1] - inner / U):.0f} .. "
              f"{(ib.bounds[3] - inner / U):.0f} mm ({len(loops) - 1} inner loops, not used)")
    f1 = [e for e in ents_in(A, xs0 / U + off_1f + 5, inner / U + 5, xs1 / U + off_1f - 5, ym / U - 5)
          if e[0] == "LINE" and e[1] == "1" and abs(e[4].dxf.start.y - e[4].dxf.end.y) < 1]
    print(f"1F plan wall lines (layer 1) across the passage (local y mm): {sorted({round(e[4].dxf.start.y - inner / U) for e in f1})}")


if __name__ == "__main__":
    main()
