"""REPORTING V3 - workbook layouts (generic over a BOQ_LINES model).

Trade workbook:  TOTAL | GF | 1F | 2F+ROOF | OTHER+EXTERNAL | DETAIL | TRACE
  level sheet    navy floor title, thick divider, groups (green band), one row per BOQ line (formula text beside the
                 engine value), then the floor subtotals (SUMIFS over the rows that are IN TOTAL, one per summary item
                 and unit, light blue)
  TOTAL          one row per summary item: each level cell links to that level's subtotal, TOTAL = SUM of the levels
Master:          MASTER_SUMMARY (trade x level, values from the frozen matrix, totals by SUM) | one sheet per level |
                 COMPLETENESS | BLOCKERS | OWNER_QUESTIONS
Reconciliation:  one block per trade: Urban value (locked) | manual check (yellow input) | difference | % | status
"""

from __future__ import annotations

from collections import defaultdict

from openpyxl.worksheet.pagebreak import Break

from .book import QTY_FMT, Book

LEVEL_SHEET = {"GF": "GF", "1F": "1F", "2F_ROOF": "2F+ROOF", "OTHER_EXTERNAL": "OTHER+EXTERNAL"}
IN_TOTAL = ("COMPUTED", "PARTIAL")


def _q(u):
    return QTY_FMT.get(u, "#,##0.000")


def _ref(sheet, cell):
    return f"'{sheet}'!{cell}"


def _rnd(v, n=6):
    return None if v is None else round(v, n)


