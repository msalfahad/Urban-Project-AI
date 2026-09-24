"""One pass of the engine: identity, openings to hosts, components to spaces, spaces to measurement objects.

The order matters and is the argument of the whole design.  Identity first, so everything downstream can be
matched across revisions.  Openings before wall quantities, because a wall's net area is not knowable until its
holes are known.  Spaces before finishes, because a finish belongs to a room and not to whatever fragment the
extractor happened to produce.
"""

from __future__ import annotations

from engine.qs_core import identity, invariants, openings as op, spaces as sp
from engine.qs_core.entities import (ASSIGNED_TO_SPACE, CONFIDENCE_NONE, CONFIDENCE_PROVEN, Evidence,
                                     KIND_EXTERNAL, KIND_WALL_BAND, MeasurementObject, SPACE_LABEL_CONFLICT,
                                     UNRESOLVED)

FLOOR_FINISH = "FLOOR_FINISH"
WALL_BAND_TRADE = "WALL_BAND"
FINISH_UNRESOLVED = "FINISH_CLASSIFICATION_UNRESOLVED"
FINAL = "FINAL_QUANTITY_AVAILABLE"


def _floor_objects(spaces_, revision):
    out = []
    for s in sorted(spaces_, key=lambda x: x.room_id):
        settled = s.status == ASSIGNED_TO_SPACE and s.label_status != SPACE_LABEL_CONFLICT
        out.append(MeasurementObject(
            measurement_object_id=f"MO::{FLOOR_FINISH}::{s.room_id}",
            trade=FLOOR_FINISH, unit="m2", quantity=round(s.area, 6), floor=s.floor,
            source_revision=revision, room_id=s.room_id,
            basis="the assembled space's own floor components",
            status=FINAL if settled else FINISH_UNRESOLVED,
            confidence=s.confidence,
            evidence=[Evidence("MEASURED_ON_A_SEMANTIC_SPACE",
                               {"COMPONENTS": s.component_refs, "LABEL": s.label,
                                "LABEL_STATUS": s.label_status})]))
    return out


def _wall_objects(rows, revision):
    return [MeasurementObject(
        measurement_object_id=f"MO::{WALL_BAND_TRADE}::{r['COMPONENT_REF']}",
        trade=WALL_BAND_TRADE, unit="m2", quantity=r["NET_AREA_M2"], floor=r["FLOOR"],
        source_revision=revision, component_ref=r["COMPONENT_REF"],
        basis="the band's own length and height, less the openings whose host it is",
        status=r["STATUS"],
        confidence=CONFIDENCE_PROVEN if r["STATUS"] == FINAL else CONFIDENCE_NONE,
        evidence=[Evidence("WALL_BAND_NET_OF_ITS_OWN_OPENINGS",
                           {"GROSS_M2": r["GROSS_AREA_M2"], "DEDUCTION_M2": r["OPENING_DEDUCTION_M2"],
                            "THICKNESS_M": r["THICKNESS_M"]})]) for r in rows]


def run(plan, max_opening_span, wall_height=None, plan_window_area=None, closure_tolerance=1e-6,
        wall_geometry_includes_openings=None):
    """Run the engine over one plan.

    Every input that is a judgement is an argument WITHOUT a default: the widest gap an opening can explain, and
    whether the extractor draws a wall through its own doorway, are facts about a source.  A default here would
    be a constant smuggled into the engine, which is exactly what this design exists to prevent.
    """
    if wall_height is not None and wall_geometry_includes_openings is None:
        raise ValueError("wall_geometry_includes_openings must be stated when a wall height is given: only the "
                         "extractor knows whether its wall geometry already spans its openings")
    comps, tol = plan["COMPONENTS"], plan["TOLERANCE_M"]
    revision = plan["REVISION"]
    id_report = identity.assign_identity(list(comps) + list(plan["OPENINGS"]), revision)

    segments = [c for c in comps if c.kind == KIND_WALL_BAND]
    bands = op.build_wall_lines(segments, tol, max_opening_span)
    register = op.build_opening_register(plan["OPENINGS"], bands, tol)
    assembly = sp.assemble_semantic_spaces(comps, plan["BARRIERS"], plan["OPENINGS"], plan["LABELS"],
                                           tol, plan["SLIVER_MIN_DIMENSION_M"], revision)
    wall_rows = (op.wall_band_quantities(bands, register, wall_height, wall_geometry_includes_openings)
                 if wall_height is not None else [])

    objects = _floor_objects(assembly["SPACES"], revision) + _wall_objects(wall_rows, revision)

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
    }
    if plan_window_area is not None:
        checks["closure"] = invariants.floor_closure(comps, plan_window_area, closure_tolerance)
    checks = {k: v for k, v in checks.items() if v is not None}

    return {
        "REVISION": revision,
        "WALL_LINES": [b.as_dict() for b in bands],
        "IDENTITY": id_report,
        "OPENING_REGISTER": register,
        "MEMBERSHIP_REGISTER": assembly["MEMBERSHIP"],
        "SEAM_REGISTER": assembly["SEAMS"],
        "SPACES": [s.as_dict() for s in assembly["SPACES"]],
        "SPACE_OBJECTS": assembly["SPACES"],
        "WALL_ROWS": wall_rows,
        "MEASUREMENT_OBJECTS": [m.as_dict() for m in objects],
        "MEASUREMENT_OBJECT_LIST": objects,
        "INVARIANTS": invariants.evaluate_all(**checks),
        "UNRESOLVED": unresolved_questions(register, assembly, objects),
    }


def unresolved_questions(register, assembly, objects):
    """What the engine could not settle, each with the quantity it holds up and the evidence that is missing."""
    out = []
    for o in register["REGISTER"]:
        if o["HOST_ASSIGNMENT_STATUS"] == "HOST_ASSIGNED":
            continue
        out.append({"QUESTION": f"Which wall hosts opening {o['OPENING_REF']}?",
                    "KIND": "HOST_WALL_UNRESOLVED", "FLOOR": o["FLOOR"],
                    "AFFECTED_QUANTITY_M2": o["AREA_M2"],
                    "CANDIDATES": [c["COMPONENT_REF"] for c in o["HOST_CANDIDATES"]],
                    "EVIDENCE": o["HOST_EVIDENCE"],
                    "BLOCKS": "the split of wall quantity between thicknesses on this floor"})
    for s in assembly["SPACES"]:
        if s.status == ASSIGNED_TO_SPACE and s.label_status != SPACE_LABEL_CONFLICT:
            continue
        out.append({"QUESTION": (f"What is space {s.room_id}? " +
                                 ("Two labels fall inside one continuous floor area."
                                  if s.label_status == SPACE_LABEL_CONFLICT
                                  else "Its boundary evidence is mixed.")),
                    "KIND": s.label_status if s.label_status == SPACE_LABEL_CONFLICT else "SEAM_EVIDENCE_MIXED",
                    "FLOOR": s.floor, "AFFECTED_QUANTITY_M2": round(s.area, 6),
                    "CANDIDATES": s.labels_seen, "EVIDENCE": [e.as_dict() for e in s.evidence],
                    "BLOCKS": "the floor finish of this space"})
    for c in assembly["MEMBERSHIP"]:
        if c["STATUS"] == UNRESOLVED and c["ROOM_ID"] is None and c["KIND"] == KIND_EXTERNAL:
            out.append({"QUESTION": f"Is {c['COMPONENT_REF']} external, or part of the space it meets?",
                        "KIND": "EXTERNAL_BOUNDARY_UNRESOLVED", "FLOOR": c["FLOOR"],
                        "AFFECTED_QUANTITY_M2": c["AREA_M2"], "CANDIDATES": [],
                        "EVIDENCE": c["EVIDENCE"], "BLOCKS": "whether this area is measured as internal floor"})
    return sorted(out, key=lambda q: (q["KIND"], q["QUESTION"]))
