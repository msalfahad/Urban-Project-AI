"""T-260 DOOR_CLASS_WIDTH_EVIDENCE_V1 (research module, NOT wired into any method; standard library only).

Decides, from drawing evidence only, the class and the opening width of a door that a candidate run holds, so the Checker
can rule it and lane I can release or keep it held. Any villa. Rules applied (owner, knowledge 1.8.0):
  UP-DOOR-CLS-001 internal doors PVC; UP-DOOR-CLS-002 doors to genuine outdoor spaces ALUMINIUM (exception: a kitchen /
  pantry door into an ENCLOSED interior corridor stays internal); UP-DOOR-CLS-003 bathroom doors PVC; UP-DOOR-CLS-004 the
  main entrance is its own category, identified by entrance evidence (label, entrance sequence, schedule, elevation),
  never by exterior adjacency or a door symbol alone; UP-DOOR-CLS-005 lift openings excluded; UP-DOOR-AREA-001 area =
  structural opening width x height, as-drawn and owner-required views never mixed; UP-DOOR-HGT-001 / Q-55 C door head
  2.20 m where no sheet prints one (ASSUMED - OWNER-APPROVED); Q-67 A (owner 2026-10-20): a roofed side passage is an
  external open-air space IF the current architectural drawings confirm it is open to outside air without enclosing
  doors or glazing.

Width (ERS s.3, Checker method 2026-10-24 02:44): the structural opening = the gap between the collinear wall-face line
ends, read on BOTH wall faces. Both faces agree (within TOL) -> SETTLED; they differ -> CONFLICT (range, never the larger
end); one face only -> HELD (a one-face reading cannot exclude a rebate or a splayed reveal). A door block's frame extent or
leaf is never the opening (a block can overlap the masonry it is drawn on).

Side status for the class: EXTERIOR needs drawing evidence on that side (exterior-coded space, nothing drawn beyond the
facade to the plot, an outdoor stair / landing reached with nothing drawn across, or a passage whose mouth has no door,
glazing or wall drawn across it on the plan AND on a second sheet (elevation / section)); an owner decision binding the
space is also accepted. A freelancer row is never class evidence. UNKNOWN on one side with nothing EXTERIOR on the other
-> class HELD (never PVC by default, UP-SPACE-001 conflict note).
Missing never becomes 0: a HELD area is None with its cause.
"""
from __future__ import annotations

METHOD = "DOOR_CLASS_WIDTH_EVIDENCE_V1"
ALU, PVC, MAIN, EXCL = "DOOR.EXTERNAL.ALUMINIUM", "DOOR.INTERNAL.PVC", "DOOR.MAIN_ENTRANCE", "EXCLUDED_LIFT"
DC, AS, HELD, CONFLICT = "DRAWING-CONFIRMED", "ASSUMED - OWNER-APPROVED", "HELD", "CONFLICT"
TOL = 0.005                     # m: two face readings of one opening agree within 5 mm
Q55_HEIGHT = 2.20               # Q-55 C / UP-DOOR-HGT-001 owner fallback (only where no sheet prints a head)
EXTERIOR_EVIDENCE = {"EXTERIOR_CODED", "NOTHING_BEYOND_TO_PLOT", "OUTDOOR_STAIR_LANDING", "OPEN_MOUTH", "OWNER_DECISION"}
ENTRANCE_EVIDENCE = {"LABEL", "ENTRANCE_SEQUENCE", "SCHEDULE", "ELEVATION_ENTRANCE"}
NOT_EVIDENCE = {"FREELANCER", "ENGINE_CANDIDATE", "LAYER_NAME", "SWING", "SYMBOL_ONLY"}


class EvidenceRefused(ValueError):
    """A reading that the rules forbid as evidence (freelancer class, block extent as opening, held shown as 0)."""


def opening_width(faces, block_frame_m=None):
    """faces: list of dicts {face, gap_m, handles}. Returns {status, width_m, range_m, cause}."""
    readings = [f for f in faces if f.get("gap_m") is not None]
    if any(f.get("source") in ("BLOCK_FRAME", "ELEVATION_FRAME", "LEAF") for f in readings):
        raise EvidenceRefused("a door block's frame / leaf extent or a fabrication frame is never the opening")
    plan = [f for f in readings if f.get("source", "PLAN") == "PLAN"]
    other = [f for f in readings if f.get("source") == "ELEVATION_OPENING"]   # a second sheet printing the opening
    if len(plan) < 2 or len({f["face"] for f in plan}) < 2:
        return {"status": HELD, "width_m": None, "range_m": None,
                "cause": "opening read on one wall face only: both faces are required (rebate / splay not excluded)"}
    vals = [round(float(f["gap_m"]), 3) for f in plan + other]
    lo, hi = min(vals), max(vals)
    if hi - lo <= TOL:
        w = round(sum(vals) / len(vals), 3)
        note = ""
        if block_frame_m is not None and abs(block_frame_m - w) > TOL:
            note = f"block frame {block_frame_m:.3f} differs: a symbol, not the opening"
        return {"status": DC, "width_m": w, "range_m": None, "cause": note}
    return {"status": CONFLICT, "width_m": None, "range_m": [lo, hi],
            "cause": "the two wall faces give different openings: CONFLICT carried as a range, never its larger end"}


def side_status(side):
    """side: {kind: INTERIOR | EXTERIOR | PASSAGE | LIFT | UNKNOWN, evidence: [...], ...}.
    PASSAGE: {mouths: [{drawn_across_plan: [...], drawn_across_second_sheet: [...] | None}], enclosed_by_door_or_glazing}
    Returns (EXTERIOR | INTERIOR | LIFT | UNKNOWN, reason)."""
    ev = set(side.get("evidence", []))
    if ev & NOT_EVIDENCE and not ev - NOT_EVIDENCE:
        return "UNKNOWN", f"only non-evidence given ({sorted(ev & NOT_EVIDENCE)})"
    kind = side.get("kind", "UNKNOWN")
    if kind == "LIFT":
        return "LIFT", "lift landing (UP-DOOR-CLS-005)"
    if kind == "PASSAGE":
        mouths = side.get("mouths", [])
        open_ = [m for m in mouths if not m.get("drawn_across_plan")]
        if not open_:
            return "INTERIOR", "every mouth is closed by a drawn door, glazing or wall: an enclosed corridor"
        confirmed = [m for m in open_ if m.get("drawn_across_second_sheet") == []]
        if not confirmed:
            return "UNKNOWN", ("mouth open on the plan, not confirmed on a second sheet (elevation / section): "
                               "Q-67 A condition not established")
        return "EXTERIOR", "mouth open to outside air, nothing drawn across on the plan and a second sheet (Q-67 A)"
    if kind == "EXTERIOR":
        if ev & EXTERIOR_EVIDENCE:
            return "EXTERIOR", "exterior by evidence: " + ", ".join(sorted(ev & EXTERIOR_EVIDENCE))
        return "UNKNOWN", "called exterior without drawing evidence"
    if kind == "INTERIOR":
        return "INTERIOR", "interior space"
    return "UNKNOWN", "side not established"


def door_class(door):
    """door: {sides: [side, side], entrance_evidence: [...], enters_main_building: bool, bathroom: bool,
    class_sources: [...]}. Returns {status, class, rule, reason}."""
    if "FREELANCER" in set(door.get("class_sources", [])):
        raise EvidenceRefused("a freelancer row is never class evidence")
    st = [side_status(s) for s in door["sides"]]
    kinds = [k for k, _ in st]
    if "LIFT" in kinds:
        return {"status": DC, "class": EXCL, "rule": "UP-DOOR-CLS-005", "reason": st[kinds.index("LIFT")][1]}
    ent = set(door.get("entrance_evidence", [])) & ENTRANCE_EVIDENCE
    if ent and door.get("enters_main_building"):
        return {"status": DC, "class": MAIN, "rule": "UP-DOOR-CLS-004", "reason": "entrance evidence: " +
                ", ".join(sorted(ent))}
    if "EXTERIOR" in kinds:
        return {"status": DC, "class": ALU, "rule": "UP-DOOR-CLS-002",
                "reason": st[kinds.index("EXTERIOR")][1] + ("; no entrance evidence (UP-DOOR-CLS-004 not met)"
                                                             if door.get("main_entrance_candidate") else "")}
    if kinds == ["INTERIOR", "INTERIOR"]:
        return {"status": DC, "class": PVC, "rule": "UP-DOOR-CLS-003" if door.get("bathroom") else "UP-DOOR-CLS-001",
                "reason": "both sides interior"}
    return {"status": HELD, "class": None, "rule": "UP-DOOR-CLS-001/002",
            "reason": "; ".join(r for k, r in st if k == "UNKNOWN") + " (never PVC by default)"}


def door_area(width, height_m=None, height_printed=False):
    """width: result of opening_width. Returns {status, m2, cause}; HELD -> m2 None (never 0)."""
    if width["status"] != DC:
        return {"status": HELD, "m2": None, "range_m2": (
            [round(width["range_m"][0] * (height_m or Q55_HEIGHT), 3), round(width["range_m"][1] *
                                                                          (height_m or Q55_HEIGHT), 3)]
            if width.get("range_m") else None), "cause": width["cause"]}
    h = height_m if height_printed and height_m else Q55_HEIGHT
    st = DC if height_printed and height_m else AS
    return {"status": st, "m2": round(width["width_m"] * h, 3), "range_m2": None,
            "cause": "" if st == DC else "head 2.20 m Q-55 C (no sheet prints a door head)"}


def check_not_zero(rows):
    """Adverse guard: a HELD row shown with 0 m2 is refused."""
    for r in rows:
        if r["status"] in (HELD, CONFLICT) and r.get("m2") == 0:
            raise EvidenceRefused(f"{r['id']}: a held quantity is never 0")
    return True


def ledger(doors):
    """doors: [{id, before: {class_candidates, width_range_m}, faces, block_frame_m, sides, ...}] ->
    rows with class, width, area and SETTLED / STILL-HELD, and the aluminium-line delta."""
    rows = []
    for d in doors:
        w = opening_width(d["faces"], d.get("block_frame_m"))
        c = door_class(d)
        a = door_area(w) if c["status"] == DC else {"status": HELD, "m2": None, "range_m2": None,
                                                    "cause": c["reason"]}
        settled = c["status"] == DC and w["status"] == DC
        rows.append({"id": d["id"], "class": c["class"], "class_status": c["status"], "class_rule": c["rule"],
                     "class_reason": c["reason"], "width_m": w["width_m"], "width_status": w["status"],
                     "width_note": w["cause"], "m2": a["m2"] if settled else None,
                     "status": a["status"] if settled else HELD, "outcome": "SETTLED" if settled else "STILL-HELD"})
    check_not_zero(rows)
    return rows
