"""BLOCKWORK_BASIS_RULES_V1: drawing-derived blockwork (masonry) basis rules (A1 class A, T-449 round 3 = blockwork).

Owner follow-up directive 2026-11-02 (MISSION.md, A1): a project-specific correction is (A) a drawing-derived rule,
(B) a declared project fact (URBAN_PROJECT_CONFIG_V1) or (C) an unexplained patch. The V3.0.26 candidate input carries a
per-wall blockwork fill that Checker-merged ledgers computed by hand (T-333 over register v4). This module states the
GENERAL rules behind it, so a villa's block-wall lines follow from its drawn wall pieces plus its declared facts:

  R-MAS-PIECE-HEIGHT-1  (owner Q-60 A) a block wall rises from its structural floor to the underside of whatever sits on
                        it: piece height = declared storey height (structural top to structural top) - printed depth of
                        the beam over the piece, or - the printed slab thickness where no beam runs over it. A storey
                        that is not declared (a split-level annex, owner Q-54 B), a member whose depth is not printed,
                        or a piece with nothing drawn over it keeps that piece HELD (never 0, never a default depth).
  R-MAS-OPENING-DEDUCT-1 (owner Q-73: full deduction of every actual opening; Q-55 C: a door with no printed height takes
                        the declared company fallback height): the deducted area is the drawn opening outline inside the
                        masonry when it is drawn, else width x printed height, else (doors only) width x the declared
                        fallback height -> the wall's status becomes ASSUMED - OWNER-APPROVED; anything else HELD.
                        An opening inside a HELD piece is deducted with that piece (never from the established part).
  R-MAS-WALL-NET-1      wall net = sum over its closable pieces of length x height - its deducted openings. Every piece
                        closable -> VALUED; some piece HELD and some closable -> PART (the established part is a value,
                        the held pieces are named, the wall total is never presented); nothing closable -> HELD.
  R-MAS-DROP-1          (R-T288-1, owner D-41 open) a piece under a SUNKEN slab panel rises to storey - t - d with the
                        drop d not printed: the wall carries U - L x d, U = its net at d = 0 (an upper bound, never a
                        quantity) and L = the summed sunken length; state DROP, never evaluated.
  R-MAS-PANEL-SAME-1    the wall-panel geometry line (m2) is the same physical face as the masonry material line (m2).
  R-MAS-VOLUME-1        wall volume (m3) = wall area (m2) x the wall's drawn thickness (m).

Results carry state VALUED / PART / DROP / HELD, the value only when VALUED or PART (the established part), the upper
bound only on DROP, the facts used and the held pieces by name. Missing never becomes 0. Standard library only, no
engine import: facts arrive as any object with lookup(fact_id) (the URBAN_PROJECT_CONFIG_V1 loader's interface).
Wired into no candidate method (an unwired producer: candidate wiring is a new V3.0.x under Checker Gate B).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Sequence

DEFAULT_GUARD_CLASS = "UNWIRED_PRODUCER"  # T-212: computes masonry quantities, wired nowhere (guard due at integration)
RULE_VERSION = "BLOCKWORK_BASIS_RULES_V1"

HELD = "HELD"
VALUED = "VALUED"
PART = "PART"
DROP = "DROP"
DRAWING_CONFIRMED = "DRAWING-CONFIRMED"
ASSUMED_OWNER_APPROVED = "ASSUMED — OWNER-APPROVED"
DOOR = "DOOR"
MAX_STOREY_M = 12.0       # a storey height above this is a unit error (mm read as m), refused
MAX_PIECE_M = 200.0


class BlockworkRuleError(ValueError):
    """an input the rules refuse (the code is the first word of the message)."""


def _pos(x, what, hi=MAX_PIECE_M):
    if not isinstance(x, (int, float)) or isinstance(x, bool) or not math.isfinite(x) or x <= 0 or x > hi:
        raise BlockworkRuleError(f"BAD_UNITS: {what} must be a positive number of metres (<= {hi}), got {x!r}")
    return float(x)


@dataclass(frozen=True)
class Piece:
    """one length of a wall under one soffit: the drawn length (m) and what sits on it (beam depth or slab thickness,
    both printed, metres). held_reason names why nothing usable is drawn over it (no member, depth not printed, a dome
    opening, a stair-foot with no landing member, ...)."""

    piece_id: str
    length_m: float
    depth_m: float | None = None          # printed depth of the beam over the piece
    slab_t_m: float | None = None         # printed slab thickness where no beam runs over the piece
    sunken: bool = False                  # under a SUNKEN slab panel (R-MAS-DROP-1)
    held_reason: str | None = None


@dataclass(frozen=True)
class Opening:
    """one opening built into the wall. outline_m2 = the drawn outline inside the masonry (an arch, a jamb inside the
    wall) when drawn; else width_m x height_m (printed); a DOOR with no printed height may take the declared fallback."""

    opening_id: str
    kind: str
    width_m: float | None = None
    height_m: float | None = None
    outline_m2: float | None = None
    in_held_piece: bool = False


@dataclass(frozen=True)
class WallResult:
    rule: str
    wall_id: str
    state: str                            # VALUED / PART / DROP / HELD
    value: float | None                   # m2: the net (VALUED) or the established part (PART)
    status: str | None = None             # DRAWING-CONFIRMED / ASSUMED — OWNER-APPROVED of the value or bound
    upper_m2: float | None = None         # DROP only: U at d = 0 (an upper bound, never a quantity)
    drop_length_m: float | None = None    # DROP only: L of U - L x d
    deducted_m2: float = 0.0
    held: tuple[str, ...] = ()
    facts_used: tuple[str, ...] = ()
    formula: str = ""
    pieces: tuple = field(default_factory=tuple)


def storey_height(cfg, fact_id):
    """(metres, None) when the declared storey height is usable, else (None, reason). Refuses a unit error."""
    lk = cfg.lookup(fact_id)
    if not lk.usable:
        return None, f"{fact_id} HELD: {lk.reason}"
    if lk.fact.quantity_kind != "LENGTH":
        raise BlockworkRuleError(f"BAD_FACT: {fact_id} is a {lk.fact.quantity_kind}, not a LENGTH")
    return _pos(lk.base_value(), fact_id, MAX_STOREY_M), None


def piece_height(storey_m, piece: Piece):
    """R-MAS-PIECE-HEIGHT-1: (height_m, None) or (None, held reason). storey_m None -> HELD (storey not declared)."""
    _pos(piece.length_m, f"{piece.piece_id} length")
    if piece.held_reason:
        return None, piece.held_reason
    if piece.depth_m is not None and piece.slab_t_m is not None:
        raise BlockworkRuleError(f"TWO_SOFFITS: {piece.piece_id} names a beam and a slab; one soffit per piece")
    if storey_m is None:
        return None, "storey height not declared"
    if piece.depth_m is not None:
        d = _pos(piece.depth_m, f"{piece.piece_id} beam depth", 3.0)
    elif piece.slab_t_m is not None:
        d = _pos(piece.slab_t_m, f"{piece.piece_id} slab thickness", 1.0)
    else:
        return None, "no member with a printed soffit drawn over the piece"
    h = storey_m - d
    if h <= 0:
        raise BlockworkRuleError(f"BAD_LEVEL: {piece.piece_id}: soffit depth {d} >= storey {storey_m}")
    return round(h, 6), None


def opening_deduction(cfg, op: Opening, door_fallback_fact=None):
    """R-MAS-OPENING-DEDUCT-1: (area_m2, status, fact_or_None) or (None, HELD reason, None)."""
    if op.outline_m2 is not None:
        return _pos(op.outline_m2, f"{op.opening_id} outline", 100.0), DRAWING_CONFIRMED, None
    if op.width_m is None:
        return None, f"{op.opening_id}: width not drawn", None
    w = _pos(op.width_m, f"{op.opening_id} width", 20.0)
    if op.height_m is not None:
        return round(w * _pos(op.height_m, f"{op.opening_id} height", 12.0), 6), DRAWING_CONFIRMED, None
    if op.kind != DOOR or door_fallback_fact is None:
        return None, f"{op.opening_id}: height not printed (only a door takes the declared fallback)", None
    lk = cfg.lookup(door_fallback_fact)
    if not lk.usable:
        return None, f"{op.opening_id}: {door_fallback_fact} HELD: {lk.reason}", None
    h = _pos(lk.base_value(), door_fallback_fact, 6.0)
    return round(w * h, 6), ASSUMED_OWNER_APPROVED, door_fallback_fact


def wall_net(cfg, wall_id: str, storey_fact: str, pieces: Sequence[Piece], openings: Sequence[Opening] = (),
             door_fallback_fact: str | None = None, held_notes: Sequence[str] = ()) -> WallResult:
    """R-MAS-WALL-NET-1 / R-MAS-DROP-1 for one wall. held_notes: printed notes that put an unsized member over the
    wall (e.g. a tie beam called for by a note with no size): the whole wall is HELD by name.
    An opening that cannot be deducted outside the held pieces makes the whole wall HELD (its position against the
    pieces is what would decide the part, so no established part is presented)."""
    if not pieces:                                  # no wall band / member bound to it: HELD by name, never 0
        return WallResult("R-MAS-WALL-NET-1", wall_id, HELD, None, None, held=tuple(held_notes) + (
            "no drawn wall piece (no wall band or member bound)",), formula="no drawn piece")
    ids = [p.piece_id for p in pieces]
    if len(set(ids)) != len(ids):
        raise BlockworkRuleError(f"DUPLICATE_PIECE: {wall_id}")
    st, st_why = storey_height(cfg, storey_fact)
    used = [storey_fact] if st is not None else []
    closable, held, sunk, rows = 0.0, [], 0.0, []
    for p in pieces:
        h, why = piece_height(st, p)
        if h is None:
            held.append(f"{p.piece_id} {p.length_m:.4f} m: {why if why != 'storey height not declared' else st_why}")
            rows.append((p.piece_id, p.length_m, None))
            continue
        closable += p.length_m * h
        if p.sunken:
            sunk += p.length_m
        rows.append((p.piece_id, p.length_m, h))
    status, ded, terms, op_held = DRAWING_CONFIRMED, 0.0, [], []
    for op in openings:
        if op.in_held_piece:
            continue                                # deducted with its held piece, never from the established part
        a, s, fct = opening_deduction(cfg, op, door_fallback_fact)
        if a is None:
            op_held.append(f"opening {s}")
            continue
        ded += a
        terms.append(f"{op.opening_id} {a:.4f}")
        if s == ASSUMED_OWNER_APPROVED:
            status = ASSUMED_OWNER_APPROVED
            if fct not in used:
                used.append(fct)
    any_closable = any(h is not None for _, _, h in rows)
    gross = " + ".join(f"{L:.4f} x {h:.4f}" for _, L, h in rows if h is not None)
    formula = f"[{gross}] - [{' + '.join(terms) or '0'}]"
    if not any_closable or op_held or held_notes:
        why = "no closable piece" if not any_closable else ("held note" if held_notes else "opening not deductible")
        return WallResult("R-MAS-WALL-NET-1", wall_id, HELD, None, None,
                          held=tuple(held_notes) + tuple(op_held) + tuple(held), facts_used=tuple(used),
                          formula=why, pieces=tuple(rows))
    net = round(closable - ded, 6)
    if net <= 0 and held:                           # the openings sit in the held pieces: no part is established
        return WallResult("R-MAS-WALL-NET-1", wall_id, HELD, None, None, held=tuple(held) + (
            f"openings {ded:.4f} m2 exceed the closable part {closable:.4f} m2: their position against the held "
            f"pieces is not read",), facts_used=tuple(used), formula=formula, pieces=tuple(rows))
    if net <= 0:
        raise BlockworkRuleError(f"NON_POSITIVE: {wall_id}: openings {ded} >= closable gross {closable}")
    if sunk > 0:
        return WallResult("R-MAS-DROP-1", wall_id, DROP, None, status, upper_m2=net, drop_length_m=round(sunk, 6),
                          deducted_m2=round(ded, 6), held=tuple(held) + (f"drop d of the sunken panel over "
                                                                         f"{sunk:.4f} m",),
                          facts_used=tuple(used), formula=f"{formula} - {sunk:.4f} x d", pieces=tuple(rows))
    state = PART if held else VALUED
    return WallResult("R-MAS-WALL-NET-1", wall_id, state, net, status, deducted_m2=round(ded, 6), held=tuple(held),
                      facts_used=tuple(used), formula=formula, pieces=tuple(rows))


@dataclass(frozen=True)
class RangeResult:
    rule: str
    state: str                            # HELD (a range kept beside a held line, never summed)
    low: float | None
    high: float | None
    formula: str = ""
    facts_used: tuple[str, ...] = ()
    held_reason: str | None = None


def parapet_block_alternative(cfg, run_id: str, centreline_m: float, height_m: float, upstand_fact: str,
                              material_decided_rc: bool = False) -> RangeResult:
    """R-MAS-PARAPET-BLOCK-ALT-1 (owner blockwork rule: block above the RC upstand is masonry, exclusive with the RC
    above it): while the parapet material above the upstand is HELD, the block alternative is the range
    [0, centreline x (printed height - declared minimum RC upstand)]; all-RC decided -> [0, 0]. A height not above the
    upstand gives no block (range [0, 0]); an undeclared upstand keeps the range blank (HELD, never 0)."""
    rule = "R-MAS-PARAPET-BLOCK-ALT-1"
    c = _pos(centreline_m, f"{run_id} centreline")
    h = _pos(height_m, f"{run_id} height", 6.0)
    if material_decided_rc:
        return RangeResult(rule, HELD, 0.0, 0.0, "all RC decided: no block", ())
    lk = cfg.lookup(upstand_fact)
    if not lk.usable:
        return RangeResult(rule, HELD, None, None, "", (), f"{upstand_fact} HELD: {lk.reason}")
    up = _pos(lk.base_value(), upstand_fact, 3.0)
    hi = round(c * max(h - up, 0.0), 6)
    return RangeResult(rule, HELD, 0.0, hi, f"[0, {c} x ({h} - {up})]", (upstand_fact,),
                       "parapet material above the upstand HELD (block OR RC)")


def panel_area(res: WallResult):
    """R-MAS-PANEL-SAME-1: the wall-panel m2 is the masonry m2 (same face, same state)."""
    return res.value


def volume(res: WallResult, thickness_m: float):
    """R-MAS-VOLUME-1: m3 = m2 x drawn thickness; a HELD / DROP wall has no volume (never 0)."""
    t = _pos(thickness_m, "wall thickness", 1.0)
    return None if res.value is None else round(res.value * t, 6)
