"""REVEAL PHYSICALITY (R8.19) - whether a reveal SURFACE physically exists, decided BEFORE any finish.

A reveal face (segment from the owning room face to the frame / track line) is
  PHYSICAL_REVEAL_ESTABLISHED  when it is covered by an ADMITTED wall / structural part (a topology-boundary or
                               structural role in the certified arrangement), or lies on the end of an ESTABLISHED wall
                               band whose end is classified OPENING_JAMB for THIS opening (both masonry faces terminate
                               on the jamb line, so the band end face spans the wall thickness);
  NO_PHYSICAL_REVEAL           when its depth is zero (frame flush with that face) - zero surface;
  PHYSICALITY_UNRESOLVED       otherwise - the contributor is blocked / null.
Never evidence: a fixture / furniture / glazing / window / frame / aluminium line, a finish default (plaster), an owner
finish rule, symmetry with the other jamb. The candidates seen and rejected are recorded.

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib
import json
import math

POLICY_ID = "REVEAL_PHYSICALITY_POLICY_V1"
ESTABLISHED, NONE, UNRESOLVED = "PHYSICAL_REVEAL_ESTABLISHED", "NO_PHYSICAL_REVEAL", "PHYSICALITY_UNRESOLVED"
ADMITTED_ROLES = ("TOPOLOGY_BOUNDARY", "STRUCTURAL_OBSTACLE")
BAND_ESTABLISHED, BAND_END_JAMB = "WALL_BAND_ESTABLISHED", "OPENING_JAMB"


def _on(p, a, b, eps):
    L = math.dist(a, b)
    if L <= eps:
        return math.dist(p, a) <= eps
    t = ((p[0] - a[0]) * (b[0] - a[0]) + (p[1] - a[1]) * (b[1] - a[1])) / (L * L)
    if t < -eps / L or t > 1 + eps / L:
        return False
    q = (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))
    return math.dist(p, q) <= eps


def covered(a, b, c, d, eps) -> bool:
    """Segment a-b lies on segment c-d (within eps)."""
    return _on(a, c, d, eps) and _on(b, c, d, eps)


def physicality(a, b, *, depth_m, opening, wall_parts, band_ends, other_parts=(), eps) -> dict:
    """a, b: the reveal face (owner face point -> frame line point). wall_parts: [(key, roles, (x0, y0, x1, y1))];
    band_ends: [{"band_id", "state", "kind", "opening": [...], "segment": (x0, y0, x1, y1)}];
    other_parts: [(key, layer, (x0, y0, x1, y1))] - non-admitted parts, recorded as rejected when they cover a-b."""
    seg = [list(a), list(b)]
    if depth_m is not None and depth_m <= 0:
        return {"state": NONE, "segment": seg, "evidence": [], "rejected": [], "why": "frame flush with this face"}
    if math.dist(a, b) <= eps:
        return {"state": NONE, "segment": seg, "evidence": [], "rejected": [], "why": "zero-length reveal face"}
    ev = [{"kind": "ADMITTED_WALL_PART", "part": k, "roles": sorted(r)} for k, r, g in wall_parts
          if set(r) & set(ADMITTED_ROLES) and covered(a, b, g[:2], g[2:4], eps)]
    ev += [{"kind": "ESTABLISHED_WALL_BAND_END", "band_id": e["band_id"], "end_kind": e["kind"]} for e in band_ends
           if e["state"] == BAND_ESTABLISHED and e["kind"] == BAND_END_JAMB and any(opening in o for o in e["opening"])
           and covered(a, b, e["segment"][:2], e["segment"][2:4], eps)]
    rej = [{"part": k, "layer": lay, "why": "not an admitted wall / structural part"} for k, lay, g in other_parts
           if covered(a, b, g[:2], g[2:4], eps)]
    return {"state": ESTABLISHED if ev else UNRESOLVED, "segment": seg, "evidence": ev, "rejected": rej,
            "why": "physical surface established" if ev else
            "no admitted wall part and no established band end covers this reveal face"}


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID, "states": [ESTABLISHED, NONE, UNRESOLVED], "admitted_roles": list(ADMITTED_ROLES),
           "band_end": f"{BAND_ESTABLISHED} band, end kind {BAND_END_JAMB} for the same opening, covering the face",
           "order": "physicality first; finish (REVEAL_FINISH_POLICY_V1) only on an established surface",
           "never": ["a fixture / furniture / glazing / window / frame / aluminium line as a reveal surface",
                     "a finish default as proof of a surface", "symmetry with the opposite jamb",
                     "a reveal surface with zero depth", "an unresolved reveal inside a complete total"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec
