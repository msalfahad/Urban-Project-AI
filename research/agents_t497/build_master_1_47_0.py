"""T-497: build rules/coverage/BOQ_FAMILY_MASTER_1.47.0.json = 1.45.0 (never edited) + the pending ARCH_TAKEOFF_V3.0.50
package (tools/family_master_candidate.py rule r3) + the B1-02 text it changes. 1.46.0 is claimed in parallel by T-483 r2
(V3.0.49); under the merge-order rule the package merged second rebases on the first (its registry then supersedes the
other's). No capability, owner or candidate state changes; candidate census, candidate blocks, promotion and the
earlier pending entries copied unchanged (promoting merged pending packages is T-483 r2's gate fix, not this task's).

    python3 -I research/agents_t497/build_master_1_47_0.py --task-commit <sha> | --check
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

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.45.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.47.0.json"
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
MOD = "engine/source/arch_v3050.py"
RULE = "research/agents_t497/zone_ownership_v1.py"
TST = "tests/t497_zone_ownership/test_zone_ownership.py"
PENDING = {
    "task": "T-497", "method_version": "ARCH_TAKEOFF_V3.0.50", "module": MOD,
    "status": FMC.PENDING_STATUS, "integrates": ["T-350", "T-484"],
    "tests": ["tests/t497_zone_ownership"],
    "changes_families_by_item_code": ["STR.EARTH.EXCAVATION"],
    "note": "T-497 (research/agents_t497/T-497_ZONE_OWNERSHIP.md; Checker F-C-T350R4-1): the V3.0.48 external main "
            "ground-beam trench range 1.203269 .. 1.432834 m3 restated on the plan it alone owns (R-T497-1: every "
            "excavation zone subtracts the plans of all earlier zones, in the plot and beyond) = 1.069269 .. 1.176467 "
            "m3, the Checker's drawn-outline figures exactly; STR.EARTH.EXCAVATION held bound 8.467769 .. 9.824584 -> "
            "8.333769 .. 9.568217 m3; every other V3.0.48 line byte-identical; the Gate B integration package",
}
PROPOSED = ("1.47.0 (T-497): moved by the pending ARCH_TAKEOFF_V3.0.50 package (Gate B); the released capability of "
            "V2.9 + route G is unchanged")
OPT_IN = "ARCH_TAKEOFF_V3.0.50 (engine/source/arch_v3050.py, opt-in candidate; pending Gate B, T-497)"
MISS = ("V3.0.50: the ext main GB trench restated on its own plan 1.069269 .. 1.176467 m3 (F10F drawn-outline scenario; "
        "other S02 readings up to +0.037 in plot / +0.047499 with beyond-plot, named); working space, beyond-plot "
        "parts and the other trench zones still HELD")


def _at(path, pattern):
    for i, ln in enumerate((ROOT / path).read_text(encoding="utf-8").splitlines(), 1):
        if re.search(pattern, ln):
            return f"{path}:{i}"
    raise SystemExit(f"{path}: no line matches {pattern!r}")


def build(task_commit):
    old = json.loads(OLD.read_text(encoding="utf-8"))
    new = copy.deepcopy(old)
    new["version"] = "1.47.0"
    new["supersedes"] = ("1.45.0 (kept unchanged on disk; every family except B1-02, every released-configuration "
                         "field, the candidate census, every candidate block, the promotion record and the earlier "
                         "pending entries copied unchanged; 1.46.0 is T-483 r2's, built in parallel)")
    new["source"] = (str(old.get("source", "")) + " | 1.47.0 (T-497): 1.45.0 + pending ARCH_TAKEOFF_V3.0.50 (rule r3) "
                     "+ the B1-02 text it changes; no candidate state changes")
    new["pending_packages"] = list(old.get("pending_packages") or []) + [dict(PENDING, task_commit=task_commit)]
    f = {x["code"]: x for x in new["families"]}["B1-02"]
    f["evidence"] = list(f["evidence"]) + [
        f"{_at(MOD, r'^def changes_for')} changes_for(): a V3.0.48 ranged excavation zone restated on the plan it alone "
        f"owns (never above the range it replaces); {_at(MOD, r'^def check_zone_owner')} check_zone_owner() (the "
        f"V3.0.48 invariants re-run on every other line); {_at(RULE, r'^def own_plans')} own_plans() (R-T497-1, every "
        f"m2 once, asserted); {_at(TST, r'^def test_trench_crossing')} (villa E497 by hand)"]
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
        print("1.47.0 equals its builder:", ok, "| problems:", bad)
        return 0 if ok and not bad else 1
    if not TASK_COMMIT:
        print("--task-commit <40-hex sha of the commit that adds engine/source/arch_v3050.py> is required")
        return 2
    NEW.write_text(text(build(TASK_COMMIT)), encoding="utf-8")
    print("written", NEW.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
