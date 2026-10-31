"""T-328: build rules/coverage/BOQ_FAMILY_MASTER_1.26.0.json = 1.25.0 (never edited) + the pending ARCH_TAKEOFF_V3.0.31
package (tools/family_master_candidate.py rule r3) + the registry ownership census the Lead asked for (T-328 (g) / (h)).

    python3 -I research/agents_t328/build_master_1_26_0.py --task-commit <sha> | --check

Why a new version: the V3.0.31 module (engine/source/arch_v3031.py) is newer than every registry version on the head;
a package cannot name its merge commit or checker verdict before the Checker merges it, so V3.0.31 is declared PENDING
(READY_FOR_GATE_B, its task commit), raises no candidate state and names no family in a candidate block.

(a) B13-01 Roofing build-up owns the four codes V3.0.31 writes (FIN.ROOF.SCREED / .INSULATION / .PROTECTION / .FINISH):
    NOT_IMPLEMENTED -> IMPLEMENTED_NOT_INTEGRATED (tested code, read only by the opt-in candidate), name terms dropped.
(g) OWNERSHIP CENSUS (F-T199-5): every UPPER.UPPER literal of every V3.0.x module (engine/source/arch_v30*.py) is owned
    by one family or listed apart with its reason. The 1.25.0 scan saw STR / FIN / ARCH / MAS / DOOR / MET only and
    missed, in merged packages:
      EXT.PAVING.INTERLOCK, EXT.FLOOR.PORCELAIN, EXT.FLOOR.OUTDOOR (arch_v3025.py: outdoor court floor lines) -> B13-02
          'Interlock / external paving' (the family of outdoor hard floors; NOT_IMPLEMENTED -> IMPLEMENTED_NOT_INTEGRATED);
      WP.FOUNDATION.* (8 codes, arch_v3015.py: footing membrane / screed / sides, lift-pit membrane / board / screed,
          buried-face liquid coat, procurement) -> B8-08 'Foundations / basement / below-grade walls'
          (NOT_IMPLEMENTED -> IMPLEMENTED_NOT_INTEGRATED);
      EXT.POOL.WATER_FACE (arch_v3025.py:95 POOL_FINISH_ITEM: the pool water-face finish line) -> APART with its reason
          (no family of the 100 is a pool finish: B8-09 is pool internal waterproofing, B10-10 pool concrete);
      FLOOR.INTERNAL / FLOOR.OUTDOOR (arch_v3014.py:103 FLOOR_KEYS: floor-scope keys, no line carries them as an item
          code) and WATERPROOFING.FOUNDATION (arch_v3015.py:83 FAMILY: the subtrade label) -> APART, not item codes.
(h) Lead element-register ruling F-T199-4: non-stair guard rails are their own element, owner trade metalwork: a NEW
    family B13-08 'Guard railings outside stairs' owns MET.RAILING.GUARD (removed from item_codes_without_family); the
    registry now carries 100 families (the 99-family list of 1.0.0 .. 1.25.0 kept in its order, B13-08 appended).
Candidate blocks, in_v3_0_candidate and released figures of the existing families are NOT changed (a pending package
raises no candidate state; the merged V3.0.15 / V3.0.25 / V3.0.30 candidate states are the Checker's FMC records). No
quantity changes with this file.
"""

from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.25.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.26.0.json"
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
V3031 = "engine/source/arch_v3031.py"
V3030 = "engine/source/arch_v3030.py"
V3025 = "engine/source/arch_v3025.py"
V3015 = "engine/source/arch_v3015.py"
V3014 = "engine/source/arch_v3014.py"
T328T = "tests/t328_roof_buildup/test_arch_v3031.py"
T343T = "tests/t343_outdoor_floor_integration/test_arch_v3025.py"
T270T = "tests/t270_foundation_wp_lines/test_arch_v3015.py"
T199T = "tests/t199_formwork_metalwork/test_arch_v3030.py"
PENDING = {
    "task": "T-328", "method_version": "ARCH_TAKEOFF_V3.0.31", "module": V3031,
    "status": FMC.PENDING_STATUS, "integrates": ["T-321", "T-339"], "tests": ["tests/t328_roof_buildup"],
    "changes_families_by_item_code": [],
    "note": "T-328 (research/agents_t328/T-328_ROOF_BUILDUP_INTEGRATION.md): the missing roof build-up category B13-01 "
            "as its own line family: one line per roof x layer from the merged T-321 layer ledger bound by the merged "
            "T-339 FILL table (FIN.ROOF.SCREED one m3 per roof HELD on t0, FIN.ROOF.INSULATION / .PROTECTION UNKNOWN "
            "blank, FIN.ROOF.FINISH area MEASURED, the top roof HELD on Q-34); every V3.0.30 line byte-identical; the "
            "Gate B integration package; names no family",
}
PROPOSED = "1.26.0 (T-328): PROPOSED by the worker, effective with the Gate B merge, the Checker confirms"


def _at(path, pattern):
    """'path:N' of the first line of path matching pattern (citations resolve on the tree this file is built on)."""
    for i, ln in enumerate((ROOT / path).read_text(encoding="utf-8").splitlines(), 1):
        if re.search(pattern, ln):
            return f"{path}:{i}"
    raise SystemExit(f"{path}: no line matches {pattern!r}")


def moves():
    return {
        "B13-01": {
            "capability": "IMPLEMENTED_NOT_INTEGRATED",
            "implementation": "ARCH_TAKEOFF_V3.0.31 (opt-in): FIN.ROOF.SCREED / FIN.ROOF.INSULATION / "
                              "FIN.ROOF.PROTECTION / FIN.ROOF.FINISH",
            "item_codes": ["FIN.ROOF.FINISH", "FIN.ROOF.INSULATION", "FIN.ROOF.PROTECTION", "FIN.ROOF.SCREED"],
            "evidence_set": [
                f"{_at(V3031, r'^SCREED, INSUL, PROT, FINISH =')} SCREED, INSUL, PROT, FINISH = the four roof layer codes; "
                f"{_at(V3031, r'^LAYERS = ')} LAYERS: one line per roof x layer (screed m3, insulation / protection / "
                f"finish m2); {_at(V3031, r'^def layer_line')} layer_line(): finish MEASURED, screed / insulation / "
                "protection BLANK by name (t0 D-39, scope UNKNOWN), the top roof HELD (Q-34)",
                f"{_at(T328T, r'^def test_hand_totals_and_states')} test_hand_totals_and_states() (V328 by hand: finish "
                f"47.140 + 20.000 = 67.140 m2, screed 1.400 m3) / {_at(T328T, r'^def test_adverse_a_second_falls')[len(T328T):]} "
                "test_adverse_a_second_falls_layer_for_q45_is_refused()",
            ],
            "opt_in_readers": "ARCH_TAKEOFF_V3.0.31 (engine/source/arch_v3031.py, opt-in candidate; pending Gate B, "
                              "T-328)",
            "missing": ("not in the released method; in the opt-in V3.0.31 the screed volume (t0 unprinted, D-39), the "
                        "insulation / protection layers (scope UNKNOWN) and every layer of the top roof (Q-34) stay "
                        "blank (never 0); finish material by specification"),
            "note": "1.0.0 .. 1.25.0 said NOT_IMPLEMENTED (no item code, no module); " + PROPOSED,
        },
        "B13-02": {
            "capability": "IMPLEMENTED_NOT_INTEGRATED",
            "implementation": "ARCH_TAKEOFF_V3.0.25 (opt-in): EXT.PAVING.INTERLOCK / EXT.FLOOR.PORCELAIN / "
                              "EXT.FLOOR.OUTDOOR",
            "item_codes": ["EXT.FLOOR.OUTDOOR", "EXT.FLOOR.PORCELAIN", "EXT.PAVING.INTERLOCK"],
            "evidence_set": [
                f"{_at(V3025, r'^ITEMS = [{]')} ITEMS: EXT.PAVING.INTERLOCK (court interlock), EXT.FLOOR.PORCELAIN "
                f"(outdoor porcelain) and {_at(V3025, r'^MATERIAL_HELD_ITEM =')[len(V3025):]} MATERIAL_HELD_ITEM = "
                f"EXT.FLOOR.OUTDOOR (material HELD); {_at(V3025, r'^def piece_line')[len(V3025):]} piece_line()",
                f"{_at(T343T, r'^def test_villa_lines_closure_and_states')} test_villa_lines_closure_and_states()",
            ],
            "opt_in_readers": "ARCH_TAKEOFF_V3.0.25 .. V3.0.31 (engine/source/arch_v3025.py, merged T-343 r2; "
                              "opt-in candidate)",
            "missing": "not in the released method; outdoor floor material HELD where unprinted (EXT.FLOOR.OUTDOOR)",
            "note": ("1.0.0 .. 1.25.0 said NOT_IMPLEMENTED: the 1.25.0 scan did not see the EXT. prefix (F-T199-5); "
                     + PROPOSED),
        },
        "B8-08": {
            "capability": "IMPLEMENTED_NOT_INTEGRATED",
            "implementation": "ARCH_TAKEOFF_V3.0.15 (opt-in): WP.FOUNDATION.* (WATERPROOFING.FOUNDATION family)",
            "item_codes": ["WP.FOUNDATION.BURIED_LIQUID", "WP.FOUNDATION.FOOTING_MEMBRANE",
                           "WP.FOUNDATION.FOOTING_SCREED", "WP.FOUNDATION.FOOTING_SIDES",
                           "WP.FOUNDATION.LIFT_PIT_BOARD", "WP.FOUNDATION.LIFT_PIT_MEMBRANE",
                           "WP.FOUNDATION.LIFT_PIT_SCREED", "WP.FOUNDATION.PROCUREMENT"],
            "evidence_set": [
                f"{_at(V3015, r'^ITEMS = [{]')} ITEMS: the eight WP.FOUNDATION.* codes (footing underlay membrane / "
                f"screed / sides, lift-pit membrane / board / screed, buried-face liquid coat, procurement); "
                f"{_at(V3015, r'^def record_line')[len(V3015):]} record_line()",
                f"{_at(T270T, r'^def test_family_totals_equal_the_hand_calculation')} "
                "test_family_totals_equal_the_hand_calculation()",
            ],
            "opt_in_readers": "ARCH_TAKEOFF_V3.0.15 .. V3.0.31 (engine/source/arch_v3015.py, merged T-270; opt-in "
                              "candidate)",
            "missing": "not in the released method; held pieces (footing sides by formation, pit walls by depth) blank",
            "note": ("1.0.0 .. 1.25.0 said NOT_IMPLEMENTED: the 1.25.0 scan did not see the WP. prefix (F-T199-5); "
                     + PROPOSED),
        },
    }


def new_family(old):
    tmpl = copy.deepcopy(next(f for f in old["families"] if f["code"] == "B7-13"))
    return dict(tmpl, **{
        "code": "B13-08", "group": "B13 Other",
        "item_en": "Guard railings outside stairs (roof / floor edge / balcony / fence), installed length",
        "item_ar": "درابزين حماية (أسطح / حواف / شرفات / أسوار)", "unit": "lm",
        "capability": "IMPLEMENTED_NOT_INTEGRATED", "capability_1_0_0": "NOT_IMPLEMENTED", "capability_change": "RAISED",
        "implementation": "ARCH_TAKEOFF_V3.0.30 (opt-in): MET.RAILING.GUARD",
        "source_needed": "roof / floor plans, elevations", "next_slice": "S5",
        "evidence": [
            f"{_at(V3030, r'^RAIL_STAIR, RAIL_GUARD')} RAIL_GUARD = MET.RAILING.GUARD; "
            f"{_at(V3030, r'^RAIL_KIND = ')[len(V3030):]} RAIL_KIND: ROOF_GUARD / BALCONY_GUARD / FLOOR_EDGE_GUARD / "
            f"FENCE_RAILING write it; {_at(V3030, r'^def rail_line')[len(V3030):]} rail_line(): lm on the installed path",
            f"{_at(T199T, r'^def test_railing_and_shutter_lines')} test_railing_and_shutter_lines()",
        ],
        "released_method_reads": "none",
        "opt_in_readers": "ARCH_TAKEOFF_V3.0.30 .. V3.0.31 (engine/source/arch_v3030.py, merged T-199 r3; opt-in "
                          "candidate)",
        "missing": "not in the released method; held runs blank by name (T-164 RL-04 / RL-07 / RL-09 / RL-10 / RL-11)",
        "in_v3_0_candidate": "no", "v3_0_planned_tasks": [],
        "development_villa": {"released_run": [], "candidate_run_v2_13": []},
        "item_codes": ["MET.RAILING.GUARD"], "in_v3_0_candidate_1_1_0": "no",
        "note": ("NEW in 1.26.0 (T-328 (h)): Lead element-register ruling F-T199-4 (Lead 2026-10-31 08:30): a guard rail "
                 "on an open edge outside a stair is its own element, owner trade metalwork, separate from the stair "
                 "guardrail B7-09 (never counted as a stair railing); 1.25.0 listed the code apart; capability_1_0_0 "
                 "NOT_IMPLEMENTED stands for 'no family before 1.26.0'; " + PROPOSED),
    })


