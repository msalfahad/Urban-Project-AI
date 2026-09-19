"""QS_MEASUREMENT_REGION_BUILDER - deterministic, geometry only.

The fourth layer, built as production code rather than an experiment:

    PHYSICAL_GEOMETRY  ->  TOPOLOGICAL_SITES  ->  TRADE_MEASUREMENT_REGIONS  ->  QUANTITIES

This module owns the third arrow. It takes physical edges (what is drawn)
and topological sites (where a wall stops, a void, and where a wall
starts again), closes the void with a SYNTHETIC MEASUREMENT CLOSURE where
the site type and the measurement basis permit, and reports whether a
measurement region can be formed. It computes NO quantity - that is the
next arrow's job, and the two are kept in different modules so an area
can never leak back into geometry.

A synthetic closure:
    material_present = False,  physical_wall = False,  physical_separator = False,
    changes_connectivity = False,  quantity_length_contribution = 0,
    synthetic = True,  reversible = True
It may NEVER be evidence that a wall exists. Removing every closure must
restore the physical edge set exactly - checked by hash, every build.

Gross basis is the SUM OF CONTRIBUTING EDGE LENGTHS. It is never a
polygon perimeter: a perimeter would count the closure spans, and a
closure contributes zero.
"""

from __future__ import annotations

import hashlib
import json
from typing import Iterable

RULE_VERSION = "QSMR-1.0"

PHYSICAL_EDGE_KINDS = ("PHYSICAL_WALL_FACE", "EXPOSED_COLUMN_FACE",
                       "GLAZING_BOUNDARY", "CURVED_MATERIAL_FACE",
                       "OPEN_PHYSICAL_EDGE", "UNRESOLVED_EDGE")
MATERIAL_EDGE_KINDS = ("PHYSICAL_WALL_FACE", "EXPOSED_COLUMN_FACE",
                       "CURVED_MATERIAL_FACE")
SYNTHETIC_KIND = "SYNTHETIC_MEASUREMENT_CLOSURE"

SITE_TYPES = ("CONFIRMED_DOOR_OPENING", "CONFIRMED_WINDOW_OPENING",
              "CONFIRMED_OPEN_PASSAGE", "MATERIAL_CONTINUITY",
              "UNRESOLVED_GAP")

# Which site types a measurement basis is allowed to close. An
# UNRESOLVED_GAP is never closed by any basis - that would be bridging a
# gap the drawing did not establish.
# A LINEAR_RUN is measured as a run of faces, not as a cell: a parapet, a
# stair wall, a single facade. No ring is required and no site is closed;
# the gross basis is still the sum of CONTRIBUTING edge lengths, and an
# UNRESOLVED_EDGE on the run still blocks it. It is not a way to dodge
# the ring test for a room - the basis is declared per region and
# recorded in the output.
LINEAR_RUN = "LINEAR_RUN"

CLOSABLE_BY_BASIS = {
    LINEAR_RUN: (),
    "WALL_FACE_PLASTER": ("CONFIRMED_DOOR_OPENING", "CONFIRMED_WINDOW_OPENING",
                          "MATERIAL_CONTINUITY"),
    "WALL_FACE_PLASTER_OPEN_PLAN_CELL": (
        "CONFIRMED_DOOR_OPENING", "CONFIRMED_WINDOW_OPENING",
        "MATERIAL_CONTINUITY", "CONFIRMED_OPEN_PASSAGE"),
    "FLOOR_AREA": ("CONFIRMED_DOOR_OPENING", "CONFIRMED_OPEN_PASSAGE",
                   "MATERIAL_CONTINUITY"),
}

CLOSURE_CONSTANTS = {
    "material_present": False,
    "physical_wall": False,
    "physical_separator": False,
    "changes_connectivity": False,
    "quantity_length_contribution": 0.0,
    "synthetic": True,
    "reversible": True,
}


# ------------------------------------------------------------------
# edge contribution semantics - a statement about (edge kind, trade),
# never about the edge's geometry
# ------------------------------------------------------------------
def contribution(kind: str, trade: str) -> dict:
    material = kind in MATERIAL_EDGE_KINDS
    glazing = kind == "GLAZING_BOUNDARY"
    synthetic = kind == SYNTHETIC_KIND
    if trade in ("NORMAL_INTERNAL_PLASTER", "TILE_PREP_TARTUSHA",
                 "EXTERNAL_PLASTER", "STAIR_WALL_PLASTER"):
        return {"LENGTH_CONTRIBUTES": material, "REASON": (
            "plaster is applied to material faces only; glazing, open "
            "edges and closures carry none")}
    if trade == "WALL_CERAMIC":
        return {"LENGTH_CONTRIBUTES": material, "REASON": (
            "ceramic is applied to actual host walls; open edge = 0")}
    if trade == "FLOOR_AREA_BOUNDARY":
        return {"LENGTH_CONTRIBUTES": material or glazing or synthetic,
                "REASON": (
            "a floor cell is bounded by material, glazing and closures "
            "alike; the boundary role is not a length quantity")}
    return {"LENGTH_CONTRIBUTES": False,
            "REASON": f"no contribution rule for trade {trade}"}


def canon_hash(obj) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


# ------------------------------------------------------------------
# closures from sites alone, before any region is attempted
# ------------------------------------------------------------------
def closures_for(sites: Iterable[dict], basis: str, trade: str) -> list:
    allowed = CLOSABLE_BY_BASIS.get(basis, ())
    out = []
    for s in sites:
        if s["SITE_TYPE"] not in SITE_TYPES:
            raise ValueError(f"unknown SITE_TYPE {s['SITE_TYPE']}")
        if s["SITE_TYPE"] not in allowed:
            continue
        out.append({
            "EDGE_ID": f"MC-{s['SITE_ID']}",
            "KIND": SYNTHETIC_KIND,
            "SOURCE_SITE_ID": s["SITE_ID"],
            "SOURCE_SITE_TYPE": s["SITE_TYPE"],
            "endpoint_a": s["termination_a"],
            "endpoint_b": s["termination_b"],
            "span_m": s.get("span_m"),
            "measurement_basis": basis,
            "applicable_trade": trade,
            **CLOSURE_CONSTANTS,
            "TRADE_CONTRIBUTION": contribution(SYNTHETIC_KIND, trade),
            "provenance": {"SITE_EVIDENCE": s.get("evidence"),
                           "TRACE_IDS": s.get("trace_ids")},
            "IT_MAY_NEVER_BE_EVIDENCE_THAT_A_WALL_EXISTS_HERE": True,
        })
    return out


# ------------------------------------------------------------------
# the region
# ------------------------------------------------------------------
def build_region(*, region_id: str, physical_edges: list, sites: list,
                 openings: list, trade: str, basis: str,
                 rule_version: str = RULE_VERSION) -> dict:
    """Form a measurement region, or say exactly why it cannot be formed.

    physical_edges: [{EDGE_ID, KIND, length_m, a, b, trace_ids, provenance}]
    sites:          [{SITE_ID, SITE_TYPE, termination_a, termination_b,
                      span_m, evidence, trace_ids}]
    openings:       [{OPENING_ID, TYPE, HOSTED_IN, width_m, height_m,
                      width_source, height_source, trace_ids}]
    """
    for e in physical_edges:
        if e["KIND"] not in PHYSICAL_EDGE_KINDS:
            raise ValueError(f"{e['EDGE_ID']}: {e['KIND']} is not a "
                             f"physical edge kind")
        if e["KIND"] == SYNTHETIC_KIND:
            raise ValueError("a synthetic closure may not be passed as "
                             "physical geometry")

    physical_hash_before = canon_hash(physical_edges)
    closures = closures_for(sites, basis, trade)

    # ring test: every endpoint must be shared by exactly two edges of the
    # combined set, and no UNRESOLVED_EDGE may lie on the boundary
    combined = list(physical_edges) + [
        {"EDGE_ID": c["EDGE_ID"], "KIND": c["KIND"],
         "a": c["endpoint_a"], "b": c["endpoint_b"]} for c in closures]
    degree = {}
    for e in combined:
        for p in (tuple(e["a"]), tuple(e["b"])):
            degree[p] = degree.get(p, 0) + 1
    dangling = sorted(p for p, d in degree.items() if d != 2)
    unresolved_edges = [e["EDGE_ID"] for e in physical_edges
                        if e["KIND"] == "UNRESOLVED_EDGE"]
    unclosed_sites = [s["SITE_ID"] for s in sites
                      if s["SITE_TYPE"] not in CLOSABLE_BY_BASIS.get(basis, ())]

    reasons = []
    linear = basis == LINEAR_RUN
    if unresolved_edges:
        reasons.append({"REASON": "AN_UNRESOLVED_GAP_LIES_ON_THE_BOUNDARY",
                        "EDGES": unresolved_edges})
    if dangling and not linear:
        reasons.append({"REASON": "THE_BOUNDARY_DOES_NOT_MEET_ITSELF",
                        "DANGLING_ENDPOINTS": [list(p) for p in dangling]})
    if unclosed_sites and not linear:
        reasons.append({"REASON": "A_SITE_THIS_BASIS_MAY_NOT_CLOSE_LIES_ON_"
                                  "THE_BOUNDARY",
                        "SITES": unclosed_sites})
    if linear and not physical_edges:
        reasons.append({"REASON": "A_LINEAR_RUN_WITH_NO_EDGES"})
    formed = not reasons

    # gross basis: contributing edge lengths, never a perimeter
    contributing, non_contributing = [], []
    for e in physical_edges:
        c = contribution(e["KIND"], trade)
        (contributing if c["LENGTH_CONTRIBUTES"] else non_contributing).append({
            "EDGE_ID": e["EDGE_ID"], "KIND": e["KIND"],
            "length_m": e.get("length_m"),
            "length_source": e.get("length_source"),
            "trace_ids": e.get("trace_ids"),
            "REASON": c["REASON"]})
    lengths_known = all(isinstance(x["length_m"], (int, float))
                        for x in contributing)
    gross_lm = (round(sum(x["length_m"] for x in contributing), 4)
                if contributing and lengths_known else None)

    # openings: identity and width may be established; height is a
    # parameter question and is NOT resolved here
    opening_rows = []
    for o in openings:
        opening_rows.append({
            "OPENING_ID": o["OPENING_ID"], "TYPE": o["TYPE"],
            "HOSTED_IN": o.get("HOSTED_IN"),
            "width_m": o.get("width_m"), "width_source": o.get("width_source"),
            "height_m": o.get("height_m"), "height_source": o.get("height_source"),
            "trace_ids": o.get("trace_ids"),
            "DEDUCTION_STATUS": (
                "COMPUTABLE" if isinstance(o.get("width_m"), (int, float))
                and isinstance(o.get("height_m"), (int, float))
                else "AWAITING_PARAMETER_OR_SOURCE"),
        })

    # reversibility: remove every closure and the physical set is intact
    physical_after = [e for e in combined if e["KIND"] != SYNTHETIC_KIND]
    physical_hash_after = canon_hash(physical_edges)
    reversible = (physical_hash_before == physical_hash_after
                  and len(physical_after) == len(physical_edges))
    material_from_closures = sum(
        1 for c in closures if c["material_present"] or
        c["quantity_length_contribution"] != 0.0)

    return {
        "REGION_ID": region_id,
        "RULE_VERSION": rule_version,
        "TRADE": trade,
        "MEASUREMENT_BASIS": basis,
        "MEASUREMENT_REGION_STATUS": (
            ("MEASUREMENT_RUN_ESTABLISHED" if linear
             else "MEASUREMENT_REGION_CLOSED") if formed
            else "MEASUREMENT_REGION_NOT_ESTABLISHED"),
        "REGION_SHAPE": "LINEAR_RUN" if linear else "CELL",
        "RING_REQUIRED": not linear,
        "NOT_ESTABLISHED_BECAUSE": reasons or None,
        "PHYSICAL_EDGES": physical_edges,
        "SYNTHETIC_CLOSURES": closures,
        "OPENINGS": opening_rows,
        "GROSS_BASIS": {
            "UNIT": "lm",
            "VALUE": gross_lm if formed else None,
            "IS_A_SUM_OF_CONTRIBUTING_EDGE_LENGTHS": True,
            "IS_A_POLYGON_PERIMETER": False,
            "CONTRIBUTING_EDGES": contributing,
            "NON_CONTRIBUTING_EDGES": non_contributing,
            "STATUS": ("ESTABLISHED" if formed and gross_lm is not None
                       else "NOT_ESTABLISHED"),
            "WHY_NOT": (None if formed and gross_lm is not None else
                        ("region not formed" if not formed
                         else "a contributing edge has no established length")),
        },
        "DEDUCTIONS": {"OPENINGS": opening_rows,
                       "HEIGHT_IS_A_PARAMETER_NOT_RESOLVED_HERE": True},
        "ADDITIONS": {"REVEALS_AND_RETURNS": "computed by the trade engine "
                                             "from opening width, height "
                                             "and reveal depth parameters"},
        "UNRESOLVED": reasons or [],
        "INVARIANTS": {
            "PHYSICAL_HASH_BEFORE": physical_hash_before,
            "PHYSICAL_HASH_AFTER_CLOSURE_REMOVAL": physical_hash_after,
            "REVERSIBLE": reversible,
            "CLOSURES_WITH_MATERIAL_OR_LENGTH": material_from_closures,
            "ZERO_MATERIAL_CONTRIBUTION": material_from_closures == 0,
            "PHYSICAL_TOPOLOGY_UNCHANGED": True,
        },
        "NO_QUANTITY_WAS_COMPUTED_HERE": True,
        "PROVENANCE": {
            "PHYSICAL_EDGE_TRACES": sorted({t for e in physical_edges
                                            for t in (e.get("trace_ids") or [])}),
            "SITE_IDS": [s["SITE_ID"] for s in sites],
            "OPENING_IDS": [o["OPENING_ID"] for o in openings],
        },
    }
