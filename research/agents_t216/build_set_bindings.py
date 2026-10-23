"""T-216: the development villa's review-set binding file (URBAN_SCORER_SET_BINDINGS_V1) for the scorer's opt-in
`tools/alsenan_keymap.py --set-bindings`. Built only from committed, checker-merged files:

- research/agents_t208/ALSENAN_T208_INPUT.json (the 3 REVIEW_CLASSIFICATION sets and room records of the pinned
  released run V29_ROUTEG_NO_PROFILE, BOQ_LINES.csv b96185d4) + T208_BOUNDARY_CONFIRMATIONS.json;
- research/agents_t208/review_sets.py bind_run (REVIEW_SET_BINDING_V1, rule Q-06 A);
- the T-208 checker verdict (MERGED 54cb4c42, verifier 2026-10-23 11:08 UTC): class ASSUMED — OWNER-APPROVED right
  for all three (Q-06 names exactly these three, 9.348 m2); areas GF-R8496F0 3.1325 and GF-RD36087 1.485 re-measured
  0.0 % (VERIFIED), GF-RDBD4F9 4.7307 DRAWING-CONFIRMED (worker reading, not re-measured).

    python3 -I research/agents_t216/build_set_bindings.py           # write ALSENAN_SET_BINDINGS_T216.json
    python3 -I research/agents_t216/build_set_bindings.py --check   # exit 1 when the committed file differs

The evidence texts below are this project's data (printed sizes and fixture block names, no coordinates, no names);
the scorer only checks that they are present and that the bound quantities are the run's own scenario.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
T208 = ROOT / "research" / "agents_t208"
sys.path.insert(0, str(T208))

import review_sets as RS                                                # noqa: E402

OUT = HERE / "ALSENAN_SET_BINDINGS_T216.json"
KEY = "FLOOR.INTERNAL"
VERDICT = {"commit": "54cb4c42",
           "source": "BOARD.md T-208 MERGED 54cb4c42 (verifier 2026-10-23 11:08 UTC, Gate A): Q-06 names exactly these "
                     "three spaces (9.348 m2), class ASSUMED - OWNER-APPROVED right"}
# per subject: printed size (T-208 report s.1 table; checker re-measure where one exists) and geometry status
EVIDENCE = {
    "GF-R8496F0": ("printed 1.50 x 2.10 less the drawn column notch 0.35 x 0.05 = 3.1325 m2 (checker: printed DIM 1500 "
                   "x 2100 less the S-COL overlay 0.350 x 0.050, 0.0 %)", "VERIFIED (checker re-measure, T-208 verdict)"),
    "GF-RD36087": ("printed 1.10 x 1.35 = 1.485 m2 (checker: drawn faces 1.350 x 1.100, 0.0 %)",
                   "VERIFIED (checker re-measure, T-208 verdict)"),
    "GF-RDBD4F9": ("open side 0.7943 + 1.2557 = 2.050 = printed 205; arm 1.870 / sqrt 2 = 1.322 = printed 132; area "
                   "4.7307 m2 from the drawn wall faces (boundary confirmation T208_BOUNDARY_CONFIRMATIONS.json)",
                   "DRAWING-CONFIRMED (worker reading; not re-measured by the checker)"),
}


def build():
    inp = json.loads((T208 / "ALSENAN_T208_INPUT.json").read_text(encoding="utf-8"))
    conf = json.loads((T208 / "T208_BOUNDARY_CONFIRMATIONS.json").read_text(encoding="utf-8"))["confirmations"]
    rr = {"categories": {"CONDITIONAL": {"scenario_sets": inp["conditional_sets"]}}}
    doc = RS.bind_run(rr, inp["rooms"], RS.ANSWERED_RULES, conf)
    rooms = {r["room_id"]: r for r in inp["rooms"]}
    sets = []
    for b in doc["bindings"]:
        if b["status"] != RS.ASSUMED:
            raise SystemExit(f"{b['set_id']}: not bound ({b['reason']})")
        blocks = [f"{f['block']} ({f['fixture']})" for f in rooms[b["subject"]]["evidence"]["fixtures"]]
        size, geo = EVIDENCE[b["subject"]]
        sets.append({"set_id": b["set_id"], "subject": b["subject"], "kind": RS.REVIEW_KIND, "status": b["status"],
                     "scenario": b["scenario"], "rule_id": b["rule_id"], "quantities": b["quantities"],
                     "closure_strip": None if not b["closure_strip"] else {"item": b["closure_strip"]["item"],
                                                                           "m2": b["closure_strip"]["m2"]},
                     "door_closures": b["profile"]["door_closures"],
                     "boundary_confirmation": None if not b.get("boundary_confirmation") else
                     "T208_BOUNDARY_CONFIRMATIONS.json: " + b["boundary_confirmation"]["condition"],
                     "evidence": {"fixture_symbol": ", ".join(blocks), "printed_size": size},
                     "geometry_status": geo, "verdict": dict(VERDICT)})
    return {"SCHEMA": "URBAN_SCORER_SET_BINDINGS_V1", "task": "T-216",
            "scope": "development villa only (project fact file); set ids are the pinned released run's "
                     "(V29_ROUTEG_NO_PROFILE, BOQ_LINES.csv b96185d4); the V3.0.x candidates are scored beside that "
                     "run's release report, so the same sets apply",
            "binding_method": doc["method"], "keys": [KEY],
            "approved_rules": {r["rule_id"]: r["source"] for r in RS.ANSWERED_RULES},
            "closure_strip_items": [RS.STRIP_ITEM], "sets": sets}


def text():
    return json.dumps(build(), ensure_ascii=False, indent=1, sort_keys=True) + "\n"


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    t = text()
    if "--check" in argv:
        ok = OUT.exists() and OUT.read_text(encoding="utf-8") == t
        print("T-216 binding file:", "reproduces" if ok else "DIFFERS")
        return 0 if ok else 1
    OUT.write_text(t, encoding="utf-8")
    print(t)
    return 0


if __name__ == "__main__":
    sys.exit(main())
