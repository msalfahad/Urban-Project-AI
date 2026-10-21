"""FLOOR AREA RECONCILIATION (M9 S4) - every m2 of a floor plan in exactly one category, or an explicit residual.

    reconcile(S, rooms, lines, *, floor) -> record          S = arch_rooms.spaces(...), rooms / lines = arch_measure

The plan's TS01 faces partition the area inside the wall network's outer boundary (the gross floor plate). Each face
is split into the categories below by positive evidence only; the parts of a face always add up to its area:

    WALL_AND_COLUMN_MASS   thin faces with no threshold: wall bodies, columns, junction pieces
    DOORWAY_STRIPS         the piece of an opening in the wall thickness (threshold strips)
    SLIVERS                faces below the space size limit
    ROOM_FLOOR             a room with one room word (or one kind): its floor surface
    OPEN_PLAN_FLOOR        an open plan of compatible room words measured as one finish
    UNALLOCATED_MERGED     a face holding wet + dry or interior + exterior words: a boundary is missing (review)
    UNALLOCATED_MIXED      a face holding room words of different kinds with no finish decision (review)
    UNALLOCATED_UNLABELLED a space with no room word (review)
    VOID                   the outlined void inside a face (open to below: never floor)
    SHAFT                  shafts / lift wells (a shaft word, or the same doorless footprint on every storey)
    STAIR_FLIGHTS          the treads of the flights drawn on THIS plan (stair finish, not floor finish)
    STAIR_LANDINGS_BOUND   a stair space less its treads: landings and any well (an upper bound of the landings)
    STAIR_BELOW_SEEN       a flight of the plan below seen through an opening (counted once, on the plan below)
    EXTERNAL               balcony / terrace / garden / pool / roof faces (kept apart from the internal floor)

Totals: internal physical floor = room + open plan + unallocated + doorway strips + stair flights + landings (the floor
that physically exists inside, finished or not); the sum of single-label rooms is reported as a PART of it, never as
the floor area. Conservation: plate (outer boundary of each wall network) - sum of faces = residual; a residual above
the tolerance is listed (RESIDUAL_UNRESOLVED), never spread. Project-agnostic; stdlib only.
"""

from __future__ import annotations

from collections import defaultdict

from engine.source import arch_rooms as AR
from engine.source import plane_poly as PP

POLICY_ID = "ARCH_FLOOR_RECONCILIATION_V1"
TOL_M2 = 0.05
CATEGORIES = ("WALL_AND_COLUMN_MASS", "DOORWAY_STRIPS", "SLIVERS", "ROOM_FLOOR", "OPEN_PLAN_FLOOR",
              "UNALLOCATED_MERGED", "UNALLOCATED_MIXED", "UNALLOCATED_UNLABELLED", "VOID", "SHAFT", "STAIR_FLIGHTS",
              "STAIR_LANDINGS_BOUND", "STAIR_BELOW_SEEN", "EXTERNAL")
INTERNAL_FLOOR = ("ROOM_FLOOR", "OPEN_PLAN_FLOOR", "UNALLOCATED_MERGED", "UNALLOCATED_MIXED", "UNALLOCATED_UNLABELLED",
                  "DOORWAY_STRIPS", "STAIR_FLIGHTS", "STAIR_LANDINGS_BOUND")
FINISH_ITEMS = ("FIN.FLOOR.PORCELAIN", "FIN.FLOOR.WET_TILE", "FIN.MARBLE.TREAD", "FIN.MARBLE.LANDING")


def _void_windows(f, voids, u):
    ids = {v["void_id"] for v in f.get("voids") or ()}
    return [[(x * u, y * u) for x, y in v["corners"]] for v in voids if v["void_id"] in ids and v.get("corners")]


def _treads(f, flights, wins, u):
    """(area of the flights' tread quads inside the face, of which inside its voids) m2."""
    tot = in_void = 0.0
    for fl in flights:
        for q in fl.get("tread_quads") or ():
            qm = [(x * u, y * u) for x, y in q]
            tot += PP.region_area_in_convex(f["polygon_m"], f["hole_polygons_m"], qm)
            for w in wins:
                cut = PP.clip_convex(qm, w)
                if len(cut) >= 3:
                    in_void += PP.region_area_in_convex(f["polygon_m"], f["hole_polygons_m"], cut)
    return tot, min(in_void, tot)


