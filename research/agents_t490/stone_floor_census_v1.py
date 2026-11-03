"""STONE_FLOOR_CENSUS_V1 (T-490, rule R-T490-1): applicability and measure of a stone / marble FLOOR finish (B3-03)
for entrance, stair-hall, landing and threshold spaces, with the overlap against the families that already carry them.

Any villa. No layer name, room id or dimension of a training villa is in this module.

R-T490-1 (scope: floor finishes of entrance / stair-hall spaces; provenance T-490):
  1. Define the element first: ROOM_FLOOR (a floor at a storey level inside a room or hall), STAIR_LANDING /
     STAIR_ARRIVAL / TREADS (parts of a stair, UP-STAIR-005 / OWNER_RULE_STAIRS_2026-10-24), THRESHOLD (the strip in a
     door's wall thickness, listed by opening id, R-T246), FLOOR_OR_LANDING (a floor at the foot / top of a flight
     whose landing depth is printed nowhere: storey floor or landing is not established), UNREAD (a drawn piece not
     yet classed). No default rule applies to FLOOR_OR_LANDING (neither default is written for it).
  2. Material by the evidence order: a project source (finish schedule, plan note, legend) > an OWNER CONFIRMED rule
     > a documented default rule. Two different materials at the same, highest level -> HELD (conflict). No source
     at all -> HELD. A default rule applies only to the element it is written for (the dry-porcelain default never
     to a stair part, the stair-marble rule never to a room floor).
  3. Family: a stone / marble ROOM_FLOOR named by a project source is B3-03; a marble stair part is B7 (never B3-03);
     a threshold is B3-04 (never B3-03); a porcelain room floor is B3-01; material HELD -> HELD, the candidate
     families named.
  4. Area: polygon (m or mm, any rotation or mirror) less fixed SOLID items; a door opening never changes the floor
     area of the space (its threshold strip lies in the wall, outside the face, and goes to B3-04 by opening id).
     No polygon and no sourced area -> area HELD, never 0.
  5. Nothing is counted twice: B3-03 adds a NEW quantity only when no released carrier line holds the area. If the
     area sits in a porcelain line and a project source names stone, the row is a MOVE (porcelain - area,
     B3-03 + area, villa total unchanged), never an addition. A space already carried as porcelain under the default
     is NOT_APPLICABLE for B3-03 and adds 0.
"""
from __future__ import annotations

import math

METHOD = "STONE_FLOOR_CENSUS_V1"
RULE = "R-T490-1"

ELEMENTS = {"ROOM_FLOOR", "FLOOR_OR_LANDING", "STAIR_LANDING", "STAIR_ARRIVAL", "TREADS", "THRESHOLD", "UNREAD"}
STAIR_ELEMENTS = {"STAIR_LANDING", "STAIR_ARRIVAL", "TREADS"}
EVIDENCE_LEVEL = {"PROJECT_SCHEDULE": 3, "PLAN_NOTE": 3, "LEGEND": 3, "OWNER_RULE": 2, "DEFAULT_RULE": 1}
STONE = {"MARBLE", "STONE", "GRANITE"}
MATERIALS = STONE | {"PORCELAIN", "CERAMIC"}
UNITS = {"m": 1.0, "mm": 0.001}
# a default rule is written for one kind of element only (step 2)
DEFAULT_SCOPE = {"PORCELAIN": {"ROOM_FLOOR"}, "CERAMIC": {"ROOM_FLOOR"}, "MARBLE": STAIR_ELEMENTS}
EPS = 1e-9


class CensusError(ValueError):
    """Refused input: the census never guesses."""


def polygon_area(points, unit):
    if unit not in UNITS:
        raise CensusError(f"unit {unit!r} refused (m or mm only)")
    if not points or len(points) < 3:
        raise CensusError("polygon needs at least 3 points")
    f = UNITS[unit]
    s = 0.0
    n = len(points)
    for i in range(n):
        x0, y0 = points[i]
        x1, y1 = points[(i + 1) % n]
        s += x0 * y1 - x1 * y0
    a = abs(s) / 2.0 * f * f
    if a <= EPS:
        raise CensusError("degenerate polygon")
    return a


def _area(obj, unit, what):
    if obj.get("polygon") is not None:
        return polygon_area(obj["polygon"], obj.get("unit", unit)), "POLYGON"
    if obj.get("area_m2") is not None:
        a = float(obj["area_m2"])
        if a < 0 or not math.isfinite(a):
            raise CensusError(f"{what}: area {a} refused")
        if not obj.get("area_source"):
            raise CensusError(f"{what}: a given area needs its source")
        return a, obj["area_source"]
    return None, None


def material_of(space):
    """Step 2: returns (material or None, basis, note)."""
    ev = space.get("material_evidence", [])
    usable = []
    for e in ev:
        k = e.get("kind")
        if k not in EVIDENCE_LEVEL:
            raise CensusError(f"{space['id']}: evidence kind {k!r} refused")
        m = e.get("material")
        if m not in MATERIALS:
            raise CensusError(f"{space['id']}: material {m!r} refused")
        if k == "DEFAULT_RULE" and space["element"] not in DEFAULT_SCOPE.get(m, set()):
            continue  # a default never applies outside its own element
        if k == "OWNER_RULE" and e.get("condition_met") is False:
            continue  # a conditional owner answer whose condition the geometry does not meet
        usable.append(e)
    if not usable:
        return None, "NO_SOURCE", "no project source, owner rule or applicable default names the material"
    top = max(EVIDENCE_LEVEL[e["kind"]] for e in usable)
    at_top = {e["material"] for e in usable if EVIDENCE_LEVEL[e["kind"]] == top}
    norm = {"STONE" if m in STONE else m for m in at_top}
    if len(norm) > 1:
        return None, "CONFLICT", f"different materials at the same evidence level: {sorted(at_top)}"
    best = [e for e in usable if EVIDENCE_LEVEL[e["kind"]] == top][0]
    return best["material"], best["kind"], best.get("rule", "")


def family_of(element, material, basis=None):
    if element == "FLOOR_OR_LANDING":
        if material is None:
            return "HELD", ["B3-01", "B7"]
        if material in STONE:
            # a project source naming the hall finish makes it a stone floor; an owner stair rule makes it a landing
            return ("B3-03", ["B3-03"]) if EVIDENCE_LEVEL.get(basis, 0) == 3 else ("B7", ["B7"])
        return "B3-01", ["B3-01"]
    if material is None:
        if element == "THRESHOLD":
            return "B3-04", ["B3-04"]
        if element in STAIR_ELEMENTS:
            return "HELD", ["B7"]
        return "HELD", ["B3-01", "B3-03", "B7"] if element == "ROOM_FLOOR" else ["UNREAD"]
    if element == "THRESHOLD":
        return "B3-04", ["B3-04"]
    if element in STAIR_ELEMENTS:
        return ("B7", ["B7"]) if material in STONE else ("B3-01", ["B3-01"])
    if element == "ROOM_FLOOR":
        return ("B3-03", ["B3-03"]) if material in STONE else ("B3-01", ["B3-01"])
    return "HELD", ["UNREAD"]


