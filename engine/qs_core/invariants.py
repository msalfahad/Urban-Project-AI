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


# ---------------------------------------------------------------- the publication contract
def blocked_never_enters_a_published_total(publication, rows, quantity_field):
    """A published subtotal may not contain a blocked row, and a blocked row may not carry a quantity.

    This is the check the R4 output could not pass: every wall row was blocked, every subtotal was published,
    and nothing in the engine objected, because nothing was asked to.
    """
    from engine.qs_core import quantities as QY

    offenders = []
    for key, sub in publication["SUBTOTALS"].items():
        if sub["FINAL_QUANTITY"] is not None and sub["ROWS_BLOCKED"]:
            offenders.append({"SUBTOTAL": key, "FINAL_QUANTITY": sub["FINAL_QUANTITY"],
                              "BLOCKED_ROWS": sub["BLOCKED_ROW_REFS"],
                              "WHY": "a quantity was published over rows that are not final"})
    for r in rows:
        if r.get("STATUS") != QY.FINAL and r.get(quantity_field) is not None:
            offenders.append({"ROW": r.get("COMPONENT_REF"), "STATUS": r.get("STATUS"),
                              quantity_field: r.get(quantity_field),
                              "WHY": "a blocked row carries a value under the publishable field name, where a "
                                     "later sum would pick it up"})
    if publication["PUBLISHED_TOTAL"] is not None and publication["BLOCKED_SUBTOTAL_COUNT"]:
        offenders.append({"TOTAL": publication["PUBLISHED_TOTAL"],
                          "BLOCKED_SUBTOTALS": publication["BLOCKED_SUBTOTAL_COUNT"],
                          "WHY": "a total was published although some of its subtotals are null"})
    return _rec("INV-15_A_BLOCKED_ROW_NEVER_REACHES_A_PUBLISHED_TOTAL", not offenders,
                {"SUBTOTALS": len(publication["SUBTOTALS"]), "ROWS": len(rows),
                 "QUANTITY_FIELD": quantity_field}, 0, {"OFFENDERS": offenders},
                "every subtotal checked against its own blocked-row list, and every blocked row checked for a "
                "value under the publishable field name")


def unusual_band_is_not_billed_on_thickness_alone(identity_register, rows):
    """Having a measurable thickness is not being a wall."""
    from engine.qs_core import masonry as MA, quantities as QY

    ident = {r["COMPONENT_REF"]: r for r in identity_register["REGISTER"]}
    offenders = []
    for r in rows:
        i = ident.get(r.get("COMPONENT_REF"))
        if r.get("STATUS") != QY.FINAL:
            continue
        if i is None:
            offenders.append({"ROW": r.get("COMPONENT_REF"), "WHY": "billed with no identity record at all"})
        elif not i["BILLABLE_AS_MASONRY"]:
            offenders.append({"ROW": r.get("COMPONENT_REF"),
                              "GEOMETRY_IDENTITY": i["GEOMETRY_IDENTITY"],
                              "MATERIAL_IDENTITY": i["MATERIAL_IDENTITY"],
                              "WHY": "billed although one of its two identities is not established"})
        elif not i["THICKNESS_FAMILY_PROVED"] and not i.get("ANNOTATION"):
            offenders.append({"ROW": r.get("COMPONENT_REF"), "THICKNESS_M": i["THICKNESS_M"],
                              "FAMILY_MEMBERS": i["THICKNESS_FAMILY_MEMBERS"],
                              "WHY": "billed on a thickness that occurs once in the whole drawing, with no "
                                     "annotation to support it"})
    return _rec("INV-16_A_BAND_IS_NOT_BILLED_AS_MASONRY_BECAUSE_IT_HAS_A_THICKNESS", not offenders,
                {"IDENTITY_RECORDS": len(ident), "ROWS": len(rows),
                 "BILLABLE_GEOMETRY": list(MA.BILLABLE_GEOMETRY),
                 "BILLABLE_MATERIAL": list(MA.BILLABLE_MATERIAL)}, 0, {"OFFENDERS": offenders},
                "every final row matched to its identity record and to the thickness family behind it")


