"""T-483 r2: build rules/coverage/BOQ_FAMILY_MASTER_1.46.0.json = 1.45.0 (never edited)
  (1) + the PROMOTION of the two packages 1.45.0 holds pending that have since merged (T-443 V3.0.47, merge c814c55d;
      T-350b V3.0.48, merge 5de697ff), by the T-485 rule R-T485-1 (a merged package never stays pending): merge commit
      and Checker verdict from git and the board (out/PROMOTIONS_SOURCE_1_46_0.json, t483_promotions_source.py), the
      families each package changed from the LINE DIFF V3.0.46 -> V3.0.47 -> V3.0.48 of a reproduced chain run
      (out/T483_PACKAGE_FAMILIES.json, research/agents_t485/t485_package_families.py unchanged), and the candidate
      census re-run at V3.0.48 (out/LINE_INDEX_V3_0_48.json, research/agents_t479/t479_registry_census.py unchanged;
      verdict set board verdicts/V3.0.44, downgrade snapshot research/agents_t469, as 1.43.0 .. 1.45.0);
  (2) + the pending ARCH_TAKEOFF_V3.0.49 package (T-483, tools/family_master_candidate.py rule r3) and the B3-06 text
      of the family whose lines it changes.

Family blocks: a family the line diff names is re-derived (package added, state INTEGRATED_IN_CANDIDATE_AND_TESTED when
the V3.0.48 census releases a quantity of it, else HELD_IN_CANDIDATE; released / held text from the census); every
other family must have a census identical to 1.45.0's (asserted: its lines are byte-identical V3.0.46 -> V3.0.48), so
only its candidate method version / as-of package move to V3.0.48 / T-350b. No quantity, capability, owner or line
change with this file; the released default is untouched.

    python3 -I research/agents_t483/build_master_1_46_0.py --task-commit <sha> | --check
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

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.45.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.46.0.json"
VERSION = "1.46.0"
PROMOTIONS = HERE / "out/PROMOTIONS_SOURCE_1_46_0.json"
ATTRIB = HERE / "out/T483_PACKAGE_FAMILIES.json"
INDEX = HERE / "out/LINE_INDEX_V3_0_48.json"
BOARD_COMMIT = "f371bc6e"
OLD_CAND = "ARCH_TAKEOFF_V3.0.46"
CAND, AS_OF = "ARCH_TAKEOFF_V3.0.48", "T-350b"
I, H, BL, NI = FMC.STATES
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
MOD = "engine/source/arch_v3049.py"
TST = "tests/t483_skirting_remainder/test_arch_v3049.py"
PENDING = {
    "task": "T-483", "method_version": "ARCH_TAKEOFF_V3.0.49", "module": MOD,
    "status": FMC.PENDING_STATUS, "integrates": ["T-481", "T-410", "T-422"],
    "tests": ["tests/t483_skirting_remainder"],
    "changes_families_by_item_code": ["FIN.SKIRTING"],
    "note": "T-483 r2 (research/agents_t483/T-483_SKIRTING_REMAINDER_INTEGRATION.md): the Checker-verified T-481 census "
            "integrated on the merged V3.0.48: GF-01 W11 / W12 sills 0.70 above the +0.30 floor (section B-B) -> "
            "skirting under them, room line 14.218 -> 18.128 lm, its range line NOT_APPLICABLE (carried once); W02 and "
            "W17 floor glazing: their held ranges closed NOT_APPLICABLE; the 1F dressing walked by handle 5.100 lm (was "
            "HELD BLANK); the 1F shaft faces 9.050 lm and the W13 / W25 range 2.200 lm stay HELD in FIN.SKIRTING until "
            "T-501 gives them a B7-07 / B7-08 home; every other V3.0.48 line byte-identical; the Gate B integration "
            "package",
}
PROPOSED = ("1.46.0 (T-483 r2): moved by the pending ARCH_TAKEOFF_V3.0.49 package (Gate B); the released capability "
            "of V2.9 + route G is unchanged")
OPT_IN = "ARCH_TAKEOFF_V3.0.49 (engine/source/arch_v3049.py, opt-in candidate; pending Gate B, T-483 r2)"
MISS = ("in the opt-in candidate V3.0.49: W11 / W12 skirted, W02 / W17 floor glazing (ranges closed); the 1F dressing "
        "valued 5.100 lm; still open: R-T481-3 on the 1F shaft (9.050 lm inside the 1F living net, W13 / W25 range "
        "0 .. 2.200 held) until B7-07 / B7-08 have candidate lines (T-501), the W02 pier D-53")


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
            "development_villa_run": f"{v['lines']} lines, V3_0_{n}_BOQ_LINES.json {v['lines_sha256'][:8]} (T-483 r2 "
                                     f"chain run, reproduced)",
            "note": pending["note"], "promoted_in": f"{VERSION} (T-483 r2)"}


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
    changed = " | ".join(keep + [f"V3.0.47 .. V3.0.48 by line diff (T-483 r2): {since}",
                                 f"census {CAND}: released {rel or 'none'}"])
    okeep = [x for x in (old.get("open") or "").split(" | ") if x and not x.startswith("held in the candidate ")]
    open_ = " | ".join(okeep + [f"held in the candidate {CAND}: {held or 'none'} (never 0, never summed; see "
                                f"candidate_census)"])
    return {"state": state, "method_version": CAND, "packages": pk, "as_of_package": AS_OF, "changed": changed,
            "open": open_, "released_in_candidate": rel if state == I else "none",
            "candidate_basis": f"CENSUS {CAND} (candidate_census) + LINE DIFF V3.0.7 .. V3.0.46 (T-485) + V3.0.47 .. "
                               f"V3.0.48 (T-483 r2)"}


def carried_block(f):
    c = dict(f["candidate"], method_version=CAND, as_of_package=AS_OF)
    if str(c.get("candidate_basis", "")).startswith("CENSUS"):
        for k in ("changed", "open", "candidate_basis"):
            c[k] = str(c.get(k) or "").replace(f"census {OLD_CAND}", f"census {CAND}").replace(
                f"held in the candidate {OLD_CAND}", f"held in the candidate {CAND}")
        c["candidate_basis"] = (f"CENSUS {CAND} (candidate_census) + LINE DIFF V3.0.7 .. V3.0.46 (T-485) + V3.0.47 .. "
                                f"V3.0.48 (T-483 r2: no line of the family changed)")
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
        raise SystemExit(f"promotion source {sorted(prom)} is not every pending package of 1.45.0")
    promoted = [promote(p, prom[p["task"]], attrib) for p in pend]
    new["supersedes"] = (f"{old['version']} (kept unchanged on disk; every released-configuration field copied "
                         f"unchanged; its {len(promoted)} pending packages promoted to candidate_packages; the families "
                         f"they changed re-derived at {CAND}, every other family's candidate block moved to {CAND} "
                         f"with its census asserted unchanged; B3-06 text for the pending V3.0.49 package)")
    new["source"] = (old["source"] + f" | {VERSION} (T-483 r2): {old['version']} + the {len(promoted)} merged pending "
                     f"packages promoted (R-T485-1, merge commit + Checker verdict each; census + line diff at {CAND}) "
                     "+ pending ARCH_TAKEOFF_V3.0.49 (rule r3) + the family whose lines it changes; no quantity, "
                     "capability or owner change")
    head = new["v3_0_candidate"].split(": the same opt-in candidate", 1)
    if len(head) != 2:
        raise SystemExit("v3_0_candidate text has no head to restate")
    v48 = attrib["versions"][CAND]
    new["v3_0_candidate"] = (f"{CAND} (T-350b merge {prom['T-350b']['merge_commit'][:8]}, Verifier "
                             f"{prom['T-350b']['verdict_time']}, Gate B PASS; BOQ_LINES {v48['lines_sha256'][:8]}): "
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
                raise SystemExit(f"{code}: no line changed V3.0.46 -> V3.0.48 but its census moved")
            f["candidate"] = carried_block(f)
        counts[f["candidate"]["state"]] += 1
        yes_no[f["in_v3_0_candidate"]] += 1
    new["candidate_state_counts"] = counts
    new["in_v3_0_candidate_counts"] = yes_no

    fams = {f["code"]: f for f in new["families"]}
    f = fams["B3-06"]
    f["evidence"] = list(f["evidence"]) + [
        f"{_at(MOD, r'^def changes_for')} changes_for(): RELEASE of a window base under a sill established above the "
        f"floor (range line counted in the room line), CLOSE_RANGE of a held range whose windows are floor glazing or "
        f"stair-owned, WALK of a blocked dry-cell line by handle (openings by id); {_at(MOD, r'^def load_inputs')} "
        f"load_inputs() (sill in m, cover, closure); {_at(MOD, r'^def check_remainder')} check_remainder(); "
        f"{_at(TST, r'^def test_release_rises_by_the_window_edges_and_closes')} (villa K483 by hand)"]
    f["opt_in_readers"] = str(f.get("opt_in_readers") or "") + " | " + OPT_IN
    f["missing"] = str(f.get("missing") or "") + " | " + MISS
    f["note"] = str(f.get("note") or "") + " | " + PROPOSED

    old_cen = old["candidate_census"]
    new["candidate_census"] = dict(
        old_cen, method_version=CAND, lines=census["lines"], lines_sha256=index["inputs"]["lines"],
        verdicts_sha256=index["inputs"].get("verdicts"), downgrades_sha256=index["inputs"].get("downgrades"),
        index="research/agents_t483/out/LINE_INDEX_V3_0_48.json (sha256 " + hashlib.sha256(INDEX.read_bytes()).hexdigest()
              + ")",
        scope=(f"the development villa run of the merged candidate of record V3.0.48 (T-350b merge "
               f"{prom['T-350b']['merge_commit'][:8]}; BOQ_LINES {v48['lines_sha256'][:8]} reproduced by T-483 r2 from "
               "the Drive copies, V3.0.46 = 35d70129 and V3.0.47 = e86a53a8 on the way); the V3.0.44 verdict set and "
               "the T-469 downgrade snapshot bind by line content, as in 1.43.0"),
        families=cc, not_a_boq_lines=census["not_a_boq_lines"], no_family=census["no_family"],
        issue_counts=census["issue_counts"],
        stale_in_candidate_vs_registry=C.compare_blocks({"families": cc, "candidate_version": CAND}, new),
        previous={"method_version": old_cen["method_version"], "lines": old_cen["lines"],
                  "lines_sha256": old_cen["lines_sha256"]})
    new["promotion"] = {
        "task": "T-483", "round": "r2", "from_registry": old["version"], "promoted": [p["task"] for p in promoted],
        "previous_promotion": {"task": old["promotion"]["task"], "from_registry": old["promotion"]["from_registry"],
                               "promoted": old["promotion"]["promoted"]},
        "merge_commits_source": "research/agents_t483/out/PROMOTIONS_SOURCE_1_46_0.json (sha256 "
                                + hashlib.sha256(PROMOTIONS.read_bytes()).hexdigest() + ")",
        "line_diff": "research/agents_t483/out/T483_PACKAGE_FAMILIES.json (sha256 "
                     + hashlib.sha256(ATTRIB.read_bytes()).hexdigest() + ")",
        "rule": old["promotion"]["rule"],
        "quantity_change": "none (no engine, method, line or capability field moves)",
        "line_index": "research/agents_t483/out/LINE_INDEX_V3_0_48.json"}
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
