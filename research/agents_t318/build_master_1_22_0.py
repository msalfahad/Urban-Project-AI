"""T-318: build rules/coverage/BOQ_FAMILY_MASTER_1.22.0.json = 1.21.0 (never edited) + the pending ARCH_TAKEOFF_V3.0.27
package (tools/family_master_candidate.py rule r3).

    python3 -I research/agents_t318/build_master_1_22_0.py --task-commit <sha> | --check

Why a new version: the V3.0.27 module (engine/source/arch_v3027.py) is newer than every registry version on the head,
and a package cannot name its merge commit or checker verdict before the Checker merges it, so V3.0.27 is declared
PENDING (status READY_FOR_GATE_B, its task commit), raises no family state and names no family. Every field of 1.21.0
is copied unchanged (the T-279 V3.0.26 entry included). The slab reinforcement family state moves only with the
Checker's verdict.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.21.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.22.0.json"
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
PENDING = {
    "task": "T-318", "method_version": "ARCH_TAKEOFF_V3.0.27", "module": "engine/source/arch_v3027.py",
    "status": FMC.PENDING_STATUS, "integrates": ["T-307", "T-316", "T-306"],
    "tests": ["tests/t318_slab_bar_end_split"],
    "changes_families_by_item_code": [],
    "note": "T-318 (research/agents_t318/T-318_SLAB_BAR_END_INTEGRATION.md): the 98 suspended-slab DEVELOPMENT / "
            "ANCHORAGE and 98 TOP BARS OVER SUPPORTS lines (STR.REBAR kg, BOUNDED_EXPOSURE since V3.0.5) re-booked bar "
            "end by bar end from the merged T-307 / T-316 support-class ledgers (owner option B 2026-10-29): "
            "development 8 NOT_APPLICABLE (all ends continuous), 59 split (drawn straight part 136.573 .. 150.695 kg "
            "valued, legs / undrawn ends BLANK), 31 BLANK; top 7 re-based, 79 split (note 2 vs p.15 envelope on the "
            "valued ends 612.077 .. 1,618.961 kg), 12 BLANK; every other V3.0.26 line byte-identical; the Gate B "
            "integration package; names no family",
}


def build(task_commit):
    old = json.loads(OLD.read_text(encoding="utf-8"))
    new = copy.deepcopy(old)
    new["version"] = "1.22.0"
    new["supersedes"] = ("1.21.0 (kept unchanged on disk; every family, count, released-configuration field and the "
                         "pending entries up to T-279 copied unchanged)")
    new["source"] = (str(old.get("source", "")) + " | 1.22.0 (T-318): 1.21.0 + pending ARCH_TAKEOFF_V3.0.27 "
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
        print("1.22.0 equals its builder:", ok, "| problems:", bad)
        return 0 if ok and not bad else 1
    if not TASK_COMMIT:
        print("--task-commit <40-hex sha of the commit that adds engine/source/arch_v3027.py> is required")
        return 2
    NEW.write_text(text(build(TASK_COMMIT)), encoding="utf-8")
    print("written", NEW.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
