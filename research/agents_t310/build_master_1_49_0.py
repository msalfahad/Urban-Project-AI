"""T-310 r4: build rules/coverage/BOQ_FAMILY_MASTER_1.49.0.json = 1.48.0 (never edited)
  (1) + the PROMOTION of the package 1.48.0 holds pending that has since merged (T-483 V3.0.51, merge ea7d375f), by
      the T-485 rule R-T485-1 (a merged package never stays pending): merge commit and Checker verdict from git and the
      board (out/PROMOTIONS_SOURCE_1_49_0.json, t310_promotions_source.py), the families it changed from the LINE DIFF
      V3.0.50 -> V3.0.51 of a reproduced chain run (out/T310_PACKAGE_FAMILIES.json, t310_package_families.py with the
      T-485 diff rules unchanged), and the candidate census re-run at V3.0.51 (out/LINE_INDEX_V3_0_51.json,
      research/agents_t479/t479_registry_census.py unchanged; verdict set board verdicts/V3.0.44, downgrade snapshot
      research/agents_t469, as 1.43.0 .. 1.48.0); the method is research/agents_t483/build_master_1_48_0.py, unchanged
      but for the version span;
  (2) + the pending ARCH_TAKEOFF_V3.0.52 package (T-310, tools/family_master_candidate.py rule r3) and the B8-01 /
      B8-02 / B8-03 / B8-09 text of the families whose lines it changes or adds; B8-09 owns the two pool layer codes
      WP.POOL.MEMBRANE and WP.POOL.PROTECTION_SCREED (ELEMENT_REGISTER: the pool membrane is its own family, never
      inside B8-08 or the concrete line; function HELD S8.2).

The census is taken with the 1.48.0 family codes (the candidate of record V3.0.51 carries no pool layer line); the B8-09
codes are added after it, so the census describes the merged candidate only. No quantity, capability, owner or line
change with this file; the released default is untouched.

    python3 -I research/agents_t310/build_master_1_49_0.py --task-commit <sha> | --check
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
for _p in (ROOT, ROOT / "research" / "agents_t479", ROOT / "research" / "agents_t485"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import t479_registry_census as C  # noqa: E402
import build_master_1_43_0 as B  # noqa: E402  (unit text and release rule of T-485, unchanged)
from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.48.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.49.0.json"
VERSION = "1.49.0"
PROMOTIONS = HERE / "out/PROMOTIONS_SOURCE_1_49_0.json"
ATTRIB = HERE / "out/T310_PACKAGE_FAMILIES.json"
INDEX = HERE / "out/LINE_INDEX_V3_0_51.json"
BOARD_COMMIT = "1b72909b"
OLD_CAND = "ARCH_TAKEOFF_V3.0.50"
CAND, AS_OF = "ARCH_TAKEOFF_V3.0.51", "T-483"
DIFF_SPAN = "V3.0.51"
WHO = "T-310 r4"
I, H, BL, NI = FMC.STATES
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
MOD = "engine/source/arch_v3052.py"
TST = "tests/t310_wet_area_wp/test_arch_v3052.py"
PENDING = {
    "task": "T-310", "method_version": "ARCH_TAKEOFF_V3.0.52", "module": MOD,
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
            "every other V3.0.51 line byte-identical; the Gate B integration package",
}

PROPOSED = ("1.49.0 (T-310): moved by the pending ARCH_TAKEOFF_V3.0.52 package (Gate B); the released capability "
            "of V2.9 + route G is unchanged")

OPT_IN = "ARCH_TAKEOFF_V3.0.52 (engine/source/arch_v3052.py, opt-in candidate; pending Gate B, T-310)"

MISS = {
    "B8-01": ("in the opt-in candidate V3.0.52: pantry floor membrane 13.455 m2 (box 13.500 - column 0.045, "
              "DRAWING-CONFIRMED; flush-column reading +0.045 named); penetrations still HELD"),
    "B8-02": ("in the opt-in candidate V3.0.52: one transition line per physical door (11 keyed, 2 duplicates NOT "
              "APPLICABLE, 3 missing doors HELD BLANK); every transition figure HELD / bounded (detail not printed); "
              "the pantry door's threshold / transition MISSING (binding piece)"),
    "B8-03": ("in the opt-in candidate V3.0.52: 1F east bath upturn 1.580 m2 (run by policy V3; doorway segments HELD "
              "beside); 3 window termination lines NOT APPLICABLE; the pantry open-side termination MISSING"),
    "B8-09": ("in the opt-in candidate V3.0.52: pool membrane 29.582355 m2 and protection screed 1.524503 m3 on the "
              "base and outer wall faces (DRAWING-CONFIRMED); upstand faces HELD (C9), membrane function HELD (S8.2); "
              "no water-side waterproofing is printed"),
}

POOL_CODES = ["WP.POOL.MEMBRANE", "WP.POOL.PROTECTION_SCREED"]


def _at(path, pattern):
    for i, ln in enumerate((ROOT / path).read_text(encoding="utf-8").splitlines(), 1):
        if re.search(pattern, ln):
            return f"{path}:{i}"
    raise SystemExit(f"{path}: no line matches {pattern!r}")


def verdict_text(p):
    return (f"MERGED (Verifier {p['verdict_time']}, Gate B; board {p['board_file']} row {re.sub(r'[a-z]$', '', p['task'])} "
            f"at agents/control {BOARD_COMMIT}: '{p['board_status_head']}')")


def promote(pending, prom, attrib):
    v = attrib["versions"][pending["method_version"]]
    n = pending["method_version"].split(".")[-1]
    return {"task": pending["task"], "method_version": pending["method_version"], "module": pending["module"],
            "merge_commit": prom["merge_commit"], "verdict": verdict_text(prom), "gate": "GATE_B",
            "integrates": list(pending["integrates"]), "tests": list(pending["tests"]),
            "task_commit": pending["task_commit"],
            "changes_families_by_item_code": list(pending["changes_families_by_item_code"]),
            "families_changed_by_line_diff": sorted(v["families"]), "lines_touched": v["touched"],
            "families_record_only_by_line_diff": list(v["record_families"]), "lines_record_only": v["record_only"],
            "development_villa_run": f"{v['lines']} lines, V3_0_{n}_BOQ_LINES.json {v['lines_sha256'][:8]} ({WHO} "
                                     f"chain run, reproduced)",
            "note": pending["note"], "promoted_in": f"{VERSION} ({WHO})"}


def _since(t, ver, codes):
    return f"{t} ({ver}): " + ", ".join(f"{ic} +{n['added']} -{n['removed']} ~{n['changed']}"
                                        for ic, n in sorted(codes.items()))


def touched_block(f, cen, new_pk, pkg_versions):
    old = f["candidate"]
    pk = list(old.get("packages") or [])
    for t, _ver, _codes in new_pk:
        if t not in pk:
            pk.append(t)
    pk.sort(key=lambda t: pkg_versions[t])
    state = I if B.releases(cen) else H
    rel = B._units_text(cen["units"], "released")
    held = B._units_text(cen["units"], "held")
    keep = [x for x in (old.get("changed") or "").split(" | ") if x and not x.startswith("census ")]
    since = "; ".join(_since(t, ver, codes) for t, ver, codes in new_pk)
    changed = " | ".join(keep + [f"{DIFF_SPAN} by line diff ({WHO}): {since}",
                                 f"census {CAND}: released {rel or 'none'}"])
    okeep = [x for x in (old.get("open") or "").split(" | ") if x and not x.startswith("held in the candidate ")]
    open_ = " | ".join(okeep + [f"held in the candidate {CAND}: {held or 'none'} (never 0, never summed; see "
                                f"candidate_census)"])
    return {"state": state, "method_version": CAND, "packages": pk, "as_of_package": AS_OF, "changed": changed,
            "open": open_, "released_in_candidate": rel if state == I else "none",
            "candidate_basis": f"CENSUS {CAND} (candidate_census) + LINE DIFF V3.0.7 .. V3.0.46 (T-485) + "
                               f"V3.0.47 .. V3.0.50 (T-483 r2) + {DIFF_SPAN} ({WHO})"}


def carried_block(f):
    c = dict(f["candidate"], method_version=CAND, as_of_package=AS_OF)
    if str(c.get("candidate_basis", "")).startswith("CENSUS"):
        for k in ("changed", "open", "candidate_basis"):
            c[k] = str(c.get(k) or "").replace(f"census {OLD_CAND}", f"census {CAND}").replace(
                f"held in the candidate {OLD_CAND}", f"held in the candidate {CAND}")
        c["candidate_basis"] = (f"CENSUS {CAND} (candidate_census) + LINE DIFF V3.0.7 .. V3.0.46 (T-485) + V3.0.47 .. "
                                f"V3.0.50 (T-483 r2) + {DIFF_SPAN} ({WHO}: no line of the family changed)")
    return c


def build(task_commit):
    old = json.loads(OLD.read_text(encoding="utf-8"))
    prom = {p["task"]: p for p in json.loads(PROMOTIONS.read_text(encoding="utf-8"))}
    attrib = json.loads(ATTRIB.read_text(encoding="utf-8"))
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    new = copy.deepcopy(old)
    new["version"] = VERSION
    pend = old["pending_packages"]
    if sorted(prom) != sorted(p["task"] for p in pend):
        raise SystemExit(f"promotion source {sorted(prom)} is not every pending package of {old['version']}")
    promoted = [promote(p, prom[p["task"]], attrib) for p in pend]
    new["supersedes"] = (f"{old['version']} (kept unchanged on disk; every released-configuration field copied "
                         f"unchanged; its {len(promoted)} pending packages promoted to candidate_packages; the families "
                         f"they changed re-derived at {CAND}, every other family's candidate block moved to {CAND} "
                         f"with its census asserted unchanged; B8-01 / B8-02 / B8-03 / B8-09 text for the pending V3.0.52 "
                         f"package, B8-09 owning the two pool layer codes)")
    new["source"] = (old["source"] + f" | {VERSION} ({WHO}): {old['version']} + the {len(promoted)} merged pending "
                     f"package(s) promoted (R-T485-1, merge commit + Checker verdict each; census + line diff at {CAND}) "
                     "+ pending ARCH_TAKEOFF_V3.0.52 (rule r3) + the waterproofing families it changes; B8-09 owns the "
                     "two pool layer codes; no quantity, capability or owner change")
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
            f["candidate"] = touched_block(f, cc[code], by_family[code], pkg_versions)
        else:
            if cc[code] != oc[code]:
                raise SystemExit(f"{code}: no line changed V3.0.50 -> V3.0.51 but its census moved")
            f["candidate"] = carried_block(f)
        counts[f["candidate"]["state"]] += 1
        yes_no[f["in_v3_0_candidate"]] += 1
    new["candidate_state_counts"] = counts
    new["in_v3_0_candidate_counts"] = yes_no

    old_cen = old["candidate_census"]
    new["candidate_census"] = dict(
        old_cen, method_version=CAND, lines=census["lines"], lines_sha256=index["inputs"]["lines"],
        verdicts_sha256=index["inputs"].get("verdicts"), downgrades_sha256=index["inputs"].get("downgrades"),
        index="research/agents_t310/out/LINE_INDEX_V3_0_51.json (sha256 " + hashlib.sha256(INDEX.read_bytes()).hexdigest()
              + ")",
        scope=(f"the development villa run of the merged candidate of record V3.0.51 (T-483 merge "
               f"{prom[AS_OF]['merge_commit'][:8]}; BOQ_LINES {vc['lines_sha256'][:8]} reproduced by {WHO} from "
               "the Drive copies, V3.0.48 = 33a81c53 and V3.0.50 = d40c4ec5 on the way); the "
               "V3.0.44 verdict set and the T-469 downgrade snapshot bind by line content, as in 1.43.0"),
        families=cc, not_a_boq_lines=census["not_a_boq_lines"], no_family=census["no_family"],
        issue_counts=census["issue_counts"],
        stale_in_candidate_vs_registry=C.compare_blocks({"families": cc, "candidate_version": CAND}, new),
        previous={"method_version": old_cen["method_version"], "lines": old_cen["lines"],
                  "lines_sha256": old_cen["lines_sha256"]})
    new["promotion"] = {
        "task": "T-310", "round": "r4", "from_registry": old["version"], "promoted": [p["task"] for p in promoted],
        "previous_promotion": {"task": old["promotion"]["task"], "from_registry": old["promotion"]["from_registry"],
                               "promoted": old["promotion"]["promoted"]},
        "merge_commits_source": "research/agents_t310/out/PROMOTIONS_SOURCE_1_49_0.json (sha256 "
                                + hashlib.sha256(PROMOTIONS.read_bytes()).hexdigest() + ")",
        "line_diff": "research/agents_t310/out/T310_PACKAGE_FAMILIES.json (sha256 "
                     + hashlib.sha256(ATTRIB.read_bytes()).hexdigest() + ")",
        "rule": old["promotion"]["rule"],
        "quantity_change": "none (no engine, method, line or capability field moves)",
        "line_index": "research/agents_t310/out/LINE_INDEX_V3_0_51.json"}

    # (2) the pending V3.0.52 package's families (after the census: it describes the merged candidate only)
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
    f["note"] = str(f["note"]) + (" | 1.49.0 (T-310): owns WP.POOL.MEMBRANE (m2) and WP.POOL.PROTECTION_SCREED (m3), "
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
        doc = build(tc)
        ok = NEW.read_text(encoding="utf-8") == text(doc)
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
