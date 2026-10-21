"""A21_VISUAL_QS_PILOT_01 - declared and hashed before A21 reads anything.

A21 is an INDEPENDENT VISUAL QS OBSERVER. It is not a replacement for
deterministic CAD geometry and it may not touch it. The point is a second
measurement path that works the way a surveyor reads a drawing, so that A22
can later compare the two STRUCTURALLY rather than comparing totals.

A22 is specified here and has NO execution authority until A21 freezes.
"""

from __future__ import annotations

import hashlib

EXPERIMENT_ID = "A21_VISUAL_QS_PILOT_01"
EXPERIMENT_CLASS = "BLIND_INDEPENDENT_MEASUREMENT_PILOT"
PROTOCOL_VERSION = 1

THE_PURPOSE = (
    "to establish a genuinely independent QS-style measurement path: "
    "drawing -> spaces, surfaces, openings, treatments -> a shown "
    "calculation -> subtotal by room -> by floor -> by trade. Not to "
    "replace deterministic geometry with a model")

# ==================================================================
# 1. the permanent layering - A21 may not mutate any of it
# ==================================================================

DETERMINISTIC_LAYERS = ("PHYSICAL_GEOMETRY", "TOPOLOGICAL_SITES",
                        "TRADE_MEASUREMENT_REGIONS", "QUANTITIES")

A21_MAY = (
    "read architectural drawings visually",
    "identify rooms and functional areas",
    "identify likely walls, openings, stairs, facades and surfaces",
    "read printed dimensions and heights",
    "apply explicit Urban QS rules supplied to it",
    "construct an auditable human-style calculation",
    "return UNKNOWN, NEED_HEIGHT, NEED_WINDOW_SCHEDULE or HUMAN_REVIEW",
    "challenge deterministic output later, through A22",
)

A21_MAY_NOT = (
    "modify CAD geometry",
    "modify E1.4",
    "invent dimensions to make quantities work",
    "tune to a benchmark",
    "use a known final quantity as evidence",
    "silently assume a missing dimension",
    "declare itself authoritative because another agent agrees",
    "write directly to the Manager or Firebase system",
)

# ==================================================================
# 2. the pilot trades - never combined into one number
# ==================================================================

TRADES = (
    ("A_NORMAL_INTERNAL_PLASTER", "m2"),
    ("B_INTERNAL_TILE_PREP_TARTUSHA", "m2"),
    ("C_EXTERNAL_PLASTER", "m2"),
    ("D_STAIR_WALL_PLASTER", "m2"),
    ("E_STAIR_UNDERSIDE_TREATMENT", "m2"),
    ("F_OPENING_REVEALS_AND_RETURNS", "m2"),
    ("G_STEEL_CORNER_AND_EDGE_PROFILES", "lm"),
    ("H_EXTERNAL_CONTROL_JOINTS", "lm"),
)

THEY_SHARE_GEOMETRY_BUT_ARE_DIFFERENT_TREATMENTS = (
    "a surface may appear in more than one trade's geometry and still be "
    "a different QS treatment. They are never summed into one figure, and "
    "m2 is never added to lm")

# ==================================================================
# 3. the height rule
# ==================================================================

HEIGHT_PRIORITY = (
    "1_EXPLICIT_DRAWING_ELEVATION_OR_SECTION_DIMENSION",
    "2_EXPLICIT_PROJECT_SPECIFIC_HEIGHT_SETTING",
    "3_OWNER_CONFIRMED_HEIGHT",
    "4_UNKNOWN_OWNER_INPUT_REQUIRED",
)

NO_UNIVERSAL_PLASTER_HEIGHT = (
    "A21 may not assume a universal plaster height. A storey height is "
    "not a plaster height: floor buildup, beams and drops, and ceiling "
    "conditions reduce it. If the usable wall-treatment height cannot be "
    "established, the calculation for that surface STOPS and returns "
    "HEIGHT_REQUIRED. 3.00, 3.20 and 3.40 are not invented")

HEIGHT_IS_A_PARAMETER_NEVER_BAKED_IN = (
    "height enters as a named parameter. Changing it must recalculate "
    "every dependent quantity deterministically, in CODE, without the "
    "model recomputing anything and without the geometry being rebuilt")

# ==================================================================
# 4. openings
# ==================================================================

OPENING_SOURCE_PRIORITY = (
    "ACTUAL_DRAWING_OR_SCHEDULE",
    "PROJECT_SPECIFIC_OWNER_INPUT",
    "TEMPORARY_OWNER_DEFAULT",
    "UNKNOWN",
)

