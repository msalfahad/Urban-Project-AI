"""T-753: B13-06 JOINERY census (kitchen / pantry base runs and worktops, vanity counters, built-in cupboards and
wardrobes), per floor and room, in each item's own unit (research only: nothing wired, no BOQ line produced).

PHYSICAL ELEMENT. A fitted joinery unit is a drawn installation fixed to the building:
  * a BASE RUN (base cabinets under a worktop, or a counter): measured along its FRONT EDGE in lm, its worktop in plan m2;
    an L or U run is ONE unit: its inside corner is counted once (the corner square belongs to the plan area once and to
    neither front leg, so lm along the front never counts it twice);
  * a BUILT-IN CUPBOARD / WARDROBE: the plan symbol "front line + one corner-to-corner diagonal" on a box whose back is a
    wall face; measured along its front in lm and counted in pcs; its front face in m2 = lm x the PRINTED height, which is
    HELD (never a default height) where no elevation prints it;
  * a VANITY counter: a counter outline that holds basin symbols (the basins themselves stay B12-01, excluded by id).

WHAT IS NOT A UNIT. A block whose content is text only (a room tag, e.g. a block named 'WARDROBE' that prints a word) is
never a unit, whatever its name (L-T743-1 / T-744: type by content and geometry, never by tag name). A closed box with a
diagonal that is enclosed by walls and stacks floor to floor is a lift / shaft symbol, not joinery. Loose furniture
(stools, beds, tables) is excluded. A fixture-layer line whose parallel twin on a wall layer sits a wall thickness away is
a wall face, not a front.

NO DEFAULTS. Heights, carcass / door material and worktop material are never assumed: unprinted -> HELD with a designer-
item cause; a quantity that needs them is None (never 0). Units nobody drew (e.g. wall cabinets) are listed NOT_DRAWN with
no quantity.

Statuses (ENGINEERING_REASONING_STANDARD s.2.6): DRAWING-CONFIRMED = from the drawn CAD geometry; HELD = needs a fact the
drawings do not print; nothing here is VERIFIED (the Checker re-measures).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

METHOD_ID = "JOINERY_CENSUS_T753_V1"

BASE_RUN = "BASE_RUN"                 # base cabinets / counter under a worktop (kitchen, pantry, bar peninsula)
VANITY = "VANITY_COUNTER"
CUPBOARD = "BUILT_IN_CUPBOARD"        # wardrobe / cupboard symbol: front + one diagonal
KINDS = (BASE_RUN, VANITY, CUPBOARD)

DRAWING_CONFIRMED = "DRAWING-CONFIRMED"
HELD = "HELD"
NOT_DRAWN = "NOT_DRAWN"

# a drawn cupboard / counter is 0.30 - 0.90 m deep (a 0.30 m shelf unit to a 0.90 m island leg); outside this range a
# front + diagonal pair is not read as a joinery box (a 1.6 m lift car with a diagonal is 1.47 m deep)
DEPTH_MIN_M = 0.30
DEPTH_MAX_M = 0.90
TOL_M = 0.005                         # endpoint coincidence on a CAD drawing (5 mm)
# a fixture-layer line with a parallel wall-layer twin this far away is a wall face (wall thickness 0.10 - 0.40 m)
WALL_TWIN_MIN_M = 0.05
WALL_TWIN_MAX_M = 0.40


# ------------------------------------------------------------------------------------------------------- geometry
def _d(p, q):
    return math.hypot(q[0] - p[0], q[1] - p[1])


def _near(p, q, tol=TOL_M):
    return _d(p, q) <= tol


def _proj(p, a, b):
    """-> (t along a->b as a length, signed perpendicular offset, foot point)."""
    L = _d(a, b)
    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    vx, vy = p[0] - a[0], p[1] - a[1]
    t = vx * ux + vy * uy
    return t, ux * vy - uy * vx, (a[0] + t * ux, a[1] + t * uy)


def _seg_dist(p, a, b):
    t, off, foot = _proj(p, a, b)
    L = _d(a, b)
    if t < 0:
        return _d(p, a)
    if t > L:
        return _d(p, b)
    return abs(off)


def _area(ring):
    s = 0.0
    for i in range(len(ring)):
        (x1, y1), (x2, y2) = ring[i], ring[(i + 1) % len(ring)]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2.0


def _simple(ring):
    """True when no two non-adjacent edges of the ring cross (a self-crossing outline is a misreading)."""
    n = len(ring)

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    for i in range(n):
        a, b = ring[i], ring[(i + 1) % n]
        for j in range(i + 2, n):
            if (j + 1) % n == i:
                continue
            c, d = ring[j], ring[(j + 1) % n]
            d1, d2, d3, d4 = cross(a, b, c), cross(a, b, d), cross(c, d, a), cross(c, d, b)
            if ((d1 > 1e-12 and d2 < -1e-12) or (d1 < -1e-12 and d2 > 1e-12)) and \
                    ((d3 > 1e-12 and d4 < -1e-12) or (d3 < -1e-12 and d4 > 1e-12)):
                return False
    return True


@dataclass(frozen=True)
class Seg:
    """a drawn straight segment, in metres, with its CAD id and layer."""
    ref: str
    a: tuple
    b: tuple
    layer: str = ""

    @property
    def length(self):
        return _d(self.a, self.b)


# ------------------------------------------------------------------------------------- what is (not) a joinery item
def is_tag_block(entity_types):
    """a block whose content is text only (TEXT / MTEXT / ATTDEF / ATTRIB) is a label, never a joinery unit, whatever
    its name ('WARDROBE', 'KITCHEN'). An empty block is no evidence either (False: not a tag, not a unit)."""
    t = [str(x).upper() for x in entity_types]
    return bool(t) and all(x in ("TEXT", "MTEXT", "ATTDEF", "ATTRIB") for x in t)


def is_wall_face(front, wall_segs):
    """True when a wall-layer segment runs parallel to `front` at a wall thickness and overlaps most of it: then the
    'front' is the other face of a wall, not a joinery front."""
    for w in wall_segs:
        t1, o1, _ = _proj(w.a, front.a, front.b)
        t2, o2, _ = _proj(w.b, front.a, front.b)
        if abs(o1 - o2) > TOL_M:
            continue                                           # not parallel
        off = abs(o1)
        if not (WALL_TWIN_MIN_M <= off <= WALL_TWIN_MAX_M):
            continue
        lo, hi = max(0.0, min(t1, t2)), min(front.length, max(t1, t2))
        if hi - lo >= 0.8 * front.length:
            return True
    return False


def cupboard_symbol(front, diag):
    """the plan symbol of a built-in cupboard / wardrobe: a front line and one diagonal that starts at one end of the
    front and ends opposite the OTHER end, at the box depth. -> {"depth_m", "front_m"} or None."""
    for shared, other in ((front.a, front.b), (front.b, front.a)):
        for p, q in ((diag.a, diag.b), (diag.b, diag.a)):
            if not _near(p, shared):
                continue
            t, off, _ = _proj(q, front.a, front.b)
            t_other, _, _ = _proj(other, front.a, front.b)
            depth = abs(off)
            if abs(t - t_other) <= TOL_M and DEPTH_MIN_M <= depth <= DEPTH_MAX_M:
                return {"depth_m": depth, "front_m": front.length}
    return None


def find_cupboard_symbols(segs, wall_segs=()):
    """machine scan: every (front, diagonal) pair among fixture-layer LINE segments that forms the cupboard symbol and
    whose front is not a wall face. -> [(front.ref, diag.ref, depth_m, front_m)] (each front once)."""
    out, used = [], set()
    for f in segs:
        if f.ref in used or f.length < DEPTH_MIN_M:
            continue
        for g in segs:
            if g.ref == f.ref or g.ref in used:
                continue
            s = cupboard_symbol(f, g)
            if s and g.length > f.length * 0.999 and not is_wall_face(f, wall_segs):
                out.append((f.ref, g.ref, round(s["depth_m"], 4), round(s["front_m"], 4)))
                used.update((f.ref, g.ref))
                break
    return out


# ------------------------------------------------------------------------------------------------- one unit
@dataclass
class Unit:
    """one joinery unit read from the drawing.

    ring: the plan outline (metres), front chain first then the back (wall / open edge) chain;
    front: the segments that are the FRONT edge (lm is measured on these only); returns: the end returns to the wall
    (part of the outline, not of the lm); evidence: the symbol / content that types it (a diagonal ref, contained basin
    refs ...); excluded: ids of other trades' items inside it (basins -> B12-01)."""
    unit_id: str
    kind: str
    floor: str
    room_id: str
    ring: list
    front: list
    returns: list = field(default_factory=list)
    evidence: list = field(default_factory=list)
    excluded: list = field(default_factory=list)
    height_m: float | None = None        # printed height (an elevation / section), else None -> HELD
    height_source: str = ""
    note: str = ""


def _on_ring(seg, ring, tol=0.001):
    for p in (seg.a, seg.b, ((seg.a[0] + seg.b[0]) / 2, (seg.a[1] + seg.b[1]) / 2)):
        if min(_seg_dist(p, ring[i], ring[(i + 1) % len(ring)]) for i in range(len(ring))) > tol:
            return False
    return True


# depth is read square to the front at these fractions of each front edge (the ends touch the end walls, so they are
# not sampled; a tapering back gives a range)
DEPTH_SAMPLES = (0.02, 0.25, 0.5, 0.75, 0.98)


def _ray_hit(p, n, a, b):
    """distance along ray p + t n (t > 0) to segment a-b, or None."""
    ex, ey = b[0] - a[0], b[1] - a[1]
    den = n[0] * ey - n[1] * ex
    if abs(den) < 1e-12:
        return None
    wx, wy = a[0] - p[0], a[1] - p[1]
    t = (wx * ey - wy * ex) / den
    s = (wx * n[1] - wy * n[0]) / den
    if t > 1e-9 and -1e-9 <= s <= 1 + 1e-9:
        return t
    return None


def _inside(p, ring):
    ins, n = False, len(ring)
    for i in range(n):
        (x1, y1), (x2, y2) = ring[i], ring[(i + 1) % n]
        if (y1 > p[1]) != (y2 > p[1]) and p[0] < (x2 - x1) * (p[1] - y1) / (y2 - y1) + x1:
            ins = not ins
    return ins


def _depth_at(s, f, ring, back):
    """depth of the unit square to front edge s at fraction f: along the inward normal to the first back edge."""
    L = s.length
    ux, uy = (s.b[0] - s.a[0]) / L, (s.b[1] - s.a[1]) / L
    p = (s.a[0] + f * L * ux, s.a[1] + f * L * uy)
    for n in ((-uy, ux), (uy, -ux)):
        if _inside((p[0] + 0.01 * n[0], p[1] + 0.01 * n[1]), ring):
            hits = [t for a, b in back if (t := _ray_hit(p, n, a, b)) is not None]
            return min(hits) if hits else None
    return None


def measure(u):
    """-> the unit's quantities, each with its status. Raises ValueError on a misread outline (a front or return that
    is not on the outline, a self-crossing outline, a depth outside the joinery range)."""
    if u.kind not in KINDS:
        raise ValueError(f"unknown joinery kind {u.kind!r}")
    if len(u.ring) < 3 or not _simple(u.ring):
        raise ValueError(f"{u.unit_id}: outline is not a simple polygon")
    if not u.front:
        raise ValueError(f"{u.unit_id}: no front edge")
    for s in list(u.front) + list(u.returns):
        if not _on_ring(s, u.ring):
            raise ValueError(f"{u.unit_id}: {s.ref} is not on the unit outline")
    front_ids = {s.ref for s in u.front} | {s.ref for s in u.returns}
    # the back = the ring edges that are not front / return edges
    n = len(u.ring)
    back = []
    for i in range(n):
        a, b = u.ring[i], u.ring[(i + 1) % n]
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        if any(_seg_dist(mid, s.a, s.b) <= 0.001 and _seg_dist(a, s.a, s.b) <= 0.001 and _seg_dist(b, s.a, s.b) <= 0.001
               for s in list(u.front) + list(u.returns)):
            continue
        back.append((a, b))
    if not back:
        raise ValueError(f"{u.unit_id}: no back edge")
    depths = []
    for s in u.front:
        for f in DEPTH_SAMPLES:
            d = _depth_at(s, f, u.ring, back)
            if d is None:
                raise ValueError(f"{u.unit_id}: no back face behind {s.ref} at {f:.2f} of its length")
            depths.append(d)
    dmin, dmax = min(depths), max(depths)
    # the full depth must be a joinery depth; a back cut by an angled wall may taper below it toward one end (reported)
    if not (DEPTH_MIN_M - TOL_M <= dmax <= DEPTH_MAX_M + TOL_M) or dmin <= 0:
        raise ValueError(f"{u.unit_id}: depth {dmin:.3f} .. {dmax:.3f} m outside the joinery range")
    front_lm = sum(s.length for s in u.front)
    area = _area(u.ring)
    # inside corners of the front chain (two front legs meeting at a vertex): each counted once in the plan area
    corners = 0
    fr = list(u.front)
    for i in range(len(fr)):
        for j in range(i + 1, len(fr)):
            if any(_near(p, q, 0.001) for p in (fr[i].a, fr[i].b) for q in (fr[j].a, fr[j].b)):
                corners += 1
    q = {"unit_id": u.unit_id, "kind": u.kind, "floor": u.floor, "room_id": u.room_id,
         "front_refs": [s.ref for s in u.front], "return_refs": [s.ref for s in u.returns],
         "evidence": list(u.evidence), "excluded": list(u.excluded),
         "front_lm": {"value": round(front_lm, 4), "status": DRAWING_CONFIRMED},
         "depth_m": {"min": round(dmin, 4), "max": round(dmax, 4), "status": DRAWING_CONFIRMED},
         "plan_m2": {"value": round(area, 4), "status": DRAWING_CONFIRMED},
         "inside_corners": corners, "pcs": 1, "note": u.note}
    if u.kind == CUPBOARD:
        if u.height_m is None:
            q["front_face_m2"] = {"value": None, "status": HELD,
                                  "reason": "height not printed (no interior elevation / section of the unit): "
                                            "designer item, never a default height"}
        else:
            q["front_face_m2"] = {"value": round(front_lm * u.height_m, 4), "status": DRAWING_CONFIRMED,
                                  "height_source": u.height_source}
    else:
        q["worktop_m2"] = {"value": round(area, 4), "status": DRAWING_CONFIRMED,
                           "material": {"value": None, "status": HELD, "reason": "worktop material not printed"}}
        q["cabinet_height_m"] = {"value": u.height_m, "status": DRAWING_CONFIRMED if u.height_m else HELD,
                                 "reason": "" if u.height_m else "base cabinet / counter height not printed"}
    q["material"] = {"status": HELD, "reason": "carcass / door material and finish not printed (designer item)"}
    return q


def census(units, *, not_drawn=()):
    """-> {"units": [measure(u)], "by_room": {room: {kind: {"pcs", "front_lm", "plan_m2"}}}, "totals": {kind: ...},
    "not_drawn": [...]} . not_drawn: [{"room_id", "item", "reason"}] listed with value None, never 0."""
    rows = [measure(u) for u in units]
    by_room, totals = {}, {}
    for r in rows:
        for bucket in (by_room.setdefault(f'{r["floor"]}/{r["room_id"]}', {}), totals):
            k = bucket.setdefault(r["kind"], {"pcs": 0, "front_lm": 0.0, "plan_m2": 0.0})
            k["pcs"] += 1
            k["front_lm"] = round(k["front_lm"] + r["front_lm"]["value"], 4)
            k["plan_m2"] = round(k["plan_m2"] + r["plan_m2"]["value"], 4)
    nd = [{**x, "value": None, "status": NOT_DRAWN} for x in not_drawn]
    return {"method": METHOD_ID, "units": rows, "by_room": by_room, "totals": totals, "not_drawn": nd}
