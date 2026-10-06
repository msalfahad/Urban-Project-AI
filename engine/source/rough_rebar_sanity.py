"""ROUGH REBAR SANITY ENGINE (generic).

A sanity / calibration check ONLY:   ROUGH_STEEL_KG = CONCRETE_M3 x ROUGH_RATIO_KG_PER_M3   (per category).

It never produces official reinforcement. The official hierarchy stays
    drawing / schedule / detail -> deterministic BBS -> actual kg -> procurement adjustment (separately).
Nothing here reads, writes or changes a BBS quantity: actual figures are only placed BESIDE the rough figure.

Rules
  * every concrete occurrence is classified into ONE structural element class, mapped explicitly to ONE rough category
    (an occurrence in two categories is an error - no double counting);
  * an element class with no mapping, or a category with no configured ratio, is ROUGH_RATIO_NOT_CONFIGURED - no guess;
  * concrete is carried by release state; the RELEASED basis (verified + lower bound) and the MODELLED basis
    (+ provisional) are reported separately; BLOCKED concrete never enters a rough estimate;
  * a whole-project kg/m3 is an INFORMATIONAL KPI only and is never used for production;
  * a rough-vs-actual gap is a VARIANCE, never "missing steel".

The ratios themselves are a PROFILE (owner rule, SANITY_CHECK_ONLY) supplied as data - none is written here.
Stdlib only.
"""

from __future__ import annotations

import copy
from collections import defaultdict

POLICY_ID = "ROUGH_REBAR_SANITY_V1"
FOOTER = ("Rough kg/m3 values are Urban estimating/sanity heuristics and are not a substitute for bar-by-bar "
          "reinforcement takeoff.")
NOT_CONFIGURED = "ROUGH_RATIO_NOT_CONFIGURED"
CONCRETE_STATES = ("VERIFIED", "LOWER_BOUND", "PROVISIONAL", "BLOCKED")
RELEASED_STATES = ("VERIFIED", "LOWER_BOUND")
MODELLED_STATES = ("VERIFIED", "LOWER_BOUND", "PROVISIONAL")

# structural usage groups (element classes)
ELEMENT_CLASSES = (
    "FOUNDATION_PAD", "COMBINED_FOOTING", "STRIP_FOOTING", "RAFT", "PILE_CAP", "FOUNDATION_NECK",
    "FOUNDATION_STRAP_BEAM",
    "GROUND_BEAM", "GROUND_SLAB", "BOUNDARY_GROUND_BEAM",
    "COLUMN", "STRUCTURAL_WALL",
    "BEAM", "CONTINUOUS_BEAM", "RING_BEAM", "LINTEL", "BEAM_COLUMN_JOINT",
    "SOLID_SLAB", "FLAT_SLAB", "RIBBED_SLAB",
    "STAIR", "DOME",
    "POOL_BASE", "POOL_WALL", "POOL_BEAM",
    "PARAPET_RC", "PARAPET_STIFFENER_COLUMN", "PARAPET_TOP_RING_BEAM",
    "LIFT_PIT", "LIFT_WALL", "LIFT_TIE_BEAM",
    "WATER_TANK", "SPECIAL_RC_ELEMENT",
    "PLAIN_CONCRETE",          # blinding / lean concrete: never reinforced, never in a rough category
)

# explicit default mapping element class -> rough category; a profile may replace it. Classes absent from the mapping
# (e.g. LINTEL, PARAPET_*, LIFT_*, WATER_TANK, SPECIAL_RC_ELEMENT) are deliberately NOT_CONFIGURED until an owner maps
# them; PLAIN_CONCRETE is excluded by design.
DEFAULT_MAPPING = {
    "FOUNDATION_PAD": "FOUNDATIONS_RELATED", "COMBINED_FOOTING": "FOUNDATIONS_RELATED",
    "STRIP_FOOTING": "FOUNDATIONS_RELATED", "RAFT": "FOUNDATIONS_RELATED", "PILE_CAP": "FOUNDATIONS_RELATED",
    "FOUNDATION_NECK": "FOUNDATIONS_RELATED", "FOUNDATION_STRAP_BEAM": "FOUNDATIONS_RELATED",
    "GROUND_BEAM": "GROUND_BEAMS_AND_GROUND_SLAB", "GROUND_SLAB": "GROUND_BEAMS_AND_GROUND_SLAB",
    "BOUNDARY_GROUND_BEAM": "GROUND_BEAMS_AND_GROUND_SLAB",
    "COLUMN": "WALLS_AND_COLUMNS", "STRUCTURAL_WALL": "WALLS_AND_COLUMNS",
    "BEAM_COLUMN_JOINT": "WALLS_AND_COLUMNS",      # column bars and ties run through the joint
    "BEAM": "BEAMS", "CONTINUOUS_BEAM": "BEAMS", "RING_BEAM": "BEAMS",
    "SOLID_SLAB": "SLABS", "FLAT_SLAB": "SLABS", "RIBBED_SLAB": "SLABS",
    "STAIR": "STAIRS_AND_DOME", "DOME": "STAIRS_AND_DOME",
    "POOL_BASE": "SWIMMING_POOL", "POOL_WALL": "SWIMMING_POOL", "POOL_BEAM": "SWIMMING_POOL",
}
EXCLUDED_CLASSES = ("PLAIN_CONCRETE",)

# keyword classifier (used only when the occurrence carries no explicit element_class)
_KEYWORDS = (
    ("PLAIN_CONCRETE", ("BLINDING", "PLAIN CONCRETE", "LEAN CONCRETE")),
    ("FOUNDATION_STRAP_BEAM", ("STRAP",)), ("FOUNDATION_NECK", ("NECK", "PEDESTAL")),
    ("COMBINED_FOOTING", ("COMBINED FOOTING",)), ("STRIP_FOOTING", ("STRIP FOOTING",)), ("RAFT", ("RAFT",)),
    ("PILE_CAP", ("PILE CAP",)), ("FOUNDATION_PAD", ("ISOLATED FOOTING", "FOOTING", "PAD")),
    ("BOUNDARY_GROUND_BEAM", ("BOUNDARY WALL BEAM", "BOUNDARY GROUND BEAM")),
    ("GROUND_BEAM", ("GROUND BEAM",)), ("GROUND_SLAB", ("GROUND SLAB", "SLAB ON GRADE")),
    ("POOL_BASE", ("POOL BASE",)), ("POOL_WALL", ("POOL WALL", "SWIMMING POOL")),
    ("LIFT_PIT", ("LIFT PIT",)), ("LIFT_TIE_BEAM", ("LIFT TIE",)), ("LIFT_WALL", ("LIFT WALL", "LIFT SHAFT")),
    ("PARAPET_STIFFENER_COLUMN", ("PARAPET STIFFENER", "PARAPET COLUMN")),
    ("PARAPET_TOP_RING_BEAM", ("PARAPET RING", "PARAPET TOP")), ("PARAPET_RC", ("PARAPET",)),
    ("DOME", ("DOME",)), ("STAIR", ("STAIR",)), ("LINTEL", ("LINTEL",)), ("RING_BEAM", ("RING BEAM",)),
    ("BEAM_COLUMN_JOINT", ("JOINT",)), ("CONTINUOUS_BEAM", ("CONTINUOUS BEAM",)), ("BEAM", ("BEAM", "DOWNSTAND")),
    ("STRUCTURAL_WALL", ("STRUCTURAL WALL", "SHEAR WALL", "RC WALL")), ("COLUMN", ("COLUMN",)),
    ("RIBBED_SLAB", ("RIBBED", "HORDI")), ("FLAT_SLAB", ("FLAT SLAB",)), ("SOLID_SLAB", ("SLAB",)),
    ("WATER_TANK", ("WATER TANK", "TANK")),
)


class RoughRebarError(ValueError):
    pass


def classify(occ):
    """Element class of one concrete occurrence: its explicit `element_class` if given (validated), else the keyword
    classifier over `description`. Returns (class, basis); (None, 'UNCLASSIFIED') when nothing matches."""
    ec = occ.get("element_class")
    if ec:
        if ec not in ELEMENT_CLASSES:
            raise RoughRebarError(f"unknown element class {ec}")
        return ec, "EXPLICIT"
    text = " ".join(str(occ.get(k) or "") for k in ("description", "family", "kind")).upper()
    for cls, words in _KEYWORDS:
        if any(w in text for w in words):
            return cls, "KEYWORD"
    return None, "UNCLASSIFIED"


def validate_profile(profile):
    """A rough profile: {profile_id, authority: URBAN_OWNER_RULE, use: SANITY_CHECK_ONLY, ratios_kg_per_m3: {cat:
    int}, mapping (optional)}. Ratios must be positive integers; authority and use are mandatory."""
    if profile.get("authority") != "URBAN_OWNER_RULE" or profile.get("use") != "SANITY_CHECK_ONLY":
        raise RoughRebarError("rough profile must be URBAN_OWNER_RULE / SANITY_CHECK_ONLY")
    for cat, v in (profile.get("ratios_kg_per_m3") or {}).items():
        if not isinstance(v, int) or isinstance(v, bool) or v <= 0:
            raise RoughRebarError(f"ratio for {cat} must be a positive integer kg/m3")
    mapping = profile.get("mapping") or DEFAULT_MAPPING
    for ec, cat in mapping.items():
        if ec not in ELEMENT_CLASSES:
            raise RoughRebarError(f"mapping uses unknown element class {ec}")
        if ec in EXCLUDED_CLASSES:
            raise RoughRebarError(f"{ec} cannot be mapped to a rough category")
    return profile


def ratio_for(category, profile):
    r = (profile.get("ratios_kg_per_m3") or {}).get(category)
    return (r, "CONFIGURED") if r else (None, NOT_CONFIGURED)


def rough_check(occurrences, profile, actual=None):
    """occurrences: [{occurrence_id, element_class? | description, concrete_m3, concrete_state}].
    actual: {category: {released_kg, provisional_kg, blocked_components, complete: bool}} - read only.
    Returns {categories, unassigned, excluded, footer}."""
    validate_profile(profile)
    mapping = profile.get("mapping") or DEFAULT_MAPPING
    seen = {}
    cats = defaultdict(lambda: {s: 0.0 for s in CONCRETE_STATES} | {"occurrences": []})
    unassigned, excluded = [], []
    for o in occurrences:
        oid = o["occurrence_id"]
        if oid in seen:
            raise RoughRebarError(f"occurrence {oid} entered twice (double counting)")
        ec, basis = classify(o)
        st = o.get("concrete_state")
        if st not in CONCRETE_STATES:
            raise RoughRebarError(f"{oid}: concrete_state must be one of {CONCRETE_STATES}")
        if ec in EXCLUDED_CLASSES:
            excluded.append({"occurrence_id": oid, "element_class": ec, "why": "plain concrete is not reinforced"})
            seen[oid] = None
            continue
        cat = mapping.get(ec) if ec else None
        if cat is None:
            unassigned.append({"occurrence_id": oid, "element_class": ec, "classifier_basis": basis,
                               "state": NOT_CONFIGURED, "concrete_m3": o.get("concrete_m3"), "concrete_state": st})
            seen[oid] = None
            continue
        seen[oid] = cat
        if o.get("concrete_m3") is not None:
            cats[cat][st] += o["concrete_m3"]
        cats[cat]["occurrences"].append(oid)
    out = {}
    for cat, c in sorted(cats.items()):
        r, rs = ratio_for(cat, profile)
        rel = sum(c[s] for s in RELEASED_STATES)
        mod = sum(c[s] for s in MODELLED_STATES)
        row = {"category": cat, "ratio_kg_per_m3": r, "ratio_state": rs,
               "verified_concrete_m3": c["VERIFIED"], "lower_bound_concrete_m3": c["LOWER_BOUND"],
               "provisional_concrete_m3": c["PROVISIONAL"], "blocked_concrete_m3": c["BLOCKED"],
               "released_concrete_m3": rel, "modelled_concrete_m3": mod,
               "rough_reference_kg_released_basis": None if r is None else rel * r,
               "rough_reference_kg_modelled_basis": None if r is None else mod * r,
               "occurrences": len(c["occurrences"]), "use": "SANITY_CHECK_ONLY"}
        a = copy.deepcopy((actual or {}).get(cat))
        if a is not None:
            row["actual_released_kg"] = a.get("released_kg")
            row["actual_provisional_kg"] = a.get("provisional_kg")
            row["actual_blocked_components"] = a.get("blocked_components", [])
            row["actual_complete"] = bool(a.get("complete"))
            if row["actual_complete"] and r is not None and a.get("released_kg") is not None:
                ref = row["rough_reference_kg_modelled_basis"]
                row["actual_bbs_kg"] = a["released_kg"]
                row["delta_kg"] = a["released_kg"] - ref
                row["delta_percent"] = None if not ref else 100.0 * row["delta_kg"] / ref
                row["comparison_state"] = "BBS_COMPLETE_VARIANCE"
            else:
                row["comparison_state"] = "BBS_INCOMPLETE_SIDE_BY_SIDE"      # never "missing steel"
        out[cat] = row
    return {"policy_id": POLICY_ID, "profile_id": profile.get("profile_id"), "categories": out,
            "unassigned": unassigned, "excluded": excluded, "footer": FOOTER}


