"""The invariants, evaluated from evidence.

Each one returns a record rather than a boolean: what it looked at, what it allows, what it found, and how.  A
check that only confirms the engine's own chosen interpretation is worth nothing, so every one of these is
written to be capable of failing on real output, and the mutation tests prove that it does.
"""

from __future__ import annotations

import random
import re
from pathlib import Path

from engine.qs_core import identity
from engine.qs_core.entities import (ASSIGNED_TO_SPACE, EXTERNAL_OPEN_AREA, HOST_ASSIGNED, KIND_COLUMN,
                                     KIND_FLOOR_REGION, KIND_SLIVER, KIND_WALL_BAND, NON_ROOM_GEOMETRY,
                                     UNRESOLVED)

PRICING_FIELDS = ("WASTE_PERCENT", "PROCUREMENT_QUANTITY", "UNIT_RATE", "AMOUNT")


def _rec(name, ok, inputs, tolerance, result, method):
    return {"INVARIANT": name, "PASS": bool(ok), "INPUTS": inputs, "TOLERANCE": tolerance,
            "RESULT": result, "METHOD": method}


def one_host_per_opening(register):
    offenders = [o["OPENING_REF"] for o in register["REGISTER"]
                 if o["HOST_ASSIGNMENT_STATUS"] == HOST_ASSIGNED and not o["HOST_COMPONENT_REF"]]
    multi = [o["OPENING_REF"] for o in register["REGISTER"]
             if isinstance(o["HOST_COMPONENT_REF"], (list, tuple))]
    return _rec("INV-01_EVERY_OPENING_HAS_AT_MOST_ONE_HOST", not offenders and not multi,
                {"OPENINGS": register["OPENING_COUNT"]}, 0,
                {"ASSIGNED_WITHOUT_A_HOST": offenders, "HOSTED_BY_MORE_THAN_ONE": multi},
                "every register row's host field read; a host is a single component reference or nothing")


def deductions_reconcile(register, wall_rows, tolerance):
    assigned = sum(r["OPENING_DEDUCTION_M2"] for r in wall_rows)
    expected = register["ASSIGNED_AREA_M2"]
    total = register["TOTAL_OPENING_AREA_M2"]
    sum_parts = register["ASSIGNED_AREA_M2"] + register["UNRESOLVED_AREA_M2"]
    ok = abs(assigned - expected) <= tolerance and abs(sum_parts - total) <= tolerance
    return _rec("INV-02_DEDUCTIONS_RECONCILE_WITH_THE_CANONICAL_REGISTER", ok,
                {"CANONICAL_TOTAL_M2": total, "ASSIGNED_M2": register["ASSIGNED_AREA_M2"],
                 "UNRESOLVED_M2": register["UNRESOLVED_AREA_M2"]}, tolerance,
                {"SUM_OF_WALL_ROW_DEDUCTIONS_M2": round(assigned, 9),
                 "ASSIGNED_PLUS_UNRESOLVED_M2": round(sum_parts, 9)},
                "the wall rows' deductions summed independently and compared with the register's own totals")


def deductions_match_band_by_band(register, wall_rows, tolerance):
    """Not just the right total: the right deduction against the right wall.

    Pro-rata allocation keeps the floor total exactly and puts the material against the wrong thickness, so a
    check on the total alone cannot see it.  This one compares band by band with the canonical register.
    """
    expected = register["DEDUCTION_BY_WALL_COMPONENT_M2"]
    offenders = []
    for r in wall_rows:
        want = expected.get(r["COMPONENT_REF"], 0.0)
        if abs(r["OPENING_DEDUCTION_M2"] - want) > tolerance:
            offenders.append({"COMPONENT_REF": r["COMPONENT_REF"], "IN_THE_WALL_ROW": r["OPENING_DEDUCTION_M2"],
                              "IN_THE_REGISTER": want,
                              "DIFFERENCE": round(r["OPENING_DEDUCTION_M2"] - want, 9)})
    return _rec("INV-14_EVERY_DEDUCTION_SITS_ON_THE_BAND_THAT_HOSTS_IT", not offenders,
                {"WALL_ROWS": len(wall_rows), "BANDS_WITH_A_DEDUCTION": len(expected)}, tolerance,
                {"OFFENDERS": offenders},
                "each wall row's deduction compared with the canonical register's own per-band total")


def unresolved_never_allocated(register, wall_rows, tolerance):
    unresolved_refs = set(register["UNRESOLVED_REFS"])
    allocated = sum(r["OPENING_DEDUCTION_M2"] for r in wall_rows)
    ok = abs(allocated - register["ASSIGNED_AREA_M2"]) <= tolerance
    blocked = [r["COMPONENT_REF"] for r in wall_rows if r["STATUS"] != "FINAL_QUANTITY_AVAILABLE"]
    return _rec("INV-03_AN_UNRESOLVED_OPENING_IS_NEVER_SILENTLY_ALLOCATED",
                ok and (not unresolved_refs or blocked),
                {"UNRESOLVED_OPENINGS": sorted(unresolved_refs)}, tolerance,
                {"ALLOCATED_M2": round(allocated, 9), "ASSIGNED_M2": register["ASSIGNED_AREA_M2"],
                 "BLOCKED_WALL_ROWS": blocked},
                "the unresolved area is absent from every wall row, and the affected rows are blocked")


def no_wall_material_as_floor(membership):
    offenders = [m["COMPONENT_REF"] for m in membership
                 if m["KIND"] in (KIND_WALL_BAND, KIND_COLUMN, KIND_SLIVER)
                 and (m["ROOM_ID"] or m["STATUS"] == ASSIGNED_TO_SPACE)]
    return _rec("INV-04_NO_WALL_MATERIAL_BECOMES_FLOOR_FINISH", not offenders,
                {"COMPONENTS": len(membership)}, 0, {"OFFENDERS": offenders},
                "every non-room kind checked for a room membership it must not have")


def every_component_resolved_once(membership):
    allowed = {ASSIGNED_TO_SPACE, NON_ROOM_GEOMETRY, EXTERNAL_OPEN_AREA, UNRESOLVED}
    refs = [m["COMPONENT_REF"] for m in membership]
    dup = sorted({r for r in refs if refs.count(r) > 1})
    bad = [m["COMPONENT_REF"] for m in membership if m["STATUS"] not in allowed]
    return _rec("INV-05_EVERY_COMPONENT_ENDS_IN_EXACTLY_ONE_STATE", not dup and not bad,
                {"COMPONENTS": len(refs), "ALLOWED_STATES": sorted(allowed)}, 0,
                {"APPEARS_MORE_THAN_ONCE": dup, "IN_NO_ALLOWED_STATE": bad},
                "the membership register counted by reference, and every state checked against the allowed set")


def space_areas_match_members(spaces, components, tolerance):
    by_ref = {c.component_ref: c for c in components}
    worst, worst_room = 0.0, None
    for s in spaces:
        total = sum(by_ref[r].area for r in s.component_refs)
        if abs(total - s.area) > worst:
            worst, worst_room = abs(total - s.area), s.room_id
    return _rec("INV-06_A_SPACE_AREA_IS_THE_SUM_OF_ITS_COMPONENTS", worst <= tolerance,
                {"SPACES": len(spaces)}, tolerance,
                {"WORST_DIFFERENCE_M2": round(worst, 9), "WORST_ROOM": worst_room},
                "each space's published area compared with its member components re-summed")


def floor_closure(components, window_area, tolerance):
    total = sum(c.area for c in components)
    return _rec("INV-07_FLOOR_CLOSURE_IS_PRESERVED", abs(total - window_area) <= tolerance,
                {"COMPONENTS": len(components), "PLAN_WINDOW_AREA_M2": round(window_area, 9)}, tolerance,
                {"SUM_OF_COMPONENTS_M2": round(total, 9),
                 "RESIDUAL_M2": round(window_area - total, 9)},
                "every component's area summed and compared with the plan window it came from")


def identity_is_order_independent(components, revision, shuffles=5, seed=20260924, assign=None):
    """Assign identity over shuffled input and require the same answer.  The assigner is an argument so a
    defective one can be put through the same check and be seen to fail."""
    assign = assign or identity.assign_identity
    rnd = random.Random(seed)
    base = list(components)
    assign(base, revision)
    reference = {c.component_ref: c.uid for c in base}
    mismatches = []
    for _ in range(shuffles):
        shuffled = list(components)
        rnd.shuffle(shuffled)
        for c in shuffled:
            c.uid = None
        assign(shuffled, revision)
        for c in shuffled:
            if reference[c.component_ref] != c.uid:
                mismatches.append(c.component_ref)
    return _rec("INV-08_REVISION_ORDER_DOES_NOT_CHANGE_IDENTITY", not mismatches,
                {"COMPONENTS": len(base), "SHUFFLES": shuffles}, 0,
                {"COMPONENTS_WHOSE_UID_MOVED": sorted(set(mismatches))},
                "identity assigned repeatedly over shuffled input and compared with the first assignment")


def continuous_floor_is_one_space(seams, membership, continuous_relation="CONTINUOUS_FLOOR"):
    """Two pieces of floor that continue into one another belong to one room, label or no label."""
    room = {m["COMPONENT_REF"]: m["ROOM_ID"] for m in membership}
    offenders = [{"A": s["A"], "B": s["B"], "ROOM_A": room.get(s["A"]), "ROOM_B": room.get(s["B"])}
                 for s in seams if s["RELATION"] == continuous_relation
                 and room.get(s["A"]) != room.get(s["B"])]
    return _rec("INV-11_CONTINUOUS_FLOOR_IS_ONE_SPACE", not offenders,
                {"SEAMS": len(seams)}, 0, {"OFFENDERS": offenders},
                "every seam the engine read as continuous checked against the room each side ended up in")


def ambiguous_hosts_are_surfaced(register, decisive_margin):
    """An opening whose two best candidates are within the decisive margin may not be quietly assigned."""
    offenders = []
    for o in register["REGISTER"]:
        cands = o["HOST_CANDIDATES"]
        if o["HOST_ASSIGNMENT_STATUS"] != HOST_ASSIGNED or len(cands) < 2:
            continue
        if cands[0]["SCORE"] - cands[1]["SCORE"] < decisive_margin:
            offenders.append({"OPENING_REF": o["OPENING_REF"], "MARGIN":
                              round(cands[0]["SCORE"] - cands[1]["SCORE"], 6)})
    return _rec("INV-12_AN_AMBIGUOUS_HOST_IS_NEVER_QUIETLY_ASSIGNED", not offenders,
                {"OPENINGS": register["OPENING_COUNT"], "DECISIVE_MARGIN": decisive_margin}, 0,
                {"ASSIGNED_DESPITE_A_TIE": offenders},
                "the top two candidate scores of every assigned opening compared with the decisive margin")


def checks_are_evidence_based(checks, forbidden_tokens):
    """A check that cites a known answer as its input is not a check; it is the answer, written twice."""
    bad = []
    for c in checks:
        blob = repr({"INPUTS": c.get("INPUTS"), "RESULT": c.get("RESULT"), "METHOD": c.get("METHOD")})
        if not c.get("METHOD") or not c.get("INPUTS"):
            bad.append({"CHECK": c.get("INVARIANT"), "WHY": "no method or no inputs"})
        for tok in forbidden_tokens:
            if tok in blob:
                bad.append({"CHECK": c.get("INVARIANT"), "WHY": f"cites the comparison value {tok}"})
    return _rec("INV-13_EVERY_CHECK_IS_EVIDENCE_BASED", not bad,
                {"CHECKS": len(checks), "TOKENS_CHECKED": len(forbidden_tokens)}, 0, {"OFFENDERS": bad},
                "each check's own inputs and method inspected for a stated expected answer")


def no_comparison_input(paths, forbidden_tokens):
    """The production code may not contain a comparison total, a project name or a known answer.

    The token list belongs to the caller: embedding it here would be the very thing it forbids.
    """
    hits = []
    for p in paths:
        text = Path(p).read_text("utf-8")
        for tok in forbidden_tokens:
            for m in re.finditer(re.escape(tok), text):
                line = text.count("\n", 0, m.start()) + 1
                hits.append({"FILE": str(p), "LINE": line, "TOKEN": tok})
    return _rec("INV-09_NO_COMPARISON_TOTAL_OR_PROJECT_NAME_IN_PRODUCTION_CODE", not hits,
                {"FILES": [str(p) for p in paths], "TOKENS_CHECKED": len(forbidden_tokens)}, 0,
                {"HITS": hits},
                "every production source file scanned for every forbidden token supplied by the caller")


def pricing_fields_separate_and_empty(measurement_objects):
    bad = []
    for m in measurement_objects:
        d = m.as_dict() if hasattr(m, "as_dict") else m
        for f in PRICING_FIELDS:
            if f not in d:
                bad.append({"OBJECT": d.get("MEASUREMENT_OBJECT_ID"), "MISSING_FIELD": f})
            elif d[f] is not None:
                bad.append({"OBJECT": d.get("MEASUREMENT_OBJECT_ID"), "FIELD": f, "VALUE": d[f]})
        if "MEASURED_QUANTITY" not in d or "MEASURED_UNIT" not in d:
            bad.append({"OBJECT": d.get("MEASUREMENT_OBJECT_ID"), "MISSING_FIELD": "MEASURED_QUANTITY/UNIT"})
    return _rec("INV-10_QUANTITY_UNIT_AND_PRICING_STAY_SEPARATE_AND_EMPTY", not bad,
                {"OBJECTS": len(measurement_objects), "PRICING_FIELDS": list(PRICING_FIELDS)}, 0,
                {"OFFENDERS": bad},
                "every measurement object checked for the six separate fields, four of which must be empty")


def evaluate_all(**checks):
    rows = [v for v in checks.values()]
    return {"CHECKS": rows, "PASSED": sum(1 for r in rows if r["PASS"]), "OF": len(rows),
            "ALL_PASS": all(r["PASS"] for r in rows)}
