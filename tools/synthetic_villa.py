"""SYNTHETIC VILLA (M2) - structural DXF drawings generated from a design spec, with ground truth from the SPEC.

    python3 -I tools/synthetic_villa.py OUT_DIR SEED [SEED ...]

The truth is computed analytically from the design (grid spans, member sizes, schedule bars) - it never reads the DXF
and shares no geometry code with the engine. The drawing is what a draftsman would produce from the same design:
beam faces from column face to column face, column outlines (some as rotated / mirrored block inserts), footing
outlines with combined marks, slab thickness tag, an opening (VOID + X), schedules as attribute-row blocks, titles
in English or Arabic, units in mm or m, varied layer and tag spellings. Variants inject the hard cases: an untagged
span on a tagged line, a beam drawn at another width than its schedule, a beam type missing from the schedule, a
curved beam, an opening bay.

DEFECTS (generate(..., defects=True)): the same design drawn the way real drawings arrive - beam faces broken into
collinear pieces, duplicated lines, face ends stopping short of (gap <= 2 mm) or running into (<= 20 mm) the column,
footing outlines as loose lines, grid axes with bubbles and labels, linear dimensions, MTEXT tags with formatting
codes, tags pushed further off the face, solid hatches in the columns. defects="hard" widens the end gaps to 6-15 mm,
beyond any snap tolerance: the engine must then REPORT the open faces, not guess them. The truth is unchanged: the defects are
drafting noise, not design changes (a face that stops 2 mm short still means a beam from face to face).

Conventions the truth uses are the generic convention set's BASE values (cover, anchorage, lap, hook table), stated
in the truth file, so the comparison isolates detection, geometry and parsing.
"""

from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COL_TYPES = [(0.20, 0.40), (0.25, 0.50), (0.30, 0.30), (0.20, 0.60), (0.30, 0.50)]
BEAM_TYPES = [(0.20, 0.50), (0.25, 0.60), (0.20, 0.40), (0.30, 0.70), (0.25, 0.50)]
FTG_TYPES = [(1.2, 1.2, 0.40), (1.5, 1.3, 0.45), (1.8, 1.6, 0.50), (2.0, 2.0, 0.55)]
LAYERS = [
    {"beam": "S-BEAM", "col": "S-COL", "ftg": "S-FTG", "text": "S-TEXT", "open": "S-OPEN", "frame": "SHEET",
     "sched": "S-SCHED"},
    {"beam": "BEAM EDGE", "col": "COLUMNS", "ftg": "FOUNDATION", "text": "ANNO", "open": "VOIDS", "frame": "BORDER",
     "sched": "SCHEDULE"},
    {"beam": "1", "col": "STR-COL", "ftg": "STR-FDN", "text": "TXT", "open": "2", "frame": "DEFPOINTS",
     "sched": "TBL"},
]
TITLES = {"EN": {"FOUNDATION": "FOUNDATION PLAN", "GF": "GROUND FLOOR ROOF SLAB", "1F": "FIRST FLOOR ROOF SLAB",
                 "SCHED": "SCHEDULE OF FOOTINGS COLUMNS AND BEAMS"},
          "AR": {"FOUNDATION": "مخطط القواعد", "GF": "سقف الدور الأرضي", "1F": "سقف الدور الأول",
                 "SCHED": "جدول القواعد والأعمدة والجسور"}}
TAGSETS = [
    {"ftg": ("FO-TY", "W", "H", "DEPHT", "SH-B", "SH-D", "LO-B", "LO-D"), "col": "COL-T",
     "beam": ("BEAM", "W", "H", "BOT-B", "BOT-D", "TOP-B", "TOP-D", "STI-B", "D"), "unit": "cm"},
    {"ftg": ("MARK", "WIDTH", "LENGTH", "DEPTH", "SH-N", "SH-DIA", "LO-N", "LO-DIA"), "col": "TYPE",
     "beam": ("TYPE", "WIDTH", "DEPTH", "BOT-N", "BOT-DIA", "TOP-N", "TOP-DIA", "LINK-N", "LINK-DIA"), "unit": "mm"},
]
BASE = {"cover_beam": 0.025, "cover_col": 0.04, "cover_ftg": 0.05, "anch_d": 40, "lap_d": 50}


def kgm(d):
    return d * d / 162.0


def aci_hook_add(db, kind):
    """ACI 318-19 hook addition re-derived here (independent of engine.source.bbs_optimiser)."""
    if kind == "135_TIE":
        D = (4 if db <= 16 else 6) * db
        tail = max(6 * db, 75.0)
        ang = 135.0
    else:
        D = (6 if db <= 25 else 8) * db
        tail = 12 * db
        ang = 90.0
    rc = D / 2 + db / 2
    return (tail + math.radians(ang) * rc - (D / 2 + db)) / 1000.0


def link_len(b, h, c, d):
    dm = d / 1000.0
    a, bb = b - 2 * c - dm, h - 2 * c - dm
    D = (4 if d <= 16 else 6) * dm
    rc = D / 2 + dm / 2
    return 2 * (a + bb) - 8 * rc + 2 * math.pi * rc + 2 * aci_hook_add(d, "135_TIE")


def design(seed):
    R = random.Random(seed)
    nx, ny = R.choice([2, 3, 3, 4]), R.choice([2, 2, 3])
    sx = [round(R.uniform(3.2, 5.8) / 0.05) * 0.05 for _ in range(nx)]
    sy = [round(R.uniform(3.2, 5.6) / 0.05) * 0.05 for _ in range(ny)]
    xs = [0.0]
    for s in sx:
        xs.append(round(xs[-1] + s, 3))
    ys = [0.0]
    for s in sy:
        ys.append(round(ys[-1] + s, 3))
    ctypes = R.sample(range(len(COL_TYPES)), 2)
    cmin = min(min(COL_TYPES[c]) for c in ctypes)
    ok = [k for k, (B, _) in enumerate(BEAM_TYPES) if B <= cmin + 1e-9]     # a beam never wider than its column
    btypes = [ok[(seed + n) % len(ok)] if len(ok) < 3 else x for n, x in enumerate(R.sample(ok, min(3, len(ok))))]
    while len(btypes) < 3:
        btypes.append(ok[len(btypes) % len(ok)])
    ftypes = R.sample(range(len(FTG_TYPES)), 2)
    cols = []
    for i, x in enumerate(xs):
        for j, y in enumerate(ys):
            ct = ctypes[(i + j) % 2]
            rot = R.choice([0, 90]) if seed % 3 else 0
            cols.append({"i": i, "j": j, "x": x, "y": y, "type": f"C{ct + 1}", "sec": COL_TYPES[ct], "rot": rot,
                         "mirror": bool(seed % 4 == 1 and (i + j) % 3 == 0), "block": seed % 2 == 1,
                         "ftg": f"F{ftypes[(i * 7 + j) % 2] + 1}"})
    var = {"units": "m" if seed % 5 == 2 else "mm", "lang": "AR" if seed % 3 == 2 else "EN",
           "layers": LAYERS[seed % 3], "tags": TAGSETS[seed % 2], "curved": seed % 2 == 0,
           "untagged_span": True, "width_conflict": seed % 3 == 0, "missing_type": seed % 4 == 3,
           "opening": True}
    return {"seed": seed, "xs": xs, "ys": ys, "cols": cols, "ctypes": [f"C{c + 1}" for c in ctypes],
            "btypes": [f"B{b + 1}" for b in btypes], "ftypes": [f"F{f + 1}" for f in ftypes], "var": var,
            "slab_t": {"GF": 0.16, "1F": 0.16}, "heights": {"GF": 4.0, "1F": 3.6}, "R": R}


def _dim(col, axis):
    """column extent along an axis ('x' or 'y') after rotation."""
    b, h = col["sec"]
    w, d = (b, h) if col["rot"] == 0 else (h, b)
    return w if axis == "x" else d


