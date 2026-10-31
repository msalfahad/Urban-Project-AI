"""T-385 extract (run once on private inputs, outside the repository): writes ALSENAN_T385_INPUT.json, the only input of
t385_alsenan.py. It keeps VALUES ONLY: candidate concrete line ids, item codes, element ids, floor, state, net, bounds and
the line's own formula text; the freelancer's sheet rows as (sheet title, row number, element mark when it is an ASCII
drawing mark, m3). No coordinates, no client name, no rate, no amount, no free text of the workbook.

    python3 -I research/agents_t385/t385_extract.py --lines <run>/V3_0_29_BOQ_LINES.json \
        --downgrades <board>/docs/agents/verdicts/V3.0.29/DOWNGRADES.json --freelancer <private>/<concrete workbook>.xlsx \
        --out <checkout>/.work/private/t385/ALSENAN_T385_INPUT.json   (never inside a worktree)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

CANDIDATE = "ARCH_TAKEOFF_V3.0.29"
SUMMARY_SHEET_ROWS = (15, 17, 18, 19, 20, 21, 22, 23)       # family totals, sheet 1 (key map T001C reference rows)
MARK = re.compile(r"^[A-Z][A-Z0-9 .+\-]{0,12}$")


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def freelancer_rows(path):
    import openpyxl  # private-input step only
    wb = openpyxl.load_workbook(path, data_only=True)
    ws0 = wb.worksheets[0]
    totals = {}
    for r in SUMMARY_SHEET_ROWS:
        v = ws0.cell(r, 5).value      # column E: quantity (H is the rebar tonnage, never read)
        if not _num(v):
            raise SystemExit(f"summary row {r}: no number")
        totals[f"RC:{ws0.title}:{r}"] = round(float(v), 6)
    rows = []
    for si, ws in enumerate(wb.worksheets[1:], start=1):
        for r in range(10, ws.max_row + 1):
            net = ws.cell(r, 9).value if si != 6 else ws.cell(r, 7).value   # stair sheet: net in column G
            a = ws.cell(r, 1).value
            label = a.strip() if isinstance(a, str) else ""
            if not _num(net):
                continue
            mark = label if MARK.match(label or "") else ""
            # a printed sub-total row (no dimensions in B..D) is kept as a TOTAL, never as an element
            dims = [ws.cell(r, c).value for c in (2, 3, 4)]
            kind = "ELEMENT" if any(_num(x) for x in dims) else "TOTAL"
            rows.append({"ref": f"{ws.title}:{r}", "sheet": si, "row": r, "mark": mark, "kind": kind,
                         "m3": round(float(net), 6)})
    return totals, rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--lines", required=True)
    ap.add_argument("--downgrades", required=True)
    ap.add_argument("--freelancer", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    doc = json.loads(Path(a.lines).read_text(encoding="utf-8"))
    lines = doc if isinstance(doc, list) else doc["lines"]
    conc = []
    for ln in lines:
        if not str(ln.get("item_code", "")).startswith("STR.CONC."):
            continue
        loc = ln.get("location") or {}
        br = ln.get("bounded_range") if isinstance(ln.get("bounded_range"), dict) else {}
        eid = loc.get("element_id") or ""
        row = {"line_id": ln["line_id"], "item_code": ln["item_code"], "unit": ln.get("unit"),
               "element_id": re.sub(r"@[^:]*", "", eid),            # drawing coordinates dropped
               "floor": loc.get("floor"), "evidence_state": ln.get("evidence_state"),
               "measured_net": ln.get("measured_net"), "bounded_low": br.get("low"), "bounded_high": br.get("high"),
               "formula": re.sub(r"@[0-9.,\-]+", "", str((ln.get("calculation") or {}).get("formula") or ""))[:400]}
        conc.append(row)
    conc.sort(key=lambda r: (r["item_code"], r["element_id"] or "", r["line_id"]))
    dg = json.loads(Path(a.downgrades).read_text(encoding="utf-8"))["downgrades"]
    ids = {r["line_id"] for r in conc}
    dgs = [{"downgrade_id": d["downgrade_id"], "line_ids": sorted(set(d["line_ids"]) & ids),
            "basis_label": d["basis_label"]} for d in dg if set(d["line_ids"]) & ids]
    totals, rows = freelancer_rows(a.freelancer)
    out = {"schema": "T385_INPUT_V1", "candidate": CANDIDATE, "candidate_lines_json_sha256": _sha(a.lines),
           "downgrades_sha256": _sha(a.downgrades), "freelancer_file": "Drive: Urban BOQ private data / Alsenan chalet "
           "project / the concrete + rebar workbook (حصر خرسانة+الحديد (1).xlsx)", "freelancer_sha256": _sha(a.freelancer),
           "concrete_lines": conc, "downgrades": dgs, "freelancer_family_totals": totals, "freelancer_rows": rows}
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(len(conc), "concrete lines;", len(dgs), "downgrades;", len(rows), "freelancer rows")


if __name__ == "__main__":
    main()
