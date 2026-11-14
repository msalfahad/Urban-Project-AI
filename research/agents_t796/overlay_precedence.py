"""MAIN FILL overlay precedence for the board workbook tools (T-796, rule R-T796-1; every villa).

A main-chat fix row (MAIN_CHAT_FIX_ROWS_V1: line_id, before, after, label, basis) was written against one index. The
workbook tools used to apply every row over every newer index, so a stale row overrode a value wired later (V3.0.86:
STR.EARTH.DISPOSAL 10.476796 RELEASED shown as HELD 105.632 .. 115.546). Precedence:

  APPLY    the index line still carries the row's `before` state and no `fill_basis` (nothing newer touched it)
  ALREADY  the index line already carries the row's `after` state (wired; no-op)
  SKIP     anything else: the line is absent, carries a later fix row's `fill_basis`, or moved since the row was written;
           the index value stands and the skip is logged with the reason and the two values.

Byte-identical copy on agents/control: docs/agents/boq/overlay.py (the board tools import it).
"""
from __future__ import annotations

TOL = 1e-6
APPLY, ALREADY, SKIP_ABSENT, SKIP_NEWER, SKIP_CHANGED = "APPLY", "ALREADY", "SKIP_ABSENT", "SKIP_NEWER", "SKIP_CHANGED"


def _num(x):
    return None if x is None else float(x)


def line_state(line):
    return (line["class"], _num(line.get("measured_net")), _num(line.get("held_low")), _num(line.get("held_high")))


def row_state(s):
    return (s["class"], _num(s.get("net")), _num(s.get("low")), _num(s.get("high")))


def same(a, b):
    if a[0] != b[0]:
        return False
    for x, y in zip(a[1:], b[1:]):
        if (x is None) != (y is None):
            return False
        if x is not None and abs(x - y) > TOL:
            return False
    return True


def decide(line, row):
    """Return (action, reason) for one fix row over one index line (None = line absent)."""
    if line is None:
        return SKIP_ABSENT, "line id not in this index"
    cur, aft = line_state(line), row_state(row["after"])
    if same(cur, aft):
        return ALREADY, "index already carries the row's after state"
    if line.get("fill_basis"):
        return SKIP_NEWER, "index line carries a later fix row's fill_basis: " + str(line["fill_basis"])[:160]
    if "before" not in row or not same(cur, row_state(row["before"])):
        return SKIP_CHANGED, "index line moved since the row was written (its state is not the row's before state)"
    return APPLY, "index line still at the row's before state"


def apply_overlay(lines, fill):
    """Apply a MAIN FILL set to `lines` (list of index line dicts, mutated in place). Returns the decision log."""
    by_id = {l["line_id"]: l for l in lines}
    log = []
    for r in fill["rows"]:
        l = by_id.get(r["line_id"])
        act, why = decide(l, r)
        ent = dict(line_id=r["line_id"], item_code=r.get("item_code"), unit=r.get("unit"), set=r.get("set"), action=act,
                   reason=why, index=None if l is None else list(line_state(l)), row_after=list(row_state(r["after"])))
        if act == APPLY:
            a = r["after"]
            if a["class"] == "RELEASED":
                l["class"] = "RELEASED"; l["measured_net"] = a["net"]; l["held_low"] = l["held_high"] = None
            else:
                l["class"] = a["class"]; l["measured_net"] = a.get("net"); l["held_low"] = a.get("low"); l["held_high"] = a.get("high")
            l["fill_label"] = r.get("label")
        log.append(ent)
    return log


def summary(log):
    out = {}
    for e in log:
        out[e["action"]] = out.get(e["action"], 0) + 1
    return out
