"""Number (b) as a committed table: the workbook's Compare sheet (build_boq.py) written as COMPARE_<ver>.md, one row per
freelancer trade section / key, candidate vs freelancer in units and %, with the reading and the V12 classes. The .xlsx
stays git-ignored; this file is what the board keeps. Reference comparison only, never engineering verification.

    python3 -I compare_md.py workbook.xlsx out.md
"""
from __future__ import annotations

import sys

import openpyxl


def fmt(x, nd=2):
    if x is None or x == "":
        return ""
    if isinstance(x, (int, float)):
        return f"{x:,.{nd}f}"
    return str(x).replace("|", "/")


def main(argv):
    wb = openpyxl.load_workbook(argv[0], read_only=True)
    c = wb["Compare"]
    rows = list(c.iter_rows(values_only=True))
    title, hdr, data = rows[0][0], rows[2], [r for r in rows[3:] if r and r[0]]
    col = {h: i for i, h in enumerate(hdr)}
    keep = ["Section", "Trade (freelancer label)", "Unit", "Item codes", "Freelancer", "Engine now: calculated",
            "Engine now: held low", "Engine now: held high", "Blank lines now", "Difference (calc - freelancer)",
            "% of freelancer (calc only)", "ENGINE_RIGHT", "ENGINE_WRONG", "RULE_DIFFERENCE", "HELD (V12)",
            "UNRESOLVED (V12)", "Reading"]
    out = [f"# Compare: {str(title).split(' vs ')[0].replace('Candidate ', '')} vs the freelancer (number (b))", "",
           "REFERENCE ONLY, never engineering verification. Built by compare_md.py from the Compare sheet of build_boq.py "
           "(freelancer totals from RECONCILED_STATEMENT_T635 / T001C key map / BENCHMARK_NORMALISED; engine = this line "
           "index; class columns are the V12 statement split in the section's unit, not recomputed).", "",
           "| " + " | ".join(keep) + " |", "|" + "---|" * len(keep)]
    for r in data:
        cells = []
        for h in keep:
            v = r[col[h]]
            cells.append(fmt(v, 1 if h.startswith("%") else 2))
        out.append("| " + " | ".join(cells) + " |")
    out += ["", f"{len(data)} rows."]
    open(argv[1], "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("rows", len(data))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
