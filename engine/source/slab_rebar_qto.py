"""S7 SLAB REBAR QTO - restricted project-basis slab reinforcement quantities over a frozen readiness register (generic).

A quantity round that never widens its population: only the items a frozen readiness round released as candidates
may carry mass; every other item stays listed, in its own lane, with no kg (not even 0).

Rules
  * Rate density. N bars/m is a density, not a bar count. Over local bar strips (non-overlapping, each with a
    width w and a local run l along the bar):  L_total = N x f x sum(w x l)  (metres), f = density fraction.
    For a rectangle this is N x f x width x run. The equivalent count N x f x W is never rounded, never +1, never
    ceil / floor; PHYSICAL_BBS_COUNT stays UNRESOLVED unless the source gives a count.
  * Unit mass from rebar_unit_mass (D^2 / 162, D in mm). kg = L_total x kg/m. No kg/m2 or kg/m3 factor.
  * Explicit counts ('3Ø16') release mass only when BOTH the count authority and the length authority hold; a
    count whose length is unknown carries no kg.
  * Authority split. A ratio printed in the source (1/3 of the span, 0.125 L, 50 %) is PROJECT_SOURCE; the
    measurement convention that applies it where the source is silent (origin, span basis, local bar line) is a
    separate field with its own authority. The two are never collapsed into one field.
  * Six terminal lanes: SOURCE_DERIVED_PHYSICAL (the source establishes the full physical component),
    PROJECT_BASIS_QTO, PROJECT_BASIS_NUMERIC (a minimum value used as a number, e.g. 25 mm minimum cover),
    BLOCKED_UNQUANTIFIED, EXCLUDED_SPECIAL_STRUCTURE, SOURCE_CONFLICT. Only the first three carry kg.
  * Labels VERIFIED_PHYSICAL / AS_BUILT / SOURCE_EXACT are never produced, and no total is FINAL_SLAB_REBAR: an
    incomplete round reports RESTRICTED_S7_PROJECT_BASIS_KG.
  * Conservation helpers: overlap-free strips, strip coverage of the panel area, density budget per strip,
    duplicate keys (one physical support family quantified once), and level-by-level mass reconciliation.

Stdlib + engine.source.rebar_unit_mass only. No project data.
"""

from __future__ import annotations

import math
from collections import defaultdict

from engine.source import rebar_unit_mass as UM


class SlabRebarQtoError(ValueError):
    pass


TOL = 1e-9

# ------------------------------------------------------------------ lanes
SOURCE_DERIVED_PHYSICAL = "SOURCE_DERIVED_PHYSICAL"
PROJECT_BASIS_QTO = "PROJECT_BASIS_QTO"
PROJECT_BASIS_NUMERIC = "PROJECT_BASIS_NUMERIC"
BLOCKED_UNQUANTIFIED = "BLOCKED_UNQUANTIFIED"
EXCLUDED_SPECIAL_STRUCTURE = "EXCLUDED_SPECIAL_STRUCTURE"
SOURCE_CONFLICT = "SOURCE_CONFLICT"
LANES = (SOURCE_DERIVED_PHYSICAL, PROJECT_BASIS_QTO, PROJECT_BASIS_NUMERIC, BLOCKED_UNQUANTIFIED,
         EXCLUDED_SPECIAL_STRUCTURE, SOURCE_CONFLICT)
MASS_LANES = (SOURCE_DERIVED_PHYSICAL, PROJECT_BASIS_QTO, PROJECT_BASIS_NUMERIC)
NO_MASS_LANES = (BLOCKED_UNQUANTIFIED, EXCLUDED_SPECIAL_STRUCTURE, SOURCE_CONFLICT)
FORBIDDEN_LABELS = ("VERIFIED_PHYSICAL", "AS_BUILT", "SOURCE_EXACT", "FINAL_SLAB_REBAR")
RESTRICTED_TOTAL = "RESTRICTED_S7_PROJECT_BASIS_KG"
ACTUAL_LENGTH_NOT_ESTABLISHED = "ACTUAL_AS_BUILT_LENGTH_NOT_ESTABLISHED"
UNRESOLVED = "UNRESOLVED"

# ------------------------------------------------------------------ authorities
PROJECT_SOURCE = "PROJECT_SOURCE"                       # printed in the project drawings
PROJECT_GEOMETRY = "PROJECT_GEOMETRY"                   # measured face to face on the project geometry
URBAN_OWNER_MEASUREMENT_RULE = "URBAN_OWNER_MEASUREMENT_RULE"   # a declared Urban convention
MINIMUM_PROJECT_COVER = "MINIMUM_PROJECT_COVER"         # a minimum value, never an exact one
AUTHORITY_BLOCKED = "BLOCKED"
AUTHORITIES = (PROJECT_SOURCE, PROJECT_GEOMETRY, URBAN_OWNER_MEASUREMENT_RULE, MINIMUM_PROJECT_COVER,
               AUTHORITY_BLOCKED)

COUNT_RATE_DENSITY = "RATE_DENSITY"
COUNT_SOURCE_EXPLICIT = "SOURCE_EXPLICIT_COUNT"
COUNT_UNRESOLVED = "COUNT_UNRESOLVED"

UNIT_MASS_METHOD = {"method": UM.D2_OVER_162, "authority": "Urban project default (R3): kg/m = D^2 / 162"}


# ------------------------------------------------------------------ quantities
def unit_mass(dia_mm):
    """kg per metre of one bar (D^2 / 162, D in mm), unrounded."""
    if dia_mm is None or float(dia_mm) <= 0:
        raise SlabRebarQtoError(f"diameter must be positive: {dia_mm!r}")
    return UM.kg_per_m(float(dia_mm), UNIT_MASS_METHOD)


def rectangle_length_m(rate_per_m, width_m, run_m, *, fraction=1.0):
    """Equivalent bar length of a rate over a rectangle: N x f x width x run (m). Never rounded."""
    _check_rate(rate_per_m, fraction)
    if width_m < 0 or run_m < 0:
        raise SlabRebarQtoError("width and run must be non-negative")
    return float(rate_per_m) * float(fraction) * float(width_m) * float(run_m)


def rate_strip_length(rate_per_m, strips, *, fraction=1.0):
    """Rate density over local bar strips. strips: iterable of (width_mm, run_mm) - non-overlapping widths with the
    local run of each. Returns the equivalent count (N x f x W, unrounded), the distribution width W (m), the
    width-weighted mean run (m), the equivalent total length N x f x sum(w x l) (m) and the physical BBS count
    (UNRESOLVED)."""
    _check_rate(rate_per_m, fraction)
    ws, wl = [], []
    for w, l in strips:
        if w < 0 or l < 0:
            raise SlabRebarQtoError(f"strip width and run must be non-negative: {(w, l)}")
        ws.append(float(w))
        wl.append(float(w) * float(l))
    width_mm = math.fsum(ws)
    integral_mm2 = math.fsum(wl)
    rf = float(rate_per_m) * float(fraction)
    return {"equivalent_count": rf * width_mm / 1000.0, "width_m": width_mm / 1000.0,
            "mean_run_m": (integral_mm2 / width_mm / 1000.0) if width_mm > 0 else 0.0,
            "integral_m2": integral_mm2 / 1e6, "length_m": rf * integral_mm2 / 1e6,
            "physical_bbs_count": UNRESOLVED}


def _check_rate(rate_per_m, fraction):
    if rate_per_m is None or float(rate_per_m) <= 0:
        raise SlabRebarQtoError(f"rate must be positive: {rate_per_m!r}")
    if not 0.0 < float(fraction) <= 1.0:
        raise SlabRebarQtoError(f"density fraction must be in (0, 1]: {fraction!r}")


def mass(dia_mm, length_m):
    """kg of an equivalent length of one diameter: L x D^2 / 162."""
    if length_m is None or length_m < 0:
        raise SlabRebarQtoError(f"length must be a non-negative number: {length_m!r}")
    um = unit_mass(dia_mm)
    return {"unit_mass_kg_m": um, "kg": float(length_m) * um, "method": UNIT_MASS_METHOD["method"]}


def explicit_count_mass(count, dia_mm, *, count_authority, length_authority, length_m=None):
    """A source count ('3Ø16') carries mass only when the count AND the length are both established."""
    ok = count_authority not in (None, AUTHORITY_BLOCKED) and length_authority not in (None, AUTHORITY_BLOCKED) \
        and length_m is not None
    if not ok:
        return {"kg": None, "length_m": None, "count": count, "lane": BLOCKED_UNQUANTIFIED,
                "why": "COUNT_AND_LENGTH_AUTHORITY_REQUIRED (no kg from a count alone)"}
    L = float(count) * float(length_m)
    return {"kg": mass(dia_mm, L)["kg"], "length_m": L, "count": count, "lane": PROJECT_BASIS_QTO, "why": None}


# ------------------------------------------------------------------ authority split
def authority_record(*, ratio=None, ratio_rule=None, ratio_authority=None, span_basis=None, span_authority=None,
                     origin=None, origin_authority=None, conventions=()):
    """One extent's authorities, kept in separate fields: the source ratio and the convention applying it.
    A printed ratio must cite its rule and be PROJECT_SOURCE; a convention (an Urban rule id) never sits in the
    ratio field."""
    if ratio is not None:
        if not ratio_rule or ratio_authority != PROJECT_SOURCE:
            raise SlabRebarQtoError("a printed ratio needs its source rule and PROJECT_SOURCE authority")
        if not 0.0 < float(ratio) < 1.0:
            raise SlabRebarQtoError(f"ratio out of range: {ratio}")
    for a in (span_authority, origin_authority):
        if a is not None and a not in AUTHORITIES:
            raise SlabRebarQtoError(f"unknown authority {a!r}")
    if any(str(c).startswith(PROJECT_SOURCE) for c in conventions):
        raise SlabRebarQtoError("a convention is not a project source")
    return {"SOURCE_RATIO": ratio, "SOURCE_RATIO_RULE": ratio_rule, "SOURCE_RATIO_AUTHORITY": ratio_authority,
            "SPAN_BASIS": span_basis, "SPAN_BASIS_AUTHORITY": span_authority, "MEASUREMENT_ORIGIN": origin,
            "MEASUREMENT_ORIGIN_AUTHORITY": origin_authority, "URBAN_CONVENTIONS": list(conventions)}


def top_extent_authority(*, ratio_rule, origin_stated_by_source, span_stated_by_source, urban_rule):
    """1/3 of the span over a support. The ratio is the source's; origin and span basis are the source's only where
    it states them, otherwise the Urban rule (support face into the clear span)."""
    conv = [] if (origin_stated_by_source and span_stated_by_source) else [urban_rule]
    return authority_record(
        ratio=1.0 / 3.0, ratio_rule=ratio_rule, ratio_authority=PROJECT_SOURCE,
        span_basis="CLEAR_SPAN of the panel on each side, along each bar line",
        span_authority=PROJECT_SOURCE if span_stated_by_source else URBAN_OWNER_MEASUREMENT_RULE,
        origin="SUPPORT_FACE (extension into the clear span)",
        origin_authority=PROJECT_SOURCE if origin_stated_by_source else URBAN_OWNER_MEASUREMENT_RULE,
        conventions=conv)


def curtailment_authority(*, ratio_rule, span_stated_by_source, origin_stated_by_source, local_bar_line_rule=None,
                          extra_conventions=()):
    """0.125 L stop of the curtailed 50 %. Ratio and the 50/50 split are the source's; a local bar-line L on an
    irregular panel (and any other convention) is recorded beside it."""
    conv = ([local_bar_line_rule] if local_bar_line_rule else []) + list(extra_conventions)
    return authority_record(
        ratio=0.125, ratio_rule=ratio_rule, ratio_authority=PROJECT_SOURCE,
        span_basis="CLEAR_SPAN" + (" (local L along each bar line)" if local_bar_line_rule else ""),
        span_authority=PROJECT_SOURCE if span_stated_by_source else URBAN_OWNER_MEASUREMENT_RULE,
        origin="FACE_OF_SUPPORT",
        origin_authority=PROJECT_SOURCE if origin_stated_by_source else URBAN_OWNER_MEASUREMENT_RULE,
        conventions=conv)


# ------------------------------------------------------------------ lanes
def s7_lane(*, count_basis, length_authorities, blocked=False, conflict=False, special=False,
            uses_minimum_cover=False, physical_complete=False):
    """The terminal lane of one item. SOURCE_DERIVED_PHYSICAL needs an explicit source count, source-only lengths
    and a complete physical component (no blocked complement)."""
    if special:
        return EXCLUDED_SPECIAL_STRUCTURE
    if conflict:
        return SOURCE_CONFLICT
    if blocked or count_basis == COUNT_UNRESOLVED or not length_authorities or \
            AUTHORITY_BLOCKED in length_authorities:
        return BLOCKED_UNQUANTIFIED
    if uses_minimum_cover or MINIMUM_PROJECT_COVER in length_authorities:
        return PROJECT_BASIS_NUMERIC
    if count_basis == COUNT_SOURCE_EXPLICIT and physical_complete and \
            set(length_authorities) <= {PROJECT_SOURCE}:
        return SOURCE_DERIVED_PHYSICAL
    return PROJECT_BASIS_QTO


def cover_portion(uses_minimum_cover):
    """A portion that uses a minimum cover (e.g. 25 mm) as a number is PROJECT_BASIS_NUMERIC, never exact."""
    if uses_minimum_cover:
        return {"lane": PROJECT_BASIS_NUMERIC, "note": ACTUAL_LENGTH_NOT_ESTABLISHED,
                "length_authority": MINIMUM_PROJECT_COVER}
    return {"lane": PROJECT_BASIS_QTO, "note": None, "length_authority": None}


def check_label(text):
    """Raise on a forbidden label (VERIFIED_PHYSICAL, AS_BUILT, SOURCE_EXACT, FINAL_SLAB_REBAR)."""
    up = str(text).upper()
    for bad in FORBIDDEN_LABELS:
        if bad in up:
            raise SlabRebarQtoError(f"forbidden label {bad} in {text!r}")
    return text


