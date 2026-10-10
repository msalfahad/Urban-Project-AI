"""ROOM SLICE (M2) - architectural rooms from wall line work: floor area, perimeter, skirting and wet-room
waterproofing by the Urban Projects rule library (data/trade_rules/URBAN_PROJECTS_RULE_LIBRARY.json). Generic, stdlib.

Faces come from the TS01 topology engine over the wall layers plus the door THRESHOLD lines (door-layer segments that
lie on a wall face line and end at wall ends on both sides: the jamb-to-jamb line a door block draws across the
opening). Door leaves and swing arcs
never bound a room; a swing arc gives the door width (its radius). Each bounded face is classified from evidence:

    ROOM          holds a room label (EN / AR vocabulary; the output carries the English name only)
    DOORWAY       thin (2 A / P below the wall-thickness limit) and bounded by a threshold: the piece in the wall
    WALL          thin, no threshold: wall mass
    UNLABELLED    anything else - a COVERAGE RISK (a room without a label, or a space the plan does not name)

Per ROOM (rule ids from the library):
    floor_m2         face area, holes subtracted                                  UP-CER-001 (floor polygon)
    perimeter_lm     the one-sided boundary (interior stubs excluded)             UP-CER-002 (wall base run)
    door_widths_lm   threshold length on the room's boundary
    skirting_lm      perimeter - door widths                                       UP-CER-003
                     a wet room: 0 when the wall tile is full height (UP-CER-004); when the height is not
                     established the skirting stays UNRESOLVED with both readings shown
    wp_floor_m2      wet room floor + its doorway pieces (membrane continues)      UP-WP-001, UP-WP-003
    wp_upturn_m2     (perimeter - door widths) x 0.15                              UP-WP-002
"""

from __future__ import annotations

import math
import re

from engine.source import drawing_model as DM
from engine.source import member_detection as MD
from engine.source import topology as TP

POLICY_ID = "ROOM_SLICE_V1"
ROOM_WORDS = [                        # (canonical English name, wet, patterns EN / AR)
    ("MASTER BEDROOM", False, (r"MASTER\s*BED", r"غرفة\s*نوم\s*رئيسية", r"ماستر")),
    ("BEDROOM", False, (r"BED\s*ROOM", r"BEDROOM", r"غرفة\s*نوم", r"نوم")),
    ("LIVING", False, (r"LIVING", r"SALA", r"صالة", r"معيشة")),
    ("MAJLIS", False, (r"MAJLIS", r"DIWANIYA", r"مجلس", r"ديوانية")),
    ("DINING", False, (r"DINING", r"طعام")),
    ("KITCHEN", False, (r"KITCHEN", r"PANTRY", r"مطبخ")),
    ("BATHROOM", True, (r"BATH", r"TOILET", r"\bWC\b", r"W\.C", r"SHOWER", r"حمام", r"دورة\s*مياه")),
    ("LAUNDRY", True, (r"LAUNDRY", r"غسيل")),
    ("MAID", False, (r"MAID", r"خادمة")),
    ("STORE", False, (r"STORE", r"STORAGE", r"مخزن")),
    ("CORRIDOR", False, (r"CORRIDOR", r"LOBBY", r"HALL", r"ممر", r"موزع")),
]
UPTURN_M = 0.15                        # UP-WP-002
WALL_THICK_LIMIT_M = 0.45              # 2A/P below this: a thin face (wall mass or doorway)


def room_name(text):
    u = DM.normalize(text).upper()
    for name, wet, pats in ROOM_WORDS:
        if any(re.search(p, u) for p in pats):
            return name, wet
    return None, False


def _collinear(s, w, eps):
    (x1, y1), (x2, y2) = w["a"], w["b"]
    L = math.hypot(x2 - x1, y2 - y1)
    if L <= 0:
        return False
    nx, ny = -(y2 - y1) / L, (x2 - x1) / L
    da = abs((s["a"][0] - x1) * nx + (s["a"][1] - y1) * ny)
    db = abs((s["b"][0] - x1) * nx + (s["b"][1] - y1) * ny)
    return da <= eps and db <= eps


