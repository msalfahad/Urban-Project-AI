"""T-485: build rules/coverage/BOQ_FAMILY_MASTER_1.43.0.json = 1.42.0 (T-419, never edited) + the registry PROMOTION of
every merged candidate package (F-T479-1). NO quantity, capability, owner state, line or default changes.

    python3 -I research/agents_t485/build_master_1_43_0.py [--check] [--base X.json --version V --out Y.json]

(--base / --version / --out: the registry version is allotted at merge; the package READY second re-runs this builder
on the first merged registry, which then carries that package as pending or merged.)

1 PROMOTION: the 39 packages 1.42.0 lists in pending_packages (V3.0.8 .. V3.0.46) all merged; each moves to
  candidate_packages with its merge commit (the one merge on the working branch whose second parent holds the
  package's task commit and whose first parent does not: research/agents_t485/out/PROMOTIONS_SOURCE.json, re-checked
  by tests/t485_registry_promotion with git) and its Checker verdict (the head of the board status of its row, quoted
  verbatim, board agents/control 26ad2473). pending_packages becomes empty; candidate = ARCH_TAKEOFF_V3.0.46 / T-419.
2 CANDIDATE BLOCKS re-derived for every family at V3.0.46 from two line facts, never from an earlier package's text:
  - which packages changed the family: the line diff V3.0.(n-1) -> V3.0.n of a reproduced chain run
    (research/agents_t485/t485_package_families.py -> out/T485_PACKAGE_FAMILIES.json; item codes and counts only);
  - what the candidate carries: candidate_census, re-run by the T-479 census tool on the merged V3.0.46 run (BOQ_LINES
    35d70129 reproduced; out/LINE_INDEX_V3_0_46.json: line id, item code, unit, class, net, bounds, binding only).
  Rules: census yes + a package changed it -> INTEGRATED_IN_CANDIDATE_AND_TESTED when the family releases a quantity
  in the candidate, else HELD_IN_CANDIDATE; census yes + no package -> IN_CANDIDATE_BASE_LINES; census no ->
  NOT_IN_CANDIDATE (B8-07 / B9-02: 'no_line', with the row that will fill it); a family that owns no item code
  cannot be line-attributed: its V3.0.7 state is CARRIED, labelled so ('candidate_basis'), never re-derived.
  Earlier packages named by a V3.0.7 block are kept (their holds / releases trace stands).
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for _p in (ROOT, HERE, ROOT / "research" / "agents_t479"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import t479_registry_census as C  # noqa: E402
from tools import family_master_candidate as FMC  # noqa: E402

BASE = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.42.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.43.0.json"
VERSION = "1.43.0"
INDEX = HERE / "out/LINE_INDEX_V3_0_46.json"
PROMOTIONS = HERE / "out/PROMOTIONS_SOURCE.json"
ATTRIB = HERE / "out/T485_PACKAGE_FAMILIES.json"
BOARD_COMMIT = "26ad2473"
CAND, AS_OF = "ARCH_TAKEOFF_V3.0.46", "T-419"
I, H, BL, NI = FMC.STATES
NO_LINE_FILLED_BY = {"B8-07": "T-486", "B9-02": "T-487"}       # board rows that will fill them (Lead 2026-11-03 08:17)
STALE_NOTE = ("B8-08", "B10-13", "B7-13")                       # 1.41.0 notes that say 'as of V3.0.7'
UNITS_ORDER = ("m3", "m2", "lm", "m", "kg", "nr", "pcs", "item")


def _vkey(v):
    return FMC.version_key(v)


def verdict_text(p):
    return (f"MERGED (Verifier {p['verdict_time']}, Gate B; board {p['board_file']} row {p['task']} at agents/control "
            f"{BOARD_COMMIT}: '{p['board_status_head']}')")


def _units_text(units, key):
    parts = []
    for u in sorted(units, key=lambda x: (UNITS_ORDER.index(x) if x in UNITS_ORDER else 99, x)):
        v = units[u]
        if key == "released" and v["released_lines"]:
            parts.append(f"{u} {v['released']} ({v['released_lines']} lines)")
        if key == "held" and v["held_lines"]:
            b = (f", bounded {v['held_low']} .. {v['held_high']}" if v["held_lines"] > v["held_unknown_lines"]
                 else "")
            parts.append(f"{u} {v['held_lines']} lines ({v['held_unknown_lines']} UNKNOWN{b})")
    return "; ".join(parts)


def releases(census_fam):
    return any(v["released_lines"] for v in (census_fam.get("units") or {}).values())


def promote(pending, prom, attrib):
    """pending package (base registry) -> merged candidate package (this version)"""
    v = attrib["versions"][pending["method_version"]]
    rec = {"task": pending["task"], "method_version": pending["method_version"], "module": pending["module"],
           "merge_commit": prom["merge_commit"], "verdict": verdict_text(prom), "gate": "GATE_B",
           "integrates": list(pending["integrates"]), "tests": list(pending["tests"]),
           "task_commit": pending["task_commit"],
           "changes_families_by_item_code": list(pending["changes_families_by_item_code"]),
           "families_changed_by_line_diff": sorted(v["families"]),
           "lines_touched": v["touched"],
           "families_record_only_by_line_diff": list(v["record_families"]),
           "lines_record_only": v["record_only"],
           "development_villa_run": f"{v['lines']} lines, V3_0_{_vkey(pending['method_version'])}_BOQ_LINES.json "
                                    f"{v['lines_sha256'][:8]} (T-485 chain run, reproduced)",
           "note": pending["note"], "promoted_in": f"{VERSION} (T-485)"}
    return rec


def family_block(f, census_fam, by_family, pkg_versions):
    """-> (candidate block, in_v3_0_candidate)"""
    c, yn = _family_block(f, census_fam, by_family, pkg_versions)
    rec = (by_family.get("_record") or {}).get(f["code"])
    if rec and census_fam["in_candidate"] == "yes":
        c["record_only_packages"] = list(rec)        # text / identity / listing changes only: raise no state
    return c, yn


def _family_block(f, census_fam, by_family, pkg_versions):
    old = f["candidate"]
    code = f["code"]
    present = census_fam["in_candidate"]
    new_pk = by_family.get(code, [])
    if present == C.NOT_LINE_ATTRIBUTABLE:
        c = dict(old, method_version=CAND, as_of_package=AS_OF,
                 candidate_basis="CARRIED from ARCH_TAKEOFF_V3.0.7 (T-203 / 1.2.0): the family owns no item code, so no "
                                 "line census or line diff can attribute lines to it; state and packages NOT re-derived")
        return c, f["in_v3_0_candidate"]
    if present == "no":
        if old.get("packages") or new_pk:
            raise SystemExit(f"{code}: no candidate line but packages {old.get('packages')} {new_pk}")
        c = {"state": NI, "method_version": CAND, "packages": [], "as_of_package": AS_OF, "changed": "",
             "open": "no candidate line; the released capability above is unchanged",
             "released_in_candidate": "none",
             "candidate_basis": f"CENSUS {CAND} (candidate_census) + LINE DIFF V3.0.7 .. V3.0.46 (T-485)"}
        if code in NO_LINE_FILLED_BY:
            c["no_line"] = {
                "item_codes": list(f["item_codes"]),
                "registry_before": f"1.2.0 .. {by_family.get('_base', 'the base registry')} read {old['state']} (in_v3_0_candidate yes) without a line",
                "checked": "no line of these item codes in any reproduced candidate version V3.0.7 .. V3.0.46 "
                           "(T-485 chain run, out/T485_PACKAGE_FAMILIES.json item_code_presence) nor in the census of "
                           "V3.0.46 (T-479 F-T479-2 on V3.0.45; T-485 census on V3.0.46)",
                "filled_by": NO_LINE_FILLED_BY[code]}
            c["open"] = (f"NO_LINE: the candidate emits no {' / '.join(f['item_codes'])} line at any version; "
                         f"{NO_LINE_FILLED_BY[code]} will fill it; until then the family is outside the candidate (never "
                         "0, never 'base lines')")
        return c, "no"
    # present == "yes"
    pk = list(old.get("packages") or [])
    for t in new_pk:
        if t not in pk:
            pk.append(t)
    pk.sort(key=lambda t: pkg_versions[t])
    rel = _units_text(census_fam["units"], "released")
    held = _units_text(census_fam["units"], "held")
    basis = f"CENSUS {CAND} (candidate_census) + LINE DIFF V3.0.7 .. V3.0.46 (T-485)"
    if not pk:
        c = {"state": BL, "method_version": CAND, "packages": [], "as_of_package": AS_OF, "changed": "",
             "open": "no verified piece integrated; the lines are the base run's (see 'missing' for the released path, "
                     "which shares their code)" + (f"; held in the candidate: {held}" if held else ""),
             "released_in_candidate": "base lines", "candidate_basis": basis}
        return c, "yes"
    state = I if releases(census_fam) else H
    since = "; ".join(f"{t} ({by_family['_v'][t]}): " + ", ".join(
        f"{ic} +{n['added']} -{n['removed']} ~{n['changed']}" for ic, n in sorted(by_family["_codes"][(t, code)].items()))
        for t in new_pk)
    changed = " | ".join(x for x in (
        old.get("changed") and f"to V3.0.7: {old['changed']}",
        since and f"V3.0.8 .. V3.0.46 by line diff (lines added + / removed - / changed ~): {since}",
        f"census {CAND}: released {rel or 'none'}") if x)
    open_ = " | ".join(x for x in (
        old.get("open") and old["state"] != BL and f"to V3.0.7: {old['open']}",
        f"held in the candidate {CAND}: {held or 'none'} (never 0, never summed; see candidate_census)") if x)
    c = {"state": state, "method_version": CAND, "packages": pk, "as_of_package": AS_OF, "changed": changed,
         "open": open_, "released_in_candidate": rel if state == I else "none", "candidate_basis": basis}
    return c, "yes"


def census_problems(doc):
    """Every line-attributable family's candidate state against candidate_census and the line-diff packages."""
    bad = []
    cc = doc["candidate_census"]["families"]
    diffed = {p["task"]: set(p.get("families_changed_by_line_diff") or []) for p in doc["candidate_packages"]}
    for f in doc["families"]:
        code, c, k = f["code"], f["candidate"], cc[f["code"]]
        s = c["state"]
        if k["in_candidate"] == C.NOT_LINE_ATTRIBUTABLE:
            if not str(c.get("candidate_basis", "")).startswith("CARRIED"):
                bad.append(f"{code}: owns no item code but its state is not labelled CARRIED")
            continue
        if k["in_candidate"] == "no" and s != NI:
            bad.append(f"{code}: census no, state {s}")
        if k["in_candidate"] == "yes" and s == NI:
            bad.append(f"{code}: census yes, state NOT_IN_CANDIDATE")
        if s == H and releases(k):
            bad.append(f"{code}: HELD_IN_CANDIDATE but the census releases a quantity")
        if s == I and not releases(k):
            bad.append(f"{code}: INTEGRATED_IN_CANDIDATE_AND_TESTED but the census releases nothing")
        touched = [t for t, fs in diffed.items() if code in fs]
        if s == BL and touched:
            bad.append(f"{code}: IN_CANDIDATE_BASE_LINES but changed by {touched}")
        for t in touched:
            if t not in c["packages"]:
                bad.append(f"{code}: changed by {t} (line diff) but its block does not name it")
    return bad


def stale_pending(doc, merged_task_commit):
    """A pending package whose task commit is merged (merged_task_commit(commit) -> bool) is stale: it must have moved
    to candidate_packages. -> [task]"""
    return [p["task"] for p in doc.get("pending_packages") or () if merged_task_commit(p["task_commit"])]


def build(base=BASE, version=VERSION):
    old = json.loads(Path(base).read_text(encoding="utf-8"))
    prom = {p["task"]: p for p in json.loads(PROMOTIONS.read_text(encoding="utf-8"))}
    attrib = json.loads(ATTRIB.read_text(encoding="utf-8"))
    new = copy.deepcopy(old)
    new["version"] = version
    pend = old["pending_packages"]
    missing = [t for t in prom if t not in {p["task"] for p in pend}]
    assert not missing, f"PROMOTIONS_SOURCE names packages the base registry does not hold pending: {missing}"
    promoted = [promote(p, prom[p["task"]], attrib) for p in pend if p["task"] in prom]
    still_pending = [p for p in pend if p["task"] not in prom]   # a package READY after this one (rebase at merge)
    new["supersedes"] = (f"{old['version']} (kept unchanged on disk; every released-configuration field copied unchanged; "
                         f"the {len(promoted)} pending packages promoted to candidate_packages; every family's candidate "
                         f"block re-derived at {CAND})")
    new["source"] = (old["source"] + f" | {version} (T-485, F-T479-1): {old['version']} + the {len(promoted)} merged "
                     "pending packages promoted (merge commit + Checker verdict each) + every family's candidate block "
                     f"re-derived at {CAND} from candidate_census and a line diff of the reproduced chain run "
                     "(research/agents_t485); no quantity, capability or owner change")
    new["v3_0_candidate"] = (
        f"{CAND} (T-419 merge af1eaeb4, Verifier 2026-11-03 09:35 UTC, Gate B PASS; BOQ_LINES 35d70129): the same "
        "opt-in candidate extended in place since ARCH_TAKEOFF_V3.0 (T-131 b1a6d6d): ARCH_TAKEOFF_V2.13 + route G with "
        "the M4 profile + the checker-verified pieces of candidate_packages; every line outside a package's rows "
        "byte-identical to the previous version (asserted by each package). NOT the released default "
        "(ARCH_TAKEOFF_V2.9 + route G stays released; the owner switches it). 'in_v3_0_candidate' = the candidate emits "
        "lines of the family; 'candidate.state' says how; 'v3_0_planned_tasks' = queued or READY lane I packages that "
        "change them next")
    cand = dict(old["candidate"], method_version=CAND, as_of_package=AS_OF)
    cand["scope_of_the_figures"] = (old["candidate"]["scope_of_the_figures"] + f"; from {version} the family blocks state "
                                    "the candidate of record by line census (candidate_census) and line diff")
    new["candidate"] = cand
    new["candidate_packages"] = old["candidate_packages"] + promoted
    new["pending_packages"] = still_pending
    pkg_versions = {p["task"]: _vkey(p["method_version"]) for p in new["candidate_packages"]}

    by_family = {"_v": {}, "_codes": {}, "_record": {}, "_base": old["version"]}
    for p in promoted:
        v = attrib["versions"][p["method_version"]]
        for fam in v["record_families"]:
            by_family["_record"].setdefault(fam, []).append(p["task"])
        by_family["_v"][p["task"]] = p["method_version"].replace("ARCH_TAKEOFF_", "")
        for fam, codes in v["families"].items():
            by_family.setdefault(fam, []).append(p["task"])
            by_family["_codes"][(p["task"], fam)] = codes

    merged = {t for p in new["candidate_packages"] for t in [p["task"], *p["integrates"]]}
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    census = C.census(index, new)            # the registry's own item-code ownership (unchanged from the base)
    if census["candidate_version"] != CAND or census["issue_counts"]:
        raise SystemExit(f"census {census['candidate_version']} issues {census['issue_counts']}")
    cc = {c: census["families"][c] for c in sorted(census["families"])}
    counts = {s: 0 for s in FMC.STATES}
    yes_no = {"yes": 0, "no": 0}
    for f in new["families"]:
        c, yn = family_block(f, cc[f["code"]], by_family, pkg_versions)
        f["candidate"] = c
        f["in_v3_0_candidate"] = yn
        planned = [t for t in f.get("v3_0_planned_tasks") or [] if t not in merged]
        if f["code"] in NO_LINE_FILLED_BY and NO_LINE_FILLED_BY[f["code"]] not in planned:
            planned.append(NO_LINE_FILLED_BY[f["code"]])
        f["v3_0_planned_tasks"] = planned
        if f["code"] in STALE_NOTE:
            f["note"] = f["note"] + (f" | {version} (T-485): the merged packages are promoted and the candidate block "
                                     f"states {CAND} (census + line diff); the 1.41.0 remark 'as of V3.0.7' no longer "
                                     "applies")
        counts[c["state"]] += 1
        yes_no[yn] += 1
    new["candidate_state_counts"] = counts
    new["in_v3_0_candidate_counts"] = yes_no

    old_cen = old["candidate_census"]
    new["candidate_census"] = {
        "method_version": CAND,
        "builder": old_cen["builder"],
        "lines": census["lines"],
        "lines_sha256": index["inputs"]["lines"],
        "verdicts_sha256": index["inputs"].get("verdicts"),
        "downgrades_sha256": index["inputs"].get("downgrades"),
        "index": "research/agents_t485/out/LINE_INDEX_V3_0_46.json (sha256 "
                 + hashlib.sha256(INDEX.read_bytes()).hexdigest() + ")",
        "scope": "the development villa run of the merged candidate of record V3.0.46 (T-419 merge af1eaeb4; BOQ_LINES "
                 "35d70129 reproduced by T-485 from the Drive copies, every V3.0.7 .. V3.0.45 file on the way, V3.0.45 = "
                 "5972888b); the V3.0.44 verdict set and the T-469 downgrade snapshot bind by line content, as in 1.41.0",
        "meaning": old_cen["meaning"].replace("the 'candidate' blocks above stay as of V3.0.7",
                                              "the family 'candidate' blocks are derived from it (1.43.0, T-485)"),
        "families": cc,
        "not_a_boq_lines": census["not_a_boq_lines"],
        "no_family": census["no_family"],
        "issue_counts": census["issue_counts"],
        "stale_in_candidate_vs_registry": C.compare_blocks({"families": cc, "candidate_version": CAND}, new),
        "previous": {"method_version": old_cen["method_version"], "lines": old_cen["lines"],
                     "lines_sha256": old_cen["lines_sha256"]}}
    new["promotion"] = {
        "task": "T-485", "from_registry": old["version"], "promoted": [p["task"] for p in promoted],
        "merge_commits_source": "research/agents_t485/out/PROMOTIONS_SOURCE.json (sha256 "
                                + hashlib.sha256(PROMOTIONS.read_bytes()).hexdigest() + ")",
        "line_diff": "research/agents_t485/out/T485_PACKAGE_FAMILIES.json (sha256 "
                     + hashlib.sha256(ATTRIB.read_bytes()).hexdigest() + ")",
        "rule": "R-T485-1: a merged package never stays in pending_packages; a family's candidate state is derived from "
                "the candidate's lines (census + line diff), never carried from a package's text; a family that owns no "
                "item code is CARRIED and labelled so",
        "quantity_change": "none (no engine, method, line or capability field moves)",
        "line_index": "research/agents_t485/out/LINE_INDEX_V3_0_46.json"}
    return new


def text(doc):
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


def main(argv):
    base, version, out = BASE, VERSION, NEW
    if "--base" in argv:
        base = Path(argv[argv.index("--base") + 1])
    if "--version" in argv:
        version = argv[argv.index("--version") + 1]
    if "--out" in argv:
        out = Path(argv[argv.index("--out") + 1])
    doc = build(base, version)
    probs = FMC.check(doc, root=ROOT, is_ancestor=FMC.git_is_ancestor) + census_problems(doc)
    for b in probs:
        print("PROBLEM", b)
    s = text(doc)
    if "--check" in argv:
        ok = out.read_text(encoding="utf-8") == s
        print(version, "reproduces" if ok else "DIFFERS", f"{len(probs)} problem(s)")
        return 0 if ok and not probs else 1
    out.write_text(s, encoding="utf-8")
    print("written", out.relative_to(ROOT), doc["candidate_state_counts"], doc["in_v3_0_candidate_counts"],
          f"{len(probs)} problem(s)")
    return 1 if probs else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