def project_intensity_kpi(total_steel_kg, total_concrete_m3):
    """Whole-project kg/m3 - INFORMATIONAL only, never a production or rough-estimation basis."""
    return {"kg_per_m3": None if not total_concrete_m3 else total_steel_kg / total_concrete_m3,
            "use": "INFORMATIONAL_KPI_NOT_FOR_PRODUCTION",
            "why": "steel intensity is category-specific; one villa-wide ratio is never applied"}


def summary_rows(result):
    """Rows for a BOQ summary: actual and rough are separate columns, never combined."""
    rows = []
    for cat, r in result["categories"].items():
        rows.append({"CATEGORY": cat, "CONCRETE_M3_RELEASED": r["released_concrete_m3"],
                     "CONCRETE_M3_MODELLED": r["modelled_concrete_m3"], "ROUGH_KG_PER_M3": r["ratio_kg_per_m3"],
                     "ROUGH_REBAR_KG_MODELLED": r["rough_reference_kg_modelled_basis"],
                     "ACTUAL_RELEASED_KG": r.get("actual_released_kg"),
                     "ACTUAL_PROJECTED_KG": None if r.get("actual_released_kg") is None else
                     (r.get("actual_released_kg") or 0) + (r.get("actual_provisional_kg") or 0),
                     "VARIANCE_KG": r.get("delta_kg"), "STATE": r.get("comparison_state", "NO_ACTUAL")})
    return {"rows": rows, "footer": result["footer"]}


def schema():
    return {"schema": "ROUGH_REBAR_SANITY_SCHEMA", "policy_id": POLICY_ID, "element_classes": list(ELEMENT_CLASSES),
            "default_mapping": DEFAULT_MAPPING, "excluded_classes": list(EXCLUDED_CLASSES),
            "concrete_states": list(CONCRETE_STATES), "footer": FOOTER,
            "rules": ["rough = concrete x category ratio; sanity only",
                      "one occurrence -> one element class -> one category; never two",
                      "unmapped class / unconfigured ratio -> ROUGH_RATIO_NOT_CONFIGURED (no guess)",
                      "released basis (verified + lower bound) and modelled basis (+ provisional) kept apart",
                      "blocked concrete never enters a rough figure",
                      "actual BBS is read only and shown beside the rough figure",
                      "whole-project kg/m3 is an informational KPI only"]}
