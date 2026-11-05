"""T-498 r2: build rules/coverage/BOQ_FAMILY_MASTER_1.55.0.json = 1.54.0 (T-310 r7, merged 87ef8718; never edited)
  (1) + the PROMOTION of the one package 1.54.0 holds pending that has since merged (T-310 r7 V3.0.57, merge 87ef8718,
      Verifier 2026-11-04 22:45 Gate B), by the T-485 rule R-T485-1, with the T-483 r2 promotion functions UNCHANGED
      (research/agents_t483/build_master_1_48_0.py): merge commit and verdict from git and the board
      (out/PROMOTIONS_SOURCE_1_55_0.json, t498_promotions_source.py on 1.54.0), the families the package changed from
      the LINE DIFF V3.0.56 -> V3.0.57 of this task's reproduced chain run (out/T498_PACKAGE_FAMILIES.json,
      t498_package_families.py, chain (56, 57)), and the candidate census re-run at V3.0.57
      (out/LINE_INDEX_V3_0_57.json, research/agents_t479/t479_registry_census.py unchanged; verdict set board
      verdicts/V3.0.44 b3b08dd7, downgrade snapshot research/agents_t469 81732639);
  (2) + the pending ARCH_TAKEOFF_V3.0.58 package (T-498, tools/family_master_candidate.py rule r3), the B9-01 / B9-04
      text, and the four item codes the package's lines carry: MAS.UNITS.BLACK / MAS.UNITS.WHITE owned by B9-01 (the
      'pcs procurement' part of block walls) and MAS.MORTAR.BLACK / MAS.GLUE.AAC owned by B9-04 (mortar / glue), one
      family per code. B9-04 owned no item code: its census entry moves from 'n/a' to 'no' (0 lines at V3.0.57,
      asserted); B9-01's census is unchanged (no line of the new codes at V3.0.57); candidate states stay until a
      promotion;
  (3) B9-04 CAPABILITY NOT_IMPLEMENTED -> IMPLEMENTED_NOT_INTEGRATED (RAISED; the T-199 1.25.0 precedent): merged,
      tested code now writes its two codes (engine/source/arch_v3058.py, opt-in only; the released V2.9 + route G reads
      none of it); its name_terms leave with NOT_IMPLEMENTED; capability counts re-derived.

r1 built 1.54.0 on 1.53.0 for the same package as V3.0.57; T-310 merged 1.54.0 / V3.0.57 first (merge-order rule: the
package READY later rebases and renumbers). No quantity, owner or line change with this file; the released default is
untouched.

    python3 -I research/agents_t498/build_master_1_55_0.py --task-commit <sha> | --check
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for _p in (ROOT, ROOT / "research" / "agents_t479", ROOT / "research" / "agents_t485", ROOT / "research" / "agents_t483"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import t479_registry_census as C  # noqa: E402
import build_master_1_43_0 as B  # noqa: E402  (unit text and release rule of T-485, unchanged)
import build_master_1_48_0 as P48  # noqa: E402  (T-483 r2 promotion functions, unchanged)
from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.54.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.55.0.json"
VERSION = "1.55.0"
PROMOTIONS = HERE / "out/PROMOTIONS_SOURCE_1_55_0.json"
ATTRIB = HERE / "out/T498_PACKAGE_FAMILIES.json"
INDEX = HERE / "out/LINE_INDEX_V3_0_57.json"
BOARD_COMMIT = "0884a2d0"
OLD_CAND = "ARCH_TAKEOFF_V3.0.56"
CAND, AS_OF = "ARCH_TAKEOFF_V3.0.57", "T-310"
DIFF_SPAN = "V3.0.57"
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
MOD = "engine/source/arch_v3058.py"
TST = "tests/t498_block_materials/test_arch_v3058.py"
UB, UW, MO, GL = "MAS.UNITS.BLACK", "MAS.UNITS.WHITE", "MAS.MORTAR.BLACK", "MAS.GLUE.AAC"
NEW_CODES = {"B9-04": [MO, GL]}
ADD_CODES = {"B9-01": [UB, UW]}   # B9-01 already owns MAS.BLOCK etc.: codes appended
PENDING = {
    "task": "T-498", "method_version": "ARCH_TAKEOFF_V3.0.58", "module": MOD,
    "status": FMC.PENDING_STATUS, "integrates": ["T-453", "T-506", "T-487", "T-488"],
    "tests": ["tests/t498_block_materials"],
    "changes_families_by_item_code": [UB, UW, MO, GL],
    "note": "T-498 (research/agents_t498/T-498_BLOCK_MATERIALS_INTEGRATION.md): blockwork material lines beside the "
            "MAS.BLOCK lines (R-T498-1), recomputed on the V3.0.57 masonry lines (= V3.0.56: T-310 moved "
            "waterproofing only) with the merged T-453 r2 machinery "
            "(material base = contract net - REQUIRED RC lintel faces bound to the B9-02 lines): black 0.20 units "
            "1,075.80 pcs (86.064 m2 VERIFIED), mortar 1.269444 m3 PROVISIONAL (10.155552 bags, 1.396388 m3 sand "
            "beside), AAC glue 20.061 kg VERIFIED + 23.535 kg PROVISIONAL + range 842.06025 .. 861.32025 kg (3 lines); "
            "0.15 m black units / mortar, white units and every held masonry line blank by name; the Gate B "
            "integration package",
}
PROPOSED = ("1.55.0 (T-498): moved by the pending ARCH_TAKEOFF_V3.0.58 package (Gate B); the released capability of "
            "V2.9 + route G is unchanged; the V3.0.58 lines stay pending until a promotion version")
OPT_IN = "ARCH_TAKEOFF_V3.0.58 (engine/source/arch_v3058.py, opt-in candidate; pending Gate B, T-498)"
MISS = {"B9-01": "V3.0.58: black 0.20 units 1,075.80 pcs theoretical on 86.064 m2 (2 lines); 0.15 m black units HELD "
                 "(module not stated); white AAC units HELD (face not selected); procurement / breakage HELD",
        "B9-04": "V3.0.58: black mortar 1.269444 m3 PROVISIONAL (10 mm joint owner-provisional), 0.15 m mortar HELD "
                 "(T-367 beside); AAC glue 43.596 kg point + 842.06025 .. 861.32025 kg range; project bag group HELD "
                 "(16 held lines); the cross-trade cement / sand total is T-511's census"}

def _at(path, pattern):
    for i, ln in enumerate((ROOT / path).read_text(encoding="utf-8").splitlines(), 1):
        if re.search(pattern, ln):
            return f"{path}:{i}"
    raise SystemExit(f"{path}: no line matches {pattern!r}")


CONSTANTS = (("VERSION", VERSION), ("BOARD_COMMIT", BOARD_COMMIT), ("OLD_CAND", OLD_CAND), ("CAND", CAND),
             ("AS_OF", AS_OF), ("DIFF_SPAN", DIFF_SPAN))


def build(task_commit):
    """the T-483 r2 promotion functions read their module constants: they point at THIS promotion while it is built
    and are restored afterwards (the 1.48.0 builder itself is never changed)"""
    saved = {k: getattr(P48, k) for k, _v in CONSTANTS}
    try:
        for k, v in CONSTANTS:
            setattr(P48, k, v)
        return _build(task_commit)
    finally:
        for k, v in saved.items():
            setattr(P48, k, v)


def _build(task_commit):
    old = json.loads(OLD.read_text(encoding="utf-8"))
    prom = {p["task"]: p for p in json.loads(PROMOTIONS.read_text(encoding="utf-8"))}
    attrib = json.loads(ATTRIB.read_text(encoding="utf-8"))
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    new = copy.deepcopy(old)
    new["version"] = VERSION
    pend = old["pending_packages"]
    if sorted(prom) != sorted(p["task"] for p in pend):
        raise SystemExit(f"promotion source {sorted(prom)} is not every pending package of {old['version']}")
    promoted = [dict(P48.promote(p, prom[p["task"]], attrib), promoted_in=f"{VERSION} (T-498)") for p in pend]
    for p in promoted:
        p["development_villa_run"] = p["development_villa_run"].replace("T-483 r2 chain run", "T-498 chain run")
    new["supersedes"] = (f"{old['version']} (kept unchanged on disk; every released-configuration field copied "
                         f"unchanged; its {len(promoted)} pending package promoted to candidate_packages; the families "
                         f"it changed re-derived at {CAND}, every other family's candidate block moved to {CAND} with "
                         f"its census asserted unchanged (B9-04: n/a -> no by its new item codes); B9-01 / B9-04 text "
                         f"and the four item codes for the pending V3.0.58 package; B9-04 capability "
                         f"NOT_IMPLEMENTED -> IMPLEMENTED_NOT_INTEGRATED)")
    new["source"] = (old["source"] + f" | {VERSION} (T-498): {old['version']} + the {len(promoted)} merged pending "
                     f"package promoted (R-T485-1, merge commit + Checker verdict; census + line diff at {CAND}) + "
                     "pending ARCH_TAKEOFF_V3.0.58 (rule r3) + the B9-01 / B9-04 text and the four material item "
                     "codes it adds + B9-04 capability NOT_IMPLEMENTED -> IMPLEMENTED_NOT_INTEGRATED (opt-in code writes "
                     "its codes, file:line); no quantity or owner change")
    head = new["v3_0_candidate"].split(": the same opt-in candidate", 1)
    if len(head) != 2:
        raise SystemExit("v3_0_candidate text has no head to restate")
    vc = attrib["versions"][CAND]
    new["v3_0_candidate"] = (f"{CAND} ({AS_OF} merge {prom[AS_OF]['merge_commit'][:8]}, Verifier "
                             f"{prom[AS_OF]['verdict_time']}, Gate B PASS; BOQ_LINES {vc['lines_sha256'][:8]}): "
                             "the same opt-in candidate" + head[1])
    new["candidate"] = dict(old["candidate"], method_version=CAND, as_of_package=AS_OF)
    new["candidate_packages"] = old["candidate_packages"] + promoted
    new["pending_packages"] = [dict(PENDING, task_commit=task_commit)]
    pkg_versions = {p["task"]: FMC.version_key(p["method_version"]) for p in new["candidate_packages"]}

    fams0 = {f["code"]: f for f in new["families"]}
    for code, codes in NEW_CODES.items():
        if fams0[code].get("item_codes") or fams0[code]["candidate"]["state"] != "NOT_IN_CANDIDATE":
            raise SystemExit(f"{code}: already owns item codes or is in the candidate")
        fams0[code]["item_codes"] = list(codes)
    for code, codes in ADD_CODES.items():
        if set(codes) & set(fams0[code].get("item_codes") or ()):
            raise SystemExit(f"{code}: already owns {codes}")
        fams0[code]["item_codes"] = list(fams0[code]["item_codes"]) + list(codes)
    by_family = {}
    for p in promoted:
        v = attrib["versions"][p["method_version"]]
        for fam, codes in v["families"].items():
            by_family.setdefault(fam, []).append((p["task"], p["method_version"].replace("ARCH_TAKEOFF_", ""), codes))

    census = C.census(index, new)
    if census["candidate_version"] != CAND or census["issue_counts"]:
        raise SystemExit(f"census {census['candidate_version']} issues {census['issue_counts']}")
    cc = {c: census["families"][c] for c in sorted(census["families"])}
    oc = old["candidate_census"]["families"]
    counts = {s: 0 for s in FMC.STATES}
    yes_no = {"yes": 0, "no": 0, "N/A": 0}
    for f in new["families"]:
        code = f["code"]
        if code in by_family:
            if cc[code]["in_candidate"] != "yes":
                raise SystemExit(f"{code}: changed by a package but census {cc[code]['in_candidate']}")
            f["candidate"] = P48.touched_block(f, cc[code], by_family[code], pkg_versions)
            f["candidate"]["changed"] = f["candidate"]["changed"].replace(f"{DIFF_SPAN} by line diff (T-483 r2)",
                                                                          f"{DIFF_SPAN} by line diff (T-498)")
            f["candidate"]["candidate_basis"] = f["candidate"]["candidate_basis"].replace(
                f"+ {DIFF_SPAN} (T-483 r2)", f"+ {DIFF_SPAN} (T-498)")
        else:
            if code in NEW_CODES:
                want = dict(oc[code], in_candidate="no")
                if oc[code]["in_candidate"] != C.NOT_LINE_ATTRIBUTABLE or cc[code] != want:
                    raise SystemExit(f"{code}: its census must move only from n/a to 'no' with 0 lines")
            elif cc[code] != oc[code]:
                raise SystemExit(f"{code}: no line changed V3.0.56 -> V3.0.57 but its census moved")
            f["candidate"] = P48.carried_block(f)
            f["candidate"]["candidate_basis"] = f["candidate"]["candidate_basis"].replace(
                f"+ {DIFF_SPAN} (T-483 r2: no line", f"+ {DIFF_SPAN} (T-498: no line")
        if code in by_family and f["candidate"]["state"] != "NOT_IN_CANDIDATE" and f["in_v3_0_candidate"] == "no":
            # a family whose first candidate lines merged (B9-02 by T-487) enters the candidate: the flag follows its
            # re-derived state (tools/family_master_candidate.py rule: yes for every in-candidate state)
            f["in_v3_0_candidate"] = "yes"
        counts[f["candidate"]["state"]] += 1
        yes_no[f["in_v3_0_candidate"]] += 1
    new["candidate_state_counts"] = counts
    new["in_v3_0_candidate_counts"] = yes_no

    fams = {f["code"]: f for f in new["families"]}
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
    old_cen = old["candidate_census"]
    new["candidate_census"] = dict(
        old_cen, method_version=CAND, lines=census["lines"], lines_sha256=index["inputs"]["lines"],
        verdicts_sha256=index["inputs"].get("verdicts"), downgrades_sha256=index["inputs"].get("downgrades"),
        index="research/agents_t498/out/LINE_INDEX_V3_0_57.json (sha256 " + hashlib.sha256(INDEX.read_bytes()).hexdigest()
              + ")",
        scope=(f"the development villa run of the merged candidate of record V3.0.57 (T-310 r7 merge "
               f"{prom[AS_OF]['merge_commit'][:8]}; BOQ_LINES {vc['lines_sha256'][:8]} reproduced by T-498 from the "
               "Drive copies, V3.0.56 = 4e25c54f on the way); the V3.0.44 "
               "verdict set and the T-469 downgrade snapshot bind by line content, as in 1.43.0"),
        families=cc, not_a_boq_lines=census["not_a_boq_lines"], no_family=census["no_family"],
        issue_counts=census["issue_counts"],
        stale_in_candidate_vs_registry=C.compare_blocks({"families": cc, "candidate_version": CAND}, new),
        previous={"method_version": old_cen["method_version"], "lines": old_cen["lines"],
                  "lines_sha256": old_cen["lines_sha256"]})
    new["promotion"] = {
        "task": "T-498", "round": "r2", "from_registry": old["version"], "promoted": [p["task"] for p in promoted],
        "previous_promotion": {"task": old["promotion"]["task"], "from_registry": old["promotion"]["from_registry"],
                               "promoted": old["promotion"]["promoted"]},
        "merge_commits_source": "research/agents_t498/out/PROMOTIONS_SOURCE_1_55_0.json (sha256 "
                                + hashlib.sha256(PROMOTIONS.read_bytes()).hexdigest() + ")",
        "line_diff": "research/agents_t498/out/T498_PACKAGE_FAMILIES.json (sha256 "
                     + hashlib.sha256(ATTRIB.read_bytes()).hexdigest() + ")",
        "rule": old["promotion"]["rule"],
        "quantity_change": "none (no engine, method, line or capability field moves)",
        "line_index": "research/agents_t498/out/LINE_INDEX_V3_0_57.json"}
    return new


RAISE = "B9-04"
RAISE_IMPL = "ARCH_TAKEOFF_V3.0.58 (opt-in): MAS.MORTAR.BLACK, MAS.GLUE.AAC"


def raise_capability(new):
    """(3): B9-04 NOT_IMPLEMENTED -> IMPLEMENTED_NOT_INTEGRATED by merged-candidate code that writes its codes (opt-in
    only: released_method_reads stays 'none'); rank and counts as T-199 build_master_1_25_0 derives them"""
    f = {x["code"]: x for x in new["families"]}[RAISE]
    if f["capability"] != "NOT_IMPLEMENTED" or f["released_method_reads"] != "none":
        raise SystemExit(f"{RAISE}: not a NOT_IMPLEMENTED family the released route never reads")
    rank = {k: i for i, k in enumerate(new["capability_states"])}
    f["capability"] = "IMPLEMENTED_NOT_INTEGRATED"
    c0, c1 = rank[f["capability_1_0_0"]], rank[f["capability"]]
    f["capability_change"] = "UNCHANGED" if c0 == c1 else ("RAISED" if c1 < c0 else "LOWERED")
    f["implementation"] = RAISE_IMPL
    f.pop("name_terms", None)
    f["evidence"] = [e for e in f["evidence"] if not e.startswith("no method emits a line of this family")]
    f["missing"] = MISS[RAISE] + " | released route: block mortar / glue not measured"
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
