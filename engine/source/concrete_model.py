"""PHYSICAL NON-OVERLAPPING CONCRETE MODEL (V1) + STAIR CONCRETE (V1).

physical_model()  one storey plate: every cubic metre owned by exactly one component
                    SLAB             net plate area (voids / stair / lift openings removed) x t, continuous over beams
                                     and columns
                    DOWNSTAND_BEAM   CLEAR_FACE_TO_FACE length x B x (D - t)
                    BEAM_COLUMN_JOINT column plan area x (D_ctrl - t)   (node under the slab, above the column soffit)
                    COLUMN           plan area x (interval - D_ctrl)
                  a component without a computed value is listed BLOCKED with its reason and never enters the total;
                  the total is labelled COMPLETE only when nothing is blocked.
gross_beam_view() reporting view: length x B x full D per beam (never added to the physical total).
stair()           waist (sloping length x width x waist) + wedges (0.5 x riser x going x width x n) + landings
                  (area x thickness); stair beams are separate items. Any missing input -> BLOCKED_INPUT_MISSING with
                  the list; a steps x tread x riser volume is never used.

Project-agnostic; stdlib only. Metres / cm as named.
"""

from __future__ import annotations

import hashlib
import json
import math

POLICY_ID = "PHYSICAL_CONCRETE_MODEL_V1"
STAIR_POLICY_ID = "STAIR_CONCRETE_V1"


def downstand(*, length_m, B_cm, D_cm, t_cm) -> float:
    if D_cm < t_cm:
        raise ValueError("beam shallower than the slab it carries")
    return length_m * B_cm / 100.0 * (D_cm - t_cm) / 100.0


def physical_model(*, slab=None, beams=(), joints=(), columns=()) -> dict:
    """slab {"net_area_m2", "t_cm"} or {"blocked": reason, "t_cm"?} (a printed thickness keeps the downstands
    measurable while the plate outline is blocked); beams [{"id", "length_m"|None, "B_cm", "D_cm", "blocked"?}];
    joints [{"id", "volume_m3"|None}]; columns [{"id", "volume_m3"|None, "blocked"?}]."""
    comp, blocked = [], []
    if slab and slab.get("net_area_m2") is not None and slab.get("t_cm"):
        comp.append({"component": "SLAB", "id": "SLAB", "volume_m3": round(slab["net_area_m2"] * slab["t_cm"] / 100.0, 6),
                     "formula": "net plate area x t"})
        t = slab["t_cm"]
    else:
        blocked.append({"component": "SLAB", "id": "SLAB", "reason": (slab or {}).get("blocked", "SLAB_NOT_ESTABLISHED")})
        t = (slab or {}).get("t_cm")
    for b in beams:
        if b.get("blocked") or b.get("length_m") is None or t is None:
            blocked.append({"component": "DOWNSTAND_BEAM", "id": b["id"],
                            "reason": b.get("blocked") or ("SLAB_THICKNESS_UNKNOWN" if t is None else "LENGTH_NOT_MEASURED")})
            continue
        comp.append({"component": "DOWNSTAND_BEAM", "id": b["id"],
                     "volume_m3": round(downstand(length_m=b["length_m"], B_cm=b["B_cm"], D_cm=b["D_cm"], t_cm=t), 6),
                     "formula": "clear length x B x (D - t)"})
    for j in joints:
        (comp if j.get("volume_m3") is not None else blocked).append(
            {"component": "BEAM_COLUMN_JOINT", "id": j["id"], "volume_m3": j.get("volume_m3")} if j.get("volume_m3") is not None
            else {"component": "BEAM_COLUMN_JOINT", "id": j["id"], "reason": j.get("blocked", "JOINT_NOT_COMPUTED")})
    for c in columns:
        (comp if c.get("volume_m3") is not None and not c.get("blocked") else blocked).append(
            {"component": "COLUMN", "id": c["id"], "volume_m3": c.get("volume_m3")} if c.get("volume_m3") is not None
            and not c.get("blocked") else {"component": "COLUMN", "id": c["id"], "reason": c.get("blocked", "HEIGHT_NOT_PROVED")})
    by = {}
    for c in comp:
        by[c["component"]] = round(by.get(c["component"], 0.0) + c["volume_m3"], 6)
    return {"components": comp, "blocked": blocked, "by_component_m3": by,
            "computed_total_m3": round(sum(c["volume_m3"] for c in comp), 6),
            "total_state": "COMPLETE" if not blocked else "PARTIAL (blocked components excluded, listed)",
            "invariant": "each cubic metre in exactly one component: slab owns the plate depth everywhere; beams own "
                         "only the part below the slab between support faces; joints own the node under the slab; "
                         "columns stop at the controlling soffit"}


def gross_beam_view(beams) -> list:
    return [{"id": b["id"], "volume_m3": round(b["length_m"] * b["B_cm"] / 100.0 * b["D_cm"] / 100.0, 6),
             "basis": "length x B x full D (REPORTING VIEW - never added to the physical total)"}
            for b in beams if b.get("length_m") is not None and not b.get("blocked")]


# ------------------------------------------------------------------ stairs
def stair(*, flights=(), landings=(), name="STAIR") -> dict:
    """flights [{"risers", "riser_m", "going_m", "width_m", "waist_m"}]; landings [{"area_m2", "thickness_m"}]."""
    need = ("risers", "riser_m", "going_m", "width_m", "waist_m")
    missing = sorted({k for f in flights for k in need if f.get(k) in (None, 0)} |
                     {k for l in landings for k in ("area_m2", "thickness_m") if l.get(k) in (None, 0)})
    if not flights:
        missing = sorted(set(missing) | {"flights"})
    if missing:
        return {"name": name, "state": "BLOCKED_INPUT_MISSING", "missing": missing, "volume_m3": None,
                "never": "steps x tread x riser"}
    parts = []
    for i, f in enumerate(flights):
        n = f["risers"]
        horiz = n * f["going_m"]
        rise = n * f["riser_m"]
        slope = math.hypot(horiz, rise)
        waist = slope * f["width_m"] * f["waist_m"]
        wedges = 0.5 * f["riser_m"] * f["going_m"] * f["width_m"] * n
        parts.append({"flight": i + 1, "waist_m3": round(waist, 6), "wedges_m3": round(wedges, 6),
                      "sloping_length_m": round(slope, 6)})
    land = [{"landing": i + 1, "volume_m3": round(l["area_m2"] * l["thickness_m"], 6)} for i, l in enumerate(landings)]
    tot = sum(p["waist_m3"] + p["wedges_m3"] for p in parts) + sum(l["volume_m3"] for l in land)
    return {"name": name, "state": "COMPUTED", "flights": parts, "landings": land, "volume_m3": round(tot, 6),
            "stair_beams": "separate items (beam schedule)"}


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID, "stair_policy_id": STAIR_POLICY_ID,
           "components": ["SLAB", "DOWNSTAND_BEAM", "BEAM_COLUMN_JOINT", "COLUMN"],
           "reporting_views": ["GROSS_BEAM"],
           "stair": "waist + wedges + landings; beams separate; blocked when any input is missing"}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec
