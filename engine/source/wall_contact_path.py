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


# ====================================================================================== V3 (R8.16)
"""WALL_CONTACT_PATH_POLICY_V3 - floor-contact skirting authority.

A plan cuts the building ABOVE the floor: a window in plan is not an opening at the floor. Every boundary span is
classified by FLOOR CONTACT (first match wins):
  PHYSICAL_OPENING_JAMB      the span lies on a jamb record (the short side of a door strip or of an open passage)
  TOPOLOGY_CLOSURE           a zero-material closure (zero on every path; it may only LOCATE a jamb record)
  DOOR_PRESENT               a door closure: skirting stops at the opening edge
  FULL_HEIGHT_GLAZED_OPENING glazing / closure whose floor contact is proven floor-level: the path breaks
  WINDOW_ABOVE_FLOOR         glazing whose sill is proven above the floor: the wall below carries skirting
                             (a trade-only SKIRTING_CONTINUITY_UNDER_WINDOW span; topology untouched)
  FLOOR_CONTACT_UNPROVEN     glazing without sill / floor evidence: withheld
  AUTHORISED_OBSTACLE_FACE   an isolated closed loop with owner physical obstacle authority
  COLUMN_FACE / REAL_WALL_FACE
  UNPROVEN_EDGE              anything else (withheld)
Jamb records (one per physical surface, counted once from the record, never from a closure edge):
  DOOR       the reveal sides of a door strip           -> ZERO skirting (DOOR_PRESENT: STOP_AT_OPENING)
  DOORLESS   the short sides of an OPEN_PASSAGE_SITE     -> counted when PHYSICAL (a drawn cap, or the end of an
                                                            ESTABLISHED band whose faces end flush) and the method
                                                            includes doorless jambs
The clear width of any opening is zero. A full-wall-tile room has no skirting.
"""

POLICY_ID_V3 = "WALL_CONTACT_PATH_POLICY_V3"
PHYSICAL_OPENING_JAMB, DOOR_PRESENT, DOORLESS_OPENING = "PHYSICAL_OPENING_JAMB", "DOOR_PRESENT", "DOORLESS_OPENING"
FULL_HEIGHT_GLAZED, WINDOW_ABOVE_FLOOR = "FULL_HEIGHT_GLAZED_OPENING", "WINDOW_ABOVE_FLOOR"
FLOOR_CONTACT_UNPROVEN, AUTHORISED_OBSTACLE_FACE, UNPROVEN_EDGE = "FLOOR_CONTACT_UNPROVEN", "AUTHORISED_OBSTACLE_FACE", \
    "UNPROVEN_EDGE"
ABOVE_FLOOR, FLOOR_LEVEL = "ABOVE_FLOOR", "FLOOR_LEVEL"
DOOR_JAMB, DOORLESS_JAMB = "DOOR", "DOORLESS"
CLASSES_V3 = (PHYSICAL_OPENING_JAMB, TOPOLOGY_CLOSURE, DOOR_PRESENT, FULL_HEIGHT_GLAZED, WINDOW_ABOVE_FLOOR,
              FLOOR_CONTACT_UNPROVEN, AUTHORISED_OBSTACLE_FACE, COLUMN_FACE, REAL_WALL_FACE, UNPROVEN_EDGE)
PAYABLE_V3 = (REAL_WALL_FACE, COLUMN_FACE, AUTHORISED_OBSTACLE_FACE, WINDOW_ABOVE_FLOOR)
WITHHELD_V3 = (FLOOR_CONTACT_UNPROVEN, UNPROVEN_EDGE)
PHYSICAL_WALL_ENDS = ("CAPPED", "ALIGNED_FREE_END", "OPENING_JAMB")
COMPUTED_WITH_WITHHELD = "COMPUTED_WITH_WITHHELD_SPANS"


@dataclass(frozen=True)
class SkirtingMethodV3:
    method_id: str
    version: int
    authority: dict
    door: str = "STOP_AT_OPENING_NO_JAMB"
    doorless_jambs: str = INCLUDED
    obstacle_faces: str = INCLUDED
    column_faces: str = INCLUDED

    @property
    def ref(self):
        return f"{self.method_id}@v{self.version}"


