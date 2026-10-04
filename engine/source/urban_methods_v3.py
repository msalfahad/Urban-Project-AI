"""URBAN METHOD REGISTER V3 - methods adopted by owner decision OD-V3 (Mohammad, Alsenan final BOQ round), added to the
V1 register (urban_methods, frozen) without changing it.

Authority order for every quantity input (highest first):
    SOURCE / DETAIL  >  PROJECT_OWNER_FACT  >  URBAN_FALLBACK (this register)  >  BLOCKED
A fallback is never labelled SOURCE, never used where the source contradicts it, and every value it supplies says so.

Methods are versioned, scope-limited and overrideable per project / floor (resolve(..., project_override)).
Project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib
import json

from . import urban_methods as UM1

SOURCE, PROJECT_OWNER_FACT, URBAN_FALLBACK, BLOCKED = "SOURCE", "PROJECT_OWNER_FACT", "URBAN_FALLBACK", "BLOCKED"
AUTHORITY_ORDER = (SOURCE, PROJECT_OWNER_FACT, URBAN_FALLBACK, BLOCKED)
BY_SPEC, UNRESOLVED_MATERIAL = "BY_SPEC", "UNRESOLVED"

METHODS = {
    "URBAN-RESIDENTIAL-FLOOR-BUILDUP-FALLBACK@v1": {
        "statement": "residential floor build-up (screed + finish) = 0.10 m when neither the source / detail nor a "
                     "project owner fact establishes it; labelled URBAN_FALLBACK, never SOURCE; not used where the "
                     "source contradicts it; overrideable per project and per floor",
        "applies_to": ["RESIDENTIAL_FLOOR"], "never_applies_to": ["ROOF", "WET_ROOM_FALL_ZONE_SOURCED", "STAIR"],
        "parameters": {"buildup_m": 0.10}, "precedence": [SOURCE, PROJECT_OWNER_FACT], "decision": "OD-V3-1"},
    "URBAN-FINISH-QUANTITY-INDEPENDENT-OF-MATERIAL@v1": {
        "statement": "a defensible measured geometry (floor, ceiling, wall face, skirting path ...) is released even "
                     "when the finish material is not source-proven; MEASURED GEOMETRY and MATERIAL AUTHORITY are kept "
                     "apart; material = SOURCE / URBAN METHOD / BY_SPEC (unresolved) - an unknown material never "
                     "blocks the area", "applies_to": ["FINISH_QUANTITY"], "never_applies_to": [],
        "parameters": {"material_when_unknown": BY_SPEC}, "precedence": [SOURCE, PROJECT_OWNER_FACT],
        "decision": "OD-V3-2"},
    "URBAN-DRY-FLOOR-PORCELAIN-DEFAULT@v1": {
        "statement": "dry internal floors: porcelain unless the project specification overrides",
        "applies_to": ["DRY_ROOM_FLOOR"], "never_applies_to": ["WET_ROOM_FLOOR", "EXTERNAL", "ROOF", "STAIR"],
        "parameters": {"material": "PORCELAIN"}, "precedence": ["PROJECT_SPECIFICATION"], "decision": "OD-V3-2"},
    "URBAN-WET-FLOOR-TILED@v1": {
        "statement": "wet / service room floors: tiled finish (tile type by specification)",
        "applies_to": ["WET_ROOM_FLOOR", "SERVICE_ROOM_FLOOR"], "never_applies_to": ["DRY_ROOM_FLOOR"],
        "parameters": {"material": "TILE (type BY_SPEC)"}, "precedence": ["PROJECT_SPECIFICATION"],
        "decision": "OD-V3-2"},
    "URBAN-NO-SKIRTING-FULL-TILE-WET@v1": {
        "statement": "no normal skirting in wet / service rooms with full-height wall tile",
        "applies_to": ["WET_ROOM", "SERVICE_ROOM"], "never_applies_to": ["DRY_ROOM"], "parameters": {},
        "precedence": ["PROJECT_SPECIFICATION"], "decision": "OD-V3-2"},
    "URBAN-CEILING-QUANTITY-WITHOUT-MATERIAL@v1": {
        "statement": "physical / visible ceiling area is calculated independently; no ceiling is assumed gypsum unless "
                     "a source / project fact / versioned ceiling-finish method authorises it - otherwise MATERIAL = "
                     "BY_SPEC / UNRESOLVED and the area is still published", "applies_to": ["CEILING"],
        "never_applies_to": ["VOID", "DOUBLE_HEIGHT_OPEN_ZONE"], "parameters": {"material": BY_SPEC},
        "precedence": [SOURCE, PROJECT_OWNER_FACT], "decision": "OD-V3-2"},
    "URBAN-REBAR-NET-AND-PROCUREMENT@v1": {
        "statement": "rebar weight = sum(count x length x kg/m) per bar set; NET_DESIGN_WEIGHT uses only bars the source "
                     "/ detail supports (cover and laps from the structural notes); PROCUREMENT_WEIGHT_INCL_LAPS adds "
                     "laps where a continuous bar exceeds the 12 m stock length, splicing is permitted and no detail "
                     "contradicts it; hooks / bends / stirrup closing only from an explicit detail, the structural "
                     "notes or an adopted detailing standard - otherwise BLOCKED_DETAILING; never kg/m3",
        "applies_to": ["REBAR"], "never_applies_to": [], "parameters": {"stock_length_m": 12.0},
        "precedence": [SOURCE, PROJECT_OWNER_FACT], "decision": "OD-V3-3"},
    "URBAN-FINISH-EXTRAS-SEPARATE-ITEMS@v1": {
        "statement": "gypsum / decor area (m2), cornice (lm), cove light / cove profile (lm), plaster corner beads / "
                     "profiles (lm), spatter dash (m2), door reveals (m2), window reveals (m2) and other finish "
                     "profiles (lm) are separate BOQ items wherever source geometry supports them - never buried in "
                     "plaster, paint or wall tile; opening deduction and reveal addition stay separate calculations",
        "applies_to": ["FINISH_EXTRA"], "never_applies_to": [], "parameters": {},
        "precedence": [SOURCE, PROJECT_OWNER_FACT], "decision": "OD-V3-4"},
}

ALL_METHODS = {**UM1.METHODS, **METHODS}


def applies(method_id, element_kind) -> bool:
    m = ALL_METHODS[method_id]
    if element_kind in m["never_applies_to"]:
        return False
    return element_kind in m["applies_to"]


def resolve(method_id, project_override=None) -> dict:
    m = ALL_METHODS[method_id]
    params = dict(m["parameters"])
    auth = URBAN_FALLBACK if method_id in METHODS else method_id
    if project_override:
        params.update(project_override.get("parameters", {}))
        auth = f"{PROJECT_OWNER_FACT} {project_override.get('id')} over {method_id}"
    return {"method": method_id, "parameters": params, "authority": auth}


def pick(candidates) -> dict:
    """The highest-authority candidate [{"authority": ..., "value": ...}]; BLOCKED when none has a value.
    A fallback is refused when a SOURCE value exists that contradicts it (the source simply wins)."""
    ranked = sorted((c for c in candidates if c.get("value") is not None),
                    key=lambda c: AUTHORITY_ORDER.index(c["authority"]))
    if not ranked:
        return {"authority": BLOCKED, "value": None}
    return dict(ranked[0], overridden=[c for c in ranked[1:]])


def register() -> dict:
    rows = [dict({"id": k}, **v) for k, v in sorted(METHODS.items())]
    rec = {"SCHEMA": "URBAN_METHOD_REGISTER_V3", "extends": "URBAN_METHOD_REGISTER_V1 (urban_methods, unchanged)",
           "authority_order": list(AUTHORITY_ORDER), "methods": rows, "v1_methods": sorted(UM1.METHODS),
           "rule": "a method is versioned, scope-limited and overrideable; it is never a project fact; a fallback is "
                   "never labelled SOURCE"}
    rec["digest"] = hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()
    return rec
