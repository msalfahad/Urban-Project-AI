"""REPORTING V2 - standard report assembly (project-agnostic).

assemble() takes the project header, the ADDITIVE lines and the adapter's breakdown / schedule / info / tech sheets,
builds 00_TOTAL_SUMMARY (the only sheet whose lines may be added) and returns the REPORTING_MODEL_V2 dict:

    00_TOTAL_SUMMARY   project header, MAIN TOTALS BY TRADE (one ADDITIVE row per line, a SUBTOTAL per trade and
                       unit when it has two or more numeric lines), TOTALS BY FLOOR (declared sums of the same lines
                       by level - BREAKDOWN_ONLY), coverage by status (counts of lines, not quantities), key notes
    then the adapter's sheets in the order given.
"""

from __future__ import annotations

from collections import OrderedDict

from . import terms as T
from .model import (POLICY_ID, col, combine, digest, is_q, qsum, row, section, sheet, worst)

SUMMARY_NAME = "00_TOTAL_SUMMARY"
ONLY_SUMMARY = "Project totals: use 00_TOTAL_SUMMARY only."
LEVEL_ORDER = ("FOUNDATION", "GF", "1F", "2F", "ROOF", "EXTERNAL", "UNASSIGNED")


def _group(ln):
    """Trade-total group of a line: (key, en, ar). Lines of one group are the same kind of item in one unit."""
    g = ln.get("group")
    if g:
        return g
    en, ar = T.trade(ln["trade"])
    return (f"{ln['trade']}|{ln['unit']}", en, ar)


def _trade_rows(lines):
    """MAIN TOTALS BY TRADE: one TOTAL row per group = declared sum of its ADDITIVE lines (blocked lines excluded)."""
    groups = OrderedDict()
    for ln in lines:
        if ln["cls"] == "ADDITIVE":
            groups.setdefault(_group(ln), []).append(ln)
    rows = []
    for (gk, gen, gar), lns in groups.items():
        nums = [x for x in lns if x["qty"]["q"] is not None]
        st = worst([x["status"] for x in lns])
        st = ("PARTIAL" if nums else "BLOCKED") if st == "BLOCKED" else st
        qty = (qsum([x["qty"] for x in nums]) if len(nums) > 1 else dict(nums[0]["qty"])) if nums else \
            {"q": None, "blocked": "ALL_LINES_BLOCKED"}
        cnt = OrderedDict((k, sum(1 for x in lns if x["status"] == k)) for k in ("COMPUTED", "PARTIAL", "REVIEW", "BLOCKED"))
        cov = ", ".join(f"{v} {k.lower()}" for k, v in cnt.items() if v) + f" line{'s' if len(lns) > 1 else ''}: " + \
            ", ".join(x["id"] for x in lns)
        rows.append(row([T.trade(lns[0]["trade"])[0], gar, gen, qty | {"unit": lns[0]["unit"]}, lns[0]["unit"], st, cov, "TOTAL"],
                        role="TOTAL", status=st, explains=None))
    return rows


def _line_rows(lines):
    rows = []
    by_trade = OrderedDict()
    for ln in lines:
        by_trade.setdefault(ln["trade"], []).append(ln)
    for tk, lns in by_trade.items():
        en, ar = T.trade(tk)
        rows.append(row([en, ar, "", None, "", "", "", ""], role="NOTE", note="GROUP"))
        for ln in lns:
            alt = f"same item as {ln['alternative_of']} - do not add" if ln.get("alternative_of") else ""
            rows.append(row([ln["id"], ln["desc_ar"], ln["desc_en"], ln["qty"] | {"unit": ln["unit"]}, ln["unit"], ln["status"],
                             "; ".join(x for x in (alt, ln.get("note") or "") if x), ln["cls"]],
                            cls=ln["cls"], status=ln["status"], explains=ln["id"]))
    return rows


def _matrix(lines, levels):
    groups = OrderedDict()
    for ln in lines:
        if ln["cls"] != "ADDITIVE" or not ln.get("matrix"):
            continue
        groups.setdefault(ln["matrix"], []).append(ln)
    groups = OrderedDict((g, l) for g, l in groups.items() if any(x["qty"]["q"] is not None for x in l))
    cols = [col("level", "FLOOR", "الدور", "text", width=26), col("level_ar", "", "", "ar", width=16)]
    for g, l in groups.items():
        cols.append(col(g, g, T.trade(l[0]["trade"])[1], "qty", unit=l[0]["unit"], width=12))
    rows = []
    for lv in levels + ["PROJECT"]:
        en, ar = T.level(lv)
        cells, sts = [en, ar], []
        for g, l in groups.items():
            parts = [p for x in l for p in x["parts"] if lv == "PROJECT" or p["level"] == lv]
            nums = [p["cell"] for p in parts if p["cell"]["q"] is not None]
            if nums:
                cells.append(qsum(nums) if len(nums) > 1 else dict(nums[0]))
            elif parts:
                cells.append({"q": None, "blocked": "ALL_PARTS_BLOCKED"})
            else:
                cells.append({"q": None, "na": ""})
            sts.append(combine(parts) if parts else None)
        st = worst([s for s in sts if s])
        rows.append(row(cells, role="TOTAL" if lv == "PROJECT" else "ITEM",
                        cls=None if lv == "PROJECT" else "BREAKDOWN_ONLY", status=st,
                        explains=None if lv == "PROJECT" else "MATRIX@" + lv))
    return section("FLOOR_TOTALS", T.section("FLOOR_TOTALS"), cols, rows,
                   note="Each cell adds the ADDITIVE lines of that column at that level (BREAKDOWN_ONLY); the TOTAL PROJECT row "
                        "equals the trade lines above. Blank = no line at that level; BLOCKED = only blocked parts.")


