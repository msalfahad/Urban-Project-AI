"""T-315: build rules/coverage/BOQ_FAMILY_MASTER_1.16.0.json = 1.15.0 (never edited) + the pending ARCH_TAKEOFF_V3.0.21
package (tools/family_master_candidate.py rule r3).

    python3 -I research/agents_t244/build_master_1_16_0.py --task-commit <sha> | --check

Why a new version: the V3.0.21 module (engine/source/arch_v3021.py) is newer than every registry version on the head,
and a package cannot name its merge commit or checker verdict before the Checker merges it, so V3.0.21 is declared
PENDING (status READY_FOR_GATE_B, its task commit), raises no family state and names no family. Every field of 1.15.0
is copied unchanged (the T-244 V3.0.20 entry included: the Checker moves merged packages in the next version).
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.15.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.16.0.json"
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
PENDING = {
    "task": "T-315", "method_version": "ARCH_TAKEOFF_V3.0.21", "module": "engine/source/arch_v3021.py",
    "status": FMC.PENDING_STATUS, "integrates": ["T-312"],
    "tests": ["tests/t315_wall_tile_family"],
    "changes_families_by_item_code": [],
    "note": "T-315 (research/agents_t315/T-315_WALL_TILE_FAMILY.md): the wall-tile family FIN.WALL.TILE from the "
            "merged T-312 face ledger: 11 blank lines filled 307.9616 m2 (ASSUMED - OWNER-APPROVED: Q-48 A heights, "
            "Q-55 C door heads), 6 lines kept BLANK (annex G2 / Q-54 B / D-39; GF-10 / GF-11 level T-088), ONE new "
            "pantry line 32.3422 m2 (UP-PANTRY-003 host walls); paint of every tiled room carries no figure "
            "(asserted); the Gate B integration package; names no family until merged",
}


def build(task_commit):
    old = json.loads(OLD.read_text(encoding="utf-8"))
    new = copy.deepcopy(old)
    new["version"] = "1.16.0"
    new["supersedes"] = ("1.15.0 (kept unchanged on disk; every family, count, released-configuration field and the "
                         "pending entries up to T-244 copied unchanged)")
    new["source"] = (str(old.get("source", "")) + " | 1.16.0 (T-315): 1.15.0 + pending ARCH_TAKEOFF_V3.0.21 "
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
        print("1.16.0 equals its builder:", ok, "| problems:", bad)
        return 0 if ok and not bad else 1
    if not TASK_COMMIT:
        print("--task-commit <40-hex sha of the commit that adds engine/source/arch_v3021.py> is required")
        return 2
    NEW.write_text(text(build(TASK_COMMIT)), encoding="utf-8")
    print("written", NEW.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
