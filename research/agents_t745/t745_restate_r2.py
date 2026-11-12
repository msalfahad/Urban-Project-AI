"""T-745 r2: restate the development-villa census under DRAIN_RUN_CENSUS_T745_V2 (length basis by the sheet notes,
rule R-T380-1). Nothing in the engine is written; no BOQ line.

Input: out/T745_ALSENAN_RUNS_V1_REJECTED.json, the r1 census (run ids, systems, diameters, scaled lm; no coordinates)
whose drawn lengths the Checker reproduced (verdict 2026-11-12T20:25Z: collector 25.540, GCO branch 8.258, 1F P 4in
6.054 m). The r1 private reading (page points) was not retained between runs, so the r2 output is restated from the
committed r1 records; t745_alsenan.py applies the same basis directly when run with a reading that carries
'sheet_notes'. Output: out/T745_ALSENAN_RUNS.json.

Usage (checkout root): python3 -I research/agents_t745/t745_restate_r2.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import t745_runs as R  # noqa: E402

# The NOTES box of each sheet, transcribed by eye in this run (the sheet text is outlined vectors, no text layer;
# rendered at 300 dpi). Drive 'Alsenan chalet project' / sanitary-7757.pdf p.1 GF, p.2 1F, p.3 2F: the same note.
SHEET_NOTES = {
    "GF": "NOTES:- THE BUILDER TO WORK WITH STATED DIMENSIONS NOT TO SCALE DRAWING.",
    "1F": "NOTES:- THE BUILDER TO WORK WITH STATED DIMENSIONS NOT TO SCALE DRAWING.",
    "2F": "NOTES:- THE BUILDER TO WORK WITH STATED DIMENSIONS NOT TO SCALE DRAWING.",
}
# Printed pipe dimensions found on the sheets: none (the only printed lengths are the plot sides 31.37 / 15.00 m,
# used by r1 for the scale). So no run has a stated length.
STATED_M: dict = {}

# 1F-M03 (label 'P 4in B.T.T.S.') is ONE drawn segment of 6.054 m; the WC branch (0.508 m drawn) tees into it 5.587 m
# from its upper end, so 0.467 m of the segment lies past the tee. The label is read over the whole segment by
# continuity of the one drawn line (r1); this run measured the split on the vector pens.
LABEL_NOTES = {
    "1F-M03": "P 4in label read over the whole drawn segment 6.054 m (scaled info): 5.587 m to the WC tee + 0.467 m "
              "past the tee; the 4in applies to the part past the tee only by continuity of the one drawn line",
}


def restate(v1, notes=SHEET_NOTES, stated=STATED_M):
    basis = {floor: R.sheet_basis(notes.get(floor)) for floor in v1["sheet_scale"]}
    recs = []
    for r in v1["runs"]:
        b = basis[r["floor"]]
        rec = {"run_id": r["run_id"], "floor": r["floor"], "system": r["system"], "diameter_in": r["diameter_in"],
               "pen": r["pen"], "segments": r["segments"], "bridged_gaps": r["bridged_gaps"]}
        if r["status"] == "SYMBOL_MARK":
            rec.update(status="SYMBOL_MARK", lm=None, scaled_info_lm=r["lm"], symbol_mark=True)
        else:
            run = R.Run(run_id=r["run_id"], floor=r["floor"], pen=r["pen"], segments=[], system=r["system"],
                        diameter_in=r["diameter_in"], stated_m=stated.get(r["run_id"]))
            st = R.run_status(run, b)
            if st == R.HELD_SCHEMATIC:
                rec.update(status=st, lm=None, scaled_info_lm=r["lm"], symbol_mark=False)
            elif run.stated_m is not None:
                rec.update(status=st, lm=run.stated_m, scaled_info_lm=None, symbol_mark=False)
            else:
                rec.update(status=st, lm=r["lm"], scaled_info_lm=None, symbol_mark=False)
        if r["run_id"] in LABEL_NOTES:
            rec["label_note"] = LABEL_NOTES[r["run_id"]]
        recs.append(rec)
    riser_recs = [{"riser_id": z["riser_id"], "system": z["system"], "diameter_in": z["diameter_in"],
                   "status": z["lm"]["status"], "low": z["lm"]["low"], "high": z["lm"]["high"]} for z in v1["risers"]]
    not_drawn = [(x["system"], x["cause"]) for x in v1["rows"] if x["status"] == R.HELD_NOT_DRAWN]
    rows, marks = R.table_from_records(recs, riser_recs, not_drawn)
    return {
        "method": R.METHOD_ID, "restated_from": "out/T745_ALSENAN_RUNS_V1_REJECTED.json (DRAIN_RUN_CENSUS_T745_V1)",
        "source": v1["source"], "rule": "R-T380-1 (merged T-380): a run is MEASURABLE only on a printed dimension or "
        "printed levels at both ends; never scaled under a not-to-scale note",
        "sheet_scale": v1["sheet_scale"], "sheet_basis": basis, "sheet_notes": notes, "pens": v1["pens"],
        "runs": recs, "risers": v1["risers"], "rows": rows, "totals_by_state": R.totals_by_state(rows),
        "symbol_marks": marks, "floor_drain_outlets": v1["floor_drain_outlets"],
        "labels_refused": v1["labels_refused"],
    }


def main():
    v1 = json.loads((HERE / "out" / "T745_ALSENAN_RUNS_V1_REJECTED.json").read_text(encoding="utf-8"))
    out = restate(v1)
    (HERE / "out" / "T745_ALSENAN_RUNS.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n",
                                                         encoding="utf-8")
    print(json.dumps(out["totals_by_state"], indent=1))
    for r in out["rows"]:
        print(r["kind"], r["floor"], r["system"], r["diameter_in"], r["status"], r["runs"], r["lm"], r["lm_high"],
              r.get("scaled_info_lm"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
