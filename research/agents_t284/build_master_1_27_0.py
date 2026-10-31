"""T-284: build rules/coverage/BOQ_FAMILY_MASTER_1.27.0.json = 1.26.0 (never edited) + the pending ARCH_TAKEOFF_V3.0.32
package (tools/family_master_candidate.py rule r3) + the owners of the codes it writes.

    python3 -I research/agents_t284/build_master_1_27_0.py --task-commit <sha> | --check

Why a new version: the V3.0.32 module (engine/source/arch_v3032.py) is newer than every registry version on the head;
a package cannot name its merge commit or checker verdict before the Checker merges it, so V3.0.32 is declared PENDING
(READY_FOR_GATE_B, its task commit), raises no candidate state and names no family in a candidate block.

Owners of the four new codes (ownership census of T-328 (g): every UPPER.UPPER literal of every V3.0.x module is owned
by one family or listed apart with its reason):
  FIN.CEILING.BULKHEAD -> B5-04 'Bulkheads / dropped ceilings' (BLOCKED_BY_SOURCE -> IMPLEMENTED_NOT_INTEGRATED: the
      owner method Q-48 A + Q-43 measures the vertical faces without a reflected ceiling plan; tested code read only by
      the opt-in candidate);
  FIN.PAINT.CEILING -> B4-06 'Internal paint' (the paint trade; capability unchanged PARTIAL, the code added beside
      FIN.PAINT: owner Q-57 A modified measures the paintable gypsum surface separately);
  FIN.STAIR.SOFFIT -> NEW B7-15 'Stair soffit finish', FIN.DOME.SOFFIT -> NEW B5-06 'Dome intrados finish' (no family
      of the 100 is either; V3.0.32 writes each only as a BLANK held line: BLOCKED_BY_SOURCE; appended after B13-08).
Candidate blocks, in_v3_0_candidate and released figures of the existing families are NOT changed. No quantity changes
with this file.
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

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.26.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.27.0.json"
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
V3032 = "engine/source/arch_v3032.py"
T284T = "tests/t284_ceiling_integration/test_arch_v3032.py"
PENDING = {
    "task": "T-284", "method_version": "ARCH_TAKEOFF_V3.0.32", "module": V3032,
    "status": FMC.PENDING_STATUS, "integrates": ["T-283", "T-335", "T-281"],
    "tests": ["tests/t284_ceiling_integration"],
    "changes_families_by_item_code": [],
    "note": "T-284 (research/agents_t284/T-284_CEILING_INTEGRATION.md): the ceiling line family filled from the merged "
            "ceilings r3 ledger (T-283) bound to the FIN.CEILING line ids by the merged T-335 FILL table: decor per "
            "room (DRAWING-CONFIRMED, lines PROVISIONAL), owner bulkhead faces FIN.CEILING.BULKHEAD and ceiling paint "
            "FIN.PAINT.CEILING (ASSUMED - OWNER-APPROVED), stair soffits FIN.STAIR.SOFFIT and dome intrados "
            "FIN.DOME.SOFFIT BLANK by item; every other V3.0.31 line byte-identical; the Gate B integration package; "
            "names no family",
}
PROPOSED = "1.27.0 (T-284): PROPOSED by the worker, effective with the Gate B merge, the Checker confirms"


def _at(path, pattern):
    """'path:N' of the first line of path matching pattern (citations resolve on the tree this file is built on)."""
    for i, ln in enumerate((ROOT / path).read_text(encoding="utf-8").splitlines(), 1):
        if re.search(pattern, ln):
            return f"{path}:{i}"
    raise SystemExit(f"{path}: no line matches {pattern!r}")


def moves(old):
    b406 = next(f for f in old["families"] if f["code"] == "B4-06")
    return {
        "B5-04": {
            "capability": "IMPLEMENTED_NOT_INTEGRATED",
            "implementation": "ARCH_TAKEOFF_V3.0.32 (opt-in): FIN.CEILING.BULKHEAD",
            "item_codes": ["FIN.CEILING.BULKHEAD"],
            "evidence_set": [
                f"{_at(V3032, r'^CEILING, BULKHEAD, PAINT =')} BULKHEAD = FIN.CEILING.BULKHEAD; "
                f"{_at(V3032, r'^def changes_for')[len(V3032):]} changes_for(): one bulkhead line per room, owner "
                "method (Q-48 A + Q-43: free beam edge with decor on the open side x 0.15 m), ASSUMED - OWNER-APPROVED",
                f"{_at(T284T, r'^def test_room_lines_by_hand')} test_room_lines_by_hand() (V284: 6.00 m x 0.15 = "
                f"0.900 m2) / {_at(T284T, r'^def test_bulkhead_without_owner_rule_refused')[len(T284T):]} "
                "test_bulkhead_without_owner_rule_refused()",
            ],
            "opt_in_readers": "ARCH_TAKEOFF_V3.0.32 (engine/source/arch_v3032.py, opt-in candidate; pending Gate B, "
                              "T-284)",
            "missing": ("not in the released method; in the opt-in V3.0.32 the owner-method faces only: bulkhead edges "
                        "on CONFLICT / HELD beams, the drawing-derived candidate (D-40) and dropped ceilings stay HELD "
                        "by name; a reflected ceiling plan is still needed for anything beyond the owner method"),
            "note": "1.0.0 .. 1.26.0 said BLOCKED_BY_SOURCE (no item code, no module); " + PROPOSED,
        },
        "B4-06": {
            "item_codes": ["FIN.PAINT", "FIN.PAINT.CEILING"],
            "evidence_set": list(b406["evidence"]) + [
                f"{_at(V3032, r'^CEILING, BULKHEAD, PAINT =')} PAINT = FIN.PAINT.CEILING (paint on the gypsum ceiling "
                f"= decor + bulkhead faces, Q-57 A mod (6)); {_at(V3032, r'^def check_ceilings')[len(V3032):]} "
                "check_ceilings(): paint of a room = its decor + bulkhead lines",
                f"{_at(T284T, r'^def test_paint_not_decor_plus_bulkhead_refused')} "
                "test_paint_not_decor_plus_bulkhead_refused()",
            ],
            "opt_in_readers": "ARCH_TAKEOFF_V3.0.32 (engine/source/arch_v3032.py: FIN.PAINT.CEILING, opt-in candidate; "
                              "pending Gate B, T-284)",
            "note": ("1.27.0 (T-284): FIN.PAINT.CEILING added beside FIN.PAINT (ceiling paint is a layer of its own, "
                     "never inside a wall paint line or the ceiling area line, R-T335-1); capability unchanged; "
                     + PROPOSED),
        },
    }


def new_families(old):
    """B7-15 stair soffit finish and B5-06 dome intrados finish: no family of the 100 is either (B7-12 stair concrete,
    B7-13 stair formwork, B5-01 room ceilings, B10-09 dome concrete, B10-13 formwork); appended after B13-08 (the
    1.26.0 order kept). The opt-in V3.0.32 writes each only as a BLANK held line: BLOCKED_BY_SOURCE."""
    out = []
    for code, group, en, ar, const, src, missing, note in (
            ("B7-15", "B7 Stairs", "Stair soffit finish (flight / landing undersides)", "تشطيب بطنية الدرج",
             "STAIR_SOFFIT", "stair sections, a verified soffit ledger, the owner's method O / D",
             "the stair soffit true area is not verified whole (T-281: two sample flights); method O vs D is a "
             "RULE_DIFFERENCE with no owner rule; curved / winder / junction rows HELD: one BLANK line per stair",
             "a stair soffit is the underside of the flight / landing (T-281 STAIR_SOFFIT_V1), excluded from the room "
             "ceilings (R-CEIL-R3-1) and owned by no family before 1.27.0"),
            ("B5-06", "B5 Ceilings", "Dome intrados finish", "تشطيب باطن القبة", "DOME_SOFFIT",
             "designer: what closes the dome opening (DCR-4); dome section",
             "what closes the dome opening is not drawn (designer DCR-4): one BLANK line per dome, the open disc and "
             "the S0 intrados beside, never in FIN.CEILING",
             "the open dome position is not a decor ceiling (T-283 / T-335); its intrados finish had no family before "
             "1.27.0")):
        tmpl = copy.deepcopy(next(f for f in old["families"] if f["code"] == "B7-13"))
        out.append(dict(tmpl, **{
            "code": code, "group": group, "item_en": en, "item_ar": ar, "unit": "m2",
            "capability": "BLOCKED_BY_SOURCE", "capability_1_0_0": "NOT_IMPLEMENTED", "capability_change": "RAISED",
            "implementation": f"ARCH_TAKEOFF_V3.0.32 (opt-in): FIN.{const.replace('_', '.')} (blank held lines only)",
            "source_needed": src, "next_slice": "S5",
            "evidence": [
                f"{_at(V3032, r'^STAIR_SOFFIT, DOME_SOFFIT =')} STAIR_SOFFIT = FIN.STAIR.SOFFIT, DOME_SOFFIT = "
                f"FIN.DOME.SOFFIT; {_at(V3032, r'^def check_ceilings')[len(V3032):]} check_ceilings(): a valued "
                "stair soffit / dome intrados line is refused (they stay HELD)",
                f"{_at(T284T, r'^def test_held_lines_blank_never_zero')} test_held_lines_blank_never_zero() / "
                f"{_at(T284T, r'^def test_valued_stair_soffit_refused')[len(T284T):]} test_valued_stair_soffit_refused()",
            ],
            "released_method_reads": "none",
            "opt_in_readers": "ARCH_TAKEOFF_V3.0.32 (engine/source/arch_v3032.py, opt-in candidate; pending Gate B, "
                              "T-284)",
            "missing": missing, "in_v3_0_candidate": "no", "v3_0_planned_tasks": [],
            "development_villa": {"released_run": [], "candidate_run_v2_13": []},
            "item_codes": [f"FIN.{const.replace('_', '.')}"], "in_v3_0_candidate_1_1_0": "no",
            "note": f"NEW in 1.27.0 (T-284): {note}; capability_1_0_0 NOT_IMPLEMENTED stands for 'no family before "
                    f"1.27.0'; " + PROPOSED,
        }))
    return out


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
    new["version"] = "1.27.0"
    new["supersedes"] = ("1.26.0 (kept unchanged on disk; every family except B5-04 / B4-06 and the new B7-15 / B5-06, every released-"
                         "configuration field and the pending entries up to T-328 copied unchanged)")
    new["source"] = (str(old.get("source", "")) + " | 1.27.0 (T-284): 1.26.0 + pending ARCH_TAKEOFF_V3.0.32 (rule r3 "
                     "of tools/family_master_candidate.py) + the owners of its four codes; no candidate state changes")
    new["pending_packages"] = list(old.get("pending_packages") or []) + [dict(PENDING, task_commit=task_commit)]
    by = {f["code"]: f for f in new["families"]}
    for code, mv in moves(old).items():
        _move(by[code], mv, new["capability_states"])
    new["families"] += new_families(old)
    _recount(new)
    new["item_code_scan"] += (" | 1.27.0 (T-284): same scan; FIN.CEILING.BULKHEAD -> B5-04, FIN.PAINT.CEILING -> B4-06, "
                              "FIN.STAIR.SOFFIT -> new B7-15, FIN.DOME.SOFFIT -> new B5-06 (blank held lines only); 102 families")
    return new


def text(doc):
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"


def main(argv):
    if "--check" in argv:
        cur = json.loads(NEW.read_text(encoding="utf-8"))
        tc = cur["pending_packages"][-1]["task_commit"]
        ok = NEW.read_text(encoding="utf-8") == text(build(tc))
        bad = FMC.check(cur, root=ROOT, is_ancestor=FMC.git_is_ancestor)
        print("1.27.0 equals its builder:", ok, "| problems:", bad)
        return 0 if ok and not bad else 1
    if not TASK_COMMIT:
        print("--task-commit <40-hex sha of the commit that adds engine/source/arch_v3032.py> is required")
        return 2
    NEW.write_text(text(build(TASK_COMMIT)), encoding="utf-8")
    print("written", NEW.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