def beams_of(D):
    """Beam spans on every grid line between adjacent columns: type by line index; one span untagged; one type
    missing from the schedule; one drawn at another width (all from the design, deterministic)."""
    xs, ys = D["xs"], D["ys"]
    col = {(c["i"], c["j"]): c for c in D["cols"]}
    out = []
    k = 0
    for j, y in enumerate(ys):
        for i in range(len(xs) - 1):
            a, b = col[(i, j)], col[(i + 1, j)]
            out.append({"axis": "x", "line": j, "a": a, "b": b, "type": D["btypes"][j % 3], "k": k})
            k += 1
    for i, x in enumerate(xs):
        for j in range(len(ys) - 1):
            a, b = col[(i, j)], col[(i, j + 1)]
            out.append({"axis": "y", "line": i, "a": a, "b": b, "type": D["btypes"][(i + 1) % 3], "k": k})
            k += 1
    for bm in out:
        B, H = BEAM_TYPES[int(bm["type"][1:]) - 1]
        bm["B"], bm["H"] = B, H
        ax = bm["axis"]
        if ax == "x":
            bm["clear"] = (bm["b"]["x"] - bm["a"]["x"]) - _dim(bm["a"], "x") / 2 - _dim(bm["b"], "x") / 2
        else:
            bm["clear"] = (bm["b"]["y"] - bm["a"]["y"]) - _dim(bm["a"], "y") / 2 - _dim(bm["b"], "y") / 2
        bm["tagged"] = True
        bm["drawn_B"] = B
    # an untagged span: the second span on line 0 (same type as its line): the engine may inherit it
    line0 = [b for b in out if b["axis"] == "x" and b["line"] == 0]
    if D["var"]["untagged_span"] and len(line0) >= 2:
        line0[1]["tagged"] = False
    if D["var"]["width_conflict"]:
        cand = [b for b in out if b["axis"] == "y" and b["B"] >= 0.25]
        if cand:
            cand[0]["drawn_B"] = round(cand[0]["B"] - 0.05, 3)                   # drawn narrower than scheduled
    for b in out:
        b["mid_design"] = ((b["a"]["x"] + b["b"]["x"]) / 2, (b["a"]["y"] + b["b"]["y"]) / 2)
    return out


def schedule_rows(D):
    rows = {"FOOTING": [], "COLUMN": [], "BEAM": []}
    for f in D["ftypes"]:
        L, W, Dp = FTG_TYPES[int(f[1:]) - 1]
        rows["FOOTING"].append({"mark": f, "L": L, "W": W, "D": Dp, "sh": (round(L / 0.15) + 1, 12),
                                "lo": (round(W / 0.15) + 1, 12)})
    for c in D["ctypes"]:
        B, H = COL_TYPES[int(c[1:]) - 1]
        rows["COLUMN"].append({"mark": c, "B": B, "H": H, "bars": (6 if B * H < 0.12 else 8, 16)})
    for i, b in enumerate(D["btypes"]):
        if D["var"]["missing_type"] and i == 2:
            continue                                      # a beam type on the plan but missing from the schedule
        B, H = BEAM_TYPES[int(b[1:]) - 1]
        rows["BEAM"].append({"mark": b, "B": B, "H": H, "bot": (3, 16), "top": (2, 12), "sti": (5, 8)})
    if D["var"]["curved"]:
        rows["BEAM"].append({"mark": "B9", "B": 0.2, "H": 0.5, "bot": (2, 14), "top": (2, 12), "sti": (5, 8)})
    return rows


SHEET_ORDER = ["FOUNDATION", "GF", "1F", "SCHED"]


def to_drawing(D, sheet, x, y):
    s = 1.0 if D["var"]["units"] == "m" else 1000.0
    n = SHEET_ORDER.index(sheet)
    return ((n * 45.0 + 4.0 + x) * s, (4.0 + y) * s)


def truth(D):
    """Quantities from the design only."""
    rows = schedule_rows(D)
    beams = beams_of(D)
    sched_b = {r["mark"]: r for r in rows["BEAM"]}
    t = {"FOOTINGS": 0.0, "COLUMNS": 0.0, "BEAMS_TOTAL_DEPTH": 0.0, "BEAMS_BELOW_SLAB": 0.0, "SLABS": 0.0,
         "STEEL_FOOTINGS": 0.0, "STEEL_COLUMNS_MAIN": 0.0, "STEEL_BEAMS": 0.0}
    comp = {"footings": [], "columns": [], "beams": [], "panels": []}
    fr = {r["mark"]: r for r in rows["FOOTING"]}
    for c in D["cols"]:
        f = fr[c["ftg"]]
        t["FOOTINGS"] += f["L"] * f["W"] * f["D"]
        comp["footings"].append({"x": c["x"], "y": c["y"], "type": c["ftg"],
                                 "at": to_drawing(D, "FOUNDATION", c["x"], c["y"])})
        L, W = sorted((f["L"], f["W"]), reverse=True)
        n, d = f["sh"]
        t["STEEL_FOOTINGS"] += n * (W - 2 * BASE["cover_ftg"]) * kgm(d)
        n, d = f["lo"]
        t["STEEL_FOOTINGS"] += n * (L - 2 * BASE["cover_ftg"]) * kgm(d)
    cr = {r["mark"]: r for r in rows["COLUMN"]}
    for st in ("GF", "1F"):
        h = D["heights"][st]
        for c in D["cols"]:
            r = cr[c["type"]]
            t["COLUMNS"] += r["B"] * r["H"] * h
            n, d = r["bars"]
            t["STEEL_COLUMNS_MAIN"] += n * (h + BASE["lap_d"] * d / 1000) * kgm(d)
            comp["columns"].append({"x": c["x"], "y": c["y"], "storey": st})
    for st in ("GF", "1F"):
        tt = D["slab_t"][st]
        for bm in beams:
            sb = sched_b.get(bm["type"])
            comp["beams"].append({"storey": st, "axis": bm["axis"], "a": (bm["a"]["x"], bm["a"]["y"]),
                                  "b": (bm["b"]["x"], bm["b"]["y"]), "type": bm["type"], "in_schedule": bool(sb),
                                  "at": to_drawing(D, st, *bm["mid_design"]), "tagged": bm["tagged"]})
            if not sb:
                continue
            t["BEAMS_TOTAL_DEPTH"] += sb["B"] * sb["H"] * bm["clear"]
            t["BEAMS_BELOW_SLAB"] += sb["B"] * (sb["H"] + tt) * bm["clear"]
            L = bm["clear"]
            for n, d in (sb["bot"], sb["top"]):
                t["STEEL_BEAMS"] += n * (L + 2 * BASE["anch_d"] * d / 1000) * kgm(d)
            n, d = sb["sti"]
            t["STEEL_BEAMS"] += (n * L + 1) * link_len(sb["B"], sb["H"], BASE["cover_beam"], d) * kgm(d)
        if D["var"]["curved"]:
            Rc, th = 2.0, math.radians(90)
            sb = sched_b["B9"]
            t["BEAMS_TOTAL_DEPTH"] += sb["B"] * sb["H"] * Rc * th
            t["BEAMS_BELOW_SLAB"] += sb["B"] * (sb["H"] + tt) * Rc * th
            L = Rc * th
            for n, d in (sb["bot"], sb["top"]):
                t["STEEL_BEAMS"] += n * (L + 2 * BASE["anch_d"] * d / 1000) * kgm(d)
            n, d = sb["sti"]
            t["STEEL_BEAMS"] += (n * L + 1) * link_len(sb["B"], sb["H"], BASE["cover_beam"], d) * kgm(d)
            # annular-sector centroid: rho = 2 sin(a) / (3 a) x (R^3 - r^3) / (R^2 - r^2), a = half angle, on 45 deg
            cx, cy = D["xs"][-1] + 5.0, D["ys"][-1] / 2.0
            ro, ri, a = Rc + sb["B"] / 2, Rc - sb["B"] / 2, th / 2
            rho = 2 * math.sin(a) / (3 * a) * (ro ** 3 - ri ** 3) / (ro ** 2 - ri ** 2)
            comp["beams"].append({"storey": st, "axis": "arc", "type": "B9", "in_schedule": True, "tagged": True,
                                  "at": to_drawing(D, st, cx + rho * math.cos(a), cy + rho * math.sin(a))})
        # slab panels: each bay between beam faces, minus column corners beyond the beam faces; opening bay excluded
        xs, ys = D["xs"], D["ys"]
        col = {(c["i"], c["j"]): c for c in D["cols"]}
        bx = {(b["axis"], b["line"], (b["a"]["i"] if b["axis"] == "x" else b["a"]["j"])): b for b in beams}
        for i in range(len(xs) - 1):
            for j in range(len(ys) - 1):
                if D["var"]["opening"] and (i, j) == (0, 0):
                    continue
                bs = bx[("x", j, i)]["drawn_B"] / 2
                bn = bx[("x", j + 1, i)]["drawn_B"] / 2
                bw = bx[("y", i, j)]["drawn_B"] / 2
                be = bx[("y", i + 1, j)]["drawn_B"] / 2
                x0, x1, y0, y1 = xs[i] + bw, xs[i + 1] - be, ys[j] + bs, ys[j + 1] - bn
                area = (x1 - x0) * (y1 - y0)
                for (ci, cj) in ((i, j), (i + 1, j), (i, j + 1), (i + 1, j + 1)):
                    c = col[(ci, cj)]
                    hx, hy = _dim(c, "x") / 2, _dim(c, "y") / 2
                    ox = max(0.0, min(x1, c["x"] + hx) - max(x0, c["x"] - hx))
                    oy = max(0.0, min(y1, c["y"] + hy) - max(y0, c["y"] - hy))
                    area -= ox * oy
                t["SLABS"] += area * tt
                comp["panels"].append({"storey": st, "i": i, "j": j, "area": area,
                                       "at": to_drawing(D, st, (x0 + x1) / 2, (y0 + y1) / 2)})
    return {"seed": D["seed"], "quantities": t, "components": {k: len(v) for k, v in comp.items()},
            "component_list": comp, "conventions_used": BASE, "variant": {k: v for k, v in D["var"].items()
                                                                          if k != "layers"} | {"layers": D["var"]["layers"]},
            "storey_heights": D["heights"]}


