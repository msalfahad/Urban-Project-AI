"""A21_VISUAL_TRACE_AND_SOURCE_SUFFICIENCY_01 - protocol, declared first.

The presentation question is closed. Source presentation is no longer the
primary bottleneck; what remains is source SUFFICIENCY, evidence
TRACEABILITY, and the QS inputs the drawing never contained.

This phase builds three things and reconciles nothing:

  A  a PRE-READ stage that decides which sheets a question needs, before
     any measuring reader is given anything
  B  a visual trace schema, so every claim can be pointed at on the sheet
     and projected back to the original PDF page
  C  a parameter layer, so an owner-supplied height is never recorded as
     drawing evidence

    python3 -m research.a21_trace_sufficiency_01.protocol
"""

from __future__ import annotations

import hashlib
from pathlib import Path

PHASE_ID = "A21_VISUAL_TRACE_AND_SOURCE_SUFFICIENCY_01"

# ==================================================================
# WHAT IS CARRIED IN FROM THE CLOSED EXPERIMENTS
# ==================================================================

ACCEPTED_CONCLUSION = (
    "source presentation is no longer the primary bottleneck",
    "the remaining limits are source sufficiency, evidence traceability, "
    "and missing project / QS inputs",
    "no third presentation run is authorised",
)

PRESERVED_UNTOUCHED = (
    "A21_SOURCE_PRESENTATION_BASELINE and every artifact of it",
    "A21_SOURCE_PRESENTATION_IMPROVED and every artifact of it",
    "the frozen protocol, selection rule and decisions hashes",
    "DEV-01, DEV-02 and DEV-03 exactly as written",
)

THE_FINDING_THAT_MUST_SURVIVE = (
    "better pixels do not create a missing plaster height. Do not continue "
    "trying to infer a plaster height visually when the source does not "
    "establish one. If the owner later supplies 3.20 m it is recorded as "
    "SOURCE_TYPE = OWNER_PROJECT_INPUT, never as a drawing-derived height, "
    "and that distinction must survive into A22")

NOT_IN_THIS_PHASE = (
    "no A22", "no Excel", "no benchmark quantities",
    "no E1.4 quantities exposed to A21", "no E1.5", "no E2",
    "no BOQ", "no reconciliation of any quantity",
)

SUCCESS_IS_NOT_QUANTITY_ACCURACY = (
    "nothing here is judged on how close a number is to anything. It is "
    "judged on whether a claim can be found on the drawing, whether a "
    "printed dimension can be tied to the geometry it supports, whether a "
    "processed-image coordinate maps back to the original page, and "
    "whether a default can still be mistaken for evidence")

SUCCESS_CRITERIA = {
    "A": "every measured claim can be highlighted on the drawing",
    "B": "every printed dimension can be linked to the geometry it supports",
    "C": "every processed-image coordinate maps back to the original PDF page",
    "D": "a case cannot access undeclared sources",
    "E": "an incomplete packet fails BEFORE A21 rather than making A21 hunt",
    "F": "changing a QS parameter changes the arithmetic without changing "
         "the visual interpretation",
    "G": "no synthetic or default input is mislabelled as drawing evidence",
}

# ==================================================================
# PART A - SOURCE SUFFICIENCY
# ==================================================================

WHY_A_PRE_READ_STAGE_EXISTS = (
    "DEV-02 and DEV-03 showed the same failure twice: a case legitimately "
    "needed a sheet its packet did not declare, and the readers went and "
    "got it. Four readings of CASE-5 and four of CASE-6 did this. The "
    "readers were not misbehaving - the packets could not answer their "
    "own questions")

THE_THREE_WRONG_FIXES = (
    "allowing unrestricted browsing - then blindness means nothing",
    "forcing the reader to stay inside an incomplete packet - then the "
    "refusal is an artefact of my packet, not of the drawing",
    "adding sheets after seeing the answer - then the packet is fitted "
    "to the result",
)

THE_PRE_READ_QUESTION = (
    "which architectural source sheets are required to answer this "
    "measurement question?")

PRE_READ_MAY_INSPECT = (
    "the drawing index", "floor plans", "section markers",
    "elevation markers", "sheet titles", "cross references",
)
PRE_READ_MUST_NOT_INSPECT = (
    "A21 results", "E1.4 quantity results", "Excel quantities",
    "benchmark answers",
)

WHY_IT_IS_A_READER_AND_NOT_CODE = (
    "the source is a 400 DPI scan with zero extractable characters, and "
    "the CAD model space carries no per-sheet titles. A section marker on "
    "a raster cannot be found deterministically without OCR, which this "
    "system does not have and will not pretend to have. So the pre-read "
    "stage READS - and is sealed exactly like a measuring reader, from a "
    "directory that contains sheets and nothing else")

