"""T-399: build rules/coverage/BOQ_FAMILY_MASTER_1.29.0.json = 1.28.0 (never edited) + the pending ARCH_TAKEOFF_V3.0.34
package (tools/family_master_candidate.py rule r3) + the B4-02 coverage binding as evidence on its family row.

    python3 -I research/agents_t399/build_master_1_29_0.py --task-commit <sha> | --check

Why a new version: the V3.0.34 module (engine/source/arch_v3034.py) is newer than every registry version on the head;
a package cannot name its merge commit or checker verdict before the Checker merges it, so V3.0.34 is declared PENDING
(READY_FOR_GATE_B, its task commit), raises no candidate state and names no family in a candidate block.

B4-02 'kitchen / laundry / pantry tiled zones': its released capability stays NOT_IMPLEMENTED (the released V2.9 +
route G is unchanged) and its candidate state stays NOT_IN_CANDIDATE (a pending package raises none). What moves is
the evidence: the family row gains 'coverage_in_candidate' = COVERED_BY_B4-01 (pending T-399), with the file:line of
the binding and the Checker-verified table it rests on, so the family is no longer a silent gap: on a villa where the
owner wet scope reaches the room, the zone IS the wall-tile line (no second quantity); a printed band, or a kitchen open
to a dry plan, stays a real B4-02 line to build (next_slice). No new item code; no quantity changes with this file.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.28.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.29.0.json"
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
PENDING = {
    "task": "T-399", "method_version": "ARCH_TAKEOFF_V3.0.34", "module": "engine/source/arch_v3034.py",
    "status": FMC.PENDING_STATUS, "integrates": ["T-351", "T-388"],
    "tests": ["tests/t399_tile_zones"],
    "changes_families_by_item_code": [],
    "note": "T-399 (research/agents_t399/T-399_TILE_ZONES_INTEGRATION.md): B4-02 kitchen / laundry / pantry tiled "
            "zones from the Checker-verified T-351 face table: each zone (kitchen GF-06 HELD, laundry 1F-07 "
            "52.5290 m2, pantry GF-07 32.3422 m2 on its line, own table 32.3750: residual +0.0328 m2 named, F-T351-1) "
            "bound to its room's FIN.WALL.TILE line, no B4-02 line added (a band on a wall-tile face is the same "
            "tile twice); the pantry paint line HL:WALL_FINISH:GF_07:PAINT BLOCKED_RFI blank -> "
            "NOT_APPLICABLE_WITH_EVIDENCE (T-388 finding d); every other V3.0.33 line byte-identical; the Gate B "
            "integration package; names no family",
}
COVERAGE = {
    "state": "COVERED_BY_B4-01",
    "status": "PENDING (T-399 READY_FOR_GATE_B; not a candidate state until merged)",
    "method_version": "ARCH_TAKEOFF_V3.0.34",
    "evidence": ["engine/source/arch_v3034.py:243-297 zone_check: every verified zone bound to its room's one "
                 "FIN.WALL.TILE line (state / figure as the table read, residual named, backing = carrier, no valued "
                 "paint or ordinary plaster on the room)",
                 "engine/source/arch_v3034.py:300-349 changes_for: ZONE_PAINT_NA (paint under a full-height zone)",
                 "research/agents_t351/CROSSCHECK_T351.csv (T-351 MERGED f0bd9f3c, Gate A PASS): 24 faces, "
                 "B4-02 new faces 0, overlap 0.0000 m2"],
    "zones": {"GF-06 kitchen": "HELD (annex owner height, G2 / Q-54 B)",
              "1F-07 laundry": "52.5290 m2 on L-b2077eee5a71a975bd74",
              "GF-07 pantry": "32.3422 m2 on L-f5c5a1a9c9ee2b644cb5 (own table 32.3750: +0.0328 m2 named residual)"},
    "still_open": "a printed band or a kitchen open to a dry plan (UP-WET-001 precondition fails) is a real B4-02 "
                  "line: no code yet (R-T351-1 / -3 band from a print only, held blank otherwise)",
}


def build(task_commit):
    old = json.loads(OLD.read_text(encoding="utf-8"))
    new = copy.deepcopy(old)
    new["version"] = "1.29.0"
    new["supersedes"] = ("1.28.0 (kept unchanged on disk; every family, every released-configuration field and the "
                         "pending entries up to T-397 copied unchanged; B4-02 gains its coverage evidence)")
    new["source"] = (str(old.get("source", "")) + " | 1.29.0 (T-399): 1.28.0 + pending ARCH_TAKEOFF_V3.0.34 (rule r3 "
                     "of tools/family_master_candidate.py) + B4-02 coverage_in_candidate (COVERED_BY_B4-01, pending); "
                     "no new code, no capability or candidate state changes")
    new["pending_packages"] = list(old.get("pending_packages") or []) + [dict(PENDING, task_commit=task_commit)]
    new["item_code_scan"] += (" | 1.29.0 (T-399): same scan; V3.0.34 writes no new code (it restates one FIN.PAINT "
                              "line, B4-06's)")
    fam = next(f for f in new["families"] if f["code"] == "B4-02")
    fam["coverage_in_candidate"] = copy.deepcopy(COVERAGE)
    return new


def text(doc):
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"


def main(argv):
    if "--check" in argv:
        cur = json.loads(NEW.read_text(encoding="utf-8"))
        tc = cur["pending_packages"][-1]["task_commit"]
        ok = NEW.read_text(encoding="utf-8") == text(build(tc))
        bad = FMC.check(cur, root=ROOT, is_ancestor=FMC.git_is_ancestor)
        print("1.29.0 equals its builder:", ok, "| problems:", bad)
        return 0 if ok and not bad else 1
    if not TASK_COMMIT:
        print("--task-commit <40-hex sha of the commit that adds engine/source/arch_v3034.py> is required")
        return 2
    NEW.write_text(text(build(TASK_COMMIT)), encoding="utf-8")
    print("written", NEW.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
