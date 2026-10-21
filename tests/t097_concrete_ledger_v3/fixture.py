"""T-097 hand fixture: a synthetic structural villa (tools/synthetic_villa, design-driven, NOT a client drawing) with
the four cases CONCRETE_LEDGER_V3 changes drawn onto its ground-floor slab plan by hand rules from the DESIGN numbers:

  P  a planted column: a column outline of a scheduled column type drawn INSIDE a tagged beam's width, a quarter of the
     clear span from its start, long side along the beam; label 'P.C <b>x<h>' (cm) above the beam with a landing line
     and a leader to a circle round the column. V1 cuts the beam there (the untagged piece is held as an unlabelled
     span across a support); V3: one span, clear span x B x H.
  R1 a ring beam: two concentric faces, each four quarter arcs, radial gap = a scheduled beam width B; the beam's mark
     printed tangent to the outer face at 45 deg. Isolated: its concrete is the whole annulus pi (ro^2 - ri^2) x H.
  R2 a second ring, inner face one full CIRCLE, outer face four arcs, no mark: HELD, or OWNER_RULE with a passed rule.
  S  'SECTION A-A' on the schedule sheet: a dimensioned outline = the beam B x H (printed in the schedule unit) with an
     upstand w x h flush right on top; its cut line on the plan crosses one tagged span (view arrows + letters 'A').
     Upstand = w x h x that span's clear length.

Everything is placed in design metres and written through the generator's own sheet transform (units mm or m).
`mirror_dxf` mirrors a whole written drawing x -> -x (texts keep their reading direction mod 180)."""
from __future__ import annotations

import math

from tools import synthetic_villa as SV

UP_W, UP_H = 0.10, 0.15          # printed upstand (m)
R_IN = 1.00                      # inner ring radius (m)


def _s(D):
    return 1.0 if D["var"]["units"] == "m" else 1000.0


def P(D, sheet, x, y):
    return SV.to_drawing(D, sheet, x, y)


def plan(seed):
    """the design and the hand truth of the added cases (no engine)."""
    D = SV.design(seed)
    beams = SV.beams_of(D)
    rows = SV.schedule_rows(D)
    sched = {r["mark"]: (r["B"], r["H"]) for r in rows["BEAM"]}
    cols = {c: SV.COL_TYPES[int(c[1:]) - 1] for c in D["ctypes"]}
    ok = [b for b in beams if b["axis"] == "x" and b["tagged"] and b["type"] in sched and b["drawn_B"] == b["B"]
          and not b.get("cb")]
    # P: a tagged x span whose width equals the short side of a scheduled column type, longest clear span
    pl = None
    for b in sorted(ok, key=lambda b: -b["clear"]):
        ct = next((c for c, (cb, ch) in sorted(cols.items()) if abs(min(cb, ch) - b["B"]) < 1e-9 and
                   max(cb, ch) + 1.0 < 0.25 * b["clear"] * 2), None)
        if ct and b["line"] not in (0, len(D["ys"]) - 1):
            pl = (b, ct)
            break
    if pl is None:
        raise ValueError(f"seed {seed}: no span fits the planted-column case")
    b, ct = pl
    x0 = b["a"]["x"] + SV._dim(b["a"], "x") / 2
    x1 = b["b"]["x"] - SV._dim(b["b"], "x") / 2
    cw, cl = sorted(cols[ct])
    xc = x0 + 0.25 * (x1 - x0)
    planted = {"beam": b["type"], "B": b["B"], "H": b["H"], "y": b["a"]["y"], "x0": x0, "x1": x1, "xc": xc,
               "col": ct, "col_w": cw, "col_l": cl, "label": f"P.C {round(cw * 100)}x{round(cl * 100)}",
               "clear": x1 - x0, "v3_m3": (x1 - x0) * b["B"] * b["H"]}
    # S: a tagged span of scheduled width on another line (top-most first), cut at 30 % of its clear span
    cand = [x for x in ok if x["line"] != b["line"]]
    s = sorted(cand, key=lambda x: (-x["line"], x["a"]["x"]))[0]      # top-most other line, first span
    sx0 = s["a"]["x"] + SV._dim(s["a"], "x") / 2
    sx1 = s["b"]["x"] - SV._dim(s["b"], "x") / 2
    section = {"beam": s["type"], "B": s["B"], "H": s["H"], "y": s["a"]["y"], "x0": sx0, "x1": sx1,
               "xc": sx0 + 0.30 * (sx1 - sx0), "clear": sx1 - sx0, "w": UP_W, "h": UP_H,
               "v_m3": UP_W * UP_H * (sx1 - sx0)}
    # rings: the narrowest scheduled beam width; centres right of the grid
    mk, (B, H) = min(sched.items(), key=lambda kv: (kv[1][0], kv[0]))
    cx = D["xs"][-1] + 5.0
    rings = [{"c": (cx, D["ys"][-1] * 0.30), "ri": R_IN, "ro": R_IN + B, "mark": mk, "B": B, "H": H,
              "inner": "ARCS", "printed": True},
             {"c": (cx, D["ys"][-1] * 0.80), "ri": R_IN, "ro": R_IN + B, "mark": mk, "B": B, "H": H,
              "inner": "CIRCLE", "printed": False}]
    for r in rings:
        r["annulus_m2"] = math.pi * (r["ro"] ** 2 - r["ri"] ** 2)
        r["v_m3"] = r["annulus_m2"] * H
    return D, {"planted": planted, "section": section, "rings": rings, "unit": D["var"]["tags"]["unit"]}


