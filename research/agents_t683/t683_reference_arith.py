"""T-683 R-T683-3 run on the development villa's reference workbook (private copy, never committed).

Drive "Alsenan chalet project", the concrete + rebar workbook, decoded with `agent_env.sh decode` into .work/private.
For every keyed concrete cover total (summary sheet rows that the key map T001B keys), the cell it reads is expanded
through its sub-total / carry chain to the item rows (R-T683-3 (a)); omitted / doubled rows and the residual are written
to out/T683_REFERENCE_ARITH.json as NUMBERS ONLY (sheet index, row number, m3): no label, no row text, no client data.

    python3 -I research/agents_t683/t683_reference_arith.py --workbook .work/private/concrete_rebar.xlsx [--write]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import OrderedDict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "research" / "agents_t679"))
import t683_rules as R  # noqa: E402

OUT = HERE / "out" / "T683_REFERENCE_ARITH.json"
KEYMAP = "tests/alsenan/T001B_KEY_MAP.json"
REF_RE = re.compile(r"^='?(.+?)'?!([A-Z]+)(\d+)$")


def grid(ws):
    return {(c.row, c.column): c.value for row in ws.iter_rows() for c in row if c.value is not None}


def run(path: str) -> OrderedDict:
    import openpyxl
    wf = openpyxl.load_workbook(path)
    wv = openpyxl.load_workbook(path, data_only=True)
    summary = wf.worksheets[0]
    keys = [k for k in json.loads((ROOT / KEYMAP).read_text(encoding="utf-8"))["keys"] if k["trade"] == "CONCRETE"]
    names = [ws.title for ws in wf.worksheets]
    out = OrderedDict()
    for k in keys:
        row = int(k["reference_id"].rsplit(":", 1)[1])
        f = next((c.value for c in summary[row] if isinstance(c.value, str) and c.value.startswith("=")), None)
        m = REF_RE.match(f or "")
        if not m:
            raise R.Refused(f"{k['key']}: summary row {row} reads no single cell ({f!r})")
        sheet, col, r = m.group(1), R.col_no(m.group(2)), int(m.group(3))
        ws, vs = wf[sheet], wv[sheet]
        cells, values = grid(ws), grid(vs)
        item_col = 9 if any(c == 9 and isinstance(v, (int, float)) for (_, c), v in values.items()) else 7
        # the stair sheet keeps its volumes in column G, the others in column I
        if (r, col) not in cells:
            raise R.Refused(f"{k['key']}: cover cell absent")
        fnd = R.audit_cover(cells, values, (r, col), item_col)
        items = R.item_values(cells, values, (r, col), item_col)
        # rows the chain reaches are the cover; rows it does not reach above the cover are the omitted findings
        arith = R.arithmetic(vs.cell(r, col).value, [v for v in items], fnd) if fnd else None
        out[k["key"]] = OrderedDict(
            reference_id=k["reference_id"], sheet_index=names.index(sheet), cover_cell=f"{m.group(2)}{r}",
            cover_value=R.s(R.D(vs.cell(r, col).value).quantize(R.Decimal("0.000001"))),
            item_rows=len(items), findings=[{x: y for x, y in fi.items()} for fi in fnd],
            arithmetic=arith, verdict="NO SLIP: every item row reached once" if not fnd else
            "REFERENCE ARITHMETIC: see findings (no engine verdict)")
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--workbook", required=True)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args(argv)
    res = OrderedDict(schema="URBAN_T683_REFERENCE_ARITH_V1", rule="R-T683-3 1.0.0",
                      source="Drive 'Alsenan chalet project', concrete + rebar workbook (private copy; numbers only)",
                      keys=run(a.workbook))
    txt = json.dumps(res, ensure_ascii=False, indent=1, default=str) + "\n"
    if a.write:
        OUT.parent.mkdir(exist_ok=True)
        OUT.write_text(txt, encoding="utf-8")
    for k, v in res["keys"].items():
        print(k, v["cover_cell"], v["cover_value"], v["item_rows"], v["verdict"], v["findings"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
