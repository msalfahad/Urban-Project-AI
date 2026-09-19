"""PART C - the parameter layer and deterministic recalculation.

The experiments established a boundary the system has to respect: the
drawing establishes GEOMETRY and does not establish every QS INPUT. So
the inputs live in their own layer, each carrying where it came from, and
a quantity inherits the weakest provenance of everything that made it.

Three states, never mixed:

  SOURCE_ESTABLISHED_QUANTITY   every input from a permitted project source
  OWNER_PARAMETRIC_QUANTITY     geometry from the source, a QS input from
                                the owner. Legitimate, but not drawing-derived
  PROVISIONAL_DEFAULT_QUANTITY  something is still a temporary default

AGENTS EXTRACT AND EXPLAIN. CODE CALCULATES. So A21 supplies lengths,
identities and traces; the arithmetic happens here; and changing a height
re-runs the arithmetic and nothing else.

    python3 -m research.a21_trace_sufficiency_01.parameters
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.a21_trace_sufficiency_01 import protocol as P

OUT = Path("data/experiments/A21_TRACE_SUFFICIENCY_01")

SOURCE_TYPES = P.PARAMETER_SOURCE_TYPES

# which provenance is weakest - a quantity inherits the weakest input
PROVENANCE_RANK = {
    "DRAWING": 0,
    "SPECIFICATION": 0,
    "URBAN_STANDARD": 1,
    "CONTRACTOR_RULE": 1,
    "OWNER_PROJECT_INPUT": 2,
    "TEMPORARY_DEFAULT": 3,
    "UNKNOWN": 4,
}
RANK_TO_STATE = {
    0: "SOURCE_ESTABLISHED_QUANTITY",
    1: "SOURCE_ESTABLISHED_QUANTITY",
    2: "OWNER_PARAMETRIC_QUANTITY",
    3: "PROVISIONAL_DEFAULT_QUANTITY",
    4: "NOT_ESTABLISHED",
}

THE_RULE_THAT_MATTERS = (
    "a quantity is only as established as its weakest input. One "
    "TEMPORARY_DEFAULT anywhere in a calculation makes the whole result "
    "PROVISIONAL_DEFAULT_QUANTITY, however many printed dimensions went "
    "in beside it. There is no averaging of provenance")


def parameter(pid, value, unit, source_type, source_reference, *,
              project_specific=False, owner_confirmed=False,
              default_or_actual="ACTUAL", version=1, status="ACTIVE"):
    if source_type not in SOURCE_TYPES:
        raise ValueError(f"unknown SOURCE_TYPE {source_type}")
    if source_type == "TEMPORARY_DEFAULT" and default_or_actual != "DEFAULT":
        raise ValueError("a TEMPORARY_DEFAULT must be marked DEFAULT")
    if source_type == "OWNER_PROJECT_INPUT" and not owner_confirmed:
        raise ValueError("an OWNER_PROJECT_INPUT must be OWNER_CONFIRMED")
    if source_type == "DRAWING" and owner_confirmed:
        raise ValueError(
            "a DRAWING parameter is not owner-confirmed - that is exactly "
            "the confusion this layer exists to prevent")
    return {
        "PARAMETER_ID": pid, "VALUE": value, "UNIT": unit,
        "SOURCE_TYPE": source_type, "SOURCE_REFERENCE": source_reference,
        "PROJECT_SPECIFIC": project_specific,
        "OWNER_CONFIRMED": owner_confirmed,
        "DEFAULT_OR_ACTUAL": default_or_actual,
        "VERSION": version, "STATUS": status,
    }


def default_registry() -> dict:
    """The parameter set as the experiments actually left it.

    APPLICABLE_PLASTER_HEIGHT is deliberately UNKNOWN. Twenty-four case
    readings failed to establish it from the drawing, and inventing one
    here would undo the only thing those readings proved.
    """
    return {p["PARAMETER_ID"]: p for p in [
        parameter("APPLICABLE_PLASTER_HEIGHT", None, "m", "UNKNOWN",
                  "not established by the drawing in any of 24 readings",
                  status="AWAITING_OWNER_INPUT"),
        parameter("DOOR_HEIGHT", 2.20, "m", "TEMPORARY_DEFAULT",
                  "authorised temporary owner default",
                  default_or_actual="DEFAULT"),
        parameter("WINDOW_HEIGHT", 1.50, "m", "TEMPORARY_DEFAULT",
                  "authorised temporary owner default",
                  default_or_actual="DEFAULT"),
        parameter("DOOR_REVEAL_DEPTH", None, "m", "UNKNOWN",
                  "frame set-back within the wall is not drawn",
                  status="AWAITING_SOURCE"),
        parameter("WINDOW_REVEAL_DEPTH", None, "m", "UNKNOWN",
                  "frame set-back within the wall is not drawn",
                  status="AWAITING_SOURCE"),
        parameter("ROOF_PARAPET_RULE", None, None, "UNKNOWN",
                  "no rule states how a parapet face height is measured "
                  "from the structural level", status="AWAITING_OWNER_INPUT"),
        parameter("CONTROL_JOINT_RULE", None, None, "UNKNOWN",
                  "no spacing is drawn, noted or specified anywhere",
                  status="AWAITING_OWNER_INPUT"),
    ]}


def with_owner_height(reg: dict, value: float, version: int) -> dict:
    """The owner supplies a plaster height. It is NOT drawing evidence."""
    reg = json.loads(json.dumps(reg))
    reg["APPLICABLE_PLASTER_HEIGHT"] = parameter(
        "APPLICABLE_PLASTER_HEIGHT", value, "m", "OWNER_PROJECT_INPUT",
        "supplied by the owner for this project; not read from any sheet",
        project_specific=True, owner_confirmed=True, version=version)
    return reg


# ==================================================================
# deterministic calculation
# ==================================================================

def compute(geometry: list, reg: dict) -> dict:
    """Geometry comes from A21. Arithmetic happens here. Nothing else."""
    lines = []
    for g in geometry:
        inputs = [("LENGTH_M", g.get("SOURCE_TYPE") or "UNKNOWN")]
        h = reg.get(g["HEIGHT_PARAMETER"]) or {}
        inputs.append((g["HEIGHT_PARAMETER"], h.get("SOURCE_TYPE", "UNKNOWN")))
        for extra in g.get("EXTRA_PARAMETERS") or []:
            e = reg.get(extra) or {}
            inputs.append((extra, e.get("SOURCE_TYPE", "UNKNOWN")))

        length = g.get("LENGTH_M")
        height = h.get("VALUE")
        area = (round(length * height, 4)
                if isinstance(length, (int, float))
                and isinstance(height, (int, float)) else None)
        rank = max(PROVENANCE_RANK.get(t, 4) for _, t in inputs)
        state = RANK_TO_STATE[rank]
        if area is None:
            state = "NOT_ESTABLISHED"
        lines.append({
            "ITEM_ID": g["ITEM_ID"],
            "CASE_ID": g["CASE_ID"],
            "TREATMENT": g["TREATMENT"],
            "SUPPORTED_BY_TRACES": g.get("SUPPORTED_BY_TRACES"),
            "LENGTH_M": length,
            "HEIGHT_PARAMETER": g["HEIGHT_PARAMETER"],
            "HEIGHT_VALUE": height,
            "AREA_M2": area,
            "CALCULATION": (f"{length} m x {height} m = {area} m2"
                            if area is not None
                            else f"{length} m x UNKNOWN = NOT_ESTABLISHED"),
            "INPUT_PROVENANCE": {k: v for k, v in inputs},
            "QUANTITY_STATE": state,
        })
    return {"LINES": lines,
            "BY_STATE": {s: sum(1 for l in lines if l["QUANTITY_STATE"] == s)
                         for s in sorted({l["QUANTITY_STATE"]
                                          for l in lines})}}


def schema_doc() -> dict:
    return {
        "PHASE_ID": P.PHASE_ID,
        "ARTIFACT": "PARAMETER_SCHEMA",
        "PARAMETER_FIELDS": list(P.PARAMETER_FIELDS),
        "SOURCE_TYPES": list(SOURCE_TYPES),
        "THREE_QUANTITY_STATES": P.THREE_QUANTITY_STATES,
        "THEY_ARE_NEVER_MIXED": True,
        "PROVENANCE_RANK": PROVENANCE_RANK,
        "THE_RULE_THAT_MATTERS": THE_RULE_THAT_MATTERS,
        "CONSTRUCTOR_REFUSES": [
            "a TEMPORARY_DEFAULT not marked DEFAULT",
            "an OWNER_PROJECT_INPUT that is not OWNER_CONFIRMED",
            "a DRAWING parameter marked OWNER_CONFIRMED",
        ],
        "THE_FINDING_THAT_MUST_SURVIVE": P.THE_FINDING_THAT_MUST_SURVIVE,
        "PARAMETRIC_RECALCULATION": P.PARAMETRIC_RECALCULATION,
        "REGISTRY_AS_THE_EXPERIMENTS_LEFT_IT": default_registry(),
    }


def write_schema() -> str:
    p = OUT / "PARAMETER_SCHEMA.json"
    p.write_text(json.dumps(schema_doc(), indent=2, ensure_ascii=False) + "\n",
                 encoding="utf-8")
    return hashlib.sha256(p.read_bytes()).hexdigest()


if __name__ == "__main__":
    print(json.dumps({"PARAMETER_SCHEMA_SHA256": write_schema()}, indent=2))
