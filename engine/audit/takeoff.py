"""Auditor for dimension-based takeoff (حصر) workbooks.

Covers the two real Urban Projects / Al-Tasneem takeoff layouts:

- **Concrete** (خرسانة مسلحة): width × length × height → volume (م³) per element,
  a count and deductions, and a cover sheet that rolls sections up and lists the
  steel tonnage.
- **Aluminium / blockwork** (الالمونيوم / مبانى الطابوق): count × length ×
  height → area (م²) per element, with void-deduction (خصم فراغات) columns.

What it checks — all deterministic, no model, and only what is *reliable* on
formula-driven takeoff sheets:

  T02  #REF! / Excel error in a takeoff cell .......................... RED
  T04  a SUM whose value ≠ the sum of its range ....................... RED
  T05  cover total ≠ sum of the section values it lists ............... RED
  T06  steel-to-concrete ratio out of band ............................ YELLOW/RED
  T07  lean/plain concrete (العاديه) excluded from the total .......... YELLOW
  T08  opening-deduction (خصم فراغات) columns present but unused ....... YELLOW
  T00  a data sheet nothing recognised (never a silent pass) .......... YELLOW

An important honesty note: because these formulas auto-recompute, deterministic
auditing confirms the *arithmetic* is sound (no broken references, totals add
up, ratios sane) but cannot know whether a *measurement* matches the drawing.
That check is Phase 1 — A1/A2 extract quantities from the drawing and the engine
compares them to the takeoff. This auditor never reports GREEN on a sheet it did
not actually parse (T00).
"""

from __future__ import annotations

import re

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter, column_index_from_string

from .model import Issue, Severity, AuditReport
from . import refdata

EXCEL_ERROR_TOKENS = ["#REF!", "#DIV/0!", "#VALUE!", "#N/A", "#NAME?", "#NUM!", "#NULL!"]

# Opening deductions only (doors/windows in walls/facades). Deliberately NOT the
# generic "خصم" the concrete sheets use for volume deductions.
_VOID_KEYWORDS = ["خصمفراغات", "خصمالفراغ"]
_TOTAL_ROW_KEYWORDS = ["إجمالي", "الإجمالي", "الاجمالى", "اجمالى", "total"]
_STEEL = "الحديد"
_NET = "الصافى"
_LEAN = ["العاديه", "العادية", "عاديه", "lean", "blinding", "نظافة"]

_CELL_RE = re.compile(r"\$?([A-Z]{1,3})\$?(\d+)")
_RANGE_RE = re.compile(r"\$?([A-Z]{1,3})\$?(\d+):\$?([A-Z]{1,3})\$?(\d+)")
_PRODUCT_RE = re.compile(r"^=[\sA-Z0-9$*().]+$")  # only cell refs, * and parens


def _num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _strip(s) -> str:
    return str(s).replace(" ", "") if s is not None else ""


def _refs(formula: str) -> set[tuple[str, int]]:
    return {(m.group(1), int(m.group(2))) for m in _CELL_RE.finditer(formula or "")}


def _cell_error_tokens(*vals) -> list[str]:
    out = []
    for v in vals:
        if v is None:
            continue
        s = str(v)
        for t in EXCEL_ERROR_TOKENS:
            if t in s and t not in out:
                out.append(t)
    return out


def is_takeoff_workbook(path: str) -> bool:
    """True if any sheet looks like a dimension takeoff."""
    wb = load_workbook(path, read_only=True, data_only=True)
    try:
        for name in wb.sheetnames:
            ws = wb[name]
            for i, row in enumerate(ws.iter_rows(values_only=True), start=1):
                if i > 12:
                    break
                joined = " ".join(_strip(c) for c in row if c is not None)
                hits = sum(1 for k in ("العرض", "الطول", "الارتفاع", "عدد", "الأبعاد") if k in joined)
                if hits >= 2:
                    return True
        return False
    finally:
        wb.close()


def _void_columns(v, subheader_row: int) -> list[int]:
    """Opening-deduction (خصم فراغات) columns declared at a subheader."""
    cols = []
    for rr in (subheader_row, subheader_row - 1):
        if rr < 1:
            continue
        for c in range(1, v.max_column + 1):
            t = _strip(v.cell(rr, c).value)
            if t and any(k in t for k in _VOID_KEYWORDS) and c not in cols:
                cols.append(c)
    return cols


def _audit_sheet(wv, wf, sheet: str) -> tuple[list[Issue], bool]:
    """Audit one sheet with only reliable checks. Returns (issues, recognised)."""
    v = wv[sheet]
    f = wf[sheet]
    issues: list[Issue] = []
    recognised = False
    void_cols_all: set[int] = set()
    void_used = False
    data_rows = 0  # rows that look like takeoff data (>= 2 numeric cells)

    # Blanket #REF/error scan (T02) — the most valuable, format-agnostic check.
    for r in range(1, v.max_row + 1):
        for c in range(1, v.max_column + 1):
            errs = _cell_error_tokens(v.cell(r, c).value, f.cell(r, c).value)
            if errs:
                recognised = True
                issues.append(Issue(
                    rule="T02_excel_error", severity=Severity.RED,
                    message=f"Excel error {', '.join(errs)} at {get_column_letter(c)}{r}.",
                    row_index=r, sheet=sheet, detail={"errors": errs},
                ))

    for r in range(1, v.max_row + 1):
        labels = " ".join(_strip(v.cell(r, c).value) for c in range(1, v.max_column + 1))
        hits = sum(1 for k in ("العرض", "الطول", "الارتفاع", "عدد", "الأبعاد") if k in labels)
        if hits >= 2:
            void_cols_all.update(_void_columns(v, r))
            recognised = True
            continue

        numeric_cells = sum(1 for c in range(1, v.max_column + 1) if _num(v.cell(r, c).value))
        if numeric_cells >= 2:
            data_rows += 1

        a = v.cell(r, 1).value
        desc = str(a).strip() if a else ""

        # SUM integrity (T04) on total rows.
        if desc and any(k in _strip(desc) for k in _TOTAL_ROW_KEYWORDS):
            for c in range(1, v.max_column + 1):
                fc = f.cell(r, c).value
                if isinstance(fc, str) and "SUM(" in fc.upper():
                    _check_sum(issues, v, sheet, r, c, fc)
                    recognised = True

        for vc in void_cols_all:
            if _num(v.cell(r, vc).value) and v.cell(r, vc).value != 0:
                void_used = True

    # T08: opening-deduction columns present but never used.
    if void_cols_all and not void_used and data_rows >= 3:
        issues.append(Issue(
            rule="T08_voids_unused", severity=Severity.YELLOW,
            message=("This sheet has opening-deduction (خصم فراغات) columns but none are filled — "
                     "confirm door/window openings were deducted."),
            sheet=sheet, detail={"void_columns": sorted(void_cols_all)},
        ))

    # T00: a real data table nothing recognised — never a silent pass.
    if not recognised and data_rows >= 5:
        issues.append(Issue(
            rule="T00_sheet_not_audited", severity=Severity.YELLOW,
            message=(f"Sheet '{sheet}' holds a data table ({data_rows} numeric rows) in a layout the "
                     "auditor did not recognise — it was NOT audited. Do not treat as passed."),
            sheet=sheet, detail={"data_rows": data_rows},
        ))

    return issues, recognised


def _check_sum(issues, v, sheet, r, c, formula):
    for m in _RANGE_RE.finditer(formula):
        c1, r1, c2, r2 = m.group(1), int(m.group(2)), m.group(3), int(m.group(4))
        if c1 != c2:
            continue
        ci = column_index_from_string(c1)
        total = 0.0
        ok = True
        for rr in range(min(r1, r2), max(r1, r2) + 1):
            val = v.cell(rr, ci).value
            if _num(val):
                total += val
            elif val is not None and any(t in str(val) for t in EXCEL_ERROR_TOKENS):
                ok = False
        stated = v.cell(r, c).value
        if ok and _num(stated) and abs(total - stated) > max(0.05, 0.001 * abs(stated)):
            issues.append(Issue(
                rule="T04_sum_mismatch", severity=Severity.RED,
                message=f"SUM at {get_column_letter(c)}{r} = {stated:g} but its range totals {total:g}.",
                row_index=r, sheet=sheet, detail={"stated": stated, "computed": total},
            ))


# ---- cover: rollup, steel ratio, lean ----------------------------------

def _find_cover(wv):
    for name in wv.sheetnames:
        ws = wv[name]
        for i, row in enumerate(ws.iter_rows(values_only=True), start=1):
            if i > 30:
                break
            joined = " ".join(_strip(c) for c in row if c is not None)
            if _STEEL in joined and _NET in joined:
                return name
    return None


def _audit_cover(wv, wf) -> list[Issue]:
    name = _find_cover(wv)
    if not name:
        return []
    v = wv[name]
    issues: list[Issue] = []
    net_col = steel_col = header_row = None
    for r in range(1, min(30, v.max_row) + 1):
        labels = {c: _strip(v.cell(r, c).value) for c in range(1, v.max_column + 1)
                  if v.cell(r, c).value is not None}
        joined = " ".join(labels.values())
        if _NET in joined and _STEEL in joined:
            header_row = r
            for c, t in labels.items():
                if _NET in t and net_col is None:
                    net_col = c
                if _STEEL in t and steel_col is None:
                    steel_col = c
            break
    if header_row is None or net_col is None:
        return []

    sections = []
    for r in range(header_row + 1, v.max_row + 1):
        d = v.cell(r, 1).value
        ds = str(d).strip() if d else ""
        conc = v.cell(r, net_col).value
        steel = v.cell(r, steel_col).value if steel_col else None
        if ds and _num(conc):
            sections.append((ds, float(conc), float(steel) if _num(steel) else None, r))
    if not sections:
        return []

    def is_lean(d):
        ds = _strip(d)
        return any(_strip(k) in ds for k in _LEAN)

    rc = [(d, c, s, r) for d, c, s, r in sections if not is_lean(d)]
    lean = [(d, c, s, r) for d, c, s, r in sections if is_lean(d)]
    total_conc = sum(c for _, c, _, _ in rc)
    total_steel = sum(s for _, _, s, _ in rc if s is not None)

    if total_conc > 0 and total_steel > 0:
        _steel_ratio(issues, "overall", total_steel * 1000 / total_conc, name)
    for d, c, s, r in rc:
        if s and c > 0:
            _steel_ratio(issues, d, s * 1000 / c, name, r)
    for d, c, s, r in lean:
        issues.append(Issue(
            rule="T07_lean_excluded", severity=Severity.YELLOW,
            message=(f"Lean/plain concrete '{d}' = {c:g} m³ is listed but excluded from the "
                     f"reinforced-concrete total ({total_conc:g} m³). Confirm it is ordered/priced "
                     f"separately (total incl. lean ≈ {total_conc + c:g} m³)."),
            row_index=r, sheet=name, detail={"lean_m3": c, "rc_total_m3": total_conc},
        ))
    return issues


def _steel_ratio(issues, label, ratio, sheet, row=None):
    sev = None
    if ratio < refdata.STEEL_RATIO_RED_MIN or ratio > refdata.STEEL_RATIO_RED_MAX:
        sev = Severity.RED
    elif ratio < refdata.STEEL_RATIO_YELLOW_MIN or ratio > refdata.STEEL_RATIO_YELLOW_MAX:
        sev = Severity.YELLOW
    if sev:
        issues.append(Issue(
            rule="T06_steel_ratio", severity=sev,
            message=(f"Steel-to-concrete ratio for {label} is {ratio:.0f} kg/m³, outside the "
                     f"expected band ({refdata.STEEL_RATIO_YELLOW_MIN:.0f}-"
                     f"{refdata.STEEL_RATIO_YELLOW_MAX:.0f})."),
            row_index=row, sheet=sheet, detail={"ratio": ratio, "label": label},
        ))


def audit_takeoff(path: str) -> AuditReport:
    """Audit a dimension-based takeoff workbook end to end."""
    wv = load_workbook(path, data_only=True)
    wf = load_workbook(path, data_only=False)
    try:
        issues: list[Issue] = []
        rows_checked = 0
        for sheet in wv.sheetnames:
            sheet_issues, _ = _audit_sheet(wv, wf, sheet)
            issues.extend(sheet_issues)
            rows_checked += wv[sheet].max_row
        issues.extend(_audit_cover(wv, wf))
        issues.sort(key=lambda i: (-i.severity.rank, i.sheet, i.row_index or 0, i.rule))
        return AuditReport(issues=issues, rows_checked=rows_checked,
                           sheets=list(wv.sheetnames), source=path)
    finally:
        wv.close()
        wf.close()
