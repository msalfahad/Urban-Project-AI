"""LANDING_CENSUS_V1 (T-493, rule R-T493-1): every landing-like surface of every staircase, classed, measured, given
ONE owner trade and ONE line, with the stacked-surface overlap check that keeps B3 floor and B7 stair marble apart.

Any villa. No layer name, room id or dimension of a training villa is in this module. Research only (UNWIRED).

R-T493-1 (scope: stair landings, arrivals and the floors at flight ends; provenance T-493; rules UP-STAIR-005,
UP-STAIR-001, OWNER_RULE_STAIRS_2026-10-24 S-9 (2) / A3 / A4 / A6, Q-66 B, Q-70 A, R-T490-1, UP-QTY-STATUS-001):
  1. Define the element first, from the levels and the flights that touch the surface:
     - STAIR_LANDING: a flat surface at a level that is NOT a storey floor level, reached by at least one arriving and
       left by at least one departing flight (a half, quarter or split-level landing). It can only be stair: trade
       B7, material marble by UP-STAIR-005 (owner MANDATORY) unless a project source names another material.
     - STAIR_ARRIVAL: a surface AT a storey floor level at a flight end that an owner answer makes part of the stair
       (Q-66 B; Q-70 A only when its geometric condition is recorded as met). Trade B7, marble.
     - FLOOR: a surface at a storey floor level at a flight end that lies inside a room whose floor line carries it
       (open plan; no landing drawn as its own zone). Trade B3 (the room's line); never a B7 line (A6).
     - FLOOR_OR_LANDING: a surface at a storey floor level at a flight end, bounded as its own zone (a stair-room
       part), with no printed landing depth and no owner answer: landing or floor is not established. Area measured,
       material HELD (never defaulted to porcelain or marble, R-T490-1), owner trade named as the candidates.
     - WINDER: a tapered step of a turn: tread family, NOT a landing (S-9: never generated, never counted as landing).
  2. Area = the drawn polygon (S-9 (2): never width x width or a fixed half-landing formula), in m or mm, any rotation
     or mirror, less fixed SOLID items standing inside it (a column notch). The landing's edge toward an ARRIVING
     flight is that flight's last nosing (the landing owns its nosing projection, T-269); the edge toward a DEPARTING
     flight is that flight's first nosing line (the first tread owns its projection). No closed polygon -> area HELD
     (None), never 0.
  3. A split-level landing (A3) is two surfaces with their own levels; their split may stay HELD while the total plan
     area is established, because the closing riser only moves the boundary between two marble surfaces.
  4. One surface, one line. Two parts that overlap in plan AT THE SAME LEVEL are refused (double count). Parts that
     overlap in plan at DIFFERENT levels are stacked surfaces (a landing over a lower lobby): both are measured, the
     plan overlap is reported in m2 and the surface overlap is 0.
  5. A B3 floor line and a B7 line never carry the same surface: the census refuses a part claimed by both families.
  6. A bound line ("landings 0 .. X") is checked against its itemised content: a bound whose content holds no
     landing is NOT_APPLICABLE as a landing bound; a landing found inside it leaves it as its own line.
"""
from __future__ import annotations

from shapely.affinity import scale as _scale
from shapely.geometry import Polygon

METHOD = "LANDING_CENSUS_V1"
RULE = "R-T493-1"
UNITS = {"m": 1.0, "mm": 0.001}
ELEMENTS = {"STAIR_LANDING", "STAIR_ARRIVAL", "FLOOR", "FLOOR_OR_LANDING", "WINDER"}
MATERIALS = {"MARBLE", "PORCELAIN", "GRANITE", "STONE", "CERAMIC"}
LEVEL_TOL = 0.005   # m: a surface within 5 mm of a storey floor level is AT that level
AREA_TOL = 1e-6     # m2


class CensusError(ValueError):
    """Refused input: the census never guesses."""


