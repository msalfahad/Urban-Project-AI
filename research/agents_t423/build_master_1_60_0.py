"""T-423 r3: build rules/coverage/BOQ_FAMILY_MASTER_1.60.0.json = 1.59.0 (T-651; never edited)
  + the pending ARCH_TAKEOFF_V3.0.60 package (T-423, tools/family_master_candidate.py rule r3) and the B3-01 / B3-04 /
    B4-01 / B4-03 / B5-01 text of the families whose lines it re-records (the r1 1.55.0 text, renumbered V3.0.58 ->
    V3.0.60; no quantity, no new code, no capability move).
No promotion: 1.59.0 holds no pending package (T-651 promoted T-498 / V3.0.59), so the candidate of record stays
ARCH_TAKEOFF_V3.0.59, its census and every family's candidate block are copied unchanged. r1 staged 1.55.0 for this
package (T-507 merged that number first: merge-order rule, renumber at hand-in). No quantity, capability, owner or line
change with this file; the released default is untouched.

    python3 -I research/agents_t423/build_master_1_60_0.py --task-commit <sha> | --check
"""
from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, ROOT / "research" / "agents_t485"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import build_master_1_43_0 as B  # noqa: E402  (census problems of T-485, unchanged)
from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.59.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.60.0.json"
VERSION = "1.60.0"
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
MOD = "engine/source/arch_v3060.py"
TST = "tests/t423_split_remainder/test_arch_v3060.py"
FAMS = ("B3-01", "B3-04", "B4-01", "B4-03", "B5-01")
PENDING = {
    "task": "T-423", "method_version": "ARCH_TAKEOFF_V3.0.60", "module": MOD,
    "status": FMC.PENDING_STATUS, "integrates": ["T-246", "T-284", "T-283", "T-335", "T-388", "T-327", "T-330"],
    "tests": ["tests/t423_split_remainder"],
    "changes_families_by_item_code": ["FIN.CEILING", "FIN.WALL.TILE", "FIN.PLASTER", "FIN.MARBLE.THRESHOLD",
                                      "FIN.FLOOR.PORCELAIN"],
    "note": "T-423 (research/agents_t423/T-423_SPLIT_REMAINDER.md): 5 FIN.CEILING lines list their HELD dome piece by id "
            "(T-330 ceiling FLAG 6 -> 1, the GF open plan set aside by name); the 1F-02 door hole D-1F-04 1.760 m2 "
            "moved to its doorway face piece on the tile and backing records (room 27.9101 unchanged); 14 marble "
            "thresholds one material state URBAN_METHOD (UP-THR-001); 15 strips carry m2 / m.l / pcs as a "
            "measure_pair; on V3.0.59 75331a76 -> V3.0.60 8c8a9642: 22 lines text-only, totals unchanged; the Gate B "
            "integration package",
}
PROPOSED = ("1.60.0 (T-423): re-recorded by the pending ARCH_TAKEOFF_V3.0.60 package (Gate B); no quantity moves; the "
            "released capability of V2.9 + route G is unchanged")
OPT_IN = "ARCH_TAKEOFF_V3.0.60 (engine/source/arch_v3060.py, opt-in candidate; pending Gate B, T-423)"
MISS = {
    "B5-01": ("in the opt-in candidate V3.0.60: 5 ceiling lines list their dome piece by id; the GF open-plan list "
              "set aside (9.785604 m2 not closed by id)"),
    "B4-01": "in the opt-in candidate V3.0.60: D-1F-04 booked on the 1F-02 doorway piece; GF annex faces HELD",
    "B4-03": "in the opt-in candidate V3.0.60: D-1F-04 booked on the 1F-02 doorway piece (backing); GF annex HELD",
    "B3-04": "in the opt-in candidate V3.0.60: one material state URBAN_METHOD; m2 / m.l / pcs as measure pair",
    "B3-01": "in the opt-in candidate V3.0.60: the D-1F-03 dry strip carries m2 / m.l / pcs as a measure pair",
}


def _at(path, pattern):
    for i, ln in enumerate((ROOT / path).read_text(encoding="utf-8").splitlines(), 1):
        if re.search(pattern, ln):
            return f"{path}:{i}"
    raise SystemExit(f"{path}: no line matches {pattern!r}")


def build(task_commit):
    old = json.loads(OLD.read_text(encoding="utf-8"))
    if old["pending_packages"]:
        raise SystemExit(f"{old['version']} holds pending packages {[p['task'] for p in old['pending_packages']]}: "
                         "a promotion must come first (R-T485-1)")
    if old["candidate"]["method_version"] != "ARCH_TAKEOFF_V3.0.59":
        raise SystemExit(f"{old['version']}: candidate of record {old['candidate']['method_version']}, expected "
                         "ARCH_TAKEOFF_V3.0.59 (V3.0.60 extends it)")
    new = copy.deepcopy(old)
    new["version"] = VERSION
    new["supersedes"] = (f"{old['version']} (kept unchanged on disk; every released-configuration field, every T-637 "
                         "field, the candidate of record ARCH_TAKEOFF_V3.0.59, its census and every family's "
                         "candidate block copied unchanged; B3-01 / B3-04 / B4-01 / B4-03 / B5-01 text for the "
                         "pending V3.0.60 package)")
    new["source"] = (old["source"] + f" | {VERSION} (T-423 r3): {old['version']} + pending ARCH_TAKEOFF_V3.0.60 "
                     "(rule r3) + the finishes families it re-records; no promotion, no quantity, capability or "
                     "owner change")
    new["pending_packages"] = [dict(PENDING, task_commit=task_commit)]
    fams = {f["code"]: f for f in new["families"]}
    ev = (f"{_at(MOD, r'^def changes_for')} changes_for(): LIST_CEILING / MOVE_FACE_DEDUCTION / NOT_APPLICABLE / "
          f"MATERIAL_STATE / MEASURE_PAIR by line id, stale bindings refused; "
          f"{_at(MOD, r'^def check_split_remainder')} check_split_remainder(); "
          f"{_at(TST, r'^def test_hand_values')} (villa V423 by hand)")
    for code in FAMS:
        f = fams[code]
        f["evidence"] = list(f["evidence"]) + [ev]
        f["opt_in_readers"] = (OPT_IN if str(f.get("opt_in_readers") or "none") == "none" else
                               str(f.get("opt_in_readers")) + " | " + OPT_IN)
        f["missing"] = str(f.get("missing") or "") + " | " + MISS[code]
        f["note"] = str(f.get("note") or "") + " | " + PROPOSED
    return new


def text(doc):
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"


def main(argv):
    if "--check" in argv:
        cur = json.loads(NEW.read_text(encoding="utf-8"))
        tc = cur["pending_packages"][-1]["task_commit"]
        ok = NEW.read_text(encoding="utf-8") == text(build(tc))
        bad = FMC.check(cur, root=ROOT, is_ancestor=FMC.git_is_ancestor) + B.census_problems(cur)
        print(f"{VERSION} equals its builder:", ok, "| problems:", bad)
        return 0 if ok and not bad else 1
    if not TASK_COMMIT:
        print(f"--task-commit <40-hex sha of the commit that adds {MOD}> is required")
        return 2
    doc = build(TASK_COMMIT)
    bad = FMC.check(doc, root=ROOT, is_ancestor=FMC.git_is_ancestor) + B.census_problems(doc)
    for b in bad:
        print("PROBLEM", b)
    NEW.write_text(text(doc), encoding="utf-8")
    print("written", NEW.relative_to(ROOT), f"({len(bad)} problem(s))")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
