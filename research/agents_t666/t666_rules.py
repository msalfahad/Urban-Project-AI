"""T-666 rules (research, unwired): one owner per junction square of an unlabelled beam piece, and one owner for a
boundary element on a stretch it shares in plan with a building ground beam. Any villa.

R-T666-1 ONE OWNER PER JUNCTION SQUARE (beam piece ends). At each end of a beam piece the square where it meets another
    member (piece width x the other member's width in plan) has exactly one owner line, decided in this order:
    (a) COLUMN: the square lies inside a column outline -> the column owns it (UP-CONC-JOINT-001: the column owns the
        joint prism to the slab top; every beam is net of it); the piece ends at the column face.
    (b) THROUGH MEMBER: the square lies inside the measured extent of another line (its stated basis bills it: a span
        between its own supports that covers the square) -> that line owns it; the piece ends at that member's near
        face. If the piece may be deeper than the through member, the part of the piece below the through member's
        soffit inside its footprint is an exposure 0 .. A x (d_piece_high - d_through) named beside the piece, never
        added to the through member and never silently dropped.
    (c) NO OTHER LINE BILLS IT (the neighbour lines stop at the piece's faces as drawn, the drawn outline of the piece
        runs through the square to an outer line) -> the piece keeps it and runs to its far / outer face (R-CONC-OWN-1:
        the element that would otherwise lose it keeps it; never in neither). If an abutting member that stops at the
        square is deeper than the piece's low depth, the corner below the piece soffit is a GAP exposure
        0 .. A x max(0, d_abut - d_piece_low) named beside, never added and never 0 by silence.
    A square covered by two owners (DOUBLE) or only partly by one (PARTIAL) is refused: HELD, the owner is not guessed.
    The face-to-face length of the piece = its drawn extent less the squares owned by others. A near-face length is
    never taken where (c) applies (it would leave the square in no line); a far-face length is never taken where (a) or
    (b) applies (the square would be counted twice).
R-T666-2 BOUNDARY ELEMENT ON A STRETCH SHARED WITH A BUILDING GROUND BEAM. A boundary band drawn continuous on the
    foundation plan under a stretch where the building stands on the plot line keeps that stretch when the sheet draws
    it there (the drawing shows it: it is not removed for being under a building). Plan coincidence alone deducts
    nothing (Q-62 A cond): the shared concrete is the 3-D intersection of the two prisms. Vertical relation:
    DISJOINT (printed: e.g. the G.B detail runs from slab level to the outer ground level and the band lies at the
    excavation depth below, or a note puts brick between) -> each line keeps its own prism, deduction 0;
    INTERSECT with a stated precedence -> the intersection is owned once by the precedence owner, deducted from the
    other in its ledger; INTERSECT with no stated precedence, or UNKNOWN levels -> HELD with the exposure
    0 .. shared length x band width x band depth beside the band line, never deducted by guess, never counted twice.

Provenance: T-666 (2026-11-10, worker 1) on Checker F-T661-1 (T-661 Gate B verdict) and the T-659 boundary-band
residual; UP-CONC-JOINT-001 (column-beam joint), R-CONC-OWN-1 1.0.0-proposed (T-189), R-T660-2, R-T659-3, owner Q-20,
Q-62 A cond, ERS s.2.4. Scope: every villa (the Alsenan figures are one application).
"""
from __future__ import annotations

from decimal import Decimal

Q6 = Decimal("0.000001")


class Refused(ValueError):
    """A reading the rules refuse."""


def _m(v, what, allow_zero=False):
    if v is None:
        raise Refused(f"{what} not printed / not drawn: HELD, never 0")
    d = Decimal(str(v))
    if d < 0 or (d == 0 and not allow_zero):
        raise Refused(f"{what} {v}: not positive")
    if d > 50 and not what.startswith("coordinate"):
        raise Refused(f"{what} {v}: dimensions in m (a value above 50 reads as mm)")
    return d


def _box(b, what):
    if b is None or len(b) != 4:
        raise Refused(f"{what}: outline not drawn")
    x0, y0, x1, y1 = (Decimal(str(v)) for v in b)
    if x1 <= x0 or y1 <= y0:
        raise Refused(f"{what}: empty outline")
    return x0, y0, x1, y1


def _inside(a, b, tol):
    return a[0] >= b[0] - tol and a[1] >= b[1] - tol and a[2] <= b[2] + tol and a[3] <= b[3] + tol


def _overlap(a, b):
    return min(a[2], b[2]) > max(a[0], b[0]) and min(a[3], b[3]) > max(a[1], b[1])


