"""T-770 r7: build rules/coverage/BOQ_FAMILY_MASTER_1.84.0.json = 1.83.0 (never edited; T-770 r6 promoted, candidate of
record ARCH_TAKEOFF_V3.0.83, no pending package) + the ARCH_TAKEOFF_V3.0.84 package (T-770 r7, FILL_WIRE_V4,
R-T770-1 .. -5; tools/family_master_candidate.py rule r3). 20 NEW item codes (the T-771 added lines) join the families the
Checker-verified T-771 set maps them to (master_mapping_proposal.item_codes_to_family; every family already exists and owns
none of them); the proposal's MOVE of FIN.EXT.FINISH B4-07 -> B4-04 is NOT done here (an ownership change of an existing
code, left to the round that wires T-760, the exterior render set).

Two modes, ONE version number, on the 1.83.0 pattern (research/agents_t770/build_master_1_83_0.py, the T-314 r4 _step
unchanged with this version's constants):

  --write             PENDING: V3.0.84 pending (the task branch, as handed in for Gate B).
  --promote [--write] PROMOTED (the Verifier IN the merge, after t770_promotions_source_1_84_0.py wrote
                      out/PROMOTIONS_SOURCE_1_84_0.json and t770_package_families_1_84_0.py (chain 83 84) on the
                      Verifier's own Drive chain run wrote out/T770_PACKAGE_FAMILIES_1_84_0.json): families re-derived at
                      V3.0.84 from the census out/LINE_INDEX_V3_0_84.json; then write_manifest_1_84_0.py.
  --check             the committed file equals the builder in the mode it was written in; 0 problems.

Package id T-770d (fourth package of board row T-770, branch agents/task-T-770; T-770 = r2-r4, T-770b = r5, T-770c = r6).

No quantity, capability or line change with this file; the released default is untouched.

    bash scripts/agent_env.sh run --tree task-T-770 research/agents_t770/build_master_1_84_0.py [--write | --promote --write | --check]
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.83.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.84.0.json"
VERSION = "1.84.0"
TASK_COMMIT = "5eb5d82ada239631f22b38124705edeebc4cc2bc"     # the commit that added engine/source/arch_v3084.py
CODES = ["ARCH.SHUTTER", "ARCH.THRESHOLD", "ARCH.WINDOW", "ARCH.WINDOW_REVEAL", "DOOR.INTERNAL.PVC", "DOOR.MAIN_ENTRANCE", "FIN.CEILING", "FIN.CEILING.BULKHEAD", "FIN.CEILING.CORNICE", "FIN.CEILING.GYPSUM", "FIN.DOME.SOFFIT", "FIN.MARBLE.LANDING", "FIN.MARBLE.LIFT_SURROUND", "FIN.MARBLE.RISER", "FIN.MARBLE.TREAD", "FIN.SPATTER_DASH", "FIN.STAIR.FLIGHT", "FIN.STAIR.NOSING", "FIN.STAIR.SKIRTING.SLOPED", "FIN.STAIR.SKIRTING.ZIGZAG", "FIN.STAIR.SOFFIT", "FIN.STAIR.STEP_LM", "FIN.WALL.TILE.EDGE", "JOIN.KITCHEN.BASE", "JOIN.KITCHEN.WALL", "JOIN.WARDROBE", "MAS.MESH_STRIP", "MAS.SHARMAT", "MEP.SAN.BASIN", "MEP.SAN.FLOOR_DRAIN_3IN", "MEP.SAN.FLOOR_DRAIN_4IN", "MEP.SAN.KITCHEN_SINK", "MEP.SAN.SHOWER_TRAY", "MEP.SAN.SHOWER_WALKIN", "MEP.SAN.WASHING_MACHINE_POINT", "MEP.SAN.WC", "MET.RAILING.POST", "SITE.EXCAVATION_SUPPORT"]
PENDING = {"task": "T-770d", "method_version": "ARCH_TAKEOFF_V3.0.84", "module": "engine/source/arch_v3084.py",
           "status": FMC.PENDING_STATUS, "integrates": ["T-766", "T-768", "T-771"],
           "tests": ["tests/t770_fill_wire"], "changes_families_by_item_code": CODES,
           "note": "T-770 r7 (DELIVERY MODE wiring, research/agents_t770/v3084_index.py) on the V3.0.83 candidate (T-770 "
                   "r6): T-766 stair finishes 66 rows + 2 landing lines (18 sloped-skirting form alternatives "
                   "EXCLUDED_WITH_REASON, never 0), T-768 openings / ceilings / domes 43 rows (9 EXCLUDED with their "
                   "reasons), T-771 missing families 22 added lines (3 ranges kept HELD, mesh / sharmat OPTIONAL; "
                   "spatter, gypsum and nosing recomputed from their carriers on the wired candidate; exterior spatter "
                   "deferred until T-760 is wired); non-measured figures PROVISIONAL, never VERIFIED; every other line "
                   "byte-identical; blank non-rebar lines 124 -> 56",
           "task_commit": TASK_COMMIT}


HERE = Path(__file__).resolve().parent
PROMOTIONS = HERE / "out/PROMOTIONS_SOURCE_1_84_0.json"
ATTRIB = HERE / "out/T770_PACKAGE_FAMILIES_1_84_0.json"
INDEX = HERE / "out/LINE_INDEX_V3_0_84.json"
OLD_CAND, CAND, WHO = "ARCH_TAKEOFF_V3.0.83", "ARCH_TAKEOFF_V3.0.84", "T-770d"
DIFF_SPAN = "V3.0.83 .. V3.0.84"
NEW_CODES = {   # the merged T-771 set's master_mapping_proposal.item_codes_to_family (research/agents_t771/out/FIX_ROWS.json)
    "B1-06": ["SITE.EXCAVATION_SUPPORT"], "B4-05": ["FIN.SPATTER_DASH"], "B4-10": ["FIN.WALL.TILE.EDGE"],
    "B5-02": ["FIN.CEILING.GYPSUM"], "B5-03": ["FIN.CEILING.CORNICE"], "B7-05": ["FIN.STAIR.NOSING"],
    "B7-11": ["MET.RAILING.POST"], "B9-03": ["MAS.MESH_STRIP", "MAS.SHARMAT"],
    "B12-01": ["MEP.SAN.BASIN", "MEP.SAN.FLOOR_DRAIN_3IN", "MEP.SAN.FLOOR_DRAIN_4IN", "MEP.SAN.KITCHEN_SINK",
               "MEP.SAN.SHOWER_TRAY", "MEP.SAN.SHOWER_WALKIN", "MEP.SAN.WASHING_MACHINE_POINT", "MEP.SAN.WC"],
    "B13-06": ["JOIN.KITCHEN.BASE", "JOIN.KITCHEN.WALL", "JOIN.WARDROBE"],
}
NEW_CODE_NOTE = "1.84.0 (T-770 r7): item code(s) of the merged T-771 added lines (its master_mapping_proposal)"


def build():
    """PENDING 1.84.0 (task branch)."""
    old = json.loads(OLD.read_text(encoding="utf-8"))
    if old.get("version") != "1.83.0" or old.get("pending_packages"):
        raise SystemExit(f"base registry {old.get('version')} is not a promoted 1.83.0 (pending "
                         f"{[p.get('task') for p in old.get('pending_packages') or []]})")
    if old["candidate"]["method_version"] != OLD_CAND:
        raise SystemExit(f"1.83.0 candidate of record {old['candidate']['method_version']}, expected {OLD_CAND}")
    new = copy.deepcopy(old)
    new["version"] = VERSION
    new["supersedes"] = ("1.83.0 (kept unchanged on disk; every field copied unchanged) + the pending "
                         "ARCH_TAKEOFF_V3.0.84 package (T-770 r7)")
    new["source"] = old["source"] + (" | 1.84.0 (T-770 r7): 1.83.0 + pending ARCH_TAKEOFF_V3.0.84 (rule r3 of "
                                     "tools/family_master_candidate.py, FILL_WIRE_V3) handed in for Gate B, promoted "
                                     "in the merge by --promote; 20 new item codes (T-771 mapping); no capability change")
    new["pending_packages"] = list(old.get("pending_packages") or []) + [PENDING]
    fams = {f["code"]: f for f in new["families"]}
    for code, codes in NEW_CODES.items():
        f = fams[code]
        for c in codes:
            if any(c in (g.get("item_codes") or ()) for g in new["families"]):
                raise SystemExit(f"{c} already owned")
            f["item_codes"] = sorted(list(f["item_codes"]) + [c])
        f["note"] = str(f.get("note") or "") + " | " + NEW_CODE_NOTE
    return new


def build_promoted():
    """the T-770 r7 promotion in its own merge, on the pending 1.84.0: the T-314 r4 step (T-483 r2 functions unchanged)
    with this version's module constants, restored afterwards."""
    for p in (ROOT / "research" / "agents_t314", ROOT / "research" / "agents_t479", ROOT / "research" / "agents_t485",
              ROOT / "research" / "agents_t483"):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
    import build_master_1_80_0 as M314  # noqa: E402
    consts = {"VERSION": VERSION, "FROM_REGISTRY": "1.83.0", "WHO": WHO}
    saved = {k: getattr(M314, k) for k in consts}
    try:
        for k, v in consts.items():
            setattr(M314, k, v)
        doc = M314._step(build(), who=WHO, promotions=PROMOTIONS, attrib=ATTRIB, index=INDEX, old_cand=OLD_CAND,
                         cand=CAND, as_of=WHO, diff_span=DIFF_SPAN, promoted_in=f"{VERSION} ({WHO}, in the merge)",
                         supersedes_tail=None)
    finally:
        for k, v in saved.items():
            setattr(M314, k, v)
    doc["supersedes"] = doc["supersedes"] + ("; the package promoted in its own merge and every family's candidate "
                                             f"block moved to {CAND}")
    return doc


def text(doc):
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"


def problems(doc):
    for p in (ROOT / "research" / "agents_t479", ROOT / "research" / "agents_t485", ROOT / "research" / "agents_t483"):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
    import build_master_1_43_0 as B  # noqa: E402  (census problems of T-485, unchanged)
    return FMC.check(doc, root=ROOT, is_ancestor=FMC.git_is_ancestor) + B.census_problems(doc)


def main(argv):
    if "--check" in argv:
        cur = json.loads(NEW.read_text(encoding="utf-8"))
        promoted = not cur.get("pending_packages")
        doc = build_promoted() if promoted else build()
        ok = NEW.read_text(encoding="utf-8") == text(doc)
        bad = problems(cur)
        print(f"{VERSION} equals its builder ({'promoted' if promoted else 'pending'}):", ok, "| problems:", bad)
        return 0 if ok and not bad else 1
    doc = build_promoted() if "--promote" in argv else build()
    bad = problems(doc)
    for b in bad:
        print("PROBLEM", b)
    if "--write" in argv:
        NEW.write_text(text(doc), encoding="utf-8")
        print("written", NEW.relative_to(ROOT), f"({len(bad)} problem(s))")
    print(VERSION, "pending:", [x["task"] for x in doc.get("pending_packages") or []], "| candidate:",
          doc["candidate"]["method_version"], "| problems:", bad)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
