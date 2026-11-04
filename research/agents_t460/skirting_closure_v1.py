"""SKIRTING LINE CLOSURE V1 (T-460 item 2, research, unwired): every FIN.SKIRTING line of a candidate BOQ is reconciled
line by line: gross - listed deductions + listed additions = net. A difference means a deduction (or an addition) that
is in the net but not on the line, so a reviewer cannot add it back or check it: it is named, never absorbed.

PHYSICAL ELEMENT: the strip at the foot of a finished dry wall / column face (UP-SKIRT-001, UP-CER-003). The line's
gross is the room boundary walk; each listed deduction is a piece of that walk with no skirting (a door / passage
opening, floor-level glazing, a boundary that is not a wall); a listed addition is a piece skirted beyond the walk
(e.g. a sill-window threshold restored, R-T422 / R-T481). Net = gross - deductions + additions, to 0.0005 lm.

    close(line) -> {"line_id", "state", "gross", "net", "listed_ded", "listed_add", "residual_lm", ...}
    ledger(lines) -> {"rows", "summary"}
States (R-T460-2):
    CLOSES                 |residual| <= TOL_LM
    UNLISTED_DEDUCTION     residual > TOL_LM: the net is shorter than the listed walk; the missing piece is named by
                           its residual and the line's range partner (if any) - never closed by a plug
    UNLISTED_ADDITION      residual < -TOL_LM: the net is longer than the listed walk
    NO_GROSS               a quantity without a gross walk (the walk cannot be re-added)
    NO_QUANTITY            a line with no measured net (HELD / BOUNDED / NOT_APPLICABLE / EXCLUDED): reported once,
                           not reconciled, never 0
"""

from __future__ import annotations

POLICY = "SKIRTING_LINE_CLOSURE_V1"
RULES = ("UP-SKIRT-001", "UP-CER-003", "UP-QTY-STATUS-001", "R-T460-2")
TOL_LM = 0.0005


def _lm(items):
    tot = 0.0
    for d in items or ():
        v = d.get("lm", d.get("length_m"))
        if v is None:
            return None
        tot += float(v)
    return tot


def close(line):
    g, n = line.get("gross"), line.get("net", line.get("measured_net"))
    ded, add = _lm(line.get("deductions")), _lm(line.get("additions"))
    base = {"line_id": line.get("line_id"), "evidence_state": line.get("evidence_state"), "gross": g, "net": n,
            "listed_ded": None if ded is None else round(ded, 6), "listed_add": None if add is None else round(add, 6),
            "residual_lm": None}
    if n is None:
        return dict(base, state="NO_QUANTITY")
    if g is None:
        return dict(base, state="NO_GROSS")
    if ded is None or add is None:
        return dict(base, state="NO_GROSS", note="a listed piece carries no length")
    r = g - ded + add - n
    st = "CLOSES" if abs(r) <= TOL_LM else ("UNLISTED_DEDUCTION" if r > 0 else "UNLISTED_ADDITION")
    return dict(base, residual_lm=round(r, 6), state=st)


def ledger(lines):
    rows = [close(ln) for ln in lines if ln.get("item_code", "FIN.SKIRTING") == "FIN.SKIRTING"]
    states = sorted({r["state"] for r in rows})
    summ = {"policy": POLICY, "lines": len(rows), "by_state": {s: sum(r["state"] == s for r in rows) for s in states},
            "net_sum_lm": round(sum(r["net"] for r in rows if r["net"] is not None), 6),
            "unlisted_ded_lm": round(sum(r["residual_lm"] for r in rows if r["state"] == "UNLISTED_DEDUCTION"), 6),
            "unlisted_add_lm": round(-sum(r["residual_lm"] for r in rows if r["state"] == "UNLISTED_ADDITION"), 6)}
    return {"rows": rows, "summary": summ}
