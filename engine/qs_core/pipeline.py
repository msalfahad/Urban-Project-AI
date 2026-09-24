"""One pass of the engine, in the order the evidence allows.

The order is the argument of the whole design, and this round changed it in three places.  Openings are now
ADMITTED before they are hosted, because "which wall is this in" is unanswerable for something that is not an
opening.  Wall lines are assembled only where the source proves continuity, because a wall invented across a gap
carries every quantity on it into the bill.  And identity - is this band masonry at all - is settled before
anything measures it, because a thickness is a measurement and not a name.

What comes out is two separate things that this engine no longer mixes: quantities that are finished, and
questions that are not.
"""

from __future__ import annotations

from engine.qs_core import (admission as AD, dependency as DEP, evidence as EV, identity, invariants,
                            masonry as MA, openings as op, quantities as QY, space_validation as SV,
                            spaces as sp)
from engine.qs_core.entities import (ASSIGNED_TO_SPACE, CONFIDENCE_NONE, CONFIDENCE_PROVEN, Evidence,
                                     KIND_EXTERNAL, KIND_WALL_BAND, MeasurementObject, SPACE_LABEL_CONFLICT,
                                     UNRESOLVED)

FLOOR_FINISH = "FLOOR_FINISH"
WALL_BAND_TRADE = "MASONRY_WALL"
FINISH_UNRESOLVED = "FINISH_CLASSIFICATION_UNRESOLVED"
EXCLUDED_NOT_MASONRY = "EXCLUDED_NOT_MASONRY"
FINAL = QY.FINAL


def _floor_objects(spaces_, revision):
    out = []
    for s in sorted(spaces_, key=lambda x: x.room_id):
        settled = s.status == ASSIGNED_TO_SPACE and s.label_status != SPACE_LABEL_CONFLICT
        out.append(MeasurementObject(
            measurement_object_id=f"MO::{FLOOR_FINISH}::{s.room_id}",
            trade=FLOOR_FINISH, unit="m2", quantity=round(s.area, 6) if settled else None, floor=s.floor,
            source_revision=revision, room_id=s.room_id,
            basis="the assembled space's own floor components",
            status=FINAL if settled else FINISH_UNRESOLVED,
            confidence=s.confidence,
            evidence=[Evidence("MEASURED_ON_A_SEMANTIC_SPACE",
                               {"COMPONENTS": s.component_refs, "LABEL": s.label,
                                "LABEL_STATUS": s.label_status,
                                "DIAGNOSTIC_ONLY_AREA_M2": None if settled else round(s.area, 6)})]))
    return out


def _wall_objects(rows, revision):
    return [MeasurementObject(
        measurement_object_id=f"MO::{WALL_BAND_TRADE}::{r['COMPONENT_REF']}",
        trade=WALL_BAND_TRADE, unit="m2", quantity=r["NET_AREA_M2"], floor=r["FLOOR"],
        source_revision=revision, component_ref=r["COMPONENT_REF"],
        basis="the line's own length on its evidenced basis and height, less the openings whose host it is",
        status=r["STATUS"],
        confidence=CONFIDENCE_PROVEN if r["STATUS"] == FINAL else CONFIDENCE_NONE,
        evidence=[Evidence("WALL_LINE_NET_OF_ITS_OWN_OPENINGS",
                           {"GROSS_M2": r["GROSS_AREA_M2"], "DEDUCTION_M2": r["OPENING_DEDUCTION_M2"],
                            "THICKNESS_M": r["THICKNESS_M"], "IDENTITY": r["WALL_IDENTITY"],
                            "OPENING_BASIS": r["OPENING_BASIS"],
                            "DIAGNOSTIC_ONLY_NET_AREA_M2":
                                r.get(QY.diagnostic_name("NET_AREA_M2"))})])
        for r in rows]