def write_dxf(D, path):
    import ezdxf
    from ezdxf.math import Vec2
    v = D["var"]
    s = 1.0 if v["units"] == "m" else 1000.0                     # metres -> drawing units
    L = v["layers"]
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 6 if v["units"] == "m" else 4
    msp = doc.modelspace()
    for lay in L.values():
        if lay not in doc.layers:
            doc.layers.add(lay)
    th = 0.2 * s
    sheet_w, sheet_h = 40.0, 30.0
    order = SHEET_ORDER
    origin = {k: (n * (sheet_w + 5.0), 0.0) for n, k in enumerate(order)}

    def P(k, x, y):
        ox, oy = origin[k]
        return ((ox + 4.0 + x) * s, (oy + 4.0 + y) * s)

    def rect(k, cx, cy, w, h, layer):
        x0, y0 = P(k, cx - w / 2, cy - h / 2)
        x1, y1 = P(k, cx + w / 2, cy + h / 2)
        msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs={"layer": layer})

    def text(k, val, x, y, rot=0.0, layer=None, h=None):
        tx = msp.add_text(val, dxfattribs={"layer": layer or L["text"], "height": h or th, "rotation": rot})
        tx.set_placement(P(k, x, y))

    for k in order:
        ox, oy = origin[k]
        msp.add_lwpolyline([(ox * s, oy * s), ((ox + sheet_w) * s, oy * s), ((ox + sheet_w) * s, (oy + sheet_h) * s),
                            (ox * s, (oy + sheet_h) * s)], close=True, dxfattribs={"layer": L["frame"]})
        tt = msp.add_text(TITLES[v["lang"]][k], dxfattribs={"layer": L["text"], "height": 0.4 * s})
        tt.set_placement(((ox + 1.0) * s, (oy + sheet_h - 1.5) * s))          # inside the frame, top left
    # column blocks (rotated / mirrored inserts) - one block per column type, centred on the origin
    for ct in D["ctypes"]:
        B, H = COL_TYPES[int(ct[1:]) - 1]
        blk = doc.blocks.new(name=f"COLBLK_{ct}")
        blk.add_lwpolyline([(-B / 2 * s, -H / 2 * s), (B / 2 * s, -H / 2 * s), (B / 2 * s, H / 2 * s),
                            (-B / 2 * s, H / 2 * s)], close=True, dxfattribs={"layer": "0"})
    rows = schedule_rows(D)
    fr = {r["mark"]: r for r in rows["FOOTING"]}
    for c in D["cols"]:
        f = fr[c["ftg"]]
        if v.get("defects") and (c["i"] + c["j"]) % 2 == 0:
            x0, y0 = c["x"] - f["L"] / 2, c["y"] - f["W"] / 2
            x1, y1 = c["x"] + f["L"] / 2, c["y"] + f["W"] / 2
            for p0, p1 in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
                msp.add_line(P("FOUNDATION", *p0), P("FOUNDATION", *p1), dxfattribs={"layer": L["ftg"]})
        else:
            rect("FOUNDATION", c["x"], c["y"], f["L"], f["W"], L["ftg"])
        text("FOUNDATION", f"{c['type']}/{c['ftg']}", c["x"] - f["L"] / 2 + 0.08, c["y"] - f["W"] / 2 + 0.1)
        for k in ("FOUNDATION", "GF", "1F"):
            B, H = c["sec"]
            if c["block"]:
                ins = msp.add_blockref(f"COLBLK_{c['type']}", P(k, c["x"], c["y"]),
                                       dxfattribs={"layer": L["col"], "rotation": c["rot"]})
                if c["mirror"]:
                    ins.dxf.xscale = -1.0
            else:
                w, d = (B, H) if c["rot"] == 0 else (H, B)
                rect(k, c["x"], c["y"], w, d, L["col"])
            if v.get("defects") and k != "FOUNDATION":
                w, d = (B, H) if c["rot"] == 0 else (H, B)
                ht = msp.add_hatch(color=7, dxfattribs={"layer": L["col"]})
                x0, y0 = P(k, c["x"] - w / 2, c["y"] - d / 2)
                x1, y1 = P(k, c["x"] + w / 2, c["y"] + d / 2)
                ht.paths.add_polyline_path([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], is_closed=True)
            if k != "FOUNDATION":
                w, d = (B, H) if c["rot"] == 0 else (H, B)
                text(k, c["type"], c["x"] + w / 2 + 0.05, c["y"] + d / 2 + 0.05, h=0.15 * s)
    beams = beams_of(D)
    DF = v.get("defects")
    RD = random.Random(D["seed"] * 7919 + 13)                    # defect noise only - never touches the design
    applied = {}

    def note(code):
        applied[code] = applied.get(code, 0) + 1

    def face(k, p0, p1, layer):
        """one beam face from p0 to p1 (design metres); with defects: end gap / overshoot, break, duplicate."""
        (x0, y0), (x1, y1) = p0, p1
        if DF:
            ln = math.hypot(x1 - x0, y1 - y0)
            ux, uy = (x1 - x0) / ln, (y1 - y0) / ln
            g0, g1 = (0.006, 0.015) if DF == "hard" else (0.0005, 0.002)     # "hard": gaps beyond any snap
            e0 = RD.choice([0.0, -RD.uniform(g0, g1), RD.uniform(0.002, 0.02)])
            e1 = RD.choice([0.0, -RD.uniform(g0, g1), RD.uniform(0.002, 0.02)])
            for e in (e0, e1):
                if e < 0:
                    note("END_GAP")
                elif e > 0:
                    note("END_OVERSHOOT")
            x0, y0, x1, y1 = x0 - ux * e0, y0 - uy * e0, x1 + ux * e1, y1 + uy * e1
            if RD.random() < 0.4:
                t = RD.uniform(0.3, 0.7)
                xm, ym = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
                msp.add_line(P(k, x0, y0), P(k, xm, ym), dxfattribs={"layer": layer})
                msp.add_line(P(k, xm, ym), P(k, x1, y1), dxfattribs={"layer": layer})
                note("BROKEN_FACE")
            else:
                msp.add_line(P(k, x0, y0), P(k, x1, y1), dxfattribs={"layer": layer})
            if RD.random() < 0.15:
                msp.add_line(P(k, x0, y0), P(k, x1, y1), dxfattribs={"layer": layer})
                note("DUPLICATE_LINE")
            return
        msp.add_line(P(k, x0, y0), P(k, x1, y1), dxfattribs={"layer": layer})

    def tag(k, val, x, y, rot, h):
        if DF and RD.random() < 0.5:
            mt = msp.add_mtext("{\\fArial|b0|i0|c0|p34;" + val + "}", dxfattribs={"layer": L["text"],
                                                                                  "char_height": h, "rotation": rot})
            mt.set_location(P(k, x, y))
            note("MTEXT_TAG")
            return
        text(k, val, x, y, rot, h=h)

    for k in ("GF", "1F"):
        for bm in beams:
            a, b = bm["a"], bm["b"]
            hw = bm["drawn_B"] / 2
            push = RD.uniform(0.05, 0.15) if DF else 0.0              # a tag further off the face
            if push:
                note("TAG_PUSHED")
            if bm["axis"] == "x":
                x0, x1 = a["x"] + _dim(a, "x") / 2, b["x"] - _dim(b, "x") / 2
                for off in (-hw, hw):
                    face(k, (x0, a["y"] + off), (x1, a["y"] + off), L["beam"])
                if bm["tagged"]:
                    tag(k, bm["type"], (x0 + x1) / 2 - 0.2, a["y"] + hw + 0.06 + push, 0.0, 0.15 * s)
            else:
                y0, y1 = a["y"] + _dim(a, "y") / 2, b["y"] - _dim(b, "y") / 2
                for off in (-hw, hw):
                    face(k, (a["x"] + off, y0), (a["x"] + off, y1), L["beam"])
                if bm["tagged"]:
                    tag(k, bm["type"], a["x"] - hw - 0.06 - push, (y0 + y1) / 2 - 0.2, 90.0, 0.15 * s)
        if DF:
            _grid_and_dims(D, k, msp, P, s, doc, note)
        if D["var"]["curved"]:
            cx, cy = D["xs"][-1] + 5.0, D["ys"][-1] / 2.0
            for r in (2.0 - 0.1, 2.0 + 0.1):
                msp.add_arc(P(k, cx, cy), r * s, 0, 90, dxfattribs={"layer": L["beam"]})
            text(k, "B9", cx + 1.3, cy + 1.3, 315.0, h=0.15 * s)
        # thickness tag inside one panel; opening (VOID + X) in bay (0, 0)
        xs, ys = D["xs"], D["ys"]
        text(k, f"T={int(D['slab_t'][k] * 100)}", (xs[-2] + xs[-1]) / 2, (ys[-2] + ys[-1]) / 2)
        if D["var"]["opening"]:
            x0, x1, y0, y1 = xs[0] + 0.3, xs[1] - 0.3, ys[0] + 0.3, ys[1] - 0.3
            msp.add_line(P(k, x0, y0), P(k, x1, y1), dxfattribs={"layer": L["open"]})
            msp.add_line(P(k, x0, y1), P(k, x1, y0), dxfattribs={"layer": L["open"]})
            text(k, "VOID" if v["lang"] == "EN" else "فتحة", (x0 + x1) / 2 + 0.3, (y0 + y1) / 2 + 0.6)
    # schedules as attribute rows
    u = 100.0 if v["tags"]["unit"] == "cm" else 1000.0
    T = v["tags"]

    def row_block(name, tags):
        blk = doc.blocks.new(name=name)
        for n, tg in enumerate(tags):
            blk.add_attdef(tg, (n * 0.8 * s, 0), dxfattribs={"height": 0.15 * s, "layer": L["sched"]})
        return name

    def place(name, tags, values, y):
        ins = msp.add_blockref(name, P("SCHED", 1.0, y), dxfattribs={"layer": L["sched"]})
        ins.add_auto_attribs(dict(zip(tags, [str(x) for x in values])))
    fb = row_block("FTG_ROW", T["ftg"])
    y = 20.0
    for r in rows["FOOTING"]:
        place(fb, T["ftg"], [r["mark"], f"{r['L'] * u:g}", f"{r['W'] * u:g}", f"{r['D'] * u:g}", r["sh"][0],
                             r["sh"][1], r["lo"][0], r["lo"][1]], y)
        y -= 0.6
    ctags = (T["col"], "GR.W", "GR.H", "GR.R", "GR.D", "1ST.W", "1ST.H", "1ST.R", "1ST.D")
    cb = row_block("COL_ROW", ctags)
    for r in rows["COLUMN"]:
        place(cb, ctags, [r["mark"], f"{r['B'] * u:g}", f"{r['H'] * u:g}", r["bars"][0], r["bars"][1],
                          f"{r['B'] * u:g}", f"{r['H'] * u:g}", r["bars"][0], r["bars"][1]], y)
        y -= 0.6
    bb = row_block("BEAM_ROW", T["beam"])
    for r in rows["BEAM"]:
        place(bb, T["beam"], [r["mark"], f"{r['B'] * u:g}", f"{r['H'] * u:g}", r["bot"][0], r["bot"][1], r["top"][0],
                              r["top"][1], r["sti"][0], r["sti"][1]], y)
        y -= 0.6
    doc.saveas(path)
    D["defects_applied"] = applied
    return path


