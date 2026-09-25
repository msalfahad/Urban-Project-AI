"""MATERIAL-ROLE EXCLUSIVITY / OVERLAP AUDIT - deterministic, generic.

The owner's review of the CASE-6 SE-elevation overlay exposed the rule this
module exists for:

    TRACE OVERLAP  !=  MATERIAL OVERLAP

Two traces can share pixels because they are two semantic views of one
object (a parapet body and its external face line), because two different
objects project onto the same area of an elevation (a dome behind a
parapet), because a child sits on its host (a capping band on a wall), or
because two readings assign incompatible material roles to the same
place (an open lattice balustrade and a solid plasterable face). Only the
last kind is a contradiction, and only the audit can say which is which.

VOCABULARY (fixed)

    OVERLAP_RELATION
      SAME_OBJECT_MULTIPLE_SEMANTIC_VIEWS   one physical object, two traces
      DIFFERENT_OBJECTS_SAME_PROJECTION     two objects, one drawing area
      PARTIAL_OVERLAP                       distinct objects sharing part
      MUTUALLY_EXCLUSIVE_MATERIAL_ROLES     roles that cannot both be true
      ALLOWED_LAYER_OVERLAP                 host / child, or annotation
      UNRESOLVED_OVERLAP                    nothing above can be established

Every physical object carries: PHYSICAL_OBJECT_ID, MATERIAL_ROLE,
TRADE_CONTRIBUTION_ROLE, CONTRIBUTION_PRIORITY, MUTUALLY_EXCLUSIVE_WITH,
HOST_OBJECT, CHILD_OBJECT. Every quantity contribution carries a
TRADE_CONTRIBUTION_ID, and the double-count guard refuses two contributions
that resolve to the same id or to a forbidden pair.

THE PARAPET / BALUSTRADE RULE (§4)

    an OPEN_BALUSTRADE has PLASTERABLE_SOLID_FACE = 0. It contributes no
    plaster face. Only a SOLID base under it (its own object, its own
    trace) contributes, and only for its own height.

WHAT THIS MODULE WILL NOT DO

  * decide that two traces are the same object from prose. Object
    membership comes from an explicit OBJECT_MAP the controller declares
    and the output records; without it the relation stays UNRESOLVED.
  * resolve a MUTUALLY_EXCLUSIVE pair by picking a winner silently. The
    default CONTRIBUTION_PRIORITY is EXCLUDE_BOTH_UNTIL_RESOLVED.
"""

from __future__ import annotations

import hashlib
import json
from itertools import combinations

from shapely.geometry import LineString, Polygon, box

AUDIT_RULE_VERSION = "MRA-1.0"

OVERLAP_RELATIONS = (
    "SAME_OBJECT_MULTIPLE_SEMANTIC_VIEWS", "DIFFERENT_OBJECTS_SAME_PROJECTION",
    "PARTIAL_OVERLAP", "MUTUALLY_EXCLUSIVE_MATERIAL_ROLES",
    "ALLOWED_LAYER_OVERLAP", "UNRESOLVED_OVERLAP",
)

# material role by effective claim type - the generic default; a controller
# may override per trace with a recorded reason
ROLE_BY_CLAIM_TYPE = {
    "WALL_SEGMENT": "WALL_FACE",
    "COLUMN": "COLUMN_FACE",
    "PARAPET": "PARAPET_SOLID_FACE",
    "BALUSTRADE": "OPEN_BALUSTRADE",
    "GLAZING": "GLAZING",
    "DOOR": "DOOR_OPENING",
    "WINDOW": "WINDOW_OPENING",
    "OPEN_EDGE": "NO_MATERIAL",
    "STAIR": "STAIR_BODY",
    "UNRESOLVED_FEATURE": "UNRESOLVED",
}
ANNOTATION_ROLE = "NON_MATERIAL_ANNOTATION"   # dimensions, marks, refs, ids
MATERIAL_ROLES = (
    "WALL_FACE", "COLUMN_FACE", "PARAPET_SOLID_FACE", "OPEN_BALUSTRADE",
    "CAPPING_BAND", "GLAZING", "DOOR_OPENING", "WINDOW_OPENING",
    "NO_MATERIAL", "STAIR_BODY", "PIER_FACE", "UNRESOLVED",
)

