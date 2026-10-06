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
