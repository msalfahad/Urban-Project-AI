"""OBSTACLE AUTHORITY (R8.15) - which room holes stand on PHYSICAL authority, kept apart from topology geometry.

TS01 realises every admitted closed loop as geometry. Where such a loop is an ISOLATED CLOSED LOOP (wall_bands V5:
a closed single-entity loop touching no admitted segment of another entity) its geometry is not physical authority.
A hole it cuts out of a room is:
  OWNER_PHYSICAL_OBSTACLE   every segment of the entity is bound by an APPLYING owner physical fact of kind
                            BUILT_OBSTACLE (exact part keys + fingerprints, this revision / anchor / region / frame)
  UNPROVEN_OBSTACLE         otherwise (the hole stays as TS01 computes it, carried as a release blocker)
The fact never changes topology: TS01 already made the hole, so for topology it is corroboration only. It never
transfers to another entity with the same shape, layer or presentation (a dashed X is never a bound part).

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib
import json
import math

from . import owner_claims as OC

POLICY_ID = "OBSTACLE_AUTHORITY_POLICY_V1"
OWNER_PHYSICAL_OBSTACLE = "OWNER_PHYSICAL_OBSTACLE"
UNPROVEN_OBSTACLE = "UNPROVEN_OBSTACLE"
BUILT_OBSTACLE = "BUILT_OBSTACLE"


def _entity(key):
    return key.rsplit("|", 1)[0]


def entity_authority(isolated_loops, bound_facts) -> dict:
    """isolated_loops: [{"entity", "segments": [part keys]}] (wall_bands V5); bound_facts: [(PhysicalFact, binding)].
    -> {entity: {"state", "fact", "physical_class", "parts_bound"}}."""
    out = {}
    for loop in isolated_loops:
        ent, segs = loop["entity"], set(loop["segments"])
        rec = {"state": UNPROVEN_OBSTACLE, "fact": None, "physical_class": None, "segments": len(segs)}
        for f, b in bound_facts:
            if f.kind != BUILT_OBSTACLE or b.get("binding") != OC.APPLIES:
                continue
            keys = {k for k, _fp, _r in f.parts}
            if segs and segs <= keys:
                rec = {"state": OWNER_PHYSICAL_OBSTACLE, "fact": f.ref,
                       "physical_class": f.statement.get("physical_class"), "segments": len(segs),
                       "topology_effect": f.statement.get("topology_effect"),
                       "floor_effect": f.statement.get("floor_effect"),
                       "ceiling_effect": f.statement.get("ceiling_effect")}
                break
        out[ent] = rec
    return out


def shoelace(pts) -> float:
    return abs(math.fsum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
                         for i in range(len(pts)))) / 2


def site_holes(site, isolated_loops, authority, unit2) -> dict | None:
    """The holes of one site cut by isolated loops: their area (TS01: gross outer - net) and whether each loop has
    physical authority. None when no isolated loop cuts the site."""
    seg = {s: x["entity"] for x in isolated_loops for s in x["segments"]}
    hs = set(site.get("hole_source_ids", []))
    ents = sorted({seg[s] for s in hs if s in seg})
    if not ents:
        return None
    pure = hs <= set(seg)
    states = {e: authority.get(e, {}).get("state", UNPROVEN_OBSTACLE) for e in ents}
    return {"site": site["site_id"], "entities": ents, "states": states,
            "hole_area_m2": round((site["gross_outer_area"] - site["area"]) * unit2, 6) if pure else None,
            "holes_only_isolated_loops": pure,
            "authorised": all(v == OWNER_PHYSICAL_OBSTACLE for v in states.values()),
            "facts": sorted({authority[e]["fact"] for e in ents if authority.get(e, {}).get("fact")})}


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID, "states": [OWNER_PHYSICAL_OBSTACLE, UNPROVEN_OBSTACLE],
           "authority": "an APPLYING owner physical fact of kind BUILT_OBSTACLE binding EVERY segment of the entity",
           "never": ["a topology change", "authority from shape, size, layer or a dashed X", "transfer to another "
                     "entity, revision or project", "a material type beyond the fact", "a quantity"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec
