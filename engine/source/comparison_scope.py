"""COMPARISON SCOPE MAPPER (generic).

Production quantities stay physical and granular (footing, strap, ground beam, ground slab, neck, column, slab,
beam downstand, beam-column joint, stair, dome, pool wall, pool base, ...). A VIEW assembles those physical components
into one reporting convention (Urban physical, a QS workbook, an external oracle ...) WITHOUT changing them.

Every view category states
    MEASUREMENT_BASIS     e.g. BEAM_DOWNSTAND_ONLY vs BEAM_GROSS_DEPTH, SLAB_FULL_DEPTH vs SLAB_NET_OF_BEAMS
    INCLUDED_COMPONENTS   physical component kinds it sums
    EXCLUDED_COMPONENTS   kinds it explicitly leaves out
    OVERLAP_POLICY        how shared concrete (slab over a beam, beam-column joint) is allocated

Comparison of two views' categories is
    DIRECTLY_COMPARABLE              same basis and same included kinds
    COMPARABLE_AFTER_NORMALIZATION   different allocation, but a declared normalisation group makes the union
                                     comparable (e.g. BEAMS + SLABS together)
    NOT_COMPARABLE                   otherwise - and no percentage is ever reported for it.
Stdlib only.
"""

from __future__ import annotations

from collections import defaultdict

POLICY_ID = "COMPARISON_SCOPE_V1"
DIRECT = "DIRECTLY_COMPARABLE"
NORMALIZED = "COMPARABLE_AFTER_NORMALIZATION"
NOT_COMPARABLE = "NOT_COMPARABLE"
RESULTS = (DIRECT, NORMALIZED, NOT_COMPARABLE)

VIEWS = ("URBAN_PHYSICAL_VIEW", "FREELANCER_QS_VIEW", "UC4N_VIEW", "CHRISTIANNP_VIEW")


class ScopeError(ValueError):
    pass


def make_view(view_id, categories, normalization_groups=()):
    """categories: [{category, measurement_basis, included_components[], excluded_components[], overlap_policy}].
    normalization_groups: [{group_id, categories[], basis}] - unions that are comparable across allocation
    conventions. A component kind may appear in ONE category of a view only."""
    owner = {}
    for c in categories:
        for k in c["included_components"]:
            if k in owner:
                raise ScopeError(f"{view_id}: component {k} in two categories ({owner[k]}, {c['category']})")
            owner[k] = c["category"]
        for f in ("measurement_basis", "overlap_policy"):
            if not c.get(f):
                raise ScopeError(f"{view_id}/{c['category']}: {f} is required")
    return {"view_id": view_id, "categories": {c["category"]: c for c in categories},
            "component_owner": owner, "normalization_groups": list(normalization_groups)}


def assemble(view, components):
    """components: [{component_id, kind, quantity, unit, state}] (physical, never modified).
    Each component lands in exactly one category of the view, or in `unmapped`. Returns category totals."""
    totals = defaultdict(lambda: {"quantity": 0.0, "components": [], "states": defaultdict(float),
                                  "missing_value": []})
    unmapped, used = [], set()
    for c in components:
        if c["component_id"] in used:
            raise ScopeError(f"component {c['component_id']} supplied twice")
        used.add(c["component_id"])
        cat = view["component_owner"].get(c["kind"])
        if cat is None:
            unmapped.append(c["component_id"])
            continue
        t = totals[cat]
        t["components"].append(c["component_id"])
        if c.get("quantity") is None:
            t["missing_value"].append(c["component_id"])
        else:
            t["quantity"] += c["quantity"]
            t["states"][c.get("state", "UNSTATED")] += c["quantity"]
    out = {}
    for cat, meta in view["categories"].items():
        t = totals.get(cat, {"quantity": 0.0, "components": [], "states": {}, "missing_value": []})
        out[cat] = {"category": cat, "quantity": t["quantity"], "components": list(t["components"]),
                    "by_state": dict(t["states"]), "components_without_value": list(t["missing_value"]),
                    "measurement_basis": meta["measurement_basis"],
                    "included_components": list(meta["included_components"]),
                    "excluded_components": list(meta.get("excluded_components", [])),
                    "overlap_policy": meta["overlap_policy"]}
    return {"view_id": view["view_id"], "categories": out, "unmapped_components": unmapped}


def comparability(meta_a, meta_b):
    """Compare two category descriptors (each: measurement_basis, included_components)."""
    if meta_a["measurement_basis"] == meta_b["measurement_basis"] and \
            set(meta_a["included_components"]) == set(meta_b["included_components"]):
        return DIRECT
    return NOT_COMPARABLE


def compare_values(a, b, status):
    """Difference and percentage - the percentage only when the basis matches."""
    if a is None or b is None:
        return {"difference": None, "difference_percent": None, "status": NOT_COMPARABLE, "why": "a side has no value"}
    if status == NOT_COMPARABLE:
        return {"difference": None, "difference_percent": None, "status": status,
                "why": "measurement basis differs - no difference or percentage reported"}
    d = a - b
    return {"difference": d, "difference_percent": None if not b else 100.0 * d / b, "status": status}


# ------------------------------------------------------------------ version stamps (pre-S4)
# Every footing-rebar comparison record names the engine state that produced each side. Two Urban values from
# different engine states are never compared as if they were one: the caller must declare a cross-state
# (regression) comparison, and a different drawing is never comparable.
STAMP_FIELDS = ("ENGINE_COMMIT", "REGISTER_VERSION", "DRAWING_SHA", "CALCULATION_ROUND")
SAME_ENGINE_STATE = "SAME_ENGINE_STATE"
CROSS_ENGINE_STATE = "CROSS_ENGINE_STATE"
DIFFERENT_DRAWING = "DIFFERENT_DRAWING"


def stamp(**fields) -> dict:
    """A comparison stamp; every field in STAMP_FIELDS is required and non-empty."""
    miss = [f for f in STAMP_FIELDS if not fields.get(f)]
    extra = sorted(set(fields) - set(STAMP_FIELDS))
    if miss or extra:
        raise ScopeError(f"stamp: missing {miss}, unknown {extra}")
    return {f: str(fields[f]) for f in STAMP_FIELDS}


def stamp_relation(a, b) -> str:
    a, b = stamp(**a), stamp(**b)
    if a["DRAWING_SHA"] != b["DRAWING_SHA"]:
        return DIFFERENT_DRAWING
    if any(a[f] != b[f] for f in ("ENGINE_COMMIT", "REGISTER_VERSION", "CALCULATION_ROUND")):
        return CROSS_ENGINE_STATE
    return SAME_ENGINE_STATE


def compare_stamped(a, b, status, *, stamp_a, stamp_b, cross_state=False):
    """compare_values() with both sides' stamps. A different drawing -> NOT_COMPARABLE. A cross-state pair (old
    Urban vs new Urban) is refused unless the caller declares cross_state=True, and then it is labelled."""
    rel = stamp_relation(stamp_a, stamp_b)
    if rel == DIFFERENT_DRAWING:
        out = {"difference": None, "difference_percent": None, "status": NOT_COMPARABLE,
               "why": "the two sides measured different drawings"}
    else:
        if rel == CROSS_ENGINE_STATE and not cross_state:
            raise ScopeError("the two sides come from different engine states "
                             f"({stamp_a.get('ENGINE_COMMIT')} / {stamp_b.get('ENGINE_COMMIT')}); declare "
                             "cross_state=True for a regression comparison")
        out = compare_values(a, b, status)
    out.update(engine_relation=rel, stamp_a=stamp(**stamp_a), stamp_b=stamp(**stamp_b))
    return out


def normalized_group(rows_by_category, group):
    """Sum a normalisation group's categories (e.g. BEAMS + SLABS) on one side; None if any member has no value."""
    vals = [rows_by_category.get(c) for c in group["categories"]]
    if any(v is None for v in vals):
        return None
    return sum(vals)


def schema():
    return {"schema": "COMPARISON_SCOPE_SCHEMA", "policy_id": POLICY_ID, "views": list(VIEWS),
            "results": list(RESULTS), "stamp_fields": list(STAMP_FIELDS),
            "engine_relations": [SAME_ENGINE_STATE, CROSS_ENGINE_STATE, DIFFERENT_DRAWING],
            "rules": ["production quantities are physical and granular; views never change them",
                      "every view category carries measurement basis, included / excluded components and overlap "
                      "policy",
                      "a component kind belongs to one category of a view",
                      "a percentage is reported only for a matching basis",
                      "allocation conventions that differ (beam gross vs downstand) are compared only through a "
                      "declared normalisation group",
                      "every stamped comparison names both engine states; a cross-state pair must be declared and a "
                      "different drawing is never comparable"]}
