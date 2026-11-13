"""T-770: build rules/coverage/BOQ_FAMILY_MASTER_1.81.0.json = 1.80.0 (never edited; T-314 promoted, candidate of
record ARCH_TAKEOFF_V3.0.79, no pending package) + the ARCH_TAKEOFF_V3.0.81 package (T-770, FILL_WIRE_V1,
R-T770-1 / R-T770-2; tools/family_master_candidate.py rule r3) + the one NEW item code it adds, STR.CONC.SAFETY (the
owner-materiality safety line, R-T770-2 g), owned by B9-02 (lintels: 9 of the 13 ignored pieces, 0.339 of 0.428 m3;
ownership of a cross-family allowance line is the Lead's element-register call, recorded in the family note).

Two modes, ONE version number (r3, Verifier FAULT 1 on r2 / R-T485-1 / the ADOPTED lesson: a merged integration package
leaves the registry promoted in the same merge), on the T-314 r4 pattern (research/agents_t314/build_master_1_80_0.py:
its _step / _promote, i.e. the T-483 r2 promotion functions, unchanged, with this version's constants):

  --write             PENDING: V3.0.81 pending (the task branch, as handed in for Gate B).
  --promote [--write] PROMOTED (run by the Verifier IN the merge, after
                      research/agents_t770/t770_promotions_source.py has written out/PROMOTIONS_SOURCE_1_81_0.json and
                      research/agents_t770/t770_package_families.py, on the Verifier's own Drive chain run, has written
                      out/T770_PACKAGE_FAMILIES.json): families re-derived at V3.0.81 from the census
                      out/LINE_INDEX_V3_0_81.json; then research/agents_t770/write_manifest.py.
  --check             the committed file equals the builder in the mode it was written in; 0 problems.

No quantity, capability, owner or line change with this file; the released default is untouched.

    bash scripts/agent_env.sh run --tree task-T-770 research/agents_t770/build_master_1_81_0.py [--write | --promote --write | --check]
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

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.80.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.81.0.json"
VERSION = "1.81.0"
TASK_COMMIT = "c24bf648bf6cc958414f5b183f19a4a8ce10ce62"     # the commit that added engine/source/arch_v3081.py
CODES = ["FIN.FLOOR.BED.DRY", "FIN.FLOOR.BED.WET", "FIN.PAINT", "FIN.PLASTER", "FIN.ROOF.FINISH", "FIN.ROOF.INSULATION",
         "FIN.ROOF.PROTECTION", "FIN.ROOF.SCREED", "FIN.WP.ROOF", "STR.CONC.BEAM", "STR.CONC.BLINDING",
         "STR.CONC.BOUNDARY_PAD", "STR.CONC.COLUMN", "STR.CONC.DOME", "STR.CONC.GROUND_BEAM", "STR.CONC.LIFT",
         "STR.CONC.LINTEL", "STR.CONC.NECK", "STR.CONC.PARAPET", "STR.CONC.POOL", "STR.CONC.SAFETY", "STR.CONC.STAIR",
         "STR.FORMWORK", "STR.FORMWORK.STAIR"]
PENDING = {"task": "T-770", "method_version": "ARCH_TAKEOFF_V3.0.81", "module": "engine/source/arch_v3081.py",
           "status": FMC.PENDING_STATUS, "integrates": ["T-762", "T-761"], "tests": ["tests/t770_fill_wire"],
           "changes_families_by_item_code": CODES,
           "note": "T-770 r2 (DELIVERY MODE wiring, research/agents_t770/v3081_index.py) on the V3.0.79 candidate (T-314): "
                   "three Checker-verified family groups by line id with labels and bases: MAIN_FILL_ALL less its 126 "
                   "formwork rows (T-762 Gate A double count CONFIRMED) and its disposal row (T-764 verified figure "
                   "wires with T-764) = 81 rows; T-762 formwork 336 rows, 33 cover deductions netted into their hosts "
                   "(R-T770-2 f); T-761 concrete 80 rows, 13 known pieces < 0.05 m3 IGNORED_SMALL under ONE added "
                   "STR.CONC.SAFETY 1 m3 line (R-T770-2 g); non-measured figures PROVISIONAL, never VERIFIED; every "
                   "other line byte-identical; blank non-rebar lines 691 -> 295",
           "task_commit": TASK_COMMIT}


HERE = Path(__file__).resolve().parent
PROMOTIONS = HERE / "out/PROMOTIONS_SOURCE_1_81_0.json"
ATTRIB = HERE / "out/T770_PACKAGE_FAMILIES.json"
INDEX = HERE / "out/LINE_INDEX_V3_0_81.json"
OLD_CAND, CAND, WHO = "ARCH_TAKEOFF_V3.0.79", "ARCH_TAKEOFF_V3.0.81", "T-770"
DIFF_SPAN = "V3.0.79 .. V3.0.81"
NEW_CODES = {"B9-02": ["STR.CONC.SAFETY"]}
NEW_CODE_NOTE = ("1.81.0 (T-770): owns the NEW item code STR.CONC.SAFETY = ONE concrete safety line (owner materiality "
                 "2026-11-13: known pieces < 0.05 m3 ignored by line id, safety = 1 m3 if their sum < 1 m3, else the "
                 "sum; label SAFETY, PROVISIONAL, never VERIFIED); placed here because 9 of its 13 ignored pieces "
                 "(0.339 of 0.428 m3) are lintels, the rest beams 2 / ground beams 2; the Lead may move it by a "
                 "registry version (element register ownership)")


def build():
    """PENDING 1.81.0 (task branch)."""
    old = json.loads(OLD.read_text(encoding="utf-8"))
    if old.get("version") != "1.80.0" or old.get("pending_packages"):
        raise SystemExit(f"base registry {old.get('version')} is not a promoted 1.80.0 (pending "
                         f"{[p.get('task') for p in old.get('pending_packages') or []]})")
    if old["candidate"]["method_version"] != OLD_CAND:
        raise SystemExit(f"1.80.0 candidate of record {old['candidate']['method_version']}, expected {OLD_CAND}")
    new = copy.deepcopy(old)
    new["version"] = VERSION
    new["supersedes"] = ("1.80.0 (kept unchanged on disk; every field copied unchanged) + the pending "
                         "ARCH_TAKEOFF_V3.0.81 package (T-770) + B9-02 owns the new item code STR.CONC.SAFETY")
    new["source"] = old["source"] + (" | 1.81.0 (T-770): 1.80.0 + pending ARCH_TAKEOFF_V3.0.81 (rule r3 of "
                                     "tools/family_master_candidate.py, FILL_WIRE_V1) handed in for Gate B, promoted "
                                     "in the merge by --promote; new item code STR.CONC.SAFETY (B9-02); no quantity, "
                                     "capability or owner change")
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
    """the T-770 promotion in its own merge, on the pending 1.81.0: the T-314 r4 step (T-483 r2 functions unchanged)
    with this version's module constants, restored afterwards."""
    for p in (ROOT / "research" / "agents_t314", ROOT / "research" / "agents_t479", ROOT / "research" / "agents_t485",
              ROOT / "research" / "agents_t483"):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
    import build_master_1_80_0 as M314  # noqa: E402
    consts = {"VERSION": VERSION, "FROM_REGISTRY": "1.80.0", "WHO": WHO}
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
