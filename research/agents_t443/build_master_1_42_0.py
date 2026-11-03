"""T-443: build rules/coverage/BOQ_FAMILY_MASTER_1.42.0.json = 1.41.0 (never edited) + the pending ARCH_TAKEOFF_V3.0.46
package (tools/family_master_candidate.py rule r3) + the family whose lines V3.0.46 splits.

    python3 -I research/agents_t443/build_master_1_42_0.py --task-commit <sha> | --check

Why 1.42.0: 1.41.0 is the merged T-479 registry refresh (c3cbeb99) on top of the merged T-478 package (V3.0.45);
under the Lead's merge-order rule the package READY second rebuilds its registry on the latest merged one (a package
merged before this one, e.g. V3.0.46 of another stream, means a rebase and a renumber at merge).
Family V3.0.46 touches: B3-06 skirting only (evidence, opt-in reader, missing / note text). No capability, owner or
candidate state changes; candidate_census (V3.0.45) copied unchanged; no quantity changes with this file.
"""

from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.41.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.42.0.json"
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
MOD = "engine/source/arch_v3046.py"
TST = "tests/t443_stair_room_skirting/test_arch_v3046.py"
PENDING = {
    "task": "T-443", "method_version": "ARCH_TAKEOFF_V3.0.46", "module": MOD,
    "status": FMC.PENDING_STATUS, "integrates": ["T-441", "T-410", "T-418", "T-421"],
    "tests": ["tests/t443_stair_room_skirting"],
    "changes_families_by_item_code": ["FIN.SKIRTING"],
    "note": "T-443 (research/agents_t443/T-443_STAIR_ROOM_SKIRTING_SPLIT.md): the two BLOCKED stair-room skirting lines "
            "split by floor part from the Checker-verified T-441 face tables: GF hall +1.00 4.650 lm and back lobby "
            "+0.30 1.400 lm (material HELD with their floors), 2F lobby 3.350 lm (porcelain Q-70 A, VERIFIED), 2F "
            "arrival 4.150 lm (material HELD beside the marble landing); OP-002 deducted whole as a lift opening, no "
            "jamb skirting; divider band, OP-020 reveal jambs and the lobby west face HELD BLANK children; GF parent "
            "HELD with the unread strip face 0.200, 2F parent NOT_APPLICABLE; every other V3.0.45 line "
            "byte-identical; the Gate B integration package",
}
PROPOSED = ("1.42.0 (T-443): moved by the pending ARCH_TAKEOFF_V3.0.46 package (Gate B); the released capability of "
            "V2.9 + route G is unchanged")
OPT_IN = "ARCH_TAKEOFF_V3.0.46 (engine/source/arch_v3046.py, opt-in candidate; pending Gate B, T-443)"
MISS = ("in the opt-in candidate V3.0.46: the walled stair rooms carry their floor parts' skirting (13.550 lm valued, "
        "material HELD except the 2F lobby, Q-70 A); divider band, reveal jambs and the back lobby west face HELD "
        "BLANK; flight faces stay with B7-07 / B7-08 (form ORR-007); the 1F shaft binding R-T481-3 waits")


def _at(path, pattern):
    for i, ln in enumerate((ROOT / path).read_text(encoding="utf-8").splitlines(), 1):
        if re.search(pattern, ln):
            return f"{path}:{i}"
    raise SystemExit(f"{path}: no line matches {pattern!r}")


def build(task_commit):
    old = json.loads(OLD.read_text(encoding="utf-8"))
    new = copy.deepcopy(old)
    new["version"] = "1.42.0"
    new["supersedes"] = ("1.41.0 (kept unchanged on disk; every family except B3-06, every released-configuration "
                         "field, the candidate census and the pending entries up to T-478 copied unchanged)")
    new["source"] = (str(old.get("source", "")) + " | 1.42.0 (T-443): 1.41.0 + pending ARCH_TAKEOFF_V3.0.46 (rule r3 "
                     "of tools/family_master_candidate.py) + the family whose lines it splits; no candidate state "
                     "changes")
    new["pending_packages"] = list(old.get("pending_packages") or []) + [dict(PENDING, task_commit=task_commit)]
    f = next(x for x in new["families"] if x["code"] == "B3-06")
    f["evidence"] = list(f["evidence"]) + [
        f"{_at(MOD, r'^def changes_for')} changes_for(): SPLIT of a BLOCKED stair-room skirting line into one child "
        f"per floor part (openings by id, a lift opening whole with no jambs), HELD BLANK face groups, the parent "
        f"keeping the named remainder; {_at(MOD, r'^def load_inputs')} load_inputs() (cover, one base one owner, "
        f"closure in lm); {_at(MOD, r'^def check_stair_rooms')} check_stair_rooms(); "
        f"{_at(TST, r'^def test_part_children_hand_figures')} (villa K443 by hand)"]
    f["opt_in_readers"] = str(f.get("opt_in_readers") or "") + " | " + OPT_IN
    f["missing"] = str(f.get("missing") or "") + " | " + MISS
    f["note"] = str(f.get("note") or "") + " | " + PROPOSED
    return new


def text(doc):
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"


def main(argv):
    if "--check" in argv:
        cur = json.loads(NEW.read_text(encoding="utf-8"))
        tc = cur["pending_packages"][-1]["task_commit"]
        ok = NEW.read_text(encoding="utf-8") == text(build(tc))
        bad = FMC.check(cur, root=ROOT, is_ancestor=FMC.git_is_ancestor)
        print("1.42.0 equals its builder:", ok, "| problems:", bad)
        return 0 if ok and not bad else 1
    if not TASK_COMMIT:
        print("--task-commit <40-hex sha of the commit that adds engine/source/arch_v3046.py> is required")
        return 2
    NEW.write_text(text(build(TASK_COMMIT)), encoding="utf-8")
    print("written", NEW.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
