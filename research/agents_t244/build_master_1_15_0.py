"""T-244: build rules/coverage/BOQ_FAMILY_MASTER_1.15.0.json = 1.14.0 (never edited) + the pending ARCH_TAKEOFF_V3.0.20
package (tools/family_master_candidate.py rule r3).

    python3 -I research/agents_t244/build_master_1_15_0.py --task-commit <sha> | --check

Why a new version: the V3.0.20 module (engine/source/arch_v3020.py) is newer than every registry version on the head,
and a package cannot name its merge commit or checker verdict before the Checker merges it, so V3.0.20 is declared
PENDING (status READY_FOR_GATE_B, its task commit), raises no family state and names no family. Every field of 1.14.0
is copied unchanged (the T-255 V3.0.19 entry included: the Checker moves merged packages in the next version).
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.14.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.15.0.json"
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
PENDING = {
    "task": "T-244", "method_version": "ARCH_TAKEOFF_V3.0.20", "module": "engine/source/arch_v3020.py",
    "status": FMC.PENDING_STATUS, "integrates": ["T-302", "T-238", "T-237", "T-227", "T-255"],
    "tests": ["tests/t244_finish_revision"],
    "changes_families_by_item_code": [],
    "note": "T-244 (research/agents_t244/T-244_FINISH_REVISION.md): the internal plaster / paint room-face lines take "
            "the opening outlines merged ledgers settled (1F-11 W17 room-side hole 8.7414 .. 8.9965 HELD: the released "
            "59.4511 leaves the released total, BOUNDED 61.4626 .. 61.7177 m2 each code; 1F-13 W15 / W16 4.3629 each); "
            "the Gate B integration package; names no family until merged",
}


def build(task_commit):
    old = json.loads(OLD.read_text(encoding="utf-8"))
    new = copy.deepcopy(old)
    new["version"] = "1.15.0"
    new["supersedes"] = ("1.14.0 (kept unchanged on disk; every family, count, released-configuration field and the "
                         "pending entries up to T-255 copied unchanged)")
    new["source"] = (str(old.get("source", "")) + " | 1.15.0 (T-244): 1.14.0 + pending ARCH_TAKEOFF_V3.0.20 "
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
        print("1.15.0 equals its builder:", ok, "| problems:", bad)
        return 0 if ok and not bad else 1
    if not TASK_COMMIT:
        print("--task-commit <40-hex sha of the commit that adds engine/source/arch_v3020.py> is required")
        return 2
    NEW.write_text(text(build(TASK_COMMIT)), encoding="utf-8")
    print("written", NEW.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
