"""T-560 B11 REINFORCEMENT TONNAGE RECONCILIATION rules (REBAR_TONNAGE_RECONCILE_V1; R-T560-1 .. 5; every villa;
research, unwired).

Physical element (ERS s.2.1): each bar group of each structural element (main bars, links, side bars, starters, laps
where a drawing note governs, bar ends), mass = developed length x unit mass, kg internally; metric tons only at the
reporting boundary (OWNER_RULE_REBAR_2026-10-24 s.1). Installed (net) mass and procurement mass (waste, stock-length
offcuts, laps for transport length) are separate accounts and never compared with each other.

R-T560-1  BENCHMARK BASIS. A benchmark tonnage is classified by what the benchmark itself prints:
            COUNTED     bar rows exist (diameter, count or spacing, length, kg) for the element family;
            RATIO       a formula of the family's concrete volume x a printed rate (kg/m3 or t/m3);
            TYPED_LUMP  a typed constant with no bar row and no formula (the basis is NOT PRINTED).
          Only COUNTED vs COUNTED is a like-for-like comparison. RATIO or TYPED_LUMP against counted bars is
          RULE_DIFF: never AGREE, never an accuracy percentage; the difference is a signed gap split into causes.
          A rate that merely reproduces a typed value after rounding is reported as an interval observation, never
          adopted as his method (no assumption).
R-T560-2  UNITS. kg internally; t = kg / 1000 once, 6 dp, at the reporting boundary. Every benchmark value carries the
          unit its own header prints; a value whose row says kg presented as t is refused; a family value whose
          implied mass per m3 of that family's own concrete exceeds the density of steel (7,850 kg/m3) is a unit
          error and is refused (it cannot be physical).
R-T560-3  ENGINE SIDE. Per engine family the candidate lines are kept in four parts: VALUED (sum of measured_net),
          HELD_RANGE (sum of held_low .. sum of held_high), HELD_BLANK (count of held lines with no bound; never 0),
          EXCLUDED (count; superseded rows carry nothing). A held range is never added into the valued figure; the
          family table re-adds exactly (6 dp) to the candidate totals in every part.
R-T560-4  SCOPE GROUPS. A benchmark family is mapped by its own printed scope (its sheet rows), an engine family by its
          element ids. When the two splits cross (one element class in different families on the two sides), the
          comparison is made on the SMALLEST COMMON GROUP that contains both; a benchmark lump is never split by an
          invented proportion. Every engine family and every benchmark family belongs to exactly one group.
R-T560-5  CAUSES. Per group: gap_valued = his - engine VALUED; the bounded held part [low, high] explains at most
          that much; the remainder his - VALUED - [high .. low] is carried by (a) HELD_BLANK groups (unbounded, named),
          (b) SCOPE items in one list only (named), (c) the benchmark method (RULE_DIFF: his basis not printed), (d)
          laps / waste only where the benchmark or a drawing note prints them, otherwise UNKNOWN. The remainder is a
          NAMED residual, never attributed to a single cause without evidence and never a percentage.
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

Q6 = Decimal("0.000001")
STEEL_DENSITY_KG_M3 = Decimal("7850")
BASES = ("COUNTED", "RATIO", "TYPED_LUMP")
UNITS = ("kg", "t")


def d6(x) -> Decimal:
    if x is None:
        raise ValueError("missing value: a held or absent quantity is never 0")
    if isinstance(x, float):
        x = repr(x)
    return Decimal(str(x)).quantize(Q6, rounding=ROUND_HALF_UP)


# ---- R-T560-2 units ----------------------------------------------------------------------------------------------
def to_t(value, unit: str) -> Decimal:
    """Reporting boundary: kg -> t once; t stays t. Anything else is refused."""
    if unit not in UNITS:
        raise ValueError(f"unit {unit!r} is not a reinforcement mass unit (kg or t)")
    v = Decimal(str(value)) if not isinstance(value, Decimal) else value
    return d6(v / Decimal(1000)) if unit == "kg" else d6(v)


def bench_value(value, header_unit: str, row_unit: str | None = None) -> Decimal:
    """A benchmark cell in t: its header unit governs; a row that says kg cannot be read as t (relabelling refused)."""
    if header_unit not in UNITS:
        raise ValueError(f"benchmark header unit {header_unit!r} not printed as kg or t")
    if row_unit is not None and row_unit != header_unit:
        raise ValueError(f"unit relabelled: row prints {row_unit}, header prints {header_unit}")
    return to_t(value, header_unit)


def plausible_t(t_value: Decimal, concrete_m3) -> Decimal:
    """Implied kg per m3 of the family's own concrete; above the steel density it is a unit error, not a quantity."""
    m3 = Decimal(str(concrete_m3))
    if m3 <= 0:
        raise ValueError("no concrete volume: plausibility cannot be checked")
    kg_m3 = Decimal(t_value) * 1000 / m3
    if kg_m3 > STEEL_DENSITY_KG_M3:
        raise ValueError(f"unit error: {kg_m3:.1f} kg per m3 of concrete exceeds the density of steel")
    return kg_m3.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def rate_interval(t_value, concrete_m3, dp: int = 2):
    """Every rate r (kg/m3) with round(V x r / 1000, dp) == t_value: [lo, hi). An observation, never his method."""
    half = Decimal(1).scaleb(-dp) / 2
    v = Decimal(str(concrete_m3))
    t = Decimal(str(t_value))
    return ((t - half) * 1000 / v).quantize(Decimal("0.01")), ((t + half) * 1000 / v).quantize(Decimal("0.01"))


# ---- R-T560-1 basis ----------------------------------------------------------------------------------------------
def classify_basis(has_bar_rows: bool, formula: str | None) -> str:
    if has_bar_rows:
        return "COUNTED"
    if formula:
        return "RATIO"
    return "TYPED_LUMP"


def comparison_class(bench_basis: str, engine_basis: str = "COUNTED") -> str:
    if bench_basis not in BASES or engine_basis not in BASES:
        raise ValueError("unknown basis")
    return "LIKE_FOR_LIKE" if bench_basis == engine_basis == "COUNTED" else "RULE_DIFF"


def refuse_agreement(cls: str, verdict: str):
    if cls == "RULE_DIFF" and verdict in ("AGREE", "AGREEMENT", "MATCH"):
        raise ValueError("a ratio / typed lump against counted bars is never 'agreement'")
    return verdict


# ---- R-T560-3 engine parts -----------------------------------------------------------------------------------------
def engine_parts(lines):
    """lines: dicts with class (RELEASED|HELD|EXCLUDED), measured_net, held_low, held_high, unit kg."""
    val = Decimal(0)
    lo = Decimal(0)
    hi = Decimal(0)
    blank = 0
    excl = 0
    n_val = n_rng = 0
    for ln in lines:
        if ln.get("unit") != "kg":
            raise ValueError(f"engine rebar line in {ln.get('unit')!r}: kg internally only")
        c = ln["class"]
        if c == "RELEASED":
            if ln.get("measured_net") is None:
                raise ValueError("valued line with no quantity")
            val += Decimal(str(ln["measured_net"]))
            n_val += 1
        elif c == "HELD":
            if ln.get("measured_net") is not None:
                raise ValueError("held line carries a valued quantity: held never enters the valued sum")
            if ln.get("held_low") is None and ln.get("held_high") is None:
                blank += 1
            else:
                if ln.get("held_low") is None or ln.get("held_high") is None:
                    raise ValueError("half-open held range: both bounds or none")
                a, b = Decimal(str(ln["held_low"])), Decimal(str(ln["held_high"]))
                if a > b:
                    raise ValueError("held range low above high")
                lo += a
                hi += b
                n_rng += 1
        elif c == "EXCLUDED":
            if ln.get("measured_net") not in (None,) or ln.get("held_low") is not None:
                raise ValueError("an excluded row carries a quantity")
            excl += 1
        else:
            raise ValueError(f"unknown line class {c!r}")
    return {"valued_kg": d6(val) if n_val else None, "n_valued": n_val,
            "held_low_kg": d6(lo) if n_rng else None, "held_high_kg": d6(hi) if n_rng else None, "n_range": n_rng,
            "held_blank": blank, "excluded": excl}


def add_parts(parts):
    """Re-add family parts exactly; an absent part stays None (never 0)."""
    out = {"valued_kg": None, "held_low_kg": None, "held_high_kg": None, "n_valued": 0, "n_range": 0,
           "held_blank": 0, "excluded": 0}
    for p in parts:
        for k in ("valued_kg", "held_low_kg", "held_high_kg"):
            if p[k] is not None:
                out[k] = d6((out[k] or Decimal(0)) + p[k])
        for k in ("n_valued", "n_range", "held_blank", "excluded"):
            out[k] += p[k]
    return out


