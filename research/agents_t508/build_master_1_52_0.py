"""T-508: build rules/coverage/BOQ_FAMILY_MASTER_1.52.0.json = 1.51.0 (T-480, merged 1b66b719; never edited)
  (1) + the PROMOTION of the one package 1.51.0 holds pending that has since merged (T-480 V3.0.54, merge 1b66b719,
      Verifier 2026-11-04 15:45 Gate B), by the T-485 rule R-T485-1 (a merged package never stays pending), with the
      T-483 r2 promotion functions UNCHANGED (research/agents_t483/build_master_1_48_0.py promote / touched_block /
      carried_block, its module constants set to this promotion): merge commit and verdict from git and the board
      (out/PROMOTIONS_SOURCE_1_52_0.json, research/agents_t483/t483_promotions_source.build on 1.51.0), the families
      the package changed from the LINE DIFF V3.0.53 -> V3.0.54 of this task's reproduced chain run
      (out/T508_PACKAGE_FAMILIES.json, research/agents_t483/t483_package_families.attribute, chain (53, 54)), and the
      candidate census re-run at V3.0.54 (out/LINE_INDEX_V3_0_54.json, research/agents_t479/t479_registry_census.py
      unchanged; verdict set board verdicts/V3.0.44 b3b08dd7, downgrade snapshot research/agents_t469 81732639);
  (2) + the pending ARCH_TAKEOFF_V3.0.55 package (T-508, tools/family_master_candidate.py rule r3), the B3-06 / B7-07 /
      B7-08 text, and the two item codes the package's lines carry: FIN.STAIR.SKIRTING.ZIGZAG owned by B7-07 (zigzag)
      and FIN.STAIR.SKIRTING.SLOPED owned by B7-08 (sloped), one code per family (a code owned by two families is a
      census issue). B7-07 / B7-08 owned no item code: their census entry moves from 'n/a: owns no item code' to 'no'
      (0 lines at V3.0.54, asserted); their state stays NOT_IN_CANDIDATE until a promotion after Gate B.

T-310 may build its own master in parallel on a READY branch; under the merge-order rule the package merged later
rebases on the earlier. No quantity, capability, owner or line change with this file; the V3.0.55 lines stay pending
until a promotion version after Gate B; the released default is untouched.

    python3 -I research/agents_t508/build_master_1_52_0.py --task-commit <sha> | --check
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
ATTRIB = HERE / "out/T508_PACKAGE_FAMILIES.json"
INDEX = HERE / "out/LINE_INDEX_V3_0_54.json"
BOARD_COMMIT = "84b29148"
OLD_CAND = "ARCH_TAKEOFF_V3.0.53"
CAND, AS_OF = "ARCH_TAKEOFF_V3.0.54", "T-480"
DIFF_SPAN = "V3.0.54"
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
MOD = "engine/source/arch_v3055.py"
TST = "tests/t508_stair_skirting/test_arch_v3055.py"
ZIG, SLO = "FIN.STAIR.SKIRTING.ZIGZAG", "FIN.STAIR.SKIRTING.SLOPED"
NEW_CODES = {"B7-07": [ZIG], "B7-08": [SLO]}
PENDING = {
    "task": "T-508", "method_version": "ARCH_TAKEOFF_V3.0.55", "module": MOD,
    "status": FMC.PENDING_STATUS, "integrates": ["T-501"],
    "tests": ["tests/t508_stair_skirting"],
    "changes_families_by_item_code": ["FIN.SKIRTING", ZIG, SLO],
    "note": "T-508 (research/agents_t508/T-508_STAIR_SKIRTING_INTEGRATION.md): the stair skirting home from the "
            "Checker-merged T-501 table (R-T508-1): the 1F living room line's shaft stretches at +5.50 (no floor at "
            "that level) retired by closure 9.050 lm (41.435360 -> 32.385360) and its W13 / W25 held range 0 .. 2.200 "
            "NOT_APPLICABLE, both carried by the stair / landing piece lines; landings FIN.SKIRTING 6.100 lm "
            "DRAWING-CONFIRMED (MS1-LD 1.150, MS2-LD 3.700, RS-LD 1.250) + 3 held landing pieces blank; every flight / "
            "step piece a blank zigzag (B7-07) / sloped (B7-08) pair, never additive, form not chosen (ORR-007): "
            "HELD-FORM zigzag 23.300481 / sloped 17.009049 lm beside; FIN.SKIRTING 212.379 -> 209.429 lm; the Gate B "
            "integration package",
}
PROPOSED = ("1.52.0 (T-508): moved by the pending ARCH_TAKEOFF_V3.0.55 package (Gate B); the released capability of "
            "V2.9 + route G is unchanged; the V3.0.55 lines stay pending until a promotion version")
OPT_IN = "ARCH_TAKEOFF_V3.0.55 (engine/source/arch_v3055.py, opt-in candidate; pending Gate B, T-508)"
MISS = {"B3-06": "V3.0.55: 1F living shaft stretches 9.050 lm retired to the stair pieces; landings 6.100 lm "
                 "DRAWING-CONFIRMED (MS2-LD 3.700 own-measured by the Checker); MS1-LD.N / MS2-LD.W13 / MS2-LD.W25 "
                 "held blank (sills / heads vs the landing not printed); MS1-U top 0.300 lm CONFLICT stays in the 1F "
                 "room line until the Q-46 RFI",
        "B7-07": "V3.0.55: one blank zigzag line per flight / step piece (HELD-FORM 13 pieces 23.300481 lm beside; "
                 "held / conflict / unknown pieces blank by cause); the form (ORR-007) is not chosen",
        "B7-08": "V3.0.55: one blank sloped line per flight / step piece (HELD-FORM 13 pieces 17.009049 lm beside; "
                 "held / conflict / unknown pieces blank by cause); the form (ORR-007) is not chosen"}

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
    promoted = [dict(P48.promote(p, prom[p["task"]], attrib), promoted_in=f"{VERSION} (T-508)") for p in pend]
    for p in promoted:
        p["development_villa_run"] = p["development_villa_run"].replace("T-483 r2 chain run", "T-508 chain run")
    new["supersedes"] = (f"{old['version']} (kept unchanged on disk; every released-configuration field copied "
                         f"unchanged; its {len(promoted)} pending package promoted to candidate_packages; the families "
                         f"it changed re-derived at {CAND}, every other family's candidate block moved to {CAND} with "
                         f"its census asserted unchanged (B7-07 / B7-08: n/a -> no by their new item codes); B3-06 / B7-07 / B7-08 text "
                         f"and the two item codes for the pending V3.0.55 package; T-310 "
                         f"builds its own in parallel)")
    new["source"] = (old["source"] + f" | {VERSION} (T-508): {old['version']} + the {len(promoted)} merged pending "
                     f"package promoted (R-T485-1, merge commit + Checker verdict; census + line diff at {CAND}) + "
                     "pending ARCH_TAKEOFF_V3.0.55 (rule r3) + the B3-06 / B7-07 / B7-08 text and the B7-07 / B7-08 item "
                     "codes it adds; no quantity, capability or owner change")
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

    fams0 = {f["code"]: f for f in new["families"]}
    for code, codes in NEW_CODES.items():
        if fams0[code].get("item_codes") or fams0[code]["candidate"]["state"] != "NOT_IN_CANDIDATE":
            raise SystemExit(f"{code}: already owns item codes or is in the candidate")
        fams0[code]["item_codes"] = list(codes)
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
                                                                          f"{DIFF_SPAN} by line diff (T-508)")
            f["candidate"]["candidate_basis"] = f["candidate"]["candidate_basis"].replace(
                f"+ {DIFF_SPAN} (T-483 r2)", f"+ {DIFF_SPAN} (T-508)")
        else:
            if code in NEW_CODES:
                want = dict(oc[code], in_candidate="no")
                if oc[code]["in_candidate"] != C.NOT_LINE_ATTRIBUTABLE or cc[code] != want:
                    raise SystemExit(f"{code}: its census must move only from n/a to 'no' with 0 lines")
            elif cc[code] != oc[code]:
                raise SystemExit(f"{code}: no line changed V3.0.53 -> V3.0.54 but its census moved")
            f["candidate"] = P48.carried_block(f)
            f["candidate"]["candidate_basis"] = f["candidate"]["candidate_basis"].replace(
                f"+ {DIFF_SPAN} (T-483 r2: no line", f"+ {DIFF_SPAN} (T-508: no line")
        if code in by_family and f["candidate"]["state"] != "NOT_IN_CANDIDATE" and f["in_v3_0_candidate"] == "no":
            # a family whose first candidate lines merged (B9-02 by T-487) enters the candidate: the flag follows its
            # re-derived state (tools/family_master_candidate.py rule: yes for every in-candidate state)
            f["in_v3_0_candidate"] = "yes"
        counts[f["candidate"]["state"]] += 1
        yes_no[f["in_v3_0_candidate"]] += 1
    new["candidate_state_counts"] = counts
    new["in_v3_0_candidate_counts"] = yes_no

    fams = {f["code"]: f for f in new["families"]}
    ev = (f"{_at(MOD, r'^def changes_for')} changes_for(): room stretches along a shaft with no floor at their level "
          f"retired by closure (level-aware), landing pieces valued in FIN.SKIRTING, flight / step pieces a blank "
          f"zigzag / sloped pair (never additive, never both valued); {_at(MOD, r'^def check_stair_skirting')} "
          f"check_stair_skirting(); {_at(TST, r'^def test_hand_figures')} (villa K508 by hand)")
    for code in ("B3-06", "B7-07", "B7-08"):
        f = fams[code]
        f["evidence"] = list(f["evidence"]) + [ev]
        f["opt_in_readers"] = (str(f["opt_in_readers"]) + " | " + OPT_IN) if f.get("opt_in_readers") not in \
            (None, "", "none") else OPT_IN
        f["missing"] = str(f.get("missing") or "") + " | " + MISS[code]
        f["note"] = (str(f["note"]) + " | " + PROPOSED) if f.get("note") else PROPOSED

    old_cen = old["candidate_census"]
    new["candidate_census"] = dict(
        old_cen, method_version=CAND, lines=census["lines"], lines_sha256=index["inputs"]["lines"],
        verdicts_sha256=index["inputs"].get("verdicts"), downgrades_sha256=index["inputs"].get("downgrades"),
        index="research/agents_t508/out/LINE_INDEX_V3_0_54.json (sha256 " + hashlib.sha256(INDEX.read_bytes()).hexdigest()
              + ")",
        scope=(f"the development villa run of the merged candidate of record V3.0.54 (T-480 merge "
               f"{prom[AS_OF]['merge_commit'][:8]}; BOQ_LINES {vc['lines_sha256'][:8]} reproduced by T-508 from the "
               "Drive copies, V3.0.53 = 36863f6c on the way); the V3.0.44 "
               "verdict set and the T-469 downgrade snapshot bind by line content, as in 1.43.0"),
        families=cc, not_a_boq_lines=census["not_a_boq_lines"], no_family=census["no_family"],
        issue_counts=census["issue_counts"],
        stale_in_candidate_vs_registry=C.compare_blocks({"families": cc, "candidate_version": CAND}, new),
        previous={"method_version": old_cen["method_version"], "lines": old_cen["lines"],
                  "lines_sha256": old_cen["lines_sha256"]})
    new["promotion"] = {
        "task": "T-508", "round": "r1", "from_registry": old["version"], "promoted": [p["task"] for p in promoted],
        "previous_promotion": {"task": old["promotion"]["task"], "from_registry": old["promotion"]["from_registry"],
                               "promoted": old["promotion"]["promoted"]},
        "merge_commits_source": "research/agents_t508/out/PROMOTIONS_SOURCE_1_52_0.json (sha256 "
                                + hashlib.sha256(PROMOTIONS.read_bytes()).hexdigest() + ")",
        "line_diff": "research/agents_t508/out/T508_PACKAGE_FAMILIES.json (sha256 "
                     + hashlib.sha256(ATTRIB.read_bytes()).hexdigest() + ")",
        "rule": old["promotion"]["rule"],
        "quantity_change": "none (no engine, method, line or capability field moves)",
        "line_index": "research/agents_t508/out/LINE_INDEX_V3_0_54.json"}
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
