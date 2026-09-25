"""The A21 baseline pilot freeze, pre-registered by hash.

The run artifacts live under data/, which is gitignored under the client-data
policy. Nothing from a client drawing is committed. What IS committed is this
register: the hash of every freeze artifact, so that a later claim about what
A21 returned can be checked against bytes rather than against a memory.

    python3 -m research.a21_visual_qs_pilot_01.freeze_registry

Order matters and is part of the record. Each pass was frozen on its own,
before the other pass was read; the comparison was built only after both
freezes existed; the blindness proof came last. Nothing was averaged and no
answer was chosen for being the more plausible one.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

RUN_DIR = Path("data/experiments/A21_VISUAL_QS_PILOT_01")

RUN_ID = "A21_SOURCE_PRESENTATION_BASELINE"

# ------------------------------------------------------------------
# the approved inputs, unchanged by the run
# ------------------------------------------------------------------
APPROVED_PROTOCOL_HASH = (
    "d6de5dc1a99f315a8a1bf409acce71f59ab3f75295baab660c655682029e7201")
APPROVED_SELECTION_RULE_HASH = (
    "75f2d71a12397dd8a52fa1457fdc0665d98c9dda6b8afbee9228791c2815cfc6")
DECISIONS_HASH = (
    "a5b0fbcaa5b3d9b54a8e79c6595e68fff1452eaea818cfb005168b6b4db83eff")
SOURCE_PREPARATION_DECISION_SHA256 = (
    "31ade8b0cab3c835e0fecdc881698799379d39df2cbdfa500db604ed45ebc2af")

# ------------------------------------------------------------------
# the freeze, in the order it was written
# ------------------------------------------------------------------
FREEZE_SHA256 = {
    "A21_INPUT_MANIFEST.json":
        "f6cebb4455560400fc288548198ae0abdee2cf774a60e474f7fe39315774f98e",
    "PROTOCOL_DEVIATIONS.json":
        "b75fa3a2c686035cc6bdd1c01d2f93627c985cdbad47d5f7b65df4195e273cf2",
    "BASELINE_FREEZE.json":
        "d670b28972e0be8a0f27f1255de1aaf8a6c6d242835228788b3a43d0c60ab302",
    "PASS2_FREEZE.json":
        "d2af8d4f3ddccbc417108fa3f12d45d314dfafe0d2f7ae61f0de6f95f4dbe86b",
    "PASS_COMPARISON.json":
        "7630c18c9738cace95098c2eff158a69ecd3a036507940344b39f4206c6b82f5",
    "BLINDNESS_PROOF.json":
        "c8dda7bbcee3d1f7e7f38ff45ae30bb59a93e274bc182bc916602d3602886533",
}

# ------------------------------------------------------------------
# THE FREEZE DIGEST IS NOT THE HASH OF A FILE
# ------------------------------------------------------------------
# A21_FREEZE_SHA256 is the digest over the 43-entry {path: sha256} manifest
# that A21_FREEZE.json carries. It cannot be the hash of A21_FREEZE.json
# itself - that file contains the digest, so hashing it would be circular.
# Recomputing it is therefore a MANIFEST recomputation, done by
# verify_freeze_digest() below, not a file comparison.

A21_FREEZE_SHA256 = (
    "5335486d28ab3eb8869545a3f169af90769ef8d46156f48e7fe59536dbdc9434")
FILES_COVERED_BY_THE_FREEZE = 43
FREEZE_DIGEST_RULE = (
    "sha256(json.dumps(FILES, sort_keys=True).encode()), where FILES maps "
    "each of the 43 frozen paths to its own sha256")

# the four reader outputs, each frozen inside its own pass
READER_OUTPUT_SHA256 = {
    "a21_raw/A21_reader1.json":
        "5b06da9ed883c66296720b927be271f1b5b45b9f95de26e38b1133b23ca8ee41",
    "a21_raw/A21_reader2.json":
        "5f8772c96714527a97a58d9db4132890ff5a240dbd4d88ce79fb94c4d8085f59",
    "a21_raw/PASS2_cases_1_3.json":
        "d19e7002be002fc3987aa78bc2ee5af862c70c61464e26a4e963fb48400592d3",
    "a21_raw/PASS2_cases_4_6.json":
        "68145c827f44d318b6f0da8c953a3848d9559f0519fafdcfc46ac7ad788dd6da",
}

PROMPT_SHA256 = {
    "prompts/GROUP_A_CASES_1_3.txt":
        "9369c49d4d298eee04dbcabbbb1d93f3ec70319c76564553e31909af28ff36c1",
    "prompts/GROUP_B_CASES_4_6.txt":
        "6d6f42a164799a3cb88e5645048935a55231e809783653106bab0e449cfb7cb9",
}

ORDER_OF_OPERATIONS_AS_RUN = (
    "protocol and selection approved and hashed",
    "decisions recorded without touching either hash",
    "sandbox sealed and screened",
    "source-preparation decision written and hashed at 12:43:58",
    "first reader output written at 12:46 - the decision predates it",
    "baseline pass frozen before pass 2 returned",
    "pass 2 frozen on its own",
    "only then: comparison and blindness proof",
)

# ------------------------------------------------------------------
# what the comparison found - recorded, not resolved
# ------------------------------------------------------------------
DIFFERENCES_BETWEEN_PASSES = (
    {"CASE_ID": "CASE-5-EXTERNAL-FACADE",
     "FIELD": "STOREY_HEIGHT_VALUE",
     "PASS_1": 4.0, "PASS_2": 4.5,
     "CLASSIFICATION": "HEIGHT_DIFFERENCE",
     "RESOLVED": False},
    {"CASE_ID": "CASE-6-ROOF-PARAPET",
     "FIELD": "APPLICABLE_PLASTER_HEIGHT_STATUS",
     "PASS_1": "PLASTER_HEIGHT_NOT_ESTABLISHED",
     "PASS_2": "ESTABLISHED_WITH_CAVEAT",
     "CLASSIFICATION": "REFUSAL_STATUS_DIFFERENCE",
     "RESOLVED": False},
)

EVIDENCE_INDEPENDENCE_STATUS = "PARTIALLY_SHARED"
INDEPENDENCE_COMPONENTS = ("SHARED_SOURCE", "SHARED_RULE", "SHARED_METHOD")

WHAT_AGREEMENT_HERE_MEANS = (
    "repeatability of one visual method under fixed inputs. Same model "
    "family, byte-identical rules, the same scan, the same unrotated "
    "presentation. An echo is not a witness, and this may never be recorded "
    "as independent confirmation that a reading is correct")

# ------------------------------------------------------------------
# the one deliverable that could not be produced
# ------------------------------------------------------------------
OVERLAYS_NOT_PRODUCIBLE = {
    "REQUIRED_BY": "the A21 directive, visual QA overlays",
    "WHY_NOT": (
        "the A21 schema captured SEG_ID, DESCRIPTION, LENGTH_M, SOURCE_TYPE, "
        "SOURCE_LOCATION and STATUS - and no coordinate, anchor or pixel "
        "reference. A segment id therefore cannot be placed on the drawing "
        "without inventing a position for it"),
    "WHAT_WAS_NOT_DONE": (
        "no overlay was drawn from guessed positions, and no overlay was "
        "reported as produced"),
    "FIX_FOR_THE_IMPROVED_RUN": (
        "the schema must carry, per segment and per opening, the sheet it "
        "was read on and a pixel anchor on that sheet, so an overlay is a "
        "redraw of what the reader saw rather than a reconstruction"),
}

A22_WAS_NOT_RUN = True
EXCEL_WAS_NOT_OPENED = True
E1_4_WAS_NOT_EXPOSED_TO_ANY_READER = True
NOTHING_WAS_AVERAGED_OR_SELECTED = True


def verify_freeze_digest() -> dict:
    """Recompute the 43-file manifest digest under FREEZE_DIGEST_RULE."""
    import json
    path = RUN_DIR / "A21_FREEZE.json"
    if not path.exists():
        return {"PRESENT": False, "EXPECTED": A21_FREEZE_SHA256}
    freeze = json.loads(path.read_text())
    files = freeze["FILES"]
    got = hashlib.sha256(
        json.dumps(files, sort_keys=True).encode()).hexdigest()
    return {"PRESENT": True,
            "FILES_IN_MANIFEST": len(files),
            "EXPECTED": A21_FREEZE_SHA256,
            "RECOMPUTED": got,
            "MATCHES": got == A21_FREEZE_SHA256,
            "ALSO_DECLARED_INSIDE_THE_FILE":
                freeze.get("A21_FREEZE_SHA256") == A21_FREEZE_SHA256}


def verify() -> dict:
    """Do the frozen artifacts still hash to what was registered here?"""
    out = {}
    for rel, expected in {**FREEZE_SHA256, **READER_OUTPUT_SHA256,
                          **PROMPT_SHA256}.items():
        path = RUN_DIR / rel
        if not path.exists():
            out[rel] = {"PRESENT": False, "EXPECTED_SHA256": expected}
            continue
        got = hashlib.sha256(path.read_bytes()).hexdigest()
        out[rel] = {"PRESENT": True,
                    "EXPECTED_SHA256": expected,
                    "ACTUAL_SHA256": got,
                    "UNCHANGED": got == expected}
    return out


if __name__ == "__main__":
    import json
    checked = verify()
    present = [k for k, v in checked.items() if v["PRESENT"]]
    print(json.dumps({
        "RUN_ID": RUN_ID,
        "A21_FREEZE_SHA256": A21_FREEZE_SHA256,
        "FREEZE_DIGEST": verify_freeze_digest(),
        "REGISTERED_ARTIFACTS": len(checked),
        "PRESENT_ON_THIS_MACHINE": len(present),
        "ALL_PRESENT_ONES_UNCHANGED": all(
            checked[k]["UNCHANGED"] for k in present),
        "DIFFERENCES_BETWEEN_PASSES_STILL_UNRESOLVED": [
            d["CASE_ID"] for d in DIFFERENCES_BETWEEN_PASSES],
        "OVERLAYS": "NOT_PRODUCIBLE - see OVERLAYS_NOT_PRODUCIBLE",
    }, indent=2))