def square_owner(square, *, columns=(), through=(), piece_id, tol="0.001"):
    """R-T666-1: (kind, owner id) for one junction square; columns / through = [(id, box)] in m (plan)."""
    sq = _box(square, "junction square")
    t = Decimal(tol)
    hits, partial = [], []
    for kind, members in (("COLUMN", columns), ("THROUGH", through)):
        for mid, b in members:
            bb = _box(b, f"{kind} {mid}")
            if _inside(sq, bb, t):
                hits.append((kind, mid))
            elif _overlap(sq, bb):
                partial.append((kind, mid))
    if partial:
        raise Refused(f"PARTIAL: square only partly inside {partial}: owner not established, HELD")
    cols = [h for h in hits if h[0] == "COLUMN"]
    if len(cols) > 1 or (not cols and len(hits) > 1):
        raise Refused(f"DOUBLE: square inside {hits}: two owners, HELD")
    if cols:
        return cols[0]          # (a) the column owns the joint prism even where a beam line is drawn through it
    if hits:
        return hits[0]          # (b)
    return ("PIECE", piece_id)  # (c)


def owned_length(drawn_extent, ends):
    """R-T666-1 face-to-face length: drawn extent along the piece axis less the end squares owned by others.

    drawn_extent = (a, b) in m along the axis; ends = [(s, t, (kind, owner))] for the squares inside the extent."""
    a, b = (Decimal(str(v)) for v in drawn_extent)
    if b <= a:
        raise Refused("empty piece extent")
    length = b - a
    for s, t, (kind, _owner) in ends:
        s, t = Decimal(str(s)), Decimal(str(t))
        if not (a <= s < t <= b):
            raise Refused("end square outside the piece's drawn extent")
        if s != a and t != b:
            raise Refused("a junction square in mid-span is not an end square")
        if kind != "PIECE":
            length -= t - s
    return _m(length, "face-to-face length")


def envelope(width, length, depth_low, depth_high):
    """R-T660-2 bound on the owned length: (low, high) m3."""
    b, L = _m(width, "drawn width"), _m(length, "face-to-face length")
    lo, hi = _m(depth_low, "low depth"), _m(depth_high, "high depth")
    if lo > hi:
        raise Refused("low depth above high depth")
    return (b * L * lo).quantize(Q6), (b * L * hi).quantize(Q6)


def depth_exposure(kind, area, *, d_other, d_piece_low, d_piece_high):
    """R-T666-1 named exposure beside the piece for an owned square (never added to a total)."""
    A = _m(area, "square area")
    other = _m(d_other, "other member depth")
    plo, phi = _m(d_piece_low, "piece low depth"), _m(d_piece_high, "piece high depth")
    if kind == "THROUGH":   # piece deeper than the member it frames into
        return Decimal(0), (A * max(Decimal(0), phi - other)).quantize(Q6)
    if kind == "PIECE":     # abutting member deeper than the piece's low depth (corner below the piece soffit)
        return Decimal(0), (A * max(Decimal(0), other - plo)).quantize(Q6)
    return Decimal(0), Decimal(0)   # COLUMN: the column runs to the slab top, any piece depth is inside it


def stretch_ownership(*, shared_length, band_width, band_depth_low, band_depth_high, relation, precedence=None):
    """R-T666-2: what the band line keeps on a stretch shared in plan with a building G.B.

    relation: 'DISJOINT' (printed), 'INTERSECT' or 'UNKNOWN'. Returns a dict; never deducts by plan overlap."""
    L = _m(shared_length, "shared length", allow_zero=True)
    b = _m(band_width, "band width")
    lo, hi = _m(band_depth_low, "band low depth"), _m(band_depth_high, "band high depth")
    if lo > hi:
        raise Refused("band low depth above high depth")
    if relation == "DISJOINT":
        return {"status": "OWNED_ONCE_EACH", "deduction_m3": Decimal(0), "exposure_m3": (Decimal(0), Decimal(0))}
    if relation == "INTERSECT" and precedence in ("BAND", "GROUND_BEAM"):
        return {"status": f"OWNED_ONCE_BY_{precedence}", "deduction_m3": None,
                "note": "intersection volume from the printed levels, deducted from the other line in its ledger"}
    if relation in ("INTERSECT", "UNKNOWN"):
        return {"status": "HELD_EXPOSURE", "deduction_m3": None,
                "exposure_m3": (Decimal(0), (L * b * hi).quantize(Q6))}
    raise Refused(f"vertical relation {relation!r} not one of DISJOINT / INTERSECT / UNKNOWN")
