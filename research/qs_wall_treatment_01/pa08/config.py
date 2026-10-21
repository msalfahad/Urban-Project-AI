"""PA08 second-villa blind validation: locations, the development-exposure registry, frozen tolerances.

Nothing here knows any project's geometry.  The exposure registry lists what the engine was developed or regressed on,
so a candidate source can be refused as independent by hash or alias before anything reads it.
"""

from __future__ import annotations

import os
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as P

OUT = Path(P.OUT_DIR)
OUT8 = OUT / os.environ.get("PA08_OUT_TAG", "pa08")
SEALED_DIR = OUT8 / "sealed"          # truth pack copies, hashed before the blind run, never on the blind allowlist
BLIND_DIR = OUT8 / "blind"            # production output of the blind run, frozen before the truth is opened

# development / regression exposure: any candidate matching one of these by hash or alias is NOT independent
DEVELOPMENT_PROJECTS = {
    "P7757": {"ROLE": "development and regression project (E1, PA01-PA07)", "PATHS": ["data/runs/cad_convert/P7757_ARCHITECTURAL.json", "data/golden/7757/inputs/P7757_DRAWINGS.pdf",
                                                                                   "/root/.claude/uploads/93607c01-16a4-590f-af7c-1c2701c3b240/96ccda3b-ST7757.pdf"]},
    "23010": {"ROLE": "earlier regression project (E1 / AE01 / SSE02 rounds; plotted PDF only)", "PATHS": ["data/golden/23010/inputs/AR-00_MAR2023.pdf"]},
}
DEVELOPMENT_ALIASES = ("7757", "P7757", "23010", "AR-00")

TOLERANCES = {
    "STRAIGHT_DEVELOPED_LENGTH": {"RULE": "max(10 mm, 0.5 %)", "ABS_MM": 10.0, "REL": 0.005},
    "CURVED_DEVELOPED_LENGTH": {"RULE": "0.5 %", "REL": 0.005},
    "OPENING_WIDTH": {"RULE": "10 mm", "ABS_MM": 10.0},
    "ROLE": {"RULE": "EXACT (wall / opening / open-edge role)"},
    "MATERIAL_PRESENT": {"RULE": "EXACT"},
    "PHYSICAL_SPACE_COUNT": {"RULE": "EXACT"},
    "COLUMN_EXPOSED_FACE": {"RULE": "EXACT for manually verified faces"},
    "FROZEN": True, "EDIT_AFTER_RESULT": "forbidden",
}
COMPARISON_CLASSES = ("EXACT_MATCH", "WITHIN_TOLERANCE", "ROLE_MISMATCH", "GEOMETRY_MISMATCH", "OPENING_MISMATCH", "SPACE_TOPOLOGY_MISMATCH", "MISSING_DETECTION", "FALSE_POSITIVE",
                      "HUMAN_REVIEW_SAFE", "NOT_COMPARABLE")
REQUIRED_CASE_KINDS = {"V1": "ordinary rectangular room", "V2": "room with a door opening", "V3": "irregular / L-shaped room", "V4": "curved wall or curved opening",
                       "V5": "open-plan or ambiguous topology condition", "V6": "column / wall junction"}
OPTIONAL_CASE_KINDS = {"V7": "glazing", "V8": "shaft", "V9": "stair", "V10": "angled wall", "V11": "double-height condition"}
