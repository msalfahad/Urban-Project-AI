"""T-423: build rules/coverage/BOQ_FAMILY_MASTER_1.55.0.json = 1.54.0 (T-310 r7, merged 87ef8718; never edited)
  (1) + the PROMOTION of the one package 1.54.0 holds pending that has since merged (T-310 V3.0.57, merge 87ef8718,
      Verifier 2026-11-04 22:45 Gate B), by the T-485 rule R-T485-1, with the T-483 r2 promotion functions UNCHANGED
      (research/agents_t483/build_master_1_48_0.py, its module constants set to this promotion, exactly as
      research/agents_t310/build_master_1_54_0.py): merge commit and verdict from git and the board
      (out/PROMOTIONS_SOURCE_1_55_0.json, t423_promotions_source.py on 1.54.0), the families the package changed from
      the LINE DIFF V3.0.56 -> V3.0.57 of this task's reproduced chain run (out/T423_PACKAGE_FAMILIES.json,
      t423_package_families.py, chain (56, 57)), and the candidate census re-run at V3.0.57
      (out/LINE_INDEX_V3_0_57.json, research/agents_t479/t479_registry_census.py unchanged; the same tool on V3_0_56
      reproduces T-310's LINE_INDEX_V3_0_56.json byte for byte);
  (2) + the pending ARCH_TAKEOFF_V3.0.58 package (T-423, tools/family_master_candidate.py rule r3) and the B3-01 /
      B3-04 / B4-01 / B4-03 / B5-01 text of the families whose lines it re-records (no quantity, no new code).

No quantity, capability, owner or line change with this file; the released default is untouched.

    python3 -I research/agents_t423/build_master_1_55_0.py --task-commit <sha> | --check
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
ATTRIB = HERE / "out/T423_PACKAGE_FAMILIES.json"
INDEX = HERE / "out/LINE_INDEX_V3_0_57.json"
BOARD_COMMIT = "7166a313"
OLD_CAND = "ARCH_TAKEOFF_V3.0.56"
CAND, AS_OF = "ARCH_TAKEOFF_V3.0.57", "T-310"
DIFF_SPAN = "V3.0.57"
WHO = "T-423"
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
MOD = "engine/source/arch_v3058.py"
TST = "tests/t423_split_remainder/test_arch_v3058.py"
PENDING = {
    "task": "T-423", "method_version": "ARCH_TAKEOFF_V3.0.58", "module": MOD,
    "status": FMC.PENDING_STATUS, "integrates": ["T-246", "T-284", "T-283", "T-335", "T-388", "T-327", "T-330"],
    "tests": ["tests/t423_split_remainder"],
    "changes_families_by_item_code": ["FIN.CEILING", "FIN.WALL.TILE", "FIN.PLASTER", "FIN.MARBLE.THRESHOLD",
                                      "FIN.FLOOR.PORCELAIN"],
    "note": "T-423 (research/agents_t423/T-423_SPLIT_REMAINDER.md): 5 FIN.CEILING lines list their HELD dome piece by id "
            "(T-330 ceiling FLAG 6 -> 1, the GF open plan set aside by name); the 1F-02 door hole D-1F-04 1.760 m2 "
            "moved to its doorway face piece on the tile and backing records (room 27.9101 unchanged); 14 marble "
            "thresholds one material state URBAN_METHOD (UP-THR-001); 15 strips carry m2 / m.l / pcs as a "
            "measure_pair; 22 lines text-only, totals unchanged; the Gate B integration package",
}

PROPOSED = ("1.55.0 (T-423): re-recorded by the pending ARCH_TAKEOFF_V3.0.58 package (Gate B); no quantity moves; the "
            "released capability of V2.9 + route G is unchanged")

OPT_IN = "ARCH_TAKEOFF_V3.0.58 (engine/source/arch_v3058.py, opt-in candidate; pending Gate B, T-423)"

MISS = {
    "B5-01": ("in the opt-in candidate V3.0.58: 5 ceiling lines list their dome piece by id; the GF open-plan list "
              "set aside (9.785604 m2 not closed by id)"),
    "B4-01": "in the opt-in candidate V3.0.58: D-1F-04 booked on the 1F-02 doorway piece; GF annex faces HELD",
    "B4-03": "in the opt-in candidate V3.0.58: D-1F-04 booked on the 1F-02 doorway piece (backing); GF annex HELD",
    "B3-04": "in the opt-in candidate V3.0.58: one material state URBAN_METHOD; m2 / m.l / pcs as measure pair",
    "B3-01": "in the opt-in candidate V3.0.58: the D-1F-03 dry strip carries m2 / m.l / pcs as a measure pair",
}

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
    promoted = [dict(P48.promote(p, prom[p["task"]], attrib), promoted_in=f"{VERSION} ({WHO})") for p in pend]
    for p in promoted:
        p["development_villa_run"] = p["development_villa_run"].replace("T-483 r2 chain run", f"{WHO} chain run")
    new["supersedes"] = (f"{old['version']} (kept unchanged on disk; every released-configuration field copied "
                         f"unchanged; its {len(promoted)} pending package promoted to candidate_packages; the families "
                         f"it changed re-derived at {CAND}, every other family's candidate block moved to {CAND} with "
                         f"its census asserted unchanged; B3-01 / B3-04 / B4-01 / B4-03 / B5-01 text for the pending "
                         f"V3.0.58 package; T-498 may build its own in parallel)")
    new["source"] = (old["source"] + f" | {VERSION} ({WHO}): {old['version']} + the {len(promoted)} merged pending "
                     f"package promoted (R-T485-1, merge commit + Checker verdict; census + line diff at {CAND}) + "
                     "pending ARCH_TAKEOFF_V3.0.58 (rule r3) + the finishes families it re-records; no quantity, "
                     "capability or owner change")
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
                                                                          f"{DIFF_SPAN} by line diff ({WHO})")
            f["candidate"]["candidate_basis"] = f["candidate"]["candidate_basis"].replace(
                f"+ {DIFF_SPAN} (T-483 r2)", f"+ {DIFF_SPAN} ({WHO})")
        else:
            if cc[code] != oc[code]:
                raise SystemExit(f"{code}: no line changed V3.0.56 -> V3.0.57 but its census moved")
            f["candidate"] = P48.carried_block(f)
            f["candidate"]["candidate_basis"] = f["candidate"]["candidate_basis"].replace(
                f"+ {DIFF_SPAN} (T-483 r2: no line", f"+ {DIFF_SPAN} ({WHO}: no line")
        if code in by_family and f["candidate"]["state"] != "NOT_IN_CANDIDATE" and f["in_v3_0_candidate"] == "no":
            # a family whose first candidate lines merged (B9-02 by T-487) enters the candidate: the flag follows its
            # re-derived state (tools/family_master_candidate.py rule: yes for every in-candidate state)
            f["in_v3_0_candidate"] = "yes"
        counts[f["candidate"]["state"]] += 1
        yes_no[f["in_v3_0_candidate"]] += 1
    new["candidate_state_counts"] = counts
    new["in_v3_0_candidate_counts"] = yes_no

    old_cen = old["candidate_census"]
    new["candidate_census"] = dict(
        old_cen, method_version=CAND, lines=census["lines"], lines_sha256=index["inputs"]["lines"],
        verdicts_sha256=index["inputs"].get("verdicts"), downgrades_sha256=index["inputs"].get("downgrades"),
        index="research/agents_t423/out/LINE_INDEX_V3_0_57.json (sha256 " + hashlib.sha256(INDEX.read_bytes()).hexdigest()
              + ")",
        scope=(f"the development villa run of the merged candidate of record V3.0.57 (T-310 merge "
               f"{prom[AS_OF]['merge_commit'][:8]}; BOQ_LINES {vc['lines_sha256'][:8]} reproduced by {WHO} from the "
               "Drive copies, V3.0.55 = a498fc61 and V3.0.56 = 4e25c54f on the way); the V3.0.44 "
               "verdict set and the T-469 downgrade snapshot bind by line content, as in 1.43.0"),
        families=cc, not_a_boq_lines=census["not_a_boq_lines"], no_family=census["no_family"],
        issue_counts=census["issue_counts"],
        stale_in_candidate_vs_registry=C.compare_blocks({"families": cc, "candidate_version": CAND}, new),
        previous={"method_version": old_cen["method_version"], "lines": old_cen["lines"],
                  "lines_sha256": old_cen["lines_sha256"]})
    new["promotion"] = {
        "task": "T-423", "round": "r1", "from_registry": old["version"], "promoted": [p["task"] for p in promoted],
        "previous_promotion": {"task": old["promotion"]["task"], "from_registry": old["promotion"]["from_registry"],
                               "promoted": old["promotion"]["promoted"]},
        "merge_commits_source": "research/agents_t423/out/PROMOTIONS_SOURCE_1_55_0.json (sha256 "
                                + hashlib.sha256(PROMOTIONS.read_bytes()).hexdigest() + ")",
        "line_diff": "research/agents_t423/out/T423_PACKAGE_FAMILIES.json (sha256 "
                     + hashlib.sha256(ATTRIB.read_bytes()).hexdigest() + ")",
        "rule": old["promotion"]["rule"],
        "quantity_change": "none (no engine, method, line or capability field moves)",
        "line_index": "research/agents_t423/out/LINE_INDEX_V3_0_57.json"}
    # (2) the pending V3.0.58 package's families (after the census: it describes the merged candidate only)
    fams = {f["code"]: f for f in new["families"]}
    for code in ("B3-01", "B3-04", "B4-01", "B4-03", "B5-01"):
        f = fams[code]
        f["evidence"] = list(f["evidence"]) + [
            f"{_at(MOD, r'^def changes_for')} changes_for(): LIST_CEILING / MOVE_FACE_DEDUCTION / NOT_APPLICABLE / "
            f"MATERIAL_STATE / MEASURE_PAIR by line id, stale bindings refused; "
            f"{_at(MOD, r'^def check_split_remainder')} check_split_remainder(); "
            f"{_at(TST, r'^def test_hand_values')} (villa V423 by hand)"]
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
