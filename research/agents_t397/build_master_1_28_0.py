"""T-397: build rules/coverage/BOQ_FAMILY_MASTER_1.28.0.json = 1.27.0 (never edited) + the pending ARCH_TAKEOFF_V3.0.33
package (tools/family_master_candidate.py rule r3).

    python3 -I research/agents_t397/build_master_1_28_0.py --task-commit <sha> | --check

Why a new version: the V3.0.33 module (engine/source/arch_v3033.py) is newer than every registry version on the head;
a package cannot name its merge commit or checker verdict before the Checker merges it, so V3.0.33 is declared PENDING
(READY_FOR_GATE_B, its task commit), raises no candidate state and names no family in a candidate block.

No new code: V3.0.33 writes only STR.CONC.GROUND_SLAB, STR.CONC.BEAM, STR.CONC.COLUMN (restated lines) and
STR.CONC.LIFT (one new HELD BLANK line, the lift-pit walls: family B10-10 'Pool / tank / lift pit / pump room', which
already owns STR.CONC.LIFT). Every family, every released-configuration field and every pending entry up to T-284 is
copied unchanged. No quantity changes with this file.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.27.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.28.0.json"
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
PENDING = {
    "task": "T-397", "method_version": "ARCH_TAKEOFF_V3.0.33", "module": "engine/source/arch_v3033.py",
    "status": FMC.PENDING_STATUS, "integrates": ["T-391", "T-392", "T-394", "T-256"],
    "tests": ["tests/t397_structural_corrections"],
    "changes_families_by_item_code": [],
    "note": "T-397 (research/agents_t397/T-397_STRUCTURAL_CORRECTIONS.md): structural concrete corrections of "
            "Checker-verified reconciliations line id by line id: the held ground-slab cell's bound to its own slab "
            "panels (T-391 F1), three GF beams restored to their drawn cells (T-146 ring-overlap GAP, T-392) and CB8 "
            "to the carrier face (DOUBLE + GAP apart, T-392), 15 printed-vs-drawn column CONFLICT lines as BOUNDED "
            "ranges (T-394 P1 on the T-256 readings), the missing lift-pit wall line HELD BLANK with its plan ring "
            "beside (T-394 P2, STR.CONC.LIFT, B10-10); every other V3.0.32 line byte-identical; the Gate B "
            "integration package; names no family",
}


def build(task_commit):
    old = json.loads(OLD.read_text(encoding="utf-8"))
    new = copy.deepcopy(old)
    new["version"] = "1.28.0"
    new["supersedes"] = ("1.27.0 (kept unchanged on disk; every family, every released-configuration field and the "
                         "pending entries up to T-284 copied unchanged)")
    new["source"] = (str(old.get("source", "")) + " | 1.28.0 (T-397): 1.27.0 + pending ARCH_TAKEOFF_V3.0.33 (rule r3 "
                     "of tools/family_master_candidate.py); no new code, no family or candidate state changes")
    new["pending_packages"] = list(old.get("pending_packages") or []) + [dict(PENDING, task_commit=task_commit)]
    new["item_code_scan"] += (" | 1.28.0 (T-397): same scan; V3.0.33 writes no new code (STR.CONC.LIFT for the lift-pit "
                              "wall line is B10-10's)")
    return new


def text(doc):
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"


def main(argv):
    if "--check" in argv:
        cur = json.loads(NEW.read_text(encoding="utf-8"))
        tc = cur["pending_packages"][-1]["task_commit"]
        ok = NEW.read_text(encoding="utf-8") == text(build(tc))
        bad = FMC.check(cur, root=ROOT, is_ancestor=FMC.git_is_ancestor)
        print("1.28.0 equals its builder:", ok, "| problems:", bad)
        return 0 if ok and not bad else 1
    if not TASK_COMMIT:
        print("--task-commit <40-hex sha of the commit that adds engine/source/arch_v3033.py> is required")
        return 2
    NEW.write_text(text(build(TASK_COMMIT)), encoding="utf-8")
    print("written", NEW.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
