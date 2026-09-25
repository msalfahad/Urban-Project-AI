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

from engine.qs_core import (admission as AD, dependency as DEP, evidence as EV, final_state as FS,
                            hosting as HO, identity, invariants, masonry as MA, openings as op,
                            questions as QN, quantities as QY, report_claims as RCL,
                            room_category as RC,
                            space_validation as SV, spaces as sp)
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
                            "THICKNESS_M": r["THICKNESS_M"],
                            "GEOMETRY_IDENTITY": r["WALL_GEOMETRY_IDENTITY"],
                            "MATERIAL_IDENTITY": r["WALL_MATERIAL_IDENTITY"],
                            "MATERIAL_EVIDENCE": r["MATERIAL_EVIDENCE"],
                            "OPENING_BASIS": r["OPENING_BASIS"],
                            "DIAGNOSTIC_ONLY_NET_AREA_M2":
                                r.get(QY.diagnostic_name("NET_AREA_M2"))})])
        for r in rows]


def run(plan, max_opening_span, drafting_resolution_m, wall_height_evidence=None, plan_window_area=None,
        closure_tolerance=1e-6, schedule_rows=(), continuation_geometry=(), cad_continuity=(),
        annotations=None, material_claims=None, material_map=None, thickness_families=None,
        wall_layers=(), subject_of=None, room_category_mapping=None, category_resolver=None,
        standard_table=None, standard_reference=None, needs_a_category=None, space_role=None,
        material_scopes=None, exclusion_evidence=None):
    """Run the engine over one plan, in the order the evidence allows.

    Admission decides what EXISTS, from what the source names, and consults no wall geometry.  Host resolution
    then asks the wall SEGMENTS which wall each opening interrupts, and only a resolved host supplies the
    opening's depth.  Wall lines are assembled after that, using the confirmed openings themselves as the
    evidence that two collinear segments are one interrupted wall.  Identity - is this wall geometry, and what
    is it made of - is settled on two independent axes before anything is measured.
    """
    comps, tol = plan["COMPONENTS"], plan["TOLERANCE_M"]
    revision = plan["REVISION"]
    segments = [c for c in comps if c.kind == KIND_WALL_BAND]

    # 1 -- existence, from what the source names.  No wall geometry is consulted here.
    population = AD.normalize_opening_population(plan["CANDIDATES"], schedule_rows, drafting_resolution_m, tol)

    # 2 -- which wall does each confirmed opening interrupt?  Answered against the segments, and allowed to
    #      fail without retracting the opening.
    hosts = HO.resolve_hosts(plan["CANDIDATES"], segments, tol)

    # the population view is refreshed after hosting: a candidate's published classification is the one it
    # leaves the whole stage with, not the one it had before its host was attempted
    population = AD.refresh(population, plan["CANDIDATES"])
    confirmed = AD.admitted_openings(plan["CANDIDATES"], tol, subject_of=subject_of, revision=revision)
    id_report = identity.assign_identity(list(comps) + list(confirmed), revision)

    # 3 -- wall lines, closed where the source proves continuity; a confirmed opening IS that proof.  This
    #      needs the openings' footprints, which hosting has supplied, and nothing about their dimensions.
    bands, gap_log = op.build_wall_lines(segments, tol, max_opening_span, openings=confirmed,
                                         continuation_geometry=continuation_geometry,
                                         cad_continuity=cad_continuity)

    # 3b - which wall LINE each resolved host belongs to.  Part of the opening's final state, because the
    #      deduction, the graph and the questions must all be told the same wall.
    op.assign_host_lines(confirmed, bands)

    # 4 -- the spaces, because room USE is evidence about an opening's dimensions and has to be gathered
    #      before the dimensions are closed, not after the quantities have been computed from them
    assembly = sp.assemble_semantic_spaces(comps, plan["BARRIERS"],
                                           [o for o in confirmed if o.rect is not None], plan["LABELS"],
                                           tol, plan["SLIVER_MIN_DIMENSION_M"], revision)
    validation = SV.validate(assembly["SPACES"], assembly["MEMBERSHIP"], assembly["SEAMS"],
                             floor=plan.get("FLOOR"))

    # 5 -- the standard by room use, applied only where nothing of higher authority answered
    categories = _resolve_room_categories(confirmed, assembly["SPACES"], tol, room_category_mapping,
                                          category_resolver, standard_table, standard_reference,
                                          needs_a_category, subject_of, revision, space_role=space_role)

    # 6 -- THE EVIDENCE BARRIER.  Every dimension this run will ever have is now resolved.  Nothing below may
    #      change what an opening says, and everything below records the version it was derived from.
    final = FS.freeze(confirmed)

    # 7 -- derived state: areas, deductions, bases, identity, dependencies, rows, questions
    register = FS.stamp(op.register_from_hosts(confirmed, bands, tol), final)
    basis = op.evaluate_opening_basis(bands, [o for o in confirmed if o.rect is not None], tol)
    ident = MA.classify_wall_identity(bands, tol, annotations=annotations, families=thickness_families,
                                      material_claims=material_claims, material_map=material_map,
                                      revision=revision, wall_layers=wall_layers,
                                      material_scopes=material_scopes, exclusion_evidence=exclusion_evidence)
    ident_by_ref = {r["COMPONENT_REF"]: r for r in ident["REGISTER"]}

    height_ok = EV.established(wall_height_evidence)
    graph = FS.stamp(DEP.build(register, bands, basis, ident_by_ref, height_ok, tol, population=population),
                     final)

    wall_rows = op.wall_band_quantities(bands, register, wall_height_evidence or {}, basis,
                                        graph["BLOCKED"], ident_by_ref) if wall_height_evidence else []

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
             "WALL_GEOMETRY_IDENTITY": r["WALL_GEOMETRY_IDENTITY"], "WHY": r["EXCLUDED_BECAUSE"],
             "REASON_KIND": r.get("EXCLUDED_REASON_KIND"),
             QY.diagnostic_name("NET_AREA_M2"): r.get(QY.diagnostic_name("NET_AREA_M2"))}
            for r in wall_rows if r["STATUS"] == EXCLUDED_NOT_MASONRY]
        publication["ROW_CATEGORIES"] = {
            "FINAL": sum(1 for r in wall_rows if r["STATUS"] == FINAL),
            "BLOCKED": sum(1 for r in wall_rows if r["STATUS"] == "BLOCKED_PENDING_ANSWERS"),
            "EXCLUDED": sum(1 for r in wall_rows if r["STATUS"] == EXCLUDED_NOT_MASONRY),
            "OF": len(wall_rows),
            "WHY_THREE": "an excluded row is not a released quantity and not an open question; reporting two "
                         "categories forces it into one of them and overstates whichever it joins"}
        publication["EXCLUSION_RULE"] = (
            "a band the drawing settles is not a wall is excluded from the masonry quantity and listed here; "
            "it does not block a subtotal, because its identity is settled")

    questions = FS.stamp(unresolved_questions(final, assembly, population, hosts, graph, basis, ident),
                         final)
    blockers = DEP.blocker_sets(graph, questions, wall_rows)

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
        "publication": invariants.blocked_never_enters_a_published_total(publication, wall_rows, "NET_AREA_M2")
        if publication else None,
        "identity_not_thickness": invariants.unusual_band_is_not_billed_on_thickness_alone(ident, wall_rows)
        if wall_rows else None,
        "material_not_shape": invariants.material_is_never_inferred_from_shape(ident, wall_rows),
        "exclusions": invariants.excluded_bands_do_not_block_a_subtotal(wall_rows, publication)
        if publication else None,
        "deduction_provenance": invariants.deductions_trace_to_width_and_height_evidence(register),
        "continuity": invariants.wall_continuity_is_proved_not_permitted(gap_log),
        "basis": invariants.opening_basis_is_decided_per_wall_line(basis, bands),
        "scope": invariants.blocking_is_limited_to_the_affected_scope(graph, wall_rows) if wall_rows else None,
        "admission": invariants.every_candidate_leaves_admission_classified(population),
        "barrier": invariants.derived_registers_share_one_evidence_version(
            final, confirmed, [register, graph, questions]),
        "coherent": invariants.the_opening_registers_agree_with_the_final_state(final, register),
        "idempotent": invariants.dependency_impacts_are_unique(questions),
        "conserved": invariants.named_source_openings_are_conserved(population, hosts, register),
        "existence": invariants.existence_is_not_retracted_by_host_failure(population, hosts),
    }
    if plan_window_area is not None:
        checks["closure"] = invariants.floor_closure(comps, plan_window_area, closure_tolerance)
    checks = {k: v for k, v in checks.items() if v is not None}


    return {
        "REVISION": revision,
        "FINAL_OPENING_STATE": final,
        "CONFIRMED_OPENINGS": confirmed,
        "EVIDENCE_VERSION": final["EVIDENCE_VERSION"],
        "EVIDENCE_BARRIER": FS.verify(final, confirmed),
        "BLOCKER_SETS": blockers,
        "OPENING_POPULATION": population,
        "HOST_REGISTER": hosts,
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
        "ROOM_CATEGORY_REGISTER": categories,
        "WALL_ROWS": wall_rows,
        "PUBLICATION": publication,
        "MEASUREMENT_OBJECTS": [m.as_dict() for m in objects],
        "MEASUREMENT_OBJECT_LIST": objects,
        "INVARIANTS": invariants.evaluate_all(**checks),
        "QUESTIONS": questions,
        "UNRESOLVED": questions["ROOT_QUESTIONS"],
    }


def _resolve_room_categories(openings, spaces, tolerance, mapping, resolver, table, reference,
                             needs_a_category, subject_of, revision, space_role=None):
    """Resolve each opening's host room and category, and let the standard answer where nothing else did."""
    needs = needs_a_category or (lambda o: o.opening_type == "WINDOW")
    rows = []
    for o in sorted(openings, key=lambda x: x.opening_ref):
        if not needs(o) or o.candidate is None:
            continue
        room = RC.resolve_host_room(o.candidate, spaces, tolerance, space_role=space_role)
        cat = RC.category_for(room, mapping or {}, resolver=resolver)
        claim = RC.standard_claim(cat, table, reference or "APPLICABLE_STANDARD")
        applied = False
        if claim is not None:
            subject = dict(o.admission.get("SUBJECT") or {})
            before = o.admission.get("HEIGHT_EVIDENCE") or {}
            after = EV.resolve("height", list(o.candidate.height_claims) + [claim], tolerance,
                               subject=subject, revision=revision)
            o.admission["HEIGHT_EVIDENCE"] = after
            if EV.established(after):
                o.height, o.height_source = after["VALUE"], after["SOURCE"]
                applied = after["REFERENCE"] == claim.reference
            del before
        rows.append({"OPENING_REF": o.opening_ref, "TYPE": o.opening_type, "FLOOR": o.floor,
                     "ROOM": room, "CATEGORY": cat,
                     "STANDARD_CLAIM": None if claim is None else claim.as_dict(),
                     "STANDARD_ANSWERED_THE_HEIGHT": applied,
                     "HEIGHT_EVIDENCE": o.admission.get("HEIGHT_EVIDENCE"),
                     "WHY": ("the standard answered because nothing of higher authority did" if applied else
                             "something of higher authority already answered, or nothing could")})
    return RC.build_register(rows)


def acceptance_document(result, metamorphic=None, narrative=None, claims=None):
    """The published document, in the shape the independent gate reads.  It contains no engine objects."""
    doc = {
        "FINAL_OPENING_STATE": result.get("FINAL_OPENING_STATE"),
        "EVIDENCE_VERSIONS": {
            "OPENING_REGISTER": (result.get("OPENING_REGISTER") or {}).get(FS.VERSION_FIELD),
            "DEPENDENCY_GRAPH": (result.get("DEPENDENCY_GRAPH") or {}).get(FS.VERSION_FIELD),
            "QUESTIONS": (result.get("QUESTIONS") or {}).get(FS.VERSION_FIELD)},
        "EVIDENCE_BARRIER": result.get("EVIDENCE_BARRIER"),
        "BLOCKER_SETS": result.get("BLOCKER_SETS"),
        "PUBLICATION": result.get("PUBLICATION"),
        "WALL_ROWS": result.get("WALL_ROWS") or [],
        "OPENING_POPULATION": result.get("OPENING_POPULATION"),
        "HOST_REGISTER": result.get("HOST_REGISTER"),
        "QUESTIONS": result.get("QUESTIONS"),
        "WALL_IDENTITY_REGISTER": (result.get("WALL_IDENTITY") or {}).get("REGISTER", []),
        "WALL_IDENTITY": result.get("WALL_IDENTITY"),
        "OPENING_REGISTER_ROWS": (result.get("OPENING_REGISTER") or {}).get("REGISTER", []),
        "GAP_LOG": result.get("GAP_LOG"),
        "OPENING_BASIS": result.get("OPENING_BASIS"),
        "WALL_IDENTITY": result.get("WALL_IDENTITY"),
        "WALL_LINE_STATUS": {
            "BLOCKED": (result.get("DEPENDENCY_GRAPH") or {}).get("BLOCKED_WALL_LINES", []),
            "NOT_BLOCKED": (result.get("DEPENDENCY_GRAPH") or {}).get("NON_BLOCKED_WALL_LINES", []),
        },
        "SPACE_VALIDATION": result.get("SPACE_VALIDATION"),
        "ROOM_CATEGORY_REGISTER": result.get("ROOM_CATEGORY_REGISTER"),
        "METAMORPHIC": metamorphic or {},
        "NARRATIVE_ASSERTIONS": narrative or default_narrative(result),
    }
    doc["REPORT_CLAIMS"] = claims if claims is not None else default_report_claims(doc)
    return doc


def default_report_claims(doc):
    """The claims a report of THIS document is allowed to make, each checked against its own register.

    Anything a reader would repeat as a number or as a cause is declared here, so that the gate re-reads it.
    Whether the prose contains a number nobody declared is a different question, and the register says so.
    """
    reg = RCL.Register(doc)
    pop = doc.get("OPENING_POPULATION") or {}
    hosts = doc.get("HOST_REGISTER") or {}
    qs = doc.get("QUESTIONS") or {}
    blockers = doc.get("BLOCKER_SETS") or {}
    final = doc.get("FINAL_OPENING_STATE") or {}
    reg.claim("C-POPULATION", "the source names {value} openings on this floor",
              "OPENING_POPULATION.NAMED_BY_THE_SOURCE_COUNT", pop.get("NAMED_BY_THE_SOURCE_COUNT"))
    reg.claim("C-PHYSICAL", "{value} physical openings were admitted",
              "OPENING_POPULATION.PHYSICAL_OPENING_COUNT", pop.get("PHYSICAL_OPENING_COUNT"))
    reg.claim("C-HOSTED", "{value} of them have a resolved host",
              "HOST_REGISTER.HOST_CONFIRMED", hosts.get("HOST_CONFIRMED"))
    reg.claim("C-QUESTIONS", "{value} unique facts remain unanswered",
              "QUESTIONS.ROOT_QUESTION_COUNT", qs.get("ROOT_QUESTION_COUNT"))
    reg.claim("C-IMPACTS", "those facts hold up {value} dependent values",
              "QUESTIONS.DEPENDENCY_IMPACT_COUNT", qs.get("DEPENDENCY_IMPACT_COUNT"))
    reg.claim("C-RELEASABLE", "{value} blocked nodes would be released by a single answer",
              "BLOCKER_SETS.NODES_RELEASED_BY_ONE_ANSWER",
              blockers.get("NODES_RELEASED_BY_ONE_ANSWER"), kind=RCL.RELEASE,
              note="a node with two blockers is released by neither answer alone")
    reg.claim("C-MULTIPLE", "{value} blocked nodes are waiting on more than one answer",
              "BLOCKER_SETS.NODES_WITH_SEVERAL_BLOCKERS",
              blockers.get("NODES_WITH_SEVERAL_BLOCKERS"), kind=RCL.RELEASE)
    reg.claim("C-HEIGHTS", "{value} openings have an established height",
              "FINAL_OPENING_STATE.HEIGHT_ESTABLISHED", final.get("HEIGHT_ESTABLISHED"))
    reg.claim("C-BARRIER", "the derived registers all describe the frozen evidence state: {value}",
              "EVIDENCE_BARRIER.UNCHANGED", (doc.get("EVIDENCE_BARRIER") or {}).get("UNCHANGED"),
              kind=RCL.STATUS)
    rows = doc.get("WALL_ROWS") or []
    reg.claim("C-ROWS", "{value} wall rows were assessed", None, len(rows), kind=RCL.COUNT,
              query=lambda d: len(d.get("WALL_ROWS") or []))
    return reg.as_dict()


def default_narrative(result):
    """The few statements a reader takes away, each tied to the register that decides it.

    A report that contradicts its own registers is the failure no internal invariant can see, so the claims
    are published as paths into the document and the gate re-reads them.
    """
    pop = result.get("OPENING_POPULATION") or {}
    hosts = result.get("HOST_REGISTER") or {}
    qs = result.get("QUESTIONS") or {}
    ident = result.get("WALL_IDENTITY") or {}
    out = [
        {"STATEMENT": "the source names this many openings",
         "REGISTER_PATH": "OPENING_POPULATION.NAMED_BY_THE_SOURCE_COUNT",
         "VALUE": pop.get("NAMED_BY_THE_SOURCE_COUNT")},
        {"STATEMENT": "this many physical openings were admitted",
         "REGISTER_PATH": "OPENING_POPULATION.PHYSICAL_OPENING_COUNT",
         "VALUE": pop.get("PHYSICAL_OPENING_COUNT")},
        {"STATEMENT": "this many of them have a resolved host",
         "REGISTER_PATH": "HOST_REGISTER.HOST_CONFIRMED", "VALUE": hosts.get("HOST_CONFIRMED")},
        {"STATEMENT": "this many unique facts remain unanswered",
         "REGISTER_PATH": "QUESTIONS.ROOT_QUESTION_COUNT", "VALUE": qs.get("ROOT_QUESTION_COUNT")},
        {"STATEMENT": "this many bands are established as masonry",
         "REGISTER_PATH": "WALL_IDENTITY.MATERIAL_COUNTS.MASONRY_CONFIRMED",
         "VALUE": (ident.get("MATERIAL_COUNTS") or {}).get("MASONRY_CONFIRMED")},
    ]
    return [a for a in out if a["VALUE"] is not None]


