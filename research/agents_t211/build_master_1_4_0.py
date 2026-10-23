"""T-211: build rules/coverage/BOQ_FAMILY_MASTER_1.4.0.json = 1.3.0 (never edited) + the pending ARCH_TAKEOFF_V3.0.9
package (tools/family_master_candidate.py rule r3).

    python3 -I research/agents_t211/build_master_1_4_0.py --task-commit <sha> | --check

Why a new version: the V3.0.9 module (engine/source/arch_v309.py) is newer than every registry version on the head,
and a package cannot name its merge commit or checker verdict before the Checker merges it, so V3.0.9 is declared
PENDING (status READY_FOR_GATE_B, its task commit), raises no family state and names no family. Every field of 1.3.0
is copied unchanged (T-231 stays pending there: its move to candidate_packages with the re-derived STR.CONC.STRAP /
STR.CONC.COLUMN families is its own lane I follow-up, not this package). The version after the T-211 merge moves the
package to candidate_packages and re-derives FIN.PLASTER / FIN.PAINT (room faces: 3 lines PROVISIONAL, 2 of them
checker-VERIFIED, 8 HELD ranges, 4 HELD without a figure per code).
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.3.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.4.0.json"
# the commit on agents/task-T-211 that adds engine/source/arch_v309.py (an ancestor of every later head of the branch and
# of the Checker's merge)
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
PENDING = {
    "task": "T-211", "method_version": "ARCH_TAKEOFF_V3.0.9", "module": "engine/source/arch_v309.py",
    "status": FMC.PENDING_STATUS, "integrates": ["T-128", "T-173", "T-227"],
    "tests": ["tests/t211_arch_v309"],
    "changes_families_by_item_code": ["FIN.PLASTER", "FIN.PAINT"],
    "note": "integration package for Gate B (research/agents_t211/T-211_ARCH_V309.md); names no family until merged",
}


def build(task_commit):
    old = json.loads(OLD.read_text(encoding="utf-8"))
    new = copy.deepcopy(old)
    new["version"] = "1.4.0"
    new["supersedes"] = ("1.3.0 (kept unchanged on disk; every family, count, released-configuration field and the "
                         "T-231 pending entry copied unchanged)")
    new["source"] = (str(old.get("source", "")) + " | 1.4.0 (T-211): 1.3.0 + pending ARCH_TAKEOFF_V3.0.9 (rule r3 of "
                     "tools/family_master_candidate.py) handed in for Gate B; no family state changes until it merges")
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
        print("1.4.0 equals its builder:", ok, "| problems:", bad)
        return 0 if ok and not bad else 1
    if not TASK_COMMIT:
        print("--task-commit <40-hex sha of the commit that adds engine/source/arch_v309.py> is required")
        return 2
    NEW.write_text(text(build(TASK_COMMIT)), encoding="utf-8")
    print("written", NEW.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
