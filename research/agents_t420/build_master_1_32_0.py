"""T-420: build rules/coverage/BOQ_FAMILY_MASTER_1.32.0.json = 1.31.0 (never edited) + the pending ARCH_TAKEOFF_V3.0.37
package (tools/family_master_candidate.py rule r3) + the owner family of the codes V3.0.37 writes.

    python3 -I research/agents_t420/build_master_1_32_0.py --task-commit <sha> | --check

Why a new version: the V3.0.37 module (engine/source/arch_v3037.py) is newer than every registry version on the head;
a package cannot name its merge commit or checker verdict before the Checker merges it, so V3.0.37 is declared PENDING
(READY_FOR_GATE_B, its task commit), raises no candidate state and names no family in a candidate block.

B3-05 'Screed / build-up' owns the two codes V3.0.37 writes (FIN.FLOOR.BED.DRY / .WET, each an m2 + m3 measure pair);
its capability stays IMPLEMENTED_NOT_INTEGRATED (tested code, read only by the opt-in candidate) and its candidate state
NOT_IN_CANDIDATE (pending). No quantity changes with this file.
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

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.31.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.32.0.json"
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
V3037 = "engine/source/arch_v3037.py"
T420T = "tests/t420_floor_bed_fill/test_arch_v3037.py"
BED_CODES = ["FIN.FLOOR.BED.DRY", "FIN.FLOOR.BED.WET"]
PENDING = {
    "task": "T-420", "method_version": "ARCH_TAKEOFF_V3.0.37", "module": V3037,
    "status": FMC.PENDING_STATUS, "integrates": ["T-414"],
    "tests": ["tests/t420_floor_bed_fill"],
    "changes_families_by_item_code": list(BED_CODES),
    "note": "T-420 (research/agents_t420/T-420_FLOOR_BED_INTEGRATION.md): the MISSING category B3-05 floor bed, one "
            "bed per valued floor-finish line bound by id (40 beds: 19 dry 288.1458 m2, 21 wet 85.5756 m2), each an "
            "m2 line (= the finish net) and an installed m3 line as the owner Q-45 range (dry 8.6444 .. 11.5258, wet "
            "3.4230 .. 5.1345 m3, ASSUMED - OWNER-APPROVED) with the drawing bound beside (dry 0 .. 14.5144 m3, "
            "F-C-T414-1; wet HELD, no bound); 13 NOT_APPLICABLE finish lines carry no bed; every other V3.0.36 "
            "line byte-identical; the Gate B integration package",
}
PROPOSED = ("1.32.0 (T-420): moved by the pending ARCH_TAKEOFF_V3.0.37 package (Gate B); the released capability of "
            "V2.9 + route G is unchanged (no released method reads these codes)")


def _at(path, pattern):
    for i, ln in enumerate((ROOT / path).read_text(encoding="utf-8").splitlines(), 1):
        if re.search(pattern, ln):
            return f"{path}:{i}"
    raise SystemExit(f"{path}: no line matches {pattern!r}")


def moves():
    return {
        "B3-05": {
            "capability": "IMPLEMENTED_NOT_INTEGRATED",
            "implementation": ("ARCH_TAKEOFF_V3.0.37 (opt-in): " + " / ".join(BED_CODES) + " (m2 = the bound floor-"
                               "finish net; installed m3 = the owner Q-45 range, BOUNDED_EXPOSURE, drawing bound beside); "
                               "engine/source/finish_materials_table.py (T-086) stays the procurement view"),
            "item_codes": list(BED_CODES),
            "evidence_set": [
                f"{_at(V3037, r'^NEW_ITEMS = ')} NEW_ITEMS: the two bed codes; {_at(V3037, r'^def load_inputs')} "
                "load_inputs(): owner range required (no default thickness), a roof / terrace / stair / pool / "
                "foundation / outdoor / balcony row refused, held as 0 refused, a wet room never takes a dry b, an "
                f"upper bound never below the drawn b; {_at(V3037, r'^def check_beds')} check_beds(): one m2 + one m3 "
                "per bed, a measure pair (price one basis), bound to a valued floor-finish line",
                f"{_at(T420T, r'^def test_hand_figures')} test_hand_figures() (V420 by hand: dry 39.50 m2, owner "
                "1.185 .. 1.58 m3; wet 6.00 m2, 0.24 .. 0.36 m3) / "
                f"{_at(T420T, r'^def test_bed_on_a_roof_refused')[len(T420T):]} test_bed_on_a_roof_refused()",
                "engine/source/finish_materials_table.py:1 \"FINISH MATERIALS TABLE V1\": the procurement view (T-086, "
                "commit 6002856), unchanged",
            ],
            "opt_in_readers": "ARCH_TAKEOFF_V3.0.37 (engine/source/arch_v3037.py, opt-in candidate; pending Gate B, "
                              "T-420)",
            "missing": ("not in the released method; in the opt-in V3.0.37 the drawn bed stays HELD (tile thickness "
                        "printed nowhere, D-40), wet / sunken levels printed nowhere (D-41), balcony screed thickness "
                        "not given (Q-41), spaces without a floor-finish line carry no bed (T-421)"),
            "note": ("1.0.0 said NOT_IMPLEMENTED; 1.x (T-086) IMPLEMENTED_NOT_INTEGRATED as a material range only; "
                     + PROPOSED),
        },
    }


def _move(fam, mv, states):
    for k in ("item_codes", "implementation", "opt_in_readers", "missing", "note"):
        if k in mv:
            fam[k] = copy.deepcopy(mv[k])
    if "evidence_set" in mv:
        fam["evidence"] = list(mv["evidence_set"])
    if "capability" in mv:
        fam["capability"] = mv["capability"]
        rank = {s: i for i, s in enumerate(states)}
        c0, c1 = rank[fam["capability_1_0_0"]], rank[fam["capability"]]
        fam["capability_change"] = "UNCHANGED" if c0 == c1 else ("RAISED" if c1 < c0 else "LOWERED")
    if fam["capability"] != "NOT_IMPLEMENTED":
        fam.pop("name_terms", None)


def _recount(new):
    fam = new["families"]
    new["capability_counts"] = {k: sum(1 for f in fam if f["capability"] == k) for k in new["capability_states"]}
    new["capability_change_counts"] = {k: sum(1 for f in fam if f["capability_change"] == k)
                                       for k in ("RAISED", "LOWERED", "UNCHANGED")}
    new["in_v3_0_candidate_counts"] = {k: sum(1 for f in fam if f["in_v3_0_candidate"] == k) for k in ("yes", "no")}
    new["candidate_state_counts"] = {k: sum(1 for f in fam if f["candidate"]["state"] == k)
                                     for k in new["candidate_state_counts"]}


def build(task_commit):
    old = json.loads(OLD.read_text(encoding="utf-8"))
    new = copy.deepcopy(old)
    new["version"] = "1.32.0"
    new["supersedes"] = ("1.31.0 (kept unchanged on disk; every family except B3-05, every released-configuration "
                         "field and the pending entries up to T-246 copied unchanged)")
    new["source"] = (str(old.get("source", "")) + " | 1.32.0 (T-420): 1.31.0 + pending ARCH_TAKEOFF_V3.0.37 (rule r3 "
                     "of tools/family_master_candidate.py) + B3-05 owns FIN.FLOOR.BED.DRY / .WET (capability "
                     "IMPLEMENTED_NOT_INTEGRATED unchanged); no candidate state changes")
    new["pending_packages"] = list(old.get("pending_packages") or []) + [dict(PENDING, task_commit=task_commit)]
    by = {f["code"]: f for f in new["families"]}
    for code, mv in moves().items():
        _move(by[code], mv, new["capability_states"])
    _recount(new)
    new["item_code_scan"] += " | 1.32.0 (T-420): same scan; V3.0.37 writes FIN.FLOOR.BED.DRY / .WET (B3-05)"
    return new


def text(doc):
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"


def main(argv):
    if "--check" in argv:
        cur = json.loads(NEW.read_text(encoding="utf-8"))
        tc = cur["pending_packages"][-1]["task_commit"]
        ok = NEW.read_text(encoding="utf-8") == text(build(tc))
        bad = FMC.check(cur, root=ROOT, is_ancestor=FMC.git_is_ancestor)
        print("1.32.0 equals its builder:", ok, "| problems:", bad)
        return 0 if ok and not bad else 1
    if not TASK_COMMIT:
        print("--task-commit <40-hex sha of the commit that adds engine/source/arch_v3037.py> is required")
        return 2
    NEW.write_text(text(build(TASK_COMMIT)), encoding="utf-8")
    print("written", NEW.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
