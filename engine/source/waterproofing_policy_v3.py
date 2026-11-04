"""WATERPROOFING POLICY V3 (T-310) - the NEW version of waterproofing_policy_v2.py (T-458, kept unchanged as history).

One change, the Checker finding F-C-T458-2 (Verifier T-458 Gate A, decision FEEDBACK 2026-11-02: fixed in T-310): in V2
an item whose rows are ALL held (no MEASURED row) printed a subtotal 'measured_m2': 0.0, which reads as a quantity of
zero. Held is never 0 (UP-QTY-STATUS-001). V3 prints such an item's subtotal as HELD: 'measured_m2' None, 'state'
HELD, its held row count beside. An item with at least one MEASURED row keeps its measured sum (state MEASURED, or
PARTIAL when held rows sit beside it, so a partial sum is never read as the whole). Every row, every rule and every
figure of V2 is reused as is (wet() delegates to V2.wet); roof() and procurement() are V2's.

POLICY_ID is distinct from V2's and V1's (engine/source/waterproofing_policy.py, engine/source/waterproofing.py).
Project-agnostic; stdlib + engine.source only.
"""

from __future__ import annotations

from engine.source import waterproofing_policy_v2 as WP2

POLICY_ID = "WATERPROOFING_POLICY_V3_UPTURN_020_NO_DOOR_DEDUCTION_HELD_SUBTOTAL"
SUPERSEDES = "WATERPROOFING_POLICY_V2_UPTURN_020_NO_DOOR_DEDUCTION (engine/source/waterproofing_policy_v2.py)"
DEFAULT_GUARD_CLASS = "GUARDED_VIA_V3.0.6"  # T-310 r2: read by V3.0.52 only (guard re-check)
MEASURED, HELD, NOT_BILLED, PARTIAL = WP2.MEASURED, WP2.HELD, WP2.NOT_BILLED, "PARTIAL"
COVERAGE_INSIDE_PIECE, SEPARATE_RETURN, DOORWAY_DETAILS = (WP2.COVERAGE_INSIDE_PIECE, WP2.SEPARATE_RETURN,
                                                           WP2.DOORWAY_DETAILS)
ROOF_UPTURN_M = WP2.ROOF_UPTURN_M
roof = WP2.roof
procurement = WP2.procurement


def subtotals(items) -> dict:
    """Per item: MEASURED rows summed; an item with no MEASURED row is HELD (measured_m2 None, never 0.0); an item with
    MEASURED and HELD rows is PARTIAL (its sum is the measured part only); NOT_BILLED rows are counted, never summed."""
    out = {}
    for it in items:
        t = out.setdefault(it["item"], {"measured_m2": None, "measured_rows": 0, "held_rows": 0, "not_billed_rows": 0})
        if it["state"] == MEASURED:
            if it.get("m2") is None:
                raise ValueError(f"{it['item']} {it['component']}: a MEASURED row without a figure")
            t["measured_m2"] = round((t["measured_m2"] or 0.0) + it["m2"], 6)
            t["measured_rows"] += 1
        elif it["state"] == HELD:
            if it.get("m2") is not None:
                raise ValueError(f"{it['item']} {it['component']}: a HELD row carries a figure (held is blank)")
            t["held_rows"] += 1
        elif it["state"] == NOT_BILLED:
            t["not_billed_rows"] += 1
        else:
            raise ValueError(f"{it['item']}: unknown row state {it['state']!r}")
    for t in out.values():
        t["state"] = (HELD if not t["measured_rows"] and t["held_rows"] else
                      PARTIAL if t["measured_rows"] and t["held_rows"] else
                      MEASURED if t["measured_rows"] else NOT_BILLED)
    return out


def wet(*, floor_m2, boundary_lm, doors=(), room) -> dict:
    """V2.wet() (rows and rules unchanged) with the V3 subtotals: an all-held item prints HELD, never 0.0."""
    r = WP2.wet(floor_m2=floor_m2, boundary_lm=boundary_lm, doors=doors, room=room)
    return dict(r, policy=POLICY_ID, row_policy=WP2.POLICY_ID, totals=subtotals(r["items"]))


def upturn_run(*, boundary_lm, door_widths_m, room) -> dict:
    """The wet-room upturn LINE value per UP-WP-002 2.0.0 / UP-WP-003 1.1.0: the boundary run excluding the doorway
    segments x 0.20 (a window above the upturn is NOT an opening of the run), each doorway segment its own row, HELD
    while the project's doorway detail is not established. -> {"run_m2", "run_lm", "upturn_m", "segments": [...]}"""
    doors = [{"id": f"door-{i + 1}", "width_m": w, "wall_t_m": None, "doorway_detail": None}
             for i, w in enumerate(door_widths_m)]
    r = wet(floor_m2=None, boundary_lm=boundary_lm, doors=doors, room=room)
    run = next(i for i in r["items"] if i["component"] == "BOUNDARY_RUN_EXCL_DOORWAYS")
    if run["state"] != MEASURED:
        return {"state": HELD, "run_m2": None, "reason": run.get("reason"), "policy": POLICY_ID}
    segs = [i for i in r["items"] if i["component"] == "DOORWAY_SEGMENT"]
    return {"state": MEASURED, "run_m2": run["m2"], "run_lm": round(boundary_lm - sum(door_widths_m), 6),
            "upturn_m": run["upturn_m"], "upturn_authority": run.get("upturn_authority"),
            "segments": [{"state": s["state"], "reason": s.get("reason"), "if_billed_m2": s.get("if_billed_m2")}
                         for s in segs], "policy": POLICY_ID}


__all__ = ["POLICY_ID", "SUPERSEDES", "wet", "subtotals", "upturn_run", "roof", "procurement"]
