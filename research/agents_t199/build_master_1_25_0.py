"""T-199: build rules/coverage/BOQ_FAMILY_MASTER_1.25.0.json = 1.24.0 (never edited) + the pending ARCH_TAKEOFF_V3.0.30
package (tools/family_master_candidate.py rule r3).

    python3 -I research/agents_t199/build_master_1_25_0.py --task-commit <sha> | --check

Why a new version: the V3.0.30 module (engine/source/arch_v3030.py) is newer than every registry version on the head,
and a package cannot name its merge commit or checker verdict before the Checker merges it, so V3.0.30 is declared
PENDING (status READY_FOR_GATE_B, its task commit), raises no CANDIDATE state and names no family in a candidate
block. Every other field of 1.24.0 is copied unchanged (the T-327 V3.0.29 entry included).

r2 (Checker 2026-10-31 02:58, T-199 REJECTED r1, gate f): the registry must own every item code the code writes, and
no NOT_IMPLEMENTED family may own a written code or a function name term (tests/t130_family_master guard). 1.25.0
therefore (FAMILY_MOVES below, PROPOSED for the Checker to confirm with the Gate B merge):
  B10-13 Formwork (all elements)  owns STR.FORMWORK        capability unchanged (IMPLEMENTED_NOT_INTEGRATED)
  B7-13  Stair formwork           owns STR.FORMWORK.STAIR  NOT_IMPLEMENTED -> IMPLEMENTED_NOT_INTEGRATED
  B6-05  Shutters                 owns ARCH.SHUTTER        NOT_IMPLEMENTED -> IMPLEMENTED_NOT_INTEGRATED
  B7-10  Wall-mounted handrail    owns FIN.HANDRAIL        NOT_IMPLEMENTED -> IMPLEMENTED_NOT_INTEGRATED
IMPLEMENTED_NOT_INTEGRATED is the registry's own definition of the case: tested code measures the family, only an
opt-in method (ARCH_TAKEOFF_V3.0.30) reads it, the released V2.9 + route G does not (released_method_reads stays
"none"). The moved families drop their name_terms (a name term belongs to a NOT_IMPLEMENTED family only). Candidate
blocks, in_v3_0_candidate and the released run figures are NOT changed: a pending package raises no candidate state.
No quantity changes with this file.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.24.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.25.0.json"
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
PENDING = {
    "task": "T-199", "method_version": "ARCH_TAKEOFF_V3.0.30", "module": "engine/source/arch_v3030.py",
    "status": FMC.PENDING_STATUS, "integrates": ["T-163", "T-164", "T-308", "T-311", "T-332", "T-352"],
    "tests": ["tests/t199_formwork_metalwork"],
    "changes_families_by_item_code": [],
    "note": "T-199 (research/agents_t199/T-199_FORMWORK_METALWORK_INTEGRATION.md): the two missing categories as their "
            "own line families: formwork face by face beside its member's concrete line from the merged T-332 r2 FILL "
            "table (formwork r5 = T-163 r3 + T-264 + T-293 + T-308) and the T-352 stair sides (STR.FORMWORK, "
            "STR.FORMWORK.STAIR; CALCULATED 1,061.727 + 4.105 m2, held faces and the OQ-10 alternatives BLANK, the "
            "parapet faces of T-311 HELD with no line); railings by run (MET.RAILING.GUARD, FIN.RAILING; 38.916 lm "
            "confirmed, RL-02 / RL-03 Checker-verified) and shutters by leaf (ARCH.SHUTTER 6 pcs, area HELD); every "
            "V3.0.29 line byte-identical; the Gate B integration package; names no family",
}


V3030 = "engine/source/arch_v3030.py"
T199T = "tests/t199_formwork_metalwork/test_arch_v3030.py"
OPT_IN = "ARCH_TAKEOFF_V3.0.30 (engine/source/arch_v3030.py, opt-in candidate; pending Gate B, T-199)"
PROPOSED = "1.25.0 (T-199 r2): PROPOSED by the worker, effective with the Gate B merge, the Checker confirms"
FAMILY_MOVES = {
    "B10-13": {
        "item_codes": ["STR.FORMWORK"],
        "evidence_add": [
            f"{V3030}:80 FW_CODE = STR.FORMWORK: one formwork line per formed face group beside its bound concrete line "
            "(face by face from the merged T-332 r2 FILL table; CALCULATED / HELD blank / OQ-10 alternatives beside, "
            f"never summed); {V3030}:352 fw_line()",
            f"{T199T}:147 test_hand_totals_and_states() (V199 by hand: STR.FORMWORK 18.300 m2) / :160 "
            "test_valued_line_beside_its_concrete_line_with_its_state()",
        ],
        "opt_in_readers": "none (standalone tool tools/struct_n10.py); " + OPT_IN,
        "missing": ("not in the released method; in the opt-in V3.0.30 the held faces, the OQ-10 FORMED / EARTH_CAST "
                    "pairs and the parapet faces stay blank (never 0); owner conventions FW-D1 .. FW-D4 open"),
    },
    "B7-13": {
        "capability": "IMPLEMENTED_NOT_INTEGRATED",
        "implementation": "ARCH_TAKEOFF_V3.0.30 (opt-in): STR.FORMWORK.STAIR",
        "item_codes": ["STR.FORMWORK.STAIR"],
        "evidence_set": [
            f"{V3030}:80 FW_STAIR_CODE = STR.FORMWORK.STAIR: stair waist / landing soffits from the merged T-332 r2 "
            f"FILL table and the T-352 stair side faces; {V3030}:335 _fw_code() routes a STR.CONC.STAIR member to it",
            f"{T199T}:147 test_hand_totals_and_states() (V199 by hand: STR.FORMWORK.STAIR 3.300 + 0.850 = 4.150 m2) / "
            ":302 test_stair_side_on_non_stair_line_refused()",
        ],
        "opt_in_readers": OPT_IN,
        "missing": ("not in the released method; in the opt-in V3.0.30 the held stair wall / member sides stay blank "
                    "(never 0)"),
        "note": ("1.0.0 .. 1.24.0 said NOT_IMPLEMENTED (no item code, no module); " + PROPOSED),
    },
    "B6-05": {
        "capability": "IMPLEMENTED_NOT_INTEGRATED",
        "implementation": "ARCH_TAKEOFF_V3.0.30 (opt-in): ARCH.SHUTTER",
        "item_codes": ["ARCH.SHUTTER"],
        "evidence_set": [
            f"{V3030}:464 shutter_lines(): ARCH.SHUTTER pcs by drawn leaf count (MEASURED, from the merged T-164 "
            "census) and the m2 line BLANK (BLOCKED_RFI: no owner rule sets the area basis)",
            f"{T199T}:198 test_railing_and_shutter_lines() / :337 test_shutter_area_given_refused()",
        ],
        "opt_in_readers": OPT_IN,
        "missing": "not in the released method; shutter area and material HELD (no owner rule sets the basis)",
        "note": ("1.0.0 .. 1.24.0 said NOT_IMPLEMENTED (no item code, no module); " + PROPOSED),
    },
    "B7-10": {
        "capability": "IMPLEMENTED_NOT_INTEGRATED",
        "implementation": "ARCH_TAKEOFF_V3.0.30 (opt-in): FIN.HANDRAIL",
        "evidence_set": [
            "FIN.HANDRAIL is defined in the item master (engine/source/boq_line.py:91 FIN.HANDRAIL)",
            f"{V3030}:95 RAIL_KIND: a WALL_HANDRAIL run of the merged T-164 census writes FIN.HANDRAIL; {V3030}:431 "
            "rail_line(): a drawn run MEASURED in lm on its installed path, a run not drawn EXCLUDED_WITH_REASON "
            "(UP-STAIR-013), blank",
            f"{T199T}:405 test_wall_handrail_drawn_and_not_drawn() (V199 by hand: 3.089 + 1.000 = 4.089 lm)",
        ],
        "opt_in_readers": OPT_IN,
        "missing": ("not in the released method; on the development villa no wall handrail is drawn (one "
                    "EXCLUDED_WITH_REASON line in the opt-in candidate)"),
        "note": ("1.0.0 .. 1.24.0 said NOT_IMPLEMENTED (defined, no module emitted it); " + PROPOSED),
    },
}


def _move(fam, mv, states):
    for k in ("item_codes", "implementation", "opt_in_readers", "missing", "note"):
        if k in mv:
            fam[k] = copy.deepcopy(mv[k])
    if "evidence_set" in mv:
        fam["evidence"] = list(mv["evidence_set"])
    fam["evidence"] = list(fam["evidence"]) + list(mv.get("evidence_add") or [])
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


def build(task_commit):
    old = json.loads(OLD.read_text(encoding="utf-8"))
    new = copy.deepcopy(old)
    new["version"] = "1.25.0"
    new["supersedes"] = ("1.24.0 (kept unchanged on disk; every family except B10-13 / B7-13 / B6-05 / B7-10 (r2), "
                         "every released-configuration field and the pending entries up to T-327 copied unchanged)")
    new["source"] = (str(old.get("source", "")) + " | 1.25.0 (T-199): 1.24.0 + pending ARCH_TAKEOFF_V3.0.30 "
                     "(rule r3 of tools/family_master_candidate.py); no candidate state changes")
    new["pending_packages"] = list(old.get("pending_packages") or []) + [dict(PENDING, task_commit=task_commit)]
    by = {f["code"]: f for f in new["families"]}
    for code, mv in FAMILY_MOVES.items():
        _move(by[code], mv, new["capability_states"])
    _recount(new)
    new["source"] += (" | r2 (Checker 2026-10-31 02:58): the item codes V3.0.30 writes are owned (STR.FORMWORK B10-13, "
                      "STR.FORMWORK.STAIR B7-13, ARCH.SHUTTER B6-05, FIN.HANDRAIL B7-10) and B7-13 / B6-05 / B7-10 move "
                      "NOT_IMPLEMENTED -> IMPLEMENTED_NOT_INTEGRATED (opt-in only), PROPOSED; candidate states unchanged")
    new["item_code_scan"] += (" | from 1.25.0 the same two guards run at full strength against this registry in "
                              "tests/t199_formwork_metalwork/test_family_master_1_25_0.py; the 1.1.0 checks exempt only "
                              "what the governing (newest) registry owns or moved, and only while it passes them")
    return new


def text(doc):
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"


def main(argv):
    if "--check" in argv:
        cur = json.loads(NEW.read_text(encoding="utf-8"))
        tc = cur["pending_packages"][-1]["task_commit"]
        ok = NEW.read_text(encoding="utf-8") == text(build(tc))
        bad = FMC.check(cur, root=ROOT, is_ancestor=FMC.git_is_ancestor)
        print("1.25.0 equals its builder:", ok, "| problems:", bad)
        return 0 if ok and not bad else 1
    if not TASK_COMMIT:
        print("--task-commit <40-hex sha of the commit that adds engine/source/arch_v3030.py> is required")
        return 2
    NEW.write_text(text(build(TASK_COMMIT)), encoding="utf-8")
    print("written", NEW.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
