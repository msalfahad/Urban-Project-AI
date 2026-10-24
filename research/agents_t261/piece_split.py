"""T-261: blockwork register v2 blockers, wall by wall: the piece split of a wall with a held piece (any villa).

Research module, imported by nothing in engine/; it moves no BOQ line and edits no register (register v2, T-228, is read
only). It answers one question per held-net wall: which part of the wall's net is established by printed evidence and
which part stays HELD, and with which openings.

Rule R-T261-1 (piece split, any villa; provenance: R-T228-1 point 5 'a range is carried as its common part + a HELD
increment', BLOCKWORK_RESOLUTION_PROGRAMME.md s.2 / s.5, ERS s.3 'build before deduct', WORKFLOW_CONTROLS s.5):
  1. A wall is cut into height pieces between drawn faces (column faces, band edges). A piece is ESTABLISHED when its
     base is the storey basis and its top is a member whose depth is printed (or a printed slab underside), so its
     height comes from the member; every other piece is HELD with the missing item named. Allowed height sources:
     'member' (printed depth under Q-60 A), 'slab' (printed slab thickness), 'checker' (a Checker's own figure).
     A finish height, a freelancer height, a default or a storey height with no member is refused (BAD_SOURCE).
  2. A piece whose base is not the storey basis (a stair-foot landing, a sunken floor) or whose top is a stair member
     with no floor-level member printed with it (R-T228-3) is HELD, whatever its top member says.
  3. Each opening is assigned to the ONE piece its two jambs lie in, by drawn geometry (jamb offsets measured from that
     piece's start face). An opening whose jambs straddle a piece boundary cannot be split without its head geometry:
     the wall gets no established part (STRADDLE), it stays wholly HELD.
  4. Established part = sum(length x height of established pieces) - sum(openings inside them). HELD increment = the
     held pieces with the openings inside them; it is reported as a figure ('not a quantity') or a bound, never 0 and
     never added to an established total. Wall net = established part + HELD increment.
  5. The pieces close to the wall's census length (gross_from_pieces lesson, Checker 2026-10-23 18:01): a residual
     length between the pieces and the census is itself a HELD piece with its cause named, never spread over the pieces.
  6. Lengths are metres; a value above 100 m on a villa wall is a millimetre slip and is refused (UNITS).
  7. (r2, after the Checker's 2026-10-24 15:10 rejection) An established 'member' or 'slab' piece names the drawn extent
     of the member it stands under (face to face on the drawing, with its source) and is never longer than that
     extent (OVER_MEMBER); a member piece with no named extent is refused (EXTENT_UNNAMED). Census length beyond the
     drawn faces (a corner or junction overlap of a centreline census) is its own piece under whatever member actually
     spans it there: established only when that member's depth is printed, otherwise HELD; never stretched onto a
     neighbouring member to close the census.
  8. (r3, after the Checker's 2026-10-24 17:00 rejection) Rule 7 holds for EVERY established member / slab piece of a
     split, inherited or new: an extent taken from an earlier register (its gross or weighted height carried onto a
     length), a census remainder or any extent that is not re-derived on the drawing is not a drawn extent and is
     refused (EXTENT_UNNAMED, markers in INHERITED_EXTENT_MARKERS). A piece's extent names its band / slab handles.
  9. (r3, refines point 3) An opening whose jambs run on from the piece they start in into the NEXT pieces (in list
     order) is deducted once from the established part when, and only when, its head height is given with its source
     (a printed head or an answered owner decision, e.g. Q-55 C) and every piece it spans is ESTABLISHED with a height
     above that head: the opening is then a rectangle wholly below every soffit it passes under, so its area does not
     depend on how the wall is cut. Otherwise (no head, a spanned piece HELD, a soffit at or below the head, a jamb
     before the start piece) the wall stays wholly HELD (STRADDLE), as in point 3.
"""
from __future__ import annotations

from dataclasses import dataclass, field

ALLOWED_SOURCES = ("member", "slab", "checker")
REFUSED_SOURCES = ("finish", "freelancer", "default", "storey", "convention")
TOL = 0.0015
# rule 8: wording that marks an extent as inherited / closed, not drawn (case-insensitive)
INHERITED_EXTENT_MARKERS = ("register", "not re-derived", "census remainder", "remainder of the census",
                            "closed to census", "weighted", "carried")