def floor_contact(*, sill_m=None, sill_authority=None, floor_level_authority=None) -> dict:
    """Floor contact of ONE glazed opening: a proven sill above the floor -> ABOVE_FLOOR; proven floor-level glazing /
    door -> FLOOR_LEVEL; otherwise UNPROVEN. A plan line is corroboration only, never the authority."""
    if floor_level_authority:
        return {"state": FLOOR_LEVEL, "authority": floor_level_authority}
    if sill_m is not None and sill_m > 0 and sill_authority:
        return {"state": ABOVE_FLOOR, "sill_m": sill_m, "authority": sill_authority}
    return {"state": FLOOR_CONTACT_UNPROVEN, "authority": None}


def _overlap(p0, p1, a, b, eps):
    """Collinear overlap length of segment p0-p1 with segment a-b (0 when not collinear within eps)."""
    if not (_on(p0, a, b, eps) or _on(p1, a, b, eps) or _on(a, p0, p1, eps) or _on(b, p0, p1, eps)):
        return 0.0
    L = math.dist(a, b)
    if L <= eps:
        return 0.0
    u = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
    if abs((p1[0] - p0[0]) * u[1] - (p1[1] - p0[1]) * u[0]) > eps or \
            abs((p0[0] - a[0]) * u[1] - (p0[1] - a[1]) * u[0]) > eps:
        return 0.0
    s0, s1 = sorted(((p0[0] - a[0]) * u[0] + (p0[1] - a[1]) * u[1], (p1[0] - a[0]) * u[0] + (p1[1] - a[1]) * u[1]))
    return max(0.0, min(s1, L) - max(s0, 0.0))


def passage_jambs(passage, bands_by_id, eps) -> list:
    """The two SHORT sides of an OPEN_PASSAGE_SITE as jamb records (LEFT = the passage band end, RIGHT = the target).
    A side is PHYSICAL when it is a wall end of an ESTABLISHED band (drawn cap or faces ending flush); a side that is
    the continuous face of another wall is CONTINUOUS_WALL_FACE (wall path already, never a jamb record)."""
    poly = [tuple(p) for p in passage["polygon"]]
    sides = sorted(((poly[i], poly[(i + 1) % 4]) for i in range(4)), key=lambda s: math.dist(*s))[:2]
    own = [tuple(map(tuple, j["segment"])) for j in passage.get("jamb_faces", [])]
    out = []
    for a, b in sides:
        rec = {"opening": passage["passage_id"], "kind": DOORLESS_JAMB, "segment": (a, b), "length": math.dist(a, b)}
        if any(_overlap(a, b, p, q, eps) >= math.dist(a, b) - 2 * eps for p, q in own):
            band = bands_by_id.get(passage["band_id"], {})
            ok = band.get("state") == "WALL_BAND_ESTABLISHED" and passage.get("end_kind") in PHYSICAL_WALL_ENDS
            rec.update(side="LEFT", source=f"BANDEND|{passage['band_id']}|{passage['band_end']}",
                       end_kind=passage.get("end_kind"), physical=ok)
        elif str(passage.get("target", "")).startswith("BANDEND|"):
            _, bid, k = passage["target"].split("|")
            band = bands_by_id.get(bid, {})
            kind = next((e["kind"] for e in band.get("ends", []) if e["end"] == int(k)), None)
            rec.update(side="RIGHT", source=passage["target"], end_kind=kind,
                       physical=band.get("state") == "WALL_BAND_ESTABLISHED" and kind in PHYSICAL_WALL_ENDS + (
                           "OPENING_JAMB",))
        else:
            rec.update(side="RIGHT", source=passage.get("target"), end_kind="CONTINUOUS_WALL_FACE", physical=False,
                       continuous_wall_face=True)
        out.append(rec)
    return out


