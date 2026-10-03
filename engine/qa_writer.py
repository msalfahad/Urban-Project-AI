"""E40 writer — puts the QA workbook on disk as .xlsx and adds no values.

Separate from `engine.qa_workbook` on purpose. The data layer decides what each
cell says; this file decides what it looks like. A writer that also computed
would be a second place for a quantity to come from, and then two files would
have to agree about what the answer is.

The only things added here are presentation: a header band, frozen panes,
column widths, and a visible tint on the columns a human is meant to write in.
"""

from __future__ import annotations

from engine.qa_workbook import UNKNOWN, Workbook

# A checker column is tinted so a blank in it reads as "your line", not as a
# value someone forgot. NOT_ESTABLISHED is tinted too, for the opposite reason.
FILL_HUMAN = "FFF7E6"
FILL_UNKNOWN = "FDECEA"
FILL_HEADER = "EAEFF5"

MAX_WIDTH = 52
MIN_WIDTH = 10


def write(workbook: Workbook, path: str) -> str:
    """Write the workbook. Returns the path written."""
    from openpyxl import Workbook as XlWorkbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    xl = XlWorkbook()
    xl.remove(xl.active)

    head = Font(bold=True)
    header_fill = PatternFill("solid", fgColor=FILL_HEADER)
    human_fill = PatternFill("solid", fgColor=FILL_HUMAN)
    unknown_fill = PatternFill("solid", fgColor=FILL_UNKNOWN)
    wrap = Alignment(wrap_text=True, vertical="top")

    for sheet in workbook.sheets:
        ws = xl.create_sheet(sheet.name[:31])
        r = 1
        ws.cell(r, 1, f"{workbook.title} — {sheet.name}").font = Font(
            bold=True, size=13)
        r += 1
        for note in sheet.notes:
            c = ws.cell(r, 1, note)
            c.alignment = wrap
            c.font = Font(italic=True, size=9)
            r += 1
        r += 1

        header_row = r
        for i, col in enumerate(sheet.columns, 1):
            c = ws.cell(r, i, col)
            c.font = head
            c.fill = header_fill
            c.alignment = wrap
        r += 1

        human = set(sheet.human_columns)
        for row in sheet.rows:
            for i, col in enumerate(sheet.columns, 1):
                v = row.get(col, UNKNOWN)
                c = ws.cell(r, i, v)
                if col in human:
                    c.fill = human_fill
                elif v == UNKNOWN:
                    c.fill = unknown_fill
            r += 1

        ws.freeze_panes = ws.cell(header_row + 1, 1)
        for i, col in enumerate(sheet.columns, 1):
            longest = max([len(str(col))]
                          + [len(str(row.get(col, ""))) for row in sheet.rows])
            ws.column_dimensions[get_column_letter(i)].width = max(
                MIN_WIDTH, min(MAX_WIDTH, longest + 2))

    ws = xl.create_sheet("How to read this", 0)
    ws.column_dimensions["A"].width = 26
    ws.column_dimensions["B"].width = 100
    rows = [("Project", workbook.project_id), ("Workbook", workbook.title), ("", "")]
    rows += [("WARNING", w) for w in workbook.warnings]
    rows += [("", ""), ("NOT_ESTABLISHED", "No value was established. This is "
              "NOT zero. Zero means a proved quantity of zero.")]
    rows += [("Tinted amber", "A column for the checker to write in. A blank "
              "there is a blank line, not a missing value.")]
    rows += [("", "")] + [("Provenance", f"{k}: {v}") for k, v in
                          workbook.provenance]
    for i, (a, b) in enumerate(rows, 1):
        ws.cell(i, 1, a).font = Font(bold=True)
        c = ws.cell(i, 2, b)
        c.alignment = Alignment(wrap_text=True, vertical="top")
    xl.save(path)
    return path