class SplitError(ValueError):
    def __init__(self, code: str, msg: str):
        super().__init__(f"{code}: {msg}")
        self.code = code


@dataclass
class Piece:
    pid: str
    length_m: float
    height_m: float | None = None          # None = no established height
    source: str = ""                        # member / slab / checker (rule 1)
    base_is_storey_basis: bool = True       # rule 2
    top_is_stair_member: bool = False       # rule 2 (R-T228-3)
    floor_member_with_stair: bool = False   # a floor-level member printed beside the stair mark
    held_item: str = ""                     # the exact missing item when the piece is HELD
    held_figure_m2: str = ""                # text figure / bound for a HELD piece ('not a quantity')
    drawn_extent_m: float | None = None     # rule 7: drawn face-to-face extent of the member above
    extent_source: str = ""                 # rule 7: where that extent is drawn (handles / merged register)


@dataclass
class Opening:
    oid: str
    piece: str
    jamb_a_m: float     # offsets from the piece's start face
    jamb_b_m: float
    area_m2: float
    head_m: float | None = None      # rule 9: head height above the storey basis, with its source
    head_source: str = ""


@dataclass
class Split:
    wall_id: str
    established_m2: float | None
    established_gross_m2: float
    established_deductions_m2: float
    held_pieces: list = field(default_factory=list)
    held_openings: list = field(default_factory=list)
    status: str = ""
    why: str = ""
    spanning: list = field(default_factory=list)   # rule 9: (opening id, [piece ids]) deducted across pieces


def _check_len(v: float, what: str):
    if v is None or v < 0:
        raise SplitError("NEGATIVE", f"{what} {v}")
    if v > 100.0:
        raise SplitError("UNITS", f"{what} {v} m on a villa wall: a millimetre value, refused")


def piece_established(p: Piece) -> tuple[bool, str]:
    """Rule 1 / 2: is this piece's height established, and if not, why."""
    if p.source in REFUSED_SOURCES:
        raise SplitError("BAD_SOURCE", f"{p.pid}: height source '{p.source}' never sets a block height (Q-60 A)")
    if p.height_m is None:
        return False, p.held_item or "no member with a printed depth above the piece (Q-60 A has nothing to stop at)"
    if p.source not in ALLOWED_SOURCES:
        raise SplitError("BAD_SOURCE", f"{p.pid}: height {p.height_m} with no named source")
    if not p.base_is_storey_basis:
        return False, p.held_item or "piece stands on a printed level other than the storey basis (base not established)"
    if p.top_is_stair_member and not p.floor_member_with_stair:
        return False, p.held_item or "top member is a stair member with no floor-level member printed (R-T228-3)"
    if p.height_m <= 0:
        raise SplitError("NEGATIVE", f"{p.pid}: height {p.height_m}")
    if p.source in ("member", "slab"):
        if p.drawn_extent_m is None or not p.extent_source:
            raise SplitError("EXTENT_UNNAMED", f"{p.pid}: an established {p.source} piece names the drawn extent of "
                                               "its member and its source (rule 7)")
        low = p.extent_source.lower()
        hit = [m for m in INHERITED_EXTENT_MARKERS if m in low]
        if hit:
            raise SplitError("EXTENT_UNNAMED", f"{p.pid}: extent source '{p.extent_source[:60]}' is inherited / closed "
                                               f"({', '.join(hit)}), not a drawn member extent (rule 8)")
        _check_len(p.drawn_extent_m, f"{p.pid} drawn extent")
        if p.length_m > p.drawn_extent_m + TOL:
            raise SplitError("OVER_MEMBER", f"{p.pid}: {p.length_m:.3f} m under a member drawn {p.drawn_extent_m:.3f} m "
                                            "face to face; the excess is its own piece (rule 7)")
    return True, ""


def split_wall(wall_id: str, pieces: list[Piece], openings: list[Opening], census_length_m: float) -> Split:
    """Rule R-T261-1. Returns the established part, the deductions inside it and the HELD increment."""
    _check_len(census_length_m, "census length")
    ids = [p.pid for p in pieces]
    if len(ids) != len(set(ids)):
        raise SplitError("DUPLICATE_PIECE", f"{wall_id}: {ids}")
    for p in pieces:
        _check_len(p.length_m, f"{p.pid} length")
    total = sum(p.length_m for p in pieces)
    if abs(total - census_length_m) > TOL:
        raise SplitError("NOT_CLOSED", f"{wall_id}: pieces {total:.4f} m vs census {census_length_m:.4f} m; a residual "
                                       "is its own HELD piece with its cause (rule 5)")
    by_id = {p.pid: p for p in pieces}
    est = {}
    reasons = {}
    for p in pieces:
        ok, why = piece_established(p)
        est[p.pid] = ok
        if not ok:
            reasons[p.pid] = why
    spanning = []
    for o in openings:
        if o.piece not in by_id:
            raise SplitError("UNKNOWN_PIECE", f"{o.oid} -> {o.piece}")
        p = by_id[o.piece]
        a, b = sorted((o.jamb_a_m, o.jamb_b_m))
        _check_len(b, f"{o.oid} jamb")
        if o.area_m2 <= 0:
            raise SplitError("NEGATIVE", f"{o.oid} area {o.area_m2}")
        if a < -TOL or b > p.length_m + TOL:
            span, why = _span(o, a, b, pieces, est)
            if span is None:
                return Split(wall_id, None, 0.0, 0.0, [p.pid for p in pieces if not est[p.pid]], [o.oid], "STRADDLE",
                             f"{o.oid} jambs {a:.3f} .. {b:.3f} m leave piece {p.pid} (0 .. {p.length_m:.3f}): {why}; "
                             "the wall stays wholly HELD")
            spanning.append((o.oid, span))
    held = [p for p in pieces if not est[p.pid]]
    gross = sum(p.length_m * p.height_m for p in pieces if est[p.pid])
    ded = sum(o.area_m2 for o in openings if est[by_id[o.piece].pid])
    held_ops = [o.oid for o in openings if not est[o.piece]]
    if not any(est.values()):
        return Split(wall_id, None, 0.0, 0.0, [p.pid for p in held], held_ops, "HELD",
                     "no piece has an established height")
    if ded - gross > TOL:
        raise SplitError("NEGATIVE", f"{wall_id}: deductions {ded:.3f} exceed the established gross {gross:.3f}")
    status = "SPLIT" if held else "ESTABLISHED"
    why = "; ".join(f"{k}: {v}" for k, v in reasons.items())
    return Split(wall_id, round(gross - ded, 4), round(gross, 4), round(ded, 4), [p.pid for p in held], held_ops,
                 status, why, spanning)


def _span(o: Opening, a: float, b: float, pieces: list, est: dict):
    """Rule 9: the consecutive pieces an opening covers from its start piece, or (None, why)."""
    if a < -TOL:
        return None, "a jamb lies before its start piece (offsets are measured from that piece's start face)"
    if o.head_m is None or not o.head_source:
        return None, "no head height with its source: no split without the head geometry"
    _check_len(o.head_m, f"{o.oid} head")
    idx = [p.pid for p in pieces].index(o.piece)
    start, span = 0.0, []
    for p in pieces[idx:]:
        if start >= b - TOL:
            break
        span.append(p)
        start += p.length_m
    if start < b - TOL:
        return None, "the opening runs past the last piece"
    for p in span:
        if not est[p.pid]:
            return None, f"it spans HELD piece {p.pid}"
        if p.height_m <= o.head_m + TOL:
            return None, f"piece {p.pid} soffit {p.height_m:.3f} m is not above the head {o.head_m:.3f} m"
    return [p.pid for p in span], ""


def wall_total_text(s: Split, held_figure: str) -> str:
    """Rule 4: the wall net is never a single number while a piece is HELD; the held part is never 0."""
    if s.status == "ESTABLISHED":
        return f"{s.established_m2:.4f}"
    if s.established_m2 is None:
        return f"HELD (figure {held_figure}, not a quantity)"
    if not held_figure or held_figure.strip() in ("0", "0.0", "0.000"):
        raise SplitError("HELD_AS_ZERO", f"{s.wall_id}: the HELD increment needs its figure or bound, never 0")
    return f"{s.established_m2:.4f} established + HELD increment ({held_figure}, not a quantity)"
