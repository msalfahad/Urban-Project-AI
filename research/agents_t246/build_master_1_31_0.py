"""T-246: build rules/coverage/BOQ_FAMILY_MASTER_1.31.0.json = 1.30.0 (never edited) + the pending ARCH_TAKEOFF_V3.0.36
package (tools/family_master_candidate.py rule r3). V3.0.36 re-lists the canonical deductions of 39 existing lines; it
writes no new item code and changes no family's capability or candidate state. No quantity changes with this file.

    python3 -I research/agents_t246/build_master_1_31_0.py --task-commit <sha> | --check
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.30.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.31.0.json"
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
V3036 = "engine/source/arch_v3036.py"
PENDING = {
    "task": "T-246", "method_version": "ARCH_TAKEOFF_V3.0.36", "module": V3036,
    "status": FMC.PENDING_STATUS, "integrates": ["T-341", "T-345", "T-296"],
    "tests": ["tests/t246_deduction_listing"],
    "changes_families_by_item_code": [],
    "note": "T-246 (research/agents_t246/T-246_DEDUCTION_LISTING_INTEGRATION.md): canonical deduction lists by opening "
            "/ element id on 39 valued lines (plaster 4, paint 4, wall tile 12, skirting 10, porcelain 2, wall run 7) "
            "from the merged T-341 fill and T-345 trace, the two porcelain gross fields restated to their faces, "
            "window-threshold rows with their T-296 physical reading (flag only); no quantity, state or total moves; "
            "every other V3.0.35 line byte-identical; the Gate B integration package",
}


def build(task_commit):
    old = json.loads(OLD.read_text(encoding="utf-8"))
    new = copy.deepcopy(old)
    new["version"] = "1.31.0"
    new["supersedes"] = ("1.30.0 (kept unchanged on disk; every family, every released-configuration field and the "
                         "pending entries up to T-400 copied unchanged)")
    new["source"] = (str(old.get("source", "")) + " | 1.31.0 (T-246): 1.30.0 + pending ARCH_TAKEOFF_V3.0.36 (rule r3 "
                     "of tools/family_master_candidate.py); no family, code or candidate state changes")
    new["pending_packages"] = list(old.get("pending_packages") or []) + [dict(PENDING, task_commit=task_commit)]
    new["item_code_scan"] += " | 1.31.0 (T-246): same scan; V3.0.36 writes no new item code (lists only)"
    return new


def text(doc):
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"


def main(argv):
    if "--check" in argv:
        cur = json.loads(NEW.read_text(encoding="utf-8"))
        tc = cur["pending_packages"][-1]["task_commit"]
        ok = NEW.read_text(encoding="utf-8") == text(build(tc))
        bad = FMC.check(cur, root=ROOT, is_ancestor=FMC.git_is_ancestor)
        print("1.31.0 equals its builder:", ok, "| problems:", bad)
        return 0 if ok and not bad else 1
    if not TASK_COMMIT:
        print("--task-commit <40-hex sha of the commit that adds engine/source/arch_v3036.py> is required")
        return 2
    NEW.write_text(text(build(TASK_COMMIT)), encoding="utf-8")
    print("written", NEW.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
