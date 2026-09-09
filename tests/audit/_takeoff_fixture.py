"""Builds a synthetic concrete-takeoff (حصر) workbook mirroring the real format.

Stands in for the client's confidential takeoff files (which are never committed).
It reproduces the structure the takeoff auditor targets — dimension → volume
elements, a cover with section totals + steel, a lean-concrete row, and one
#REF! — so the takeoff auditor is proven without shipping real data.
"""

from __future__ import annotations

from openpyxl import Workbook


def build_concrete_takeoff(path: str, *, with_ref_error: bool = True) -> str:
    wb = Workbook()

    # Section sheet: foundations (القواعد-like)
    ws = wb.active
    ws.title = "القواعد"
    ws.append([None] * 9)                                              # 1
    ws.append(["بيان البند", "الحجم العنصر", None, None, None, "العدد", "خصم", None, "الحجم صافي م³"])  # 2 header
    ws.append([None, "العرض م", "الطول م", "الارتفاع م", "الحجم م³", None, "الحجم م³", "العدد", None])  # 3 subheader
    # element rows (E = D*C*B volume per element; I = E*F net)
    ws["A4"] = "F"; ws["B4"] = 0.8; ws["C4"] = 0.9; ws["D4"] = 0.3
    ws["E4"] = "=D4*C4*B4"; ws["F4"] = 4; ws["I4"] = "=E4*F4"
    ws["A5"] = "F2"; ws["B5"] = 1.7; ws["C5"] = 1.9; ws["D5"] = 0.35
    ws["E5"] = "=D5*C5*B5"; ws["F5"] = 2; ws["I5"] = "=E5*F5"
    ws["A6"] = "إجمالي"; ws["I6"] = "=SUM(I4:I5)"

    # Cover sheet (ورقة1-like): sections + steel, lean excluded
    cov = wb.create_sheet("ورقة1")
    cov.append([None] * 9)                                             # 1
    cov.append(["البيان", "الكميات", None, None, "الصافى", "اجمالى عام", "العدد", "كميات الحديد(طن)", "سعرالوحدة"])  # 2 header
    cov["A3"] = "الخرسانه العاديه"; cov["E3"] = 47.055                 # lean, excluded
    cov["A4"] = "اجمالى القواعد"; cov["E4"] = 77.63; cov["H4"] = 5.8
    cov["A5"] = "اجمالى الحوائط والأعمدة"; cov["E5"] = 39.75; cov["H5"] = 7.95
    cov["A6"] = "اجمالى الخرسانة المسلحة"; cov["F6"] = "=E4+E5"        # RC total (excl lean)
    if with_ref_error:
        cov["A7"] = "Total"; cov["D7"] = "#REF!"                       # broken cross-sheet total

    wb.save(path)
    return path
