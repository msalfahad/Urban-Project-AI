"""T-343: build rules/coverage/BOQ_FAMILY_MASTER_1.20.0.json = 1.19.0 (never edited) + the pending ARCH_TAKEOFF_V3.0.25
package (tools/family_master_candidate.py rule r3).

    python3 -I research/agents_t343/build_master_1_20_0.py --task-commit <sha> | --check

Why a new version: the V3.0.25 module (engine/source/arch_v3025.py) is newer than every registry version on the head,
and a package cannot name its merge commit or checker verdict before the Checker merges it, so V3.0.25 is declared
PENDING (status READY_FOR_GATE_B, its task commit), raises no family state and names no family. Every field of 1.19.0
is copied unchanged (the T-338 V3.0.24 entry included: the Checker moves merged packages in the next version). When
merged, V3.0.25 is the first candidate line of family B13-02 (interlock / external paving, NOT_IMPLEMENTED today) and
adds outdoor marble (E1 treads / risers / landing), outdoor porcelain and the HELD pool water-face finish: the family
states move only with the Checker's verdict, in the next version.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.19.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.20.0.json"
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
PENDING = {
    "task": "T-343", "method_version": "ARCH_TAKEOFF_V3.0.25", "module": "engine/source/arch_v3025.py",
    "status": FMC.PENDING_STATUS, "integrates": ["T-342", "T-157", "T-183"],
    "tests": ["tests/t343_outdoor_floor_integration"],
    "changes_families_by_item_code": [],
    "note": "T-343 (research/agents_t343/T-343_OUTDOOR_FLOOR_INTEGRATION.md): an OMISSION closed: the GF court face "
            "(T-342 binding, T-157 pieces) as 7 outdoor floor lines (west court interlock 119.5416 m2 ASSUMED - "
            "OWNER-APPROVED; north side walk porcelain 21.0142 m2 with the owner manual 23.955 beside; E1 marble "
            "treads 3.3594, risers 1.96, landing 5.1794 m2; covered porch 10.6785 and pool deck 6.548912 m2 (r2, "
            "R-T343-1: face to the glazed band's court face ARC 201, less the exact D), finish HELD as ranges [a, a]) "
            "and the pool water-face finish HELD BLANK (bound 21.308727 m2, finished depth 1.15 from DIMENSION 2E5E); "
            "the plan pieces close on the face less the exact pool D, less the SX-02 glazing reveal strip 0.561577 "
            "(held with T-154, never deck), with the T-157 frame-line tessellation -0.004653 named, within 0.0009 m2 "
            "(T-157 re-add rounding); every V3.0.24 line byte-identical; the Gate B integration package r2; names "
            "no family",
}


def build(task_commit):
    old = json.loads(OLD.read_text(encoding="utf-8"))
    new = copy.deepcopy(old)
    new["version"] = "1.20.0"
    new["supersedes"] = ("1.19.0 (kept unchanged on disk; every family, count, released-configuration field and the "
                         "pending entries up to T-338 copied unchanged)")
    new["source"] = (str(old.get("source", "")) + " | 1.20.0 (T-343): 1.19.0 + pending ARCH_TAKEOFF_V3.0.25 "
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
        print("1.20.0 equals its builder:", ok, "| problems:", bad)
        return 0 if ok and not bad else 1
    if not TASK_COMMIT:
        print("--task-commit <40-hex sha of the commit that adds engine/source/arch_v3025.py> is required")
        return 2
    NEW.write_text(text(build(TASK_COMMIT)), encoding="utf-8")
    print("written", NEW.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
