"""T-397: the integration-package summary of a finished v3033_run.py directory (engine ids, codes, units, quantities;
no coordinate, no name). Writes research/agents_t397/summary_t397.json (with --write) and prints it.

    python3 -I research/agents_t397/t397_summary.py <run dir>/v3033 [--write]

What it states (Gate B, WORKFLOW_CONTROLS s.1): per changed line before (V3.0.32 and released V2.9) and after; the
identity of every other line with V3.0.32 (count + sha); totals per code V3.0.32 -> V3.0.33 (valued, range, blank);
the structural concrete families of T-385 (CL-GF / CL-1F / GS-SLAB / BM-GF) before and after; the downstream lines of
the touched members (formwork, rebar, finishes that name the same element) and whether they moved (they must not).
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


def _r(x):
    return None if x is None else round(float(x), 6)


def main(argv):
    run = Path(argv[1])
    l32 = json.loads((run / "V3_0_32_BOQ_LINES.json").read_text(encoding="utf-8"))
    l33 = json.loads((run / "V3_0_33_BOQ_LINES.json").read_text(encoding="utf-8"))
    l32 = l32["lines"] if isinstance(l32, dict) else l32
    l33 = l33["lines"] if isinstance(l33, dict) else l33
    led = json.loads((run / "V3_0_33_INTEGRATION_LEDGER.json").read_text(encoding="utf-8"))
    rj = json.loads((run / "V3_0_33_RUN.json").read_text(encoding="utf-8"))
    diff = list(csv.DictReader((run / "V3_0_33_DIFF.csv").read_text(encoding="utf-8").splitlines()))
    b32 = {x["line_id"]: x for x in l32}
    rows = []
    for r in led["rows"]:
        rows.append({k: r[k] for k in ("action", "record_action", "line_id", "item_code", "floor", "unit",
                                       "before_released_v2_9", "before_v3_0_32", "before_held_range_v3_0_32",
                                       "after_v3_0_33", "after_held_range_v3_0_33", "evidence_status")})
        rows[-1]["verification"] = r["verification"].get("task")
    touched = {r["line_id"] for r in rows}
    elems = {(b32.get(t) or {}).get("location", {}).get("element_id") for t in touched} - {None}
    down = []
    for x in l33:
        if x["line_id"] in touched:
            continue
        txt = json.dumps(x.get("calculation") or {}) + json.dumps(x.get("location") or {})
        hit = [e for e in elems if e and e in txt]
        if hit:
            same = A30.line_sha(x) == A30.line_sha(b32[x["line_id"]])
            down.append({"line_id": x["line_id"], "item_code": x["item_code"], "unit": x["unit"],
                         "state": x["evidence_state"], "qty": _r(x.get("measured_net")),
                         "range": x.get("bounded_range") and [_r(x["bounded_range"]["low"]),
                                                              _r(x["bounded_range"]["high"])],
                         "names_touched_elements": len(hit), "byte_identical_to_v3_0_32": same})

    def fam(lines, code, floor=None):
        o = {"valued": 0.0, "valued_lines": 0, "range_low": 0.0, "range_high": 0.0, "range_lines": 0, "blank": 0}
        for x in lines:
            if x["item_code"] != code or (floor and x["location"].get("floor") != floor):
                continue
            if x["evidence_state"] == "BOUNDED_EXPOSURE":
                o["range_low"] += x["bounded_range"]["low"]
                o["range_high"] += x["bounded_range"]["high"]
                o["range_lines"] += 1
            elif x.get("measured_net") is not None and x["evidence_state"] in ("MEASURED", "SOURCE_DERIVED",
                                                                                "PROVISIONAL"):
                o["valued"] += x["measured_net"]
                o["valued_lines"] += 1
            elif x["evidence_state"] == "BLOCKED_RFI":
                o["blank"] += 1
        return {k: _r(v) if isinstance(v, float) else v for k, v in o.items()}

    fams = {}
    for name, code, fl in (("CL-GF", "STR.CONC.COLUMN", "GF"), ("CL-1F", "STR.CONC.COLUMN", "1F"),
                           ("GS", "STR.CONC.GROUND_SLAB", None), ("BM-GF", "STR.CONC.BEAM", "GF"),
                           ("LIFT", "STR.CONC.LIFT", None)):
        fams[name] = {"v3_0_32": fam(l32, code, fl), "v3_0_33": fam(l33, code, fl)}
    outside = [x for x in l33 if x["line_id"] not in touched]
    out = {"schema": "T397_SUMMARY_V1", "method": rj["method"], "extends": rj["extends"],
           "lines": {"v3_0_32": len(l32), "v3_0_33": len(l33)},
           "v3_0_32_lines_json_sha256": hashlib.sha256((run / "V3_0_32_BOQ_LINES.json").read_bytes()).hexdigest(),
           "v3_0_33_lines_json_sha256": hashlib.sha256((run / "V3_0_33_BOQ_LINES.json").read_bytes()).hexdigest(),
           "outside_rows": len(outside),
           "outside_rows_identical": sum(1 for x in outside if A30.line_sha(x) == A30.line_sha(b32[x["line_id"]])),
           "identity": {k: rj["identity"].get(k) for k in ("replaced", "added", "outside_rows_sha256", "corrections",
                                                            "diff")},
           "diff_vs_v3_0_32": {k: sum(1 for d in diff if d["vs_v3_0_32"] == k) for k in
                               sorted({d["vs_v3_0_32"] for d in diff})},
           "diff_vs_released_v2_9": {k: sum(1 for d in diff if d["vs_released_v2_9"] == k) for k in
                                     sorted({d["vs_released_v2_9"] for d in diff})},
           "totals_moved_by_code": rj["totals_moved_by_code"], "families": fams, "rows": rows,
           "downstream_naming_touched_elements": down,
           "piece_log": {k: v for k, v in rj["piece_logs"][0].items() if k != "sources"}}
    txt = json.dumps(out, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    if "--write" in argv:
        (Path(__file__).resolve().parent / "summary_t397.json").write_text(txt, encoding="utf-8")
    print(txt)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