# ------------------------------------------------------------------ conservation
def _interval_at(s, t):
    (t0, t1, a0, a1, b0, b1) = s
    if abs(t1 - t0) <= TOL:
        return a0, b0
    u = (t - t0) / (t1 - t0)
    return a0 + u * (a1 - a0), b0 + u * (b1 - b0)


def strip_overlaps(strips, *, tol=1e-6):
    """Pairs of strips that share plan area. A strip is (id, t0, t1, a0, a1, b0, b1): across the bar from t0 to t1,
    its run along the bar is [a0, b0] at t0 and [a1, b1] at t1 (linear between). Exact for linear edges: the
    overlap is tested at the ends of the common transverse range and where the edges cross."""
    out = []
    S = sorted(((sid, tuple(map(float, r))) for sid, *r in strips), key=lambda s: (s[1][0], str(s[0])))
    box = [(min(r[2], r[3]), max(r[4], r[5])) for _, r in S]
    for i in range(len(S)):
        for j in range(i + 1, len(S)):
            (ia, a), (ib, b) = S[i], S[j]
            if b[0] >= a[1] - tol:                    # sorted by t0: no later strip reaches back into a
                break
            if min(box[i][1], box[j][1]) - max(box[i][0], box[j][0]) <= tol:   # apart along the bar
                continue
            lo, hi = max(a[0], b[0]), min(a[1], b[1])
            if hi - lo <= tol:
                continue
            ts = {lo, hi}
            for e_a, e_b in (((a[2], a[3]), (b[2], b[3])), ((a[4], a[5]), (b[4], b[5])),
                             ((a[2], a[3]), (b[4], b[5])), ((a[4], a[5]), (b[2], b[3]))):
                fa = (e_a[0], e_a[1])
                fb = (e_b[0], e_b[1])
                da = (fa[1] - fa[0]) / (a[1] - a[0]) if a[1] - a[0] > TOL else 0.0
                db = (fb[1] - fb[0]) / (b[1] - b[0]) if b[1] - b[0] > TOL else 0.0
                if abs(da - db) > TOL:
                    t = (fb[0] - db * b[0] - fa[0] + da * a[0]) / (da - db)
                    if lo < t < hi:
                        ts.add(t)
            for t in sorted(ts):
                a_lo, a_hi = _interval_at(a, t)
                b_lo, b_hi = _interval_at(b, t)
                if min(a_hi, b_hi) - max(a_lo, b_lo) > tol:
                    out.append((ia, ib))
                    break
    return out


def strip_coverage(strips, area_mm2, *, rel_tol=1e-9):
    """sum(width x mean local run) of a family's strips against the panel area: no gap, no excess."""
    got = math.fsum(float(w) * float(l) for w, l in strips)
    ok = abs(got - float(area_mm2)) <= rel_tol * max(abs(float(area_mm2)), 1.0)
    return {"integral_mm2": got, "area_mm2": float(area_mm2), "difference_mm2": got - float(area_mm2),
            "reconciled": ok}


def density_budget(fractions, *, full=True):
    """Released density fractions at one point of a strip: exactly 1 for a fully released family, never above 1."""
    s = math.fsum(float(f) for f in fractions)
    return abs(s - 1.0) <= TOL if full else s <= 1.0 + TOL


def duplicates(keys):
    """Keys seen more than once (one physical support family is quantified once)."""
    seen = defaultdict(int)
    for k in keys:
        seen[k] += 1
    return sorted((k for k, n in seen.items() if n > 1), key=str)


def reconcile(rows, levels, *, value="kg", rel_tol=1e-9):
    """Sum a value at each level (a row key, e.g. component, owner, floor, diameter) and check every level adds up
    to the same total. rows: dicts; levels: key names. Rows with value None are not mass (and must not be in rows
    for a mass reconciliation)."""
    vals = [r[value] for r in rows]
    if any(v is None for v in vals):
        raise SlabRebarQtoError("a row without a value cannot be reconciled as mass")
    total = math.fsum(vals)
    out = {"total": total, "levels": {}}
    for lv in levels:
        g = defaultdict(list)
        for r in rows:
            g[r[lv]].append(r[value])
        sums = {k: math.fsum(v) for k, v in g.items()}
        s = math.fsum(sums.values())
        out["levels"][lv] = {"groups": len(sums), "sum": s, "by": sums,
                             "ok": abs(s - total) <= rel_tol * max(abs(total), 1.0)}
    out["ok"] = all(v["ok"] for v in out["levels"].values())
    return out


def blind_source_hits(text, forbidden):
    """Tokens of a reference / donor / estimate that a blind quantity builder must not contain."""
    return [t for t in forbidden if t in text]
