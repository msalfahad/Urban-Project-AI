"""T-400: build rules/coverage/BOQ_FAMILY_MASTER_1.30.0.json = 1.29.0 (never edited) + the pending ARCH_TAKEOFF_V3.0.35
package (tools/family_master_candidate.py rule r3) + the owners of the codes V3.0.35 writes.

    python3 -I research/agents_t400/build_master_1_30_0.py --task-commit <sha> | --check

Why a new version: the V3.0.35 module (engine/source/arch_v3035.py) is newer than every registry version on the head;
a package cannot name its merge commit or checker verdict before the Checker merges it, so V3.0.35 is declared PENDING
(READY_FOR_GATE_B, its task commit), raises no candidate state and names no family in a candidate block.

(a) B13-04 'Fencing / gates' owns the nine EXT.FENCE.* codes V3.0.35 writes (wall plane, block net, block count,
    masonry below N.G., face, top, plaster, paint, gate leaf): NOT_IMPLEMENTED -> IMPLEMENTED_NOT_INTEGRATED (tested
    code, read only by the opt-in candidate), name terms dropped. Its candidate state stays NOT_IN_CANDIDATE (pending).
(b) B10-11 'Boundary wall concrete' owns the new STR.CONC.BOUNDARY_PAD (the boundary pad footings, HELD blank): the
    family of the boundary wall's concrete (its STR.CONC.BOUNDARY_WALL band line is bound, not changed); its capability
    and candidate state are unchanged.
No quantity changes with this file.
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

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.29.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.30.0.json"
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
V3035 = "engine/source/arch_v3035.py"
T400T = "tests/t400_boundary_fence/test_arch_v3035.py"
FENCE_CODES = ["EXT.FENCE.BLOCK", "EXT.FENCE.BLOCK_COUNT", "EXT.FENCE.FACE", "EXT.FENCE.GATE",
               "EXT.FENCE.MASONRY_BELOW_NG", "EXT.FENCE.PAINT", "EXT.FENCE.PLASTER", "EXT.FENCE.TOP", "EXT.FENCE.WALL"]
PAD_CODE = "STR.CONC.BOUNDARY_PAD"
PENDING = {
    "task": "T-400", "method_version": "ARCH_TAKEOFF_V3.0.35", "module": V3035,
    "status": FMC.PENDING_STATUS, "integrates": ["T-396", "T-403", "T-404", "T-361"],
    "tests": ["tests/t400_boundary_fence"],
    "changes_families_by_item_code": [],
    "note": "T-400 (research/agents_t400/T-400_BOUNDARY_FENCE_INTEGRATION.md): the MISSING category B13-04 boundary "
            "fence and gates, component by component: wall plane north 83.1305 + street 14.840 = 97.9705 m2, faces "
            "north outside 83.1305 + plot 82.0705 = 165.201 m2 and the north top 31.37 m.l DRAWING-CONFIRMED; block "
            "net / type / count, every plaster / paint layer, the sea / passage runs, the street faces / top / "
            "stop-end, the masonry below N.G. (AT_LEAST 17.628 m2), the pads and the G-01 leaf HELD blank by name; "
            "the upper boundary G.B held range 0 .. 3.5256 m3 (drawn gross); the lower band (line-content "
            "downgrade) and G-02 = D-GF-15 bound by id, never a second line; every other V3.0.34 line "
            "byte-identical; the Gate B integration package",
}
PROPOSED = ("1.30.0 (T-400): moved by the pending ARCH_TAKEOFF_V3.0.35 package (Gate B); the released capability of "
            "V2.9 + route G is unchanged (no released method reads these codes)")


def _at(path, pattern):
    for i, ln in enumerate((ROOT / path).read_text(encoding="utf-8").splitlines(), 1):
        if re.search(pattern, ln):
            return f"{path}:{i}"
    raise SystemExit(f"{path}: no line matches {pattern!r}")


def moves():
    return {
        "B13-04": {
            "capability": "IMPLEMENTED_NOT_INTEGRATED",
            "implementation": "ARCH_TAKEOFF_V3.0.35 (opt-in): " + " / ".join(FENCE_CODES),
            "item_codes": list(FENCE_CODES),
            "evidence_set": [
                f"{_at(V3035, r'^NEW_ITEMS = ')} NEW_ITEMS: the nine boundary codes; {_at(V3035, r'^VALUE_CODES = ')} "
                "VALUE_CODES: only the wall plane, the physical face and the top may carry a figure; "
                f"{_at(V3035, r'^def load_inputs')} load_inputs(): a valued component equals its terms, a held one is "
                f"blank with its bound beside; {_at(V3035, r'^def check_boundary')} check_boundary(): one line per component, "
                "no fence element outside the family, a gate counted once",
                f"{_at(T400T, r'^def test_lines_added_values_and_blanks')} test_lines_added_values_and_blanks() (V400 "
                "by hand: plane 43.200 + 13.920 = 57.120 m2, faces 85.920 m2, top 18.00 m) / "
                f"{_at(T400T, r'^def test_adverse_block_net_valued')[len(T400T):]} test_adverse_block_net_valued()",
            ],
            "opt_in_readers": "ARCH_TAKEOFF_V3.0.35 (engine/source/arch_v3035.py, opt-in candidate; pending Gate B, "
                              "T-400)",
            "missing": ("not in the released method; in the opt-in V3.0.35 the block net / type / count, every finish "
                        "layer, the sea element (Q-63 C), the passage closure, the street profile, the masonry below "
                        "N.G. (formation a minimum) and the G-01 leaf stay blank (never 0)"),
            "note": "1.0.0 .. 1.29.0 said NOT_IMPLEMENTED (no item code, no module); " + PROPOSED,
        },
    }


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
    new["version"] = "1.30.0"
    new["supersedes"] = ("1.29.0 (kept unchanged on disk; every family except B13-04 / B10-11, every released-"
                         "configuration field and the pending entries up to T-399 copied unchanged)")
    new["source"] = (str(old.get("source", "")) + " | 1.30.0 (T-400): 1.29.0 + pending ARCH_TAKEOFF_V3.0.35 (rule r3 "
                     "of tools/family_master_candidate.py) + B13-04 owns the EXT.FENCE.* codes (IMPLEMENTED_NOT_"
                     "INTEGRATED) + B10-11 owns STR.CONC.BOUNDARY_PAD; no candidate state changes")
    new["pending_packages"] = list(old.get("pending_packages") or []) + [dict(PENDING, task_commit=task_commit)]
    by = {f["code"]: f for f in new["families"]}
    for code, mv in moves().items():
        _move(by[code], mv, new["capability_states"])
    b11 = by["B10-11"]
    b11["item_codes"] = sorted(set(b11["item_codes"]) | {PAD_CODE})
    b11["note"] = ((b11.get("note") + " | ") if b11.get("note") else "") + (
        f"1.30.0 (T-400): owns {PAD_CODE} (boundary pad footings, HELD blank in the opt-in V3.0.35: count not "
        "printed); capability and candidate state unchanged")
    _recount(new)
    new["item_code_scan"] += (" | 1.30.0 (T-400): same scan; V3.0.35 writes EXT.FENCE.* (B13-04) and "
                              "STR.CONC.BOUNDARY_PAD (B10-11) and restates one STR.CONC.GROUND_BEAM line (B10-04's)")
    return new


def text(doc):
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"


def main(argv):
    if "--check" in argv:
        cur = json.loads(NEW.read_text(encoding="utf-8"))
        tc = cur["pending_packages"][-1]["task_commit"]
        ok = NEW.read_text(encoding="utf-8") == text(build(tc))
        bad = FMC.check(cur, root=ROOT, is_ancestor=FMC.git_is_ancestor)
        print("1.30.0 equals its builder:", ok, "| problems:", bad)
        return 0 if ok and not bad else 1
    if not TASK_COMMIT:
        print("--task-commit <40-hex sha of the commit that adds engine/source/arch_v3035.py> is required")
        return 2
    NEW.write_text(text(build(TASK_COMMIT)), encoding="utf-8")
    print("written", NEW.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
