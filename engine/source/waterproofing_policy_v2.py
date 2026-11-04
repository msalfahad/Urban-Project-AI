"""WATERPROOFING POLICY V2 (T-458, owner directive 2026-11-02 C3) - the NEW version of waterproofing_policy.py (V1).

V1 (engine/source/waterproofing_policy.py, kept unchanged as history) still carries the superseded wet-room rule of
URBAN_PROJECTS_RULE_LIBRARY 1.4.0 UP-WP-002 1.0.0: upturn 0.15 m and the door widths DEDUCTED from the upturn length.
The owner rule is UP-WP-002 2.0.0 (rule store 1.5.0, owner Q-03): upturn 0.20 m; the membrane runs through the doorway
(UP-WP-003, owner Q-35 C): the upturn line is the one-sided boundary INCLUDING the door crossings (no door deduction)
and each doorway is its own transition line (door width x wall thickness), wet area by wet area.

wet()          one wet area, every row its own physical piece, per UP-WP-001 / -002 2.0.0 / -003 1.1.0 (latest
               approved in the rule store): FIN.WP.FLOOR = the room floor face + one DOORWAY_PIECE row per door
               (door width x wall depth, PART OF the floor waterproofing area, UP-WP-003); FIN.WP.UPTURN = the boundary
               run EXCLUDING the doorways x 0.20 + one DOORWAY_SEGMENT row per door (door width x 0.20, UP-WP-002
               reported_separately). Doors never reduce the upturn: the run + the segments = the whole boundary x 0.20.
               Doorway double count (UP-WP-003 1.1.0 "only one is billed" where the detail puts the 0.20 m coverage
               inside the doorway piece): per door a doorway_detail input -
                 COVERAGE_INSIDE_PIECE  the segment lies inside the piece: the piece is billed (in the floor), the
                                        segment row is NOT_BILLED (covered_by the piece row);
                 SEPARATE_RETURN        a return built beside the piece: both billed;
                 None / anything else   the segment row is HELD DOORWAY_CONTINUATION_NOT_ESTABLISHED (never 0, never
                                        both by default); the piece stays billed (it is floor area either way).
               A missing input makes ITS row HELD (never 0). (T-458 r2; r1 billed the segment AND the piece always.)
roof()         unchanged from V1 (URBAN-ROOF-WATERPROOF-UPTURN-200@v1: 0.20 m at every roof-region edge).
procurement()  unchanged from V1 (a lap factor only when a system with a stated lap is named).

POLICY_ID is distinct from engine/source/waterproofing.py (R8.18), which also calls itself WATERPROOFING_POLICY_V1:
the two V1 modules share one id with opposite doorway rules (V1 here deducts doors, R8.18 does not). SUPERSEDED lists
every engine site found by T-458 that still states the legacy rule, each with the run-time evidence that no released or
candidate path reaches it, or (urban_methods) reaches it without reading the value (research/agents_t458/T-458_UPTURN_PATHS.md). Units: metres in, m2 / m out; a caller in
another unit converts first (u = metres per drawing unit). Project-agnostic; stdlib + engine.source.rule_store only.
"""

from __future__ import annotations

POLICY_ID = "WATERPROOFING_POLICY_V2_UPTURN_020_NO_DOOR_DEDUCTION"
SUPERSEDES = "WATERPROOFING_POLICY_V1 (engine/source/waterproofing_policy.py)"
DEFAULT_GUARD_CLASS = "GUARDED_VIA_V3.0.6"  # T-310 r2: wired via V3 into V3.0.55 (guard re-check)
ROOF_UPTURN_M = 0.20
MEASURED, HELD, NOT_BILLED = "MEASURED", "HELD", "NOT_BILLED"
COVERAGE_INSIDE_PIECE, SEPARATE_RETURN = "COVERAGE_INSIDE_PIECE", "SEPARATE_RETURN"
DOORWAY_DETAILS = (COVERAGE_INSIDE_PIECE, SEPARATE_RETURN)

