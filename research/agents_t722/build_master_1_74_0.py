"""T-722: build rules/coverage/BOQ_FAMILY_MASTER_1.74.0.json = 1.73.0 (T-703, merged and promoted; never edited)
  + the ARCH_TAKEOFF_V3.0.73 package (T-722, CONCRETE_GATE_B_V9; tools/family_master_candidate.py rule r3) and the
    B10-04 / B10-06 / B10-07 / B10-10 / B10-12 / B7-12 text of the families whose lines it restates.

Two modes, ONE version number (the ADOPTED lesson: a merged integration package leaves the registry promoted in the
same merge, F-C-T563-1 / T-651 / ... / T-693 / T-704 / T-703); the builder is research/agents_t703/build_master_1_73_0.py
with its constants pointed at this package (functions unchanged):

  --task-commit <sha> [--write]  PENDING: V3.0.73 pending (the task branch, before Gate B), candidate of record V3.0.72.
  --promote [--write]            PROMOTED (run by the Verifier IN the merge, after t722_promotions_source.py has written
                                 out/PROMOTIONS_SOURCE_1_74_0.json): families re-derived at V3.0.73 from
                                 out/T722_PACKAGE_FAMILIES.json and the census out/LINE_INDEX_V3_0_73.json.
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

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.73.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.74.0.json"
VERSION = "1.74.0"
MOD = "engine/source/arch_v3073.py"
TST = "tests/t722_concrete_side/test_arch_v3073.py"
PROMOTIONS = HERE / "out/PROMOTIONS_SOURCE_1_74_0.json"
ATTRIB = HERE / "out/T722_PACKAGE_FAMILIES.json"
INDEX = HERE / "out/LINE_INDEX_V3_0_73.json"
OLD_CAND, CAND, AS_OF = "ARCH_TAKEOFF_V3.0.72", "ARCH_TAKEOFF_V3.0.73", "T-722"
DIFF_SPAN = "V3.0.72 .. V3.0.73"
WHO = "T-722"
FAMS = ("B10-04", "B10-06", "B10-07", "B10-10", "B10-12", "B7-12")
NEW_CODES = {}
PENDING = {
    "task": "T-722", "method_version": CAND, "module": MOD, "status": FMC.PENDING_STATUS,
    "integrates": ["T-707", "T-711", "T-712", "T-721", "T-723"], "tests": ["tests/t722_concrete_side"],
    "changes_families_by_item_code": ["STR.CONC.BEAM", "STR.CONC.COLUMN", "STR.CONC.GROUND_BEAM", "STR.CONC.LIFT",
                                      "STR.CONC.PARAPET", "STR.CONC.STAIR"],
    "note": "T-722 (research/agents_t722/T-722_CONCRETE_GATE_B9.md): CONCRETE_GATE_B_V9 from the merged T-707 / T-711 / "
            "T-712 / T-721 ledgers as mapped by T-723: 5 held column lows raised by the one-plane 2F roof slab top "
            "(COLUMN held low 11.67283 -> 11.80007 m3, high unchanged); 13 HELD blank lines carry an AT_LEAST beside "
            "(2 tank columns, lift pit walls, 4 parapets, 1 stair, 4 ground beams of which 3 restate their V3.0.63 "
            "figure, the east dome ring); 18 blank lines name their holding item; 18 figures already beside "
            "confirmed; no released quantity moves; every other line byte-identical; the Gate B integration package",
}
PROPOSED = ("1.74.0 (T-722): restated by the ARCH_TAKEOFF_V3.0.73 package (Gate B): held column lows raised by a "
            "one-plane slab-top transfer, lower-end figures beside HELD blank concrete lines, holding items named; the "
            "released capability of V2.9 + route G is unchanged")
OPT_IN = "ARCH_TAKEOFF_V3.0.73 (engine/source/arch_v3073.py, opt-in candidate; Gate B package T-722)"
MISS = {
    "B10-04": ("in the opt-in candidate V3.0.73: 17 HELD blank ground beams carry AT_LEAST beside (family 5.099845 "
               "m3, never summed; 3 restated from V3.0.63 by the T-712 re-measure), 3 court stretches named (D-35); "
               "the boundary G.B at N.G. line keeps its 0 .. 3.5256 record while blank (no ledger restates it)"),
    "B10-06": ("in the opt-in candidate V3.0.73: 5 held 2F column lows raised by the one-plane 2F roof slab top "
               "(R-T707-1, +0.12724 m3 on the held low), the 2F tank columns C2 / C3 blank with AT_LEAST 0.3287 each "
               "beside (D-44 high open)"),
    "B10-07": ("in the opt-in candidate V3.0.73: the east dome-opening ring AT_LEAST 0.115155 m3 beside (D-28), 11 edge "
               "projections blank with D-05 / D-26 named"),
    "B10-10": ("in the opt-in candidate V3.0.73: lift pit walls AT_LEAST 1.903 m3 beside (D-43 pit depth), the GF lift "
               "tie beam blank with D-43 named"),
    "B10-12": ("in the opt-in candidate V3.0.73: the 4 RC parapet lines carry AT_LEAST beside (1.799103 / 1.677886 / "
               "2.949453 / 1.6245 m3, Q-65 C + D-39 b_edge)"),
    "B7-12": ("in the opt-in candidate V3.0.73: ST-01 GF -> 1F remainder AT_LEAST 1.213429 m3 beside (C-ST-4 / D-67), "
              "3 stair parts named (C-ST-3, S-9, D-08)"),
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
                         f"{OLD_CAND} (V3.0.73 extends it)")
    new = copy.deepcopy(old)
    new["version"] = VERSION
    new["supersedes"] = (f"{old['version']} (kept unchanged on disk; every released-configuration field, every T-637 "
                         f"field, the candidate of record {OLD_CAND}, its census and every family's candidate block "
                         "copied unchanged; B10 / B7-12 text for the V3.0.73 package)")
    new["source"] = (old["source"] + f" | {VERSION} (T-722): {old['version']} + ARCH_TAKEOFF_V3.0.73 (rule r3; "
                     "promoted in the merge by --promote) + the family it names; no quantity, "
                     "capability or owner change")
    new["pending_packages"] = [dict(PENDING, task_commit=task_commit)]
    fams = {f["code"]: f for f in new["families"]}
    ev = (f"{_at(MOD, r'^def _entry')} _entry() / {_at(MOD, r'^def _restate')} _restate(): column lows raised, "
          f"lower-end figures beside held blank concrete lines, holding items named, from the merged ledgers; "
          f"{_at(MOD, r'^def narrow_low')} narrow_low(); {_at(MOD, r'^def figures_beside')} figures_beside(); "
          f"{_at(MOD, r'^def check_concrete')} check_concrete(); {_at(TST, r'^def test_normal_hand_figures')} "
          f"(villa C722 by hand)")
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
    new["supersedes"] = old["supersedes"].replace("for the V3.0.73 package)", "for the V3.0.73 package; the package "
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
        index="research/agents_t722/out/LINE_INDEX_V3_0_73.json (sha256 " + hashlib.sha256(INDEX.read_bytes()).hexdigest()
              + ")",
        scope=(f"the development villa run of the candidate V3.0.73 (T-722 merge {prom[AS_OF]['merge_commit'][:8]}; "
               f"BOQ_LINES {vc['lines_sha256'][:8]} from the Drive copies, V3.0.72 = "
               f"{attrib['versions'][OLD_CAND]['lines_sha256'][:8]} on the way); the V3.0.44 verdict set and the T-469 "
               "downgrade snapshot bind by line content, as in 1.43.0"),
        families=cc, not_a_boq_lines=census["not_a_boq_lines"], no_family=census["no_family"],
        issue_counts=census["issue_counts"],
        stale_in_candidate_vs_registry=C.compare_blocks({"families": cc, "candidate_version": CAND}, new),
        previous={"method_version": old_cen["method_version"], "lines": old_cen["lines"],
                  "lines_sha256": old_cen["lines_sha256"]})
    new["promotion"] = {
        "task": WHO, "round": "r1 (in the merge)", "from_registry": "1.73.0", "promoted": [p["task"] for p in promoted],
        "previous_promotion": {"task": old["promotion"]["task"], "from_registry": old["promotion"]["from_registry"],
                               "promoted": old["promotion"]["promoted"]},
        "merge_commits_source": "research/agents_t722/out/PROMOTIONS_SOURCE_1_74_0.json (sha256 "
                                + hashlib.sha256(PROMOTIONS.read_bytes()).hexdigest() + ")",
        "line_diff": "research/agents_t722/out/T722_PACKAGE_FAMILIES.json (sha256 "
                     + hashlib.sha256(ATTRIB.read_bytes()).hexdigest() + ")",
        "rule": old["promotion"]["rule"],
        "quantity_change": "none (no engine, method, line or capability field moves with this file)",
        "line_index": "research/agents_t722/out/LINE_INDEX_V3_0_73.json"}
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
