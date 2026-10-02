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
from dataclasses import dataclass

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
            rec = {"sources": sorted(e["sources"]), "roles": sorted(e["roles"]), "length": ln, "hole": hole}
            if e["kind"] == "S":
                rec["p0"], rec["p1"] = tuple(arr.nodes[e["n0"]]), tuple(arr.nodes[e["n1"]])
            out.append(rec)
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


# ====================================================================================== V2 (R8.15)
"""WALL_CONTACT_PATH_POLICY_V2 - a PHYSICAL PATH (what meets the floor at a vertical surface) kept apart from the
SKIRTING MEASUREMENT REGION (what a trade method counts on it).

Classes (V1 classes refined; first match wins):
  OPENING_JAMB      the edge lies on a jamb face of an open passage (drawn cap OR zero-material topology closure):
                    a reveal surface, never room wall face - counted only under a RETURN method
  TOPOLOGY_CLOSURE  any other zero-material closure (zero length on every path)
  GLAZED_OPENING    a glazing closure across an opening
  DOOR_OPENING      a door closure
  OBSTACLE_FACE     an edge of an isolated closed loop WITH physical obstacle authority (obstacle_authority)
  UNPROVEN_OBSTACLE an edge of an isolated closed loop without it (withheld)
  WINDOW_OPENING    a glazing line lying on a wall face line (roles GLAZING_BOUNDARY + wall roles)
  COLUMN_FACE       a wall-role edge carrying a STRUCTURAL_OBSTACLE source
  REAL_WALL_FACE    a wall-role edge
  OTHER             anything else (withheld)
Furniture, wardrobes and joinery are never site boundaries, so the wall behind them stays on both paths.

A SkirtingMethod states, with its authority, what the measurement does with each physical condition:
  window_treatment  DEDUCT_EVERY_WINDOW_WIDTH (every window / glazed width off, wall below or not) |
                    FOLLOW_WALL_BELOW (included where wall stands below, off at floor-level glazing, withheld if
                    unknown)
  jamb_return       NO_RETURN | RETURN_TO_FRAME (jamb faces counted) | UNRESOLVED (withheld)
  obstacle_faces / column_faces   INCLUDED | EXCLUDED | UNRESOLVED
A full-wall-tile room has NO skirting whatever its path. Any withheld length makes the room INCOMPLETE (no number).
"""

POLICY_ID_V2 = "WALL_CONTACT_PATH_POLICY_V2"
OPENING_JAMB, COLUMN_FACE, OBSTACLE_FACE, WINDOW_OPENING = "OPENING_JAMB", "COLUMN_FACE", "OBSTACLE_FACE", \
    "WINDOW_OPENING"
GLAZING_ROLE = "GLAZING_BOUNDARY"
OWNER_PHYSICAL_OBSTACLE = "OWNER_PHYSICAL_OBSTACLE"
DEDUCT_WINDOWS, FOLLOW_WALL_BELOW = "DEDUCT_EVERY_WINDOW_WIDTH", "FOLLOW_WALL_BELOW"
NO_RETURN, RETURN_TO_FRAME, UNRESOLVED = "NO_RETURN", "RETURN_TO_FRAME", "UNRESOLVED"
INCLUDED, EXCLUDED = "INCLUDED", "EXCLUDED"
COMPUTED, INCOMPLETE = "COMPUTED", "INCOMPLETE_WITHHELD"
CLASSES_V2 = (OPENING_JAMB, TOPOLOGY_CLOSURE, GLAZED_OPENING, DOOR_OPENING, OBSTACLE_FACE, UNPROVEN_OBSTACLE,
              WINDOW_OPENING, COLUMN_FACE, REAL_WALL_FACE, OTHER)
PHYSICAL_CONTACT = (REAL_WALL_FACE, COLUMN_FACE, OBSTACLE_FACE, OPENING_JAMB)


@dataclass(frozen=True)
class SkirtingMethod:
    method_id: str
    version: int
    authority: dict                                   # parameter -> source reference(s)
    window_treatment: str = DEDUCT_WINDOWS
    jamb_return: str = NO_RETURN
    obstacle_faces: str = INCLUDED
    column_faces: str = INCLUDED

    @property
    def ref(self):
        return f"{self.method_id}@v{self.version}"


def _on(p, a, b, eps):
    ax, ay, bx, by = a[0], a[1], b[0], b[1]
    L = math.dist(a, b)
    if L <= eps:
        return math.dist(p, a) <= eps
    t = ((p[0] - ax) * (bx - ax) + (p[1] - ay) * (by - ay)) / (L * L)
    if t < -eps / L or t > 1 + eps / L:
        return False
    return abs((bx - ax) * (p[1] - ay) - (by - ay) * (p[0] - ax)) / L <= eps


