"""TRADE_DEPENDENCY_MATRIX - which evidence a trade quantity needs, and how a physical space that holds several
semantic zones blocks (or does not block) each trade.

    physical space -> semantic zone(s) -> trade measurement region -> quantity -> release (release_model_v2)

A trade is blocked by an unresolved semantic split ONLY when the zones it spans need different treatments for that
trade (porcelain vs wet tile; skirting vs none; internal vs external plaster; painted vs tiled wall). A trade whose
quantity is independent of the split is not blocked (e.g. ceiling area over DRY + WET zones of one indoor space).
No physical wall is ever invented to separate zones.

    family(trade, zone_class)                        -> the treatment family of one zone for one trade
    evaluate(trade, space)                           -> {components, blocking, applicable, rule}
    MATRIX                                           -> the matrix itself (published as a register)

space = {"upstream_status": room status, "semantic_state": SINGLE | MULTI_RESOLVED | MULTI_UNRESOLVED | UNLABELLED |
         CANDIDATE_LABEL, "zone_classes": [DRY | WET | SERVICE | EXTERNAL | VOID | UNKNOWN ...],
         "void_split_resolved": bool, "geometry": grade, "heights": grade or None}
Stdlib only, project-agnostic.
"""

from __future__ import annotations

from engine.source import release_model_v2 as R

POLICY_ID = "TRADE_DEPENDENCY_MATRIX_V1"
BLOCKED_SPLIT = "BLOCKED_SEMANTIC_TRADE_BOUNDARY"

# treatment family per zone class, per trade (None = the trade does not apply in that zone)
_FAMILY = {
    "FLOOR_FINISH": {"DRY": "DRY_FLOOR", "WET": "WET_TILE", "SERVICE": "WET_TILE", "EXTERNAL": "EXTERNAL_PAVING",
                     "VOID": None, "UNKNOWN": "UNKNOWN"},
    "SKIRTING": {"DRY": "SKIRTING", "WET": None, "SERVICE": None, "EXTERNAL": None, "VOID": None, "UNKNOWN": "UNKNOWN"},
    "CEILING": {"DRY": "INTERNAL_CEILING", "WET": "INTERNAL_CEILING", "SERVICE": "INTERNAL_CEILING",
                "EXTERNAL": "EXTERNAL_SOFFIT", "VOID": "INTERNAL_CEILING", "UNKNOWN": "INTERNAL_CEILING"},
    "PLASTER": {"DRY": "INTERNAL_PLASTER", "WET": "INTERNAL_PLASTER", "SERVICE": "INTERNAL_PLASTER",
                "EXTERNAL": "EXTERNAL_RENDER", "VOID": None, "UNKNOWN": "INTERNAL_PLASTER"},
    "PAINT": {"DRY": "PAINT", "WET": None, "SERVICE": None, "EXTERNAL": "EXTERNAL_PAINT", "VOID": None,
              "UNKNOWN": "UNKNOWN"},
    "WALL_TILE": {"DRY": None, "WET": "WET_WALL_TILE", "SERVICE": "WET_WALL_TILE", "EXTERNAL": None, "VOID": None,
                  "UNKNOWN": "UNKNOWN"},
    "WATERPROOFING": {"DRY": None, "WET": "WET_ROOM_WP", "SERVICE": "WET_ROOM_WP", "EXTERNAL": None, "VOID": None,
                      "UNKNOWN": "UNKNOWN"},
}
_FAMILY["SPATTER_DASH"] = _FAMILY["PLASTER"]
_FAMILY["CORNER_BEAD"] = _FAMILY["PLASTER"]
_FAMILY["CORNICE"] = _FAMILY["CEILING"]
_FAMILY["THRESHOLD"] = {k: "THRESHOLD" for k in _FAMILY["FLOOR_FINISH"]}

