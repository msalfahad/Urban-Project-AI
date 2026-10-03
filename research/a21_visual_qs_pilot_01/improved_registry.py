"""The improved run's frozen artifacts, registered by hash as they appear.

data/ is gitignored, so the artifacts cannot be committed. Their hashes
can, and each pass's entry is committed BEFORE the next pass returns.
That ordering is the evidence that no pass was adjusted in the light of
another - it is visible in the git history, not just asserted here.

    python3 -m research.a21_visual_qs_pilot_01.improved_registry
"""

from __future__ import annotations

import hashlib
from pathlib import Path

RUN_DIR = Path("data/experiments/A21_VISUAL_QS_PILOT_01")
RUN_ID = "A21_SOURCE_PRESENTATION_IMPROVED"

# ------------------------------------------------------------------
# PASS 1 - frozen and committed while pass 2 had not yet been launched
# ------------------------------------------------------------------
PASS1_FREEZE_SHA256 = (
    "3d338e74a675280b7edfd60ebe5c4175027c3f69064d562d9242d7059ff9002c")
PASS1_READER_SHA256 = {
    "improved_raw/IMP_PASS1_cases_1_3.json":
        "bbf970768f2c05d4db68cc844c6b9864186fd2a1a188545954dee0ba46e1926c",
    "improved_raw/IMP_PASS1_cases_4_6.json":
        "37cfde7bc7b1fe75f2c91b7013438a0531034a23cfdd242afe97b6a542641893",
}

# ------------------------------------------------------------------
# PASS 2 - filled in after it freezes, in its own commit
# ------------------------------------------------------------------
PASS2_FREEZE_SHA256 = (
    "8fedccb529328eeb4b1db8394eb264cc4c4facfa52b6bcc91fe8da77963282ad")
PASS2_READER_SHA256 = {
    "improved_raw/IMP_PASS2_cases_1_3.json":
        "cc66fd38e9121fbc1a3b9791836f0ef2430c4e22d5b1e0f9073d33685ca6a455",
    "improved_raw/IMP_PASS2_cases_4_6.json":
        "b5a0a1e6754e1a65bd0c626f2f01a839e4b1261db78172f845a0f1b192d5eba0",
}

COMPARISON_SHA256 = (
    "e58c3e09bced87546692a57d629dcd85b0b8159dc228ea7e88b098fa0b1f3344")
FINDINGS_SHA256 = (
    "ffacc11cb7266159c3e1b676c404ad0d437a233daef0f61de6c1457ce69fcd91")

ORDER_OF_OPERATIONS = (
    "improved protocol declared and hashed",
    "packets built, screened and committed",
    "prompts generated from the frozen baseline bytes and committed",
    "the measuring instrument written and validated on the baseline",
    "pass 1 read, frozen alone, and its hash committed",
    "only then: pass 2 launched",
    "pass 2 frozen alone",
    "only then: the baseline-vs-improved comparison",
)


def _registered() -> dict:
    out = dict(PASS1_READER_SHA256)
    out.update(PASS2_READER_SHA256)
    if PASS1_FREEZE_SHA256:
        out["IMPROVED_PASS1_FREEZE.json"] = PASS1_FREEZE_SHA256
    if PASS2_FREEZE_SHA256:
        out["IMPROVED_PASS2_FREEZE.json"] = PASS2_FREEZE_SHA256
    if COMPARISON_SHA256:
        out["A21_SOURCE_PRESENTATION_COMPARISON.json"] = COMPARISON_SHA256
    if FINDINGS_SHA256:
        out["A21_SOURCE_PRESENTATION_FINDINGS.json"] = FINDINGS_SHA256
    return out


def verify() -> dict:
    out = {}
    for rel, expected in _registered().items():
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
        "PASS2_REGISTERED_YET": PASS2_FREEZE_SHA256 is not None,
        "COMPARISON_REGISTERED_YET": COMPARISON_SHA256 is not None,
    }, indent=2))
