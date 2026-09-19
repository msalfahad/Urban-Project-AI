"""The phase's artifacts, registered by hash. PARTIAL - and it says so.

Two of the four trace readers never produced a reading: they terminated
on an API session rate limit. The register, the overlays and the mapping
check therefore cover CASE-1 and CASE-4 only. Nothing has been inferred
for CASE-3 or CASE-6, and no artifact claims coverage it does not have.

    python3 -m research.a21_trace_sufficiency_01.phase_registry
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

RUN_DIR = Path("data/experiments/A21_TRACE_SUFFICIENCY_01")
PHASE_ID = "A21_VISUAL_TRACE_AND_SOURCE_SUFFICIENCY_01"

SUBSET_SELECTION_PROTOCOL_STATUS = "E1_4_INFLUENCED_MEMBERSHIP_UNCHANGED"

ARTIFACT_SHA256 = {
    "PILOT_SUBSET_SELECTION.json":
        "f4ecb254e55fb155806bf5b336b61945b979db157913a7cbe78ecc5cef8fe83c",
    "E1_4_INFLUENCE_AUDIT.json":
        "9c2ec5bbc9a3a13e953a1973069e7be6e1490d48fabd4fbbed0b6bcd98471c22",
    "SHEET_INDEX.json":
        "90cdf51b729107ee455e206cc313e609c5f41d309ce761c6965f7e09419b6d6d",
    "DOCUMENT_GRAPH_CANDIDATES.json":
        "6c6ace14d64bb7cf890104897d17fc9b04a383b00ba6aa5cb39d5c1de7ee7fb4",
    "CASE_SOURCE_REQUIREMENTS.json":
        "2db2baaa8d11db1a0206d15caf1d04c91723fcb0d227a31fe217b010672ea2f3",
    "CONTROLLER_SOURCE_REQUIREMENTS.json":
        "33efa3e9fed3e2e28625e2f22f0e6fafb375343f5329c83b1b8ad9b6d65d68fc",
    "A21_READER_SOURCE_MANIFEST.json":
        "bb656a5e5ec60b83103c246396689ec60dce2bd721a589060a2d824022406c60",
    "CASE_SANDBOX_MANIFESTS.json":
        "6984ba8f741707d3f41f77ae4f94b2bd11514f7db7f71a03a1733807d428d335",
    "VISUAL_TRACE_SCHEMA.json":
        "e5767c03f48a3f777acdd27a4d0da1aed4ca88630564847729f0de75a0edbb6c",
    "TRACE_REGISTER.json":
        "52e7cef808b98b81cba246642c9f8251e0176d6a6ffa533523632b2963707012",
    "OVERLAY_INDEX.json":
        "ebb5242e03c829b36d9328b6acfaecd0dfc160affaf5f843f007303ee124039d",
    "ORIGINAL_SOURCE_MAPPING_TEST.json":
        "ab05b9b75bd1cd49c19086314ce953ea2b4c6adf5750207cf818d2303edd636c",
    "PARAMETER_SCHEMA.json":
        "cca46ba3161cf3c5e428cd7161a1be7536183d56746ede94c39f330cf7018dae",
    "PARAMETRIC_RECALCULATION_TEST.json":
        "eedf2d9ae6a6ae8baabed9a42cb1d04b68d7228433b308b63337c1f517a497ff",
}

TRACE_READING_SHA256 = {
    "trace_raw/CASE-1-NORMAL-PLASTER.json": None,   # filled by verify()
    "trace_raw/CASE-4-STAIR.json": None,
}

# ------------------------------------------------------------------
# what did not happen, recorded as plainly as what did
# ------------------------------------------------------------------
COVERAGE = {
    "SUBSET_FROZEN": ["CASE-1-NORMAL-PLASTER", "CASE-3-DOOR-AND-WINDOW",
                      "CASE-4-STAIR", "CASE-6-ROOF-PARAPET"],
    "TRACED": ["CASE-1-NORMAL-PLASTER", "CASE-4-STAIR"],
    "NOT_TRACED": ["CASE-3-DOOR-AND-WINDOW", "CASE-6-ROOF-PARAPET"],
    "WHY_NOT": (
        "both readers terminated on an API session rate limit before "
        "writing their file. This is an infrastructure failure, not a "
        "finding about the drawing, and nothing about those two cases has "
        "been inferred from the two that completed"),
    "WHAT_THE_SUBSET_LOSES_MEANWHILE": (
        "the opening characteristic and the parapet/balustrade "
        "distinction are both unexercised. CASE-3 carried the opening "
        "traces and CASE-6 the solid-versus-open parapet split, so the "
        "pilot currently demonstrates the schema on a room boundary and a "
        "vertical condition only"),
    "THE_PACKETS_FOR_BOTH_ARE_BUILT_AND_FROZEN": True,
}

RESULTS = {
    "TRACES_ACCEPTED": 119,
    "TRACES_REJECTED": 1,
    "DANGLING_SUPPORTED_BY": 0,
    "SUPPORTED_BY_LINKS_RESOLVED": 74,
    "OVERLAY_IMAGES": 10,
    "ROUND_TRIP_WORST_ERROR_PX": 0.0,
    "RANDOM_POINT_INK_AGREEMENT": 1.0,
    "REAL_TRACE_MAPPING_AGREEMENT": 1.0,
    "REAL_TRACES_CHECKED": 119,
    "PARAMETRIC_RECALCULATION_ALL_CHECKS_PASS": True,
}

# ------------------------------------------------------------------
# defects the phase found in ITSELF
# ------------------------------------------------------------------
SELF_INFLICTED_DEFECTS_FOUND = (
    {"WHAT": "the reader-visible TASK.json carried the pre-read's "
             "interpretations",
     "IMPACT_IF_UNCAUGHT": "the readers would have been told where the "
                           "curved stair is drawn and which dimensions to "
                           "look for; every CASE-1 and CASE-4 trace would "
                           "have been worthless",
     "CAUGHT_BY": "the owner's control, before any reader ran",
     "FIX": "controller/reader split plus a 916-phrase screen"},
    {"WHAT": "the trace validator rejected 43 well-formed dimension traces",
     "IMPACT_IF_UNCAUGHT": "a 36 percent rejection rate would have been "
                           "read as reader failure when it was schema "
                           "failure - the validator never implemented the "
                           "dimension geometry the protocol defines",
     "CAUGHT_BY": "looking at why the rejections happened instead of "
                  "reporting the rate",
     "FIX": "geometry_fields_for() accepts TEXT_BBOX, DIMENSION_LINE_TRACE "
            "and both extension lines for dimension claim types"},
    {"WHAT": "the validator demanded a VALUE_M from every dimension",
     "IMPACT_IF_UNCAUGHT": "a running dimension chain - a real drawing "
                           "construct with five values and no single one - "
                           "was rejected for being honest about it",
     "CAUGHT_BY": "reading the one remaining rejection rather than "
                  "accepting a 1 in 120 loss",
     "FIX": "only an ESTABLISHED dimension must carry a value"},
    {"WHAT": "the first ink-agreement test scored 0.4 to 0.6",
     "IMPACT_IF_UNCAUGHT": "the transform would have been blamed for a "
                           "defect in the test",
     "CAUGHT_BY": "the number being too low to believe",
     "FIX": "compare patches of equal PHYSICAL size, not equal pixel size"},
)


def verify() -> dict:
    out = {}
    for rel, expected in ARTIFACT_SHA256.items():
        p = RUN_DIR / rel
        if not p.exists():
            out[rel] = {"PRESENT": False, "EXPECTED_SHA256": expected}
            continue
        got = hashlib.sha256(p.read_bytes()).hexdigest()
        out[rel] = {"PRESENT": True, "EXPECTED_SHA256": expected,
                    "ACTUAL_SHA256": got, "UNCHANGED": got == expected}
    for rel in TRACE_READING_SHA256:
        p = RUN_DIR / rel
        out[rel] = ({"PRESENT": True,
                     "SHA256": hashlib.sha256(p.read_bytes()).hexdigest()}
                    if p.exists() else {"PRESENT": False})
    return out


if __name__ == "__main__":
    c = verify()
    checked = [k for k, v in c.items() if v.get("EXPECTED_SHA256")
               and v["PRESENT"]]
    print(json.dumps({
        "PHASE_ID": PHASE_ID,
        "SUBSET_SELECTION_PROTOCOL_STATUS": SUBSET_SELECTION_PROTOCOL_STATUS,
        "ARTIFACTS_REGISTERED": len(ARTIFACT_SHA256),
        "ALL_UNCHANGED": all(c[k]["UNCHANGED"] for k in checked),
        "COVERAGE": COVERAGE,
        "RESULTS": RESULTS,
        "TRACE_READINGS": {k: v for k, v in c.items()
                           if k.startswith("trace_raw/")},
    }, indent=2))
