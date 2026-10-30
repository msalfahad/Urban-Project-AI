"""T-354 Alsenan check (committed inputs only: ALSENAN_SOIL_TREATMENT_INPUT.json; sheet / note numbers and handles).

Writes SHEET_SEARCH_T354.csv, RELATED_LAYERS_T354.csv and summary.json next to this file when run as a script;
main(write=False) returns the rows and the summary for the tests."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import soil_treatment_v1 as S  # noqa: E402

INPUT = HERE / "ALSENAN_SOIL_TREATMENT_INPUT.json"


def main(write: bool = True):
    inp = json.loads(INPUT.read_text(encoding="utf-8"))
    scope = S.scope_status(inp["sheet_search"], inp["set_sheets"], sources=())
    per_discipline = {}
    for r in inp["sheet_search"]:
        d = r["sheet"].split()[0]
        per_discipline.setdefault(d, {"sheets": 0, "requires": 0})
        per_discipline[d]["sheets"] += 1
        per_discipline[d]["requires"] += len(r["requires"])
    hits = inp["dxf_text_census"]["hits"]
    summary = {
        "rule": S.RULE_ID,
        "b1_05_scope": scope,
        "sheets": per_discipline,
        "dxf_records": inp["dxf_text_census"]["records"],
        "dxf_hits_by_class": {c: sum(1 for h in hits if h["class"] == c) for c in sorted({h["class"] for h in hits})},
        "related_layers_not_soil_treatment": len(inp["related_printed_layers"]),
        "specification_issued": False,
        "freelancer_row": None,
        "engine_line": None,
        "quantity_m2": None,
        "zones_if_required": [z["zone"] for z in inp["zones_if_required"]],
        "verdict_proposal": "NOT_IN_DRAWN_SCOPE: missing from both BOQs is correct for this set; no difference to "
                            "reconcile (engine 0 lines, freelancer 0 rows, drawings require none)",
    }
    sheet_rows = [{"sheet": r["sheet"], "searched": r["searched"],
                   "soil_treatment": "required (" + ", ".join(r["requires"]) + ")" if r["requires"] else "absent",
                   "read": r["read"], "notes_read": r["notes_read"]} for r in inp["sheet_search"]]
    if write:
        with open(HERE / "SHEET_SEARCH_T354.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(sheet_rows[0]))
            w.writeheader()
            w.writerows(sheet_rows)
        with open(HERE / "RELATED_LAYERS_T354.csv", "w", newline="", encoding="utf-8") as f:
            rows = inp["related_printed_layers"]
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        (HERE / "summary.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    return sheet_rows, summary


if __name__ == "__main__":
    rows, summ = main()
    print(json.dumps({"status": summ["b1_05_scope"]["status"], "sheets": summ["sheets"]}, indent=1))
