"""T-319: build rules/coverage/BOQ_FAMILY_MASTER_1.18.0.json = 1.17.0 (never edited) + the pending ARCH_TAKEOFF_V3.0.23
package (tools/family_master_candidate.py rule r3).

    python3 -I research/agents_t319/build_master_1_18_0.py --task-commit <sha> | --check

Why a new version: the V3.0.23 module (engine/source/arch_v3023.py) is newer than every registry version on the head,
and a package cannot name its merge commit or checker verdict before the Checker merges it, so V3.0.23 is declared
PENDING (status READY_FOR_GATE_B, its task commit), raises no family state and names no family. Every field of 1.17.0
is copied unchanged (the T-331 V3.0.22 entry included: the Checker moves merged packages in the next version). Once
merged, the parapet concrete family (B10-12, STR.CONC.PARAPET) is HELD in the candidate: every line blank with its
bound, released_in_candidate "none".
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.17.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.18.0.json"
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
PENDING = {
    "task": "T-319", "method_version": "ARCH_TAKEOFF_V3.0.23", "module": "engine/source/arch_v3023.py",
    "status": FMC.PENDING_STATUS, "integrates": ["T-311", "T-324"],
    "tests": ["tests/t319_parapet_rc_integration"],
    "changes_families_by_item_code": [],
    "note": "T-319 (research/agents_t319/T-319_PARAPET_RC_INTEGRATION.md): the RC part of every roof / terrace parapet "
            "run, a structural category no candidate line carried (MISSING: the beam lines stop at the slab top), "
            "added as its own concrete family STR.CONC.PARAPET, one line per roof chain (annex, GF terrace, 1F roof, "
            "2F roof; 25 runs = the 24 T-311 runs + the T-324 C5 annex boundary run), each BLOCKED (HELD, BLANK) "
            "with its bound beside it: floor top x 0.30 (DRAWING-CONFIRMED, any b_edge) 8.0509 m3, lower bound "
            "max(0.30, b_edge + margin) x top HELD (F-T311-C1), all RC 18.9809 .. 20.0953 m3 at b_edge 0 + 26.9725 "
            "m3 per m of b_edge (open); material per run Q-65 C (designer), b_edge D-39; the block alternative stays "
            "in MAS.BLOCK (exclusive, never added); the Gate B integration package; names no family until merged",
}


def build(task_commit):
    old = json.loads(OLD.read_text(encoding="utf-8"))
    new = copy.deepcopy(old)
    new["version"] = "1.18.0"
    new["supersedes"] = ("1.17.0 (kept unchanged on disk; every family, count, released-configuration field and the "
                         "pending entries up to T-331 copied unchanged)")
    new["source"] = (str(old.get("source", "")) + " | 1.18.0 (T-319): 1.17.0 + pending ARCH_TAKEOFF_V3.0.23 "
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
        print("1.18.0 equals its builder:", ok, "| problems:", bad)
        return 0 if ok and not bad else 1
    if not TASK_COMMIT:
        print("--task-commit <40-hex sha of the commit that adds engine/source/arch_v3023.py> is required")
        return 2
    NEW.write_text(text(build(TASK_COMMIT)), encoding="utf-8")
    print("written", NEW.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
