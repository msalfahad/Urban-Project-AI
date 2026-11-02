"""T-476: handrails / guardrails along the slope, flight by flight (any villa; research module, not wired into a method).

Builds on the Checker-merged T-164 census (runs) and T-393 (per-segment release, R-T393-1 turns, R-T393-2 single
binding, R-T393-3 guard side). What this module adds:

1. Flight census (ERS s.2.1, physical element first). Every flight is described by its own goings, going and riser;
   its pitch line (first nosing to last nosing) is n_goings x going in plan and n_goings x riser in rise, and the rail
   on the slope is hypot(plan, rise) (UP-STAIR-012 v2.0.0, installed 3D path). Each SIDE of a flight is OPEN or WALL:
     OPEN + rail drawn      -> guard on the slope, family B7-09 (FIN.RAILING), DRAWING-CONFIRMED
     OPEN + rail not drawn  -> HELD (designer item: what stands there), length None, never 0
     WALL + wall rail drawn -> wall-mounted handrail, family B7-10 (FIN.HANDRAIL)
     WALL + none drawn      -> NOT_APPLICABLE (UP-STAIR-013: a wall handrail only where shown / specified)
   A side whose guard is drawn at the FLOOR level beside the flight (a floor-edge band, horizontal) is not a rail on the
   slope: it is a horizontal guard (R-T476-1).
2. R-T476-1 slope vs level: an INCLINED segment is billed only as hypot(plan, rise) with rise > 0; submitting the plan
   length of an inclined segment as its installed length is refused; a HORIZONTAL segment has rise 0.
3. R-T476-2 one home per physical flight side: the plan reader's per-flight FIN.RAILING lines (UP-STAIR-012 per open
   side) and the census runs describe the same guards. Each reader line is bound to exactly ONE physical flight with
   its reading (PRIMARY, PARTIAL_PRIMARY, SPLIT_PART = the rest of the same flight on the same plan, SEEN_THROUGH_VOID,
   SEEN_THROUGH_OPENING); a physical flight with two primary
   readings is refused; an unbound reader line is refused; a reader line bound to a flight whose sides are all homed in
   run segments is RETIRED (it carries no figure, ever). A reader OPEN / WALL side that differs from the census is
   named (SIDE_DIFFERS), never silently taken.
4. R-T476-3 family of a horizontal guard: a horizontal guard drawn as ONE band continuous with a stair balustrade stays
   in that run (B7-09); a separately drawn floor-edge / roof / balcony / fence band is B13-08 (MET.RAILING.GUARD).

Pure functions; no file or drawing access. `python3 -I research/agents_t476/t476_handrail_runs.py --check` runs the
hand-calculated synthetic fixture (Villa E, not the development villa) with its adverse cases.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass

OPEN, WALL = "OPEN", "WALL"
INCLINED, HORIZONTAL = "INCLINED", "HORIZONTAL"
CONFIRMED, HELD, UNKNOWN, NOT_APPLICABLE = "DRAWING-CONFIRMED", "HELD", "UNKNOWN", "NOT_APPLICABLE"
FAM_STAIR, FAM_WALL, FAM_GUARD = "B7-09", "B7-10", "B13-08"
CODE = {FAM_STAIR: "FIN.RAILING", FAM_WALL: "FIN.HANDRAIL", FAM_GUARD: "MET.RAILING.GUARD"}
READINGS = ("PRIMARY", "PARTIAL_PRIMARY", "SPLIT_PART", "SEEN_THROUGH_VOID", "SEEN_THROUGH_OPENING")
MAX_GOING_M = 0.60        # a going above this is not a stair going (mm read as m, or a landing)
MAX_RISER_M = 0.25
MAX_SEGMENT_M = 100.0


class RailInputError(ValueError):
    """A required fact is missing or contradictory: the item is HELD or refused, never silently 0."""


def _pos(x, name):
    if x is None or not isinstance(x, (int, float)) or isinstance(x, bool) or not math.isfinite(x) or x <= 0:
        raise RailInputError(f"{name}: a positive length in metres is required, got {x!r}")
    return float(x)


@dataclass(frozen=True)
class Flight:
    """One physical flight: n_goings between its first and last nosing (= risers - 1 on a flight that starts and ends
    with a riser), going and riser in metres; plan_m overrides n_goings x going where the rail path is curved (the band
    length between the first and last riser lines, measured on the drawing)."""
    flight_id: str
    risers: int
    riser_m: float
    going_m: float
    plan_m: float | None = None

    def __post_init__(self):
        if not isinstance(self.risers, int) or self.risers < 2:
            raise RailInputError(f"{self.flight_id}: a flight needs at least 2 risers")
        _pos(self.riser_m, f"{self.flight_id} riser")
        _pos(self.going_m, f"{self.flight_id} going")
        if self.riser_m > MAX_RISER_M or self.going_m > MAX_GOING_M:
            raise RailInputError(f"{self.flight_id}: riser {self.riser_m} / going {self.going_m} not a stair "
                                 "(mm read as m?)")
        if self.plan_m is not None:
            _pos(self.plan_m, f"{self.flight_id} plan")

    @property
    def goings(self) -> int:
        return self.risers - 1

    @property
    def plan(self) -> float:
        return self.plan_m if self.plan_m is not None else self.goings * self.going_m

    @property
    def rise(self) -> float:
        return self.goings * self.riser_m

    @property
    def pitch_length(self) -> float:
        return math.hypot(self.plan, self.rise)


def segment_length(kind: str, plan_m: float, rise_m: float | None, length_m: float | None = None) -> float:
    """R-T476-1: the installed length of a segment. INCLINED needs rise > 0 and is hypot(plan, rise); a supplied
    length equal to the plan of an inclined run (the plan projection billed as the slope) is refused. HORIZONTAL has
    rise 0 and is the plan length."""
    plan = _pos(plan_m, "plan")
    if plan > MAX_SEGMENT_M:
        raise RailInputError(f"plan {plan} m: not one railing segment (mm read as m?)")
    if kind == INCLINED:
        if rise_m is None or rise_m <= 0:
            raise RailInputError("INCLINED segment without its rise: the plan length is not the installed length")
        L = math.hypot(plan, rise_m)
        if length_m is not None and abs(length_m - L) > 1e-6:
            if abs(length_m - plan) <= 1e-6:
                raise RailInputError(f"plan length {plan:.3f} billed for an inclined run (installed {L:.6f})")
            raise RailInputError(f"stated length {length_m} != hypot(plan, rise) {L:.6f}")
        return L
    if kind == HORIZONTAL:
        if rise_m not in (None, 0, 0.0):
            raise RailInputError(f"HORIZONTAL segment with rise {rise_m}: it is inclined or a turn (R-T393-1)")
        return plan
    raise RailInputError(f"unknown segment kind {kind!r}")


def classify_side(side: str, rail_drawn: bool, wall_rail_drawn: bool = False, floor_level_band: bool = False):
    """-> (family or None, status). See the module docstring, item 1."""
    if side == OPEN:
        if floor_level_band:
            return FAM_GUARD, CONFIRMED
        return (FAM_STAIR, CONFIRMED) if rail_drawn else (FAM_STAIR, HELD)
    if side == WALL:
        if rail_drawn and not wall_rail_drawn:
            raise RailInputError("a guard on a walled side (R-T393-3): only a wall handrail where drawn")
        return (FAM_WALL, CONFIRMED) if wall_rail_drawn else (None, NOT_APPLICABLE)
    raise RailInputError(f"unknown side kind {side!r}")


@dataclass(frozen=True)
class ReaderLine:
    """A plan-reader per-flight FIN.RAILING line, as the reader saw it (sides OPEN / WALL with plan lengths)."""
    line_id: str
    floor: str
    reader_flight: str
    sides: tuple            # ((side_name, OPEN|WALL, plan_m), ...)
    measured: float | None = None


def bind_reader_lines(readers, bindings, census_sides, homes):
    """R-T476-2. bindings: {line_id: (physical_flight_id, reading)}; census_sides: {flight_id: (OPEN|WALL, ...)} the
    census's own side kinds of that physical flight (from its census rows, not from the reader); the reader's side kinds
    are compared as a multiset (the reader's side_a / side_b carry no compass orientation); homes: {flight_id: [segment
    ids holding its sides]}.
    -> list of dicts (line_id, flight, reading, action RETIRE / HOLD_OPEN, side_check)."""
    seen_primary = {}
    out = []
    for r in readers:
        if r.line_id not in bindings:
            raise RailInputError(f"{r.line_id}: reader line bound to no physical flight")
        fid, reading = bindings[r.line_id]
        if reading not in READINGS:
            raise RailInputError(f"{r.line_id}: unknown reading {reading!r}")
        if r.measured is not None:
            raise RailInputError(f"{r.line_id}: a per-flight line carries a figure beside the runs (same guard twice)")
        if reading in ("PRIMARY", "PARTIAL_PRIMARY"):
            if fid in seen_primary:
                raise RailInputError(f"{fid}: two primary readings ({seen_primary[fid]}, {r.line_id})")
            seen_primary[fid] = r.line_id
        cs = census_sides.get(fid)
        if cs is None:
            raise RailInputError(f"{r.line_id}: physical flight {fid} not in the census")
        rk = tuple(sorted(k for _n, k, _p in r.sides))
        diffs = [] if rk == tuple(sorted(cs)) else [f"reader {rk}, census {tuple(sorted(cs))}"]
        action = "RETIRE" if homes.get(fid) else "HOLD_OPEN"
        out.append({"line_id": r.line_id, "floor": r.floor, "reader_flight": r.reader_flight, "flight": fid,
                    "reading": reading, "action": action, "homes": list(homes.get(fid) or ()),
                    "side_check": "AGREE" if not diffs else "SIDE_DIFFERS: " + "; ".join(diffs)})
    return out


def family_totals(segments):
    """segments: iterable of dicts with family, status, length (None unless CONFIRMED). -> {family: {...}}."""
    t = {}
    for s in segments:
        if s["status"] == NOT_APPLICABLE:
            if s.get("length") is not None:
                raise RailInputError(f"{s['id']}: NOT_APPLICABLE carries a figure")
            continue
        f = t.setdefault(s["family"], {"confirmed_lm": 0.0, "confirmed_n": 0, "held_n": 0, "unknown_n": 0})
        if s["status"] == CONFIRMED:
            if s["length"] is None:
                raise RailInputError(f"{s['id']}: confirmed without a length")
            f["confirmed_lm"] = round(f["confirmed_lm"] + s["length"], 6)
            f["confirmed_n"] += 1
        elif s["status"] in (HELD, UNKNOWN):
            if s.get("length") is not None:
                raise RailInputError(f"{s['id']}: {s['status']} carries a figure (held is blank, never 0)")
            f["held_n" if s["status"] == HELD else "unknown_n"] += 1
    return t


# ---- synthetic fixture: Villa E (hand calculation; not the development villa) -------------------------------------
# Dog-leg, floor-to-floor 3.15 m: flight A and flight B each 9 risers 0.175 m, going 0.280 m.
#   pitch line per flight: 8 goings -> plan 2.240, rise 1.400; hypot = sqrt(5.0176 + 1.9600) = 2.641515 lm
#   inner (well) side OPEN with a drawn band, outer side against the shaft wall, no wall handrail drawn
#   level half-landing turn round a 0.20 m well (both ends at +1.575): 0.250 lm horizontal
#   top floor-edge guard over the opening, ONE band continuous with flight B's: 1.100 lm horizontal (B7-09, R-T476-3)
#   separate floor-edge band beside a short flight (another band): 0.900 lm horizontal (B13-08)
#   B7-09 total = 2 x 2.641515 + 0.250 + 1.100 = 6.633030 lm; B13-08 = 0.900 lm; B7-10 none.

def villa_e():
    A = Flight("E-A", 9, 0.175, 0.280)
    B = Flight("E-B", 9, 0.175, 0.280)
    segs = [
        {"id": "E-A-in", "family": FAM_STAIR, "status": CONFIRMED,
         "length": segment_length(INCLINED, A.plan, A.rise)},
        {"id": "E-B-in", "family": FAM_STAIR, "status": CONFIRMED,
         "length": segment_length(INCLINED, B.plan, B.rise)},
        {"id": "E-TURN", "family": FAM_STAIR, "status": CONFIRMED, "length": segment_length(HORIZONTAL, 0.250, 0.0)},
        {"id": "E-TOP", "family": FAM_STAIR, "status": CONFIRMED, "length": segment_length(HORIZONTAL, 1.100, 0.0)},
        {"id": "E-EDGE", "family": FAM_GUARD, "status": CONFIRMED, "length": segment_length(HORIZONTAL, 0.900, None)},
    ]
    return A, B, segs


def _check() -> int:
    A, B, segs = villa_e()
    ok = abs(A.pitch_length - 2.641515) < 5e-7 and abs(B.pitch_length - 2.641515) < 5e-7
    t = family_totals(segs)
    ok &= abs(t[FAM_STAIR]["confirmed_lm"] - 6.633030) < 5e-6 and abs(t[FAM_GUARD]["confirmed_lm"] - 0.9) < 1e-9
    try:
        segment_length(INCLINED, 2.240, None)
        ok = False
    except RailInputError:
        pass
    print("Villa E", "PASS" if ok else "FAIL", t)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(_check() if "--check" in sys.argv else 0)
