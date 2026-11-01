"""T-425 stair TREAD / STEP binding check: one physical flight, one valued tread line (research method, any villa).

Physical element first (ERS s.2.1). A TREAD is the horizontal going surface behind one drawn FRONT (nosing) edge of a
flight; a WINDER is a tapered tread in a turn; a LANDING / FLOOR edge is the top nosing of a flight and has no tread
behind it (T-412 R-T412-1). A FLIGHT is one physical run of steps between two levels. On storey plans the same flight
can be drawn on more than one sheet: on the plan whose cut it lies below (its own reading) and again on the plan above,
seen down through the stair opening (a SEEN-THROUGH reading), or hidden above the cut on the plan below (a PARTIAL
reading). A take-off that values more than one reading of one flight counts the marble twice.

Rules (proposed, research, any villa):
  R-T425-1  one flight occurrence, one valued tread line: every valued tread / step line is bound to exactly one drawn
            flight (or HELD by name as UNBOUND), and a drawn flight carries at most ONE valued tread line and ONE valued
            step line; any further valued reading of the same flight is a DOUBLE_COUNT and is not valued (its quantity
            moves to the flight's single line, never added).
  R-T425-2  the tread count of a flight is the number of drawn front edges of kind TREAD (solid AND hidden layers,
            a front edge drawn twice once; T-412 R-T412-3), never "engine lines - 1"; the corrected tread area is the
            sum over those treads of drawn going x drawn width, each term drawn; a tread whose going is not drawn on any
            sheet keeps its piece / step-lm (front edge drawn) but its m2 is HELD by name (never 0, never a uniform-going
            default).
  R-T425-3  a reading bound to a flight whose geometry the owner holds (winder turn with conflicting counts, owner S-9;
            curved flight without section, Q-50 A cond) is not valued: HELD with that cause, whatever the reading's
            own count.
Nothing here computes a rate or a total of money; units are m2 (B7-02 tread marble) and lm (B7-06 commercial step).
"""

from __future__ import annotations

from dataclasses import dataclass, field

TOL = 1e-6
MAX_DIM_M = 20.0
VALUED_STATES = ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL")
CONFIRMED, HELD = "DRAWING-CONFIRMED", "HELD"
KEEP, CORRECT, DOUBLE, FOLD, HOLD = "KEEP", "CORRECT", "DOUBLE_COUNT", "FOLDED", "HELD"


class BindingInputError(ValueError):
    """A refused input: the check never guesses a flight, a going, a count or a unit."""


@dataclass(frozen=True)
class Tread:
    front: str                     # front-edge id (handle) of this tread
    width_m: float                 # drawn front-edge length across the flight (m)
    going_m: float | None          # drawn front-to-next-riser going (m); None = not drawn on any sheet
    going_source: str = ""         # where the going is drawn (sheet / handles); required when going_m is given


@dataclass(frozen=True)
class Flight:
    fid: str
    treads: tuple                  # Tread, in riser order
    held_cause: str = ""           # non-empty: the owner / designer holds this flight's geometry (R-T425-3)


@dataclass(frozen=True)
class Reading:
    """One candidate flight reading = its tread line (m2) and step line (lm)."""
    engine_flight: str
    flight: str | None             # bound drawn flight id, or None (UNBOUND)
    role: str                      # 'OWN' (the governing reading), 'SEEN_THROUGH', 'PARTIAL', 'UNBOUND'
    tread_line: str
    step_line: str
    state: str
    treads: int
    tread_m2: float | None
    step_lm: float | None
    basis: str = ""


@dataclass
class Row:
    line_id: str
    code: str
    engine_flight: str
    flight: str | None
    action: str
    before: float | None
    after: float | None
    status: str
    cause: str
    beside: float | None = None
    delta: float = 0.0
    notes: list = field(default_factory=list)


def _chk_dim(v, what):
    if v is None:
        return
    if not (0 < v <= MAX_DIM_M):
        raise BindingInputError(f"{what} {v!r} m out of range (mm passed as m, or 0)")


def validate(flights, readings):
    fl = {}
    for f in flights:
        if f.fid in fl:
            raise BindingInputError(f"flight {f.fid} given twice")
        fronts = [t.front for t in f.treads]
        if len(set(fronts)) != len(fronts):
            raise BindingInputError(f"{f.fid}: a front edge counted twice (one edge, one tread)")
        for t in f.treads:
            _chk_dim(t.width_m, f"{f.fid} {t.front} width")
            _chk_dim(t.going_m, f"{f.fid} {t.front} going")
            if t.going_m is not None and not t.going_source:
                raise BindingInputError(f"{f.fid} {t.front}: a going without its drawing source")
        fl[f.fid] = f
    seen = set()
    for r in readings:
        if r.engine_flight in seen:
            raise BindingInputError(f"reading {r.engine_flight} given twice")
        seen.add(r.engine_flight)
        if r.role not in ("OWN", "SEEN_THROUGH", "PARTIAL", "UNBOUND"):
            raise BindingInputError(f"{r.engine_flight}: unknown role {r.role}")
        if (r.flight is None) != (r.role == "UNBOUND"):
            raise BindingInputError(f"{r.engine_flight}: role UNBOUND iff no drawn flight")
        if r.flight is not None and r.flight not in fl:
            raise BindingInputError(f"{r.engine_flight}: bound to an unknown flight {r.flight}")
        if r.state in VALUED_STATES and (r.tread_m2 is None or r.step_lm is None):
            raise BindingInputError(f"{r.engine_flight}: a valued state without a quantity")
        for q in (r.tread_m2, r.step_lm):
            if q is not None and q < 0:
                raise BindingInputError(f"{r.engine_flight}: a negative quantity")
    own = {}
    for r in readings:
        if r.role == "OWN":
            if r.flight in own:
                raise BindingInputError(f"flight {r.flight} has two OWN readings ({own[r.flight]}, {r.engine_flight})")
            own[r.flight] = r.engine_flight
    return fl


def drawn_quantities(f):
    """(treads, step_lm confirmed, tread_m2 confirmed, held treads list) of a drawn flight (R-T425-2)."""
    step = sum(t.width_m for t in f.treads)
    m2 = sum(t.width_m * t.going_m for t in f.treads if t.going_m is not None)
    held = [t.front for t in f.treads if t.going_m is None]
    held_beside = None
    if held:
        gs = [t.going_m for t in f.treads if t.going_m is not None]
        # beside figure only (never the quantity): the held treads at the flight's drawn going where all drawn goings
        # agree; otherwise no beside figure
        if gs and max(gs) - min(gs) < TOL:
            held_beside = round(sum(t.width_m for t in f.treads if t.going_m is None) * gs[0], 6)
    return len(f.treads), round(step, 6), round(m2, 6), held, held_beside


def bind(flights, readings):
    """per candidate line: KEEP / CORRECT / DOUBLE_COUNT / HELD with before / after (R-T425-1 .. 3)."""
    fl = validate(flights, readings)
    valued = [r for r in readings if r.state in VALUED_STATES]
    by_flight = {}
    for r in valued:
        if r.flight is not None:
            by_flight.setdefault(r.flight, []).append(r)
    rows = []
    for r in readings:
        if r.state not in VALUED_STATES:
            for code, line in (("B7-02", r.tread_line), ("B7-06", r.step_line)):
                rows.append(Row(line, code, r.engine_flight, r.flight, KEEP, None, None, r.state,
                                "not valued in the candidate (exposure / blocked); unchanged"))
            continue
        if r.flight is None:
            for code, line, q in (("B7-02", r.tread_line, r.tread_m2), ("B7-06", r.step_line, r.step_lm)):
                rows.append(Row(line, code, r.engine_flight, None, HOLD, q, None, HELD,
                                "UNBOUND: the reading matches no drawn flight; held by name, never 0", beside=q,
                                delta=-q))
            continue
        f = fl[r.flight]
        if f.held_cause:
            for code, line, q in (("B7-02", r.tread_line, r.tread_m2), ("B7-06", r.step_line, r.step_lm)):
                rows.append(Row(line, code, r.engine_flight, r.flight, HOLD, q, None, HELD, f.held_cause, beside=q,
                                delta=-q))
            continue
        group = by_flight[r.flight]
        carrier = _carrier(group)
        n, step, m2, held, beside = drawn_quantities(f)
        if r is not carrier:
            if r.role == "PARTIAL":
                act, why = FOLD, (f"FOLDED: a partial reading of {r.flight} ({r.treads} treads); the whole drawn flight "
                                  f"is valued once on {carrier.engine_flight} (R-T425-1)")
            else:
                act, why = DOUBLE, (f"DOUBLE_COUNT: {r.role} reading of {r.flight}, the same physical treads valued on "
                                    f"{carrier.engine_flight} (R-T425-1)")
            for code, line, q in (("B7-02", r.tread_line, r.tread_m2), ("B7-06", r.step_line, r.step_lm)):
                rows.append(Row(line, code, r.engine_flight, r.flight, act, q, None, "SUPERSEDED", why, delta=-q))
            continue
        # the carrier carries the whole drawn flight once
        others = [x for x in group if x is not carrier]
        notes = [f"{x.engine_flight} ({x.role}, {x.treads} treads) not valued beside this line" for x in others]
        eng = r.treads + sum(x.treads for x in others if x.role == "PARTIAL")
        if eng != n:
            notes.append(f"engine reads {eng} treads, drawn {n}")
        for code, line, q, new in (("B7-02", r.tread_line, r.tread_m2, m2), ("B7-06", r.step_line, r.step_lm, step)):
            if code == "B7-02" and held:
                cause = (f"drawn {n} treads; {len(held)} tread(s) {', '.join(held)}: going not drawn on any sheet, "
                         f"m2 HELD by name (beside {beside}), the other {n - len(held)} valued (R-T425-2)")
            else:
                cause = f"drawn {n} treads (R-T425-2)"
            act = KEEP if abs(new - q) < 5e-4 and not (code == "B7-02" and held) else CORRECT
            rows.append(Row(line, code, r.engine_flight, r.flight, act, q, round(new, 6), CONFIRMED, cause,
                            beside=beside if code == "B7-02" and held else None, delta=round(new - q, 6),
                            notes=list(notes)))
    return rows


def _carrier(group):
    """the one reading that carries the flight: its OWN reading; else the reading with the most treads, then id."""
    own = [x for x in group if x.role == "OWN"]
    if own:
        return own[0]
    return sorted(group, key=lambda x: (-x.treads, x.engine_flight))[0]


def totals(rows):
    out = {}
    for code in ("B7-02", "B7-06"):
        rs = [r for r in rows if r.code == code]
        out[code] = {
            "valued_before": round(sum(r.before for r in rs if r.before is not None), 6),
            "valued_after": round(sum(r.after for r in rs if r.after is not None), 6),
            "double_count_removed": round(sum(r.before for r in rs if r.action == DOUBLE), 6),
            "folded": round(sum(r.before for r in rs if r.action == FOLD), 6),
            "held_by_name": round(sum(r.before for r in rs if r.action == HOLD and r.before is not None), 6),
        }
    return out
