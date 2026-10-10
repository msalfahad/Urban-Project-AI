"""BOQ REPORT LAYER (R8.19) - a PRESENTATION layer over evidence rows. It calculates NOTHING.

Every report quantity is COPIED from one named field of its evidence row (or is null); every row keeps its trace
(run id, source revision, trade row, sites, surface ids, authority digest, rule ids, owner facts, release state).
Status (one of STATUSES, derived from the evidence row - never typed):
  RELEASED                  only with a release record on the evidence row (release_state == RELEASED)
  COMPUTED_SHADOW_COMPLETE  the evidence row has a COMPLETE value and no unresolved contributor
  AUTHORISED_SUBTOTAL       no complete value, an authorised subtotal exists (shown as such, never as approved)
  BLOCKED                   neither: quantity null
approved_for_boq is True only for RELEASED. No pricing, no sums, no manual edits: validate() re-derives every row
from its evidence row and refuses any difference.

Project-agnostic; stdlib only.
"""

from __future__ import annotations

import hashlib
import json

POLICY_ID = "BOQ_REPORT_LAYER_V1"
RELEASED, COMPLETE, SUBTOTAL, BLOCKED = "RELEASED", "COMPUTED_SHADOW_COMPLETE", "AUTHORISED_SUBTOTAL", "BLOCKED"
STATUSES = (COMPLETE, SUBTOTAL, BLOCKED, RELEASED)
COLUMNS = ("ITEM_CODE", "TRADE", "DESCRIPTION_AR", "DESCRIPTION_EN", "LOCATION_FLOOR", "ROOM_ZONE", "QTY", "UNIT",
           "STATUS", "SOURCE", "RULE_AUTHORITY", "NOTES_BLOCKERS")
TRACE = ("run_id", "source_revision", "trade_row", "sites", "surface_ids", "authority_digest", "rule_ids",
         "owner_facts", "release_state")


def _digest(o):
    return hashlib.sha256(json.dumps(o, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()


def status(ev: dict) -> tuple:
    """(status, qty source field) from an evidence row: {"complete", "authorised_subtotal", "unresolved",
    "release_state"}."""
    if ev.get("release_state") == RELEASED and ev.get("complete") is not None:
        return RELEASED, "complete"
    if ev.get("complete") is not None and not ev.get("unresolved"):
        return COMPLETE, "complete"
    if ev.get("authorised_subtotal") is not None:
        return SUBTOTAL, "authorised_subtotal"
    return BLOCKED, None


def report_rows(ev: dict, item: dict) -> list:
    """The report rows of one evidence row: one TOTAL row + one row per room (each room quantity copied from
    ev["per_room"][site]["qty"])."""
    st, field = status(ev)
    trace = {k: ev.get(k) for k in TRACE}
    notes = list(ev.get("blockers") or [])
    base = {"ITEM_CODE": item["item_code"], "TRADE": item["trade"], "DESCRIPTION_AR": item["description_ar"],
            "DESCRIPTION_EN": item["description_en"], "LOCATION_FLOOR": ev.get("floor"), "UNIT": ev["unit"],
            "STATUS": st, "SOURCE": ev.get("source"), "RULE_AUTHORITY": ev.get("rule_ids"),
            "NOTES_BLOCKERS": notes, "approved_for_boq": st == RELEASED, "qty_field": field, "trace": trace}
    rows = [dict(base, ROW_KIND="TOTAL", ROOM_ZONE="ALL", QTY=ev.get(field) if field else None,
                 evidence_row=ev["row_id"])]
    for sid, r in sorted((ev.get("per_room") or {}).items()):
        rows.append(dict(base, ROW_KIND="ROOM", ROOM_ZONE=r["zones"], QTY=r["qty"] if field else None,
                         evidence_row=ev["row_id"], trace=dict(trace, sites=[sid])))
    return rows


def build(evidence_rows: list, items: dict, *, run: dict) -> dict:
    rows = [r for ev in evidence_rows for r in report_rows(ev, items[ev["row_id"]])]
    rep = {"policy": POLICY_ID, "columns": list(COLUMNS), "statuses": list(STATUSES), "run": run, "rows": rows,
           "pricing": None, "calculates": False}
    rep["digest"] = _digest({k: v for k, v in rep.items() if k != "digest"})
    return rep


def validate(rep: dict, evidence_rows: list, items: dict) -> dict:
    """Re-derive every row from its evidence row; any difference (number, status, trace) fails."""
    expect = build(evidence_rows, items, run=rep["run"])
    diffs = [{"i": i, "report": a, "expected": b} for i, (a, b) in enumerate(zip(rep["rows"], expect["rows"]))
             if a != b]
    if len(rep["rows"]) != len(expect["rows"]):
        diffs.append({"error": "row count", "report": len(rep["rows"]), "expected": len(expect["rows"])})
    bad = [r["ITEM_CODE"] for r in rep["rows"] if r["STATUS"] not in STATUSES or
           (r["approved_for_boq"] and r["STATUS"] != RELEASED) or (r["STATUS"] == BLOCKED and r["QTY"] is not None)]
    untraced = [r["ITEM_CODE"] for r in rep["rows"] if any(k not in r["trace"] for k in TRACE)]
    ok = not diffs and not bad and not untraced and rep["digest"] == expect["digest"]
    return {"state": "PASS" if ok else "FAIL", "differences": diffs, "status_violations": bad,
            "untraced": untraced, "rows": len(rep["rows"])}


def policy_record() -> dict:
    rec = {"policy_id": POLICY_ID, "columns": list(COLUMNS), "statuses": list(STATUSES), "trace": list(TRACE),
           "quantity": "copied verbatim from one evidence field (complete / authorised_subtotal) or null",
           "never": ["a calculation, sum or rounding in the report", "a price", "a subtotal or blocked value shown as "
                     "approved", "RELEASED without a release record", "a row without its trace", "a manual edit"]}
    rec["digest"] = _digest(rec)
    return rec