OPENING_FIELDS = (
    "OPENING_ID", "TYPE", "COUNT", "WIDTH", "HEIGHT", "AREA", "SOURCE",
    "ACTUAL_OR_DEFAULT", "DEDUCTION_APPLIED", "REVEAL_APPLIED",
    "CONFIDENCE_STATUS",
)

# Supplied by the owner in the directive. A default is usable ONLY when the
# actual cannot be read AND the owner authorises it, and it is always
# recorded as a default, never as a measurement.
TEMPORARY_OWNER_DEFAULTS = {
    "DEFAULT_DOOR_WIDTH_M": 1.00,
    "DEFAULT_DOOR_HEIGHT_M": 2.20,
    "DEFAULT_WINDOW_WIDTH_M": 1.50,
    "DEFAULT_WINDOW_HEIGHT_M": 1.50,
}

A_DEFAULT_IS_NOT_A_MEASUREMENT = (
    "every quantity resting on a default carries ACTUAL_OR_DEFAULT = "
    "DEFAULT and the trace says so. Real houses have many window sizes; a "
    "schedule, when supplied, must recalculate dependent quantities "
    "without redoing the room geometry")

# ==================================================================
# 5-6. deductions and reveals, never hidden
# ==================================================================

WALL_QUANTITY_FIELDS = (
    "GROSS_WALL_FACE_M2",
    "DOOR_DEDUCTION_M2",
    "WINDOW_DEDUCTION_M2",
    "OTHER_OPENING_DEDUCTION_M2",
    "NET_PRINCIPAL_WALL_FACE_M2",
    "REVEAL_RETURN_M2",
    "FINAL_TREATMENT_M2",
)

NEVER_HIDE_A_DEDUCTION = (
    "every deduction appears as its own line. A final number that cannot "
    "be decomposed into gross, deductions and reveals is not an auditable "
    "quantity")

REVEAL_RULES = (
    "openings have depth, and reveal area is kept separate from principal "
    "wall face",
    "a window's applicable reveal faces are computed separately",
    "a door's left jamb, right jamb and head are computed separately",
    "actual wall thickness is read where available; otherwise the depth "
    "is a project setting or UNKNOWN - never a constant",
)

# ==================================================================
# 7. steel profiles - a separate deterministic layer
# ==================================================================

STEEL_PROFILE_COMPONENTS = (
    "DOOR_JAMB_PROFILE_LM", "DOOR_HEAD_PROFILE_LM",
    "WINDOW_JAMB_PROFILE_LM", "WINDOW_HEAD_PROFILE_LM",
    "WINDOW_SILL_EDGE_PROFILE_LM", "EXTERNAL_CORNER_PROFILE_LM",
    "INTERNAL_EXPOSED_EDGE_PROFILE_LM", "OTHER_PROFILE_LM",
)

NOT_EVERY_OPENING_GETS_EVERY_PROFILE = (
    "applicability is decided by the Urban rule library, not assumed. A "
    "profile nobody established is not measured")

RULE_INFORMATION_IS_NOT_A_BENCHMARK_QUANTITY = (
    "the human workbook holds both. RULE INFORMATION may eventually "
    "become an Urban rule; a HUMAN BENCHMARK QUANTITY stays sealed for "
    "the whole blind pilot. The workbook is not opened during A21")

# ==================================================================
# 8. internal treatment classification
# ==================================================================

TREATMENTS = (
    ("NORMAL_BLOCK_WALL", "normal plaster"),
    ("STRUCTURAL_COLUMN", "bonding treatment, then plaster where "
                          "applicable - recorded separately, never "
                          "silently treated as blockwork"),
    ("BEAM", "NOT normal plaster under the current owner rule. Visible is "
             "not the same as plastered"),
    ("STAIR_WALL", "plaster applicable"),
    ("STAIR_UNDERSIDE", "measured separately, never buried in wall m2"),
    ("CERAMIC_OR_PORCELAIN_ROOM", "tile prep / tartusha, NOT normal "
                                  "internal plaster"),
    ("ELEVATOR_INTERIOR", "not automatically normal cement plaster. "
                          "Separate or UNKNOWN unless the specification "
                          "establishes it"),
)

TILE_PREP_ROOM_EXAMPLES = (
    "bathroom", "kitchen", "pantry", "washing or laundry room",
    "ironing room", "shower, WC and service rooms",
    "any room whose wall finish the specification makes ceramic or "
    "porcelain",
)

# ==================================================================
# 9. floor and ceiling
# ==================================================================

NO_GENERIC_CEILING_PLASTER = (
    "there is no generic ceiling plaster quantity and none is created")

FLOOR_AND_CEILING_ARE_SEPARATE = (
    "FLOOR_FINISH_AREA_M2 and CEILING_PLAN_AREA_M2 are established "
    "independently. Ceiling geometry may start from floor-plan geometry "
    "but must exclude stair openings, voids, double-height spaces, roof "
    "openings and anywhere no ceiling exists. Floor area is never blindly "
    "copied")

# ==================================================================
# 10-12. external work
# ==================================================================

EXTERNAL_RULE = (
    "external plaster is calculated facade by facade and floor by floor. "
    "Whole-house footprint perimeter multiplied by total building height "
    "is forbidden unless the geometry actually supports it. Each floor "
    "owns its own exterior envelope, and an upper floor's wall lengths "
    "are never inferred from the ground floor")

EXTERNAL_FIELDS = (
    "EXTERNAL_GROSS_WALL_FACE_M2", "EXTERNAL_OPENINGS_M2",
    "EXTERNAL_REVEALS_RETURNS_M2", "EXTERNAL_NET_PLASTER_M2",
)

PARAPET_FIELDS = (
    "ROOF_PARAPET_EXTERNAL_FACE_M2", "ROOF_PARAPET_INTERNAL_FACE_M2",
    "ROOF_PARAPET_TOP_OR_CAPPING_M2",
)

PARAPET_IS_PARAMETERISED = (
    "the owner's construction rule - about four block courses plus a "
    "concrete capping - is a PARAMETER SET, not a constant. Nothing "
    "hard-codes 0.90 m. Both faces are measured because the internal face "
    "is exposed around the roof, and corners are not double counted. "
    "Actual project geometry overrides the owner default")

CONTROL_JOINT_SOURCE_PRIORITY = (
    "DRAWING_OR_SPECIFICATION", "URBAN_CONFIRMED_RULE",
    "MANUFACTURER_OR_SYSTEM_REQUIREMENT", "OWNER_INPUT_REQUIRED",
)

CONTROL_JOINT_SPACING_IS_NEVER_INVENTED = (
    "A21 may identify facade extents, floor transitions, corners, "
    "material transitions and candidate locations. Required spacing and "
    "detail come from the sources above and from nowhere else. The result "
    "is EXTERNAL_CONTROL_JOINT_LM, never buried inside plaster m2")

# ==================================================================
# 14-15. showing the work
# ==================================================================

THE_TRACE_IS_THE_DELIVERABLE = (
    "a bare 'GROUND FLOOR PLASTER = 850.27 m2' is not an answer. Every "
    "quantity shows wall by wall, opening by opening, reveal by reveal, "
    "so a surveyor can check it in a minute")

DRILL_PATH = ("HOUSE", "FLOOR", "ROOM_OR_FACADE", "SURFACE",
              "OPENING_OR_DEDUCTION", "RULE", "SOURCE")

M2_AND_LM_ARE_NEVER_MIXED = (
    "area and length are different units and appear on different lines of "
    "every summary")

# ==================================================================
# 16. the parametric model
# ==================================================================

PARAMETERS = (
    "GROUND_PLASTER_HEIGHT", "FIRST_PLASTER_HEIGHT", "ROOF_PLASTER_HEIGHT",
    "DEFAULT_DOOR_WIDTH", "DEFAULT_DOOR_HEIGHT",
    "DEFAULT_WINDOW_WIDTH", "DEFAULT_WINDOW_HEIGHT",
    "DOOR_REVEAL_DEPTH", "WINDOW_REVEAL_DEPTH",
    "ROOF_BLOCK_COURSES", "ROOF_BLOCK_COURSE_HEIGHT", "ROOF_CAPPING_HEIGHT",
)

A21_PROPOSES_CODE_RECALCULATES = (
    "A21 may propose a parameter and must name the one it used. When a "
    "parameter changes, CODE recalculates every dependent quantity. The "
    "model does not recompute hundreds of numbers, because a model that "
    "recomputes is a model that can drift")

# ==================================================================
# 17. evidence on every input
# ==================================================================

INPUT_FIELDS = ("VALUE", "UNIT", "SOURCE", "SOURCE_LOCATION",
                "SOURCE_TYPE", "ACTUAL_OR_DEFAULT", "RULE_ID", "STATUS")

SOURCE_TYPES = (
    "DRAWING_PRINTED_DIMENSION", "DRAWING_SCALED_MEASUREMENT",
    "DRAWING_SCHEDULE", "PROJECT_SPECIFICATION", "OWNER_PROJECT_INPUT",
    "TEMPORARY_OWNER_DEFAULT", "URBAN_RULE", "VISUAL_INTERPRETATION",
)

NO_UNEXPLAINED_NUMBERS = (
    "every number carries where it came from and whether it is actual or "
    "default. A number without a source is not admitted to the trace")

# ==================================================================
# 18-19. blindness, and the right to refuse
# ==================================================================

A21_MAY_SEE = (
    "the original architectural drawing and its pages",
    "appropriate visual renderings of them",
    "printed dimensions visible on those pages",
    "the project rules explicitly supplied in the directive",
    "architectural sections and elevations needed to understand height",
)

A21_MUST_NOT_SEE = (
    "E1.4 room areas",
    "deterministic final quantities",
    "human Excel quantity totals",
    "corrected target polygons",
    "known P7757 benchmark areas",
    "previous reconciliation deltas",
    "any expected answer",
)

STATUSES = ("ESTABLISHED", "PROVISIONAL", "OWNER_INPUT_REQUIRED",
            "SOURCE_REQUIRED", "HUMAN_REVIEW", "NOT_APPLICABLE")

REFUSALS = ("HEIGHT_REQUIRED", "WINDOW_SCHEDULE_REQUIRED",
            "STAIR_GEOMETRY_REQUIRED", "FINISH_TREATMENT_REQUIRED")

AN_UNKNOWN_BEATS_A_FABRICATED_QUANTITY = (
    "A21 is never required to produce a number. A refusal with a named "
    "reason is a result, and it costs a person one look at the drawing. A "
    "fabricated quantity costs a wrong building")

# ==================================================================
# 20. visual QA
# ==================================================================

OVERLAY_RULES = (
    "every calculated room or zone gets an overlay that does not obscure "
    "the drawing",
    "identity, wall segments counted, openings deducted, openings NOT "
    "deducted and why, plaster against tile prep, stair surfaces, facade "
    "segments and unresolved sites are all shown",
    "IDs on the drawing, never prose: W01, D01, SEG-01, UNK-01",
    "the calculation trace maps every ID back to its meaning",
)

# ==================================================================
# 21-22. A22, specified now, powerless until A21 freezes
# ==================================================================

A22_HAS_NO_AUTHORITY_YET = (
    "A22 is specified architecturally and may not reconcile, approve, "
    "adjust or influence anything until A21 has produced a frozen "
    "independent result. Until then it does not run")

A22_COMPARES = (
    "IDENTITY", "GEOMETRY", "DIMENSIONS", "HEIGHT", "OPENING_COUNT",
    "OPENING_DIMENSIONS", "TREATMENT", "GROSS_QUANTITY", "DEDUCTIONS",
    "ADDITIONS", "NET_QUANTITY", "RULE", "MEASUREMENT_BASIS", "SOURCE",
)

A22_VERDICTS = (
    "STRUCTURAL_AGREEMENT", "NUMERIC_AGREEMENT_ONLY", "BASIS_DIFFERENCE",
    "SCOPE_DIFFERENCE", "OPENING_DIFFERENCE", "HEIGHT_DIFFERENCE",
    "GEOMETRY_DIFFERENCE", "TREATMENT_DIFFERENCE",
    "IDENTITY_MAPPING_DIFFERENCE", "HUMAN_MEASUREMENT_ERROR_OR_OMISSION",
    "ENGINE_GEOMETRY_ERROR", "VISUAL_QS_ERROR", "UNRESOLVED",
    "HUMAN_REVIEW_REQUIRED",
)

NUMERIC_AGREEMENT_ONLY_IS_A_WARNING = (
    "two numbers landing close together is not a pass. CAD 60.1 against "
    "A21 60.0 proves nothing if one counted 12 walls and 3 doors at 3.20 "
    "and the other 11 walls and 4 doors at 3.00. That is "
    "NUMERIC_AGREEMENT_ONLY and it goes to a human")

CONSENSUS_IS_NOT_TRUTH = (
    "three agents agreeing is not correctness. Agents share errors. "
    "Agreement reduces review burden only when the derivations are "
    "independently compatible, which is why A22 compares derivations")