def census_space(space, unit="m"):
    sid = space.get("id")
    if not sid:
        raise CensusError("space without id")
    if space.get("element") not in ELEMENTS:
        raise CensusError(f"{sid}: element {space.get('element')!r} refused")
    area, basis = _area(space, unit, sid)
    fixed = 0.0
    for f in space.get("fixed", []):
        fa, _ = _area(f, unit, f"{sid}/{f.get('id')}")
        if fa is None:
            raise CensusError(f"{sid}: fixed item {f.get('id')} has no area")
        fixed += fa
    net = None
    if area is not None:
        net = area - fixed
        if net < -EPS:
            raise CensusError(f"{sid}: fixed items {fixed:.4f} exceed the face {area:.4f}")
        net = max(net, 0.0)
    material, mbasis, mnote = material_of(space)
    family, candidates = family_of(space["element"], material, mbasis)

    carriers = space.get("carriers", [])
    released = sum(float(c["area_m2"]) for c in carriers if c.get("area_m2") is not None)
    held_hi = sum(float(c["held"][1]) for c in carriers if c.get("held"))
    porcelain_released = sum(float(c["area_m2"]) for c in carriers
                             if c.get("area_m2") is not None and c.get("family") == "B3-01"
                             and c.get("material") in ("PORCELAIN", "CERAMIC"))
    stone_carried = sum(float(c["area_m2"]) for c in carriers
                        if c.get("area_m2") is not None and c.get("family") in ("B3-03",))

    thresholds = [{"opening_id": o["id"], "family": "B3-04",
                   "strip_m2": (o["width"] * o["depth"]) if o.get("depth") is not None else None}
                  for o in space.get("openings", [])]

    b303_new = 0.0
    b303_move = 0.0
    b303_held = None
    if family == "B3-03":
        status = "APPLICABLE"
        if net is None:
            b303_held = [0.0, None]
            status = "APPLICABLE_AREA_HELD"
        elif porcelain_released > EPS:
            b303_move = net
            status = "APPLICABLE_MOVE"
        else:
            b303_new = max(net - stone_carried, 0.0)
    elif family in ("B7", "B3-04", "B6"):
        status = "CARRIED_ELSEWHERE" if material in STONE or family == "B3-04" else "NOT_APPLICABLE"
    elif family == "B3-01":
        status = "NOT_APPLICABLE"
    else:
        status = "HELD"
        if "B3-03" in candidates:
            b303_held = [0.0, net]  # never 0 as a figure: a bound kept with its cause
    has_released = any(c.get("area_m2") is not None for c in carriers)
    diff = None
    if net is not None and has_released:
        diff = released - net
    if not carriers:
        line_state = "NO_LINE"
    elif not has_released:
        line_state = "HELD_ONLY"
    else:
        line_state = "RELEASED"
    return {
        "id": sid, "name": space.get("name", ""), "floor": space.get("floor", ""), "element": space["element"],
        "area_m2": None if net is None else round(net, 6), "area_basis": basis, "fixed_m2": round(fixed, 6),
        "material": material, "material_basis": mbasis, "material_note": mnote,
        "family": family, "candidate_families": candidates, "status": status,
        "b3_03_new_m2": round(b303_new, 6), "b3_03_move_m2": round(b303_move, 6), "b3_03_held": b303_held,
        "carried_released_m2": round(released, 6), "carried_held_high_m2": round(held_hi, 6),
        "carriers": [c.get("line_id") for c in carriers],
        "carrier_minus_measure_m2": None if diff is None else round(diff, 6), "line_state": line_state,
        "thresholds": thresholds,
        "owner_trade": {"B3-03": "marble / stone floor", "B3-01": "tiler (porcelain floor)", "B7": "stair marble",
                        "B3-04": "door-threshold marble", "HELD": "undecided: " + " / ".join(candidates)}[family]
        if family in ("B3-03", "B3-01", "B7", "B3-04", "HELD") else family,
        "evidence": space.get("evidence", ""),
    }


def census(spaces, unit="m"):
    ids = [s.get("id") for s in spaces]
    if len(set(ids)) != len(ids):
        raise CensusError("duplicate space id")
    rows = [census_space(s, unit) for s in spaces]
    tot = {
        "b3_03_new_m2": round(sum(r["b3_03_new_m2"] for r in rows), 6),
        "b3_03_move_m2": round(sum(r["b3_03_move_m2"] for r in rows), 6),
        "b3_03_held_high_m2": round(sum((r["b3_03_held"][1] or 0.0) for r in rows if r["b3_03_held"]), 6),
        "b3_03_held_unbounded": sum(1 for r in rows if r["b3_03_held"] and r["b3_03_held"][1] is None),
        "by_status": {},
        "by_family_m2": {},
    }
    for r in rows:
        tot["by_status"][r["status"]] = tot["by_status"].get(r["status"], 0) + 1
        if r["area_m2"] is not None:
            tot["by_family_m2"][r["family"]] = round(tot["by_family_m2"].get(r["family"], 0.0) + r["area_m2"], 6)
    if tot["b3_03_new_m2"] <= EPS and tot["b3_03_move_m2"] <= EPS and not any(r["b3_03_held"] for r in rows):
        tot["b3_03_applicability"] = "NOT_APPLICABLE"
    elif tot["b3_03_new_m2"] > EPS or tot["b3_03_move_m2"] > EPS:
        tot["b3_03_applicability"] = "APPLICABLE"
    else:
        tot["b3_03_applicability"] = "POSSIBLY_APPLICABLE_HELD"
    return {"method": METHOD, "rule": RULE, "rows": rows, "totals": tot}
