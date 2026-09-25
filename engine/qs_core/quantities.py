"""The publication contract: what may be presented as a quantity, and what may only be presented as a question.

A number beside a frozen figure is read as an answer, whatever the status column next to it says.  If every row
behind it was blocked, the reader has been handed a comparison that means nothing and looks like a correction.

So blocked and final are separated at the point of arithmetic rather than at the point of presentation.  A
blocked row does not carry a quantity at all: it carries a DIAGNOSTIC_ONLY value, under a name that cannot be
summed by accident.  A subtotal with one blocked contributor is null - not provisional, not indicative, null -
and the bill line says what has to be answered before it becomes a number.
"""

from __future__ import annotations

FINAL = "FINAL_QUANTITY_AVAILABLE"
DIAGNOSTIC_PREFIX = "DIAGNOSTIC_ONLY_"

STATUS_FINAL = "FINAL"
STATUS_BLOCKED = "BLOCKED_PENDING_ANSWERS"
STATUS_EMPTY = "NO_CONTRIBUTING_ROWS"


def diagnostic_name(field):
    return f"{DIAGNOSTIC_PREFIX}{field}"


def row_quantity(row, field):
    """The publishable quantity of a row: a number when the row is final, and nothing at all when it is not."""
    return row.get(field) if row.get("STATUS") == FINAL else None


def publish(rows, group_of, field, unit, what, blocked_groups=None, reasons_of=None):
    """Group rows into subtotals that obey the contract, and say what each blocked one is waiting for.

    `blocked_groups` lets a caller block a subtotal for a reason that is not visible in its rows - a band whose
    identity is unresolved might belong to this thickness and is not in these rows at all.
    """
    blocked_groups = dict(blocked_groups or {})
    groups = {}
    for r in rows:
        g = group_of(r)
        s = groups.setdefault(g, {"GROUP": g, "UNIT": unit, "WHAT": what, "ROWS_FINAL": 0, "ROWS_BLOCKED": 0,
                                  "FINAL_ROW_REFS": [], "BLOCKED_ROW_REFS": [], "_final": 0.0, "_all": 0.0,
                                  "REASONS": []})
        ref = r.get("COMPONENT_REF") or r.get("MEASUREMENT_OBJECT_ID") or r.get("REF")
        value = r.get(field)
        if value is None:
            value = r.get(diagnostic_name(field))
        value = 0.0 if value is None else value
        s["_all"] += value
        if r.get("STATUS") == FINAL:
            s["ROWS_FINAL"] += 1
            s["FINAL_ROW_REFS"].append(ref)
            s["_final"] += value
        else:
            s["ROWS_BLOCKED"] += 1
            s["BLOCKED_ROW_REFS"].append(ref)
            reason = {"REF": ref, "STATUS": r.get("STATUS"), "WHY": r.get("BLOCKED_NOTE")}
            if reasons_of:
                reason["DETAIL"] = reasons_of(r)
            s["REASONS"].append(reason)

    for g, extra in blocked_groups.items():
        s = groups.setdefault(g, {"GROUP": g, "UNIT": unit, "WHAT": what, "ROWS_FINAL": 0, "ROWS_BLOCKED": 0,
                                  "FINAL_ROW_REFS": [], "BLOCKED_ROW_REFS": [], "_final": 0.0, "_all": 0.0,
                                  "REASONS": []})
        s["REASONS"].append(extra)

    out = {}
    for g, s in sorted(groups.items(), key=lambda kv: (kv[0] is None, kv[0])):
        blocked = bool(s["ROWS_BLOCKED"]) or g in blocked_groups
        empty = not s["ROWS_FINAL"] and not s["ROWS_BLOCKED"]
        rec = {
            "GROUP": g, "WHAT": what, "UNIT": unit,
            "STATUS": STATUS_EMPTY if empty else (STATUS_BLOCKED if blocked else STATUS_FINAL),
            "FINAL_QUANTITY": None if blocked or empty else round(s["_final"], 6),
            diagnostic_name("SUM_OF_EVERY_ROW"): round(s["_all"], 6),
            diagnostic_name("SUM_OF_FINAL_ROWS"): round(s["_final"], 6),
            "ROWS_FINAL": s["ROWS_FINAL"], "ROWS_BLOCKED": s["ROWS_BLOCKED"],
            "FINAL_ROW_REFS": sorted(x for x in s["FINAL_ROW_REFS"] if x),
            "BLOCKED_ROW_REFS": sorted(x for x in s["BLOCKED_ROW_REFS"] if x),
            "WAITING_ON": s["REASONS"],
            "WHY_NULL": (None if not blocked and not empty else
                         "no row contributes to this group" if empty else
                         "at least one contributor is not final, so this subtotal is not a quantity; the "
                         "diagnostic sums beside it are arithmetic on unfinished rows and are not a result"),
        }
        out[str(g)] = rec

    any_blocked = any(r["STATUS"] != STATUS_FINAL for r in out.values())
    # No rows at all is not evidence that there is nothing to measure.  Publishing 0.0 for a trade the
    # extraction simply did not produce is the same error as publishing a subtotal over blocked rows.
    return {
        "WHAT": what, "UNIT": unit,
        "SUBTOTALS": out,
        "PUBLISHED_TOTAL": (None if any_blocked or not out
                            else round(sum(r["FINAL_QUANTITY"] for r in out.values()), 6)),
        "NOTHING_TO_PUBLISH": not out,
        "PUBLISHED_SUBTOTAL_COUNT": sum(1 for r in out.values() if r["STATUS"] == STATUS_FINAL),
        "BLOCKED_SUBTOTAL_COUNT": sum(1 for r in out.values() if r["STATUS"] == STATUS_BLOCKED),
        diagnostic_name("TOTAL_OF_EVERY_ROW"): round(sum(r[diagnostic_name("SUM_OF_EVERY_ROW")]
                                                         for r in out.values()), 6),
        "CONTRACT": "a subtotal is a number only when every row behind it is final; otherwise it is null and "
                    "the diagnostic sums beside it are named so that they cannot be mistaken for, or added "
                    "to, a quantity",
    }
