"""OWNER FINISH SCOPE (M9 Phase 2B-1, ARCH_TAKEOFF_V2.3 only) - the owner wet-area scope and the surfaces V2.2 left as
questions although an approved rule answers them (knowledge registry: UP-WET-001, UP-FIN-WALL-001, UP-FIN-PAINT-001,
UP-FIN-PLASTER-001, UP-SKIRT-001, UP-THR-001, UP-WP-ROOF-001).

    finish_scope(room)                         -> {"scope": WET | DRY | NONE | REVIEW, "rule", "basis", "flags"
                                                  (open items, raised as unresolved), "notes" (information)}
    wall_tile_height(hs)                       -> the governing wall-tile height of a wet room (full height = the
                                                  clear-height ladder; an explicit source height governs, flagged
                                                  when lower)
    threshold_lines(ctx, strips, rooms, floor) -> doorway strips of door / passage openings: marble threshold at wet
                                                  doorways, floor porcelain (once) elsewhere; everything else returned
                                                  untouched for the V2 strip register
    jamb_plaster_lines(ctx, openings, floor, door_heights)  -> PROVISIONAL door jamb / head plaster
    passage_jamb_skirting(ctx, openings, rooms, floor)      -> PROVISIONAL skirting on doorless-opening jambs
    exterior_wp_lines(ctx, room, ...)          -> PROVISIONAL waterproofing of balconies / roofs drawn as spaces

Nothing here changes a drawn dimension; every line names the registry rule it applies and its state. Lines built
on an assumption (an owner fallback height, a frame detail not drawn) are PROVISIONAL, never confirmed.
Project-agnostic; stdlib only."""

from __future__ import annotations

from engine.source import arch_rooms as AR
from engine.source import knowledge as K

POLICY_ID = "OWNER_FINISH_SCOPE_V1"
WET, DRY, NONE, REVIEW = "WET", "DRY", "NONE", "REVIEW"
NO_FINISH_KINDS = (AR.STAIR, AR.SHAFT, AR.VOID, AR.EXTERIOR)
Q_STRIP_PROVISIONAL_DOOR = ("THRESHOLD_OF_PROVISIONAL_DOOR (UP-THR-001 sets the finish: marble at a wet doorway, floor "
                            "porcelain otherwise): the strip lies at a door symbol that closes a wall gap with no band "
                            "opening; the door's sides and width are not established - measured strip shown")
Q_STRIP_NOT_TAKEN = ("THRESHOLD_STRIP_NOT_ATTRIBUTED (UP-THR-001 sets the finish): the strip is bounded by several "
                     "openings, or a face of its opening does not fit the opening; which doorway owns it is not "
                     "established - measured strip shown")
Q_STRIP_WET_REVIEW = ("THRESHOLD_OF_SPACE_UNDER_WET_REVIEW (UP-THR-001, UP-WET-002): the doorway of a space whose wet / "
                      "dry type is under review - marble threshold if it is wet, floor porcelain if it is dry; the "
                      "finish follows the review - measured strip shown")
WET_REVIEW_ISSUES = ("WET_CLASSIFICATION_REVIEW", "WC_CANDIDATE_REVIEW")


def finish_scope(room):
    """the owner finish scope of one measured space (UP-WET-001). A closed room whose functions are all wet areas is
    WET; a face joining a wet function with a dry one is REVIEW (the wet zone's extent is not drawn: the dry treatment
    stays, flagged); stairs, shafts, voids and exterior spaces carry no room finish (NONE)."""
    codes = list(room.get("codes") or ())
    kind = room.get("kind")
    wet = set(K.wet_codes())
    if room.get("class") not in ("ROOM", "MIXED") or not codes or kind is None:
        return {"scope": NONE if kind in NO_FINISH_KINDS else REVIEW if codes else NONE, "rule": "UP-WET-001",
                "basis": "not measured as a room", "flags": []}
    if kind in NO_FINISH_KINDS:
        return {"scope": NONE, "rule": "UP-WET-001", "basis": f"{kind} space: no room finish", "flags": []}
    w = [c for c in codes if c in wet]
    if w and len(w) == len(codes):
        flags = [f"WET_SCOPE_PROJECT_CONFIRMATION: {c} is a wet area where the project scope establishes it"
                 for c in w if c in K.confirm_codes()]
        notes = ["PANTRY_ZONE: an open (American) pantry is a functional zone (UP-PANTRY-001)"] \
            if room.get("zone") and "PANTRY" in w else []
        return {"scope": WET, "rule": "UP-WET-001", "basis": "owner wet area (" + "+".join(codes) + ")",
                "flags": flags, "notes": notes}
    if w:
        return {"scope": REVIEW, "rule": "UP-WET-001", "basis": "open plan of a wet function (" + "+".join(w) +
                ") and a dry one: the wet zone's extent is not drawn",
                "flags": ["OPEN_PLAN_WET_SCOPE_EXTENT: the wet area of this open plan is not bounded by a drawn "
                          "line or wall; the dry treatment is kept and the wet scope is not applied"]}
    return {"scope": DRY, "rule": "UP-SKIRT-001", "basis": "dry room", "flags": []}


def wall_tile_height(hs):
    """the wall-tile height of a wet room (UP-FIN-WALL-001) from the arch_measure height ladders hs: an explicit
    WALL_TILE source / project height governs (precedence 1 / 4 over the general rule, 5); otherwise full height =
    the clear-height ladder (the paint ladder, to the finished ceiling). -> a wall_height-shaped dict + "full"."""
    tile, clear = hs["WALL_TILE"], hs["PAINT"]
    explicit = [c for c in tile.get("candidates") or () if c.get("kind") in ("SOURCE_FINISH_HEIGHT",
                                                                              "OWNER_PROJECT_FACT")
                and c.get("state") == "ESTABLISHED"]
    if explicit:
        full = None
        if clear.get("state") == "ESTABLISHED":
            full = explicit[0]["value_m"] >= clear["value_m"] - 1e-6
        flag = ("WALL_TILE_BELOW_OWNER_FULL_HEIGHT: the explicit wall-tile height "
                f"{explicit[0]['value_m']:.2f} m is below the clear height {clear['value_m']:.2f} m (UP-FIN-WALL-001 "
                "asks for full height; the explicit source governs)") if full is False else None
        return dict(tile, full=full, flag=flag, rule="UP-FIN-WALL-001")
    if clear.get("state") == "ESTABLISHED":
        return dict(clear, governing="OWNER_FULL_HEIGHT (UP-FIN-WALL-001): " + str(clear.get("governing")),
                    authority=f"UP-FIN-WALL-001 full height = clear height ({clear.get('authority')})", full=True,
                    flag=None, rule="UP-FIN-WALL-001")
    return dict(clear, full=True, flag=None, rule="UP-FIN-WALL-001",
                why="full height by UP-FIN-WALL-001; the clear height itself is not established")


def _strip_room(floor, key, what):
    return {"room_id": f"{floor}-STRIP-{key}", "floor": floor, "name_en": what, "name_ar": AR.UNNAMED[1]}


def _rooms_of_opening(rooms, oid):
    return [r for r in rooms if oid in (r.get("doors") or []) + (r.get("passages") or [])]


def threshold_lines(ctx, strips, rooms, floor, *, line, wet_review=False):
    """-> (lines, unresolved, remaining_strips). The doorway strip faces of ONE door / passage opening (one line per
    opening, as the V2 strip register groups them), every face geometry-verified: next to a WET room (UP-WET-001) at a door -> FIN.MARBLE.THRESHOLD (clear opening width x the strip
    depth; the strip is in no room floor, so the adjacent porcelain is deducted by construction); any other doorway ->
    FIN.FLOOR.PORCELAIN for the strip, counted once (UP-THR-001). A pantry doorway is PROVISIONAL (conflict CF-03);
    an external doorway and a doorless opening into a wet area are PROVISIONAL. Every other strip is returned to the
    V2 strip register unchanged. wet_review (ARCH_TAKEOFF_V2.7 only): a doorway with no wet side and a side whose type
    is under wet-classification review (UP-WET-002) is not given a dry finish - its strips go back to the register
    with the review question; False is the V2.3 .. V2.6 path, unchanged."""
    lines, unresolved, rest = [], [], []
    groups = {}                                     # the strip faces of one opening make one line (as the V2 register)
    for s in strips:
        if s["class"] != "THRESHOLD" or len(s["opening_ids"]) != 1:
            rest.append(s)
            continue
        groups.setdefault(s["opening_ids"][0], []).append(s)
    for oid, ss in sorted(groups.items()):
        if not all(s["geometry_verified"] for s in ss):
            rest.extend(ss)
            continue
        s = ss[0]
        kind = s["opening_kinds"][0] if s["opening_kinds"] else None
        side = _rooms_of_opening(rooms, oid)
        scopes = [(r, finish_scope(r)) for r in side]
        wet_sides = [r for r, sc in scopes if sc["scope"] == WET]
        if wet_review and not wet_sides and any(str(r.get("issue") or "").startswith(WET_REVIEW_ISSUES) for r in side):
            rest.extend(dict(x, question=Q_STRIP_WET_REVIEW) for x in ss)
            continue
        g = s["geometry"]
        width, depth = g.get("opening_width_m"), g.get("depth_m")
        room = _strip_room(floor, oid, f"doorway {oid}")
        notes, ev = [], None
        codes = sorted({c for r in side for c in r.get("codes") or ()})
        names = " | ".join(r["name_en"] for r in side) or "-"
        if kind == "DOOR" and wet_sides:
            code, element, rule = "FIN.MARBLE.THRESHOLD", "marble threshold", "UP-THR-001"
            formula = "clear door opening width x the doorway strip depth (measured strip face)"
            if any("PANTRY" in (r.get("codes") or ()) for r in wet_sides):
                ev = "PROVISIONAL"
                notes.append("PANTRY_THRESHOLD_RULE_CONFLICT (CF-03, OQ-01): the master prompt makes the pantry a wet "
                             "area; the Urban marble-threshold rule lists it as not applicable")
                unresolved.append({"room_id": room["room_id"], "floor": floor, "item": code,
                                   "reason": "PANTRY_THRESHOLD_RULE_CONFLICT (OQ-01): marble threshold or floor "
                                             f"porcelain at the pantry doorway {oid}"})
            if len(side) < 2:
                ev = "PROVISIONAL"
                notes.append("one side of the doorway is outside the plan's rooms")
            notes.append("the wet and dry floor finishes end at the marble; the strip is in neither room floor")
        else:
            code, element, rule = "FIN.FLOOR.PORCELAIN", "doorway strip", "UP-THR-001"
            formula = "the doorway strip face (floor finish continues through the doorway, counted once)"
            if kind == "PASSAGE" and wet_sides:
                ev = "PROVISIONAL"
                notes.append("a doorless opening into a wet area: the marble-threshold rule applies to doorways; the "
                             "strip is taken as floor porcelain")
            if len(side) < 2:
                ev = "PROVISIONAL"
                notes.append("an external doorway: the strip is taken as the interior floor porcelain (UP-THR-001 "
                             "'other doorways'); an exterior sill is by specification")
        inputs = {"opening_id": oid, "opening_kind": kind, "length_m": width, "depth_m": depth,
                  "strips": [x["strip_id"] for x in ss], "sides": names, "side_codes": codes, "geometry_verified": True}
        split = [x["split_from"] for x in ss if x.get("split_from")]
        if split:                                   # ARCH_TAKEOFF_V2.6 (D-V26-07): the clip of a longer face
            inputs["split_from"] = split[0]
            notes.append(f"STRIP_SPLIT_AT_OPENING_BOX (D-V26-07): the doorway face ({split[0]['face_m2']:.4f} m2) "
                         f"runs on past the jambs between wall lines; this opening's box is taken, "
                         f"{split[0]['remainder_m2']:.4f} m2 beyond the jambs is wall (WALL_BAND_REMAINDER)")
        lines.append(line(ctx, item_code=code, room=room, element=element, unit="m2",
                          net=round(sum(x["area_m2"] for x in ss), 6), ev=ev, formula=formula,
                          inputs=inputs, rule_id=rule, notes="; ".join(notes)))
    # the strips left to the V2 register keep their measurement and lose the finish question UP-THR-001 answers:
    # what is still open is which doorway owns the strip (E) or the door itself (B: no band opening)
    rest = [s if s.get("question") == Q_STRIP_WET_REVIEW else
            dict(s, question=Q_STRIP_PROVISIONAL_DOOR if s["door_closures"] and not s["opening_ids"] else
                 Q_STRIP_NOT_TAKEN) if s["class"] == "THRESHOLD" else s for s in rest]
    return lines, unresolved, rest


def jamb_plaster_lines(ctx, openings, floor, door_height, *, line):
    """door jamb and head plaster (UP-FIN-PLASTER-001): 2 x wall thickness x door height + wall thickness x opening
    width, per door opening; always PROVISIONAL (the frame detail decides how much is plastered); the height comes
    from door_height(opening) -> {"value_m", "state"} (a source, or the owner fallback: HEIGHT_ASSUMED)."""
    lines = []
    for o in openings:
        if o["kind"] != "DOOR":
            continue
        h = door_height(o)
        room = {"room_id": f"{floor}-OPENING-{o['opening_id']}", "floor": floor,
                "name_en": f"door opening {o['opening_id']}", "name_ar": AR.UNNAMED[1]}
        if h is None or h.get("value_m") is None:
            lines.append(line(ctx, item_code="FIN.PLASTER", room=room, element="door jambs and head", unit="m2",
                              net=None, formula="2 x wall thickness x door height + wall thickness x opening width",
                              inputs={"width_m": o["width_m"], "wall_t_m": o["wall_t_m"]}, rule_id="UP-FIN-PLASTER-001",
                              rfi={"question": "door height not established for the jamb plaster", "unlocks":
                                   room["room_id"]}))
            continue
        t, w, H = o["wall_t_m"], o["width_m"], h["value_m"]
        net = round(2 * t * H + t * w, 6)
        lines.append(line(ctx, item_code="FIN.PLASTER", room=room, element="door jambs and head", unit="m2", net=net,
                          ev="PROVISIONAL", formula="2 x wall thickness x door height + wall thickness x opening width",
                          inputs={"width_m": w, "wall_t_m": t, "height_m": H, "height_state": h["state"],
                                  "height_source": h.get("source")}, rule_id="UP-FIN-PLASTER-001",
                          notes="; ".join(x for x in (
                              "FRAME_ALIGNMENT_PLASTER: confirm with the frame detail how much of the jambs and head "
                              "is plastered", "HEIGHT_ASSUMED" if h["state"] == "ASSUMED" else "") if x)))
    return lines


def passage_jamb_skirting(ctx, openings, rooms, floor, *, line):
    """skirting on the two jambs of a doorless opening between two dry rooms (URBAN-SKIRTING-OPENING-METHOD: real
    floor-side jambs of a doorless opening are skirted; UP-SKIRT-001): 2 x wall thickness, PROVISIONAL (the jamb as a
    real vertical surface and the floor finish reaching it are not verified from a plan)."""
    lines = []
    for o in openings:
        if o["kind"] != "PASSAGE":
            continue
        side = _rooms_of_opening(rooms, o["opening_id"])
        if len(side) != 2 or any(finish_scope(r)["scope"] != DRY for r in side):
            continue
        room = {"room_id": f"{floor}-OPENING-{o['opening_id']}", "floor": floor,
                "name_en": f"passage {o['opening_id']}", "name_ar": AR.UNNAMED[1]}
        lines.append(line(ctx, item_code="FIN.SKIRTING", room=room, element="passage jambs", unit="lm",
                          net=round(2 * o["wall_t_m"], 6), ev="PROVISIONAL", formula="2 jambs x wall thickness",
                          inputs={"wall_t_m": o["wall_t_m"], "rooms": [r["room_id"] for r in side]},
                          rule_id="UP-SKIRT-001",
                          notes="PASSAGE_JAMB_SKIRTING: the jambs of a doorless opening between two dry rooms; the "
                                "jamb surfaces and the floor finish reaching them are not verified from a plan"))
    return lines


def exterior_wp_lines(ctx, room, area_m2, perimeter_lm, *, line):
    """balcony / terrace / roof spaces (UP-WP-ROOF-001): PROVISIONAL floor waterproofing over the drawn area; a roof
    also its 0.20 m upturn (URBAN-ROOF-WATERPROOF-UPTURN-200@v1); a balcony upturn is by specification."""
    codes = set(room.get("codes") or ())
    lines = []
    if not codes & {"BALCONY", "ROOF"}:
        return lines
    lines.append(line(ctx, item_code="FIN.WP.FLOOR", room=room, element="exterior wp_floor", unit="m2",
                      net=round(area_m2, 6), ev="PROVISIONAL", formula="drawn exterior space area",
                      inputs={"codes": sorted(codes)}, rule_id="UP-WP-ROOF-001",
                      notes="EXTERIOR_WATERPROOFING: membrane system by specification (one system is never assumed "
                            "for every location)"))
    if "ROOF" in codes:
        lines.append(line(ctx, item_code="FIN.WP.UPTURN", room=room, element="roof wp_upturn", unit="m2",
                          net=round(perimeter_lm * 0.20, 6), ev="PROVISIONAL",
                          formula="roof region perimeter x 0.20 m (URBAN-ROOF-WATERPROOF-UPTURN-200@v1)",
                          inputs={"perimeter_lm": round(perimeter_lm, 6), "upturn_h_m": 0.20}, rule_id="UP-WP-ROOF-001",
                          notes="the upturn follows the roof edges drawn on the plan"))
    else:
        lines.append(line(ctx, item_code="FIN.WP.UPTURN", room=room, element="exterior wp_upturn", unit="m2", net=None,
                          formula="balcony edge x upturn height (by specification)",
                          inputs={"perimeter_lm": round(perimeter_lm, 6)}, rule_id="UP-WP-ROOF-001",
                          rfi={"question": "EXTERIOR_WP_UPTURN_BY_SPECIFICATION: the balcony membrane upturn height "
                                           "is set by the specified system", "unlocks": room["room_id"]}))
    return lines


def policy_record():
    return {"policy": POLICY_ID, "rules": ["UP-WET-001", "UP-FIN-WALL-001", "UP-FIN-PAINT-001", "UP-FIN-PLASTER-001",
                                           "UP-SKIRT-001", "UP-THR-001", "UP-WP-ROOF-001"],
            "rule_set": K.RULE_SET, "rule_set_digest": K.digest(), "wet_codes": list(K.wet_codes())}
