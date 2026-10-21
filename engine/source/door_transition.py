"""DOOR FINISH TRANSITION (R8.14) - where one floor finish meets another inside a door threshold, as a TRADE
measurement subdivision of ONE physical opening site (never a topology split of the building).

The threshold site is the reveal strip between the door's two parallel face closures (topology.opening_closures:
closure A along the closed leaf, closure B across the far jamb ends). Its DOOR_FINISH_TRANSITION_PLANE is taken from,
in order of authority:
  1 AUTHORED_LEAF_PLANE   the door symbol's hinge (closed-leaf line) lies STRICTLY inside the reveal (beyond eps_r
                          from both faces): the frame / leaf position is drawn
  2 OWNER_CENTRED_DOOR    a bound, scoped owner method fact says the door sits in the middle, applied to the
                          ESTABLISHED parallel face pair: the mid-plane between the two face closures
  -  otherwise UNRESOLVED_TRANSITION_PLANE (never wall thickness / 2 by default)
A symbol whose hinge lies ON a face (SYMBOL_ANCHORED_AT_FACE) establishes the opening (width, swing, host wall), not
the frame plane.

Allocation of the strip (area from the physical threshold site; the parts always sum to it exactly):
  MARBLE_THRESHOLD_EXPLICIT   an explicit marble / threshold evidence record names this opening -> one region
  CONTINUOUS_SAME_FINISH      both sides carry the same floor treatment -> one region, counted once
  SPLIT_AT_DOOR_PLANE         different treatments -> side A up to the plane, side B beyond it
  UNRESOLVED_FINISH           a side has no authoritative treatment
  UNRESOLVED_TRANSITION_PLANE different treatments but no plane authority
  UNRESOLVED_GEOMETRY         the faces are not parallel or the site area is not the strip area
For a CEILING trade the threshold is the door's top reveal (US-07 type rule): NOT_IN_TRADE (recorded for reveals).

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib
import json
import math

POLICY_ID = "DOOR_TRANSITION_POLICY_V1"
AUTHORED_LEAF_PLANE = "AUTHORED_LEAF_PLANE"
OWNER_CENTRED_DOOR = "OWNER_CENTRED_DOOR"
UNRESOLVED_PLANE = "UNRESOLVED_TRANSITION_PLANE"
SYMBOL_AT_FACE = "SYMBOL_ANCHORED_AT_FACE"
MARBLE = "MARBLE_THRESHOLD_EXPLICIT"
CONTINUOUS = "CONTINUOUS_SAME_FINISH"
SPLIT = "SPLIT_AT_DOOR_PLANE"
UNRESOLVED_FINISH = "UNRESOLVED_FINISH"
UNRESOLVED_GEOMETRY = "UNRESOLVED_GEOMETRY"
NOT_IN_TRADE = "NOT_IN_TRADE"
RESOLVED = (MARBLE, CONTINUOUS, SPLIT)
PARAMS = {"inside_reveal_margin": "eps_r (a hinge within eps_r of a face is ON that face)",
          "parallel": "|cross(u_A, u_B)| x length <= eps_r and equal lengths within eps_r",
          "area_check": "|site area - width x thickness| <= eps_r x site perimeter",
          "split_areas": "side A = site area x offset / thickness; side B = site area - side A (exact sum)"}


def _sub(p, q):
    return (p[0] - q[0], p[1] - q[1])


def transition_plane(face_a, face_b, hinge, *, eps_r, owner_centred=None) -> dict:
    """face_a / face_b: ((x, y), (x, y)) of the two door-face closures; hinge: the door symbol's hinge point.
    owner_centred: the ref of a bound owner method fact establishing a centred door, or None."""
    (a0, a1), (b0, b1) = face_a, face_b
    la, lb = math.dist(a0, a1), math.dist(b0, b1)
    if la <= eps_r or lb <= eps_r:
        return {"authority": UNRESOLVED_PLANE, "geometry": UNRESOLVED_GEOMETRY, "why": "degenerate face"}
    u = ((a1[0] - a0[0]) / la, (a1[1] - a0[1]) / la)
    n = (-u[1], u[0])
    ub = _sub(b1, b0)
    if abs(u[0] * ub[1] - u[1] * ub[0]) > eps_r or abs(la - lb) > eps_r:
        return {"authority": UNRESOLVED_PLANE, "geometry": UNRESOLVED_GEOMETRY, "why": "faces not parallel / equal"}
    off = lambda p: _sub(p, a0)[0] * n[0] + _sub(p, a0)[1] * n[1]
    t = off(b0)
    if t < 0:
        n, t = (-n[0], -n[1]), -t
        off = lambda p: _sub(p, a0)[0] * n[0] + _sub(p, a0)[1] * n[1]
    rec = {"width": la, "thickness": t, "normal_from_a": n, "hinge_offset": None if hinge is None else off(hinge)}
    h = rec["hinge_offset"]
    if h is not None and eps_r < h < t - eps_r:
        return dict(rec, authority=AUTHORED_LEAF_PLANE, offset=h, symbol="HINGE_INSIDE_REVEAL")
    sym = SYMBOL_AT_FACE if h is not None and (abs(h) <= eps_r or abs(h - t) <= eps_r) else "NO_INSIDE_LEAF"
    if owner_centred:
        return dict(rec, authority=OWNER_CENTRED_DOOR, offset=t / 2, symbol=sym, fact=owner_centred,
                    evidence="ESTABLISHED_PARALLEL_FACE_PAIR (closures A / B)")
    return dict(rec, authority=UNRESOLVED_PLANE, offset=None, symbol=sym)


def allocate(site_area, perimeter, plane, side_a, side_b, *, eps_r, marble=None) -> dict:
    """side_a / side_b: {"site", "class", "treatment"} of the rooms beyond face A / face B; marble: an explicit
    evidence record {"ref", ...} naming this opening, or None."""
    sides = {"A": side_a, "B": side_b}
    rec = {"site_area": site_area, "plane": {k: plane.get(k) for k in ("authority", "offset", "thickness", "width",
                                                                         "symbol", "fact", "hinge_offset")},
           "sides": sides, "marble_evidence": marble, "regions": []}
    if plane.get("geometry") == UNRESOLVED_GEOMETRY:
        return dict(rec, state=UNRESOLVED_GEOMETRY)
    if abs(site_area - plane["width"] * plane["thickness"]) > eps_r * perimeter:
        return dict(rec, state=UNRESOLVED_GEOMETRY, why="the site is not the face-pair strip")
    if marble is not None:
        return dict(rec, state=MARBLE, regions=[{"side": "AB", "treatment": MARBLE, "area": site_area}])
    ta, tb = side_a.get("treatment"), side_b.get("treatment")
    if ta is None or tb is None:
        return dict(rec, state=UNRESOLVED_FINISH)
    if ta == tb:
        return dict(rec, state=CONTINUOUS, regions=[{"side": "AB", "site": [side_a["site"], side_b["site"]],
                                                     "treatment": ta, "area": site_area}])
    if plane["authority"] == UNRESOLVED_PLANE:
        return dict(rec, state=UNRESOLVED_PLANE)
    a = site_area * plane["offset"] / plane["thickness"]
    return dict(rec, state=SPLIT, regions=[{"side": "A", "site": side_a["site"], "treatment": ta, "area": a},
                                           {"side": "B", "site": side_b["site"], "treatment": tb,
                                            "area": site_area - a}])


def contribution(alloc, treatment) -> float:
    """The area this allocation gives to one floor treatment (each region exactly once)."""
    return math.fsum(r["area"] for r in alloc.get("regions", []) if r["treatment"] == treatment)


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID, "plane_authority": [AUTHORED_LEAF_PLANE, OWNER_CENTRED_DOOR, UNRESOLVED_PLANE],
           "states": [MARBLE, CONTINUOUS, SPLIT, UNRESOLVED_FINISH, UNRESOLVED_PLANE, UNRESOLVED_GEOMETRY,
                      NOT_IN_TRADE], "params": PARAMS,
           "never": ["wall thickness / 2 without a scoped owner fact", "the whole strip to one side of a split",
                     "a strip outside every floor quantity", "a strip counted twice", "marble without explicit evidence",
                     "a topology split of the building"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec
