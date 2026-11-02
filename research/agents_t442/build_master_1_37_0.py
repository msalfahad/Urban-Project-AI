"""T-442: build rules/coverage/BOQ_FAMILY_MASTER_1.37.0.json = 1.36.0 (never edited) + the pending ARCH_TAKEOFF_V3.0.42
package (tools/family_master_candidate.py rule r3) + the families whose lines V3.0.42 adds, values or re-texts.

    python3 -I research/agents_t442/build_master_1_37_0.py --task-commit <sha> | --check

Why a new version: the V3.0.42 module (engine/source/arch_v3042.py) is newer than every registry version on the head; a
package cannot name its merge commit or checker verdict before the Checker merges it, so V3.0.42 is declared PENDING
(READY_FOR_GATE_B, its task commit), raises no candidate state and names no family in a candidate block.

Families V3.0.42 touches (evidence, opt-in reader, missing / note text only): B10-05 ground slab (the held lift-shaft
cell valued at its four re-measured panels, one new line for the stair-zone panel), B10-06 columns (13 CONFLICT lines
re-texted D-63 -> D-66, no figure), B10-10 lift (the pit-wall line re-texted D-43 -> the T-401 basis, no figure). No
capability, owner or candidate state changes; no quantity changes with this file.
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

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.36.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.37.0.json"
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
V3042 = "engine/source/arch_v3042.py"
T442T = "tests/t442_ground_slab_integration/test_arch_v3042.py"
PENDING = {
    "task": "T-442", "method_version": "ARCH_TAKEOFF_V3.0.42", "module": V3042,
    "status": FMC.PENDING_STATUS, "integrates": ["T-444", "T-436", "T-433", "T-401"],
    "tests": ["tests/t442_ground_slab_integration"],
    "changes_families_by_item_code": ["STR.CONC.GROUND_SLAB", "STR.CONC.COLUMN", "STR.CONC.LIFT"],
    "note": "T-442 (research/agents_t442/T-442_GROUND_SLAB_INTEGRATION.md): the Checker-verified ground-slab panels: "
            "the held lift-shaft cell L-41cfb82e valued at OWN-007 / 009 / 010 / 047 35.6054 m2 x printed T 0.10 = "
            "3.560540 m3 (T-444, shaft 2.8125 = raft-top pit floor and ring 0.880 = pit wall named beside); one new "
            "ground-slab line for the stair-zone panel OWN-011 8.372326 m2 x 0.10 = 0.837233 m3 (T-436, the cell's "
            "'stair zone' exclusion retired); cause texts only: 13 column CONFLICT lines D-63 -> D-66 (RFI-S20), the "
            "CL-LIFT pit-wall line D-43 -> the T-401 basis (T-433); every other V3.0.41 line byte-identical; the Gate B "
            "integration package",
}
PROPOSED = ("1.37.0 (T-442): moved by the pending ARCH_TAKEOFF_V3.0.42 package (Gate B); the released capability of "
            "V2.9 + route G is unchanged")
OPT_IN = "ARCH_TAKEOFF_V3.0.42 (engine/source/arch_v3042.py, opt-in candidate; pending Gate B, T-442)"
TOUCH = {
    "B10-05": "in the opt-in candidate V3.0.42: the freelancer's plate beyond the drawn network (6.3864 m2) UNRESOLVED; "
              "the two lift-side panels (0.1143 m2) not placed; the beam-stub end triangles (-0.009 m3) not wired "
              "(worker-traced only)",
    "B10-06": None,
    "B10-10": None,
}


def _at(path, pattern):
    for i, ln in enumerate((ROOT / path).read_text(encoding="utf-8").splitlines(), 1):
        if re.search(pattern, ln):
            return f"{path}:{i}"
    raise SystemExit(f"{path}: no line matches {pattern!r}")


def moves(old_by):
    ev = (f"{_at(V3042, r'^def changes_for')} changes_for(): a held slab cell valued at its re-measured panels x T "
          f"(shaft / ring beside with their owners), a stair-zone panel added as one ground-slab line, cause texts "
          f"re-named with every figure kept; {_at(V3042, r'^def check_slab')} check_slab(): slab line = panels x T, "
          f"no panel in two lines, one line per cell, no live held-bound record on a valued cell, a re-texted line "
          f"moves no figure; {_at(T442T, '^def test_hand_figures_g442')} test_hand_figures_g442() (G442 by hand)")
    out = {}
    for code, miss in TOUCH.items():
        f = old_by[code]
        mv = {"evidence_set": list(f["evidence"]) + [ev],
              "opt_in_readers": str(f.get("opt_in_readers") or "") + " | " + OPT_IN,
              "note": str(f.get("note") or "") + " | " + PROPOSED}
        if miss:
            mv["missing"] = str(f.get("missing") or "") + " | " + miss
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
    new["version"] = "1.37.0"
    new["supersedes"] = ("1.36.0 (kept unchanged on disk; every family except B10-05, B10-06, B10-10, every "
                         "released-configuration field and the pending entries up to T-431 copied unchanged)")
    new["source"] = (str(old.get("source", "")) + " | 1.37.0 (T-442): 1.36.0 + pending ARCH_TAKEOFF_V3.0.42 (rule r3 "
                     "of tools/family_master_candidate.py) + the families whose lines it adds, values or re-texts; no "
                     "candidate state changes")
    new["pending_packages"] = list(old.get("pending_packages") or []) + [dict(PENDING, task_commit=task_commit)]
    by = {f["code"]: f for f in new["families"]}
    for code, mv in moves({f["code"]: f for f in old["families"]}).items():
        _move(by[code], mv, new["capability_states"])
    _recount(new)
    new["item_code_scan"] += (" | 1.37.0 (T-442): same scan; V3.0.42 writes no new code (its added line is "
                              "STR.CONC.GROUND_SLAB, already owned)")
    return new


def text(doc):
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"


def main(argv):
    if "--check" in argv:
        cur = json.loads(NEW.read_text(encoding="utf-8"))
        tc = cur["pending_packages"][-1]["task_commit"]
        ok = NEW.read_text(encoding="utf-8") == text(build(tc))
        bad = FMC.check(cur, root=ROOT, is_ancestor=FMC.git_is_ancestor)
        print("1.37.0 equals its builder:", ok, "| problems:", bad)
        return 0 if ok and not bad else 1
    if not TASK_COMMIT:
        print("--task-commit <40-hex sha of the commit that adds engine/source/arch_v3042.py> is required")
        return 2
    NEW.write_text(text(build(TASK_COMMIT)), encoding="utf-8")
    print("written", NEW.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