def deductions_trace_to_width_and_height_evidence(register):
    """A deduction is an area, and an area is two independent facts.  Both have to be established."""
    from engine.qs_core import evidence as EV

    offenders = []
    for o in register["REGISTER"]:
        if o["AREA_M2"] is None:
            continue
        adm = o.get("ADMISSION") or {}
        w, h = adm.get("WIDTH_EVIDENCE"), adm.get("HEIGHT_EVIDENCE")
        if not EV.established(w) or not EV.established(h):
            offenders.append({"OPENING_REF": o["OPENING_REF"],
                              "WIDTH_STATUS": (w or {}).get("STATUS", "NO_RECORD"),
                              "HEIGHT_STATUS": (h or {}).get("STATUS", "NO_RECORD"),
                              "WHY": "an area is being deducted without an established record for both of the "
                                     "dimensions it is made of"})
        elif w.get("REFERENCE") is not None and w.get("REFERENCE") == h.get("REFERENCE") \
                and w.get("SOURCE") == EV.MEASURED_GEOMETRY:
            offenders.append({"OPENING_REF": o["OPENING_REF"], "REFERENCE": w.get("REFERENCE"),
                              "WHY": "width and height come from the same measured object, so the two facts "
                                     "are not independent"})
    return _rec("INV-17_EVERY_DEDUCTION_TRACES_TO_WIDTH_EVIDENCE_AND_HEIGHT_EVIDENCE", not offenders,
                {"OPENINGS": register["OPENING_COUNT"], "HIERARCHY": list(EV.HIERARCHY)}, 0,
                {"OFFENDERS": offenders},
                "each deducted opening's two evidence records read and checked for establishment and for "
                "independence of source")


def wall_continuity_is_proved_not_permitted(gap_log):
    """A gap may be closed by evidence that something spans it, never by a maximum span alone."""
    from engine.qs_core import openings as OP

    allowed = {OP.GAP_BRIDGED_BY_CONFIRMED_OPENING, OP.GAP_BRIDGED_BY_CONTINUATION_GEOMETRY,
               OP.GAP_BRIDGED_BY_DECLARED_CAD_CONTINUITY}
    offenders = [g for g in gap_log if g["BRIDGED"] and g["RELATION"] not in allowed]
    return _rec("INV-18_A_WALL_IS_CONTINUED_ONLY_WHERE_SOMETHING_SPANS_THE_GAP", not offenders,
                {"GAPS_EXAMINED": len(gap_log), "RELATIONS_THAT_PROVE_CONTINUITY": sorted(allowed)}, 0,
                {"BRIDGED_WITHOUT_EVIDENCE": offenders},
                "every gap the assembler closed checked for the evidence relation that closed it")


def opening_basis_is_decided_per_wall_line(basis_by_ref, wall_lines):
    """One Boolean for a whole source is an assumption about a mixed population."""
    from engine.qs_core import openings as OP

    offenders = []
    for ln in wall_lines:
        b = basis_by_ref.get(ln.component_ref)
        if b is None:
            offenders.append({"COMPONENT_REF": ln.component_ref, "WHY": "no basis record"})
            continue
        if b["BASIS"] in (OP.MATERIAL_SPANS, OP.MATERIAL_STOPS) and not b["OPENINGS_TESTED"]:
            offenders.append({"COMPONENT_REF": ln.component_ref, "BASIS": b["BASIS"],
                              "WHY": "a basis was stated for this line without testing a single opening "
                                     "against its material"})
    bases = sorted({b["BASIS"] for b in basis_by_ref.values()})
    return _rec("INV-19_THE_OPENING_BASIS_IS_EVIDENCED_LINE_BY_LINE", not offenders,
                {"WALL_LINES": len(wall_lines), "BASES_FOUND": bases}, 0, {"OFFENDERS": offenders},
                "every wall line's basis record checked for the openings it was decided on")