# legacy sites that still state 0.15 m and / or the upturn door deduction: superseded by THIS policy (never reached by
# the released V2.9 + route G or the candidate ARCH_TAKEOFF_V3.0.40 run; T-458 run-time trace)
SUPERSEDED = (
    {"site": "engine/source/waterproofing_policy.py WET_UPTURN_M / wet()", "legacy": "0.15 m; perimeter - door widths",
     "policy_id": "WATERPROOFING_POLICY_V1", "id_clash_with": "engine/source/waterproofing.py"},
    {"site": "engine/source/room_slice.py UPTURN_M", "legacy": "0.15 m; (perimeter - door widths) x 0.15",
     "policy_id": "ROOM_SLICE_V1", "id_clash_with": None},
    {"site": "engine/finishes_rules.py UPTURN_M / upturn()", "legacy": "0.15 m; wall run - openings",
     "policy_id": None, "id_clash_with": None},
    {"site": "engine/source/arch_quantity_truth.py waterproofing(upturn_m=0.15)", "legacy": "0.15 m default "
     "(door crossings not deducted)", "policy_id": None, "id_clash_with": None},
    {"site": "data/trade_rules/URBAN_PROJECTS_RULE_LIBRARY.json UP-WP-002 1.0.0 (read by engine/rule_library.py)",
     "legacy": "0.15 m; 'less the openings that interrupt it'", "policy_id": "URBAN_PROJECTS_RULE_LIBRARY 1.4.0",
     "id_clash_with": None},
    {"site": "engine/source/urban_methods.py URBAN-ROOF-WATERPROOF-UPTURN-200@v1 parameters.wet_upturn_m",
     "legacy": "0.15 m stated for wet rooms (method applies to ROOF_REGION only)", "policy_id": None,
     "id_clash_with": None, "reached_by_candidate": True, "read": False,
     "note": "REACHED BUT UNREAD (F-C-T458-1): the candidate imports urban_methods (arch_v302 -> "
             "footing_rebar_population_v1 -> urban_methods_v3 -> urban_methods), but the only resolve() caller asks the "
             "footing stock-length rule; no code reads wet_upturn_m or resolves the roof method"},
)


def _upturn_rule():
    from engine.source import rule_store as RS
    r = RS.rule("UP-WP-002", RS.LATEST_APPROVED)
    return float(r["value"]), f"UP-WP-002 {r.get('version')} (rule store {RS.LATEST_APPROVED})"


def _row(item, component, state, m2, rule, **kw):
    return {"item": item, "component": component, "state": state, "m2": None if m2 is None else round(m2, 6),
            "rule": rule, **kw}


def wet(*, floor_m2, boundary_lm, doors=(), room) -> dict:
    """One wet area. floor_m2: the room floor face (doorway pieces NOT included; they are added as their own rows);
    boundary_lm: the one-sided boundary INCLUDING every door crossing (never perimeter - doors); doors:
    [{"id", "width_m", "wall_t_m", "doorway_detail"}], a value None when not established; doorway_detail one of
    DOORWAY_DETAILS from the project's threshold / water-stop / return detail, None when the detail is not known."""
    up, authority = _upturn_rule()
    items = []
    if floor_m2 is None:
        items.append(_row("FIN.WP.FLOOR", "ROOM_FACE", HELD, None, "UP-WP-001", reason="WET_FLOOR_NOT_ESTABLISHED"))
    else:
        items.append(_row("FIN.WP.FLOOR", "ROOM_FACE", MEASURED, floor_m2, "UP-WP-001", formula="wet floor face"))
    widths = [d.get("width_m") for d in doors]
    if boundary_lm is None:
        items.append(_row("FIN.WP.UPTURN", "BOUNDARY_RUN_EXCL_DOORWAYS", HELD, None, "UP-WP-002",
                          reason="UPTURN_RUN_NOT_ESTABLISHED", upturn_m=up))
    elif any(w is None for w in widths):
        items.append(_row("FIN.WP.UPTURN", "BOUNDARY_RUN_EXCL_DOORWAYS", HELD, None, "UP-WP-002",
                          reason="DOORWAY_WIDTH_NOT_ESTABLISHED (the run beside the doorways cannot be split off)",
                          upturn_m=up, boundary_lm=round(boundary_lm, 6),
                          whole_boundary_m2=round(boundary_lm * up, 6)))
    else:
        run = boundary_lm - sum(widths)
        if run < -1e-9:
            raise ValueError(f"{room}: door widths {sum(widths):.3f} m exceed the boundary {boundary_lm:.3f} m")
        items.append(_row("FIN.WP.UPTURN", "BOUNDARY_RUN_EXCL_DOORWAYS", MEASURED, run * up, "UP-WP-002",
                          upturn_m=up, upturn_authority=authority, boundary_lm=round(boundary_lm, 6),
                          door_crossings_deducted=False,
                          formula=f"(boundary incl. door crossings {boundary_lm:.3f} - doorway segments "
                                  f"{sum(widths):.3f}) m x {up:g} m; the doorway segments are their own rows"))
    for d in doors:
        w, t, det, oid = d.get("width_m"), d.get("wall_t_m"), d.get("doorway_detail"), d.get("id")
        piece = f"{oid}:DOORWAY_PIECE"
        if w is None or t is None:
            items.append(_row("FIN.WP.FLOOR", "DOORWAY_PIECE", HELD, None, "UP-WP-003", opening=oid, row_id=piece,
                              part_of_floor_area=True, reason="DOORWAY_DEPTH_OR_WIDTH_NOT_ESTABLISHED"))
        else:
            items.append(_row("FIN.WP.FLOOR", "DOORWAY_PIECE", MEASURED, w * t, "UP-WP-003", opening=oid, row_id=piece,
                              part_of_floor_area=True, formula="door width x wall depth (part of the floor area)"))
        seg = dict(opening=oid, row_id=f"{oid}:DOORWAY_SEGMENT", upturn_m=up, doorway_detail=det)
        phys = None if w is None else round(w * up, 6)
        if w is None:
            items.append(_row("FIN.WP.UPTURN", "DOORWAY_SEGMENT", HELD, None, "UP-WP-002/UP-WP-003",
                              reason="DOORWAY_WIDTH_NOT_ESTABLISHED", **seg))
        elif det == COVERAGE_INSIDE_PIECE:
            items.append(_row("FIN.WP.UPTURN", "DOORWAY_SEGMENT", NOT_BILLED, None, "UP-WP-003",
                              physical_m2=phys, covered_by=piece,
                              reason="the project detail puts the 0.20 m coverage inside the doorway piece: only one "
                                     "is billed (UP-WP-003 1.1.0); the piece, which contains it, is billed", **seg))
        elif det == SEPARATE_RETURN:
            items.append(_row("FIN.WP.UPTURN", "DOORWAY_SEGMENT", MEASURED, w * up, "UP-WP-002/UP-WP-003",
                              formula=f"door width {w:.3f} m x {up:g} m (separate return: billed beside the piece)",
                              **seg))
        else:
            why = "DOORWAY_CONTINUATION_NOT_ESTABLISHED" if det is None else \
                f"DOORWAY_CONTINUATION_NOT_ESTABLISHED (unrecognised doorway_detail {det!r})"
            items.append(_row("FIN.WP.UPTURN", "DOORWAY_SEGMENT", HELD, None, "UP-WP-003", reason=why,
                              if_billed_m2=phys, **seg))
    totals = {}
    for it in items:
        t = totals.setdefault(it["item"], {"measured_m2": 0.0, "held_rows": 0, "not_billed_rows": 0})
        if it["state"] == MEASURED:
            t["measured_m2"] = round(t["measured_m2"] + it["m2"], 6)
        elif it["state"] == HELD:
            t["held_rows"] += 1
        else:
            t["not_billed_rows"] += 1
    held = [f'{i["item"]}:{i["component"]}' + (f':{i["opening"]}' if i.get("opening") else "")
            for i in items if i["state"] == HELD]
    return {"room": room, "policy": POLICY_ID, "state": HELD if held else MEASURED, "held_items": held,
            "items": items, "totals": totals, "laps": "NOT_INCLUDED (procurement factor)"}


def roof(*, area_m2, perimeter_m, region) -> dict:
    if area_m2 is None or perimeter_m is None:
        return {"region": region, "state": "BLOCKED_REGION", "physical_m2": None, "policy": POLICY_ID}
    up = perimeter_m * ROOF_UPTURN_M
    return {"region": region, "state": "COMPUTED", "flat_m2": round(area_m2, 6), "upturn_m2": round(up, 6),
            "physical_m2": round(area_m2 + up, 6), "upturn_m": ROOF_UPTURN_M, "policy": POLICY_ID,
            "method": "URBAN-ROOF-WATERPROOF-UPTURN-200@v1", "laps": "NOT_INCLUDED (procurement factor)"}


def procurement(physical_m2, *, system=None, lap_factor=None) -> dict:
    if physical_m2 is None or not system or lap_factor is None:
        return {"state": "NOT_APPLIED", "why": "membrane system / lap / physical quantity not known",
                "procurement_m2": None}
    return {"state": "COMPUTED", "system": system, "lap_factor": lap_factor,
            "procurement_m2": round(physical_m2 * lap_factor, 6)}
