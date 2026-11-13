"""T-770: build rules/coverage/BOQ_FAMILY_MASTER_1.80.0.json = 1.79.0 (never edited) + the PENDING ARCH_TAKEOFF_V3.0.81
package (T-770 round 1, FILL_WIRE_V1, R-T770-1; tools/family_master_candidate.py rule r3). 1.79.0's own pending T-738
(merged 208c5689 but not yet promoted by its Verifier) is carried unchanged: its promotion stays the Verifier's
(research/agents_t738/build_master_1_79_0.py --promote); nothing here changes a family state, a capability, an owner
rule or a line. When T-738 is promoted into a newer registry, rebuild this file on it.

    bash scripts/agent_env.sh run --tree task-T-770 research/agents_t770/build_master_1_80_0.py [--write | --check]
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.79.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.80.0.json"
VERSION = "1.80.0"
TASK_COMMIT = "c24bf648bf6cc958414f5b183f19a4a8ce10ce62"     # the commit that added engine/source/arch_v3081.py
CODES = ["FIN.FLOOR.BED.DRY", "FIN.FLOOR.BED.WET", "FIN.PAINT", "FIN.PLASTER", "FIN.ROOF.FINISH", "FIN.ROOF.INSULATION",
         "FIN.ROOF.PROTECTION", "FIN.ROOF.SCREED", "FIN.WP.ROOF", "STR.EARTH.DISPOSAL", "STR.FORMWORK",
         "STR.FORMWORK.STAIR"]
PENDING = {"task": "T-770", "method_version": "ARCH_TAKEOFF_V3.0.81", "module": "engine/source/arch_v3081.py",
           "status": FMC.PENDING_STATUS, "integrates": ["T-738"], "tests": ["tests/t770_fill_wire"],
           "changes_families_by_item_code": CODES,
           "note": "T-770 round 1 (DELIVERY MODE wiring, research/agents_t770): the owner-session fix-row set "
                   "MAIN_FILL_ALL (207 rows: FLOOR_BED 44 DEFAULT, FORMWORK_RATIO 126 ESTIMATE, ROOF_LAYERS 14 "
                   "ESTIMATE, PLASTER_DRY 11 DEFAULT, PAINT_DRY 11 ESTIMATE, EARTH_DISPOSAL 1 ESTIMATE range) applied "
                   "by line id on the V3.0.78 candidate (T-738) with labels and bases; non-measured figures "
                   "PROVISIONAL, never VERIFIED; every other line byte-identical; blank non-rebar lines 692 -> 551",
           "task_commit": TASK_COMMIT}


def build():
    old = json.loads(OLD.read_text(encoding="utf-8"))
    if old.get("version") != "1.79.0":
        raise SystemExit(f"base registry {old.get('version')} is not 1.79.0")
    new = copy.deepcopy(old)
    new["version"] = VERSION
    new["supersedes"] = ("1.79.0 (kept unchanged on disk; every field copied unchanged; its pending T-738 carried "
                         "until its Verifier promotes it) + the pending ARCH_TAKEOFF_V3.0.81 package (T-770)")
    new["source"] = old["source"] + (" | 1.80.0 (T-770): 1.79.0 + pending ARCH_TAKEOFF_V3.0.81 (rule r3 of "
                                     "tools/family_master_candidate.py, FILL_WIRE_V1) handed in for Gate B; no family "
                                     "state changes until it merges")
    new["pending_packages"] = list(old.get("pending_packages") or []) + [PENDING]
    return new


def text(doc):
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"


def main(argv):
    doc = build()
    p = FMC.check(doc, root=ROOT, is_ancestor=FMC.git_is_ancestor)
    if "--check" in argv:
        ok = NEW.is_file() and NEW.read_text(encoding="utf-8") == text(doc)
        print(f"{VERSION} equals its builder:", ok, "| problems:", p)
        return 0 if ok else 1
    if "--write" in argv:
        NEW.write_text(text(doc), encoding="utf-8")
    print(VERSION, "pending:", [x["task"] for x in doc["pending_packages"]], "| problems:", p)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
