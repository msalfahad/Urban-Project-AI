"""T-410 stair skirting (B7-07 zigzag / B7-08 sloped) per SIDE of every flight and landing: research method, any villa.

Physical element (ERS s.2.1): a stair skirting (owner term توشيح, UP-VOCAB-005) is a strip fixed to a WALL face along a
flight or landing, at the treads. It exists only where a wall face stands beside the stair at that height. An OPEN side
(guarded by a balustrade, B7-09, or an unguarded edge) has nothing to fix it to: never skirted. A landing that lies
inside a floor (arrival at floor level) is room skirting (B3-06), never stair skirting.

Two forms, both owner rules (library 1.4.0):
  UP-STAIR-010 zigzag: the path that follows every riser and every going along the side (sum of rises + goings);
  UP-STAIR-011 sloped: the rake, hypot(plan run, total rise), longer than the plan run.
Which form a project takes is a PROJECT answer (data/registry/OWNER_RULE_REQUESTS.json ORR-007, still an owner rule
request): with no rule, note or detail fixing it, a sloping stretch is HELD by name with both form-conditional figures
reported BESIDE the blank, never as the quantity. A horizontal stretch (a landing at one level) has one length in both
forms (rise 0), so it does not wait on the form.

A side is cut into stretches along the flight's plan run (s = 0 at the first riser line, s = run at the last):
  WALL    a wall face is drawn on the side over [s0, s1] on every plan that cuts the element's storey, no opening drawn
  HELD    a wall is drawn but an opening is drawn in it over [s0, s1] (its height against the flight not established),
          or the element itself is held (winders, a closing riser with no position)
  OPEN    a balustrade / guard band or an unguarded edge: never skirted
  UNKNOWN a band whose role (guard or string) is not established, or no wall face drawn on the side

Riser i stands at s_i = i * going (i = 0 .. n-1; drawn positions, never assumed n-1 goings: the caller passes the drawn
goings count and S-9 (1) holds). In a stretch [s0, s1) the zigzag path is the plan length plus the rises of the risers
standing in it (the last stretch is closed at s = run). The sloped path is the plan length times hypot(run, rise)/run.
A curved side is measured on its developed line (arc length on the side's radius); a chord is refused. Winders are
never generated (owner S-9): a winder region is a HELD stretch with plan length and rise reported, never a path.

Rule R-T410-4 (T-410 r2, Checker finding on the r1 table; any villa): a wall side is ANY vertical finished face on the
side, a wall face OR a column face (structural columns live on their own CAD layer, e.g. S-COL.BON, beside the wall
layer). 'No face drawn' is a finding only when NEITHER layer draws a face over the stretch: a stretch flagged
`no_face` that overlaps a column face is refused (check_faces). A column standing PROUD of the wall line by p adds a
return of length p at each end where the side continues as a WALL face (a horizontal piece, the same in either form,
counted once, `returns_lm`); an end that meets a HELD / UNKNOWN stretch leaves that return held with the stretch; an
end beyond the element's own extent (the column runs past a landing edge) has no return on the element.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

UNIT = "lm"
WALL, HELD, OPEN, UNKNOWN = "WALL", "HELD", "OPEN", "UNKNOWN"
CLASSES = (WALL, HELD, OPEN, UNKNOWN)
CONFIRMED = "DRAWING-CONFIRMED"
FORM_HELD = "HELD-FORM"     # form not fixed for the project (ORR-007): blank with both figures beside
EPS = 1e-9


class SkirtingInputError(ValueError):
    """A refused input: the method never guesses a dimension, a side or a form."""


@dataclass(frozen=True)
class Flight:
    """A straight flight on its drawn geometry (metres). goings = number of drawn goings between first and last riser."""
    fid: str
    risers: int
    riser: float
    goings: int
    going: float

    def __post_init__(self):
        if self.risers <= 0 or self.goings < 0 or self.riser <= 0 or self.going <= 0:
            raise SkirtingInputError(f"{self.fid}: risers / goings / sizes must be positive")
        if self.riser > 0.30 or self.going > 0.60:
            raise SkirtingInputError(f"{self.fid}: riser {self.riser} / going {self.going} are not metres")
        if self.goings > self.risers:
            raise SkirtingInputError(f"{self.fid}: more goings than risers is not a flight")

    @property
    def run(self) -> float:
        return self.goings * self.going

    @property
    def rise(self) -> float:
        return self.risers * self.riser

    def riser_positions(self):
        # n risers on n positions; with goings == risers - 1 the last riser stands at s = run (drawn case);
        # with goings == risers the flight ends on a tread (last going beyond the last riser)
        return [i * self.going for i in range(self.risers)]


@dataclass(frozen=True)
class Stretch:
    """One part of one side. For a flight side s0 / s1 are run positions; for a landing side `plan` is its length."""
    sid: str
    element: str                 # flight id, landing id or turn id
    side: str                    # 'wall side' label (e.g. 'west', 'outer', 'south')
    cls: str
    s0: float = 0.0
    s1: float = 0.0
    plan: float | None = None    # horizontal stretch (landing) plan length
    level_rise: float = 0.0      # rise inside a held stretch (reported only)
    curved_radius: float | None = None
    curved_angle_deg: float | None = None
    chord: float | None = None   # a chord may be passed only to be refused
    cause: str = ""
    evidence: str = ""
    binds: tuple = ()
    railing_run: str = ""        # B7-09 run id on an OPEN side
    face: str = "wall"           # R-T410-4: 'wall' or 'column' (the finished face the strip is fixed to)
    returns_lm: float = 0.0      # R-T410-4: proud-column returns on this stretch, each counted once
    no_face: bool = False        # the stretch's cause is 'no face drawn' (checked against every face layer)

    def __post_init__(self):
        if self.cls not in CLASSES:
            raise SkirtingInputError(f"{self.sid}: class {self.cls!r}")
        if self.cls in (HELD, UNKNOWN) and not self.cause:
            raise SkirtingInputError(f"{self.sid}: a {self.cls} stretch names its cause")
        if self.chord is not None:
            raise SkirtingInputError(f"{self.sid}: a curved side is measured on its developed line, never a chord")
        if self.cls in (WALL, HELD) and self.railing_run:
            raise SkirtingInputError(f"{self.sid}: a guarded side ({self.railing_run}) is never also skirted")
        if self.cls == OPEN and not (self.railing_run or self.cause):
            raise SkirtingInputError(f"{self.sid}: an OPEN side names its guard run or why it is open")
        if self.face not in ("wall", "column"):
            raise SkirtingInputError(f"{self.sid}: face {self.face!r}")
        if self.returns_lm < 0 or (self.returns_lm > 0 and self.cls != WALL):
            raise SkirtingInputError(f"{self.sid}: returns are counted only on a WALL stretch, never negative")
        if self.no_face and self.cls != UNKNOWN:
            raise SkirtingInputError(f"{self.sid}: a 'no face' stretch is UNKNOWN, never {self.cls}")


@dataclass(frozen=True)
class Face:
    """A finished vertical face read on one side (element, side) over [s0, s1] (run or landing-local positions).
    kind 'wall' or 'column'; proud = how far a column face stands in front of the wall line (0 = flush)."""
    element: str
    side: str
    kind: str
    s0: float
    s1: float
    proud: float = 0.0
    ref: str = ""

    def __post_init__(self):
        if self.kind not in ("wall", "column") or self.s1 <= self.s0 or self.proud < 0:
            raise SkirtingInputError(f"face {self.ref}: kind / extent / projection")
        if self.proud > 0.30:
            raise SkirtingInputError(f"face {self.ref}: projection {self.proud} is not metres")


def _flight_stretch_paths(f: Flight, s0: float, s1: float, last: bool):
    if s0 < -EPS or s1 > f.run + EPS or s1 < s0 - EPS:
        raise SkirtingInputError(f"{f.fid}: stretch [{s0}, {s1}] outside the run 0 .. {f.run}")
    n = sum(1 for s in f.riser_positions() if s0 - EPS <= s < s1 - EPS or (last and abs(s - s1) <= EPS))
    plan = s1 - s0
    zig = plan + n * f.riser
    slope = plan * (math.hypot(f.run, f.rise) / f.run) if f.run > 0 else None
    return plan, n, zig, slope


def measure(flights: dict, stretches: list) -> list:
    """Every stretch -> one row: plan, risers inside, zigzag and sloped figures, quantity and status.

    Quantity: horizontal WALL stretch -> its length (form-independent), CONFIRMED; sloping WALL stretch -> blank,
    form HELD (both figures beside); HELD / UNKNOWN -> blank (never 0); OPEN -> no skirting (0 by rule, not missing).
    """
    rows, seen = [], set()
    by_el: dict = {}
    for st in stretches:
        if st.sid in seen:
            raise SkirtingInputError(f"duplicate stretch id {st.sid}")
        seen.add(st.sid)
        by_el.setdefault((st.element, st.side), []).append(st)
    # last stretch of each flight side is closed at s = run
    last_of = {}
    for key, sts in by_el.items():
        if key[0] in flights:
            last_of[key] = max(sts, key=lambda x: x.s1).sid
    for st in stretches:
        f = flights.get(st.element)
        if st.curved_radius is not None:
            if st.curved_angle_deg is None or st.curved_radius <= 0:
                raise SkirtingInputError(f"{st.sid}: curved side needs radius and swept angle")
            plan, n, zig, slope = st.curved_radius * math.radians(st.curved_angle_deg), None, None, None
        elif f is not None:
            plan, n, zig, slope = _flight_stretch_paths(f, st.s0, st.s1, last_of[(st.element, st.side)] == st.sid)
        else:
            plan = st.plan if st.plan is not None else (st.s1 - st.s0 if st.s1 > st.s0 else None)
            if plan is None or plan < 0:
                raise SkirtingInputError(f"{st.sid}: landing stretch needs its plan length")
            n = 0
            zig = plan + st.level_rise if st.level_rise == 0 else None
            slope = plan if st.level_rise == 0 else None
        horizontal = f is None and st.curved_radius is None and st.level_rise == 0
        if st.returns_lm:              # R-T410-4: horizontal return pieces, the same in either form
            zig = None if zig is None else zig + st.returns_lm
            slope = None if slope is None else slope + st.returns_lm
        if st.cls == WALL:
            if horizontal:
                qty, status, form = plan + st.returns_lm, CONFIRMED, "HORIZONTAL (form-independent)"
            else:
                qty, status, form = None, FORM_HELD, "FORM HELD (ORR-007): zigzag UP-STAIR-010 or sloped UP-STAIR-011"
        elif st.cls == OPEN:
            qty, status, form = 0.0, "NOT_SKIRTED (open side)", ""
            n, zig, slope = None, None, None
        else:
            qty, status, form = None, st.cls, ""
        rows.append({
            "sid": st.sid, "element": st.element, "side": st.side, "class": st.cls,
            "plan_lm": round(plan, 6), "risers_in": n,
            "zigzag_lm": None if zig is None else round(zig, 6),
            "sloped_lm": None if slope is None else round(slope, 6),
            "level_rise_m": st.level_rise, "qty_lm": None if qty is None else round(qty, 6),
            "status": status, "form": form, "railing_run": st.railing_run, "cause": st.cause,
            "evidence": st.evidence, "binds": "|".join(st.binds),
            "face": st.face if st.cls == WALL else "", "returns_lm": round(st.returns_lm, 6),
        })
    check(rows, flights, stretches)
    return rows


def check(rows: list, flights: dict, stretches: list) -> None:
    """Invariants: held never 0; an open side never skirted; one physical side piece binds once; each flight side
    is covered once, without gap or overlap, when it is listed."""
    binds = {}
    for r in rows:
        if r["class"] in (HELD, UNKNOWN) and r["qty_lm"] is not None:
            raise SkirtingInputError(f"{r['sid']}: a {r['class']} stretch carries no number (never 0)")
        if r["class"] == OPEN and r["qty_lm"] not in (0.0, None):
            raise SkirtingInputError(f"{r['sid']}: an open side is never skirted")
        for b in filter(None, r["binds"].split("|")):
            if b in binds:
                raise SkirtingInputError(f"{b} bound twice ({binds[b]}, {r['sid']})")
            binds[b] = r["sid"]
    sides: dict = {}
    for st in stretches:
        if st.element in flights and st.curved_radius is None:
            sides.setdefault((st.element, st.side), []).append(st)
    for (el, side), sts in sides.items():
        sts = sorted(sts, key=lambda x: x.s0)
        pos = 0.0
        for st in sts:
            if abs(st.s0 - pos) > 1e-6:
                raise SkirtingInputError(f"{el} {side}: gap or overlap at s = {pos} ({st.sid} starts {st.s0})")
            pos = st.s1
        if abs(pos - flights[el].run) > 1e-6:
            raise SkirtingInputError(f"{el} {side}: side covered to {pos}, run {flights[el].run}")


def _side_stretches(stretches, element, side):
    out = []
    for st in stretches:
        if st.element == element and st.side == side and st.curved_radius is None:
            s0, s1 = (st.s0, st.s1) if st.s1 > st.s0 else (0.0, st.plan or 0.0)
            out.append((s0, s1, st))
    return sorted(out, key=lambda x: x[0])


def column_returns(face: Face, stretches: list):
    """R-T410-4: the returns a PROUD column face makes on its side -> (confirmed_lm, held_lm, carrier sid)."""
    if face.kind != "column" or face.proud <= EPS:
        return 0.0, 0.0, None
    side = _side_stretches(stretches, face.element, face.side)
    if not side:
        raise SkirtingInputError(f"face {face.ref}: no stretch on {face.element} {face.side}")
    lo, hi = side[0][0], side[-1][1]
    carrier = None
    for s0, s1, st in side:
        if min(s1, face.s1) - max(s0, face.s0) > EPS:
            if st.cls != WALL or st.face != "column":
                raise SkirtingInputError(f"face {face.ref}: a proud column face lies in {st.sid} ({st.cls}, "
                                         f"face {st.face}); a column face is a WALL stretch of face 'column'")
            carrier = st.sid
    conf = held = 0.0
    for end, probe in ((face.s0, face.s0 - 1e-6), (face.s1, face.s1 + 1e-6)):
        if probe < lo - EPS or probe > hi + EPS:
            continue                        # the column runs past the element: no return on it
        nb = next((st for s0, s1, st in side if s0 - EPS <= probe <= s1 + EPS and not (face.s0 <= probe <= face.s1)),
                  None)
        if nb is None:
            continue
        if nb.cls == WALL:
            conf += face.proud
        elif nb.cls in (HELD, UNKNOWN):
            held += face.proud
    return round(conf, 9), round(held, 9), carrier


def check_faces(stretches: list, faces: list) -> list:
    """R-T410-4 on a side table: a 'no face' stretch overlapping ANY face (wall or column) is refused; every proud
    column face sits in a WALL stretch of face 'column' whose returns_lm equals its confirmed returns. Returns one
    row per column face (ref, carrier, proud, confirmed / held returns)."""
    out, carried = [], {}
    for fc in faces:
        for s0, s1, st in _side_stretches(stretches, fc.element, fc.side):
            if st.no_face and min(s1, fc.s1) - max(s0, fc.s0) > EPS:
                raise SkirtingInputError(f"{st.sid}: classed 'no face' but the {fc.kind} face {fc.ref} stands on "
                                         f"{fc.s0:.3f} .. {fc.s1:.3f}: a column face is a face (R-T410-4)")
        conf, held, carrier = column_returns(fc, stretches)
        if carrier:
            carried[carrier] = carried.get(carrier, 0.0) + conf
        out.append({"ref": fc.ref, "element": fc.element, "side": fc.side, "kind": fc.kind, "s0": fc.s0,
                    "s1": fc.s1, "proud": fc.proud, "carrier": carrier or "", "returns_confirmed_lm": conf,
                    "returns_held_lm": held})
    for st in stretches:
        if st.face == "column" and abs(st.returns_lm - carried.get(st.sid, 0.0)) > 1e-6:
            raise SkirtingInputError(f"{st.sid}: returns {st.returns_lm} vs {carried.get(st.sid, 0.0)} from its "
                                     "column faces")
    return out


def winder_region(*_a, **_k):
    """Owner S-9: winders are never generated. A winder corner is a HELD stretch (plan + rise reported)."""
    raise SkirtingInputError("winders are never generated (owner S-9); list the winder corner as a HELD stretch")


def totals(rows: list) -> dict:
    out = {"confirmed_horizontal_lm": 0.0, "form_held_zigzag_lm": 0.0, "form_held_sloped_lm": 0.0,
           "held_plan_lm": 0.0, "held_risers": 0, "unknown_plan_lm": 0.0, "open_plan_lm": 0.0}
    for r in rows:
        if r["status"] == CONFIRMED:
            out["confirmed_horizontal_lm"] += r["qty_lm"]
        elif r["status"] == FORM_HELD:
            out["form_held_zigzag_lm"] += r["zigzag_lm"]
            out["form_held_sloped_lm"] += r["sloped_lm"]
        elif r["class"] == HELD:
            out["held_plan_lm"] += r["plan_lm"]
            out["held_risers"] += r["risers_in"] or 0
        elif r["class"] == UNKNOWN:
            out["unknown_plan_lm"] += r["plan_lm"]
        elif r["class"] == OPEN:
            out["open_plan_lm"] += r["plan_lm"]
    return {k: (round(v, 6) if isinstance(v, float) else v) for k, v in out.items()}
