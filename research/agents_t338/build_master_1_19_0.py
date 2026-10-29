"""T-338: build rules/coverage/BOQ_FAMILY_MASTER_1.19.0.json = 1.18.0 (never edited) + the pending ARCH_TAKEOFF_V3.0.24
package (tools/family_master_candidate.py rule r3).

    python3 -I research/agents_t338/build_master_1_19_0.py --task-commit <sha> | --check

Why a new version: the V3.0.24 module (engine/source/arch_v3024.py) is newer than every registry version on the head,
and a package cannot name its merge commit or checker verdict before the Checker merges it, so V3.0.24 is declared
PENDING (status READY_FOR_GATE_B, its task commit), raises no family state and names no family. Every field of 1.18.0
is copied unchanged (the T-319 V3.0.23 entry included: the Checker moves merged packages in the next version).
V3.0.24 changes no family state when merged either: it moves no quantity (text and an NA line's gross only).
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.18.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.19.0.json"
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
PENDING = {
    "task": "T-338", "method_version": "ARCH_TAKEOFF_V3.0.24", "module": "engine/source/arch_v3024.py",
    "status": FMC.PENDING_STATUS, "integrates": ["T-334"],
    "tests": ["tests/t338_line_state_v3024"],
    "changes_families_by_item_code": [],
    "note": "T-338 (research/agents_t338/T-338_LINE_STATE_INTEGRATION.md): the merged T-334 line-state findings fixed in "
            "the candidate's line TEXT only: 350 released STR.REBAR ledger lines (8,311.066 kg) print count x length "
            "x d^2/162 = kg from their own records instead of the empty 'held: ' fallback of arch_v303; the "
            "NOT_APPLICABLE skirting line drops its gross 7.6 lm (kept on record); 15 finish / space lines end their "
            "formula on their own net or held range; no quantity, state word, range or line id moves (every line's "
            "quantity byte-identical to V3.0.23); the Gate B integration package; names no family",
}


def build(task_commit):
    old = json.loads(OLD.read_text(encoding="utf-8"))
    new = copy.deepcopy(old)
    new["version"] = "1.19.0"
    new["supersedes"] = ("1.18.0 (kept unchanged on disk; every family, count, released-configuration field and the "
                         "pending entries up to T-319 copied unchanged)")
    new["source"] = (str(old.get("source", "")) + " | 1.19.0 (T-338): 1.18.0 + pending ARCH_TAKEOFF_V3.0.24 "
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
        print("1.19.0 equals its builder:", ok, "| problems:", bad)
        return 0 if ok and not bad else 1
    if not TASK_COMMIT:
        print("--task-commit <40-hex sha of the commit that adds engine/source/arch_v3024.py> is required")
        return 2
    NEW.write_text(text(build(TASK_COMMIT)), encoding="utf-8")
    print("written", NEW.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
