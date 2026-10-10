"""ACCURATE_BOQ_REBAR - the official reinforcement takeoff (generic).

Quantities come only from drawing occurrences, schedules, structural details, deterministic geometry, approved
project claims and explicitly identified approved engineering methods, computed bar-by-bar / component-by-component
by the trade engines (column_rebar, rebar_model, slab_rebar_binding, ...). This module only collects their parts,
checks them and states what has been established:

  * every part carries one of the five states VERIFIED / LOWER_BOUND / PROVISIONAL / BLOCKED_MODELLED /
    BLOCKED_UNQUANTIFIED, and the states are never merged into one figure;
  * every part names its basis; a basis outside the admissible set (a per-volume ratio, a reference QS figure, an
    external oracle figure) is refused - an incomplete quantity stays incomplete;
  * official status per category: FINAL / LOWER_BOUND / PARTIAL / BLOCKED; the project is FINAL only when every
    category is FINAL, otherwise FINAL_REBAR_NOT_ESTABLISHED.

This module has no estimating input of any kind and imports nothing from the estimating side (dependency test:
tests/structural_comparison_engine/test_rebar_product_firewall.py, declarations in rebar_product_registry.py). Stdlib only.
"""

from __future__ import annotations

import copy
from collections import defaultdict

PRODUCT = "ACCURATE_BOQ_REBAR"
TITLE_EN = "ACCURATE BOQ REBAR"
TITLE_AR = "حديد التسليح الفعلي من المخططات"

VERIFIED, LOWER_BOUND, PROVISIONAL = "VERIFIED", "LOWER_BOUND", "PROVISIONAL"
BLOCKED_MODELLED, BLOCKED_UNQUANTIFIED = "BLOCKED_MODELLED", "BLOCKED_UNQUANTIFIED"
STATES = (VERIFIED, LOWER_BOUND, PROVISIONAL, BLOCKED_MODELLED, BLOCKED_UNQUANTIFIED)
RELEASED_STATES = (VERIFIED, LOWER_BOUND)

FINAL, PARTIAL, BLOCKED = "FINAL", "PARTIAL", "BLOCKED"
OFFICIAL_STATUSES = (FINAL, LOWER_BOUND, PARTIAL, BLOCKED)
FINAL_REBAR_NOT_ESTABLISHED = "FINAL_REBAR_NOT_ESTABLISHED"

ADMISSIBLE_BASES = ("DRAWING_OCCURRENCE", "SCHEDULE", "STRUCTURAL_DETAIL", "DETERMINISTIC_GEOMETRY",
                    "APPROVED_PROJECT_CLAIM", "APPROVED_ENGINEERING_METHOD")

CATEGORIES = ("FOUNDATIONS", "GROUND_BEAMS", "GROUND_SLAB", "COLUMNS", "WALLS", "BEAMS", "SLABS", "STAIRS", "DOME",
              "POOL", "LIFT", "PARAPET", "SPECIAL_RC")

COMPONENTS = (
    "FOOTING_BOTTOM_SHORT", "FOOTING_BOTTOM_LONG", "FOOTING_TOP_SHORT", "FOOTING_TOP_LONG", "BOXED_REBAR",
    "FOOTING_SIDE_BAR", "NECK_MAIN_BAR", "NECK_TIE", "STRAP_BEAM_BAR", "STRAP_BEAM_STIRRUP",
    "COLUMN_MAIN_BAR", "COLUMN_TIE", "COLUMN_SECTION_TRANSITION", "COLUMN_OTHER_DETAIL",
    "LAP", "STARTER", "ANCHORAGE",
    "BEAM_BOTTOM_BAR", "BEAM_TOP_BAR", "BEAM_EXTRA_BAR", "BEAM_SIDE_BAR", "BEAM_STIRRUP",
    "SLAB_BOTTOM_X", "SLAB_BOTTOM_Y", "SLAB_TOP_SUPPORT", "SLAB_TOP_X", "SLAB_TOP_Y", "SLAB_EDGE_BAR",
    "SLAB_OPENING_TRIMMER", "TEMPERATURE_BAR",
    "WALL_VERTICAL", "WALL_HORIZONTAL", "STAIR_MAIN_BAR", "STAIR_DISTRIBUTION_BAR", "DOME_MERIDIONAL",
    "DOME_HOOP", "RING_BEAM_BAR", "POOL_WALL_BAR", "POOL_BASE_BAR", "SPECIAL_DETAIL_BAR",
)

# column_rebar component -> accurate component (the column engine's own registers keep the detail)
COLUMN_COMPONENT_MAP = {"MAIN_BARS": "COLUMN_MAIN_BAR", "TIES": "COLUMN_TIE", "LAP": "LAP", "STARTER": "STARTER",
                        "ANCHORAGE": "ANCHORAGE", "OTHER_EXTRA": "COLUMN_OTHER_DETAIL"}
COLUMN_BASIS = ("DRAWING_OCCURRENCE", "SCHEDULE", "STRUCTURAL_DETAIL", "DETERMINISTIC_GEOMETRY",
                "APPROVED_PROJECT_CLAIM")


class AccurateRebarError(ValueError):
    pass


def validate_part(p):
    """One accurate part: {part_id, category, component, state, kg, basis: [..], source_refs?}."""
    pid = p.get("part_id")
    if not pid:
        raise AccurateRebarError("part without part_id")
    if p.get("category") not in CATEGORIES:
        raise AccurateRebarError(f"{pid}: category {p.get('category')} is not an accurate category")
    if p.get("component") not in COMPONENTS:
        raise AccurateRebarError(f"{pid}: component {p.get('component')} is not a registered component")
    st = p.get("state")
    if st not in STATES:
        raise AccurateRebarError(f"{pid}: state must be one of {STATES}")
    kg = p.get("kg")
    if st == BLOCKED_UNQUANTIFIED:
        if kg is not None:
            raise AccurateRebarError(f"{pid}: a BLOCKED_UNQUANTIFIED part carries no kg")
    elif kg is None or isinstance(kg, bool) or not isinstance(kg, (int, float)) or kg < 0:
        raise AccurateRebarError(f"{pid}: {st} needs a non-negative kg")
    basis = p.get("basis") or ()
    if not basis:
        raise AccurateRebarError(f"{pid}: no basis - an accurate quantity must name its source basis")
    bad = [b for b in basis if b not in ADMISSIBLE_BASES]
    if bad:
        raise AccurateRebarError(f"{pid}: inadmissible basis {bad} - accurate rebar comes only from {ADMISSIBLE_BASES}")
    return p


def official_status(row):
    """FINAL: everything verified. LOWER_BOUND: released only, some of it a lower bound. PARTIAL: something released
    and / or provisional parts with something still open. BLOCKED: nothing released and nothing provisional."""
    open_parts = row["provisional_parts"] > 0 or row["blocked_modelled_parts"] > 0 \
        or row["blocked_unquantified_parts"] > 0
    if row["released_parts"] == 0 and row["provisional_parts"] == 0:
        return BLOCKED
    if open_parts:
        return PARTIAL
    if row["lower_bound_parts"] > 0:
        return LOWER_BOUND
    return FINAL


def summarise(parts):
    """Category and project rows; the five states stay in separate columns and no 'final' total is formed unless
    every category is FINAL. Inputs are not modified."""
    parts = copy.deepcopy(list(parts))
    seen = set()
    rows = defaultdict(lambda: {"verified_kg": 0.0, "lower_bound_kg": 0.0, "provisional_kg": 0.0,
                                "blocked_modelled_kg": 0.0, "blocked_unquantified_parts": 0, "released_parts": 0,
                                "lower_bound_parts": 0, "provisional_parts": 0, "blocked_modelled_parts": 0,
                                "components": defaultdict(lambda: defaultdict(float))})
    for p in parts:
        validate_part(p)
        if p["part_id"] in seen:
            raise AccurateRebarError(f"part {p['part_id']} entered twice")
        seen.add(p["part_id"])
        r = rows[p["category"]]
        st = p["state"]
        if st == BLOCKED_UNQUANTIFIED:
            r["blocked_unquantified_parts"] += 1
            r["components"][p["component"]][st] += 1
            continue
        key = {VERIFIED: "verified_kg", LOWER_BOUND: "lower_bound_kg", PROVISIONAL: "provisional_kg",
               BLOCKED_MODELLED: "blocked_modelled_kg"}[st]
        r[key] += p["kg"]
        r["components"][p["component"]][st] += p["kg"]
        if st in RELEASED_STATES:
            r["released_parts"] += 1
        if st == LOWER_BOUND:
            r["lower_bound_parts"] += 1
        if st == PROVISIONAL:
            r["provisional_parts"] += 1
        if st == BLOCKED_MODELLED:
            r["blocked_modelled_parts"] += 1
    cats = {}
    for c in CATEGORIES:
        if c not in rows:
            continue
        r = rows[c]
        out = {k: v for k, v in r.items() if k != "components"}
        out["category"] = c
        out["released_kg"] = r["verified_kg"] + r["lower_bound_kg"]
        out["projected_kg"] = out["released_kg"] + r["provisional_kg"]       # released + provisional, never blocked
        out["components"] = {k: dict(v) for k, v in sorted(r["components"].items())}
        out["official_status"] = official_status(out)
        cats[c] = out
    proj = {k: sum(r[k] for r in cats.values()) for k in
            ("verified_kg", "lower_bound_kg", "provisional_kg", "blocked_modelled_kg", "blocked_unquantified_parts",
             "released_kg", "projected_kg")}
    final = bool(cats) and all(r["official_status"] == FINAL for r in cats.values())
    proj["final_rebar"] = FINAL if final else FINAL_REBAR_NOT_ESTABLISHED
    proj["final_rebar_kg"] = proj["verified_kg"] if final else None
    return {"product": PRODUCT, "categories": cats, "project": proj, "states": list(STATES),
            "rule": "states are never merged; an incomplete quantity is never completed by an estimate"}


# ------------------------------------------------------------------ S4 provenance contract (pre-S4 hardening)
# Every Accurate Footing Rebar (S4) part carries part["provenance"] with these fields from its first
# implementation. This extends the accurate part; it is not a second receipt system: the run-manifest digests stay
# where they are, and ENGINE_COMMIT / REGISTER_VERSION / CALCULATION_ROUND are the same stamp the comparison
# layer checks (comparison_scope.STAMP_FIELDS).
S4_PROVENANCE_FIELDS = (
    "PROJECT_ID", "DRAWING_ID", "DRAWING_SHA", "REVISION", "SHEET_REGION", "SOURCE_HANDLES", "SOURCE_TEXT",
    "FOOTING_OCCURRENCE_ID", "FOOTING_MARK", "COMPONENT", "RULE_ID", "CONVENTION_ID", "MEASUREMENT_STATE",
    "AUTHORITY_STATE", "RELEASE_STATE", "FORMULA", "INPUTS", "ENGINE_COMMIT", "REGISTER_VERSION",
    "CALCULATION_ROUND",
)
S4_BOUND_FIELDS = ("LOW", "BEST", "HIGH", "UNQUANTIFIED_COMPONENTS")
MEASUREMENT_STATES = ("MEASURED", "SCHEDULE_DERIVED", "CONVENTION_DERIVED", "NOT_MEASURED")
# authority of the semantics behind a part; only the first four may stand behind a released (or modelled) kg
RELEASING_AUTHORITIES = ("SOURCE_EXPLICIT", "SOURCE_DERIVED_HIGH_CONFIDENCE", "APPROVED_PROJECT_CLAIM",
                         "APPROVED_ENGINEERING_METHOD")
PROVISIONAL_AUTHORITIES = ("UNAPPROVED_METHOD",)
NON_QUANTIFYING_AUTHORITIES = ("PROJECT_PATTERN_ONLY", "GENERIC_HYPOTHESIS", "UNRESOLVED", "SOURCE_CONFLICT")
AUTHORITY_STATES = RELEASING_AUTHORITIES + PROVISIONAL_AUTHORITIES + NON_QUANTIFYING_AUTHORITIES
_SHA = __import__("re").compile(r"^[0-9a-f]{64}$")


