"""T-266: build rules/coverage/BOQ_FAMILY_MASTER_1.13.0.json = 1.12.0 (never edited) + the pending ARCH_TAKEOFF_V3.0.18
package (tools/family_master_candidate.py rule r3).

    python3 -I research/agents_t266/build_master_1_13_0.py --task-commit <sha> | --check

Why a new version: the V3.0.18 module (engine/source/arch_v3018.py) is newer than every registry version on the head,
and a package cannot name its merge commit or checker verdict before the Checker merges it, so V3.0.18 is declared
PENDING (status READY_FOR_GATE_B, its task commit), raises no family state and names no family. Every field of 1.12.0
is copied unchanged (the T-254 V3.0.17 entry included: the Checker moves merged packages in the next version).
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.12.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.13.0.json"
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
PENDING = {
    "task": "T-266", "method_version": "ARCH_TAKEOFF_V3.0.18", "module": "engine/source/arch_v3018.py",
    "status": FMC.PENDING_STATUS, "integrates": ["T-290", "T-258", "T-289", "T-278", "T-286", "T-254"],
    "tests": ["tests/t266_component_closure"],
    "changes_families_by_item_code": [],
    "note": "T-266 (research/agents_t266/T-266_COMPONENT_CLOSURE.md): stair lines brought to the merged T-290 / T-258 r2 "
            "component ledger line id by line id (three held lines split: 1.227952 m3 VERIFIED, 1.536225 ASSUMED - "
            "OWNER-APPROVED Q-50 A cond, 0.100286 DRAWING-CONFIRMED on their own lines, the remainder blank; MS2-LD "
            "0.4696 DRAWING-CONFIRMED; ST-03 HELD blank on the T-289 row), the 1F arrival landing marble material "
            "line (T-278, Q-66 B), the GF pantry piece 1.100 m2 WET (T-286, Q-37 A); dome drums a named omission; "
            "the Gate B integration package; names no family until merged",
}


def build(task_commit):
    old = json.loads(OLD.read_text(encoding="utf-8"))
    new = copy.deepcopy(old)
    new["version"] = "1.13.0"
    new["supersedes"] = ("1.12.0 (kept unchanged on disk; every family, count, released-configuration field and the "
                         "pending entries up to T-254 copied unchanged)")
    new["source"] = (str(old.get("source", "")) + " | 1.13.0 (T-266): 1.12.0 + pending ARCH_TAKEOFF_V3.0.18 "
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
        print("1.13.0 equals its builder:", ok, "| problems:", bad)
        return 0 if ok and not bad else 1
    if not TASK_COMMIT:
        print("--task-commit <40-hex sha of the commit that adds engine/source/arch_v3018.py> is required")
        return 2
    NEW.write_text(text(build(TASK_COMMIT)), encoding="utf-8")
    print("written", NEW.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
