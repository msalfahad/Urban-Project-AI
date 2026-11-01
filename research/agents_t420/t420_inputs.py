"""T-420: the URBAN_V3037_INPUTS_V1 project inputs of ARCH_TAKEOFF_V3.0.37 (engine.source.arch_v3037), built ONLY from
Checker-merged files, each pinned by sha256 (an edited file stops the build). Every figure and id is READ from those
files; the owner ranges are READ from the merged FLOOR_BED_V1 module (owner Q-45 / Q-41, its own constants).

  research/agents_t414/ROOM_TABLE_T414.csv + summary.json   T-414 (MERGED 4f81eda1, Verifier 2026-11-01T05:25Z Gate A
      PASS on 3439b2b4): one row per candidate floor-finish line (53: 40 valued, 13 NOT_APPLICABLE), kind, layer, the
      finish line's state and net, the T-214 build-up b of the room's own zone, the owner Q-45 m3 range and the drawing
      bound;
  research/agents_t414/floor_bed_v1.py   the same merge: OWNER_BED (Q-45 ranges, rule text) read, not retyped;
  Checker finding F-C-T414-1 (the same verdict): the 1F dry UPPER bound takes the upper end of T-214's drawn range
      0.049 .. 0.051 -> b_upper 0.051 for zone 1F-DRY (the only zone the verdict corrects).

    python3 -I research/agents_t420/t420_inputs.py [project_id]      # prints the row count per action / kind
"""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TABLE = ROOT / "research/agents_t414/ROOM_TABLE_T414.csv"
SUMMARY = ROOT / "research/agents_t414/summary.json"
FBV1 = ROOT / "research/agents_t414/floor_bed_v1.py"
PINS = {TABLE: "7bc3752cd32e7e4a0858fbdbf849c704fd7701ab9abf305192ff30807ddc7baf",
        SUMMARY: "eadb730f221ee81fa4da40847ac06fe913266418b3746223c2b1a4110fbe6531"}
CHECKER_RUN = ("Verifier 2026-11-01T05:25Z session_01E6cPnc6Jh7Vm8mD5NE (Gate A PASS on 3439b2b4; finding F-C-T414-1: "
               "1F drawing bound b upper 0.051, total bound 0 .. 14.5143 m3)")
SOURCES = {
    "T-414": {"task": "T-414", "file": "research/agents_t414/ROOM_TABLE_T414.csv; research/agents_t414/summary.json",
              "sha256": f"{PINS[TABLE]}; {PINS[SUMMARY]}",
              "merge_commit": "4f81eda1faf6a0cf29caa9285dabbf31c39f0905", "checker_run": CHECKER_RUN},
}
B_UPPER = {"1F-DRY": {"b": 0.051, "source": "Checker F-C-T414-1 (T-214 verdict: 1F b 0.05 DRAWING-CONFIRMED with "
                                            "0.049 .. 0.051 between sources; an upper bound takes 0.051)"}}
ZONE = {"DRY": "{floor}-DRY", "WET": "{floor}-WET"}


def _rel(p):
    return str(p.relative_to(ROOT))


def _read(p):
    b = p.read_bytes()
    h = hashlib.sha256(b).hexdigest()
    if h != PINS[p]:
        raise SystemExit(f"{_rel(p)}: sha256 {h[:12]} is not the merged {PINS[p][:12]} (an edited ledger stops)")
    return b.decode("utf-8")


def _owner():
    spec = importlib.util.spec_from_file_location("t414_floor_bed_v1", FBV1)
    fb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fb)
    return {k: {"lo": v["lo"], "hi": v["hi"], "rule": v["rule"]} for k, v in fb.OWNER_BED.items()}


def _f(x):
    return None if x in (None, "") else float(x)


def build(project_id=None):
    rows_in = list(csv.DictReader(_read(TABLE).splitlines()))
    summ = json.loads(_read(SUMMARY))
    if summ.get("rows") != len(rows_in):
        raise SystemExit("ROOM_TABLE_T414.csv and summary.json disagree on the row count")
    rows = []
    for t in rows_in:
        na = t["m2_status"] == "NOT_APPLICABLE"
        e = {"item_code": t["finish_code"], "element_id": t["element_id"], "evidence_state": t["candidate_state"]}
        r = {"action": "NOT_APPLICABLE" if na else "BED", "finish_line": t["finish_line"], "kind": t["kind"],
             "space_kind": t["kind"], "layer": t["layer"], "floor": t["floor"],
             "zone": ZONE[t["kind"]].format(floor=t["floor"]), "expect": e, "membrane_in_room": t["membrane_in_room"],
             "source_tasks": ["T-414"]}
        if not na:
            e["measured_net"] = _f(t["area_m2"])
            r["area_status"] = t["m2_status"]
            r["ledger"] = {"m3_owner_low": _f(t["m3_owner_low"]), "m3_owner_high": _f(t["m3_owner_high"]),
                           "b": _f(t["build_up_b"]), "m3_drawing_high": _f(t["m3_drawing_high"]),
                           "drawing_status": t["m3_drawing_status"], "owner_check": t["owner_check"]}
        rows.append(r)
    return {"schema": "URBAN_V3037_INPUTS_V1", "project_id": project_id, "sources": list(SOURCES.values()),
            "owner": _owner(), "b_upper": B_UPPER, "rows": rows}


def main(argv):
    doc = build(argv[0] if argv else None)
    c = {}
    for r in doc["rows"]:
        k = f"{r['action']}|{r['kind']}"
        c[k] = c.get(k, 0) + 1
    print(json.dumps({"rows": len(doc["rows"]), "by_action_kind": c, "owner": doc["owner"], "b_upper": doc["b_upper"]},
                     indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
