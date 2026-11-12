"""T-725 rules (project-agnostic; scope: every villa). Research only, unwired. Built on R-T714-1 (a held formwork line
takes its member's bound face by face), R-STAIR-FW-SIDE-1 (T-352: side forms per side, wall / member contacts 0 .. x),
the T-281 soffit methods O / D, R-T718-2 (stopper-to-stopper floors from drawn geometry only), R-CONC-OWN-1 and
R-T696-1 (directed rounding); none of them edited. OWNER_RULE_STAIRS_2026-10-24 S-9: winders / curved parts are never
generated.

R-T725-1 1.0.0  ONE STAIR READING = ONE RISER COUNT WITH ITS OWN RISE FOR EVERY PIECE.
    A reading of a stair (a section, a structural plan, an architectural plan) is a riser count per piece whose sum is
    the reading's total; its rise = storey height / that total, used for EVERY piece of the reading (flights, turn,
    landings' levels). A reading that takes its count from one source and its rise from another (e.g. 12 + 4 + 12 = 28
    structural risers at the section's 4.50 / 27) is refused: it is not a buildable stair.

R-T725-2 1.0.0  STAIR FORMWORK FACES: WHAT IS FORMED, FROM DRAWN GEOMETRY ONLY.
    (a) Riser form = drawn riser width x the reading's rise, for a riser face that is exposed and the stair's; a riser
        line drawn inside a member band (beam / ground beam) is a face whose owner depends on that member's unprinted
        level: 0 .. face (never both lines).
    (b) Winder / curved risers: a floor only from drawn evidence (drawn front lines, or n fronts each at least the
        narrow side of the DRAWN turn region, R-T718-2); a generated subdivision or a rise that the governing rule
        holds (a curved part) gives no figure.
    (c) Waist soffit = the underside of the waist by drawn flight: method O = plan x sec (flight from its first riser
        line), method D = O less the slab-borne foot strip (g / r) x t x sec x width where the flight starts on a slab;
        never the plan area. A warped / undrawn soffit over a DRAWN region has the region's plan area as its floor (a
        surface is never smaller than its projection) and no high.
    (d) Side profile (stringer) = step triangles + waist band between stations; method O as the owner concrete region,
        method D clipped at the slab top at a foot that starts on a slab (below the slab top nothing is formed).
    (e) A contact with a wall, a member or a held junction whose sequence is not printed is CAP_ONLY 0 .. face; an
        interface between two concrete members is formed at most once (the caps of the two lines share it).

R-T725-3 1.0.0  LINE CLASS: LOW = THE LEAST COHERENT READING, NEVER 0, NEVER A REMOVED ITEM.
    Each coherent reading (R-T725-1) x soffit method gives a line low = sum of face lows and a high = sum of face highs
    when every high is known. Line low = min over readings, line high = max over readings (None if any is open).
    low > 0 and high known -> BOUNDED; low > 0 and high open -> AT_LEAST; low = 0 -> BLANK_NAMED with the cap beside
    when known (never 0, never a range from 0, never an AT_MOST printed as a quantity). A blank names a LIVE cause: a
    designer item removed from the package (e.g. a resolved D-id) is refused; the line names the live item that holds it.
"""
from __future__ import annotations

import math
import sys
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "agents_t696"))
import bound_rounding_v1 as BR  # noqa: E402

D = BR.D
RULES = {"R-T725-1": "1.0.0", "R-T725-2": "1.0.0", "R-T725-3": "1.0.0"}
LINE_CLASSES = ("BOUNDED", "AT_LEAST", "BLANK_NAMED")
MAX_FACE_M2 = 1000.0          # a single face above 1000 m2 is a unit error (mm read as m)
MAX_RISE_M = 0.30             # a rise above 0.30 m is not a stair riser (unit / count error)


class Refused(ValueError):
    pass


