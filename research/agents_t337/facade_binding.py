"""T-337 rules: bind every exterior face, opening and facade component to ONE owner line (every villa).

Research module (unwired). It changes no engine module, rule or knowledge file and no candidate line.

R-T337-1  OWNER LINE BY ELEMENT AND LEVEL BAND. A drawn exterior face band is owned by exactly one line:
          * PLINTH            band below the lowest F.F.L. of the face (outer ground -> F.F.L.);
          * STOREY <floor>    band inside [F.F.L. of <floor>, next level of that floor) where the next level is the
                              next F.F.L. above, or the finished ROOF level when <floor> is the top floor under that roof;
                              the floor is chosen by the band's LEVELS, not by which plan outline draws the face (a face
                              standing on a lower roof below the next F.F.L. is a storey face of the floor whose levels
                              contain it);
          * PARAPET <roof>    band above a finished roof level up to the parapet top (never folded into a storey line,
                              also when the storey's formula 'top floor to the parapet top' would reach it);
          * SLAB_EDGE         the exposed edge of a plate over open air (no wall below it): its own line; HELD while the
                              edge depth is not printed, never 0.
          A band that crosses a level boundary is refused until it is split at that level (split_at).
R-T337-2  OPENINGS ONCE, BY HOLE, ON THE LINE OF THE BAND THAT HOLDS THEM. An opening is deducted once, by its hole in
          the face (never the window measure), from the line owning the band its hole lies in; a hole whose head or sill
          leaves that band is refused; a parapet / plinth / slab-edge line takes no deduction unless a hole lies in it.
          A HELD hole is a bounded range [0, cap] with the cap <= its band area; the line stays HELD (no point value).
R-T337-3  ITEM UNITS AND STATUSES. m2 face lines, m.l edge lines (arrises, stop-ends, coping, drip) and m2 surface items
          (parapet tops, inner faces) are separate lines; an m.l item never enters an m2 line; a HELD quantity carries a
          range and no point value, an UNKNOWN quantity carries no number, and neither is ever 0.

Statuses (WORKFLOW_CONTROLS s.5): VERIFIED, DRAWING-CONFIRMED, ASSUMED — OWNER-APPROVED, HELD, UNKNOWN.
"""

from __future__ import annotations

from dataclasses import dataclass, field

EPS = 1e-6
STATUSES = ("VERIFIED", "DRAWING-CONFIRMED", "ASSUMED — OWNER-APPROVED", "HELD", "UNKNOWN")


class BindingError(ValueError):
    pass


@dataclass(frozen=True)
class Part:
    """One building part with its own printed levels (metres, one datum): floors ((floor, F.F.L.), ...) ascending and
    `top`, the level its top floor ends at (its finished roof, or the plate above when it is covered). A ground floor
    with two F.F.L.s (an annex at +0.30 beside a house at +1.00) is two parts; both bind to the same storey line."""
    name: str
    floors: tuple
    top: float

    def lowest_ffl(self):
        return self.floors[0][1]


def split_at(bottom, top, level):
    """Split a band at a level strictly inside it; a level outside returns the band unchanged."""
    if top < bottom - EPS:
        raise BindingError("band top below its bottom")
    if bottom + EPS < level < top - EPS:
        return [(bottom, level), (level, top)]
    return [(bottom, top)]


def owner_of(kind, floor=None, roof=None):
    """Owner line key for a band kind (R-T337-1)."""
    if kind == "plinth":
        return ("PLINTH", None)
    if kind == "storey":
        if floor is None:
            raise BindingError("a storey band needs its floor")
        return ("STOREY", floor)
    if kind == "parapet":
        if roof is None:
            raise BindingError("a parapet band needs its roof")
        return ("PARAPET", roof)
    if kind == "slab_edge":
        return ("SLAB_EDGE", floor)
    raise BindingError(f"unknown band kind {kind!r}")


def band_kind(bottom, top, part, roof=None):
    """Classify one band of a face of `part` (R-T337-1). `roof` is the finished roof level the face rises above when
    it does (its parapet). Returns (kind, owner floor). The storey is chosen by levels only. Refuses a band that
    crosses a level boundary (the F.F.L., the roof, the next F.F.L.)."""
    if top < bottom - EPS:
        raise BindingError("band top below its bottom")
    ffl0 = part.lowest_ffl()
    if top <= ffl0 + EPS:
        return "plinth", None
    if bottom < ffl0 - EPS:
        raise BindingError(f"band {bottom}->{top} crosses the F.F.L. {ffl0}: split it first")
    if roof is not None:
        if bottom >= roof - EPS:
            return "parapet", None
        if top > roof + EPS:
            raise BindingError(f"band {bottom}->{top} crosses the roof level {roof}: split it first")
    owner, nxt = None, None
    for i, (f, z) in enumerate(part.floors):
        if z <= bottom + EPS:
            owner = f
            nxt = part.floors[i + 1][1] if i + 1 < len(part.floors) else part.top
    if top > nxt + EPS:
        raise BindingError(f"band {bottom}->{top} crosses the level {nxt}: split it first")
    return "storey", owner


def hole_on_band(sill_abs, head_abs, bottom, top):
    """R-T337-2: the hole must lie inside its band."""
    if sill_abs is None or head_abs is None:
        return True  # area established, datum HELD: checked by the caller with physical bounds
    if sill_abs < bottom - EPS or head_abs > top + EPS:
        raise BindingError(f"hole {sill_abs}->{head_abs} leaves its band {bottom}->{top}")
    return True


def check_qty(unit, lo, hi, status):
    if status not in STATUSES:
        raise BindingError(f"unknown status {status!r}")
    if status == "UNKNOWN":
        if lo is not None or hi is not None:
            raise BindingError("an UNKNOWN quantity carries no number")
        return
    if lo is None or hi is None:
        if status == "HELD":
            return  # HELD with no bound: blank, never 0
        raise BindingError("a measured quantity needs a value")
    if hi < lo - EPS:
        raise BindingError("range hi below lo")
    if status == "HELD" and hi <= EPS:
        raise BindingError("a HELD quantity is never 0")
    if status != "HELD" and abs(hi - lo) > EPS:
        raise BindingError(f"a range is HELD, not {status}")


@dataclass
class Book:
    """One owner per face key and per opening; lines keep their units apart (R-T337-1 .. 3)."""
    unit_of: dict = field(default_factory=dict)       # line -> unit
    faces: dict = field(default_factory=dict)         # face key -> (line, lo, hi, status)
    openings: dict = field(default_factory=dict)      # opening key -> (line, fixed, lo, hi, status)
    items: dict = field(default_factory=dict)         # item key -> (line, lo, hi, status)

    def line(self, name, unit):
        if self.unit_of.get(name, unit) != unit:
            raise BindingError(f"line {name} is {self.unit_of[name]}, not {unit}")
        self.unit_of[name] = unit

    def add_face(self, key, line, lo, hi, status):
        if key in self.faces:
            raise BindingError(f"face {key} already owned by {self.faces[key][0]}")
        if self.unit_of.get(line) != "m2":
            raise BindingError(f"face {key}: line {line} is not an m2 face line")
        check_qty("m2", lo, hi, status)
        self.faces[key] = (line, lo, hi, status)

    def add_opening(self, key, face_key, fixed, lo, hi, status):
        if key in self.openings:
            raise BindingError(f"opening {key} deducted twice")
        if face_key not in self.faces:
            raise BindingError(f"opening {key}: its face {face_key} is not booked")
        line, f_lo, f_hi, _st = self.faces[face_key]
        cap = f_hi if f_hi is not None else 0.0
        if (hi if hi is not None else fixed) > cap + EPS:
            raise BindingError(f"opening {key}: hole larger than its band")
        if status == "HELD" and (lo is None or hi is None or hi <= EPS):
            raise BindingError(f"opening {key}: a HELD hole needs a bound, never 0")
        self.openings[key] = (line, fixed, lo, hi, status)

    def add_item(self, key, line, unit, lo, hi, status):
        if key in self.items:
            raise BindingError(f"item {key} already booked")
        self.line(line, unit)
        check_qty(unit, lo, hi, status)
        self.items[key] = (line, lo, hi, status)

    def totals(self, line):
        """(gross lo, gross hi, deduct fixed, deduct held lo, deduct held hi, net lo, net hi, n faces, n openings)."""
        g_lo = g_hi = 0.0
        n = 0
        for _k, (ln, lo, hi, _st) in self.faces.items():
            if ln == line:
                n += 1
                g_lo += lo or 0.0
                g_hi += hi or 0.0
        d_fix = d_lo = d_hi = 0.0
        m = 0
        for _k, (ln, fixed, lo, hi, st) in self.openings.items():
            if ln == line:
                m += 1
                if st == "HELD":
                    d_lo += lo
                    d_hi += hi
                else:
                    d_fix += fixed
        return g_lo, g_hi, d_fix, d_lo, d_hi, g_lo - d_fix - d_hi, g_hi - d_fix - d_lo, n, m
