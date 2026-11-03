"""T-478: build rules/coverage/BOQ_FAMILY_MASTER_1.40.0.json = 1.39.0 (never edited) + the pending ARCH_TAKEOFF_V3.0.45
package (tools/family_master_candidate.py rule r3) + the family whose lines V3.0.45 splits, re-ranges or adds.

    python3 -I research/agents_t478/build_master_1_40_0.py --task-commit <sha> | --check

Why 1.40.0: 1.39.0 is the merged T-422 package (V3.0.44, merge b4e22291); under the Lead's merge-order rule the
package READY second rebuilds its registry on the first merged one, so OLD is 1.39.0.
Family V3.0.45 touches: B10-01 blinding only (evidence, opt-in reader, missing / note text). No capability, owner or
candidate state changes; no quantity changes with this file.
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

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.39.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.40.0.json"
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
MOD = "engine/source/arch_v3045.py"
TST = "tests/t478_blinding_integration/test_integration_villa_c.py"
PENDING = {
    "task": "T-478", "method_version": "ARCH_TAKEOFF_V3.0.45", "module": MOD,
    "status": FMC.PENDING_STATUS, "integrates": ["T-445", "T-322", "T-233"],
    "tests": ["tests/t478_blinding_integration"],
    "changes_families_by_item_code": ["STR.CONC.BLINDING"],
    "note": "T-478 (research/agents_t478/T-478_BLINDING_INTEGRATION.md): the footing-blinding line L-98eb2d58 "
            "15.179437 m3 SPLIT: valued at the 24 Checker-VERIFIED pits 12.734438 m3, FF raft held 2.256 .. 2.352 "
            "(at least 2.070, S08) and beyond the plot line held 0 .. 0.189 (S06) on their own lines; F10 + F range "
            "0.552 .. 0.590 -> 0.435 .. 0.590 (owner F10-alone scenario + S06 clip); ground-beam blinding netting "
            "record (range unchanged); boundary-wall base blinding added HELD BLANK; every other V3.0.44 line "
            "byte-identical (rebased on the merged V3.0.44); the Gate B integration package",
}
PROPOSED = ("1.40.0 (T-478): moved by the pending ARCH_TAKEOFF_V3.0.45 package (Gate B); the released capability of "
            "V2.9 + route G is unchanged")
OPT_IN = "ARCH_TAKEOFF_V3.0.45 (engine/source/arch_v3045.py, opt-in candidate; pending Gate B, T-478)"
MISS = ("in the opt-in candidate V3.0.45: footing blinding valued at the 24 VERIFIED pits only; FF raft (S08), beyond "
        "the plot line (S06), F10 + F (S02), ground beams (S09 / S11), straps (S07) held; boundary-wall base HELD BLANK "
        "(pad count not printed)")


def _at(path, pattern):
    for i, ln in enumerate((ROOT / path).read_text(encoding="utf-8").splitlines(), 1):
        if re.search(pattern, ln):
            return f"{path}:{i}"
    raise SystemExit(f"{path}: no line matches {pattern!r}")


def build(task_commit):
    old = json.loads(OLD.read_text(encoding="utf-8"))
    new = copy.deepcopy(old)
    new["version"] = "1.40.0"
    new["supersedes"] = ("1.39.0 (kept unchanged on disk; every family except B10-01, every released-configuration "
                         "field and the pending entries up to T-422 copied unchanged)")
    new["source"] = (str(old.get("source", "")) + " | 1.40.0 (T-478): 1.39.0 + pending ARCH_TAKEOFF_V3.0.45 (rule r3 "
                     "of tools/family_master_candidate.py) + the family whose lines it splits, re-ranges or adds; no "
                     "candidate state changes")
    new["pending_packages"] = list(old.get("pending_packages") or []) + [dict(PENDING, task_commit=task_commit)]
    f = next(x for x in new["families"] if x["code"] == "B10-01")
    f["evidence"] = list(f["evidence"]) + [
        f"{_at(MOD, r'^def changes_for')} changes_for(): SPLIT of a mixed blinding line (verified layer valued, held "
        f"pieces their own lines, re-adding to the former value), RANGE_FIX by scenario with the plot-line clip, "
        f"NETTING record, ADD_HELD; {_at(MOD, r'^def check_blinding')} check_blinding(); "
        f"{_at(MOD, r'^def blinding_pieces')} blinding_pieces() (every villa); "
        f"{_at(TST, r'^def test_split_value_add_range_net')} (villa C by hand)"]
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
        print("1.40.0 equals its builder:", ok, "| problems:", bad)
        return 0 if ok and not bad else 1
    if not TASK_COMMIT:
        print("--task-commit <40-hex sha of the commit that adds engine/source/arch_v3045.py> is required")
        return 2
    NEW.write_text(text(build(TASK_COMMIT)), encoding="utf-8")
    print("written", NEW.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
