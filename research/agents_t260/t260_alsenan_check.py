"""T-260 Alsenan check (development villa): the four aluminium-door candidates the candidate holds, ruled by
DOOR_CLASS_WIDTH_EVIDENCE_V1 on the committed values-only input; SETTLED / STILL-HELD split with m2 deltas for lane I;
reconciliation to the freelancer's aluminium rows. Nothing is applied to any BOQ line.

    python3 -I research/agents_t260/t260_alsenan_check.py          # writes LEDGER_T260.csv and summary.json
    python3 -I research/agents_t260/t260_alsenan_check.py --check  # rebuilds in memory, compares byte for byte
"""
from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import door_evidence as E  # noqa: E402

INP = HERE / "ALSENAN_T260_INPUT.json"
COLS = ["id", "class", "class_status", "class_rule", "width_m", "width_status", "m2", "status", "outcome",
        "class_reason", "width_note"]


def _r(x):
    return round(x, 3) + 0.0


def main(write=True):
    inp = json.loads(INP.read_text(encoding="utf-8"))
    rows = E.ledger(inp["doors"])
    rel = inp["released_unchanged"]
    released_before = _r(sum(v["m2"] for v in rel.values()))
    settled = [r for r in rows if r["outcome"] == "SETTLED"]
    still = [r for r in rows if r["outcome"] == "STILL-HELD"]
    alu_settled = [r for r in settled if r["class"] == E.ALU]
    alu_after = _r(released_before + sum(r["m2"] for r in alu_settled))
    # what each settled door leaves in the other lines' held ranges (T-232 rule 4: each class candidate from 0)
    by = {d["id"]: d for d in inp["doors"]}
    pvc_lo, pvc_hi = inp["other_lines_before"]["PVC_GF_held_m2"]
    main_lo, main_hi = inp["other_lines_before"]["MAIN_ENTRANCE_held_m2"]
    pvc_hi_after, main_hi_after = pvc_hi, main_hi
    for r in alu_settled:
        cands = by[r["id"]]["before"]["classes"]
        if E.PVC in cands:
            pvc_hi_after -= E.Q55_HEIGHT * by[r["id"]]["faces"][0]["gap_m"]
        if E.MAIN in cands:
            main_hi_after -= E.Q55_HEIGHT * by[r["id"]]["faces"][0]["gap_m"]
    fr = inp["freelancer"]["rows"]
    fl_pcs = sum(v["pcs"] for v in fr.values())
    fl_m2 = _r(sum(v["m2"] for v in fr.values()))
    pcs_after = len(rel) + len(alu_settled)
    # reconciliation his -> ours (ERS s.2.4): heights, widths, count
    eng = {k: v["width_m"] for k, v in rel.items()}
    eng.update({r["id"]: r["width_m"] for r in alu_settled})
    heights = _r(fl_pcs * 1.0 * (E.Q55_HEIGHT - 2.4))
    widths = _r(sum((w - 1.0) * E.Q55_HEIGHT for w in eng.values()))
    count = _r((pcs_after - fl_pcs) * 1.0 * E.Q55_HEIGHT)
    residual = _r(alu_after - (fl_m2 + heights + widths + count))
    summary = {
        "method": E.METHOD,
        "aluminium_line_m2": {"before_released": released_before, "before_held_range": [1.98, 8.8],
                              "settled_here": _r(sum(r["m2"] for r in alu_settled)), "after_if_ruled": alu_after,
                              "after_held": [r["id"] for r in still if r["class"] in (E.ALU, None)],
                              "pcs_before": [2, 6], "pcs_after_if_ruled": pcs_after},
        "other_lines_if_ruled": {"PVC_GF_held_m2": [pvc_lo, _r(pvc_hi_after)],
                                 "MAIN_ENTRANCE_held_m2": [main_lo, _r(main_hi_after)], "MAIN_ENTRANCE_pcs": 1},
        "freelancer": {"pcs": fl_pcs, "m2": fl_m2, "diff_m2": _r(alu_after - fl_m2),
                       "diff_pct": round(100.0 * (alu_after - fl_m2) / fl_m2, 2),
                       "reconciliation_his_to_ours": {"heights_Q55C_2.20_vs_2.40": heights,
                                                      "widths_drawn_jambs": widths,
                                                      "count_drawn_5_GF_vs_his_4": count, "residual": residual}},
        "cross_trade": "widths equal the census T-198 for all four (1.00 / 1.00 / 1.00 / 0.90): block / plaster / "
                       "paint deductions (T-175, T-228 GF-W10 at 0.90) unchanged",
        "settled": [r["id"] for r in settled], "still_held": [r["id"] for r in still],
    }
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLS, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in COLS})
    out = {"LEDGER_T260.csv": buf.getvalue(),
           "summary.json": json.dumps(summary, indent=1, ensure_ascii=False, sort_keys=True) + "\n"}
    if write:
        for k, v in out.items():
            (HERE / k).write_text(v, encoding="utf-8")
    return rows, summary, out


if __name__ == "__main__":
    if "--check" in sys.argv:
        _, _, out = main(write=False)
        bad = [k for k, v in out.items() if (HERE / k).read_text(encoding="utf-8") != v]
        print("CHECK", "FAIL " + ", ".join(bad) if bad else "PASS")
        sys.exit(1 if bad else 0)
    _, s, _ = main()
    print(json.dumps(s, indent=1, ensure_ascii=False))
