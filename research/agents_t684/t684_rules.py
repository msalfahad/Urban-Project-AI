"""T-684 rules: what a turn square of a dog-leg stair IS on a given storey (winders, a flat landing, or a lower turn
seen through the open shaft), from the drawings only. Research module, unwired; no engine, rule-version or knowledge
file is changed. Proposed rules (labelled, a rule change is a new rule version when adopted):

R-T684-1 (turn element, any villa): radiating lines drawn in a turn square on a storey's plan are NOT by themselves
  winders of that storey (owner S-9: winders are never generated; only drawn ones count, and a drawn winder is a
  riser of that storey). The square is classified from three independent drawn facts of THAT storey:
  (a) the riser budget: printed storey height H, the flights' risers n_i (section count) and the riser r measured on
      the section; the turn holds n_turn = (H - sum n_i * r) / r risers, which must be a whole number (+-0.25);
  (b) the section through the stair: the number of risers it draws in the turn zone (None = not readable);
  (c) the lower storey: whether the same radiating lines (same place, angles and lengths, +-10 mm / 1 deg) are drawn
      as that storey's turn AND the zone is open between the two (no floor, landing or slab drawn below the cut).
  WINDERS only when (a) leaves >= 2 risers for the turn and (b) draws the same number. A flat LANDING when (a) leaves
  0 risers, or 1 (a SPLIT-LEVEL landing with one closing riser), and (b) draws no riser beyond that closing riser.
  Lines that coincide with the lower storey's turn through an open zone are SEEN_BELOW: the physical winders belong
  to the lower storey and are counted once there. Anything else is UNDETERMINED (HELD, never 0, never a landing by
  default).
R-T684-2 (layers): a line on an annotation layer (text, dimension, hatch, grid) is never a winder; a line on the
  hidden / overhead layer is a winder only through R-T684-1 (a)+(b): hidden is how a plan draws its own turn ABOVE
  the cut (the development villa's GF turn), so it neither proves nor refutes winders.
R-T684-3 (dependent lines): the element decision moves the concrete (turn wedges vs a landing plate), tread / riser /
  nosing counts, skirting along the turn walls and the shaft finish bands as ONE package; a finish line never
  re-decides the element on its own.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

UNITS = {"m": 1.0, "cm": 0.01, "mm": 0.001}
ANNOTATION_ROLES = {"ANNOTATION", "DIMENSION", "TEXT", "HATCH", "GRID"}
LAYER_ROLES = {"VISIBLE", "HIDDEN"} | ANNOTATION_ROLES


def to_m(value, unit):
    """a length in metres; an unknown unit is refused (never guessed)."""
    if value is None:
        return None
    if unit not in UNITS:
        raise ValueError(f"unit {unit!r} refused: give m, cm or mm")
    return float(value) * UNITS[unit]


@dataclass(frozen=True)
class Seg:
    """one drawn line in the turn square, coordinates relative to the square's inner corner (metres)."""
    x1: float
    y1: float
    x2: float
    y2: float
    role: str = "VISIBLE"            # VISIBLE / HIDDEN / an annotation role

    def length(self):
        return math.hypot(self.x2 - self.x1, self.y2 - self.y1)

    def angle(self):
        return math.degrees(math.atan2(self.y2 - self.y1, self.x2 - self.x1)) % 180.0


def radiating(segs, tol=0.06):
    """the non-orthogonal lines of the square that start at (or within tol of) the inner corner (0, 0)."""
    out = []
    for s in segs:
        a = s.angle()
        if min(a % 90.0, 90.0 - a % 90.0) < 1.0:
            continue
        if min(math.hypot(s.x1, s.y1), math.hypot(s.x2, s.y2)) <= tol:
            out.append(s)
    return out


def _key(s):
    # orientation-free description of a radiating line: its far end relative to the corner
    p = (s.x2, s.y2) if math.hypot(s.x2, s.y2) >= math.hypot(s.x1, s.y1) else (s.x1, s.y1)
    return p


def coincide(upper, lower, tol_m=0.010):
    """True when every radiating line of the upper storey has a twin in the lower storey's turn (same far end within
    tol, i.e. same angle and length) and the counts agree. Coordinates are in each storey's own square frame, so a
    mirrored or rotated plan is compared after the caller maps both squares to the same corner frame."""
    if not upper or len(upper) != len(lower):
        return False
    used = set()
    for u in upper:
        pu = _key(u)
        hit = None
        for i, lo in enumerate(lower):
            if i in used:
                continue
            pl = _key(lo)
            if math.hypot(pu[0] - pl[0], pu[1] - pl[1]) <= tol_m:
                hit = i
                break
        if hit is None:
            return False
        used.add(hit)
    return True


@dataclass
class StoreyTurn:
    storey: str
    height_m: float | None                     # printed storey height (H)
    flight_risers: list                        # risers of each straight flight of the storey (section count)
    riser_m: float | None                      # riser measured on the section
    segs: list = field(default_factory=list)   # every drawn line in the turn square (Seg)
    section_turn_risers: int | None = None     # risers the section draws in the turn zone (None = not readable)
    lower_turn_segs: list | None = None        # the lower storey's turn lines (Seg), same corner frame
    open_below: bool | None = None             # no floor / landing / slab drawn below the cut in the zone


def budget(t: StoreyTurn):
    """risers left for the turn: (H - sum n_i r) / r; None when a datum is missing; refused when not whole."""
    if t.height_m is None or t.riser_m is None or not t.flight_risers or any(n is None for n in t.flight_risers):
        return None, "missing datum (storey height, riser or a flight count): HELD"
    if t.height_m <= 0 or t.riser_m <= 0:
        raise ValueError("storey height and riser must be > 0")
    rest = (t.height_m - sum(t.flight_risers) * t.riser_m) / t.riser_m
    n = round(rest)
    if abs(rest - n) > 0.25 or n < 0:
        return None, f"riser budget not whole ({rest:.3f} risers): the readings disagree, HELD"
    return n, f"(H {t.height_m:.3f} - {sum(t.flight_risers)} x {t.riser_m:.4f}) / {t.riser_m:.4f} = {rest:.3f} -> {n}"


def classify(t: StoreyTurn):
    """R-T684-1 / -2: the element of the turn square on this storey, with the reasons. Never returns a number for a
    missing datum; UNDETERMINED is HELD."""
    for s in t.segs:
        if s.role not in LAYER_ROLES:
            raise ValueError(f"layer role {s.role!r} refused")
    reasons = []
    drawing = [s for s in t.segs if s.role not in ANNOTATION_ROLES]
    ignored = [s for s in t.segs if s.role in ANNOTATION_ROLES]
    if ignored:
        reasons.append(f"{len(ignored)} line(s) on an annotation layer ignored (R-T684-2)")
    rad = radiating(drawing)
    n_turn, why = budget(t)
    reasons.append("riser budget: " + why)
    seen_below = bool(rad) and t.open_below is True and t.lower_turn_segs is not None \
        and coincide(rad, radiating(t.lower_turn_segs))
    if rad:
        reasons.append(f"{len(rad)} radiating line(s) from the inner corner ({sorted({s.role for s in rad})})")
    if seen_below:
        reasons.append("the radiating lines coincide line for line with the lower storey's turn through an open zone: "
                       "SEEN_BELOW (counted once on the lower storey)")
    if n_turn is None:
        return dict(element="UNDETERMINED", status="HELD", turn_risers=None, lines_are="SEEN_BELOW" if seen_below
                    else ("UNRESOLVED" if rad else None), reasons=reasons)
    sec = t.section_turn_risers
    if sec is None:
        reasons.append("section: turn zone not readable")
    else:
        reasons.append(f"section: {sec} riser(s) drawn in the turn zone")
    if n_turn >= 2:
        if sec == n_turn and rad and not seen_below:
            return dict(element="WINDERS", status="DRAWN", turn_risers=n_turn, lines_are="WINDERS", reasons=reasons)
        reasons.append("winders need the budget AND the section AND own (not seen-below) lines")
        return dict(element="UNDETERMINED", status="HELD", turn_risers=n_turn,
                    lines_are="SEEN_BELOW" if seen_below else ("UNRESOLVED" if rad else None), reasons=reasons)
    # n_turn 0 or 1: no room for winders on this storey
    if sec is not None and sec != n_turn:
        reasons.append("section and budget disagree")
        return dict(element="UNDETERMINED", status="HELD", turn_risers=n_turn,
                    lines_are="SEEN_BELOW" if seen_below else ("UNRESOLVED" if rad else None), reasons=reasons)
    if rad and not seen_below:
        reasons.append("radiating lines that are neither this storey's risers nor a seen-below turn: CONFLICT")
        return dict(element="LANDING_SPLIT" if n_turn == 1 else "LANDING", status="CONFLICT", turn_risers=n_turn,
                    lines_are="UNRESOLVED", reasons=reasons)
    return dict(element="LANDING_SPLIT" if n_turn == 1 else "LANDING", status="DRAWN", turn_risers=n_turn,
                lines_are="SEEN_BELOW" if seen_below else None, reasons=reasons)