def door_jambs(openings, closures) -> list:
    """The two reveal sides of every door strip (closures A and B) as DOOR jamb records - zero skirting."""
    geo = {c.source_id: c.geometry for c in closures}
    out = []
    for occ, st in sorted(openings.items()):
        if not st.get("closure_a") or not st.get("closure_b"):
            continue
        a, b = geo[st["closure_a"]], geo[st["closure_b"]]
        pa, pb = [(a[0], a[1]), (a[2], a[3])], [(b[0], b[1]), (b[2], b[3])]
        for p in pa:
            q = min(pb, key=lambda z: math.dist(p, z))
            out.append({"opening": occ, "kind": DOOR_JAMB, "segment": (p, q), "length": math.dist(p, q),
                        "physical": True, "source": "door strip reveal side"})
    return out


def classify_v3(edge, *, obstacle_authority=None, floor_contact_by_entity=None) -> str:
    src = edge["sources"]
    fc = floor_contact_by_entity or {}
    if any(s.startswith("TCLOSURE|") for s in src):
        return TOPOLOGY_CLOSURE
    if any(s.startswith("CLOSURE|GLAZED|") for s in src) or GLAZING_ROLE in edge["roles"]:
        st = {fc.get(_entity(s), {}).get("state") for s in src} | {fc.get(s, {}).get("state") for s in src}
        if FLOOR_LEVEL in st:
            return FULL_HEIGHT_GLAZED
        if ABOVE_FLOOR in st:
            return WINDOW_ABOVE_FLOOR                          # the sill authority proves the wall below
        return FLOOR_CONTACT_UNPROVEN
    if any(s.startswith("CLOSURE|") for s in src):
        return DOOR_PRESENT
    auth = obstacle_authority or {}
    ent = {_entity(s) for s in src}
    if ent & set(auth):
        return AUTHORISED_OBSTACLE_FACE if all(auth[e] == OWNER_PHYSICAL_OBSTACLE for e in ent & set(auth)) else \
            UNPROVEN_EDGE
    roles = set(edge["roles"])
    if roles and roles <= set(WALL_ROLES):
        return COLUMN_FACE if "STRUCTURAL_OBSTACLE" in roles else REAL_WALL_FACE
    return UNPROVEN_EDGE


def measure_v3(edges, method: SkirtingMethodV3, *, full_wall_tile=False, jambs=(), eps=0.0, obstacle_authority=None,
               floor_contact_by_entity=None) -> dict:
    """The skirting measurement of ONE room site (native units). Returns payable length, per-class components,
    excluded spans, withheld spans, the under-window continuity spans and the jamb records counted."""
    if full_wall_tile:
        return {"state": NO_SKIRTING, "length": 0.0, "components": {}, "excluded": {}, "withheld": [],
                "continuity_under_windows": [], "jambs_counted": [], "method": method.ref}
    comp, excl, withheld, cont, touched = defaultdict(float), defaultdict(float), [], [], {}
    for e in edges:
        ln = e["length"]
        jpart = 0.0
        if "p0" in e:
            for i, j in enumerate(jambs):
                ov = _overlap(e["p0"], e["p1"], j["segment"][0], j["segment"][1], eps)
                if ov > eps:
                    touched[i] = touched.get(i, 0.0) + ov
                    jpart += ov
        rest = max(0.0, ln - jpart)
        if rest <= eps:
            continue                                           # the whole edge is a jamb surface (record counts)
        c = classify_v3(e, obstacle_authority=obstacle_authority, floor_contact_by_entity=floor_contact_by_entity)
        if c in (REAL_WALL_FACE,):
            comp[c] += rest
        elif c in (COLUMN_FACE, AUTHORISED_OBSTACLE_FACE):
            mode = method.column_faces if c == COLUMN_FACE else method.obstacle_faces
            if mode == INCLUDED:
                comp[c] += rest
            elif mode == EXCLUDED:
                excl[c] += rest
            else:
                withheld.append({"class": c, "length": rest, "sources": e["sources"][:3]})
        elif c == WINDOW_ABOVE_FLOOR:
            comp[c] += rest
            cont.append({"span": "SKIRTING_CONTINUITY_UNDER_WINDOW", "length": rest, "sources": e["sources"][:3],
                         "material_authority": "real wall below the window (floor contact)"})
        elif c in (DOOR_PRESENT, TOPOLOGY_CLOSURE, FULL_HEIGHT_GLAZED):
            excl[c] += rest
        else:
            withheld.append({"class": c, "length": rest, "sources": e["sources"][:3]})
    counted = []
    for i, ov in sorted(touched.items()):
        j = jambs[i]
        if j["kind"] == DOOR_JAMB:
            excl["DOOR_JAMB"] += j["length"]
            counted.append(dict(j, counted=0.0, why="DOOR_PRESENT: no jamb skirting"))
        elif j.get("physical") and method.doorless_jambs == INCLUDED:
            comp[PHYSICAL_OPENING_JAMB] += j["length"]
            counted.append(dict(j, counted=j["length"]))
        else:
            excl["DOORLESS_JAMB_NOT_COUNTED"] += j["length"]
            counted.append(dict(j, counted=0.0, why="not physical" if not j.get("physical") else "method excludes"))
    total = math.fsum(comp.values())
    return {"state": COMPUTED_WITH_WITHHELD if withheld else COMPUTED, "length": total,
            "components": dict(sorted(comp.items())), "excluded": dict(sorted(excl.items())), "withheld": withheld,
            "withheld_length": math.fsum(w["length"] for w in withheld), "continuity_under_windows": cont,
            "jambs_counted": counted, "method": method.ref}


def policy_record_v3() -> dict:
    rec = {"policy_id": POLICY_ID_V3, "extends": POLICY_ID_V2, "classes": list(CLASSES_V3), "payable": list(PAYABLE_V3),
           "withheld": list(WITHHELD_V3), "jamb_records": {DOOR_JAMB: "zero (STOP_AT_OPENING)",
                                                           DOORLESS_JAMB: "physical short sides counted once"},
           "physical_wall_ends": list(PHYSICAL_WALL_ENDS),
           "floor_contact": [ABOVE_FLOOR, FLOOR_LEVEL, FLOOR_CONTACT_UNPROVEN],
           "never": ["a plan-cut window as a floor opening without vertical evidence", "a topology closure as material "
                     "or skirting", "a jamb counted from a closure edge", "skirting across any clear opening",
                     "a door jamb return", "a room polygon perimeter", "a furniture / wardrobe deduction",
                     "skirting in a full-wall-tile room", "a published quantity without a frozen, blind-tested policy"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec


# ====================================================================================== V4 (R8.17)
"""WALL_CONTACT_PATH_POLICY_V4 - V3 with OPENING-SIDE RELATIONS kept apart from PHYSICAL JAMB SURFACES.

V3-O1 (R8.16): measure_v3 subtracted the overlap of EVERY jamb record from the wall path before testing whether the
record was physical, so a non-physical opening side (the continuous face of another wall) consumed real wall contact
that no class then counted. V4:
  * only a PHYSICAL jamb record may consume path length: a door / glazed-door strip reveal side, or the end of an
    ESTABLISHED band (drawn cap / faces ending flush); a record whose source is a topology closure is never physical;
  * a non-physical record is an OPENING_SIDE annotation: it never shortens an edge;
  * every edge length is conserved: consumed by a physical jamb + classified span (payable / excluded / withheld);
  * opening PHYSICAL CLASS is resolved before any sill fact: a glazed occurrence whose authority says it is a DOOR
    (e.g. SLIDING_GLAZED_DOOR reaching the floor) is SLIDING_GLAZED_DOOR_TO_FLOOR / DOOR_PRESENT - zero across, its
    jambs zero - and can never receive SKIRTING_CONTINUITY_UNDER_WINDOW;
  * trade eligibility is applied after geometry: door / glazed-door jambs 0, doorless physical jambs once.
Topology is never touched (trade measurement only).
"""

POLICY_ID_V4 = "WALL_CONTACT_PATH_POLICY_V4"
SLIDING_GLAZED_DOOR_TO_FLOOR = "SLIDING_GLAZED_DOOR_TO_FLOOR"
SLIDING_GLAZED_DOOR, GLAZED_DOOR, EXTERNAL_DOOR = "SLIDING_GLAZED_DOOR", "GLAZED_DOOR", "EXTERNAL_DOOR"
DOOR_CLASSES = (SLIDING_GLAZED_DOOR, GLAZED_DOOR, EXTERNAL_DOOR)
GLAZED_DOOR_JAMB = "GLAZED_DOOR"
CLASSES_V4 = (PHYSICAL_OPENING_JAMB, TOPOLOGY_CLOSURE, DOOR_PRESENT, SLIDING_GLAZED_DOOR_TO_FLOOR,
              FULL_HEIGHT_GLAZED, WINDOW_ABOVE_FLOOR, FLOOR_CONTACT_UNPROVEN, AUTHORISED_OBSTACLE_FACE, COLUMN_FACE,
              REAL_WALL_FACE, UNPROVEN_EDGE)
PAYABLE_V4 = PAYABLE_V3
EXCLUDED_V4 = (DOOR_PRESENT, SLIDING_GLAZED_DOOR_TO_FLOOR, TOPOLOGY_CLOSURE, FULL_HEIGHT_GLAZED)
ZERO_JAMB_KINDS = (DOOR_JAMB, GLAZED_DOOR_JAMB)


def opening_contact(*, physical_class=None, contact=None, authority=None, sill_m=None, sill_authority=None) -> dict:
    """Floor contact + physical class of ONE glazed occurrence. A physical-class authority (an owner / source fact
    saying what the object IS) is resolved FIRST: a door class is never a window, whatever sill fact exists."""
    to_floor = contact in ("OPENING_TO_FLOOR", FLOOR_LEVEL)
    if physical_class and authority:
        if physical_class in DOOR_CLASSES:
            return {"state": FLOOR_LEVEL if to_floor else FLOOR_CONTACT_UNPROVEN, "physical_class": physical_class,
                    "authority": authority}
        if to_floor:
            return {"state": FLOOR_LEVEL, "physical_class": physical_class, "authority": authority}
    st = floor_contact(sill_m=sill_m, sill_authority=sill_authority)
    return dict(st, physical_class=physical_class or ("NORMAL_WINDOW" if st["state"] == ABOVE_FLOOR else None))


def is_physical_jamb(j) -> bool:
    """Positive physical evidence only: the record says physical AND its source is a real surface, never a topology
    closure or a helper relation."""
    src = str(j.get("source") or "")
    return bool(j.get("physical")) and not src.startswith(("TCLOSURE|", "CLOSURE|")) and \
        not j.get("continuous_wall_face")


def glazed_door_jambs(closures, contact_by_opening) -> list:
    """The two reveal sides of every glazed occurrence whose physical class is a DOOR (from its face closures F1 / F2)
    as zero-skirting door jamb records."""
    by = defaultdict(dict)
    for c in closures:
        sid = c.source_id
        if sid.startswith("CLOSURE|GLAZED|") and sid.rsplit("|", 1)[1] in ("F1", "F2"):
            by[sid.split("|", 1)[1].rsplit("|", 1)[0]][sid.rsplit("|", 1)[1]] = c.geometry
    out, seen = [], set()
    for oid, fs in sorted(by.items()):
        st = contact_by_opening.get(oid) or {}
        if st.get("physical_class") not in DOOR_CLASSES or set(fs) != {"F1", "F2"}:
            continue
        a, b = fs["F1"], fs["F2"]
        pa, pb = [(a[0], a[1]), (a[2], a[3])], [(b[0], b[1]), (b[2], b[3])]
        for p in pa:
            q = min(pb, key=lambda z: math.dist(p, z))
            key = tuple(sorted((tuple(round(v, 6) for v in p), tuple(round(v, 6) for v in q))))
            if key in seen:                                   # two glazing lines of ONE door share its reveal sides
                continue
            seen.add(key)
            out.append({"opening": oid, "kind": GLAZED_DOOR_JAMB, "segment": (p, q), "length": math.dist(p, q),
                        "physical": True, "source": "glazed door strip reveal side",
                        "physical_class": st["physical_class"]})
    return out


def classify_v4(edge, *, obstacle_authority=None, floor_contact_by_entity=None) -> str:
    src = edge["sources"]
    fc = floor_contact_by_entity or {}
    if any(s.startswith("TCLOSURE|") for s in src):
        return TOPOLOGY_CLOSURE
    if any(s.startswith("CLOSURE|GLAZED|") for s in src) or GLAZING_ROLE in edge["roles"]:
        recs = [fc.get(s) or fc.get(_entity(s)) for s in src]
        recs = [r for r in recs if r]
        if any(r.get("physical_class") in DOOR_CLASSES for r in recs):     # the object IS a door: never a window
            door = [r for r in recs if r.get("physical_class") in DOOR_CLASSES]
            if any(r["physical_class"] == SLIDING_GLAZED_DOOR and r["state"] == FLOOR_LEVEL for r in door):
                return SLIDING_GLAZED_DOOR_TO_FLOOR
            return DOOR_PRESENT if all(r["state"] == FLOOR_LEVEL for r in door) else FLOOR_CONTACT_UNPROVEN
        st = {r["state"] for r in recs}
        if FLOOR_LEVEL in st:
            return FULL_HEIGHT_GLAZED
        if ABOVE_FLOOR in st:
            return WINDOW_ABOVE_FLOOR
        return FLOOR_CONTACT_UNPROVEN
    return classify_v3(edge, obstacle_authority=obstacle_authority)


def measure_v4(edges, method: SkirtingMethodV3, *, full_wall_tile=False, jambs=(), eps=0.0, obstacle_authority=None,
               floor_contact_by_entity=None) -> dict:
    """The skirting measurement of ONE room site (native units) under V4: only physical jamb records consume path
    length; every edge length is conserved and reported."""
    boundary = math.fsum(e["length"] for e in edges)
    if full_wall_tile:
        return {"state": NO_SKIRTING, "length": 0.0, "components": {}, "excluded": {}, "withheld": [],
                "continuity_under_windows": [], "jambs_counted": [], "opening_side_annotations": [],
                "conservation": {"boundary": boundary, "reconciles": True, "note": "no skirting path"},
                "method": method.ref}
    comp, excl, withheld, cont, touched, notes = defaultdict(float), defaultdict(float), [], [], {}, {}
    consumed_total, classified_total = 0.0, 0.0
    for e in edges:
        ln = e["length"]
        jpart = 0.0
        if "p0" in e:
            for i, j in enumerate(jambs):
                ov = _overlap(e["p0"], e["p1"], j["segment"][0], j["segment"][1], eps)
                if ov <= eps:
                    continue
                if is_physical_jamb(j):
                    touched[i] = touched.get(i, 0.0) + ov
                    jpart += ov
                else:
                    notes[i] = notes.get(i, 0.0) + ov             # annotation only: the edge keeps its length
        jpart = min(jpart, ln)
        rest = ln - jpart
        consumed_total += jpart
        if rest <= eps:
            continue
        classified_total += rest
        c = classify_v4(e, obstacle_authority=obstacle_authority, floor_contact_by_entity=floor_contact_by_entity)
        if c == REAL_WALL_FACE:
            comp[c] += rest
        elif c in (COLUMN_FACE, AUTHORISED_OBSTACLE_FACE):
            mode = method.column_faces if c == COLUMN_FACE else method.obstacle_faces
            if mode == INCLUDED:
                comp[c] += rest
            elif mode == EXCLUDED:
                excl[c] += rest
            else:
                withheld.append({"class": c, "length": rest, "sources": e["sources"][:3]})
        elif c == WINDOW_ABOVE_FLOOR:
            comp[c] += rest
            cont.append({"span": "SKIRTING_CONTINUITY_UNDER_WINDOW", "length": rest, "sources": e["sources"][:3],
                         "material_authority": "real wall below the window (floor contact)"})
        elif c in EXCLUDED_V4:
            excl[c] += rest
        else:
            withheld.append({"class": c, "length": rest, "sources": e["sources"][:3]})
    counted = []
    for i, ov in sorted(touched.items()):
        j = jambs[i]
        if j["kind"] in ZERO_JAMB_KINDS:
            excl["DOOR_JAMB"] += j["length"]
            counted.append(dict(j, counted=0.0, consumed=ov, why="DOOR_PRESENT: no jamb skirting"))
        elif method.doorless_jambs == INCLUDED:
            comp[PHYSICAL_OPENING_JAMB] += j["length"]
            counted.append(dict(j, counted=j["length"], consumed=ov))
        else:
            excl["DOORLESS_JAMB_NOT_COUNTED"] += j["length"]
            counted.append(dict(j, counted=0.0, consumed=ov, why="method excludes"))
    annotations = [dict(jambs[i], overlap=ov, consumed=0.0, why="OPENING_SIDE relation, not a physical jamb")
                   for i, ov in sorted(notes.items())]
    total = math.fsum(comp.values())
    wl = math.fsum(w["length"] for w in withheld)
    span_sum = math.fsum(v for k, v in comp.items() if k != PHYSICAL_OPENING_JAMB) + \
        math.fsum(v for k, v in excl.items() if k not in ("DOOR_JAMB", "DOORLESS_JAMB_NOT_COUNTED")) + wl
    cons = {"boundary": boundary, "consumed_by_physical_jambs": consumed_total, "classified": classified_total,
            "class_sum": span_sum, "residual": boundary - consumed_total - span_sum}
    cons["reconciles"] = abs(cons["residual"]) <= max(eps, 1e-9) * (1 + len(edges)) and \
        abs(classified_total - span_sum) <= max(eps, 1e-9) * (1 + len(edges))
    return {"state": COMPUTED_WITH_WITHHELD if withheld else COMPUTED, "length": total,
            "components": dict(sorted(comp.items())), "excluded": dict(sorted(excl.items())), "withheld": withheld,
            "withheld_length": wl, "continuity_under_windows": cont, "jambs_counted": counted,
            "opening_side_annotations": annotations, "conservation": cons, "method": method.ref}


def policy_record_v4() -> dict:
    rec = {"policy_id": POLICY_ID_V4, "extends": POLICY_ID_V3, "classes": list(CLASSES_V4),
           "payable": list(PAYABLE_V4), "excluded": list(EXCLUDED_V4), "withheld": list(WITHHELD_V3),
           "door_classes": list(DOOR_CLASSES),
           "jamb_records": {DOOR_JAMB: "zero (STOP_AT_OPENING)", GLAZED_DOOR_JAMB: "zero (a glazed DOOR is a door)",
                            DOORLESS_JAMB: "physical short sides counted once"},
           "physical_jamb": "physical = true by positive source evidence (strip reveal side, or an ESTABLISHED band "
                            "end CAPPED / ALIGNED_FREE_END / OPENING_JAMB); never a topology closure source; never a "
                            "CONTINUOUS_WALL_FACE side",
           "consumption": "only a physical jamb record may consume path length; a non-physical record is an "
                          "OPENING_SIDE annotation and never shortens an edge",
           "conservation": "per site: boundary = consumed by physical jambs + payable spans + excluded spans + "
                           "withheld spans (checked)",
           "resolution_order": ["physical class authority (a door is never a window)", "floor-level authority",
                                "sill authority", "otherwise FLOOR_CONTACT_UNPROVEN (withheld)"],
           "physical_wall_ends": list(PHYSICAL_WALL_ENDS),
           "fixes": ["V3-O1: non-physical opening-side records consumed continuous wall face"],
           "never": ["a non-physical record consuming wall contact", "a topology closure as material, skirting or a "
                     "jamb", "SKIRTING_CONTINUITY_UNDER_WINDOW at a door-class glazed occurrence", "skirting across "
                     "any clear opening", "a door / glazed-door jamb return", "a room polygon perimeter",
                     "a furniture / wardrobe deduction", "skirting in a full-wall-tile room",
                     "a published quantity without a frozen, blind-tested policy"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec
