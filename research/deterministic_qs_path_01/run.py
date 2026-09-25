"""DETERMINISTIC_QS_PATH_01 - P7757, from the frozen A21 traces, to the gate.

Runs the whole deterministic chain on the four frozen trace cases:

    TRACE_REGISTER  ->  trace_to_region  ->  qs_measurement_region
                    ->  plaster_trade_engine (parameter registry as-is)

and freezes what comes out. The parameter registry is the project's
current one: APPLICABLE_PLASTER_HEIGHT is UNKNOWN because no accepted
project source or owner project input establishes it. No owner value is
introduced here. No benchmark is opened. E1.4 is not consulted.

This is the "deterministic result frozen" that the A22 gate will later
require, and it is frozen with every quantity NOT_ESTABLISHED, because
that is what the evidence supports.

    python3 -m research.deterministic_qs_path_01.run
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from engine import plaster_trade_engine as E
from engine import qs_measurement_region as M
from engine import trace_to_region as A
from research.a21_trace_sufficiency_01 import parameters as PM

OUT = Path("data/experiments/DETERMINISTIC_QS_PATH_01")
TRACE_REGISTER = Path("data/experiments/A21_TRACE_SUFFICIENCY_01/TRACE_REGISTER.json")

# basis per case is a MEASUREMENT decision, declared here, not tuned:
# open-plan zones are attempted as cells under the open-plan basis; a
# stair wall and a parapet are runs.
PLAN = [
    ("CASE-1-NORMAL-PLASTER", "GROUND_FLOOR_PLAN", "NORMAL_INTERNAL_PLASTER",
     "WALL_FACE_PLASTER_OPEN_PLAN_CELL"),
    ("CASE-3-DOOR-AND-WINDOW", "GROUND_FLOOR_PLAN", "NORMAL_INTERNAL_PLASTER",
     "WALL_FACE_PLASTER_OPEN_PLAN_CELL"),
    ("CASE-4-STAIR", "GROUND_FLOOR_PLAN", "STAIR_WALL_PLASTER", M.LINEAR_RUN),
    ("CASE-6-ROOF-PARAPET", "SECOND_FLOOR_ROOF_PLAN", "EXTERNAL_PLASTER",
     M.LINEAR_RUN),
]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    reg = PM.default_registry()
    assert reg["APPLICABLE_PLASTER_HEIGHT"]["VALUE"] is None
    cases, gate = [], []
    for cid, sheet, trade, basis in PLAN:
        region = A.run_case(cid, plan_sheet=sheet, trade=trade, basis=basis)
        sheet_out = E.calculate(region, reg, treatment=trade)
        gb = region["GROSS_BASIS"]
        blockers = []
        for x in region.get("NOT_ESTABLISHED_BECAUSE") or []:
            blockers.append(x["REASON"])
        if gb["STATUS"] != "ESTABLISHED":
            blockers.append(f"GROSS_BASIS: {gb.get('WHY_NOT')}")
        blockers.append("APPLICABLE_PLASTER_HEIGHT is UNKNOWN")
        cases.append({
            "CASE_ID": cid, "PLAN_SHEET": sheet, "TRADE": trade,
            "MEASUREMENT_BASIS": basis,
            "REGION": region, "SHEET": sheet_out,
            "SUMMARY": {
                "MEASUREMENT_REGION_STATUS": region["MEASUREMENT_REGION_STATUS"],
                "GROSS_BASIS_LM": gb["VALUE"],
                "GROSS_BASIS_STATUS": gb["STATUS"],
                "CONTRIBUTING_EDGES_WITH_LENGTH": sum(
                    1 for e in gb["CONTRIBUTING_EDGES"]
                    if isinstance(e["length_m"], (int, float))),
                "CONTRIBUTING_EDGES_TOTAL": len(gb["CONTRIBUTING_EDGES"]),
                "OPENINGS_TRACED": len(region["OPENINGS"]),
                "QUANTITY_STATE": sheet_out["QUANTITY_STATE"],
                "BLOCKERS": blockers,
            },
        })
        gate.append({"CASE_ID": cid, "BLOCKERS": blockers})

    body = {
        "PHASE_ID": "DETERMINISTIC_QS_PATH_01",
        "TRACE_REGISTER_SHA256": sha(TRACE_REGISTER),
        "PARAMETER_REGISTRY_AS_RUN": reg,
        "OWNER_HEIGHT_INTRODUCED": False,
        "BENCHMARK_OPENED": False,
        "E1_4_CONSULTED": False,
        "CASES": cases,
        "GATE": {
            "STATE": "OWNER_INPUT_REQUIRED",
            "WHY": "every P7757 plaster quantity on the traced cases needs "
                   "APPLICABLE_PLASTER_HEIGHT, and the two open-plan cases "
                   "additionally need a zone-boundary rule the drawing "
                   "does not carry",
            "PER_CASE": gate,
        },
        "NOTHING_WAS_FORCED": True,
    }
    p = OUT / "P7757_DETERMINISTIC_PATH_FREEZE.json"
    p.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n",
                 encoding="utf-8")
    return {"SHA256": sha(p),
            "SUMMARY": {c["CASE_ID"]: c["SUMMARY"] for c in cases}}


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
