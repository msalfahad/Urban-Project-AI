"""Evaluate the workbook's own formulas, and write the results back as cached values.

Two jobs, one evaluator.  The quality checks are supposed to test the workbook a reviewer will open rather than
the Python that wrote it, so they read the formulas and work them out the way a spreadsheet would.  And a file
written by openpyxl carries formulas with no cached result, so a reader whose viewer does not recalculate sees
blanks; the same evaluated values are injected into the sheet XML as `<v>` so the file shows its numbers whether
or not anything recalculates it.

The grammar is deliberately tiny - it is the grammar this workbook actually uses - and anything outside it raises
rather than guessing a value.
"""

from __future__ import annotations

import re
import shutil
import zipfile
from pathlib import Path

REF = re.compile(r"(?:'([^']+)'!)?\$?([A-Z]{1,3})\$?(\d+)")
RANGE = re.compile(r"SUM\((?:'([^']+)'!)?([A-Z]{1,3}\d+):([A-Z]{1,3}\d+)\)")
BLANK = "__BLANK__"          # what a formula returns when it deliberately yields ""


class FormulaError(Exception):
    pass


def _col_row(a):
    m = REF.match(a)
    return m.group(2), int(m.group(3))


def value(wb, sheet, coord, depth=0, memo=None):
    """What a spreadsheet would show in this cell."""
    memo = {} if memo is None else memo
    key = (sheet, coord)
    if key in memo:
        return memo[key]
    if depth > 60:
        raise FormulaError(f"formula recursion at {sheet}!{coord}")
    raw = wb[sheet][coord].value
    if not isinstance(raw, str) or not raw.startswith("="):
        memo[key] = raw
        return raw
    memo[key] = _evaluate(wb, sheet, raw[1:], depth, memo)
    return memo[key]


def _sum_range(wb, sheet, m, depth, memo):
    sh = m.group(1) or sheet
    c0, r0 = _col_row(m.group(2))
    c1, r1 = _col_row(m.group(3))
    if c0 != c1:
        raise FormulaError(f"multi-column range {m.group(0)}")
    total = 0.0
    for r in range(r0, r1 + 1):
        v = value(wb, sh, f"{c0}{r}", depth + 1, memo)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            total += v
    return total


def _count_range(wb, sheet, a, b, depth, memo):
    c0, r0 = _col_row(a)
    c1, r1 = _col_row(b)
    if c0 != c1:
        raise FormulaError("multi-column COUNT")
    n = 0
    for r in range(r0, r1 + 1):
        v = value(wb, sheet, f"{c0}{r}", depth + 1, memo)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            n += 1
    return n


def _evaluate(wb, sheet, f, depth, memo):
    f = f.strip()

    # the three IF shapes this workbook uses, each of which exists to keep a cell blank until it is earned
    m = re.fullmatch(r'IF\(([A-Z]{1,3}\d+)="","",(.+)\)', f)
    if m:
        return BLANK if value(wb, sheet, m.group(1), depth + 1, memo) in (None, "", BLANK) \
            else _evaluate(wb, sheet, m.group(2), depth, memo)
    m = re.fullmatch(r'IF\(OR\(([A-Z]{1,3}\d+)="",([A-Z]{1,3}\d+)=""\),"",(.+)\)', f)
    if m:
        a = value(wb, sheet, m.group(1), depth + 1, memo)
        b = value(wb, sheet, m.group(2), depth + 1, memo)
        return BLANK if a in (None, "", BLANK) or b in (None, "", BLANK) \
            else _evaluate(wb, sheet, m.group(3), depth, memo)
    m = re.fullmatch(r'IF\(COUNT\(([A-Z]{1,3}\d+):([A-Z]{1,3}\d+)\)=0,"",SUM\(([A-Z]{1,3}\d+):([A-Z]{1,3}\d+)\)\)', f)
    if m:
        if _count_range(wb, sheet, m.group(1), m.group(2), depth, memo) == 0:
            return BLANK
        return _sum_range(wb, sheet, re.match(RANGE, f"SUM({m.group(3)}:{m.group(4)})"), depth, memo)

    expr = RANGE.sub(lambda m: repr(_sum_range(wb, sheet, m, depth, memo)), f)

    def one(m):
        v = value(wb, m.group(1) or sheet, f"{m.group(2)}{m.group(3)}", depth + 1, memo)
        if v is None or v == "" or v == BLANK:
            return "0.0"
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return repr(float(v))
        raise FormulaError(f"{sheet}: reference to a non-numeric cell in {f}")

    expr = REF.sub(one, expr)
    if not re.fullmatch(r"[0-9eE+\-*/.() ]+", expr):
        raise FormulaError(f"{sheet}: unsupported formula {f}")
    return eval(expr)  # noqa: S307 - the pattern above admits arithmetic and nothing else


def evaluate_all(wb):
    """Every formula cell in the book, evaluated.  Raises on anything the grammar does not cover."""
    memo, out = {}, {}
    for name in wb.sheetnames:
        ws = wb[name]
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str) and c.value.startswith("="):
                    out[(name, c.coordinate)] = value(wb, name, c.coordinate, 0, memo)
    return out


# ------------------------------------------------------------------ cached results in the file itself
def _sheet_paths(zf):
    """Sheet name -> the part inside the xlsx that holds it, in workbook order."""
    wbxml = zf.read("xl/workbook.xml").decode("utf-8")
    rels = zf.read("xl/_rels/workbook.xml.rels").decode("utf-8")
    rid_to_target = {}
    for rel in re.findall(r"<Relationship\b[^>]*/?>", rels):
        rid = re.search(r'Id="([^"]+)"', rel)
        tgt = re.search(r'Target="([^"]+)"', rel)
        if rid and tgt:
            rid_to_target[rid.group(1)] = tgt.group(1)
    out = {}
    for sheet in re.findall(r"<sheet\b[^>]*/?>", wbxml):
        name = re.search(r'name="([^"]+)"', sheet)
        rid = re.search(r'r:id="([^"]+)"', sheet)
        if not (name and rid):
            continue
        t = rid_to_target[rid.group(1)]
        out[name.group(1).replace("&amp;", "&")] = "xl/" + t.lstrip("/").replace("xl/", "", 1)
    return out


def inject_cached_values(path, values):
    """Write each evaluated result into the file beside its formula, so the workbook shows its numbers at rest.

    The formula stays exactly as written - this adds the `<v>` a calculating application would have stored.
    """
    path = Path(path)
    src = path.with_suffix(".tmp.xlsx")
    shutil.move(str(path), str(src))
    with zipfile.ZipFile(src) as zin:
        sheets = _sheet_paths(zin)
        by_part = {}
        for (sheet, coord), v in values.items():
            by_part.setdefault(sheets[sheet], {})[coord] = v
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename in by_part:
                    data = _patch_sheet(data.decode("utf-8"), by_part[item.filename]).encode("utf-8")
                zout.writestr(item, data)
    src.unlink()
    return len(values)


def _patch_sheet(xml, cells):
    def repl(m):
        coord = m.group(1)
        # a self-closing <c .../> holds nothing to cache, and must not swallow the cell that follows it
        if m.group(2).startswith("/>") or coord not in cells:
            return m.group(0)
        v = cells[coord]
        body = m.group(0)
        body = re.sub(r"<v\s*/>|<v>.*?</v>", "", body, flags=re.S)
        if v is BLANK or v == BLANK:
            cached, attr = "<v></v>", ' t="str"'
        elif isinstance(v, (int, float)) and not isinstance(v, bool):
            cached, attr = f"<v>{repr(float(v))}</v>", ""
        else:
            return m.group(0)
        head = re.match(r"<c [^>]*>", body).group(0)
        new_head = re.sub(r' t="[^"]*"', "", head)
        if attr:
            new_head = new_head[:-1] + attr + ">"
        body = body.replace(head, new_head, 1)
        return body.replace("</c>", cached + "</c>")

    return re.sub(r"<c r=\"([A-Z]{1,3}\d+)\"[^>]*?(/>|>.*?</c>)", repl, xml, flags=re.S)