def split_face(f, voids, u, measured_as_room):
    """-> {category: m2} for one face; the parts add up to the face area."""
    a = f["area_m2"]
    cls = f["class"]
    if cls == "WALL":
        return {"WALL_AND_COLUMN_MASS": a}
    if cls == "DOORWAY":
        return {"DOORWAY_STRIPS": a}
    if cls == "SLIVER":
        return {"SLIVERS": a}
    kinds = {AR.LEX[c][2] for c in f["codes"]}
    if kinds == {AR.EXTERIOR}:
        return {"EXTERNAL": a}
    if kinds and kinds <= {AR.SHAFT}:
        return {"SHAFT": a}
    parts = defaultdict(float)
    void = min(f.get("void_m2") or 0.0, a)
    parts["VOID"] = void
    if f["codes"] == ["VOID"]:
        parts["VOID"] = a
        return dict(parts)
    flights = (f.get("symbols_inside") or {}).get("stair_flights") or ()
    wins = _void_windows(f, voids, u)
    own = [x for x in flights if not x.get("drawn_on_plan_below")]
    below = [x for x in flights if x.get("drawn_on_plan_below")]
    t_own, t_own_v = _treads(f, own, wins, u)
    t_below, t_below_v = _treads(f, below, wins, u)
    parts["STAIR_FLIGHTS"] = max(t_own - t_own_v, 0.0)
    parts["STAIR_BELOW_SEEN"] = max(t_below - t_below_v, 0.0)
    rest = max(a - parts["VOID"] - parts["STAIR_FLIGHTS"] - parts["STAIR_BELOW_SEEN"], 0.0)
    if kinds == {AR.STAIR}:
        parts["STAIR_LANDINGS_BOUND"] = rest
    elif cls == "ROOM":
        parts["ROOM_FLOOR"] = rest
    elif cls == "MIXED":
        parts["OPEN_PLAN_FLOOR" if measured_as_room else "UNALLOCATED_MIXED"] = rest
    elif cls == "MERGED":
        parts["UNALLOCATED_MERGED"] = rest
    else:
        parts["UNALLOCATED_UNLABELLED"] = rest
    return {k: v for k, v in parts.items() if v > 1e-9}


