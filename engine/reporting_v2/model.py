"""REPORTING MODEL V2 - the one presentation model both renderers (XLSX, PDF) draw from. It measures NOTHING.

FORMULA POLICY (Reporting V2 + QS reconciliation addendum): no formula ever creates or replaces an engine quantity;
engine quantities are register values copied verbatim (locked cells). Formulas are allowed ONLY for report totals /
subtotals, manual QS check arithmetic, differences, percentages, reconciliation status and coverage counts. A formula
cell is a structured spec {"f": {"op", "args"}, "v": evaluated value, "expect": deterministic value or None}: the
renderer writes it as an Excel formula, evaluate() computes it in Python (exact decimal sums), validate() requires
v == expect for every report total. Manual input cells {"input": value} are the only editable cells.

A quantity cell is one of:
    {"q": v, "src": "REGISTER:/json/pointer"}    a value copied from a frozen register (re-resolved by validate())
    {"q": v, "sum": [src, ...]}                   DECLARED_SUM: a plain sum of register values (same trade + unit),
                                                  every addend recorded - the only arithmetic allowed
    {"q": None, "blocked": code}                  no quantity; never written as 0
    {"q": None, "na": text}                       not applicable / not published by any register
Every displayed item row has a class:
    ADDITIVE            one canonical line per physical item; lives on the summary sheet only
    BREAKDOWN_ONLY      repeats / explains an ADDITIVE line (names it in 'explains'); never added again
    ALTERNATIVE_MEASURE the same physical item on another basis or unit
    TRACE_ONLY          evidence / QA / counts; no quantity to add
SUBTOTAL / TOTAL rows are declared sums of ADDITIVE item rows of one unit.

Technical status codes are kept on every row; the four display states are a presentation alias (STATUS_ALIAS +
prefix rules). An unknown code fails the build - nothing is silently re-labelled.
"""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from pathlib import Path

POLICY_ID = "URBAN_REPORTING_MODEL_V2"
STATUS_TEXT = {"COMPUTED": "Computed", "PARTIAL": "Partial", "REVIEW": "Review", "BLOCKED": "Blocked", "INFO": "Info"}
CLASSES = ("ADDITIVE", "BREAKDOWN_ONLY", "ALTERNATIVE_MEASURE", "TRACE_ONLY")
ROLES = ("ITEM", "SUBTOTAL", "TOTAL", "NOTE")
DISPLAY = ("COMPUTED", "PARTIAL", "REVIEW", "BLOCKED", "INFO")
UNITS = ("m3", "m2", "lm", "m", "nr", "kg")
SHEET_ROLES = ("SUMMARY", "BREAKDOWN", "SCHEDULE", "INFO", "TECH", "RECON")
TOL = 1e-9

# exact technical code -> display state (presentation alias only; the code stays on the row)
STATUS_ALIAS = {
    "COMPUTED": "COMPUTED", "COMPUTED_SHADOW_COMPLETE": "COMPUTED", "PROVEN": "COMPUTED", "MEASURED": "COMPUTED",
    "PROVEN_UNBOUND_DOMINATED": "COMPUTED", "SLAB_SOFFIT": "COMPUTED", "CLOSED / COMPUTED": "COMPUTED",
    "CERTIFIED_WITH_OWNER_FACT": "COMPUTED", "MEASURED_WITH_WIDTH_DEVIATION": "COMPUTED", "BOUND": "COMPUTED",
    "COMPLETE (MIN_RADIUS_ARC, method)": "COMPUTED", "PASS": "COMPUTED", "RELEASED": "COMPUTED",
    "DOOR": "COMPUTED",
    "COMPUTED_PARTIAL": "PARTIAL", "AUTHORISED_SUBTOTAL": "PARTIAL", "COMPUTED_FROM_TYPICAL_DETAIL": "PARTIAL",
    "WINDOW_CANDIDATE": "PARTIAL",
    "OWNER_DERIVED_REVIEW_REQUIRED": "REVIEW", "REVIEW_REQUIRED": "REVIEW", "REGION_FROM_SLAB_OPENING": "REVIEW",
    "GLAZED_OPENING_FUNCTION_UNKNOWN": "REVIEW", "ESTABLISHED": "INFO", "NOT_ESTABLISHED": "INFO",
    "SOURCE_CONFLICT": "BLOCKED", "UNRESOLVED": "BLOCKED", "NOT_CLOSED": "BLOCKED", "NO_BAND_ADJACENT_TO_TAG": "BLOCKED",
    "NO_BAND_AT_SCHEDULED_BREADTH": "BLOCKED", "NO_BAND_PARALLEL_TO_TAG": "BLOCKED", "TAG_INSIDE_SUPPORT": "BLOCKED",
    "SPAN_COUNT_MISMATCH": "BLOCKED", "BAND_TYPE_CONFLICT": "BLOCKED", "NOT_TAGGED_ON_PLAN": "INFO",
    "NOT_DRAWN_ON_STOREY_SHEET": "INFO", "NOT_IN_STOREY": "INFO", "INFO": "INFO", "NOT_MEASURED": "INFO",
    "NOT_IN_SCOPE": "INFO", "FAIL": "BLOCKED",
}
PREFIX_ALIAS = (("BLOCKED", "BLOCKED"), ("PARTIAL", "PARTIAL"), ("COMPUTED_PARTIAL", "PARTIAL"),
                ("NOT_CLOSED", "BLOCKED"), ("REVIEW", "REVIEW"))
SEVERITY = {"BLOCKED": 4, "PARTIAL": 3, "REVIEW": 2, "COMPUTED": 1, "INFO": 0}


def display_status(code: str) -> str:
    if code in STATUS_ALIAS:
        return STATUS_ALIAS[code]
    for p, d in PREFIX_ALIAS:
        if code.startswith(p):
            return d
    raise KeyError(f"technical status {code!r} has no display alias")


def alias_table(codes) -> list:
    return [[c, display_status(c), "exact" if c in STATUS_ALIAS else "prefix"] for c in sorted(set(codes))]


# ------------------------------------------------------------------ registers
class Registers:
    """Frozen register files, read-only. ref = 'NAME:/json/pointer' (RFC 6901 tokens; '~1' = '/')."""

    def __init__(self, files: dict, root: Path | None = None):
        self.files = {n: Path(p) for n, p in files.items()}
        self.root = root
        self.data = {n: json.loads(p.read_text()) for n, p in self.files.items()}
        self.sha = {n: hashlib.sha256(p.read_bytes()).hexdigest() for n, p in self.files.items()}
        self.used = set()

    def get(self, ref: str):
        name, _, ptr = ref.partition(":")
        o = self.data[name]
        for tok in [t for t in ptr.split("/") if t != ""]:
            tok = tok.replace("~1", "/").replace("~0", "~")
            o = o[int(tok)] if isinstance(o, list) else o[tok]
        self.used.add(name)
        return o

    def q(self, ref: str) -> dict:
        v = self.get(ref)
        if v is not None and (isinstance(v, bool) or not isinstance(v, (int, float))):
            raise TypeError(f"{ref} is not a number: {v!r}")
        return {"q": v, "src": ref} if v is not None else {"q": None, "blocked": "NULL_IN_REGISTER", "src": ref}

    def inputs(self) -> dict:
        rel = (lambda p: str(p.relative_to(self.root)) if self.root else str(p))
        return {n: {"file": rel(self.files[n]), "sha256": self.sha[n]} for n in sorted(self.files)}


def ptr(*parts) -> str:
    return "/" + "/".join(str(p).replace("~", "~0").replace("/", "~1") for p in parts)


def dsum(values) -> float:
    """Exact decimal addition of register values (their shortest decimal form): no binary rounding noise, no rounding."""
    values = list(values)
    if all(isinstance(v, int) and not isinstance(v, bool) for v in values):
        return sum(values)
    return float(sum((Decimal(repr(v)) for v in values), Decimal(0)))


def qsum(cells) -> dict:
    """DECLARED_SUM of numeric register cells (or of other declared sums)."""
    cells = list(cells)
    if not cells:
        raise ValueError("empty declared sum")
    srcs = []
    for c in cells:
        if not is_q(c) or c["q"] is None:
            raise ValueError(f"declared sum over a non-numeric cell {c!r}")
        srcs += c["sum"] if "sum" in c else [c["src"]]
    return {"q": dsum(c["q"] for c in cells), "sum": srcs}


def blocked(code: str, src: str | None = None) -> dict:
    return {"q": None, "blocked": code} | ({"src": src} if src else {})


def na(text: str) -> dict:
    return {"q": None, "na": text}


def is_q(c) -> bool:
    return isinstance(c, dict) and "q" in c


# ------------------------------------------------------------------ formulas and manual inputs
FORMULA_OPS = ("SUM", "SUMNB", "DIFF", "PCT", "RSTATUS", "PROD", "COUNTIFS", "COUNT", "DIV")
RSTATUS = ("MATCH", "CLOSE", "REVIEW", "NOT COMPARABLE", "ENGINE BLOCKED", "NOT CHECKED")


def ref(sec, rowkey, colkey) -> dict:
    """A cell of the same sheet: section id, row key, column key."""
    return {"ref": [sec, rowkey, colkey]}


def rng(sec, rk1, rk2, colkey) -> dict:
    return {"range": [sec, rk1, rk2, colkey]}


def sub(a, b) -> dict:
    """A PROD factor (a - b), e.g. beam depth below the slab D - t."""
    return {"sub": [a, b]}


def fcell(op, *args, expect=None, fmt=None) -> dict:
    if op not in FORMULA_OPS:
        raise ValueError(op)
    return {"f": {"op": op, "args": list(args)}, "v": None, "expect": expect, "fmt": fmt}


def inp(value=None, itype="num") -> dict:
    """A manual-check input cell (the only editable cells); value = an optional pre-fill from the source schedule."""
    return {"input": value, "itype": itype}


def qty_text(c) -> str:
    """The text written for an empty quantity: BLOCKED (never 0) or the not-applicable text."""
    return "BLOCKED" if "blocked" in c else (c.get("na") or "—")


def is_f(c) -> bool:
    return isinstance(c, dict) and "f" in c


def is_in(c) -> bool:
    return isinstance(c, dict) and "input" in c


def _sheet_index(sheet):
    idx = {}
    for sec in sheet["sections"]:
        keys = {c["key"]: j for j, c in enumerate(sec["columns"])}
        keys["__kinds__"] = [c["kind"] for c in sec["columns"]]
        for i, r in enumerate(sec["rows"]):
            rk = r.get("key", i)
            idx[(sec["id"], rk)] = (r, keys, i)
        idx[("__order__", sec["id"])] = [r.get("key", i) for i, r in enumerate(sec["rows"])]
    return idx


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def evaluate(model) -> int:
    """Compute v for every formula cell (Python mirror of the Excel formulas). Returns the number of formula cells."""
    n = 0
    for s in model["sheets"]:
        idx = _sheet_index(s)
        memo = {}

        def cell_value(sec, rk, ck):
            r, keys, _ = idx[(sec, rk)]
            j = keys[ck]
            if j >= len(r["cells"]):
                return None
            c = r["cells"][j]
            if keys["__kinds__"][j] == "status" and c in STATUS_TEXT:
                return STATUS_TEXT[c]
            if is_q(c):
                return c["q"] if c["q"] is not None else qty_text(c)
            if is_in(c):
                return c["input"]
            if is_f(c):
                return fval(c, (sec, rk, ck))
            return c

        def values(a):
            if "ref" in a:
                return [cell_value(*a["ref"])]
            sec, k1, k2, ck = a["range"]
            order = idx[("__order__", sec)]
            i1, i2 = order.index(k1), order.index(k2)
            return [cell_value(sec, k, ck) for k in order[i1:i2 + 1]]

        def fval(c, key):
            if key in memo:
                return memo[key]
            op, args = c["f"]["op"], c["f"]["args"]
            if op == "SUM":
                v = dsum([x for a in args for x in values(a) if _num(x)])
            elif op == "SUMNB":
                xs = [x for a in args for x in values(a) if _num(x)]
                v = dsum(xs) if xs else ""
            elif op == "DIFF":
                u, mm = values(args[0])[0], values(args[1])[0]
                v = round(mm - u, 9) if _num(u) and _num(mm) else ""        # ROUND(m-u, 9): no -0.000 from float noise
            elif op == "PCT":
                u, mm = values(args[0])[0], values(args[1])[0]
                v = round((mm - u) / u, 9) if _num(u) and _num(mm) and u != 0 else ""
            elif op == "RSTATUS":
                u, mm = values(args[0])[0], values(args[1])[0]
                t1, t2 = values(args[2])[0], values(args[3])[0]
                if u == "BLOCKED":
                    v = "ENGINE BLOCKED"
                elif not _num(u):
                    v = "NOT COMPARABLE"
                elif mm is None or mm == "":
                    v = "NOT CHECKED"
                elif not _num(mm):
                    v = "NOT COMPARABLE"
                elif u == 0:
                    v = "MATCH" if abs(mm) <= 1e-9 else "REVIEW"
                else:
                    e = abs(mm / u - 1)
                    v = "MATCH" if e <= t1 else ("CLOSE" if e <= t2 else "REVIEW")
            elif op == "PROD":
                *fs, div = args
                xs = []
                for a in fs:
                    if "sub" in a:                                       # (a - b) factor
                        x, y = values(a["sub"][0])[0], values(a["sub"][1])[0]
                        xs.append(x - y if _num(x) and _num(y) else None)
                    else:
                        xs.extend(values(a))
                if all(_num(x) for x in xs):
                    p = 1.0
                    for x in xs:
                        p *= x
                    v = p / div
                else:
                    v = ""
            elif op == "COUNTIFS":
                pairs = list(zip(args[0::2], args[1::2]))
                cols = [values(a) for a, _ in pairs]
                hit = lambda x, crit: x not in (None, "") if crit == "<>" else x == crit
                v = sum(1 for row_vals in zip(*cols) if all(hit(x, crit) for x, (_, crit) in zip(row_vals, pairs)))
            elif op == "COUNT":
                v = sum(1 for a in args for x in values(a) if _num(x))
            elif op == "DIV":
                a, b = values(args[0])[0], values(args[1])[0]
                v = a / b if _num(a) and _num(b) and b else ""
            memo[key] = v
            c["v"] = v
            return v

        for sec in s["sections"]:
            keys = [c["key"] for c in sec["columns"]]
            for i, r in enumerate(sec["rows"]):
                for j, c in enumerate(r["cells"]):
                    if is_f(c):
                        fval(c, (sec["id"], r.get("key", i), keys[j]))
                        n += 1
    return n


def worst(states) -> str:
    states = [s for s in states if s]
    return max(states, key=lambda s: SEVERITY[s]) if states else "INFO"


def combine(parts) -> str:
    """Status of a line from its parts: numbers + any blocked / partial -> PARTIAL; none numeric -> BLOCKED."""
    st = [p["status"] for p in parts]
    has_num = any(is_q(p["cell"]) and p["cell"]["q"] is not None for p in parts)
    w = worst(st)
    if w == "BLOCKED":
        return "PARTIAL" if has_num else "BLOCKED"
    return w


# ------------------------------------------------------------------ builders
def part(level, cell, tech, note=None) -> dict:
    """One level's share of a line: a register cell (or declared sum) with its technical status."""
    return {"level": level, "cell": cell, "tech": tech, "status": display_status(tech), "note": note}