def _poly(points, unit):
    if unit not in UNITS:
        raise CensusError(f"unit {unit!r} refused (m or mm only)")
    if points is None:
        return None
    if len(points) < 3:
        raise CensusError("polygon needs at least 3 points")
    f = UNITS[unit]
    p = Polygon([(x * f, y * f) for x, y in points])
    if not p.is_valid or p.area <= AREA_TOL:
        raise CensusError("polygon is not a valid closed area")
    return p


def classify(part, storey_levels):
    """Step 1. part: level (m), arriving / departing flight ids, in_room_floor_line (bool), owner_answer (dict or
    None: {'id', 'condition_met'}), kind_hint 'WINDER' for a drawn tapered step."""
    if part.get("kind_hint") == "WINDER":
        return "WINDER"
    lvl = part.get("level")
    if lvl is None:
        raise CensusError(f"{part.get('id')}: level missing (a landing is classed by its level)")
    at_floor = any(abs(lvl - s) <= LEVEL_TOL for s in storey_levels)
    arr, dep = part.get("arriving") or [], part.get("departing") or []
    if not at_floor:
        if not arr or not dep:
            raise CensusError(f"{part.get('id')}: a surface between storeys needs an arriving and a departing flight")
        return "STAIR_LANDING"
    if not arr and not dep:
        raise CensusError(f"{part.get('id')}: a floor-level surface with no flight end is not a census part")
    ans = part.get("owner_answer")
    if ans and ans.get("condition_met") is True:
        return "STAIR_ARRIVAL"
    if part.get("in_room_floor_line"):
        return "FLOOR"
    return "FLOOR_OR_LANDING"


def material(element, part):
    """Step 1 material: project source > owner rule; nothing defaulted to a floor-level zone."""
    src = part.get("project_material")
    if src is not None:
        if src not in MATERIALS:
            raise CensusError(f"{part.get('id')}: unknown material {src!r}")
        return src, "PROJECT_SOURCE"
    if element == "STAIR_LANDING":
        return "MARBLE", "OWNER_RULE UP-STAIR-005 (MANDATORY)"
    if element == "STAIR_ARRIVAL":
        return "MARBLE", f"OWNER_ANSWER {part['owner_answer']['id']}"
    if element == "FLOOR":
        return None, "the room's floor line (B3) decides"
    if element == "WINDER":
        return None, "tread family (not a landing)"
    return None, "HELD: no printed landing depth, no owner answer, no project source (R-T490-1)"


def trade(element):
    return {"STAIR_LANDING": "B7-04", "STAIR_ARRIVAL": "B7-04", "FLOOR": "B3-01", "WINDER": "B7-02",
            "FLOOR_OR_LANDING": "HELD (B3-01 or B7-04)"}[element]


def measure(part):
    """Step 2: polygon less SOLID items inside it; None when no closed polygon is drawn."""
    unit = part.get("unit", "m")
    p = _poly(part.get("polygon"), unit)
    if p is None:
        return None, 0.0
    cut = 0.0
    for s in part.get("solids", []):
        q = _poly(s, unit)
        inter = p.intersection(q).area
        if inter <= AREA_TOL:
            raise CensusError(f"{part.get('id')}: a listed solid does not touch the surface")
        cut += inter
        p = p.difference(q)
    return p.area, cut


def census(parts, storey_levels):
    """Steps 1-5 over every part of one villa. Returns rows + overlap pairs; refuses a same-level double count or a
    surface claimed by two families."""
    rows, geoms, seen = [], [], set()
    for part in parts:
        pid = part.get("id")
        if not pid or pid in seen:
            raise CensusError(f"duplicate or missing id {pid!r}")
        seen.add(pid)
        el = classify(part, storey_levels)
        mat, basis = material(el, part)
        area, cut = measure(part)
        claims = set(part.get("claimed_by", []))
        if any(c.startswith("B3") for c in claims) and any(c.startswith("B7") for c in claims):
            raise CensusError(f"{pid}: one surface claimed by B3 and B7")
        if area is None:
            # a room floor at a flight end is measured by its room's line; a winder by the tread family; anything
            # else without a polygon is HELD (never 0)
            status = {"FLOOR": "IN_ROOM_LINE", "WINDER": "TREAD_FAMILY"}.get(el, "AREA_HELD")
        else:
            status = "MATERIAL_HELD" if mat is None and el == "FLOOR_OR_LANDING" else "MEASURED"
        rows.append({"id": pid, "stair": part.get("stair"), "element": el, "level": part.get("level"),
                     "area_m2": None if area is None else round(area, 6), "solid_cut_m2": round(cut, 6),
                     "material": mat, "material_basis": basis, "trade": trade(el), "status": status,
                     "line": part.get("line"), "line_state": part.get("line_state")})
        if area is not None:
            g = _poly(part["polygon"], part.get("unit", "m"))
            geoms.append((pid, part["level"], g, el))
    overlaps = []
    for i in range(len(geoms)):
        for j in range(i + 1, len(geoms)):
            a, b = geoms[i], geoms[j]
            ov = a[2].intersection(b[2]).area
            if ov <= AREA_TOL:
                continue
            if abs(a[1] - b[1]) <= LEVEL_TOL:
                raise CensusError(f"{a[0]} and {b[0]} overlap {ov:.4f} m2 at one level: double count")
            overlaps.append({"a": a[0], "b": b[0], "plan_overlap_m2": round(ov, 6), "surface_overlap_m2": 0.0,
                             "levels": [a[1], b[1]]})
    return {"method": METHOD, "rule": RULE, "rows": rows, "stacked": overlaps,
            "b3_b7_shared_m2": 0.0}


def split_level(surfaces, total_polygon, unit="m"):
    """Step 3: a split-level landing. surfaces: [{'id','level','polygon' or None}]. Returns the total plan area (from
    the union polygon) and each surface's area, None for a surface whose split is not established."""
    tot = _poly(total_polygon, unit).area
    out = []
    known = 0.0
    for s in surfaces:
        if s.get("polygon") is None:
            out.append({"id": s["id"], "level": s["level"], "area_m2": None})
        else:
            a = _poly(s["polygon"], unit).area
            known += a
            out.append({"id": s["id"], "level": s["level"], "area_m2": round(a, 6)})
    if known > tot + AREA_TOL:
        raise CensusError("split surfaces exceed the landing total")
    if all(o["area_m2"] is not None for o in out) and abs(known - tot) > 1e-4:
        raise CensusError(f"split surfaces {known:.4f} do not re-add to the total {tot:.4f}")
    return {"total_m2": round(tot, 6), "surfaces": out}


def bound_check(bound_high, content):
    """Step 6. content: [{'id','m2','kind'}] itemising the bound; kinds LANDING / TREAD / WINDER / SOLID / VOID /
    UNREAD / FLOOR. The items must re-add to the bound (else refused). Returns the verdict and the landing share."""
    s = sum(c["m2"] for c in content)
    if abs(s - bound_high) > 1e-4:
        raise CensusError(f"bound content {s:.4f} does not re-add to the bound {bound_high:.4f}")
    landing = sum(c["m2"] for c in content if c["kind"] == "LANDING")
    verdict = "NOT_APPLICABLE_AS_LANDING_BOUND" if landing <= AREA_TOL else "LANDINGS_LEAVE_AS_OWN_LINES"
    return {"verdict": verdict, "landing_m2": round(landing, 6),
            "non_landing_m2": round(bound_high - landing, 6)}


def mirror_scale(points, sx, sy):
    """Test helper kept beside the method: mirror a polygon (shapely, no hand-coded sign flips)."""
    return list(_scale(Polygon(points), xfact=sx, yfact=sy, origin=(0, 0)).exterior.coords)[:-1]
