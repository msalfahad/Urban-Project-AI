"""REBAR SANITY VARIANCE - report layer between ACCURATE_BOQ_REBAR and ROUGH_REBAR_SUMMARY (generic).

The only place the two reinforcement products meet. It reads a frozen accurate summary
(accurate_boq_rebar.summarise) and a rough summary (rough_rebar_sanity.rough_summary), places them side by side and
reports a SANITY_VARIANCE where both exist. It returns new rows only: neither input is changed, no accurate state or
release status is touched, and a large variance raises REBAR_SANITY_REVIEW - nothing else. A gap is never called
missing steel.

Variance is computed only where the accurate category has nothing blocked (no BLOCKED_MODELLED kg and no
BLOCKED_UNQUANTIFIED part); otherwise the figures are shown side by side.
Stdlib only.
"""

from __future__ import annotations

import copy

from engine.source import accurate_boq_rebar as AB
from engine.source import rough_rebar_sanity as RR

SANITY_VARIANCE = "SANITY_VARIANCE"
SIDE_BY_SIDE = "SIDE_BY_SIDE_ACCURATE_INCOMPLETE"
NO_ACCURATE = "NO_ACCURATE_QUANTITY"
NO_ROUGH = "NO_ROUGH_REFERENCE"
REVIEW_FLAG = "REBAR_SANITY_REVIEW"
DEFAULT_REVIEW_THRESHOLD_PERCENT = 25.0          # URBAN_DEFAULT_CANDIDATE - owner to confirm

# accurate category -> rough category (report-layer configuration; None = NOT_CONFIGURED for a rough reference)
ACCURATE_TO_ROUGH = {
    "FOUNDATIONS": "FOUNDATIONS_RELATED", "GROUND_BEAMS": "GROUND_BEAMS_AND_GROUND_SLAB",
    "GROUND_SLAB": "GROUND_BEAMS_AND_GROUND_SLAB", "COLUMNS": "WALLS_AND_COLUMNS", "BEAMS": "BEAMS",
    "SLABS": "SLABS", "STAIRS": "STAIRS_AND_DOME", "DOME": "STAIRS_AND_DOME", "POOL": "SWIMMING_POOL",
    "WALLS": None, "LIFT": None, "PARAPET": None, "SPECIAL_RC": None,
}


def _accurate_by_rough(accurate):
    out, unmapped = {}, []
    for cat, r in accurate["categories"].items():
        rc = ACCURATE_TO_ROUGH.get(cat)
        if rc is None:
            unmapped.append({"accurate_category": cat, "state": RR.NOT_CONFIGURED})
            continue
        g = out.setdefault(rc, {"accurate_categories": [], "released_kg": 0.0, "provisional_kg": 0.0,
                                "blocked_modelled_kg": 0.0, "blocked_unquantified_parts": 0, "statuses": []})
        g["accurate_categories"].append(cat)
        for k in ("released_kg", "provisional_kg", "blocked_modelled_kg", "blocked_unquantified_parts"):
            g[k] += r[k]
        g["statuses"].append(r["official_status"])
    return out, unmapped


def compare(accurate, rough, review_threshold_percent=DEFAULT_REVIEW_THRESHOLD_PERCENT):
    """Rows {category, ACCURATE_*, ROUGH_REFERENCE_KG, SANITY_VARIANCE_KG / _PERCENT, state, flags}."""
    if accurate.get("product") != AB.PRODUCT or rough.get("product") != RR.PRODUCT:
        raise ValueError("compare needs an ACCURATE_BOQ_REBAR summary and a ROUGH_REBAR_SUMMARY")
    acc, unmapped = _accurate_by_rough(copy.deepcopy(accurate))
    rgh = copy.deepcopy(rough)["categories"]
    rows = []
    for cat in RR.ROUGH_CATEGORIES:
        a, r = acc.get(cat), rgh.get(cat)
        if a is None and r is None:
            continue
        ref = None if r is None else r["rough_kg_modelled_basis"]
        row = {"category": cat, "accurate_categories": [] if a is None else a["accurate_categories"],
               "ACCURATE_RELEASED_KG": None if a is None else a["released_kg"],
               "ACCURATE_PROVISIONAL_KG": None if a is None else a["provisional_kg"],
               "ACCURATE_BLOCKED_MODELLED_KG": None if a is None else a["blocked_modelled_kg"],
               "ACCURATE_BLOCKED_UNQUANTIFIED_PARTS": None if a is None else a["blocked_unquantified_parts"],
               "ACCURATE_PROJECTED_KG": None if a is None else a["released_kg"] + a["provisional_kg"],
               "ACCURATE_OFFICIAL_STATUS": None if a is None else sorted(set(a["statuses"])),
               "ROUGH_REFERENCE_KG": ref, "ROUGH_RATIO_STATE": None if r is None else r["ratio_state"],
               "SANITY_VARIANCE_KG": None, "SANITY_VARIANCE_PERCENT": None, "flags": []}
        if a is None:
            row["state"] = NO_ACCURATE
        elif ref is None:
            row["state"] = NO_ROUGH if r is None else RR.NOT_CONFIGURED
        elif a["blocked_modelled_kg"] > 0 or a["blocked_unquantified_parts"] > 0:
            row["state"] = SIDE_BY_SIDE
        else:
            v = row["ACCURATE_PROJECTED_KG"] - ref
            row["SANITY_VARIANCE_KG"] = v
            row["SANITY_VARIANCE_PERCENT"] = None if not ref else 100.0 * v / ref
            row["state"] = SANITY_VARIANCE
            if row["SANITY_VARIANCE_PERCENT"] is not None and abs(row["SANITY_VARIANCE_PERCENT"]) >= \
                    review_threshold_percent:
                row["flags"].append(REVIEW_FLAG)
        rows.append(row)
    return {"rows": rows, "accurate_not_configured_for_rough": unmapped,
            "review_threshold_percent": review_threshold_percent,
            "rule": "variance is a sanity signal only; it never changes ACCURATE_BOQ_REBAR"}


def project_intensity_kpi(accurate, rough):
    """Whole-project kg/m3 - INFORMATIONAL only; never a production or estimating basis."""
    kg = accurate["project"]["released_kg"]
    m3 = sum(r["released_concrete_m3"] for r in rough["categories"].values())
    return {"kg_per_m3_released": None if not m3 else kg / m3, "use": "INFORMATIONAL_KPI_NOT_FOR_PRODUCTION",
            "why": "steel intensity is category-specific; one villa-wide ratio is never applied"}
