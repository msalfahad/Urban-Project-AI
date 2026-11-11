"""T-706 own read of the reference beam sheet block that carries the 0.128 m3 slip (R-T706-3): the rows of the 1F beam
block, the row range its carry cell sums and the row range its total cell sums, and the member of each omitted row.

Drive "Alsenan chalet project" / the concrete + rebar workbook (private copy via `agent_env.sh decode`). Writes NUMBERS
ONLY (sheet index, row numbers, m3, the member mark / section / storey of the omitted row, which are drawing marks):
no label text, no client data.

    .work/venv/bin/python -I research/agents_t706/t706_reference.py --workbook .work/private/concrete_rebar.xlsx [--write]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out" / "T706_REFERENCE_1F_BEAM.json"
SHEET = 4                    # the beam sheet (T-683 out/T683_REFERENCE_ARITH.json: CONC.BEAM sheet_index 4)


def _range(formula):
    m = re.fullmatch(r"=SUM\(I(\d+):I(\d+)\)", str(formula).replace(" ", ""))
    return (int(m.group(1)), int(m.group(2))) if m else None


def run(path):
    import openpyxl
    wv = openpyxl.load_workbook(path, data_only=True).worksheets[SHEET]
    wf = openpyxl.load_workbook(path).worksheets[SHEET]
    # the two SUM cells of column I whose ranges overlap the block of the omitted row (T-683 finding: row 59)
    sums = []
    for r in range(1, wf.max_row + 1):
        rg = _range(wf.cell(r, 9).value)
        if rg and rg[0] <= 60 <= rg[1] and rg[0] >= 55:
            sums.append({"row": r, "range": rg, "value": f"{Decimal(str(wv.cell(r, 9).value)):.6f}"})
    if len(sums) != 2:
        raise SystemExit(f"T-706: expected the carry and the total SUM cells of the 1F block, found {sums}")
    carry, total = sorted(sums, key=lambda s: s["range"][0])
    lo, hi = carry["range"][0], carry["range"][1]
    rows = {r: f"{Decimal(str(wv.cell(r, 9).value or 0)):.6f}" for r in range(lo, hi + 1) if wv.cell(r, 9).value}
    omitted = [r for r in range(carry["range"][0], total["range"][0])]
    members = {}
    for r in omitted:
        b, c, d = (wv.cell(r, k).value for k in (2, 3, 4))
        members[r] = {"mark": str(wv.cell(r, 1).value).strip(), "storey": "1F",
                      "section": f"{Decimal(str(b)):.2f} x {Decimal(str(c)):.2f}", "length_m": f"{Decimal(str(d)):.2f}"}
    return {"schema": "URBAN_T706_REFERENCE_1F_BEAM_V1", "rule": "R-T706-3 1.0.0",
            "source": "Drive 'Alsenan chalet project', concrete + rebar workbook (private copy; numbers only)",
            "sheet_index": SHEET, "rows_m3": {str(k): v for k, v in rows.items()},
            "carry": {"row": carry["row"], "range": carry["range"], "value": carry["value"]},
            "total": {"row": total["row"], "range": total["range"], "value": total["value"]},
            "omitted_row_members": {str(k): v for k, v in members.items()}}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--workbook", required=True)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    out = run(a.workbook)
    print(json.dumps({k: v for k, v in out.items() if k != "rows_m3"}, indent=1))
    if a.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