def classify_v2(edge, *, obstacle_authority=None, jamb_segments=(), eps=0.0) -> str:
    """obstacle_authority: {isolated entity: state}; jamb_segments: [((x, y), (x, y))] of open-passage jamb faces."""
    src = edge["sources"]
    if "p0" in edge and any(_on(edge["p0"], a, b, eps) and _on(edge["p1"], a, b, eps) for a, b in jamb_segments):
        return OPENING_JAMB
    if any(s.startswith("TCLOSURE|") for s in src):
        return TOPOLOGY_CLOSURE
    if any(s.startswith("CLOSURE|GLAZED|") for s in src):
        return GLAZED_OPENING
    if any(s.startswith("CLOSURE|") for s in src):
        return DOOR_OPENING
    auth = obstacle_authority or {}
    ent = {_entity(s) for s in src}
    if ent & set(auth):
        return OBSTACLE_FACE if all(auth[e] == OWNER_PHYSICAL_OBSTACLE for e in ent & set(auth)) else \
            UNPROVEN_OBSTACLE
    roles = set(edge["roles"])
    if GLAZING_ROLE in roles and roles - {GLAZING_ROLE} and roles - {GLAZING_ROLE} <= set(WALL_ROLES):
        return WINDOW_OPENING
    if roles and roles <= set(WALL_ROLES):
        return COLUMN_FACE if "STRUCTURAL_OBSTACLE" in roles else REAL_WALL_FACE
    return OTHER


def physical_path(edges, **kw) -> dict:
    """What meets the floor at a vertical surface, per class - a record, never a quantity."""
    by = defaultdict(lambda: [0, 0.0])
    for e in edges:
        c = classify_v2(e, **kw)
        by[c][0] += 1
        by[c][1] += e["length"]
    return {"by_class": {k: {"edges": v[0], "length": v[1]} for k, v in sorted(by.items())},
            "floor_contact_length": math.fsum(v[1] for k, v in by.items() if k in PHYSICAL_CONTACT),
            "window_segments_wall_below": "per opening (source / owner evidence)"}


def measure(edges, method: SkirtingMethod, *, full_wall_tile=False, wall_below=None, **kw) -> dict:
    """The skirting measurement of ONE room site under a method. wall_below: {glazing source entity: True / False}
    (FOLLOW_WALL_BELOW only). Lengths are in the edges' native unit."""
    if full_wall_tile:
        return {"state": NO_SKIRTING, "length": 0.0, "components": {}, "excluded": {}, "withheld": [],
                "method": method.ref}
    wall_below = wall_below or {}
    comp, excl, withheld = defaultdict(float), defaultdict(float), []
    for e in edges:
        c = classify_v2(e, **kw)
        if c == REAL_WALL_FACE:
            comp[c] += e["length"]
            continue
        if c in (COLUMN_FACE, OBSTACLE_FACE):
            mode = method.column_faces if c == COLUMN_FACE else method.obstacle_faces
            (comp if mode == INCLUDED else excl)[c] += e["length"] if mode != UNRESOLVED else 0.0
            if mode == UNRESOLVED:
                withheld.append({"class": c, "length": e["length"], "sources": e["sources"][:3]})
            continue
        if c == OPENING_JAMB:
            if method.jamb_return == RETURN_TO_FRAME:
                comp[c] += e["length"]
            elif method.jamb_return == NO_RETURN:
                excl[c] += e["length"]
            else:
                withheld.append({"class": c, "length": e["length"], "sources": e["sources"][:3]})
            continue
        if c in (WINDOW_OPENING, GLAZED_OPENING):
            if method.window_treatment == DEDUCT_WINDOWS:
                excl[c] += e["length"]
                continue
            wb = {wall_below.get(_entity(s)) for s in e["sources"]} - {None}
            if wb == {True}:
                comp[c] += e["length"]
            elif wb == {False}:
                excl[c] += e["length"]
            else:
                withheld.append({"class": c, "length": e["length"], "sources": e["sources"][:3],
                                 "why": "wall below the opening not established"})
            continue
        if c in (DOOR_OPENING, TOPOLOGY_CLOSURE):
            excl[c] += e["length"]
            continue
        withheld.append({"class": c, "length": e["length"], "sources": e["sources"][:3]})
    return {"state": INCOMPLETE if withheld else COMPUTED,
            "length": None if withheld else math.fsum(comp.values()),
            "length_without_withheld": math.fsum(comp.values()), "components": dict(sorted(comp.items())),
            "excluded": dict(sorted(excl.items())), "withheld": withheld, "method": method.ref}


def policy_record_v2() -> dict:
    rec = {"policy_id": POLICY_ID_V2, "extends": POLICY_ID, "classes": list(CLASSES_V2),
           "physical_contact": list(PHYSICAL_CONTACT),
           "method_parameters": {"window_treatment": [DEDUCT_WINDOWS, FOLLOW_WALL_BELOW],
                                 "jamb_return": [NO_RETURN, RETURN_TO_FRAME, UNRESOLVED],
                                 "obstacle_faces": [INCLUDED, EXCLUDED, UNRESOLVED],
                                 "column_faces": [INCLUDED, EXCLUDED, UNRESOLVED]},
           "always_off": [DOOR_OPENING, TOPOLOGY_CLOSURE], "withheld": [UNPROVEN_OBSTACLE, OTHER],
           "full_wall_tile": NO_SKIRTING, "incomplete": "any withheld length -> no number for that room",
           "never": ["a room polygon perimeter", "skirting across a door or an open passage", "skirting on a "
                     "topology closure", "a furniture / wardrobe deduction", "skirting in a full-wall-tile room",
                     "a jamb return without a RETURN method", "a window rule from a layer name alone",
                     "a published quantity without a frozen, blind-tested policy"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec
