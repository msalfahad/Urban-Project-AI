"""T-255: build rules/coverage/BOQ_FAMILY_MASTER_1.14.0.json = 1.13.0 (never edited) + the pending ARCH_TAKEOFF_V3.0.19
package (tools/family_master_candidate.py rule r3).

    python3 -I research/agents_t255/build_master_1_14_0.py --task-commit <sha> | --check

Why a new version: the V3.0.19 module (engine/source/arch_v3019.py) is newer than every registry version on the head,
and a package cannot name its merge commit or checker verdict before the Checker merges it, so V3.0.19 is declared
PENDING (status READY_FOR_GATE_B, its task commit), raises no family state and names no family. Every field of 1.13.0
is copied unchanged (the T-266 V3.0.18 entry included: the Checker moves merged packages in the next version).
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.13.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.14.0.json"
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
PENDING = {
    "task": "T-255", "method_version": "ARCH_TAKEOFF_V3.0.19", "module": "engine/source/arch_v3019.py",
    "status": FMC.PENDING_STATUS, "integrates": ["T-254", "T-232", "T-249", "T-250", "T-285", "T-292"],
    "tests": ["tests/t255_end_closure"],
    "changes_families_by_item_code": [],
    "note": "T-255 (research/agents_t255/T-255_RING_AND_OPENING_TRACE.md): the ring ground beam BAND0043 closed on its "
            "drawn faces (Checker F-T254-01: 1.7349 -> 1.746943 m3, DRAWING-CONFIRMED) and the W03 / W18 opening "
            "deduction trace (no line changed); the Gate B integration package; names no family until merged",
}


def build(task_commit):
    old = json.loads(OLD.read_text(encoding="utf-8"))
    new = copy.deepcopy(old)
    new["version"] = "1.14.0"
    new["supersedes"] = ("1.13.0 (kept unchanged on disk; every family, count, released-configuration field and the "
                         "pending entries up to T-266 copied unchanged)")
    new["source"] = (str(old.get("source", "")) + " | 1.14.0 (T-255): 1.13.0 + pending ARCH_TAKEOFF_V3.0.19 "
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
        print("1.14.0 equals its builder:", ok, "| problems:", bad)
        return 0 if ok and not bad else 1
    if not TASK_COMMIT:
        print("--task-commit <40-hex sha of the commit that adds engine/source/arch_v3019.py> is required")
        return 2
    NEW.write_text(text(build(TASK_COMMIT)), encoding="utf-8")
    print("written", NEW.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