def trade_book(model, code, trade, trade_ar, out_dir, meta) -> dict:
    lines = [x for x in model["lines"] if x["trade"] == trade]
    names = model["level_names"]
    name = f"{code}_{trade}.xlsx"
    b = Book(out_dir / name, project=meta["project"], phase=meta["phase"])
    tot = b.sheet("TOTAL", [44, 30, 8, 14, 14, 14, 16, 16, 12])
    lv_sub = {}                                               # (level, item, unit) -> (cell, expected)
    sheets = {}
    for lv in model["levels"]:
        sheets[lv] = b.sheet(LEVEL_SHEET[lv], [5, 16, 46, 34, 46, 7, 13, 12, 7, 28, 30, 8])
    # ---------------- level sheets
    for lv in model["levels"]:
        ws = sheets[lv]
        en, ar = names[lv]
        b.title(ws, f"{trade.replace('_', ' ')} - {en}", f"{trade_ar} - {ar}",
                f"{meta['project']} | {meta['phase']} | engine values are frozen (locked); light blue = subtotal formula")
        b.header(ws, ["#", "CODE", "DESCRIPTION", "الوصف", "CALCULATION / FORMULA / REASON", "UNIT", "QTY", "STATUS",
                      "IN TOTAL", "SUMMARY ITEM", "AUTHORITY", "LINE"])
        xs = [x for x in lines if x["level"] == lv]
        first = ws._row
        if not xs:
            b.note(ws, "No item of this trade at this level.")
        groups = defaultdict(list)
        for x in xs:
            groups[x["group"]].append(x)
        n = 0
        for g, gx in groups.items():
            b.band(ws, g)
            for x in gx:
                n += 1
                inn = "Y" if x["status"] in IN_TOTAL and x["qty"] is not None and x["sumrow"] else "N"
                b.row(ws, [n, x["code"], x["desc_en"], x["desc_ar"], x["formula"], x["unit"], x["qty"],
                           x["status"], inn,
                           x["sumrow"] or "-", x["authority"], x["line_id"]],
                      kinds=[None] * 6 + ["qty"], fmts=[None] * 6 + [_q(x["unit"])], status_col=7, ar_cols=(3,),
                      wrap_cols=(2, 4, 10))
        last = ws._row - 1
        b.divider(ws)
        # subtotals
        sub = defaultdict(float)
        for x in xs:
            if x["status"] in IN_TOTAL and x["qty"] is not None and x["sumrow"]:
                sub[(x["sumrow"], x["unit"])] += x["qty"]
        if sub:
            b.band(ws, f"SUBTOTALS - {en}   |   المجاميع - {ar}", color="2C4E78")
            for (item, unit), v in sorted(sub.items()):
                f = (f'=SUMIFS($G${first}:$G${last},$J${first}:$J${last},"{item}",$F${first}:$F${last},"{unit}",'
                     f'$I${first}:$I${last},"Y")')
                r = b.row(ws, ["", "", f"SUBTOTAL - {item}", "", "sum of the rows above marked IN TOTAL = Y", unit,
                               {"f": f, "expect": _rnd(v)}, "", "", item, "", ""],
                          fmts=[None] * 6 + [_q(unit)], bold=True)
                lv_sub[(lv, item, unit)] = (f"G{r}", v)
        ws.row_breaks.append(Break(id=ws._row))
    # ---------------- TOTAL sheet
    b.title(tot, f"{trade.replace('_', ' ')} - TRADE TOTAL", f"{trade_ar} - الإجمالي",
            f"{meta['project']} | each level cell links to that level's subtotal; TOTAL = SUM of the levels")
    b.header(tot, ["SUMMARY ITEM", "البند", "UNIT", "GF", "1F", "2F + ROOF", "OTHER + EXT", "TOTAL", "STATUS"])
    rows = [r for r in model["master"]["rows"] if r["trade"] == trade]
    for r in rows:
        vals = [r["item"], r["item_ar"], r["unit"]]
        exp_total = 0.0
        for lv in model["levels"]:
            k = (lv, r["item"], r["unit"])
            if k in lv_sub:
                cell, v = lv_sub[k]
                vals.append({"f": "=" + _ref(LEVEL_SHEET[lv], cell), "expect": _rnd(v)})
                exp_total += v
            else:
                vals.append(0)
        rr = tot._row
        vals.append({"f": f"=SUM(D{rr}:G{rr})", "expect": _rnd(exp_total)})
        vals.append(r["status"])
        b.row(tot, vals, fmts=[None, None, None] + [_q(r["unit"])] * 5, status_col=8, ar_cols=(1,), bold=False)
    b.skip(tot)
    b.note(tot, "Only COMPUTED and PARTIAL lines enter a total; REVIEW lines are shown on the level sheets but never added; "
                "BLOCKED lines carry no quantity and state their reason. Different units are never added together.")
    # ---------------- DETAIL
    det = b.sheet("DETAIL", [8, 18, 30, 60, 13, 12, 9, 9, 12, 12, 12, 12, 12, 13])
    b.title(det, f"{trade.replace('_', ' ')} - DETAILED CALCULATION", f"{trade_ar} - تفاصيل الحساب")
    b.header(det, ["LINE", "CODE", "REF", "FORMULA", "QTY", "STATUS", "DIA", "COUNT", "STRAIGHT L", "HOOK / BEND",
                   "LAP ADD", "TOTAL L", "KG/M", "PROCUREMENT KG"])
    for x in lines:
        for d in x["details"]:
            b.row(det, [x["line_id"], x["code"], d.get("ref"), d.get("formula"), d.get("qty"), d.get("status"),
                        d.get("dia_mm"), d.get("count"), d.get("straight_length_m"), d.get("hook_bend_addition_m"),
                        d.get("lap_addition_m"), d.get("total_bar_length_m"), d.get("kg_per_m"),
                        d.get("procurement_weight_kg")],
                  fmts=[None, None, None, None, "#,##0.000"], status_col=5, wrap_cols=(3,))
    # ---------------- TRACE
    tr = b.sheet("TRACE", [8, 18, 10, 16, 50, 40, 30])
    b.title(tr, f"{trade.replace('_', ' ')} - TRACEABILITY", f"{trade_ar} - التتبع")
    b.header(tr, ["LINE", "CODE", "LEVEL", "STATUS", "AUTHORITY", "REGISTER / TRACE", "SUMMARY ITEM"])
    for x in lines:
        b.row(tr, [x["line_id"], x["code"], x["level"], x["status"], x["authority"], x["trace"], x["sumrow"] or "-"],
              status_col=3, wrap_cols=(4, 5))
    return b.save()


