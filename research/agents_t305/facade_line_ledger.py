"""T-305 rules: the EXTERIOR PLASTER / SIGMA FACE-TO-LINE LEDGER (every villa; pure functions, no drawing input).

Physical element (ERS s.2.1): the exterior plaster (with its Sigma coat, owner notes Sigma 2026-10-21: Sigma is not a
separate area) is applied to the OUTER FACE of the built masonry / concrete envelope. A face exists where a wall stands;
it is measured once, as a band between printed levels (T-159), and the plaster covers it less every opening by the
area of its HOLE in that face (owner Q-73 A confirmed: full openings, only where masonry physically exists; T-302: the
developed hole, never the window measure of the aluminium line).

R-T305-1 (face -> line, one owner per face portion):
  a portion of a drawn exterior face belongs to the candidate facade line of floor F only where the line's own formula
  reaches it: the side is on F's facade run and the band lies inside [F.F.L.(F), F.F.L.(next)] (UP-FACADE-001,
  ARCH.FACADE / FIN.EXT.FINISH); below the lowest floor's F.F.L. it belongs to that floor's plinth line; every other
  part (a parapet outer face above the next F.F.L., a face standing on a lower roof, the top floor where no next F.F.L.
  exists) is NO_LINE: a missing category, carried with its m2 and status, never 0. The formula's reach beyond a face
  (a roof edge below the next F.F.L.) is a named LINE_FORMULA_OVERREACH, never an area of wall.
R-T305-2 (opening -> face): each opening is deducted once, on the one face whose band holds it, by its hole area:
  printed / drawing-confirmed hole -> fixed; owner fallback (Q-55 C door 2.20) -> ASSUMED — OWNER-APPROVED; height
  not established -> HELD with an upper cap (never 0, never a guess). A deduction larger than the face band is refused;
  the window (aluminium) measure is refused as a wall hole when a hole measure exists.
R-T305-3 (items beside the faces): parapet inner faces and tops are m2 ITEMS of their own (never wall m2 of the
  facade line); corners / arrises are m.l (never added to m2); a face or item booked to two lines is refused.

Statuses (WORKFLOW_CONTROLS s.5): DRAWING-CONFIRMED, ASSUMED — OWNER-APPROVED, HELD, UNKNOWN; ledger states IN_LINE /
NO_LINE / OTHER_TRADE / NOT_APPLICABLE.
"""

from __future__ import annotations

from dataclasses import dataclass, field

LEDGER_STATES = ("IN_LINE", "NO_LINE", "OTHER_TRADE", "NOT_APPLICABLE")
EVIDENCE = ("DRAWING-CONFIRMED", "ASSUMED — OWNER-APPROVED", "HELD", "UNKNOWN", "VERIFIED")
EPS = 1e-9


class LedgerError(ValueError):
    """a booking the ledger refuses (double booking, a window measure as a hole, m.l in m2, a missing face as 0)."""


@dataclass(frozen=True)
class FacadeLine:
    """one candidate line that can own exterior wall faces: its id, item, floor and the band its formula reaches."""
    line_id: str
    item_code: str
    floor: str
    kind: str                    # "STOREY" (F.F.L. -> next F.F.L.) or "PLINTH" (ground -> lowest F.F.L.)
    band_lo: float | None        # level in m; None = not established by the line (no reach)
    band_hi: float | None
    evidence_state: str = ""
    quantity: float | None = None


@dataclass
class Portion:
    """one band of one drawn face (a row of the T-159 face table)."""
    floor: str
    side: str
    facing: str
    portion: str                 # EDGE / FLUSH / COVERED / OVER_LOWER_ROOF / SLAB_EDGE_BELOW / ...
    length_m: float
    bottom: float | None
    top: float | None
    area_m2: float | None        # geometric (ground to top) area of this band; None = HELD
    status: str
    band_kind: str = "storey"    # "plinth" / "storey" / "parapet" / "over_lower_roof" / "slab_edge"
    held_lo: float | None = None
    held_hi: float | None = None
    run_floor: str | None = None  # whose facade run the side is on (default: floor)


def band_kind(p_floor, bottom, top, ffl, next_ffl, portion_name=""):
    """name a band by the floor levels it spans: plinth (below the floor's F.F.L.), storey (inside F.F.L. -> next),
    parapet (above the next F.F.L. or above a roof edge). A band that straddles a boundary is refused: the face table
    splits bands at printed levels, so a straddle means a band not cut where a line's reach ends."""
    if portion_name.upper().startswith("SLAB_EDGE"):
        return "slab_edge"
    if bottom is None or top is None:
        raise LedgerError(f"{p_floor}: a band without both levels cannot be classed")
    if top < bottom - EPS:
        raise LedgerError(f"{p_floor}: band top {top} below bottom {bottom}")
    if top <= ffl + EPS:
        return "plinth" if not portion_name.upper().startswith("OVER_LOWER_ROOF") else "over_lower_roof"
    if bottom >= ffl - EPS and (next_ffl is None or top <= next_ffl + EPS):
        return "storey"
    if next_ffl is not None and bottom >= next_ffl - EPS:
        return "parapet"
    raise LedgerError(f"{p_floor}: band {bottom}..{top} straddles F.F.L. {ffl} / next {next_ffl}: split it first")


def split_at(bottom, top, level):
    """cut a band at a level (inside it): -> [(bottom, level), (level, top)] or [(bottom, top)]."""
    if level is None or not (bottom + EPS < level < top - EPS):
        return [(bottom, top)]
    return [(bottom, level), (level, top)]


def owner_of(portion: Portion, lines: list[FacadeLine], floors: dict, lowest: str):
    """R-T305-1: -> (state, line or None, reason). floors: {floor: (ffl, next_ffl or None)}."""
    if portion.area_m2 is None and portion.held_hi is None and portion.band_kind != "slab_edge":
        raise LedgerError(f"{portion.floor} {portion.side}: a face with no area and no bound would read as 0")
    run_floor = portion.run_floor or portion.floor
    ffl, nxt = floors[run_floor]
    cands = [ln for ln in lines if ln.floor == run_floor]
    if portion.band_kind == "plinth":
        if run_floor != lowest:
            return "NO_LINE", None, "below this floor's F.F.L. on an upper floor: no candidate line reaches it"
        pl = [ln for ln in cands if ln.kind == "PLINTH"]
        if len(pl) == 1:
            return "IN_LINE", pl[0], "lowest floor's plinth line (ground -> F.F.L.)"
        return "NO_LINE", None, f"{len(pl)} plinth lines on the lowest floor (one is needed)"
    if portion.band_kind in ("over_lower_roof", "slab_edge"):
        return "NO_LINE", None, ("a face standing on a lower roof, below its own floor's F.F.L.: outside every "
                                 "candidate formula" if portion.band_kind == "over_lower_roof" else
                                 "slab edge over open air: no depth printed, no candidate line (owner Q-68 C)")
    if portion.band_kind == "parapet":
        return "NO_LINE", None, ("parapet outer face above the next F.F.L.: the candidate formula ends at the next "
                                 "F.F.L." if nxt is not None else "parapet outer face: top floor, no next F.F.L.")
    st = [ln for ln in cands if ln.kind == "STOREY"]
    if len(st) != 1:
        return "NO_LINE", None, f"{len(st)} storey facade lines on {run_floor} (one is needed)"
    ln = st[0]
    if ln.band_lo is None or ln.band_hi is None:
        return "NO_LINE", None, (f"{ln.line_id} exists on {run_floor} but its formula has no established band "
                                 "(no next F.F.L.): it reaches no face")
    if portion.bottom is not None and portion.top is not None and (
            portion.bottom < ln.band_lo - EPS or portion.top > ln.band_hi + EPS):
        raise LedgerError(f"{portion.floor} {portion.side}: storey band {portion.bottom}..{portion.top} outside "
                          f"{ln.line_id} reach {ln.band_lo}..{ln.band_hi}: split it first")
    return "IN_LINE", ln, "storey band inside the line's F.F.L. -> next F.F.L."


@dataclass
class Opening:
    """one opening on one face: its hole on that face."""
    opening_id: str
    floor: str
    side: str
    width_m: float | None
    sill_m: float | None         # above the floor's F.F.L.
    head_m: float | None
    hole_m2: float | None        # established hole area on THIS face (developed / arched outline)
    status: str
    cap_m2: float | None = None  # upper bound when the hole is HELD
    window_measure_m2: float | None = None  # the aluminium line's measure (record only, never the deduction)
    source: str = ""
    face_width_m: float | None = None       # the face length available to the hole (a hole never exceeds it)


def deduction(op: Opening, band_area_m2: float | None, *, use_window_measure: bool = False):
    """R-T305-2: -> dict(fixed, lo, hi, status). fixed = established hole; HELD -> lo 0 .. hi cap (the RANGE, never a
    midpoint). The window measure as the hole is refused when a hole measure exists or is held."""
    if use_window_measure:
        raise LedgerError(f"{op.opening_id}: the window (aluminium) measure is not the hole in the wall face")
    if op.status == "HELD":
        if op.cap_m2 is None:
            raise LedgerError(f"{op.opening_id}: a HELD hole needs a cap (an upper bound), never 0")
        cap = op.cap_m2
        if band_area_m2 is not None and cap > band_area_m2 + EPS:
            cap = band_area_m2
        return {"fixed": None, "lo": 0.0, "hi": cap, "status": "HELD"}
    if op.hole_m2 is None:
        raise LedgerError(f"{op.opening_id}: {op.status} without a hole area")
    if band_area_m2 is not None and op.hole_m2 > band_area_m2 + EPS:
        raise LedgerError(f"{op.opening_id}: hole {op.hole_m2} m2 larger than its face band {band_area_m2} m2")
    return {"fixed": op.hole_m2, "lo": op.hole_m2, "hi": op.hole_m2, "status": op.status}


def hole_on_face(width_m, sill_m, head_m, face_width_m=None):
    """a rectangular hole on one face, its width limited to the face length it sits in: -> (m2, overhang_m)."""
    if None in (width_m, sill_m, head_m):
        return None, None
    if head_m < sill_m - EPS:
        raise LedgerError("head below sill")
    w = width_m if face_width_m is None else min(width_m, face_width_m)
    return w * (head_m - sill_m), max(0.0, width_m - w)


class Book:
    """one owner per face portion / item / opening: a second booking of the same key is refused."""

    def __init__(self):
        self.rows = {}

    def add(self, key, state, line_id=None, unit="m2", **kw):
        if state not in LEDGER_STATES:
            raise LedgerError(f"{key}: unknown ledger state {state}")
        if key in self.rows:
            raise LedgerError(f"{key}: booked twice ({self.rows[key]['state']} {self.rows[key].get('line_id')} "
                              f"and {state} {line_id})")
        if state == "IN_LINE" and not line_id:
            raise LedgerError(f"{key}: IN_LINE without a line id")
        if state != "IN_LINE" and line_id:
            raise LedgerError(f"{key}: {state} carries a line id")
        self.rows[key] = dict(kw, key=key, state=state, line_id=line_id, unit=unit)
        return self.rows[key]


def add_to_area(total_m2, qty, unit):
    """m.l (corners, arrises) never enter an m2 total."""
    if unit != "m2":
        raise LedgerError(f"a {unit} quantity cannot be added to a wall area")
    return total_m2 + qty


def to_wall_line(kind, qty, unit, line: FacadeLine):
    """R-T305-3: only a wall FACE band enters a facade wall line; a parapet top / inner face, a corner (m.l) or any other
    item is refused (it is its own item, never wall m2 of the facade line)."""
    if kind != "WALL_FACE":
        raise LedgerError(f"{kind} is not a wall face: it cannot be booked to the facade line {line.line_id}")
    if unit != "m2":
        raise LedgerError(f"a {unit} quantity cannot be booked to the m2 line {line.line_id}")
    if qty is None:
        raise LedgerError(f"a face without a quantity cannot be booked to {line.line_id} as 0")
    return qty


def item_owner(kind):
    """R-T305-3: beside-the-face items and who owns them on the candidate (none of them is the facade wall line)."""
    table = {
        "PARAPET_INNER_FACE": ("NO_LINE", "parapet inner face (roof side): m2 item, not a facade face"),
        "PARAPET_TOP": ("NO_LINE", "parapet top surface: m2 item (coping profile per the architect), never wall m2"),
        "CORNER_ML": ("NO_LINE", "external arrises: their own m.l line (owner notes, correction 2026-10-22)"),
        "BOUNDARY_WALL": ("OTHER_TRADE", "site boundary fence: not a house face (owner Q-65 C: material HELD)"),
        "DOME": ("NOT_APPLICABLE", "owner notes Sigma item 3: no domes in this scope"),
        "DRIP_EDGE": ("NO_LINE", "drip band: nothing drawn (section A-A plain parapet), owner not answered: UNKNOWN"),
        "FRAME_MOULDING": ("NO_LINE", "facade frame mouldings: drawn on the elevations, profile not drawn (HELD)"),
    }
    if kind not in table:
        raise LedgerError(f"unknown item kind {kind}")
    return table[kind]
