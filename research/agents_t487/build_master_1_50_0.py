"""T-487: build rules/coverage/BOQ_FAMILY_MASTER_1.50.0.json = 1.48.0 (T-483 r2, merged ea7d375f; never edited)
  (1) + the PROMOTION of the one package 1.48.0 holds pending that has since merged (T-483 V3.0.51, merge ea7d375f,
      Verifier 2026-11-04 08:06 Gate B), by the T-485 rule R-T485-1 (a merged package never stays pending), with the
      T-483 r2 promotion functions UNCHANGED (research/agents_t483/build_master_1_48_0.py promote / touched_block /
      carried_block, its module constants set to this promotion): merge commit and verdict from git and the board
      (out/PROMOTIONS_SOURCE_1_50_0.json, research/agents_t483/t483_promotions_source.build on 1.48.0), the families
      the package changed from the LINE DIFF V3.0.50 -> V3.0.51 of this task's reproduced chain run
      (out/T487_PACKAGE_FAMILIES.json, research/agents_t483/t483_package_families.attribute, chain (50, 51)), and the
      candidate census re-run at V3.0.51 (out/LINE_INDEX_V3_0_51.json, research/agents_t479/t479_registry_census.py
      unchanged; verdict set board verdicts/V3.0.44 b3b08dd7, downgrade snapshot research/agents_t469 81732639);
  (2) + the pending ARCH_TAKEOFF_V3.0.53 package (T-487, tools/family_master_candidate.py rule r3) and the B9-02 text.

1.49.0 is T-310's (V3.0.52), built in parallel on a READY branch; under the merge-order rule the package merged later
rebases on the earlier. No quantity, capability, owner or line change with this file; B9-02 stays NOT_IN_CANDIDATE in
the census (its lines are V3.0.53's, pending) until a promotion version after Gate B; the released default is untouched.

    python3 -I research/agents_t487/build_master_1_50_0.py --task-commit <sha> | --check
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

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.48.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.50.0.json"
VERSION = "1.50.0"
PROMOTIONS = HERE / "out/PROMOTIONS_SOURCE_1_50_0.json"
ATTRIB = HERE / "out/T487_PACKAGE_FAMILIES.json"
INDEX = HERE / "out/LINE_INDEX_V3_0_51.json"
BOARD_COMMIT = "99b724b3"
OLD_CAND = "ARCH_TAKEOFF_V3.0.50"
CAND, AS_OF = "ARCH_TAKEOFF_V3.0.51", "T-483"
DIFF_SPAN = "V3.0.51"
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
MOD = "engine/source/arch_v3053.py"
TST = "tests/t487_lintel_lines/test_arch_v3053.py"
PENDING = {
    "task": "T-487", "method_version": "ARCH_TAKEOFF_V3.0.53", "module": MOD,
    "status": FMC.PENDING_STATUS, "integrates": ["T-453"],
    "tests": ["tests/t487_lintel_lines"],
    "changes_families_by_item_code": ["STR.CONC.LINTEL"],
    "note": "T-487 (research/agents_t487/T-487_LINTEL_LINES.md; F-T479-2): the B9-02 lintel lines added from the "
            "Checker-verified T-453 r2 lintel ledger by the printed structural LINTEL SCHEDULE (R-T487-1): 60 "
            "STR.CONC.LINTEL m3 lines, one per opening in masonry: 16 REQUIRED PROVISIONAL 1 piece each = 1.016 m3 "
            "(formwork 14.845 m2 and host faces beside, not booked), 42 HELD + 2 FLAGGED BLOCKED_RFI blank by name; "
            "MAS.BLOCK contract area and every V3.0.51 line byte-identical; the Gate B integration package",
}
PROPOSED = ("1.50.0 (T-487): moved by the pending ARCH_TAKEOFF_V3.0.53 package (Gate B); the released capability of "
            "V2.9 + route G is unchanged; the candidate block stays NOT_IN_CANDIDATE until a promotion version")
OPT_IN = "ARCH_TAKEOFF_V3.0.53 (engine/source/arch_v3053.py, opt-in candidate; pending Gate B, T-487)"
MISS = ("V3.0.53: 16 REQUIRED RC lintels 1.016 m3 PROVISIONAL (jamb bearing, RC-column jambs and the 0.06 m build-up "
        "STAND-IN open); 42 HELD (head / host wall not established) and 2 FLAGGED (W13, W26: which piece is over the "
        "opening) blank; lintel formwork (B10-13) beside, bar steel kg (B11) HELD; precast-rule villas (no printed "
        "schedule) not wired")


def _at(path, pattern):
    for i, ln in enumerate((ROOT / path).read_text(encoding="utf-8").splitlines(), 1):
        if re.search(pattern, ln):
            return f"{path}:{i}"
    raise SystemExit(f"{path}: no line matches {pattern!r}")


def _set_promotion_constants():
    """the T-483 r2 promotion functions read their module constants: point them at THIS promotion"""
    for k, v in (("VERSION", VERSION), ("BOARD_COMMIT", BOARD_COMMIT), ("OLD_CAND", OLD_CAND), ("CAND", CAND),
                 ("AS_OF", AS_OF), ("DIFF_SPAN", DIFF_SPAN)):
        setattr(P48, k, v)


def build(task_commit):
    _set_promotion_constants()
    old = json.loads(OLD.read_text(encoding="utf-8"))
    prom = {p["task"]: p for p in json.loads(PROMOTIONS.read_text(encoding="utf-8"))}
    attrib = json.loads(ATTRIB.read_text(encoding="utf-8"))
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    new = copy.deepcopy(old)
    new["version"] = VERSION
    pend = old["pending_packages"]
    if sorted(prom) != sorted(p["task"] for p in pend):
        raise SystemExit(f"promotion source {sorted(prom)} is not every pending package of {old['version']}")
    promoted = [dict(P48.promote(p, prom[p["task"]], attrib), promoted_in=f"{VERSION} (T-487)") for p in pend]
    for p in promoted:
        p["development_villa_run"] = p["development_villa_run"].replace("T-483 r2 chain run", "T-487 chain run")
    new["supersedes"] = (f"{old['version']} (kept unchanged on disk; every released-configuration field copied "
                         f"unchanged; its {len(promoted)} pending package promoted to candidate_packages; the families "
                         f"it changed re-derived at {CAND}, every other family's candidate block moved to {CAND} with "
                         f"its census asserted unchanged; B9-02 text for the pending V3.0.53 package; 1.49.0 is "
                         f"T-310's, built in parallel)")
    new["source"] = (old["source"] + f" | {VERSION} (T-487): {old['version']} + the {len(promoted)} merged pending "
                     f"package promoted (R-T485-1, merge commit + Checker verdict; census + line diff at {CAND}) + "
                     "pending ARCH_TAKEOFF_V3.0.53 (rule r3) + the B9-02 text it changes; no quantity, capability or "
                     "owner change")
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
                                                                          f"{DIFF_SPAN} by line diff (T-487)")
            f["candidate"]["candidate_basis"] = f["candidate"]["candidate_basis"].replace(
                f"+ {DIFF_SPAN} (T-483 r2)", f"+ {DIFF_SPAN} (T-487)")
        else:
            if cc[code] != oc[code]:
                raise SystemExit(f"{code}: no line changed V3.0.50 -> V3.0.51 but its census moved")
            f["candidate"] = P48.carried_block(f)
            f["candidate"]["candidate_basis"] = f["candidate"]["candidate_basis"].replace(
                f"+ {DIFF_SPAN} (T-483 r2: no line", f"+ {DIFF_SPAN} (T-487: no line")
        counts[f["candidate"]["state"]] += 1
        yes_no[f["in_v3_0_candidate"]] += 1
    new["candidate_state_counts"] = counts
    new["in_v3_0_candidate_counts"] = yes_no

    fams = {f["code"]: f for f in new["families"]}
    f = fams["B9-02"]
    f["evidence"] = list(f["evidence"]) + [
        f"{_at(MOD, r'^def changes_for')} changes_for(): one STR.CONC.LINTEL m3 line per opening in masonry, REQUIRED "
        f"valued B x D x (w + 2 x bearing) recomputed from the printed schedule and asserted equal to the ledger, "
        f"HELD / FLAGGED blank; {_at(MOD, r'^def check_lintels')} check_lintels(); "
        f"{_at(TST, r'^def test_hand_quantities_and_states')} (villa L by hand, 0.14225 m3)"]
    f["opt_in_readers"] = str(f.get("opt_in_readers") or "") + " | " + OPT_IN
    f["missing"] = str(f.get("missing") or "") + " | " + MISS
    f["note"] = str(f.get("note") or "") + " | " + PROPOSED

    old_cen = old["candidate_census"]
    new["candidate_census"] = dict(
        old_cen, method_version=CAND, lines=census["lines"], lines_sha256=index["inputs"]["lines"],
        verdicts_sha256=index["inputs"].get("verdicts"), downgrades_sha256=index["inputs"].get("downgrades"),
        index="research/agents_t487/out/LINE_INDEX_V3_0_51.json (sha256 " + hashlib.sha256(INDEX.read_bytes()).hexdigest()
              + ")",
        scope=(f"the development villa run of the merged candidate of record V3.0.51 (T-483 merge "
               f"{prom[AS_OF]['merge_commit'][:8]}; BOQ_LINES {vc['lines_sha256'][:8]} reproduced by T-487 from the "
               "Drive copies, V3.0.47 = e86a53a8, V3.0.48 = 33a81c53 and V3.0.50 = d40c4ec5 on the way); the V3.0.44 "
               "verdict set and the T-469 downgrade snapshot bind by line content, as in 1.43.0"),
        families=cc, not_a_boq_lines=census["not_a_boq_lines"], no_family=census["no_family"],
        issue_counts=census["issue_counts"],
        stale_in_candidate_vs_registry=C.compare_blocks({"families": cc, "candidate_version": CAND}, new),
        previous={"method_version": old_cen["method_version"], "lines": old_cen["lines"],
                  "lines_sha256": old_cen["lines_sha256"]})
    new["promotion"] = {
        "task": "T-487", "round": "r1", "from_registry": old["version"], "promoted": [p["task"] for p in promoted],
        "previous_promotion": {"task": old["promotion"]["task"], "from_registry": old["promotion"]["from_registry"],
                               "promoted": old["promotion"]["promoted"]},
        "merge_commits_source": "research/agents_t487/out/PROMOTIONS_SOURCE_1_50_0.json (sha256 "
                                + hashlib.sha256(PROMOTIONS.read_bytes()).hexdigest() + ")",
        "line_diff": "research/agents_t487/out/T487_PACKAGE_FAMILIES.json (sha256 "
                     + hashlib.sha256(ATTRIB.read_bytes()).hexdigest() + ")",
        "rule": old["promotion"]["rule"],
        "quantity_change": "none (no engine, method, line or capability field moves)",
        "line_index": "research/agents_t487/out/LINE_INDEX_V3_0_51.json"}
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