def write(seed, path, *, cases=("P", "R", "S"), leader=True, print_h=True):
    """write the synthetic villa with the added cases; returns (D, truth). leader=False draws the planted-column
    label without its landing line and leader; print_h=False leaves the upstand height unprinted."""
    import ezdxf
    D, T = plan(seed)
    SV.write_dxf(D, path)
    doc = ezdxf.readfile(path)
    msp = doc.modelspace()
    L = D["var"]["layers"]
    s = _s(D)
    h = 0.15 * s

    def line(a, b, layer):
        msp.add_line(P(D, "GF", *a), P(D, "GF", *b), dxfattribs={"layer": layer})

    def text(sheet, val, x, y, rot=0.0, ht=h):
        t = msp.add_text(val, dxfattribs={"layer": L["text"], "height": ht, "rotation": rot})
        t.set_placement(P(D, sheet, x, y))

    if "P" in cases:
        p = T["planted"]
        y = p["y"]
        x0, y0 = P(D, "GF", p["xc"] - p["col_l"] / 2, y - p["col_w"] / 2)
        x1, y1 = P(D, "GF", p["xc"] + p["col_l"] / 2, y + p["col_w"] / 2)
        msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], close=True, dxfattribs={"layer": L["col"]})
        msp.add_circle(P(D, "GF", p["xc"], y), 0.45 * s, dxfattribs={"layer": L["text"]})
        lx, ly = p["xc"] - 1.6, y + 1.2                       # label anchor
        text("GF", p["label"], lx, ly)
        if leader:
            line((lx - 0.05, ly - 0.05), (lx + 1.30, ly - 0.05), L["text"])      # landing line under the label
            tip = (p["xc"] - 0.45 * math.cos(math.radians(45)), y + 0.45 * math.sin(math.radians(45)))
            line((lx + 1.30, ly - 0.05), tip, L["text"])                         # leader to the circle
    if "R" in cases:
        for r in T["rings"]:
            c = P(D, "GF", *r["c"])
            for k in range(4):
                msp.add_arc(c, r["ro"] * s, 90 * k, 90 * (k + 1), dxfattribs={"layer": L["beam"]})
                if r["inner"] == "ARCS":
                    msp.add_arc(c, r["ri"] * s, 90 * k, 90 * (k + 1), dxfattribs={"layer": L["beam"]})
            if r["inner"] == "CIRCLE":
                msp.add_circle(c, r["ri"] * s, dxfattribs={"layer": L["beam"]})
            if r["printed"]:
                a = math.radians(45)
                d = r["ro"] + 0.06
                text("GF", r["mark"], r["c"][0] + d * math.cos(a), r["c"][1] + d * math.sin(a), rot=135.0)
    if "S" in cases:
        S_ = T["section"]
        y = S_["y"]
        xc = S_["xc"]
        line((xc, y - 0.80), (xc, y + 0.80), L["text"])                          # cut line
        for yy in (y - 0.70, y + 0.70):
            line((xc - 0.05, yy), (xc + 0.35, yy), L["text"])                    # view arrows
            text("GF", "A", xc + 0.45, yy - 0.05, ht=0.20 * s)
        # the section view on the schedule sheet, drawn 1:1 in drawing units, printed in the schedule unit
        k = 1000.0 if T["unit"] == "mm" else 100.0
        W, Hh, w, hh = S_["B"], S_["H"], S_["w"], S_["h"]
        ox, oy = 25.0, 6.0
        pts = [(0, 0), (W, 0), (W, Hh + hh), (W - w, Hh + hh), (W - w, Hh), (0, Hh)]
        msp.add_lwpolyline([P(D, "SCHED", ox + x, oy + yv) for x, yv in pts], close=True,
                           dxfattribs={"layer": L["text"]})

        def dim(p1, p2, val, vertical, off):
            a, b = P(D, "SCHED", ox + p1[0], oy + p1[1]), P(D, "SCHED", ox + p2[0], oy + p2[1])
            base = (a[0] + off * s, a[1]) if vertical else (a[0], a[1] - off * s)
            dm = msp.add_linear_dim(base=base, p1=a, p2=b, angle=90 if vertical else 0, text=f"{val:g}",
                                    dxfattribs={"layer": L["text"]})
            dm.render()
        dim((0, 0), (W, 0), round(W * k, 6), False, 0.3)
        dim((0, 0), (0, Hh), round(Hh * k, 6), True, -0.3)
        dim((W - w, Hh + hh), (W, Hh + hh), round(w * k, 6), False, -0.3)
        if print_h:
            dim((W - w, Hh), (W - w, Hh + hh), round(hh * k, 6), True, -0.2)
        text("SCHED", "SECTION A-A", ox - 0.2, oy - 0.6, ht=0.20 * s)
    doc.saveas(path)
    return D, T


def mirror_dxf(src, dst):
    """the whole drawing mirrored x -> -x (every model-space entity transformed; ezdxf keeps texts readable)."""
    import ezdxf
    from ezdxf.math import Matrix44
    doc = ezdxf.readfile(src)
    m = Matrix44.scale(-1.0, 1.0, 1.0)
    for e in list(doc.modelspace()):
        try:
            e.transform(m)
        except (NotImplementedError, AttributeError, ezdxf.DXFError):
            raise
    doc.saveas(dst)
    return dst