# what each material role contributes to the wall-treatment trades
TRADE_CONTRIBUTION_ROLE = {
    "WALL_FACE": "PLASTER_FACE",
    "PIER_FACE": "PLASTER_FACE",
    "COLUMN_FACE": "COLUMN_BONDING_PLUS_PLASTER",
    "PARAPET_SOLID_FACE": "PARAPET_FACE_PLASTER",
    "OPEN_BALUSTRADE": "NONE",          # §4: PLASTERABLE_SOLID_FACE = 0
    "CAPPING_BAND": "PARAPET_CAPPING",  # its own item, never a wall face
    "GLAZING": "NONE",
    "DOOR_OPENING": "DEDUCTION_AND_REVEAL",
    "WINDOW_OPENING": "DEDUCTION_AND_REVEAL",
    "NO_MATERIAL": "NONE",
    "STAIR_BODY": "STAIR_ITEM",
    "UNRESOLVED": "UNRESOLVED",
    ANNOTATION_ROLE: "NONE",
}
PLASTERABLE_SOLID_FACE = {
    r: (TRADE_CONTRIBUTION_ROLE[r] in ("PLASTER_FACE", "PARAPET_FACE_PLASTER",
                                       "COLUMN_BONDING_PLUS_PLASTER"))
    for r in TRADE_CONTRIBUTION_ROLE}

# roles that cannot both be true at one place
MUTUALLY_EXCLUSIVE = {
    frozenset({"OPEN_BALUSTRADE", "PARAPET_SOLID_FACE"}),
    frozenset({"OPEN_BALUSTRADE", "WALL_FACE"}),
    frozenset({"GLAZING", "WALL_FACE"}),
    frozenset({"GLAZING", "PARAPET_SOLID_FACE"}),
    frozenset({"NO_MATERIAL", "WALL_FACE"}),
    frozenset({"NO_MATERIAL", "PARAPET_SOLID_FACE"}),
    frozenset({"WALL_FACE", "PARAPET_SOLID_FACE"}),   # WALL_PARAPET_CONFLICT
}
# host / child pairs whose overlap is a layer, not a contradiction
ALLOWED_LAYER_PAIRS = {
    frozenset({"PARAPET_SOLID_FACE", "CAPPING_BAND"}),
    frozenset({"WALL_FACE", "DOOR_OPENING"}),
    frozenset({"WALL_FACE", "WINDOW_OPENING"}),
    frozenset({"WALL_FACE", "GLAZING"}),       # only when HOSTED_IN says so
    frozenset({"WALL_FACE", "COLUMN_FACE"}),
    frozenset({"PARAPET_SOLID_FACE", "PIER_FACE"}),
}
HOST_OF = {"DOOR_OPENING": "WALL_FACE", "WINDOW_OPENING": "WALL_FACE",
           "GLAZING": "WALL_FACE", "CAPPING_BAND": "PARAPET_SOLID_FACE",
           "COLUMN_FACE": "WALL_FACE", "PIER_FACE": "PARAPET_SOLID_FACE"}

DEFAULT_PRIORITY = "EXCLUDE_BOTH_UNTIL_RESOLVED"
STROKE_HALF_WIDTH_PX = 3.0
SAME_PROJECTION_RATIO = 0.90
JUNCTION_RATIO = 0.05

GUARD_CONFLICTS = (
    "DUPLICATE_PHYSICAL_CONTRIBUTION", "PARENT_CHILD_DOUBLE_COUNT",
    "BALUSTRADE_PARAPET_CONFLICT", "WALL_PARAPET_CONFLICT",
    "OPENING_HOST_DOUBLE_COUNT",
)


