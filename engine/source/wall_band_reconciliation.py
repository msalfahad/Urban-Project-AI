"""WALL_BAND_RECONCILIATION (generic): independent wall-length methods and the classified disagreement.

    METHOD A  the engine's own wall topology / bands (established + ambiguous, with column overlap recorded)
    METHOD B  nearest parallel-face pairing of raw wall lines at a nominal width (pair_parallel_faces)
    METHOD C  room-boundary / adjacency reconstruction (optional - supplied by the caller)
    METHOD D  layer / width classifier (width histogram of the pairs)

Each Method-B interval is classified by local evidence:
    COLUMN_OVERLAP_POLICY      the interval runs through a column outline
    OPENING_SPAN               the interval crosses an opening symbol (door / window extent)
    DUPLICATE_FACE             a face already used by a longer pair over the same stretch
    PAIRED_WALL                otherwise
and the per-floor difference A vs B is split into
    URBAN_AMBIGUOUS_NOT_MEASURED, COLUMN_OVERLAP_POLICY, OPENING_SPAN, DUPLICATE_FACE, URBAN_MISSED_OR_UNRESOLVED.
Nothing is averaged; no method overwrites another. Stdlib only.
"""

from __future__ import annotations

import math

PAIRED_WALL, COLUMN_OVERLAP, OPENING_SPAN, DUPLICATE_FACE = (
    "PAIRED_WALL", "COLUMN_OVERLAP_POLICY", "OPENING_SPAN", "DUPLICATE_FACE")
CLASSES = ("URBAN_MISSED", "ORACLE_FALSE_PAIR", "WIDTH_MISCLASSIFIED", "COLUMN_OVERLAP_POLICY", "DUPLICATE_FACE",
           "FINISH_LINE_FALSE_POSITIVE", "UNRESOLVED")


def _unit(seg):
    x1, y1, x2, y2 = seg
    L = math.hypot(x2 - x1, y2 - y1)
    return ((x2 - x1) / L, (y2 - y1) / L, L) if L else (0.0, 0.0, 0.0)


def pair_parallel_faces(segments, width, *, tol=15.0, min_overlap=200.0, angle_tol=0.01, min_len=100.0):
    """segments: [(id, x1, y1, x2, y2)] in drawing units. Returns intervals [{a, b, width, length, p0, p1}] where
    p0-p1 is the overlap on face a. A face may pair with several partners (classified later)."""
    segs = []
    for sid, x1, y1, x2, y2 in segments:
        ux, uy, L = _unit((x1, y1, x2, y2))
        if L >= min_len:
            segs.append((sid, x1, y1, ux, uy, L, x2, y2))
    out = []
    for i, a in enumerate(segs):
        for b in segs[i + 1:]:
            if abs(a[3] * b[4] - a[4] * b[3]) > angle_tol:
                continue
            d = abs((b[1] - a[1]) * (-a[4]) + (b[2] - a[2]) * a[3])
            if abs(d - width) > tol:
                continue
            t1 = (b[1] - a[1]) * a[3] + (b[2] - a[2]) * a[4]
            t2 = (b[6] - a[1]) * a[3] + (b[7] - a[2]) * a[4]
            lo, hi = max(0.0, min(t1, t2)), min(a[5], max(t1, t2))
            if hi - lo > min_overlap:
                out.append({"a": a[0], "b": b[0], "width": round(d, 1), "length": hi - lo,
                            "p0": (a[1] + a[3] * lo, a[2] + a[4] * lo), "p1": (a[1] + a[3] * hi, a[2] + a[4] * hi),
                            "axis": (a[3], a[4])})
    return out


def _overlap_on(iv, box):
    """Length of the interval p0-p1 inside an axis-aligned box (x0, y0, x1, y1)."""
    (x0, y0), (x1, y1) = iv["p0"], iv["p1"]
    L = math.hypot(x1 - x0, y1 - y0)
    if L == 0:
        return 0.0
    t0, t1 = 0.0, 1.0
    for p, d, lo, hi in ((x0, x1 - x0, box[0], box[2]), (y0, y1 - y0, box[1], box[3])):
        if abs(d) < 1e-12:
            if p < lo or p > hi:
                return 0.0
            continue
        a, b = (lo - p) / d, (hi - p) / d
        t0, t1 = max(t0, min(a, b)), min(t1, max(a, b))
    return max(0.0, t1 - t0) * L


def classify(intervals, *, column_boxes=(), opening_boxes=(), buffer=None):
    """Split every interval's length into PAIRED_WALL / COLUMN_OVERLAP_POLICY / OPENING_SPAN / DUPLICATE_FACE."""
    buf = buffer if buffer is not None else 0.0
    grow = lambda b: (b[0] - buf, b[1] - buf, b[2] + buf, b[3] + buf)  # noqa: E731
    ordered = sorted(enumerate(intervals), key=lambda t: -t[1]["length"])
    used = {}                                   # face id -> list of (t0, t1) along its own axis (rounded coords)
    out = [None] * len(intervals)
    for idx, iv in ordered:
        L = iv["length"]
        col = min(L, sum(_overlap_on(iv, grow(b)) for b in column_boxes))
        opn = min(L - col, sum(_overlap_on(iv, grow(b)) for b in opening_boxes))
        key = (round(iv["p0"][0]), round(iv["p0"][1]), round(iv["p1"][0]), round(iv["p1"][1]))
        dup = 0.0
        for face in (iv["a"], iv["b"]):
            if any(k == key or _same_stretch(k, key) for k in used.get(face, [])):
                dup = L
        used.setdefault(iv["a"], []).append(key)
        used.setdefault(iv["b"], []).append(key)
        if dup:
            parts = {DUPLICATE_FACE: L}
        else:
            parts = {PAIRED_WALL: L - col - opn, COLUMN_OVERLAP: col, OPENING_SPAN: opn}
        out[idx] = dict(iv, parts={k: v for k, v in parts.items() if v > 0})
    return out


def _same_stretch(k1, k2, tol=5.0):
    return all(abs(a - b) <= tol for a, b in zip(k1, k2))


def totals(classified, scale=1000.0):
    agg = {}
    for iv in classified:
        for k, v in iv["parts"].items():
            agg[k] = agg.get(k, 0.0) + v / scale
    return {k: round(v, 3) for k, v in sorted(agg.items())}


def explain(method_a, method_b_totals):
    """method_a: {established_m, ambiguous_m, column_overlap_m}; method_b_totals: totals(...) of one floor/width.
    Returns the classified difference B - A (positive = B longer)."""
    b_wall = method_b_totals.get(PAIRED_WALL, 0.0)
    a_meas = method_a["established_m"]
    diff = b_wall - a_meas
    amb = min(max(diff, 0.0), method_a.get("ambiguous_m", 0.0))
    rest = diff - amb
    return {"method_a_established_m": a_meas, "method_a_ambiguous_m": method_a.get("ambiguous_m", 0.0),
            "method_b_paired_wall_m": b_wall, "difference_m": round(diff, 3),
            "URBAN_AMBIGUOUS_NOT_MEASURED": round(amb, 3),
            "COLUMN_OVERLAP_POLICY": method_b_totals.get(COLUMN_OVERLAP, 0.0),
            "OPENING_SPAN": method_b_totals.get(OPENING_SPAN, 0.0),
            "DUPLICATE_FACE": method_b_totals.get(DUPLICATE_FACE, 0.0),
            "URBAN_MISSED_OR_UNRESOLVED": round(rest, 3)}
