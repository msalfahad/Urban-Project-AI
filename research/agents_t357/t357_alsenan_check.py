"""T-357 Alsenan check (committed inputs only: ALSENAN_GROUND_INPUT.json, values / handles / pages; no coordinates).

Writes LEVEL_REGISTER_T357.csv, SHEET_SEARCH_T357.csv, EG_COEFFICIENTS_T357.csv and summary.json next to this file
when run as a script; main(write=False) returns the rows and the summary for the tests."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ground_reference_v1 as G  # noqa: E402

INPUT = HERE / "ALSENAN_GROUND_INPUT.json"


def main(write: bool = True):
    inp = json.loads(INPUT.read_text(encoding="utf-8"))
    corners = list(inp["plot"]["corners"])
    eg = G.existing_ground_reference(inp["level_marks"], corners)
    area = G.polygon_area(inp["plot"]["polygon_local_m"], inp["unit"])
    sides_ok = all(abs(s["printed_m"] - s["dxf_length_m"]) < 0.005 for s in inp["plot"]["sides"])
    cov = G.check_coverage_percentages(area, inp["coverage_rows"])
    sheets = [s["sheet"] for s in inp["sheet_search"]]
    clr = G.clearance_scope(inp["sheet_search"], sheets)
    coefs = G.eg_shift_coefficients(inp["eg_components"])
    gf = inp["storey_areas_printed"]["GF"]["area_m2"]
    summary = {
        "existing_ground": {"status": eg["status"], "value_m": eg["value_m"], "per_corner": eg["per_corner"],
                            "refs_n": len(eg["refs"]), "reasons": eg["reasons"]},
        "plot": {"area_m2": round(area, 4), "sides_printed_equal_dxf": sides_ok, "status": "DERIVED",
                 "basis": "15.00 x 31.37 printed side lengths; DXF boundary lines agree; plot area itself not printed"},
        "coverage_check": cov,
        "storeys_printed_m2": {k: v["area_m2"] for k, v in inp["storey_areas_printed"].items() if isinstance(v, dict)},
        "plot_minus_gf_printed_m2": round(area - gf, 4),
        "clearance": clr,
        "eg_coefficients": coefs,
        "counts": {"level_marks": len(inp["level_marks"]), "sheets_searched": len(sheets)},
    }
    rows = []
    for mk in inp["level_marks"]:
        rows.append({"kind": mk["kind"], "value_m": "" if mk["value"] is None else mk["value"], "sheet": mk["sheet"],
                     "handle": mk["handle"], "corner": mk.get("corner") or "", "labels": mk["labels"]})
    if write:
        with open(HERE / "LEVEL_REGISTER_T357.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        with open(HERE / "SHEET_SEARCH_T357.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["sheet", "searched", "clearance_notes", "ground_level_values", "what"])
            for s in inp["sheet_search"]:
                w.writerow([s["sheet"], s["searched"], ";".join(s["clearance_notes"]) or "absent",
                            ";".join(s["ground_level_values"]), s["what"]])
        with open(HERE / "EG_COEFFICIENTS_T357.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(coefs[0]))
            w.writeheader()
            for c in coefs:
                w.writerow({k: ("" if v is None else v) for k, v in c.items()})
        (HERE / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return rows, summary


if __name__ == "__main__":
    _, s = main()
    print(json.dumps({k: s[k] for k in ("existing_ground", "plot", "plot_minus_gf_printed_m2")}, indent=1))
    print(s["coverage_check"]["status"], s["clearance"]["status"])
    for c in s["eg_coefficients"]:
        print(c["coef_m3_per_m"], c["id"])