# ==================================================================
# 23. the human learning loop
# ==================================================================

RESOLUTION_FIELDS = (
    "RESOLUTION_ID", "PROJECT_ID", "DRAWING_REVISION", "TRADE", "QUESTION",
    "ORIGINAL_EVIDENCE", "A21_INTERPRETATION",
    "DETERMINISTIC_INTERPRETATION", "HUMAN_DECISION", "REASON",
    "RULE_CREATED_OR_UPDATED", "RULE_VERSION",
    "PROJECT_SPECIFIC_OR_URBAN_STANDARD", "EFFECTIVE_DATE",
)

A_CORRECTION_DOES_NOT_SILENTLY_TEACH_GEOMETRY = (
    "only an explicitly approved rule may affect future projects. A "
    "one-project correction is not a company-wide rule, and nothing is "
    "learned by a model from a human answer")


def protocol_hash() -> str:
    parts = [EXPERIMENT_ID, f"V{PROTOCOL_VERSION}", EXPERIMENT_CLASS,
             THE_PURPOSE, THEY_SHARE_GEOMETRY_BUT_ARE_DIFFERENT_TREATMENTS,
             NO_UNIVERSAL_PLASTER_HEIGHT, HEIGHT_IS_A_PARAMETER_NEVER_BAKED_IN,
             A_DEFAULT_IS_NOT_A_MEASUREMENT, NEVER_HIDE_A_DEDUCTION,
             NOT_EVERY_OPENING_GETS_EVERY_PROFILE,
             RULE_INFORMATION_IS_NOT_A_BENCHMARK_QUANTITY,
             NO_GENERIC_CEILING_PLASTER, FLOOR_AND_CEILING_ARE_SEPARATE,
             EXTERNAL_RULE, PARAPET_IS_PARAMETERISED,
             CONTROL_JOINT_SPACING_IS_NEVER_INVENTED,
             THE_TRACE_IS_THE_DELIVERABLE, M2_AND_LM_ARE_NEVER_MIXED,
             A21_PROPOSES_CODE_RECALCULATES, NO_UNEXPLAINED_NUMBERS,
             AN_UNKNOWN_BEATS_A_FABRICATED_QUANTITY,
             A22_HAS_NO_AUTHORITY_YET, NUMERIC_AGREEMENT_ONLY_IS_A_WARNING,
             CONSENSUS_IS_NOT_TRUTH,
             A_CORRECTION_DOES_NOT_SILENTLY_TEACH_GEOMETRY]
    for seq in (DETERMINISTIC_LAYERS, A21_MAY, A21_MAY_NOT, HEIGHT_PRIORITY,
                OPENING_SOURCE_PRIORITY, OPENING_FIELDS,
                WALL_QUANTITY_FIELDS, REVEAL_RULES, STEEL_PROFILE_COMPONENTS,
                TILE_PREP_ROOM_EXAMPLES, EXTERNAL_FIELDS, PARAPET_FIELDS,
                CONTROL_JOINT_SOURCE_PRIORITY, DRILL_PATH, PARAMETERS,
                INPUT_FIELDS, SOURCE_TYPES, A21_MAY_SEE, A21_MUST_NOT_SEE,
                STATUSES, REFUSALS, OVERLAY_RULES, A22_COMPARES,
                A22_VERDICTS, RESOLUTION_FIELDS):
        parts += list(seq)
    parts += [f"{a}:{b}" for a, b in TRADES]
    parts += [f"{a}:{b}" for a, b in TREATMENTS]
    parts += [f"{k}={v}" for k, v in sorted(TEMPORARY_OWNER_DEFAULTS.items())]
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def record() -> dict:
    g = globals()
    keys = [k for k in g if k.isupper() and not k.startswith("_")]
    out = {"EXPERIMENT_ID": EXPERIMENT_ID,
           "PROTOCOL_VERSION": PROTOCOL_VERSION,
           "PROTOCOL_HASH": protocol_hash()}
    for k in sorted(keys):
        v = g[k]
        out[k] = list(v) if isinstance(v, tuple) else v
    return out


if __name__ == "__main__":
    import json
    print(json.dumps({"PROTOCOL_HASH": protocol_hash(),
                      "trades": len(TRADES),
                      "parameters": len(PARAMETERS),
                      "a22_verdicts": len(A22_VERDICTS)}, indent=2))
