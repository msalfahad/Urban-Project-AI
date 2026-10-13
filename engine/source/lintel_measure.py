"""LINTEL MEASURE (M4) - masonry-wall openings of an architectural floor plan and the lintels a printed lintel
schedule gives them (generic; stdlib + engine.source.opening_census / lintel_qto). No layer name is read: the wall
layers are the ones whose lines pair at a wall thickness.

    wall_layers(segments, unit_m)       layers whose own lines form wall bands (two faces 0.10 - 0.45 m apart over
                                        at least 0.3 m), keeping those with at least 20 % of the best layer's bands
    openings(segments, unit_m, layers, columns)
                                        opening_census on the wall layers: a gap in a wall band where BOTH faces stop,
                                        each end a masonry jamb, a column jamb or a closure; anything else is rejected;
                                        a column standing inside the gap cuts it at its face (a column jamb)
    beam_over(opening, beam_polys)      FULL / PARTIAL / NONE: a structural beam band of the slab above covers the
                                        opening strip (then the beam carries the wall: no separate lintel)
    lintel(opening, rows, ...)          the schedule row by opening width (lintel_qto.row_for_width, bounds inclusive,
                                        never rounded into a band), the section B (wall) x D (row), the length opening +
                                        a bearing on each masonry jamb (none on a column jamb), bars and stirrups
Not every opening gets a lintel: one under a beam, one wider than the schedule, one between two bands of it, or
one with an unbounded end is reported with its reason, never measured.
"""

from __future__ import annotations

import math
from collections import Counter

from engine.source import lintel_qto as LQ
from engine.source import member_detection as MD
from engine.source import opening_census as OC
from engine.source import opening_gaps as OG

POLICY_ID = "LINTEL_MEASURE_V1"


def _segs(segments, layers):
    return [(s["id"], tuple(s["a"]), tuple(s["b"])) for s in segments if s["layer"] in layers]


def wall_layers(segments, unit_m, *, t_m=(0.10, 0.45), share=0.2):
    k = 1.0 / unit_m / 1000.0                                  # drawing units per mm
    by = {}
    for s in segments:
        if MD._layer_role(s["layer"]) in MD.ANNOTATION_ROLES + ("COLUMN",):
            continue
        by.setdefault(s["layer"], []).append(s)
    score = {}
    for lay, ss in by.items():
        fl = OC.face_lines(_segs(ss, {lay}), ang_res_deg=0.5, off_tol=2.0 * k, join_tol=5.0 * k, min_len=100.0 * k)
        score[lay] = len(OC.wall_bands(fl, t_m[0] / unit_m, t_m[1] / unit_m, min_overlap=0.3 / unit_m))
    best = max(score.values(), default=0)
    return sorted(l for l, v in score.items() if best and v >= max(3, share * best)), score


def openings(segments, unit_m, layers, columns=(), *, t_m=(0.10, 0.45), min_gap_m=0.5, tol="LEGACY"):
    """the census runs on each wall layer by itself (a composite wall drawn on several layers keeps a line between
    its faces, which a combined census would refuse); closures (jamb lines, perpendicular faces) come from every
    non-annotation layer. Openings found twice (one gap, two layers) are kept once."""
    k = 1.0 / unit_m / 1000.0
    # S6: LEGACY merges the two wall faces' covers within 1.0 drawing unit (1 mm only in a mm drawing);
    # UNIT_RELATIVE merges within 1 mm in any unit (identical at mm: 1e-3 / 0.001 == 1.0). opening_gaps.band_gaps
    # calls the frozen opening_census.band_gaps itself at 1.0
    merge_tol = 1.0 if tol == "LEGACY" else 1e-3 / unit_m
    closures = [(s["id"], tuple(s["a"]), tuple(s["b"])) for s in segments
                if MD._layer_role(s["layer"]) not in MD.ANNOTATION_ROLES]
    obst = [(f"COL{i}", MD.box_poly(c)) for i, c in enumerate(columns)]
    out, rej = [], Counter()
    for lay in layers:
        fl = OC.face_lines(_segs(segments, {lay}), ang_res_deg=0.5, off_tol=2.0 * k, join_tol=5.0 * k,
                           min_len=100.0 * k)
        bands = OC.wall_bands(fl, t_m[0] / unit_m, t_m[1] / unit_m, min_overlap=0.3 / unit_m)
        for b in bands:
            gaps = OG.band_gaps(b, min_gap=min_gap_m / unit_m, jamb_tol=30.0 * k, obstacles=obst,
                                column_reach=60.0 * k, closures=closures, merge_tol=merge_tol)
            for g in [x for g0 in gaps for x in _split_at_columns(g0, b, obst, min_gap_m / unit_m)]:
                if g["state"] != OC.OPENING:
                    rej[g["state"]] += 1
                    continue
                lo, hi = sorted((b["A"]["off"], b["B"]["off"]))
                u, n = b["u"], b["n"]
                sm, om = (g["s0"] + g["s1"]) / 2, (lo + hi) / 2
                c = (u[0] * sm + n[0] * om, u[1] * sm + n[1] * om)
                if any(math.dist(c, o["centre"]) * unit_m <= 0.2 and abs(o["width_m"] - g["width"] * unit_m) <= 0.05
                       for o in out):
                    rej["DUPLICATE_ON_ANOTHER_LAYER"] += 1
                    continue
                out.append({"opening_id": f"OP-{len(out) + 1:03d}", "band_id": b["band_id"], "layer": lay,
                            "u": u, "n": n, "s0": g["s0"], "s1": g["s1"], "o0": lo, "o1": hi,
                            "width_m": g["width"] * unit_m, "wall_t_m": g["t"] * unit_m,
                            "start_jamb": g["start_jamb"], "end_jamb": g["end_jamb"], "centre": c,
                            "split_at_column": g.get("split_at_column", False)})
    return out, dict(rej)


def _split_at_columns(g, band, obst, min_gap):
    """a column standing inside a wall gap (the wall faces resume only behind it) bounds the opening at its near
    face: the gap is cut at every such column, each cut end a COLUMN_JAMB; pieces narrower than min_gap are dropped
    (the wall reach between a jamb and a column face is not an opening)."""
    u, n = band["u"], band["n"]
    lo, hi = sorted((band["A"]["off"], band["B"]["off"]))
    cuts = []
    for _, poly in obst:
        ss = [p[0] * u[0] + p[1] * u[1] for p in poly]
        oo = [p[0] * n[0] + p[1] * n[1] for p in poly]
        if max(oo) <= lo or min(oo) >= hi:
            continue
        a, b = max(min(ss), g["s0"]), min(max(ss), g["s1"])
        if b - a > 1e-9:
            cuts.append((a, b))
    if not cuts:
        return [g]
    cuts.sort()
    out, s, jamb = [], g["s0"], g["start_jamb"]
    for a, b in cuts + [(g["s1"], g["s1"])]:
        end = g["end_jamb"] if a >= g["s1"] else OC.COLUMN_JAMB
        if a - s >= min_gap:
            st = OC.OPENING if OC.UNBOUNDED not in (jamb, end) else OC.REJECTED
            out.append(dict(g, s0=s, s1=a, width=a - s, start_jamb=jamb, end_jamb=end, state=st,
                            split_at_column=True))
        s, jamb = max(s, b), OC.COLUMN_JAMB
    return out


def beam_over(op, beam_polys):
    """FULL when one beam band covers at least half the wall thickness over the whole opening width."""
    u, n = op["u"], op["n"]
    strip = {"s0": op["s0"], "s1": op["s1"], "o0": op["o0"], "o1": op["o1"]}
    best = "NONE"
    for poly in beam_polys:
        ss = [x * u[0] + y * u[1] for x, y in poly]
        oo = [x * n[0] + y * n[1] for x, y in poly]
        rel = LQ.strip_relation(strip, {"s0": min(ss), "s1": max(ss), "o0": min(oo), "o1": max(oo)})["relation"]
        if rel == LQ.FULL:
            return "FULL"
        if rel == LQ.PARTIAL:
            best = "PARTIAL"
    return best


def lintel(op, rows, *, bearing_m=(0.15, 0.20, 0.25), cover_m=(0.04, 0.025, 0.02), width_unit_per_mm=0.1):
    """-> {state, row, B, D, length (triple), concrete (triple), bars [(role, n, dia, length triple)], stirrups} or a
    reason. rows: [{row_id, lo, hi (printed width unit), D_m, bottom (n, d), top (n, d), stirrup_rate (n, d)}]."""
    state, row = LQ.row_for_width(rows, op["width_m"] * 1000.0, unit_per_mm=width_unit_per_mm)
    if state != LQ.IN_ROW:
        return {"state": state}
    B, D = op["wall_t_m"], row["D_m"]
    ends = [j for j in (op["start_jamb"], op["end_jamb"]) if j != OC.COLUMN_JAMB]
    L = tuple(op["width_m"] + len(ends) * b for b in bearing_m)
    conc = tuple(B * D * x for x in L)
    bars = []
    for role in ("bottom", "top"):
        if row.get(role):
            n, d = row[role]
            bars.append((role.upper(), n, d, tuple(max(x - 2 * c, 0.0) for x, c in zip(L, cover_m))))
    st = None
    if row.get("stirrup_rate"):
        r, d = row["stirrup_rate"]
        st = {"rate_per_m": r, "dia_mm": d, "count": tuple(math.ceil(r * x - 1e-9) for x in L)}
    return {"state": "MEASURED", "row": row["row_id"], "B_m": B, "D_m": D, "length_m": L, "concrete_m3": conc,
            "bars": bars, "stirrups": st, "bearing_ends": len(ends)}


def policy_record():
    return {"policy": POLICY_ID, "rule": "a lintel only for a jambed opening in a masonry wall band, with no structural "
                                         "beam over it, inside a printed schedule band; every other opening is "
                                         "reported with its reason"}
