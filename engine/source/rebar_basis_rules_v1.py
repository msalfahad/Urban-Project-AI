"""REBAR_BASIS_RULES_V1: drawing-derived reinforcement basis rules (A1 class A, T-449 round 2 = reinforcement).

Owner follow-up directive 2026-11-02 (MISSION.md, A1): a project-specific correction is (A) a drawing-derived rule,
(B) a declared project fact (the per-project config, schema URBAN_PROJECT_CONFIG_V1) or (C) an unexplained patch. The
reinforcement lines of the candidate come from Checker-merged hand ledgers (V3.0.3 / V3.0.5 inputs), are re-stated by
V3.0.24 (REBAR_FORMULA: count x length x kg/m = net) and re-based by V3.0.27 (suspended-slab bar ends and top bars by
support class). This module states the GENERAL rules behind those inputs, so a villa's reinforcement lines follow from
its drawing readings plus its declared facts and no per-line value:

  R-REBAR-POPULATION-1     a bar population = count x length x unit mass of its diameter (kg); the count must come
                           from a printed schedule row / detail of its own, the length is the drawn / derived length;
                           unit mass by the project's DECLARED method (REBAR.UNIT_MASS.METHOD). A missing count,
                           length, diameter, schedule row or method keeps the population HELD, never 0. Lengths are
                           metres; a length declared in mm is converted once; a metre value above 50 (an mm figure
                           read as m) or an mm value below 50 (a m figure read as mm) is refused.
  R-REBAR-READINGS-RANGE-1 a held population printed with several defensible count / length readings (owner Q-71: no
                           universal N = n x L + 1) is a HELD range min .. max over its readings; an information-only
                           reading (C_info) is shown, never a range end; no reading -> HELD with no range.
  R-REBAR-DEV-RANGE-1      a bar-end development taken from a note printed as 'k1 d .. k2 d' (training villa p.8 note 9:
                           40 d compression .. 70 d tension, zone not printed) is a HELD range n x k d x unit mass;
                           never a released quantity (owner 2026-10-24 s.4 / s.6: the note governs only the bar groups
                           it names; 'at least 70 d' is a minimum).
  R-REBAR-CANDIDATE-RANGE-1 a member held over several printed candidates (schedule marks, p.13-type section details)
                           is a HELD range: min of the candidates' lows .. max of their highs; a candidate with no
                           defined figure keeps it HELD with no range.
  R-SLAB-BAR-END-1         suspended-slab BOTTOM bar ends by support class (typical slab-on-beams detail): CONTINUOUS
                           -> no development (0 m with evidence, NOT_APPLICABLE); EDGE_BEAM -> straight part = drawn
                           support width - the printed end clear cover (DECLARED REBAR.SLAB.BAR_END.CLEAR_COVER), the
                           up-turn leg HELD; STEP_EDGE / OPENING_EDGE / IRREGULAR_SUPPORT -> HELD. A line's valued
                           part = min .. max over its count readings of (sum of straight parts) x unit mass.
  R-SLAB-TOP-EXTENT-1      suspended-slab TOP bars over supports by support class: CONTINUOUS -> in-panel extent =
                           declared factor x max(L_this, L_other) from the face + half the drawn band (an unknown
                           L_other leaves the side HELD, never the own span substituted); EDGE_BEAM -> declared end
                           factor x L_this + the part across the beam BOUND [w - cover, w]; held classes HELD. The two
                           extents of one bar segment never exceed its clear span: past it, a BOUND [ln, min(a, ln) +
                           min(b, ln)] (one through bar .. two overlapping bars). The bar size is the DECLARED size of
                           the support top bars (REBAR.SLAB.TOP.BAR_DIA, the plan note), never the panel's mesh label.
                           A panel printed with a full top mesh (T&B) is UNRESOLVED (no value).
  R-REBAR-UNIT-T-1         kg internal at full precision, t = kg / 1000 once at the BOQ boundary (owner 2026-10-24
                           s.1, declared REBAR.BOQ_UNIT); sums per state only, never across states.

Every result is a RuleResult: state VALUED / BOUND / BOUND_PART_WITH_HELD / HELD / NOT_APPLICABLE / UNRESOLVED, value
only when VALUED, a range kept beside a bound or held line, the formula and the facts used. Missing never becomes 0.
Standard library only, no engine import: the facts arrive as a config object that offers lookup(fact_id) (the
URBAN_PROJECT_CONFIG_V1 loader's interface; any object with it works). Wired into no candidate method yet (an unwired
producer: the candidate wiring is a new V3.0.x version under Checker Gate B). Lap splices (owner 40 d / 60 d
convention, stock length) and Q-71 link counting are NOT rules of this version: no candidate line of the training
villa uses them (no bar run over the 12 m stock; links are held over their readings); the lap-count formula is
T-459's.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable, Mapping, Sequence

DEFAULT_GUARD_CLASS = "UNWIRED_PRODUCER"  # T-212: computes reinforcement kg, wired nowhere (guard at integration)
RULE_VERSION = "REBAR_BASIS_RULES_V1"

HELD = "HELD"
VALUED = "VALUED"
NOT_APPLICABLE = "NOT_APPLICABLE"
UNRESOLVED = "UNRESOLVED"
BOUND_PART_WITH_HELD = "BOUND_PART_WITH_HELD"
BOUND = "BOUND"                # a valued range over the count readings with nothing held (never one figure)

F_UNIT_MASS = "REBAR.UNIT_MASS.METHOD"
F_BOQ_UNIT = "REBAR.BOQ_UNIT"
F_END_COVER = "REBAR.SLAB.BAR_END.CLEAR_COVER"
F_TOP_CONT = "REBAR.SLAB.TOP.CONT_EXTENT_FACTOR"
F_TOP_END = "REBAR.SLAB.TOP.END_EXTENT_FACTOR"
F_TOP_DIA = "REBAR.SLAB.TOP.BAR_DIA"            # the plan note that sizes the support top bars (not the mesh label)

UNIT_MASS_METHODS = {"D2_OVER_162": 162.0, "D2_OVER_162_16": 162.16}   # kg/m = d^2 / k, d in mm
CONTINUOUS_CLASSES = ("CONTINUOUS", "CONTINUOUS_WIDE_BEAM")
HELD_CLASSES = ("STEP_EDGE", "OPENING_EDGE", "IRREGULAR_SUPPORT", "CANTILEVER_ROOT")
SUPPORT_CLASSES = CONTINUOUS_CLASSES + ("EDGE_BEAM",) + HELD_CLASSES
MAX_M = 50.0             # a metre length above this is an mm figure read as m
MIN_MM = 50.0            # an mm length below this is a metre figure read as mm


@dataclass(frozen=True)
class RuleResult:
    rule: str
    state: str                        # VALUED / BOUND / BOUND_PART_WITH_HELD / HELD / NOT_APPLICABLE / UNRESOLVED
    value: float | None               # kg only when VALUED
    low: float | None = None          # range beside a held / bound line (never summed into the BOQ as a value)
    high: float | None = None
    formula: str = ""
    facts_used: tuple[str, ...] = ()
    held_reason: str | None = None
    readings: Mapping[str, float] = field(default_factory=dict)


def _num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _fact(cfg, fact_id):
    """(fact, None) when usable, else (None, reason)."""
    lk = cfg.lookup(fact_id)
    if not lk.usable:
        return None, f"{fact_id} HELD: {lk.reason}"
    return lk.fact, None


def length_m(value, unit: str = "m") -> float:
    """one length to metres, refusing a unit mix-up (R-REBAR-POPULATION-1)."""
    if not _num(value) or value < 0:
        raise ValueError(f"length must be a finite non-negative number, got {value!r}")
    if unit == "m":
        if value > MAX_M:
            raise ValueError(f"UNIT_REFUSED: {value} m reads as an mm figure (bar lengths over {MAX_M:g} m)")
        return float(value)
    if unit == "mm":
        if 0 < value < MIN_MM:
            raise ValueError(f"UNIT_REFUSED: {value} mm reads as a metre figure")
        return float(value) / 1000.0
    raise ValueError(f"UNIT_REFUSED: length unit {unit!r} (m or mm)")


def unit_mass(cfg, d_mm) -> tuple[float | None, str | None]:
    """kg/m of one diameter by the DECLARED method. (value, None) or (None, held reason)."""
    if not _num(d_mm) or d_mm <= 0:
        return None, "bar diameter not printed"
    if d_mm < 4 or d_mm > 60:
        raise ValueError(f"UNIT_REFUSED: bar diameter {d_mm} is not a mm diameter (4 .. 60)")
    f, why = _fact(cfg, F_UNIT_MASS)
    if f is None:
        return None, why
    k = UNIT_MASS_METHODS.get(f.value)
    if k is None:
        return None, f"{F_UNIT_MASS} = {f.value!r} is not a method of {RULE_VERSION}"
    return d_mm * d_mm / k, None


def bar_population(cfg, *, count, length, d_mm, length_unit: str = "m", schedule_row: str | None = "PRINTED"
                   ) -> RuleResult:
    """R-REBAR-POPULATION-1: one bar population (one schedule row / component)."""
    rule = "R-REBAR-POPULATION-1"
    used = (F_UNIT_MASS,)
    if schedule_row != "PRINTED":
        return RuleResult(rule, HELD, None, formula="count not from a printed schedule row of its own",
                          facts_used=used, held_reason=f"schedule row {schedule_row!r}: never released")
    missing = [n for n, v in (("count", count), ("length", length), ("diameter", d_mm)) if v is None]
    if missing:
        return RuleResult(rule, HELD, None, formula="incomplete population", facts_used=used,
                          held_reason="not printed: " + ", ".join(missing))
    if not _num(count) or count < 0 or abs(count - round(count)) > 1e-9:
        raise ValueError(f"a bar count must be a whole non-negative number, got {count!r}")
    L = length_m(length, length_unit)
    u, why = unit_mass(cfg, d_mm)
    if u is None:
        return RuleResult(rule, HELD, None, formula="unit mass not declared", facts_used=used, held_reason=why)
    kg = count * L * u
    return RuleResult(rule, VALUED, kg, formula=f"{count:g} x {L:.4f} m x {u:.6f} kg/m (d{d_mm:g}) = {kg:.6f} kg",
                      facts_used=used)


def readings_range(readings: Mapping[str, float] | None, *, info_prefixes: Sequence[str] = ("C_info",)
                   ) -> RuleResult:
    """R-REBAR-READINGS-RANGE-1: min .. max over the defensible readings (kg); info readings shown, never an end."""
    rule = "R-REBAR-READINGS-RANGE-1"
    rd = {k: float(v) for k, v in (readings or {}).items() if _num(v)}
    ends = {k: v for k, v in rd.items() if not any(k.startswith(p) for p in info_prefixes)}
    if not ends:
        return RuleResult(rule, HELD, None, formula="no reading printed", held_reason="no defensible reading",
                          readings=rd)
    if any(v < 0 for v in ends.values()):
        raise ValueError("a reading is negative")
    return RuleResult(rule, HELD, None, low=min(ends.values()), high=max(ends.values()),
                      formula="min .. max over " + " / ".join(sorted(ends)), held_reason="readings differ (Q-71)",
                      readings=rd)


def development_range(cfg, *, count, d_mm, k_low: float, k_high: float) -> RuleResult:
    """R-REBAR-DEV-RANGE-1: n bar ends x k d (k_low .. k_high printed by the note) x unit mass; HELD range only."""
    rule = "R-REBAR-DEV-RANGE-1"
    if not (_num(k_low) and _num(k_high) and 0 < k_low <= k_high):
        raise ValueError("the note's multiples must satisfy 0 < k_low <= k_high")
    if count is None or d_mm is None:
        return RuleResult(rule, HELD, None, formula="bar-end count or diameter not on the record",
                          facts_used=(F_UNIT_MASS,), held_reason="range needs the count and the diameter")
    u, why = unit_mass(cfg, d_mm)
    if u is None:
        return RuleResult(rule, HELD, None, facts_used=(F_UNIT_MASS,), held_reason=why)
    lo = count * k_low * d_mm / 1000.0 * u
    hi = count * k_high * d_mm / 1000.0 * u
    return RuleResult(rule, HELD, None, low=lo, high=hi, facts_used=(F_UNIT_MASS,),
                      formula=f"{count:g} x {k_low:g} d .. {k_high:g} d x {u:.6f} kg/m (d{d_mm:g})",
                      held_reason="zone (tension / compression) not printed: a note range, never released")


def development_range_groups(cfg, groups: Sequence[tuple[float, float]], *, ends: int, k_low: float, k_high: float
                             ) -> RuleResult:
    """R-REBAR-DEV-RANGE-1 for a member whose bars are several printed groups (n, d): ends x sum(n x k d x unit
    mass(d)), k_low .. k_high; HELD range only."""
    if not groups or not _num(ends) or ends <= 0:
        return RuleResult("R-REBAR-DEV-RANGE-1", HELD, None, facts_used=(F_UNIT_MASS,),
                          held_reason="bar groups or the number of bar ends not printed")
    lo = hi = 0.0
    for n, d in groups:
        r = development_range(cfg, count=ends * n, d_mm=d, k_low=k_low, k_high=k_high)
        if r.low is None:
            return r
        lo, hi = lo + r.low, hi + r.high
    return RuleResult("R-REBAR-DEV-RANGE-1", HELD, None, low=lo, high=hi, facts_used=(F_UNIT_MASS,),
                      formula=f"{ends} ends x " + " + ".join(f"{n:g} d{d:g}" for n, d in groups)
                              + f" x {k_low:g} d .. {k_high:g} d", held_reason="zone not printed: a note range")


def candidates_range(ranges: Mapping[str, tuple[float | None, float | None] | None]) -> RuleResult:
    """R-REBAR-CANDIDATE-RANGE-1: a member held over several printed candidates (schedule marks, section details):
    min of the candidates' lows .. max of their highs; a candidate with no figure keeps the member HELD with no
    range (never treated as 0 unless the candidate itself prints no such component)."""
    rule = "R-REBAR-CANDIDATE-RANGE-1"
    if not ranges:
        return RuleResult(rule, HELD, None, held_reason="no candidate")
    if any(v is None or v[0] is None or v[1] is None for v in ranges.values()):
        return RuleResult(rule, HELD, None, held_reason="a candidate has no defined figure (no project detail)")
    lo = min(v[0] for v in ranges.values())
    hi = max(v[1] for v in ranges.values())
    return RuleResult(rule, HELD, None, low=lo, high=hi, formula="min .. max over candidates " + " / ".join(
        sorted(ranges)), held_reason="the governing candidate is a designer item")


# ------------------------------------------------------------------------------------------------ slabs
@dataclass(frozen=True)
class BarEnd:
    """one end of one bar segment of a slab line, read from the drawing (lengths in m)."""

    reading: str                   # count reading 'A' / 'B'
    support: str                   # SUPPORT_CLASSES
    width_m: float | None = None   # drawn band width along the bar
    seg_len_m: float | None = None # clear span of the segment (top bars)
    other_span_m: float | None = None  # clear span of the panel beyond a continuous support (top bars)
    bar: int = 0
    segment: int = 0
    end: str = "lo"                # 'lo' / 'hi'


def _cls(support):
    if support not in SUPPORT_CLASSES:
        raise ValueError(f"SUPPORT_CLASS_REFUSED: {support!r}")
    return support


def slab_bottom_end(cfg, end: BarEnd) -> tuple[float | None, str | None]:
    """R-SLAB-BAR-END-1 for one bottom-bar end -> (straight length m or None, held reason or None). 0.0 at a
    continuous support is a measured 0 with evidence (no development drawn), not a missing value."""
    s = _cls(end.support)
    if s in CONTINUOUS_CLASSES:
        return 0.0, None
    if s in HELD_CLASSES:
        return None, f"{s}: no drawn bar end"
    f, why = _fact(cfg, F_END_COVER)
    if f is None:
        return None, why
    cover = f.base_value()
    if end.width_m is None:
        return None, "EDGE_BEAM end without its drawn width"
    w = length_m(end.width_m)
    if w <= cover:
        raise ValueError(f"EDGE_BEAM width {w} m not wider than the end cover {cover} m")
    return w - cover, None


def slab_development_line(cfg, ends: Iterable[BarEnd], d_mm) -> RuleResult:
    """R-SLAB-BAR-END-1 for one slab development line (bottom layer): NOT_APPLICABLE when every end is continuous;
    BOUND_PART_WITH_HELD (valued straight parts, up-turn legs / held ends HELD) when an edge beam is present; else
    HELD. low / high = min / max over the count readings of sum(straight) x unit mass."""
    rule = "R-SLAB-BAR-END-1"
    ends = list(ends)
    if not ends:
        raise ValueError("a development line needs its bar ends")
    classes = {_cls(e.support) for e in ends}
    used = (F_END_COVER, F_UNIT_MASS)
    if classes <= set(CONTINUOUS_CLASSES):
        return RuleResult(rule, NOT_APPLICABLE, None, formula="every bar end continuous: no development drawn",
                          facts_used=())
    if "EDGE_BEAM" not in classes:
        return RuleResult(rule, HELD, None, formula="no edge-beam end", facts_used=(),
                          held_reason="ends " + ",".join(sorted(classes & set(HELD_CLASSES))) + " not drawn")
    u, why = unit_mass(cfg, d_mm)
    if u is None:
        return RuleResult(rule, HELD, None, facts_used=used, held_reason=why)
    ext = {}
    for e in ends:
        if e.support != "EDGE_BEAM":
            ext.setdefault(e.reading, 0.0)
            continue
        s, why = slab_bottom_end(cfg, e)
        if s is None:
            return RuleResult(rule, HELD, None, facts_used=used, held_reason=why)
        ext[e.reading] = ext.get(e.reading, 0.0) + s
    kg = {k: v * u for k, v in ext.items()}
    return RuleResult(rule, BOUND_PART_WITH_HELD, None, low=min(kg.values()), high=max(kg.values()), facts_used=used,
                      formula="straight parts (w - cover) at edge-beam ends x unit mass, min .. max over readings "
                              + " / ".join(f"{k} {ext[k]:.4f} m" for k in sorted(ext)),
                      held_reason="up-turn legs and non-edge held ends", readings={k: kg[k] for k in sorted(kg)})


def slab_top_end(cfg, end: BarEnd) -> dict:
    """R-SLAB-TOP-EXTENT-1 for one top-bar end -> {status, in_panel, over_band, across (lo, hi), held}."""
    s = _cls(end.support)
    if s in HELD_CLASSES:
        return dict(status=HELD, in_panel=None, over_band=0.0, across=(0.0, 0.0), held=s)
    L = length_m(end.seg_len_m) if end.seg_len_m is not None else None
    if L is None:
        return dict(status=HELD, in_panel=None, over_band=0.0, across=(0.0, 0.0), held="clear span not drawn")
    if s in CONTINUOUS_CLASSES:
        f, why = _fact(cfg, F_TOP_CONT)
        if f is None:
            return dict(status=HELD, in_panel=None, over_band=0.0, across=(0.0, 0.0), held=why)
        if end.width_m is None:
            raise ValueError("continuous end without its drawn band width")
        if end.other_span_m is None:
            return dict(status=HELD, in_panel=None, over_band=length_m(end.width_m) / 2.0, across=(0.0, 0.0),
                        held="OTHER_SPAN_UNKNOWN")
        return dict(status=VALUED, in_panel=f.base_value() * max(L, length_m(end.other_span_m)),
                    over_band=length_m(end.width_m) / 2.0, across=(0.0, 0.0), held=None)
    fe, why = _fact(cfg, F_TOP_END)
    fc, why2 = _fact(cfg, F_END_COVER)
    if fe is None or fc is None:
        return dict(status=HELD, in_panel=None, over_band=0.0, across=(0.0, 0.0), held=why or why2)
    cover = fc.base_value()
    if end.width_m is None or end.width_m <= cover:
        raise ValueError("EDGE_BEAM end without a drawn width wider than the end cover")
    w = length_m(end.width_m)
    return dict(status=VALUED, in_panel=fe.base_value() * L, over_band=0.0, across=(w - cover, w),
                held="HOOK_DOWN_LEG")


def _overlap(ln, a, b):
    """one bar segment's two in-panel extents never exceed its clear span -> (cut_low, cut_high) m."""
    if a is not None and b is not None:
        s = a + b
        if s <= ln + 1e-9:
            return 0.0, 0.0
        return s - ln, s - (min(a, ln) + min(b, ln))
    v = a if a is not None else b
    if v is None or v <= ln + 1e-9:
        return 0.0, 0.0
    return v - ln, v - ln


