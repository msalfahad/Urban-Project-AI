"""T-580 MANIFEST OVERLAY (R-T580-1, every villa on the engine's line-index scheme). Research / integration preparation
only (lane I, non-candidate): it applies normalised wiring operations to a COPY of a pinned line index in memory and
reports; it never writes a candidate, released, rule, knowledge or registry file.

A line index is {line_id: {item_code, unit, element_id, class, measured_net, held_low, held_high}} (the census schema
of LINE_INDEX_V3_0_57). An operation (op) is one manifest row on one line:

  ADD        a new line (line_id 'NEW:...'); refused when the id exists or the same (item_code, element_id) is live
  SET        quantity state of an existing line moves (before must equal the index, else STALE with both states)
  RECODE     item_code changes, quantity identical (before checked)
  RETIRE     the line leaves the index (before checked)
  TEXT_ONLY  text / fields only: the quantity state must not move (before checked, after = before)
  LEDGER     a ledger entry on a line whose own state stays (before checked, no figure)
  BESIDE     a figure printed beside a line whose own state stays (before checked)

Refusals (OverlayError, the package is not applied):
  R1 two packages writing one line id, or one op id twice (steps of ONE package may chain on a line it adds or
     moves: the package is one Gate B unit; across packages the second must supersede the first by name)
  R2 an after state that prints HELD / missing as 0 (HELD with value 0, a HELD line whose bound collapses to 0 .. 0,
     or a line that was HELD / blank becoming RELEASED 0)
  R3 an ADD on an existing id, or an ADD duplicating a live (item_code, element_id)
Flags (the overlay continues, the row is NOT applied):
  STALE   the op's stated before differs from the index (both values printed)
  NO_BEFORE   an op on an existing line with no stated before (the package must state it)
Cross-trade conflicts: two live lines of one LAYER (item family; FIN.FLOOR split into finish and bed) on one HOST
(element id without the 'MATERIAL:' prefix, cut at '#') in one unit, written by different sources (the candidate
counts as one source); a conflict is EXPLAINED only by a declared ruling naming its source and fix row.
Totals: per (item code, unit): released count and sum, HELD count, HELD bound sums (low, high; an open high is
counted as OPEN, never as 0), blank HELD count; EXCLUDED apart.
"""

from __future__ import annotations

import copy
import re
from decimal import Decimal

KINDS = ("ADD", "SET", "RECODE", "RETIRE", "TEXT_ONLY", "LEDGER", "BESIDE")
QFIELDS = ("class", "measured_net", "held_low", "held_high")
TOL = Decimal("0.0000005")          # half a unit of the 6th decimal: the index prints 6 dp


class OverlayError(Exception):
    pass


def _d(x):
    return None if x is None else Decimal(str(x))


def state(line):
    return {k: line.get(k) for k in QFIELDS}


def same_state(a, b):
    if a.get("class") != b.get("class"):
        return False
    for k in QFIELDS[1:]:
        x, y = _d(a.get(k)), _d(b.get(k))
        if (x is None) != (y is None):
            return False
        if x is not None and abs(x - y) > TOL:
            return False
    return True


def family(code):
    """item family = the first two dot segments (FIN.PAINT, STR.CONC, MAS.GLUE ...)."""
    return ".".join(code.split(".")[:2])


def layer(code):
    f = family(code)
    if f == "FIN.FLOOR":
        return "FIN.FLOOR.BED" if ".BED" in code else "FIN.FLOOR"
    return f


def host(element_id):
    e = element_id[len("MATERIAL:"):] if element_id.startswith("MATERIAL:") else element_id
    return e.split("#")[0]


def check_after(op):
    """R2: HELD / missing is never printed as 0."""
    a, b = op.get("after") or {}, op.get("before") or {}
    cls = a.get("class")
    if cls == "HELD":
        if _d(a.get("measured_net")) is not None:
            raise OverlayError(f"R2 HELD_AS_VALUE: {op['op_id']} HELD with a value {a.get('measured_net')}")
        lo, hi = _d(a.get("held_low")), _d(a.get("held_high"))
        if hi is not None and hi == 0 and (lo is None or lo == 0):
            raise OverlayError(f"R2 HELD_AS_0: {op['op_id']} HELD bound collapses to 0 .. 0")
    if cls == "RELEASED":
        v = _d(a.get("measured_net"))
        if v is None:
            raise OverlayError(f"R2 RELEASED_BLANK: {op['op_id']} RELEASED with no value")
        if v == 0 and (op["kind"] == "ADD" or b.get("class") in ("HELD", None) or b.get("measured_net") is None):
            raise OverlayError(f"R2 HELD_AS_0: {op['op_id']} a HELD / missing quantity printed RELEASED 0")


def validate(ops):
    seen, ids = {}, set()
    for op in ops:
        if op["kind"] not in KINDS:
            raise OverlayError(f"unknown op kind {op['kind']} ({op['op_id']})")
        if op["op_id"] in ids:
            raise OverlayError(f"R1 TWO_ROWS_ONE_LINE: op {op['op_id']} given twice")
        ids.add(op["op_id"])
        lid = op["line_id"]
        if lid in seen and seen[lid]["package"] != op["package"]:
            raise OverlayError(f"R1 TWO_ROWS_ONE_LINE: {lid} written by {seen[lid]['op_id']} ({seen[lid]['package']}) "
                               f"and {op['op_id']} ({op['package']})")
        seen.setdefault(lid, op)
        if op["kind"] in ("ADD", "SET", "RECODE"):
            check_after(op)


