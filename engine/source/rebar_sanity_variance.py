"""REBAR SANITY VARIANCE - report layer between ACCURATE_BOQ_REBAR and ROUGH_REBAR_SUMMARY (generic).

The only place the two reinforcement products meet. It reads a frozen accurate summary
(accurate_boq_rebar.summarise) and a rough summary (rough_rebar_sanity.rough_summary), places them side by side and
reports a SANITY_VARIANCE only where it is evaluable. Neither input is changed, no accurate state or release status
is touched, and a gap is never called missing steel.

Evaluable only when ALL hold, otherwise a NOT_EVALUABLE state is reported instead of a percentage:
  * the accurate side has no BLOCKED_MODELLED kg and no BLOCKED_UNQUANTIFIED part   (NOT_EVALUABLE_INCOMPLETE_ACCURATE)
  * the rough concrete basis has no blocked concrete                              (NOT_EVALUABLE_INCOMPLETE_CONCRETE)
  * the element classes behind the rough concrete are all covered by accurate parts of the same rough category
                                                                                    (NOT_EVALUABLE_SCOPE_MISMATCH)
Tiers on |variance %|:  < 15 NORMAL  | 15-<25 WATCH | 25-<40 REBAR_SANITY_REVIEW | >= 40 MAJOR_SANITY_REVIEW.
Stdlib only.
"""

from __future__ import annotations

import copy

from engine.source import accurate_boq_rebar as AB
from engine.source import rough_rebar_sanity as RR

SANITY_VARIANCE = "SANITY_VARIANCE"
NOT_EVALUABLE_INCOMPLETE_ACCURATE = "NOT_EVALUABLE_INCOMPLETE_ACCURATE"
NOT_EVALUABLE_INCOMPLETE_CONCRETE = "NOT_EVALUABLE_INCOMPLETE_CONCRETE"
NOT_EVALUABLE_SCOPE_MISMATCH = "NOT_EVALUABLE_SCOPE_MISMATCH"
SIDE_BY_SIDE = NOT_EVALUABLE_INCOMPLETE_ACCURATE                 # back-compatible name
NO_ACCURATE = "NO_ACCURATE_QUANTITY"
NO_ROUGH = "NO_ROUGH_REFERENCE"
NORMAL, WATCH, REVIEW, MAJOR = "NORMAL", "WATCH", "REBAR_SANITY_REVIEW", "MAJOR_SANITY_REVIEW"
REVIEW_FLAG = REVIEW
TIERS = ((15.0, NORMAL), (25.0, WATCH), (40.0, REVIEW), (float("inf"), MAJOR))

# accurate category -> rough category and the element classes it measures (report-layer configuration)
ACCURATE_TO_ROUGH = {
    "FOUNDATIONS": "FOUNDATIONS_RELATED", "GROUND_BEAMS": "GROUND_BEAMS_AND_GROUND_SLAB",
    "GROUND_SLAB": "GROUND_BEAMS_AND_GROUND_SLAB", "COLUMNS": "WALLS_AND_COLUMNS", "BEAMS": "BEAMS",
    "SLABS": "SLABS", "STAIRS": "STAIRS_AND_DOME", "DOME": "STAIRS_AND_DOME", "POOL": "SWIMMING_POOL",
    "WALLS": None, "LIFT": None, "PARAPET": None, "SPECIAL_RC": None,
}
ACCURATE_CATEGORY_CLASSES = {
    "FOUNDATIONS": ("FOUNDATION_PAD", "COMBINED_FOOTING", "STRIP_FOOTING", "FOUNDATION_STRAP_BEAM"),
    "GROUND_BEAMS": ("GROUND_BEAM", "BOUNDARY_GROUND_BEAM"), "GROUND_SLAB": ("GROUND_SLAB",),
    "COLUMNS": ("COLUMN", "BEAM_COLUMN_JOINT"), "BEAMS": ("BEAM", "CONTINUOUS_BEAM", "RING_BEAM"),
    "SLABS": ("SOLID_SLAB", "FLAT_SLAB", "RIBBED_SLAB"), "STAIRS": ("STAIR",), "DOME": ("DOME",),
    "POOL": ("POOL_BASE", "POOL_WALL", "POOL_BEAM"),
}
NECK_COMPONENTS = ("NECK_MAIN_BAR", "NECK_TIE")


def tier(pct):
    a = abs(pct)
    return next(name for limit, name in TIERS if a < limit)


def _accurate_by_rough(accurate, profile):
    out, unmapped = {}, []

    def bucket(rc):
        return out.setdefault(rc, {"accurate_categories": set(), "classes": set(), "released_kg": 0.0,
                                   "provisional_kg": 0.0, "blocked_modelled_kg": 0.0,
                                   "blocked_unquantified_parts": 0, "statuses": set()})

    for cat, r in accurate["categories"].items():
        comps = r.get("components") or {}
        neck_kg = {k: v for k, v in comps.items() if k in NECK_COMPONENTS}
        rc = ACCURATE_TO_ROUGH.get(cat)
        if rc is None and not neck_kg:
            unmapped.append({"accurate_category": cat, "state": RR.NOT_CONFIGURED})
            continue
        # necks follow the rough profile's own mapping of FOUNDATION_NECK
        neck_rc = RR.category_of("FOUNDATION_NECK", profile)
        moved = {"released_kg": 0.0, "provisional_kg": 0.0, "blocked_modelled_kg": 0.0,
                 "blocked_unquantified_parts": 0}
        if neck_kg and neck_rc:
            g = bucket(neck_rc)
            g["accurate_categories"].add(f"{cat}:NECK")
            g["classes"].add("FOUNDATION_NECK")
            for states in neck_kg.values():
                rel = states.get("VERIFIED", 0.0) + states.get("LOWER_BOUND", 0.0)
                g["released_kg"] += rel
                g["provisional_kg"] += states.get("PROVISIONAL", 0.0)
                g["blocked_modelled_kg"] += states.get("BLOCKED_MODELLED", 0.0)
                g["blocked_unquantified_parts"] += int(states.get("BLOCKED_UNQUANTIFIED", 0))
                moved["released_kg"] += rel
                moved["provisional_kg"] += states.get("PROVISIONAL", 0.0)
                moved["blocked_modelled_kg"] += states.get("BLOCKED_MODELLED", 0.0)
                moved["blocked_unquantified_parts"] += int(states.get("BLOCKED_UNQUANTIFIED", 0))
            g["statuses"].add(r["official_status"])
        if rc is None:
            continue
        g = bucket(rc)
        g["accurate_categories"].add(cat)
        g["classes"].update(ACCURATE_CATEGORY_CLASSES.get(cat, ()))
        for k in moved:
            g[k] += r[k] - moved[k]
        g["statuses"].add(r["official_status"])
    return out, unmapped


def compare(accurate, rough, profile=None):
    """Rows {category, ACCURATE_*, ROUGH_REFERENCE_KG, SANITY_VARIANCE_KG / _PERCENT, state, tier, flags}."""
    if accurate.get("product") != AB.PRODUCT or rough.get("product") != RR.PRODUCT:
        raise ValueError("compare needs an ACCURATE_BOQ_REBAR summary and a ROUGH_REBAR_SUMMARY")
    acc, unmapped = _accurate_by_rough(copy.deepcopy(accurate), profile)
    rgh = copy.deepcopy(rough)["categories"]
    rows = []
    for cat in RR.ROUGH_CATEGORIES:
        a, r = acc.get(cat), rgh.get(cat)
        if a is None and r is None:
            continue
        ref = None if r is None else r["rough_kg_modelled_basis"]
        row = {"category": cat, "accurate_categories": [] if a is None else sorted(a["accurate_categories"]),
               "ACCURATE_RELEASED_KG": None if a is None else a["released_kg"],
               "ACCURATE_PROVISIONAL_KG": None if a is None else a["provisional_kg"],
               "ACCURATE_BLOCKED_MODELLED_KG": None if a is None else a["blocked_modelled_kg"],
               "ACCURATE_BLOCKED_UNQUANTIFIED_PARTS": None if a is None else a["blocked_unquantified_parts"],
               "ACCURATE_PROJECTED_KG": None if a is None else a["released_kg"] + a["provisional_kg"],
               "ACCURATE_OFFICIAL_STATUS": None if a is None else sorted(a["statuses"]),
               "ROUGH_REFERENCE_KG": ref, "ROUGH_RATIO_STATE": None if r is None else r["ratio_state"],
               "SANITY_VARIANCE_KG": None, "SANITY_VARIANCE_PERCENT": None, "tier": None, "flags": []}
        missing_scope = sorted(set(r.get("element_classes", [])) - a["classes"]) if (a and r) else []
        row["scope_not_covered_by_accurate"] = missing_scope
        if a is None:
            row["state"] = NO_ACCURATE
        elif ref is None:
            row["state"] = NO_ROUGH if r is None else RR.NOT_CONFIGURED
        elif a["blocked_modelled_kg"] > 0 or a["blocked_unquantified_parts"] > 0:
            row["state"] = NOT_EVALUABLE_INCOMPLETE_ACCURATE
        elif r["blocked_concrete_m3"] > 0:
            row["state"] = NOT_EVALUABLE_INCOMPLETE_CONCRETE
        elif missing_scope:
            row["state"] = NOT_EVALUABLE_SCOPE_MISMATCH
        else:
            v = row["ACCURATE_PROJECTED_KG"] - ref
            row["SANITY_VARIANCE_KG"] = v
            row["SANITY_VARIANCE_PERCENT"] = None if not ref else 100.0 * v / ref
            row["state"] = SANITY_VARIANCE
            if row["SANITY_VARIANCE_PERCENT"] is not None:
                row["tier"] = tier(row["SANITY_VARIANCE_PERCENT"])
                if row["tier"] in (REVIEW, MAJOR):
                    row["flags"].append(row["tier"])
        rows.append(row)
    return {"rows": rows, "accurate_not_configured_for_rough": unmapped,
            "tiers": [{"below_pct": lim, "tier": name} for lim, name in TIERS],
            "rule": "variance is a sanity signal only; it never changes ACCURATE_BOQ_REBAR"}


def project_intensity_kpi(accurate, rough):
    """Whole-project kg/m3 - INFORMATIONAL only; never a production or estimating basis."""
    kg = accurate["project"]["released_kg"]
    m3 = sum(r["released_concrete_m3"] for r in rough["categories"].values())
    return {"kg_per_m3_released": None if not m3 else kg / m3, "use": "INFORMATIONAL_KPI_NOT_FOR_PRODUCTION",
            "why": "steel intensity is category-specific; one villa-wide ratio is never applied"}
