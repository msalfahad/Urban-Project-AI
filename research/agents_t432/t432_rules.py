"""T-432 length basis of a whole-stair plate row: developed-profile constructions of a multi-piece stair (any villa).

Research module (lane S). It changes no engine module, candidate line, rule or knowledge version and releases nothing.

Question (ERS s.2.4): a freelancer row prints ONE length L for a whole stair (curved and straight flights, landings).
Is L one stated construction of the DRAWN stair (no free parameter), as his ST-01 length was the developed profile
run + n x riser of one flight (T-417, R-T417-1)? A construction is a fixed pair (PATH, BASIS):

  PATH  where the plan length is measured on every piece, the same rule on every piece:
        INNER  the inner opening edge (curved: arc at r_in; straight: the void-side lane edge; landing: inner corner)
        CENTRE the lane centreline of each piece (curved: arc at (r_in + r_out) / 2; landing: L-path between the two
               flights' centrelines)
        RISERS the polyline through the midpoints of the drawn riser lines (drawn points only, no convention)
        OUTER  the outer edge (curved: arc at r_out up to its end, then the outer straight edge; landing: the two outer
               sides)
  BASIS how the rise enters
        PLAN       plan length only
        PROFILE    plan + every drawn riser once (treads + riser faces; T-417's exact ST-01 basis)
        INCLINED   each flight's own sqrt(plan^2 + rise^2), landings flat
        PROFILE_LANDING_IN_BOTH  plan + rise with each landing counted in both adjoining flights (a sibling-row
                   construction: a landing shared by two flight rows)
  COUNT constructions (no path): n_treads x printed going (+ rise), for rows built from a tread count.

Rules (R-T432-n), every villa:
  R-T432-1 ONE PATH PER CONSTRUCTION: a construction measures every piece on the same path; mixing paths between pieces
           (e.g. outer on the curve, centre on the straight) is a free parameter and is refused (MixedPathError).
  R-T432-2 A LANDING HAS NO RISE: a landing piece carries 0 risers; a construction that adds a rise on a landing (the
           arriving flight's rise counted again at the landing) is refused (RiseOnLandingError). Every drawn riser is
           counted once in a PROFILE basis: the sum of the pieces' risers must equal the stair's drawn riser count.
  R-T432-3 DEVELOPED ARC: a curved piece's plan length is the arc on its path (R-T415-1); a chord is refused.
  R-T432-4 EXACT OR NOTHING: a row length is TRACED only when exactly ONE construction reproduces it within the row's
           printed precision tolerance (default 0.0005 m: a length printed as 16.4 is read as 16.400, as T-417 read
           5.3 as 5.300 and reproduced it to 0 mm); two or more -> AMBIGUOUS; none -> UNRESOLVED with every
           construction and its misfit listed. The nearest construction is never chosen because it is nearest (ERS s.2.4).
  R-T432-5 RESTATEMENT: an AREA_BEYOND_DRAWN term (R-T415-6) moves out of UNRESOLVED only with a TRACED construction;
           otherwise it stays whole (never split by a nearest construction, never 0).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

PATHS = ("INNER", "CENTRE", "RISERS", "OUTER")
BASES = ("PLAN", "PROFILE", "INCLINED", "PROFILE_LANDING_IN_BOTH")
EXACT_TOL = 0.0005


class Refused(ValueError):
    """A construction or input outside the rules."""


class MixedPathError(Refused):
    """R-T432-1."""


class RiseOnLandingError(Refused):
    """R-T432-2."""


class ChordError(Refused):
    """R-T432-3."""


def r6(x):
    return round(float(x) + 0.0, 6)


def _pos(name, v, allow_zero=False):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or math.isnan(v):
        raise Refused(f"{name} must be a number, got {v!r}")
    if v < 0 or (v == 0 and not allow_zero):
        raise Refused(f"{name} must be positive, got {v!r}")
    return float(v)


@dataclass(frozen=True)
class Piece:
    """One drawn piece of a stair in walking order. plan: {path: plan length m}; kind 'curved' | 'straight' |
    'landing'; n_risers: drawn riser lines owned by this piece (a landing owns 0)."""
    id: str
    kind: str
    n_risers: int
    plan: dict
    chord: dict = field(default_factory=dict)  # curved only, information: refused if offered as the plan length

    def __post_init__(self):
        if self.kind not in ("curved", "straight", "landing"):
            raise Refused(f"{self.id}: kind {self.kind!r}")
        if not isinstance(self.n_risers, int) or isinstance(self.n_risers, bool) or self.n_risers < 0:
            raise Refused(f"{self.id}: the number of risers is a drawn whole count, got {self.n_risers!r}")
        if self.kind == "landing" and self.n_risers:
            raise RiseOnLandingError(f"{self.id}: a landing carries no riser (R-T432-2)")
        if self.kind != "landing" and self.n_risers == 0:
            raise Refused(f"{self.id}: a flight without drawn risers")
        for p in PATHS:
            if p not in self.plan:
                raise Refused(f"{self.id}: plan length on path {p} missing (never 0)")
            _pos(f"{self.id} plan {p}", self.plan[p], allow_zero=(self.kind == "landing"))
        for p, c in self.chord.items():
            if self.kind == "curved" and abs(self.plan[p] - c) < 1e-6 and c > 0:
                raise ChordError(f"{self.id}: the chord {c} was given as the plan length on {p} (R-T432-3)")


@dataclass
class Stair:
    pieces: list
    riser: float
    drawn_risers: int
    riser_status: str = ""

    def __post_init__(self):
        _pos("riser", self.riser)
        if self.riser > 0.30:
            raise Refused(f"riser {self.riser} m: millimetres read as metres or not a riser")
        n = sum(p.n_risers for p in self.pieces)
        if n != self.drawn_risers:
            raise Refused(f"pieces own {n} risers, the stair has {self.drawn_risers} drawn (R-T432-2: each once)")
        ids = [p.id for p in self.pieces]
        if len(set(ids)) != len(ids):
            raise Refused("a piece listed twice")

    @property
    def rise(self):
        return self.drawn_risers * self.riser


def length(stair: Stair, path, basis, rise_on_landing=False):
    """One construction (PATH, BASIS). path may be a dict {piece id: path} only to be REFUSED (R-T432-1)."""
    if isinstance(path, dict):
        if len(set(path.values())) > 1:
            raise MixedPathError(f"paths {sorted(set(path.values()))} mixed between pieces (R-T432-1)")
        path = next(iter(path.values()))
    if path not in PATHS or basis not in BASES:
        raise Refused(f"unknown construction {path!r} / {basis!r}")
    if rise_on_landing:
        raise RiseOnLandingError("a rise added on a landing (R-T432-2)")
    plan = sum(p.plan[path] for p in stair.pieces)
    if basis == "PLAN":
        return plan
    if basis == "PROFILE":
        return plan + sum(p.n_risers * stair.riser for p in stair.pieces)
    if basis == "INCLINED":
        return sum(math.hypot(p.plan[path], p.n_risers * stair.riser) if p.kind != "landing" else p.plan[path]
                   for p in stair.pieces)
    # PROFILE_LANDING_IN_BOTH: every interior landing appears in the flight before and the flight after it
    extra = 0.0
    for i, p in enumerate(stair.pieces):
        if p.kind == "landing" and 0 < i < len(stair.pieces) - 1:
            extra += p.plan[path]
    return plan + extra + stair.rise


def count_constructions(n_treads, going, landing_plans, rise):
    """COUNT family: n_treads x going, with / without each landing path and the rise."""
    _pos("going", going)
    if not isinstance(n_treads, int) or n_treads <= 0:
        raise Refused("tread count is a drawn whole count")
    out = {}
    base = n_treads * going
    for lname, lv in [("no landing", 0.0)] + [(f"landing {k}", v) for k, v in landing_plans.items()]:
        out[f"COUNT {n_treads} x {going:g} + {lname}"] = base + lv
        out[f"COUNT {n_treads} x {going:g} + {lname} + rise"] = base + lv + rise
    return out


def flight_profile(stair: Stair, piece_id, path):
    p = next((x for x in stair.pieces if x.id == piece_id), None)
    if p is None or p.kind == "landing":
        raise Refused(f"{piece_id}: not a flight of this stair")
    return p.plan[path] + p.n_risers * stair.riser


def one_length_constructions(stair: Stair):
    """ONE_LENGTH family (R-T417 sibling rule): one flight's own developed profile carried to every flight of the
    stair (n_flights x profile), without and with the landings once on the same path."""
    flights = [p for p in stair.pieces if p.kind != "landing"]
    out = {}
    for f in flights:
        for path in PATHS:
            prof = flight_profile(stair, f.id, path)
            land = sum(p.plan[path] for p in stair.pieces if p.kind == "landing")
            out[f"ONE_LENGTH {len(flights)} x {f.id} / {path} profile"] = len(flights) * prof
            out[f"ONE_LENGTH {len(flights)} x {f.id} / {path} profile + landing"] = len(flights) * prof + land
    return out


def constructions(stair: Stair, n_treads=None, going=None, landing_plans=None):
    out = {}
    for p in PATHS:
        for b in BASES:
            out[f"{p} / {b}"] = length(stair, p, b)
    out.update(one_length_constructions(stair))
    if n_treads is not None:
        out.update(count_constructions(n_treads, going, landing_plans or {}, stair.rise))
    return {k: r6(v) for k, v in out.items()}


def classify(his_len, cands: dict, tol=EXACT_TOL):
    """R-T432-4."""
    _pos("his length", his_len)
    table = sorted(([k, v, r6(v - his_len)] for k, v in cands.items()), key=lambda t: (abs(t[2]), t[0]))
    exact = [t for t in table if abs(t[2]) <= tol]
    if len(exact) == 1:
        state = "TRACED"
    elif len(exact) > 1:
        state = "AMBIGUOUS"
    else:
        state = "UNRESOLVED"
    return dict(state=state, exact=[t[0] for t in exact], nearest=table[0], table=table, tol=tol)


def restate_area_beyond(term_m3, his_len, his_w, his_t, drawn_area, result, construction_terms=None):
    """R-T432-5: the AREA_BEYOND_DRAWN m3 term. TRACED -> split into named terms (must close); else whole."""
    term = float(term_m3)
    check = his_t * (his_w * his_len - drawn_area)
    if abs(check + term) > 1e-6 and abs(check - term) > 1e-6:
        raise Refused(f"term {term} is not his t x (area - drawn) = {check}")
    if result["state"] != "TRACED":
        return dict(state=result["state"], terms=[dict(kind="UNRESOLVED", m3=r6(term))], unexplained_m3=r6(term))
    terms = construction_terms or []
    s = sum(t["m3"] for t in terms)
    if abs(s - term) > 1e-6:
        raise Refused(f"traced terms {s} do not close {term}")
    return dict(state="TRACED", terms=terms, unexplained_m3=0.0)
