"""T-483: build rules/coverage/BOQ_FAMILY_MASTER_1.45.0.json = 1.44.0 (never edited) + the pending ARCH_TAKEOFF_V3.0.48
package (tools/family_master_candidate.py rule r3) + the family whose lines V3.0.48 changes.

    python3 -I research/agents_t483/build_master_1_45_0.py --task-commit <sha> | --check

Family V3.0.48 touches: B3-06 skirting only (evidence, opt-in reader, missing / note text). No capability, owner or
candidate state changes; candidate_census and every family's candidate block copied unchanged (promotion happens after
merge); no quantity changes with this file. Version allotted at merge (Lead merge-order rule): renumber if another
package merges first.
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

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.44.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.45.0.json"
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
MOD = "engine/source/arch_v3048.py"
TST = "tests/t483_skirting_remainder/test_arch_v3048.py"
PENDING = {
    "task": "T-483", "method_version": "ARCH_TAKEOFF_V3.0.48", "module": MOD,
    "status": FMC.PENDING_STATUS, "integrates": ["T-481", "T-410", "T-422"],
    "tests": ["tests/t483_skirting_remainder"],
    "changes_families_by_item_code": ["FIN.SKIRTING"],
    "note": "T-483 (research/agents_t483/T-483_SKIRTING_REMAINDER_INTEGRATION.md): the Checker-verified T-481 census "
            "integrated: GF-01 W11 / W12 sills 0.70 above the +0.30 floor (section B-B) -> skirting under them, room "
            "line 14.218 -> 18.128 lm, its range line NOT_APPLICABLE (carried once); W02 and W17 floor glazing: their "
            "held ranges closed NOT_APPLICABLE; the 1F dressing walked by handle 5.100 lm (was HELD BLANK); the 1F "
            "shaft faces 9.050 lm and the W13 / W25 range 2.200 lm WAITING (owner B7-07 / B7-08 not in the "
            "candidate); every other V3.0.47 line byte-identical; the Gate B integration package",
}
PROPOSED = ("1.45.0 (T-483): moved by the pending ARCH_TAKEOFF_V3.0.48 package (Gate B); the released capability of "
            "V2.9 + route G is unchanged")
OPT_IN = "ARCH_TAKEOFF_V3.0.48 (engine/source/arch_v3048.py, opt-in candidate; pending Gate B, T-483)"
MISS = ("in the opt-in candidate V3.0.48: W11 / W12 skirted, W02 / W17 floor glazing (ranges closed); the 1F dressing "
        "valued 5.100 lm; still open: R-T481-3 on the 1F shaft (9.050 lm inside the 1F living net, W13 / W25 range "
        "0 .. 2.200 held) until B7-07 / B7-08 have candidate lines, the W02 pier D-53")


def _at(path, pattern):
    for i, ln in enumerate((ROOT / path).read_text(encoding="utf-8").splitlines(), 1):
        if re.search(pattern, ln):
            return f"{path}:{i}"
    raise SystemExit(f"{path}: no line matches {pattern!r}")


def build(task_commit):
    old = json.loads(OLD.read_text(encoding="utf-8"))
    new = copy.deepcopy(old)
    new["version"] = "1.45.0"
    new["supersedes"] = ("1.44.0 (kept unchanged on disk; every family except B3-06, every released-configuration "
                         "field, the candidate census, every candidate block and the promotion record copied "
                         "unchanged)")
    new["source"] = (str(old.get("source", "")) + " | 1.45.0 (T-483): 1.44.0 + pending ARCH_TAKEOFF_V3.0.48 (rule r3 "
                     "of tools/family_master_candidate.py) + the family whose lines it changes; no candidate state "
                     "changes")
    new["pending_packages"] = list(old.get("pending_packages") or []) + [dict(PENDING, task_commit=task_commit)]
    f = next(x for x in new["families"] if x["code"] == "B3-06")
    f["evidence"] = list(f["evidence"]) + [
        f"{_at(MOD, r'^def changes_for')} changes_for(): RELEASE of a window base under a sill established above the "
        f"floor (range line counted in the room line), CLOSE_RANGE of a held range whose windows are floor glazing or "
        f"stair-owned, WALK of a blocked dry-cell line by handle (openings by id); {_at(MOD, r'^def load_inputs')} "
        f"load_inputs() (sill in m, cover, closure); {_at(MOD, r'^def check_remainder')} check_remainder(); "
        f"{_at(TST, r'^def test_release_rises_by_the_window_edges_and_closes')} (villa K483 by hand)"]
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
        print("1.45.0 equals its builder:", ok, "| problems:", bad)
        return 0 if ok and not bad else 1
    if not TASK_COMMIT:
        print("--task-commit <40-hex sha of the commit that adds engine/source/arch_v3048.py> is required")
        return 2
    NEW.write_text(text(build(TASK_COMMIT)), encoding="utf-8")
    print("written", NEW.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
