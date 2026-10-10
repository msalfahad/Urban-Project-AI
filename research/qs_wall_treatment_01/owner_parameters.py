"""The P7757 parameter registry after the owner answered the gate.

Central and editable HERE, versioned in git. Every owner value is stored
exactly as the parameter layer requires:

    SOURCE_TYPE = OWNER_PROJECT_INPUT, OWNER_CONFIRMED = true,
    DEFAULT_OR_ACTUAL = PROJECT_INPUT, STATUS = ESTABLISHED_FOR_PROJECT

and every quantity depending on one is an OWNER_PARAMETRIC_QUANTITY, never
a SOURCE_ESTABLISHED_QUANTITY. Temporary defaults stay TEMPORARY_DEFAULT
and make their quantities PROVISIONAL_DEFAULT_QUANTITY. What no accepted
source or owner input establishes stays UNKNOWN.

Scope rules the owner set with the values (§8): the normal internal plaster
height is NOT propagated to double-height zones, stair wells, facades,
parapets or tartusha rooms. Those carry their own parameters below, and
those parameters are UNKNOWN until the owner or a source establishes them.

    python3 -m research.qs_wall_treatment_01.owner_parameters
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.a21_trace_sufficiency_01 import parameters as PM
from research.qs_wall_treatment_01 import protocol as P

OWNER_REFERENCE = "owner directive to the long-horizon orchestrator, 2026-09-19"
REGISTRY_VERSION = 2


def _owner(reg, pid, value, unit, ref):
    return PM.with_owner_value(reg, pid, value, unit, REGISTRY_VERSION, ref)


def _default(pid, value, unit, ref, note=None):
    p = PM.parameter(pid, value, unit, "TEMPORARY_DEFAULT", ref,
                     default_or_actual="DEFAULT", version=REGISTRY_VERSION)
    if note:
        p["NOTE"] = note
    return p


def _unknown(pid, unit, ref, status="AWAITING_OWNER_INPUT"):
    return PM.parameter(pid, None, unit, "UNKNOWN", ref, status=status,
                        version=REGISTRY_VERSION)


def p7757_registry() -> dict:
    reg = PM.default_registry()          # the frozen experiments' registry
    # ---- §7 owner project inputs -----------------------------------
    reg = _owner(reg, "NORMAL_INTERNAL_PLASTER_HEIGHT", 3.20, "m",
                 OWNER_REFERENCE + " §7: NORMAL INTERNAL PLASTER HEIGHT")
    reg = _owner(reg, "EXTERNAL_STOREY_HEIGHT_GROUND", 4.00, "m",
                 OWNER_REFERENCE + " §7: EXTERNAL storey height GROUND")
    reg = _owner(reg, "EXTERNAL_STOREY_HEIGHT_FIRST", 4.50, "m",
                 OWNER_REFERENCE + " §7: EXTERNAL storey height FIRST")
    reg = _owner(reg, "EXTERNAL_STOREY_HEIGHT_SECOND_ROOF_ROOM", 4.00, "m",
                 OWNER_REFERENCE + " §7: EXTERNAL storey height SECOND-ROOF ROOM")
    for pid in ("NORMAL_INTERNAL_PLASTER_HEIGHT",):
        reg[pid]["SCOPE_RULE"] = (
            "normal rooms only; NOT propagated to double-height zones, "
            "stair wells, facades, parapets or tartusha rooms (§8)")
    # the frozen experiments' id stays as the experiments left it: UNKNOWN.
    # it is superseded for normal rooms by NORMAL_INTERNAL_PLASTER_HEIGHT
    reg["APPLICABLE_PLASTER_HEIGHT"]["SUPERSEDED_BY"] = "NORMAL_INTERNAL_PLASTER_HEIGHT"
    # ---- §15 temporary opening defaults ----------------------------
    reg["DOOR_WIDTH"] = _default("DOOR_WIDTH", 1.00, "m",
                                 "authorised temporary default (§15)")
    reg["DOOR_HEIGHT"] = _default("DOOR_HEIGHT", 2.20, "m",
                                  "authorised temporary default (§15)")
    reg["WINDOW_WIDTH"] = _default("WINDOW_WIDTH", 1.50, "m",
                                   "authorised temporary default (§15)")
    reg["WINDOW_HEIGHT"] = _default("WINDOW_HEIGHT", 1.50, "m",
                                    "authorised temporary default (§15)")
    # ---- §16 reveals: actual wins; these are defaults --------------
    reg["WINDOW_REVEAL_DEPTH"] = _default(
        "WINDOW_REVEAL_DEPTH", 0.20, "m", "owner approximate (~0.20) (§16)",
        note="an actual reveal depth from a section or schedule replaces it")
    reg["DOOR_REVEAL_DEPTH"] = _default(
        "DOOR_REVEAL_DEPTH", 0.15, "m", "owner gave 0.15 / 0.20 (§16); the "
        "smaller value is the default, 0.20 is a scenario",
        note="ALTERNATIVE_VALUE 0.20 is run in scenario mode only")
    reg["DOOR_REVEAL_DEPTH"]["ALTERNATIVE_VALUE"] = 0.20
    # ---- what stays UNKNOWN ----------------------------------------
    reg["DOUBLE_HEIGHT_PLASTER_HEIGHT"] = _unknown(
        "DOUBLE_HEIGHT_PLASTER_HEIGHT", "m",
        "no accepted project source or owner project input establishes it; "
        "the normal height is not propagated to double-height zones (§8)")
    reg["STAIR_WELL_PLASTER_HEIGHT"] = _unknown(
        "STAIR_WELL_PLASTER_HEIGHT", "m",
        "no accepted project source or owner project input establishes it (§8, §20)")
    reg["TARTUSHA_HEIGHT"] = _unknown(
        "TARTUSHA_HEIGHT", "m",
        "no accepted project source or owner project input establishes it (§18)")
    reg["STEEL_PROFILE_RULE"] = _unknown(
        "STEEL_PROFILE_RULE", None,
        "which edges take a steel profile is a specification / owner rule "
        "not yet provided; eligible edge lengths are reported per category (§17)",
        status="AWAITING_SOURCE")
    reg["CONTROL_JOINT_RULE"] = _unknown(
        "CONTROL_JOINT_RULE", None,
        "no accepted project source or owner project input establishes a "
        "control-joint spacing; none is invented (§24)")
    reg["ROOF_PARAPET_RULE"] = _unknown(
        "ROOF_PARAPET_RULE", None,
        "no general parapet rule; each parapet face is measured from its "
        "own traced dimensions or left unresolved (§22, §23)")
    # §22 - the 0.90 m concept, held as a CONDITIONAL owner input that is
    # bound to no condition yet, so it is applied nowhere
    reg["PARAPET_HEIGHT_CONCEPT_0_90"] = {
        **PM.parameter("PARAPET_HEIGHT_CONCEPT_0_90", 0.90, "m",
                       "OWNER_PROJECT_INPUT", OWNER_REFERENCE + " §22",
                       project_specific=True, owner_confirmed=True,
                       default_or_actual="PROJECT_INPUT",
                       version=REGISTRY_VERSION, status="CONDITIONAL_NOT_APPLIED"),
        "APPLIES_ONLY_TO": [],
        "RULE": "usable only as OWNER_PROJECT_INPUT for a specific unresolved "
                "parapet condition the owner names; never a general height",
    }
    return reg


def export(path: str | None = None) -> str:
    out = Path(path or P.OUT_DIR) / "P7757_OWNER_PARAMETERS.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    body = {"PHASE_ID": P.PHASE_ID, "ARTIFACT": "P7757_OWNER_PARAMETERS",
            "REGISTRY_VERSION": REGISTRY_VERSION,
            "OWNER_REFERENCE": OWNER_REFERENCE,
            "OWNER_INPUT_NEVER_BECOMES_DRAWING_DERIVED":
                PM.OWNER_INPUT_NEVER_BECOMES_DRAWING_DERIVED,
            "REGISTRY": p7757_registry()}
    out.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    return hashlib.sha256(out.read_bytes()).hexdigest()


if __name__ == "__main__":
    print(json.dumps({"P7757_OWNER_PARAMETERS_SHA256": export()}, indent=2))
