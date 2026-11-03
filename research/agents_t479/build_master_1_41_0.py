"""T-479: build rules/coverage/BOQ_FAMILY_MASTER_1.41.0.json = 1.40.0 (never edited) + the registry corrections of
three Checker / handoff findings of 2 Nov. NO quantity, capability of an existing family, owner state, candidate state
or default changes.

    python3 -I research/agents_t479/build_master_1_41_0.py [--check]

1 LINES OUTSIDE EVERY FAMILY (T-471 F-1, 2 candidate lines):
  - EXT.POOL.WATER_FACE (engine/source/arch_v3025.py POOL_FINISH_ITEM, the pool water-face finish line, held
    BLOCKED_RFI blank): a physical work item (tile / mosaic on the water floor and walls) that no family of 1.40.0 is:
    B8-09 is pool internal WATERPROOFING, B10-10 pool CONCRETE, B13-02 outdoor FLOORS (the owner rule of 2026-10-21:
    "the pool water is never a floor"). -> NEW family B13-09 'Pool / tank internal finish (water faces)', unit m2,
    owning that one code (removed from item_codes_without_family). Capability BLOCKED_BY_SOURCE (the finish is printed
    on no sheet: T-309 / T-343), candidate state NOT_IN_CANDIDATE as of the registry's candidate V3.0.7 (the line is
    newer: V3.0.25), exactly as B7-15 / B5-06 entered in 1.27.0.
  - ARCH.EXTERIOR (engine/source/arch_measure.py: a space with no finish kind gets ARCH.SPACE / ARCH.EXTERIOR with its
    area): an AREA REGISTER line of an exterior space, not a work item. OQ-04 was answered A (owner 2026-10-21 20:25:
    outside finishes ARE in the BOQ) and those finishes are their own B13-02 lines (OWNER_RULE_OUTDOOR_FLOORS), the
    waterproofing B8-06 / B8-07; the garden band's classification is with the designer (D-48). -> declared in the new
    top-level 'not_a_boq_line_codes' with that evidence; it stays in item_codes_without_family (the code scan guard of
    tests/t130_family_master keeps working) and is reported apart by the census, never dropped, never summed into a
    family.
2 STALE CANDIDATE BLOCKS (T-353, T-474): every family's 'candidate' block is dated V3.0.7 / T-193 (no registry version
  since 1.3.0 has moved a merged package from pending_packages to candidate_packages), so B8-08 (carried since V3.0.15,
  T-270) and B10-13 / B7-13 (since V3.0.30, T-199) read 'in_v3_0_candidate: no'. Rewriting 'candidate' alone is refused
  by tools/family_master_candidate.py (every family must name the registry's candidate version, and 38 merged packages
  would have to be promoted with their verdicts first). -> NEW top-level 'candidate_census': a fresh line-level census
  of the candidate of record (research/agents_t479/t479_registry_census.py on the merged V3.0.44 run) for EVERY family,
  dated by its own method version and lines sha256; and the stale reader text of the three families corrected
  (opt_in_readers / v3_0_planned_tasks / note) with file:line evidence. The 'candidate' blocks stay as of V3.0.7
  (the registry-wide promotion is a separate step, reported as finding F-T479-1).
3 VERDICT SHARE (T-353): the census reports per family and unit VERIFIED_WHOLE and VERIFIED_COMPONENT apart; B8-08: 7 of
  7 Checker-verified lines bound (2 WHOLE, 5 COMPONENT each covering its whole line; their groups still hold the
  F10 / F and pit-wall HELD lines, so a WHOLE group verdict is impossible by tools/boq_export_v1.bind_verdict).
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
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import t479_registry_census as C  # noqa: E402
OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.40.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.41.0.json"
INDEX = HERE / "out/LINE_INDEX_V3_0_44.json"
REFRESHED = ("B8-08", "B10-13", "B7-13")


def _at(path, pattern):
    for i, ln in enumerate((ROOT / path).read_text(encoding="utf-8").splitlines(), 1):
        if re.search(pattern, ln):
            return f"{path}:{i}"
    raise SystemExit(f"{path}: no line matches {pattern!r}")


def pool_family():
    return {
        "code": "B13-09", "group": "B13 Other", "item_en": "Pool / tank internal finish (water faces)",
        "item_ar": "تشطيب وجه المياه "
                   "للمسبح", "unit": "m2",
        "capability": "BLOCKED_BY_SOURCE", "capability_1_0_0": "NOT_IMPLEMENTED", "capability_change": "RAISED",
        "implementation": "ARCH_TAKEOFF_V3.0.25 (opt-in): EXT.POOL.WATER_FACE (one held line per pool, blank, its "
                          "geometric bound beside)",
        "source_needed": "the pool finish specification (tile / mosaic, which faces) on a sheet or an owner rule",
        "next_slice": "S5",
        "evidence": [
            f"{_at('engine/source/arch_v3025.py', r'^POOL_FINISH_ITEM =')} POOL_FINISH_ITEM = EXT.POOL.WATER_FACE; "
            f"{_at('engine/source/arch_v3025.py', r'^def pool_line')} pool_line(): the water-face finish line "
            "(water floor + walls to the rim), held BLOCKED_RFI with its bound beside, never valued",
            f"{_at('tests/t343_outdoor_floor_integration/test_arch_v3025.py', 'POOL_FINISH_ITEM')} (villa by hand: "
            "the pool line held, never 0)",
            "research/agents_t309 (MERGED 834ada3e): the pool detail prints no finish hatch on the water side; "
            "research/agents_t343 (V3.0.25): the line, BLOCKED_RFI blank, bound 21.308727 m2 beside on the "
            "development villa"],
        "released_method_reads": "none",
        "opt_in_readers": "ARCH_TAKEOFF_V3.0.25 .. V3.0.44 (engine/source/arch_v3025.py, merged T-343; opt-in "
                          "candidate; census: research/agents_t479)",
        "missing": "the finish is printed on no sheet and no owner rule sets it: the line stays BLOCKED_RFI blank "
                   "(never 0); not a floor (owner rule 2026-10-21: the pool water is never a floor) and not the pool "
                   "waterproofing (B8-09)",
        "in_v3_0_candidate": "no", "v3_0_planned_tasks": [],
        "development_villa": {"released_run": [], "candidate_run_v2_13": []},
        "item_codes": ["EXT.POOL.WATER_FACE"], "in_v3_0_candidate_1_1_0": "no",
        "candidate": {"state": "NOT_IN_CANDIDATE", "method_version": "ARCH_TAKEOFF_V3.0.7", "packages": [],
                      "as_of_package": "T-193", "changed": "",
                      "open": "no candidate line as of V3.0.7 (the line is newer: V3.0.25); see candidate_census",
                      "released_in_candidate": "none"},
        "note": "NEW in 1.41.0 (T-479, from T-471 finding F-1 and T-328 finding F-T328-2): the pool water-face finish "
                "line was owned by no family (1.26.0 .. 1.40.0 item_codes_without_family); capability_1_0_0 "
                "NOT_IMPLEMENTED stands for 'no family before 1.41.0'; PROPOSED by the worker, effective with the "
                "Gate B merge, the Checker confirms",
    }


NOT_A_BOQ = {
    "ARCH.EXTERIOR": {
        "meaning": "the area of an exterior space (garden band, court, roof) as an AREA REGISTER line: a space with no "
                   "finish kind is written with its area; it is no work item of any family",
        "evidence": [
            "engine/source/arch_measure.py:323 ec = ARCH.EXTERIOR if kind == EXTERIOR else ARCH.SPACE (the space "
            "register line of a space with no finish kind, net = the space area)",
            "OWNER_QUESTIONS_ANSWERED OQ-04 (owner 2026-10-21 20:25, answer A): outside finishes ARE in the BOQ, each as "
            "its own finish line by OWNER_RULE_OUTDOOR_FLOORS_2026-10-21 (family B13-02); waterproofing B8-06 / B8-07",
            "the garden band's classification (floor or landscape) is with the designer, D-48 (OQ-04 record; "
            "research/agents_t431: band 9.101 m2 ARCH.EXTERIOR unchanged, curb 0.604 held on D-48)"],
        "rule": "reported apart by every census, never dropped, never summed into a family; if D-48 makes the band a "
                "floor, its finish is a NEW B13-02 line, never this register line re-labelled",
        "since": "1.41.0 (T-479)"},
}


def build(index):
    old = json.loads(OLD.read_text(encoding="utf-8"))
    new = copy.deepcopy(old)
    new["version"] = "1.41.0"
    new["supersedes"] = ("1.40.0 (kept unchanged on disk; every family except B8-08, B10-13, B7-13 (reader text only) "
                         "copied unchanged; family B13-09 added; pending packages unchanged)")
    new["source"] = (str(old.get("source", "")) + " | 1.41.0 (T-479): 1.40.0 + family B13-09 (pool water-face "
                     "finish) + not_a_boq_line_codes (ARCH.EXTERIOR) + candidate_census (fresh line census of the "
                     "merged V3.0.44 run) + the reader text of B8-08 / B10-13 / B7-13; no quantity, no candidate state")
    iw = dict(new["item_codes_without_family"])
    iw.pop("EXT.POOL.WATER_FACE")
    iw["ARCH.EXTERIOR"] = (iw["ARCH.EXTERIOR"] + " | 1.41.0: declared NOT_A_BOQ_LINE (not_a_boq_line_codes) with "
                           "its evidence")
    new["item_codes_without_family"] = iw
    new["not_a_boq_line_codes"] = copy.deepcopy(NOT_A_BOQ)
    new["families"].append(pool_family())

    fams = {f["code"]: f for f in new["families"]}
    hub = "tools/urban_boq_m9.py"
    f = fams["B8-08"]
    f["opt_in_readers"] = ("ARCH_TAKEOFF_V3.0.15 .. V3.0.44 (engine/source/arch_v3015.py, merged T-270; "
                           f"{_at(hub, r'^    v3015 = a.method in')} runs the V3.0.15 extension for every method "
                           "V3.0.15 .. V3.0.45; opt-in candidate)")
    f["note"] = (f["note"] + " | 1.41.0 (T-479, from the T-353 Checker note): the candidate CARRIES the eight "
                 "WP.FOUNDATION codes since V3.0.15 (census V3.0.44 in candidate_census); 'in_v3_0_candidate: no' and "
                 "the 'candidate' block are as of V3.0.7 (registry-wide, F-T479-1), not a statement about V3.0.44")
    for code in ("B10-13", "B7-13"):
        g = fams[code]
        g["opt_in_readers"] = g["opt_in_readers"].replace(
            "ARCH_TAKEOFF_V3.0.30 (engine/source/arch_v3030.py, opt-in candidate; pending Gate B, T-199)",
            f"ARCH_TAKEOFF_V3.0.30 .. V3.0.44 (engine/source/arch_v3030.py, merged T-199; "
            f"{_at(hub, r'^    v3030 = a.method in')} runs it for every method V3.0.30 .. V3.0.45; opt-in candidate)")
        assert "merged T-199" in g["opt_in_readers"], code
        if g.get("v3_0_planned_tasks") == ["T-199"]:
            g["v3_0_planned_tasks"] = []
        g["note"] = (str(g.get("note") or "") + " | 1.41.0 (T-479, from the T-474 handoff): T-199 merged; the "
                     "candidate CARRIES this family since V3.0.30 (census V3.0.44 in candidate_census); "
                     "'in_v3_0_candidate: no' and the 'candidate' block are as of V3.0.7 (registry-wide, F-T479-1)")

    cap = dict(new["capability_counts"])
    cap["BLOCKED_BY_SOURCE"] += 1
    new["capability_counts"] = cap
    chg = dict(new["capability_change_counts"])
    chg["RAISED"] += 1
    new["capability_change_counts"] = chg
    yn = dict(new["in_v3_0_candidate_counts"])
    yn["no"] += 1
    new["in_v3_0_candidate_counts"] = yn
    cs = dict(new["candidate_state_counts"])
    cs["NOT_IN_CANDIDATE"] += 1
    new["candidate_state_counts"] = cs

    census = C.census(index, new)                      # the census against THIS registry (B13-09, NOT_A_BOQ_LINE)
    stale = C.compare_blocks(census, new)
    new["candidate_census"] = {
        "method_version": census["candidate_version"],
        "builder": "research/agents_t479/t479_registry_census.py (line class and verdict binding as T-469; "
                   "every line in exactly one bucket: family / NOT_A_BOQ_LINE / NO_FAMILY)",
        "lines": census["lines"],
        "lines_sha256": index["inputs"]["lines"],
        "verdicts_sha256": index["inputs"].get("verdicts"),
        "downgrades_sha256": index["inputs"].get("downgrades"),
        "index": "research/agents_t479/out/LINE_INDEX_V3_0_44.json (sha256 "
                 + hashlib.sha256(INDEX.read_bytes()).hexdigest() + ")",
        "scope": "the development villa run of the merged candidate of record V3.0.44 (T-422 merge b4e22291), "
                 "reproduced from the Drive copies; the pending V3.0.45 (T-478) changes B10-01 lines only",
        "meaning": "per family: in_candidate yes/no, lines, item codes present and, per unit, released / held "
                   "(bounded low .. high, UNKNOWN count) / excluded, and the Checker-verified share apart: "
                   "VERIFIED_WHOLE (group verdict) and VERIFIED_COMPONENT (a one-line verdict equal to the whole "
                   "line); held is never 0 and never summed; this block states the candidate, the 'candidate' "
                   "blocks above stay as of V3.0.7",
        "families": {c: census["families"][c] for c in sorted(census["families"])},
        "not_a_boq_lines": census["not_a_boq_lines"],
        "no_family": census["no_family"],
        "issue_counts": census["issue_counts"],
        "stale_in_candidate_vs_registry": stale,
    }
    return new


def text(doc):
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


def main(argv):
    out = text(build(json.loads(INDEX.read_text(encoding="utf-8"))))
    if "--check" in argv:
        ok = NEW.read_text(encoding="utf-8") == out
        print("1.41.0", "reproduces" if ok else "DIFFERS")
        return 0 if ok else 1
    NEW.write_text(out, encoding="utf-8")
    print("written", NEW.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
