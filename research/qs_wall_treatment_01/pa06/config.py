"""P7757 as input data for the PA06 pipeline (regression project, not the design target).

Supervised configuration: sources, the recorded PA04 visual sheet reads (AI_ROLE data with provenance), the
approved owner parameter registry, no layer overrides (roles are discovered), no view assignments (storeys
come from the storey register).  The blind configuration (blind_v2.py) carries sources only, plus the owner
registry in declared test mode.
"""

from __future__ import annotations

from pathlib import Path

from research.qs_wall_treatment_01 import owner_parameters as OP, protocol as P
from research.qs_wall_treatment_01.pa05 import config_p7757 as C5

OUT = Path(P.OUT_DIR)
OUT6 = OUT / "pa06"
BLIND_DIR = Path("data/experiments/P7757_BLIND_REBUILD_02")


def owner_registry():
    reg = OP.p7757_registry()
    reg["_REGISTRY_ID"] = "P7757_OWNER_PARAMETERS (research/qs_wall_treatment_01/owner_parameters.py; OWNER_PROJECT_INPUT + authorised temporary defaults)"
    return reg


def supervised():
    return {
        "PROJECT_ID": "P7757", "DRAWING_FAMILY": "VILLA_KUWAIT_2026", "REVISION": "R0", "CAD_UNITS": "mm", "RULE_VERSION": "URBAN_RULES_PA06_DRAFT", "MAX_RUNTIME_S": 900,
        "SOURCES": [{"PATH": C5.DECODE, "KIND": "CAD_DECODE_JSON", "FAMILY": "ARCHITECTURAL"}, {"PATH": C5.ARCH_PDF, "KIND": "PDF", "FAMILY": "ARCHITECTURAL"}, {"PATH": C5.ST_PDF, "KIND": "PDF", "FAMILY": "STRUCTURAL"}],
        "SHEET_METADATA": {C5.ARCH_PDF: {k: {"AI_ROLE": r, "AI_EVIDENCE": e} for k, (r, e) in C5.ARCH_SHEET_READS.items()}, C5.ST_PDF: {k: {"AI_ROLE": r, "AI_EVIDENCE": e} for k, (r, e) in C5.ST_SHEET_READS.items()}},
        "VIEW_ASSIGNMENTS": [], "LAYER_OVERRIDES": None, "OWNER_INPUTS": [], "PRINTED_LABELS": [], "OWNER_ANCHORS": [], "AI_LABELS": [],
        "DECLARED_UNITS": {}, "OWNER_PARAMETER_REGISTRY": owner_registry(), "OWNER_STOREY_NAMES": {}, "SHEET_INDEX_OWNER": {},
        "TRADES": ["NORMAL_INTERNAL_PLASTER", "WET_ROOM_SPLATTER", "COLUMN_BONDING"],
    }


def blind():
    """Sources only; the owner registry is declared as test-mode input; no reads, no assignments, no overrides."""
    cfg = supervised()
    cfg["SHEET_METADATA"] = {}
    return cfg
