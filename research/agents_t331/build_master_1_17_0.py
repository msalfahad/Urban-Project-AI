"""T-331: build rules/coverage/BOQ_FAMILY_MASTER_1.17.0.json = 1.16.0 (never edited) + the pending ARCH_TAKEOFF_V3.0.22
package (tools/family_master_candidate.py rule r3).

    python3 -I research/agents_t331/build_master_1_17_0.py --task-commit <sha> | --check

Why a new version: the V3.0.22 module (engine/source/arch_v3022.py) is newer than every registry version on the head,
and a package cannot name its merge commit or checker verdict before the Checker merges it, so V3.0.22 is declared
PENDING (status READY_FOR_GATE_B, its task commit), raises no family state and names no family. Every field of 1.16.0
is copied unchanged (the T-315 V3.0.21 entry included: the Checker moves merged packages in the next version).
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.16.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.17.0.json"
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
PENDING = {
    "task": "T-331", "method_version": "ARCH_TAKEOFF_V3.0.22", "module": "engine/source/arch_v3022.py",
    "status": FMC.PENDING_STATUS, "integrates": ["T-329", "T-312", "T-315"],
    "tests": ["tests/t331_wet_backing_integration"],
    "changes_families_by_item_code": [],
    "note": "T-331 (research/agents_t331/T-331_WET_BACKING_INTEGRATION.md): the plaster backing behind the wall tile "
            "(UP-FIN-PAINT-001 substrate, Q-45 B coat) from the merged T-329 ledger into the blank FIN.PLASTER lines "
            "of the tiled rooms, face by face, each bound to its room's own FIN.WALL.TILE line (backing - tile = 0): "
            "11 wet-room lines 307.9616 m2 + the pantry line 32.3422 m2 filled (ASSUMED - OWNER-APPROVED: Q-43 = "
            "Q-48 A heights, Q-55 C door heads), each with its canonical deductions by opening id and the band above "
            "the tile beside it (owner method 0; drawing-derived 0 .. 16.2125 m2 HELD, Q-52 C); 6 lines kept BLANK "
            "(G2 / Q-54 B / D-39; T-088), reason and band 0 .. 6.8845 m2 recorded; two cut skirting notes completed "
            "(L-af6fb2d3, L-71e2e002); the Gate B integration package; names no family until merged",
}


def build(task_commit):
    old = json.loads(OLD.read_text(encoding="utf-8"))
    new = copy.deepcopy(old)
    new["version"] = "1.17.0"
    new["supersedes"] = ("1.16.0 (kept unchanged on disk; every family, count, released-configuration field and the "
                         "pending entries up to T-315 copied unchanged)")
    new["source"] = (str(old.get("source", "")) + " | 1.17.0 (T-331): 1.16.0 + pending ARCH_TAKEOFF_V3.0.22 "
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
        print("1.17.0 equals its builder:", ok, "| problems:", bad)
        return 0 if ok and not bad else 1
    if not TASK_COMMIT:
        print("--task-commit <40-hex sha of the commit that adds engine/source/arch_v3022.py> is required")
        return 2
    NEW.write_text(text(build(TASK_COMMIT)), encoding="utf-8")
    print("written", NEW.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
