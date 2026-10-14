"""ARCHITECTURAL COMPLETENESS (M9 S6, ARCH_TAKEOFF_V2) - every physical region and every eligible finish surface ends
in a measured quantity, an explicit exclusion with its reason, or a BLOCKED / RFI record. Never a silent gap.

    strip_register(S, floor)                 every DOORWAY face (a strip in the wall thickness) reviewed one by one
    strip_lines(ctx, strips, floor)          one BLOCKED_RFI line per opening: the measured strip, no material
    surface_rfis(ctx, M, floor, facts, ...)  RFI lines / records for surfaces V1 leaves silent (stair walls and
                                             skirting, the band above partial-height wet tile, exterior finish scope)
    coverage(S, M, strips, lines, unresolved, floor)
                                             three separate views: physical regions (the face partition), functional
                                             spaces (rooms x surfaces) and finish zones; UNACCOUNTED must be empty
    column_evidence(S, M, fills, box, floor) entity completeness for columns: every filled member-sized shape in the
                                             plan lies on a measured column or is listed with its room (review flag)
    unread_fills(S, M, fills, box, floor)    fills the plan reader does not read (deep / MINSERT hatches, SOLIDs)
    distorted_arc_blocks(inserts, box, floor) blocks with arcs (door swings) inserted at a non-uniform scale
    flag(rec, drawing, region)               the V2 records' cause / module / next action

It post-processes the V1 measurement (engine.source.arch_measure is not changed), so ARCH_TAKEOFF_V1 is unaffected.
Nothing here decides a material, a threshold finish, a garden finish, a kitchen membrane, a stair-hall finish or an
opening-deduction rule: each is measured where the geometry allows and handed to the owner as a question.

Strips: a DOORWAY face is bounded by the threshold lines of the opening(s) it lies in (arch_rooms tags each threshold
THR|<opening>|i) and possibly by a door closure or glazing lines. Its class comes from that evidence and is then
checked against the opening's own geometry (every vertex inside the opening's band box; depth <= the wall thickness):
    THRESHOLD       door / passage opening (or a door closed by its leaf symbol): a floor strip whose finish is not
                    established (Q-S6-1)
    WINDOW_REVEAL   the part of a window opening between a wall face and the glazing: wall below a sill OR floor of a
                    floor-level window / glazed door - the sill is not in the plan, so the floor status is not
                    established (never excluded automatically)
    UNATTRIBUTED    no opening, or openings of different kinds: reviewed as it is
Project-agnostic; stdlib only.
"""

from __future__ import annotations

import math
import re
from collections import defaultdict

from engine.source import arch_floor as AF
from engine.source import arch_measure as AM
from engine.source import arch_plan as AP
from engine.source import arch_rooms as AR
from engine.source import member_detection as MD

POLICY_ID = "ARCH_COMPLETENESS_V1"
TOL_M2 = 0.05
GEOM_TOL_M = 0.01
SURFACES = ("FLOOR", "CEILING", "WALLS", "SKIRTING")
SURFACE_ITEMS = {"FLOOR": ("FIN.FLOOR.PORCELAIN", "FIN.FLOOR.WET_TILE", "FIN.MARBLE.TREAD", "FIN.MARBLE.LANDING",
                           "FIN.STAIR.FLIGHT"),
                 "CEILING": ("FIN.CEILING",),
                 "WALLS": ("FIN.PLASTER", "FIN.PAINT", "FIN.WALL.TILE"),
                 "SKIRTING": ("FIN.SKIRTING",)}
STRIP_ITEMS = {"THRESHOLD": "ARCH.THRESHOLD", "WINDOW_REVEAL": "ARCH.WINDOW_REVEAL", "UNATTRIBUTED": "ARCH.THRESHOLD"}
Q_THRESHOLD = ("THRESHOLD_FINISH_NOT_ESTABLISHED (Q-S6-1): the strip of the opening in the wall thickness is floor; "
               "its finish (a threshold piece, the room floor continued, or other) and how it is measured are owner "
               "decisions - measured strip shown, no material assumed")
Q_REVEAL = ("WINDOW_REVEAL_FLOOR_STATUS_NOT_ESTABLISHED: the strip between the wall face and the glazing of a window "
            "opening is wall below the sill, or floor if the window reaches the floor (French window / glazed door); "
            "the sill height is not in the plan (window schedule / elevation) - measured strip shown, not counted as "
            "floor and not excluded")
Q_UNATTRIBUTED = ("STRIP_NOT_ATTRIBUTED: a strip in the wall thickness that no single opening kind bounds; review what "
                  "it is (door, window, passage or wall) - measured strip shown")
Q_STAIR_WALLS = ("STAIR_HALL_FINISH_NOT_ESTABLISHED (Q-S6-4): the stair enclosure's walls ({what}) carry no rule in "
                 "the architectural scope; measured wall run shown, no finish assumed")
Q_PAINT_BAND = ("FINISH_ABOVE_WALL_TILE_NOT_ESTABLISHED (Q7): the wall band between the wall tile ({tile:.2f} m) and "
                "the finish height ({paint:.2f} m) of a wet room has no finish rule (paint, tile to full height, other); "
                "band measured gross, before openings")
Q_PAINT_BAND_HEIGHTS = ("FINISH_ABOVE_WALL_TILE_NOT_ESTABLISHED (Q7): a wet room's finish above the wall tile has no "
                        "rule, and the tile height or the finish height is not established either")
Q_PAINT_BAND_EXPLICIT = ("WALL_BAND_ABOVE_EXPLICIT_TILE (Q7, UP-FIN-WALL-001): an explicit wall-tile height "
                         "({tile:.2f} m) governs this owner wet area below its finish height ({paint:.2f} m); the owner "
                         "rule tiles to full height, so the band between them has no finish until the project source "
                         "is confirmed; band measured gross, before openings")
Q_PAINT_BAND_EXPLICIT_HEIGHTS = ("WALL_BAND_ABOVE_EXPLICIT_TILE (Q7, UP-FIN-WALL-001): an explicit wall-tile height "
                                 "governs this owner wet area, and the finish height above it is not established")
Q_EXTERIOR = ("EXTERIOR_FINISH_SCOPE_NOT_ESTABLISHED (Q1): an external space ({codes}, {area:.2f} m2) - its floor "
              "finish (paving, planting, interlock, porcelain, ...), whether it is covered (a ceiling / soffit) and its "
              "wall finishes are owner decisions; no finish assumed")
EXCLUSIONS = {
    "WALL_AND_COLUMN_MASS": "the wall and column bodies: no floor surface",
    "SLIVERS": "a face below the space size limit (a drafting gap): no floor surface",
    "VOID": "an outlined void: open to below, no floor at this level",
    "STAIR_BELOW_SEEN": "the flight of the plan below seen through an opening: counted once, on the plan below",
    "SHAFT": "a shaft / duct: no internal floor finish (NO_FINISH policy of the architectural route since M9 S2; "
             "a shaft finish needs its own specification)",
}
FLAG_RULES = (
    # ARCH_TAKEOFF_V2.3 (owner_finish_scope; knowledge registry 1.0.0) - prefixes no earlier method emits
    (r"^WALL_BAND_ABOVE_EXPLICIT_TILE", "SOURCE", "arch_completeness.surface_rfis",
     "confirm the project's wall-tile height (it governs UP-FIN-WALL-001 full height) and give the band's finish"),
    (r"^THRESHOLD_OF_PROVISIONAL_DOOR", "SOURCE", "owner_finish_scope.threshold_lines",
     "give the door schedule, or draw the door's opening in the wall band: the strip then takes UP-THR-001"),
    (r"^THRESHOLD_STRIP_NOT_ATTRIBUTED", "REVIEW", "owner_finish_scope.threshold_lines",
     "review which doorway owns the strip against the drawing"),
    (r"^PANTRY_THRESHOLD_RULE_CONFLICT", "REVIEW", "owner_finish_scope.threshold_lines",
     "owner question OQ-01 (knowledge registry conflict CF-03)"),
    (r"^DOOR_OPENING_HEAD_ALLOWANCE", "REVIEW", "door_standards.door_scenarios",
     "owner question OQ-02 (knowledge registry conflict CF-11): the head allowance of an enlarged wall opening"),
    (r"^THRESHOLD_FINISH_NOT_ESTABLISHED", "SOURCE", "arch_completeness.strip_lines",
     "give the threshold finish and its measurement rule (owner decision Q-S6-1), or the door / window schedule"),
    (r"^WINDOW_REVEAL_FLOOR_STATUS_NOT_ESTABLISHED", "SOURCE", "arch_completeness.strip_lines",
     "give the window sill heights (window schedule / elevations): a sill above the floor makes the strip wall"),
    (r"^STRIP_NOT_ATTRIBUTED", "REVIEW", "arch_completeness.strip_register",
     "review the strip against the drawing: which opening (if any) it belongs to"),
    (r"^STAIR_HALL_FINISH_NOT_ESTABLISHED", "SOURCE", "arch_completeness.surface_rfis",
     "decide the stair-hall wall finishes and skirting (owner decision Q-S6-4) from the finish schedule"),
    (r"^FINISH_ABOVE_WALL_TILE_NOT_ESTABLISHED", "SOURCE", "arch_completeness.surface_rfis",
     "decide the finish above partial-height wet-room tile (owner decision Q7) and give the heights"),
    (r"^EXTERIOR_FINISH_SCOPE_NOT_ESTABLISHED", "SOURCE", "arch_completeness.surface_rfis",
     "give the external works / landscape scope and finish schedule (owner decision Q1)"),
    (r"^COLUMN_EVIDENCE_NOT_MEASURED", "SOFTWARE", "arch_completeness.column_evidence",
     "check the listed fills against the drawing: a column the plan reader lost leaves the room's net floor, skirting "
     "and column faces unmeasured (the reader fix is S6 Phase 2; --layer-roles LAYER=COLUMN where the layer is right)"),
    (r"^FILLS_NOT_READ", "SOFTWARE", "arch_completeness.unread_fills",
     "check the room against the drawing (the fills sit in nested blocks / MINSERT cells / SOLIDs; reading them is "
     "S6 Phase 2), or bind / explode the blocks in CAD"),
    (r"^DOOR_SYMBOLS_DISTORTED", "SOFTWARE", "arch_completeness.distorted_arc_blocks",
     "check the openings of this plan: a door drawn with a non-uniformly scaled block may be classed as a passage"),
    (r"^ADMISSION:", "REVIEW", "engine.source.discovery", "see DRAWING_DISCOVERY.json: the finding and its remedy"),
)


def flag(rec, *, drawing, region=None):
    cause, mod, nxt = "REVIEW", "arch_completeness", "review the item against the drawings"
    for pat, c, m, a in FLAG_RULES:
        if re.search(pat, rec.get("reason") or "", re.I) or re.search(pat, rec.get("item") or ""):
            cause, mod, nxt = c, m, a
            break
    ref = {"drawing": drawing}
    if region:
        ref.update(region_id=region.get("region_id"), sheet_id=region.get("sheet_id"))
    return dict(rec, location={"floor": rec.get("floor"), "room_id": rec.get("room_id")}, source_ref=ref,
                module_function=mod, cause=cause, next_action=nxt)


# ====================================================================== strips
def _box_of(o):
    return o["u"], o["n"], min(o["s0"], o["s1"]), max(o["s0"], o["s1"]), min(o["o0"], o["o1"]), max(o["o0"], o["o1"])


def _within(poly, o, tol):
    (ux, uy), (nx, ny), s0, s1, o0, o1 = _box_of(o)
    for x, y in poly:
        s, t = x * ux + y * uy, x * nx + y * ny
        if not (s0 - tol <= s <= s1 + tol and o0 - tol <= t <= o1 + tol):
            return False
    return True


def strip_register(S, floor):
    """-> [strip], one per DOORWAY face, with its evidence, geometry check, class and disposition."""
    u = S["unit_m"]
    ops = S.get("openings_by_id") or {o["opening_id"]: o for o in S.get("openings") or ()}
    out = []
    for f in S["faces"]:
        if f["class"] != "DOORWAY":
            continue
        oids = list(f.get("opening_ids") or ())
        kinds = sorted({ops[i]["kind"] for i in oids if i in ops})
        closures = sorted({c.rsplit("|", 1)[0] for c in f.get("closure_ids") or ()})
        roles = {k: round(v, 4) for k, v in (f.get("outer_role_lm") or {}).items()}
        glazing = roles.get("WINDOW", 0.0) > 0
        if kinds == ["WINDOW"]:
            cls = "WINDOW_REVEAL"
        elif kinds and set(kinds) <= {"DOOR", "PASSAGE"}:
            cls = "THRESHOLD"
        elif not kinds and closures:
            cls = "THRESHOLD"
        else:
            cls = "UNATTRIBUTED"
        geom = {"checked_against": oids, "within_opening_box": None, "depth_m": None, "wall_t_m": None}
        if oids and all(i in ops for i in oids):
            o = ops[oids[0]]
            width = o.get("width_m") or 0.0
            geom.update(within_opening_box=all(_within(f["polygon"], ops[i], GEOM_TOL_M / u) for i in oids),
                        depth_m=round(f["area_m2"] / width, 4) if width else None,
                        wall_t_m=round(o.get("wall_t_m") or 0.0, 4), opening_width_m=round(width, 4))
            if geom["depth_m"] is not None and geom["wall_t_m"]:
                geom["depth_within_wall"] = geom["depth_m"] <= geom["wall_t_m"] + GEOM_TOL_M
            # the strip's own extent in the opening's frame (along the wall / across it), for the reviewer
            (ux, uy), (nx, ny) = o["u"], o["n"]
            ss_ = [x * ux + y * uy for x, y in f["polygon"]]
            tt_ = [x * nx + y * ny for x, y in f["polygon"]]
            geom["extent_along_m"] = round((max(ss_) - min(ss_)) * u, 4)
            geom["extent_across_m"] = round((max(tt_) - min(tt_)) * u, 4)
        verified = bool(geom.get("within_opening_box")) and geom.get("depth_within_wall", False)
        if cls == "WINDOW_REVEAL":
            geom["bounded_by_glazing"] = glazing
            verified = verified and glazing
        geom["failed_checks"] = [c for c, ok in (("NO_OPENING", bool(oids)), ("OPENING_UNKNOWN", all(i in ops for i in oids)),
                                                 ("OUTSIDE_OPENING_BOX", geom.get("within_opening_box")),
                                                 ("DEPTH_OVER_WALL", geom.get("depth_within_wall")),
                                                 ("NOT_BOUNDED_BY_GLAZING", geom.get("bounded_by_glazing", True)),
                                                 ("SPANS_SEVERAL_OPENINGS", len(oids) <= 1),
                                                 ("MIXED_OPENING_KINDS", len(kinds) <= 1))
                                 if ok is False or (ok is None and c not in ("OUTSIDE_OPENING_BOX", "DEPTH_OVER_WALL"))]
        q = {"THRESHOLD": Q_THRESHOLD, "WINDOW_REVEAL": Q_REVEAL, "UNATTRIBUTED": Q_UNATTRIBUTED}[cls]
        if cls != "UNATTRIBUTED" and not verified and not (cls == "THRESHOLD" and closures and not oids):
            q = Q_UNATTRIBUTED + f" (classified {cls} from its boundary, but its geometry does not fit the opening)"
            cls = "UNATTRIBUTED"
        out.append({"strip_id": f["face_id"], "floor": floor, "area_m2": round(f["area_m2"], 6),
                    "opening_ids": oids, "opening_kinds": kinds, "door_closures": closures, "bounded_by_lm": roles,
                    "class": cls, "geometry": geom, "geometry_verified": verified,
                    "floor_status": {"THRESHOLD": "FLOOR (finish not established)",
                                     "WINDOW_REVEAL": "NOT_ESTABLISHED (sill height not in the plan)",
                                     "UNATTRIBUTED": "NOT_ESTABLISHED"}[cls],
                    "disposition": "BLOCKED_RFI", "question": q,
                    "polygon_m": [(round(x * u, 4), round(y * u, 4)) for x, y in f["polygon"]]})
    return out


def _pseudo_room(floor, key, what):
    return {"room_id": f"{floor}-{key}", "floor": floor, "name_en": what, "name_ar": AR.UNNAMED[1]}


def strip_lines(ctx, strips, floor):
    """one BLOCKED_RFI line per opening (strips of one opening grouped; unattributed strips one line each)."""
    groups = defaultdict(list)
    for s in strips:
        key = (s["class"], "+".join(s["opening_ids"]) or "+".join(s["door_closures"]) or s["strip_id"])
        groups[key].append(s)
    lines, unresolved = [], []
    for (cls, key), ss in sorted(groups.items()):
        safe = re.sub(r"[^A-Za-z0-9+_-]", "_", key)[:60]
        what = {"THRESHOLD": "threshold strip", "WINDOW_REVEAL": "window reveal strip",
                "UNATTRIBUTED": "unattributed strip"}[cls]
        room = _pseudo_room(floor, f"STRIP-{safe}", f"{what} {key}")
        m2 = round(sum(s["area_m2"] for s in ss), 6)
        g = ss[0]["geometry"]
        lines.append(AM._line(ctx, item_code=STRIP_ITEMS[cls], room=room, element=what, unit="m2", net=None,
                              formula="sum of the strip faces of the opening in the wall thickness (TS01)",
                              inputs={"measured_strip_m2": m2, "strips": [s["strip_id"] for s in ss],
                                      "opening_ids": ss[0]["opening_ids"], "opening_kinds": ss[0]["opening_kinds"],
                                      "door_closures": ss[0]["door_closures"],
                                      "opening_width_m": g.get("opening_width_m"), "wall_t_m": g.get("wall_t_m"),
                                      "geometry_verified": all(s["geometry_verified"] for s in ss),
                                      "floor_status": ss[0]["floor_status"]},
                              rule_id=None, rfi={"question": ss[0]["question"], "unlocks": room["room_id"]}))
        unresolved.append({"room_id": room["room_id"], "floor": floor, "item": STRIP_ITEMS[cls],
                           "reason": ss[0]["question"] + f" [{m2:.3f} m2]"})
    return lines, unresolved


# ====================================================================== surfaces V1 leaves silent
def _room_lines(lines, rid):
    return [ln for ln in lines if (ln.get("location") or {}).get("room_id") == rid]


def _h(ln):
    return ((ln.get("calculation") or {}).get("inputs") or {}).get("height_m")


def surface_rfis(ctx, M, floor, facts=None, floor_level_m=None, floor_above_level_m=None, owner_scope=False):
    """-> (lines, unresolved) for the surfaces V1 measures with no line and no RFI. owner_scope (ARCH_TAKEOFF_V2.3):
    the paint band of an owner wet area follows UP-FIN-WALL-001 / UP-FIN-PAINT-001 (full-height porcelain: no band,
    no question)."""
    lines, unresolved = [], []
    for rm in M["rooms"]:
        rid, kind = rm["room_id"], rm.get("kind")
        mine = _room_lines(M["lines"], rid)
        if owner_scope and (rm.get("finish_scope") or {}).get("scope") == "WET" and rm["class"] in ("ROOM", "MIXED"):
            from engine.source import owner_finish_scope as OFS
            if any(ln["item_code"] == "FIN.PAINT" for ln in mine):
                continue
            hs = AM.heights(floor, rm.get("level_m") if rm.get("level_m") is not None else floor_level_m,
                            floor_above_level_m, facts or {})
            th = OFS.wall_tile_height(hs)
            if th["full"]:
                lines.append(AM._line(ctx, item_code="FIN.PAINT", room=rm, element="paint above wall tile",
                                      unit="m2", net=None, ev="NOT_APPLICABLE_WITH_EVIDENCE",
                                      formula="UP-FIN-PAINT-001: full-height wall porcelain, no band above it",
                                      inputs={"wall_tile_governing": th.get("governing")}, rule_id="UP-FIN-PAINT-001",
                                      notes="no paint: the wall porcelain of an owner wet area runs to the finished "
                                            "ceiling (UP-FIN-WALL-001)"))
                continue
            # an explicit wall-tile height below the finish height governs (precedence over the owner rule): the band
            # above it is part of that flagged conflict (WALL_TILE_BELOW_OWNER_FULL_HEIGHT), not an open finish rule
            tile = next((ln for ln in mine if ln["item_code"] == "FIN.WALL.TILE" and _h(ln) is not None), None)
            t_h = _h(tile) if tile is not None else th.get("value_m")
            paint = hs["PAINT"]["value_m"] if hs["PAINT"]["state"] == "ESTABLISHED" else None
            if t_h is not None and paint is not None:
                run = ((tile.get("calculation") or {}).get("inputs") or {}).get("wall_run_lm") if tile else None
                q = Q_PAINT_BAND_EXPLICIT.format(tile=t_h, paint=paint)
                inputs = {"wall_tile_h_m": t_h, "finish_h_m": paint, "band_h_m": round(paint - t_h, 6),
                          "wall_run_lm": run,
                          "band_gross_m2": round(run * (paint - t_h), 6) if run is not None else None}
            else:
                q = Q_PAINT_BAND_EXPLICIT_HEIGHTS
                inputs = {"wall_tile_h_m": t_h, "finish_h_m": paint}
            lines.append(AM._line(ctx, item_code="FIN.PAINT", room=rm, element="finish above wall tile", unit="m2",
                                  net=None, formula="wall run x (finish height - wall tile height), before openings",
                                  inputs=inputs, rule_id="UP-FIN-WALL-001", rfi={"question": q, "unlocks": rid}))
            unresolved.append({"room_id": rid, "floor": floor, "item": "FIN.PAINT", "reason": q})
            continue
        if kind == AR.STAIR:
            run = (rm.get("runs_lm") or {}).get("perimeter") or rm.get("perimeter_lm")
            wall = (rm.get("runs_lm") or {}).get("wall")
            for code, el, what in (("FIN.PLASTER", "stair hall plaster", "plaster"),
                                   ("FIN.PAINT", "stair hall paint", "paint"),
                                   ("FIN.SKIRTING", "stair hall skirting", "skirting")):
                if any(ln["item_code"] == code for ln in mine):
                    continue
                q = Q_STAIR_WALLS.format(what=what)
                lines.append(AM._line(ctx, item_code=code, room=rm, element=el, unit="lm" if code == "FIN.SKIRTING"
                                      else "m2", net=None, formula="stair enclosure walls (finish scope not established)",
                                      inputs={"perimeter_lm": run, "wall_lm": wall, "runs_lm": rm.get("runs_lm")},
                                      rule_id=None, rfi={"question": q, "unlocks": rid}))
                unresolved.append({"room_id": rid, "floor": floor, "item": code, "reason": q})
        elif kind == AR.WET and rm["class"] in ("ROOM", "MIXED"):
            if any(ln["item_code"] == "FIN.PAINT" for ln in mine):
                continue
            tile = next((ln for ln in mine if ln["item_code"] == "FIN.WALL.TILE" and _h(ln) is not None), None)
            hs = AM.heights(floor, rm.get("level_m") if rm.get("level_m") is not None else floor_level_m,
                            floor_above_level_m, facts or {})
            paint = hs["PAINT"]["value_m"] if hs["PAINT"]["state"] == "ESTABLISHED" else None
            if tile is not None and paint is not None and _h(tile) >= paint - 1e-6:
                lines.append(AM._line(ctx, item_code="FIN.PAINT", room=rm, element="paint above wall tile",
                                      unit="m2", net=None, ev="NOT_APPLICABLE_WITH_EVIDENCE",
                                      formula="no band: the wall tile reaches the finish height",
                                      inputs={"wall_tile_h_m": _h(tile), "finish_h_m": paint}, rule_id=None,
                                      notes="the wall tile runs to the finish height: no wall band above it"))
                continue
            if tile is not None and paint is not None:
                run = ((tile.get("calculation") or {}).get("inputs") or {}).get("wall_run_lm")
                q = Q_PAINT_BAND.format(tile=_h(tile), paint=paint)
                inputs = {"wall_tile_h_m": _h(tile), "finish_h_m": paint, "band_h_m": round(paint - _h(tile), 6),
                          "wall_run_lm": run,
                          "band_gross_m2": round(run * (paint - _h(tile)), 6) if run is not None else None}
            else:
                q = Q_PAINT_BAND_HEIGHTS
                inputs = {"wall_tile_h_m": _h(tile) if tile else None, "finish_h_m": paint}
            lines.append(AM._line(ctx, item_code="FIN.PAINT", room=rm, element="finish above wall tile", unit="m2",
                                  net=None, formula="wall run x (finish height - wall tile height), before openings",
                                  inputs=inputs, rule_id=None, rfi={"question": q, "unlocks": rid}))
            unresolved.append({"room_id": rid, "floor": floor, "item": "FIN.PAINT", "reason": q})
        elif kind == AR.EXTERIOR:
            q = Q_EXTERIOR.format(codes="+".join(rm.get("codes") or ()) or "-", area=rm.get("area_m2") or 0.0)
            unresolved.append({"room_id": rid, "floor": floor, "item": "ARCH.EXTERIOR", "reason": q})
    return lines, unresolved


# ====================================================================== entity completeness (columns, door symbols)
def _quad_sides(ring):
    pts = []
    for p in ring:
        if not pts or math.dist(p, pts[-1]) > 1e-9:
            pts.append(p)
    if len(pts) > 1 and math.dist(pts[0], pts[-1]) <= 1e-9:
        pts.pop()
    if len(pts) != 4:
        return None, None
    return [math.dist(pts[i], pts[(i + 1) % 4]) for i in range(4)], pts


def _in_box(p, b, tol=0.0):
    return b[0] - tol <= p[0] <= b[2] + tol and b[1] - tol <= p[1] <= b[3] + tol


