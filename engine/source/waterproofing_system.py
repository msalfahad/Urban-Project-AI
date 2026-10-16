"""WATERPROOFING SYSTEM (M9 Phase 2B-2, ARCH_TAKEOFF_V2.4 only) - the owner's membrane standards (knowledge registry
1.1.0: UP-WP-001 roll, UP-WP-002 lap, UP-WP-003 upturn, UP-WP-004 penetrations, UP-WP-MAT-001 three quantities,
UP-WP-LAY-001 layout, UP-WP-DOOR-001 doorway transitions) applied to every waterproofed area of a run, every value
resolved through the project rules (UP-RULES-001).

    system_spec(resolver, target)          -> the membrane spec of an area and the resolution of each value
    penetrations(room, ents, unit_m)       -> drains / outlets / sleeves drawn inside the area (counted), fixtures
                                              (indicative only), the state (COUNTED_FROM_DRAWING / NOT_SHOWN)
    transitions(area, resolver)            -> one record per doorway / break: continuation, threshold transition or
                                              termination, its alternatives with quantities, the selected detail
    room_layout(area, spec, c)             -> the membrane layout of the area (membrane_layout's polygon strips, at
                                              least two orientations, a deterministic selection) with the corners,
                                              penetrations and withheld detailing of this module
    area_schedule(area, layout)            -> the area's schedule row: A net, B installed, independent rolls, waste
    cutting_plan(areas)                    -> per membrane system: every area's full-width pieces cut from shared
                                              rolls (first fit decreasing): the procurement rolls (C)
    schedule(areas, plans)                 -> per area, per floor, per system and project totals
    boq_lines(ctx, areas, line)            -> the ARCH_TAKEOFF_V2.4 waterproofing lines: FIN.WP.WALL_UPTURN,
                                              FIN.WP.DOORWAY_TRANSITION, FIN.WP.TERMINATION, FIN.WP.PENETRATION

Three quantities, never mixed (UP-WP-MAT-001): A the net area (the BOQ line FIN.WP.FLOOR), B the installed membrane
(laid area: coverage + upturns + doorway pieces + laps, from the layout), C the procurement rolls (the cutting plan).
A roll count is CONFIRMED only with a project-specified system, measured geometry and every detail resolved; otherwise
PROVISIONAL with what is withheld. Nothing here changes a drawn dimension. Project-agnostic; stdlib only."""

from __future__ import annotations

import copy
import math
import re

from engine.source import knowledge as K
from engine.source import material_spec as MS
from engine.source import membrane_layout as ML

POLICY_ID = "WATERPROOFING_SYSTEM_V1"
METHOD = "MEMBRANE_POLYGON_STRIPS_V2_4"
TOL_M = 0.02
WET, EXTERIOR = "WET", "EXTERIOR"
DEFAULT_SYSTEM = {WET: "URBAN_DEFAULT_WET_AREA", EXTERIOR: "URBAN_DEFAULT_EXTERIOR"}
ALTERNATIVES = ("UPTURN_ACROSS_THRESHOLD", "CONTINUATION_TERMINATED", "JAMB_RETURNS")
# drawn evidence of a penetration (block names / texts inside the area); generic CAD vocabulary
PEN_PATTERNS = (
    ("FLOOR_DRAIN", re.compile(r"(?i)(FLOOR\s*DRAIN|(^|[^A-Z])F\.\s?D\.?($|[^A-Z])|(^|[^A-Z])FD($|[^A-Z0-9])|GULLY|"
                               r"FLOOR\s*TRAP|(^|[^A-Z])F\.\s?T\.?($|[^A-Z])|(^|[^A-Z])FT($|[^A-Z0-9])|DRAIN)")),
    ("ROOF_DRAIN", re.compile(r"(?i)(ROOF\s*DRAIN|(^|[^A-Z])R\.\s?D\.?($|[^A-Z])|(^|[^A-Z])RD($|[^A-Z0-9])|RAIN\s*WATER|"
                              r"(^|[^A-Z])R\.?W\.?P($|[^A-Z])|SCUPPER)")),
    ("PIPE_PENETRATION", re.compile(r"(?i)(PIPE\s*SLEEVE|SLEEVE|(^|[^A-Z])S\.?V\.?P($|[^A-Z])|SOIL\s*STACK|"
                                    r"(^|[^A-Z])P\.\s?S\.?($|[^A-Z]))")),
    ("PLUMBING_OUTLET", re.compile(r"(?i)(FLOOR\s*OUTLET|(^|[^A-Z])OUTLET($|[^A-Z])|CLEAN\s*OUT|(^|[^A-Z])C\.\s?O\.?"
                                   r"($|[^A-Z]))")),
)
INDICATIVE_FIXTURES = ("WC", "SHOWER", "BASIN", "KITCHEN_APPLIANCE", "WASHING_MACHINE")


class WaterproofingError(ValueError):
    pass


# ------------------------------------------------------------------------------------------------ values
def target_of(area):
    return {"floor": area["floor"], "room_id": area["room_id"], "codes": list(area.get("codes") or ())}


def system_spec(resolver, target, scope):
    """-> (spec, basis): the membrane spec of an area (roll, laps) and the resolution of every value it uses."""
    res = {k: resolver.get(r, p, target) for k, (r, p) in {
        "roll_width_m": ("UP-WP-001", "roll_width_m"), "roll_length_m": ("UP-WP-001", "roll_length_m"),
        "lap_m": ("UP-WP-002", "lap_m"), "upturn_h_m": ("UP-WP-003", "upturn_h_m"),
        "system": ("UP-WP-MAT-001", "system"), "min_reusable_m": ("UP-WP-LAY-001", "min_reusable_m"),
        "doorway_detail": ("UP-WP-DOOR-001", "doorway_detail"),
        "termination_detail": ("UP-WP-003", "termination_detail"),
        "penetration_treatment": ("UP-WP-004", "penetration_treatment"),
        "corner_treatment": ("UP-WP-004", "corner_treatment")}.items()}
    blocked = [k for k in ("roll_width_m", "roll_length_m", "lap_m", "upturn_h_m") if res[k]["value"] is None]
    sysv = res["system"]["value"]
    system_id = (sysv or {}).get("system_id") or DEFAULT_SYSTEM[scope]
    spec = None
    if not blocked:
        spec = MS.membrane(MS.DEFAULT_MEMBRANE)
        W, L, lap = res["roll_width_m"]["value"], res["roll_length_m"]["value"], res["lap_m"]["value"]
        spec.update(spec_id=system_id, roll_width_m=W, roll_length_m=L, roll_area_m2=W * L, min_side_lap_m=lap,
                    min_end_lap_m=lap, corner_treatment=None, penetration_detail=None,
                    system=(sysv or {}).get("name") or f"{system_id} (membrane system not specified)",
                    lap_source={"side": f"{res['lap_m']['state']}: {res['lap_m']['source']}",
                                "end": f"{res['lap_m']['state']}: {res['lap_m']['source']}"},
                    authority=f"UP-WP-001 / UP-WP-002 ({K.rule_set()})")
        MS.validate(spec)
    basis = {k: {kk: v.get(kk) for kk in ("value", "state", "urban_value", "source", "project_rule_ids", "conflict",
                                         "note")} for k, v in res.items()}
    return spec, basis, {"system_id": system_id, "specified": sysv is not None,
                         "group": (system_id, res["roll_width_m"]["value"], res["roll_length_m"]["value"],
                                   res["lap_m"]["value"]), "blocked": blocked}


