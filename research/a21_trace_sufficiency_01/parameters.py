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


WHY_A_PARAMETER_IS_UNKNOWN = (
    "a parameter is UNKNOWN when NO CURRENTLY ACCEPTED PROJECT SOURCE OR "
    "OWNER_PROJECT_INPUT ESTABLISHES ITS VALUE. That is the definition, "
    "and it is a property of the project's evidence, not of any "
    "experiment. A reading that failed to find a value is validation "
    "evidence for the status; it is never the reason for it. Stated this "
    "way the schema is reusable on a project that never ran an experiment "
    "at all")

VALIDATION_EVIDENCE = {
    "APPLICABLE_PLASTER_HEIGHT": {
        "OBSERVATION": (
            "across two frozen visual experiments, 23 of 24 case readings "
            "returned PLASTER_HEIGHT_NOT_ESTABLISHED, and the one "
            "exception read its value off a sheet its packet had not "
            "declared"),
        "WHAT_IT_SUPPORTS": (
            "that the P7757 drawing set does not establish this parameter"),
        "WHAT_IT_IS_NOT": (
            "the definition of the UNKNOWN status. The status would be "
            "UNKNOWN on a project where no experiment had ever run"),
    },
}


def default_registry() -> dict:
    """The parameter set for this project, by the general definition.

    Every entry below is UNKNOWN for one reason only: no accepted project
    source and no owner project input establishes it. See
    WHY_A_PARAMETER_IS_UNKNOWN, and VALIDATION_EVIDENCE for the separate
    experimental observation that supports the status here.
    """
    return {p["PARAMETER_ID"]: p for p in [
        parameter("APPLICABLE_PLASTER_HEIGHT", None, "m", "UNKNOWN",
                  "no accepted project source and no owner project input "
                  "establishes this value",
                  status="AWAITING_OWNER_INPUT"),
        parameter("DOOR_HEIGHT", 2.20, "m", "TEMPORARY_DEFAULT",
                  "authorised temporary owner default",
                  default_or_actual="DEFAULT"),
        parameter("WINDOW_HEIGHT", 1.50, "m", "TEMPORARY_DEFAULT",
                  "authorised temporary owner default",
                  default_or_actual="DEFAULT"),
        parameter("DOOR_REVEAL_DEPTH", None, "m", "UNKNOWN",
                  "no accepted project source establishes it",
                  status="AWAITING_SOURCE"),
        parameter("WINDOW_REVEAL_DEPTH", None, "m", "UNKNOWN",
                  "no accepted project source establishes it",
                  status="AWAITING_SOURCE"),
        parameter("ROOF_PARAPET_RULE", None, None, "UNKNOWN",
                  "no accepted project source or owner project input "
                  "establishes it", status="AWAITING_OWNER_INPUT"),
        parameter("CONTROL_JOINT_RULE", None, None, "UNKNOWN",
                  "no accepted project source or owner project input "
                  "establishes it", status="AWAITING_OWNER_INPUT"),
    ]}


def with_owner_value(reg: dict, pid: str, value, unit, version: int,
                     reference: str) -> dict:
    """An owner supplies a parameter. It never becomes drawing evidence."""
    reg = json.loads(json.dumps(reg))
    p = parameter(pid, value, unit, "OWNER_PROJECT_INPUT", reference,
                  project_specific=True, owner_confirmed=True,
                  version=version)
    p["DEFAULT_OR_ACTUAL"] = "PROJECT_INPUT"
    p["STATUS"] = "ESTABLISHED_FOR_PROJECT"
    reg[pid] = p
    return reg


OWNER_INPUT_NEVER_BECOMES_DRAWING_DERIVED = (
    "an owner-supplied value is stored SOURCE_TYPE = OWNER_PROJECT_INPUT, "
    "OWNER_CONFIRMED = true, DEFAULT_OR_ACTUAL = PROJECT_INPUT, STATUS = "
    "ESTABLISHED_FOR_PROJECT. Every quantity depending on it is an "
    "OWNER_PARAMETRIC_QUANTITY and never a SOURCE_ESTABLISHED_QUANTITY. "
    "The constructor makes the alternative unrepresentable: a DRAWING "
    "parameter marked OWNER_CONFIRMED raises")


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
        "WHY_A_PARAMETER_IS_UNKNOWN": WHY_A_PARAMETER_IS_UNKNOWN,
        "VALIDATION_EVIDENCE_HELD_SEPARATELY": VALIDATION_EVIDENCE,
        "OWNER_INPUT_NEVER_BECOMES_DRAWING_DERIVED":
            OWNER_INPUT_NEVER_BECOMES_DRAWING_DERIVED,
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
