"""WALL-CONTACT PATH (R8.14) - the edges of a room where a floor-level wall finish (skirting) can run, classified from
the source of each one-sided boundary edge of a certified TS01 site. Never a room perimeter.

  REAL_WALL_FACE       an admitted wall / structural-obstacle source            -> on the path
  DOOR_OPENING         a door closure (CLOSURE|<door>|A / B)                     -> stops the path
  GLAZED_OPENING       a glazing closure (CLOSURE|GLAZED|...)                    -> stops the path (deduction rules
                                                                                    such as QP-09 decide the rest)
  TOPOLOGY_CLOSURE     a zero-material topology closure (TCLOSURE|)              -> ZERO length, never skirting
  UNPROVEN_OBSTACLE    an edge of an isolated closed loop without physical authority -> withheld
  OTHER                any other role                                            -> withheld
Furniture, wardrobes and joinery are not site boundaries, so the wall behind them stays on the path. Interior stubs
(edges walked on both sides) are excluded. A room whose class carries full wall tile has NO skirting path at all.

This module classifies; it does not publish a quantity. A length becomes a row only under a frozen, blind-tested
policy (the jamb-return rule at topology-closed wall ends has no physical-length authority yet).

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict

POLICY_ID = "WALL_CONTACT_PATH_POLICY_V1"
REAL_WALL_FACE, DOOR_OPENING, GLAZED_OPENING = "REAL_WALL_FACE", "DOOR_OPENING", "GLAZED_OPENING"
TOPOLOGY_CLOSURE, UNPROVEN_OBSTACLE, OTHER = "TOPOLOGY_CLOSURE", "UNPROVEN_OBSTACLE", "OTHER"
ON_PATH = (REAL_WALL_FACE,)
WALL_ROLES = ("TOPOLOGY_BOUNDARY", "STRUCTURAL_OBSTACLE")
NO_SKIRTING = "NO_SKIRTING_FULL_WALL_TILE"


def _entity(sid):
    return sid.rsplit("|", 1)[0]


def site_edges(arr, site) -> list:
    """One-sided boundary edges of a site (outer + holes): [{"sources", "roles", "length", "hole"}]."""
    cycles = [(c, False) for c in [arr.faces[site["face"]]["cycle"]]] + [(c, True) for c in site.get("hole_cycles", [])]
    seen = defaultdict(int)
    for c, _ in cycles:
        for ei, _ in c:
            seen[ei] += 1
    out = []
    for c, hole in cycles:
        for ei, _ in c:
            if seen[ei] != 1:
                continue
            e = arr.edges[ei]
            ln = math.dist(arr.nodes[e["n0"]], arr.nodes[e["n1"]]) if e["kind"] == "S" else \
                e["prim"].r * (e["t1"] - e["t0"])
            out.append({"sources": sorted(e["sources"]), "roles": sorted(e["roles"]), "length": ln, "hole": hole})
    return out


def classify(edge, *, isolated_entities=()) -> str:
    src = edge["sources"]
    if any(s.startswith("TCLOSURE|") for s in src):
        return TOPOLOGY_CLOSURE
    if any(s.startswith("CLOSURE|GLAZED|") for s in src):
        return GLAZED_OPENING
    if any(s.startswith("CLOSURE|") for s in src):
        return DOOR_OPENING
    if any(_entity(s) in set(isolated_entities) for s in src):
        return UNPROVEN_OBSTACLE
    if edge["roles"] and all(r in WALL_ROLES for r in edge["roles"]):
        return REAL_WALL_FACE
    return OTHER


def path(edges, *, full_wall_tile=False, isolated_entities=()) -> dict:
    if full_wall_tile:
        return {"state": NO_SKIRTING, "by_class": {}, "on_path_length": 0.0, "withheld": []}
    by = defaultdict(lambda: [0, 0.0])
    withheld = []
    for e in edges:
        c = classify(e, isolated_entities=isolated_entities)
        by[c][0] += 1
        by[c][1] += e["length"]
        if c in (UNPROVEN_OBSTACLE, OTHER):
            withheld.append({"class": c, "sources": e["sources"][:3]})
    return {"state": "CLASSIFIED", "by_class": {k: {"edges": v[0], "length": v[1]} for k, v in sorted(by.items())},
            "on_path_length": math.fsum(v[1] for k, v in by.items() if k in ON_PATH), "withheld": withheld}


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID, "classes": [REAL_WALL_FACE, DOOR_OPENING, GLAZED_OPENING, TOPOLOGY_CLOSURE,
                                               UNPROVEN_OBSTACLE, OTHER], "on_path": list(ON_PATH),
           "never": ["a room polygon perimeter", "skirting across a door or an open passage", "skirting on a "
                     "topology closure", "a furniture / wardrobe deduction", "skirting in a full-wall-tile room",
                     "a published quantity without a frozen, blind-tested policy"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec
