"""T-655: build rules/coverage/BOQ_FAMILY_MASTER_1.62.0.json = 1.61.0 (T-563, merged; never edited)
  + the PROMOTION of the two packages 1.61.0 holds pending that have since merged (T-423 r3 ARCH_TAKEOFF_V3.0.60, merge
    62e18eed, Verifier 2026-11-09 14:05 Gate B step 3; T-563 ARCH_TAKEOFF_V3.0.61, merge e04d99d9, Verifier 2026-11-09
    16:13 Gate B step 4), by the T-485 rule R-T485-1, with the T-483 r2 promotion functions UNCHANGED
    (research/agents_t483/build_master_1_48_0.py, its module constants set to this promotion, exactly as T-525 / T-651
    did): merge commits and verdicts from git and the board (out/PROMOTIONS_SOURCE_1_62_0.json,
    t655_promotions_source.py on 1.61.0), the families each package changed from the LINE DIFF V3.0.59 -> V3.0.60 ->
    V3.0.61 of this task's reproduced chain run (out/T655_PACKAGE_FAMILIES.json, t655_package_families.py, chain
    (59, 60, 61)), and the candidate census re-run at V3.0.61 (out/LINE_INDEX_V3_0_61.json,
    research/agents_t479/t479_registry_census.py unchanged; the same tool on V3_0_59 reproduces T-651's
    LINE_INDEX_V3_0_61.json byte for byte).

GATE FIX F-C-T563-1 (tests/t485_registry_promotion red on the working branch: T-423 and T-563 merged but still pending
in the newest registry). No new pending package is added (T-655 is registry-only: no method version, no line). No
quantity, capability, owner or line change with this file; the released default is untouched; every field of 1.61.0
outside the promotion set is copied unchanged.

    python3 -I research/agents_t655/build_master_1_62_0.py --write | --check
"""
from __future__ import annotations

import copy
import hashlib
import json
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

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.61.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.62.0.json"
VERSION = "1.62.0"
PROMOTIONS = HERE / "out/PROMOTIONS_SOURCE_1_62_0.json"
ATTRIB = HERE / "out/T655_PACKAGE_FAMILIES.json"
INDEX = HERE / "out/LINE_INDEX_V3_0_61.json"
BOARD_COMMIT = "b3bb1535"    # agents/control at the T-655 claim (holds the T-423 and T-563 verdicts)
OLD_CAND = "ARCH_TAKEOFF_V3.0.59"
CAND, AS_OF = "ARCH_TAKEOFF_V3.0.61", "T-563"
DIFF_SPAN = "V3.0.60 .. V3.0.61"
WHO = "T-655"

CONSTANTS = (("VERSION", VERSION), ("BOARD_COMMIT", BOARD_COMMIT), ("OLD_CAND", OLD_CAND), ("CAND", CAND),
             ("AS_OF", AS_OF), ("DIFF_SPAN", DIFF_SPAN))


def build():
    """the T-483 r2 promotion functions read their module constants: they point at THIS promotion while it is built
    and are restored afterwards (the 1.48.0 builder itself is never changed)"""
    saved = {k: getattr(P48, k) for k, _v in CONSTANTS}
    try:
        for k, v in CONSTANTS:
            setattr(P48, k, v)
        return _build()
    finally:
        for k, v in saved.items():
            setattr(P48, k, v)


def _build():
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
    new["supersedes"] = (f"{old['version']} (kept unchanged on disk; every released-configuration field and every "
                         f"T-637 field copied unchanged; its {len(promoted)} pending package promoted to "
                         f"candidate_packages; the families it changed re-derived at {CAND}, every other family's "
                         f"candidate block moved to {CAND} with its census asserted unchanged; no new pending package "
                         f"(T-655 is a registry gate fix; T-314 r3 renumbers its pending master above this file at hand-in)")
    new["source"] = (old["source"] + f" | {VERSION} ({WHO}, gate fix): {old['version']} + the {len(promoted)} merged "
                     f"pending package promoted (R-T485-1, merge commit + Checker verdict; census + line diff at "
                     f"{CAND}); no pending package; no quantity, capability or owner change")
    head = new["v3_0_candidate"].split(": the same opt-in candidate", 1)
    if len(head) != 2:
        raise SystemExit("v3_0_candidate text has no head to restate")
    vc = attrib["versions"][CAND]
    new["v3_0_candidate"] = (f"{CAND} ({AS_OF} merge {prom[AS_OF]['merge_commit'][:8]}, Verifier "
                             f"{prom[AS_OF]['verdict_time']}, Gate B PASS; BOQ_LINES {vc['lines_sha256'][:8]}): "
                             "the same opt-in candidate" + head[1])
    new["candidate"] = dict(old["candidate"], method_version=CAND, as_of_package=AS_OF)
    new["candidate_packages"] = old["candidate_packages"] + promoted
    new["pending_packages"] = []
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
                raise SystemExit(f"{code}: no line changed {OLD_CAND[-7:]} -> {CAND[-7:]} but its census moved")
            f["candidate"] = P48.carried_block(f)
            f["candidate"]["candidate_basis"] = f["candidate"]["candidate_basis"].replace(
                f"+ {DIFF_SPAN} (T-483 r2: no line", f"+ {DIFF_SPAN} ({WHO}: no line")
        if code in by_family and f["candidate"]["state"] != "NOT_IN_CANDIDATE" and f["in_v3_0_candidate"] == "no":
            f["in_v3_0_candidate"] = "yes"
        counts[f["candidate"]["state"]] += 1
        yes_no[f["in_v3_0_candidate"]] += 1
    new["candidate_state_counts"] = counts
    new["in_v3_0_candidate_counts"] = yes_no

    old_cen = old["candidate_census"]
    new["candidate_census"] = dict(
        old_cen, method_version=CAND, lines=census["lines"], lines_sha256=index["inputs"]["lines"],
        verdicts_sha256=index["inputs"].get("verdicts"), downgrades_sha256=index["inputs"].get("downgrades"),
        index="research/agents_t655/out/LINE_INDEX_V3_0_61.json (sha256 " + hashlib.sha256(INDEX.read_bytes()).hexdigest()
              + ")",
        scope=(f"the development villa run of the merged candidate of record V3.0.61 (T-563 merge "
               f"{prom[AS_OF]['merge_commit'][:8]}; BOQ_LINES {vc['lines_sha256'][:8]} reproduced by {WHO} from the "
               f"Drive copies, V3.0.59 = {attrib['versions'][OLD_CAND]['lines_sha256'][:8]} and V3.0.60 = "
               f"{attrib['versions']['ARCH_TAKEOFF_V3.0.60']['lines_sha256'][:8]} on the way); the V3.0.44 verdict set and the T-469 downgrade "
               "snapshot bind by line content, as in 1.43.0"),
        families=cc, not_a_boq_lines=census["not_a_boq_lines"], no_family=census["no_family"],
        issue_counts=census["issue_counts"],
        stale_in_candidate_vs_registry=C.compare_blocks({"families": cc, "candidate_version": CAND}, new),
        previous={"method_version": old_cen["method_version"], "lines": old_cen["lines"],
                  "lines_sha256": old_cen["lines_sha256"]})
    new["promotion"] = {
        "task": WHO, "round": "r1", "from_registry": old["version"], "promoted": [p["task"] for p in promoted],
        "previous_promotion": {"task": old["promotion"]["task"], "from_registry": old["promotion"]["from_registry"],
                               "promoted": old["promotion"]["promoted"]},
        "merge_commits_source": "research/agents_t655/out/PROMOTIONS_SOURCE_1_62_0.json (sha256 "
                                + hashlib.sha256(PROMOTIONS.read_bytes()).hexdigest() + ")",
        "line_diff": "research/agents_t655/out/T655_PACKAGE_FAMILIES.json (sha256 "
                     + hashlib.sha256(ATTRIB.read_bytes()).hexdigest() + ")",
        "rule": old["promotion"]["rule"],
        "quantity_change": "none (no engine, method, line or capability field moves)",
        "line_index": "research/agents_t655/out/LINE_INDEX_V3_0_61.json"}
    return new


def text(doc):
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"


def problems(doc):
    return FMC.check(doc, root=ROOT, is_ancestor=FMC.git_is_ancestor) + B.census_problems(doc)


def main(argv):
    if "--check" in argv:
        ok = NEW.read_text(encoding="utf-8") == text(build())
        bad = problems(json.loads(NEW.read_text(encoding="utf-8")))
        print(f"{VERSION} equals its builder:", ok, "| problems:", bad)
        return 0 if ok and not bad else 1
    if "--write" not in argv:
        print("--write or --check is required")
        return 2
    doc = build()
    bad = problems(doc)
    for b in bad:
        print("PROBLEM", b)
    NEW.write_text(text(doc), encoding="utf-8")
    print("written", NEW.relative_to(ROOT), f"({len(bad)} problem(s))")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
