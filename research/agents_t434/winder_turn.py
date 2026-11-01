"""T-434 winder-turn reading test (research module; any villa; NOT wired into any method).

Physical element: a WINDER TURN is the part of a flight between the front of its first winder and the edge of the
landing it reaches. Its quantities are owned by the riser COUNT (how many risers the turn has between two printed
levels) and by the drawn SUBDIVISION (the front edge of every winder). Different sheets of one set often draw a turn
with different counts (section, architectural plan, structural slab plan). This module tests each reading against the
physical checks and names the governing one only with a GOVERNING REASON; it never picks the reading that fits best.

Rules applied (owner):
- Q-46 A: for a stair whose section and plans disagree, the SECTION counts; plans are checks + RFI.
- OWNER_RULE_STAIRS_2026-10-24 s.1: finished riser 0.150 - 0.170 m and going 0.280 - 0.300 m are CHECKS (owner
  preferences), never defaults and never a reason to overwrite a drawing (s.4 S-4 (8), S-8).
- S-9: winders are never generated; drawn and dimensioned winders are measured; missing geometry -> HELD.
- T-267 acceptance A8: drawn winders with geometry missing -> winder geometry AND its marble HELD; other flights measured.
- WORKFLOW_CONTROLS s.5: HELD quantities are None (blank), never 0.

Units: metres only. A value that looks like millimetres (a riser above 1 m, a going above 2 m) is refused.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

RISER_CHECK = (0.150, 0.170)      # owner preference CHECK (finished riser), OWNER_RULE_STAIRS_2026-10-24 s.1
GOING_CHECK = (0.280, 0.300)      # owner preference CHECK (going)
LEVEL_TOL = 0.010                 # scaled section levels are indicative: agreement within 10 mm
RUN_TOL = 0.050                   # foot positions: a scaled 1:100 section agrees within 50 mm (0.5 mm on paper); the
                                  # conflicts tested are a whole going (0.300) or more

CONFIRMED = "DRAWING-CONFIRMED"
HELD = "HELD"
GOVERNING = "GOVERNING"
REJECTED = "REJECTED"
CONFLICT = "CONFLICT"


class ReadingError(ValueError):
    pass


def _m(name, v, hi):
    if v is None:
        raise ReadingError(f"{name}: missing (never defaulted)")
    v = float(v)
    if not (0 < v <= hi):
        raise ReadingError(f"{name}={v}: not a metre value in (0, {hi}] (mm given as m?)")
    return v


@dataclass(frozen=True)
class Reading:
    """One sheet's reading of the flight from the lower floor to the landing reached by the turn.

    straight_risers: risers of the straight part, the last of them fronting the first winder.
    turn_risers: risers from the first winder to the landing (the last one is the landing edge).
    foot_s: run position of the first straight front, measured from the first-winder front (negative, metres).
    tread_levels: levels the sheet DRAWS for the winder treads (a section's dashed treads), lowest first; () if none.
    """
    name: str
    source: str
    straight_risers: int
    turn_risers: int
    foot_s: float | None = None
    going: float | None = None
    tread_levels: tuple = ()

    def __post_init__(self):
        if self.straight_risers < 1 or self.turn_risers < 1:
            raise ReadingError(f"{self.name}: counts must be >= 1")
        if self.going is not None:
            _m(f"{self.name}.going", self.going, 2.0)


def evaluate(r: Reading, ffl_low: float, level_landing: float, plan_foot_s: list[float]) -> dict:
    """Checks of one reading. ffl_low / level_landing are PRINTED finished levels (m). plan_foot_s: the foot
    positions other drawings draw (m, same reference). Uniform finished risers between the two printed levels."""
    rise = level_landing - ffl_low
    if not (0 < rise <= 10):
        raise ReadingError(f"rise {rise}: not a storey part in metres")
    n = r.straight_risers + r.turn_risers
    riser = rise / n
    _m(f"{r.name}.riser", riser, 1.0)
    out = {"reading": r.name, "source": r.source, "risers_to_landing": n, "riser_m": round(riser, 6),
           "riser_check": "PASS" if RISER_CHECK[0] - 1e-9 <= riser <= RISER_CHECK[1] + 1e-9 else "FAIL"}
    if r.going is not None:
        out["going_check"] = "PASS" if GOING_CHECK[0] - 1e-9 <= r.going <= GOING_CHECK[1] + 1e-9 else "FAIL"
        out["straight_run_m"] = round((r.straight_risers - 1) * r.going, 6)
    if r.foot_s is not None and plan_foot_s:
        agree = [p for p in plan_foot_s if abs(p - r.foot_s) <= RUN_TOL]
        out["foot_agrees_with"] = len(agree)
        out["foot_check"] = "PASS" if agree else "FAIL"
    # predicted winder tread levels: tread behind front k sits at ffl + k * riser, k = straight .. n - 1
    pred = [ffl_low + k * riser for k in range(r.straight_risers, n)]
    out["predicted_tread_levels"] = [round(x, 4) for x in pred]
    return out


def level_fit(pred: list[float], drawn: tuple) -> tuple[str, float | None]:
    """Compare drawn tread levels (lowest first, possibly fewer than predicted: a tread hidden behind a cut slab)
    with the predicted ones, matched from the lowest. Returns (PASS / FAIL / NONE, worst miss in m)."""
    if not drawn:
        return "NONE", None
    if len(drawn) > len(pred):
        return "FAIL", None
    miss = max(abs(a - b) for a, b in zip(pred, drawn))
    return ("PASS" if miss <= LEVEL_TOL else "FAIL"), round(miss, 4)


def governing(readings: list[Reading], ffl_low: float, level_landing: float, owner_rule_source: str | None,
              section_levels: tuple = ()) -> dict:
    """Name the governing reading of the turn count, or HELD with the conflict named.

    A reading governs ONLY when an answered owner rule names its source (Q-46 A: the section) AND it is consistent with
    the drawn evidence (the drawn tread levels, and the foot position at least one other drawing draws). The fit of the
    other readings is reported as checks; the best-fitting reading is NEVER selected without a governing reason."""
    if not readings:
        raise ReadingError("no readings")
    names = [r.name for r in readings]
    if len(set(names)) != len(names):
        raise ReadingError("reading named twice")
    feet = {r.name: r.foot_s for r in readings if r.foot_s is not None}
    table = []
    for r in readings:
        others = [v for k, v in feet.items() if k != r.name]
        ev = evaluate(r, ffl_low, level_landing, others)
        ev["level_check"], ev["level_miss_m"] = level_fit(
            [ffl_low + k * ev["riser_m"] for k in range(r.straight_risers, ev["risers_to_landing"])], section_levels)
        table.append(ev)
    res = {"table": table, "governing": None, "turn_risers": None, "status": HELD, "reason": ""}
    if owner_rule_source is None:
        res["reason"] = "NO_GOVERNING_REASON: no answered owner rule names a source; best fit is not a reason"
        for ev in table:
            ev["verdict"] = CONFLICT
        return res
    gov = [r for r in readings if r.source == owner_rule_source]
    if len(gov) != 1:
        res["reason"] = f"NO_GOVERNING_REASON: the rule's source '{owner_rule_source}' is not exactly one reading"
        for ev in table:
            ev["verdict"] = CONFLICT
        return res
    g = gov[0]
    gev = next(ev for ev in table if ev["reading"] == g.name)
    bad = [k for k in ("level_check", "foot_check") if gev.get(k) == "FAIL"]
    if bad:
        res["reason"] = f"CONFLICT: the governing source {g.name} fails {bad} against the other drawn evidence"
        for ev in table:
            ev["verdict"] = CONFLICT
        return res
    for ev in table:
        if ev["reading"] == g.name:
            ev["verdict"] = GOVERNING
        else:
            why = [k for k in ("riser_check", "level_check", "foot_check") if ev.get(k) == "FAIL"]
            ev["verdict"] = REJECTED
            ev["rejected_because"] = why or ["differs from the governing source (Q-46 A); no check fails"]
    res.update(governing=g.name, turn_risers=g.turn_risers, status=CONFIRMED,
               reason=f"owner rule names '{owner_rule_source}' and it is consistent with the drawn evidence")
    return res


def shoelace(poly: list[tuple[float, float]]) -> float:
    if len(poly) < 3:
        raise ReadingError("polygon needs 3 points")
    s = 0.0
    for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]):
        s += x0 * y1 - x1 * y0
    return abs(s) / 2.0


@dataclass
class TurnDrawing:
    """What the plans draw for the turn: winder front lengths (m, source 'drawn' only), the landing edge (length and
    the drawings that draw it at one position), the turn region (front of the first winder to the landing edge)."""
    winder_fronts: list = field(default_factory=list)       # [(handle, length_m, source)]
    landing_edge_m: float | None = None
    landing_edge_drawings: tuple = ()
    region_polygon: list = field(default_factory=list)       # [(x, y)] in metres


def turn_quantities(turn_risers: int | None, d: TurnDrawing) -> dict:
    """Nosing / tread quantities of the turn for a governing count. Winders are never generated (S-9): a drawn
    subdivision with a different number of winder fronts than the governing count leaves every winder front and the
    turn marble HELD (A8), with the drawn figures beside, never as the quantity."""
    for h, ln, src in d.winder_fronts:
        if src != "drawn":
            raise ReadingError(f"winder front {h}: source '{src}' (winders are never generated, S-9)")
        _m(f"front {h}", ln, 5.0)
    region = round(shoelace(d.region_polygon), 6) if d.region_polygon else None
    if region is not None:
        _m("turn region area", region, 50.0)
    out = {"turn_risers": turn_risers, "nosing_pieces": None, "winder_tread_pieces": None,
           "landing_edge": {"status": HELD, "lm": None, "beside_lm": d.landing_edge_m},
           "winder_fronts": {"status": HELD, "lm": None, "drawn_count": len(d.winder_fronts),
                             "beside_lm": round(sum(x[1] for x in d.winder_fronts), 6) if d.winder_fronts else None},
           "tread_marble": {"status": HELD, "m2": None, "beside_m2": region}}
    if turn_risers is None:
        out["cause"] = "TURN_COUNT_HELD"
        return out
    out["nosing_pieces"] = turn_risers                    # one riser, one nosing (R-T412-1)
    out["winder_tread_pieces"] = turn_risers              # first winder fronted by the last straight front
    if d.landing_edge_m is not None and len(set(d.landing_edge_drawings)) >= 2:
        out["landing_edge"] = {"status": CONFIRMED, "lm": _m("landing edge", d.landing_edge_m, 10.0),
                               "drawings": sorted(set(d.landing_edge_drawings))}
    if len(d.winder_fronts) == turn_risers - 1:
        out["winder_fronts"] = {"status": CONFIRMED, "lm": round(sum(x[1] for x in d.winder_fronts), 6),
                                "drawn_count": len(d.winder_fronts)}
        out["tread_marble"] = {"status": CONFIRMED if region is not None else HELD, "m2": region,
                               "beside_m2": None}
    else:
        out["cause"] = (f"WINDER_SUBDIVISION_NOT_DRAWN: the plans draw {len(d.winder_fronts)} winder fronts (a "
                        f"{len(d.winder_fronts) + 1}-riser turn); the governing count is {turn_risers}; winders are "
                        "never generated (S-9); winder fronts and turn marble HELD (A8)")
    return out


def reach(ranges: dict[str, tuple[int, int]]) -> tuple[int, int]:
    """Smallest and largest total piece count any combination of drawn readings gives."""
    lo = sum(a for a, _ in ranges.values())
    hi = sum(b for _, b in ranges.values())
    return lo, hi


def rotate(poly, deg, mirror=False):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    out = [((-x if mirror else x) * c - y * s, (-x if mirror else x) * s + y * c) for x, y in poly]
    return out
