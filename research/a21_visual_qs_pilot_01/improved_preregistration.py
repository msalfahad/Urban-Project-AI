"""The improved run's INPUTS, pre-registered by hash BEFORE any reader ran.

data/ is gitignored, so the packets and prompts themselves cannot be
committed. Their hashes can, and this file is committed before the first
reader is launched. That is what makes "the packet and the prompts were
not shaped by the improved answers" checkable instead of asserted.

    python3 -m research.a21_visual_qs_pilot_01.improved_preregistration
"""

from __future__ import annotations

import hashlib
from pathlib import Path

RUN_DIR = Path("data/experiments/A21_VISUAL_QS_PILOT_01")
RUN_ID = "A21_SOURCE_PRESENTATION_IMPROVED"

IMPROVED_PROTOCOL_HASH = (
    "90fb4030449b2dab04c731eba5304981e7c8fd598c56cfb3a193c197bae4228e")

INPUT_SHA256 = {
    "IMPROVED_INPUT_MANIFEST.json":
        "697a13117551821c10e0b6611efc1306ab13425c6487a32d56b6b3bbd1a69bdd",
    "IMPROVED_PROMPT_RECORD.json":
        "c899af756ad65ce59b6d1e42624ca48e6beac5d6b841334651122921b802917a",
    "prompts_improved/PASS1_GROUP_A_CASES_1_3.txt":
        "9b466f92674b22fa73628012a442b770e5cb56b79d0c905fddeafb2cf940fab6",
    "prompts_improved/PASS1_GROUP_B_CASES_4_6.txt":
        "e7a1f83653151056109df684e617c7c9c690836bb4a340afadf282f0a2a691f3",
    "prompts_improved/PASS2_GROUP_A_CASES_1_3.txt":
        "d303181cc73418bf7e653dc932b10c86eff9e5a038db929310a78a2be6523ba3",
    "prompts_improved/PASS2_GROUP_B_CASES_4_6.txt":
        "69dd8008a3a6d9fa1ba0553638d47bcb165ea2747eba977ba5984b63bec6a1b1",
}

# ------------------------------------------------------------------
# what the presentation change actually bought, measured, not claimed
# ------------------------------------------------------------------
# effective displayed scale relative to the baseline's presentation of
# the same sheet - rotation + content trim + a single LANCZOS reduction
# instead of two unknown ones.
EFFECTIVE_SCALE_VS_BASELINE = {
    "GROUND_FLOOR_PLAN": 1.081,
    "SECOND_FLOOR_ROOF_PLAN": 1.081,
    "SOUTH_EAST_ELEVATION": 1.468,
    "SECTION_A_A": 1.404,
    "SECTION_B_B": 1.082,
}

DETAIL_CROP_PX = {
    "CASE-1-NORMAL-PLASTER": [1892, 1893],
    "CASE-2-TILE-PREP": [1893, 1892],
    "CASE-3-DOOR-AND-WINDOW": [1893, 1893],
    "CASE-4-STAIR": None,
    "CASE-5-EXTERNAL-FACADE": None,
    "CASE-6-ROOF-PARAPET": None,
}

WHAT_THE_DETAIL_CROP_CHANGED = (
    "the baseline crop was 2840 px of JPEG, which the runtime reduced by "
    "about 0.70, leaving a 2.5 mm printed digit near 27 px. The improved "
    "crop is 1892 px of lossless PNG that passes the runtime untouched, "
    "so the same digit sits at its full 39 px. Fewer metres of building "
    "per image, every pixel of them real")

ROTATION_VERIFIED_PER_PAGE = {
    "GROUND_FLOOR_PLAN": 90, "SECOND_FLOOR_ROOF_PLAN": 90,
    "SOUTH_EAST_ELEVATION": 90, "SECTION_A_A": 90, "SECTION_B_B": 90,
}
ROTATION_WAS_CHECKED_NOT_ASSUMED = (
    "all five pages happen to need the same +90 CCW, but each was "
    "rendered and inspected on its own before the run. A wrong rotation "
    "measured worse than no rotation, so 'they are probably all the "
    "same' was not good enough")

NO_READER_HAD_RUN_WHEN_THIS_WAS_COMMITTED = True


def verify() -> dict:
    out = {}
    for rel, expected in INPUT_SHA256.items():
        p = RUN_DIR / rel
        if not p.exists():
            out[rel] = {"PRESENT": False, "EXPECTED_SHA256": expected}
            continue
        got = hashlib.sha256(p.read_bytes()).hexdigest()
        out[rel] = {"PRESENT": True, "EXPECTED_SHA256": expected,
                    "ACTUAL_SHA256": got, "UNCHANGED": got == expected}
    return out


if __name__ == "__main__":
    import json
    c = verify()
    present = [k for k, v in c.items() if v["PRESENT"]]
    print(json.dumps({
        "RUN_ID": RUN_ID,
        "REGISTERED": len(c),
        "PRESENT": len(present),
        "ALL_UNCHANGED": all(c[k]["UNCHANGED"] for k in present),
        "EFFECTIVE_SCALE_VS_BASELINE": EFFECTIVE_SCALE_VS_BASELINE,
    }, indent=2))
