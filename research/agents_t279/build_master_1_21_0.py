"""T-279: build rules/coverage/BOQ_FAMILY_MASTER_1.21.0.json = 1.20.0 (never edited) + the pending ARCH_TAKEOFF_V3.0.26
package (tools/family_master_candidate.py rule r3).

    python3 -I research/agents_t279/build_master_1_21_0.py --task-commit <sha> | --check

Why a new version: the V3.0.26 module (engine/source/arch_v3026.py) is newer than every registry version on the head,
and a package cannot name its merge commit or checker verdict before the Checker merges it, so V3.0.26 is declared
PENDING (status READY_FOR_GATE_B, its task commit), raises no family state and names no family. Every field of 1.20.0
is copied unchanged (the T-343 V3.0.25 entry included). When merged, V3.0.26 is the first candidate quantity of family
B9-01 (block walls by type and thickness, PARTIAL): the family state moves only with the Checker's verdict.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.20.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.21.0.json"
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
PENDING = {
    "task": "T-279", "method_version": "ARCH_TAKEOFF_V3.0.26", "module": "engine/source/arch_v3026.py",
    "status": FMC.PENDING_STATUS, "integrates": ["T-333", "T-291", "T-288", "T-261", "T-274"],
    "tests": ["tests/t279_blockwork_integration"],
    "changes_families_by_item_code": [],
    "note": "T-279 (research/agents_t279/T-279_BLOCKWORK_INTEGRATION.md): the 21 held storey / thickness blockwork "
            "lines (MAS.BLOCK, ARCH.WALL_PANEL m2, ARCH.WALL_VOLUME m3; BLOCKED_RFI blank since V3.0.15) carry the "
            "T-333 r2 fill wall by wall: closable walls on their own lines by status and block type (MAS.BLOCK "
            "579.1011 m2 = VERIFIED 297.847 on 18 walls + DRAWING-CONFIRMED 157.6488 + ASSUMED - OWNER-APPROVED "
            "123.6053 (Q-55 C doors); m3 = m2 x t), the parents BLANK with every held wall, drop term (46.8019 - "
            "7.9131 d m2, never evaluated), held piece and width-CONFLICT increment named; every other V3.0.25 "
            "line byte-identical; the Gate B integration package; names no family",
}


def build(task_commit):
    old = json.loads(OLD.read_text(encoding="utf-8"))
    new = copy.deepcopy(old)
    new["version"] = "1.21.0"
    new["supersedes"] = ("1.20.0 (kept unchanged on disk; every family, count, released-configuration field and the "
                         "pending entries up to T-343 copied unchanged)")
    new["source"] = (str(old.get("source", "")) + " | 1.21.0 (T-279): 1.20.0 + pending ARCH_TAKEOFF_V3.0.26 "
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
        print("1.21.0 equals its builder:", ok, "| problems:", bad)
        return 0 if ok and not bad else 1
    if not TASK_COMMIT:
        print("--task-commit <40-hex sha of the commit that adds engine/source/arch_v3026.py> is required")
        return 2
    NEW.write_text(text(build(TASK_COMMIT)), encoding="utf-8")
    print("written", NEW.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