# ------------------------------------------------------------------ R-T725-1
@dataclass(frozen=True)
class Reading:
    name: str
    storey_m: float
    pieces: tuple            # ((piece, n_risers), ...) in walking order
    count_source: str
    rise_source: str
    total_declared: int | None = None   # a total printed by the rise source (e.g. the section's 27)

    def __post_init__(self):
        if self.storey_m is None or self.storey_m <= 0:
            raise Refused(f"{self.name}: storey height missing")
        n = sum(k for _, k in self.pieces)
        if n < 2 or any(k < 0 for _, k in self.pieces):
            raise Refused(f"{self.name}: riser counts invalid")
        if self.total_declared is not None and self.total_declared != n:
            raise Refused(f"R-T725-1: reading {self.name} counts {n} risers ({self.count_source}) but takes its rise "
                          f"from a total of {self.total_declared} ({self.rise_source}): not one stair")
        if self.rise > MAX_RISE_M:
            raise Refused(f"{self.name}: rise {self.rise:.4f} m is not a riser (unit / count)")

    @property
    def total(self) -> int:
        return sum(k for _, k in self.pieces)

    @property
    def rise(self) -> float:
        return self.storey_m / self.total

    def n(self, piece: str) -> int:
        for p, k in self.pieces:
            if p == piece:
                return k
        raise Refused(f"{self.name}: piece {piece} not in the reading")


def sec(r: float, g: float) -> float:
    if r <= 0 or g <= 0:
        raise Refused("riser and going must be positive")
    return math.hypot(g, r) / g


# ------------------------------------------------------------------ R-T725-2 geometry
def side_profile(r: float, g: float, t: float | None, n_lines: int, s_a: float, s_b: float, *, clip_floor: bool) -> float:
    """Side-elevation area (m2) between stations s_a <= s_b of a flight with n_lines riser lines (first at s = 0, z = 0
    on the floor it starts from). Top = (j + 1) r on going j; bottom = soffit line (r / g) s - t sec (method O) or
    max(0, that) (method D, clip_floor). Exact piecewise integration."""
    if t is None or t <= 0:
        raise Refused("waist thickness not printed: the side profile is HELD, never computed with 0")
    if n_lines < 2:
        raise Refused("a flight needs at least two riser lines")
    s_end = (n_lines - 1) * g
    if not (-1e-9 <= s_a <= s_b <= s_end + 1e-9):
        raise Refused(f"strip {s_a} .. {s_b} outside the flight 0 .. {s_end}")
    k, ts = r / g, t * sec(r, g)
    s0 = ts / k                                  # where the soffit line leaves the floor (method D)
    cuts = sorted({s_a, s_b, *[j * g for j in range(n_lines) if s_a < j * g < s_b]}
                  | ({s0} if clip_floor and s_a < s0 < s_b else set()))
    area = 0.0
    for a, b in zip(cuts, cuts[1:]):
        j = min(int(math.floor((a + 1e-12) / g)), n_lines - 2)
        top = (j + 1) * r
        if clip_floor and b <= s0 + 1e-12:
            area += top * (b - a)                      # bottom = floor (0)
        else:
            area += (top + ts) * (b - a) - k * (b * b - a * a) / 2.0
    return area


def soffit_true(plan_m2: float, r: float, g: float) -> float:
    """Method O: developed waist underside = plan x sec."""
    if plan_m2 is None or plan_m2 <= 0:
        raise Refused("soffit plan missing")
    return plan_m2 * sec(r, g)


def soffit_d(plan_m2: float, width: float, r: float, g: float, t: float | None, *, foot_on_slab: bool) -> float:
    """Method D: method O less the slab-borne foot strip (the waist rises out of the slab at s = (g / r) t sec)."""
    if t is None or t <= 0:
        raise Refused("waist thickness not printed: method D needs it")
    strip = width * (g / r) * t * sec(r, g) if foot_on_slab else 0.0
    if strip >= plan_m2:
        raise Refused("foot strip larger than the flight plan")
    return (plan_m2 - strip) * sec(r, g)


def riser_forms(widths, r: float, *, drawn: bool) -> float:
    """R-T725-2 (a)/(b): sum of drawn riser widths x rise. Generated widths are refused."""
    if not drawn:
        raise Refused("S-9: riser widths not drawn (generated subdivision) give no figure")
    ws = list(widths)
    if not ws or any(w is None or w <= 0 for w in ws):
        raise Refused("a riser width is missing")
    if r <= 0 or r > MAX_RISE_M:
        raise Refused(f"rise {r} not a riser")
    return sum(ws) * r


def winder_floor(n_risers: int, region_narrow_side: float, r: float, *, region_drawn: bool) -> float:
    """R-T725-2 (b): n fronts not drawn, each crossing the DRAWN turn region, each at least its narrow side."""
    if not region_drawn:
        raise Refused("S-9: the turn region is not drawn: no winder floor")
    if n_risers < 1 or region_narrow_side is None or region_narrow_side <= 0:
        raise Refused("winder count / region missing")
    return n_risers * region_narrow_side * r


def warped_floor(region_plan_m2: float | None, *, region_drawn: bool) -> float:
    """R-T725-2 (c): an undrawn (warped) soffit over a drawn region: floor = the region's plan, high open."""
    if not region_drawn or region_plan_m2 is None or region_plan_m2 <= 0:
        raise Refused("warped soffit floor needs the drawn region")
    return region_plan_m2


# ------------------------------------------------------------------ R-T725-3 line class
@dataclass
class Face:
    face_id: str
    kind: str
    lo: float | None            # None: no figure (BLOCK)
    hi: float | None            # None: open
    basis: str = ""
    contact: str = "FORMED"     # FORMED | CAP_ONLY | BLOCK

    def check(self):
        if self.contact == "BLOCK":
            return
        if self.lo is None or self.lo < 0:
            raise Refused(f"{self.face_id}: low missing or negative")
        if self.hi is not None and self.hi + 1e-12 < self.lo:
            raise Refused(f"{self.face_id}: low {self.lo} > high {self.hi}")
        if max(self.lo, self.hi or 0.0) > MAX_FACE_M2:
            raise Refused(f"{self.face_id}: {max(self.lo, self.hi or 0)} m2 is a unit error")
        if self.contact == "CAP_ONLY" and self.lo != 0.0:
            raise Refused(f"{self.face_id}: a CAP_ONLY face has low 0")


@dataclass
class LineResult:
    line_id: str
    cls: str
    low: Decimal | None
    high: Decimal | None
    cap: Decimal | None
    readings: dict = field(default_factory=dict)
    cause: str | None = None


def class_line(line_id: str, faces_by_reading: dict, *, cause: str | None, live_items: set, removed_items: set,
               cited: tuple = ()) -> LineResult:
    """faces_by_reading: {reading: [Face, ...]}; a BLOCK face anywhere makes the line BLANK_NAMED (no cap from it)."""
    bad = [c for c in cited if c in removed_items]
    if bad:
        raise Refused(f"R-T725-3: {line_id} cites removed item(s) {bad}: name the live item that holds it")
    if any(c not in live_items for c in cited):
        raise Refused(f"R-T725-3: {line_id} cites an unknown item {[c for c in cited if c not in live_items]}")
    if not faces_by_reading:
        raise Refused(f"{line_id}: no reading")
    per, block = {}, False
    for rd, faces in faces_by_reading.items():
        if not faces:
            raise Refused(f"{line_id}/{rd}: no face")
        for f in faces:
            f.check()
        if any(f.contact == "BLOCK" for f in faces):
            block = True
            per[rd] = (None, None)
            continue
        lo = sum(f.lo for f in faces)
        hi = None if any(f.hi is None for f in faces) else sum(f.hi for f in faces)
        per[rd] = (lo, hi)
    if block:
        if not cause:
            raise Refused(f"{line_id}: a blank needs its cause")
        return LineResult(line_id, "BLANK_NAMED", None, None, None, per, cause)
    # inputs are stated to 1e-4 m: binary noise below 1e-10 is removed before the directed rounding (R-T696-1)
    low = round(min(v[0] for v in per.values()), 10)
    highs = [v[1] for v in per.values()]
    high = None if any(h is None for h in highs) else round(max(highs), 10)
    if low <= 1e-12:
        if not cause:
            raise Refused(f"{line_id}: a blank needs its cause")
        cap = BR.round_high(high) if high is not None else None
        return LineResult(line_id, "BLANK_NAMED", None, None, cap, per, cause)
    if high is None:
        return LineResult(line_id, "AT_LEAST", BR.round_low(low), None, None, per, cause)
    lo_r, hi_r = BR.bound(D(repr(low)), D(repr(high)), exact=True)
    return LineResult(line_id, "BOUNDED", lo_r, hi_r, None, per, cause)