# ---- R-T560-4 groups -----------------------------------------------------------------------------------------------
def check_groups(groups: dict, engine_families, bench_families):
    """groups: {gid: {"engine": [...], "bench": [...]}}; every family in exactly one group."""
    seen_e, seen_b = {}, {}
    for gid, g in groups.items():
        for f in g["engine"]:
            if f in seen_e:
                raise ValueError(f"engine family {f} in two groups ({seen_e[f]}, {gid})")
            seen_e[f] = gid
        for f in g["bench"]:
            if f in seen_b:
                raise ValueError(f"benchmark family {f} in two groups ({seen_b[f]}, {gid})")
            seen_b[f] = gid
    miss_e = sorted(set(engine_families) - set(seen_e))
    miss_b = sorted(set(bench_families) - set(seen_b))
    if miss_e or miss_b:
        raise ValueError(f"family in no group: engine {miss_e}, benchmark {miss_b}")
    return True


# ---- R-T560-5 causes -----------------------------------------------------------------------------------------------
def causes(his_t, eng: dict, bench_basis: str, scope_items=(), blank_groups=()):
    """Signed cause split in t for one group. his_t None = the benchmark has no family for this group (NO_ROW)."""
    val_t = to_t(eng["valued_kg"], "kg") if eng["valued_kg"] is not None else None
    lo_t = to_t(eng["held_low_kg"], "kg") if eng["held_low_kg"] is not None else None
    hi_t = to_t(eng["held_high_kg"], "kg") if eng["held_high_kg"] is not None else None
    v = val_t if val_t is not None else Decimal(0)        # an absent valued part adds nothing; it is reported None
    out = {"his_t": his_t, "engine_valued_t": val_t, "engine_held_low_t": lo_t, "engine_held_high_t": hi_t,
           "engine_held_blank_lines": eng["held_blank"], "scope_items": list(scope_items),
           "blank_groups": list(blank_groups)}
    if his_t is None:
        out.update(cls="NO_ROW", gap_valued_t=None, residual_low_t=None, residual_high_t=None, percent=None)
        return out
    cls = comparison_class(bench_basis)
    gap = d6(his_t - v)
    lo = lo_t if lo_t is not None else Decimal(0)
    hi = hi_t if hi_t is not None else Decimal(0)
    out.update(cls=cls, gap_valued_t=gap, held_bounded_t=(d6(lo), d6(hi)),
               residual_low_t=d6(gap - hi), residual_high_t=d6(gap - lo),
               residual_carried_by=[c for c, on in (("HELD_BLANK", eng["held_blank"] > 0),
                                                     ("SCOPE_ONE_LIST", bool(scope_items)),
                                                     ("METHOD_RULE_DIFF", cls == "RULE_DIFF"),
                                                     ("LAPS_WASTE_UNKNOWN", True)) if on],
               percent=None)
    return out


# ---- hand counting (Q-71: only where the drawing prints spacing, cover and the faces) -------------------------------
def bars_one_way(width_m, cover_m, spacing_m):
    """N = 1 + floor((B - 2c) / s): first and last bar at the cover line, printed spacing between. Not universal
    (Q-71): a drawing that prints another convention (first bar at s/2, a count) governs. Missing input -> HELD."""
    for name, x in (("width", width_m), ("cover", cover_m), ("spacing", spacing_m)):
        if x is None:
            return None, f"HELD: {name} not printed"
        if Decimal(str(x)) > 50:
            raise ValueError(f"{name} {x}: millimetres given where metres are required")
    b, c, s = (Decimal(str(x)) for x in (width_m, cover_m, spacing_m))
    if s <= 0 or b - 2 * c <= 0:
        raise ValueError("non-physical spacing or cover")
    return 1 + int((b - 2 * c) // s), "COUNTED"


def mat_mass_kg(bx, by, cover, s_x, s_y, kg_per_m):
    """Bottom mat of a pad: bars parallel to x are counted across by, length bx - 2c; and vice versa. Hooks / bends
    not included (a drawing detail adds them as its own group)."""
    nx, st1 = bars_one_way(by, cover, s_x)
    ny, st2 = bars_one_way(bx, cover, s_y)
    if nx is None or ny is None:
        return {"status": st1 if nx is None else st2, "kg": None}
    k = Decimal(str(kg_per_m))
    lx = Decimal(str(bx)) - 2 * Decimal(str(cover))
    ly = Decimal(str(by)) - 2 * Decimal(str(cover))
    kg = nx * lx * k + ny * ly * k
    return {"status": "COUNTED", "n_x": nx, "n_y": ny, "len_x": d6(lx), "len_y": d6(ly), "kg": d6(kg)}