def line(lid, trade, desc_en, desc_ar, unit, parts, *, cls="ADDITIVE", note=None, alternative_of=None, basis=None,
         status=None) -> dict:
    nums = [p["cell"] for p in parts if p["cell"]["q"] is not None]
    qty = qsum(nums) if nums else blocked("NO_NUMERIC_PART")
    if len(nums) == 1:
        qty = dict(nums[0])
    return {"id": lid, "trade": trade, "desc_en": desc_en, "desc_ar": desc_ar, "unit": unit, "parts": parts,
            "qty": qty, "status": status or combine(parts), "cls": cls, "note": note, "alternative_of": alternative_of,
            "basis": basis}


def col(key, en, ar="", kind="text", unit=None, width=None):
    """kind: text | ar | qty | count | dim | status | code | cls | pct | num | rstatus"""
    return {"key": key, "en": en, "ar": ar, "kind": kind, "unit": unit, "width": width}


def row(cells, *, role="ITEM", cls=None, status=None, tech=None, explains=None, note=None, key=None):
    if role == "ITEM" and cls is None and any(is_q(c) for c in cells):
        raise ValueError("an item row with a quantity needs a class")
    r = {"role": role, "cls": cls, "status": status, "tech": tech, "explains": explains, "note": note, "cells": list(cells)}
    if key is not None:
        r["key"] = key
    return r


def section(sid, title, columns, rows, *, kind="table", note=None):
    return {"id": sid, "title_en": title[0], "title_ar": title[1], "kind": kind, "columns": columns, "rows": rows,
            "note": note}


def sheet(name, title, role, sections, *, level=None, note=None):
    assert role in SHEET_ROLES
    return {"name": name, "title_en": title[0], "title_ar": title[1], "role": role, "level": level,
            "sections": sections, "note": note}


# ------------------------------------------------------------------ validation
def iter_cells(model):
    for s in model["sheets"]:
        for sec in s["sections"]:
            for i, r in enumerate(sec["rows"]):
                for j, c in enumerate(r["cells"]):
                    yield s, sec, i, r, j, c


def validate(model, regs: Registers) -> dict:
    problems, nq, nsum = [], 0, 0
    lines = {ln["id"]: ln for ln in model["lines"]}
    if len(lines) != len(model["lines"]):
        problems.append("duplicate ADDITIVE line id")
    summary = [s for s in model["sheets"] if s["role"] == "SUMMARY"]
    if len(summary) != 1 or model["sheets"][0] is not summary[0]:
        problems.append("exactly one SUMMARY sheet, first")

    def check_q(c, where):
        nonlocal nq, nsum
        if c["q"] is None:
            if not ({"blocked", "na"} & set(c)):
                problems.append(f"{where}: empty quantity without blocked / na marker")
            return
        if isinstance(c["q"], bool) or not isinstance(c["q"], (int, float)):
            problems.append(f"{where}: non-numeric quantity")
            return
        nq += 1
        if "src" in c:
            if regs.get(c["src"]) != c["q"]:
                problems.append(f"{where}: {c['src']} = {regs.get(c['src'])!r} != shown {c['q']!r}")
        elif "sum" in c:
            nsum += 1
            tot = dsum(regs.get(s) for s in c["sum"])
            if abs(tot - c["q"]) > TOL:
                problems.append(f"{where}: declared sum {tot} != shown {c['q']}")
        else:
            problems.append(f"{where}: quantity without source")

    for ln in model["lines"]:
        if ln["cls"] not in ("ADDITIVE", "ALTERNATIVE_MEASURE"):
            problems.append(f"line {ln['id']}: class {ln['cls']}")
        if ln["unit"] not in UNITS:
            problems.append(f"line {ln['id']}: unit {ln['unit']}")
        if ln["status"] not in DISPLAY:
            problems.append(f"line {ln['id']}: status {ln['status']}")
        nums = [p["cell"] for p in ln["parts"] if p["cell"]["q"] is not None]
        for p in ln["parts"]:
            check_q(p["cell"], f"line {ln['id']} {p['level']}")
            display_status(p["tech"])
        if nums:
            if abs(dsum(c["q"] for c in nums) - ln["qty"]["q"]) > TOL:
                problems.append(f"line {ln['id']}: parts do not add to the line")
        elif ln["qty"]["q"] is not None:
            problems.append(f"line {ln['id']}: quantity without numeric parts")
        if ln["status"] == "COMPUTED" and any(p["status"] in ("BLOCKED", "PARTIAL") for p in ln["parts"]):
            problems.append(f"line {ln['id']}: COMPUTED with blocked / partial parts")
        if ln.get("alternative_of") and ln["alternative_of"] not in lines:
            problems.append(f"line {ln['id']}: alternative of unknown line")

    seen_add = set()
    for s, sec, i, r, j, c in iter_cells(model):
        where = f"{s['name']}/{sec['id']}/{i}/{j}"
        if is_q(c):
            check_q(c, where)
        if j == 0:
            if r["role"] not in ROLES:
                problems.append(f"{where}: role {r['role']}")
            if r["role"] == "ITEM" and any(is_q(x) for x in r["cells"]):
                if r["cls"] not in CLASSES:
                    problems.append(f"{where}: class {r['cls']}")
                if r["cls"] == "ADDITIVE" and s["role"] != "SUMMARY":
                    problems.append(f"{where}: ADDITIVE row outside the summary sheet")
                if s["role"] == "SUMMARY" and r["cls"] in ("ADDITIVE", "ALTERNATIVE_MEASURE") and r["explains"] in lines:
                    if lines[r["explains"]]["cls"] != r["cls"]:
                        problems.append(f"{where}: summary row class differs from its line")
                    seen_add.add(r["explains"])
                elif r["cls"] == "ADDITIVE":
                    problems.append(f"{where}: ADDITIVE row is not a line")
                if r["cls"] in ("BREAKDOWN_ONLY", "ALTERNATIVE_MEASURE") and r["explains"] is not None and \
                        not r["explains"].startswith("MATRIX@") and r["explains"].split("@")[0] not in lines:
                    problems.append(f"{where}: explains unknown line {r['explains']}")
            if r["status"] is not None and r["status"] not in DISPLAY:
                problems.append(f"{where}: status {r['status']}")
            if r["tech"] is not None:
                try:
                    display_status(r["tech"])
                except KeyError as e:
                    problems.append(f"{where}: {e}")
            for x in r["cells"]:
                if is_q(x) and x["q"] is None and r["status"] == "COMPUTED" and "na" not in x:
                    problems.append(f"{where}: blocked quantity on a COMPUTED row")
    try:
        nf = evaluate(model)
    except (KeyError, ValueError) as e:                                  # a formula that points at a removed row fails closed
        problems.append(f"formula reference unresolved: {e}")
        nf = 0
    for s, sec, i, r, j, c in iter_cells(model):
        if is_f(c) and c.get("expect") is not None:
            v = c["v"]
            if not (_num(v) and abs(v - c["expect"]) <= TOL):
                problems.append(f"{s['name']}/{sec['id']}/{i}/{j}: formula {c['f']['op']} = {v!r} != deterministic {c['expect']!r}")
        if (is_f(c) or is_in(c)) and r["cls"] == "ADDITIVE" and sec["columns"][j]["kind"] == "qty" and is_f(c) is False:
            problems.append(f"{s['name']}/{sec['id']}/{i}/{j}: input cell in an ADDITIVE quantity")
    missing = set(lines) - seen_add
    if missing:
        problems.append(f"ADDITIVE lines not on the summary: {sorted(missing)}")
    return {"state": "PASS" if not problems else "FAIL", "problems": problems, "quantity_cells": nq, "declared_sums": nsum,
            "formula_cells": nf, "lines": len(lines)}


def digest(o) -> str:
    return hashlib.sha256(json.dumps(o, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()
