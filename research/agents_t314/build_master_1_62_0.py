"""T-314 r2: build rules/coverage/BOQ_FAMILY_MASTER_1.62.0.json = 1.61.0 (T-563; never edited)
  + the pending ARCH_TAKEOFF_V3.0.62 package (T-314, exterior plaster / Sigma face rows R-T314-1;
    tools/family_master_candidate.py rule r3) after the pending T-423 (V3.0.60) and T-563 (V3.0.61) packages, and the
    B4-04 (external plaster) / B4-07 (FIN.EXT.FINISH) text of the families whose lines it restates.
No promotion (no pending package has a Gate B verdict on this tree): the candidate of record stays
ARCH_TAKEOFF_V3.0.59, its census and every family's candidate block are copied unchanged. Version and master number are
allotted at merge (Gate B order: T-423 merged 62e18eed with 1.60.0 still listing it pending; T-563 then this package);
if a promotion lands first the builder is re-run on that registry (renumber, merge-order rule). No quantity,
capability, owner or line change with this file; the released default is untouched.

    python3 -I research/agents_t314/build_master_1_62_0.py --task-commit <sha> | --check
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

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.61.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.62.0.json"
VERSION = "1.62.0"
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
MOD = "engine/source/arch_v3062.py"
TST = "tests/t314_facade_faces/test_arch_v3062.py"
FAMS = ("B4-04", "B4-07")
PENDING = {
    "task": "T-314", "method_version": "ARCH_TAKEOFF_V3.0.62", "module": MOD,
    "status": FMC.PENDING_STATUS, "integrates": ["T-305", "T-311", "T-324", "T-337", "T-348", "T-349", "T-567"],
    "tests": ["tests/t314_facade_faces"],
    "changes_families_by_item_code": ["FIN.EXT.FINISH"],
    "note": "T-314 (research/agents_t314/T-314_FACADE_FACE_ROWS.md): exterior plaster / Sigma face rows (R-T314-1) "
            "into FIN.EXT.FINISH by element and levels (storey, parapet outer / inner / top, plinth, slab edge), "
            "holes once on the face that holds them, held faces / holes as ranges or blank, never 0: 3 storey lines "
            "HELD blank -> restated, 15 element lines ADDED; point 152.005 m2 + 13 bounded lines, net 1,007.93 .. "
            "1,085.61 m2; every other line byte-identical; the Gate B integration package",
}
PROPOSED = ("1.62.0 (T-314): restated by the pending ARCH_TAKEOFF_V3.0.62 package (Gate B): FIN.EXT.FINISH face rows "
            "by element; the released capability of V2.9 + route G is unchanged")
OPT_IN = "ARCH_TAKEOFF_V3.0.62 (engine/source/arch_v3062.py, opt-in candidate; pending Gate B, T-314)"
MISS = {
    "B4-04": ("in the opt-in candidate V3.0.62: exterior face rows by element (R-T314-1); W02 / D-GF-07 holes, parapet "
              "heights, plinth bottom / finish and 6 slab-edge depths HELD; corners m.l, copings, drips, beads, frames "
              "and the upturn-zone face named MISSING (no item code yet)"),
    "B4-07": ("in the opt-in candidate V3.0.62: FIN.EXT.FINISH 18 lines from the face set of record (T-567), owner "
              "Q-07 B figure beside, never the quantity; specification of the finish still not read"),
}


def _at(path, pattern):
    for i, ln in enumerate((ROOT / path).read_text(encoding="utf-8").splitlines(), 1):
        if re.search(pattern, ln):
            return f"{path}:{i}"
    raise SystemExit(f"{path}: no line matches {pattern!r}")


def build(task_commit):
    old = json.loads(OLD.read_text(encoding="utf-8"))
    if [p["task"] for p in old["pending_packages"]] != ["T-423", "T-563"]:
        raise SystemExit(f"{old['version']} pending packages {[p['task'] for p in old['pending_packages']]}: expected "
                         "exactly T-423 (V3.0.60) and T-563 (V3.0.61) below this package")
    if old["candidate"]["method_version"] != "ARCH_TAKEOFF_V3.0.59":
        raise SystemExit(f"{old['version']}: candidate of record {old['candidate']['method_version']}, expected "
                         "ARCH_TAKEOFF_V3.0.59 (V3.0.62 extends the pending V3.0.61)")
    new = copy.deepcopy(old)
    new["version"] = VERSION
    new["supersedes"] = (f"{old['version']} (kept unchanged on disk; every released-configuration field, every T-637 "
                         "field, the candidate of record ARCH_TAKEOFF_V3.0.59, its census, the pending T-423 / T-563 "
                         "packages and every family's candidate block copied unchanged; B4-04 / B4-07 text for the "
                         "pending V3.0.62 package)")
    new["source"] = (old["source"] + f" | {VERSION} (T-314): {old['version']} + pending ARCH_TAKEOFF_V3.0.62 "
                     "(rule r3, after the pending V3.0.60 / V3.0.61) + the exterior finish families it names; no promotion, no "
                     "quantity, capability or owner change")
    new["pending_packages"] = list(old["pending_packages"]) + [dict(PENDING, task_commit=task_commit)]
    fams = {f["code"]: f for f in new["families"]}
    ev = (f"{_at(MOD, r'^def changes_for')} changes_for(): face rows by element and levels, stale bindings "
          f"refused; {_at(MOD, r'^def check_faces')} check_faces(): faces / holes once, held never 0; "
          f"{_at(MOD, r'^def check_totals')} check_totals(); "
          f"{_at(TST, r'^def test_')} (synthetic villa by hand)")
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