def canon_hash(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


# ------------------------------------------------------------------
# geometry
# ------------------------------------------------------------------
def geometry_of(t: dict):
    """Shapely area geometry for a trace, or None. Polylines are buffered
    by half a stroke so a face LINE can overlap a face POLYGON."""
    if t.get("PIXEL_POLYGON") and len(t["PIXEL_POLYGON"]) >= 3:
        p = Polygon([tuple(q) for q in t["PIXEL_POLYGON"]])
        return p.buffer(0) if not p.is_valid else p
    if t.get("PIXEL_POLYLINE") and len(t["PIXEL_POLYLINE"]) >= 2:
        return LineString([tuple(q) for q in t["PIXEL_POLYLINE"]]).buffer(
            STROKE_HALF_WIDTH_PX)
    if t.get("PIXEL_BBOX"):
        x0, y0, x1, y1 = t["PIXEL_BBOX"]
        return box(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
    return None


# ------------------------------------------------------------------
# roles
# ------------------------------------------------------------------
def material_role(t: dict, overrides: dict | None = None) -> dict:
    ct = t.get("EFFECTIVE_CLAIM_TYPE") or t.get("CLAIM_TYPE")
    ov = (overrides or {}).get(t["TRACE_ID"])
    if ov:
        if ov["MATERIAL_ROLE"] not in MATERIAL_ROLES:
            raise ValueError(f"unknown MATERIAL_ROLE {ov['MATERIAL_ROLE']}")
        return {"MATERIAL_ROLE": ov["MATERIAL_ROLE"],
                "ROLE_ASSIGNED_BY": "CONTROLLER_DECLARATION",
                "ROLE_REASON": ov.get("REASON")}
    role = ROLE_BY_CLAIM_TYPE.get(ct, ANNOTATION_ROLE)
    return {"MATERIAL_ROLE": role, "ROLE_ASSIGNED_BY": "CLAIM_TYPE_DEFAULT",
            "ROLE_REASON": f"default role for {ct}"}


def physical_objects(traces: list, *, object_map: dict | None = None,
                     role_overrides: dict | None = None,
                     solid_base_of: dict | None = None) -> list:
    """One record per trace with its object membership and roles.

    object_map     {PHYSICAL_OBJECT_ID: [TRACE_ID, ...]} declared by the
                   controller; a trace outside the map is its own object
                   (PO:<TRACE_ID>) and that is recorded.
    solid_base_of  {balustrade TRACE_ID: parapet TRACE_ID} - the §4 solid
                   base under an open balustrade, when one was traced.
    """
    object_map = object_map or {}
    member_of = {}
    for oid, members in object_map.items():
        for m in members:
            if m in member_of:
                raise ValueError(f"trace {m} declared in two objects")
            member_of[m] = oid
    out = []
    for t in traces:
        r = material_role(t, role_overrides)
        role = r["MATERIAL_ROLE"]
        oid = member_of.get(t["TRACE_ID"], f"PO:{t['TRACE_ID']}")
        host = HOST_OF.get(role)
        rec = {
            "TRACE_ID": t["TRACE_ID"], "SHEET_ID": t.get("SHEET_ID"),
            "PHYSICAL_OBJECT_ID": oid,
            "OBJECT_MEMBERSHIP": ("DECLARED" if t["TRACE_ID"] in member_of
                                  else "SINGLETON_BY_DEFAULT"),
            **r,
            "TRADE_CONTRIBUTION_ROLE": TRADE_CONTRIBUTION_ROLE[role],
            "PLASTERABLE_SOLID_FACE": PLASTERABLE_SOLID_FACE[role],
            "CONTRIBUTION_PRIORITY": DEFAULT_PRIORITY,
            "MUTUALLY_EXCLUSIVE_WITH": sorted(
                next(iter(p - {role})) for p in MUTUALLY_EXCLUSIVE if role in p),
            "HOST_OBJECT": None, "CHILD_OBJECT": None,
            "HOST_ROLE_EXPECTED": host,
            "HOSTED_IN": t.get("HOSTED_IN"),
            "VISUAL_TRACE_STATUS": t.get("VISUAL_TRACE_STATUS"),
        }
        if role == "OPEN_BALUSTRADE":
            base = (solid_base_of or {}).get(t["TRACE_ID"])
            rec["SOLID_BASE_TRACE"] = base
            rec["BALUSTRADE_RULE"] = (
                "PLASTERABLE_SOLID_FACE = 0; the solid base, if traced, "
                "contributes as its own object for its own height only")
        out.append(rec)
    by_id = {o["TRACE_ID"]: o for o in out}
    for o in out:
        h = o["HOSTED_IN"]
        h = h[0] if isinstance(h, list) and h else h
        if isinstance(h, str) and h in by_id:
            o["HOST_OBJECT"] = by_id[h]["PHYSICAL_OBJECT_ID"]
            by_id[h]["CHILD_OBJECT"] = (by_id[h]["CHILD_OBJECT"] or [])
            by_id[h]["CHILD_OBJECT"].append(o["PHYSICAL_OBJECT_ID"])
    return out


# ------------------------------------------------------------------
# overlap audit
# ------------------------------------------------------------------
def _classify(a: dict, b: dict, inter_area: float, min_area: float) -> tuple:
    ra, rb = a["MATERIAL_ROLE"], b["MATERIAL_ROLE"]
    pair = frozenset({ra, rb})
    if a["PHYSICAL_OBJECT_ID"] == b["PHYSICAL_OBJECT_ID"]:
        return ("SAME_OBJECT_MULTIPLE_SEMANTIC_VIEWS",
                "both traces are declared members of one physical object")
    hosted = (a["HOST_OBJECT"] == b["PHYSICAL_OBJECT_ID"]
              or b["HOST_OBJECT"] == a["PHYSICAL_OBJECT_ID"])
    if hosted:
        return ("ALLOWED_LAYER_OVERLAP", "child hosted in its host (HOSTED_IN)")
    if pair in ALLOWED_LAYER_PAIRS and (ra in HOST_OF or rb in HOST_OF):
        # a layer pair without a HOSTED_IN link: allowed only when the child
        # role names the other as its expected host
        child = a if ra in HOST_OF else b
        host = b if child is a else a
        if HOST_OF[child["MATERIAL_ROLE"]] == host["MATERIAL_ROLE"]:
            return ("ALLOWED_LAYER_OVERLAP",
                    f"{child['MATERIAL_ROLE']} layered on its expected host "
                    f"{host['MATERIAL_ROLE']} (no HOSTED_IN link; geometric)")
    if pair in MUTUALLY_EXCLUSIVE:
        return ("MUTUALLY_EXCLUSIVE_MATERIAL_ROLES",
                f"{ra} and {rb} cannot both be true at one place")
    if "UNRESOLVED" in pair:
        return ("UNRESOLVED_OVERLAP", "one trace has no established material role")
    if min_area > 0 and inter_area / min_area >= SAME_PROJECTION_RATIO:
        return ("UNRESOLVED_OVERLAP",
                "near-total overlap of two objects not declared as one: "
                "DIFFERENT_OBJECTS_SAME_PROJECTION is possible but is a "
                "claim the controller must declare")
    return ("PARTIAL_OVERLAP", "distinct objects sharing part of their area")


def overlap_audit(traces: list, *, object_map=None, role_overrides=None,
                  solid_base_of=None, same_projection_pairs=None) -> dict:
    """Audit every same-sheet pair of material-bearing traces."""
    objs = physical_objects(traces, object_map=object_map,
                            role_overrides=role_overrides,
                            solid_base_of=solid_base_of)
    by_id = {o["TRACE_ID"]: o for o in objs}
    geoms = {t["TRACE_ID"]: geometry_of(t) for t in traces}
    declared_same_projection = {frozenset(p) for p in (same_projection_pairs or [])}
    material = [t for t in traces
                if by_id[t["TRACE_ID"]]["MATERIAL_ROLE"] != ANNOTATION_ROLE
                and geoms[t["TRACE_ID"]] is not None]
    relations, adjacencies = [], []
    for ta, tb in combinations(material, 2):
        if ta["SHEET_ID"] != tb["SHEET_ID"]:
            continue
        ga, gb = geoms[ta["TRACE_ID"]], geoms[tb["TRACE_ID"]]
        inter = ga.intersection(gb)
        a, b = by_id[ta["TRACE_ID"]], by_id[tb["TRACE_ID"]]
        if inter.is_empty or inter.area <= 0.0:
            if ga.distance(gb) <= 1.0:
                adjacencies.append({"A": ta["TRACE_ID"], "B": tb["TRACE_ID"],
                                    "RELATION": "ADJACENT_NO_AREA_OVERLAP"})
            continue
        min_area = min(ga.area, gb.area)
        pair = frozenset({ta["TRACE_ID"], tb["TRACE_ID"]})
        if pair in declared_same_projection:
            rel, why = ("DIFFERENT_OBJECTS_SAME_PROJECTION",
                        "declared by the controller as two objects at "
                        "different depths projecting onto one area")
        else:
            rel, why = _classify(a, b, inter.area, min_area)
        # a sliver where two traced elements meet end-to-end is a junction,
        # not a shared area; it is flagged so the estimate can treat it as
        # one, but the relation itself is not softened
        junction_like = (min_area > 0 and inter.area / min_area < JUNCTION_RATIO
                         and rel in ("MUTUALLY_EXCLUSIVE_MATERIAL_ROLES",
                                     "PARTIAL_OVERLAP"))
        rec = {
            "A": ta["TRACE_ID"], "B": tb["TRACE_ID"], "SHEET_ID": ta["SHEET_ID"],
            "JUNCTION_LIKE": junction_like,
            "A_ROLE": a["MATERIAL_ROLE"], "B_ROLE": b["MATERIAL_ROLE"],
            "A_OBJECT": a["PHYSICAL_OBJECT_ID"], "B_OBJECT": b["PHYSICAL_OBJECT_ID"],
            "INTERSECTION_PX2": round(inter.area, 1),
            "OVERLAP_RATIO_OF_SMALLER": round(inter.area / min_area, 4) if min_area else None,
            "OVERLAP_RELATION": rel, "WHY": why,
            "IS_A_MATERIAL_CONTRADICTION": rel == "MUTUALLY_EXCLUSIVE_MATERIAL_ROLES",
            "CONTRIBUTION_PRIORITY": (DEFAULT_PRIORITY
                                      if rel in ("MUTUALLY_EXCLUSIVE_MATERIAL_ROLES",
                                                 "UNRESOLVED_OVERLAP", "PARTIAL_OVERLAP")
                                      else "NOT_NEEDED"),
        }
        relations.append(rec)
    counts = {r: sum(1 for x in relations if x["OVERLAP_RELATION"] == r)
              for r in OVERLAP_RELATIONS}
    body = {
        "AUDIT_RULE_VERSION": AUDIT_RULE_VERSION,
        "PHYSICAL_OBJECTS": objs,
        "OVERLAP_RELATIONS": relations,
        "ADJACENCIES": adjacencies,
        "COUNTS": counts,
        "MATERIAL_CONTRADICTIONS": [r for r in relations
                                    if r["IS_A_MATERIAL_CONTRADICTION"]],
        "MATERIAL_CONTRADICTIONS_BEYOND_JUNCTIONS": [
            r for r in relations
            if r["IS_A_MATERIAL_CONTRADICTION"] and not r["JUNCTION_LIKE"]],
        "TRACE_OVERLAP_IS_NOT_MATERIAL_OVERLAP": True,
        "TRACES_AUDITED": [t["TRACE_ID"] for t in material],
        "TRACES_EXCLUDED_AS_ANNOTATION_OR_NO_AREA": [
            t["TRACE_ID"] for t in traces if t not in material],
    }
    body["AUDIT_SHA256"] = canon_hash({k: v for k, v in body.items()})
    return body


# ------------------------------------------------------------------
# double-count guard on quantity contributions
# ------------------------------------------------------------------
def trade_contribution_id(trade: str, physical_object_id: str, face_id: str,
                          item: str) -> str:
    return f"{trade}:{physical_object_id}:{face_id}:{item}"


def guard_contributions(contributions: list, objects: list | None = None) -> dict:
    """Refuse two contributions that resolve to one physical contribution.

    Each contribution: {TRADE_CONTRIBUTION_ID, TRADE, PHYSICAL_OBJECT_ID,
    FACE_ID, ITEM, MATERIAL_ROLE, HOST_OBJECT (opt), TRACE_IDS}.
    """
    seen, conflicts = {}, []
    by_obj = {}
    for c in contributions:
        cid = c["TRADE_CONTRIBUTION_ID"]
        if cid in seen:
            conflicts.append({"CONFLICT": "DUPLICATE_PHYSICAL_CONTRIBUTION",
                              "IDS": [cid], "TRACES": [seen[cid].get("TRACE_IDS"),
                                                       c.get("TRACE_IDS")]})
        seen[cid] = c
        by_obj.setdefault((c["TRADE"], c["PHYSICAL_OBJECT_ID"], c["FACE_ID"]), []).append(c)
    face_items = {}
    for c in contributions:
        face_items.setdefault((c["TRADE"], c["PHYSICAL_OBJECT_ID"], c["FACE_ID"]), []).append(c)
    for ca, cb in combinations(contributions, 2):
        if ca["TRADE"] != cb["TRADE"]:
            continue
        ra, rb = ca.get("MATERIAL_ROLE"), cb.get("MATERIAL_ROLE")
        same_face = (ca["FACE_ID"] == cb["FACE_ID"]
                     and ca["PHYSICAL_OBJECT_ID"] != cb["PHYSICAL_OBJECT_ID"])
        if ca.get("HOST_OBJECT") == cb["PHYSICAL_OBJECT_ID"] or \
                cb.get("HOST_OBJECT") == ca["PHYSICAL_OBJECT_ID"]:
            if ca["ITEM"] == cb["ITEM"] == "FACE":
                conflicts.append({"CONFLICT": "PARENT_CHILD_DOUBLE_COUNT",
                                  "IDS": [ca["TRADE_CONTRIBUTION_ID"],
                                          cb["TRADE_CONTRIBUTION_ID"]]})
            if {ca["ITEM"], cb["ITEM"]} == {"FACE", "OPENING_AREA"} and \
                    "OPENING" in str(ra) + str(rb):
                # an opening counted as a face AND as its host's area
                conflicts.append({"CONFLICT": "OPENING_HOST_DOUBLE_COUNT",
                                  "IDS": [ca["TRADE_CONTRIBUTION_ID"],
                                          cb["TRADE_CONTRIBUTION_ID"]]})
        if same_face and frozenset({ra, rb}) == frozenset(
                {"OPEN_BALUSTRADE", "PARAPET_SOLID_FACE"}):
            conflicts.append({"CONFLICT": "BALUSTRADE_PARAPET_CONFLICT",
                              "IDS": [ca["TRADE_CONTRIBUTION_ID"],
                                      cb["TRADE_CONTRIBUTION_ID"]]})
        if same_face and frozenset({ra, rb}) == frozenset(
                {"WALL_FACE", "PARAPET_SOLID_FACE"}):
            conflicts.append({"CONFLICT": "WALL_PARAPET_CONFLICT",
                              "IDS": [ca["TRADE_CONTRIBUTION_ID"],
                                      cb["TRADE_CONTRIBUTION_ID"]]})
    # §4: a single balustrade FACE contribution is refused on its own
    for c in contributions:
        if c.get("MATERIAL_ROLE") == "OPEN_BALUSTRADE" and c["ITEM"] == "FACE" \
                and c.get("VALUE"):
            conflicts.append({"CONFLICT": "BALUSTRADE_PARAPET_CONFLICT",
                              "IDS": [c["TRADE_CONTRIBUTION_ID"]],
                              "WHY": "an OPEN_BALUSTRADE contributed a plaster "
                                     "face; PLASTERABLE_SOLID_FACE is 0"})
    return {"GUARD_RULE_VERSION": AUDIT_RULE_VERSION,
            "CONTRIBUTIONS": len(contributions),
            "CONFLICTS": conflicts,
            "GUARD_STATUS": "CLEAN" if not conflicts else "CONFLICTS_FOUND",
            "A_CONFLICT_BLOCKS_THE_TOTAL": True}
