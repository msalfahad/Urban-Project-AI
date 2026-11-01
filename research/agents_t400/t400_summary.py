"""T-400: summary_t400.json from a finished v3035_run.py output directory (values, engine ids, states and hashes only:
no coordinate, no name). `--check` compares the committed summary with a fresh one.

    python3 -I research/agents_t400/t400_summary.py <private>/t400/v3035 [--check]
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "summary_t400.json"
REC = "boundary_fence_v3035"


def _sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def build(d):
    d = Path(d)
    l34 = json.loads((d / "V3_0_34_BOQ_LINES.json").read_text(encoding="utf-8"))
    l35 = json.loads((d / "V3_0_35_BOQ_LINES.json").read_text(encoding="utf-8"))
    run = json.loads((d / "V3_0_35_RUN.json").read_text(encoding="utf-8"))
    b34 = {x["line_id"]: x for x in l34}
    added, changed = [], []
    for x in l35:
        r = ((x.get("calculation") or {}).get("inputs") or {}).get(REC)
        if not r:
            continue
        row = {"line_id": x["line_id"], "item_code": x["item_code"], "element_id": x["location"]["element_id"],
               "unit": x["unit"], "state": x["evidence_state"], "quantity": x.get("measured_net"),
               "range": x.get("bounded_range") and [x["bounded_range"].get("low"), x["bounded_range"].get("high")],
               "evidence_status": r.get("evidence_status"), "beside": r.get("beside"), "terms": r.get("terms"),
               "tasks": r.get("tasks")}
        (changed if x["line_id"] in b34 else added).append(row)
    ident = run["identity"]
    return {"schema": "URBAN_T400_SUMMARY_V1", "method": run["method"], "extends": run["extends"],
            "files_sha256": {n: _sha(d / n) for n in ("V3_0_34_BOQ_LINES.json", "V3_0_34_BOQ_LINES.csv",
                                                       "V3_0_35_BOQ_LINES.json", "V3_0_35_BOQ_LINES.csv",
                                                       "V3_0_35_DIFF.csv", "V3_0_35_INTEGRATION_LEDGER.csv")},
            "identity": {k: ident[k] for k in ("v3_0_34_lines", "v3_0_35_lines", "replaced", "added", "outside_rows",
                                               "outside_rows_identical_to_v3_0_34", "fence", "bound", "diff",
                                               "outside_rows_sha256")},
            "added": added, "restated": changed, "totals_moved_by_code": run["totals_moved_by_code"],
            "waiting": sorted(run["waiting_pieces"])}


def text(doc):
    return json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True) + "\n"


def main(argv):
    doc = build(argv[1])
    if "--check" in argv:
        ok = OUT.read_text(encoding="utf-8") == text(doc)
        print("summary_t400.json reproduces:", ok)
        return 0 if ok else 1
    OUT.write_text(text(doc), encoding="utf-8")
    print("written", OUT.name)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
