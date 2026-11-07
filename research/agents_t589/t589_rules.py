"""T-589 R-T589-1: structural closable-component classification (proposed, every villa).

A reconciliation component (a member by mark, a bar group by face, an earthworks zone) that is not VERIFIED is put in
exactly one closure class, by what is missing for VERIFIED:

  VERIFIED_ON_RECORD      the Checker re-measured THIS component's quantity himself (verdict reference required);
                          a confirmed class or a confirmed total of a larger group is not enough.
  CLOSABLE_FROM_DRAWINGS  every value the component needs is printed or drawn on the governing set; it needs a
                          sheet reference (sheet + page / detail / handle) and a re-measure pack id.
  DESIGNER_ITEM           a value the component needs is not printed (or two sheets conflict): it needs a designer
                          item id (D-nn) or an RFI id (RFI-..., S-nn label of the RFI re-review); never an owner question.
  OWNER_RULE_GAP          the drawings are complete but no Urban rule governs the measurement: it needs the rule
                          reference of the gap; an owner question only when ERS s.2.7 is met (then in s.6 format).

(a) one class per component; an unknown class is refused. (b) CLOSABLE without a sheet reference or a pack is refused.
(c) DESIGNER without a D-nn / RFI id is refused. (d) VERIFIED without the Checker verdict reference is refused.
(e) quantities stay in their unit (m3 / t / nr / lm), kg is refused inside a t table, mm refused; a held quantity is a
range or HELD with its item, never 0, never summed into a point; no percentage of a held or rule-difference figure.
(f) class sums are per unit and per basis (difference reference - engine / engine valued / engine held bound) only.
(g) a component may be split (part VERIFIED, part CLOSABLE ...) only into named parts that re-add to the component.
"""
from __future__ import annotations

import re
from decimal import Decimal

D = Decimal
CLASSES = ("VERIFIED_ON_RECORD", "CLOSABLE_FROM_DRAWINGS", "DESIGNER_ITEM", "OWNER_RULE_GAP")
UNITS = ("m3", "t", "nr", "lm", "m2")
BASES = ("DIFFERENCE", "ENGINE_VALUED", "ENGINE_HELD")
SHEET_RE = re.compile(r"\b(p\.\s?\d+|[A-Z]{1,4}-\d{2,3}|handle [0-9A-F]{2,5})\b")
DESIGNER_RE = re.compile(r"^(D-\d{2}|RFI-[A-Z]+(-[A-Z]+)?-?\d{2}|S\d{2})$")
CHECKER_RE = re.compile(r"Checker|Verifier")


class ClassError(ValueError):
    pass


def q(x) -> Decimal:
    if isinstance(x, float):
        raise ClassError("float quantity refused: give a decimal string")
    return D(str(x))


def check_quantity(qt: dict, unit_table: str | None = None) -> None:
    """(e): one quantity record {unit, basis, value | low/high | held}."""
    u = qt.get("unit")
    if u not in UNITS:
        raise ClassError(f"unit {u!r} refused (kg, mm, % are not table units)")
    if unit_table and u != unit_table:
        raise ClassError(f"unit {u} inside a {unit_table} table refused")
    if qt.get("basis") not in BASES:
        raise ClassError(f"basis {qt.get('basis')!r} refused")
    if "pct" in qt:
        raise ClassError("percentage refused on a component")
    if qt["basis"] == "ENGINE_HELD":
        if "value" in qt:
            raise ClassError("a held quantity is never a point value")
        if qt.get("low") is None and not qt.get("held_item"):
            raise ClassError("a held quantity needs a low end or its held item")
        if qt.get("low") is not None and qt.get("high") is not None and q(qt["low"]) > q(qt["high"]):
            raise ClassError("low > high refused")
    else:
        if "value" not in qt:
            raise ClassError("a valued / difference quantity needs its value")
        q(qt["value"])


def check_component(c: dict, unit_table: str | None = None) -> None:
    for k in ("id", "section", "closure_class", "evidence", "missing", "quantity"):
        if not c.get(k) and c.get(k) != []:
            raise ClassError(f"{c.get('id')}: field {k} missing")
    cl = c["closure_class"]
    if cl not in CLASSES:
        raise ClassError(f"{c['id']}: class {cl!r} refused")
    check_quantity(c["quantity"], unit_table)
    if cl == "CLOSABLE_FROM_DRAWINGS":
        refs = c.get("sheet_refs") or []
        if not refs or not all(isinstance(r, str) and SHEET_RE.search(r) for r in refs):
            raise ClassError(f"{c['id']}: CLOSABLE without a sheet reference refused")
        if not c.get("pack"):
            raise ClassError(f"{c['id']}: CLOSABLE without a re-measure pack refused")
    if cl == "DESIGNER_ITEM":
        refs = c.get("designer_refs") or []
        if not refs or not all(DESIGNER_RE.match(r) for r in refs):
            raise ClassError(f"{c['id']}: DESIGNER without a D-nn / RFI id refused")
    if cl == "VERIFIED_ON_RECORD":
        if not CHECKER_RE.search(c.get("verified_by") or ""):
            raise ClassError(f"{c['id']}: VERIFIED without the Checker verdict reference refused")
    if cl == "OWNER_RULE_GAP":
        if not c.get("rule_gap"):
            raise ClassError(f"{c['id']}: OWNER_RULE_GAP without the rule reference refused")
        if c.get("owner_question") and not c.get("ers_2_7_met"):
            raise ClassError(f"{c['id']}: owner question without ERS s.2.7 refused")


def check_split(whole: str, parts: list[str]) -> None:
    """(g) named parts re-add exactly to the component."""
    if sum(q(p) for p in parts) != q(whole):
        raise ClassError(f"split parts {parts} do not re-add to {whole}")


def section_table(section: str, unit: str, comps: list[dict]) -> dict:
    """One table per section: n per class and quantity per class, per unit and basis (f). Held stays a range."""
    for c in comps:
        check_component(c)
    out = {"section": section, "n": len(comps), "by_class": {}}
    for cl in CLASSES:
        cs = [c for c in comps if c["closure_class"] == cl]
        row = {"n": len(cs), "quantity": {}}
        for c in cs:
            qt = c["quantity"]
            key = f"{qt['unit']}|{qt['basis']}"
            acc = row["quantity"].setdefault(key, {"n": 0})
            acc["n"] += 1
            if qt["basis"] == "ENGINE_HELD":
                lo = acc.get("low_known", D(0)) + (q(qt["low"]) if qt.get("low") is not None else D(0))
                acc["low_known"] = lo
                if qt.get("high") is None:
                    acc["high"] = "HELD"
                elif acc.get("high") != "HELD":
                    acc["high"] = acc.get("high", D(0)) + q(qt["high"])
                if qt.get("low") is None:
                    acc["low_held_items"] = acc.get("low_held_items", 0) + 1
            else:
                acc["sum"] = acc.get("sum", D(0)) + q(qt["value"])
                acc["gross_abs"] = acc.get("gross_abs", D(0)) + abs(q(qt["value"]))
        row["quantity"] = {k: {kk: (str(vv) if isinstance(vv, Decimal) else vv) for kk, vv in v.items()}
                           for k, v in sorted(row["quantity"].items())}
        out["by_class"][cl] = row
    if sum(r["n"] for r in out["by_class"].values()) != len(comps):
        raise ClassError("class counts do not add to n")
    return out
