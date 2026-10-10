"""REPORTING V2 - standard report assembly (project-agnostic).

assemble() takes the project header, the ADDITIVE lines and the adapter's breakdown / schedule / info / tech sheets,
builds 00_TOTAL_SUMMARY (the only sheet whose lines may be added) and returns the REPORTING_MODEL_V2 dict:

    00_TOTAL_SUMMARY   project header, MAIN TOTALS BY TRADE (one TOTAL per item group and unit = SUM formula over the
                       frozen line totals), TOTALS BY FLOOR (SUM formulas over the frozen per-level line cells -
                       BREAKDOWN_ONLY), coverage by status (COUNTIFS over the lines, not quantities), key notes, PROJECT
                       BOQ LINES (the ADDITIVE lines: frozen values, never formulas)
    then the adapter's sheets in the order given.

reconciliation_sheet() builds 08_QS_RECONCILIATION (Urban values locked beside manual checks; see the design spec §9).
Every formula carries the deterministic value it must equal where one exists (validate() checks it).
"""

from __future__ import annotations

from collections import OrderedDict

from . import terms as T
from .model import (POLICY_ID, blocked, col, combine, digest, dsum, evaluate, fcell, inp, is_q, na, qsum, ref, rng, row, section,
                    sheet, worst)

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


def _level_cell(ln, lv):
    parts = [p for p in ln["parts"] if p["level"] == lv]
    nums = [p["cell"] for p in parts if p["cell"]["q"] is not None]
    if nums:
        return (qsum(nums) if len(nums) > 1 else dict(nums[0])) | {"unit": ln["unit"]}
    if parts:
        return blocked("ALL_PARTS_BLOCKED")
    return na("")


def _line_rows(lines, levels):
    """PROJECT BOQ LINES: one ADDITIVE (or ALTERNATIVE_MEASURE) row per line, its share per level and the line total -
    all frozen values (register values / declared sums, locked cells). Formulas only ever add these rows up."""
    rows = []
    by_trade = OrderedDict()
    for ln in lines:
        by_trade.setdefault(ln["trade"], []).append(ln)
    width = 6 + len(levels) + 2
    for tk, lns in by_trade.items():
        en, ar = T.trade(tk)
        rows.append(row([en, ar, ""] + [None] * (width - 3), role="NOTE", note="GROUP", key=f"G:{tk}"))
        for ln in lns:
            cells = [_level_cell(ln, lv) for lv in levels]
            total = ln["qty"] | {"unit": ln["unit"]}           # the canonical line quantity: frozen value, never a formula
            alt = f"same item as {ln['alternative_of']} - do not add" if ln.get("alternative_of") else ""
            rows.append(row([ln["id"], ln["desc_ar"], ln["desc_en"], ln["unit"], ln["status"], ln["cls"]] + cells +
                            [total, "; ".join(x for x in (alt, ln.get("note") or "") if x)],
                            cls=ln["cls"], status=ln["status"], explains=ln["id"], key=ln["id"]))
    return rows


def _trade_rows(lines):
    """MAIN TOTALS BY TRADE: one TOTAL row per group = SUM formula over the line totals of its ADDITIVE lines
    (validated against the deterministic declared sum); blocked lines excluded, never counted as 0."""
    groups = OrderedDict()
    for ln in lines:
        if ln["cls"] == "ADDITIVE":
            groups.setdefault(_group(ln), []).append(ln)
    rows = []
    for (gk, gen, gar), lns in groups.items():
        nums = [x for x in lns if x["qty"]["q"] is not None]
        st = worst([x["status"] for x in lns])
        st = ("PARTIAL" if nums else "BLOCKED") if st == "BLOCKED" else st
        if nums:
            expect = (qsum([x["qty"] for x in nums]) if len(nums) > 1 else nums[0]["qty"])["q"]
            qty = fcell("SUM", *[ref("BOQ_LINES", x["id"], "total") for x in nums], expect=expect, fmt=lns[0]["unit"])
        else:
            qty = {"q": None, "blocked": "ALL_LINES_BLOCKED"}
        cnt = OrderedDict((k, sum(1 for x in lns if x["status"] == k)) for k in ("COMPUTED", "PARTIAL", "REVIEW", "BLOCKED"))
        cov = ", ".join(f"{v} {k.lower()}" for k, v in cnt.items() if v) + f" line{'s' if len(lns) > 1 else ''}: " + \
            ", ".join(x["id"] for x in lns)
        rows.append(row([T.trade(lns[0]["trade"])[0], gar, gen, qty, lns[0]["unit"], st, cov, "TOTAL"],
                        role="TOTAL", status=st, explains=None, key=f"T:{gk}"))
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
    rows, numeric_rows = [], {g: [] for g in groups}
    for lv in levels + ["PROJECT"]:
        en, ar = T.level(lv)
        cells, sts = [en, ar], []
        for g, l in groups.items():
            parts = [p for x in l for p in x["parts"] if lv == "PROJECT" or p["level"] == lv]
            nums = [p["cell"] for p in parts if p["cell"]["q"] is not None]
            if nums:
                expect = qsum(nums)["q"] if len(nums) > 1 else nums[0]["q"]
                if lv == "PROJECT":
                    cells.append(fcell("SUM", *[ref("FLOOR_TOTALS", k, g) for k in numeric_rows[g]], expect=expect))
                else:
                    lines_here = [x for x in l if any(p["level"] == lv and p["cell"]["q"] is not None for p in x["parts"])]
                    cells.append(fcell("SUM", *[ref("BOQ_LINES", x["id"], lv) for x in lines_here], expect=expect))
                    numeric_rows[g].append(lv)
            elif parts:
                cells.append({"q": None, "blocked": "ALL_PARTS_BLOCKED"})
            else:
                cells.append({"q": None, "na": ""})
            sts.append(combine(parts) if parts else None)
        st = worst([s for s in sts if s])
        rows.append(row(cells, role="TOTAL" if lv == "PROJECT" else "ITEM",
                        cls=None if lv == "PROJECT" else "BREAKDOWN_ONLY", status=st,
                        explains=None if lv == "PROJECT" else "MATRIX@" + lv, key=lv))
    return section("FLOOR_TOTALS", T.section("FLOOR_TOTALS"), cols, rows,
                   note="Each cell is a SUM formula over the PROJECT BOQ LINES of that column at that level (BREAKDOWN_ONLY); the "
                        "TOTAL PROJECT row adds the floors. Formulas are presentation totals only - validated against the "
                        "deterministic declared sums. Blank = no line at that level; BLOCKED = only blocked parts.")


def _coverage(line_rows):
    keys = [r["key"] for r in line_rows]
    first, last = keys[0], keys[-1]
    cols = [col("status", "STATUS", "الحالة", "status", width=18), col("label_ar", "", "", "ar", width=12),
            col("lines", "REPORT LINES", "عدد البنود", "count", width=12), col("share", "SHARE OF LINES", "النسبة", "pct", width=12)]
    rows = []
    for s in ("COMPUTED", "PARTIAL", "REVIEW", "BLOCKED"):
        n = sum(1 for r in line_rows if r["cls"] == "ADDITIVE" and r["status"] == s)
        rows.append(row([s, T.STATUS_LABEL[s][1],
                         fcell("COUNTIFS", rng("BOQ_LINES", first, last, "status"), T.STATUS_LABEL[s][0],
                               rng("BOQ_LINES", first, last, "cls"), "ADDITIVE", expect=n),
                         fcell("DIV", ref("COVERAGE", s, "lines"), ref("COVERAGE", "TOTAL", "lines"))],
                        cls="TRACE_ONLY", status=s, key=s))
    rows.append(row(["TOTAL", "", fcell("SUM", rng("COVERAGE", "COMPUTED", "BLOCKED", "lines"),
                                        expect=sum(1 for r in line_rows if r["cls"] == "ADDITIVE")), ""], role="TOTAL", key="TOTAL"))
    return section("COVERAGE", T.section("COVERAGE"), cols, rows, kind="coverage",
                   note="Counts of ADDITIVE report lines by status (COUNTIFS over PROJECT BOQ LINES) - quantities in different "
                        "units cannot be added, so coverage is by line, not by quantity.")


