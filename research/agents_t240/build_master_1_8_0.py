"""T-240 WP1: build rules/coverage/BOQ_FAMILY_MASTER_1.8.0.json = 1.7.0 (never edited) + the pending
ARCH_TAKEOFF_V3.0.13 package (tools/family_master_candidate.py rule r3).

    python3 -I research/agents_t240/build_master_1_8_0.py --task-commit <sha> | --check

Why a new version: the V3.0.13 module (engine/source/arch_v3013.py) is newer than every registry version on the head,
and a package cannot name its merge commit or checker verdict before the Checker merges it, so V3.0.13 is declared
PENDING (status READY_FOR_GATE_B once WP4 hands it in, its task commit), raises no family state and names no family.
Every field of 1.7.0 is copied unchanged (the T-231 / T-211 / T-232 / T-239 / T-146 pending entries stay as they were:
their move to candidate_packages with re-derived families is the post-merge registry version, a lane I follow-up).
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.7.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.8.0.json"
# the commit on agents/task-T-240 that adds engine/source/arch_v3013.py (an ancestor of every later head of the branch and
# of the Checker's merge)
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
PENDING = {
    "task": "T-240", "method_version": "ARCH_TAKEOFF_V3.0.13", "module": "engine/source/arch_v3013.py",
    "status": FMC.PENDING_STATUS, "integrates": ["T-223", "T-218"],
    "tests": ["tests/t240_floor_scope"],
    "changes_families_by_item_code": ["FIN.FLOOR.PORCELAIN", "ARCH.SPACE", "ARCH.THRESHOLD"],
    "note": "T-240 work package 1 of 4 (research/agents_t240/T-240_WP1.md): one strip / face, one line - the 1F dressing "
            "into the internal floor line, three sills to held thresholds, the GF side passage to the outdoor key, a "
            "wall-top strip retired; the Gate B hand-in is WP4; names no family until merged",
}


def build(task_commit):
    old = json.loads(OLD.read_text(encoding="utf-8"))
    new = copy.deepcopy(old)
    new["version"] = "1.8.0"
    new["supersedes"] = ("1.7.0 (kept unchanged on disk; every family, count, released-configuration field and the "
                         "T-231 / T-211 / T-232 / T-239 / T-146 pending entries copied unchanged)")
    new["source"] = (str(old.get("source", "")) + " | 1.8.0 (T-240 WP1): 1.7.0 + pending ARCH_TAKEOFF_V3.0.13 "
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
        print("1.8.0 equals its builder:", ok, "| problems:", bad)
        return 0 if ok and not bad else 1
    if not TASK_COMMIT:
        print("--task-commit <40-hex sha of the commit that adds engine/source/arch_v3013.py> is required")
        return 2
    NEW.write_text(text(build(TASK_COMMIT)), encoding="utf-8")
    print("written", NEW.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
