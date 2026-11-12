"""T-717: build rules/coverage/BOQ_FAMILY_MASTER_1.75.0.json = 1.74.0 (T-722, merged and promoted; never edited)
  + the ARCH_TAKEOFF_V3.0.74 package (T-717, FINISH_GATE_B_V2; tools/family_master_candidate.py rule r3) and the
    B4-03 / B4-06 text of the families whose lines it restates or adds.

Two modes, ONE version number (the ADOPTED lesson: a merged integration package leaves the registry promoted in the
same merge, F-C-T563-1 / T-651 / ... / T-703 / T-722); the builder is research/agents_t722/build_master_1_74_0.py
with its constants pointed at this package (functions unchanged):

  --task-commit <sha> [--write]  PENDING: V3.0.74 pending (the task branch, before Gate B), candidate of record V3.0.73.
  --promote [--write]            PROMOTED (run by the Verifier IN the merge, after t717_promotions_source.py has written
                                 out/PROMOTIONS_SOURCE_1_75_0.json): families re-derived at V3.0.74 from
                                 out/T717_PACKAGE_FAMILIES.json and the census out/LINE_INDEX_V3_0_74.json.
  --check                        the committed file equals the builder in the mode it was written in; 0 problems.

No quantity, capability, owner or line change with this file; the released default is untouched.
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

import build_master_1_43_0 as B  # noqa: E402  (census problems / unit text of T-485, unchanged)
from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.74.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.75.0.json"
VERSION = "1.75.0"
MOD = "engine/source/arch_v3074.py"
TST = "tests/t717_finish_gate_b2/test_arch_v3074.py"
PROMOTIONS = HERE / "out/PROMOTIONS_SOURCE_1_75_0.json"
ATTRIB = HERE / "out/T717_PACKAGE_FAMILIES.json"
INDEX = HERE / "out/LINE_INDEX_V3_0_74.json"
OLD_CAND, CAND, AS_OF = "ARCH_TAKEOFF_V3.0.73", "ARCH_TAKEOFF_V3.0.74", "T-717"
DIFF_SPAN = "V3.0.73 .. V3.0.74"
WHO = "T-717"
FAMS = ("B4-03", "B4-06")
NEW_CODES = {}
PENDING = {
    "task": "T-717", "method_version": CAND, "module": MOD, "status": FMC.PENDING_STATUS,
    "integrates": ["T-701", "T-702", "T-709", "T-719", "T-723"], "tests": ["tests/t717_finish_gate_b2"],
    "changes_families_by_item_code": ["FIN.PAINT", "FIN.PLASTER"],
    "note": "T-717 (research/agents_t717/T-717_FINISH_GATE_B2.md): FINISH_GATE_B_V2 from the merged T-701 / T-702 / "
            "T-709 ledgers as mapped by T-723 (hub T-717, 36 rows): 4 HELD plaster lines restated (annex GF-01 / GF-04 "
            "to the R-T701-2 datum bound, GF-01 with F-T709-1; GF-07 / GF-14 wet bands per T-702 (c)); 30 FIN.PAINT "
            "return lines added HELD (27 bounded 0 .. face, 3 blank, R-T709-4); 2 stairwell band lines added HELD "
            "(plaster 0.839412 .. 0.870912, paint 3.344721 .. 3.525121 m2, R-T709-1, void V-01 T-719); no released "
            "quantity moves; every other line byte-identical; the Gate B integration package",
}
PROPOSED = ("1.75.0 (T-717): restated by the ARCH_TAKEOFF_V3.0.74 package (Gate B): annex plaster widened to the datum "
            "bound, GF wet bands restated, return paint and stairwell bands added HELD; the released capability of "
            "V2.9 + route G is unchanged")
OPT_IN = "ARCH_TAKEOFF_V3.0.74 (engine/source/arch_v3074.py, opt-in candidate; Gate B package T-717)"
MISS = {
    "B4-03": ("in the opt-in candidate V3.0.74: annex GF-01 / GF-04 plaster widened to the R-T701-2 datum bound "
              "(47.949844 .. 66.249856 with F-T709-1 W12, 34.33 .. 43.78 m2), GF-07 / GF-14 wet bands restated on "
              "beam B27 / B11 and the sunken panels (D-41), the ST-02 stairwell plaster band +5.29 .. +5.50 added "
              "HELD 0.839412 .. 0.870912 m2; the beam faces under the 1F well walls HELD by name"),
    "B4-06": ("in the opt-in candidate V3.0.74: 30 return-paint lines HELD (27 at 0 .. the face's plaster m2, sum 0 .. "
              "24.15; 3 blank; 5 NOT_ESTABLISHED between wet rooms), the ST-02 stairwell paint band +4.65 .. +5.50 HELD "
              "3.344721 .. 3.525121 m2; GF-01 paint 0.010824 m2 high (F-T709-1) waits for its own restatement"),
}


def _at(path, pattern):
    for i, ln in enumerate((ROOT / path).read_text(encoding="utf-8").splitlines(), 1):
        if re.search(pattern, ln):
            return f"{path}:{i}"
    raise SystemExit(f"{path}: no line matches {pattern!r}")


def build_pending(task_commit):
    old = json.loads(OLD.read_text(encoding="utf-8"))
    if old["pending_packages"]:
        raise SystemExit(f"{old['version']} pending packages {[p['task'] for p in old['pending_packages']]}: expected "
                         "none (renumber on the newer registry, merge-order rule)")
    if old["candidate"]["method_version"] != OLD_CAND:
        raise SystemExit(f"{old['version']}: candidate of record {old['candidate']['method_version']}, expected "
                         f"{OLD_CAND} (V3.0.74 extends it)")
    new = copy.deepcopy(old)
    new["version"] = VERSION
    new["supersedes"] = (f"{old['version']} (kept unchanged on disk; every released-configuration field, every T-637 "
                         f"field, the candidate of record {OLD_CAND}, its census and every family's candidate block "
                         "copied unchanged; B4-03 / B4-06 text for the V3.0.74 package)")
    new["source"] = (old["source"] + f" | {VERSION} (T-717): {old['version']} + ARCH_TAKEOFF_V3.0.74 (rule r3; "
                     "promoted in the merge by --promote) + the family it names; no quantity, "
                     "capability or owner change")
    new["pending_packages"] = [dict(PENDING, task_commit=task_commit)]
    fams = {f["code"]: f for f in new["families"]}
    ev = (f"{_at(MOD, r'^def _restate_entry')} _restate_entry() / {_at(MOD, '^def _restate[(]')} _restate(): held plaster "
          f"lines restated to merged bounds; {_at(MOD, r'^def _return_line')} _return_line(); "
          f"{_at(MOD, r'^def band_figure')} band_figure(); {_at(MOD, r'^def check_finishes')} check_finishes(); "
          f"{_at(TST, r'^def test_totals_by_hand')} (villa F717 by hand)")
    for code in FAMS:
        f = fams[code]
        for c in NEW_CODES.get(code, ()):
            if c in f["item_codes"]:
                raise SystemExit(f"{code}: {c} already owned")
            f["item_codes"] = sorted(list(f["item_codes"]) + [c])
        f["evidence"] = list(f["evidence"]) + [ev]
        f["opt_in_readers"] = (OPT_IN if str(f.get("opt_in_readers") or "none") == "none" else
                               str(f.get("opt_in_readers")) + " | " + OPT_IN)
        f["missing"] = str(f.get("missing") or "") + " | " + MISS[code]
        f["note"] = str(f.get("note") or "") + " | " + PROPOSED
    return new


def build_promoted(task_commit):
    """the T-655 promotion (T-483 r2 functions unchanged, module constants pointed at this promotion and restored)"""
    import build_master_1_48_0 as P48  # noqa: E402
    board = {p.get("board_commit") for p in json.loads(PROMOTIONS.read_text(encoding="utf-8"))}
    if len(board) != 1 or not re.fullmatch(r"[0-9a-f]{8}", str(next(iter(board)))):
        raise SystemExit(f"{PROMOTIONS.name}: one agents/control board commit (8 hex) expected, got {board}")
    consts = (("VERSION", VERSION), ("BOARD_COMMIT", next(iter(board))), ("OLD_CAND", OLD_CAND), ("CAND", CAND),
              ("AS_OF", AS_OF), ("DIFF_SPAN", DIFF_SPAN))
    saved = {k: getattr(P48, k, None) for k, _v in consts}
    try:
        for k, v in consts:
            setattr(P48, k, v)
        return _promote(build_pending(task_commit), P48)
    finally:
        for k, v in saved.items():
            setattr(P48, k, v)


def _promote(old, P48):
    import t479_registry_census as C  # noqa: E402
    prom = {p["task"]: p for p in json.loads(PROMOTIONS.read_text(encoding="utf-8"))}
    pend = old["pending_packages"]
    if sorted(prom) != [WHO] or [p["task"] for p in pend] != [WHO]:
        raise SystemExit(f"promotion source {sorted(prom)} / pending {[p['task'] for p in pend]}: expected [{WHO}]")
    attrib = json.loads(ATTRIB.read_text(encoding="utf-8"))
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    new = copy.deepcopy(old)
    promoted = [dict(P48.promote(p, prom[p["task"]], attrib), promoted_in=f"{VERSION} ({WHO}, in the merge)")
                for p in pend]
    for p in promoted:
        p["development_villa_run"] = p["development_villa_run"].replace("T-483 r2 chain run", f"{WHO} chain run")
    new["supersedes"] = old["supersedes"].replace("for the V3.0.74 package)", "for the V3.0.74 package; the package "
                                                  "promoted in its own merge and every family's candidate block moved "
                                                  f"to {CAND})")
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
        index="research/agents_t717/out/LINE_INDEX_V3_0_74.json (sha256 " + hashlib.sha256(INDEX.read_bytes()).hexdigest()
              + ")",
        scope=(f"the development villa run of the candidate V3.0.74 (T-717 merge {prom[AS_OF]['merge_commit'][:8]}; "
               f"BOQ_LINES {vc['lines_sha256'][:8]} from the Drive copies, V3.0.73 = "
               f"{attrib['versions'][OLD_CAND]['lines_sha256'][:8]} on the way); the V3.0.44 verdict set and the T-469 "
               "downgrade snapshot bind by line content, as in 1.43.0"),
        families=cc, not_a_boq_lines=census["not_a_boq_lines"], no_family=census["no_family"],
        issue_counts=census["issue_counts"],
        stale_in_candidate_vs_registry=C.compare_blocks({"families": cc, "candidate_version": CAND}, new),
        previous={"method_version": old_cen["method_version"], "lines": old_cen["lines"],
                  "lines_sha256": old_cen["lines_sha256"]})
    new["promotion"] = {
        "task": WHO, "round": "r1 (in the merge)", "from_registry": "1.74.0", "promoted": [p["task"] for p in promoted],
        "previous_promotion": {"task": old["promotion"]["task"], "from_registry": old["promotion"]["from_registry"],
                               "promoted": old["promotion"]["promoted"]},
        "merge_commits_source": "research/agents_t717/out/PROMOTIONS_SOURCE_1_75_0.json (sha256 "
                                + hashlib.sha256(PROMOTIONS.read_bytes()).hexdigest() + ")",
        "line_diff": "research/agents_t717/out/T717_PACKAGE_FAMILIES.json (sha256 "
                     + hashlib.sha256(ATTRIB.read_bytes()).hexdigest() + ")",
        "rule": old["promotion"]["rule"],
        "quantity_change": "none (no engine, method, line or capability field moves with this file)",
        "line_index": "research/agents_t717/out/LINE_INDEX_V3_0_74.json"}
    return new


def text(doc):
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"


def problems(doc):
    return FMC.check(doc, root=ROOT, is_ancestor=FMC.git_is_ancestor) + B.census_problems(doc)


def _task_commit(cur):
    for p in list(cur.get("pending_packages") or ()) + list(cur.get("candidate_packages") or ()):
        if p["task"] == WHO:
            return p["task_commit"]
    raise SystemExit(f"{NEW.name} holds no {WHO} package")


def main(argv):
    if "--check" in argv:
        cur = json.loads(NEW.read_text(encoding="utf-8"))
        tc = _task_commit(cur)
        doc = build_promoted(tc) if not cur["pending_packages"] else build_pending(tc)
        ok = NEW.read_text(encoding="utf-8") == text(doc)
        bad = problems(cur)
        print(f"{VERSION} equals its builder ({'promoted' if not cur['pending_packages'] else 'pending'}):", ok,
              "| problems:", bad)
        return 0 if ok and not bad else 1
    if "--promote" in argv:
        doc = build_promoted(_task_commit(json.loads(NEW.read_text(encoding="utf-8"))))
    elif "--task-commit" in argv:
        doc = build_pending(argv[argv.index("--task-commit") + 1])
    else:
        print("--task-commit <sha> | --promote | --check is required")
        return 2
    bad = problems(doc)
    for b in bad:
        print("PROBLEM", b)
    if "--write" in argv:
        NEW.write_text(text(doc), encoding="utf-8")
        print("written", NEW.relative_to(ROOT), f"({len(bad)} problem(s))")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