def blocking_is_limited_to_the_affected_scope(graph, rows):
    """Every blocked row must be reachable from an open question; a blanket block hides finished work."""
    from engine.qs_core import quantities as QY

    named = set(graph["BLOCKED"])
    unexplained = sorted(r["COMPONENT_REF"] for r in rows
                         if r.get("STATUS") != QY.FINAL
                         and r["COMPONENT_REF"] not in named
                         and not r.get("BLOCKED_BY"))
    over = []
    for ref, b in graph["BLOCKED"].items():
        if b["NODE_KIND"] == "WALL_LINE" and not b["REASONS"]:
            over.append({"NODE": ref, "WHY": "blocked with no reason recorded"})
    return _rec("INV-20_A_QUESTION_BLOCKS_ONLY_WHAT_ITS_ANSWER_COULD_CHANGE", not unexplained and not over,
                {"ROWS": len(rows), "BLOCKED_NODES": len(named)}, 0,
                {"BLOCKED_WITHOUT_A_GRAPH_REASON": unexplained, "BLOCKED_WITH_NO_REASON": over},
                "every blocked row traced back to a node the dependency graph blocked, and every blocked node "
                "checked for the reason that blocked it")


def every_candidate_leaves_admission_classified(population):
    """Nothing is deleted on the way in: every candidate leaves with a class and a reason."""
    from engine.qs_core import admission as AD

    bad = [c["CANDIDATE_REF"] for c in population["POPULATION"]
           if c["CLASSIFICATION"] not in AD.CLASSES or not c["EVIDENCE"]]
    lost = population["CANDIDATES_IN"] - len(population["POPULATION"])
    return _rec("INV-21_EVERY_OPENING_CANDIDATE_LEAVES_ADMISSION_WITH_A_CLASS_AND_A_REASON",
                not bad and lost == 0,
                {"CANDIDATES_IN": population["CANDIDATES_IN"], "CLASSES": list(AD.CLASSES)}, 0,
                {"UNCLASSIFIED_OR_UNEXPLAINED": sorted(bad), "CANDIDATES_DROPPED": lost},
                "the admitted population counted against the candidates offered, and each one checked for a "
                "class and the evidence behind it")


def excluded_bands_do_not_block_a_subtotal(rows, publication):
    """A settled exclusion is not an open question, and an open question is not an exclusion.

    Both errors cost quantities: treating a column as an unanswered question withholds finished masonry, and
    treating an unresolved band as an exclusion publishes a subtotal that could still grow.
    """
    excluded = {r["COMPONENT_REF"] for r in rows if r.get("STATUS") == "EXCLUDED_NOT_MASONRY"}  # noqa: E501
    listed = {r["COMPONENT_REF"] for r in publication.get("EXCLUDED_ROWS", [])}
    offenders = []
    if excluded != listed:
        offenders.append({"NOT_LISTED": sorted(excluded - listed), "LISTED_WITHOUT_BEING_EXCLUDED":
                          sorted(listed - excluded)})
    for sub in publication["SUBTOTALS"].values():
        for ref in sub["BLOCKED_ROW_REFS"]:
            if ref in excluded:
                offenders.append({"SUBTOTAL": sub["GROUP"], "REF": ref,
                                  "WHY": "a band whose identity is settled is blocking a subtotal"})
    for r in rows:
        if r.get("STATUS") != "EXCLUDED_NOT_MASONRY":
            continue
        if not r.get("EXCLUDED_BECAUSE") or r.get("NET_AREA_M2") is not None:
            offenders.append({"REF": r["COMPONENT_REF"],
                              "WHY": "excluded without a reason, or still carrying a publishable quantity"})
    return _rec("INV-22_A_SETTLED_EXCLUSION_NEITHER_BLOCKS_NOR_IS_BILLED", not offenders,
                {"ROWS": len(rows), "EXCLUDED": len(excluded)}, 0, {"OFFENDERS": offenders},
                "every excluded band checked against the publication's exclusion list and against every "
                "subtotal's blocked-row list")


