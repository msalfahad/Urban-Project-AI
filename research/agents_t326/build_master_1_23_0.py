"""T-326: build rules/coverage/BOQ_FAMILY_MASTER_1.23.0.json = 1.22.0 (never edited) + the pending ARCH_TAKEOFF_V3.0.28
package (tools/family_master_candidate.py rule r3).

    python3 -I research/agents_t326/build_master_1_23_0.py --task-commit <sha> | --check

Why a new version: the V3.0.28 module (engine/source/arch_v3028.py) is newer than every registry version on the head,
and a package cannot name its merge commit or checker verdict before the Checker merges it, so V3.0.28 is declared
PENDING (status READY_FOR_GATE_B, its task commit), raises no family state and names no family. Every field of 1.22.0
is copied unchanged (the T-318 V3.0.27 entry included). The B4-08 'Reveals and returns' family state moves only with
the Checker's verdict.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.22.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.23.0.json"
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
PENDING = {
    "task": "T-326", "method_version": "ARCH_TAKEOFF_V3.0.28", "module": "engine/source/arch_v3028.py",
    "status": FMC.PENDING_STATUS, "integrates": ["T-313", "T-325"],
    "tests": ["tests/t326_reveal_fill"],
    "changes_families_by_item_code": [],
    "note": "T-326 (research/agents_t326/T-326_OPENING_REVEAL_INTEGRATION.md): the opening reveal faces from the merged "
            "T-313 r2 ledger, cross-checked row by row against the merged T-325 sills ledger: 26 blank ARCH.WINDOW_REVEAL "
            "lines filled with the outside sill / floor-level threshold only (2.9294 m2), FIN.PLASTER D-GF-07 narrowed "
            "to 1.400 m2 at the printed 2.50, missing scope added once per opening / side / item (window outside jambs "
            "+ head 9.6670 m2 ARCH.REVEAL, W18 sill 0.040 m2, five unlined doors 3.930 m2 FIN.PLASTER), held faces "
            "BLANK by name (10 lines); every other V3.0.27 line byte-identical; the Gate B integration package; names "
            "no family",
}


def build(task_commit):
    old = json.loads(OLD.read_text(encoding="utf-8"))
    new = copy.deepcopy(old)
    new["version"] = "1.23.0"
    new["supersedes"] = ("1.22.0 (kept unchanged on disk; every family, count, released-configuration field and the "
                         "pending entries up to T-318 copied unchanged)")
    new["source"] = (str(old.get("source", "")) + " | 1.23.0 (T-326): 1.22.0 + pending ARCH_TAKEOFF_V3.0.28 "
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
        print("1.23.0 equals its builder:", ok, "| problems:", bad)
        return 0 if ok and not bad else 1
    if not TASK_COMMIT:
        print("--task-commit <40-hex sha of the commit that adds engine/source/arch_v3028.py> is required")
        return 2
    NEW.write_text(text(build(TASK_COMMIT)), encoding="utf-8")
    print("written", NEW.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