def slab_top_line(cfg, ends: Iterable[BarEnd], *, full_top_mesh: bool = False) -> RuleResult:
    """R-SLAB-TOP-EXTENT-1 for one top-bar line: valued part min .. max over readings; HELD when no end is valued.
    The bar diameter is the DECLARED size of the support top bars (the plan note), never the panel's mesh label."""
    rule = "R-SLAB-TOP-EXTENT-1"
    ends = list(ends)
    used = (F_TOP_CONT, F_TOP_END, F_END_COVER, F_TOP_DIA, F_UNIT_MASS)
    if full_top_mesh:
        return RuleResult(rule, UNRESOLVED, None, formula="(T&B) panel: full top mesh printed",
                          held_reason="whether the support top bars add to the printed top mesh (designer item)")
    fd, why = _fact(cfg, F_TOP_DIA)
    if fd is None:
        return RuleResult(rule, HELD, None, facts_used=used, held_reason=why)
    d_mm = fd.base_value() * 1000.0
    u, why = unit_mass(cfg, d_mm)
    if u is None:
        return RuleResult(rule, HELD, None, facts_used=used, held_reason=why)
    lo, hi, n_held, n_val, legs = {}, {}, {}, {}, {}
    seg = {}
    for e in ends:
        r = slab_top_end(cfg, e)
        lo.setdefault(e.reading, 0.0)
        hi.setdefault(e.reading, 0.0)
        if r["held"] == "HOOK_DOWN_LEG":
            legs[e.reading] = legs.get(e.reading, 0) + 1
        if r["in_panel"] is None:
            if r["status"] == HELD:
                n_held[e.reading] = n_held.get(e.reading, 0) + 1
            seg.setdefault((e.reading, e.bar, e.segment), {"ln": e.seg_len_m})
            continue
        n_val[e.reading] = n_val.get(e.reading, 0) + 1
        lo[e.reading] += r["in_panel"] + r["over_band"] + r["across"][0]
        hi[e.reading] += r["in_panel"] + r["over_band"] + r["across"][1]
        d = seg.setdefault((e.reading, e.bar, e.segment), {"ln": e.seg_len_m})
        if e.end in d:
            raise ValueError(f"bar end booked twice: {e}")
        d[e.end] = r["in_panel"]
    for (tag, _, _), d in seg.items():
        cl, ch = _overlap(length_m(d["ln"]), d.get("lo"), d.get("hi"))
        lo[tag] -= cl
        hi[tag] -= ch
    if not n_val:
        return RuleResult(rule, HELD, None, facts_used=used, held_reason="no top-bar end valued by the detail")
    vlo = min(v * u for v in lo.values())
    vhi = max(v * u for v in hi.values())
    held = []
    if n_held:
        held.append("held ends " + ", ".join(f"{k} {v}" for k, v in sorted(n_held.items())))
    if legs:
        held.append("hook-down legs at edge beams (drawn, not dimensioned) " + ", ".join(
            f"{k} {v}" for k, v in sorted(legs.items())))
    return RuleResult(rule, BOUND_PART_WITH_HELD if held else BOUND, None, low=vlo, high=vhi, facts_used=used,
                      formula="extent by support class x unit mass, segments capped at their clear span; min .. max "
                              "over readings", held_reason="; ".join(held) or None)


def to_tonnes(cfg, kg_values: Iterable[float]) -> RuleResult:
    """R-REBAR-UNIT-T-1: sum kg unrounded, convert once to the declared BOQ unit."""
    rule = "R-REBAR-UNIT-T-1"
    vals = list(kg_values)
    if any(not _num(v) for v in vals):
        raise ValueError("a held (None) or non-numeric kg cannot enter a released sum")
    f, why = _fact(cfg, F_BOQ_UNIT)
    if f is None:
        return RuleResult(rule, HELD, None, facts_used=(F_BOQ_UNIT,), held_reason=why)
    kg = math.fsum(vals)
    if f.value == "t":
        return RuleResult(rule, VALUED, kg / 1000.0, formula=f"{kg:.6f} kg / 1000 = {kg / 1000.0:.6f} t",
                          facts_used=(F_BOQ_UNIT,))
    if f.value == "kg":
        return RuleResult(rule, VALUED, kg, formula=f"{kg:.6f} kg", facts_used=(F_BOQ_UNIT,))
    return RuleResult(rule, HELD, None, facts_used=(F_BOQ_UNIT,), held_reason=f"BOQ unit {f.value!r} unknown")