def _grid_and_dims(D, k, msp, P, s, doc, note):
    """grid axes (beyond the plan, through every column line) with bubbles and labels, and linear span dimensions."""
    if "S-GRID" not in doc.layers:
        doc.layers.add("S-GRID")
        doc.layers.add("S-DIM")
    xs, ys = D["xs"], D["ys"]
    for n, x in enumerate(xs):
        msp.add_line(P(k, x, ys[0] - 2.0), P(k, x, ys[-1] + 2.0), dxfattribs={"layer": "S-GRID"})
        msp.add_circle(P(k, x, ys[-1] + 2.5), 0.4 * s, dxfattribs={"layer": "S-GRID"})
        t = msp.add_text(str(n + 1), dxfattribs={"layer": "S-GRID", "height": 0.3 * s})
        t.set_placement(P(k, x - 0.1, ys[-1] + 2.4))
        note("GRID_AXIS")
    for n, y in enumerate(ys):
        msp.add_line(P(k, xs[0] - 2.0, y), P(k, xs[-1] + 2.0, y), dxfattribs={"layer": "S-GRID"})
        msp.add_circle(P(k, xs[0] - 2.5, y), 0.4 * s, dxfattribs={"layer": "S-GRID"})
        t = msp.add_text("ABCDEFG"[n], dxfattribs={"layer": "S-GRID", "height": 0.3 * s})
        t.set_placement(P(k, xs[0] - 2.6, y - 0.1))
        note("GRID_AXIS")
    for a, b in zip(xs, xs[1:]):
        dim = msp.add_linear_dim(base=P(k, a, ys[0] - 1.2), p1=P(k, a, ys[0]), p2=P(k, b, ys[0]),
                                 dxfattribs={"layer": "S-DIM"})
        dim.render()
        note("DIMENSION")


def profile(D):
    """The person-confirmed profile a QS would type: storey heights only (printed levels)."""
    return {"profile": f"SYNTHETIC_{D['seed']}", "confirmed_by": "synthetic generator (printed levels)",
            "manual_inputs": 2,
            "conventions": [{"id": f"STOREY_HEIGHT_{k}", "title": f"Storey height {k}", "kind": "number", "unit": "m",
                             "base": h, "low": h, "high": h, "provenance": "PRINTED_VALUE",
                             "source": "synthetic section", "rationale": "printed floor to floor"}
                            for k, h in D["heights"].items()]}


def generate(out_dir, seed, defects=False):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    D = design(seed)
    D["var"]["defects"] = defects if defects == "hard" else bool(defects)
    dxf = write_dxf(D, out / f"villa_{seed}.dxf")
    T = truth(D)
    T["defects_applied"] = D.get("defects_applied", {})
    (out / f"villa_{seed}.truth.json").write_text(json.dumps(T, indent=1, ensure_ascii=False, default=str))
    (out / f"villa_{seed}.profile.json").write_text(json.dumps(profile(D), indent=1))
    return dxf


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--defects"]
    for sd in args[1:]:
        print(generate(args[0], int(sd), defects="--defects" in sys.argv))
