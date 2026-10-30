"""T-365 Alsenan check (committed inputs only: ALSENAN_JOINTS_INPUT.json; sheet / note numbers, handles, pattern names).
Writes SHEET_SEARCH_T365.csv, JOINTS_T365.csv, HATCHES_T365.csv, FREELANCER_T365.csv and summary.json next to this file
when run as a script; main(write=False) returns the results for the tests."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import joints_scope_v1 as R  # noqa: E402

INPUT = HERE / "ALSENAN_JOINTS_INPUT.json"


def main(write: bool = True):
    inp = json.loads(INPUT.read_text(encoding="utf-8"))
    ev = R.evaluate_all(inp["joints"])
    by_id = {j["id"]: j for j in inp["joints"]}
    joint_rows = [{"id": r["id"], "kind": r["kind"], "status": r["status"],
                   "length_m": r["length_m"], "sealant_m": r["sealant_m"],
                   "owner_trade": r["trade"], "v3_0_26_line": r["line"],
                   "owner_rule": (by_id[r["id"]].get("owner_rule") or {}).get("id", ""),
                   "evidence": by_id[r["id"]]["evidence"]} for r in ev["rows"]]
    hatch_rows = []
    for f, d in inp["hatches"].items():
        for h in d["modelspace_non_solid"]:
            c = R.classify_hatch(h)
            hatch_rows.append({"file": f, "handle": h["handle"], "layer": h["layer"], "pattern": h["pattern"],
                               "class": c["class"]})
    sheet_rows = [{"sheet": s["sheet"], "read": s["read"], "joints_printed": len(s["joints"]), "found": s["found"]}
                  for s in inp["sheet_search"]]
    fl = inp["freelancer"]["rows"]
    fl_rows = [{"file": r["file"], "row": r["row"], "item": r["item"], "physical_m": r["physical_m"],
                "payable_m": r["payable_m"], "class": r["class"],
                "verdict_proposal": "RULE_DIFFERENCE (scope): a plaster-accessory row (corners, grooves, arrises) of the "
                                    "external plaster trade, not a movement joint; B13-05 double count 0; 1,297.35 m "
                                    "physical = 648.675 m at the doubled rate (ERS s.3), never 648.675 m of joint"}
               for r in fl]
    summary = {
        "rule": R.RULE_ID,
        "sheets_searched": len(sheet_rows),
        "sheets_printing_a_joint": sum(1 for s in inp["sheet_search"] if s["joints"]),
        "dxf_text_records": {k: v["records"] for k, v in inp["dxf_text_census"].items() if isinstance(v, dict)},
        "dxf_text_joint_hits": {k: len(v["hits"]) for k, v in inp["dxf_text_census"].items() if isinstance(v, dict)},
        "dxf_false_positives": sum(len(h["handles"]) for v in inp["dxf_text_census"].values() if isinstance(v, dict)
                                   for h in v["hits"] if h["class"] == "FALSE_POSITIVE"),
        "hatches_not_joint": len(hatch_rows),
        "twin_columns_gap_1_100_mm": inp["twin_column_check"]["pairs_gap_1_to_100_mm"],
        "by_status": ev["by_status"],
        "measured_total_m": ev["measured_total_m"],
        "rfi_candidates": ev["rfi"],
        "joints": joint_rows,
        "double_count": {"segments_checked": 0, "result": "0 (no joint measured; B13-02 paving and B13-01 roof build-up have "
                                                          "no line in V3.0.26; FIN.WP.ROOF m2 neither reduced nor added)"},
        "freelancer": fl_rows,
        "engine": inp["engine"],
        "verdict_proposal": "NO_QUANTITY_BOTH: neither BOQ carries a B13-05 joint and the drawings print none; the two "
                            "owner-scoped joints (roof field, outside tile field: Q-42 width 3 mm) are HELD on the Q-42 "
                            "residual (spacing / own line), never 0; the freelancer's only 'joints' row is plaster "
                            "(RULE_DIFFERENCE, scope)",
    }
    if write:
        def w(name, rows):
            with open(HERE / name, "w", newline="", encoding="utf-8") as fh:
                wr = csv.DictWriter(fh, fieldnames=list(rows[0]))
                wr.writeheader()
                wr.writerows(rows)
        w("SHEET_SEARCH_T365.csv", sheet_rows)
        w("JOINTS_T365.csv", joint_rows)
        w("HATCHES_T365.csv", hatch_rows)
        w("FREELANCER_T365.csv", fl_rows)
        (HERE / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"sheets": sheet_rows, "joints": joint_rows, "hatches": hatch_rows, "freelancer": fl_rows, "summary": summary}


if __name__ == "__main__":
    s = main()["summary"]
    print(json.dumps({k: s[k] for k in ("sheets_searched", "sheets_printing_a_joint", "dxf_text_joint_hits",
                                        "hatches_not_joint", "by_status", "measured_total_m", "rfi_candidates")},
                     indent=1))
