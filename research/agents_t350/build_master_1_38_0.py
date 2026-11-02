"""T-350: build rules/coverage/BOQ_FAMILY_MASTER_1.38.0.json = 1.37.0 (never edited) + the pending ARCH_TAKEOFF_V3.0.43
package (tools/family_master_candidate.py rule r3) + the families whose lines V3.0.43 adds or re-ranges.

    python3 -I research/agents_t350/build_master_1_38_0.py --task-commit <sha> | --check

Why a new version: the V3.0.43 module (engine/source/arch_v3043.py) is newer than every registry version on the head; a
package cannot name its merge commit or checker verdict before the Checker merges it, so V3.0.43 is declared PENDING
(READY_FOR_GATE_B, its task commit), raises no candidate state and names no family in a candidate block.

Families V3.0.43 touches: B1-02 excavation, B1-03 backfill, B1-04 disposal (item codes EARTH.EXCAVATION /
EARTH.BACKFILL / EARTH.DISPOSAL now owned; evidence, opt-in reader, missing / note text: every line HELD BLANK with the
proved bound beside), B1-01 site clearance (note only: NOT IN DRAWN SCOPE on the development villa, T-357, no line),
B10-01 blinding (the strap blinding held range 0 .. 0.912684, text only), B10-03 straps (the SB3-in-F3 held range,
text only). No capability, owner or candidate state changes; no quantity changes with this file.
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

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.37.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.38.0.json"
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
V3043 = "engine/source/arch_v3043.py"
T350T = "tests/t350_earthworks_integration/test_arch_v3043.py"
PENDING = {
    "task": "T-350", "method_version": "ARCH_TAKEOFF_V3.0.43", "module": V3043,
    "status": FMC.PENDING_STATUS, "integrates": ["T-347", "T-356", "T-357", "T-320", "T-170"],
    "tests": ["tests/t350_earthworks_integration"],
    "changes_families_by_item_code": ["EARTH.EXCAVATION", "EARTH.BACKFILL", "EARTH.DISPOSAL", "STR.CONC.BLINDING",
                                      "STR.CONC.STRAP"],
    "note": "T-350 (research/agents_t350/T-350_EARTHWORKS_INTEGRATION.md): the MISSING earthworks categories from the "
            "Checker-verified T-347 FILL table: 18 zone lines (B1-02 x 12, B1-03 x 5, B1-04 x 1), every one HELD "
            "BLANK (formation, working space, zone extent are designer items; no bulking rule); beside them: pits "
            "AT_LEAST 188.017207 m3 (+129.234 m3 per m below the printed 1.50), pool AT_LEAST 17.776576 m3, 13 "
            "interior runs ZERO_BY_BOUND (b_wet <= 0.30); existing ground DERIVED +-0.00 (T-357); held-range fixes: "
            "strap blinding L-35382b18 0.377803 .. 0.771877 -> 0 .. 0.912684 m3 (T-356), SB3 in F3 L-c823e0db "
            "0.0295 .. 0.1181 -> 0.0295 .. 0.2683 m3 (F-T347-1); every other V3.0.42 line byte-identical; the Gate B "
            "integration package",
}
PROPOSED = ("1.38.0 (T-350): moved by the pending ARCH_TAKEOFF_V3.0.43 package (Gate B); the released capability of "
            "V2.9 + route G is unchanged")
OPT_IN = "ARCH_TAKEOFF_V3.0.43 (engine/source/arch_v3043.py, opt-in candidate; pending Gate B, T-350)"
EW_CODES = {"B1-02": "EARTH.EXCAVATION", "B1-03": "EARTH.BACKFILL", "B1-04": "EARTH.DISPOSAL"}
TOUCH = {
    "B1-01": None,
    "B1-02": "in the opt-in candidate V3.0.43: 12 zone lines, all HELD BLANK (formation only a minimum, Q-21 C; "
             "working space and pits vs bulk dig, OQ-13 / RFI S1; trench sections D-33 / D-34 / D-35 / D-15; boundary "
             "depth Q-28); bounds beside: pits >= 188.017207 m3 (N-T347-1: 0.1018 m3 conservative), pool >= "
             "17.776576 m3, 13 interior runs zero while b_wet <= 0.30",
    "B1-03": "in the opt-in candidate V3.0.43: 5 zone lines, all HELD BLANK (backfill = excavation - net displacement "
             "below EG; excavation held, Z2 fill above EG not formed)",
    "B1-04": "in the opt-in candidate V3.0.43: 1 line HELD BLANK (no bulking rule; Z2 re-use from excavated material, "
             "p.13; excavation held)",
    "B10-01": None,
    "B10-04": None,
}
B1_01_NOTE = ("development villa: NOT IN DRAWN SCOPE (T-357 MERGED 90135e91: no site plan, no clearance note on any of "
              "the 31 sheets); V3.0.43 writes no line")


def _at(path, pattern):
    for i, ln in enumerate((ROOT / path).read_text(encoding="utf-8").splitlines(), 1):
        if re.search(pattern, ln):
            return f"{path}:{i}"
    raise SystemExit(f"{path}: no line matches {pattern!r}")


def moves(old_by):
    ev = (f"{_at(V3043, r'^def changes_for')} changes_for(): one HELD BLANK earthworks line per Checker-verified FILL "
          f"zone (bound, held items, bound buried lines beside), held-range fixes of named buried concrete lines; "
          f"{_at(V3043, r'^def check_earthworks')} check_earthworks(): every earthworks line held blank, each zone "
          f"once, bound lines in the candidate, a re-ranged line keeps state / rfi / id; "
          f"{_at(T350T, '^def test_hand_villa_lines_held_blank_with_bound_beside')} (E350 by hand)")
    out = {}
    for code, miss in TOUCH.items():
        f = old_by[code]
        mv = {"note": str(f.get("note") or "") + " | " + PROPOSED}
        if code == "B1-01":
            mv["note"] = str(f.get("note") or "") + " | 1.38.0 (T-350): " + B1_01_NOTE
            out[code] = mv
            continue
        mv["evidence_set"] = list(f["evidence"]) + [ev]
        mv["opt_in_readers"] = str(f.get("opt_in_readers") or "") + " | " + OPT_IN
        if code in EW_CODES:
            mv["item_codes"] = list(f["item_codes"]) + [EW_CODES[code]]
        if miss:
            mv["missing"] = str(f.get("missing") or "") + " | " + miss
        out[code] = mv
    return out


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
    new["version"] = "1.38.0"
    new["supersedes"] = ("1.37.0 (kept unchanged on disk; every family except B1-01 .. B1-04, B10-01, B10-04, every "
                         "released-configuration field and the pending entries up to T-442 copied unchanged)")
    new["source"] = (str(old.get("source", "")) + " | 1.38.0 (T-350): 1.37.0 + pending ARCH_TAKEOFF_V3.0.43 (rule r3 "
                     "of tools/family_master_candidate.py) + the families whose lines it adds or re-ranges; no "
                     "candidate state changes")
    new["pending_packages"] = list(old.get("pending_packages") or []) + [dict(PENDING, task_commit=task_commit)]
    by = {f["code"]: f for f in new["families"]}
    for code, mv in moves({f["code"]: f for f in old["families"]}).items():
        _move(by[code], mv, new["capability_states"])
    _recount(new)
    new["item_code_scan"] += (" | 1.38.0 (T-350): V3.0.43 writes three new codes EARTH.EXCAVATION / EARTH.BACKFILL / "
                              "EARTH.DISPOSAL (trade EARTHWORKS), owned by B1-02 / B1-03 / B1-04")
    return new


def text(doc):
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"


def main(argv):
    if "--check" in argv:
        cur = json.loads(NEW.read_text(encoding="utf-8"))
        tc = cur["pending_packages"][-1]["task_commit"]
        ok = NEW.read_text(encoding="utf-8") == text(build(tc))
        bad = FMC.check(cur, root=ROOT, is_ancestor=FMC.git_is_ancestor)
        print("1.38.0 equals its builder:", ok, "| problems:", bad)
        return 0 if ok and not bad else 1
    if not TASK_COMMIT:
        print("--task-commit <40-hex sha of the commit that adds engine/source/arch_v3043.py> is required")
        return 2
    NEW.write_text(text(build(TASK_COMMIT)), encoding="utf-8")
    print("written", NEW.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