def validate_s4_part(p):
    """validate_part + the S4 provenance contract. Raises AccurateRebarError naming the first defect."""
    validate_part(p)
    pid = p["part_id"]
    pv = p.get("provenance")
    if not isinstance(pv, dict):
        raise AccurateRebarError(f"{pid}: an S4 part carries a provenance record")
    # INPUTS may be an empty mapping on a blocked part (nothing was computed); every other field is non-empty
    missing = [f for f in S4_PROVENANCE_FIELDS if f not in pv or pv[f] is None or (pv[f] in ("", [], ())
                                                                                    and f != "INPUTS")]
    if missing:
        raise AccurateRebarError(f"{pid}: S4 provenance missing {missing}")
    if not _SHA.match(str(pv["DRAWING_SHA"])):
        raise AccurateRebarError(f"{pid}: DRAWING_SHA must be a sha256 hex digest")
    if not isinstance(pv["SOURCE_HANDLES"], (list, tuple)) or not all(isinstance(h, str) and h
                                                                       for h in pv["SOURCE_HANDLES"]):
        raise AccurateRebarError(f"{pid}: SOURCE_HANDLES is a non-empty list of handles")
    if not isinstance(pv["INPUTS"], dict):
        raise AccurateRebarError(f"{pid}: INPUTS is a mapping of named inputs")
    if pv["COMPONENT"] != p["component"]:
        raise AccurateRebarError(f"{pid}: provenance COMPONENT {pv['COMPONENT']} != part component {p['component']}")
    if pv["RELEASE_STATE"] != p["state"]:
        raise AccurateRebarError(f"{pid}: provenance RELEASE_STATE {pv['RELEASE_STATE']} != part state {p['state']}")
    if pv["MEASUREMENT_STATE"] not in MEASUREMENT_STATES:
        raise AccurateRebarError(f"{pid}: MEASUREMENT_STATE must be one of {MEASUREMENT_STATES}")
    auth = pv["AUTHORITY_STATE"]
    if auth not in AUTHORITY_STATES:
        raise AccurateRebarError(f"{pid}: AUTHORITY_STATE must be one of {AUTHORITY_STATES}")
    if auth in NON_QUANTIFYING_AUTHORITIES and p["state"] != BLOCKED_UNQUANTIFIED:
        raise AccurateRebarError(f"{pid}: authority {auth} never carries a quantity - the part is "
                                 f"BLOCKED_UNQUANTIFIED, not {p['state']}")
    if auth in PROVISIONAL_AUTHORITIES and p["state"] in RELEASED_STATES:
        raise AccurateRebarError(f"{pid}: authority {auth} cannot release a quantity ({p['state']})")
    if p["state"] == BLOCKED_UNQUANTIFIED and not pv.get("BLOCKING_REASON"):
        raise AccurateRebarError(f"{pid}: a BLOCKED_UNQUANTIFIED part names its BLOCKING_REASON")
    bounds = [f for f in S4_BOUND_FIELDS if f in pv]
    if bounds:
        if len(bounds) != len(S4_BOUND_FIELDS):
            raise AccurateRebarError(f"{pid}: bounds come as the set {S4_BOUND_FIELDS}, got {bounds}")
        lo, best, hi = pv["LOW"], pv["BEST"], pv["HIGH"]
        if lo is None or best is None:
            raise AccurateRebarError(f"{pid}: LOW and BEST are numbers (HIGH may be None = unbounded above)")
        if not (lo <= best and (hi is None or best <= hi)):
            raise AccurateRebarError(f"{pid}: bounds must satisfy LOW <= BEST <= HIGH")
        unq = pv["UNQUANTIFIED_COMPONENTS"]
        if not isinstance(unq, (list, tuple)) or any(c not in COMPONENTS for c in unq):
            raise AccurateRebarError(f"{pid}: UNQUANTIFIED_COMPONENTS lists registered components")
    elif p["state"] == LOWER_BOUND:
        raise AccurateRebarError(f"{pid}: a LOWER_BOUND part states its bounds {S4_BOUND_FIELDS}")
    return p


def summarise_s4(parts):
    """summarise() for S4 parts: every part must satisfy the provenance contract first."""
    parts = list(parts)
    for p in parts:
        validate_s4_part(p)
    return summarise(parts)


def from_column_rebar(parts):
    """Accurate parts from column_rebar parts ({part_id, component, release_state, kg}); data only, no import."""
    out = []
    for p in parts:
        st = p["release_state"]
        if st == "BLOCKED":
            st = BLOCKED_UNQUANTIFIED if p["kg"] is None else BLOCKED_MODELLED
        elif st not in (VERIFIED, LOWER_BOUND, PROVISIONAL):
            raise AccurateRebarError(f"{p['part_id']}: unknown column release state {st}")
        out.append({"part_id": p["part_id"], "category": "COLUMNS", "component": COLUMN_COMPONENT_MAP[p["component"]],
                    "state": st, "kg": p["kg"], "basis": list(COLUMN_BASIS),
                    "source_refs": [f"column_rebar:{p['part_id']}"]})
    return out
