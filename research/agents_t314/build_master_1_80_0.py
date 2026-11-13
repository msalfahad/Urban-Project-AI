"""T-314 r4: build rules/coverage/BOQ_FAMILY_MASTER_1.80.0.json = 1.79.0 (never edited)
  (1) + the PROMOTION of the package 1.79.0 holds pending that has since merged (T-738 ARCH_TAKEOFF_V3.0.78, merge
      208c5689, Verifier 2026-11-13 13:50 UTC; its in-merge --promote did not run), by R-T485-1 (a merged package never
      stays pending) and the 1.48.0 multi-promotion pattern: merge commit and Checker verdict from git and the board
      (out/PROMOTIONS_SOURCE_T738_1_80_0.json, t314_promotions_source.py --master 1.79.0), the families it changed from
      T-738's own line diff (research/agents_t738/out/T738_PACKAGE_FAMILIES.json) and the census at V3.0.78
      (research/agents_t738/out/LINE_INDEX_V3_0_78.json). A pending package of 1.79.0 is accepted ONLY when it is in that
      source and its merge commit is an ancestor of the head; any other pending package is refused (never promoted,
      never carried into 1.80.0);
  (2) + the ARCH_TAKEOFF_V3.0.79 package (T-314, EXT_RENDER_GATE_B_V1 + EXT_PAINT_GATE_B_V1 + EXT_EDGE_DELTA_V1;
      tools/family_master_candidate.py rule r3) and the B4-07 exterior-finish family text; NEW item code FIN.EXT.PAINT.
      Candidate of record V3.0.77 -> V3.0.78 (pending mode) -> V3.0.79 (promoted in the T-314 merge).

Two modes, ONE version number (the ADOPTED lesson: a merged integration package leaves the registry promoted in the
same merge); the promotion step is research/agents_t738/build_master_1_79_0.py's (T-483 r2 functions unchanged) with
its constants passed per step:

  --task-commit <sha> [--write]  PENDING: T-738 promoted (candidate V3.0.78), V3.0.79 pending (the task branch).
  --promote [--write]            PROMOTED (run by the Verifier IN the merge, after t314_promotions_source.py --master 1.80.0
                                 has written out/PROMOTIONS_SOURCE_1_80_0.json and t314_package_families.py has written
                                 out/T314_PACKAGE_FAMILIES.json): families re-derived at V3.0.79 from the census
                                 out/LINE_INDEX_V3_0_79.json.
  --check                        the committed file equals the builder in the mode it was written in; 0 problems.

No quantity, capability, owner or line change with this file; the released default is untouched.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for _p in (ROOT, ROOT / "research" / "agents_t479", ROOT / "research" / "agents_t485", ROOT / "research" / "agents_t483"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import build_master_1_43_0 as B  # noqa: E402  (census problems / unit text of T-485, unchanged)
from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.79.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.80.0.json"
VERSION = "1.80.0"
FROM_REGISTRY = "1.79.0"
MOD = "engine/source/arch_v3079.py"
TST = "tests/t314_ext_render_paint/test_arch_v3079.py"
PROMOTIONS = HERE / "out/PROMOTIONS_SOURCE_1_80_0.json"
ATTRIB = HERE / "out/T314_PACKAGE_FAMILIES.json"
INDEX = HERE / "out/LINE_INDEX_V3_0_79.json"
REC_CAND = "ARCH_TAKEOFF_V3.0.77"          # candidate of record in 1.79.0
OLD_CAND, CAND, AS_OF = "ARCH_TAKEOFF_V3.0.78", "ARCH_TAKEOFF_V3.0.79", "T-314"
DIFF_SPAN = "V3.0.78 .. V3.0.79"
WHO = "T-314"
# the merged-pending packages of 1.79.0 this version promotes (R-T485-1; 1.48.0 pattern), each with its own sources
MERGED_PENDING = {
    "T-738": {"promotions": HERE / "out/PROMOTIONS_SOURCE_T738_1_80_0.json",
              "attrib": ROOT / "research/agents_t738/out/T738_PACKAGE_FAMILIES.json",
              "index": ROOT / "research/agents_t738/out/LINE_INDEX_V3_0_78.json",
              "old_cand": REC_CAND, "cand": OLD_CAND, "diff_span": "V3.0.77 .. V3.0.78"},
}
FAMS = ("B4-07",)
NOTE_ONLY = {}
NEW_CODES = {"B4-07": ["FIN.EXT.PAINT"]}
PENDING = {
    "task": "T-314", "method_version": CAND, "module": MOD, "status": FMC.PENDING_STATUS,
    "integrates": ["T-756"],
    "tests": ["tests/t314_ext_render_paint"],
    "changes_families_by_item_code": ["FIN.EXT.FINISH", "FIN.EXT.PAINT", "FIN.EXT.PAINT.EDGE"],
    "note": ('T-314 r3 (research/agents_t314/T-314_R3_EXT_RENDER_PAINT.md): EXT_RENDER_GATE_B_V1 + EXT_PAINT_GATE_B_V1 + EXT_EDGE_DELTA_V1 from the merged T-756 face ledger (re-based by line id onto the candidate, re-checked on V3.0.78): the 3 FIN.EXT.FINISH storey lines restated as the sum of their face rows and 12 parapet / plinth / slab-edge render lines added (net 1008.58 .. 1085.61 m2, the 1F slab-edge line HELD blank with its valued part beside); one FIN.EXT.PAINT m2 line per render line (paint = render face by face, owner rule UP-FIN-PAINT-002); the one FIN.EXT.PAINT.EDGE corner line restated 9.185812 -> 6.585812 lm (T-754 F-T754-1); released lines and every other line byte-identical; the Gate B integration package'),
}
PROPOSED = ("1.80.0 (T-314 r3): restated by the ARCH_TAKEOFF_V3.0.79 package (Gate B): exterior render face rows and "
            "exterior paint (Sigma) = render face by face (UP-FIN-PAINT-002) from the merged T-756 face ledger, and the "
            "one T-754 corner verdict; NEW item code FIN.EXT.PAINT; HELD, the released capability of V2.9 + route G "
            "unchanged")
OPT_IN = "ARCH_TAKEOFF_V3.0.79 (engine/source/arch_v3079.py, opt-in candidate; Gate B package T-314 r3)"
MISS = {
    'B4-07': ('in the opt-in candidate V3.0.79: exterior render (FIN.EXT.FINISH) is the sum of its drawn face rows, holes once by face (Q-73 A): 3 storey lines restated and 12 parapet / plinth / slab-edge lines added, net 1008.575254 .. 1085.612926 m2 (the 1F slab-edge line HELD blank, valued part 0.535 .. 2.00625 m2 beside; 6 faces HELD by name: raster-only / hidden / SE-1 unbound); exterior paint (FIN.EXT.PAINT, new code) = render face by face, 18 lines same figures; exterior corners (FIN.EXT.PAINT.EDGE) 283.218063 .. 284.418063 -> 280.618063 .. 281.818063 lm (one T-754 corner -2.60); MISSING by name: parapet blockwork x 4, parapet-top arrises x 4, passage substrate split'),
}
SUPERSEDES_TAIL = "B4-07 text for the V3.0.79 package, new item code FIN.EXT.PAINT)"


def _at(path, pattern):
    for i, ln in enumerate((ROOT / path).read_text(encoding="utf-8").splitlines(), 1):
        if re.search(pattern, ln):
            return f"{path}:{i}"
    raise SystemExit(f"{path}: no line matches {pattern!r}")


def _head_is_ancestor(commit, root=ROOT):
    return subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", commit, "HEAD"],
                          capture_output=True).returncode == 0


def promote_merged_pending(old, merged=None, is_ancestor=None):
    """R-T485-1 on the registry this version supersedes: every pending package of `old` must be merged (in its
    promotion source, merge commit an ancestor of the head) and is promoted; an unmerged one is refused, never
    promoted and never carried. -> the registry with those packages promoted (candidate moved to the last one)"""
    merged = MERGED_PENDING if merged is None else merged
    is_ancestor = _head_is_ancestor if is_ancestor is None else is_ancestor
    doc = old
    for p in list(old.get("pending_packages") or ()):
        t = p["task"]
        if t not in merged:
            raise SystemExit(f"{old['version']} pending package {t}: not merged into this registry's sources "
                             "(an unmerged package is never promoted; renumber on the newer registry, merge-order rule)")
        src = merged[t]
        prom = {r["task"]: r for r in json.loads(Path(src["promotions"]).read_text(encoding="utf-8"))}
        if t not in prom:
            raise SystemExit(f"{t}: no merge commit / verdict in {Path(src['promotions']).name}")
        mc = prom[t]["merge_commit"]
        if not re.fullmatch(r"[0-9a-f]{40}", str(mc)) or not is_ancestor(mc):
            raise SystemExit(f"{t}: merge commit {str(mc)[:10]} is not an ancestor of the head (unmerged package "
                             "refused)")
        if doc["candidate"]["method_version"] != src["old_cand"]:
            raise SystemExit(f"{t}: candidate of record {doc['candidate']['method_version']}, expected "
                             f"{src['old_cand']}")
        one = copy.deepcopy(doc)
        one["pending_packages"] = [q for q in doc["pending_packages"] if q["task"] == t]
        rest = [q for q in doc["pending_packages"] if q["task"] != t]
        doc = _step(one, who=t, promotions=Path(src["promotions"]), attrib=Path(src["attrib"]),
                    index=Path(src["index"]), old_cand=src["old_cand"], cand=src["cand"], as_of=t,
                    diff_span=src["diff_span"], promoted_in=f"{VERSION} (T-314 r4: merged pending of {old['version']}, "
                                                            "R-T485-1)",
                    supersedes_tail=None)
        doc["pending_packages"] = rest
    return doc


def build_pending(task_commit, merged=None, is_ancestor=None):
    old = json.loads(OLD.read_text(encoding="utf-8"))
    if old["candidate"]["method_version"] != REC_CAND:
        raise SystemExit(f"{old['version']}: candidate of record {old['candidate']['method_version']}, expected "
                         f"{REC_CAND}")
    base = promote_merged_pending(old, merged, is_ancestor)
    if base["pending_packages"]:
        raise SystemExit(f"pending packages left {[p['task'] for p in base['pending_packages']]}: expected none")
    if base["candidate"]["method_version"] != OLD_CAND:
        raise SystemExit(f"candidate after the promotion {base['candidate']['method_version']}, expected {OLD_CAND} "
                         "(V3.0.79 extends it)")
    promoted = [p["task"] for p in base["candidate_packages"][len(old["candidate_packages"]):]]
    new = copy.deepcopy(base)
    new["version"] = VERSION
    new["supersedes"] = (f"{old['version']} (kept unchanged on disk; every released-configuration field and every T-637 "
                         f"field copied unchanged; its merged pending package(s) {', '.join(promoted)} promoted to "
                         f"candidate_packages (R-T485-1, merge commit + Checker verdict each), candidate of record "
                         f"{REC_CAND} -> {OLD_CAND}, the families they changed re-derived at {OLD_CAND} and every other "
                         f"family's candidate block moved to {OLD_CAND} with its census asserted unchanged; "
                         + SUPERSEDES_TAIL)
    new["source"] = (old["source"] + f" | {VERSION} (T-314 r4): {old['version']} + the merged pending "
                     f"{', '.join(promoted)} promoted (R-T485-1; census + line diff at {OLD_CAND}) + ARCH_TAKEOFF_V3.0.79 "
                     "(rule r3; promoted in the merge by --promote) + the family it names; no quantity, capability or "
                     "owner change")
    new["pending_packages"] = [dict(PENDING, task_commit=task_commit)]
    fams = {f["code"]: f for f in new["families"]}
    ev = (f"{_at(MOD, r'^def _line[(]')} _line() / {_at(MOD, '^def _restate_render')} _restate_render(): face rows summed to "
          f"the line figure (holes once by face); {_at(MOD, r'^def _new_line')} _new_line() (paint = render face by face); "
          f"{_at(MOD, r'^def check_lines')} check_lines(); "
          f"{_at(TST, r'^def test_totals_by_hand')} (villa W314 by hand)")
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
    for code, txt in NOTE_ONLY.items():
        fams[code]["note"] = str(fams[code].get("note") or "") + " | " + txt
    return new


def build_promoted(task_commit):
    """the T-314 promotion in its own merge, on the pending 1.80.0"""
    return _step(build_pending(task_commit), who=WHO, promotions=PROMOTIONS, attrib=ATTRIB, index=INDEX,
                 old_cand=OLD_CAND, cand=CAND, as_of=AS_OF, diff_span=DIFF_SPAN,
                 promoted_in=f"{VERSION} ({WHO}, in the merge)", supersedes_tail=SUPERSEDES_TAIL)


def _step(old, *, who, promotions, attrib, index, old_cand, cand, as_of, diff_span, promoted_in, supersedes_tail):
    """one promotion (T-483 r2 functions unchanged, module constants pointed at this step and restored)"""
    import build_master_1_48_0 as P48  # noqa: E402
    board = {p.get("board_commit") for p in json.loads(promotions.read_text(encoding="utf-8"))}
    if len(board) != 1 or not re.fullmatch(r"[0-9a-f]{8}", str(next(iter(board)))):
        raise SystemExit(f"{promotions.name}: one agents/control board commit (8 hex) expected, got {board}")
    consts = (("VERSION", VERSION), ("BOARD_COMMIT", next(iter(board))), ("OLD_CAND", old_cand), ("CAND", cand),
              ("AS_OF", as_of), ("DIFF_SPAN", diff_span))
    saved = {k: getattr(P48, k, None) for k, _v in consts}
    try:
        for k, v in consts:
            setattr(P48, k, v)
        return _promote(old, P48, who=who, promotions=promotions, attrib_path=attrib, index_path=index,
                        old_cand=old_cand, cand=cand, as_of=as_of, diff_span=diff_span, promoted_in=promoted_in,
                        supersedes_tail=supersedes_tail)
    finally:
        for k, v in saved.items():
            setattr(P48, k, v)


def _rel(path):
    return str(Path(path).resolve().relative_to(ROOT))


def _promote(old, P48, *, who, promotions, attrib_path, index_path, old_cand, cand, as_of, diff_span, promoted_in,
             supersedes_tail):
    import t479_registry_census as C  # noqa: E402
    prom = {p["task"]: p for p in json.loads(promotions.read_text(encoding="utf-8"))}
    pend = old["pending_packages"]
    if sorted(prom) != [who] or [p["task"] for p in pend] != [who]:
        raise SystemExit(f"promotion source {sorted(prom)} / pending {[p['task'] for p in pend]}: expected [{who}]")
    attrib = json.loads(attrib_path.read_text(encoding="utf-8"))
    index = json.loads(index_path.read_text(encoding="utf-8"))
    new = copy.deepcopy(old)
    promoted = [dict(P48.promote(p, prom[p["task"]], attrib), promoted_in=promoted_in) for p in pend]
    for p in promoted:
        p["development_villa_run"] = p["development_villa_run"].replace("T-483 r2 chain run", f"{who} chain run")
    if supersedes_tail:
        if not new["supersedes"].endswith(supersedes_tail):
            raise SystemExit("supersedes text has no tail to restate")
        new["supersedes"] = new["supersedes"][:-1] + ("; the package promoted in its own merge and every family's "
                                                      f"candidate block moved to {cand})")
    head = new["v3_0_candidate"].split(": the same opt-in candidate", 1)
    if len(head) != 2:
        raise SystemExit("v3_0_candidate text has no head to restate")
    vc = attrib["versions"][cand]
    new["v3_0_candidate"] = (f"{cand} ({as_of} merge {prom[as_of]['merge_commit'][:8]}, Verifier "
                             f"{prom[as_of]['verdict_time']}, Gate B PASS; BOQ_LINES {vc['lines_sha256'][:8]}): "
                             "the same opt-in candidate" + head[1])
    new["candidate"] = dict(old["candidate"], method_version=cand, as_of_package=as_of)
    new["candidate_packages"] = old["candidate_packages"] + promoted
    new["pending_packages"] = []
    pkg_versions = {p["task"]: FMC.version_key(p["method_version"]) for p in new["candidate_packages"]}
    by_family = {}
    for p in promoted:
        v = attrib["versions"][p["method_version"]]
        for fam, codes in v["families"].items():
            by_family.setdefault(fam, []).append((p["task"], p["method_version"].replace("ARCH_TAKEOFF_", ""), codes))
    census = C.census(index, new)
    if census["candidate_version"] != cand or census["issue_counts"]:
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
            f["candidate"]["changed"] = f["candidate"]["changed"].replace(f"{diff_span} by line diff (T-483 r2)",
                                                                          f"{diff_span} by line diff ({who})")
            f["candidate"]["candidate_basis"] = f["candidate"]["candidate_basis"].replace(
                f"+ {diff_span} (T-483 r2)", f"+ {diff_span} ({who})")
        else:
            if cc[code] != oc[code]:
                raise SystemExit(f"{code}: no line changed {old_cand[-7:]} -> {cand[-7:]} but its census moved")
            f["candidate"] = P48.carried_block(f)
            f["candidate"]["candidate_basis"] = f["candidate"]["candidate_basis"].replace(
                f"+ {diff_span} (T-483 r2: no line", f"+ {diff_span} ({who}: no line")
        if code in by_family and f["candidate"]["state"] != "NOT_IN_CANDIDATE" and f["in_v3_0_candidate"] == "no":
            f["in_v3_0_candidate"] = "yes"
        counts[f["candidate"]["state"]] += 1
        yes_no[f["in_v3_0_candidate"]] += 1
    new["candidate_state_counts"] = counts
    new["in_v3_0_candidate_counts"] = yes_no
    old_cen = old["candidate_census"]
    new["candidate_census"] = dict(
        old_cen, method_version=cand, lines=census["lines"], lines_sha256=index["inputs"]["lines"],
        verdicts_sha256=index["inputs"].get("verdicts"), downgrades_sha256=index["inputs"].get("downgrades"),
        index=_rel(index_path) + " (sha256 " + hashlib.sha256(index_path.read_bytes()).hexdigest() + ")",
        scope=(f"the development villa run of the candidate {cand[-7:]} ({as_of} merge "
               f"{prom[as_of]['merge_commit'][:8]}; BOQ_LINES {vc['lines_sha256'][:8]} from the Drive copies, "
               f"{old_cand[-7:]} = {attrib['versions'][old_cand]['lines_sha256'][:8]} on the way); the V3.0.44 verdict "
               "set and the T-469 downgrade snapshot bind by line content, as in 1.43.0"),
        families=cc, not_a_boq_lines=census["not_a_boq_lines"], no_family=census["no_family"],
        issue_counts=census["issue_counts"],
        stale_in_candidate_vs_registry=C.compare_blocks({"families": cc, "candidate_version": cand}, new),
        previous={"method_version": old_cen["method_version"], "lines": old_cen["lines"],
                  "lines_sha256": old_cen["lines_sha256"]})
    new["promotion"] = {
        "task": who, "round": "r1 (in the merge)" if who == WHO else "T-314 r4 (merged pending, R-T485-1)",
        "from_registry": FROM_REGISTRY, "promoted": [p["task"] for p in promoted],
        "previous_promotion": {"task": old["promotion"]["task"], "from_registry": old["promotion"]["from_registry"],
                               "promoted": old["promotion"]["promoted"]},
        "merge_commits_source": _rel(promotions) + " (sha256 " + hashlib.sha256(promotions.read_bytes()).hexdigest()
                                + ")",
        "line_diff": _rel(attrib_path) + " (sha256 " + hashlib.sha256(attrib_path.read_bytes()).hexdigest() + ")",
        "rule": old["promotion"]["rule"],
        "quantity_change": "none (no engine, method, line or capability field moves with this file)",
        "line_index": _rel(index_path)}
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