def column_evidence(S, M, fills, box, floor, column_layers=()):
    """S6 entity completeness for columns. `fills`: every filled shape of the drawing in WCS (HATCH boundary paths and
    SOLID / TRACE outlines, at every block depth, MINSERT cells expanded - tools.arch_discovery.shapes), read
    independently of the plan reader. Each filled quadrilateral inside the plan region with every side in the column
    size range (arch_plan.COLUMN_SIDE_M) either lies on a column the route measured, or is listed with the face / room
    it stands in. A listed fill is a column the plan reader lost (a nested block, a MINSERT, a SOLID fill, a rotated or
    exploded outline, a layer with too few columns to be classed) OR a hatched wall piece / fixture: it is a review
    flag on that room, never a quantity and never a deduction.
    column_layers: the layers the route classed COLUMN on any plan of the drawing. When there are some, only fills on
    those (effective) layers are candidates - fixtures and finish hatches on other layers are counted, not listed;
    when the drawing has no column layer at all, every member-sized fill is a candidate.
    -> {"fills_in_plan", "member_sized", "on_measured_columns", "on_other_layers", "unmeasured": [...]}"""
    u = S["unit_m"]
    lo, hi = AP.COLUMN_SIDE_M
    tol = 0.02 / u
    cols = S.get("column_boxes") or ()
    room_of = {r["face_id"]: r["room_id"] for r in M["rooms"]}
    cl = set(column_layers or ())
    n_in, member, on, other, out = 0, 0, 0, 0, []
    for i, f in enumerate(fills):
        sides, pts = _quad_sides(f["ring"])
        if not pts:
            if f["ring"] and all(_in_box(p, box) for p in f["ring"]):
                n_in += 1
            continue
        c = (sum(p[0] for p in pts) / 4, sum(p[1] for p in pts) / 4)
        if not _in_box(c, box):
            continue
        n_in += 1
        if not all(lo <= x * u <= hi for x in sides):
            continue
        member += 1
        if any(_in_box(c, b, tol) for b in cols):
            on += 1
            continue
        if cl and f["layer"] not in cl:
            other += 1
            continue
        face = next((fc for fc in S["faces"] if MD.point_in_poly(c[0], c[1], fc["polygon"]) and
                     not any(MD.point_in_poly(c[0], c[1], h) for h in fc.get("hole_polygons") or ())), None)
        out.append({"fill": f.get("fill_id", i), "kind": f["kind"], "block_depth": f["depth"], "layer": f["layer"],
                    "centre": (round(c[0], 3), round(c[1], 3)), "sides_m": [round(x * u, 4) for x in sides],
                    "face_id": face["face_id"] if face else None, "face_class": face["class"] if face else None,
                    "room_id": room_of.get(face["face_id"]) if face else None})
    return {"floor": floor, "fills_in_plan": n_in, "member_sized": member, "on_measured_columns": on,
            "on_other_layers": other, "column_layers": sorted(cl), "measured_columns": len(cols), "unmeasured": out}


def column_records(ev):
    """the review records of column_evidence: one per room (or per floor for fills in no room) - travel with the BOQ."""
    by = defaultdict(list)
    for x in ev["unmeasured"]:
        by[x["room_id"] or "-"].append(x)
    out = []
    for rid, xs in sorted(by.items()):
        where = "in this room" if rid != "-" else "in wall mass / outside every space"
        out.append({"room_id": rid, "floor": ev["floor"], "item": "COLUMN_EVIDENCE",
                    "reason": f"COLUMN_EVIDENCE_NOT_MEASURED: {len(xs)} filled member-sized shape(s) {where} are not "
                              "measured as columns (a lost column, or a hatched wall piece / fixture); the room's floor, "
                              "skirting and wall quantities are unverified until reviewed: "
                              + "; ".join(f"{x['kind']}@{x['centre']} {x['sides_m'][0]}x{x['sides_m'][1]} m "
                                          f"layer {x['layer']} depth {x['block_depth']}" for x in xs[:8])})
    return out


def unread_fills(S, M, fills, box, floor):
    """the fills inside the plan region that the plan reader does not read (tools.arch_discovery.shapes marks them:
    hatches nested two or more block levels deep or in a later MINSERT cell, SOLID / TRACE fills): a column, finish or
    zone hatch drawn that way is missing from the measurement. -> (summary, records), one record per room touched
    (the fill's centre; '-' for wall mass / outside every space). A review flag, never a quantity."""
    room_of = {r["face_id"]: r["room_id"] for r in M["rooms"]}
    by = defaultdict(list)
    n = 0
    for f in fills:
        if not f.get("unread_by_plan_reader") or not f["ring"]:
            continue
        c = (sum(p[0] for p in f["ring"]) / len(f["ring"]), sum(p[1] for p in f["ring"]) / len(f["ring"]))
        if not _in_box(c, box):
            continue
        n += 1
        face = next((fc for fc in S["faces"] if MD.point_in_poly(c[0], c[1], fc["polygon"]) and
                     not any(MD.point_in_poly(c[0], c[1], h) for h in fc.get("hole_polygons") or ())), None)
        by[room_of.get(face["face_id"], "-") if face else "-"].append(f)
    recs = []
    for rid, fs in sorted(by.items()):
        kinds = dict(sorted(defaultdict(int, {k: sum(1 for f in fs if f["kind"] == k) for k in {f["kind"] for f in fs}}).items()))
        recs.append({"room_id": rid, "floor": floor, "item": "UNREAD_FILLS",
                     "reason": f"FILLS_NOT_READ: {len(fs)} fill(s) {kinds} "
                               f"{'in this room' if rid != '-' else 'in wall mass / outside every space'} are not "
                               "read by the plan reader (a hatch two or more block levels deep or in a later MINSERT "
                               "cell, a SOLID fill): a column, finish zone or area drawn by them is missing from the "
                               "measurement - the room's quantities are unverified until reviewed"})
    return {"floor": floor, "unread_fills": n, "rooms": sorted(by)}, recs


