"""T-726 rules (research, unwired; every villa): binding a reference (freelancer) wall row to a drawn shaft / stair-well
face, and checking that a shaft face is carried once between the shaft line and the room lines beside it.

Physical element (ERS 2.1). A SHAFT / STAIR-HOUSE wall face is one plane of masonry seen from inside a vertical volume
with no slab across it (stair shaft, lift shaft, double-height well); it is ONE face from its lowest exposed floor to the
soffit above it (Q-72), split into storey bands only for reporting. An edge of the volume where no wall stands (a slab
edge with a railing, an open landing side) is not a face and carries no plaster.

R-T726-1 GROUP OF A REFERENCE ROW. In a measurement sheet whose rows carry a line total (I) and, at the end of a group, a
         group subtotal (J), a row belongs to the group closed by the next J at or below it; the group is ONE element,
         named by its first row. A row without its own element name inside a group (a 'continued' row) is reconciled
         inside that element's bridge, never as an element of its own. The group subtotal must equal the sum of its I
         cells (tolerance TOL_M2), otherwise the grouping is NOT_ESTABLISHED and nothing is bound.
R-T726-2 FACE BINDING. A reference row W x H binds to a drawn face of its element when the face width is within
         max(0.10 m, 1 %) of W AND (the face's exposed height range from its merged face model, or an interval between two
         PRINTED levels that lie inside the element, used only when no face height hits and then only for a single
         width-matching face) is within max(0.05 m, 1 %) of H. One face: BOUND; several: AMBIGUOUS;
         none in scope: NO_FACE. Intervals that use a printed level outside the element (exterior grade, a lower roof
         beside another part of the building) are reported as OUT_OF_SCOPE matches and never bind. A NO_FACE row is a
         named residual on the reference side: it is never added to the engine and the engine side is never set to 0.
R-T726-3 ONCE ACROSS LINES. For a room line whose outline chain walks shaft faces, chain perimeter - room face length =
         the shaft faces it walks + its open (no-wall) edges, within TOL_LM. Excess on the room side (room face longer than
         the chain minus those): COUNTED_TWICE; deficit: DROPPED; else ONCE. An open edge carries no plaster (it is
         never part of the room face).

Statuses (WORKFLOW_CONTROLS s.5): DRAWING-CONFIRMED (by handle), HELD, UNKNOWN; results BOUND, AMBIGUOUS, NO_FACE,
OUT_OF_SCOPE, ONCE, COUNTED_TWICE, DROPPED, NOT_ESTABLISHED.
"""
from __future__ import annotations

import math
from decimal import ROUND_HALF_EVEN, Decimal

D = Decimal
TOL_M2 = D("0.005")
TOL_LM = D("0.10")          # one wall-thickness return / outline-clip rounding; below a plaster bead's width x height


def q6(x):
    return D(str(x)).quantize(D("0.000001"), rounding=ROUND_HALF_EVEN)


def _num(x, what):
    if x is None or isinstance(x, bool):
        raise ValueError(f"{what}: missing")
    try:
        v = D(str(x))
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"{what}: not a number: {x!r}") from exc
    if not v.is_finite():
        raise ValueError(f"{what}: not finite")
    return v


# ---- R-T726-1 --------------------------------------------------------------------------------------------------------
def groups(rows):
    """rows: [(row_no, I or None, J or None)] in sheet order. Returns [{rows, sum_I, J, status}] for every closed group.
    Rows before the first I are ignored; a group closes at the first row with a J."""
    out, cur = [], []
    for no, i, j in rows:
        if i is not None:
            cur.append((no, _num(i, f"row {no} I")))
        if j is not None:
            jv = _num(j, f"row {no} J")
            s = sum((v for _, v in cur), D(0))
            out.append({"rows": [n for n, _ in cur], "sum_I": q6(s), "J": q6(jv),
                        "status": "ESTABLISHED" if cur and abs(s - jv) <= TOL_M2 else "NOT_ESTABLISHED"})
            cur = []
    return out