def material_is_never_inferred_from_shape(identity_register, rows):
    """Geometry proves a wall.  It never proves what the wall is made of.

    The defect this replaces billed blockwork off a thickness that appeared twice in the drawing.  Repetition
    of a dimension is a fact about draughting, and a bill item is a fact about construction.
    """
    from engine.qs_core import masonry as MA, quantities as QY

    ident = {r["COMPONENT_REF"]: r for r in identity_register["REGISTER"]}
    offenders = []
    for r in identity_register["REGISTER"]:
        if r["MATERIAL_IDENTITY"] == MA.MATERIAL_UNKNOWN:
            continue
        ev = r.get("MATERIAL_EVIDENCE") or {}
        if ev.get("EVIDENCE_SOURCE") not in MA.MATERIAL_EVIDENCE_SOURCES:
            offenders.append({"COMPONENT_REF": r["COMPONENT_REF"],
                              "MATERIAL_IDENTITY": r["MATERIAL_IDENTITY"],
                              "EVIDENCE_SOURCE": ev.get("EVIDENCE_SOURCE"),
                              "WHY": "a material was established by something that cannot state a material"})
        if r.get("THICKNESS_FAMILY_PROVES_MATERIAL"):
            offenders.append({"COMPONENT_REF": r["COMPONENT_REF"],
                              "WHY": "a thickness family was recorded as material evidence"})
    for row in rows:
        if row.get("STATUS") != QY.FINAL:
            continue
        i = ident.get(row.get("COMPONENT_REF")) or {}
        if not (i.get("MATERIAL_EVIDENCE") or {}).get("REFERENCE"):
            offenders.append({"ROW": row.get("COMPONENT_REF"),
                              "WHY": "billed as masonry with no document stating the material"})
    return _rec("INV-23_MATERIAL_IS_NEVER_INFERRED_FROM_SHAPE_OR_REPETITION", not offenders,
                {"BANDS": len(ident), "ROWS": len(rows),
                 "SOURCES_THAT_MAY_STATE_A_MATERIAL": list(MA.MATERIAL_EVIDENCE_SOURCES)}, 0,
                {"OFFENDERS": offenders},
                "every material identity traced to the document that states it, and every billed row checked "
                "for one")


def named_source_openings_are_conserved(population, hosts, register):
    """Every object the source names survives admission, hosting and publication, or is explained.

    R5 lost thirty-five named doors between the CAD file and the report.  Nothing in the engine noticed,
    because nothing counted the source population against the published one.
    """
    named = set(population["NAMED_BY_THE_SOURCE"])
    in_population = {c["CANDIDATE_REF"] for c in population["POPULATION"]}
    physical = set(population["PHYSICAL_OPENING_REFS"])
    hosted = {r["CANDIDATE_REF"] for r in hosts["REGISTER"]}
    published = {o["OPENING_REF"] for o in register["REGISTER"]}
    lost_from_population = sorted(named - in_population)
    excluded = {c["CANDIDATE_REF"]: c["CLASSIFICATION"] for c in population["POPULATION"]
                if c["CANDIDATE_REF"] in named and c["CANDIDATE_REF"] not in physical}
    unexplained = sorted(ref for ref, cls in excluded.items()
                         if cls not in ("DUPLICATE_OF_CONFIRMED_OPENING", "OPENING_CANDIDATE_UNRESOLVED"))
    lost_before_hosting = sorted(physical - hosted)
    lost_before_publication = sorted(physical - published)
    ok = not (lost_from_population or unexplained or lost_before_hosting or lost_before_publication)
    return _rec("INV-24_A_NAMED_SOURCE_OPENING_IS_CONSERVED_TO_THE_END", ok,
                {"NAMED_BY_THE_SOURCE": len(named), "PHYSICAL": len(physical), "HOSTED": len(hosted),
                 "PUBLISHED": len(published)}, 0,
                {"LOST_FROM_THE_POPULATION": lost_from_population,
                 "EXCLUDED_WITHOUT_CONTRADICTORY_EVIDENCE": unexplained,
                 "LOST_BEFORE_HOSTING": lost_before_hosting,
                 "LOST_BEFORE_PUBLICATION": lost_before_publication},
                "the source population counted against the admitted, hosted and published populations")


def existence_is_not_retracted_by_host_failure(population, hosts):
    """An opening whose host could not be worked out is still an opening."""
    from engine.qs_core import admission as AD

    by_ref = {c["CANDIDATE_REF"]: c for c in population["POPULATION"]}
    offenders = []
    for r in hosts["REGISTER"]:
        c = by_ref.get(r["CANDIDATE_REF"], {})
        if r["HOST_STATUS"] != "HOST_CONFIRMED" and \
                c.get("CLASSIFICATION") != AD.OPENING_CONFIRMED_HOST_UNRESOLVED:
            offenders.append({"OPENING": r["CANDIDATE_REF"], "CLASSIFICATION": c.get("CLASSIFICATION"),
                              "WHY": "its host is unresolved and its existence was downgraded with it"})
        if c.get("EXISTENCE") != AD.EXISTS_CONFIRMED:
            offenders.append({"OPENING": r["CANDIDATE_REF"], "EXISTENCE": c.get("EXISTENCE"),
                              "WHY": "an opening reached host resolution without confirmed existence"})
    return _rec("INV-25_AN_UNRESOLVED_HOST_NEVER_RETRACTS_AN_OPENING", not offenders,
                {"HOSTED_OR_ATTEMPTED": len(hosts["REGISTER"]),
                 "HOST_UNRESOLVED": hosts["HOST_UNRESOLVED"]}, 0, {"OFFENDERS": offenders},
                "every host record checked against the classification the same object carries in the "
                "population")


def derived_registers_share_one_evidence_version(final, openings, registers):
    """Every register built after the barrier describes the same moment, and the objects have not moved."""
    from engine.qs_core import final_state as FS

    drift = FS.verify(final, openings)
    version = final["EVIDENCE_VERSION"]
    wrong = [{"REGISTER": i, "VERSION": (r or {}).get(FS.VERSION_FIELD, FS.UNVERSIONED)}
             for i, r in enumerate(registers)
             if (r or {}).get(FS.VERSION_FIELD) != version]
    return _rec("INV-26_EVERY_DERIVED_REGISTER_DESCRIBES_THE_FROZEN_STATE",
                drift["UNCHANGED"] and not wrong,
                {"EVIDENCE_VERSION": version, "REGISTERS": len(registers)}, 0,
                {"DRIFTED": drift["DRIFTED"], "WRONG_VERSION": wrong,
                 "MISSING_AFTER_THE_FREEZE": drift["MISSING_AFTER_THE_FREEZE"]},
                "the live openings re-read after the derived registers were built, and each register's "
                "recorded evidence version compared with the frozen one")


def the_opening_registers_agree_with_the_final_state(final, register):
    """One opening, one width, one height, one area - in whichever register a reader happens to open."""
    by_ref = {r["OPENING_REF"]: r for r in final["OPENINGS"]}
    offenders = []
    for row in register["REGISTER"]:
        want = by_ref.get(row["OPENING_REF"])
        if want is None:
            offenders.append({"OPENING_REF": row["OPENING_REF"], "WHY": "not in the frozen state"})
            continue
        for field in ("WIDTH_M", "HEIGHT_M", "AREA_M2"):
            a, b = want[field], row.get(field)
            if (a is None) != (b is None) or (a is not None and abs(a - b) > 1e-9):
                offenders.append({"OPENING_REF": row["OPENING_REF"], "FIELD": field,
                                  "FINAL_STATE": a, "REGISTER": b,
                                  "WHY": "the register was built from an earlier evidence state"})
    return _rec("INV-27_THE_OPENING_REGISTER_AGREES_WITH_THE_FINAL_EVIDENCE", not offenders,
                {"OPENINGS": len(final["OPENINGS"])}, 0, {"OFFENDERS": offenders},
                "every published width, height and area compared field by field with the frozen state")


def dependency_impacts_are_unique(questions):
    """The impact register is a set.  Walking the graph twice must not double the work it appears to release."""
    seen = {}
    for i in questions.get("DEPENDENCY_IMPACTS", []):
        key = (i["ROOT_QUESTION_ID"], str(i["NODE"]), i["NODE_KIND"], i["EFFECT"])
        seen[key] = seen.get(key, 0) + 1
    duplicates = [{"KEY": list(k), "ROWS": n} for k, n in sorted(seen.items()) if n > 1]
    return _rec("INV-28_DEPENDENCY_IMPACTS_ARE_A_SET", not duplicates,
                {"IMPACT_ROWS": len(questions.get("DEPENDENCY_IMPACTS", [])), "DISTINCT_EDGES": len(seen),
                 "REPEATED_INSERTIONS": questions.get("REPEATED_INSERTIONS")}, 0,
                {"DUPLICATES": duplicates},
                "every impact row keyed by fact, node, node kind and effect, and the keys counted")


def evaluate_all(**checks):
    rows = [v for v in checks.values()]
    return {"CHECKS": rows, "PASSED": sum(1 for r in rows if r["PASS"]), "OF": len(rows),
            "ALL_PASS": all(r["PASS"] for r in rows)}
