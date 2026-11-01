"""T-429: build rules/coverage/BOQ_FAMILY_MASTER_1.34.0.json = 1.33.0 (never edited) + the pending ARCH_TAKEOFF_V3.0.39
package (tools/family_master_candidate.py rule r3) + the B7 stair families whose lines V3.0.39 rebinds.

    python3 -I research/agents_t429/build_master_1_34_0.py --task-commit <sha> | --check

Why a new version: the V3.0.39 module (engine/source/arch_v3039.py) is newer than every registry version on the head; a
package cannot name its merge commit or checker verdict before the Checker merges it, so V3.0.39 is declared PENDING
(READY_FOR_GATE_B, its task commit), raises no candidate state and names no family in a candidate block.

Families V3.0.39 touches: B7-02 tread marble (FIN.MARBLE.TREAD), B7-06 commercial step basis (FIN.STAIR.STEP_LM), B7-03
visible riser (FIN.MARBLE.RISER: two riser lines take their reading's disposition, no quantity moves). Their 'missing'
text loses the double count (one physical flight, one valued line in the opt-in candidate) and names what stays held;
their opt-in reader becomes ARCH_TAKEOFF_V3.0.39. Capability stays PARTIAL (the released V2.9 still double counts; the
fix is opt-in only). No candidate state changes; no quantity changes with this file.
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

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.33.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.34.0.json"
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
V3039 = "engine/source/arch_v3039.py"
T429T = "tests/t429_tread_binding_integration/test_arch_v3039.py"
TREAD, STEP, RISER = "FIN.MARBLE.TREAD", "FIN.STAIR.STEP_LM", "FIN.MARBLE.RISER"
PENDING = {
    "task": "T-429", "method_version": "ARCH_TAKEOFF_V3.0.39", "module": V3039,
    "status": FMC.PENDING_STATUS, "integrates": ["T-425", "T-434"],
    "tests": ["tests/t429_tread_binding_integration"],
    "changes_families_by_item_code": [TREAD, STEP, RISER],
    "note": "T-429 (research/agents_t429/T-429_TREAD_BINDING_INTEGRATION.md): the Checker-merged T-425 tread / step "
            "binding with the T-434 winder-turn count: B7-02 valued 27.324 -> 20.010 m2 and B7-06 91.028 -> 67.850 lm "
            "(MS2-L read again on 2F SUPERSEDED as DOUBLE_COUNT with its riser line, RS-S GF F3 FOLDED, MS1-L / MS1-U / "
            "MS2-U / RS-S / RS-A carriers corrected to the drawn fronts, the MS1-T winder turn and RS-C HELD blank with "
            "their figures beside, MS2-U's last going m2 HELD beside); every other V3.0.38 line byte-identical; the "
            "Gate B integration package",
}
PROPOSED = ("1.34.0 (T-429): moved by the pending ARCH_TAKEOFF_V3.0.39 package (Gate B); the released capability of "
            "V2.9 + route G is unchanged (the released method still reads every flight reading)")
OPT_IN = "ARCH_TAKEOFF_V3.0.39 (engine/source/arch_v3039.py, opt-in candidate; pending Gate B, T-429)"


def _at(path, pattern):
    for i, ln in enumerate((ROOT / path).read_text(encoding="utf-8").splitlines(), 1):
        if re.search(pattern, ln):
            return f"{path}:{i}"
    raise SystemExit(f"{path}: no line matches {pattern!r}")


def moves(old_by):
    ev = (f"{_at(V3039, r'^def changes_for')} changes_for(): per reading KEEP / CORRECT / SUPERSEDE / HOLD from the "
          f"merged binding; {_at(V3039, r'^def check_flights')} check_flights(): one physical flight, one valued tread "
          f"and step line; {_at(V3039, r'^def level_class')} level_class() (F-C-T425-1)")
    out = {}
    for code, test, miss in (
            ("B7-02", "test_hand_figures", "released V2.9 still values the seen-through 2F reading (+3.45 m2); in the "
             "opt-in candidate V3.0.39: winder turn HELD (S-9, subdivision not drawn), round stair curved part HELD "
             "(Q-50 A cond), one last going not drawn (m2 HELD beside)"),
            ("B7-06", "test_hand_figures", "released V2.9 still values the seen-through 2F reading (+11.50 lm); in "
             "the opt-in candidate V3.0.39: winder turn and round stair curved part HELD"),
            ("B7-03", "test_seen_through_listed_without_quantity_owned_by_carrier", None)):
        f = old_by[code]
        mv = {"evidence_set": list(f["evidence"]) + [ev + f"; {_at(T429T, '^def ' + test)} {test}() (K429 by hand)"],
              "opt_in_readers": OPT_IN,
              "note": str(f.get("note") or "") + " | " + PROPOSED}
        if miss:
            mv["missing"] = miss
        out[code] = mv
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
    new["version"] = "1.34.0"
    new["supersedes"] = ("1.33.0 (kept unchanged on disk; every family except B7-02, B7-03 and B7-06, every "
                         "released-configuration field and the pending entries up to T-421 copied unchanged)")
    new["source"] = (str(old.get("source", "")) + " | 1.34.0 (T-429): 1.33.0 + pending ARCH_TAKEOFF_V3.0.39 (rule r3 "
                     "of tools/family_master_candidate.py) + the B7 stair families it rebinds; no candidate state "
                     "changes")
    new["pending_packages"] = list(old.get("pending_packages") or []) + [dict(PENDING, task_commit=task_commit)]
    by = {f["code"]: f for f in new["families"]}
    for code, mv in moves({f["code"]: f for f in old["families"]}).items():
        _move(by[code], mv, new["capability_states"])
    _recount(new)
    new["item_code_scan"] += " | 1.34.0 (T-429): same scan; V3.0.39 writes no new code"
    return new


def text(doc):
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"


def main(argv):
    if "--check" in argv:
        cur = json.loads(NEW.read_text(encoding="utf-8"))
        tc = cur["pending_packages"][-1]["task_commit"]
        ok = NEW.read_text(encoding="utf-8") == text(build(tc))
        bad = FMC.check(cur, root=ROOT, is_ancestor=FMC.git_is_ancestor)
        print("1.34.0 equals its builder:", ok, "| problems:", bad)
        return 0 if ok and not bad else 1
    if not TASK_COMMIT:
        print("--task-commit <40-hex sha of the commit that adds engine/source/arch_v3039.py> is required")
        return 2
    NEW.write_text(text(build(TASK_COMMIT)), encoding="utf-8")
    print("written", NEW.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