MATRIX = {
    "FLOOR_FINISH": {"requires": ["geometry", "upstream_status", "semantic_identity", "trade_region"],
                     "quantity_rule_dependency": False,
                     "note": "valid trade floor region; material is a specification attribute"},
    "SKIRTING": {"requires": ["geometry", "upstream_status", "semantic_identity", "trade_region"],
                 "quantity_rule_dependency": False, "note": "valid finish boundary path (dry zones only)"},
    "THRESHOLD": {"requires": ["geometry", "upstream_status"], "quantity_rule_dependency": False,
                  "note": "door strip between two closures; independent of room semantics"},
    "CEILING": {"requires": ["geometry", "upstream_status", "trade_region"], "quantity_rule_dependency": False,
                "note": "physical region allowed when indoor / external / void status is unambiguous"},
    "CORNICE": {"requires": ["geometry", "upstream_status", "trade_region", "rule_authority"],
                "quantity_rule_dependency": True, "note": "existence by specification"},
    "PLASTER": {"requires": ["geometry", "upstream_status", "trade_region", "dimension_height"],
                "quantity_rule_dependency": False, "note": "valid wall faces; internal vs external method"},
    "PAINT": {"requires": ["geometry", "upstream_status", "semantic_identity", "trade_region", "dimension_height",
                           "rule_authority"], "quantity_rule_dependency": True,
              "note": "painted (dry) vs tiled (wet) faces; height uses the Urban build-up rule"},
    "SPATTER_DASH": {"requires": ["geometry", "upstream_status", "trade_region", "rule_authority"],
                     "quantity_rule_dependency": True, "note": "coverage rule by owner"},
    "CORNER_BEAD": {"requires": ["geometry", "upstream_status", "trade_region", "rule_authority"],
                    "quantity_rule_dependency": True, "note": "coverage rule by owner"},
    "WALL_TILE": {"requires": ["geometry", "upstream_status", "semantic_identity", "trade_region", "dimension_height",
                               "rule_authority"], "quantity_rule_dependency": True,
                  "note": "wet semantic region + valid wall boundary; full-height tile is an Urban rule"},
    "WATERPROOFING": {"requires": ["geometry", "upstream_status", "semantic_identity", "trade_region",
                                   "rule_authority"], "quantity_rule_dependency": True,
                      "note": "wet semantic region + WP floor boundary; upturn height is an Urban rule"},
}


def family(trade, zone_class):
    return _FAMILY[trade].get(zone_class, "UNKNOWN")


def evaluate(trade, space) -> dict:
    """Evidence components for one trade in one physical space (feed release_model_v2.release_v2)."""
    if trade not in MATRIX:
        raise KeyError(trade)
    sem = space.get("semantic_state")
    classes = list(space.get("zone_classes") or [])
    if space.get("void_split_resolved"):
        classes = [c for c in classes if c != "VOID"]           # an established void outline resolves that split
    fams = {family(trade, c) for c in classes} or {family(trade, "UNKNOWN")}
    applicable_fams = {f for f in fams if f is not None}
    comps, blocking = {}, []
    comps["geometry"] = (space.get("geometry") or R.HIGH, "physical polygon")
    up = space.get("upstream_status")
    comps["upstream_status"] = ({"COMPUTED": R.HIGH, "COMPLETE": R.HIGH}.get(up, R.MEDIUM if up in (
        "COMPUTED_REVIEW", "REVIEW") else R.GRADE_BLOCKED), f"room status {up}")
    applicable = bool(applicable_fams)
    if sem == "MULTI_UNRESOLVED" and len(fams) > 1:
        comps["semantic_identity"] = (R.GRADE_BLOCKED, f"{BLOCKED_SPLIT}: zones need {sorted(map(str, fams))}")
        comps["trade_region"] = (R.GRADE_BLOCKED, f"{BLOCKED_SPLIT}: no source boundary between the zones")
        blocking.append(BLOCKED_SPLIT)
    elif sem == "MULTI_UNRESOLVED":
        comps["semantic_identity"] = (R.HIGH, "zones differ but share one treatment for this trade")
        comps["trade_region"] = (R.HIGH, "physical region = trade region for this trade")
    elif sem in ("UNLABELLED",):
        comps["semantic_identity"] = (R.MEDIUM, "unlabelled space: treatment family unknown")
        comps["trade_region"] = (R.HIGH, "physical region")
    elif sem == "CANDIDATE_LABEL":
        comps["semantic_identity"] = (R.MEDIUM, "name from candidate texts in the site (review)")
        comps["trade_region"] = (R.HIGH, "physical region")
    else:
        comps["semantic_identity"] = (R.HIGH, f"semantic state {sem}")
        comps["trade_region"] = (R.HIGH, "physical region")
    if "dimension_height" in MATRIX[trade]["requires"]:
        h = space.get("heights")
        comps["dimension_height"] = (h or R.HIGH, "wall heights per piece") if h != R.GRADE_BLOCKED else \
            (R.GRADE_BLOCKED, "wall height blocked")
    if "rule_authority" in MATRIX[trade]["requires"]:
        comps["rule_authority"] = (R.MEDIUM, "Urban standard / owner-pending rule fixes the quantity")
    comps = {k: v for k, v in comps.items() if k in MATRIX[trade]["requires"]}
    return {"trade": trade, "components": comps, "blocking": blocking, "applicable": applicable,
            "families": sorted(map(str, fams)), "quantity_rule_dependency": MATRIX[trade]["quantity_rule_dependency"],
            "rule": MATRIX[trade]["note"]}


def register() -> dict:
    return {"SCHEMA": "URBAN_TRADE_DEPENDENCY_MATRIX_V1", "policy": POLICY_ID, "matrix": MATRIX,
            "families": _FAMILY, "blocked_state": BLOCKED_SPLIT,
            "rule": "a trade is blocked by an unresolved semantic split only when its zones need different "
                    "treatments for that trade; no wall is invented to separate zones"}
