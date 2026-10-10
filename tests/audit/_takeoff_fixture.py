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


def build_finishing_area_mix(path: str) -> str:
    """A finishing sheet reproducing the 295.44 mixed-measure defect.

    The output column 'اجمالي مسطحات' (areas) is fed from the area column for
    landings/courtyard and from the length column for steps (count × tread) —
    square metres and linear metres summed into one area total.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "رخام+حوش"
    ws.append([None] * 8)                                              # 1
    # header row 2 (اجمالي مسطحات in column H = col 8)
    ws.append(["البيان", "عدد", "الأبعاد ( م )", None, None, None, "اجمالي النعلات", "اجمالي مسطحات"])
    # subheader row 3: طولي in C (3), مسطحات in D (4)
    ws.append([None, None, "طولي", "مسطحات", None, None, None, None])
    ws["A4"] = "الحوش"; ws["B4"] = 1; ws["D4"] = 151.8; ws["H4"] = "=D4"           # area
    ws["A5"] = "بسطه"; ws["B5"] = 1; ws["D5"] = 12.74; ws["H5"] = "=D5"            # area
    ws["A6"] = "درج"; ws["B6"] = 63; ws["C6"] = 1.2; ws["H6"] = "=B6*C6"          # LINEAR (steps)
    ws["A7"] = "درج2"; ws["B7"] = 28; ws["C7"] = 1.2; ws["H7"] = "=B7*C7"         # LINEAR
    ws["A8"] = "اجمالي مسطحات الدرج"; ws["H8"] = "=SUM(H4:H7)"                     # mixes both → T09

    wb.save(path)
    return path
