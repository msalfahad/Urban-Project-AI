"""COVERAGE CENSUS (M9 S1) - one terminal state for every BOQ family of the family master, per run (generic; stdlib).

    census(lines, *, family_coverage=None, structural_run=False, rooms_run=False, material_results=(), arch_run=False)
        -> rows
    summary(rows)                                                                                   -> counts

A family never disappears from a run: it is QUANTIFIED, BOUNDED_ONLY, BLOCKED, NOT_FOUND_IN_SOURCE, COUNTED_IN_PARENT,
NOT_RUN (the engine has the capability but this run did not exercise it), NOT_IMPLEMENTED or BLOCKED_BY_SOURCE (the
capability needs documents the engine does not read), each with its reason. The capability column comes from the
family master (rules/coverage/BOQ_FAMILY_MASTER_1.0.0.json); the run state only from what this run produced.
"""

from __future__ import annotations

from collections import Counter

from engine.source import boq_line as BL
from engine.source import rule_store as RS

RUN_STATES = ("QUANTIFIED", "BOUNDED_ONLY", "BLOCKED", "NOT_FOUND_IN_SOURCE", "COUNTED_IN_PARENT", "NOT_RUN",
              "NOT_IMPLEMENTED", "BLOCKED_BY_SOURCE")
# family master code -> canonical item codes whose lines answer it
FAMILY_ITEMS = {
    "B10-01": ("STR.CONC.BLINDING",), "B10-02": ("STR.CONC.FOOTING",), "B10-03": ("STR.CONC.NECK",),
    "B10-04": ("STR.CONC.STRAP", "STR.CONC.GROUND_BEAM"), "B10-05": ("STR.CONC.GROUND_SLAB",),
    "B10-06": ("STR.CONC.COLUMN",), "B10-07": ("STR.CONC.BEAM",), "B10-08": ("STR.CONC.SLAB",),
    "B10-09": ("STR.CONC.DOME",), "B10-10": ("STR.CONC.POOL", "STR.CONC.TANK", "STR.CONC.LIFT"),
    "B10-11": ("STR.CONC.BOUNDARY_WALL",), "B10-12": ("STR.CONC.PARAPET",), "B7-12": ("STR.CONC.STAIR",),
    "B9-02": ("STR.CONC.LINTEL",), "B11-01": ("STR.REBAR",),
    "B3-01": ("FIN.FLOOR.PORCELAIN",), "B3-02": ("FIN.FLOOR.WET_TILE",), "B4-01": ("FIN.WALL.TILE",),
    "B8-01": ("FIN.WP.FLOOR",), "B8-02": ("FIN.WP.DOORWAY",), "B8-03": ("FIN.WP.UPTURN",),
    # M9 S2 architectural route (lines of these codes come only from urban_boq_m9 arch)
    "B3-06": ("FIN.SKIRTING",), "B4-03": ("FIN.PLASTER",), "B4-06": ("FIN.PAINT",), "B5-01": ("FIN.CEILING",),
    "B6-01": ("ARCH.DOOR", "ARCH.WINDOW", "ARCH.PASSAGE"), "B7-01": ("FIN.STAIR.FLIGHT",),
    # M9 S3 stair finishes from the drawn flights
    "B7-02": ("FIN.MARBLE.TREAD",), "B7-03": ("FIN.MARBLE.RISER",), "B7-04": ("FIN.MARBLE.LANDING",),
    "B7-06": ("FIN.STAIR.STEP_LM",), "B9-01": ("MAS.BLOCK",),     # the wall run (lm) is its geometry, not its m2
}
STRUCTURAL = {k for k, v in FAMILY_ITEMS.items() if v[0].startswith("STR.")}
ROOM_FAMILIES = {"B3-01", "B3-02", "B4-01", "B8-01", "B8-02", "B8-03", "B8-05"}
# the families an architectural-plan run (arch_run) measures room by room; a room schedule run (rooms_run) keeps the
# S1 set above, so an S1 census is unchanged
ARCH_FAMILIES = ROOM_FAMILIES | {"B3-06", "B4-03", "B4-06", "B5-01", "B6-01", "B7-01", "B7-02", "B7-03", "B7-04",
                                 "B7-06", "B9-01"}
# route G family_coverage FAMILY -> master code (engine.source.family_coverage)
COVERAGE_FAMILY = {"PLAIN_CONCRETE": "B10-01", "COLUMN_NECKS": "B10-03", "LINTELS": "B9-02", "LIFT": "B10-10",
                   "POOL": "B10-10", "WATER_TANK": "B10-10", "STAIRS": "B7-12", "DOMES": "B10-09",
                   "PARAPETS": "B10-12", "WALLS": "B10-11"}
COVERAGE_STATE = {"QUANTIFIED": "QUANTIFIED", "PARTLY_QUANTIFIED": "QUANTIFIED", "BOUNDED_NOT_MEASURED": "BOUNDED_ONLY",
                  "DETECTED_NOT_QUANTIFIED": "BLOCKED", "NO_EVIDENCE_FOUND": "NOT_FOUND_IN_SOURCE",
                  "COUNTED_IN_PARENT": "COUNTED_IN_PARENT"}
SCOPE_REBAR_FAMILIES = ("STAIRS", "POOL", "DOMES", "WATER_TANK", "LIFT", "BOUNDARY_WALL", "PARAPETS", "WALLS")
ORDER = {s: i for i, s in enumerate(RUN_STATES)}


def _from_lines(ls):
    ev = Counter(ln["evidence_state"] for ln in ls)
    if any(ev[s] for s in BL.QUANTITY_STATES):
        return "QUANTIFIED", dict(ev)
    if ev["BOUNDED_EXPOSURE"]:
        return "BOUNDED_ONLY", dict(ev)
    if ev["BLOCKED_RFI"]:
        return "BLOCKED", dict(ev)
    if ev["NOT_APPLICABLE_WITH_EVIDENCE"] or ev["EXCLUDED_WITH_REASON"]:
        return "COUNTED_IN_PARENT", dict(ev)
    return None, dict(ev)


def census(lines, *, family_coverage=None, structural_run=False, rooms_run=False, material_results=(), arch_run=False):
    master = RS.family_master()
    by_code = {}
    for ln in lines:
        by_code.setdefault(ln["item_code"], []).append(ln)
    cov = {}
    for rec in family_coverage or []:
        code = COVERAGE_FAMILY.get(rec["FAMILY"])
        if code:
            cov.setdefault(code, []).append(rec)
    rows = []
    for f in master["families"]:
        code, cap = f["code"], f["capability"]
        ls = [ln for ic in FAMILY_ITEMS.get(code, ()) for ln in by_code.get(ic, [])]
        state, ev = _from_lines(ls) if ls else (None, {})
        reason = ""
        if state:
            reason = f"{len(ls)} line(s) in this run"
        if code in cov and state in (None, "BOUNDED_ONLY", "BLOCKED"):
            # the route's own family census: the strongest state any of its records reaches
            cs = sorted((COVERAGE_STATE[r["STATE"]] for r in cov[code]), key=lambda s: ORDER[s])
            if state is None or ORDER[cs[0]] < ORDER[state]:
                state = cs[0]
                reason = "; ".join(f"{r['FAMILY']}: {r['STATE']} ({r.get('REASON') or r.get('EVIDENCE') or ''})"
                                   for r in cov[code])[:400]
        if code == "B11-03" and structural_run:
            scope = [ln for ln in lines if ln["item_code"].startswith("STR.CONC.") and
                     (ln.get("physical_element") or "") in SCOPE_REBAR_FAMILIES and ln["evidence_state"] != "BLOCKED_RFI"]
            steel = [ln for ln in lines if ln["item_code"] == "STR.REBAR" and
                     (ln.get("physical_element") or "") in SCOPE_REBAR_FAMILIES]
            if scope and not steel:
                state, reason = "BLOCKED", (f"MISSING_DATA: {len(scope)} concrete line(s) of these families carry no bar "
                                            f"model (no kg/m3 ratio is ever used)")
        if code == "B8-05" and (rooms_run or arch_run):
            mem = [r for r in material_results if (r.get("material_spec") or {}).get("kind") == "MEMBRANE_SHEET"]
            done = [r for r in mem if r["state"] != "BLOCKED"]
            if done:
                state, reason = "QUANTIFIED", f"{len(done)} room roll plan(s) (procurement view, never the BOQ net)"
            elif mem:
                state, reason = "BLOCKED", mem[0]["blocked_by"]
        if state is None:
            if code in STRUCTURAL and structural_run:
                state, reason = "NOT_FOUND_IN_SOURCE", "the structural route ran and produced no line for this family"
            elif code in ROOM_FAMILIES and rooms_run:
                state, reason = "NOT_FOUND_IN_SOURCE", "the room input has no surface of this family"
            elif code in ARCH_FAMILIES and arch_run:
                state, reason = "NOT_FOUND_IN_SOURCE", "the architectural plans of this run gave no room of this family"
            elif cap == "NOT_IMPLEMENTED":
                state, reason = "NOT_IMPLEMENTED", f"no engine capability yet (next slice {f['next_slice']})"
            elif cap == "BLOCKED_BY_SOURCE":
                state, reason = "BLOCKED_BY_SOURCE", f"needs {f['source_needed']}"
            else:
                why = ("no structural drawing in this run" if code in STRUCTURAL else
                       "no room input in this run (room geometry from drawings: S2)" if code in ROOM_FAMILIES else
                       f"capability {cap} ({f['implementation']}) is not part of this route")
                state, reason = "NOT_RUN", why
        rows.append({"code": code, "group": f["group"], "item_en": f["item_en"], "item_ar": f["item_ar"],
                     "unit": f["unit"], "capability": cap, "run_state": state, "lines": len(ls),
                     "evidence": dict(sorted(ev.items())), "reason": reason, "next_slice": f["next_slice"]})
    bad = [r["code"] for r in rows if r["run_state"] not in RUN_STATES or not r["reason"]]
    if bad:
        raise ValueError(f"families without a terminal state or reason: {bad}")
    return rows


def summary(rows):
    return {"families": len(rows), "by_run_state": dict(sorted(Counter(r["run_state"] for r in rows).items())),
            "by_capability": dict(sorted(Counter(r["capability"] for r in rows).items())),
            "silent_omissions": 0}