APART_ADD = {
    "EXT.POOL.WATER_FACE": (
        f"{V3025}:95 POOL_FINISH_ITEM: the pool water-face finish line (floor + walls to the rim), written by the merged "
        "opt-in V3.0.25 (T-343 r2); no family of the 100 is a pool finish (B8-09 is pool internal waterproofing, B10-10 "
        "pool concrete, B13-02 outdoor floors: a pool face is not a court floor, refused there at load); a pool-finish "
        "family is proposed to the register owner (T-328 finding F-T328-2)"),
    "FLOOR.INTERNAL": (f"{V3014}:103 FLOOR_KEYS: a floor-scope key of the V3.0.14 records, not a line item code"),
    "FLOOR.OUTDOOR": (f"{V3014}:103 FLOOR_KEYS: a floor-scope key of the V3.0.14 records, not a line item code"),
    "WATERPROOFING.FOUNDATION": (f"{V3015}:83 FAMILY: the subtrade label of the WP.FOUNDATION.* lines (owned by B8-08), "
                                 "not a line item code"),
}
APART_DROP = ("MET.RAILING.GUARD",)


def _move(fam, mv, states):
    for k in ("item_codes", "implementation", "opt_in_readers", "missing", "note"):
        if k in mv:
            fam[k] = copy.deepcopy(mv[k])
    if "evidence_set" in mv:
        fam["evidence"] = list(mv["evidence_set"])
    if "capability" in mv:
        fam["capability"] = mv["capability"]
        rank = {s: i for i, s in enumerate(states)}
        c0, c1 = rank[fam["capability_1_0_0"]], rank[fam["capability"]]
        fam["capability_change"] = "UNCHANGED" if c0 == c1 else ("RAISED" if c1 < c0 else "LOWERED")
    if fam["capability"] != "NOT_IMPLEMENTED":
        fam.pop("name_terms", None)


def _recount(new):
    fam = new["families"]
    new["capability_counts"] = {k: sum(1 for f in fam if f["capability"] == k) for k in new["capability_states"]}
    new["capability_change_counts"] = {k: sum(1 for f in fam if f["capability_change"] == k)
                                       for k in ("RAISED", "LOWERED", "UNCHANGED")}
    new["in_v3_0_candidate_counts"] = {k: sum(1 for f in fam if f["in_v3_0_candidate"] == k) for k in ("yes", "no")}
    new["candidate_state_counts"] = {k: sum(1 for f in fam if f["candidate"]["state"] == k)
                                     for k in new["candidate_state_counts"]}


def build(task_commit):
    old = json.loads(OLD.read_text(encoding="utf-8"))
    new = copy.deepcopy(old)
    new["version"] = "1.26.0"
    new["supersedes"] = ("1.25.0 (kept unchanged on disk; every family except B13-01 / B13-02 / B8-08 and the new "
                         "B13-08, every released-configuration field and the pending entries up to T-199 copied "
                         "unchanged)")
    new["source"] = (str(old.get("source", "")) + " | 1.26.0 (T-328): 1.25.0 + pending ARCH_TAKEOFF_V3.0.31 (rule r3 "
                     "of tools/family_master_candidate.py) + the V3.0.x ownership census (F-T199-5) + the guard-railing "
                     "family B13-08 (F-T199-4); no candidate state changes")
    new["pending_packages"] = list(old.get("pending_packages") or []) + [dict(PENDING, task_commit=task_commit)]
    by = {f["code"]: f for f in new["families"]}
    for code, mv in moves().items():
        _move(by[code], mv, new["capability_states"])
    new["families"].append(new_family(old))
    apart = {k: v for k, v in new["item_codes_without_family"].items() if k not in APART_DROP}
    assert not set(APART_ADD) & set(apart)
    new["item_codes_without_family"] = dict(apart, **APART_ADD)
    _recount(new)
    new["item_code_scan"] += (" | 1.26.0 (T-328): the guard scans every prefix found in the V3.0.x modules (STR / FIN "
                              "/ ARCH / MAS / DOOR / MET / EXT / WP / FLOOR / WATERPROOFING), and every UPPER.UPPER "
                              "literal of every engine/source/arch_v30*.py module must be owned by one family or listed "
                              "apart (tests/t328_roof_buildup/test_family_master_1_26_0.py); the family list is 100 "
                              "(B13-08 appended)")
    return new


def text(doc):
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"


def main(argv):
    if "--check" in argv:
        cur = json.loads(NEW.read_text(encoding="utf-8"))
        tc = cur["pending_packages"][-1]["task_commit"]
        ok = NEW.read_text(encoding="utf-8") == text(build(tc))
        bad = FMC.check(cur, root=ROOT, is_ancestor=FMC.git_is_ancestor)
        print("1.26.0 equals its builder:", ok, "| problems:", bad)
        return 0 if ok and not bad else 1
    if not TASK_COMMIT:
        print("--task-commit <40-hex sha of the commit that adds engine/source/arch_v3031.py> is required")
        return 2
    NEW.write_text(text(build(TASK_COMMIT)), encoding="utf-8")
    print("written", NEW.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
