"""T-597 on the development villa: own re-measure of the B1 excavation PLAN side from the structural DXF (Drive
'Alsenan chalet project' / 'ST7757 dxf.dxf', decoded into .work/private; sha256 prefix 9f9d1179 checked).

Own reads, by layer and handle (no engine route, no earlier ledger read for geometry):
  - FOUNDATION PLAN frame: S-FOOTINGS closed LWPOLYLINEs, open 6-vertex LWPOLYLINEs (bounding rectangle, flagged),
    LINE squares (polygonized), S-DIM INSERT 'F' block outlines; footing label TEXT / INSERT texts inside each outline;
  - footing schedule INSERT FT / FTB (W, H, DEPHT in cm) -> every pit outline checked against its schedule size;
  - plot polygon 1658 (S-BOUN, foundation frame);
  - pool outer shell 7C6 (S-BW, BEAMS PLAN frame, translated +38 724.4 mm in x: the sheet offset, re-derived here from
    the plot rectangles 7FE / 1658 and checked on the FN repeat 80B..80E -> 1100..1103);
  - the exterior ground-beam edge lines on layer '1' (BEAMS PLAN frame) by their run handles, and the column outlines
    S-COL.BON (foundation frame).
Printed values used (cited, not re-read here): ST7757.pdf p.13 blinding projection 0.10 each side (T-170 / T-206,
Checker-verified); p.7 pool screed 5 cm + membrane 5 cm outside the shell (T-183 r2, Checker-verified).

    .work/venv/bin/python -I research/agents_t597/t597_alsenan.py .work/private/st7757.dxf
      -> research/agents_t597/out/T597_PLAN_SIDE.json (handles, sizes, m2 only; no client data)
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from shapely.geometry import LineString, Point, Polygon, box  # noqa: E402
from shapely.ops import polygonize, unary_union  # noqa: E402

import pit_union_v1 as U  # noqa: E402

SHA_PREFIX = "9f9d1179"
FP = (115000.0, 155000.0, 33000.0, 53000.0)       # foundation plan frame, raw mm
BP = (78900.0, 114200.0, 29000.0, 57100.0)        # beams plan frame, raw mm
PROJ = 0.10                                      # ST p.13 '10 | L x W | 10'
POOL_LAYERS = 0.10                               # ST p.7 5 cm screed + 5 cm membrane (T-183 r2)
PLOT_FP, PLOT_BP = "1658", "7FE"
POOL_OUTER = "7C6"
CHECKED_BEFORE = {"1B07", "1ABF", "1ADB", "1B1A", "1B2A", "1B19", "1B24", "180F"}   # T-565 Checker 8 / 24
NOT_PITS = {"FF": "lift raft: own zone Z1-PIT-FF (D-43)", "F10/F": "open outline 1B1B, two tags: zone F10F (Q-31 C)"}
EXT_RUNS = {   # exterior main ground-beam runs (class from the T-253 ledger; geometry read here): edge-line handles
    "170+7C3": ("170", "7C3"), "10A+7C9": ("10A", "7C9"), "145+7CA": ("145", "7CA"), "109+7CB": ("109", "7CB"),
    "107+7CE": ("107", "7CE"), "7D0+FC": ("7D0", "FC"), "114+115+7DF": ("114", "7DF"), "7E0+FD": ("7E0", "FD")}
EXT_ARC = ("157", "158")
# main-exterior pieces per run (T-253 class, its piece numbers #k counted along increasing x / y): the geometry of
# every piece is read here; only the class membership is taken from the T-253 ledger (cited, not re-derived)
EXT_PIECES_T253 = {"170+7C3": {1: 2.4, 2: 3.37, 3: 3.35, 4: 3.25}, "10A+7C9": {1: 4.3}, "145+7CA": {1: 1.9},
                   "109+7CB": {2: 4.4, 3: 2.7}, "107+7CE": {1: 0.3639}, "7D0+FC": {1: 2.975, 2: 5.745, 3: 6.35, 4: 1.2},
                   "114+115+7DF": {2: 1.0}, "7E0+FD": {1: 3.35, 2: 3.25}}   # T-253 L total 55.99
EXT_SECOND_EDGE = {"114+115+7DF": ("115", "7DF")}   # one beam face drawn as two collinear LINEs


EXTENT = "COMMON"   # 'COMMON' (both faces drawn) or 'EITHER' (junction squares included); both are reported


def _extent(a0, a1, b0, b1):
    if EXTENT == "COMMON":
        return max(min(a0, a1), min(b0, b1)), min(max(a0, a1), max(b0, b1))
    return min(a0, a1, b0, b1), max(a0, a1, b0, b1)


def _in(fr, x, y):
    return fr[0] <= x <= fr[1] and fr[2] <= y <= fr[3]


def read(dxf):
    import ezdxf
    from ezdxf import bbox
    raw = Path(dxf).read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if not sha.startswith(SHA_PREFIX):
        raise SystemExit(f"unexpected drawing sha {sha[:8]}")
    doc = ezdxf.readfile(dxf)
    msp, db = doc.modelspace(), doc.entitydb
    d = {"sha8": sha[:8], "outlines": {}, "labels": [], "sched": {}, "cols": []}
    lines = []
    for e in msp:
        t = e.dxftype()
        try:
            lay = e.dxf.layer
        except Exception:
            continue
        if lay == "S-FOOTINGS" and t == "LWPOLYLINE":
            pts = [(x / 1000, y / 1000) for x, y in e.get_points("xy")]
            cx = sum(p[0] for p in pts) / len(pts) * 1000
            cy = sum(p[1] for p in pts) / len(pts) * 1000
            if not _in(FP, cx, cy):
                continue
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            rect = box(min(xs), min(ys), max(xs), max(ys))
            poly = Polygon(pts) if e.closed else None
            kind = "CLOSED_LWPOLYLINE" if e.closed else "OPEN_LWPOLYLINE_BBOX"
            if poly is not None and abs(poly.area - rect.area) > 1e-9:
                kind = "CLOSED_NON_RECT"
            d["outlines"][e.dxf.handle] = {"geom": poly if poly is not None and kind != "CLOSED_NON_RECT" else rect,
                                           "kind": kind, "exact": poly}
        elif lay == "S-FOOTINGS" and t == "LINE":
            s, u = e.dxf.start, e.dxf.end
            if _in(FP, (s.x + u.x) / 2, (s.y + u.y) / 2):
                lines.append((e.dxf.handle, LineString([(s.x / 1000, s.y / 1000), (u.x / 1000, u.y / 1000)])))
        elif t == "INSERT" and lay == "S-DIM" and e.dxf.name == "F":
            b = bbox.extents([e])
            if _in(FP, b.center.x, b.center.y):
                d["outlines"][e.dxf.handle] = {"geom": box(b.extmin.x / 1000, b.extmin.y / 1000, b.extmax.x / 1000,
                                                          b.extmax.y / 1000), "kind": "INSERT_F_BLOCK",
                                               "rot": e.dxf.rotation}
        elif t == "INSERT" and e.dxf.name in ("FT", "FTB"):
            a = {x.dxf.tag: x.dxf.text for x in e.attribs}
            d["sched"][a["FO-TY"]] = (float(a["W"]) / 100, float(a["H"]) / 100, float(a["DEPHT"]) / 100,
                                      e.dxf.handle)
        elif lay == "S-COL.BON" and t == "LWPOLYLINE" and e.closed:
            pts = [(x / 1000, y / 1000) for x, y in e.get_points("xy")]
            if _in(FP, pts[0][0] * 1000, pts[0][1] * 1000):
                d["cols"].append(Polygon(pts))
        if t == "TEXT" and _in(FP, e.dxf.insert.x, e.dxf.insert.y):
            d["labels"].append((e.dxf.text.strip(), Point(e.dxf.insert.x / 1000, e.dxf.insert.y / 1000), e.dxf.handle))
        if t == "INSERT" and lay == "S-DIM" and e.dxf.name in ("CF", "F11", "F"):
            for v in e.virtual_entities():
                if v.dxftype() == "TEXT":
                    p = v.dxf.insert
                    d["labels"].append((v.dxf.text.strip(), Point(p.x / 1000, p.y / 1000), e.dxf.handle))
    # four-LINE squares
    hs = {}
    for pg in polygonize(unary_union([g for _, g in lines])):
        members = sorted(h for h, g in lines if g.distance(pg.exterior) < 1e-6 and g.length > 0
                         and pg.exterior.buffer(1e-6).contains(g))
        if len(members) == 4 and abs(pg.area - pg.envelope.area) < 1e-9:
            key = members[0]
            hs[key] = {"geom": pg, "kind": "FOUR_LINES " + " ".join(members)}
    d["outlines"].update(hs)
    # plot polygons and the sheet offset
    p1 = db.get(PLOT_FP)
    d["plot"] = Polygon([(x / 1000, y / 1000) for x, y in p1.get_points("xy")])
    p2 = db.get(PLOT_BP)
    off_x = min(x for x, _ in p1.get_points("xy")) - min(x for x, _ in p2.get_points("xy"))
    off_y = max(y for _, y in p1.get_points("xy")) - max(y for _, y in p2.get_points("xy"))
    d["offset_mm"] = (round(off_x, 3), round(off_y, 3))
    # pool outer shell
    pe = db.get(POOL_OUTER)
    d["pool_pts"] = [((x + off_x) / 1000, (y + off_y) / 1000, b) for x, y, *_r, b in
                     [(p[0], p[1], p[2], p[3], p[4]) for p in pe.get_points()]]
    # exterior GB edges (beams plan -> foundation frame)
    d["gb"] = {}
    for h in {h for pr in EXT_RUNS.values() for h in pr} | set(EXT_ARC) | {h for pr in EXT_SECOND_EDGE.values() for h in pr}:
        e = db.get(h)
        if e.dxftype() == "LINE":
            s, u = e.dxf.start, e.dxf.end
            d["gb"][h] = ("LINE", ((s.x + off_x) / 1000, (s.y + off_y) / 1000), ((u.x + off_x) / 1000, (u.y + off_y) / 1000))
        else:
            c = e.dxf.center
            d["gb"][h] = ("ARC", ((c.x + off_x) / 1000, (c.y + off_y) / 1000), e.dxf.radius / 1000,
                          e.dxf.start_angle, e.dxf.end_angle)
    return d


def label_of(d, h, g):
    """Footing label(s) inside the outline; else the nearest label within 1.00 m (flagged NEAREST)."""
    labs, near = [], []
    for t, p, lh in d["labels"]:
        m = re.match(r"^(?:C\d*|CN)?/?(F\d*|FN|FF)$", t)
        if not m:
            continue
        if g.buffer(0.001).contains(p):
            labs.append(m.group(1))
        else:
            near.append((g.distance(p), m.group(1), lh))
    if labs:
        return sorted(set(labs), key=lambda x: (len(x), x), reverse=True), "LABEL_INSIDE"
    near.sort()
    if near and near[0][0] <= 1.0:
        return [near[0][1]], "NEAREST_LABEL %.3f m (%s)" % (near[0][0], near[0][2])
    return [], "NO_LABEL"


def bulge_polygon(pts, n=8192):
    """Closed LWPOLYLINE with bulges -> polygon (n segments per half circle)."""
    out = []
    for i, (x, y, b) in enumerate(pts):
        x2, y2, _ = pts[(i + 1) % len(pts)]
        out.append((x, y))
        if abs(b) > 1e-12:
            th = 4 * math.atan(b)
            ch = math.hypot(x2 - x, y2 - y)
            r = ch / (2 * math.sin(abs(th) / 2))
            mx, my = (x + x2) / 2, (y + y2) / 2
            dd = math.sqrt(max(r * r - (ch / 2) ** 2, 0))
            ux, uy = (x2 - x) / ch, (y2 - y) / ch
            sg = 1 if b > 0 else -1
            cx, cy = mx - sg * uy * dd, my + sg * ux * dd
            a0 = math.atan2(y - cy, x - cx)
            k = max(int(n * abs(th) / math.pi), 8)
            for j in range(1, k):
                a = a0 + th * j / k
                out.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return Polygon(out)


def run(dxf):
    d = read(dxf)
    pits, others, checks = [], {}, []
    for h, o in sorted(d["outlines"].items()):
        g = o["geom"]
        lab, how = label_of(d, h, g)
        x0, y0, x1, y1 = g.bounds
        L, W = round(x1 - x0, 6), round(y1 - y0, 6)
        typ = "/".join(lab) if lab else None
        row = {"handle": h, "kind": o["kind"], "type": typ, "min_mm": [round(x0 * 1000, 1), round(y0 * 1000, 1)],
               "size_m": [L, W], "checked_before": h in CHECKED_BEFORE,
               "label_method": how}
        if typ in (None,) or (typ not in d["sched"] and typ not in ("F10/F",)):
            row["status"] = "NOT_A_PIT_OR_UNLABELLED"
            others[h] = row
            continue
        if typ in NOT_PITS:
            row["status"] = "OWN_ZONE: " + NOT_PITS[typ]
            others[h] = row
            continue
        sw, sh, sd, sref = d["sched"][typ]
        agree = sorted([L, W]) == sorted([round(sw, 6), round(sh, 6)])
        row.update({"schedule_m": [sw, sh, sd], "schedule_handle": sref, "size_vs_schedule": "AGREE" if agree else
                    "CONFLICT", "open_outline": o["kind"].startswith("OPEN")})
        checks.append(agree)
        pits.append((row, g))
    # the FN repeat on the beams plan sheet (80B..80E) is outside the foundation frame: not read as a pit
    plot = d["plot"]
    ps = [U.Pit(pid=r["handle"], cx=(g.bounds[0] + g.bounds[2]) / 2, cy=(g.bounds[1] + g.bounds[3]) / 2,
                L=r["size_m"][0], W=r["size_m"][1], projection=PROJ, unit="m", ref=r["type"]) for r, g in pits]
    # pool envelope (zone dug first: deeper, earlier in the dig order, R-T497-1)
    shell = bulge_polygon(d["pool_pts"])
    env = shell.buffer(POOL_LAYERS, quad_segs=4096)
    per = shell.length
    env_exact = U.convex_offset_area(shell.area, per, POOL_LAYERS)
    env_in = env.intersection(plot)
    pool = {"shell_m2": round(shell.area, 6), "shell_perimeter_m": round(per, 6),
            "envelope_m2_polygon": round(env.area, 6), "envelope_m2_exact": round(env_exact, 6),
            "envelope_in_plot_m2": round(env_in.area, 6), "envelope_beyond_plot_m2": round(env.area - env_in.area, 6),
            "back_face_on_plot_line": bool(abs(max(x for x, *_ in d["pool_pts"]) - plot.bounds[2]) < 1e-6)}
    # exact in-plot envelope: the straight back sits on the plot line, so the 3.50 back strip and both back corner
    # quarter-circles lie beyond it (Steiner by parts)
    back = max(x for x, *_ in d["pool_pts"]) - min(x for x, *_ in d["pool_pts"])  # not used for the back length
    ys = [y for x, y, _ in d["pool_pts"] if abs(x - plot.bounds[2]) < 1e-6]
    back_len = max(ys) - min(ys)
    pool["envelope_in_plot_m2_exact"] = round(shell.area + (per - back_len) * POOL_LAYERS + math.pi / 2 *
                                              POOL_LAYERS ** 2, 6)
    pool["back_length_m"] = round(back_len, 6)
    pits_zone = U.zone_plan("Z1-PITS-24", ps, plot=plot, earlier=[("Z1-POOL envelope", env_in)])
    # zone ownership of the 16 re-measured vs the 8 checked before
    p16 = [p for p, (r, g) in zip(ps, pits) if not r["checked_before"]]
    z16 = U.zone_plan("16 pits alone", p16, plot=None)
    per_pit = {}
    for (r, g), p in zip(pits, ps):
        pg = U.pit_polygon(p)
        pi = pg.intersection(plot)
        per_pit[r["handle"]] = {"type": r["type"], "neat_m2": round(pg.area, 6),
                                "beyond_plot_m2": round(pg.area - pi.area, 6),
                                "in_pool_envelope_in_plot_m2": round(pi.intersection(env_in).area, 6)}
    # convergence of the curved envelope: the pits' given-up m2 at coarse -> fine polygonisation
    conv = {}
    for q in (4, 16, 64, 256, 1024, 4096):
        e_q = shell.buffer(POOL_LAYERS, quad_segs=q).intersection(plot)
        sh_q = bulge_polygon(d["pool_pts"], n=max(q * 2, 8)).buffer(POOL_LAYERS, quad_segs=q).intersection(plot)
        conv[str(q)] = {"envelope_in_plot_m2": round(sh_q.area, 6),
                        "pits_given_up_m2": round(unary_union([U.pit_polygon(x) for x in ps]).intersection(plot)
                                                  .intersection(sh_q).area, 6)}
    # exterior GB trench strip (main exterior): own band geometry, pieces cut at the columns
    cols = unary_union(d["cols"])
    strips, pieces = [], []
    for run, (a, b) in EXT_RUNS.items():
        _, a0, a1 = d["gb"][a]
        if run in EXT_SECOND_EDGE:
            pts = [q for h in EXT_SECOND_EDGE[run] for q in d["gb"][h][1:]]
            b0 = min(pts)
            b1 = max(pts)
        else:
            _, b0, b1 = d["gb"][b]
        horiz = abs(a0[1] - a1[1]) < 1e-6
        if horiz:
            lo, hi = _extent(a0[0], a1[0], b0[0], b1[0])
            y_a, y_b = a0[1], b0[1]
            band = box(lo, min(y_a, y_b), hi, max(y_a, y_b))
            grow = box(lo, min(y_a, y_b) - PROJ, hi, max(y_a, y_b) + PROJ)
        else:
            lo, hi = _extent(a0[1], a1[1], b0[1], b1[1])
            x_a, x_b = a0[0], b0[0]
            band = box(min(x_a, x_b), lo, max(x_a, x_b), hi)
            grow = box(min(x_a, x_b) - PROJ, lo, max(x_a, x_b) + PROJ, hi)
        width = (band.bounds[3] - band.bounds[1]) if horiz else (band.bounds[2] - band.bounds[0])
        # pieces = the run axis split at every column the band touches (clear length face to face)
        cuts = []
        for c in d["cols"]:
            if c.intersection(band).area > 1e-6:
                cb = c.bounds
                cuts.append((cb[0], cb[2]) if horiz else (cb[1], cb[3]))
        cuts.sort()
        segs, cur = [], lo
        for c0, c1 in cuts:
            if c0 > cur + 1e-9:
                segs.append((cur, min(c0, hi)))
            cur = max(cur, c1)
        if cur < hi - 1e-9:
            segs.append((cur, hi))
        want = dict(EXT_PIECES_T253[run])
        for k, (s0, s1) in enumerate(segs, 1):
            Lp = round(s1 - s0, 4)
            exp = want.pop(k, None)
            pieces.append({"run": run, "piece": k, "L_m": Lp, "width_m": round(width, 4), "main_ext": exp is not None,
                           "L_t253_m": exp, "dL_m": None if exp is None else round(Lp - exp, 4),
                           "axis_mm": [round(s0 * 1000, 1), round(s1 * 1000, 1)]})
            if exp is not None:
                if horiz:
                    s = box(s0, band.bounds[1] - PROJ, s1, band.bounds[3] + PROJ)
                else:
                    s = box(band.bounds[0] - PROJ, s0, band.bounds[2] + PROJ, s1)
                strips.append(s)
        if want:
            pieces.append({"run": run, "unmatched_t253_pieces": want})
    # arc run: annulus between the two arcs over their common angular span, grown radially
    _, c1, r1, s1, e1 = d["gb"][EXT_ARC[0]]
    _, c2, r2, s2, e2 = d["gb"][EXT_ARC[1]]
    a_lo, a_hi = max(s1, s2), min(e1, e2)
    cx, cy = (c1[0] + c2[0]) / 2, (c1[1] + c2[1]) / 2
    rin, rout = min(r1, r2), max(r1, r2)

    def sector(r0, r1_, a0, a1, n=4096):
        pts = [(cx + r1_ * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
                cy + r1_ * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
        pts += [(cx + r0 * math.cos(math.radians(a1 - (a1 - a0) * i / n)),
                 cy + r0 * math.sin(math.radians(a1 - (a1 - a0) * i / n))) for i in range(n + 1)]
        return Polygon(pts)
    arc_beam = sector(rin, rout, a_lo, a_hi).difference(cols)
    arc_strip = sector(rin - PROJ, rout + PROJ, a_lo, a_hi).difference(cols)
    strips.append(arc_strip)
    pieces.append({"run": "ARC:157+158", "L_m": round(arc_beam.area / (rout - rin), 4), "width_m": round(rout - rin, 4),
                   "main_ext": True, "angles": [round(a_lo, 3), round(a_hi, 3)]})
    ext = unary_union(strips).difference(cols)
    ext_in = ext.intersection(plot)
    pits_all = unary_union([U.pit_polygon(p) for p in ps])
    f10f = [o["geom"] for h, o in d["outlines"].items() if h == "1B1B"][0]
    f10f_neat = box(f10f.bounds[0] - PROJ, f10f.bounds[1] - PROJ, f10f.bounds[2] + PROJ, f10f.bounds[3] + PROJ)
    ff = [o["geom"] for h, o in d["outlines"].items() if h == "1B2B"][0]
    own = ext.difference(env).difference(pits_all).difference(f10f_neat).difference(ff)
    trench = {"strip_total_m2": round(ext.area, 6), "strip_in_plot_m2": round(ext_in.area, 6),
              "strip_beyond_plot_m2": round(ext.area - ext_in.area, 6),
              "given_to_pool_m2": round(ext.intersection(env).area, 6),
              "given_to_pits_m2": round(ext.difference(env).intersection(pits_all).area, 6),
              "given_to_pits_in_plot_m2": round(ext_in.difference(env).intersection(pits_all).area, 6),
              "given_to_F10F_outline_m2": round(ext.difference(env).difference(pits_all).intersection(f10f_neat).area, 6),
              "given_to_FF_m2": round(ext.difference(env).difference(pits_all).difference(f10f_neat).intersection(ff).area, 6),
              "own_in_plot_m2": round(own.intersection(plot).area, 6), "own_beyond_plot_m2":
                  round(own.area - own.intersection(plot).area, 6), "pieces": pieces,
              "L_sum_main_ext_m": round(sum(p.get("L_m", 0) for p in pieces if p.get("main_ext")), 4)}
    trench["own_m3_at_blinding_0.10"] = [round(trench["own_in_plot_m2"] * 0.10, 6),
                                         round((trench["own_in_plot_m2"] + trench["own_beyond_plot_m2"]) * 0.10, 6)]
    out = {
        "schema": "T-597 B1 plan side: handles, sizes, m2 only (no client data)",
        "drawing": "Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf' sha256 " + d["sha8"],
        "sheet_offset_mm": d["offset_mm"],
        "pits": [r for r, _ in pits],
        "not_pits": list(others.values()),
        "size_vs_schedule": {"agree": sum(checks), "of": len(checks)},
        "pits_zone": {k: v for k, v in pits_zone.__dict__.items() if k != "geometry"},
        "pits_16_remeasured": {"per_pit_m2": z16.per_pit_m2, "sum_m2": z16.sum_m2, "union_m2": z16.union_m2,
                               "overlap_pairs": z16.overlap_pairs},
        "pool": pool, "ext_gb_trench": trench, "per_pit": per_pit, "envelope_convergence": conv,
    }
    return out


ENGINE = {  # candidate of record V3.0.58 (T-350 r4 / T-497 values, unchanged since; cited from merged files)
    "pits_plan_m2": 124.649555, "pits_depth_m_S01": 1.67, "pits_m3": 208.164757,
    "pool_plan_m2": 11.851051, "pool_depth_m": 1.50, "pool_m3": 17.776576,
    "trench_own_in_plot_m2": 10.692685, "trench_own_beyond_m2": 1.071981, "trench_m3": [1.069269, 1.176467]}


def b1_rows(out):
    """The B1-02 rows of the T-589 component list with their plan side restated (depth untouched)."""
    z, pool, tr = out["pits_zone"], out["pool"], out["ext_gb_trench"]
    pits_m3 = round(z["own_in_plot_m2"] * ENGINE["pits_depth_m_S01"], 6)
    return [
        {"id": "B1-02 valued excavation: Z1-PITS-24", "plan_m2": z["own_in_plot_m2"], "plan_status": "DRAWING-CONFIRMED",
         "plan_basis": "union of 24 neat pits (footing + 0.10, ST p.13), 24 / 24 sizes = schedule, in plot, less the "
                       "pool envelope (exact arc)", "engine_plan_m2": ENGINE["pits_plan_m2"],
         "plan_delta_m2": round(z["own_in_plot_m2"] - ENGINE["pits_plan_m2"], 6),
         "depth": "HELD by name: S01 ESTIMATED founding (RFI-S01, Q-21 C); 1.67 used only to state the effect",
         "m3_at_S01": pits_m3, "engine_m3": ENGINE["pits_m3"], "m3_delta_at_S01": round(pits_m3 - ENGINE["pits_m3"], 6),
         "cause": "the engine's pool envelope was a polygonised buffer (inscribed chords): its arc parts are smaller, "
                  "so the pits gave up 2.694820 instead of the exact 2.695761 m2"},
        {"id": "B1-02 valued excavation: Z1-POOL", "plan_m2": pool["envelope_in_plot_m2_exact"],
         "plan_status": "DRAWING-CONFIRMED", "plan_basis": "pool shell 7C6 (half circle r 1.75 + 3.50 x 1.75) grown "
         "0.10 (p.7 screed + membrane), back face on the plot line: A + (P - back) d + pi/2 d^2",
         "engine_plan_m2": ENGINE["pool_plan_m2"],
         "plan_delta_m2": round(pool["envelope_in_plot_m2_exact"] - ENGINE["pool_plan_m2"], 6),
         "depth": "printed -1.50 (T-183 r2): not S01", "m3": round(pool["envelope_in_plot_m2_exact"] * 1.5, 6),
         "engine_m3": ENGINE["pool_m3"]},
        {"id": "EW-T350:B1-02:Z1-TRENCH-EXT-GB-MAIN", "plan_m2": [tr["own_in_plot_m2"], tr["own_beyond_plot_m2"]],
         "plan_status": "DRAWING-CONFIRMED (geometry); main-exterior class from the T-253 ledger",
         "plan_basis": "17 pieces (15 straight + 2 more of 7E0+FD / 114 + 115 + 7DF, 1 arc) cut at the columns, strip "
                       "= beam + 0.10 each side (p.13), owned after pool / pits / F10F outline / FF (R-T497-1)",
         "engine_plan_m2": [ENGINE["trench_own_in_plot_m2"], ENGINE["trench_own_beyond_m2"]],
         "m3_at_blinding_0.10": tr["own_m3_at_blinding_0.10"], "engine_m3": ENGINE["trench_m3"],
         "depth": "0.10 blinding below EG (exterior GB bottom on N.G., T-253): printed; the beyond-plot part stays "
                  "HELD (S06 / D-14)"},
        {"id": "EW-T350:B1-02:Z1-PIT-FF", "plan_m2": None, "plan_status": "HELD (neat plan): footprint 20.70 m2 "
         "drawn (1B2B 4.60 x 4.50 = schedule FF), blinding projection not dimensioned on p.14", "depth": "HELD D-43"},
        {"id": "EW-T350:B1-02:Z1-PIT-F10F", "plan_m2": None, "plan_status": "HELD: open outline 1B1B (3.25 x 1.40 "
         "bounding, tags F10 + F), Q-31 C", "depth": "HELD Q-21 C"},
    ]


def main(argv):
    global EXTENT
    if len(argv) != 2:
        raise SystemExit(__doc__)
    EXTENT = "EITHER"
    either = run(argv[1])["ext_gb_trench"]
    EXTENT = "COMMON"
    out = run(argv[1])
    out["ext_gb_trench_either_face_extent"] = either
    out["b1_rows"] = b1_rows(out)
    od = HERE / "out"
    od.mkdir(exist_ok=True)
    (od / "T597_PLAN_SIDE.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    z = out["pits_zone"]
    print(json.dumps({k: z[k] for k in ("sum_m2", "union_m2", "overlap_m2", "in_plot_m2", "beyond_plot_m2",
                                         "given_up_m2", "own_in_plot_m2")}, indent=1))
    print(json.dumps(out["pool"], indent=1))
    print(json.dumps({k: v for k, v in out["ext_gb_trench"].items() if k != "pieces"}, indent=1))
    print(out["size_vs_schedule"], len(out["pits"]))


if __name__ == "__main__":
    main(sys.argv)