def group_of(rows, row_no):
    for g in groups(rows):
        if row_no in g["rows"]:
            return g
    return None


# ---- R-T726-2 --------------------------------------------------------------------------------------------------------
def tol_w(w):
    return max(D("0.10"), abs(w) * D("0.01"))


def tol_h(h):
    return max(D("0.05"), abs(h) * D("0.01"))


def bind(width, height, faces, levels_in, levels_out):
    """faces: [{id, width, h_lo, h_hi}] (h_lo / h_hi None = height not established); levels_in / levels_out: printed
    level values inside / outside the element. Returns (result, detail)."""
    W, H = _num(width, "row width"), _num(height, "row height")
    if W <= 0 or H <= 0:
        raise ValueError("row width / height must be > 0")
    tw, th = tol_w(W), tol_h(H)
    wide = [f for f in faces if abs(_num(f["width"], f["id"]) - W) <= tw]
    hits, near = [], []
    for f in wide:
        if f.get("h_lo") is None or f.get("h_hi") is None:
            near.append({"face": f["id"], "height": None, "why": "height HELD"})
            continue
        lo, hi = _num(f["h_lo"], f["id"]), _num(f["h_hi"], f["id"])
        if lo > hi:
            raise ValueError(f"{f['id']}: h_lo above h_hi")
        gap = D(0) if lo <= H <= hi else min(abs(H - lo), abs(H - hi))
        (hits if gap <= th else near).append({"face": f["id"], "height": [str(lo), str(hi)], "gap_m": str(q6(gap))})

    def pairs(vals):
        v = sorted({_num(x, "level") for x in vals})
        return [(a, b) for i, a in enumerate(v) for b in v[i + 1:] if abs((b - a) - H) <= th]
    lin = [str(x) for x in levels_in]
    inside = pairs(lin)
    outside = [p for p in pairs(lin + [str(x) for x in levels_out]) if p not in inside]
    detail = {"tol_w": str(tw), "tol_h": str(th), "width_matches": [f["id"] for f in wide], "height_hits": hits,
              "nearest": sorted(near, key=lambda r: (r.get("gap_m") is None, D(r.get("gap_m") or 0))),
              "in_scope_level_intervals": [[str(a), str(b)] for a, b in inside],
              "out_of_scope_level_intervals": [[str(a), str(b)] for a, b in outside]}
    # a full-height hit names its face; a printed-level interval only names a PART of a width-matching face, so it
    # binds only when no face hits, and only to a single width-matching face (several -> which one is not drawn)
    n = len(hits) if hits else (len(wide) if inside else 0)
    if n == 0:
        return ("NO_FACE" if not outside else "NO_FACE (OUT_OF_SCOPE matches only)"), detail
    return ("BOUND" if n == 1 else "AMBIGUOUS"), detail


# ---- R-T726-3 --------------------------------------------------------------------------------------------------------
def once(chain_lm, room_face_lm, shaft_faces_walked_lm, open_edges_lm):
    c, f = _num(chain_lm, "chain"), _num(room_face_lm, "room face")
    s = sum((_num(x, "shaft face") for x in shaft_faces_walked_lm), D(0))
    o = sum((_num(x, "open edge") for x in open_edges_lm), D(0))
    for v, w in ((c, "chain"), (f, "room face"), (s, "shaft faces"), (o, "open edges")):
        if v < 0:
            raise ValueError(f"{w} negative")
    if s + o > c:
        raise ValueError("walked shaft faces + open edges exceed the chain")
    expect = c - s - o
    d = f - expect
    res = "ONCE" if abs(d) <= TOL_LM else ("COUNTED_TWICE" if d > 0 else "DROPPED")
    return res, {"expected_room_face_lm": str(q6(expect)), "room_minus_expected_lm": str(q6(d))}


def pct(a, b):
    a, b = _num(a, "a"), _num(b, "b")
    if b == 0:
        raise ValueError("division by zero")
    return q6((a / b - 1) * 100).quantize(D("0.01"))


def finite(x):
    return isinstance(x, (int, float)) and math.isfinite(x)
