"""T-548 reconciled-quantities statement builder (any villa; research, unwired, computes no new quantity).

R-T548-1 (proposed, every villa). A reconciled-quantities statement is assembled ONLY from merged reconciliation
reports, each normalised into SECTIONS (one BOQ item family, one unit, one reference figure). The builder:
  (a) accepts the units m2 / lm / m3 / nr / kg only, and a section's rows and lines must all carry the section's unit;
      a statement total is formed per (trade, unit, reference kind) and NEVER across units (m2 + lm refused) or across
      reference kinds (a freelancer row total and an owner-question hand figure are never added together);
  (b) takes the engine VALUED total as the exact Decimal sum of the valued candidate line ids given (a declared total
      that differs is refused: no stale total); a line id is valued, held or excluded, never two of them;
  (c) requires the rows' signed differences (+ = in the reference basis and not in the engine's valued total) to sum
      EXACTLY to reference - engine valued; a table that does not close is refused, never absorbed;
  (d) classes are CLASSES only (the five of the task + TOLERANCE, the merged R-T541-1 class for an engine geometric
      approximation that is not a defect; kept apart so it is never shown as ENGINE_RIGHT agreement); 'AGREE' or any
      other label is refused; every row keeps its source report's own cause beside the class;
  (e) HELD and UNKNOWN are never agreement and never 0: a row whose engine side is HELD must be class HELD (or
      UNRESOLVED) and name at least one held line id of its section; a HELD row with a zero difference, a quantity
      None, or a held line id among the valued lines is refused;
  (f) the engine BOUNDED range is valued + the held lines' own engine bounds: low = AT_LEAST valued + the known held
      lows; high = valued + every held high, or OPEN when any held line has no engine high (a report's drawing-derived
      figure is not an engine bound and never enters the range);
  (g) ENGINE_WRONG rows must name their fix row (a board id); UNRESOLVED rows must be named (a residual is one row).
A section whose reference kind is not FREELANCER is printed with 'freelancer total: no row' and its reference named;
it is never presented as an engine-vs-freelancer figure.
"""
from __future__ import annotations

from decimal import Decimal

CLASSES = ("ENGINE_RIGHT", "ENGINE_WRONG", "RULE_DIFFERENCE", "HELD", "TOLERANCE", "UNRESOLVED")
UNITS = ("m2", "lm", "m3", "nr", "kg")
REFERENCE_KINDS = ("FREELANCER", "OWNER_QUESTION_FIGURE")
ENGINE_STATUSES = ("VALUED", "HELD", "NONE")
SCHEMA = "URBAN_T548_RECONCILED_STATEMENT_V1"


class StatementError(ValueError):
    pass


def D(x, what="quantity") -> Decimal:
    if x is None:
        raise StatementError(f"{what} unknown (None): unknown is never 0")
    if isinstance(x, bool):
        raise StatementError(f"{what}: boolean is not a quantity")
    if isinstance(x, float):
        return Decimal(repr(x))
    try:
        return Decimal(str(x))
    except Exception as e:  # noqa: BLE001
        raise StatementError(f"{what}: {x!r} is not a number") from e


def s(x: Decimal | None) -> str | None:
    if x is None:
        return None
    x = x.normalize()
    t = format(x, "f")
    return "0" if t in ("-0", "") else t


def check_section(sec: dict) -> dict:
    """Validate one normalised section and return its closed summary (rules (a)-(g))."""
    sid = sec.get("section_id") or "?"
    unit = sec.get("unit")
    if unit not in UNITS:
        raise StatementError(f"{sid}: unit {unit!r} refused ({' / '.join(UNITS)} only)")
    ref = sec.get("reference") or {}
    if ref.get("kind") not in REFERENCE_KINDS:
        raise StatementError(f"{sid}: reference kind {ref.get('kind')!r} not in {REFERENCE_KINDS}")
    if not ref.get("basis"):
        raise StatementError(f"{sid}: reference basis not named")
    ref_total = D(ref.get("total"), f"{sid} reference total")
    if ref.get("unit", unit) != unit:
        raise StatementError(f"{sid}: reference unit {ref.get('unit')!r} differs from {unit!r}")
    eng = sec.get("engine") or {}
    seen: dict[str, str] = {}
    valued = Decimal(0)
    for kind in ("valued_lines", "held_lines", "excluded_lines"):
        for ln in eng.get(kind, []):
            lid = ln.get("line_id")
            if not lid:
                raise StatementError(f"{sid}: a {kind[:-6]} line without a line id")
            if lid in seen:
                raise StatementError(f"{sid}: line {lid} is both {seen[lid]} and {kind[:-6]}")
            seen[lid] = kind[:-6]
            if ln.get("unit", unit) != unit:
                raise StatementError(f"{sid}: line {lid} unit {ln.get('unit')!r} differs from {unit!r}")
            if kind == "valued_lines":
                q = D(ln.get("qty"), f"{sid} valued line {lid}")
                if q < 0:
                    raise StatementError(f"{sid}: valued line {lid} negative")
                valued += q
    if "valued_total" in eng and D(eng["valued_total"], f"{sid} declared engine total") != valued:
        raise StatementError(f"{sid}: declared engine total {eng['valued_total']} != sum of valued lines {s(valued)}")
    held = eng.get("held_lines", [])
    low, high, open_hi = valued, valued, False
    for ln in held:
        lo, hi = ln.get("low"), ln.get("high")
        if lo is not None:
            low += D(lo, f"held {ln['line_id']} low")
        if hi is None:
            open_hi = True
        else:
            if lo is not None and D(hi) < D(lo):
                raise StatementError(f"{sid}: held line {ln['line_id']} bound high < low")
            high += D(hi, f"held {ln['line_id']} high")
    held_ids = {ln["line_id"] for ln in held}

    rows = sec.get("rows") or []
    if not rows:
        raise StatementError(f"{sid}: no rows")
    by_class = {c: Decimal(0) for c in CLASSES}
    acc = Decimal(0)
    out_rows = []
    for r in rows:
        name = r.get("name") or ""
        if not name:
            raise StatementError(f"{sid}: a row without a name")
        cls = r.get("class")
        if cls not in CLASSES:
            raise StatementError(f"{sid} / {name}: class {cls!r} refused (classes: {', '.join(CLASSES)})")
        if r.get("unit", unit) != unit:
            raise StatementError(f"{sid} / {name}: unit {r.get('unit')!r} never enters a {unit} total")
        delta = D(r.get("delta"), f"{sid} / {name} difference")
        est = r.get("engine_status")
        if est not in ENGINE_STATUSES:
            raise StatementError(f"{sid} / {name}: engine status {est!r} not in {ENGINE_STATUSES}")
        refs = list(r.get("held_line_ids") or [])
        if est == "HELD" and cls not in ("HELD", "UNRESOLVED"):
            raise StatementError(f"{sid} / {name}: engine side HELD counted as {cls}: HELD is never agreement")
        if cls == "HELD":
            if est != "HELD":
                raise StatementError(f"{sid} / {name}: class HELD but engine status {est}")
            if delta == 0:
                raise StatementError(f"{sid} / {name}: HELD row with zero difference = HELD counted as agreement")
            if not refs:
                raise StatementError(f"{sid} / {name}: HELD row names no held line id")
        for lid in refs:
            if lid not in held_ids:
                raise StatementError(f"{sid} / {name}: {lid} is not a held line of this section"
                                     + (" (it is VALUED)" if seen.get(lid) == "valued" else ""))
        if cls == "ENGINE_WRONG" and not r.get("fix_row"):
            raise StatementError(f"{sid} / {name}: ENGINE_WRONG without a named fix row")
        acc += delta
        by_class[cls] += delta
        out_rows.append({"name": name, "delta": s(delta), "class": cls, "source_cause": r.get("source_cause"),
                         "engine_status": est, "held_line_ids": refs, "fix_row": r.get("fix_row"),
                         "source": r.get("source", ""), "note": r.get("note", "")})
    diff = ref_total - valued
    if acc != diff:
        raise StatementError(f"{sid}: table does not close: rows sum to {s(acc)}, reference - engine = {s(diff)}")
    return {
        "section_id": sid, "report": sec.get("report"), "trade": sec.get("trade"), "item_codes": sec.get("item_codes", []),
        "unit": unit, "reference_kind": ref["kind"], "reference_basis": ref["basis"],
        "freelancer_total": s(ref_total) if ref["kind"] == "FREELANCER" else None,
        "reference_total": s(ref_total), "engine_valued": s(valued),
        "engine_bounded": {"low_at_least": s(low), "high": None if open_hi else s(high),
                           "high_open": open_hi},
        "held_count": len(held), "excluded_count": len(eng.get("excluded_lines", [])),
        "valued_count": len(eng.get("valued_lines", [])),
        "difference": s(diff),
        "difference_pct_of_reference": s((diff / ref_total * 100).quantize(Decimal("0.01"))) if ref_total else None,
        "by_class": {c: s(v) for c, v in by_class.items()},
        "rows": out_rows,
    }


def build_statement(sections: list[dict]) -> dict:
    """Close every section, then total per (trade, unit, reference kind); never across units or kinds."""
    closed = [check_section(x) for x in sections]
    ids = [c["section_id"] for c in closed]
    if len(set(ids)) != len(ids):
        raise StatementError("a section appears twice")
    groups: dict[tuple, dict] = {}
    for c in closed:
        k = (c["trade"], c["unit"], c["reference_kind"])
        g = groups.setdefault(k, {"trade": c["trade"], "unit": c["unit"], "reference_kind": c["reference_kind"],
                                  "sections": [], "reference_total": Decimal(0), "engine_valued": Decimal(0),
                                  "low": Decimal(0), "high": Decimal(0), "high_open": False,
                                  "held_count": 0, "by_class": {x: Decimal(0) for x in CLASSES}})
        g["sections"].append(c["section_id"])
        g["reference_total"] += D(c["reference_total"])
        g["engine_valued"] += D(c["engine_valued"])
        g["low"] += D(c["engine_bounded"]["low_at_least"])
        if c["engine_bounded"]["high_open"]:
            g["high_open"] = True
        else:
            g["high"] += D(c["engine_bounded"]["high"])
        g["held_count"] += c["held_count"]
        for x in CLASSES:
            g["by_class"][x] += D(c["by_class"][x])
    totals = []
    for k in sorted(groups, key=lambda t: (str(t[0]), t[1], t[2])):
        g = groups[k]
        diff = g["reference_total"] - g["engine_valued"]
        if sum(g["by_class"].values(), Decimal(0)) != diff:
            raise StatementError(f"total {k} does not close")
        totals.append({
            "trade": g["trade"], "unit": g["unit"], "reference_kind": g["reference_kind"], "sections": g["sections"],
            "freelancer_total": s(g["reference_total"]) if g["reference_kind"] == "FREELANCER" else None,
            "reference_total": s(g["reference_total"]), "engine_valued": s(g["engine_valued"]),
            "engine_bounded": {"low_at_least": s(g["low"]), "high": None if g["high_open"] else s(g["high"]),
                               "high_open": g["high_open"]},
            "held_count": g["held_count"], "difference": s(diff),
            "by_class": {x: s(v) for x, v in g["by_class"].items()},
        })
    return {"schema": SCHEMA, "rule": "R-T548-1", "classes": list(CLASSES), "sections": closed, "totals": totals,
            "released_quantities_changed": 0}


def merge_totals(a: dict, b: dict) -> None:
    """Guard for callers that try to add two statement totals: refused unless unit and reference kind agree."""
    if a["unit"] != b["unit"]:
        raise StatementError(f"{a['unit']} and {b['unit']} never in one total")
    if a["reference_kind"] != b["reference_kind"]:
        raise StatementError("a freelancer total and an owner-question figure never in one total")


def to_markdown(st: dict) -> str:
    L = ["| Trade | Unit | Reference | Reference total | Engine valued | Engine bounded | HELD lines | Difference "
         "(ref - engine) | ENGINE_RIGHT | ENGINE_WRONG | RULE_DIFFERENCE | HELD | TOLERANCE | UNRESOLVED |",
         "|" + "---|" * 14]
    for t in st["totals"]:
        b = t["engine_bounded"]
        rng = f"AT_LEAST {b['low_at_least']} .. {'OPEN' if b['high_open'] else b['high']}"
        ref = "freelancer row" if t["reference_kind"] == "FREELANCER" else "owner-question figure (freelancer: no row)"
        c = t["by_class"]
        L.append(f"| {t['trade']} | {t['unit']} | {ref} | {t['reference_total']} | {t['engine_valued']} | {rng} | "
                 f"{t['held_count']} | {t['difference']} | {c['ENGINE_RIGHT']} | {c['ENGINE_WRONG']} | "
                 f"{c['RULE_DIFFERENCE']} | {c['HELD']} | {c['TOLERANCE']} | {c['UNRESOLVED']} |")
    return "\n".join(L) + "\n"
