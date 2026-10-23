"""T-226 blockwork resolution 2/4: block-wall height pieces, column-containing walls (D-12) and the column / junction
audit. Pure rules (any villa; research module, imported by nothing in engine/; no drawing content, no default value).

Physical element: one height piece = a stretch of a block wall under ONE member above it (beam, slab or nothing).
Owner Q-60 A: block height = storey height (slab top to slab top) - depth of what sits on that stretch. Statuses are the
standard ones (WORKFLOW_CONTROLS s.5) and map to the owner classes of BLOCKWORK_RESOLUTION_PROGRAMME.md s.2.

Rule UP-MAS-HPIECE-001 (proposed, T-226; any villa). Which drawn evidence closes a height piece:
  R1  nothing drawn above (no beam band, no slab underside, an open dome / void)  -> HELD, never a default height.
  R2  a member is drawn but carries no mark of its own (unlabelled span, piece past a column)  -> HELD; the depths
      of the labelled members it could belong to are a BOUND (min .. max m2), never a value (owner Q-61 C(4)).
  R3  two marks on one piece with different depths (e.g. 'CB3' and 'B3 (with stair)')  -> CONFLICT range, HELD
      (owner Q-61 C(2)); a designer item, never the larger or the smaller end.
  R4  one mark, and every depth printed for that mark agrees  -> the depth closes the piece (DRAWING-CONFIRMED =
      SOURCE-SUPPORTED PENDING INDEPENDENT CHECK), EVEN WHEN the member's WIDTH is in CONFLICT (schedule vs drawn
      outline, owner Q-61 C(1)): the masonry height depends on the depth only. The width conflict stays open for the
      concrete line and is carried on the piece as a dependency (re-open if the designer re-identifies the member).
  R5  one mark whose printed depths disagree (schedule vs section) -> CONFLICT range, HELD.
  R6  a drawing that does not outline the member separately (an architectural section hatching masonry and concrete
      alike) is NOT a depth source: it neither confirms nor contradicts a printed depth and is refused as one.
  R7  a slab-plan face that merges a beam band and the column under it ('BEAM_OR_COLUMN') is not 'nothing drawn':
      the stretch inside the column-BELOW outline is column (no block; cut from the run), the stretch under the band
      beside the column is under that beam (R4 on its mark); only a stretch under neither is R1.

Rule UP-MAS-D12-001 (proposed, T-226; any villa). A wall run with a column inside it, where the architecture prints
one thickness and a structural note asks for the column thickness: gross m2 is unchanged (the column stretch is
concrete and out of the run either way); only m3 and the block product differ. Both are carried as a CONFLICT range
(drawn .. note), never chosen; a thickness with no product of that block type (e.g. 0.25 m black where the owner's
black blocks are 0.15 / 0.20 m, Q-60) is flagged NO_STANDARD_PRODUCT for the designer.

Rule UP-MAS-COLCUT-001 (proposed check, T-226; any villa). In every run whose centreline crosses a column outline,
the run length = centreline - the stretch inside columns + only explained additions (an L corner square = the
partner wall's half thickness per L end, a T-stem seat up to the through wall's half thickness, a doorway at a free
end). A residual near the in-column length means the column was counted as block (refused).
"""
from __future__ import annotations

DC, AOA, HELD, UNKNOWN = "DRAWING-CONFIRMED", "ASSUMED — OWNER-APPROVED", "HELD", "UNKNOWN"
TOL = 1e-6
MAX_STOREY_M = 8.0
MAX_DEPTH_M = 2.0
CLOSES = "CLOSED"
NOT_A_SOURCE = "NOT_A_DEPTH_SOURCE"


def _pos(v, what, cap):
    if v is None:
        return None
    v = float(v)
    if not (0 < v <= cap):
        raise ValueError(f"{what} {v} outside (0, {cap}]")
    return v


def depth_sources(sources):
    """Keep only real depth sources. Each source: {'kind': 'SCHEDULE'|'SECTION'|'DETAIL'|'ARCH_SECTION_NO_OUTLINE',
    'depth_m': float or None}. R6: a drawing that does not outline the member is refused as a depth source."""
    keep, refused = [], []
    for s in sources or ():
        k = s.get("kind")
        if k not in ("SCHEDULE", "SECTION", "DETAIL", "ARCH_SECTION_NO_OUTLINE"):
            raise ValueError(f"unknown depth source kind {k!r}")
        if k == "ARCH_SECTION_NO_OUTLINE":
            refused.append(s)
            continue
        d = _pos(s.get("depth_m"), "depth", MAX_DEPTH_M)
        if d is not None:
            keep.append({**s, "depth_m": d})
    return keep, refused


def resolve_piece(piece, storey_m):
    """One height piece -> {status, height_m (or None), bounds_m (or None), rule, why}.
    piece: {length_m, kind ('BEAM'|'SLAB'|'NONE'), marks [str], depth_sources [...], width_conflict (bool),
            candidate_depths_m [float] (R2: the labelled neighbours), mark_depths_m {mark: depth} (R3)}."""
    f2f = _pos(storey_m, "storey height", MAX_STOREY_M)
    L = _pos(piece.get("length_m"), "piece length", 50.0)
    kind = piece.get("kind")
    if kind not in ("BEAM", "SLAB", "NONE"):
        raise ValueError(f"member kind {kind!r}")
    if f2f is None:
        return {"status": HELD, "height_m": None, "bounds_m": None, "rule": "-", "why": "storey height not established"}
    if kind == "NONE":
        return {"status": HELD, "height_m": None, "bounds_m": None, "rule": "R1",
                "why": "nothing drawn above this stretch: Q-60 A has nothing to stop at (never a default height)"}
    marks = [m for m in (piece.get("marks") or []) if m]

    def h(d):
        if d >= f2f - TOL:
            raise ValueError(f"depth {d} not below storey {f2f}")
        return round(f2f - d, 6)

    def bounds(ds):
        hs = sorted(h(d) for d in ds)
        return (round(L * hs[0], 6), round(L * hs[-1], 6)), (hs[0], hs[-1])

    if kind == "BEAM" and not marks:
        c = [_pos(d, "candidate depth", MAX_DEPTH_M) for d in piece.get("candidate_depths_m") or []]
        b, hr = bounds(c) if c else (None, None)
        return {"status": HELD, "height_m": None, "bounds_m": b, "height_range_m": hr, "rule": "R2",
                "why": "member drawn with no mark of its own: candidate depths are a bound, never a value (Q-61 C(4))"}
    md = piece.get("mark_depths_m") or {}
    if kind == "BEAM" and len(set(marks)) > 1:
        ds = sorted({_pos(md[m], "mark depth", MAX_DEPTH_M) for m in marks if md.get(m) is not None})
        if len(ds) > 1 or len(ds) < len(set(marks)):
            b, hr = bounds(ds) if ds else (None, None)
            return {"status": HELD, "height_m": None, "bounds_m": b, "height_range_m": hr, "rule": "R3",
                    "why": "two marks on one member with different (or unknown) depths: CONFLICT range for the "
                           "designer (Q-61 C(2)), never an end of it"}
    keep, refused = depth_sources(piece.get("depth_sources"))
    if not keep:
        return {"status": HELD, "height_m": None, "bounds_m": None, "rule": "R6" if refused else "-",
                "why": "no printed depth" + (" (an architectural section without the member's own outline is not "
                                             "a depth source)" if refused else "")}
    ds = sorted({s["depth_m"] for s in keep})
    if len(ds) > 1:
        b, hr = bounds(ds)
        return {"status": HELD, "height_m": None, "bounds_m": b, "height_range_m": hr, "rule": "R5",
                "why": "printed depths of one member disagree: CONFLICT range, never an end"}
    note = ("width CONFLICT open (schedule vs drawn outline, Q-61 C(1)): does not enter the masonry height; re-open if "
            "the designer re-identifies the member") if piece.get("width_conflict") else ""
    return {"status": DC, "height_m": h(ds[0]), "bounds_m": None, "rule": "R4", "depth_m": ds[0],
            "why": f"{f2f} - {ds[0]} (one mark, printed depth agrees on every source)" + (f"; {note}" if note else ""),
            "dependency": note}


def split_face(in_column_below, under_band, mark=None):
    """R7: what sits over a stretch that a merged beam / column face covers. Returns 'COLUMN' (no block there),
    'BEAM' (under the band of `mark`: resolve with R4) or 'NONE' (R1)."""
    if in_column_below:
        return "COLUMN"
    if under_band:
        if not mark:
            return "BEAM_UNLABELLED"          # R2
        return "BEAM"
    return "NONE"


# ------------------------------------------------------------------------------------------------ D-12
def d12_range(net_m2, t_drawn_m, t_col_m, block_type, products=None):
    """m3 of a column-containing wall at the drawn thickness and at the note's (column) thickness: a CONFLICT range,
    never chosen. Gross / net m2 are not changed. products: {block_type: [thicknesses]} that exist (owner Q-60 /
    supplier sheet); a note thickness with no product is flagged."""
    td = _pos(t_drawn_m, "drawn thickness", 1.0)
    tc = _pos(t_col_m, "column thickness", 1.0)
    prods = products if products is not None else {"BLACK": (0.15, 0.20), "WHITE": (0.10, 0.15, 0.20, 0.25, 0.30)}
    flag = []
    if block_type not in prods:
        flag.append("BLOCK_TYPE_HELD")
    elif not any(abs(tc - x) < 1e-6 for x in prods[block_type]):
        flag.append("NO_STANDARD_PRODUCT")
    if net_m2 is None:
        return {"status": HELD, "m3_drawn": None, "m3_note": None, "d_m3": None, "flags": flag + ["NET_HELD"],
                "why": "net not formed: m3 range not formed (never 0)"}
    n = float(net_m2)
    if n < 0:
        raise ValueError("negative net")
    a, b = round(n * td, 6), round(n * tc, 6)
    if abs(td - tc) < 1e-9:
        return {"status": "NO_CONFLICT", "m3_drawn": a, "m3_note": b, "d_m3": 0.0, "flags": flag,
                "why": "drawn thickness = column thickness"}
    return {"status": "CONFLICT", "m3_drawn": a, "m3_note": b, "d_m3": round(b - a, 6), "flags": flag,
            "why": "architecture prints one thickness, the structural note asks for the column thickness: range, "
                   "never chosen (designer D-12)"}


# ------------------------------------------------------------------------------------------------ column cut audit
def column_cut(centreline_m, in_columns_m, run_m, ends, partner_half_t_m=(0.1,), free_end_doorway_m=0.0, tol=0.003):
    """UP-MAS-COLCUT-001: residual = run - (centreline - in columns) - free-end doorways must be a sum of one explained
    addition per L / T-stem end (0 or a partner's half thickness). Returns (status, residual_m)."""
    if min(centreline_m, in_columns_m, run_m, free_end_doorway_m) < 0:
        raise ValueError("negative length")
    res = round(run_m - (centreline_m - in_columns_m) - free_end_doorway_m, 6)
    n = sum(1 for e in ends if e in ("L", "T_STEM"))
    opts = {0.0}
    for _ in range(n):
        opts = {round(a + b, 6) for a in opts for b in (0.0,) + tuple(partner_half_t_m)}
    if any(abs(res - o) <= tol for o in opts):
        return ("COLUMN_CUT_ONCE" if in_columns_m > tol else "NO_COLUMN"), res
    if in_columns_m > tol and abs(res - in_columns_m) <= max(tol, 0.25 * in_columns_m):
        return "COLUMN_COUNTED_AS_BLOCK", res
    return "UNEXPLAINED", res
