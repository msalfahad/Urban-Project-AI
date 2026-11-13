"""T-770 r2: build rules/coverage/BOQ_FAMILY_MASTER_1.81.0.json = 1.80.0 (never edited; T-314 promoted, candidate of
record ARCH_TAKEOFF_V3.0.79, no pending package) + the PENDING ARCH_TAKEOFF_V3.0.81 package (T-770 r2, FILL_WIRE_V1,
R-T770-1 / R-T770-2; tools/family_master_candidate.py rule r3). Nothing here changes a family state, a capability, an
owner rule or a line; the promotion is the Verifier's after Gate B.

    bash scripts/agent_env.sh run --tree task-T-770 research/agents_t770/build_master_1_81_0.py [--write | --check]
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

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.80.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.81.0.json"
VERSION = "1.81.0"
TASK_COMMIT = "c24bf648bf6cc958414f5b183f19a4a8ce10ce62"     # the commit that added engine/source/arch_v3081.py
CODES = ["FIN.FLOOR.BED.DRY", "FIN.FLOOR.BED.WET", "FIN.PAINT", "FIN.PLASTER", "FIN.ROOF.FINISH", "FIN.ROOF.INSULATION",
         "FIN.ROOF.PROTECTION", "FIN.ROOF.SCREED", "FIN.WP.ROOF", "STR.CONC.BEAM", "STR.CONC.BLINDING",
         "STR.CONC.BOUNDARY_PAD", "STR.CONC.COLUMN", "STR.CONC.DOME", "STR.CONC.GROUND_BEAM", "STR.CONC.LIFT",
         "STR.CONC.LINTEL", "STR.CONC.NECK", "STR.CONC.PARAPET", "STR.CONC.POOL", "STR.CONC.SAFETY", "STR.CONC.STAIR",
         "STR.FORMWORK", "STR.FORMWORK.STAIR"]
PENDING = {"task": "T-770", "method_version": "ARCH_TAKEOFF_V3.0.81", "module": "engine/source/arch_v3081.py",
           "status": FMC.PENDING_STATUS, "integrates": ["T-762", "T-761"], "tests": ["tests/t770_fill_wire"],
           "changes_families_by_item_code": CODES,
           "note": "T-770 r2 (DELIVERY MODE wiring, research/agents_t770/v3081_index.py) on the V3.0.79 candidate (T-314): "
                   "three Checker-verified family groups by line id with labels and bases: MAIN_FILL_ALL less its 126 "
                   "formwork rows (T-762 Gate A double count CONFIRMED) and its disposal row (T-764 verified figure "
                   "wires with T-764) = 81 rows; T-762 formwork 336 rows, 33 cover deductions netted into their hosts "
                   "(R-T770-2 f); T-761 concrete 80 rows, 13 known pieces < 0.05 m3 IGNORED_SMALL under ONE added "
                   "STR.CONC.SAFETY 1 m3 line (R-T770-2 g); non-measured figures PROVISIONAL, never VERIFIED; every "
                   "other line byte-identical; blank non-rebar lines 691 -> 295",
           "task_commit": TASK_COMMIT}


def build():
    old = json.loads(OLD.read_text(encoding="utf-8"))
    if old.get("version") != "1.80.0" or old.get("pending_packages"):
        raise SystemExit(f"base registry {old.get('version')} is not a promoted 1.80.0 (pending "
                         f"{[p.get('task') for p in old.get('pending_packages') or []]})")
    new = copy.deepcopy(old)
    new["version"] = VERSION
    new["supersedes"] = ("1.80.0 (kept unchanged on disk; every field copied unchanged) + the pending "
                         "ARCH_TAKEOFF_V3.0.81 package (T-770 r2)")
    new["source"] = old["source"] + (" | 1.81.0 (T-770 r2): 1.80.0 + pending ARCH_TAKEOFF_V3.0.81 (rule r3 of "
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