def master_book(model, out_dir, meta) -> dict:
    b = Book(out_dir / "00_URBAN_BOQ_MASTER_SUMMARY.xlsx", project=meta["project"], phase=meta["phase"])
    ws = b.sheet("MASTER_SUMMARY", [30, 44, 30, 8, 13, 13, 13, 13, 14, 12])
    b.title(ws, "URBAN BOQ - MASTER SUMMARY (TRADE x LEVEL)", "ملخص جدول الكميات - البند × الدور",
            f"{meta['project']} | {meta['phase']} | values are the frozen engine totals; TOTAL = SUM of the levels")
    b.header(ws, ["TRADE", "SUMMARY ITEM", "البند", "UNIT", "GF", "1F", "2F + ROOF", "OTHER + EXT", "TOTAL", "STATUS"])
    trades = {t[1]: (t[0], t[2]) for t in model["trades"]}
    cur = None
    for r in model["master"]["rows"]:
        if r["trade"] != cur:
            cur = r["trade"]
            b.band(ws, f"{trades[cur][0]}  {cur.replace('_', ' ')}   |   {trades[cur][1]}")
        rr = ws._row
        b.row(ws, [r["trade"], r["item"], r["item_ar"], r["unit"]] + [r[lv] for lv in model["levels"]] +
              [{"f": f"=SUM(E{rr}:H{rr})", "expect": r["total"]}, r["status"]],
              kinds=[None] * 4 + ["qty"] * 4, fmts=[None] * 4 + [_q(r["unit"])] * 5, status_col=9, ar_cols=(2,))
    b.skip(ws)
    b.note(ws, "Like items only: plain and reinforced concrete, rebar net / straight / procurement, tile and "
               "waterproofing are separate rows; different units are never added. REVIEW and BLOCKED lines are listed "
               "in the trade workbooks and never enter these totals.")
    for lv in model["levels"]:
        s = b.sheet(LEVEL_SHEET[lv], [30, 44, 30, 8, 14, 12])
        en, ar = model["level_names"][lv]
        b.title(s, f"{en} - ALL TRADES", f"{ar} - جميع البنود")
        b.header(s, ["TRADE", "SUMMARY ITEM", "البند", "UNIT", "QTY", "STATUS"])
        for r in model["master"]["rows"]:
            if r[lv]:
                b.row(s, [r["trade"], r["item"], r["item_ar"], r["unit"], r[lv], r["status"]], kinds=[None] * 4 + ["qty"],
                      fmts=[None] * 4 + [_q(r["unit"])], status_col=5, ar_cols=(2,))
    c = b.sheet("COMPLETENESS", [26, 26, 10, 10, 10, 10, 10, 10, 11, 11, 60])
    b.title(c, "BOQ COMPLETENESS MATRIX", "مصفوفة اكتمال جدول الكميات")
    b.header(c, ["TRADE", "البند", "EXPECTED", "COMPUTED", "PARTIAL", "REVIEW", "BLOCKED", "NOT IN SRC", "COVER %",
                 "CORE %", "REMAINING REASON"])
    for r in model["completeness"]["rows"]:
        b.row(c, [r["trade"], r["trade_ar"], r["expected_items"], r["computed"], r["partial"], r["review"], r["blocked"],
                  r["not_in_source"], r["coverage_pct"], r["core_coverage_pct"], "; ".join(r["remaining_reasons"])[:400]],
              ar_cols=(1,), wrap_cols=(10,))
    bl = b.sheet("BLOCKERS", [7, 12, 40, 30, 10, 60])
    b.title(bl, "FINAL BLOCKER REGISTER", "سجل المعوقات النهائي")
    b.header(bl, ["ID", "AREA", "BLOCKER", "LINES", "CLASS", "WHY"])
    for r in model["blockers"]["rows"]:
        b.row(bl, [r["id"], r["area"], r["blocker"], r["lines"], r["class"], r["why"]], wrap_cols=(2, 3, 5))
    q = b.sheet("OWNER_QUESTIONS", [14, 8, 100])
    b.title(q, "OWNER QUESTIONS (BATCHED)", "أسئلة المالك")
    b.header(q, ["GROUP", "ID", "QUESTION"])
    for r in model["questions"]["rows"]:
        b.row(q, [r["group"], r["id"], r["question"]], wrap_cols=(2,))
    return b.save()


