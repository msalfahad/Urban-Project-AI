"""T-310 r6: build rules/coverage/BOQ_FAMILY_MASTER_1.52.0.json = 1.51.0 (T-480, merged 1b66b719; never edited)
  (1) + the PROMOTION of the one package 1.51.0 holds pending that has since merged (T-480 V3.0.54, merge 1b66b719),
      by the T-485 rule R-T485-1 (a merged package never stays pending), with the T-483 r2 promotion functions
      UNCHANGED (research/agents_t483/build_master_1_48_0.py promote / touched_block / carried_block, its module
      constants set to this promotion, exactly as research/agents_t480/build_master_1_51_0.py): merge commit and verdict
      from git and the board (out/PROMOTIONS_SOURCE_1_52_0.json, t310_promotions_source.py on 1.51.0), the families
      the package changed from the LINE DIFF V3.0.53 -> V3.0.54 of this task's reproduced chain run
      (out/T310_PACKAGE_FAMILIES.json, t310_package_families.py, chain (53, 54)), and the candidate census re-run at
      V3.0.54 (out/LINE_INDEX_V3_0_54.json, research/agents_t479/t479_registry_census.py unchanged; verdict set board
      verdicts/V3.0.44, downgrade snapshot research/agents_t469);
  (2) + the pending ARCH_TAKEOFF_V3.0.55 package (T-310, tools/family_master_candidate.py rule r3) and the B8-01 /
      B8-02 / B8-03 / B8-09 text of the families whose lines it changes or adds; B8-09 owns the two pool layer codes
      WP.POOL.MEMBRANE and WP.POOL.PROTECTION_SCREED (ELEMENT_REGISTER: the pool membrane is its own family, never
      inside B8-08 or the concrete line; function HELD S8.2).

The census is taken with the 1.51.0 family codes (the candidate of record V3.0.54 carries no pool layer line); the B8-09
codes are added after it, so the census describes the merged candidate only. r4 built the same package text as 1.49.0
on 1.48.0 (V3.0.52, never merged; T-487 took 1.50.0 and T-480 1.51.0 meanwhile). T-508 may build its own master in
parallel; under the merge-order rule the package merged later rebases. No quantity, capability, owner or line change
with this file; the released default is untouched.

    python3 -I research/agents_t310/build_master_1_52_0.py --task-commit <sha> | --check
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

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.51.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.52.0.json"
VERSION = "1.52.0"
PROMOTIONS = HERE / "out/PROMOTIONS_SOURCE_1_52_0.json"
ATTRIB = HERE / "out/T310_PACKAGE_FAMILIES.json"
INDEX = HERE / "out/LINE_INDEX_V3_0_54.json"
BOARD_COMMIT = "c2d9eb13"
OLD_CAND = "ARCH_TAKEOFF_V3.0.53"
CAND, AS_OF = "ARCH_TAKEOFF_V3.0.54", "T-480"
DIFF_SPAN = "V3.0.54"
WHO = "T-310 r6"
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
MOD = "engine/source/arch_v3055.py"
TST = "tests/t310_wet_area_wp/test_arch_v3055.py"
PENDING = {
    "task": "T-310", "method_version": "ARCH_TAKEOFF_V3.0.55", "module": MOD,
    "status": FMC.PENDING_STATUS, "integrates": ["T-303", "T-309", "T-286", "T-458"],
    "tests": ["tests/t310_wet_area_wp"],
    "changes_families_by_item_code": ["FIN.WP.WALL_UPTURN", "FIN.WP.FLOOR", "FIN.WP.TERMINATION",
                                      "FIN.WP.DOORWAY_TRANSITION", "WP.POOL.MEMBRANE", "WP.POOL.PROTECTION_SCREED"],
    "note": "T-310 (research/agents_t310/T-310_WET_AREA_POOL_WP.md): 1F east bath upturn 1.480 -> 1.580 m2 (waterproofing "
            "policy V3 run, window W18 above the upturn not deducted; doorway segment HELD beside); its 3 window "
            "termination lines NOT APPLICABLE; pantry floor 13.500 -> 13.455 m2 (column 2FAE intrusion 0.045 ruled "
            "from the drawing); 11 transition lines keyed per physical door, 2 duplicates NOT APPLICABLE, 3 missing "
            "doors added HELD BLANK; pool membrane 29.582355 m2 and protection screed 1.524503 m3 added "
            "DRAWING-CONFIRMED (upstand 0 .. 1.349668 m2 / 0 .. 0.068072 m3 and the membrane function HELD beside); "
            "every other V3.0.54 line byte-identical; the Gate B integration package",
}

PROPOSED = ("1.52.0 (T-310): moved by the pending ARCH_TAKEOFF_V3.0.55 package (Gate B); the released capability "
            "of V2.9 + route G is unchanged")

OPT_IN = "ARCH_TAKEOFF_V3.0.55 (engine/source/arch_v3055.py, opt-in candidate; pending Gate B, T-310)"

MISS = {
    "B8-01": ("in the opt-in candidate V3.0.55: pantry floor membrane 13.455 m2 (box 13.500 - column 0.045, "
              "DRAWING-CONFIRMED; flush-column reading +0.045 named); penetrations still HELD"),
    "B8-02": ("in the opt-in candidate V3.0.55: one transition line per physical door (11 keyed, 2 duplicates NOT "
              "APPLICABLE, 3 missing doors HELD BLANK); every transition figure HELD / bounded (detail not printed); "
              "the pantry door's threshold / transition MISSING (binding piece)"),
    "B8-03": ("in the opt-in candidate V3.0.55: 1F east bath upturn 1.580 m2 (run by policy V3; doorway segments HELD "
              "beside); 3 window termination lines NOT APPLICABLE; the pantry open-side termination MISSING"),
    "B8-09": ("in the opt-in candidate V3.0.55: pool membrane 29.582355 m2 and protection screed 1.524503 m3 on the "
              "base and outer wall faces (DRAWING-CONFIRMED); upstand faces HELD (C9), membrane function HELD (S8.2); "
              "no water-side waterproofing is printed"),
}

POOL_CODES = ["WP.POOL.MEMBRANE", "WP.POOL.PROTECTION_SCREED"]


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
                         f"its census asserted unchanged; B8-01 / B8-02 / B8-03 / B8-09 text for the pending V3.0.55 "
                         f"package, B8-09 owning the two pool layer codes; T-508 may build its own in parallel)")
    new["source"] = (old["source"] + f" | {VERSION} ({WHO}): {old['version']} + the {len(promoted)} merged pending "
                     f"package promoted (R-T485-1, merge commit + Checker verdict; census + line diff at {CAND}) + "
                     "pending ARCH_TAKEOFF_V3.0.55 (rule r3) + the waterproofing families it changes; B8-09 owns the two "
                     "pool layer codes; no quantity, capability or owner change")
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
                raise SystemExit(f"{code}: no line changed V3.0.53 -> V3.0.54 but its census moved")
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
        index="research/agents_t310/out/LINE_INDEX_V3_0_54.json (sha256 " + hashlib.sha256(INDEX.read_bytes()).hexdigest()
              + ")",
        scope=(f"the development villa run of the merged candidate of record V3.0.54 (T-480 merge "
               f"{prom[AS_OF]['merge_commit'][:8]}; BOQ_LINES {vc['lines_sha256'][:8]} reproduced by {WHO} from the "
               "Drive copies, V3.0.51 = c0b6d664 and V3.0.53 = 36863f6c on the way); the V3.0.44 "
               "verdict set and the T-469 downgrade snapshot bind by line content, as in 1.43.0"),
        families=cc, not_a_boq_lines=census["not_a_boq_lines"], no_family=census["no_family"],
        issue_counts=census["issue_counts"],
        stale_in_candidate_vs_registry=C.compare_blocks({"families": cc, "candidate_version": CAND}, new),
        previous={"method_version": old_cen["method_version"], "lines": old_cen["lines"],
                  "lines_sha256": old_cen["lines_sha256"]})
    new["promotion"] = {
        "task": "T-310", "round": "r6", "from_registry": old["version"], "promoted": [p["task"] for p in promoted],
        "previous_promotion": {"task": old["promotion"]["task"], "from_registry": old["promotion"]["from_registry"],
                               "promoted": old["promotion"]["promoted"]},
        "merge_commits_source": "research/agents_t310/out/PROMOTIONS_SOURCE_1_52_0.json (sha256 "
                                + hashlib.sha256(PROMOTIONS.read_bytes()).hexdigest() + ")",
        "line_diff": "research/agents_t310/out/T310_PACKAGE_FAMILIES.json (sha256 "
                     + hashlib.sha256(ATTRIB.read_bytes()).hexdigest() + ")",
        "rule": old["promotion"]["rule"],
        "quantity_change": "none (no engine, method, line or capability field moves)",
        "line_index": "research/agents_t310/out/LINE_INDEX_V3_0_54.json"}
    # (2) the pending V3.0.55 package's families (after the census: it describes the merged candidate only)
    fams = {f["code"]: f for f in new["families"]}
    for code in ("B8-01", "B8-02", "B8-03", "B8-09"):
        f = fams[code]
        f["evidence"] = list(f["evidence"]) + [
            f"{_at(MOD, r'^def changes_for')} changes_for(): REVALUE_UPTURN / REVALUE_FLOOR / NOT_APPLICABLE / "
            f"KEY_DOOR / ADD_HELD_DOOR / ADD_POOL_LAYER by line id, stale bindings refused; "
            f"{_at(MOD, r'^def load_inputs')} load_inputs() (upturn value = waterproofing policy V3 run, floor = box - "
            f"deductions, one transition per door); {_at(MOD, r'^def check_wet_area_wp')} check_wet_area_wp(); "
            f"{_at(TST, r'^def test_hand_values')} (villa W310 by hand)"]
        f["opt_in_readers"] = (OPT_IN if str(f.get("opt_in_readers") or "none") == "none" else
                               str(f.get("opt_in_readers")) + " | " + OPT_IN)
        f["missing"] = str(f.get("missing") or "") + " | " + MISS[code]
        f["note"] = str(f.get("note") or "") + " | " + PROPOSED
    f = fams["B8-09"]
    if f["item_codes"]:
        raise SystemExit(f"B8-09: owns item codes in {old['version']} (expected none)")
    f["item_codes"] = list(POOL_CODES)
    f["note"] = str(f["note"]) + (" | 1.52.0 (T-310): owns WP.POOL.MEMBRANE (m2) and WP.POOL.PROTECTION_SCREED (m3), "
                                  "the printed outer protective layers of the pool (ELEMENT_REGISTER: their own "
                                  "family, never B8-08 or the concrete line); the family's water-side waterproofing "
                                  "is not printed for the development villa")
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