def run(plan, max_opening_span, drafting_resolution_m, wall_height_evidence=None, plan_window_area=None,
        closure_tolerance=1e-6, schedule_rows=(), continuation_geometry=(), cad_continuity=(),
        annotations=None, masonry_materials=(), thickness_families=None):
    """Run the engine over one plan.

    Every input that is a judgement about a SOURCE is an argument without a default: the widest gap an opening
    can explain, and the finest distance the drawing was authored to.  A default for either would be a constant
    smuggled into the engine, which is what this design exists to prevent.  Whether a wall's drawn geometry
    spans its openings used to be a third such argument; it is now measured, line by line, from the drawing.
    """
    comps, tol = plan["COMPONENTS"], plan["TOLERANCE_M"]
    revision = plan["REVISION"]
    segments = [c for c in comps if c.kind == KIND_WALL_BAND]

    # 1 -- admission: what is actually an opening, before anything asks which wall it is in
    population = AD.normalize_opening_population(plan["CANDIDATES"], segments, schedule_rows,
                                                 drafting_resolution_m, tol)
    confirmed = AD.admitted_openings(plan["CANDIDATES"], tol)

    id_report = identity.assign_identity(list(comps) + list(confirmed), revision)

    # 2 -- wall lines, closed only where the source proves continuity
    bands, gap_log = op.build_wall_lines(segments, tol, max_opening_span, openings=confirmed,
                                         continuation_geometry=continuation_geometry,
                                         cad_continuity=cad_continuity)

    # 3 -- one host or none, then the basis of each line, then what each line IS
    register = op.build_opening_register(confirmed, bands, tol)
    basis = op.evaluate_opening_basis(bands, confirmed, tol)
    ident = MA.classify_wall_identity(bands, tol, annotations=annotations,
                                      masonry_materials=masonry_materials, families=thickness_families)
    ident_by_ref = {r["COMPONENT_REF"]: r for r in ident["REGISTER"]}

    # 4 -- what each open question actually holds up
    height_ok = EV.established(wall_height_evidence)
    graph = DEP.build(register, bands, basis, ident_by_ref, height_ok, tol, population=population)

    wall_rows = op.wall_band_quantities(bands, register, wall_height_evidence or {}, basis,
                                        graph["BLOCKED"], ident_by_ref) if wall_height_evidence else []

    assembly = sp.assemble_semantic_spaces(comps, plan["BARRIERS"], confirmed, plan["LABELS"],
                                           tol, plan["SLIVER_MIN_DIMENSION_M"], revision)
    validation = SV.validate(assembly["SPACES"], assembly["MEMBERSHIP"], assembly["SEAMS"],
                             floor=plan.get("FLOOR"))

    objects = _floor_objects(assembly["SPACES"], revision) + _wall_objects(wall_rows, revision)

    masonry_rows = [r for r in wall_rows if r["STATUS"] != EXCLUDED_NOT_MASONRY]
    publication = QY.publish(
        masonry_rows, lambda r: r["THICKNESS_FAMILY_M"],
        "NET_AREA_M2", "m2", "masonry wall area by thickness",
        blocked_groups={None if k == "None" else float(k):
                        {"KIND": "SUBTOTAL_BLOCKED", "WHY": graph["BLOCKED"][f"SUBTOTAL::{k}"]["REASONS"][0]
                         ["WHY"], "DETAIL": graph["BLOCKED"][f"SUBTOTAL::{k}"]["REASONS"]}
                        for k in graph["SUBTOTALS"]
                        if f"SUBTOTAL::{k}" in graph["BLOCKED"]}) if wall_rows else None
    if publication is not None:
        publication["EXCLUDED_ROWS"] = [
            {"COMPONENT_REF": r["COMPONENT_REF"], "FLOOR": r["FLOOR"], "THICKNESS_M": r["THICKNESS_M"],
             "WALL_IDENTITY": r["WALL_IDENTITY"], "WHY": r["EXCLUDED_BECAUSE"],
             QY.diagnostic_name("NET_AREA_M2"): r.get(QY.diagnostic_name("NET_AREA_M2"))}
            for r in wall_rows if r["STATUS"] == EXCLUDED_NOT_MASONRY]
        publication["EXCLUSION_RULE"] = (
            "a band established to be something other than masonry is excluded from the masonry quantity and "
            "listed here; it does not block a subtotal, because its identity is settled")

    checks = {
        "one_host": invariants.one_host_per_opening(register),
        "reconcile": invariants.deductions_reconcile(register, wall_rows, 1e-9) if wall_rows else None,
        "unresolved": invariants.unresolved_never_allocated(register, wall_rows, 1e-9) if wall_rows else None,
        "band_by_band": invariants.deductions_match_band_by_band(register, wall_rows, 1e-9) if wall_rows
        else None,
        "no_wall_floor": invariants.no_wall_material_as_floor(assembly["MEMBERSHIP"]),
        "one_state": invariants.every_component_resolved_once(assembly["MEMBERSHIP"]),
        "space_area": invariants.space_areas_match_members(assembly["SPACES"], comps, 1e-9),
        "order": invariants.identity_is_order_independent(list(comps), revision),
        "pricing": invariants.pricing_fields_separate_and_empty(objects),
        "continuous": invariants.continuous_floor_is_one_space(assembly["SEAMS"], assembly["MEMBERSHIP"]),
        "ambiguity": invariants.ambiguous_hosts_are_surfaced(register, op.DECISIVE_MARGIN),
        "publication": invariants.blocked_never_enters_a_published_total(publication, wall_rows, "NET_AREA_M2")
        if publication else None,
        "identity_not_thickness": invariants.unusual_band_is_not_billed_on_thickness_alone(ident, wall_rows)
        if wall_rows else None,
        "exclusions": invariants.excluded_bands_do_not_block_a_subtotal(wall_rows, publication)
        if publication else None,
        "deduction_provenance": invariants.deductions_trace_to_width_and_height_evidence(register),
        "continuity": invariants.wall_continuity_is_proved_not_permitted(gap_log),
        "basis": invariants.opening_basis_is_decided_per_wall_line(basis, bands),
        "scope": invariants.blocking_is_limited_to_the_affected_scope(graph, wall_rows) if wall_rows else None,
        "admission": invariants.every_candidate_leaves_admission_classified(population),
    }
    if plan_window_area is not None:
        checks["closure"] = invariants.floor_closure(comps, plan_window_area, closure_tolerance)
    checks = {k: v for k, v in checks.items() if v is not None}

    return {
        "REVISION": revision,
        "OPENING_POPULATION": population,
        "GAP_LOG": gap_log,
        "WALL_LINES": [b.as_dict() for b in bands],
        "WALL_LINE_OBJECTS": bands,
        "OPENING_BASIS": basis,
        "WALL_IDENTITY": ident,
        "DEPENDENCY_GRAPH": graph,
        "IDENTITY": id_report,
        "OPENING_REGISTER": register,
        "MEMBERSHIP_REGISTER": assembly["MEMBERSHIP"],
        "SEAM_REGISTER": assembly["SEAMS"],
        "SPACES": [s.as_dict() for s in assembly["SPACES"]],
        "SPACE_OBJECTS": assembly["SPACES"],
        "SPACE_VALIDATION": validation,
        "WALL_ROWS": wall_rows,
        "PUBLICATION": publication,
        "MEASUREMENT_OBJECTS": [m.as_dict() for m in objects],
        "MEASUREMENT_OBJECT_LIST": objects,
        "INVARIANTS": invariants.evaluate_all(**checks),
        "UNRESOLVED": unresolved_questions(register, assembly, population, graph, basis, ident),
    }


def acceptance_document(result, metamorphic=None):
    """The published document, in the shape the independent gate reads.  It contains no engine objects."""
    return {
        "PUBLICATION": result.get("PUBLICATION"),
        "WALL_ROWS": result.get("WALL_ROWS") or [],
        "OPENING_POPULATION": result.get("OPENING_POPULATION"),
        "OPENING_REGISTER_ROWS": (result.get("OPENING_REGISTER") or {}).get("REGISTER", []),
        "GAP_LOG": result.get("GAP_LOG"),
        "OPENING_BASIS": result.get("OPENING_BASIS"),
        "WALL_IDENTITY": result.get("WALL_IDENTITY"),
        "SPACE_VALIDATION": result.get("SPACE_VALIDATION"),
        "METAMORPHIC": metamorphic or {},
    }


def unresolved_questions(register, assembly, population, graph, basis, ident):
    """What the engine could not settle, each with the quantity it holds up and the evidence that is missing."""
    out = []
    for c in population["POPULATION"]:
        if c["CLASSIFICATION"] != AD.OPENING_CANDIDATE_UNRESOLVED:
            continue
        out.append({"QUESTION": f"Is candidate {c['CANDIDATE_REF']} an opening?",
                    "KIND": AD.OPENING_CANDIDATE_UNRESOLVED, "FLOOR": c["FLOOR"],
                    "AFFECTED_QUANTITY_M2": None, "CANDIDATES": [],
                    "EVIDENCE": c["EVIDENCE"],
                    "BLOCKS": "whether anything is deducted here at all"})
    for r in population["SCHEDULE_ROWS_WITHOUT_GEOMETRY"]:
        out.append({"QUESTION": f"Where is scheduled opening {r['SCHEDULE_REF']} on the drawing?",
                    "KIND": "SCHEDULE_ROW_WITHOUT_GEOMETRY", "FLOOR": r["FLOOR"],
                    "AFFECTED_QUANTITY_M2": None, "CANDIDATES": [], "EVIDENCE": [r],
                    "BLOCKS": "the completeness of the opening population"})
    for o in register["REGISTER"]:
        if o["HOST_ASSIGNMENT_STATUS"] == "HOST_ASSIGNED":
            if o["AREA_M2"] is None:
                out.append({"QUESTION": f"What is the height of opening {o['OPENING_REF']}?",
                            "KIND": "OPENING_HEIGHT_NOT_ESTABLISHED", "FLOOR": o["FLOOR"],
                            "AFFECTED_QUANTITY_M2": None,
                            "CANDIDATES": [o["HOST_COMPONENT_REF"]],
                            "EVIDENCE": [(o.get("ADMISSION") or {}).get("HEIGHT_EVIDENCE")],
                            "BLOCKS": f"the net area of wall line {o['HOST_COMPONENT_REF']}"})
            continue
        out.append({"QUESTION": f"Which wall hosts opening {o['OPENING_REF']}?",
                    "KIND": "HOST_WALL_UNRESOLVED", "FLOOR": o["FLOOR"],
                    "AFFECTED_QUANTITY_M2": o["AREA_M2"],
                    "CANDIDATES": [c["COMPONENT_REF"] for c in o["HOST_CANDIDATES"]],
                    "EVIDENCE": o["HOST_EVIDENCE"],
                    "BLOCKS": ("the net area of " +
                               ", ".join(c["COMPONENT_REF"] for c in o["HOST_CANDIDATES"])
                               if o["HOST_CANDIDATES"] else "nothing that can be identified")})
    for u in graph["UNASSOCIATED_OPENINGS"]:
        out.append({"QUESTION": f"Does opening {u['OPENING_REF']} exist, and in which wall?",
                    "KIND": u["KIND"], "FLOOR": u["FLOOR"], "AFFECTED_QUANTITY_M2": u["AREA_M2"],
                    "CANDIDATES": [], "EVIDENCE": [u],
                    "BLOCKS": "nothing that can be identified; recorded as a completeness risk"})
    for ref, b in sorted(basis.items()):
        if b["BASIS"] != "OPENING_BASIS_UNRESOLVED":
            continue
        out.append({"QUESTION": f"Does the drawn material of {ref} run through its openings?",
                    "KIND": "OPENING_BASIS_UNRESOLVED", "FLOOR": b["FLOOR"], "AFFECTED_QUANTITY_M2": None,
                    "CANDIDATES": [t["OPENING_REF"] for t in b["OPENINGS_TESTED"]], "EVIDENCE": [b],
                    "BLOCKS": f"the gross length of wall line {ref}"})
    for r in ident["REGISTER"]:
        if r["IDENTITY"] != MA.WALL_IDENTITY_UNRESOLVED:
            continue
        out.append({"QUESTION": f"What is band {r['COMPONENT_REF']}, {r['THICKNESS_M']} m thick?",
                    "KIND": MA.WALL_IDENTITY_UNRESOLVED, "FLOOR": r["FLOOR"], "AFFECTED_QUANTITY_M2": None,
                    "CANDIDATES": [], "EVIDENCE": [r],
                    "BLOCKS": f"the masonry subtotal at {r['THICKNESS_M']} m"})
    for s in assembly["SPACES"]:
        if s.status == ASSIGNED_TO_SPACE and s.label_status != SPACE_LABEL_CONFLICT:
            continue
        out.append({"QUESTION": (f"What is space {s.room_id}? " +
                                 ("Two labels fall inside one continuous floor area."
                                  if s.label_status == SPACE_LABEL_CONFLICT
                                  else "Its boundary evidence is mixed.")),
                    "KIND": s.label_status if s.label_status == SPACE_LABEL_CONFLICT else "SEAM_EVIDENCE_MIXED",
                    "FLOOR": s.floor, "AFFECTED_QUANTITY_M2": None,
                    "CANDIDATES": s.labels_seen, "EVIDENCE": [e.as_dict() for e in s.evidence],
                    "BLOCKS": "the floor finish of this space"})
    for c in assembly["MEMBERSHIP"]:
        if c["STATUS"] == UNRESOLVED and c["ROOM_ID"] is None and c["KIND"] == KIND_EXTERNAL:
            out.append({"QUESTION": f"Is {c['COMPONENT_REF']} external, or part of the space it meets?",
                        "KIND": "EXTERNAL_BOUNDARY_UNRESOLVED", "FLOOR": c["FLOOR"],
                        "AFFECTED_QUANTITY_M2": None, "CANDIDATES": [],
                        "EVIDENCE": c["EVIDENCE"], "BLOCKS": "whether this area is measured as internal floor"})
    return sorted(out, key=lambda q: (q["KIND"], q["QUESTION"]))
