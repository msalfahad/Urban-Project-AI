"""T-563: build rules/coverage/BOQ_FAMILY_MASTER_1.61.0.json = 1.60.0 (T-423 r3; never edited)
  + the pending ARCH_TAKEOFF_V3.0.61 package (T-563, PLASTER_HEIGHT_V1_WIRING; tools/family_master_candidate.py rule
    r3) beside the pending T-423 package (a list of pending packages, each in order) and the B4-03 (FIN.PLASTER) text
    of the family whose lines it restates; B4-06 (FIN.PAINT) gets a dated note that paint does NOT move.
No promotion (neither pending package has a Gate B verdict yet): the candidate of record stays ARCH_TAKEOFF_V3.0.59,
its census and every family's candidate block are copied unchanged. The version and master number are allotted at
merge (Lead 2026-11-09 12:20: expect V3.0.61 / 1.61.0 after T-423 r3); if T-423 is promoted first the builder is
re-run on that registry (renumber, merge-order rule). No quantity, capability, owner or line change with this file;
the released default is untouched.

    python3 -I research/agents_t563/build_master_1_61_0.py --task-commit <sha> | --check
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

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.60.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.61.0.json"
VERSION = "1.61.0"
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
MOD = "engine/source/arch_v3061.py"
TST = "tests/t563_plaster_height/test_arch_v3061.py"
FAMS = ("B4-03", "B4-06")
PENDING = {
    "task": "T-563", "method_version": "ARCH_TAKEOFF_V3.0.61", "module": MOD,
    "status": FMC.PENDING_STATUS, "integrates": ["T-556", "T-558", "T-552", "T-634"],
    "tests": ["tests/t563_plaster_height"],
    "changes_families_by_item_code": ["FIN.PLASTER"],
    "note": "T-563 (research/agents_t563/T-563_PLASTER_HEIGHT_WIRING.md): PLASTER_HEIGHT_V1_WIRING (T-558 manifest V6): "
            "11 dry FIN.PLASTER lines restated at the slab / roof soffit (Q-72, R-T556-1), all HELD (bounded) on the "
            "unprinted roof build-up (D-39 / DCR-6): 4 RELEASED lines 217.2081 m2 -> HELD 262.01799 .. 262.05199 m2, "
            "FIN.PLASTER released 580.5819 -> 363.3738 m2, 11 lines 840.64581 .. 895.89641 m2; FIN.PAINT 45 lines "
            "byte-identical; every other line byte-identical; the Gate B integration package",
}
PROPOSED = ("1.61.0 (T-563): restated by the pending ARCH_TAKEOFF_V3.0.61 package (Gate B): 4 released dry plaster "
            "lines leave the released total (HELD at their own height); the released capability of V2.9 + route G is "
            "unchanged")
OPT_IN = "ARCH_TAKEOFF_V3.0.61 (engine/source/arch_v3061.py, opt-in candidate; pending Gate B, T-563)"
MISS = {
    "B4-03": ("in the opt-in candidate V3.0.61: 11 dry plaster lines at the slab / roof soffit (Q-72), HELD on the "
              "roof build-up (D-39 / DCR-6); dry rooms outside the T-556 table not restated"),
    "B4-06": "in the opt-in candidate V3.0.61: paint unchanged at the finished ceiling G1 (plaster is its own layer)",
}


def _at(path, pattern):
    for i, ln in enumerate((ROOT / path).read_text(encoding="utf-8").splitlines(), 1):
        if re.search(pattern, ln):
            return f"{path}:{i}"
    raise SystemExit(f"{path}: no line matches {pattern!r}")


def build(task_commit):
    old = json.loads(OLD.read_text(encoding="utf-8"))
    if [p["task"] for p in old["pending_packages"]] != ["T-423"]:
        raise SystemExit(f"{old['version']} pending packages {[p['task'] for p in old['pending_packages']]}: expected "
                         "exactly T-423 (V3.0.60) below this package")
    if old["candidate"]["method_version"] != "ARCH_TAKEOFF_V3.0.59":
        raise SystemExit(f"{old['version']}: candidate of record {old['candidate']['method_version']}, expected "
                         "ARCH_TAKEOFF_V3.0.59 (V3.0.61 extends the pending V3.0.60)")
    new = copy.deepcopy(old)
    new["version"] = VERSION
    new["supersedes"] = (f"{old['version']} (kept unchanged on disk; every released-configuration field, every T-637 "
                         "field, the candidate of record ARCH_TAKEOFF_V3.0.59, its census, the pending T-423 package "
                         "and every family's candidate block copied unchanged; B4-03 / B4-06 text for the pending "
                         "V3.0.61 package)")
    new["source"] = (old["source"] + f" | {VERSION} (T-563): {old['version']} + pending ARCH_TAKEOFF_V3.0.61 "
                     "(rule r3, after the pending V3.0.60) + the plaster / paint families it names; no promotion, no "
                     "quantity, capability or owner change")
    new["pending_packages"] = list(old["pending_packages"]) + [dict(PENDING, task_commit=task_commit)]
    fams = {f["code"]: f for f in new["families"]}
    ev = (f"{_at(MOD, r'^def changes_for')} changes_for(): PLASTER_HEIGHT by line id, stale bindings and a "
          f"paint change refused; {_at(MOD, r'^def check_plaster_height')} check_plaster_height(); "
          f"{_at(MOD, r'^def check_totals')} check_totals(); "
          f"{_at(TST, r'^def test_hand_values')} (villa V563 by hand)")
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