CASE_SOURCE_REQUIREMENT_FIELDS = (
    "CASE_ID", "QUESTION", "PRIMARY_PLAN", "REQUIRED_SECTIONS",
    "REQUIRED_ELEVATIONS", "REQUIRED_DETAILS", "REQUIRED_SCHEDULES",
    "OPTIONAL_CONTEXT", "MISSING_SOURCE", "WHY_EACH_SOURCE_IS_REQUIRED",
)

SOURCE_SET_INCOMPLETE = (
    "if a required source does not exist in the drawing set, the case "
    "fails HERE, before any measuring reader is started. The reader is "
    "never sent hunting and is never asked a question its packet cannot "
    "answer")

THE_SANDBOX_RULE = (
    "the measuring sandbox is built from the FROZEN requirement list and "
    "contains nothing else. A reader cannot traverse into another case's "
    "directory because no undeclared file is mounted at all")

# ==================================================================
# PART B - VISUAL TRACE
# ==================================================================

TRACE_FIELDS = (
    "TRACE_ID", "CASE_ID", "SHEET_ID", "SOURCE_FILE_HASH",
    "SOURCE_PRESENTATION_HASH", "SOURCE_COORDINATE_SYSTEM",
    "ORIGINAL_PDF_PAGE",
)
TRACE_GEOMETRY_FIELDS = (
    "PIXEL_BBOX", "PIXEL_POINT", "PIXEL_POLYLINE", "PIXEL_POLYGON",
)
TRACE_TRANSFORM_FIELD = "ORIGINAL_PAGE_COORDINATE_TRANSFORM"

THE_TRACE_MUST_SURVIVE = ("rotation", "crop", "trim", "downscale")

CLAIM_TYPES = (
    "ROOM_IDENTITY", "WALL_SEGMENT", "OPEN_EDGE", "DOOR", "WINDOW",
    "GLAZING", "COLUMN", "STAIR", "PARAPET", "BALUSTRADE",
    "PRINTED_DIMENSION", "LEVEL_MARK", "HEIGHT_DIMENSION",
    "SECTION_REFERENCE", "ELEVATION_REFERENCE", "UNRESOLVED_FEATURE",
)

DIMENSION_AND_OBJECT_ARE_SEPARATE_EVIDENCE = (
    "the dimension TEXT and the thing it measures are two traces, linked "
    "by SUPPORTED_BY. '558 appears somewhere near the wall' is not a "
    "trace. A correct number attached to the wrong wall is not acceptable")

PRINTED_DIMENSION_FIELDS = (
    "TEXT", "UNIT_INTERPRETATION", "VALUE_M", "TEXT_BBOX",
    "DIMENSION_LINE_TRACE", "EXTENSION_LINE_A", "EXTENSION_LINE_B",
)

OVERLAY_RULES = (
    "overlays are DERIVED from the stored trace coordinates",
    "a feature is never redrawn afterwards because the text says it exists",
    "short ids on the drawing: SEG-01, D-01, W-01, DIM-01, UNK-01",
    "line style plus label, never colour alone",
    "the reviewer can match overlay <-> trace register <-> calculation "
    "line <-> original drawing",
)

# trace confidence is not quantity confidence
TRACE_STATUSES = ("TRACE_ESTABLISHED", "TRACE_PROVISIONAL",
                  "TRACE_AMBIGUOUS", "TRACE_NOT_ESTABLISHED")
VISUAL_TRACE_STATUS_IS_NOT_MEASUREMENT_STATUS = (
    "A21 may be certain it has highlighted the right wall while the "
    "wall's length is unknown; or read a printed dimension perfectly "
    "while ownership of that dimension is ambiguous. The two statuses are "
    "reported side by side and never collapsed")
NO_NUMERIC_CONFIDENCE_SCORE_YET = True

# ==================================================================
# PART C - PARAMETRIC QS INPUTS
# ==================================================================

THE_BOUNDARY_THE_EXPERIMENTS_ESTABLISHED = (
    "the drawing often establishes geometry and does not establish every "
    "construction or QS input")

PARAMETER_FIELDS = (
    "PARAMETER_ID", "VALUE", "UNIT", "SOURCE_TYPE", "SOURCE_REFERENCE",
    "PROJECT_SPECIFIC", "OWNER_CONFIRMED", "DEFAULT_OR_ACTUAL", "VERSION",
    "STATUS",
)
PARAMETER_SOURCE_TYPES = (
    "DRAWING", "SPECIFICATION", "OWNER_PROJECT_INPUT", "URBAN_STANDARD",
    "TEMPORARY_DEFAULT", "CONTRACTOR_RULE", "UNKNOWN",
)

THREE_QUANTITY_STATES = {
    "SOURCE_ESTABLISHED_QUANTITY":
        "every required input established from permitted project sources",
    "OWNER_PARAMETRIC_QUANTITY":
        "geometry from the project source, one or more QS inputs supplied "
        "by the owner or project. A legitimate project quantity, but not a "
        "drawing-derived one",
    "PROVISIONAL_DEFAULT_QUANTITY":
        "one or more inputs use a temporary default such as door 1.00 x "
        "2.20 or window 1.50 x 1.50. It must stay visibly provisional",
}
THEY_ARE_NEVER_MIXED = True

PARAMETRIC_RECALCULATION = (
    "A21 supplies wall length, opening identity, opening dimensions where "
    "available, surface treatment and trace evidence. Deterministic code "
    "does the arithmetic. Change PLASTER_HEIGHT from 3.20 to 3.30 and "
    "every dependent quantity recalculates without the visual "
    "interpretation being rerun - A21 reruns only when the geometry or "
    "the evidence changes")

# ==================================================================
# THE PILOT SUBSET - mechanical, frozen before any trace is generated
# ==================================================================

REQUIRED_CHARACTERISTICS = (
    "ORDINARY_WALL_WITH_PRINTED_DIMENSION",
    "AN_OPENING",
    "AN_AMBIGUOUS_OR_OPEN_BOUNDARY",
    "A_STAIR_OR_VERTICAL_CONDITION",
    "A_PARAPET_BALUSTRADE_DISTINCTION",
)

SUBSET_RULE = (
    "each characteristic is assigned to a case by a rule fixed BEFORE any "
    "trace is generated, using only (a) the case's own declared subject, "
    "which predates the baseline, and (b) the frozen deterministic E1.4 "
    "boundary-chain composition - the same channel the original pilot "
    "selection was permitted to use. No A21 answer is read, and no case "
    "is chosen because A21 did well on it")

SUBSET_ASSIGNMENT_RULE = {
    "ORDINARY_WALL_WITH_PRINTED_DIMENSION":
        "the room case with the HIGHEST material-wall-face fraction in "
        "the frozen E1.4 chain",
    "AN_OPENING":
        "the room case with DOOR_PORTAL count greater than zero",
    "AN_AMBIGUOUS_OR_OPEN_BOUNDARY":
        "the room case with the HIGHEST non-material fraction in the "
        "frozen E1.4 chain",
    "A_STAIR_OR_VERTICAL_CONDITION": "the case whose declared subject is "
                                     "the stair",
    "A_PARAPET_BALUSTRADE_DISTINCTION": "the case whose declared subject "
                                        "is the parapet",
}

WHY_CASE_5_FALLS_OUT = (
    "no characteristic selects it. That is worth saying out loud, because "
    "CASE-5 is the only case in twenty-four readings that produced an "
    "established plaster height. The mechanical rule drops the "
    "best-performing case, which is the opposite of cherry-picking")

A_HONEST_NOTE_ON_THE_OPENNESS_RULE = (
    "the frozen E1.4 chain does NOT agree with the visual readings about "
    "which room is open: it records the RECEPTION candidate as 26 of 29 "
    "material wall face, while four independent readings say that room "
    "has no wall on three of its sides. The rule is applied as written "
    "anyway, because changing it after noticing the disagreement would be "
    "selecting on an answer. The disagreement itself is recorded as an "
    "architecture finding - it is exactly the kind of thing a visual "
    "trace exists to settle, and it is NOT a quantity comparison and NOT "
    "a reconciliation")

# ==================================================================
# DELIVERABLES
# ==================================================================

DELIVERABLES = (
    "SOURCE_SUFFICIENCY_PROTOCOL", "CASE_SOURCE_REQUIREMENTS",
    "CASE_SANDBOX_MANIFESTS", "VISUAL_TRACE_SCHEMA", "TRACE_REGISTER",
    "OVERLAY_IMAGES", "ORIGINAL_SOURCE_MAPPING_TEST", "PARAMETER_SCHEMA",
    "PARAMETRIC_RECALCULATION_TEST", "FAILURE_CASES",
    "ARCHITECTURE_FINDINGS", "FREEZE",
)


def protocol_hash() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


if __name__ == "__main__":
    import json
    print(json.dumps({
        "PHASE_ID": PHASE_ID,
        "PROTOCOL_HASH": protocol_hash(),
        "DELIVERABLES": len(DELIVERABLES),
        "SUCCESS_IS_NOT_QUANTITY_ACCURACY": True,
        "NOT_IN_THIS_PHASE": list(NOT_IN_THIS_PHASE),
    }, indent=2))
