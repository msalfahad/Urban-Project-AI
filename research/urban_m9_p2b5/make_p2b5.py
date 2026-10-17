"""Phase 2B-5 - ARCH_TAKEOFF_V2.6 waterproofing installation layer: writes the generated views of the ten worked
examples from the engine's own V2.6 output and the independent reference calculator.

    python3 -I research/urban_m9_p2b5/make_p2b5.py

    WORKED_EXAMPLES.md        the verification chain of every example: rule -> drawing -> interpretation -> formula ->
                              expected (hand) -> engine -> difference -> PASS / FAIL -> BOQ impact
    VERIFICATION_CHAIN.csv    the same, one row per checked quantity
    JUNCTION_ALTERNATIVES.md  the floor-to-wall junction alternatives the engine reports, each rebuilt by the reference
    diagrams/IX-nn_install.svg   the installation plan the engine plans: floor strips, laps, band pieces on their runs,
                                 joints, corners, seam ends, jambs, drains / pipes
    diagrams/IX-nn_cutting.svg   the cutting plan: every roll, cut, rip and cross-cut, pieces and offcut classes

Every figure is the engine's (tests/m9_p2b5/install_engine.py) or the reference's (install_reference.py); the expected
values are the literals of install_cases.py. Nothing is typed here.
"""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT / "tests" / "m9_p2b5"), str(ROOT / "tests" / "m9_p2b4"), str(ROOT)]

import install_cases as IC                                    # noqa: E402
import install_engine as IE                                   # noqa: E402
import install_reference as IR                                # noqa: E402

DIAG = HERE / "diagrams"
TOL = 0.0005
C_FLOOR = ("#9ec5e8", "#6fa8dc")
C_BAND = ("#f6b26b", "#e69138")
C_DOOR = "#6aa84f"
C_JOINT = "#cc0000"
C_REUSE = "#ffe599"
C_WASTE = "#e06666"
C_STOCK = "#eeeeee"
C_SEAM = "#3d85c6"
INK = "#222222"


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def same(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) <= TOL
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return all(same(v, b.get(k)) for k, v in a.items())
    return a == b


def fmt(v):
    if isinstance(v, float):
        return f"{v:g}"
    if isinstance(v, dict):
        return "; ".join(f"{k} {fmt(x)}" for k, x in v.items())
    if isinstance(v, list):
        return "[" + ", ".join(fmt(x) for x in v) + "]"
    return str(v)


def diff(e, g):
    if isinstance(e, (int, float)) and not isinstance(e, bool) and isinstance(g, (int, float)) and \
            not isinstance(g, bool):
        return f"{g - e:+.4f}".rstrip("0").rstrip(".") if abs(g - e) > 1e-12 else "0"
    return "0" if same(e, g) else "differs"


# --------------------------------------------------------------------------------------------- installation plan
def _to_xy(f, a, c):
    """a strip-frame point back to drawing metres (theta 0 for every example)."""
    return (c, a) if f["direction"] == "ALONG_Y" else (a, c)


def _box(room):
    xs = [p[0] for p in room["poly"]]
    ys = [p[1] for p in room["poly"]]
    return min(xs) / 1000, min(ys) / 1000, max(xs) / 1000, max(ys) / 1000


def _along(parts, s0, s1, off=0.0, hole=False):
    """the polyline of a run between run positions s0 and s1 (metres), offset off into the room."""
    pts = []
    for p in parts:
        r0, r1 = p["from_m"], p["to_m"]
        lo, hi = max(s0, r0), min(s1, r1)
        if hi - lo <= 1e-9:
            continue
        (ax, ay), (bx, by) = p["a"], p["b"]
        ln = r1 - r0
        ux, uy = (bx - ax) / ln, (by - ay) / ln
        nx, ny = (-uy, ux) if not hole else (uy, -ux)
        t0, t1 = (lo - r0) / ln, (hi - r0) / ln
        q0 = (ax + (bx - ax) * t0 + nx * off, ay + (by - ay) * t0 + ny * off)
        q1 = (ax + (bx - ax) * t1 + nx * off, ay + (by - ay) * t1 + ny * off)
        if not pts or math.dist(pts[-1], q0) > 1e-9:
            pts.append(q0)
        pts.append(q1)
    return pts


def _wrap(t, n=110):
    out, cur = [], ""
    for w in str(t).split(" "):
        if cur and len(cur) + 1 + len(w) > n:
            out.append(cur)
            cur = "    " + w
        else:
            cur = (cur + " " + w) if cur else w
    return out + ([cur] if cur else [])


def install_svg(ex, a, path):
    room = ex["room"]
    x0, y0, x1, y1 = _box(room)
    sc = min(560 / max(x1 - x0, 1e-9), 420 / max(y1 - y0, 1e-9))
    pad, W = 60, 760
    H = int((y1 - y0) * sc + 2 * pad + 260)

    def P(x, y):
        return (pad + (x - x0) * sc, pad + (y1 - y) * sc)
    v = a["v26"]
    inst, pp = v["installation"], v["piece_plan"]
    floor = IE.WI.floor_pieces(a["layout"]["layout"]["trace"])
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="Arial" font-size="11">',
           f'<rect width="{W}" height="{H}" fill="white"/>',
           f'<text x="{pad}" y="24" font-size="14" font-weight="bold">{esc(ex["id"])} {esc(ex["title"])}</text>',
           f'<text x="{pad}" y="40" fill="#555">ARCH_TAKEOFF_V2.6 installation plan as the engine planned it (the '
           f'upturn band drawn on the floor beside its wall)</text>']
    for k, f in enumerate(floor):                                         # floor strips
        p0 = P(*_to_xy(f, f["a0"], f["c0"]))
        p1 = P(*_to_xy(f, f["a1"], f["c1"]))
        out.append(f'<rect x="{min(p0[0], p1[0]):.1f}" y="{min(p0[1], p1[1]):.1f}" width="{abs(p1[0] - p0[0]):.1f}" '
                   f'height="{abs(p1[1] - p0[1]):.1f}" fill="{C_FLOOR[k % 2]}" fill-opacity="0.45" stroke="#3d6e9e" '
                   f'stroke-width="0.6"/>')
        cx, cy = P(*_to_xy(f, f["a0"] + 0.25 * (f["a1"] - f["a0"]), (f["c0"] + f["c1"]) / 2))
        fits = f["direction"] == "ALONG_X" or f["w"] * sc >= 80          # a narrow upright strip: its id only
        lab = f'{f["id"]} {f["w"]:.2f}x{f["len"]:.2f}' if fits else f["id"]
        out.append(f'<text x="{cx:.1f}" y="{cy:.1f}" text-anchor="middle" fill="#1c3d5a">{esc(lab)}</text>')
    for z in inst["floor_seams"]:                                         # lap zones
        a0, c0, a1, c1 = z["rect_frame_m"]
        f = floor[0]
        p0, p1 = P(*_to_xy(f, a0, c0)), P(*_to_xy(f, a1, c1))
        out.append(f'<rect x="{min(p0[0], p1[0]):.1f}" y="{min(p0[1], p1[1]):.1f}" width="{abs(p1[0] - p0[0]):.1f}" '
                   f'height="{abs(p1[1] - p0[1]):.1f}" fill="{C_SEAM}" fill-opacity="0.35"/>')
    rings = [room["poly"]] + list(room.get("holes", ()))
    for ring in rings:
        pts = " ".join(f"{P(x / 1000, y / 1000)[0]:.1f},{P(x / 1000, y / 1000)[1]:.1f}" for x, y in ring)
        out.append(f'<polygon points="{pts}" fill="none" stroke="{INK}" stroke-width="1.6"/>')
    for d in room.get("doors", ()) + room.get("breaks", ()):              # doors and open edges
        e = d["edge"]
        A, B = room["poly"][e], room["poly"][(e + 1) % len(room["poly"])]
        ln = math.dist(A, B)
        q0 = (A[0] + (B[0] - A[0]) * d["t0"] / ln, A[1] + (B[1] - A[1]) * d["t0"] / ln)
        q1 = (A[0] + (B[0] - A[0]) * d["t1"] / ln, A[1] + (B[1] - A[1]) * d["t1"] / ln)
        s0, s1 = P(q0[0] / 1000, q0[1] / 1000), P(q1[0] / 1000, q1[1] / 1000)
        door = d in room.get("doors", ())
        out.append(f'<line x1="{s0[0]:.1f}" y1="{s0[1]:.1f}" x2="{s1[0]:.1f}" y2="{s1[1]:.1f}" stroke="'
                   f'{C_DOOR if door else "#999"}" stroke-width="5" stroke-dasharray="{"" if door else "6,4"}"/>')
        mx, my = (s0[0] + s1[0]) / 2, (s0[1] + s1[1]) / 2
        out.append(f'<text x="{mx:.1f}" y="{my - 7:.1f}" text-anchor="middle" fill="{C_DOOR if door else "#666"}">'
                   f'{esc(d["id"])}{" open edge" if not door else ""}</text>')
    holes_n = len(room.get("holes", ()))
    for rn in inst["runs"]:                                               # band pieces, joints, corners
        hole = rn["closed"] and rn["run"] > len(inst["runs"]) - holes_n
        off = 6.0 / sc                                                    # drawn just inside the wall line
        for q, pc in enumerate(rn["pieces"]):
            s0, s1 = pc["from_m"], pc["to_m"]
            segs = [(s0, s1)] if s0 >= 0 else [(s0 + rn["length_m"], rn["length_m"]), (0, s1)]
            for u, w in segs:
                pts = _along(rn["parts"], u, w, off, hole)
                if len(pts) < 2:
                    continue
                poly = " ".join(f"{P(*p)[0]:.1f},{P(*p)[1]:.1f}" for p in pts)
                out.append(f'<polyline points="{poly}" fill="none" stroke="{C_BAND[q % 2]}" stroke-width="7" '
                           f'stroke-opacity="0.9"/>')
            m0 = (s0 + s1) / 2 % rn["length_m"]
            mid = _along(rn["parts"], max(0.0, m0 - 0.01), m0 + 0.01, 4 * off, hole)
            if mid:
                mx, my = P(*mid[0])
                out.append(f'<text x="{mx:.1f}" y="{my + 4:.1f}" text-anchor="middle" fill="#7f4f00" '
                           f'font-weight="bold">{esc(pc["id"])}</text>')
        for jt in rn["joints"]:
            a_, b_ = jt["from_m"] % rn["length_m"], jt["to_m"] % rn["length_m"] or rn["length_m"]
            pts = _along(rn["parts"], a_, max(b_, a_ + 1e-6), off, hole)
            if pts:
                (x_a, y_a), (x_b, y_b) = P(*pts[0]), P(*pts[-1])
                out.append(f'<line x1="{x_a:.1f}" y1="{y_a:.1f}" x2="{x_b:.1f}" y2="{y_b:.1f}" stroke="{C_JOINT}" '
                           f'stroke-width="9"/>')
        for cr in rn["corners"]:
            cx, cy = P(*cr["at_m"])
            shape = (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="5" fill="none" stroke="#b45f06" stroke-width="2"/>'
                     if cr["kind"] == "INTERNAL" else
                     f'<rect x="{cx - 5:.1f}" y="{cy - 5:.1f}" width="10" height="10" fill="none" stroke="#7f6000" '
                     f'stroke-width="2"/>')
            out.append(shape)
    for it in inst["penetrations"]["items"]:
        cx, cy = P(*it["at_m"])
        out.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="5" fill="#674ea7"/><text x="{cx + 8:.1f}" '
                   f'y="{cy + 4:.1f}" fill="#674ea7">{esc(it["ref"])} clear {it["clear_m"]:.2f}</text>')
    yb = pad + (y1 - y0) * sc + 34
    b = pp["balance"]
    jun = v["junction"]
    lines = [f"rolls {b['rolls']}; consumed {b['consumed_m2']:.2f} m2 = installed {b['installed_m2']:.2f} + offcuts "
             f"{b['offcuts_m2']:.2f} (true waste {b['true_waste_m2']:.2f}, reusable subject to N-7 "
             f"{b['reusable_m2']:.2f}); roll stock {b['roll_stock_m2']:.2f} m2",
             f"band joints {inst['band_joints']}: nearest corner "
             f"{min((r['min_joint_corner_m'] for r in inst['runs'] if r['min_joint_corner_m'] is not None), default=0):.2f}"
             f" m, nearest floor-seam end "
             f"{min((r['min_joint_seam_end_m'] for r in inst['runs'] if r['min_joint_seam_end_m'] is not None), default=0):.2f}"
             f" m; jamb junctions {inst['jamb_junctions']}; corners {inst['corners']['internal']} internal / "
             f"{inst['corners']['external']} external",
             f"floor-to-wall junction {jun['state']}: rolls {jun['rolls_range'][0]} - {jun['rolls_range'][1]} over "
             "the alternatives (separate upstand flanges, continuous fold)",
             "open: " + ", ".join(v["flags"])]
    lines = [x for t in lines for x in _wrap(t)]
    for k, t in enumerate(lines):
        out.append(f'<text x="{pad}" y="{yb + 16 * k:.1f}">{esc(t)}</text>')
    ly = yb + 16 * len(lines) + 14
    legend = [("rect", C_FLOOR[0], "floor strip"), ("rect", C_SEAM, "floor lap zone"),
              ("line", C_BAND[0], "band piece (upturn)"), ("line", C_JOINT, "band joint (end lap)"),
              ("ring", "#b45f06", "internal corner"), ("sq", "#7f6000", "external corner"),
              ("line", C_DOOR, "doorway"), ("dot", "#674ea7", "drain / pipe")]
    for k, (kind, col, label) in enumerate(legend):
        x = pad + (k % 4) * 170
        y = ly + (k // 4) * 18
        if kind == "rect":
            out.append(f'<rect x="{x}" y="{y - 9}" width="14" height="10" fill="{col}" fill-opacity="0.6"/>')
        elif kind == "line":
            out.append(f'<line x1="{x}" y1="{y - 4}" x2="{x + 14}" y2="{y - 4}" stroke="{col}" stroke-width="6"/>')
        elif kind == "dot":
            out.append(f'<circle cx="{x + 7}" cy="{y - 4}" r="4" fill="{col}"/>')
        elif kind == "ring":
            out.append(f'<circle cx="{x + 7}" cy="{y - 4}" r="5" fill="none" stroke="{col}" stroke-width="2"/>')
        else:
            out.append(f'<rect x="{x + 2}" y="{y - 9}" width="10" height="10" fill="none" stroke="{col}" '
                       f'stroke-width="2"/>')
        out.append(f'<text x="{x + 20}" y="{y}">{esc(label)}</text>')
    out.append("</svg>")
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


# ------------------------------------------------------------------------------------------------ cutting plan
def cutting_svg(ex, a, path):
    pp = a["v26"]["piece_plan"]
    tree = {n["id"]: n for n in pp["tree"]}
    kids = {}
    for n in pp["tree"]:
        if n["from"] is not None:
            kids.setdefault(n["from"], []).append(n["id"])
    cls = {o["id"]: o["class"] for o in pp["offcuts"]}
    offs = {o["id"]: o for o in pp["offcuts"]}
    placed = {p["id"]: p for p in pp["pieces"]}
    L = max(r["cut_m"] + r["stock_m"] for r in pp["rolls"])
    sx, rh, pad, W = 640 / L, 70, 70, 760
    H = pad + len(pp["rolls"]) * (rh + 44) + 90
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="Arial" font-size="10">',
           f'<rect width="{W}" height="{H}" fill="white"/>',
           f'<text x="20" y="24" font-size="14" font-weight="bold">{esc(ex["id"])} cutting plan (ARCH_TAKEOFF_V2.6, '
           f'{len(pp["rolls"])} roll(s))</text>',
           '<text x="20" y="40" fill="#555">each roll 1.00 m wide drawn to scale along its length; cuts across, rips '
           'along the roll (lanes), cross-cuts within a lane</text>']

    def fill_of(n):
        if n in placed:
            k = placed[n]["kind"]
            return {"FLOOR": C_FLOOR[1], "BAND": C_BAND[1], "DOORWAY": C_DOOR, "DETAIL": "#8e7cc3"}[k]
        c = cls.get(n)
        return C_REUSE if c and c != "TRUE_WASTE" else C_WASTE

    def leafs(n, x, y, w, h, vertical):
        """draw node n in the box; its rip children stack across (y), its cross-cut children run along (x)."""
        ch = kids.get(n)
        if not ch or n in placed and tree[n]["kind"] == "FLOOR" and all(c.split(".")[-1].startswith("o") or
                                                                        c.endswith("o~") for c in ch):
            out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill_of(n)}" '
                       f'stroke="#444" stroke-width="0.6"/>')
            if w > 26 and h > 9:
                lab = n.split("/")[-1] if n not in placed else n
                out.append(f'<text x="{x + 2:.1f}" y="{y + min(h - 2, 10):.1f}">{esc(lab)}</text>')
            if n in placed and tree[n]["kind"] == "FLOOR" and ch:
                for c in ch:                                              # the floor beyond the wall line
                    o = offs.get(c, {})
                    at = o.get("in_piece_m")
                    if at:
                        ox, oy = x + w * at["along_m"] / tree[n]["l_m"], y + h * at["across_m"] / tree[n]["w_m"]
                        ow, oh = w * o["l_m"] / tree[n]["l_m"], h * o["w_m"] / tree[n]["w_m"]
                        out.append(f'<rect x="{ox:.1f}" y="{oy:.1f}" width="{ow:.1f}" height="{oh:.1f}" '
                                   f'fill="{fill_of(c)}" stroke="#444" stroke-width="0.6" stroke-dasharray="3,2"/>')
                        out.append(f'<text x="{ox + 2:.1f}" y="{oy + oh - 3:.1f}" fill="#7f6000">{esc(c)} '
                                   f'{o["w_m"]}x{o["l_m"]} offcut</text>')
                    else:
                        out.append(f'<text x="{x + 2:.1f}" y="{y + h - 2:.1f}" fill="#7f6000">{esc(c)} shaped '
                                   f'trim {o.get("area_m2", 0):.2f} m2</text>')
            return
        node = tree[n]
        if node["kind"] in ("SEGMENT", "CROSS_CUT") and n in kids and all(tree[c]["l_m"] == node["l_m"] for c in ch):
            yy = y
            for c in ch:                                                  # rip: parts across the width
                hh = h * (tree[c]["w_m"] / node["w_m"])
                leafs(c, x, yy, w, hh, vertical)
                yy += hh
        else:
            xx = x
            for c in ch:                                                  # cross-cut: pieces along the length
                ww = w * (tree[c]["l_m"] / node["l_m"])
                leafs(c, xx, y, ww, h, vertical)
                xx += ww
    y = pad
    for r in pp["rolls"]:
        out.append(f'<text x="20" y="{y + rh / 2 + 4:.1f}" font-weight="bold">roll {r["roll"]}</text>')
        x = pad
        for c in r["cuts"]:
            w = c["length_m"] * sx
            leafs(c["id"] if c["cut"] != "WHOLE" else c["parts"][0]["id"], x, y, w, rh, False)
            out.append(f'<text x="{x + 2:.1f}" y="{y + rh + 12:.1f}" fill="#333">{esc(c["id"])} {c["length_m"]:.2f}'
                       f' m</text>')
            x += w
        if r["stock_m"] > 1e-9:
            out.append(f'<rect x="{x:.1f}" y="{y}" width="{r["stock_m"] * sx:.1f}" height="{rh}" fill="{C_STOCK}" '
                       f'stroke="#999" stroke-dasharray="4,3"/><text x="{x + 3:.1f}" y="{y + rh / 2:.1f}" '
                       f'fill="#777">stock {r["stock_m"]:.2f} m</text>')
        y += rh + 44
    legend = [(C_FLOOR[1], "floor piece"), (C_BAND[1], "band piece"), (C_DOOR, "doorway piece"),
              (C_WASTE, "TRUE_WASTE"), (C_REUSE, "REUSABLE_SUBJECT_TO_N7"), (C_STOCK, "untouched roll stock")]
    for k, (col, label) in enumerate(legend):
        x = 20 + (k % 3) * 220
        yy = y + (k // 3) * 18
        out.append(f'<rect x="{x}" y="{yy - 9}" width="14" height="10" fill="{col}" stroke="#444" stroke-width="0.5"/>'
                   f'<text x="{x + 20}" y="{yy}">{esc(label)}</text>')
    out.append("</svg>")
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------------------------- tables
def chain(results):
    md = ["# The ten worked examples - verification chain (generated)", "",
          "OWNER / PROJECT RULE -> SOURCE DRAWING -> GEOMETRIC INTERPRETATION -> MEASUREMENT FORMULA -> INDEPENDENT "
          "EXPECTED RESULT -> ENGINE RESULT -> DIFFERENCE -> PASS / FAIL -> BOQ IMPACT", "",
          "Expected = the hand derivation (tests/m9_p2b5/install_cases.py, typed literals). Engine = ARCH_TAKEOFF_V2.6 "
          "(waterproofing_system + wp_install). Reference = the independent calculator rebuilding the engine's own "
          "cutting plan piece by piece (tests/m9_p2b5/install_reference.py); `-` where the reference does not compute "
          "the quantity. Tolerance 0.0005 (rounding only).", ""]
    rows = []
    n_pass = n_all = 0
    for ex, a, eng, ref in results:
        md += [f"## {ex['id']} - {ex['title']}", "",
               "**Rules:** " + "; ".join(ex["rules"]), "",
               "**Source drawing (synthetic):** ring " + fmt([tuple(round(c / 1000, 2) for c in p)
                                                            for p in ex["room"]["poly"]]) +
               (f"; doors {fmt([d['id'] for d in ex['room']['doors']])}" if ex["room"]["doors"] else "") +
               (f"; open edges {fmt([b['id'] for b in ex['room']['breaks']])}" if ex["room"].get("breaks") else "") +
               (f"; obstruction {len(ex['room']['holes'])}" if ex["room"].get("holes") else "") +
               (f"; drains {fmt([d['id'] for d in ex['room']['drains']])}" if ex["room"].get("drains") else "") +
               (f"; pipes {fmt([d['id'] for d in ex['room']['pipes']])}" if ex["room"].get("pipes") else ""), "",
               "**Geometric interpretation:** " + " ".join(ex["interpretation"]), "",
               "**Formula:** " + " ".join(ex["formula"]), "", "**Hand derivation:**", ""]
        md += [f"{k + 1}. {h}" for k, h in enumerate(ex["hand"])]
        md += ["", "| quantity | expected (hand) | engine | reference | difference | result |", "|---|---|---|---|---|---|"]
        for k, e in ex["expected"].items():
            g = eng.get(k)
            r = ref.get(k, "-") if ref else "-"
            ok = same(e, g) and (r == "-" or same(e, r))
            n_all += 1
            n_pass += ok
            md.append(f"| {k} | {fmt(e)} | {fmt(g)} | {fmt(r)} | {diff(e, g)} | {'PASS' if ok else 'FAIL'} |")
            rows.append({"example": ex["id"], "quantity": k, "expected": fmt(e), "engine": fmt(g), "reference": fmt(r),
                         "difference": diff(e, g), "result": "PASS" if ok else "FAIL"})
        flags_ok = sorted(ex["flags"]) == sorted(eng["flags"])
        n_all += 1
        n_pass += flags_ok
        md += ["", f"**Open details (flags):** expected {', '.join(sorted(ex['flags']))}; engine "
               f"{', '.join(sorted(eng['flags']))} - {'PASS' if flags_ok else 'FAIL'}", "",
               f"**BOQ impact:** {ex['boq_impact']}", "",
               f"Diagrams: `diagrams/{ex['id']}_install.svg`, `diagrams/{ex['id']}_cutting.svg`", ""]
        rows.append({"example": ex["id"], "quantity": "flags", "expected": "; ".join(sorted(ex["flags"])),
                     "engine": "; ".join(sorted(eng["flags"])), "reference": "-", "difference": "0" if flags_ok
                     else "differs", "result": "PASS" if flags_ok else "FAIL"})
    for ex in (IC.IX09, IC.IX10):
        built = [IE.area(IC.BY_ID[r]["room"] if isinstance(r, str) else r, room_id=rid)
                 for rid, r in ex["areas"].items()]
        plans = IE.shared(built)
        scope = {a_["system"]["system_id"]: a_["scope"] for a_ in built}
        if ex is IC.IX09:
            p = plans[0]
            got = {"rolls_alone": p["rolls_if_each_area_alone"], "rolls_shared": p["rolls"],
                   "consumed_m2": p["consumed_m2"], "gross_m2": p["gross_roll_area_m2"],
                   "untouched_m2": p["untouched_roll_tails_m2"],
                   "pieces": sum(len(r["pieces"]) for r in p["cutting_plan"])}
        else:
            got = {"systems": len(plans), "rolls_by_scope": {scope[p["system_id"]]: p["rolls"] for p in plans},
                   "rolls_total": sum(p["rolls"] for p in plans),
                   "rolls_if_mixed": len(IR.CR.pack([round(s["length_m"] * 1000) for a_ in built for r in
                                                     a_["layout"]["layout"]["rolls"] for s in r["segments"]], 10000))}
        md += [f"## {ex['id']} - {ex['title']}", "", "**Rules:** " + "; ".join(ex["rules"]), "",
               "**Interpretation:** " + " ".join(ex["interpretation"]), "", "**Formula:** " + " ".join(ex["formula"]),
               "", "**Hand derivation:**", ""] + [f"{k + 1}. {h}" for k, h in enumerate(ex["hand"])] + \
              ["", "| quantity | expected (hand) | engine | difference | result |", "|---|---|---|---|---|"]
        for k, e in ex["expected"].items():
            ok = same(e, got.get(k))
            n_all += 1
            n_pass += ok
            md.append(f"| {k} | {fmt(e)} | {fmt(got.get(k))} | {diff(e, got.get(k))} | {'PASS' if ok else 'FAIL'} |")
            rows.append({"example": ex["id"], "quantity": k, "expected": fmt(e), "engine": fmt(got.get(k)),
                         "reference": "-", "difference": diff(e, got.get(k)), "result": "PASS" if ok else "FAIL"})
        md += ["", f"**BOQ impact:** {ex['boq_impact']}", ""]
    md[6:6] = [f"**{n_pass} of {n_all} checks PASS.**", ""]
    (HERE / "WORKED_EXAMPLES.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    with open(HERE / "VERIFICATION_CHAIN.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["example", "quantity", "expected", "engine", "reference", "difference",
                                           "result"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    return n_pass, n_all


def junction_table(results):
    md = ["# Floor-to-wall junction alternatives (generated)", "",
          "Naming as in the owner's program: **Alternative A = continuous fold** (the floor sheet folded up the "
          "walls, no band, no connection lap; engine method CONTINUOUS_FOLD), **Alternative B = separate upturn** (a "
          "band strip with its own connection lap - the flange - onto the floor sheet, set apart from the side and "
          "end laps; engine method SEPARATE_UPSTAND). The Phase 2B-4 audit used the letters the other way round.", "",
          "The junction stays UNRESOLVED (N-11 / P-1). Flanges other than the plan's 0.10 m are sensitivity points, "
          "not standards. Every alternative plan below is the engine's own cutting plan, rebuilt by the independent "
          "reference calculator (consumed / installed / rolls equal, coverage complete); the fold is checked against "
          "the Phase 2B-4 method-B planner in the tests.", "",
          "| example | alternative | flange (m) | rolls | consumed m2 | installed m2 | seams | basis | reference |",
          "|---|---|---|---|---|---|---|---|---|"]
    for ex, a, _, _ in results:
        jun = a["v26"]["junction"]
        for alt in jun["alternatives"]:
            ref = "-"
            if alt.get("trace"):
                pl = IE.plan(a, alt["trace"])
                r = IR.summary(IR.verify_A(ex["room"], dict(IR.URBAN, j=pl["j"]), pl))
                ok = (r["rolls"], r["consumed_m2"], r["installed_m2"]) == (alt["rolls"], alt["consumed_m2"],
                                                                           alt["installed_m2"])
                ref = f"{r['rolls']} / {r['consumed_m2']:g} / {r['installed_m2']:g} {'PASS' if ok else 'FAIL'}"
            label = "A continuous fold" if alt["method"] == "CONTINUOUS_FOLD" else "B separate upturn"
            md.append(f"| {ex['id']} | {label} | {fmt(alt.get('flange_m', '-'))} | {alt['rolls']} | "
                      f"{alt['consumed_m2']:g} | {alt['installed_m2']:g} | {alt['seams']} | {alt['basis']} | {ref} |")
        fold = jun["continuous_fold"]
        if fold["state"] != "COMPUTED":
            md.append(f"| {ex['id']} | A continuous fold | - | - | - | - | - | {fold['reason']} | - |")
    md += ["", "## The flange sweeps", "", "| example | flange (m): rolls / consumed m2 |", "|---|---|"]
    for ex, a, _, _ in results:
        sw = a["v26"]["junction"]["flange_sweep"]
        md.append(f"| {ex['id']} | " + "; ".join(f"{x['flange_m']:.2f}: {x['rolls']} / {x['consumed_m2']:g}"
                                                 for x in sw) + " |")
    (HERE / "JUNCTION_ALTERNATIVES.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def main():
    DIAG.mkdir(parents=True, exist_ok=True)
    results = []
    for ex in IC.SINGLE:
        a = IE.area(ex["room"], room_id=ex["id"])
        eng = IE.figures(a)
        ref = IR.summary(IR.verify_A(ex["room"], IR.URBAN, IE.plan(a)))
        results.append((ex, a, eng, ref))
        install_svg(ex, a, DIAG / f"{ex['id']}_install.svg")
        cutting_svg(ex, a, DIAG / f"{ex['id']}_cutting.svg")
    n_pass, n_all = chain(results)
    junction_table(results)
    print(f"{n_pass}/{n_all} checks PASS; {len(results) * 2} diagrams")


if __name__ == "__main__":
    main()