def rooms(ents, wall_layers, door_layers, unit_m, *, wall_tile_full_height=None, eps_native=None, region_id="ARCH"):
    eps = eps_native if eps_native is not None else 0.5e-3 / unit_m
    walls = [s for s in ents["segments"] if s["layer"] in wall_layers]
    doors = [s for s in ents["segments"] if s["layer"] in door_layers]
    ends = [p for w in walls for p in (w["a"], w["b"])]

    def at_wall_end(p):
        return any(abs(p[0] - q[0]) <= eps and abs(p[1] - q[1]) <= eps for q in ends)
    # a threshold spans the gap between two wall pieces: collinear with a wall face AND both ends at wall ends (a
    # door leaf starts at the hinge but ends free, so it never bounds a room)
    thresholds = [d for d in doors if any(_collinear(d, w, eps) for w in walls) and at_wall_end(d["a"]) and
                  at_wall_end(d["b"])]
    swings = [a for a in ents.get("arcs", []) if a["layer"] in door_layers and 0.5 <= a["r"] * unit_m <= 1.6]
    items = [TP.BoundaryItem(s["id"], "SEGMENT", (s["a"][0], s["a"][1], s["b"][0], s["b"][1]), "WALL") for s in walls]
    items += [TP.BoundaryItem(s["id"], "SEGMENT", (s["a"][0], s["a"][1], s["b"][0], s["b"][1]), "THRESHOLD")
              for s in thresholds]
    for a in ents.get("arcs", []):
        if a["layer"] in wall_layers:
            cx, cy = a["c"]
            a0 = math.atan2(a["s"][1] - cy, a["s"][0] - cx)
            a1 = math.atan2(a["e"][1] - cy, a["e"][0] - cx)
            if a["dir"] == "CW":
                a0, a1 = a1, a0
            if a1 <= a0:
                a1 += 2 * math.pi
            items.append(TP.BoundaryItem(a["id"], "ARC", (cx, cy, a["r"], a0, a1), "WALL"))
    if not items:
        return {"policy": POLICY_ID, "rooms": [], "faces": [], "warnings": ["no wall geometry"]}
    arr = TP.build(items, eps)
    sites = TP.sites_of(arr, "M2", region_id)
    thr_ids = {s["id"] for s in thresholds}
    faces = []
    for st in sites:
        pt = TP.interior_point(arr, st["cycle"], eps)
        if pt is None:
            continue
        poly = [arr.nodes[arr.edges[ei]["n0"]] if fw else arr.nodes[arr.edges[ei]["n1"]] for ei, fw in st["cycle"]]
        area = st["area"] * unit_m ** 2
        per = st["boundary_perimeter"] * unit_m
        thin = per > 0 and 2 * area / per < WALL_THICK_LIMIT_M
        labels = [t for t in ents["texts"] if MD.point_in_poly(t["x"], t["y"], poly)]
        named = [room_name(t["value"]) for t in labels]
        named = [n for n in named if n[0]]
        thr_len = st["boundary_role_lengths"].get("THRESHOLD", 0.0) * unit_m
        touches_thr = bool(set(st["outer_boundary_source_ids"]) & thr_ids)
        if named and not thin:
            cls = "ROOM"
        elif thin:
            cls = "DOORWAY" if touches_thr else "WALL"
        else:
            cls = "UNLABELLED"
        faces.append({"face_id": st["site_id"], "class": cls, "area_m2": area, "perimeter_lm": per,
                      "threshold_lm": thr_len, "polygon": poly, "point": pt, "holes": st["holes"],
                      "name": named[0][0] if named else None, "wet": any(n[1] for n in named),
                      "names_found": sorted({n[0] for n in named}),
                      "threshold_ids": sorted(set(st["outer_boundary_source_ids"]) & thr_ids)})
    out = []
    for f in faces:
        if f["class"] != "ROOM":
            continue
        skirt = f["perimeter_lm"] - f["threshold_lm"]
        r = {"face_id": f["face_id"], "name": f["name"], "wet": f["wet"], "floor_m2": f["area_m2"],
             "perimeter_lm": f["perimeter_lm"], "door_widths_lm": f["threshold_lm"],
             "n_doors": len(f["threshold_ids"]), "label_conflict": len(f["names_found"]) > 1,
             "rules": ["UP-CER-001", "UP-CER-002", "UP-CER-003"]}
        if f["wet"]:
            doorway = sum(g["area_m2"] for g in faces if g["class"] == "DOORWAY" and
                          set(g["threshold_ids"]) & set(f["threshold_ids"]))
            r.update(wp_floor_m2=f["area_m2"] + doorway, wp_doorway_m2=doorway,
                     wp_upturn_m2=skirt * UPTURN_M, rules=r["rules"] + ["UP-WP-001", "UP-WP-002", "UP-WP-003"])
            if wall_tile_full_height is True:
                r.update(skirting_lm=0.0, skirting_state="ZERO_BY_RULE", rules=r["rules"] + ["UP-CER-004"])
            elif wall_tile_full_height is False:
                r.update(skirting_lm=skirt, skirting_state="MEASURED")
            else:
                r.update(skirting_lm=None, skirting_state="UNRESOLVED_WALL_TILE_HEIGHT",
                         skirting_alternatives={"FULL_HEIGHT_TILE (UP-CER-004)": 0.0, "PARTIAL_TILE": skirt})
        else:
            r.update(skirting_lm=skirt, skirting_state="MEASURED")
        out.append(r)
    risk = [{"KIND": "ROOM_" + f["class"], "face_id": f["face_id"], "area_m2": f["area_m2"]} for f in faces
            if f["class"] == "UNLABELLED"]
    risk += [{"KIND": "ROOM_LABEL_CONFLICT", "face_id": r["face_id"], "area_m2": r["floor_m2"]} for r in out
             if r["label_conflict"]]
    return {"policy": POLICY_ID, "rooms": out, "faces": faces, "coverage_risk": risk,
            "swing_widths_m": sorted(round(a["r"] * unit_m, 3) for a in swings),
            "arrangement": {"nodes": len(arr.nodes), "edges": len(arr.edges), "sites": len(sites)}}


def policy_record():
    return {"policy": POLICY_ID, "classes": ["ROOM", "DOORWAY", "WALL", "UNLABELLED"],
            "rules": ["UP-CER-001", "UP-CER-002", "UP-CER-003", "UP-CER-004", "UP-WP-001", "UP-WP-002", "UP-WP-003"],
            "rule": "rooms bounded by walls and door thresholds; area and one-sided perimeter from the topology; "
                    "skirting less door widths; wet-room skirting unresolved until the wall tile height is known"}
