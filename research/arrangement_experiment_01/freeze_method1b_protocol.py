"""Freeze the Method 1b rule set, and preserve what Method 1A established.

Nothing of Method 1b may be constructed until this has run. The rules are
written, hashed, and written to disk with the hash of the file itself, so
that a later claim about what the rules were can be checked rather than
believed.

It also records, in its own register and independently of whether Method
1b succeeds:

    METHOD_1A  failed, and the finding stands
    the B/C/D widening measurements are DEVELOPMENT_DIAGNOSTIC_ONLY
    E1_4_CLEAR_ROOM_BOUNDARY_CAPABILITY != PLANAR_PARTITION_CAPABILITY
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.arrangement_experiment_01 import method1b_protocol as M1B
from research.arrangement_experiment_01 import protocol as P

OUT = Path("data/experiments/ARRANGEMENT_EXPERIMENT_01")


def _write(path: Path, body: dict) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    body = M1B.record()
    p = OUT / "method1b" / "PROTOCOL.json"
    file_hash = _write(p, body)

    lesson = {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "WHAT_THIS_REGISTER_IS": (
            "the findings this experiment preserves regardless of what "
            "any later method does. None of them is revised by a "
            "subsequent result"),

        "METHOD_1A": {
            "METHOD": P.METHOD_1,
            "EDGE_SET": "exactly what frozen E1.4 admits to bound a clear "
                        "room face",
            "OUTCOME": "FAILED_TO_PROVIDE_A_MEANINGFUL_FLOOR_SUBDIVISION",
            "FINDING": M1B.WHAT_METHOD_1A_ESTABLISHED,
            "THIS_RESULT_IS_NOT_OVERWRITTEN_OR_REFRAMED": True,
            "IT_IS_NOT_A_FALSIFICATION_OF_THE_REPRESENTATION": (
                "Method 1A tested one admission gate. Whether a planar "
                "arrangement can hold what the drawing establishes is a "
                "different question, and Method 1b is the one corrected "
                "attempt at it"),
        },

        "THE_B_C_D_WIDENING_MEASUREMENTS": {
            "CLASSIFICATION": "DEVELOPMENT_DIAGNOSTIC_ONLY",
            "WHAT_THEY_ARE": (
                "four progressively wider edge sets built to locate "
                "whether the Method 1A starvation came from E1.4's "
                "evidence gates or from the drawing"),
            "THEY_ARE_NOT_A_METHOD": True,
            "SET_C_AND_SET_D_ARE_NOT_PROMOTED_INTO_METHOD_1B": True,
            "why": M1B.THE_B_C_D_MEASUREMENTS_ARE_NOT_A_METHOD,
        },

        "THE_ARCHITECTURAL_LESSON": {
            "STATEMENT": M1B.THE_LESSON_THIS_METHOD_EXISTS_TO_RECORD,
            "IT_IS_LEARNED_EVEN_IF_THE_ARRANGEMENT_HYPOTHESIS_FAILS": True,
            "what_was_conflated": (
                "one question - can this stretch of linework be the "
                "surface a surveyor measures a room to - was standing in "
                "for a second and different question: does this stretch "
                "of linework divide the plane. A wall face a room's "
                "finish does not follow still divides it. A column behind "
                "a plastered face still occupies space. A pool edge still "
                "separates walkable floor from water"),
            "where_it_now_lives": (
                "PLANAR_PARTITION_CAPABILITY, declared in the Method 1b "
                "protocol as a dimension independent of MATERIAL_PRESENT, "
                "CAN_OWN_CLEAR_FINISH_FACE, CAN_CONTRIBUTE_WALL_LENGTH, "
                "CAN_CONTRIBUTE_MATERIAL_LENGTH and "
                "CAN_BOUND_CLEAR_FLOOR_REGION"),
        },

        "E1_4_IS_NOT_MODIFIED": True,
        "E1_4_RUN_HASH": P.E1_4_RUN_HASH,
        "no_benchmark_or_expected_area_was_opened": True,
    }
    lesson_hash = _write(OUT / "03_METHOD_1A_RESULT_AND_THE_LESSON.json",
                         lesson)

    print(json.dumps({
        "METHOD_1B_PROTOCOL_HASH": body["METHOD_1B_PROTOCOL_HASH"],
        "PROTOCOL_JSON_FILE_SHA256": file_hash,
        "LESSON_REGISTER_SHA256": lesson_hash,
        "THE_RULES_ARE_NOW_FROZEN": True,
        "no_rule_may_change_after_the_first_cell_result": True,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
