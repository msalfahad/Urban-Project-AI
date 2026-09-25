"""Sheet / view role classifier (PA05 §4).

Deterministic clues first (title text, section markers, level symbols, cut
hatching, dimension orientation, schedule tables, sheet metadata); an AI
role may be supplied when deterministic evidence is incomplete.  A mismatch
between the two produces a CHALLENGE, never a silent selection.
"""

from __future__ import annotations

import re

ROLES = ("FLOOR_PLAN", "ROOF_PLAN", "REFLECTED_CEILING_PLAN", "ELEVATION", "SECTION", "SECTION_ELEVATION", "STRUCTURAL_PLAN", "BEAM_SCHEDULE",
         "COLUMN_SCHEDULE", "DETAIL", "DOOR_WINDOW_SCHEDULE", "FINISH_SCHEDULE", "UNKNOWN")
TITLE_RULES = (
    (r"\bREFLECTED\b|\bCEILING\b", "REFLECTED_CEILING_PLAN"),
    (r"\bROOF\b.*\bPLAN\b|\bPLAN\b.*\bROOF\b", "ROOF_PLAN"),
    (r"\bFLOOR\b.*\bPLAN\b|\bPLAN\b", "FLOOR_PLAN"),
    (r"\bSECTION\b.*\bELEVATION\b", "SECTION_ELEVATION"),
    (r"\bSECTION\b|\bSEC\b", "SECTION"),
    (r"\bELEVATION\b", "ELEVATION"),
    (r"SCHEDULE.*(BEAM)|BEAM.*SCHEDULE", "BEAM_SCHEDULE"),
    (r"SCHEDULE.*(COLUMN|FOOTING)|COLUMN.*SCHEDULE", "COLUMN_SCHEDULE"),
    (r"(DOOR|WINDOW).*SCHEDULE|SCHEDULE.*(DOOR|WINDOW)", "DOOR_WINDOW_SCHEDULE"),
    (r"FINISH.*SCHEDULE|SCHEDULE.*FINISH", "FINISH_SCHEDULE"),
    (r"\bSLAB\b|\bBEAMS?\b|\bFOUNDATION\b|\bCOLUMN.*AXIS\b", "STRUCTURAL_PLAN"),
    (r"\bDETAIL\b", "DETAIL"),
)
EVIDENCE_FIELDS = ("TITLE_TEXTS", "LEVEL_SYMBOL_COUNT", "SECTION_MARKER_COUNT", "CUT_HATCH_PRESENT", "DIMENSION_ORIENTATION", "SCHEDULE_TABLE",
                   "ROOM_LABEL_COUNT", "METADATA_ROLE", "TEXT_LAYER_AVAILABLE", "DOOR_ARC_COUNT", "CLOSED_SPACE_COUNT", "RASTER_ONLY")
PLAN_ROLES = ("FLOOR_PLAN", "ROOF_PLAN", "REFLECTED_CEILING_PLAN", "STRUCTURAL_PLAN")


def evidence(**e):
    out = {k: e.get(k) for k in EVIDENCE_FIELDS}
    return out


def deterministic_role(ev):
    titles = " ".join(str(t) for t in (ev.get("TITLE_TEXTS") or [])).upper()
    role, why = None, []
    for pat, r in TITLE_RULES:
        if re.search(pat, titles):
            role = r
            why.append(f"title matches /{pat}/ -> {r}")
            break
    if role is None and ev.get("SCHEDULE_TABLE"):
        role = "UNKNOWN"; why.append("a schedule table is present but its subject is not in the title")
    if role is None and ev.get("METADATA_ROLE"):
        role = ev["METADATA_ROLE"]; why.append("sheet metadata role (index / register) used: no readable title")
    if role is None:
        # geometry hints (CAD views with no title text): door swings + closed rooms say plan family; level marks without doors say vertical view
        doors, closed, levels = ev.get("DOOR_ARC_COUNT") or 0, ev.get("CLOSED_SPACE_COUNT") or 0, ev.get("LEVEL_SYMBOL_COUNT") or 0
        if doors >= 1 and closed >= 2:
            why.append(f"geometry hint: {doors} door swing(s) and {closed} closed spaces -> plan family (floor vs roof undecidable from geometry)")
            return "FLOOR_PLAN", why, "INCOMPLETE"
        if closed >= 2 and (ev.get("ROOM_LABEL_COUNT") or 0) >= 2 and ev.get("DIMENSION_ORIENTATION") != "VERTICAL_DOMINANT":
            why.append(f"geometry hint: {closed} closed spaces with {ev.get('ROOM_LABEL_COUNT')} text stamps and no vertical-dominant dimensions -> plan family (no door swings drawn)")
            return "FLOOR_PLAN", why, "INCOMPLETE"
        if levels >= 3 and doors == 0 and ev.get("DIMENSION_ORIENTATION") == "VERTICAL_DOMINANT":
            why.append(f"geometry hint: {levels} level marks, no door swings, vertical dimensions -> vertical view (elevation vs section undecidable)")
            return "ELEVATION", why, "INCOMPLETE"
    # refinement: an ELEVATION that carries cut hatching with level symbols along a vertical axis is a SECTION_ELEVATION
    if role == "ELEVATION" and ev.get("CUT_HATCH_PRESENT") is True:
        role = "SECTION_ELEVATION"; why.append("cut hatching present on an elevation sheet -> SECTION_ELEVATION")
    if role in ("FLOOR_PLAN", "ROOF_PLAN") and (ev.get("LEVEL_SYMBOL_COUNT") or 0) >= 3 and ev.get("DIMENSION_ORIENTATION") == "VERTICAL_DOMINANT":
        why.append("level symbols with vertical-dominant dimensions on a plan title: inconsistent evidence")
        return role, why, "INCONSISTENT"
    if role is None:
        return "UNKNOWN", why or ["no title, no schedule, no metadata"], "INCOMPLETE"
    strength = "COMPLETE" if (ev.get("TITLE_TEXTS") and ev.get("TEXT_LAYER_AVAILABLE")) else "INCOMPLETE"
    return role, why, strength


def classify(ev, ai_role=None, ai_evidence=None):
    """Returns DETERMINISTIC_ROLE / AI_ROLE / FINAL_ROLE / ROLE_STATUS / EVIDENCE.
    FINAL is the deterministic role when evidence is COMPLETE; the AI role may fill an INCOMPLETE or UNKNOWN
    deterministic result; a disagreement is a CHALLENGE and the final role is HUMAN_REVIEW."""
    d_role, why, strength = deterministic_role(ev)
    if ai_role is not None and ai_role not in ROLES:
        raise ValueError(f"unknown AI role {ai_role}")
    if ai_role is None:
        final, st = d_role, ("DETERMINISTIC" if strength == "COMPLETE" else ("DETERMINISTIC_INCOMPLETE" if d_role != "UNKNOWN" else "UNKNOWN"))
    elif d_role == "UNKNOWN":
        final, st = ai_role, "AI_FILLED_UNKNOWN"
    elif ai_role == d_role:
        final, st = d_role, "AGREED"
    elif strength != "COMPLETE" and {d_role, ai_role} <= {"ELEVATION", "SECTION_ELEVATION"}:
        # the only refinement an AI may make on incomplete evidence: an elevation is a section-elevation (cut storey)
        final, st = ai_role, "AI_REFINED_ON_INCOMPLETE_EVIDENCE"
        why = why + [f"AI: {ai_evidence}"]
    else:
        final, st = "HUMAN_REVIEW", "CHALLENGE"
        why = why + [f"AI disagrees: {ai_role} ({ai_evidence})"]
    return {"DETERMINISTIC_ROLE": d_role, "AI_ROLE": ai_role, "FINAL_ROLE": final, "ROLE_STATUS": st, "EVIDENCE": why, "EVIDENCE_STRENGTH": strength}
