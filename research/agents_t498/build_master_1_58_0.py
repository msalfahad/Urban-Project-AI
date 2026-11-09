"""T-498 r4: build rules/coverage/BOQ_FAMILY_MASTER_1.58.0.json = 1.57.0 (T-525; never edited)
  (1) + the pending ARCH_TAKEOFF_V3.0.59 package (T-498, tools/family_master_candidate.py rule r3) and the B9-01 / B9-04
      text (evidence, opt-in reader, missing, note). The four item codes the package's lines carry are ALREADY owned
      since 1.56.0 (T-637, R-T637-1: MAS.UNITS.BLACK / MAS.UNITS.WHITE on B9-01, MAS.MORTAR.BLACK / MAS.GLUE.AAC on
      B9-04, one family per code): asserted, not moved;
  (2) B9-04 CAPABILITY NOT_IMPLEMENTED -> IMPLEMENTED_NOT_INTEGRATED (RAISED; the T-199 1.25.0 precedent): tested code
      on this branch writes its two codes (engine/source/arch_v3059.py, opt-in only; the released V2.9 + route G reads
      none of it); its name_terms leave with NOT_IMPLEMENTED; the stale 'no method emits a line' evidence leaves; the
      dated 1.56.0 (T-637) evidence line is kept as history; capability counts re-derived.
No promotion: 1.57.0 holds no pending package (T-525 promoted T-507), so the candidate of record stays V3.0.58, its
census and every family's candidate block are copied unchanged. r1 .. r3 staged 1.54.0 / 1.55.0 / 1.56.0 for this
package; T-310, T-507, T-637 and T-525 merged those numbers first (merge-order rule: renumber at hand-in). No quantity,
owner or line change with this file; the released default is untouched.

    python3 -I research/agents_t498/build_master_1_58_0.py --task-commit <sha> | --check
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

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.57.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.58.0.json"
VERSION = "1.58.0"
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
MOD = "engine/source/arch_v3059.py"
TST = "tests/t498_block_materials/test_arch_v3059.py"
UB, UW, MO, GL = "MAS.UNITS.BLACK", "MAS.UNITS.WHITE", "MAS.MORTAR.BLACK", "MAS.GLUE.AAC"
OWNED = {"B9-01": [UB, UW], "B9-04": [MO, GL]}      # owned since 1.56.0 (T-637): asserted, never re-added
PENDING = {
    "task": "T-498", "method_version": "ARCH_TAKEOFF_V3.0.59", "module": MOD,
    "status": FMC.PENDING_STATUS, "integrates": ["T-453", "T-506", "T-487", "T-488"],
    "tests": ["tests/t498_block_materials"],
    "changes_families_by_item_code": [UB, UW, MO, GL],
    "note": "T-498 (research/agents_t498/T-498_BLOCK_MATERIALS_INTEGRATION.md): blockwork material lines beside the "
            "MAS.BLOCK lines (R-T498-1), recomputed on the V3.0.58 masonry lines (= V3.0.56: T-310 / T-507 moved "
            "waterproofing only) with the merged T-453 r2 machinery "
            "(material base = contract net - REQUIRED RC lintel faces bound to the B9-02 lines): black 0.20 units "
            "1,075.80 pcs (86.064 m2 VERIFIED), mortar 1.269444 m3 PROVISIONAL (10.155552 bags, 1.396388 m3 sand "
            "beside), AAC glue 20.061 kg VERIFIED + 23.535 kg PROVISIONAL + range 842.06025 .. 861.32025 kg (3 lines); "
            "0.15 m black units / mortar, white units and every held masonry line blank by name; the Gate B "
            "integration package (the stage of 74 lines; the later overlay rows on these lines chain after it, "
            "before = this package's after)",
}
PROPOSED = ("1.58.0 (T-498): moved by the pending ARCH_TAKEOFF_V3.0.59 package (Gate B); the released capability of "
            "V2.9 + route G is unchanged; the V3.0.59 lines stay pending until a promotion version")
OPT_IN = "ARCH_TAKEOFF_V3.0.59 (engine/source/arch_v3059.py, opt-in candidate; pending Gate B, T-498)"
MISS = {"B9-01": "V3.0.59: black 0.20 units 1,075.80 pcs theoretical on 86.064 m2 (2 lines); 0.15 m black units HELD "
                 "(module not stated in the stage; the Q-80 overlay rows FR-T615 chain after Gate B); white AAC units "
                 "HELD (face not selected); procurement / breakage HELD",
        "B9-04": "V3.0.59: black mortar 1.269444 m3 PROVISIONAL (10 mm joint owner-provisional), 0.15 m mortar HELD "
                 "(T-367 beside); AAC glue 43.596 kg point + 842.06025 .. 861.32025 kg range; project bag group HELD "
                 "(16 held lines); perimeter joint mortar (R-T520-1) is its own producer key, not in this stage; the "
                 "cross-trade cement / sand total is T-511's census"}
STALE_EVIDENCE = "no method emits a line of this family"


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
    new = copy.deepcopy(old)
    new["version"] = VERSION
    fams = {f["code"]: f for f in new["families"]}
    for code, codes in OWNED.items():
        if not set(codes) <= set(fams[code].get("item_codes") or ()):
            raise SystemExit(f"{code}: does not own {codes} (expected since 1.56.0, T-637)")
    owners = {}
    for f in new["families"]:
        for x in f.get("item_codes") or ():
            owners.setdefault(x, []).append(f["code"])
    if any(owners.get(c) != [fam] for fam, cs in OWNED.items() for c in cs):
        raise SystemExit("a material code is owned by more than one family")
    new["supersedes"] = (f"{old['version']} (kept unchanged on disk; every released-configuration field, every T-637 "
                         "field, the candidate of record ARCH_TAKEOFF_V3.0.58, its census and every family's "
                         "candidate block copied unchanged; B9-01 / B9-04 text for the pending V3.0.59 package; "
                         "B9-04 capability NOT_IMPLEMENTED -> IMPLEMENTED_NOT_INTEGRATED)")
    new["source"] = (old["source"] + f" | {VERSION} (T-498): {old['version']} + pending ARCH_TAKEOFF_V3.0.59 (rule r3) "
                     "+ the B9-01 / B9-04 text (codes already owned, T-637) + B9-04 capability NOT_IMPLEMENTED -> "
                     "IMPLEMENTED_NOT_INTEGRATED (opt-in code writes its codes, file:line); no promotion, no "
                     "quantity or owner change")
    new["pending_packages"] = [dict(PENDING, task_commit=task_commit)]

    ev = (f"{_at(MOD, r'^def materials_for')} materials_for(): black units / laying mortar / AAC glue / white units "
          f"beside each MAS.BLOCK line on the material base (contract net - REQUIRED lintel faces bound to valued "
          f"STR.CONC.LINTEL lines; HELD faces a named range), held masonry blank by name; "
          f"{_at(MOD, r'^def check_materials')} check_materials(); {_at(TST, r'^def test_normal_hand_figures')} "
          f"test_normal_hand_figures() (villa K498 by hand)")
    for code in ("B9-01", "B9-04"):
        f = fams[code]
        f["evidence"] = list(f["evidence"]) + [ev]
        f["opt_in_readers"] = (str(f["opt_in_readers"]) + " | " + OPT_IN) if f.get("opt_in_readers") not in \
            (None, "", "none") else OPT_IN
        f["missing"] = str(f.get("missing") or "") + " | " + MISS[code]
        f["note"] = (str(f["note"]) + " | " + PROPOSED) if f.get("note") else PROPOSED
    raise_capability(new)
    return new


RAISE = "B9-04"
RAISE_IMPL = "ARCH_TAKEOFF_V3.0.59 (opt-in): MAS.MORTAR.BLACK, MAS.GLUE.AAC"


def raise_capability(new):
    """(2): B9-04 NOT_IMPLEMENTED -> IMPLEMENTED_NOT_INTEGRATED by tested opt-in code that writes its codes
    (released_method_reads stays 'none'); rank and counts as T-199 build_master_1_25_0 derives them"""
    f = {x["code"]: x for x in new["families"]}[RAISE]
    if f["capability"] != "NOT_IMPLEMENTED" or f["released_method_reads"] != "none":
        raise SystemExit(f"{RAISE}: not a NOT_IMPLEMENTED family the released route never reads")
    rank = {k: i for i, k in enumerate(new["capability_states"])}
    f["capability"] = "IMPLEMENTED_NOT_INTEGRATED"
    c0, c1 = rank[f["capability_1_0_0"]], rank[f["capability"]]
    f["capability_change"] = "UNCHANGED" if c0 == c1 else ("RAISED" if c1 < c0 else "LOWERED")
    f["implementation"] = RAISE_IMPL
    f.pop("name_terms", None)
    f["evidence"] = [e for e in f["evidence"] if not e.startswith(STALE_EVIDENCE)]
    f["missing"] = f["missing"] + " | released route: block mortar / glue not measured"
    fam = new["families"]
    new["capability_counts"] = {k: sum(1 for x in fam if x["capability"] == k) for k in new["capability_states"]}
    new["capability_change_counts"] = {k: sum(1 for x in fam if x["capability_change"] == k)
                                       for k in ("RAISED", "LOWERED", "UNCHANGED")}


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
