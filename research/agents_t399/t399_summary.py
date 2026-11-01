"""T-399: the integration-package summary of a finished v3034_run.py directory (engine ids, codes, units, quantities;
no coordinate, no name). Writes research/agents_t399/summary_t399.json (with --write) and prints it.

    python3 -I research/agents_t399/t399_summary.py <run dir>/v3034 [--write]

What it states (Gate B, WORKFLOW_CONTROLS s.1): the zone binding per room (carrier, backing and paint lines with their
V3.0.33 / V3.0.34 state and figure); the changed line before (V3.0.33 and released V2.9) and after; the identity of
every other line with V3.0.33 (count + sha); totals per code V3.0.33 -> V3.0.34; every line of the three zone rooms
(wall finishes) before and after, so the 'no second quantity, no plaster / paint on a zone face' claim is checkable.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v30 as A30  # noqa: E402

ROOMS = ("GF-RA3AD49", "1F-R26FA0D", "GF-RC06FED")
CODES = ("FIN.WALL.TILE", "FIN.PLASTER", "FIN.PAINT")


def _r(x):
    return None if x is None else round(float(x), 6)


def _lines(p):
    d = json.loads(p.read_text(encoding="utf-8"))
    return d["lines"] if isinstance(d, dict) else d


def main(argv):
    run = Path(argv[1])
    l33, l34 = _lines(run / "V3_0_33_BOQ_LINES.json"), _lines(run / "V3_0_34_BOQ_LINES.json")
    led = json.loads((run / "V3_0_34_INTEGRATION_LEDGER.json").read_text(encoding="utf-8"))
    rj = json.loads((run / "V3_0_34_RUN.json").read_text(encoding="utf-8"))
    diff = list(csv.DictReader((run / "V3_0_34_DIFF.csv").read_text(encoding="utf-8").splitlines()))
    b33 = {x["line_id"]: x for x in l33}
    zones, rows = [], []
    for r in led["rows"]:
        if r["action"] == "ZONE_COVERED":
            zones.append({k: r.get(k) for k in ("room", "code", "engine_room", "floor", "zone", "faces",
                                                 "carrier_line", "carrier_state", "zone_m2_on_carrier",
                                                 "table_net_m2", "residual", "held_item", "backing_line",
                                                 "backing_m2", "paint_lines", "b4_02_lines_added",
                                                 "double_count_m2", "evidence_status")})
        else:
            rows.append({k: r.get(k) for k in ("action", "line_id", "item_code", "floor", "engine_room", "unit",
                                                "before_released_v2_9", "before_v3_0_33", "after_v3_0_34",
                                                "evidence_status")})
            rows[-1]["verification"] = r["verification"].get("task")
    touched = {r["line_id"] for r in rows}
    room_lines = []
    for x in l34:
        if (x.get("location") or {}).get("room_id") in ROOMS and x["item_code"] in CODES:
            o = b33[x["line_id"]]
            room_lines.append({"line_id": x["line_id"], "item_code": x["item_code"],
                               "room": x["location"]["room_id"], "element": x["location"].get("element_id"),
                               "v3_0_33": [o["evidence_state"], _r(o.get("measured_net"))],
                               "v3_0_34": [x["evidence_state"], _r(x.get("measured_net"))],
                               "byte_identical": A30.line_sha(o) == A30.line_sha(x)})
    outside = [x for x in l34 if x["line_id"] not in touched]
    out = {"schema": "T399_SUMMARY_V1", "method": rj["method"], "extends": rj["extends"],
           "lines": {"v3_0_33": len(l33), "v3_0_34": len(l34)},
           "v3_0_33_lines_json_sha256": hashlib.sha256((run / "V3_0_33_BOQ_LINES.json").read_bytes()).hexdigest(),
           "v3_0_34_lines_json_sha256": hashlib.sha256((run / "V3_0_34_BOQ_LINES.json").read_bytes()).hexdigest(),
           "v3_0_34_lines_csv_sha256": hashlib.sha256((run / "V3_0_34_BOQ_LINES.csv").read_bytes()).hexdigest(),
           "v3_0_34_diff_sha256": hashlib.sha256((run / "V3_0_34_DIFF.csv").read_bytes()).hexdigest(),
           "outside_rows": len(outside),
           "outside_rows_identical": sum(1 for x in outside if A30.line_sha(x) == A30.line_sha(b33[x["line_id"]])),
           "identity": {k: rj["identity"].get(k) for k in ("replaced", "added", "outside_rows_sha256", "tile_zones",
                                                            "zones_covered", "diff")},
           "diff_vs_v3_0_33": {k: sum(1 for d in diff if d["vs_v3_0_33"] == k) for k in
                               sorted({d["vs_v3_0_33"] for d in diff})},
           "diff_vs_released_v2_9": {k: sum(1 for d in diff if d["vs_released_v2_9"] == k) for k in
                                     sorted({d["vs_released_v2_9"] for d in diff})},
           "totals_moved_by_code": rj["totals_moved_by_code"], "zones": zones, "rows": rows,
           "zone_room_wall_finish_lines": room_lines,
           "piece_log": {k: v for k, v in rj["piece_logs"][0].items() if k != "sources"}}
    txt = json.dumps(out, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    if "--write" in argv:
        (Path(__file__).resolve().parent / "summary_t399.json").write_text(txt, encoding="utf-8")
    print(txt)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
