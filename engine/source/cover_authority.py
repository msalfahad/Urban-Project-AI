"""COVER AUTHORITY - what a concrete-cover rule lets a bar length, count or mass claim (generic, stdlib only).

Cover basis (exactly one per rule application):
  EXACT_PROJECT_COVER    the project fixes the cover (an exact rule or a dimension in the detail)
  MINIMUM_PROJECT_COVER  the project gives a minimum only ("not less than"): actual cover >= c_min
  DERIVED_EXACT_COVER    an exact cover derived from source geometry (bar line bound to a dimensioned face)
  BOUNDED_COVER          the project bounds the cover on both sides: c_min <= c <= c_max
  UNRESOLVED             no cover authority

Straight run between two covers: L(c1, c2) = D - c1 - c2, strictly decreasing in each cover.
  EXACT      -> L is exact
  MINIMUM    -> L(c_min) is the MAXIMUM straight run (actual <= value)
  BOUNDED    -> L lies in [D - 2 c_max, D - 2 c_min] (no single number is a bound of both kinds)
  UNRESOLVED -> no length
Rate count inside the covers: n(c) = ceil(rate x (W - 2c)), non-increasing in c. Whether a bar also sits at the far
edge (+1) is a separate uncertainty in the opposite direction.

Direction of an uncertainty: EXACT, UPPER (true <= value), LOWER (true >= value), NONE (no bound).
For products and sums of non-negative terms:
  EXACT x D = D;  UPPER x UPPER = UPPER;  LOWER x LOWER = LOWER;  UPPER x LOWER = NONE;  NONE x D = NONE.
An unquantified non-negative addition (a blocked leg, hook or bend) acts as LOWER.
Mass state by direction: EXACT -> SOURCE_DERIVED_EXACT, LOWER -> LOWER_BOUND, UPPER -> UPPER_BOUND_KNOWN,
NONE -> PROJECT_BASIS_NUMERIC: a number on the project-drawing calculation basis, not a bound of the as-built bar.

A cover correction may change a state. It never invents a cover, never picks an assumed actual cover and never adds
steel. A kg retraction is allowed only where the number cannot stay on its basis.
"""

from __future__ import annotations

import math

EXACT_PROJECT_COVER = "EXACT_PROJECT_COVER"
MINIMUM_PROJECT_COVER = "MINIMUM_PROJECT_COVER"
DERIVED_EXACT_COVER = "DERIVED_EXACT_COVER"
BOUNDED_COVER = "BOUNDED_COVER"
UNRESOLVED = "UNRESOLVED"
COVER_BASES = (EXACT_PROJECT_COVER, MINIMUM_PROJECT_COVER, DERIVED_EXACT_COVER, BOUNDED_COVER, UNRESOLVED)

MINIMUM, MAXIMUM, EXACT_WORDING, UNKNOWN_WORDING = "MINIMUM", "MAXIMUM", "EXACT", "UNKNOWN"
MIN_MARKERS = ("لا يقل", "لا تقل", "لايقل", "لاتقل", "الحد الأدنى", "الحد الادنى", "not less than", "minimum",
               "min.", "at least", ">=", "≥")
MAX_MARKERS = ("لا يزيد", "لا تزيد", "لايزيد", "الحد الأقصى", "not more than", "maximum", "max.", "at most", "<=", "≤")
EXACT_MARKERS = (" = ", "shall be", "is to be", "يكون")

EXACT, UPPER, LOWER, NONE = "EXACT", "UPPER", "LOWER", "NONE"
DIRECTIONS = (EXACT, UPPER, LOWER, NONE)

SOURCE_DERIVED_EXACT = "SOURCE_DERIVED_EXACT"
LOWER_BOUND = "LOWER_BOUND"
UPPER_BOUND_KNOWN = "UPPER_BOUND_KNOWN"
PROJECT_BASIS_NUMERIC = "PROJECT_BASIS_NUMERIC"
MASS_STATES = (SOURCE_DERIVED_EXACT, LOWER_BOUND, UPPER_BOUND_KNOWN, PROJECT_BASIS_NUMERIC)
_MASS_OF = {EXACT: SOURCE_DERIVED_EXACT, LOWER: LOWER_BOUND, UPPER: UPPER_BOUND_KNOWN, NONE: PROJECT_BASIS_NUMERIC}

SOURCE_EXACT_STRAIGHT_RUN = "SOURCE_EXACT_STRAIGHT_RUN"
SOURCE_MAXIMUM_STRAIGHT_RUN = "SOURCE_MAXIMUM_STRAIGHT_RUN"
SOURCE_BOUNDED_STRAIGHT_RUN = "SOURCE_BOUNDED_STRAIGHT_RUN"
STRAIGHT_RUN_UNRESOLVED = "STRAIGHT_RUN_UNRESOLVED"
_RUN_STATE = {EXACT_PROJECT_COVER: SOURCE_EXACT_STRAIGHT_RUN, DERIVED_EXACT_COVER: SOURCE_EXACT_STRAIGHT_RUN,
              MINIMUM_PROJECT_COVER: SOURCE_MAXIMUM_STRAIGHT_RUN, BOUNDED_COVER: SOURCE_BOUNDED_STRAIGHT_RUN,
              UNRESOLVED: STRAIGHT_RUN_UNRESOLVED}
_RUN_DIRECTION = {EXACT_PROJECT_COVER: EXACT, DERIVED_EXACT_COVER: EXACT, MINIMUM_PROJECT_COVER: UPPER,
                  BOUNDED_COVER: NONE, UNRESOLVED: NONE}

RECORD_TYPE = "COVER_AUTHORITY_CORRECTION"
TOL = 1e-9


class CoverAuthorityError(ValueError):
    pass


# ------------------------------------------------------------------ wording and basis
def wording_kind(text):
    """MINIMUM / MAXIMUM / EXACT / UNKNOWN from the wording of a cover rule (a minimum marker wins)."""
    t = f" {str(text or '').lower()} "
    if any(m.lower() in t for m in MIN_MARKERS):
        return MINIMUM
    if any(m.lower() in t for m in MAX_MARKERS):
        return MAXIMUM
    if any(m in t for m in EXACT_MARKERS):
        return EXACT_WORDING
    return UNKNOWN_WORDING


def classify_cover_basis(*, rule_kind, value_mm=None, detail_exact_mm=None, derived_exact_mm=None, bounds_mm=None):
    """One cover basis. A dimension in the detail or a derived exact cover outranks the general rule; a minimum rule
    never becomes exact by itself."""
    if detail_exact_mm is not None:
        return {"basis": EXACT_PROJECT_COVER, "value_mm": float(detail_exact_mm), "label": _label(
            EXACT_PROJECT_COVER, detail_exact_mm), "source": "DETAIL_DIMENSION"}
    if derived_exact_mm is not None:
        return {"basis": DERIVED_EXACT_COVER, "value_mm": float(derived_exact_mm),
                "label": _label(DERIVED_EXACT_COVER, derived_exact_mm), "source": "SOURCE_GEOMETRY"}
    if bounds_mm is not None:
        lo, hi = bounds_mm
        if lo is None or hi is None or not 0 < lo <= hi:
            raise CoverAuthorityError("a bounded cover needs 0 < c_min <= c_max")
        return {"basis": BOUNDED_COVER, "bounds_mm": [float(lo), float(hi)], "label": BOUNDED_COVER,
                "source": "SOURCE_BOUNDS"}
    if value_mm is not None and value_mm > 0:
        if rule_kind == EXACT_WORDING:
            return {"basis": EXACT_PROJECT_COVER, "value_mm": float(value_mm),
                    "label": _label(EXACT_PROJECT_COVER, value_mm), "source": "GENERAL_RULE"}
        if rule_kind == MINIMUM:
            return {"basis": MINIMUM_PROJECT_COVER, "value_mm": float(value_mm),
                    "label": _label(MINIMUM_PROJECT_COVER, value_mm), "source": "GENERAL_RULE"}
    return {"basis": UNRESOLVED, "label": UNRESOLVED, "source": None}


def _label(basis, v):
    return f"{basis}_{int(v) if float(v).is_integer() else v}"


# ------------------------------------------------------------------ straight runs and counts
def straight_run_mm(dimension_mm, c1_mm, c2_mm):
    if dimension_mm is None or c1_mm is None or c2_mm is None or min(c1_mm, c2_mm) < 0:
        raise CoverAuthorityError("a straight run needs a dimension and two non-negative covers")
    run = float(dimension_mm) - float(c1_mm) - float(c2_mm)
    if run <= 0:
        raise CoverAuthorityError("the covers leave no straight run")
    return run


def straight_run_claim(dimension_mm, basis):
    """The straight run a cover basis supports: value, direction and interval."""
    b = basis["basis"]
    if b in (EXACT_PROJECT_COVER, DERIVED_EXACT_COVER, MINIMUM_PROJECT_COVER):
        v = straight_run_mm(dimension_mm, basis["value_mm"], basis["value_mm"])
        lo = v if b != MINIMUM_PROJECT_COVER else None              # a minimum cover gives no lower limit
        return {"state": _RUN_STATE[b], "direction": _RUN_DIRECTION[b], "value_mm": v, "interval_mm": [lo, v]}
    if b == BOUNDED_COVER:
        lo_c, hi_c = basis["bounds_mm"]
        return {"state": _RUN_STATE[b], "direction": NONE, "value_mm": None,
                "interval_mm": [straight_run_mm(dimension_mm, hi_c, hi_c), straight_run_mm(dimension_mm, lo_c, lo_c)]}
    return {"state": STRAIGHT_RUN_UNRESOLVED, "direction": NONE, "value_mm": None, "interval_mm": [None, None]}


def count_at_cover(rate_per_m, width_mm, cover_mm):
    """ceil(rate x (W - 2c)) - the rate count inside both covers, no edge bar added."""
    inside = straight_run_mm(width_mm, cover_mm, cover_mm)
    if rate_per_m is None or rate_per_m <= 0:
        raise CoverAuthorityError("a rate count needs a positive rate")
    return int(math.ceil(rate_per_m * inside / 1000.0 - 1e-9))


def count_direction(count_mode, basis, edge_bar_established=False):
    """EXACT for a printed count; a rate count takes the cover direction and, while the far-edge bar is not
    established, the opposite (LOWER) direction of the +1 convention."""
    if count_mode == "EXPLICIT_COUNT":
        return EXACT
    d = _RUN_DIRECTION.get(basis["basis"], NONE)
    return d if edge_bar_established else combine(d, LOWER)


# ------------------------------------------------------------------ direction algebra
def combine(*directions):
    ds = set()
    for d in directions:
        if d not in DIRECTIONS:
            raise CoverAuthorityError(f"unknown direction {d!r}")
        ds.add(d)
    ds.discard(EXACT)
    if not ds:
        return EXACT
    if NONE in ds or ds == {UPPER, LOWER}:
        return NONE
    return ds.pop()


def with_unquantified_additions(direction, n_additions):
    """An unquantified non-negative portion (leg, hook, bend) can only add length: it acts as LOWER."""
    return combine(direction, LOWER) if n_additions else direction


def mass_state(direction):
    return _MASS_OF[direction]


# ------------------------------------------------------------------ records
def cover_correction(*, correction_id, component_id, original_state, original_kg, cover_basis, new_length_state,
                     new_count_direction, new_mass_state, correction_reason, source_evidence, correction_kg=0.0,
                     **extra):
    """COVER_AUTHORITY_CORRECTION: a state correction over a frozen component (kg change 0 unless retracted)."""
    if cover_basis not in COVER_BASES:
        raise CoverAuthorityError(f"{correction_id}: unknown cover basis {cover_basis!r}")
    if new_mass_state not in MASS_STATES:
        raise CoverAuthorityError(f"{correction_id}: unknown mass state {new_mass_state!r}")
    if new_count_direction not in DIRECTIONS:
        raise CoverAuthorityError(f"{correction_id}: unknown count direction {new_count_direction!r}")
    orig, corr = float(original_kg or 0.0), float(correction_kg or 0.0)
    if orig < 0 or corr > TOL:
        raise CoverAuthorityError(f"{correction_id}: a cover correction never adds steel")
    retained = orig + corr
    if retained < -1e-6:
        raise CoverAuthorityError(f"{correction_id}: cannot remove more than was known")
    if original_state == new_mass_state and abs(corr) <= TOL:
        raise CoverAuthorityError(f"{correction_id}: a correction changes the state or the kg")
    if new_mass_state == LOWER_BOUND and cover_basis == MINIMUM_PROJECT_COVER and \
            new_length_state == SOURCE_MAXIMUM_STRAIGHT_RUN:
        raise CoverAuthorityError(f"{correction_id}: a straight run at minimum cover is never a silent lower bound")
    if not str(correction_reason).strip() or not source_evidence:
        raise CoverAuthorityError(f"{correction_id}: a correction states its reason and evidence")
    rec = {"CORRECTION_ID": correction_id, "RECORD_TYPE": RECORD_TYPE, "COMPONENT_ID": component_id,
           "ORIGINAL_STATE": original_state, "ORIGINAL_KG": orig, "COVER_BASIS": cover_basis,
           "NEW_LENGTH_STATE": new_length_state, "NEW_COUNT_DIRECTION": new_count_direction,
           "NEW_MASS_STATE": new_mass_state, "CORRECTION_KG": corr, "RETAINED_NUMERIC_KG": max(retained, 0.0),
           "CORRECTION_REASON": correction_reason, "SOURCE_EVIDENCE": source_evidence}
    rec.update(extra)
    return rec


def conservation(original_known, corrections, corrected_known, tol=1e-6):
    corr = sum(c["CORRECTION_KG"] for c in corrections)
    checks = {"original_plus_correction_is_corrected": abs(original_known + corr - corrected_known) <= tol,
              "no_positive_correction": all(c["CORRECTION_KG"] <= TOL for c in corrections),
              "retained_plus_removed_is_original": all(
                  abs(c["RETAINED_NUMERIC_KG"] - c["CORRECTION_KG"] - c["ORIGINAL_KG"]) <= tol for c in corrections)}
    return {"original_known": original_known, "correction_kg": corr, "corrected_known": corrected_known,
            "checks": checks, "all_pass": all(checks.values())}


def policy_record():
    return {"record_type": RECORD_TYPE, "cover_bases": list(COVER_BASES), "directions": list(DIRECTIONS),
            "mass_states": list(MASS_STATES),
            "rules": ["a minimum cover makes the straight run at that cover a maximum, never a lower bound",
                      "a detail dimension or derived exact cover outranks a general minimum rule",
                      "rate counts inside the cover move with the cover; the +1 edge bar is a separate uncertainty",
                      "opposite-direction uncertainties give no bound: the number stays a project-basis value",
                      "no cover is invented and no actual cover is assumed; a correction never adds steel"]}