def assemble(project: dict, lines: list, sheets: list, regs, *, levels=None, key_notes=()) -> dict:
    levels = [lv for lv in LEVEL_ORDER if any(p["level"] == lv for ln in lines for p in ln["parts"])] if levels is None else levels
    head_cols = [col("k", "ITEM", "", "text", width=24), col("v", "VALUE", "", "text", width=60)]
    head_rows = [row([k, v], role="NOTE") for k, v in project["header"]]
    lv_cols = [col(lv, T.level(lv)[0], T.level(lv)[1], "qty", width=11) for lv in levels]
    trade_cols = [col("trade", "TRADE", "البند", "text", width=22), col("desc_ar", "DESCRIPTION AR", "الوصف", "ar", width=24),
                  col("desc_en", "DESCRIPTION EN", "", "text", width=40), col("qty", "QTY", "الكمية", "qty", width=13),
                  col("unit", "UNIT", "الوحدة", "text", width=6), col("status", "STATUS", "الحالة", "status", width=10),
                  col("note", "COVERAGE / NOTE", "ملاحظة", "text", width=44), col("cls", "CLASS", "", "cls", width=11)]
    line_cols = [col("code", "ITEM CODE", "رمز البند", "code", width=14), col("desc_ar", "DESCRIPTION AR", "الوصف", "ar", width=24),
                 col("desc_en", "DESCRIPTION EN", "", "text", width=34), col("unit", "UNIT", "", "text", width=6),
                 col("status", "STATUS", "الحالة", "status", width=10), col("cls", "CLASS", "", "cls", width=11)] + lv_cols + \
                [col("total", "LINE TOTAL", "الإجمالي", "qty", width=12), col("note", "NOTE", "", "text", width=30)]
    line_rows = _line_rows(lines, levels)
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
        _coverage([r for r in line_rows]),
        section("KEY_NOTES", T.section("KEY_NOTES"), [col("n", "NOTE", "", "text", width=120)], notes, kind="notes"),
        section("BOQ_LINES", ("PROJECT BOQ LINES (ADDITIVE)", "بنود المشروع"), line_cols, line_rows,
                note="The canonical lines: ADDITIVE lines are the only quantities that build the totals above; "
                     "ALTERNATIVE_MEASURE lines are the same item on another basis - never add both.")])
    for s in sheets:
        if s["role"] != "SUMMARY":
            s["note"] = ONLY_SUMMARY if s["role"] in ("BREAKDOWN", "SCHEDULE") else s.get("note")
    model = {"SCHEMA": "URBAN_REPORTING_MODEL_V2", "policy": POLICY_ID, "project": project, "inputs": regs.inputs(),
             "levels": levels, "lines": lines, "sheets": [summary] + list(sheets), "glossary": T.glossary_record()}
    evaluate(model)
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


# ------------------------------------------------------------------ QS reconciliation (manual check) sheet
RECON_NAME = "08_QS_RECONCILIATION"
ARCH_TRADES = ("PHYSICAL_AREA", "CEILING", "SKIRTING", "BLOCKWORK", "PLASTER", "PAINT", "FLOOR_TILE", "WALL_TILE",
               "WATERPROOFING", "MARBLE", "ALUMINIUM_GLAZING", "HIDDEN_PROFILE")
TOL_MATCH, TOL_CLOSE = 0.005, 0.03
RSTATUS_ORDER = ("MATCH", "CLOSE", "REVIEW", "NOT COMPARABLE", "ENGINE BLOCKED", "NOT CHECKED")


def recon_cols(first, manual=("MANUAL / CHECK QTY", "كمية التدقيق")):
    """Urban (locked) | manual check (yellow input, or a check formula) | difference / % / status (blue formulas)."""
    return first + [col("urban", "URBAN ENGINE QTY", "كمية أوربن", "qty", width=13), col("unit", "UNIT", "الوحدة", "text", width=6),
                    col("ustatus", "URBAN STATUS", "حالة أوربن", "status", width=10),
                    col("manual", manual[0], manual[1], "qty", width=13),
                    col("diff", "DIFFERENCE (manual - Urban)", "الفرق", "qty", width=12), col("pct", "DIFFERENCE %", "نسبة الفرق", "pct", width=9),
                    col("rstatus", "RECONCILIATION STATUS", "حالة المطابقة", "rstatus", width=15)]