# ------------------------------------------------------------------------------------------------ penetrations
def _inside(x, y, poly):
    inside = False
    n = len(poly)
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            inside = not inside
    return inside


def penetrations(room, ents, unit_m):
    """drains / outlets / sleeves drawn inside the area: block names and texts matching the penetration vocabulary
    (one count per symbol; a text next to a block of the same kind counts once). Sanitary fixtures are listed as
    indicative only (a fixture symbol does not establish an outlet through the membrane)."""
    poly, holes = room.get("polygon") or (), room.get("hole_polygons") or ()

    def inside(x, y):
        return bool(poly) and _inside(x, y, poly) and not any(_inside(x, y, h) for h in holes)
    found = []
    for i in ents.get("inserts") or ():
        b = i.get("box")
        x, y = ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2) if b else (i.get("x"), i.get("y"))
        if x is None or not inside(x, y):
            continue
        for kind, rx in PEN_PATTERNS:
            if rx.search(str(i.get("name") or "")):
                found.append({"kind": kind, "evidence": "BLOCK", "ref": i.get("id"), "name": i.get("name"),
                              "at_m": [round(x * unit_m, 4), round(y * unit_m, 4)]})
                break
    near = 0.3 / unit_m
    for t in ents.get("texts") or ():
        x, y = t.get("x"), t.get("y")
        if x is None or not inside(x, y):
            continue
        for kind, rx in PEN_PATTERNS:
            if rx.search(str(t.get("value") or "")):
                if any(f["kind"] == kind and f["evidence"] == "BLOCK" and
                       math.dist((f["at_m"][0] / unit_m, f["at_m"][1] / unit_m), (x, y)) <= near for f in found):
                    break                                   # the label of a counted symbol
                found.append({"kind": kind, "evidence": "TEXT", "ref": t.get("id"), "name": t.get("value"),
                              "at_m": [round(x * unit_m, 4), round(y * unit_m, 4)]})
                break
    found.sort(key=lambda f: (f["kind"], f["at_m"], str(f["ref"])))
    fixtures = sorted(x["fixture"] for x in ((room.get("evidence") or {}).get("fixtures") or ())
                      if x.get("fixture") in INDICATIVE_FIXTURES)
    by = {}
    for f in found:
        by[f["kind"]] = by.get(f["kind"], 0) + 1
    return {"state": "COUNTED_FROM_DRAWING" if found else "NOT_SHOWN", "count": len(found) if found else None,
            "by_kind": dict(sorted(by.items())), "items": found, "indicative_fixtures": fixtures,
            "note": "" if found else "no drain, outlet or sleeve is drawn inside the area: the count is not "
                                     "established (never zero); sanitary fixtures are indicative only"}


# ------------------------------------------------------------------------------------------------ transitions
def transitions(area, basis):
    """every break of the area boundary: doorways (continuation / threshold transition), doorless openings, glazing
    edges, zone lines and open edges (termination). Quantities of each alternative; the detail selects one; without a
    detail the item is UNRESOLVED (its quantity withheld)."""
    h = basis["upturn_h_m"]["value"]
    det, det_state = basis["doorway_detail"]["value"], basis["doorway_detail"]["state"]
    term, term_state = basis["termination_detail"]["value"], basis["termination_detail"]["state"]
    out = []
    for d in area["doorways"]:
        w, t = d["width_m"], d["depth_m"]
        rec = {"kind": "DOORWAY", "opening_id": d["opening_id"], "width_m": round(w, 6),
               "depth_m": None if t is None else round(t, 6), "other_side": d["other_side"],
               "continuation_m2": None if t is None else round(w * t, 6), "continuation_owner": d.get("owner"),
               "rule": "UP-WP-DOOR-001"}
        if d["other_side"] == "WATERPROOFED":
            rec.update(type="DOORWAY_CONTINUATION", state="RESOLVED_BY_GEOMETRY", m2=0.0, termination_lm=0.0,
                       note="both sides are waterproofed: the membrane runs through the doorway (the doorway piece, "
                            "counted once); no vertical transition")
            out.append(rec)
            continue
        alts = {"UPTURN_ACROSS_THRESHOLD": {"m2": None if h is None else round(w * h, 6), "termination_lm": 0.0},
                "CONTINUATION_TERMINATED": {"m2": 0.0, "termination_lm": round(w, 6)},
                "JAMB_RETURNS": {"m2": None if (h is None or t is None) else round(2 * t * h, 6),
                                 "termination_lm": round(w, 6)}}
        rec.update(type="DOOR_THRESHOLD_TRANSITION", alternatives=alts)
        vals = [a["m2"] for a in alts.values() if a["m2"] is not None]
        rec["range_m2"] = {"low": min(vals), "high": max(vals)} if vals else None
        if det is not None and alts[det]["m2"] is not None:
            rec.update(state="RESOLVED_BY_DETAIL", selected=det, m2=alts[det]["m2"],
                       termination_lm=alts[det]["termination_lm"], detail_state=det_state,
                       source=basis["doorway_detail"]["source"])
        else:
            rec.update(state="UNRESOLVED", selected=None, m2=None, termination_lm=None, detail_state=det_state,
                       note=("DOORWAY_WP_TRANSITION_DETAIL_REQUIRED (UP-WP-DOOR-001): door "
                             f"{d['opening_id']} {w:.2f} m to a {d['other_side'].lower().replace('_', ' ')} side - "
                             "upturn across the threshold, continuation with a termination, or jamb returns; the "
                             "quantity is withheld" if det_state != "CONFLICT_REVIEW" else
                             basis["doorway_detail"].get("note") or "PROJECT_RULE_CONFLICT"))
        out.append(rec)
    for b in area["breaks"]:
        if b["role"] in ("DOOR",):
            continue
        cont = b["role"] in ("PASSAGE", "ZONE_LINE") and b.get("other_side") == "WATERPROOFED"
        rec = {"kind": b["role"], "opening_id": b.get("id"), "length_m": round(b["length_m"], 6), "rule": "UP-WP-003",
               "other_side": b.get("other_side")}
        if cont:
            rec.update(type="DOORWAY_CONTINUATION", state="RESOLVED_BY_GEOMETRY", termination_lm=0.0,
                       note="the membrane continues into the adjacent waterproofed area")
        elif term is not None:
            rec.update(type="TERMINATION", state="RESOLVED_BY_DETAIL", selected=term,
                       termination_lm=round(b["length_m"], 6), detail_state=term_state,
                       source=basis["termination_detail"]["source"])
        else:
            rec.update(type="TERMINATION", state="UNRESOLVED", termination_lm=None, detail_state=term_state,
                       note=f"WP_TERMINATION_DETAIL_REQUIRED (UP-WP-003): {b['role'].lower().replace('_', ' ')} "
                            f"{b['length_m']:.2f} m - the membrane edge needs its termination detail; withheld")
        out.append(rec)
    return out


# ------------------------------------------------------------------------------------------------ areas
def make_area(room, feats, *, scope, net_m2, continuation_pieces=(), doorways=(), beyond=None, ents=None,
              unit_m=1.0, provisional_geometry=False, wp_floor_line_id=None, agg_eligible_lm=None, agg_glazing_lm=0.0):
    """one waterproofed area: its boundary (wp_geometry.boundary) checked against the plan's own boundary roles
    (agg_eligible_lm: wall + column + sill-wall run of the room; agg_glazing_lm: its glazing-edge run), its doorways
    with what lies beyond them (WATERPROOFED / DRY / EXTERIOR / NOT_ESTABLISHED), its other breaks and its drawn
    penetrations. The segmentation agrees when it lies between the boundary roles' upturn and that plus their glazing
    edge: a window frame / sash line on the face of a recognised window is its sill threshold, not floor glazing.
    room: {room_id, floor, name_en, codes, polygon_m, hole_polygons_m, polygon, hole_polygons (drawing units)}."""
    from engine.source import wp_geometry as WG
    bd = WG.boundary(room, feats)
    found_doors = {b["id"] for b in bd["breaks"] if b["role"] == "DOOR"}
    missing = [d["opening_id"] for d in doorways if d["opening_id"] not in found_doors]
    why = []
    if agg_eligible_lm is not None:
        seg, ge = bd["eligible_lm"], agg_glazing_lm or 0.0
        if not (agg_eligible_lm - TOL_M <= seg <= agg_eligible_lm + ge + TOL_M):
            why.append(f"the plan's boundary roles give {agg_eligible_lm:.3f} m of upturned boundary (+ {ge:.3f} m "
                       f"glazing edge), the ring segmentation {seg:.3f} m")
        elif seg - agg_eligible_lm > TOL_M:
            bd = dict(bd, window_frame_lm=round(seg - agg_eligible_lm, 6),
                      window_frame_note="window frame / sash lines on the face of recognised windows counted as the "
                                        f"sill threshold ({seg - agg_eligible_lm:.3f} m the boundary roles called "
                                        "glazing edge)")
    if missing:
        why.append("door(s) " + ", ".join(missing) + " not found on the ring")
    doorways = [dict(d) for d in doorways]
    known = {d["opening_id"] for d in doorways}
    breaks = []
    for b in bd["breaks"]:
        if b["role"] == "DOOR":
            if b["id"] not in known:                     # a door closure the opening census did not list
                doorways.append({"opening_id": b["id"], "width_m": b["length_m"], "depth_m": None,
                                 "other_side": "NOT_ESTABLISHED"})
                known.add(b["id"])
            continue
        breaks.append(dict(b, other_side=(beyond or {}).get(b["id"], "NOT_ESTABLISHED")))
    if why:
        elig = agg_eligible_lm if agg_eligible_lm is not None else bd["eligible_lm"]
        bd = dict(bd, approximate=True, approximate_why="; ".join(why), eligible_lm=round(elig, 6),
                  runs=[{"length_m": round(elig, 6), "closed": not breaks and not doorways}], corners_unreliable=True)
    return {"room_id": room["room_id"], "floor": room["floor"], "name_en": room.get("name_en"),
            "name_ar": room.get("name_ar"), "codes": list(room.get("codes") or ()), "scope": scope,
            "location_types": sorted(_location_types(room.get("codes"))), "net_m2": round(net_m2, 6),
            "provisional_geometry": provisional_geometry, "wp_floor_line_id": wp_floor_line_id,
            "polygon_m": [tuple(p) for p in room["polygon_m"]],
            "hole_polygons_m": [[tuple(p) for p in h] for h in room.get("hole_polygons_m") or ()],
            "boundary": bd, "continuation_pieces": [dict(p) for p in continuation_pieces],
            "doorways": sorted(doorways, key=lambda d: str(d["opening_id"])), "breaks": breaks,
            "penetrations": penetrations(room, ents or {}, unit_m)}


def areas_from_floor(S, M, ents, roles, unit_m, *, wp_room_ids):
    """the waterproofed areas of one measured floor: every space with a FIN.WP.FLOOR quantity line (wet rooms of the
    owner scope, balconies and roofs). wp_room_ids: every waterproofed room of the run (what lies beyond a doorway)."""
    from engine.source import wp_geometry as WG
    by_room = {}
    for ln in M["lines"]:
        by_room.setdefault(ln["location"]["room_id"], []).append(ln)
    rooms = {r["room_id"]: r for r in M["rooms"]}
    op_rooms = {o["opening_id"]: o["rooms"] for o in M["openings"]}
    ops = S["openings_by_id"]

    def side(rid, oid):
        other = [x for x in op_rooms.get(oid, ()) if x != rid]
        return "WATERPROOFED" if any(x in wp_room_ids for x in other) else ("DRY" if other else "EXTERIOR")
    out = []
    for rid, ls in sorted(by_room.items()):
        fl = next((x for x in ls if x["item_code"] == "FIN.WP.FLOOR" and x.get("measured_net") is not None), None)
        if fl is None or rid not in rooms:
            continue
        room = rooms[rid]
        scope = EXTERIOR if room.get("kind") == "EXTERIOR" else WET
        pieces = [{"opening_id": x["physical_element"].split()[-1], "width_m": x["calculation"]["inputs"]["width_m"],
                   "depth_m": x["calculation"]["inputs"]["depth_m"]} for x in ls
                  if x["item_code"] == "FIN.WP.DOORWAY" and x.get("measured_net") is not None and
                  x["calculation"]["inputs"].get("depth_m")]
        doorways = [{"opening_id": oid, "width_m": ops[oid]["width_m"], "depth_m": ops[oid]["wall_t_m"],
                     "other_side": side(rid, oid)} for oid in room.get("doors") or () if oid in ops]
        beyond = {oid: side(rid, oid) for oid in (room.get("passages") or ())}
        r = room.get("runs_lm") or {}
        agg = r.get("wall", 0.0) + r.get("column", 0.0) + r.get("window_threshold", 0.0) if r else None
        out.append(make_area(room, WG.features(S, ents, roles, unit_m, room), scope=scope, net_m2=fl["measured_net"],
                             continuation_pieces=pieces, doorways=doorways, beyond=beyond, ents=ents, unit_m=unit_m,
                             provisional_geometry=fl["evidence_state"] == "PROVISIONAL",
                             wp_floor_line_id=fl["line_id"], agg_eligible_lm=agg,
                             agg_glazing_lm=r.get("glazing_edge", 0.0) if r else 0.0))
    return out


def _location_types(codes):
    from engine.source import project_rules as PR
    return PR.location_types(codes)


def wp_line(ctx, *, item_code, room, element, unit, net, formula, inputs, ref, ev=None, rfi=None, notes="",
            bounded=None):
    """a canonical BOQ line citing a knowledge-registry rule (the rule-store ids UP-WP-00x mean other rules: CF-13)."""
    from engine.source import boq_line as BL
    if ev is None:
        ev = "SOURCE_DERIVED" if net is not None else ("BOUNDED_EXPOSURE" if bounded else "BLOCKED_RFI")
    return BL.make_line(project_id=ctx["project_id"], revision_set_sha256=ctx["revision_set_sha256"],
                        item_code=item_code, unit=unit, evidence_state=ev,
                        measured_net=net if ev in BL.QUANTITY_STATES else None,
                        element_id=f"{room['room_id']}:{element}", floor=room["floor"], room_id=room["room_id"],
                        room_name_en=room["name_en"], room_name_ar=room["name_ar"], physical_element=element,
                        formula=formula, inputs=inputs, documents=ctx["documents"], geometry_source="CAD_VECTOR",
                        geometry_confidence="EXACT_FACE" if ev in BL.QUANTITY_STATES else "NOT_ESTABLISHED",
                        rule_id=ref["rule_id"], rule_version=ref["version"], rule_set=ref["rule_set"],
                        rule_set_digest=ref["rule_set_digest"], rfi=rfi, notes=notes, bounded_range=bounded)


# ------------------------------------------------------------------------------------------------ layout
def _seams(res):
    s = (res.get("layout") or {}).get("seams") or {}
    return sum((s.get(k) or {}).get("count") or 0 for k in ("longitudinal", "transverse_floor", "upturn_end_laps"))


def room_layout(area, spec, c):
    """the membrane layout of one area through membrane_layout's polygon strips (every orientation the frame gives),
    the band runs and the upturn row of this module, the selection rule of UP-WP-LAY-001: fewest rolls, fewest seams,
    least consumed membrane, direction order."""
    geo = {"room_id": area["room_id"], "floor": area["floor"], "name_en": area.get("name_en"),
           "line_id": area.get("wp_floor_line_id"), "polygon": area["polygon_m"], "holes": area["hole_polygons_m"],
           "perimeter_lm": area["boundary"]["total_lm"]}
    loc = {k: geo.get(k) for k in ("room_id", "floor", "name_en") if geo.get(k) is not None}
    if spec is None:
        return ML.WP.blocked(method=METHOD, spec=None, reason="WP_LAYOUT_BLOCKED: a membrane value is in conflict or "
                             "missing (" + ", ".join(c["blocked"]) + ")", location=loc, line_id=geo["line_id"])
    h = c["upturn_h_m"]
    pieces = [{"door_id": p["opening_id"], "width_m": p["width_m"], "depth_m": p["depth_m"]}
              for p in area["continuation_pieces"]]
    try:
        sf = ML.surfaces_polygon(geo, upturn_h=h, doorways=pieces, doorway_detail="SEPARATE_RETURN")
    except ML.MembraneError as ex:
        return ML.WP.blocked(method=METHOD, spec=spec, reason=f"WP_LAYOUT_BLOCKED: {ex}", location=loc,
                             line_id=geo["line_id"])
    if sf is None:
        return ML.WP.blocked(method=METHOD, spec=spec, reason="WP_LAYOUT_BLOCKED: no area polygon", location=loc,
                             line_id=geo["line_id"])
    band_runs = [dict(r) for r in c["runs"]]
    band_lm = sum(r["length_m"] for r in band_runs)
    sf["rows"][0]["net_m2"] = area["net_m2"]
    sf["rows"][0]["formula"] = "the waterproofed floor (the FIN.WP.FLOOR line)"
    sf["rows"][-1] = {"item_code": "FIN.WP.WALL_UPTURN", "net_m2": band_lm * h,
                      "formula": "eligible upturn runs (+ resolved doorway transitions) x upturn height",
                      "inputs": {"upturn_lm": band_lm, "upturn_h_m": h, "runs": band_runs}}
    sf["runs"] = {"runs": band_runs or [{"length_m": 0.0, "closed": True}], "approximate": c["runs_approximate"]}
    sf["flags"] = []
    sf["_band"] = h + spec["min_side_lap_m"]
    if not band_runs:
        sf["runs"] = {"runs": [], "approximate": False}
    cc = {"upturn_h_m": h, "doorways": pieces, "doorway_detail": "SEPARATE_RETURN",
          "min_reusable_m": c.get("min_reusable_m"), "penetrations": 0, "rule_refs": c.get("rule_refs", ())}
    try:
        fl = ML._poly_floor(sf, spec)
        opts = [ML._one(sf, spec, cc, d, loc, geo, floor_fn=fl, method=METHOD) for d in ("ALONG_X", "ALONG_Y")]
    except ML.MembraneError as ex:
        return ML.WP.blocked(method=METHOD, spec=spec, reason=f"WP_LAYOUT_BLOCKED: {ex}", location=loc,
                             line_id=geo["line_id"])
    key = lambda r: (r["units"]["consumed_units"], _seams(r), round(r["consumed_m2"], 6),            # noqa: E731
                     ("ALONG_X", "ALONG_Y").index(r["layout"]["direction"]))
    sel = copy.deepcopy(min(opts, key=key))
    sel["layout"]["alternatives"] = [{"direction": r["layout"]["direction"], "rolls": r["units"]["consumed_units"],
                                      "seams": _seams(r), "consumed_m2": r["consumed_m2"],
                                      "overlap_m2": r["overlap_m2"], "cutting_waste_m2": r["cutting_waste_m2"],
                                      "packaging_surplus_m2": r["packaging"]["packaging_surplus_m2"]} for r in opts]
    sel["layout"]["selection_rule"] = ["fewest rolls (the area installed on its own)", "fewest seams",
                                       "least consumed membrane", "direction order (ALONG_X before ALONG_Y)"]
    # this module's corners, penetrations and withheld detailing replace membrane_layout's generic counts
    sel["concerns"] = [x for x in sel["concerns"] if not x.startswith(("CORNER_TREATMENT_NOT_SPECIFIED",
                                                                       "PENETRATION_DETAIL_NOT_SPECIFIED"))]
    sel["layout"]["details"] = c["details"]
    sel["concerns"] = sorted(set(sel["concerns"]) | set(c["concerns"]))
    sel["state"] = "COMPUTED_REVIEW" if sel["concerns"] else "COMPUTED"
    return sel


# ------------------------------------------------------------------------------------------------ areas
def _treatment_qty(tr, count):
    if tr is None or count is None:
        return None
    if tr["kind"] == "PATCH":
        a, b = tr["size_m"]
        return {"pcs": count, "m2": round(count * a * b, 6)}
    return {"pcs": count, "m2": None, "name": tr.get("name")}


def build_area(area, resolver):
    """resolve the area's values, its transitions, corners and penetrations, its layout and its schedule row."""
    t = target_of(area)
    spec, basis, sysinfo = system_spec(resolver, t, area["scope"])
    tr = transitions(area, basis)
    h = basis["upturn_h_m"]["value"]
    concerns, withheld = [], []
    # band runs: the eligible runs, with the doorway segments of a resolved UPTURN_ACROSS_THRESHOLD detail joined to
    # them and the jamb returns of JAMB_RETURNS added as short runs
    runs = [dict(r) for r in area["boundary"]["runs"]]
    approx = area["boundary"].get("approximate", False)
    for x in tr:
        if x.get("selected") == "UPTURN_ACROSS_THRESHOLD":
            runs.append({"length_m": x["width_m"], "closed": False})
        elif x.get("selected") == "JAMB_RETURNS" and x.get("depth_m"):
            runs += [{"length_m": x["depth_m"], "closed": False}] * 2
    unresolved_tr = [x for x in tr if x["state"] == "UNRESOLVED"]
    for x in unresolved_tr:
        withheld.append({"what": f"{x['type']} {x.get('opening_id') or x['kind']}", "range_m2": x.get("range_m2"),
                         "termination_lm_max": x.get("width_m") or x.get("length_m"), "why": x["note"]})
    cor = area["boundary"]["corners"]
    n_cor = None if area["boundary"].get("corners_unreliable") else cor["internal"] + cor["external"]
    ct = basis["corner_treatment"]["value"]
    corner_q = _treatment_qty(ct, n_cor)
    if n_cor and corner_q is None:
        withheld.append({"what": f"corner treatment ({n_cor} corners)", "why": "WP_CORNER_DETAIL_REQUIRED"})
        concerns.append(f"WP_CORNER_DETAIL_REQUIRED (UP-WP-004): {cor['internal']} internal + {cor['external']} "
                        "external corner(s) counted; corner treatment withheld")
    pen = area["penetrations"]
    pt = basis["penetration_treatment"]["value"]
    pen_q = _treatment_qty(pt, pen["count"])
    if pen["state"] == "NOT_SHOWN":
        withheld.append({"what": "penetrations", "why": "WP_PENETRATIONS_NOT_SHOWN"})
        concerns.append("WP_PENETRATIONS_NOT_SHOWN (UP-WP-004): no drain / outlet / sleeve drawn; count not "
                        "established, treatment withheld")
    elif pen_q is None or pen_q.get("m2") is None:
        withheld.append({"what": f"penetration treatment ({pen['count']})", "why": "WP_PENETRATION_DETAIL_REQUIRED"})
        if pen_q is None:
            concerns.append(f"WP_PENETRATION_DETAIL_REQUIRED (UP-WP-004): {pen['count']} drawn penetration(s); "
                            "treatment withheld")
    if not sysinfo["specified"]:
        concerns.append(f"WP_SYSTEM_NOT_SPECIFIED (UP-WP-MAT-001): {sysinfo['system_id']}")
    if approx:
        concerns.append("WP_BOUNDARY_SEGMENTATION_REVIEW: the band runs are approximated")
    concerns.append("INSTALLATION_DIRECTION_NOT_VALIDATED: lap shingling against the falls is not checked (no drain / "
                    "fall plan)")
    details = {"corners": {"internal": cor["internal"], "external": cor["external"], "count": n_cor,
                           "state": "BY_DETAIL" if corner_q else ("NOT_ESTABLISHED" if n_cor is None else
                                                                 "WITHHELD" if n_cor else "NONE"),
                           "treatment": ct, "quantity": corner_q},
               "penetrations": {"state": pen["state"], "count": pen["count"], "by_kind": pen["by_kind"],
                                "indicative_fixtures": pen["indicative_fixtures"], "treatment": pt,
                                "quantity": pen_q},
               "upturn_ends": cor["upturn_ends"]}
    c = {"upturn_h_m": h, "runs": runs, "runs_approximate": approx, "details": details, "concerns": concerns,
         "min_reusable_m": basis["min_reusable_m"]["value"], "blocked": sysinfo["blocked"],
         "rule_refs": [K.ref(x) for x in ("UP-WP-001", "UP-WP-002", "UP-WP-003", "UP-WP-004", "UP-WP-LAY-001")]}
    lay = room_layout(area, spec, c)
    area = dict(area, basis=basis, system=sysinfo, transitions=tr, withheld=withheld, layout=lay, details=details)
    area["row"] = area_schedule(area)
    return area


def area_schedule(area):
    """the schedule row of one area (UP-WP-MAT-001)."""
    lay, b, tr = area["layout"], area["basis"], area["transitions"]
    h = b["upturn_h_m"]["value"]
    elig = area["boundary"]["eligible_lm"]
    upturn_m2 = None if h is None else round(elig * h, 6)
    comp = {x["component"]: x for x in lay.get("components") or ()}
    computed = lay["state"] != "BLOCKED"
    doorway_tr_m2 = sum(x["m2"] for x in tr if x.get("kind") == "DOORWAY" and x.get("m2") is not None and
                        x["state"] == "RESOLVED_BY_DETAIL")
    term_known = sum(x.get("termination_lm") or 0.0 for x in tr if x["state"] == "RESOLVED_BY_DETAIL")
    state = "PROVISIONAL"
    if computed and area["system"]["specified"] and not area["withheld"] and area["scope"] == WET and \
            not area.get("provisional_geometry"):
        state = "CONFIRMED_BASIS"
    return {"room_id": area["room_id"], "floor": area["floor"], "name_en": area.get("name_en"), "scope": area["scope"],
            "location_types": sorted(area.get("location_types") or ()), "system_id": area["system"]["system_id"],
            "system_specified": area["system"]["specified"],
            "A_net_horizontal_m2": area["net_m2"],
            "upturn": {"eligible_lm": elig, "by_role_lm": area["boundary"]["by_role_lm"], "height_m": h,
                       "height_state": b["upturn_h_m"]["state"], "height_urban_m": b["upturn_h_m"]["urban_value"],
                       "area_m2": upturn_m2},
            "doorway_continuation_m2": round(sum(p["width_m"] * p["depth_m"] for p in area["continuation_pieces"]), 6),
            "doorway_transitions": {"count": sum(1 for x in tr if x["kind"] == "DOORWAY" and
                                                 x["type"] == "DOOR_THRESHOLD_TRANSITION"),
                                    "resolved_m2": round(doorway_tr_m2, 6),
                                    "unresolved": sum(1 for x in tr if x["kind"] == "DOORWAY" and
                                                      x["state"] == "UNRESOLVED"),
                                    "range_m2": _range([x.get("range_m2") for x in tr if x["kind"] == "DOORWAY" and
                                                        x["state"] == "UNRESOLVED"])},
            "terminations": {"resolved_lm": round(term_known, 6),
                             "unresolved_lm": round(sum(x.get("length_m") or x.get("width_m") or 0.0 for x in tr
                                                        if x["state"] == "UNRESOLVED" and x["type"] == "TERMINATION")
                                                    + sum(x["width_m"] for x in tr if x["state"] == "UNRESOLVED" and
                                                          x["kind"] == "DOORWAY"), 6)},
            "penetrations": area["details"]["penetrations"], "corners": area["details"]["corners"],
            "laps_m2": lay.get("overlap_m2"),
            "B_installed_m2": None if not computed else round(lay["placed_m2"] + lay["overlap_m2"], 6),
            "consumed_m2": lay.get("consumed_m2"), "cutting_waste_m2": lay.get("cutting_waste_m2"),
            "reusable_offcuts_m2": lay.get("reusable_offcuts_m2"),
            "rolls_if_installed_alone": (lay.get("units") or {}).get("consumed_units"),
            "gross_roll_area_if_alone_m2": None if not computed else lay["packaging"]["pack_total_m2"],
            "untouched_roll_tails_if_alone_m2": None if not computed else lay["packaging"]["packaging_surplus_m2"],
            "direction": (lay.get("layout") or {}).get("direction"),
            "withheld": area["withheld"], "state": state, "layout_state": lay["state"],
            "blocked_by": lay.get("blocked_by"),
            "rules": ["UP-WP-001", "UP-WP-002", "UP-WP-003", "UP-WP-004", "UP-WP-MAT-001", "UP-WP-LAY-001",
                      "UP-WP-DOOR-001", "UP-RULES-001"],
            "basis": {k: {"value": v["value"], "state": v["state"], "project_rule_ids": v["project_rule_ids"]}
                      for k, v in b.items()}}


def _range(rs):
    rs = [r for r in rs if r]
    if not rs:
        return None
    return {"low": round(sum(r["low"] for r in rs), 6), "high": round(sum(r["high"] for r in rs), 6)}


# ------------------------------------------------------------------------------------------------ procurement
def cutting_plan(areas):
    """per membrane system (system id + roll + lap): every computed area's full-width pieces cut from shared rolls,
    first fit decreasing (deterministic). A roll remainder is reused only where the plan cuts a piece from it."""
    groups = {}
    for a in areas:
        lay = a["layout"]
        if lay["state"] == "BLOCKED":
            continue
        groups.setdefault(a["system"]["group"], []).append(a)
    out = []
    for g, members in sorted(groups.items(), key=lambda x: _gkey(x[0])):
        sid, W, L, lap = g
        pieces = []
        for a in sorted(members, key=lambda a: a["room_id"]):
            for r in a["layout"]["layout"]["rolls"]:
                for k, s in enumerate(r["segments"]):
                    pieces.append((s["length_m"], a["room_id"], r["roll"], k, s["for"]))
        pieces.sort(key=lambda p: (-p[0], p[1], p[2], p[3]))
        rolls = []
        for ln, rid, rr, k, why in pieces:
            for roll in rolls:
                if L - roll["cut_m"] >= ln - 1e-6:
                    roll["pieces"].append({"room_id": rid, "length_m": round(ln, 4), "for": why})
                    roll["cut_m"] = round(roll["cut_m"] + ln, 6)
                    break
            else:
                rolls.append({"roll": len(rolls) + 1, "pieces": [{"room_id": rid, "length_m": round(ln, 4),
                                                                   "for": why}], "cut_m": round(ln, 6)})
        for roll in rolls:
            roll["untouched_tail_m"] = round(L - roll["cut_m"], 6)
            roll["areas"] = sorted({p["room_id"] for p in roll["pieces"]})
        consumed = sum(p[0] for p in pieces) * W
        alone = sum(a["layout"]["units"]["consumed_units"] for a in members)
        rows = [a["row"] for a in members]
        withheld = [w for a in members for w in a["withheld"]]
        specified = all(a["system"]["specified"] for a in members)
        reasons = ([] if specified else ["WP_SYSTEM_NOT_SPECIFIED: the roll is the owner standard (UP-WP-001), the "
                                         "membrane system is not named"]) + \
            ([f"{len(withheld)} withheld detailing item(s) (doorway transitions, penetrations, corners, terminations)"]
             if withheld else []) + \
            (["an area of the group is not a wet room (exterior system by specification)"]
             if any(a["scope"] != WET for a in members) else [])
        out.append({"system_id": sid, "roll_width_m": W, "roll_length_m": L, "lap_m": lap,
                    "areas": [a["room_id"] for a in sorted(members, key=lambda a: a["room_id"])],
                    "rolls": len(rolls), "rolls_if_each_area_alone": alone,
                    "gross_roll_area_m2": round(len(rolls) * W * L, 6), "consumed_m2": round(consumed, 6),
                    "untouched_roll_tails_m2": round(len(rolls) * W * L - consumed, 6),
                    "installed_m2": round(sum(r["B_installed_m2"] for r in rows), 6),
                    "net_m2": round(sum(r["A_net_horizontal_m2"] for r in rows), 6),
                    "cutting_waste_m2": round(sum(r["cutting_waste_m2"] for r in rows), 6),
                    "reusable_offcuts_m2": round(sum(r["reusable_offcuts_m2"] for r in rows), 6),
                    "roll_count_state": "CONFIRMED" if not reasons else "PROVISIONAL", "why_not_confirmed": reasons,
                    "withheld_detailing": withheld, "cutting_plan": rolls,
                    "balance": "gross = consumed (pieces) + untouched tails; consumed = installed + cutting waste + "
                               "retained offcuts (per area)",
                    "never": "combined with another membrane system"})
        bal = round(len(rolls) * W * L, 6) - round(consumed + (len(rolls) * W * L - consumed), 6)
        if abs(bal) > 1e-6 or abs(sum(r["cut_m"] for r in rolls) * W - consumed) > 1e-4:
            raise WaterproofingError(f"cutting plan of {sid} does not balance")
    return out


def _gkey(g):
    return (str(g[0]), float(g[1] or 0), float(g[2] or 0), float(g[3] or 0))


def schedule(areas, plans):
    """the waterproofing material schedule: per area, per floor and per system (never across systems), project."""
    rows = [a["row"] for a in sorted(areas, key=lambda a: (a["floor"], a["room_id"]))]
    floors = {}
    for r in rows:
        f = floors.setdefault((r["floor"], r["system_id"]), {"floor": r["floor"], "system_id": r["system_id"],
                                                              "areas": 0, "A_net_horizontal_m2": 0.0,
                                                              "upturn_m2": 0.0, "B_installed_m2": 0.0,
                                                              "rolls_if_each_area_alone": 0, "withheld": 0})
        f["areas"] += 1
        f["A_net_horizontal_m2"] = round(f["A_net_horizontal_m2"] + r["A_net_horizontal_m2"], 6)
        f["upturn_m2"] = round(f["upturn_m2"] + (r["upturn"]["area_m2"] or 0.0), 6)
        f["B_installed_m2"] = round(f["B_installed_m2"] + (r["B_installed_m2"] or 0.0), 6)
        f["rolls_if_each_area_alone"] += r["rolls_if_installed_alone"] or 0
        f["withheld"] += len(r["withheld"])
    return {"policy": POLICY_ID, "rule_set": K.rule_set(), "rule_set_digest": K.digest(), "areas": rows,
            "floors": [floors[k] for k in sorted(floors)], "systems": plans,
            "project": {"areas": len(rows), "systems": len(plans),
                        "A_net_horizontal_m2_by_system": {p["system_id"]: p["net_m2"] for p in plans},
                        "B_installed_m2_by_system": {p["system_id"]: p["installed_m2"] for p in plans},
                        "C_procurement_rolls_by_system": {p["system_id"]: p["rolls"] for p in plans},
                        "roll_count_state_by_system": {p["system_id"]: p["roll_count_state"] for p in plans},
                        "never": "a total across membrane systems"},
            "quantities": {"A": "net waterproofing area (horizontal; the FIN.WP.FLOOR lines)",
                           "B": "installed membrane (laid: coverage + upturns + doorway pieces + laps; from the layout)",
                           "C": "procurement rolls of the cutting plan, per system"}}


# ------------------------------------------------------------------------------------------------ BOQ lines
def boq_lines(ctx, areas, line):
    """the V2.4 waterproofing lines of every area: the wall upturn, the doorway transitions, the terminations and the
    penetration treatments (line(ctx, item_code=..., room=..., ...) builds a canonical line with a registry ref)."""
    lines, unresolved = [], []
    for a in sorted(areas, key=lambda a: (a["floor"], a["room_id"])):
        room = {"room_id": a["room_id"], "floor": a["floor"], "name_en": a.get("name_en") or a["room_id"],
                "name_ar": a.get("name_ar") or "-"}
        b = a["basis"]
        h, hs = b["upturn_h_m"]["value"], b["upturn_h_m"]["state"]
        ev = None if a["scope"] == WET and not a.get("provisional_geometry") else "PROVISIONAL"
        elig = a["boundary"]["eligible_lm"]
        inputs = {"eligible_lm": elig, "by_role_lm": a["boundary"]["by_role_lm"], "upturn_h_m": h,
                  "upturn_h_state": hs, "upturn_h_urban_m": b["upturn_h_m"]["urban_value"],
                  "project_rule_ids": b["upturn_h_m"]["project_rule_ids"], "runs": a["boundary"]["runs"]}
        if h is None:
            q = b["upturn_h_m"].get("note") or "PROJECT_RULE_CONFLICT (UP-RULES-001): the upturn height"
            lines.append(line(ctx, item_code="FIN.WP.WALL_UPTURN", room=room, element="wp_wall_upturn", unit="m2",
                              net=None, formula="eligible wall boundary x upturn height", inputs=inputs,
                              ref=K.ref("UP-WP-003"), rfi={"question": q, "unlocks": a["room_id"]}))
            unresolved.append({"room_id": a["room_id"], "floor": a["floor"], "item": "FIN.WP.WALL_UPTURN", "reason": q})
        else:
            lines.append(line(ctx, item_code="FIN.WP.WALL_UPTURN", room=room, element="wp_wall_upturn", unit="m2",
                              net=round(elig * h, 6), ev=ev,
                              formula=f"eligible wall boundary (walls, columns, sill walls) x {h:g} m; doorways, "
                                      "doorless openings and open edges are not wall upturn (UP-WP-DOOR-001)",
                              inputs=inputs, ref=K.ref("UP-WP-003"),
                              notes=f"upturn height {hs}" + (" (Urban standard UP-WP-003)" if hs ==
                                                            "OWNER_STANDARD_ASSUMED" else
                                                            f" ({b['upturn_h_m']['source']})")))
        for x in a["transitions"]:
            if x["kind"] == "DOORWAY":
                if x["type"] == "DOORWAY_CONTINUATION":
                    continue
                el = f"doorway transition {x['opening_id']}"
                inp = {"opening_id": x["opening_id"], "width_m": x["width_m"], "depth_m": x["depth_m"],
                       "upturn_h_m": h, "alternatives": x["alternatives"], "selected": x.get("selected"),
                       "detail_state": x.get("detail_state")}
                if x["state"] == "RESOLVED_BY_DETAIL":
                    lines.append(line(ctx, item_code="FIN.WP.DOORWAY_TRANSITION", room=room, element=el, unit="m2",
                                      net=x["m2"], ev=ev, formula=f"{x['selected']} (project detail)", inputs=inp,
                                      ref=K.ref("UP-WP-DOOR-001"), notes=f"detail: {x.get('source')}"))
                else:
                    rng = x.get("range_m2")
                    lines.append(line(ctx, item_code="FIN.WP.DOORWAY_TRANSITION", room=room, element=el, unit="m2",
                                      net=None, formula="by the project waterproofing detail (alternatives listed)",
                                      inputs=inp, ref=K.ref("UP-WP-DOOR-001"),
                                      bounded=dict(rng, basis=x["note"]) if rng else None,
                                      rfi={"question": x["note"], "unlocks": a["room_id"]}))
                    unresolved.append({"room_id": a["room_id"], "floor": a["floor"],
                                       "item": "FIN.WP.DOORWAY_TRANSITION", "reason": x["note"]})
                continue
            if x["type"] != "TERMINATION":
                continue
            el = f"termination {x['kind'].lower()} {x.get('opening_id') or ''}".strip()
            inp = {"kind": x["kind"], "opening_id": x.get("opening_id"), "length_m": x["length_m"],
                   "detail_state": x.get("detail_state")}
            if x["state"] == "RESOLVED_BY_DETAIL":
                lines.append(line(ctx, item_code="FIN.WP.TERMINATION", room=room, element=el, unit="lm",
                                  net=x["termination_lm"], ev=ev, formula=f"edge length ({x['selected']})",
                                  inputs=inp, ref=K.ref("UP-WP-003"), notes=f"detail: {x.get('source')}"))
            else:
                lines.append(line(ctx, item_code="FIN.WP.TERMINATION", room=room, element=el, unit="lm", net=None,
                                  formula="edge length, by the termination detail", inputs=inp,
                                  ref=K.ref("UP-WP-003"), bounded={"low": 0.0, "high": x["length_m"],
                                                                   "basis": x["note"]},
                                  rfi={"question": x["note"], "unlocks": a["room_id"]}))
                unresolved.append({"room_id": a["room_id"], "floor": a["floor"], "item": "FIN.WP.TERMINATION",
                                   "reason": x["note"]})
        pen = a["details"]["penetrations"]
        if pen["state"] == "COUNTED_FROM_DRAWING":
            lines.append(line(ctx, item_code="FIN.WP.PENETRATION", room=room, element="wp_penetrations", unit="pcs",
                              net=pen["count"], ev=ev, formula="drains / outlets / sleeves drawn inside the area",
                              inputs={"by_kind": pen["by_kind"], "treatment": pen["treatment"],
                                      "treatment_quantity": pen["quantity"]}, ref=K.ref("UP-WP-004"),
                              notes="treatment " + ("by detail" if pen["quantity"] else
                                                    "WITHHELD: WP_PENETRATION_DETAIL_REQUIRED (UP-WP-004)")))
            if not pen["quantity"]:
                unresolved.append({"room_id": a["room_id"], "floor": a["floor"], "item": "FIN.WP.PENETRATION",
                                   "reason": f"WP_PENETRATION_DETAIL_REQUIRED (UP-WP-004): {pen['count']} drawn "
                                             "penetration(s); the membrane treatment is withheld"})
        else:
            q = ("WP_PENETRATIONS_NOT_SHOWN (UP-WP-004): no drain / outlet / sleeve is drawn in the area; the count is "
                 "not established (never zero)" + (f"; indicative fixtures {', '.join(pen['indicative_fixtures'])}"
                                                   if pen["indicative_fixtures"] else ""))
            lines.append(line(ctx, item_code="FIN.WP.PENETRATION", room=room, element="wp_penetrations", unit="pcs",
                              net=None, formula="drains / outlets / sleeves drawn inside the area",
                              inputs={"indicative_fixtures": pen["indicative_fixtures"]}, ref=K.ref("UP-WP-004"),
                              rfi={"question": q, "unlocks": a["room_id"]}))
            unresolved.append({"room_id": a["room_id"], "floor": a["floor"], "item": "FIN.WP.PENETRATION", "reason": q})
        cor = a["details"]["corners"]
        if cor["state"] == "WITHHELD":
            unresolved.append({"room_id": a["room_id"], "floor": a["floor"], "item": "FIN.WP (material)",
                               "reason": f"WP_CORNER_DETAIL_REQUIRED (UP-WP-004): {cor['internal']} internal + "
                                         f"{cor['external']} external corner(s); corner treatment withheld"})
        if a["layout"]["state"] == "BLOCKED":
            unresolved.append({"room_id": a["room_id"], "floor": a["floor"], "item": "FIN.WP (material)",
                               "reason": a["layout"]["blocked_by"]})
        if a["boundary"].get("approximate"):
            unresolved.append({"room_id": a["room_id"], "floor": a["floor"], "item": "FIN.WP (material)",
                               "reason": "WP_BOUNDARY_SEGMENTATION_REVIEW: " + a["boundary"]["approximate_why"]})
    return lines, unresolved


def policy_record():
    return {"policy": POLICY_ID, "method": METHOD, "rule_set": K.rule_set(), "rule_set_digest": K.digest(),
            "rules": ["UP-WP-001", "UP-WP-002", "UP-WP-003", "UP-WP-004", "UP-WP-MAT-001", "UP-WP-LAY-001",
                      "UP-WP-DOOR-001", "UP-RULES-001"],
            "alternatives": list(ALTERNATIVES), "default_systems": dict(DEFAULT_SYSTEM),
            "penetration_vocabulary": [k for k, _ in PEN_PATTERNS], "indicative_fixtures": list(INDICATIVE_FIXTURES)}
