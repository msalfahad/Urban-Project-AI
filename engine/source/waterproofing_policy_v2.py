"""WATERPROOFING POLICY V2 (T-458, owner directive 2026-11-02 C3) - the NEW version of waterproofing_policy.py (V1).

V1 (engine/source/waterproofing_policy.py, kept unchanged as history) still carries the superseded wet-room rule of
URBAN_PROJECTS_RULE_LIBRARY 1.4.0 UP-WP-002 1.0.0: upturn 0.15 m and the door widths DEDUCTED from the upturn length.
The owner rule is UP-WP-002 2.0.0 (rule store 1.5.0, owner Q-03): upturn 0.20 m; the membrane runs through the doorway
(UP-WP-003, owner Q-35 C): the upturn line is the one-sided boundary INCLUDING the door crossings (no door deduction)
and each doorway is its own transition line (door width x wall thickness), wet area by wet area.

wet()          floor m2 (UP-WP-001) + gross boundary x the rule-store upturn (UP-WP-002 latest approved) + one doorway
               line per door (UP-WP-003). A missing input makes ITS item HELD (never 0); doors never reduce the upturn.
roof()         unchanged from V1 (URBAN-ROOF-WATERPROOF-UPTURN-200@v1: 0.20 m at every roof-region edge).
procurement()  unchanged from V1 (a lap factor only when a system with a stated lap is named).

POLICY_ID is distinct from engine/source/waterproofing.py (R8.18), which also calls itself WATERPROOFING_POLICY_V1:
the two V1 modules share one id with opposite doorway rules (V1 here deducts doors, R8.18 does not). SUPERSEDED lists
every engine site found by T-458 that still states the legacy rule, each with the run-time evidence that no released or
candidate path reaches it (research/agents_t458/T-458_UPTURN_PATHS.md). Units: metres in, m2 / m out; a caller in
another unit converts first (u = metres per drawing unit). Project-agnostic; stdlib + engine.source.rule_store only.
"""

from __future__ import annotations

POLICY_ID = "WATERPROOFING_POLICY_V2_UPTURN_020_NO_DOOR_DEDUCTION"
SUPERSEDES = "WATERPROOFING_POLICY_V1 (engine/source/waterproofing_policy.py)"
DEFAULT_GUARD_CLASS = "UNWIRED_PRODUCER"   # T-212: a quantity producer wired into no released or candidate method yet
ROOF_UPTURN_M = 0.20
MEASURED, HELD = "MEASURED", "HELD"

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
     "id_clash_with": None},
)


def _upturn_rule():
    from engine.source import rule_store as RS
    r = RS.rule("UP-WP-002", RS.LATEST_APPROVED)
    return float(r["value"]), f"UP-WP-002 {r.get('version')} (rule store {RS.LATEST_APPROVED})"


def wet(*, floor_m2, boundary_lm, doors=(), room) -> dict:
    """One wet area. floor_m2: the wet floor face; boundary_lm: the one-sided boundary INCLUDING every door crossing
    (never perimeter - doors); doors: [{"id", "width_m", "wall_t_m"}] (None when not established)."""
    up, authority = _upturn_rule()
    items = []
    if floor_m2 is None:
        items.append({"item": "FIN.WP.FLOOR", "state": HELD, "m2": None, "rule": "UP-WP-001",
                      "reason": "WET_FLOOR_NOT_ESTABLISHED"})
    else:
        items.append({"item": "FIN.WP.FLOOR", "state": MEASURED, "m2": round(floor_m2, 6), "rule": "UP-WP-001",
                      "formula": "wet floor face"})
    if boundary_lm is None:
        items.append({"item": "FIN.WP.UPTURN", "state": HELD, "m2": None, "rule": "UP-WP-002",
                      "reason": "UPTURN_RUN_NOT_ESTABLISHED", "upturn_m": up})
    else:
        items.append({"item": "FIN.WP.UPTURN", "state": MEASURED, "m2": round(boundary_lm * up, 6),
                      "rule": "UP-WP-002", "upturn_m": up, "upturn_authority": authority,
                      "boundary_lm": round(boundary_lm, 6), "door_crossings_deducted": False,
                      "formula": f"one-sided boundary incl. door crossings {boundary_lm:.3f} m x {up:g} m"})
    for d in doors:
        if d.get("width_m") is None or d.get("wall_t_m") is None:
            items.append({"item": "FIN.WP.DOORWAY", "state": HELD, "m2": None, "rule": "UP-WP-003",
                          "opening": d.get("id"), "reason": "DOORWAY_DEPTH_OR_WIDTH_NOT_ESTABLISHED"})
        else:
            items.append({"item": "FIN.WP.DOORWAY", "state": MEASURED, "m2": round(d["width_m"] * d["wall_t_m"], 6),
                          "rule": "UP-WP-003", "opening": d.get("id"), "formula": "door width x wall thickness"})
    held = [i["item"] for i in items if i["state"] == HELD]
    return {"room": room, "policy": POLICY_ID, "state": HELD if held else MEASURED, "held_items": held,
            "items": items, "laps": "NOT_INCLUDED (procurement factor)"}


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