def distorted_arc_blocks(inserts, box, floor):
    """inserts: blocks drawing arcs / circles inserted at a non-uniform scale (tools.arch_discovery.shapes) - their
    swings are read as ellipses, so a door drawn with one may be classed as a passage. -> records in this plan."""
    xs = [x for x in inserts if _in_box(x["at"], box)]
    if not xs:
        return []
    return [{"room_id": "-", "floor": floor, "item": "DOOR_SYMBOLS",
             "reason": f"DOOR_SYMBOLS_DISTORTED: {len(xs)} block(s) with arcs inserted at a non-uniform scale in this "
                       "plan (" + ", ".join(sorted({x['block'] for x in xs}))[:200] + "): the door swings are not "
                       "read as swings, so the opening kinds (door / passage) of this plan are unverified"}]


# ====================================================================== coverage
def _items(lines, rid, codes):
    return [ln for ln in lines if (ln.get("location") or {}).get("room_id") == rid and ln["item_code"] in codes]


def _rfis(unresolved, rid, codes):
    return [u for u in unresolved if u.get("room_id") == rid and any(str(u.get("item") or "").startswith(c)
                                                                      for c in codes)]


def _cell(state, **ev):
    return dict(state=state, **ev)


def _space_cover(rm, lines, unresolved):
    """{surface: cell} for one functional space."""
    rid, kind, cls = rm["room_id"], rm.get("kind"), rm["class"]
    space_rfi = _rfis(unresolved, rid, ("ARCH.SPACE", "FIN.FLOOR / zone"))
    measured = cls == "ROOM" or (cls == "MIXED" and kind is not None)
    out = {}
    for surf in SURFACES:
        if kind == AR.SHAFT:
            out[surf] = _cell("EXCLUDED", reason=EXCLUSIONS["SHAFT"])
            continue
        if kind == AR.VOID:
            out[surf] = _cell("EXCLUDED", reason="an outlined void has no surface of its own (open to below; the "
                                                 "ceiling over it is the room's 'ceiling over void' line)")
            continue
        if kind == AR.EXTERIOR:
            r = _rfis(unresolved, rid, ("ARCH.EXTERIOR",))
            out[surf] = _cell("RFI", records=len(r)) if r else _cell("UNACCOUNTED", why="no exterior scope record")
            continue
        if not measured:
            out[surf] = _cell("RFI", records=len(space_rfi), why="the space is not named / not one finish: one space "
                              "question covers all its surfaces") if space_rfi else \
                _cell("UNACCOUNTED", why="unmeasured space without a space RFI")
            continue
        ls = _items(lines, rid, SURFACE_ITEMS[surf])
        rf = _rfis(unresolved, rid, SURFACE_ITEMS[surf])
        if ls:
            states = sorted({ln["evidence_state"] for ln in ls})
            qty = round(sum(ln.get("measured_net") or 0.0 for ln in ls), 6)
            out[surf] = _cell("LINE" if any(ln.get("measured_net") is not None for ln in ls) else
                              ("EXCLUDED" if states == ["NOT_APPLICABLE_WITH_EVIDENCE"] else "RFI"),
                              lines=len(ls), evidence_states=states, measured=qty, rfis=len(rf))
        elif rf:
            out[surf] = _cell("RFI", records=len(rf))
        else:
            out[surf] = _cell("UNACCOUNTED", why=f"no {surf.lower()} line and no RFI")
    return out


