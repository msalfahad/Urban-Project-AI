"""T-393: railing scope reconciliation, run by run (any villa; research module, not wired into any method).

Builds on the Checker-merged T-164 census (research/agents_t164, UP-STAIR-012 installed 3D path, UP-STAIR-013 wall
handrail only where shown) and adds the three things T-164 left as one block:

1. Per-SEGMENT release (owner stair rule S-9 (4), OWNER_RULE_STAIRS_2026-10-24: "Release BOQ quantities individually
   according to their own required evidence"). A run is a list of segments; each segment carries its own evidence and
   status. A run with one undetermined turn no longer holds its drawn flights: the flights are DRAWING-CONFIRMED, the turn
   is HELD with the exact missing fact. HELD is None (blank), never 0, never a range in the measured column.
2. Turns around a stair well (rule R-T393-1 below): the plan path of a well-end turn is the band centreline from the
   last riser of one flight to the first riser of the next. A turn is measurable ONLY when its rise is known and either
   zero (both ends at one level) or its rail profile is drawn. A turn that contains a rise (winders, a closing riser on
   the landing) with no drawn profile is HELD: the plan length and the rise are reported, the installed length is not.
3. Single binding (R-T393-2): one physical turn / landing return is bound to exactly one segment id. Listing the same
   return under two flights (the common double count at a half landing) is refused. Two held parts that are the same
   physical turn (e.g. winders + quarter landing at one well end) are one segment.
4. Guard side (R-T393-3): a guard is accepted only on an OPEN side, or on a walled side where a rail is drawn / specified
   (UP-STAIR-013). An undrawn guard on a walled side is refused.

Reconciliation helper (ERS s.2.4): a difference to another party's figure is split into named, measured causes; what
is left is printed as UNEXPLAINED, never absorbed. A candidate scope that comes close is reported, never adopted.

Pure functions; no file or drawing access. `python3 -I research/agents_t393/t393_railing_runs.py --check` runs the
hand-calculated synthetic fixture (Villa D, not the development villa) with its adverse cases.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass, field

CONFIRMED, HELD, UNKNOWN, EXCLUDED = "DRAWING-CONFIRMED", "HELD", "UNKNOWN", "EXCLUDED"
STATUSES = (CONFIRMED, HELD, UNKNOWN, EXCLUDED)
MAX_PLAUSIBLE_M = 100.0   # a single railing segment longer than this is almost certainly mm read as m


class RunInputError(ValueError):
    """A required fact is missing or contradictory (the segment is HELD or refused, never silently 0)."""


@dataclass(frozen=True)
class Segment:
    run: str
    seg_id: str
    what: str
    length_m: float | None          # installed length; None when HELD / UNKNOWN / EXCLUDED
    status: str
    source: str
    missing: str = ""               # exact missing fact for HELD / UNKNOWN
    plan_m: float | None = None     # plan length where drawn (reported beside a HELD length, never billed)
    rise_m: float | None = None
    binds: tuple = field(default_factory=tuple)   # physical element keys bound by this segment (single binding)

    def __post_init__(self):
        if self.status not in STATUSES:
            raise RunInputError(f"{self.seg_id}: unknown status {self.status!r}")
        if self.status == CONFIRMED:
            if self.length_m is None:
                raise RunInputError(f"{self.seg_id}: DRAWING-CONFIRMED needs a length")
            if not (0.0 < self.length_m <= MAX_PLAUSIBLE_M):
                raise RunInputError(f"{self.seg_id}: length {self.length_m} m implausible (unit?)")
        else:
            if self.length_m is not None:
                raise RunInputError(f"{self.seg_id}: a {self.status} segment carries no length (blank, never 0)")
            if self.status in (HELD, UNKNOWN) and not self.missing:
                raise RunInputError(f"{self.seg_id}: {self.status} needs the exact missing fact")


# ---------------------------------------------------------------- geometry

def check_m(value, name):
    if value is None:
        raise RunInputError(f"{name}: missing (held, never 0)")
    v = float(value)
    if v < 0 or v > MAX_PLAUSIBLE_M:
        raise RunInputError(f"{name}: {v} m out of range (unit?)")
    return v


def flight_pitch(risers: int, riser: float, going: float) -> float:
    """UP-STAIR-012 fallback when rail extents are not drawn: nosing pitch line H = (n-1) g, V = (n-1) r."""
    if risers is None or risers < 2:
        raise RunInputError("a flight needs at least two risers for a pitch line")
    r, g = check_m(riser, "riser"), check_m(going, "going")
    return math.hypot((risers - 1) * g, (risers - 1) * r)


def well_end_turn_plan(band_outer_a: float, band_outer_b: float, band_width: float,
                       riser_a: float, riser_b: float, band_end: float) -> float:
    """R-T393-1 plan path of a well-end turn along the band CENTRELINE.

    Coordinates are along two axes of the drawing: band_outer_a / band_outer_b are the outer edges of the two bands
    across the well (axis u), band_end the outer edge of the closing band (axis v), riser_a / riser_b the last riser of
    one flight and the first riser of the next (axis v). Mirror / rotation / translation invariant (only differences)."""
    w = check_m(band_width, "band width")
    across = abs(band_outer_b - band_outer_a) - w            # centre of band a to centre of band b
    if across <= 0:
        raise RunInputError("bands overlap: no well")
    end_c = band_end - math.copysign(w / 2.0, band_end - riser_a)   # centreline of the closing band
    leg_a, leg_b = abs(end_c - riser_a), abs(end_c - riser_b)
    return across + leg_a + leg_b


def turn_segment(run: str, seg_id: str, what: str, plan_m: float, rise_m: float | None, profile_drawn: bool,
                 source: str, binds: tuple, missing_if_held: str) -> Segment:
    """R-T393-1: a turn is measured only when its rise is known and zero, or its rail profile is drawn."""
    p = check_m(plan_m, f"{seg_id} plan")
    if rise_m is None:
        return Segment(run, seg_id, what, None, HELD, source, missing_if_held or "rise inside the turn not printed",
                       plan_m=p, rise_m=None, binds=binds)
    r = check_m(rise_m, f"{seg_id} rise")
    if r == 0.0:
        return Segment(run, seg_id, what, p, CONFIRMED, source, plan_m=p, rise_m=0.0, binds=binds)
    if profile_drawn:
        return Segment(run, seg_id, what, math.hypot(p, r), CONFIRMED, source, plan_m=p, rise_m=r, binds=binds)
    return Segment(run, seg_id, what, None, HELD, source, missing_if_held, plan_m=p, rise_m=r, binds=binds)


def guard_segment(run: str, seg_id: str, what: str, length_m: float, side: str, drawn: bool, source: str,
                  binds: tuple) -> Segment:
    """R-T393-3: a guard stands on an OPEN side; on a WALL side only where a rail is drawn (UP-STAIR-013)."""
    if side not in ("OPEN", "WALL"):
        raise RunInputError(f"{seg_id}: side must be OPEN or WALL")
    if not drawn:
        raise RunInputError(f"{seg_id}: guard not drawn on a {side} side: not a segment (a render or a rule never "
                            "makes one; WALL: WALL_HANDRAIL_NOT_SPECIFIED, UP-STAIR-013)")
    return Segment(run, seg_id, what, check_m(length_m, seg_id), CONFIRMED, source, binds=binds)


def undrawn_wall_guard(seg_id: str):
    """An undrawn rail on a walled side is refused outright (never a quantity, never a HELD placeholder)."""
    raise RunInputError(f"{seg_id}: guard on a walled side not drawn: WALL_HANDRAIL_NOT_SPECIFIED (UP-STAIR-013)")


# ---------------------------------------------------------------- run table

def check_single_binding(segments) -> None:
    """R-T393-2: every physical element key is bound by exactly one segment."""
    seen = {}
    for s in segments:
        for k in s.binds:
            if k in seen:
                raise RunInputError(f"{k} bound twice: {seen[k]} and {s.seg_id} (a landing return counted on both "
                                    "flights)")
            seen[k] = s.seg_id
    ids = [s.seg_id for s in segments]
    if len(ids) != len(set(ids)):
        raise RunInputError("duplicate segment id")


def totals(segments) -> dict:
    """Per-status totals; HELD / UNKNOWN never contribute 0, they are counted and listed."""
    check_single_binding(segments)
    out = {"confirmed_lm": 0.0, "held": [], "unknown": [], "excluded": []}
    for s in segments:
        if s.status == CONFIRMED:
            out["confirmed_lm"] += s.length_m
        elif s.status == HELD:
            out["held"].append(s.seg_id)
        elif s.status == UNKNOWN:
            out["unknown"].append(s.seg_id)
        else:
            out["excluded"].append(s.seg_id)
    out["confirmed_lm"] = round(out["confirmed_lm"], 6)
    return out


def reconcile(ours: float, theirs: float, causes) -> dict:
    """ERS s.2.4: difference ours - theirs split into named measured causes; the remainder is UNEXPLAINED."""
    diff = float(ours) - float(theirs)
    named = sum(float(v) for _, v in causes)
    return {"diff": round(diff, 6), "causes": [(n, round(float(v), 6)) for n, v in causes],
            "unexplained": round(diff - named, 6)}


# ---------------------------------------------------------------- synthetic fixture (Villa D, hand-calculated)

def villa_d():
    """Dog-leg stair, floor to floor 3.20 m: two flights of 10 risers 0.160 m, going 0.280 m, a level half landing;
    bands 0.05 m on each side of a 0.20 m well; a 3.00 m gallery guard over the upper-floor opening.

    Hand calculation: pitch line H = 9 x 0.280 = 2.520, V = 9 x 0.160 = 1.440, L = sqrt(2.520^2 + 1.440^2) = 2.902413 m
    per flight. Turn: band outer edges u = 0 and 0.30 -> centres 0.025 / 0.275 -> across 0.250; closing band outer edge
    v = 3.00, centreline 2.975; last riser of flight 1 and first riser of flight 2 at v = 2.950 -> legs 0.025 + 0.025;
    turn 0.300 m, level (both ends on the landing). Gallery guard 3.000 m horizontal.
    Total = 2 x 2.902413 + 0.300 + 3.000 = 9.104826 m."""
    run = "RD-1"
    segs = [Segment(run, "F1", "flight 1 inner balustrade", flight_pitch(10, 0.160, 0.280), CONFIRMED, "plan + section",
                    binds=("F1",)),
            turn_segment(run, "T1", "half-landing turn round the well", well_end_turn_plan(0.0, 0.30, 0.05, 2.95,
                         2.95, 3.00), 0.0, False, "plan", ("LANDING-RETURN-1",), ""),
            Segment(run, "F2", "flight 2 inner balustrade", flight_pitch(10, 0.160, 0.280), CONFIRMED, "plan + section",
                    binds=("F2",)),
            guard_segment(run, "G1", "upper-floor gallery guard", 3.000, "OPEN", True, "plan", ("GALLERY-1",))]
    return segs


def _check() -> int:
    ok = True

    def eq(a, b, name, tol=1e-6):
        nonlocal ok
        good = abs(a - b) <= tol
        ok &= good
        print(("PASS " if good else "FAIL ") + f"{name}: {a:.6f} vs {b:.6f}")

    t = totals(villa_d())
    eq(t["confirmed_lm"], 9.104826, "Villa D total")
    eq(flight_pitch(10, 0.160, 0.280), 2.902413, "flight pitch line")
    # mirror / rotation: same turn with negated / swapped axes
    eq(well_end_turn_plan(0.0, -0.30, 0.05, -2.95, -2.95, -3.00), 0.300, "turn mirrored")
    eq(well_end_turn_plan(0.0, 0.30, 0.05, 0.05, 0.05, 0.00), 0.300, "turn at the other end")
    # adverse: landing return bound on both flights
    segs = villa_d() + [Segment("RD-1", "T1b", "same return on flight 2", 0.300, CONFIRMED, "x",
                                binds=("LANDING-RETURN-1",))]
    try:
        totals(segs)
        ok = False
        print("FAIL double-bound landing return accepted")
    except RunInputError:
        print("PASS double-bound landing return refused")
    # adverse: winder turn with a rise and no profile -> HELD, blank, never 0
    w = turn_segment("RD-1", "T2", "winder turn", 0.300, 0.480, False, "plan", ("WINDER-1",),
                     "rail profile over the winders not drawn")
    good = w.status == HELD and w.length_m is None
    ok &= good
    print(("PASS " if good else "FAIL ") + "winder turn without profile HELD (None)")
    try:
        undrawn_wall_guard("W1")
        ok = False
    except RunInputError:
        print("PASS undrawn guard on a walled side refused")
    return 0 if ok else 1


if __name__ == "__main__":
    if "--check" in sys.argv:
        sys.exit(_check())
    print(__doc__)