def recon_tail(sec, key, urban, unit, ustatus, manual=None):
    """The urban / manual / formula cells of one reconciliation row (same-row references; tolerances from PARAMS)."""
    m = manual if manual is not None else inp(None)
    u, mm = ref(sec, key, "urban"), ref(sec, key, "manual")
    return [urban, unit, ustatus, m, fcell("DIFF", u, mm, fmt=unit), fcell("PCT", u, mm),
            fcell("RSTATUS", u, mm, ref("PARAMS", "MATCH", "v"), ref("PARAMS", "CLOSE", "v"))]


def total_tail(sec, key, unit, urban_args, manual_args, expect):
    """A subtotal / total row: Urban = SUM of numeric Urban cells (validated against the deterministic sum), manual =
    SUM of the typed checks (blank while none is typed)."""
    return recon_tail(sec, key, fcell("SUM", *urban_args, expect=expect, fmt=unit), unit, None,
                      manual=fcell("SUMNB", *manual_args, fmt=unit))


def _params_section():
    cols = [col("k", "SETTING", "الإعداد", "text", width=30), col("v", "VALUE", "القيمة", "pct", width=10),
            col("n", "MEANING", "", "text", width=100)]
    rows = [row(["MATCH tolerance", inp(TOL_MATCH, "pct"), "|manual / Urban - 1| within this -> MATCH (editable)"], role="NOTE", key="MATCH"),
            row(["CLOSE tolerance", inp(TOL_CLOSE, "pct"), "within this -> CLOSE; beyond -> REVIEW (editable)"], role="NOTE", key="CLOSE"),
            row(["Colour key", "", "WHITE / GREY = Urban engine and report values (locked) · LIGHT YELLOW = your manual input · "
                 "LIGHT BLUE = reconciliation formula · GREEN / AMBER / RED = MATCH / CLOSE / REVIEW · GREY = ENGINE BLOCKED / "
                 "NOT CHECKED / NOT COMPARABLE"], role="NOTE", key="LEGEND"),
            row(["Status rules", "", "ENGINE BLOCKED = Urban has no quantity (never a mismatch, no %) · NOT COMPARABLE = no Urban "
                 "quantity on this basis, or a non-numeric check · NOT CHECKED = no manual value yet · Urban = 0: MATCH only "
                 "if the check is 0"], role="NOTE", key="RULES"),
            row(["Boundary", "", "Urban engine = the official QTO, copied verbatim from the frozen registers. Your manual values "
                 "are a reconciliation only: nothing typed here flows back into the engine, the registers or the totals on "
                 "00_TOTAL_SUMMARY. Sheets are protected without a password so engine cells are not edited by accident."],
                role="NOTE", key="BOUNDARY")]
    return section("PARAMS", ("CHECK SETTINGS / LEGEND", "إعدادات التدقيق"), cols, rows, kind="params")


def _blocks(levels, blocks):
    if blocks is None:
        return [(lv, T.level(lv), [lv]) for lv in levels]
    return [(k, T.level(k), lvs) for k, lvs in blocks if any(lv in levels for lv in lvs)]


def reconciliation_sheet(lines, levels, extra_sections=(), *, blocks=None):
    """08_QS_RECONCILIATION. ITEMS: every line share by floor block - Urban value locked, manual check typed in, difference
    / % / status formulas; inside a block the items of one group are contiguous and close with a SUBTOTAL; the PROJECT
    block adds the groups over all floors. Then check progress, an architectural block and the adapter's structural
    check blocks. ADDITIVE classes are never used here: every Urban cell is BREAKDOWN_ONLY of a 00 line."""
    first = [col("rt", "ROW TYPE", "نوع السطر", "code", width=9), col("code", "ITEM CODE", "رمز البند", "code", width=13),
             col("floor", "FLOOR", "الدور", "text", width=13), col("trade", "TRADE", "البند", "text", width=17),
             col("group", "ITEM GROUP", "المجموعة", "text", width=20), col("elem", "ROOM / ELEMENT", "الغرفة / العنصر", "text", width=22),
             col("en", "DESCRIPTION EN", "", "text", width=28), col("ar", "DESCRIPTION AR", "الوصف", "ar", width=22)]
    cols = recon_cols(first) + [col("notes", "CHECK NOTES", "ملاحظات التدقيق", "text", width=24)]
    sec = "ITEMS"
    by_id = {ln["id"]: ln for ln in lines}
    place = lambda ln: _group(by_id[ln["alternative_of"]]) if ln.get("alternative_of") in by_id else _group(ln)
    rows, proj, block_rows = [], OrderedDict(), OrderedDict()
    blank = [None] * 7

    def band(k, en, ar):
        rows.append(row(["FLOOR", "", en, "", "", "", "", ar] + blank + [""], role="NOTE", note="GROUP", key=f"B:{k}"))

    for bk, (ben, bar), lvs in _blocks(levels, blocks):
        band(bk, ben, bar)
        start = len(rows)
        groups = OrderedDict()
        for ln in lines:
            for pi, p in enumerate(ln["parts"]):
                if p["level"] in lvs:
                    groups.setdefault(place(ln), {"add": [], "alt": []})["alt" if ln["cls"] != "ADDITIVE" else "add"].append((ln, pi, p))
        for g, d in groups.items():
            gk, gen, gar = g
            keys = []
            for kind in ("add", "alt"):
                for ln, pi, p in d[kind]:
                    k = f"I:{ln['id']}:{pi}"
                    urban = p["cell"] | {"unit": ln["unit"]} if p["cell"]["q"] is not None else p["cell"]
                    lvname = T.level(p["level"])[0]
                    rows.append(row(["ITEM" if kind == "add" else "ALT ITEM", ln["id"], lvname, T.trade(ln["trade"])[0], gen,
                                     p.get("note") or "", ln["desc_en"] + (f" (same item as {ln['alternative_of']} - not added)"
                                                                          if kind == "alt" else ""), ln["desc_ar"]] +
                                    recon_tail(sec, k, urban, ln["unit"], p["status"]) + [inp(None, "text")],
                                    cls="BREAKDOWN_ONLY" if kind == "add" else "ALTERNATIVE_MEASURE", status=p["status"],
                                    tech=p["tech"], explains=f"{ln['id']}@{p['level']}", key=k))
                    if kind == "add":
                        keys.append((k, p["cell"]["q"]))
            nums = [q for _, q in keys if q is not None]
            if not nums:
                continue
            unit = d["add"][0][0]["unit"]
            if len(keys) >= 2:
                k = f"S:{bk}:{gk}"
                rows.append(row(["SUBTOTAL", "", ben, "", gen, f"{len(keys)} rows", f"floor subtotal - {gen}", gar] +
                                total_tail(sec, k, unit, [rng(sec, keys[0][0], keys[-1][0], "urban")],
                                           [rng(sec, keys[0][0], keys[-1][0], "manual")], dsum(nums)) + [""],
                                role="SUBTOTAL", key=k))
                proj.setdefault(g, []).append((k, dsum(nums), unit))
            else:
                proj.setdefault(g, []).append((keys[0][0] if keys[0][1] is not None else None, dsum(nums), unit))
        block_rows[bk] = (ben, [r["key"] for r in rows[start:]])
    pen, par = T.level("PROJECT")
    band("PROJECT", pen, par)
    for g, parts in proj.items():
        gk, gen, gar = g
        k = f"P:{gk}"
        rows.append(row(["TOTAL", "", pen, "", gen, "all floors", f"project total - {gen}", gar] +
                        total_tail(sec, k, parts[0][2], [ref(sec, x, "urban") for x, _, _ in parts if x],
                                   [ref(sec, x, "manual") for x, _, _ in parts if x], dsum(q for _, q, _ in parts)) + [""],
                        role="TOTAL", key=k))
    items = section(sec, ("ITEM RECONCILIATION - BY FLOOR", "مطابقة البنود حسب الدور"), cols, rows,
                    note="One row per Urban line share. Type your quantity in MANUAL / CHECK QTY (yellow); DIFFERENCE, DIFFERENCE % "
                         "and RECONCILIATION STATUS are formulas (blue). SUBTOTAL / TOTAL rows add the ITEM rows only - ALT ITEM "
                         "rows are the same item on another basis and are never added. ENGINE BLOCKED rows have no Urban quantity: "
                         "a manual value may be typed for reference, no % is calculated and the row is never a mismatch.")
    items["filter"] = True
    items["floor_blocks"] = True
    # check progress per floor block
    pcols = [col("floor", "FLOOR", "الدور", "text", width=24), col("rows", "ITEM ROWS", "عدد البنود", "count", width=9),
             col("checked", "CHECKED", "تم تدقيقه", "count", width=9)] + \
        [col(s.lower().replace(" ", "_"), s, "", "count", width=11) for s in RSTATUS_ORDER]
    prow = []
    for bk, (ben, keys) in block_rows.items():
        its = [k for k in keys if k.startswith("I:")]
        if not its:
            continue
        a, b = keys[0], keys[-1]
        R, M_ = rng(sec, a, b, "rt"), rng(sec, a, b, "manual")
        n_item = sum(1 for r in rows if r.get("key") in keys and r["cells"][0] == "ITEM")
        cells = [ben, fcell("COUNTIFS", R, "ITEM", expect=n_item), fcell("COUNTIFS", R, "ITEM", M_, "<>")]
        cells += [fcell("COUNTIFS", R, "ITEM", rng(sec, a, b, "rstatus"), s) for s in RSTATUS_ORDER]
        prow.append(row(cells, role="NOTE", key=f"PR:{bk}"))
    if prow:
        ks = [r["key"] for r in prow]
        prow.append(row([pen] + [fcell("SUM", rng("PROGRESS", ks[0], ks[-1], c["key"])) for c in pcols[1:]], role="TOTAL", key="PR:TOTAL"))
    progress = section("PROGRESS", ("CHECK PROGRESS BY FLOOR", "تقدم التدقيق حسب الدور"), pcols, prow,
                       note="Counts of ITEM rows of the item table below (formulas); they update as manual quantities are typed.")
    # architectural reconciliation (project level, one row per item group)
    acols = recon_cols([col("group", "ITEM GROUP", "المجموعة", "text", width=34), col("ar", "", "", "ar", width=22),
                        col("lines", "URBAN LINES", "البنود", "code", width=22)]) + [col("notes", "CHECK NOTES", "ملاحظات التدقيق", "text", width=24)]
    seen = OrderedDict()
    for ln in lines:
        if ln["trade"] in ARCH_TRADES and ln["cls"] == "ADDITIVE":
            seen.setdefault(_group(ln), []).append(ln)
    for t in ("MARBLE", "HIDDEN_PROFILE"):
        if not any(ln["trade"] == t for ln in lines):
            en, ar = T.trade(t)
            seen.setdefault((f"NONE:{t}", en, ar), [])
    arows = []
    for (gk, gen, gar), lns in seen.items():
        k = f"A:{gk}"
        nums = [x for x in lns if x["qty"]["q"] is not None]
        if not lns:
            urban, st, unit = na("NOT MEASURED"), "INFO", ""
        elif nums:
            urban = (qsum([x["qty"] for x in nums]) if len(nums) > 1 else dict(nums[0]["qty"])) | {"unit": lns[0]["unit"]}
            st, unit = worst([x["status"] for x in lns]), lns[0]["unit"]
            st = "PARTIAL" if st == "BLOCKED" else st
        else:
            urban, st, unit = blocked("ALL_LINES_BLOCKED"), "BLOCKED", lns[0]["unit"]
        arows.append(row([gen if lns else f"{gen} - not measured in this run (no register)", gar, ", ".join(x["id"] for x in lns)] +
                         recon_tail("ARCH", k, urban, unit, st) + [inp(None, "text")],
                         cls="BREAKDOWN_ONLY" if lns else "TRACE_ONLY", status=st, key=k))
    arch = section("ARCH", ("ARCHITECTURAL RECONCILIATION - PROJECT", "مطابقة الأعمال المعمارية - المشروع"), acols, arows,
                   note="One row per architectural item group: the Urban value is the project total of its ADDITIVE lines (blocked "
                        "lines excluded, never 0). NOT MEASURED = no Urban register for that item - a manual value is NOT COMPARABLE.")
    return sheet(RECON_NAME, ("QS RECONCILIATION / MANUAL CHECK", "المطابقة والتدقيق اليدوي"), "RECON",
                 [_params_section(), progress, items, arch] + list(extra_sections))
