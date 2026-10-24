"""T-270: build rules/coverage/BOQ_FAMILY_MASTER_1.10.0.json = 1.9.0 (never edited) + the pending ARCH_TAKEOFF_V3.0.15
package (tools/family_master_candidate.py rule r3).

    python3 -I research/agents_t270/build_master_1_10_0.py --task-commit <sha> | --check

Why a new version: the V3.0.15 module (engine/source/arch_v3015.py) is newer than every registry version on the head,
and a package cannot name its merge commit or checker verdict before the Checker merges it, so V3.0.15 is declared
PENDING (status READY_FOR_GATE_B, its task commit), raises no family state and names no family. The new line family
WATERPROOFING.FOUNDATION (BOQ family B8-08 foundations / below-grade, NOT_IMPLEMENTED in 1.9.0; the screed lines belong to B3-05, IMPLEMENTED_NOT_INTEGRATED in 1.9.0) is
named in the note and its item codes listed; the family states move only in the post-merge registry version (lane I).
Every field of 1.9.0 is copied unchanged (the T-231 / T-211 / T-232 / T-239 / T-146 / T-268 / T-240 pending entries stay
as they were).
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.9.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.10.0.json"
# the commit on agents/task-T-270 that adds engine/source/arch_v3015.py (an ancestor of every later head of the branch and
# of the Checker's merge)
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
PENDING = {
    "task": "T-270", "method_version": "ARCH_TAKEOFF_V3.0.15", "module": "engine/source/arch_v3015.py",
    "status": FMC.PENDING_STATUS, "integrates": ["T-219", "T-263"],
    "tests": ["tests/t270_foundation_wp_lines"],
    "changes_families_by_item_code": ["WP.FOUNDATION.FOOTING_MEMBRANE", "WP.FOUNDATION.FOOTING_SCREED",
                                      "WP.FOUNDATION.FOOTING_SIDES", "WP.FOUNDATION.LIFT_PIT_MEMBRANE",
                                      "WP.FOUNDATION.LIFT_PIT_BOARD", "WP.FOUNDATION.LIFT_PIT_SCREED",
                                      "WP.FOUNDATION.BURIED_LIQUID", "WP.FOUNDATION.PROCUREMENT"],
    "note": "T-270 (research/agents_t270/T-270_FOUNDATION_WP.md): a new line family WATERPROOFING.FOUNDATION (BOQ "
            "family B8-08 foundations / below-grade, NOT_IMPLEMENTED in 1.9.0; screed lines B3-05, "
            "IMPLEMENTED_NOT_INTEGRATED in 1.9.0): footing underlay "
            "membrane and protection screed on the footing outline (T-219, never the blinding), lift-pit membrane / "
            "board / screed (T-219), liquid coating of buried ground-beam faces (T-263); released parts as merged, "
            "held parts blank; the Gate B integration package; names no family until merged",
}


def build(task_commit):
    old = json.loads(OLD.read_text(encoding="utf-8"))
    new = copy.deepcopy(old)
    new["version"] = "1.10.0"
    new["supersedes"] = ("1.9.0 (kept unchanged on disk; every family, count, released-configuration field and the "
                         "T-231 / T-211 / T-232 / T-239 / T-146 / T-268 / T-240 pending entries copied unchanged)")
    new["source"] = (str(old.get("source", "")) + " | 1.10.0 (T-270): 1.9.0 + pending ARCH_TAKEOFF_V3.0.15 "
                     "(rule r3 of tools/family_master_candidate.py); no family state changes until it merges")
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
        print("1.10.0 equals its builder:", ok, "| problems:", bad)
        return 0 if ok and not bad else 1
    if not TASK_COMMIT:
        print("--task-commit <40-hex sha of the commit that adds engine/source/arch_v3015.py> is required")
        return 2
    NEW.write_text(text(build(TASK_COMMIT)), encoding="utf-8")
    print("written", NEW.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
