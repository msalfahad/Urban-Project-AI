"""P7757 supplied to the generic harness as INPUT DATA (PA05 §17).

Everything here is a fact about one project: paths, sheet index reads,
view assignments (a point inside each model-space view), layer overrides
and the owner inputs approved so far.  Nothing in engine.ingest knows any
of it.  The sheet AI roles are the recorded PA04 cold reads of the printed
sheets (pages 6 and 7 read as section-elevations with the ground storey
cut); they enter as AI_ROLE data with their evidence, never as a
deterministic fact.
"""

from __future__ import annotations

from pathlib import Path

from research.qs_wall_treatment_01 import protocol as P
from research.qs_wall_treatment_01.pa04 import common as C

OUT = Path(P.OUT_DIR)
OUT5 = OUT / "pa05"
DECODE = C.DECODE
ARCH_PDF = "data/golden/7757/inputs/P7757_DRAWINGS.pdf"
ST_PDF = "/root/.claude/uploads/93607c01-16a4-590f-af7c-1c2701c3b240/96ccda3b-ST7757.pdf"

# PA04 printed-sheet reads (AI_ROLE) for the raster architectural PDF: no text layer, so the deterministic path is UNKNOWN
ARCH_SHEET_READS = {
    "1": ("FLOOR_PLAN", "printed title GROUND FLOOR PLAN read visually; room stamps and door swings"),
    "2": ("FLOOR_PLAN", "printed title FIRST FLOOR PLAN read visually"),
    "3": ("ROOF_PLAN", "printed roof plan with parapet lines and tower"),
    "4": ("SECTION", "section A-A with level marks and cut walls"),
    "5": ("SECTION", "section B-B with level marks and cut walls"),
    "6": ("SECTION_ELEVATION", "elevation with the ground storey cut (interior visible below +5.50)"),
    "7": ("SECTION_ELEVATION", "elevation with the ground storey cut; NE side"),
    "8": ("ELEVATION", "SE elevation with arches"),
    "9": ("ELEVATION", "NW elevation with arched French windows and lattice"),
    "10": ("DETAIL", "details / schedules sheet"),
}
ST_SHEET_READS = {"1": ("STRUCTURAL_PLAN", "foundation plan"), "2": ("STRUCTURAL_PLAN", "column layout"), "3": ("STRUCTURAL_PLAN", "GF slab and beams"), "4": ("STRUCTURAL_PLAN", "FF slab and beams"),
                  "5": ("STRUCTURAL_PLAN", "roof slab and beams"), "6": ("STRUCTURAL_PLAN", "tower slab"), "7": ("STRUCTURAL_PLAN", "stair"), "8": ("DETAIL", "details"),
                  "11": ("BEAM_SCHEDULE", "continuous beam schedule (vector table, title in SHX)"), "12": ("BEAM_SCHEDULE", "beam schedule cont."), "13": ("DETAIL", "detail sheet"),
                  "14": ("DETAIL", "detail sheet"), "15": ("DETAIL", "detail sheet"), "16": ("DETAIL", "detail sheet")}

# model-space view assignments: a point inside each plan copy (PA03/PA04 established copies GF, FF = GF - 44852.65, ROOF = GF - 89705.3)
_GF_POINT = (-143000.0, -798000.0)
VIEW_ASSIGNMENTS = [
    {"POINT_MM": list(_GF_POINT), "ROLE": "FLOOR_PLAN", "STOREY": "GF", "SOURCE": "SHEET_INDEX", "AI_ROLE": "FLOOR_PLAN", "AI_EVIDENCE": "level marks ±0.00 / +0.15, room stamps, door swings"},
    {"POINT_MM": [_GF_POINT[0] + C.GF2FF, _GF_POINT[1]], "ROLE": "FLOOR_PLAN", "STOREY": "FF", "SOURCE": "SHEET_INDEX", "AI_ROLE": "FLOOR_PLAN", "AI_EVIDENCE": "plan copy at the first-floor offset; one W.C stamp"},
    {"POINT_MM": [_GF_POINT[0] - C.ROOF2GF, _GF_POINT[1]], "ROLE": "ROOF_PLAN", "STOREY": "ROOF", "SOURCE": "SHEET_INDEX", "AI_ROLE": "ROOF_PLAN", "AI_EVIDENCE": "plan copy at the roof offset; parapets and tower"},
    {"POINT_MM": [-279000.0, -798000.0], "ROLE": "SECTION", "STOREY": None, "SOURCE": "SHEET_INDEX", "AI_ROLE": "SECTION", "AI_EVIDENCE": "sections A-A / B-B cluster"},
    {"POINT_MM": [-369000.0, -798000.0], "ROLE": "ELEVATION", "STOREY": None, "SOURCE": "SHEET_INDEX", "AI_ROLE": "ELEVATION", "AI_EVIDENCE": "NW elevation cluster with arched windows"},
]


def config():
    return {
        "PROJECT_ID": "P7757", "DRAWING_FAMILY": "VILLA_KUWAIT_2026", "REVISION": "R0", "CAD_UNITS": "mm", "RULE_VERSION": "URBAN_RULES_PA05_DRAFT", "MAX_RUNTIME_S": 600,
        "SOURCES": [{"PATH": DECODE, "KIND": "CAD_DECODE_JSON", "FAMILY": "ARCHITECTURAL"}, {"PATH": ARCH_PDF, "KIND": "PDF", "FAMILY": "ARCHITECTURAL"}, {"PATH": ST_PDF, "KIND": "PDF", "FAMILY": "STRUCTURAL"}],
        "SHEET_METADATA": {ARCH_PDF: {k: {"AI_ROLE": r, "AI_EVIDENCE": e} for k, (r, e) in ARCH_SHEET_READS.items()},
                           ST_PDF: {k: {"AI_ROLE": r, "AI_EVIDENCE": e} for k, (r, e) in ST_SHEET_READS.items()}},
        "VIEW_ASSIGNMENTS": VIEW_ASSIGNMENTS,
        "LAYER_OVERRIDES": {"HIDDEN_LAYERS": ["2"], "WALL_LAYERS": ["1", "5", "W", "0"]},     # PA04: layer 2 is dashed / hidden work, not a wall
        "OWNER_INPUTS": [],
        "PRINTED_LABELS": [], "OWNER_ANCHORS": [],
    }
