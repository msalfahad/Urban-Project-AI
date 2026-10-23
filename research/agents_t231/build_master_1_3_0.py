"""T-231: build rules/coverage/BOQ_FAMILY_MASTER_1.3.0.json = 1.2.0 (never edited) + the pending ARCH_TAKEOFF_V3.0.8
package (tools/family_master_candidate.py rule r3).

    python3 -I research/agents_t231/build_master_1_3_0.py [--check]

--check rebuilds in memory and exits 1 when the file on disk differs (or the candidate check finds a problem).

Why a new version now: T-203 r2 refuses a head that carries a candidate module newer than the registry's candidate, so
the V3.0.8 module (engine/source/arch_v308.py) makes 1.2.0 stale on any head that carries it. A package cannot name its
own merge commit or checker verdict before the Checker merges it, so V3.0.8 is declared PENDING (status
READY_FOR_GATE_B, its task commit), raises no family state and names no family. Every family, count and released-
configuration field of 1.2.0 is copied unchanged; the candidate of record stays ARCH_TAKEOFF_V3.0.7 (as of T-193). The
registry version after the T-231 merge moves the package to candidate_packages with its merge commit and verdict and
re-derives the two families it changes: STR.CONC.STRAP (straps at the axis length; strap-end overlaps HELD) and
STR.CONC.COLUMN (planted columns: one DRAWING-CONFIRMED, two HELD; five NOT_DRAWN upper column lines HELD, D-65).
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.2.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.3.0.json"
# the commit on agents/task-T-231 that adds engine/source/arch_v308.py (an ancestor of every later head of the branch and
# of the Checker's merge)
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
PENDING = {
    "task": "T-231", "method_version": "ARCH_TAKEOFF_V3.0.8", "module": "engine/source/arch_v308.py",
    "status": FMC.PENDING_STATUS, "integrates": ["T-174", "T-220"],
    "tests": ["tests/t231_arch_v308"],
    "changes_families_by_item_code": ["STR.CONC.STRAP", "STR.CONC.COLUMN"],
    "note": "integration package for Gate B (research/agents_t231/T-231_ARCH_V308.md); names no family until merged",
}


def build(task_commit):
    old = json.loads(OLD.read_text(encoding="utf-8"))
    new = copy.deepcopy(old)
    new["version"] = "1.3.0"
    new["supersedes"] = ("1.2.0 (kept unchanged on disk; every family, count and released-configuration field copied "
                         "unchanged)")
    new["source"] = (str(old.get("source", "")) + " | 1.3.0 (T-231): 1.2.0 + pending_packages (rule r3 of "
                     "tools/family_master_candidate.py): ARCH_TAKEOFF_V3.0.8 handed in for Gate B; no family state "
                     "changes until it merges")
    new["pending_packages"] = [dict(PENDING, task_commit=task_commit)]
    return new


def text(doc):
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"


def main(argv):
    if "--check" in argv:
        cur = json.loads(NEW.read_text(encoding="utf-8"))
        tc = cur["pending_packages"][0]["task_commit"]
        ok = NEW.read_text(encoding="utf-8") == text(build(tc))
        bad = FMC.check(cur, root=ROOT, is_ancestor=FMC.git_is_ancestor)
        print("1.3.0 equals its builder:", ok, "| problems:", bad)
        return 0 if ok and not bad else 1
    if not TASK_COMMIT:
        print("--task-commit <40-hex sha of the commit that adds engine/source/arch_v308.py> is required")
        return 2
    NEW.write_text(text(build(TASK_COMMIT)), encoding="utf-8")
    print("written", NEW.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
