"""T-327: build rules/coverage/BOQ_FAMILY_MASTER_1.24.0.json = 1.23.0 (never edited) + the pending ARCH_TAKEOFF_V3.0.29
package (tools/family_master_candidate.py rule r3).

    python3 -I research/agents_t327/build_master_1_24_0.py --task-commit <sha> | --check

Why a new version: the V3.0.29 module (engine/source/arch_v3029.py) is newer than every registry version on the head,
and a package cannot name its merge commit or checker verdict before the Checker merges it, so V3.0.29 is declared
PENDING (status READY_FOR_GATE_B, its task commit), raises no family state and names no family. Every field of 1.23.0
is copied unchanged (the T-326 V3.0.28 entry included). The sills / thresholds family states move only with the
Checker's verdict.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.23.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.24.0.json"
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
PENDING = {
    "task": "T-327", "method_version": "ARCH_TAKEOFF_V3.0.29", "module": "engine/source/arch_v3029.py",
    "status": FMC.PENDING_STATUS, "integrates": ["T-325", "T-340"],
    "tests": ["tests/t327_sill_threshold"],
    "changes_families_by_item_code": [],
    "note": "T-327 (research/agents_t327/T-327_SILLS_THRESHOLDS_INTEGRATION.md): sills and thresholds as their own item "
            "from the merged T-325 ledger bound by the merged T-340 FILL table: the five BLOCKED ARCH.THRESHOLD closure "
            "strips retired and booked once at clear width x wall thickness (4 FIN.MARBLE.THRESHOLD 0.480 m2, 1 "
            "FIN.FLOOR.PORCELAIN 0.150 m2; 4.200 m.l, 5 pcs), the closure polygons superseded by their traces; gate "
            "D-GF-15 one BLANK ARCH.THRESHOLD line; every other V3.0.28 line byte-identical (54 carried strips asserted); "
            "the Gate B integration package; names no family",
}


def build(task_commit):
    old = json.loads(OLD.read_text(encoding="utf-8"))
    new = copy.deepcopy(old)
    new["version"] = "1.24.0"
    new["supersedes"] = ("1.23.0 (kept unchanged on disk; every family, count, released-configuration field and the "
                         "pending entries up to T-326 copied unchanged)")
    new["source"] = (str(old.get("source", "")) + " | 1.24.0 (T-327): 1.23.0 + pending ARCH_TAKEOFF_V3.0.29 "
                     "(rule r3 of tools/family_master_candidate.py); no family state changes")
    new["pending_packages"] = list(old.get("pending_packages") or []) + [dict(PENDING, task_commit=task_commit)]
    return new


def text(doc):
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"


def main(argv):
    if "--check" in argv:
        cur = json.loads(NEW.read_text(encoding="utf-8"))
        tc = cur["pending_packages"][-1]["task_commit"]
        ok = NEW.read_text(encoding="utf-8") == text(build(tc))
        bad = FMC.check(cur, root=ROOT, is_ancestor=FMC.git_is_ancestor)
        print("1.24.0 equals its builder:", ok, "| problems:", bad)
        return 0 if ok and not bad else 1
    if not TASK_COMMIT:
        print("--task-commit <40-hex sha of the commit that adds engine/source/arch_v3029.py> is required")
        return 2
    NEW.write_text(text(build(TASK_COMMIT)), encoding="utf-8")
    print("written", NEW.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
