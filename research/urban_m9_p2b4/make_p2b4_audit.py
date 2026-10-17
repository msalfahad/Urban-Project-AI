"""Phase 2B-4 - V2.5 waterproofing constructability audit: writes the generated views of the audit (diagrams, plan
tables, the junction sweep and the engine-versus-rebuild table) from the audit library in tests/m9_p2b4.

    python3 -I research/urban_m9_p2b4/make_p2b4_audit.py

Every figure here comes from the independent construction calculator (construct_reference.py) applied to the plans of
construct_cases.py, or - in ENGINE_VS_REBUILD only - from the V2.5 engine's own records. Nothing is typed by hand here.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "tests" / "m9_p2b4"))

import construct_cases as CC                                  # noqa: E402
import construct_engine as CE                                 # noqa: E402
import construct_reference as CR                              # noqa: E402

DIAG = HERE / "diagrams"
U = CR.URBAN
SWEEP_J = list(range(100, 210, 10))

C_FLOOR = ("#9ec5e8", "#6fa8dc")
C_BAND = ("#f6b26b", "#e69138")
C_DOOR = "#93c47d"
C_JOINT = "#cc0000"
C_REUSE = "#ffe599"
C_WASTE = "#e06666"
C_STOCK = "#d9d9d9"
C_CORNER = "#b45f06"
INK = "#222222"


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def m(x):
    return f"{x / 1000:.2f}"


def wrap(t, n=52):
    out, cur = [], ""
    for w in str(t).split(" "):
        if cur and len(cur) + 1 + len(w) > n:
            out.append(cur)
            cur = "   " + w
        else:
            cur = (cur + " " + w) if cur else w
    return out + ([cur] if cur else [])


def m2(x):
    return f"{x / 1e6:.2f}"


class Svg:
    def __init__(self, w, h):
        self.w, self.h, self.items = w, h, []
        self.items.append(f'<rect x="0" y="0" width="{w}" height="{h}" fill="#ffffff"/>')

    def rect(self, x, y, w, h, fill, stroke="none", sw=1, op=1.0, extra=""):
        self.items.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(w, 0):.1f}" height="{max(h, 0):.1f}" '
                          f'fill="{fill}" fill-opacity="{op}" stroke="{stroke}" stroke-width="{sw}" {extra}/>')

    def line(self, x0, y0, x1, y1, stroke=INK, sw=1, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.items.append(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" stroke="{stroke}" '
                          f'stroke-width="{sw}"{d}/>')

    def text(self, x, y, s, size=11, fill=INK, anchor="start", weight="normal", rot=None):
        tr = f' transform="rotate({rot} {x:.1f} {y:.1f})"' if rot is not None else ""
        self.items.append(f'<text x="{x:.1f}" y="{y:.1f}" font-family="Arial, Helvetica, sans-serif" '
                          f'font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}"{tr}>'
                          f'{esc(s)}</text>')

    def circle(self, x, y, r, fill, stroke=INK, sw=1):
        self.items.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}" stroke="{stroke}" '
                          f'stroke-width="{sw}"/>')

    def raw(self, s):
        self.items.append(s)

    def save(self, path):
        defs = ('<defs><pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" '
                'patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="6" stroke="#666" stroke-width="1"/>'
                '</pattern></defs>')
        path.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
                        f'viewBox="0 0 {self.w} {self.h}">{defs}' + "".join(self.items) + "</svg>\n", encoding="utf-8")


# --------------------------------------------------------------------------------------- installation plans
def _frame(poly, extra, width=640):
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    x0, y0, x1, y1 = min(xs) - extra, min(ys) - extra, max(xs) + extra, max(ys) + extra
    s = width / max(x1 - x0, y1 - y0)
    ox, oy = 70, 50
    return s, (lambda x: ox + (x - x0) * s), (lambda y: oy + (y1 - y) * s), (x1 - x0) * s, (y1 - y0) * s


def _strip_xy(along, c0, c1, a0, a1):
    return (c0, a0, c1, a1) if along == "Y" else (a0, c0, a1, c1)


def _wall_parts(room, rn, a, b):
    """The pieces of run interval [a, b] on each wall part: (edge dir, start point, end point)."""
    E = CR._edges(room["poly"])
    out = []
    for e, ta, tb, r0 in rn["parts"]:
        lo, hi = max(a, r0), min(b, r0 + tb - ta)
        if lo >= hi:
            continue
        p, q = E[e]
        (dx, dy), _ = CR._dir(p, q)
        t0, t1 = ta + lo - r0, ta + hi - r0
        out.append(((dx, dy), (p[0] + dx * t0, p[1] + dy * t0), (p[0] + dx * t1, p[1] + dy * t1)))
    return out


def _band_rects(room, rn, a, b, j, h):
    """Flange (into the room, j) and upturn folded out flat (out of the room, h) rectangles of a band interval."""
    out = []
    for (dx, dy), p0, p1 in _wall_parts(room, rn, a, b):
        nx, ny = -dy, dx                                          # into the room
        xs = sorted((p0[0], p1[0]))
        ys = sorted((p0[1], p1[1]))
        if dy == 0:
            fl = (xs[0], min(p0[1], p0[1] + ny * j), xs[1], max(p0[1], p0[1] + ny * j))
            up = (xs[0], min(p0[1], p0[1] - ny * h), xs[1], max(p0[1], p0[1] - ny * h))
        else:
            fl = (min(p0[0], p0[0] + nx * j), ys[0], max(p0[0], p0[0] + nx * j), ys[1])
            up = (min(p0[0], p0[0] - nx * h), ys[0], max(p0[0], p0[0] - nx * h), ys[1])
        out.append((fl, up, (dx, dy)))
    return out


def install_A(case, res, path):
    room = CC.ROOMS[case["room"]]
    plan = case["plan"]
    poly = room["poly"]
    j, h = plan["j"], U["h"]
    s, X, Y, W, H = _frame(poly, 420)
    svg = Svg(int(W + 140 + 400), int(H + 170))
    R = lambda r: (X(r[0]), Y(r[3]), (r[2] - r[0]) * s, (r[3] - r[1]) * s)     # noqa: E731
    lay = CR.floor_layout(poly, plan["along"], U)
    for k, st in enumerate(lay["strips"]):
        for rr in st["rects"]:
            svg.rect(*R(_strip_xy(plan["along"], *rr)), C_FLOOR[k % 2], op=0.55)
        cx = (st["c0"] + st["c1"]) / 2
        ca = (st["a0"] + st["a1"]) / 2
        px, py = (cx, ca) if plan["along"] == "Y" else (ca, cx)
        narrow = st["w"] * s < 75
        rot = (-90 if plan["along"] == "Y" else 0) if narrow else None
        svg.text(X(px) + (4 if narrow and plan["along"] == "Y" else 0), Y(py), f"S{k + 1} {m(st['w'])}",
                 11 if narrow else 12, "#0b3d6e", "middle", "bold", rot)
    # wall line and doors
    E = CR._edges(poly)
    for e, (p, q) in enumerate(E):
        svg.line(X(p[0]), Y(p[1]), X(q[0]), Y(q[1]), INK, 2.5)
    rns = CR.runs(room)
    for d in room["doors"]:
        ax, c, lo, hi = CR.door_segment(room, d)
        (dx, dy), _ = CR._dir(*E[d["edge"]])
        nx, ny = -dy, dx
        if ax == "y":
            op = (lo, min(c, c - ny * d["depth"]), hi, max(c, c - ny * d["depth"]))
            lp = (lo, min(c, c + ny * U["dl"]), hi, max(c, c + ny * U["dl"]))
            svg.line(X(lo), Y(c), X(hi), Y(c), "#ffffff", 4)
        else:
            op = (min(c, c - nx * d["depth"]), lo, max(c, c - nx * d["depth"]), hi)
            lp = (min(c, c + nx * U["dl"]), lo, max(c, c + nx * U["dl"]), hi)
            svg.line(X(c), Y(lo), X(c), Y(hi), "#ffffff", 4)
        svg.rect(*R(op), C_DOOR, "#38761d", 1, 0.9)
        svg.rect(*R(lp), C_DOOR, "#38761d", 1, 0.9)
        mx, my = (op[0] + op[2]) / 2, (op[1] + op[3]) / 2
        svg.text(X(mx), Y(my) + 4, f"{plan['doorways'][d['id']]} {d['id']}", 10, "#274e13", "middle", "bold")
    # band pieces
    for bd, rn in zip(res["band"], rns):
        for k, (pid, ln, (a, b)) in enumerate(bd["pieces"]):
            col = C_BAND[k % 2]
            rects = _band_rects(room, rn, a, b, j, h)
            for fl, up, _ in rects:
                svg.rect(*R(fl), col, "#783f04", 0.6, 0.85)
                svg.rect(*R(up), col, "#783f04", 0.6, 0.85)
            fl, up, (dx, dy) = max(rects, key=lambda t: (t[1][2] - t[1][0]) + (t[1][3] - t[1][1]))
            cx, cy = (up[0] + up[2]) / 2, (up[1] + up[3]) / 2
            svg.text(X(cx), Y(cy) + 4, pid, 10, "#5b2c00", "middle", "bold")
        for q, (a, b) in enumerate(bd["joints"]):
            for fl, up, _ in _band_rects(room, rn, a, b, j, h):
                svg.rect(*R(fl), C_JOINT, op=0.75)
                svg.rect(*R(up), C_JOINT, op=0.75)
    # floor-seam ends, stacked joints
    lay_c = CR._axes(plan["along"])[0]
    for se in res["seam_ends"]:
        if se["kind"] != "WALL":
            u, v = CR._seam_zones(lay)[se["seam"] - 1]
            a, b = E[se["edge"]]
            mid = (u + v) / 2
            pt = (mid, a[1]) if lay_c == 0 else (a[0], mid)
            svg.circle(X(pt[0]), Y(pt[1]), 4, "#000000", "#ffffff", 1)
            continue
        rn = rns[se["where"]]
        a, b = se["r"]
        pt = CR.run_point(poly, rn, (a + b) / 2)
        stacked = any(min(jb, b) - max(ja, a) > 0 for ja, jb in res["band"][se["where"]]["joints"])
        svg.circle(X(pt[0]), Y(pt[1]), 5 if stacked else 3, C_JOINT if stacked else "#000000", INK, 1)
    # corners
    for c in res["corners"]:
        v = poly[c["vertex"]]
        cx, cy = X(v[0]), Y(v[1])
        if c["kind"] == CR.INTERNAL:
            svg.circle(cx, cy, 6, "none", C_CORNER, 2)
        else:
            svg.raw(f'<polygon points="{cx},{cy - 8} {cx + 8},{cy} {cx},{cy + 8} {cx - 8},{cy}" fill="none" '
                    f'stroke="{C_CORNER}" stroke-width="2"/>')
        if c["piece_edge_at_corner"]:
            svg.text(cx + 9, cy - 9, "piece edge at corner", 10, C_JOINT, "start", "bold")
    # jambs
    for rn in rns:
        for r in (0, rn["length"]):
            pt = CR.run_point(poly, rn, r)
            x, y = X(pt[0]), Y(pt[1])
            svg.line(x - 6, y - 6, x + 6, y + 6, C_JOINT, 2.5)
            svg.line(x - 6, y + 6, x + 6, y - 6, C_JOINT, 2.5)
    # pipes
    for p in res["pipes"]:
        half = p["clear_mm"]
        svg.rect(X(p["at"][0] - half), Y(p["at"][1] + half), 2 * half * s, 2 * half * s, "none", "#674ea7", 1.2,
                 1.0, 'stroke-dasharray="4 3"')
        svg.circle(X(p["at"][0]), Y(p["at"][1]), 5, "#8e7cc3", "#351c75", 1.5)
        svg.text(X(p["at"][0]) - 8, Y(p["at"][1] + half) - 4, f"pipe sleeve: square <= {m(2 * half)} m clear",
                 10, "#351c75", "end")
    # legend and caption
    lx = int(W + 110)
    q = CR.summary(res)
    lines = [(C_FLOOR[1], "floor strip (darker where strips lap)"), (C_BAND[1], "band piece: flange on the floor"),
             (C_BAND[0], " + upturn folded out flat (outside the wall line)"), (C_JOINT, "band joint (end lap)"),
             (C_DOOR, "doorway piece: opening + lap onto the floor")]
    y = 60
    svg.text(lx, y - 20, case["id"], 14, INK, "start", "bold")
    for col, t in lines:
        svg.rect(lx, y - 10, 14, 12, col, INK, 0.5)
        svg.text(lx + 20, y, t, 11)
        y += 20
    marks = ["o  internal corner (treatment withheld)", "<>  external corner (treatment withheld)",
             "x  jamb: doorway piece meets the band end, no lap", ".  floor-seam end under the flange",
             "red dot: a band joint on a seam end (4 layers)"]
    if res["corners_external"]:
        marks.append("external corner: the folded-out upturns overlap in the drawing only")
    for t in marks:
        svg.text(lx, y, t, 11, C_CORNER if "corner" in t else INK)
        y += 18
    y += 8
    facts = [f"junction: {case['junction']}", f"reading: {case['reading']}",
             f"consumed {q['consumed_m2']:.2f} m2, installed {q['installed_m2']:.2f}",
             f"rolls {q['rolls']}, seams {q['seams']} ({q['floor_seams']} floor + {q['band_joints']} band)",
             f"joints: >= {q['min_joint_corner_m']} m from corners," if q["min_joint_corner_m"] is not None
             else "joints: none",
             f"   >= {q['min_joint_seam_end_m']} m from seam ends" if q["min_joint_seam_end_m"] is not None else "",
             f"true waste {q['true_waste_m2']:.2f}, reusable {q['reusable_m2']:.2f}, stock {q['stock_m2']:.2f}"]
    for t in facts:
        for ln in (wrap(t) if t else []):
            svg.text(lx, y, ln, 11)
            y += 17
    svg.text(70, H + 120, f"{CC.ROOMS[case['room']]['title']} - {case['title']}", 13, INK, "start", "bold")
    svg.text(70, H + 140, "plan view; the 0.20 m wall upturn is drawn folded out flat beyond the wall line; band "
             "positions are run positions from the first jamb", 11)
    svg.save(path)


def install_B(case, res, path):
    room = CC.ROOMS[case["room"]]
    plan = case["plan"]
    dv = CR.developed(room, U)
    s, X, Y, W, H = _frame(dv["rect"], 100)
    svg = Svg(int(W + 140 + 400), int(H + 170))
    R = lambda r: (X(r[0]), Y(r[3]), (r[2] - r[0]) * s, (r[3] - r[1]) * s)     # noqa: E731
    lay = CR.floor_layout(dv["rect"], plan["along"], U)
    for k, st in enumerate(lay["strips"]):
        svg.rect(*R(_strip_xy(plan["along"], st["c0"], st["c1"], st["a0"], st["a1"])), C_FLOOR[k % 2], op=0.55)
        cx = (st["c0"] + st["c1"]) / 2
        ca = (st["a0"] + st["a1"]) / 2
        px, py = (cx, ca) if plan["along"] == "Y" else (ca, cx)
        svg.text(X(px), Y(py), f"S{k + 1} {m(st['w'])} x {m(st['len'])}", 12, "#0b3d6e", "middle", "bold")
    for c in dv["corners"]:
        svg.rect(*R(c), "url(#hatch)", C_CORNER, 1.5)
    x0, y0, x1, y1 = dv["floor"]
    for a, b in ((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0)):
        svg.line(X(a[0]), Y(a[1]), X(b[0]), Y(b[1]), INK, 1.5, "6 4")
    E = CR._edges(room["poly"])
    for d in room["doors"]:
        ax, c, lo, hi = CR.door_segment(room, d)
        (dx, dy), _ = CR._dir(*E[d["edge"]])
        nx, ny = -dy, dx
        if ax == "y":
            op = (lo, min(c, c - ny * d["depth"]), hi, max(c, c - ny * d["depth"]))
            slits = [(X(t), Y(c), X(t), Y(c - ny * d["depth"])) for t in (lo, hi)]
        else:
            op = (min(c, c - nx * d["depth"]), lo, max(c, c - nx * d["depth"]), hi)
            slits = [(X(c), Y(t), X(c - nx * d["depth"]), Y(t)) for t in (lo, hi)]
        svg.rect(*R(op), "none", "#38761d", 2)
        for sl in slits:
            svg.line(*sl, C_JOINT, 4)
        svg.text(X((op[0] + op[2]) / 2), Y((op[1] + op[3]) / 2) + 4, f"{d['id']} flap", 10, "#274e13", "middle", "bold")
    for p in res["pipes"]:
        half = p["clear_mm"]
        svg.rect(X(p["at"][0] - half), Y(p["at"][1] + half), 2 * half * s, 2 * half * s, "none", "#674ea7", 1.2,
                 1.0, 'stroke-dasharray="4 3"')
        svg.circle(X(p["at"][0]), Y(p["at"][1]), 5, "#8e7cc3", "#351c75", 1.5)
    lx = int(W + 110)
    q = CR.summary(res)
    y = 60
    svg.text(lx, y - 20, case["id"], 14, INK, "start", "bold")
    for col, t in ((C_FLOOR[1], "floor strip, folded up the walls"),):
        svg.rect(lx, y - 10, 14, 12, col, INK, 0.5)
        svg.text(lx + 20, y, t, 11)
        y += 20
    for t in ("dashed: fold line (floor-to-wall junction, no lap)", "hatched: corner square - excess sheet,",
              "   folded into the corner or cut out (withheld)", "red: slit at a door jamb (detail withheld)",
              "green outline: doorway floor, sheet laid flat"):
        svg.text(lx, y, t, 11, C_CORNER if "corner" in t else INK)
        y += 18
    y += 8
    for t in (f"junction: {case['junction']}", f"consumed {q['consumed_m2']:.2f} m2, installed {q['installed_m2']:.2f}",
              f"rolls {q['rolls']}, seams {q['seams']}, corner squares {q['corner_excess_m2']:.2f} m2",
              f"reusable {q['reusable_m2']:.2f}, true waste {q['true_waste_m2']:.2f}, stock {q['stock_m2']:.2f}",
              f"seams through a doorway flap: {q['seam_crossings_doorway']}"):
        for ln in wrap(t):
            svg.text(lx, y, ln, 11)
            y += 17
    svg.text(70, H + 120, f"{room['title']} - {case['title']}", 13, INK, "start", "bold")
    svg.text(70, H + 140, "developed surface: floor + every upturn folded out flat + doorway floors", 11)
    svg.save(path)


# ------------------------------------------------------------------------------------------- cutting plans
def cutting(case, res, path):
    plan = case["plan"]
    sx, sy = 0.085, 0.15
    rows = len(plan["rolls"])
    svg = Svg(1060, 90 + rows * 250)
    rip, cross = plan.get("rip", {}), plan.get("cross", {})
    info = {r["id"]: r for r in res["pieces"]}
    off = {o["id"]: o for o in res["offcuts"]}
    room = CC.ROOMS[case["room"]]
    lay = CR.floor_layout(CR.developed(room, U)["rect"] if plan["method"] == "B" else room["poly"], plan["along"], U)
    floor_ids = [p for ent in plan["floor"] for p in ([ent] if isinstance(ent, str) else ent)]
    strip_of = {}
    for k, ent in enumerate(plan["floor"]):
        for p in ([ent] if isinstance(ent, str) else ent):
            strip_of[p] = lay["strips"][k]

    def leaf(nid, x, y, w, h):
        to = info.get(nid, {}).get("to", "")
        if nid in off:
            col = C_WASTE if off[nid]["state"] == "TRUE_WASTE" else C_REUSE
            svg.rect(x, y, w, h, col, INK, 0.6)
            if off[nid]["state"] == "TRUE_WASTE":
                svg.rect(x, y, w, h, "url(#hatch)", "none")
        elif nid in floor_ids:
            svg.rect(x, y, w, h, C_FLOOR[1], INK, 0.6, 0.8)
        elif to.startswith("doorway"):
            svg.rect(x, y, w, h, C_DOOR, INK, 0.6)
        else:
            svg.rect(x, y, w, h, C_BAND[1], INK, 0.6, 0.85)
        nd = info.get(nid)
        lbl = f"{nid} {m(nd['w'])}x{m(nd['l'])}" if nd else nid
        if w > 34 and h > 11:
            svg.text(x + 3, y + min(h - 3, 12), lbl, 10 if h > 13 else 8)
        if w > 34 and h > 26:
            svg.text(x + 3, y + 24, to.replace("floor strip", "strip").replace("cross ", "")[:int(w / 5.2)], 9, "#333")

    def draw(nid, x, y, w, h):
        if nid in rip:
            yy = y
            parts = rip[nid] + ([(nid + "~w", None)] if nid + "~w" in info else [])
            for pid, pw in parts:
                ph = (pw if pw is not None else info[pid]["w"]) * sy
                draw(pid, x, yy, w, ph)
                yy += ph
        elif nid in cross:
            xx = x
            parts = cross[nid] + ([(nid + "~l", None)] if nid + "~l" in info else [])
            for pid, pl in parts:
                pw = (pl if pl is not None else info[pid]["l"]) * sx
                draw(pid, xx, y, pw, h)
                xx += pw
        else:
            leaf(nid, x, y, w, h)
        if nid in strip_of and plan["method"] == "A":
            st = strip_of[nid]
            for k, o in enumerate(st["outside"]):
                oid = f"{nid}.o{k + 1}"
                ox = x + (o[2] - st["a0"]) * sx
                oy = y + (o[0] - st["c0"]) * sy
                draw(oid, ox, oy, (o[3] - o[2]) * sx, (o[1] - o[0]) * sy)

    for k, roll in enumerate(plan["rolls"]):
        y0 = 70 + k * 250
        svg.text(20, y0 - 12, f"roll {k + 1}  (1.00 x 10.00 m; width drawn at {sy / sx:.1f} x the length scale)",
                 12, INK, "start", "bold")
        svg.rect(40, y0, 10000 * sx, 1000 * sy, "#ffffff", INK, 1)
        at = 0
        for cid, ln in roll:
            draw(cid, 40 + at * sx, y0, ln * sx, 1000 * sy)
            svg.text(40 + at * sx + 2, y0 + 1000 * sy + 14, f"{cid} {m(at)}-{m(at + ln)}", 10)
            at += ln
        if at < 10000:
            svg.rect(40 + at * sx, y0, (10000 - at) * sx, 1000 * sy, C_STOCK, INK, 0.6)
            svg.text(40 + at * sx + 3, y0 + 14, "stock", 10)
            svg.text(40 + at * sx + 3, y0 + 28, f"{m(10000 - at)} m", 10)
    ly = 70 + rows * 250 - 60
    for i, (col, t) in enumerate(((C_FLOOR[1], "floor"), (C_BAND[1], "band piece"), (C_DOOR, "doorway piece"),
                                  (C_REUSE, "reusable offcut (N-7)"), (C_WASTE, "true waste"),
                                  (C_STOCK, "roll stock"))):
        svg.rect(40 + i * 165, ly, 14, 12, col, INK, 0.5)
        svg.text(60 + i * 165, ly + 10, t, 11)
    q = CR.summary(res)
    svg.text(40, ly + 34, f"{case['id']}: consumed {q['consumed_m2']:.2f} m2 = installed {q['installed_m2']:.2f} + "
             f"reusable {q['reusable_m2']:.2f} + true waste {q['true_waste_m2']:.2f}; stock {q['stock_m2']:.2f} m2; "
             f"{q['rolls']} rolls", 12, INK, "start", "bold")
    svg.save(path)


def section(path):
    svg = Svg(900, 360)
    for k, (title, folded) in enumerate((("A  SEPARATE_UPSTAND: floor sheet + band strip folded at the junction",
                                          False),
                                         ("B  CONTINUOUS_FOLD: the floor sheet turned up the wall", True))):
        ox = 40 + k * 440
        svg.text(ox, 30, title, 12, INK, "start", "bold")
        svg.rect(ox + 300, 60, 60, 230, "#cccccc", INK, 1)          # wall
        svg.rect(ox, 250, 300, 40, "#cccccc", INK, 1)               # floor slab
        svg.text(ox + 330, 300 + 14, "wall", 11, INK, "middle")
        svg.text(ox + 150, 300 + 14, "floor", 11, INK, "middle")
        if not folded:
            svg.rect(ox, 244, 300, 6, C_FLOOR[1], INK, 0.8)
            svg.rect(ox + 294, 170, 6, 80, C_BAND[1], INK, 0.8)
            svg.rect(ox + 200, 238, 100, 6, C_BAND[1], INK, 0.8)
            svg.text(ox + 250, 230, "flange j on the floor sheet", 10, INK, "middle")
            svg.text(ox + 290, 165, "h = 0.20", 10, INK, "end")
            svg.text(ox + 10, 236, "floor sheet stops at the wall", 10)
            svg.text(ox, 340, "junction lap = j: a product value (V2.5 uses 0.10, the UP-WP-002 joint lap); "
                     "a fillet or", 10)
            svg.text(ox, 354, "reinforcing strip, if the system needs one, is not included", 10)
        else:
            svg.rect(ox, 244, 300, 6, C_FLOOR[1], INK, 0.8)
            svg.rect(ox + 294, 170, 6, 80, C_FLOOR[1], INK, 0.8)
            svg.text(ox + 290, 165, "h = 0.20", 10, INK, "end")
            svg.text(ox + 10, 236, "one sheet, folded at the junction", 10)
            svg.text(ox, 340, "no junction lap; needs a sheet that may be folded 90 degrees, and a", 10)
            svg.text(ox, 354, "corner detail for the excess at every internal corner", 10)
    svg.save(path)


# ------------------------------------------------------------------------------------------------- tables
def plan_tables(results):
    out = ["# Plan tables (generated)", "",
           "Every plan of the audit as rebuilt by the construction calculator (`tests/m9_p2b4/construct_reference.py`):"
           " pieces, laps by type, junctions, material balance. Generated by `make_p2b4_audit.py`; nothing typed "
           "by hand.", ""]
    for case, res in results:
        q = CR.summary(res)
        out += [f"## {case['id']} - {case['title']}", "",
                f"Room {case['room']}; junction: {case['junction']}; reading: {case['reading']}.", "",
                "| Piece | Size (m) | Roll | Cut from | Goes to |", "|---|---|---|---|---|"]
        for r in res["pieces"]:
            out.append(f"| {r['id']} | {m(r['w'])} x {m(r['l'])} | {r['roll']} | {r['from'] or 'roll'} | {r['to']} |")
        out += ["", "| Quantity | m2 / count |", "|---|---|"]
        if res["method"] == "A":
            lp = res["laps"]
            out += [f"| side laps (floor strips) | {m2(lp['side'])} |", f"| floor end laps | {m2(lp['floor_end'])} |",
                    f"| floor-to-wall junction: flange {m(res['j'])} x {m(res['floor_wall_junction']['length_mm'])} m "
                    f"| {m2(lp['junction_flange'])} |",
                    f"| band end laps ({res['band_joints']} joints) | {m2(lp['band_end'])} |",
                    f"| doorway pieces onto the floor | {m2(lp['doorway'])} |",
                    f"| internal-corner flange pleats ({res['corners_internal']}) / external-corner flange gaps "
                    f"({res['corners_external']}) | {m2(res['floor_wall_junction']['pleat_area'])} / "
                    f"{m2(res['floor_wall_junction']['gap_area'])} |"]
        else:
            out += [f"| side + end laps | {m2(res['laps']['side_and_end'])} |",
                    f"| floor end laps (splices) | {res['floor_end_laps']} |",
                    f"| floor-to-wall junction | continuous fold, {m(res['floor_wall_junction']['fold_length_mm'])} m, "
                    f"no lap |", f"| corner squares (excess sheet) | {m2(res['corner_excess'])} |",
                    f"| jamb slits | {res['jamb_slits']} |"]
        out += [f"| proven subtotal (surfaces) | {q['proven_subtotal_m2']:.2f} |",
                f"| installed | {q['installed_m2']:.2f} |", f"| consumed (cut from rolls) | {q['consumed_m2']:.2f} |",
                f"| reusable offcuts (subject to N-7) | {q['reusable_m2']:.2f} |",
                f"| true waste | {q['true_waste_m2']:.2f} |", f"| roll stock (untouched) | {q['stock_m2']:.2f} |",
                f"| rolls / seams | {q['rolls']} / {q['seams']} |", ""]
        if res["method"] == "A":
            out += ["| Run | Pieces (run positions, m) | Joints (m) | Joint to corner (m) | Joint to seam end (m) | "
                    "Best order of these pieces |", "|---|---|---|---|---|---|"]
            for b in res["band"]:
                pcs = ", ".join(f"{p} {m(a)}-{m(bb)}" for p, _, (a, bb) in b["pieces"])
                js = ", ".join(f"{m(a)}-{m(bb)}" for a, bb in b["joints"]) or "-"
                best = b["best"]
                bo = (f"{' / '.join(m(x) for x in best['order'])} from {'the far' if best['reversed'] else 'the first'} "
                      f"jamb: {m(best['corner_mm']) if best['corner_mm'] is not None else '-'} / "
                      f"{m(best['seam_end_mm']) if best['seam_end_mm'] is not None else '-'}")
                out.append(f"| {b['run']} ({b['from']} -> {b['to']}, {m(b['length'])} m) | {pcs} | {js} | "
                           f"{', '.join(m(x) for x in b['joint_corner_mm']) or '-'} | "
                           f"{', '.join(m(x) for x in b['joint_seam_end_mm']) or '-'} | {bo} |")
            out += ["", "| Corner | Run position (m) | Kind | Continuous in | Piece edge on the corner |",
                    "|---|---|---|---|---|"]
            for c in res["corners"]:
                out.append(f"| vertex {c['vertex']} | {m(c['r'])} (run {c['run']}) | {c['kind']} | "
                           f"{', '.join(c['continuous_in']) or '-'} | {', '.join(c['piece_edge_at_corner']) or '-'} |")
            tp = res["t_points"]
            out += ["", f"Jambs: {len(res['jambs'])} open butt joints (doorway piece to band end). Multi-layer points: "
                    f"{tp['flange_over_seam_end']} floor-seam ends under the flange, {tp['doorway_lap_over_seam_end']}"
                    f" under a doorway lap, {tp['band_joint_over_seam_end']} band joints on a seam end."]
        else:
            n_d = sum(1 for c in res["seam_crossings"] if c["kind"] == "DOORWAY_FLAP")
            out += [f"Seam crossings of the fold lines: {len(res['seam_crossings'])} ({n_d} through a doorway flap)."]
        for p in res["pipes"]:
            out += ["", f"Pipe {p['id']} at ({m(p['at'][0])}, {m(p['at'][1])}): nearest {p['nearest']} "
                    f"{m(p['clear_mm'])} m; clearances {', '.join(f'{k} {m(v)}' for k, v in p['clearances_mm'].items())};"
                    f" a centred square collar up to {m(p['max_centred_square_patch_mm'])} m stays clear of them."]
        out += [""]
    (HERE / "PLAN_TABLES.md").write_text("\n".join(out) + "\n", encoding="utf-8")


def sweep_tables():
    rows = CR.sweep(CC.ROOM_B, U, SWEEP_J)
    out = ["# Junction-flange sweep, the 3 x 4 m bathroom (generated)", "",
           "Method A (separate upstand) with the flange on the floor j as a parameter. The values of j are "
           "sensitivity points, not standards: the membrane system's data sheet fixes j. Per direction: the "
           "least-membrane plan and the fewest-joints plan (rolls / m2 consumed / seams). "
           "**V25** = what V2.5 does (least membrane inside a direction, directions by rolls -> seams -> membrane); "
           "**RULE** = UP-WP-LAY-001 applied to every plan (rolls -> seams -> membrane). Hand-verified at j = 0.10, "
           "0.11, 0.15, 0.16 (construct_cases.SWEEP_HAND); the other rows are calculator output.", "",
           "| j (m) | Y least membrane | Y fewest joints | X least membrane | X fewest joints | V25 selects | "
           "RULE selects |", "|---|---|---|---|---|---|---|"]
    csv_rows = [["j_m", "reading", "direction", "rolls", "consumed_m2", "seams"]]
    for r in rows:
        bd = r["by_direction"]
        f = lambda v: f"{v[0]} / {v[1]:.2f} / {v[2]}"          # noqa: E731
        out.append(f"| {r['j_mm'] / 1000:.2f} | {f(bd[('Y', CR.LEAST_MEMBRANE)])} | {f(bd[('Y', CR.FEWEST_JOINTS)])} | "
                   f"{f(bd[('X', CR.LEAST_MEMBRANE)])} | {f(bd[('X', CR.FEWEST_JOINTS)])} | "
                   f"{r['V25'][0]}: {r['V25'][1]} rolls, {r['V25'][2]:.2f} m2, {r['V25'][3]} seams | "
                   f"{r['RULE'][0]}: {r['RULE'][1]} rolls, {r['RULE'][2]:.2f} m2, {r['RULE'][3]} seams |")
        for name in ("V25", "RULE"):
            csv_rows.append([f"{r['j_mm'] / 1000:.2f}", name, r[name][0], r[name][1], f"{r[name][2]:.2f}", r[name][3]])
    out += ["", "Continuous fold-up (method B) for comparison: see WPB-B in PLAN_TABLES.md (no flange, no band)."]
    (HERE / "JUNCTION_SWEEP.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    with open(HERE / "JUNCTION_SWEEP.csv", "w", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerows(csv_rows)
    return rows


def engine_table():
    out = ["# V2.5 engine versus the independent rebuild (generated)", "",
           "The engine's own records for the three audited rooms against the as-planned rebuild (WPB-A1, WPE-A1, "
           "WPD-A1). PASS = equal to 0.001.", "",
           "| Room | Quantity | V2.5 engine | Rebuild | Result |", "|---|---|---|---|---|"]
    for rid, case in (("WP-B", CC.WPB_A1), ("WP-E", CC.WPE_A1), ("WP-D", CC.WPD_A1)):
        eng = CE.engine_record(rid)
        res = CR.verify(CC.ROOMS[rid], U, case["plan"])
        q = CR.summary(res)
        cuts = sorted(ln for roll in case["plan"]["rolls"] for _, ln in roll)
        rows = [("direction", eng["direction"], "ALONG_" + case["plan"]["along"]),
                ("cuts from the rolls (m)", " ".join(m(x) for x in sorted(x for r in eng["rolls"] for x, _ in r)),
                 " ".join(m(x) for x in cuts)),
                ("band pieces (m)", " ".join(m(x) for x in sorted(eng["band_pieces_mm"])),
                 " ".join(m(x) for x in sorted(ln for b in res["band"] for _, ln, _ in b["pieces"]))),
                ("consumed m2", f"{eng['consumed_m2']:.2f}", f"{q['consumed_m2']:.2f}"),
                ("installed (B) m2", f"{eng['B_m2']:.2f}", f"{q['installed_m2']:.2f}"),
                ("laps m2", f"{eng['laps_m2']:.2f}", f"{q['laps_total_m2']:.2f}"),
                ("cutting waste m2 (engine) = true waste + reusable (rebuild)", f"{eng['waste_m2']:.2f}",
                 f"{q['true_waste_m2'] + q['reusable_m2']:.2f}"),
                ("rolls", str(eng["rolls_n"]), str(q["rolls"])),
                ("floor-to-wall lap m", f"{eng['junction_lap_m']:.2f} (UP-WP-002 joint lap)",
                 f"{case['plan']['j'] / 1000:.2f} (a parameter: product value)")]
        for name, a, b in rows:
            if "lap m" in name:
                ok = "same value - but see F-01"
            else:
                ok = "PASS" if a == b else "FAIL"
            out.append(f"| {rid} | {name} | {a} | {b} | {ok} |")
        out.append(f"| {rid} | open details listed by V2.5 | {'; '.join(eng['not_included'])} | + floor-to-wall "
                   f"junction, joint placement, jamb junctions | F-01, F-03, F-04 |")
    (HERE / "ENGINE_VS_REBUILD.md").write_text("\n".join(out) + "\n", encoding="utf-8")


def main():
    DIAG.mkdir(exist_ok=True)
    results = []
    for case in CC.PLANS:
        res = CR.verify(CC.ROOMS[case["room"]], U, case["plan"])
        results.append((case, res))
        stem = case["id"]
        (install_A if res["method"] == "A" else install_B)(case, res, DIAG / f"{stem}_install.svg")
        cutting(case, res, DIAG / f"{stem}_cutting.svg")
    section(DIAG / "JUNCTION_SECTIONS.svg")
    plan_tables(results)
    sweep_tables()
    engine_table()
    print("written:", len(list(DIAG.iterdir())), "diagrams; PLAN_TABLES.md, JUNCTION_SWEEP.md/.csv, ENGINE_VS_REBUILD.md")


if __name__ == "__main__":
    main()
