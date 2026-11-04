"""T-310: build rules/coverage/BOQ_FAMILY_MASTER_1.46.0.json = 1.45.0 (never edited) + the pending ARCH_TAKEOFF_V3.0.49
package (tools/family_master_candidate.py rule r3) + the waterproofing families whose lines V3.0.49 changes or adds.

    python3 -I research/agents_t310/build_master_1_46_0.py --task-commit <sha> | --check

Families: B8-01 (pantry floor), B8-02 (transitions keyed per door, duplicates NA, missing doors HELD), B8-03 (east
bath upturn run, window terminations NA) evidence / opt-in reader / missing / note text; B8-09 owns the two new pool
layer codes WP.POOL.MEMBRANE and WP.POOL.PROTECTION_SCREED (ELEMENT_REGISTER: the pool membrane is its own family,
never inside B8-08 or the concrete line; function HELD S8.2). No capability, owner or candidate state changes;
candidate_census and candidate blocks copied unchanged (promotion after merge); no quantity changes with this file.
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
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.46.0.json"
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
MOD = "engine/source/arch_v3049.py"
TST = "tests/t310_wet_area_wp/test_arch_v3049.py"
PENDING = {
    "task": "T-310", "method_version": "ARCH_TAKEOFF_V3.0.49", "module": MOD,
    "status": FMC.PENDING_STATUS, "integrates": ["T-303", "T-309", "T-286", "T-458"],
    "tests": ["tests/t310_wet_area_wp"],
    "changes_families_by_item_code": ["FIN.WP.WALL_UPTURN", "FIN.WP.FLOOR", "FIN.WP.TERMINATION",
                                      "FIN.WP.DOORWAY_TRANSITION", "WP.POOL.MEMBRANE", "WP.POOL.PROTECTION_SCREED"],
    "note": "T-310 (research/agents_t310/T-310_WET_AREA_POOL_WP.md): 1F east bath upturn 1.480 -> 1.580 m2 (waterproofing "
            "policy V3 run, window W18 above the upturn not deducted; doorway segment HELD beside); its 3 window "
            "termination lines NOT APPLICABLE; pantry floor 13.500 -> 13.455 m2 (column 2FAE intrusion 0.045 ruled "
            "from the drawing); 11 transition lines keyed per physical door, 2 duplicates NOT APPLICABLE, 3 missing "
            "doors added HELD BLANK; pool membrane 29.582355 m2 and protection screed 1.524503 m3 added "
            "DRAWING-CONFIRMED (upstand 0 .. 1.349668 m2 / 0 .. 0.068072 m3 and the membrane function HELD beside); "
            "every other V3.0.48 line byte-identical; the Gate B integration package",
}
PROPOSED = ("1.46.0 (T-310): moved by the pending ARCH_TAKEOFF_V3.0.49 package (Gate B); the released capability "
            "of V2.9 + route G is unchanged")
OPT_IN = "ARCH_TAKEOFF_V3.0.49 (engine/source/arch_v3049.py, opt-in candidate; pending Gate B, T-310)"
MISS = {
    "B8-01": ("in the opt-in candidate V3.0.49: pantry floor membrane 13.455 m2 (box 13.500 - column 0.045, "
              "DRAWING-CONFIRMED; flush-column reading +0.045 named); penetrations still HELD"),
    "B8-02": ("in the opt-in candidate V3.0.49: one transition line per physical door (11 keyed, 2 duplicates NOT "
              "APPLICABLE, 3 missing doors HELD BLANK); every transition figure HELD / bounded (detail not printed); "
              "the pantry door's threshold / transition MISSING (binding piece)"),
    "B8-03": ("in the opt-in candidate V3.0.49: 1F east bath upturn 1.580 m2 (run by policy V3; doorway segments HELD "
              "beside); 3 window termination lines NOT APPLICABLE; the pantry open-side termination MISSING"),
    "B8-09": ("in the opt-in candidate V3.0.49: pool membrane 29.582355 m2 and protection screed 1.524503 m3 on the "
              "base and outer wall faces (DRAWING-CONFIRMED); upstand faces HELD (C9), membrane function HELD (S8.2); "
              "no water-side waterproofing is printed"),
}
POOL_CODES = ["WP.POOL.MEMBRANE", "WP.POOL.PROTECTION_SCREED"]


def _at(path, pattern):
    for i, ln in enumerate((ROOT / path).read_text(encoding="utf-8").splitlines(), 1):
        if re.search(pattern, ln):
            return f"{path}:{i}"
    raise SystemExit(f"{path}: no line matches {pattern!r}")


def build(task_commit):
    old = json.loads(OLD.read_text(encoding="utf-8"))
    new = copy.deepcopy(old)
    new["version"] = "1.46.0"
    new["supersedes"] = ("1.45.0 (kept unchanged on disk; every family except B8-01 / B8-02 / B8-03 / B8-09, every "
                         "released-configuration field, the candidate census, every candidate block and the promotion "
                         "record copied unchanged)")
    new["source"] = (str(old.get("source", "")) + " | 1.46.0 (T-310): 1.45.0 + pending ARCH_TAKEOFF_V3.0.49 (rule "
                     "r3) + the waterproofing families it changes; B8-09 owns the two pool layer codes; no candidate "
                     "state changes")
    new["pending_packages"] = list(old.get("pending_packages") or []) + [dict(PENDING, task_commit=task_commit)]
    fams = {f["code"]: f for f in new["families"]}
    for code in ("B8-01", "B8-02", "B8-03", "B8-09"):
        f = fams[code]
        f["evidence"] = list(f["evidence"]) + [
            f"{_at(MOD, r'^def changes_for')} changes_for(): REVALUE_UPTURN / REVALUE_FLOOR / NOT_APPLICABLE / "
            f"KEY_DOOR / ADD_HELD_DOOR / ADD_POOL_LAYER by line id, stale bindings refused; "
            f"{_at(MOD, r'^def load_inputs')} load_inputs() (upturn value = waterproofing policy V3 run, floor = box - "
            f"deductions, one transition per door); {_at(MOD, r'^def check_wet_area_wp')} check_wet_area_wp(); "
            f"{_at(TST, r'^def test_hand_values')} (villa W310 by hand)"]
        f["opt_in_readers"] = (OPT_IN if str(f.get("opt_in_readers") or "none") == "none" else
                               str(f.get("opt_in_readers")) + " | " + OPT_IN)
        f["missing"] = str(f.get("missing") or "") + " | " + MISS[code]
        f["note"] = str(f.get("note") or "") + " | " + PROPOSED
    f = fams["B8-09"]
    if f["item_codes"]:
        raise SystemExit("B8-09: owns item codes in 1.45.0 (expected none)")
    f["item_codes"] = list(POOL_CODES)
    f["note"] = str(f["note"]) + (" | 1.46.0 (T-310): owns WP.POOL.MEMBRANE (m2) and WP.POOL.PROTECTION_SCREED (m3), "
                                  "the printed outer protective layers of the pool (ELEMENT_REGISTER: their own "
                                  "family, never B8-08 or the concrete line); the family's water-side waterproofing "
                                  "is not printed for the development villa")
    return new


def text(doc):
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"


def main(argv):
    if "--check" in argv:
        cur = json.loads(NEW.read_text(encoding="utf-8"))
        tc = cur["pending_packages"][-1]["task_commit"]
        ok = NEW.read_text(encoding="utf-8") == text(build(tc))
        bad = FMC.check(cur, root=ROOT, is_ancestor=FMC.git_is_ancestor)
        print("1.46.0 equals its builder:", ok, "| problems:", bad)
        return 0 if ok and not bad else 1
    if not TASK_COMMIT:
        print("--task-commit <40-hex sha of the commit that adds engine/source/arch_v3049.py> is required")
        return 2
    NEW.write_text(text(build(TASK_COMMIT)), encoding="utf-8")
    print("written", NEW.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