def unresolved_questions(final, assembly, population, hosts, graph, basis, ident):
    """Unique unanswered facts, and - separately - everything those facts hold up.

    The dimension questions are asked of the FROZEN evidence state, never of a derived field.  R6 asked them
    of AREA_M2 on the opening register, which had been serialised before the room standard answered four of
    the heights: the answer existed and the question was still on the list.  A question may exist only while
    its fact is currently unanswered, and "currently" means the final state, which is the only state a
    register built after the barrier is allowed to describe.
    """
    reg = QN.Register()

    for c in population["POPULATION"]:
        if c["CLASSIFICATION"] == AD.OPENING_CANDIDATE_UNRESOLVED:
            reg.ask("OPENING_EXISTENCE_UNRESOLVED", c["CANDIDATE_REF"],
                    f"Is {c['CANDIDATE_REF']} an opening, and of what kind?", floor=c["FLOOR"],
                    subject_kind="OPENING_CANDIDATE", evidence=c["EVIDENCE"],
                    needed_from="the drawing, a schedule row, or the owner")
    for r in population["SCHEDULE_ROWS_WITHOUT_GEOMETRY"]:
        reg.ask("SCHEDULE_ROW_WITHOUT_GEOMETRY", r["SCHEDULE_REF"],
                f"Where is scheduled opening {r['SCHEDULE_REF']} on the drawing?", floor=r["FLOOR"],
                subject_kind="SCHEDULE_ROW", evidence=[r], needed_from="the drawing")

    host_by_ref = {r["CANDIDATE_REF"]: r for r in hosts["REGISTER"]}
    for ref in hosts["HOST_UNRESOLVED_REFS"]:
        rec = host_by_ref[ref]
        qid = reg.ask("HOST_WALL_UNRESOLVED", ref, f"Which wall hosts opening {ref}?", floor=rec["FLOOR"],
                      subject_kind="PHYSICAL_OPENING", evidence=[rec],
                      needed_from="the drawing, or the owner",
                      detail={"COMPETING_HOSTS": [c["COMPONENT_REFS"] for c in rec["CANDIDATES"]],
                              "SCORES": [c["SCORE"] for c in rec["CANDIDATES"]],
                              "THE_OPENING_EXISTS": True})
        for c in rec["CANDIDATES"]:
            for node in c.get("WALL_LINES", []) or c["COMPONENT_REFS"]:
                reg.impact(qid, node, "WALL_LINE", "its net area is not final while this host is unknown")

    for o in final["OPENINGS"]:
        if o["HOST_ASSIGNMENT_STATUS"] != "HOST_ASSIGNED":
            continue                      # its host is the open fact, and that question is asked above
        if o["HEIGHT_EVIDENCE"]["STATUS"] != EV.ESTABLISHED:
            qid = reg.ask("OPENING_HEIGHT_NOT_ESTABLISHED", o["OPENING_REF"],
                          f"What is the height of opening {o['OPENING_REF']}?", floor=o["FLOOR"],
                          subject_kind="PHYSICAL_OPENING", evidence=[o["HEIGHT_EVIDENCE"]],
                          needed_from="a drawing dimension, a schedule row, or an applicable standard")
            reg.impact(qid, o["HOST_COMPONENT_REF"], "WALL_LINE",
                       "its deduction cannot be computed without this height")
        elif o["WIDTH_EVIDENCE"]["STATUS"] != EV.ESTABLISHED:
            qid = reg.ask("OPENING_WIDTH_NOT_ESTABLISHED", o["OPENING_REF"],
                          f"What is the width of opening {o['OPENING_REF']}?", floor=o["FLOOR"],
                          subject_kind="PHYSICAL_OPENING", evidence=[o["WIDTH_EVIDENCE"]],
                          needed_from="a drawing dimension, a schedule row, or an applicable standard")
            reg.impact(qid, o["HOST_COMPONENT_REF"], "WALL_LINE",
                       "its deduction cannot be computed without this width")

    asked = {r["ROOT_QUESTION_ID"] for r in reg.as_dict()["ROOT_QUESTIONS"]}
    for u in graph["UNASSOCIATED_OPENINGS"]:
        # NOT a new question wherever the same object already asked one: being unassociated with a wall is a
        # CONSEQUENCE of its host or its existence being open, not a second unanswered fact.
        existing = next((QN.root_id(k, u["OPENING_REF"]) for k in
                         ("HOST_WALL_UNRESOLVED", "OPENING_EXISTENCE_UNRESOLVED")
                         if QN.root_id(k, u["OPENING_REF"]) in asked), None)
        if existing:
            reg.impact(existing, u["FLOOR"], "EXTRACTION_COMPLETENESS",
                       "no wall line lies within this opening's own extent, so a wall may be missing from "
                       "the extraction")
        else:
            reg.ask("OPENING_NOT_ASSOCIATED_WITH_ANY_WALL", u["OPENING_REF"],
                    f"Where is the wall that opening {u['OPENING_REF']} belongs to?", floor=u["FLOOR"],
                    subject_kind="PHYSICAL_OPENING", evidence=[u], needed_from="the drawing")

    for ref, b in sorted(basis.items()):
        if b["BASIS"] != "OPENING_BASIS_UNRESOLVED":
            continue
        qid = reg.ask("OPENING_BASIS_UNRESOLVED", ref,
                      f"Does the drawn material of {ref} run through its openings?", floor=b["FLOOR"],
                      subject_kind="WALL_LINE", evidence=[b], needed_from="the drawing")
        reg.impact(qid, ref, "WALL_LINE", "its gross length is not established")

    for r in ident["REGISTER"]:
        if r["GEOMETRY_IDENTITY"] == MA.WALL_GEOMETRY_CANDIDATE:
            qid = reg.ask("WALL_GEOMETRY_NOT_ESTABLISHED", r["COMPONENT_REF"],
                          f"Is band {r['COMPONENT_REF']} a wall?", floor=r["FLOOR"],
                          subject_kind="WALL_LINE", evidence=[r], needed_from="the drawing")
            reg.impact(qid, f"SUBTOTAL::{r['THICKNESS_FAMILY_M']}", "THICKNESS_SUBTOTAL",
                       "this subtotal is larger if the band turns out to be a wall")
        # Both axes can be open at once, and they are two different facts: "is this band a wall" is answered
        # by the drawing, "what is it made of" by a specification.  Asking only the first leaves the
        # dependency graph pointing at a material question nobody asked.
        if r["MATERIAL_IDENTITY"] == MA.MATERIAL_UNKNOWN and \
                r["GEOMETRY_IDENTITY"] != MA.NON_WALL_ARTEFACT:
            # The SUBJECT is a question GROUP: the bands that share every attribute the source states about
            # them.  It is not a wall type.  R6 grouped by thickness alone and assumed one answer covered
            # every wall of that thickness - the same unsupported inference as reading material off shape,
            # made in the other direction.  Asking per line would report fifty-four questions where the
            # source has one gap; asking per thickness assumes an answer the source has not given.
            scope = r["MATERIAL_SCOPE_KEY"]
            attrs = r["MATERIAL_SCOPE_ATTRIBUTES"]
            qid = reg.ask("WALL_MATERIAL_NOT_ESTABLISHED", scope,
                          (f"What are the {attrs['THICKNESS_FAMILY_M']} m walls on {attrs['FLOOR']} drawn on "
                           f"layer {attrs['LAYER']} built from, and does that answer extend beyond them?"),
                          floor=r["FLOOR"], subject_kind="MATERIAL_SCOPE_GROUP",
                          evidence=[{"EXAMPLE_LINE": r["COMPONENT_REF"], "FLOOR": r["FLOOR"],
                                     "WHY": r["WHY_MATERIAL"],
                                     "SCOPE_ATTRIBUTES": attrs,
                                     "SOURCES_THAT_COULD_ANSWER": r["MATERIAL_EVIDENCE_SOURCES_ACCEPTED"]}],
                          needed_from="a drawing annotation, a legend, a specification, an owner input or an "
                                      "active project standard - stating which walls it covers",
                          detail={"THE_GROUP_IS_NOT_A_WALL_TYPE": r["THICKNESS_FAMILY_IS_NOT_A_WALL_TYPE"],
                                  "ANSWER_PROPAGATES": "only as far as the answering evidence states"})
            reg.impact(qid, r["COMPONENT_REF"], "WALL_LINE", "it carries no masonry quantity")
            reg.impact(qid, f"SUBTOTAL::{r['THICKNESS_FAMILY_M']}", "THICKNESS_SUBTOTAL",
                       "this subtotal is not final while the material of its walls is unstated")

    for s in assembly["SPACES"]:
        if s.status == ASSIGNED_TO_SPACE and s.label_status != SPACE_LABEL_CONFLICT:
            continue
        reg.ask("SPACE_IDENTITY_UNRESOLVED", s.room_id,
                (f"What is space {s.room_id}? " +
                 ("Two labels fall inside one continuous floor area."
                  if s.label_status == SPACE_LABEL_CONFLICT else "Its boundary evidence is mixed.")),
                floor=s.floor, subject_kind="SEMANTIC_SPACE",
                evidence=[e.as_dict() for e in s.evidence], needed_from="the drawing, or the owner")

    for c in assembly["MEMBERSHIP"]:
        if c["STATUS"] == UNRESOLVED and c["ROOM_ID"] is None and c["KIND"] == KIND_EXTERNAL:
            reg.ask("EXTERNAL_BOUNDARY_UNRESOLVED", c["COMPONENT_REF"],
                    f"Is {c['COMPONENT_REF']} external, or part of the space it meets?", floor=c["FLOOR"],
                    subject_kind="GEOMETRY_COMPONENT", evidence=c["EVIDENCE"], needed_from="the drawing")

    for node, rec in graph["BLOCKED"].items():
        for reason in rec["REASONS"]:
            ref = reason.get("OPENING_REF") or reason.get("CANDIDATE_REF") or reason.get("WALL_LINE")
            if reason["KIND"] == "WALL_MATERIAL_NOT_ESTABLISHED":
                ident_row = next((x for x in ident["REGISTER"]
                                  if x["COMPONENT_REF"] == (reason.get("WALL_LINE") or node)), None)
                if ident_row:
                    reg.impact(QN.root_id("WALL_MATERIAL_NOT_ESTABLISHED",
                                          ident_row["MATERIAL_SCOPE_KEY"]),
                               node, rec["NODE_KIND"], reason["WHY"])
                continue
            kind = {"HOST_WALL_UNRESOLVED": "HOST_WALL_UNRESOLVED",
                    "OPENING_CANDIDATE_UNRESOLVED": "OPENING_EXISTENCE_UNRESOLVED",
                    "OPENING_HEIGHT_NOT_ESTABLISHED": "OPENING_HEIGHT_NOT_ESTABLISHED",
                    "WALL_MATERIAL_NOT_ESTABLISHED": "WALL_MATERIAL_NOT_ESTABLISHED",
                    "WALL_GEOMETRY_NOT_ESTABLISHED": "WALL_GEOMETRY_NOT_ESTABLISHED",
                    "OPENING_BASIS_UNRESOLVED": "OPENING_BASIS_UNRESOLVED"}.get(reason["KIND"])
            if not kind or not ref:
                continue
            qid = QN.root_id(kind, ref)
            reg.impact(qid, node, rec["NODE_KIND"], reason["WHY"])

    return reg.as_dict()
