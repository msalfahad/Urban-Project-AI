"""T-487: build rules/coverage/BOQ_FAMILY_MASTER_1.50.0.json = 1.47.0 (never edited) + the pending ARCH_TAKEOFF_V3.0.53
package (tools/family_master_candidate.py rule r3) + the B9-02 text it changes. 1.48.0 (T-483, V3.0.51) and 1.49.0
(T-310, V3.0.52) are built in parallel on READY branches; under the merge-order rule the package merged later rebases on
the earlier (its registry then supersedes the other's, and the promotion of the merged pending packages T-443 / T-350b /
T-497 is T-483's gate fix, not this task's). No capability, owner or candidate state changes: B9-02 stays
NOT_IN_CANDIDATE in the census until a promotion version after Gate B.

    python3 -I research/agents_t487/build_master_1_50_0.py --task-commit <sha> | --check
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

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.47.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.50.0.json"
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
MOD = "engine/source/arch_v3053.py"
TST = "tests/t487_lintel_lines/test_arch_v3053.py"
PENDING = {
    "task": "T-487", "method_version": "ARCH_TAKEOFF_V3.0.53", "module": MOD,
    "status": FMC.PENDING_STATUS, "integrates": ["T-453"],
    "tests": ["tests/t487_lintel_lines"],
    "changes_families_by_item_code": ["STR.CONC.LINTEL"],
    "note": "T-487 (research/agents_t487/T-487_LINTEL_LINES.md; F-T479-2): the B9-02 lintel lines added from the "
            "Checker-verified T-453 r2 lintel ledger by the printed structural LINTEL SCHEDULE (R-T487-1): 60 "
            "STR.CONC.LINTEL m3 lines, one per opening in masonry: 16 REQUIRED PROVISIONAL 1 piece each = 1.016 m3 "
            "(formwork 14.845 m2 and host faces beside, not booked), 42 HELD + 2 FLAGGED BLOCKED_RFI blank by name; "
            "MAS.BLOCK contract area and every V3.0.50 line byte-identical; the Gate B integration package",
}
PROPOSED = ("1.50.0 (T-487): moved by the pending ARCH_TAKEOFF_V3.0.53 package (Gate B); the released capability of "
            "V2.9 + route G is unchanged; the candidate block stays NOT_IN_CANDIDATE until a promotion version")
OPT_IN = "ARCH_TAKEOFF_V3.0.53 (engine/source/arch_v3053.py, opt-in candidate; pending Gate B, T-487)"
MISS = ("V3.0.53: 16 REQUIRED RC lintels 1.016 m3 PROVISIONAL (jamb bearing, RC-column jambs and the 0.06 m build-up "
        "STAND-IN open); 42 HELD (head / host wall not established) and 2 FLAGGED (W13, W26: which piece is over the "
        "opening) blank; lintel formwork (B10-13) beside, rebar kg (B11) HELD; precast-rule villas (no printed "
        "schedule) not wired")


def _at(path, pattern):
    for i, ln in enumerate((ROOT / path).read_text(encoding="utf-8").splitlines(), 1):
        if re.search(pattern, ln):
            return f"{path}:{i}"
    raise SystemExit(f"{path}: no line matches {pattern!r}")


def build(task_commit):
    old = json.loads(OLD.read_text(encoding="utf-8"))
    new = copy.deepcopy(old)
    new["version"] = "1.50.0"
    new["supersedes"] = ("1.47.0 (kept unchanged on disk; every family except B9-02, every released-configuration "
                         "field, the candidate census, every candidate block, the promotion record and the earlier "
                         "pending entries copied unchanged; 1.48.0 / 1.49.0 are T-483's / T-310's, built in parallel)")
    new["source"] = (str(old.get("source", "")) + " | 1.50.0 (T-487): 1.47.0 + pending ARCH_TAKEOFF_V3.0.53 (rule r3) "
                     "+ the B9-02 text it changes; no candidate state changes")
    new["pending_packages"] = list(old.get("pending_packages") or []) + [dict(PENDING, task_commit=task_commit)]
    f = {x["code"]: x for x in new["families"]}["B9-02"]
    f["evidence"] = list(f["evidence"]) + [
        f"{_at(MOD, r'^def changes_for')} changes_for(): one STR.CONC.LINTEL m3 line per opening in masonry, REQUIRED "
        f"valued B x D x (w + 2 x bearing) recomputed from the printed schedule and asserted equal to the ledger, "
        f"HELD / FLAGGED blank; {_at(MOD, r'^def check_lintels')} check_lintels(); "
        f"{_at(TST, r'^def test_hand_quantities_and_states')} (villa L by hand, 0.14225 m3)"]
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
        print("1.50.0 equals its builder:", ok, "| problems:", bad)
        return 0 if ok and not bad else 1
    if not TASK_COMMIT:
        print("--task-commit <40-hex sha of the commit that adds engine/source/arch_v3053.py> is required")
        return 2
    NEW.write_text(text(build(TASK_COMMIT)), encoding="utf-8")
    print("written", NEW.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
