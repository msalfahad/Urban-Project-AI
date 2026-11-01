"""T-430: build rules/coverage/BOQ_FAMILY_MASTER_1.35.0.json = 1.34.0 (never edited) + the pending ARCH_TAKEOFF_V3.0.40
package (tools/family_master_candidate.py rule r3) + the ground-beam family whose lines V3.0.40 splits and holds.

    python3 -I research/agents_t430/build_master_1_35_0.py --task-commit <sha> | --check

Why a new version: the V3.0.40 module (engine/source/arch_v3040.py) is newer than every registry version on the head; a
package cannot name its merge commit or checker verdict before the Checker merges it, so V3.0.40 is declared PENDING
(READY_FOR_GATE_B, its task commit), raises no candidate state and names no family in a candidate block.

Family V3.0.40 touches: B10-04 strap / ground beams (STR.CONC.GROUND_BEAM: two bands split at their founded necks into
runs, one run each valued at its printed section and one HELD on D-33; one picked range end and one unprinted sliver
HELD). Its 'missing' text names what stays held; its opt-in reader becomes ARCH_TAKEOFF_V3.0.40. Capability stays
PARTIAL (the released V2.9 still bounds every ground-beam line); no owner and no candidate state changes; no quantity
changes with this file.
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

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.34.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.35.0.json"
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
V3040 = "engine/source/arch_v3040.py"
T430T = "tests/t430_gb_run_section_integration/test_arch_v3040.py"
GB = "STR.CONC.GROUND_BEAM"
PENDING = {
    "task": "T-430", "method_version": "ARCH_TAKEOFF_V3.0.40", "module": V3040,
    "status": FMC.PENDING_STATUS, "integrates": ["T-426", "T-416"],
    "tests": ["tests/t430_gb_run_section_integration"],
    "changes_families_by_item_code": [GB],
    "note": "T-430 (research/agents_t430/T-430_GB_RUN_SECTION_INTEGRATION.md): the Checker-merged T-426 ground-beam "
            "section per run with the T-416 exact neck cut: 7DC+7DD and 7E7+7E8 split at the founded necks 7F5 / 7ED "
            "(1.323 -> 0.423 m3 each: the unloaded 3.525 m run at the printed 30 x 40, VERIFIED; the loaded run an "
            "ADDED line HELD on D-33 with 0.423 .. 0.6435 / 0.6345 m3 beside; the 0.300 m neck the neck's); 177+7CD#1 "
            "HELD (range 0.5964 .. 0.9036 m3); the 0.10 m annex-arc sliver HELD blank; ground-beam valued -2.7126 m3; "
            "every other V3.0.39 line byte-identical; the Gate B integration package",
}
PROPOSED = ("1.35.0 (T-430): moved by the pending ARCH_TAKEOFF_V3.0.40 package (Gate B); the released capability of "
            "V2.9 + route G is unchanged (the released method still bounds every ground-beam line)")
OPT_IN = "ARCH_TAKEOFF_V3.0.40 (engine/source/arch_v3040.py, opt-in candidate; pending Gate B, T-430)"


def _at(path, pattern):
    for i, ln in enumerate((ROOT / path).read_text(encoding="utf-8").splitlines(), 1):
        if re.search(pattern, ln):
            return f"{path}:{i}"
    raise SystemExit(f"{path}: no line matches {pattern!r}")


def moves(old_by):
    ev = (f"{_at(V3040, r'^def changes_for')} changes_for(): a band crossed by a founded neck split into its runs "
          f"(SPLIT_VALUED / SPLIT_HELD), picked range ends and unprinted sections HELD (HOLD_RANGE / HOLD_BLANK); "
          f"{_at(V3040, r'^def check_runs')} check_runs(): valued run = b x printed D x run length, held blank with its "
          f"range, no run twice")
    f = old_by["B10-04"]
    return {"B10-04": {
        "evidence_set": list(f["evidence"]) + [ev + f"; {_at(T430T, '^def test_hand_figures_k430')} "
                                                    f"test_hand_figures_k430() (K430 by hand)"],
        "opt_in_readers": str(f.get("opt_in_readers") or "") + " | " + OPT_IN,
        "missing": (str(f.get("missing") or "") + " | in the opt-in candidate V3.0.40: two loaded runs HELD on D-33, "
                    "177+7CD#1 HELD on its title range (reading + D-33), the annex-arc sliver HELD (no printed section, "
                    "D-35); four runs under 2.5 m stay valued at the 0.40 end of D-34 (a downgrade-only extension is "
                    "proposed to the Checker)"),
        "note": str(f.get("note") or "") + " | " + PROPOSED}}


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
    new["version"] = "1.35.0"
    new["supersedes"] = ("1.34.0 (kept unchanged on disk; every family except B10-04, every released-configuration "
                         "field and the pending entries up to T-429 copied unchanged)")
    new["source"] = (str(old.get("source", "")) + " | 1.35.0 (T-430): 1.34.0 + pending ARCH_TAKEOFF_V3.0.40 (rule r3 "
                     "of tools/family_master_candidate.py) + the ground-beam family it splits and holds; no candidate "
                     "state changes")
    new["pending_packages"] = list(old.get("pending_packages") or []) + [dict(PENDING, task_commit=task_commit)]
    by = {f["code"]: f for f in new["families"]}
    for code, mv in moves({f["code"]: f for f in old["families"]}).items():
        _move(by[code], mv, new["capability_states"])
    _recount(new)
    new["item_code_scan"] += (" | 1.35.0 (T-430): same scan; V3.0.40 writes no new code (it adds two "
                              "STR.CONC.GROUND_BEAM lines, B10-04's)")
    return new


def text(doc):
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"


def main(argv):
    if "--check" in argv:
        cur = json.loads(NEW.read_text(encoding="utf-8"))
        tc = cur["pending_packages"][-1]["task_commit"]
        ok = NEW.read_text(encoding="utf-8") == text(build(tc))
        bad = FMC.check(cur, root=ROOT, is_ancestor=FMC.git_is_ancestor)
        print("1.35.0 equals its builder:", ok, "| problems:", bad)
        return 0 if ok and not bad else 1
    if not TASK_COMMIT:
        print("--task-commit <40-hex sha of the commit that adds engine/source/arch_v3040.py> is required")
        return 2
    NEW.write_text(text(build(TASK_COMMIT)), encoding="utf-8")
    print("written", NEW.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