def _coverage(lines):
    counts = OrderedDict((s, 0) for s in ("COMPUTED", "PARTIAL", "REVIEW", "BLOCKED"))
    for ln in lines:
        if ln["cls"] == "ADDITIVE":
            counts[ln["status"]] = counts.get(ln["status"], 0) + 1
    n = sum(counts.values()) or 1
    cols = [col("status", "STATUS", "الحالة", "status", width=18), col("label_ar", "", "", "ar", width=12),
            col("lines", "REPORT LINES", "عدد البنود", "count", width=12), col("share", "SHARE OF LINES", "النسبة", "pct", width=12)]
    rows = [row([s, T.STATUS_LABEL[s][1], c, round(c / n, 6)], cls="TRACE_ONLY", status=s) for s, c in counts.items()]
    return section("COVERAGE", T.section("COVERAGE"), cols, rows, kind="coverage",
                   note="Counts of ADDITIVE report lines by status - quantities in different units cannot be added, so "
                        "coverage is by line, not by quantity.")


def assemble(project: dict, lines: list, sheets: list, regs, *, levels=None, key_notes=()) -> dict:
    levels = [lv for lv in LEVEL_ORDER if any(p["level"] == lv for ln in lines for p in ln["parts"])] if levels is None else levels
    head_cols = [col("k", "ITEM", "", "text", width=24), col("v", "VALUE", "", "text", width=60)]
    head_rows = [row([k, v], role="NOTE") for k, v in project["header"]]
    trade_cols = [col("trade", "TRADE", "البند", "text", width=22), col("desc_ar", "DESCRIPTION AR", "الوصف", "ar", width=24),
                  col("desc_en", "DESCRIPTION EN", "", "text", width=40), col("qty", "QTY", "الكمية", "qty", width=13),
                  col("unit", "UNIT", "الوحدة", "text", width=6), col("status", "STATUS", "الحالة", "status", width=10),
                  col("note", "COVERAGE / NOTE", "ملاحظة", "text", width=44), col("cls", "CLASS", "", "cls", width=11)]
    line_cols = [col("code", "ITEM CODE", "رمز البند", "code", width=22)] + trade_cols[1:]
    notes = [row([n], role="NOTE") for n in list(key_notes) + [
        "Only this sheet carries project totals; floor, foundation and opening sheets are breakdowns of these lines.",
        "BLOCKED quantities are excluded from every total and are never shown as 0; see 06_BLOCKERS_OWNER_QUESTIONS.",
        "Status shown = display alias; the technical code is kept on every breakdown row and in 07_METHODS_TRACEABILITY.",
        "No benchmark value is used. No pricing. SHADOW - not approved for tender or contract."]]
    summary = sheet(SUMMARY_NAME, T.section("TOTAL_SUMMARY"), "SUMMARY", [
        section("PROJECT", ("PROJECT", "المشروع"), head_cols, head_rows, kind="info"),
        section("TRADE_TOTALS", T.section("TRADE_TOTALS"), trade_cols, _trade_rows(lines),
                note="Each total adds the ADDITIVE lines of one item kind and unit (listed in PROJECT BOQ LINES below); blocked "
                     "lines are excluded and never counted as 0."),
        _matrix(lines, levels),
        _coverage(lines),
        section("KEY_NOTES", T.section("KEY_NOTES"), [col("n", "NOTE", "", "text", width=120)], notes, kind="notes"),
        section("BOQ_LINES", ("PROJECT BOQ LINES (ADDITIVE)", "بنود المشروع"), line_cols, _line_rows(lines),
                note="The canonical lines: ADDITIVE lines are the only quantities that build the totals above; "
                     "ALTERNATIVE_MEASURE lines are the same item on another basis - never add both.")])
    for s in sheets:
        if s["role"] != "SUMMARY":
            s["note"] = ONLY_SUMMARY if s["role"] in ("BREAKDOWN", "SCHEDULE") else s.get("note")
    model = {"SCHEMA": "URBAN_REPORTING_MODEL_V2", "policy": POLICY_ID, "project": project, "inputs": regs.inputs(),
             "levels": levels, "lines": lines, "sheets": [summary] + list(sheets), "glossary": T.glossary_record()}
    model["content_digest"] = digest({k: v for k, v in model.items() if k != "content_digest"})
    return model


def quantity_cells(model) -> list:
    out = []
    for s in model["sheets"]:
        for sec in s["sections"]:
            for i, r in enumerate(sec["rows"]):
                for j, c in enumerate(r["cells"]):
                    if is_q(c):
                        out.append((s["name"], sec["id"], i, j, c))
    return out
