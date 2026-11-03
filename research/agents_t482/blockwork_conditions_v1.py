"""BLOCKWORK_CONDITIONS_V1 (T-482, research rule version; no engine / rule / knowledge version file edited).

Three wiring conditions the T-449 round 3 verdict (Checker O-1 / O-3) set before BLOCKWORK_BASIS_RULES_V1 is wired.
They EXTEND the V1 rules (engine/source/blockwork_basis_rules_v1.py, read only, imported) and never change them:

  R-MAS-ROOF-DATUM-1   (D-39, Q-54 B, Q-60 A, Q-72; T-214 / T-248 readings) a storey's top datum is the STRUCTURAL top
                       of the plate over it, one basis for every trade that reads it (block walls, columns, parapet
                       solids). A plate that also carries a floor zone with a DRAWN build-up b takes top = FFL - b
                       (DRAWING-CONFIRMED). A plate that carries ONLY roof zones (only a finished roof mark printed,
                       build-up b_r unprinted) has top = mark - b_r with b_r HELD: a wall under it carries
                       U - L x b_r (U = its net at b_r = 0, an UPPER BOUND, never a quantity; L = the summed length
                       of its closable pieces), state ROOF_DATUM, never evaluated. The architectural finished chain
                       (FFL to the finished roof) is refused as a structural storey under a roof (FINISHED_AS_STRUCTURAL).
                       A printed bound on b_r (e.g. 'upstand must be more than the roof finishing') narrows b_r only
                       when the detail is keyed to that roof AND the mark is read at that edge; otherwise it is named
                       beside, never applied.
  R-MAS-WIDTH-CONFLICT-1 (Q-61 C(1), D-27; T-215 / T-277) a wall piece under a band whose member width is a named
                       CONFLICT (schedule vs drawn) carries both readings as a CONFLICT range [min, max], each end
                       attributed to its reading; the line is BOUNDED, never one end presented as DRAWING-CONFIRMED
                       (never the larger, never the smaller, never a mean). On a DROP wall the upper bound U is the
                       MAX over the readings (an upper bound must hold under both).
  R-MAS-PARAPET-RUN-1  (T-324 C3; R-MAS-PARAPET-BLOCK-ALT-1) a parapet's block alternative is evaluated on the run's
                       centreline as DRAWN AT PARAPET (ROOF) LEVEL; a length carried from the floor outline below
                       (a bay arc under a straight roof-level parapet) is refused (FLOOR_OUTLINE_RUN). The change is
                       reconciled in m2 to its cause: delta = (c_new - c_old) x (h - upstand).

Standard library only; facts arrive through any object with lookup(fact_id) (URBAN_PROJECT_CONFIG_V1 interface).
Unwired research producer: candidate wiring is a new V3.0.x under Checker Gate B.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import blockwork_basis_rules_v1 as R  # noqa: E402  (read only)

RULE_VERSION = "BLOCKWORK_CONDITIONS_V1"
ROOF_DATUM = "ROOF_DATUM"
CONFLICT = "CONFLICT"
FLOOR = "FLOOR"
ROOF = "ROOF"


class ConditionError(ValueError):
    """an input the conditions refuse (the code is the first word of the message)."""


def _num(x, what, lo=0.0, hi=50.0, allow_zero=False):
    if not isinstance(x, (int, float)) or isinstance(x, bool) or not math.isfinite(x):
        raise ConditionError(f"BAD_UNITS: {what} must be a number of metres, got {x!r}")
    if (x < lo or (x == lo and not allow_zero)) or x > hi:
        raise ConditionError(f"BAD_UNITS: {what} out of range ({lo} .. {hi} m): {x!r}")
    return float(x)


# ===================================================================================== R-MAS-ROOF-DATUM-1
@dataclass(frozen=True)
class Zone:
    """one zone of a structural plate: FLOOR (a finished floor over it, build-up drawn or not) or ROOF (a finished
    roof mark over it). level_m = the printed finished mark; buildup_m = the DRAWN build-up (FLOOR only; a roof's
    build-up is never taken from a drawn constant layer that cannot carry its falls, T-214)."""

    zone_id: str
    kind: str
    level_m: float
    buildup_m: float | None = None
    source: str = ""


@dataclass(frozen=True)
class Plate:
    """one structural slab plate drawn at one level on a structural slab plan (no step, drop or sunken hatch between
    its zones). zones = the finished-level zones it carries."""

    plate_id: str
    zones: tuple
    source: str = ""


@dataclass(frozen=True)
class Datum:
    rule: str
    plate_id: str
    state: str                          # VALUED (top known) / ROOF_DATUM (top = upper - b_r, b_r HELD)
    top_m: float | None                 # VALUED only
    upper_m: float | None               # ROOF_DATUM only: the finished roof mark (b_r >= 0)
    basis: str = ""
    held: tuple = ()
    beside: tuple = ()


def plate_top(plate: Plate, roof_bound_note: str | None = None) -> Datum:
    """R-MAS-ROOF-DATUM-1: the structural top of one plate."""
    rule = "R-MAS-ROOF-DATUM-1"
    if not plate.zones:
        raise ConditionError(f"NO_ZONE: plate {plate.plate_id} carries no finished-level zone")
    floors = [z for z in plate.zones if z.kind == FLOOR]
    roofs = [z for z in plate.zones if z.kind == ROOF]
    if len(floors) + len(roofs) != len(plate.zones):
        raise ConditionError(f"BAD_ZONE: plate {plate.plate_id}: zone kind must be FLOOR or ROOF")
    for z in roofs:
        if z.buildup_m is not None:
            raise ConditionError(f"ROOF_BUILDUP_CONSTANT: {z.zone_id}: a roof build-up is never a drawn constant "
                                 f"layer (it cannot carry the falls; D-39 / T-214)")
    tops = []
    for z in floors:
        lv = _num(z.level_m, f"{z.zone_id} level", -20.0, 200.0)
        if z.buildup_m is None:
            continue
        b = _num(z.buildup_m, f"{z.zone_id} build-up", 0.0, 1.0, allow_zero=True)
        tops.append((round(lv - b, 6), z))
    if tops:
        vals = {t for t, _ in tops}
        if max(vals) - min(vals) > 0.0015:
            raise ConditionError(f"PLATE_CONFLICT: plate {plate.plate_id} floor zones give tops {sorted(vals)}: a "
                                 f"single plate has one top (read a step / drop instead)")
        top, z = tops[0]
        return Datum(rule, plate.plate_id, R.VALUED, top, None,
                     basis=f"{z.zone_id} FFL {z.level_m:+.2f} - drawn build-up {z.buildup_m:.3f}; one plate carries "
                           f"its {len(roofs)} roof zone(s) at the same top")
    if floors:
        return Datum(rule, plate.plate_id, R.HELD, None, None, basis="floor zone with no drawn build-up",
                     held=(f"{plate.plate_id}: floor build-up not drawn",))
    marks = sorted({round(_num(z.level_m, f"{z.zone_id} level", -20.0, 200.0), 6) for z in roofs})
    if len(marks) > 1:
        raise ConditionError(f"PLATE_CONFLICT: roof-only plate {plate.plate_id} prints marks {marks}: one plate, one "
                             f"datum (read the falls / a step instead)")
    return Datum(rule, plate.plate_id, ROOF_DATUM, None, marks[0],
                 basis=f"roof-only plate: top = {marks[0]:+.2f} - b_r", held=(
                     f"{plate.plate_id}: roof build-up b_r not printed (D-39)",),
                 beside=(roof_bound_note,) if roof_bound_note else ())


def structural_storey(base: Datum, top: Datum):
    """(storey_m, None) for a VALUED pair; (None, upper_m) when the top is a ROOF_DATUM (upper = storey at b_r = 0);
    a HELD base or top -> (None, None)."""
    if base.state != R.VALUED:
        return None, None
    if top.state == R.VALUED:
        return round(top.top_m - base.top_m, 6), None
    if top.state == ROOF_DATUM:
        return None, round(top.upper_m - base.top_m, 6)
    return None, None


def refuse_finished_chain(storey_m: float, base: Datum, top: Datum, tol=0.0005):
    """FINISHED_AS_STRUCTURAL: a storey under a roof-only plate taken from the architectural finished chain (a value
    that equals mark - FFL, or any single value while b_r is HELD) is refused."""
    if top.state == ROOF_DATUM:
        raise ConditionError(f"FINISHED_AS_STRUCTURAL: storey {storey_m} under roof-only plate {top.plate_id}: the "
                             f"structural top is {top.upper_m:+.2f} - b_r with b_r HELD (D-39); no single storey")
    s, _ = structural_storey(base, top)
    if s is not None and abs(s - storey_m) > tol:
        raise ConditionError(f"STOREY_MISMATCH: declared {storey_m} vs structural {s} ({base.plate_id} -> "
                             f"{top.plate_id})")
    return True


class _UpperCfg:
    """the config seen by V1 with ONE storey fact replaced by its b_r = 0 upper bound (a bound, never declared)."""

    def __init__(self, cfg, fact_id, upper_m):
        self._cfg, self._fid, self._u = cfg, fact_id, upper_m

    def lookup(self, fid):
        lk = self._cfg.lookup(fid)
        if fid != self._fid:
            return lk
        u = self._u

        class _Lk:
            usable = True
            reason = None
            fact = type("F", (), {"quantity_kind": "LENGTH"})()

            def base_value(self):
                return u
        return _Lk()

    def history(self, fid):
        return self._cfg.history(fid) if hasattr(self._cfg, "history") else ()


@dataclass(frozen=True)
class RoofWall:
    rule: str
    wall_id: str
    state: str                     # ROOF_DATUM (U - L x b_r) / HELD (V1 held whole wall)
    upper_m2: float | None         # the net / established part at b_r = 0 (an upper bound)
    datum_length_m: float | None   # L of U - L x b_r (closable length under the roof-only plate)
    part: bool = False             # True: U is the established part's bound (held pieces named)
    drop_length_m: float | None = None
    held: tuple = ()
    formula: str = ""
    v1_at_storey: float | None = None   # the V1 figure at a supplied what-if storey (audit only, never a quantity)


def wall_under_roof(cfg, wall_id: str, storey_fact: str, base: Datum, top: Datum, pieces: Sequence[R.Piece],
                    openings: Sequence[R.Opening] = (), door_fallback_fact=None, held_notes=(),
                    what_if_storey_m: float | None = None) -> RoofWall:
    """R-MAS-ROOF-DATUM-1 applied to one wall whose pieces sit under a roof-only plate."""
    if top.state != ROOF_DATUM:
        raise ConditionError(f"NOT_ROOF_ONLY: {top.plate_id} is {top.state}; use V1 wall_net with the storey fact")
    if base.state != R.VALUED:
        raise ConditionError(f"BASE_HELD: {base.plate_id}: the wall's base datum is not established")
    _, upper = structural_storey(base, top)
    res = R.wall_net(_UpperCfg(cfg, storey_fact, upper), wall_id, storey_fact, pieces, openings, door_fallback_fact,
                     held_notes)
    held = tuple(res.held) + (f"roof build-up b_r over {top.plate_id} not printed (D-39)",)
    if res.state == R.HELD:
        return RoofWall("R-MAS-ROOF-DATUM-1", wall_id, R.HELD, None, None, held=tuple(res.held),
                        formula=res.formula)
    L = round(math.fsum(L for _, L, h in res.pieces if h is not None), 6)
    U = res.upper_m2 if res.state == R.DROP else res.value
    wi = None
    if what_if_storey_m is not None:
        w = R.wall_net(_UpperCfg(cfg, storey_fact, what_if_storey_m), wall_id, storey_fact, pieces, openings,
                       door_fallback_fact, held_notes)
        wi = w.upper_m2 if w.state == R.DROP else w.value
    return RoofWall("R-MAS-ROOF-DATUM-1", wall_id, ROOF_DATUM, round(U, 6), L, part=res.state == R.PART,
                    drop_length_m=res.drop_length_m, held=held,
                    formula=f"{res.formula} at storey {upper:.4f} (b_r = 0) -> {U:.4f} - {L:.4f} x b_r"
                            + (f" - {res.drop_length_m:.4f} x d" if res.drop_length_m else ""),
                    v1_at_storey=None if wi is None else round(wi, 6))


# ================================================================================= R-MAS-WIDTH-CONFLICT-1
@dataclass(frozen=True)
class ConflictRange:
    rule: str
    element_id: str
    state: str                     # CONFLICT (bounded)
    low: float
    high: float
    low_reading: str
    high_reading: str
    conflict_id: str
    note: str = ""


def width_conflict(element_id: str, conflict_id: str, readings: dict, carried: float | None = None,
                   carried_status: str | None = None, tol=0.0005) -> ConflictRange:
    """readings: {reading name: m2 of the element under that reading} (at least two). A carried single figure equal to
    one end with a DRAWING-CONFIRMED status is refused (CONFLICT_ONE_END)."""
    if not conflict_id:
        raise ConditionError("NO_CONFLICT_ID: a width conflict range needs its named designer / owner item")
    if len(readings) < 2:
        raise ConditionError(f"ONE_READING: {element_id}: a CONFLICT range needs both readings")
    vals = {k: _num(v, f"{element_id} {k}", 0.0, 10000.0, allow_zero=True) for k, v in readings.items()}
    lo_k = min(vals, key=vals.get)
    hi_k = max(vals, key=vals.get)
    if carried is not None and carried_status in (R.DRAWING_CONFIRMED, "VERIFIED") and \
            (abs(carried - vals[lo_k]) <= tol or abs(carried - vals[hi_k]) <= tol) and \
            abs(vals[hi_k] - vals[lo_k]) > tol:
        raise ConditionError(f"CONFLICT_ONE_END: {element_id} carries {carried} {carried_status}, one end of the "
                             f"{conflict_id} range [{vals[lo_k]}, {vals[hi_k]}]")
    return ConflictRange("R-MAS-WIDTH-CONFLICT-1", element_id, CONFLICT, round(vals[lo_k], 6), round(vals[hi_k], 6),
                         lo_k, hi_k, conflict_id)


def drop_upper_over_readings(element_id: str, uppers: dict) -> tuple:
    """R-MAS-WIDTH-CONFLICT-1 on a DROP wall: U = max over the readings (an upper bound holds under both)."""
    if len(uppers) < 2:
        raise ConditionError(f"ONE_READING: {element_id}: the DROP bound needs every reading")
    vals = {k: _num(v, f"{element_id} U {k}", 0.0, 10000.0) for k, v in uppers.items()}
    k = max(vals, key=vals.get)
    return round(vals[k], 6), k


# ==================================================================================== R-MAS-PARAPET-RUN-1
@dataclass(frozen=True)
class ParapetRun:
    run_id: str
    centreline_m: float
    height_m: float
    drawn_at: str                  # "ROOF_LEVEL" (the roof plan's own run) or "FLOOR_OUTLINE" (the outline below)


def parapet_alternative(cfg, run: ParapetRun, upstand_fact: str, previous_centreline_m: float | None = None):
    """-> (V1 RangeResult, delta_m2 vs the previous centreline or None)."""
    if run.drawn_at != "ROOF_LEVEL":
        raise ConditionError(f"FLOOR_OUTLINE_RUN: {run.run_id}: the block alternative needs the run as drawn at "
                             f"parapet (roof) level, not {run.drawn_at}")
    res = R.parapet_block_alternative(cfg, run.run_id, run.centreline_m, run.height_m, upstand_fact)
    delta = None
    if previous_centreline_m is not None and res.high is not None:
        lk = cfg.lookup(upstand_fact)
        up = lk.base_value()
        delta = round((run.centreline_m - _num(previous_centreline_m, "previous centreline", 0.0, 200.0))
                      * max(run.height_m - up, 0.0), 6)
    return res, delta