def apply(index, packages, rulings=()):
    """apply ordered packages [(name, [ops])] to a COPY of index; returns (index_after, report)."""
    idx = copy.deepcopy(index)
    allops = [op for _, ops in packages for op in ops]
    if any(op["package"] != name for name, ops in packages for op in ops):
        raise OverlayError("an op sits in a package other than its own")
    validate(allops)
    prev = totals(idx)
    origin = {}                    # line_id -> package that wrote it
    rows, steps = [], []
    for name, ops in packages:
        applied = stale = 0
        for op in ops:
            r = {"op_id": op["op_id"], "package": name, "row": op["row"], "kind": op["kind"], "line_id": op["line_id"]}
            if op.get("beside") is not None:
                r["beside"] = op["beside"]
            lid = op["line_id"]
            if op["kind"] == "ADD":
                if lid in idx:
                    raise OverlayError(f"R3 ADD_EXISTS: {lid} ({op['op_id']})")
                dup = [k for k, l in idx.items() if l["class"] != "EXCLUDED" and l["item_code"] == op["item_code"]
                       and l["element_id"] == op["element_id"] and l.get("unit") == op["unit"]]
                if dup:
                    raise OverlayError(f"R3 DOUBLE_COUNT: {op['op_id']} adds {op['item_code']} on {op['element_id']} "
                                       f"already live as {dup[0]}")
                idx[lid] = {"line_id": lid, "item_code": op["item_code"], "unit": op["unit"],
                            "element_id": op["element_id"], **{k: op["after"].get(k) for k in QFIELDS}}
                r["status"] = "APPLIED"
            else:
                if lid not in idx:
                    r["status"] = "MISSING_LINE"
                    rows.append(r)
                    continue
                cur = idx[lid]
                b = op.get("before")
                if b is None:
                    r["status"] = "NO_BEFORE"
                    r["index"] = state(cur)
                    rows.append(r)
                    continue
                if not same_state(b, cur) or ("item_code" in b and b["item_code"] != cur["item_code"]):
                    r["status"] = "STALE"
                    r["stated_before"], r["index"] = {k: b.get(k) for k in QFIELDS}, state(cur)
                    stale += 1
                    rows.append(r)
                    continue
                if op["kind"] == "SET":
                    cur.update({k: op["after"].get(k) for k in QFIELDS})
                elif op["kind"] == "RECODE":
                    if not same_state(op["after"], cur):
                        raise OverlayError(f"RECODE_MOVES_QUANTITY: {op['op_id']}")
                    cur["item_code"] = op["after"]["item_code"]
                elif op["kind"] == "RETIRE":
                    del idx[lid]
                r["status"] = "APPLIED"
            if op["kind"] in ("ADD", "SET", "RECODE"):            # text / ledger / beside write no quantity
                origin[lid] = op.get("source", name)
            applied += 1
            rows.append(r)
        cur_t = totals(idx)
        steps.append({"package": name, "ops": len(ops), "applied": applied, "stale": stale,
                      "totals_changed": diff_totals(prev, cur_t)})
        prev = cur_t
    return idx, {"rows": rows, "steps": steps, "conflicts": conflicts(idx, origin, rulings)}


def conflicts(idx, origin, rulings=()):
    """two live lines of one family on one host, at least one written by the overlay, from different sources."""
    groups = {}
    for lid, l in idx.items():
        if l["class"] == "EXCLUDED":
            continue
        groups.setdefault((layer(l["item_code"]), host(l["element_id"]), l.get("unit")), []).append(lid)
    out = []
    for key, lids in sorted(groups.items()):
        touched = [x for x in lids if x in origin]
        if not touched or len(lids) < 2:
            continue
        srcs = sorted({origin.get(x, "CANDIDATE") for x in lids})
        if len(srcs) < 2:
            continue
        rule = next((r for r in rulings if r["layer"] == key[0] and re.search(r["host_re"], key[1])
                     and set(r["sources"]) == set(srcs)), None)
        out.append({"family": key[0], "host": key[1], "unit": key[2], "lines": sorted(lids), "sources": srcs,
                    "status": "EXPLAINED" if rule else "UNEXPLAINED",
                    "ruling": rule["ruling"] if rule else None, "fix_row": rule["fix_row"] if rule else None})
    return out


def totals(idx):
    t = {}
    for l in idx.values():
        k = f"{l['item_code']}|{l.get('unit')}"
        s = t.setdefault(k, {"released_n": 0, "released": Decimal(0), "held_n": 0, "held_blank_n": 0,
                             "held_low": Decimal(0), "held_high": Decimal(0), "held_high_open_n": 0, "excluded_n": 0})
        if l["class"] == "RELEASED":
            s["released_n"] += 1
            s["released"] += _d(l["measured_net"])
        elif l["class"] == "HELD":
            s["held_n"] += 1
            lo, hi = _d(l.get("held_low")), _d(l.get("held_high"))
            if lo is None and hi is None:
                s["held_blank_n"] += 1
            else:
                s["held_low"] += lo or Decimal(0)
                if hi is None:
                    s["held_high_open_n"] += 1
                else:
                    s["held_high"] += hi
        else:
            s["excluded_n"] += 1
    return {k: {kk: (format(v.normalize(), "f") if isinstance(v, Decimal) else v) for kk, v in s.items()}
            for k, s in sorted(t.items())}


def diff_totals(before, after):
    out = {}
    for k in sorted(set(before) | set(after)):
        if before.get(k) != after.get(k):
            out[k] = {"before": before.get(k), "after": after.get(k)}
    return out