def recon_book(model, out_dir, meta) -> dict:
    b = Book(out_dir / "10_QS_RECONCILIATION.xlsx", project=meta["project"], phase=meta["phase"])
    p = b.sheet("PARAMETERS", [40, 14, 60])
    b.title(p, "RECONCILIATION PARAMETERS", "معايير المطابقة")
    b.header(p, ["PARAMETER", "VALUE", "MEANING"], repeat=False)
    m_row = b.row(p, ["MATCH tolerance", {"input": 0.02}, "|difference| <= tolerance x Urban value -> MATCH"],
                  fmts=[None, "0.0%"])
    c_row = b.row(p, ["CLOSE tolerance", {"input": 0.10}, "<= this -> CLOSE; above -> REVIEW"], fmts=[None, "0.0%"])
    for t in model["trades"]:
        rows = [r for r in model["master"]["rows"] if r["trade"] == t[1]]
        if not rows:
            continue
        ws = b.sheet(f"{t[0]}_{t[1][:20]}", [44, 30, 8, 14, 14, 14, 10, 16])
        b.title(ws, f"QS RECONCILIATION - {t[1].replace('_', ' ')}", f"مطابقة الكميات - {t[2]}",
                "enter the manual / check quantity in the yellow cells; difference, % and status are formulas")
        b.header(ws, ["SUMMARY ITEM", "البند", "UNIT", "URBAN (frozen)", "MANUAL / CHECK", "DIFFERENCE", "%", "STATUS"])
        for r in rows:
            rr = ws._row
            b.row(ws, [r["item"], r["item_ar"], r["unit"], r["total"], {"input": None},
                       {"f": f'=IF(E{rr}="","",E{rr}-D{rr})', "expect": ""},
                       {"f": f'=IF(OR(E{rr}="",D{rr}=0),"",(E{rr}-D{rr})/D{rr})', "expect": ""},
                       {"f": f'=IF(E{rr}="","NOT CHECKED",IF(D{rr}=0,"REVIEW",IF(ABS(G{rr})<=PARAMETERS!$B${m_row},"MATCH",'
                             f'IF(ABS(G{rr})<=PARAMETERS!$B${c_row},"CLOSE","REVIEW"))))', "expect": "NOT CHECKED"}],
                  kinds=[None, None, None, "qty"], fmts=[None, None, None, _q(r["unit"]), _q(r["unit"]), _q(r["unit"]),
                                                         "0.0%"], ar_cols=(1,))
    return b.save()


def completeness_book(model, out_dir, meta) -> dict:
    b = Book(out_dir / "BOQ_COMPLETENESS_MATRIX.xlsx", project=meta["project"], phase=meta["phase"])
    c = b.sheet("COMPLETENESS", [26, 26, 10, 10, 10, 10, 10, 10, 11, 11, 70])
    b.title(c, "BOQ COMPLETENESS MATRIX", "مصفوفة اكتمال جدول الكميات",
            "coverage = (computed + 0.5 x partial) / expected items; CORE excludes the extras awaiting a coverage rule")
    b.header(c, ["TRADE", "البند", "EXPECTED", "COMPUTED", "PARTIAL", "REVIEW", "BLOCKED", "NOT IN SRC", "COVER %",
                 "CORE %", "REMAINING REASON"])
    for r in model["completeness"]["rows"]:
        b.row(c, [r["trade"], r["trade_ar"], r["expected_items"], r["computed"], r["partial"], r["review"], r["blocked"],
                  r["not_in_source"], r["coverage_pct"], r["core_coverage_pct"], "; ".join(r["remaining_reasons"])[:600]],
              ar_cols=(1,), wrap_cols=(10,))
    return b.save()