def reconcile(S, rooms, lines, *, floor):
    u = S["unit_m"]
    by_face = {r["face_id"]: r for r in rooms}
    measured = {r["face_id"] for r in rooms if r["class"] == "ROOM" or (r["class"] == "MIXED" and r["kind"] is not None)}
    cat = defaultdict(float)
    rows = []
    for f in S["faces"]:
        parts = split_face(f, S.get("voids") or (), u, f["face_id"] in measured)
        for k, v in parts.items():
            cat[k] += v
        if f["class"] in ("ROOM", "MIXED", "MERGED", "UNLABELLED") or f["area_m2"] >= AR.MIN_SPACE_M2:
            rm = by_face.get(f["face_id"])
            rows.append({"face_id": f["face_id"], "room_id": rm["room_id"] if rm else None, "class": f["class"],
                         "codes": f["codes"], "area_m2": round(f["area_m2"], 6),
                         "parts": {k: round(v, 6) for k, v in sorted(parts.items())},
                         "attached_cells_m2": round(sum(x["area_m2"] for x in f.get("attached_cells") or ()), 6)})
    faces_sum = sum(f["area_m2"] for f in S["faces"])
    plate = S.get("plate") or {}
    # a wall network standing inside a face (a column in a room) is that face's hole: its outer boundary is already
    # inside the enclosing network's, so only the top-level outer boundaries are the plate
    nested = sum(f.get("hole_area_m2") or 0.0 for f in S["faces"])
    plate_sum = (plate.get("total_m2") if plate.get("total_m2") is not None else sum(plate.get("all_m2") or ())) - nested
    residual = plate_sum - faces_sum
    fin = defaultdict(float)
    bounded = defaultdict(lambda: [0.0, 0.0])
    for ln in lines:
        if (ln.get("location") or {}).get("floor") != floor or ln["item_code"] not in FINISH_ITEMS + ("ARCH.SPACE",):
            continue
        if ln.get("measured_net") is not None:
            fin[ln["item_code"]] += ln["measured_net"]
        elif ln.get("bounded_range"):
            b = ln["bounded_range"]
            bounded[ln["item_code"]][0] += b.get("low") or 0.0
            bounded[ln["item_code"]][1] += b.get("high") or 0.0
    internal = sum(cat[k] for k in INTERNAL_FLOOR)
    floor_fin = fin["FIN.FLOOR.PORCELAIN"] + fin["FIN.FLOOR.WET_TILE"]
    finished_floor = cat["ROOM_FLOOR"] + cat["OPEN_PLAN_FLOOR"]
    shared = (S.get("zoning") or {}).get("shared") or []
    checks = [
        {"check": "faces = categories", "lhs_m2": round(faces_sum, 4), "rhs_m2": round(sum(cat.values()), 4),
         "state": "BALANCED" if abs(faces_sum - sum(cat.values())) <= TOL_M2 else "RESIDUAL_UNRESOLVED"},
        {"check": "plate = faces (the faces partition the area inside each wall network's outer boundary)",
         "lhs_m2": round(plate_sum, 4), "rhs_m2": round(faces_sum, 4), "residual_m2": round(residual, 4),
         "state": "BALANCED" if abs(residual) <= TOL_M2 else "RESIDUAL_UNRESOLVED"},
        {"check": "floor finish lines = room + open-plan floor", "lhs_m2": round(floor_fin, 4),
         "rhs_m2": round(finished_floor, 4),
         "state": "BALANCED" if abs(floor_fin - finished_floor) <= TOL_M2 else "DIFFERENT (see the rows)"}]
    return {"policy": POLICY_ID, "floor": floor,
            "gross_floor_plate_m2": round(plate.get("largest_m2") or 0.0, 4),
            "plate_components_m2": plate.get("all_m2") or [],
            "plate_top_level_m2": round(plate_sum, 4),
            "categories_m2": {k: round(cat[k], 4) for k in CATEGORIES},
            "internal_categories": list(INTERNAL_FLOOR),
            "internal_physical_floor_m2": round(internal, 4),
            "of_which": {"rooms_single_label_m2": round(cat["ROOM_FLOOR"], 4),
                         "open_plan_m2": round(cat["OPEN_PLAN_FLOOR"], 4),
                         "unallocated_m2": round(cat["UNALLOCATED_MERGED"] + cat["UNALLOCATED_MIXED"] +
                                                 cat["UNALLOCATED_UNLABELLED"], 4),
                         "doorway_strips_m2": round(cat["DOORWAY_STRIPS"], 4),
                         "stairs_and_landings_m2": round(cat["STAIR_FLIGHTS"] + cat["STAIR_LANDINGS_BOUND"], 4)},
            "not_floor_m2": {"voids": round(cat["VOID"], 4), "shafts": round(cat["SHAFT"], 4),
                             "stair_below_seen": round(cat["STAIR_BELOW_SEEN"], 4),
                             "wall_and_column_mass": round(cat["WALL_AND_COLUMN_MASS"], 4),
                             "slivers": round(cat["SLIVERS"], 4)},
            "external_m2": round(cat["EXTERNAL"], 4),
            "finish_lines_m2": {k: round(v, 4) for k, v in sorted(fin.items())},
            "finish_bounded_m2": {k: [round(v[0], 4), round(v[1], 4)] for k, v in sorted(bounded.items())},
            "shared_open_spaces": shared, "checks": checks, "rows": rows,
            "rule": "every face in exactly one category per part (positive evidence only); the single-label room sum "
                    "is a part of the internal floor, never the floor area; residuals are listed, never spread"}


def policy_record():
    return {"policy_id": POLICY_ID, "tolerance_m2": TOL_M2, "categories": list(CATEGORIES),
            "internal_floor": list(INTERNAL_FLOOR)}
