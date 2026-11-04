"""T-501: home of the stair skirting pieces (any villa; research, not wired into any candidate).

Physical element (UP-STAIR-009 .. 011, UP-SKIRT-001 1.4.0, R-T410-1 .. 4, R-T481-3, ELEMENT_REGISTER 'STAIR SKIRTING vs
ROOM SKIRTING'): a skirting is a strip fixed to a finished wall / column face at the level of what stands against it.
Along a flight it climbs with the flight (owner trade B7, form zigzag UP-STAIR-010 = family B7-07, form sloped
UP-STAIR-011 = family B7-08: BOQ_FAMILY_MASTER 1.48.0 item names); on an intermediate landing or a floor it is level
(owner trade FIN.SKIRTING, the register ruling). An open side (balustrade, slab edge, well) has nothing to fix it to and
is never skirted. Four rules, each enforced in code here:

R-T501-1 LEVEL-AWARE ONE OWNER. Every piece carries its face, its face stations s0 .. s1 (metres) and its level band
  over that range (a flight interpolates from its foot level to its head level; a landing / floor is one level). Two
  pieces on one face whose stations overlap by more than CLOSE_TOL_M AND whose level bands meet over the overlap are two
  owners of one strip: refused. Stacked pieces of different levels over the same plan length are distinct strips.

R-T501-2 RETIRE BY CLOSURE. A room-line piece measured at a floor level along a face where no floor of that level
  stands (a stair shaft) is NOT_APPLICABLE only when the stair pieces at every level cover its stations exactly
  (plan union == the retired length within CLOSE_TOL_M); the moved length is never dropped: each covering piece is its
  own line (value, or blank with cause). An uncovered station keeps the room figure.

R-T501-3 FORM DECIDES THE FAMILY, NOT THE SIDE. A sloping wall-side piece is ONE line; until the project's form is fixed
  (ORR-007) it is HELD-FORM: blank, zigzag and sloped figures beside, family 'B7-07 | B7-08'; with the form fixed it takes
  B7-07 (zigzag) or B7-08 (sloped), never both valued. A family code read as 'wall side / open side' is refused: the
  open side carries no skirting at all. A level piece (landing, floor) is form-independent.

R-T501-4 SPLIT AT A CONFLICT STATION. Where two drawings disagree on whether a station is flight or floor (the arch plan
  ends the flight at its drawn last riser, another sheet draws one more tread), the disputed stations are their own
  piece, CONFLICT (blank, both readings beside); the undisputed part keeps its status; the figure carried by an existing
  line for the disputed stations stays where it is until the conflict is closed (one owner today, never two).

Units: metres; a value that looks like millimetres (> 50) is refused. Held / unknown / conflict are blank, never 0.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

CLOSE_TOL_M = 0.0005
LEVEL_TOL_M = 0.001
FLIGHT, LANDING, ROOM, STEP = "FLIGHT", "LANDING", "ROOM", "STEP"
WALL, HELD, CONFLICT, UNKNOWN, OPEN = "WALL", "HELD", "CONFLICT", "UNKNOWN", "OPEN"
CONFIRMED, FORM_HELD = "DRAWING-CONFIRMED", "HELD-FORM"
FAMILY_BY_FORM = {"zigzag": "B7-07", "sloped": "B7-08"}      # BOQ_FAMILY_MASTER item_en 'Stair skirting zigzag / sloped'
ROOM_TRADE = "FIN.SKIRTING"


class RuleError(ValueError):
    pass


def _m(v, what):
    if v is None:
        return None
    v = float(v)
    if abs(v) > 50:
        raise RuleError(f"{what} = {v}: looks like millimetres; metres required")
    return v


@dataclass
class Piece:
    pid: str
    element: str
    face: str
    kind: str                  # FLIGHT / LANDING / ROOM / STEP
    cls: str                   # WALL / HELD / CONFLICT / UNKNOWN / OPEN
    s0: float
    s1: float
    level0: float              # level at s0 (m)
    level1: float              # level at s1 (m); == level0 for a level piece
    risers: int = 0            # risers standing in the piece (flight)
    riser: float = 0.0         # riser height (m)
    flight_run: float = 0.0    # the whole flight's plan run (m), for the rake factor (UP-STAIR-011)
    flight_rise: float = 0.0   # the whole flight's total rise (m)
    returns: float = 0.0       # column returns (horizontal, R-T410-4)
    cause: str = ""
    evidence: str = ""
    beside: dict = field(default_factory=dict)

    def __post_init__(self):
        for k in ("s0", "s1", "level0", "level1", "riser", "flight_run", "flight_rise", "returns"):
            setattr(self, k, _m(getattr(self, k), f"{self.pid}.{k}"))
        if self.s1 < self.s0 - CLOSE_TOL_M:
            raise RuleError(f"{self.pid}: s1 < s0")
        if self.kind not in (FLIGHT, LANDING, ROOM, STEP):
            raise RuleError(f"{self.pid}: kind {self.kind}")
        if self.cls not in (WALL, HELD, CONFLICT, UNKNOWN, OPEN):
            raise RuleError(f"{self.pid}: class {self.cls}")
        if self.cls in (HELD, CONFLICT, UNKNOWN) and not self.cause:
            raise RuleError(f"{self.pid}: {self.cls} without a cause")
        if self.kind in (LANDING, ROOM) and abs(self.level1 - self.level0) > LEVEL_TOL_M:
            raise RuleError(f"{self.pid}: a level piece with two levels")
        if self.kind == FLIGHT and self.cls == WALL and (self.flight_run <= 0 or self.flight_rise <= 0):
            raise RuleError(f"{self.pid}: a flight wall piece needs the flight's run and rise")

    @property
    def plan(self) -> float:
        return self.s1 - self.s0

    def band(self, a: float, b: float):
        """Level band of the piece over the stations a .. b (inside the piece)."""
        if self.kind != FLIGHT or self.plan <= 0:
            return (min(self.level0, self.level1), max(self.level0, self.level1))
        def lv(s):
            return self.level0 + (self.level1 - self.level0) * (s - self.s0) / self.plan
        la, lb = lv(a), lv(b)
        return (min(la, lb), max(la, lb))


def zigzag(p: Piece) -> float:
    """UP-STAIR-010: plan + the rises of the risers standing in the piece (+ horizontal returns)."""
    return p.plan + p.risers * p.riser + p.returns


def sloped(p: Piece) -> float:
    """UP-STAIR-011: plan x hypot(run, rise) / run of the flight (+ horizontal returns)."""
    return p.plan * math.hypot(p.flight_run, p.flight_rise) / p.flight_run + p.returns


def level_lm(p: Piece) -> float:
    return p.plan + p.returns


def check_one_owner(pieces) -> None:
    """R-T501-1. Refuses two pieces on one face that overlap in stations and meet in level."""
    live = [p for p in pieces if p.cls != OPEN]
    for i, a in enumerate(live):
        for b in live[i + 1:]:
            if a.face != b.face:
                continue
            lo, hi = max(a.s0, b.s0), min(a.s1, b.s1)
            if hi - lo <= CLOSE_TOL_M:
                continue
            ba, bb = a.band(lo, hi), b.band(lo, hi)
            if max(ba[0], bb[0]) <= min(ba[1], bb[1]) + LEVEL_TOL_M:
                # R-T501-4: a blank CONFLICT piece may lie over the figure that carries its stations today, only when
                # it names that piece as the carrier (one figure, one blank, never two figures)
                for c, o in ((a, b), (b, a)):
                    if c.cls == CONFLICT and o.cls != CONFLICT and o.pid in c.beside.get("carried_by", ()):
                        break
                else:
                    raise RuleError(f"two owners: {a.pid} and {b.pid} on {a.face} over s {lo:.3f} .. {hi:.3f}")


def plan_union(pieces, face, a, b) -> float:
    iv = sorted((max(p.s0, a), min(p.s1, b)) for p in pieces
                if p.face == face and p.cls != OPEN and min(p.s1, b) - max(p.s0, a) > CLOSE_TOL_M)
    tot, cur0, cur1 = 0.0, None, None
    for x0, x1 in iv:
        if cur1 is None or x0 > cur1 + CLOSE_TOL_M:
            if cur1 is not None:
                tot += cur1 - cur0
            cur0, cur1 = x0, x1
        else:
            cur1 = max(cur1, x1)
    if cur1 is not None:
        tot += cur1 - cur0
    return tot


def retire(room_segments, pieces) -> list:
    """R-T501-2. room_segments: [(seg_id, face, s0, s1, floor_level, status)]; returns one binding row per segment."""
    rows = []
    for sid, face, s0, s1, lvl, status in room_segments:
        s0, s1, lvl = _m(s0, sid), _m(s1, sid), _m(lvl, sid)
        stair = [p for p in pieces if p.kind != ROOM]          # rooms of other floors never 'cover' a retired piece
        cov = plan_union(stair, face, s0, s1)
        owners = [p for p in stair if p.face == face and p.cls != OPEN and min(p.s1, s1) - max(p.s0, s0) > CLOSE_TOL_M]
        def at_floor(p):
            lo_, hi_ = p.band(max(p.s0, s0), min(p.s1, s1))
            if hi_ - lo_ <= LEVEL_TOL_M:                       # a level piece: on the floor's level?
                return abs(lo_ - lvl) <= LEVEL_TOL_M
            return lo_ + LEVEL_TOL_M < lvl < hi_ - LEVEL_TOL_M  # a flight crossing the floor level inside the segment
        same = [p.pid for p in owners if p.kind != ROOM and at_floor(p)]
        if same:
            raise RuleError(f"{sid}: a stair piece at the floor's own level {lvl} ({same}): the floor stands there")
        closes = abs(cov - (s1 - s0)) <= CLOSE_TOL_M
        rows.append({"segment": sid, "face": face, "s0": round(s0, 6), "s1": round(s1, 6), "lm": round(s1 - s0, 6),
                     "status_before": status, "covered_lm": round(cov, 6), "residual_lm": round((s1 - s0) - cov, 6),
                     "decision": "NOT_APPLICABLE (no floor at its level; moved to the pieces)" if closes
                     else "KEEP (not covered: stays in the room line)",
                     "owners": " ".join(p.pid for p in sorted(owners, key=lambda q: (q.s0, q.level0)))})
    return rows


def line(p: Piece, form: str | None = None) -> dict:
    """R-T501-3. One proposed line per piece."""
    if form is not None and form not in FAMILY_BY_FORM:
        raise RuleError(f"form {form!r}: only 'zigzag' / 'sloped' (ORR-007); a side is not a form")
    row = {"pid": p.pid, "element": p.element, "face": p.face, "kind": p.kind, "cls": p.cls,
           "s0": round(p.s0, 6), "s1": round(p.s1, 6), "plan_lm": round(p.plan, 6), "risers": p.risers,
           "returns_lm": round(p.returns, 6), "level0": p.level0, "level1": p.level1,
           "family": "", "value_lm": None, "status": "", "zigzag_lm": None, "sloped_lm": None,
           "cause": p.cause, "evidence": p.evidence}
    if p.cls == OPEN:
        raise RuleError(f"{p.pid}: an open side is not skirted; it is no line (railing B7-09 owns the edge)")
    if p.kind == ROOM:
        raise RuleError(f"{p.pid}: room pieces stay in their room line")
    if p.kind in (LANDING,):
        row["family"] = ROOM_TRADE
        if p.cls == WALL:
            row["value_lm"], row["status"] = round(level_lm(p), 6), CONFIRMED
        else:
            row["status"] = p.cls
            row["level_lm_beside"] = round(level_lm(p), 6)
        return row
    if p.kind == STEP:
        row["family"] = "B7-07 | B7-08"
        row["status"] = p.cls if p.cls != WALL else FORM_HELD
        row["zigzag_lm"] = round(p.risers * p.riser, 6)        # a riser on a level piece: no going, no rake
        return row
    zz = round(zigzag(p), 6) if p.flight_run > 0 else None
    sl = round(sloped(p), 6) if p.flight_run > 0 else None
    row["zigzag_lm"], row["sloped_lm"] = zz, sl
    if p.cls != WALL:
        row["family"], row["status"] = "B7-07 | B7-08", p.cls
        return row
    if form is None:
        row["family"], row["status"] = "B7-07 | B7-08", FORM_HELD
    else:
        row["family"], row["status"] = FAMILY_BY_FORM[form], CONFIRMED
        row["value_lm"] = zz if form == "zigzag" else sl
    return row


def check_lines(rows) -> None:
    for r in rows:
        if r["status"] != CONFIRMED and r["value_lm"] is not None:
            raise RuleError(f"{r['pid']}: a {r['status']} line carries a value")
        if r["status"] == CONFIRMED and (r["value_lm"] is None or r["value_lm"] <= 0):
            raise RuleError(f"{r['pid']}: a confirmed line without a positive value")
        if r["family"] in FAMILY_BY_FORM.values() and r["zigzag_lm"] is not None and r["sloped_lm"] is not None \
                and r["value_lm"] is not None and r["value_lm"] not in (r["zigzag_lm"], r["sloped_lm"]):
            raise RuleError(f"{r['pid']}: value is neither form")


def split(p: Piece, at: float, cls_b: str, cause_b: str, risers_a: int, evidence_b: str = "") -> tuple:
    """R-T501-4. Splits p at station `at`; the part after `at` takes cls_b (CONFLICT) with its own cause."""
    at = _m(at, p.pid)
    if not (p.s0 + CLOSE_TOL_M < at < p.s1 - CLOSE_TOL_M):
        raise RuleError(f"{p.pid}: split station outside the piece")
    if not 0 <= risers_a <= p.risers:
        raise RuleError(f"{p.pid}: risers split")
    lv = p.level0 + (p.level1 - p.level0) * (at - p.s0) / p.plan
    a = Piece(p.pid + "a", p.element, p.face, p.kind, p.cls, p.s0, at, p.level0, lv, risers_a, p.riser,
              p.flight_run, p.flight_rise, p.returns, p.cause, p.evidence)
    b = Piece(p.pid + "b", p.element, p.face, p.kind, cls_b, at, p.s1, lv, p.level1, p.risers - risers_a, p.riser,
              p.flight_run, p.flight_rise, 0.0, cause_b, evidence_b or p.evidence)
    return a, b
