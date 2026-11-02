"""CONCRETE_BASIS_RULES_V1: drawing-derived concrete basis rules (A1 class A, T-449 round 1 = concrete).

Owner follow-up directive 2026-11-02 (MISSION.md, A1): a project-specific correction is (A) a drawing-derived rule,
(B) a declared project fact (the per-project config, schema URBAN_PROJECT_CONFIG_V1) or (C) an unexplained patch. The
V3.0.17 / V3.0.23 / V3.0.33 candidate inputs carry per-line concrete corrections that Checker-merged ledgers computed by
hand. This module states the GENERAL rules behind them, so a villa's lines follow from its drawing geometry plus its
declared facts and no per-line patch:

  R-GB-EXT-DEPTH-1    exterior ground beam printed 'FOLLOW ARCH.' between two printed levels: depth = structural top
                      level - outer natural ground level; volume = sum over runs of face-to-face length x drawn width x
                      depth. The zone's depth basis must be a declared, approved fact (a designer conflict on the zone
                      keeps every line HELD, its literal reading shown beside, never adopted).
  R-COL-LEVEL-HEIGHT-1  column height = top structural level - base level; volume = section x height. A level that is
                      not declared (an unprinted roof datum) keeps the line HELD.
  R-COL-SECTION-CONFLICT-1  printed schedule section vs drawn outline: equal -> one value; different -> a CONFLICT
                      range of both readings x height, HELD, never the schedule end, never a midpoint.
  R-PARAPET-RC-FLOOR-1  roof parapet RC: lower bound = top area x the printed minimum upstand above the slab top, upper
                      bound = top area x the printed parapet height (all RC); the line stays HELD while the material
                      above the upstand is undecided.

Every result is a RuleResult: state VALUED / HELD / CONFLICT, value only when VALUED, a range kept beside a held
line, the formula and the facts used. Missing never becomes 0; a declared level of 0.00 m is a real level and is used.
Standard library only, no engine import: the facts arrive as a config object that offers lookup(fact_id) and
history(fact_id) (the URBAN_PROJECT_CONFIG_V1 loader's interface; any object with them works). Wired into no
candidate method yet (an unwired producer:
the candidate wiring is a new V3.0.x version under Checker Gate B).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable, Mapping, Sequence


DEFAULT_GUARD_CLASS = "UNWIRED_PRODUCER"  # T-212: computes concrete quantities, wired nowhere (guard due at integration)
RULE_VERSION = "CONCRETE_BASIS_RULES_V1"

HELD = "HELD"                  # the config loader's HELD status string
VALUED = "VALUED"
CONFLICT = "CONFLICT"
TWO_PRINTED_LEVELS = "TWO_PRINTED_LEVELS"


@dataclass(frozen=True)
class RuleResult:
    rule: str
    state: str                        # VALUED / HELD / CONFLICT
    value: float | None               # m3 (or m) only when VALUED
    low: float | None = None          # range beside a HELD / CONFLICT line (never summed into the BOQ)
    high: float | None = None
    formula: str = ""
    facts_used: tuple[str, ...] = ()
    held_reason: str | None = None
    readings: Mapping[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Run:
    """One drawn run of a member: face-to-face length and drawn width, both metres, from the drawing geometry."""

    run_id: str
    length_m: float
    width_m: float


def _finite_positive(x, what):
    if not isinstance(x, (int, float)) or isinstance(x, bool) or not math.isfinite(x) or x <= 0:
        raise ValueError(f"{what} must be a finite positive number in metres, got {x!r}")
    return float(x)


def _level(cfg, fact_id: str):
    """(value_m, None) when the level fact is usable, else (None, reason). 0.00 m is a level, never 'missing'."""
    lk = cfg.lookup(fact_id)
    if not lk.usable:
        return None, f"{fact_id} HELD: {lk.reason}"
    if lk.fact.quantity_kind != "LENGTH":
        return None, f"{fact_id} is a {lk.fact.quantity_kind}, not a LENGTH level"
    return lk.base_value(), None


def ground_beam_exterior(cfg, runs: Sequence[Run], *, top_level: str, outer_ground_level: str,
                         depth_basis: str) -> RuleResult:
    """R-GB-EXT-DEPTH-1 for the runs of one ground-beam line in one zone."""
    rule = "R-GB-EXT-DEPTH-1"
    if not runs:
        raise ValueError("a ground-beam line needs at least one drawn run")
    plan = [(r.run_id, _finite_positive(r.length_m, f"{r.run_id} length"), _finite_positive(r.width_m,
                                                                                         f"{r.run_id} width"))
            for r in runs]
    used = (depth_basis, top_level, outer_ground_level)
    top, why_top = _level(cfg, top_level)
    ngl, why_ngl = _level(cfg, outer_ground_level)
    basis = cfg.lookup(depth_basis)
    literal = None
    if top is not None and ngl is not None:
        literal = top - ngl
    readings = {}
    if literal is not None and literal > 0:
        readings["literal_two_levels_m3"] = round(sum(L * b for _, L, b in plan) * literal, 6)
    if not basis.usable:
        # a PENDING declaration that names the zone's basis as CONFLICT (an open designer item) reports CONFLICT;
        # anything else unusable (not declared, superseded, pending another basis) is HELD. Neither carries a value.
        pend = [f for f in cfg.history(depth_basis) if f.active and f.approval_status == "PENDING"]
        state = CONFLICT if pend and pend[-1].value == CONFLICT else HELD
        return RuleResult(rule, state, None,
                          formula="depth basis not approved for this zone", facts_used=used,
                          held_reason=f"{depth_basis} HELD: {basis.reason}", readings=readings)
    if basis.fact.value != TWO_PRINTED_LEVELS:
        return RuleResult(rule, HELD, None, formula="zone depth basis is not two printed levels", facts_used=used,
                          held_reason=f"{depth_basis} = {basis.fact.value!r}", readings=readings)
    if top is None or ngl is None:
        return RuleResult(rule, HELD, None, formula="a bounding level is not declared", facts_used=used,
                          held_reason="; ".join(x for x in (why_top, why_ngl) if x), readings=readings)
    depth = top - ngl
    if depth <= 0:
        return RuleResult(rule, HELD, None, formula=f"depth {top} - {ngl} = {depth:.4f} m is not positive",
                          facts_used=used, held_reason="levels give no beam depth (inverted or equal levels)")
    vol = sum(L * b * depth for _, L, b in plan)
    terms = " + ".join(f"{rid} {L:.4f} x {b:.2f}" for rid, L, b in plan)
    return RuleResult(rule, VALUED, round(vol, 6),
                      formula=f"({terms}) x D {depth:.4f} (top {top:+.2f} - ground {ngl:+.2f}) = {vol:.6f} m3",
                      facts_used=used)


def column_between_levels(cfg, section_m2: float, *, base_level: str, top_level: str) -> RuleResult:
    """R-COL-LEVEL-HEIGHT-1: section x (top - base)."""
    rule = "R-COL-LEVEL-HEIGHT-1"
    a = _finite_positive(section_m2, "section")
    used = (base_level, top_level)
    base, why_b = _level(cfg, base_level)
    top, why_t = _level(cfg, top_level)
    if base is None or top is None:
        return RuleResult(rule, HELD, None, formula="a column end level is not declared", facts_used=used,
                          held_reason="; ".join(x for x in (why_b, why_t) if x))
    h = top - base
    if h <= 0:
        return RuleResult(rule, HELD, None, formula=f"h {top} - {base} = {h:.4f} m is not positive",
                          facts_used=used, held_reason="levels give no column height")
    return RuleResult(rule, VALUED, round(a * h, 6), formula=f"{a:.6f} m2 x ({top:.2f} - {base:.2f} = {h:.2f}) m",
                      facts_used=used)


def column_section_conflict(schedule_m2: float, drawn_m2: float, height_m: float, *, tol_m2: float = 1e-6,
                            designer_item: str = "") -> RuleResult:
    """R-COL-SECTION-CONFLICT-1: one value when the printed schedule and the drawn outline agree, else a range."""
    rule = "R-COL-SECTION-CONFLICT-1"
    s = _finite_positive(schedule_m2, "schedule section")
    d = _finite_positive(drawn_m2, "drawn section")
    h = _finite_positive(height_m, "height")
    if abs(s - d) <= tol_m2:
        return RuleResult(rule, VALUED, round(s * h, 6), formula=f"{s:.6f} m2 (schedule = drawn) x {h} m")
    rs, rd = round(s * h, 6), round(d * h, 6)
    return RuleResult(rule, CONFLICT, None, low=min(rs, rd), high=max(rs, rd),
                      formula=f"schedule {s:.6f} x {h} = {rs}; drawn {d:.6f} x {h} = {rd}",
                      held_reason=designer_item or "printed schedule differs from the drawn outline",
                      readings={"SCHEDULE": rs, "DRAWN": rd})


def parapet_rc_bounds(cfg, runs: Iterable[Mapping[str, float]], *, upstand_min: str,
                      material_item: str) -> RuleResult:
    """R-PARAPET-RC-FLOOR-1: runs carry top_lo_m2 / top_hi_m2 (drawn centreline x thickness) and h_hi_m (printed)."""
    rule = "R-PARAPET-RC-FLOOR-1"
    runs = list(runs)
    if not runs:
        raise ValueError("a parapet line needs at least one run")
    up, why = _level(cfg, upstand_min)
    hi = 0.0
    lo_area = 0.0
    for r in runs:
        tl, th, h = r["top_lo_m2"], r["top_hi_m2"], r["h_hi_m"]
        for x, w in ((tl, "top_lo_m2"), (th, "top_hi_m2"), (h, "h_hi_m")):
            _finite_positive(x, w)
        if tl > th:
            raise ValueError("top_lo_m2 above top_hi_m2")
        lo_area += tl
        hi += th * h
    if up is None:
        return RuleResult(rule, HELD, None, low=None, high=round(hi, 6), facts_used=(upstand_min,),
                          formula="no printed upstand minimum: lower bound open", held_reason=why)
    return RuleResult(rule, HELD, None, low=round(lo_area * up, 6), high=round(hi, 6), facts_used=(upstand_min,),
                      formula=f"low {lo_area:.6f} m2 x upstand {up:.2f}; high sum(top x printed h)",
                      held_reason=material_item)


def ground_beam_split_run(width_m: float, span_lo_m: float, span_hi_m: float, printed_depths_m: Sequence[float],
                          loaded: bool, held_depths_m: Sequence[float] | None = None, *,
                          tol_m: float = 0.0005) -> RuleResult:
    """R-GB-NECK-CUT-1, one run of a band split at a FOUNDED neck (the neck owns its own length).

    VALUED only when nothing lands on the run (no concentrated load), one section is printed for it and every frame
    reads the same span: width x printed depth x span. Otherwise HELD with the range width x depth_lo x span_lo ..
    width x depth_hi x span_hi beside (a loaded run: printed unloaded title .. the depth it may need), never 0."""
    rule = "R-GB-NECK-CUT-1"
    b = _finite_positive(width_m, "width")
    lo, hi = _finite_positive(span_lo_m, "span low"), _finite_positive(span_hi_m, "span high")
    if lo > hi + tol_m:
        raise ValueError("span low above span high")
    pd = [_finite_positive(x, "printed depth") for x in printed_depths_m]
    if not pd:
        return RuleResult(rule, HELD, None, formula="no printed section for the run",
                          held_reason="section not printed: blank, never 0")
    if not loaded and len(pd) == 1 and hi - lo <= tol_m:
        v = b * pd[0] * lo
        return RuleResult(rule, VALUED, round(v, 6), formula=f"{b} x {pd[0]} x {lo} = {v:.6f} m3 (unloaded run)")
    hd = [_finite_positive(x, "held depth") for x in (held_depths_m or pd)]
    dlo, dhi = min(hd), max(hd)
    return RuleResult(rule, HELD, None, low=round(b * dlo * lo, 6), high=round(b * dhi * hi, 6),
                      formula=f"{b} x {dlo} .. {dhi} x {lo} .. {hi}",
                      held_reason="a beam lands on the run (concentrated load: section not printed)" if loaded
                      else "the printed section or the span is a range of readings: a picked end is not a value")


def split_conserves_band(band_length_m: float, run_lengths_m: Iterable[float], neck_lengths_m: Iterable[float], *,
                         tol_m: float = 0.0005) -> bool:
    """R-GB-NECK-CUT-1 (b): runs + founded necks = the band, no length lost and none borrowed."""
    runs, necks = list(run_lengths_m), list(neck_lengths_m)
    return abs(sum(runs) + sum(necks) - band_length_m) <= tol_m * (len(runs) + len(necks))