def coverage(S, M, strips, lines, unresolved, floor):
    """-> {"physical_regions", "functional_spaces", "finish_zones", "unaccounted", "gate"} for one floor plan."""
    u = S["unit_m"]
    rooms = {r["face_id"]: r for r in M["rooms"]}
    measured = {r["face_id"] for r in M["rooms"] if r["class"] == "ROOM" or (r["class"] == "MIXED" and r["kind"])}
    strip_of = {s["strip_id"]: s for s in strips}
    strip_line_of = {}
    for ln in lines:
        # ARCH_TAKEOFF_V2.3 (UP-THR-001): a marble threshold / doorway-strip porcelain line accounts for its strips
        # (no V1 .. V2.2 floor line names strips)
        if ln["item_code"] in STRIP_ITEMS.values() or ln["item_code"] in ("FIN.MARBLE.THRESHOLD", "FIN.FLOOR.PORCELAIN"):
            for sid in ((ln.get("calculation") or {}).get("inputs") or {}).get("strips") or ():
                strip_line_of[sid] = ln["line_id"]
    faces, cat = [], defaultdict(lambda: defaultdict(float))
    unaccounted = []
    for f in S["faces"]:
        parts = AF.split_face(f, S.get("voids") or (), u, f["face_id"] in measured)
        rm = rooms.get(f["face_id"])
        rid = rm["room_id"] if rm else None
        for c, m2 in sorted(parts.items()):
            if c in EXCLUSIONS:
                st, ev = "EXCLUDED", {"reason": EXCLUSIONS[c]}
            elif c == "DOORWAY_STRIPS":
                s = strip_of.get(f["face_id"])
                if s and strip_line_of.get(f["face_id"]):
                    st, ev = "RFI", {"strip_class": s["class"], "line_id": strip_line_of[f["face_id"]]}
                else:
                    st, ev = "UNACCOUNTED", {"why": "a strip with no strip line"}
            elif c in ("ROOM_FLOOR", "OPEN_PLAN_FLOOR"):
                ls = _items(lines, rid, ("FIN.FLOOR.PORCELAIN", "FIN.FLOOR.WET_TILE")) if rid else []
                st, ev = ("LINE", {"lines": len(ls), "measured": round(sum(ln.get("measured_net") or 0 for ln in ls), 6)}) \
                    if ls else ("UNACCOUNTED", {"why": "a finished floor with no floor line"})
            elif c.startswith("UNALLOCATED"):
                ls = _items(lines, rid, ("ARCH.SPACE",)) if rid else []
                rf = _rfis(unresolved, rid, ("ARCH.SPACE", "FIN.FLOOR / zone")) if rid else []
                st, ev = ("RFI", {"space_lines": len(ls), "rfis": len(rf)}) if ls and rf else \
                    ("UNACCOUNTED", {"why": "an unallocated space without its space line and question"})
            elif c == "STAIR_FLIGHTS":
                ls = _items(lines, rid, ("FIN.MARBLE.TREAD",)) if rid else []
                st, ev = ("LINE" if any(ln.get("measured_net") is not None for ln in ls) else "RFI",
                          {"tread_lines": len(ls)}) if ls else ("UNACCOUNTED", {"why": "stair treads with no line"})
            elif c == "STAIR_LANDINGS_BOUND":
                ls = _items(lines, rid, ("FIN.MARBLE.LANDING",)) if rid else []
                rf = _rfis(unresolved, rid, ("FIN.MARBLE.LANDING",)) if rid else []
                st, ev = ("RFI" if not any(ln.get("measured_net") is not None for ln in ls) else "LINE",
                          {"landing_lines": len(ls), "rfis": len(rf)}) if ls or rf else \
                    ("UNACCOUNTED", {"why": "stair landings with no line and no RFI"})
            elif c == "EXTERNAL":
                ls = _items(lines, rid, ("ARCH.EXTERIOR",)) if rid else []
                rf = _rfis(unresolved, rid, ("ARCH.EXTERIOR",)) if rid else []
                st, ev = ("RFI", {"space_lines": len(ls), "rfis": len(rf)}) if ls and rf else \
                    ("UNACCOUNTED", {"why": "an external space without its line and scope question"})
            else:
                st, ev = "UNACCOUNTED", {"why": f"category {c} has no coverage rule"}
            cat[c][st] += m2
            row = {"face_id": f["face_id"], "class": f["class"], "room_id": rid, "category": c,
                   "m2": round(m2, 6), "state": st, **ev}
            faces.append(row)
            if st == "UNACCOUNTED":
                unaccounted.append(dict(row, view="PHYSICAL"))
    spaces = []
    for rm in M["rooms"]:
        cells = _space_cover(rm, lines, unresolved)
        spaces.append({"room_id": rm["room_id"], "face_id": rm["face_id"], "class": rm["class"], "kind": rm.get("kind"),
                       "codes": rm.get("codes"), "area_m2": round(rm.get("area_m2") or 0.0, 6), "surfaces": cells})
        for surf, c in cells.items():
            if c["state"] == "UNACCOUNTED":
                unaccounted.append({"view": "FUNCTIONAL", "room_id": rm["room_id"], "surface": surf, **c})
    fin = defaultdict(lambda: defaultdict(float))
    for ln in lines:
        if (ln.get("location") or {}).get("floor") == floor and ln["item_code"].startswith(("FIN.", "ARCH.")):
            fin[ln["item_code"]][ln["evidence_state"]] += ln.get("measured_net") or 0.0
    total = sum(f["area_m2"] for f in S["faces"])
    covered = sum(v for d in cat.values() for v in d.values())
    return {"policy": POLICY_ID, "floor": floor,
            "physical_regions": {"faces_m2": round(total, 4), "covered_m2": round(covered, 4),
                                 "by_category": {c: {s: round(v, 4) for s, v in sorted(d.items())}
                                                 for c, d in sorted(cat.items())},
                                 "faces": faces, "strips": strips},
            "functional_spaces": spaces,
            "finish_zones": {"zones": [{k: z.get(k) for k in ("face_id", "state", "zones")}
                                       for z in S.get("zones") or ()],
                             "finish_lines": {k: {s: round(v, 4) for s, v in sorted(d.items())}
                                              for k, d in sorted(fin.items())}},
            "unaccounted": unaccounted,
            "gate": "PASS" if not unaccounted and abs(total - covered) <= TOL_M2 else "FAIL",
            "rule": "every face part ends in LINE / RFI / EXCLUDED (with its reason); every space x surface "
                    "(floor, ceiling, walls, skirting) ends in LINE / RFI / EXCLUDED; UNACCOUNTED fails the run"}


def policy_record():
    return {"policy_id": POLICY_ID, "surfaces": list(SURFACES), "surface_items": SURFACE_ITEMS,
            "strip_items": STRIP_ITEMS, "exclusions": EXCLUSIONS, "geometry_tol_m": GEOM_TOL_M,
            "never": ["a threshold material", "a garden / exterior finish", "a kitchen membrane", "a stair-hall finish",
                      "an opening-deduction rule", "a window reveal counted as floor or excluded without its sill"]}
