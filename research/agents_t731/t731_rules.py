"""T-731 rules (project-agnostic; scope: every villa). Research only, unwired. Builds on R-T725-1 (one reading = one
riser count with its own rise) and R-T725-3 (line class by the least coherent reading); neither is edited. This file
adds the piece-wise form of R-T725-1 that F-T725-1 left open: a uniform rise over the storey is coherent only when the
reading meets every intermediate level the drawings print.

R-T731-1 1.0.0  A STAIR READING IS COHERENT ONLY BETWEEN PRINTED LEVELS.
    (a) A reading is one riser count per piece, all counts from ONE source (a section, a structural plan, an
        architectural plan). Levels are physical facts and may come from any sheet (a level mark, or a printed
        dimension from a printed level), never from another reading's count or rise.
    (b) The printed levels the stair passes (floors, a half landing) split the reading into segments; each segment's
        rise = its printed level difference / the segment's own riser count (count x riser = total rise, segment by
        segment). A segment whose count is 0 or whose rise is outside 0 < r <= 0.30 m is refused.
    (c) A reading that carries one uniform rise across an intermediate printed level and misses it by more than half
        the printing precision (0.005 m for levels printed to 0.01 m) is INCOHERENT: named with its miss, never a
        bound. So is a reading whose count and rise come from two sources (R-T725-1).
    (d) A drawn piece that a reading would have to re-count (a flight drawn with n riser lines on every source read)
        keeps its drawn count in every reading; a reading that changes it is refused.

R-T731-2 1.0.0  RESTATING A LINE WHEN A READING IS REPLACED: A LOW IS NEVER RAISED BY THE COHERENT RULE.
    Line low = min over the coherent readings, line high = max over them. If the new low is ABOVE the old low (the old
    low came from a reading now refused), the old low is kept and flagged LOW_KEPT_REFUSED_SOURCE for the Checker:
    removing a reading never raises a floor silently. A high may fall (a refused reading no longer bounds it) or rise
    (a coherent reading above it), each named old -> new.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
for _p in (HERE.parent / "agents_t725", HERE.parent / "agents_t696"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
import t725_rules as R725  # noqa: E402

Refused = R725.Refused
RULES = {"R-T731-1": "1.0.0", "R-T731-2": "1.0.0"}
LEVEL_TOL_M = 0.005          # half of 0.01 m, the printing precision of the levels
MAX_RISE_M = R725.MAX_RISE_M


@dataclass(frozen=True)
class PrintedLevel:
    name: str
    level_m: float
    source: str              # sheet + handle / mark / dimension that prints it


@dataclass(frozen=True)
class Segment:
    pieces: tuple            # piece names, walking order
    n: int
    rise_m: float            # printed level difference
    lo: str
    hi: str

    @property
    def r(self) -> float:
        return self.rise_m / self.n


def segments(reading_name: str, pieces: tuple, count_source: str, levels: list, breaks: dict) -> list:
    """pieces: ((piece, n), ...) in walking order, every count from count_source. levels: [PrintedLevel] bottom to top.
    breaks: {piece: level name} = the printed level reached at the TOP of that piece (the last piece reaches the top
    level). Returns the level-to-level segments with their own rise (R-T731-1 (b))."""
    if not count_source:
        raise Refused(f"{reading_name}: count source missing")
    if len(levels) < 2:
        raise Refused(f"{reading_name}: at least the two floor levels must be printed")
    by = {lv.name: lv for lv in levels}
    order = [lv.name for lv in levels]
    if any(levels[i + 1].level_m <= levels[i].level_m for i in range(len(levels) - 1)):
        raise Refused(f"{reading_name}: printed levels not increasing")
    segs, cur, n, lo = [], [], 0, order[0]
    for i, (p, k) in enumerate(pieces):
        if k < 0:
            raise Refused(f"{reading_name}: negative count")
        cur.append(p)
        n += k
        top = breaks.get(p) or (order[-1] if i == len(pieces) - 1 else None)
        if top is None:
            continue
        if top not in by:
            raise Refused(f"{reading_name}: level {top} not printed")
        if order.index(top) != order.index(lo) + 1:
            raise Refused(f"{reading_name}: a printed level between {lo} and {top} is skipped")
        if n <= 0:
            raise Refused(f"{reading_name}: segment {lo} -> {top} has no riser")
        rise = round(by[top].level_m - by[lo].level_m, 9)
        seg = Segment(tuple(cur), n, rise, lo, top)
        if not (0 < seg.r <= MAX_RISE_M):
            raise Refused(f"{reading_name}: rise {seg.r:.4f} m between {lo} and {top} is not a riser (unit / count)")
        segs.append(seg)
        cur, n, lo = [], 0, top
    if lo != order[-1] or cur:
        raise Refused(f"{reading_name}: the reading does not reach the top printed level")
    return segs


def uniform_misses(reading_name: str, pieces: tuple, levels: list, breaks: dict) -> list:
    """R-T731-1 (c): a reading carried at ONE rise (storey / total) over the whole stair: the miss at each intermediate
    printed level. Returns [(level name, printed, implied, miss)] for every miss above the tolerance."""
    total = sum(k for _, k in pieces)
    if total <= 0:
        raise Refused(f"{reading_name}: no riser")
    r = (levels[-1].level_m - levels[0].level_m) / total
    out, cum = [], 0
    by = {lv.name: lv for lv in levels}
    for p, k in pieces:
        cum += k
        top = breaks.get(p)
        if top and top != levels[-1].name:
            implied = levels[0].level_m + cum * r
            miss = implied - by[top].level_m
            if abs(miss) > LEVEL_TOL_M:
                out.append((top, by[top].level_m, round(implied, 6), round(miss, 6)))
    return out


def check_drawn_counts(reading_name: str, pieces: tuple, drawn: dict):
    """R-T731-1 (d): a piece drawn with the same riser count on every source keeps that count in every reading."""
    for p, k in pieces:
        if p in drawn and drawn[p] != k:
            raise Refused(f"R-T731-1 (d): {reading_name} counts {k} risers on {p}, drawn {drawn[p]} on every source read")


def restate(old_low: float | None, old_high: float | None, coherent: dict, *, tol: float = 1e-12) -> dict:
    """R-T731-2: coherent = {reading: (low, high or None)}. Returns the restated low / high with the move named."""
    if not coherent:
        raise Refused("no coherent reading: the line stays as it is (blank) and the cause is named")
    for k, (lo, hi) in coherent.items():
        if lo is None or lo <= 0:
            raise Refused(f"reading {k}: low missing or not positive (never 0)")
        if hi is not None and hi + 1e-12 < lo:
            raise Refused(f"reading {k}: low above high")
    new_low = min(v[0] for v in coherent.values())
    highs = [v[1] for v in coherent.values()]
    new_high = None if any(h is None for h in highs) else max(highs)
    flag = None
    if old_low is not None and new_low > old_low + tol:
        flag = "LOW_KEPT_REFUSED_SOURCE"
        new_low = old_low
    elif old_low is not None and new_low > old_low:
        new_low = old_low          # equal within the recorded directed rounding (R-T696-1): the recorded floor stands
    return {"low": new_low, "high": new_high, "low_moved": None if old_low is None else round(new_low - old_low, 9),
            "high_moved": None if old_high is None or new_high is None else round(new_high - old_high, 9),
            "flag": flag}
