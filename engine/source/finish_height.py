"""ARCHITECTURAL FINISH HEIGHT ENGINE (V1) - blockwork, plaster, paint and wall-tile heights are four separate
quantities with separate inputs. Independent of the structural engine: it READS a structural termination record as
evidence (keeping that record's own status) and never writes a structural value; the structural engine never reads
a ceiling or finish height.

termination()    a wall line -> BEAM_SOFFIT (a bound beam band covers the wall line on the sheet above), SLAB_SOFFIT
                 (inside a closed slab plate with no beam over it) or UNKNOWN.
wall_heights()   per wall face:
                   BLOCKWORK  structural top below -> termination soffit = interval - D (beam) or - t (slab);
                              UNKNOWN termination -> BLOCKED
                   PLASTER    URBAN-PLASTER-TO-MASONRY-TERMINATION@v1: the full masonry face (= blockwork height),
                              above a false ceiling included
                   PAINT      URBAN-PAINT-TO-FINISHED-CEILING@v1: finished floor -> finished ceiling =
                              interval - build-up above - D_ctrl(room) - ceiling allowance; the build-up above is a
                              required input (BLOCKED_FLOOR_BUILDUP when unknown); a printed ceiling level outranks
                   WALL_TILE  wet / service rooms: URBAN-WET-WALL-TILE-FULL-HEIGHT@v1 = the paint height (finished
                              ceiling); a project tile specification outranks; dry rooms: none
                   CONCEALED  dry rooms: plaster above the finished ceiling is not painted (reported)
double_height_region() a region whose plan span is evidenced (e.g. a slab opening above) keeps its span even while
                 its finish heights stay BLOCKED (no single-storey assumption).

Project-agnostic; stdlib only. Metres.
"""

from __future__ import annotations

import hashlib
import json

POLICY_ID = "ARCHITECTURAL_FINISH_HEIGHT_V1"
CEILING_ALLOWANCE_M = 0.150          # URBAN-PAINT-TO-FINISHED-CEILING@v1 (versioned method parameter)
BEAM, SLAB, UNKNOWN = "BEAM_SOFFIT", "SLAB_SOFFIT", "UNKNOWN"


def termination(*, covering_bands=(), inside_plate=False, plate_t_cm=None) -> dict:
    """covering_bands [{"type", "D_cm", "bound": bool, "coverage": 0..1}] bands over the wall line."""
    full = [b for b in covering_bands if b.get("coverage", 0) >= 0.999]
    if full:
        if any(not b["bound"] for b in full):
            return {"type": UNKNOWN, "why": "an unbound band covers the wall line", "D_cm": None}
        top = max(full, key=lambda b: b["D_cm"])
        return {"type": BEAM, "member": top["type"], "D_cm": top["D_cm"]}
    if covering_bands:
        return {"type": UNKNOWN, "why": "a band covers only part of the wall line", "D_cm": None}
    if inside_plate and plate_t_cm:
        return {"type": SLAB, "member": "SLAB", "D_cm": plate_t_cm}
    return {"type": UNKNOWN, "why": "neither a beam nor a closed slab plate is over the wall line", "D_cm": None}


def wall_heights(*, interval, term, room_ctrl_D_cm=None, wet=False, buildup_above_m=None, ceiling_level_m=None,
                 tile_spec_m=None) -> dict:
    """interval: structural vertical interval record {"interval_m", "authority"}; term: termination(); room_ctrl_D_cm
    the deepest soffit over the room (sets the finished ceiling)."""
    out = {"termination": term["type"], "interval_m": interval and interval["interval_m"],
           "interval_authority": interval and interval["authority"]}
    if interval and term["type"] in (BEAM, SLAB):
        h = round(interval["interval_m"] - term["D_cm"] / 100.0, 6)
        out["BLOCKWORK"] = {"height_m": h, "state": "COMPUTED", "basis": f"interval - {term['member']} {term['D_cm']} cm"}
        out["PLASTER"] = {"height_m": h, "state": "COMPUTED", "method": "URBAN-PLASTER-TO-MASONRY-TERMINATION@v1"}
    else:
        why = "TERMINATION_UNKNOWN" if interval else "INTERVAL_UNKNOWN"
        out["BLOCKWORK"] = {"height_m": None, "state": "BLOCKED_" + why}
        out["PLASTER"] = {"height_m": None, "state": "BLOCKED_" + why}
    if ceiling_level_m is not None:
        paint = {"height_m": ceiling_level_m, "state": "COMPUTED", "basis": "printed ceiling level"}
    elif interval is None or room_ctrl_D_cm is None:
        paint = {"height_m": None, "state": "BLOCKED_ROOM_SOFFIT_UNKNOWN"}
    elif buildup_above_m is None:
        paint = {"height_m": None, "state": "BLOCKED_FLOOR_BUILDUP",
                 "formula": "interval - build-up above - D_ctrl - 0.150"}
    else:
        paint = {"height_m": round(interval["interval_m"] - buildup_above_m - room_ctrl_D_cm / 100.0 - CEILING_ALLOWANCE_M, 6),
                 "state": "COMPUTED", "method": "URBAN-PAINT-TO-FINISHED-CEILING@v1"}
    out["PAINT"] = dict(paint, applies=not wet)
    if wet:
        if tile_spec_m is not None:
            out["WALL_TILE"] = {"height_m": tile_spec_m, "state": "COMPUTED", "basis": "project tile specification"}
        else:
            out["WALL_TILE"] = dict(paint, method="URBAN-WET-WALL-TILE-FULL-HEIGHT@v1")
    else:
        out["WALL_TILE"] = {"height_m": 0.0, "state": "NOT_APPLICABLE (dry room)"}
    if not wet and out["PLASTER"]["height_m"] is not None and paint.get("height_m") is not None:
        out["CONCEALED_PLASTER_NOT_PAINTED_M"] = round(out["PLASTER"]["height_m"] - paint["height_m"], 6)
    return out


def double_height_region(*, span_evidence, area_m2=None) -> dict:
    return {"kind": "DOUBLE_HEIGHT_FINISH_REGION", "plan_span": span_evidence, "area_m2": area_m2,
            "span_state": "COMPUTED" if area_m2 is not None else "BLOCKED",
            "paint_height": "BLOCKED (double-height wall faces need the upper ceiling and the void edge condition)",
            "rule": "the plan span is evidence; finish heights are not assumed single-storey"}


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID, "ceiling_allowance_m": CEILING_ALLOWANCE_M,
           "quantities": ["BLOCKWORK", "PLASTER", "PAINT", "WALL_TILE"], "terminations": [BEAM, SLAB, UNKNOWN],
           "never": ["a hard-coded paint height", "a fixed 3.00 m wet tile", "a structural value written from a finish"]}
    rec["digest"] = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
    return rec
