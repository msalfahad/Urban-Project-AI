"""T-421: build rules/coverage/BOQ_FAMILY_MASTER_1.33.0.json = 1.32.0 (never edited) + the pending ARCH_TAKEOFF_V3.0.38
package (tools/family_master_candidate.py rule r3) + the owner families of the codes V3.0.38 writes.

    python3 -I research/agents_t421/build_master_1_33_0.py --task-commit <sha> | --check

Why a new version: the V3.0.38 module (engine/source/arch_v3038.py) is newer than every registry version on the head; a
package cannot name its merge commit or checker verdict before the Checker merges it, so V3.0.38 is declared PENDING
(READY_FOR_GATE_B, its task commit), raises no candidate state and names no family in a candidate block.

Owners of the codes V3.0.38 writes: B3-01 'Dry floor porcelain' also owns FIN.FLOOR.FINISH_HELD (a floor-finish area
whose material is HELD); B6-07 owns FIN.MARBLE.LIFT_THRESHOLD (m2 + front edge m.l), B6-06 FIN.MARBLE.LIFT_SURROUND (m2,
HELD bound): both EXPERIMENTAL -> IMPLEMENTED_NOT_INTEGRATED (tested code read only by the opt-in candidate); B3-05's
'missing' text loses the T-421 item (the stair-room floor lines now carry their beds). No candidate state changes; no
quantity changes with this file.
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

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.32.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.33.0.json"
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
V3038 = "engine/source/arch_v3038.py"
T421T = "tests/t421_stair_lift_integration/test_arch_v3038.py"
FIN_HELD, THR, SUR = "FIN.FLOOR.FINISH_HELD", "FIN.MARBLE.LIFT_THRESHOLD", "FIN.MARBLE.LIFT_SURROUND"
PENDING = {
    "task": "T-421", "method_version": "ARCH_TAKEOFF_V3.0.38", "module": V3038,
    "status": FMC.PENDING_STATUS, "integrates": ["T-418", "T-413"],
    "tests": ["tests/t421_stair_lift_integration"],
    "changes_families_by_item_code": [FIN_HELD, "FIN.FLOOR.PORCELAIN", "FIN.MARBLE.LANDING", "ARCH.THRESHOLD", THR,
                                      SUR, "FIN.FLOOR.BED.DRY"],
    "note": "T-421 (research/agents_t421/T-421_STAIR_LIFT_INTEGRATION.md): the Checker-merged T-418 stair-room floor "
            "parts (GF stair hall 4.805 + back lobby 1.3225 m2 as FIN.FLOOR.FINISH_HELD, 2F lobby 2.500 m2 gross "
            "porcelain, the 0 .. 0.23 strip HELD) with the two FIN.MARBLE.LANDING bounds reduced in the same step, and "
            "the T-413 lift-entrance marble (B6-07 3 x 0.500 m2 + 1.000 m.l, depth ASSUMED - OWNER-APPROVED UP-ELEV-005; "
            "B6-06 HELD 2.750 .. 13.980 m2); the three ARCH.THRESHOLD LIFT_LANDING bands listed without a quantity, "
            "the GF / 1F landing porcelain and the 2F lobby net of the certain threshold floor part (0.300 m2 each, "
            "0 .. 0.200 more HELD), the beds added / restated by R-T420-1; every other V3.0.37 line byte-identical; "
            "the Gate B integration package",
}
PROPOSED = ("1.33.0 (T-421): moved by the pending ARCH_TAKEOFF_V3.0.38 package (Gate B); the released capability of "
            "V2.9 + route G is unchanged (no released method reads these codes)")


def _at(path, pattern):
    for i, ln in enumerate((ROOT / path).read_text(encoding="utf-8").splitlines(), 1):
        if re.search(pattern, ln):
            return f"{path}:{i}"
    raise SystemExit(f"{path}: no line matches {pattern!r}")


def moves(old_by):
    b301 = old_by["B3-01"]
    b305 = old_by["B3-05"]
    return {
        "B3-01": {
            "item_codes": list(b301["item_codes"]) + [FIN_HELD],
            "evidence_set": list(b301["evidence"]) + [
                f"{_at(V3038, r'^NEW_ITEMS = ')} NEW_ITEMS: {FIN_HELD} (a floor-finish area, material HELD by name); "
                f"{_at(V3038, r'^def check_landing')} check_landing(): a stair-room floor part leaves its landing "
                f"bound in the same version; {_at(T421T, r'^def test_stair_face_dropped_whole_refused')} (R-T418-1 "
                "adverse)"],
            "note": str(b301.get("note") or "") + " | " + PROPOSED + ": " + FIN_HELD + " added (T-418 stair-room parts)",
        },
        "B3-05": {
            "missing": b305["missing"].replace(", spaces without a floor-finish line carry no bed (T-421)", ""),
            "note": str(b305.get("note") or "") + " | " + PROPOSED + ": beds of the T-418 floor parts added, beds of "
                    "the floor lines the lift threshold deducts restated",
        },
        "B6-07": {
            "capability": "IMPLEMENTED_NOT_INTEGRATED",
            "implementation": f"ARCH_TAKEOFF_V3.0.38 (opt-in): {THR} m2 (drawn clear width x UP-ELEV-005 depth) + lm "
                              "(front edge); engine/elevator_marble.py (round 6) unchanged",
            "item_codes": [THR],
            "evidence_set": [
                f"{_at(V3038, r'^def _station_lines')} _station_lines(): threshold m2 + front edge m.l per landing "
                f"door; {_at(V3038, r'^def check_lift')} check_lift(): one threshold quantity per station (band "
                "listed without a quantity, floor deducts the certain part)",
                f"{_at(T421T, r'^def test_each_threshold_counted_once')} test_each_threshold_counted_once() (K421 by "
                "hand: 0.90 x 0.50 = 0.450 m2, floor part 0.225 certain)"],
            "opt_in_readers": "ARCH_TAKEOFF_V3.0.38 (engine/source/arch_v3038.py, opt-in candidate; pending Gate B, "
                              "T-421)",
            "missing": "not in the released method; threshold depth ASSUMED - OWNER-APPROVED (UP-ELEV-005) where not "
                       "printed; position across the wall band not drawn (floor deduction rest HELD)",
            "note": "1.0.0 EXPERIMENTAL (round 6 research, read by no method); " + PROPOSED,
        },
        "B6-06": {
            "capability": "IMPLEMENTED_NOT_INTEGRATED",
            "implementation": f"ARCH_TAKEOFF_V3.0.38 (opt-in): {SUR} m2, union area, HELD with its bound while the "
                              "door height is not printed; engine/elevator_marble.py (round 6) unchanged",
            "item_codes": [SUR],
            "evidence_set": [
                f"{_at(V3038, r'^def _station_lines')} _station_lines(): surround BOUNDED_EXPOSURE per landing door "
                "(never 0, never a chosen height)",
                f"{_at(T421T, r'^def test_hand_figures')} test_hand_figures() (K421: HELD 0.95 .. 4.40 m2)"],
            "opt_in_readers": "ARCH_TAKEOFF_V3.0.38 (engine/source/arch_v3038.py, opt-in candidate; pending Gate B, "
                              "T-421)",
            "missing": "door clear height printed nowhere (supplier / RFI L-1): HELD bound per station; a band whose "
                       "drawn face is narrower than the 0.50 default HELD 0 .. face (2F right on the development villa)",
            "note": "1.0.0 EXPERIMENTAL (round 6 research, read by no method); " + PROPOSED,
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
    new["version"] = "1.33.0"
    new["supersedes"] = ("1.32.0 (kept unchanged on disk; every family except B3-01, B3-05, B6-06 and B6-07, every "
                         "released-configuration field and the pending entries up to T-420 copied unchanged)")
    new["source"] = (str(old.get("source", "")) + " | 1.33.0 (T-421): 1.32.0 + pending ARCH_TAKEOFF_V3.0.38 (rule r3 "
                     "of tools/family_master_candidate.py) + B3-01 owns FIN.FLOOR.FINISH_HELD, B6-07 "
                     "FIN.MARBLE.LIFT_THRESHOLD, B6-06 FIN.MARBLE.LIFT_SURROUND; no candidate state changes")
    new["pending_packages"] = list(old.get("pending_packages") or []) + [dict(PENDING, task_commit=task_commit)]
    by = {f["code"]: f for f in new["families"]}
    for code, mv in moves({f["code"]: f for f in old["families"]}).items():
        _move(by[code], mv, new["capability_states"])
    _recount(new)
    new["item_code_scan"] += (" | 1.33.0 (T-421): same scan; V3.0.38 writes FIN.FLOOR.FINISH_HELD (B3-01), "
                              "FIN.MARBLE.LIFT_THRESHOLD (B6-07), FIN.MARBLE.LIFT_SURROUND (B6-06)")
    return new


def text(doc):
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"


def main(argv):
    if "--check" in argv:
        cur = json.loads(NEW.read_text(encoding="utf-8"))
        tc = cur["pending_packages"][-1]["task_commit"]
        ok = NEW.read_text(encoding="utf-8") == text(build(tc))
        bad = FMC.check(cur, root=ROOT, is_ancestor=FMC.git_is_ancestor)
        print("1.33.0 equals its builder:", ok, "| problems:", bad)
        return 0 if ok and not bad else 1
    if not TASK_COMMIT:
        print("--task-commit <40-hex sha of the commit that adds engine/source/arch_v3038.py> is required")
        return 2
    NEW.write_text(text(build(TASK_COMMIT)), encoding="utf-8")
    print("written", NEW.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
