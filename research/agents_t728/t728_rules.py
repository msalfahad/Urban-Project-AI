"""R-T728-1 CORNER BEAD STATE FROM ITS HOST (T-728, research; every villa). Applies the Lead ruling of 2026-11-11 16:25
(F-T705-1, ELEMENT_REGISTER 'CORNER BEAD HEIGHT STATE'): a corner bead exists where the drawn arris of a plastered face
exists; its length takes its host face's height state: on a HELD host the bead is HELD with the host's bound, never
released at a chosen height, never 0; it is released together with its host. Owner trade unchanged: plaster, B4-09.

A bead ledger row already carries its own measured length (owner method, e.g. G1 under OD-V3B-8) or its own held bound.
This rule produces NO new measurement; it decides only the bead's STATE on the target candidate, from two inputs:

  1. HOST STATE (from the host line's index entry on the target candidate):
       RELEASED  class RELEASED with a value;
       BOUNDED   class HELD with a low end (a point low == high is a bounded HELD line, not a released one);
       BLANK     class HELD with no number;
       anything else (EXCLUDED, absent, no host id) -> the row cannot be restated (BeadStateError: STALE / NO_HOST).
     A host with a one-sided beside figure is HELD; it is BOUNDED when its index entry has a low end, else BLANK.
  2. BEAD LEDGER FORM: MEASURED (a length > 0), HELD_BOUND (own low .. high, high > 0; a 0 low is allowed with a
     non-zero high, R-T698-1 rule 9), HELD_BLANK (own cause, no number).

  STATE TABLE (bead after-state):
       host RELEASED + MEASURED     -> RELEASED   value = the ledger length (released together with its host)
       host RELEASED + HELD_BOUND   -> HELD_BOUND the ledger's own bound (the bead's own cause)
       host BOUNDED  + MEASURED     -> HELD_BOUND low = high = the ledger length (held with the host's cause; the
                                       ledger length is the bead's figure, never the host's m2 and never 0)
       host BOUNDED  + HELD_BOUND   -> HELD_BOUND the ledger's own bound, both causes named
       host BLANK    + MEASURED / HELD_BOUND
                                    -> HELD_BLANK with the host's cause; the ledger figure is kept as REFERENCE TEXT
                                       only (ledger_ref), never a quantity, never summed, never 0
       any host      + HELD_BLANK   -> HELD_BLANK with the bead's own cause (+ the host's when the host is HELD)

  3. A drawing-derived band beside the owner method (e.g. G1 .. structural soffit, F-T697-1) is carried as text in
     `drawing_band`; it is never the bound and never a second quantity (Checker T-697: 'not a second quantity').
  4. ONE ARRIS ONCE: an arris id appears in one row and under one host; a repeated id or an id under two hosts fails.
  5. OWNER TRADE: every row names 'plaster (B4-09)'.
  6. NEVER 0: a RELEASED value, a point bound or a bound high of 0 fails; a HELD_BLANK carries no number.

Scope: every villa (no project data here). Provenance: Lead ruling 2026-11-11 16:25 (F-T705-1), register rulings
2026-11-11 04:20 (B4-09) / 08:25 (arris once), Checker T-697 verdict (F-T697-1 G1 = owner method), UP-QTY-STATUS-001.
"""
from __future__ import annotations

RULE_ID, RULE_VERSION = "R-T728-1", "1.0.0"
OWNER_TRADE = "plaster (B4-09)"
RELEASED, BOUNDED, BLANK = "RELEASED", "BOUNDED", "BLANK"
MEASURED, HELD_BOUND, HELD_BLANK = "MEASURED", "HELD_BOUND", "HELD_BLANK"


class BeadStateError(ValueError):
    pass


def r6(x):
    return None if x is None else round(float(x), 6)


def host_state(line):
    """rule 1 -> RELEASED / BOUNDED / BLANK, or BeadStateError."""
    if line is None:
        raise BeadStateError("STALE: host line absent from the target candidate")
    cls = line.get("class")
    if cls == "RELEASED":
        if line.get("measured_net") in (None, 0, 0.0):
            raise BeadStateError(f"{line.get('line_id')}: RELEASED host without a non-zero value")
        return RELEASED
    if cls == "HELD":
        lo, hi = line.get("held_low"), line.get("held_high")
        if lo is None and hi is None:
            return BLANK
        if lo is None:
            raise BeadStateError(f"{line.get('line_id')}: HELD host with a high end and no low end")
        if hi is not None and hi < lo:
            raise BeadStateError(f"{line.get('line_id')}: host bound inverted {lo} .. {hi}")
        return BOUNDED
    raise BeadStateError(f"{line.get('line_id')}: host class {cls!r} cannot host a bead (EXCLUDED / unknown)")


def host_bound_text(line, state):
    if state == RELEASED:
        return f"RELEASED {r6(line['measured_net'])} {line.get('unit', '')}".strip()
    if state == BOUNDED:
        hi = line.get("held_high")
        return f"HELD {r6(line['held_low'])} .. {'OPEN' if hi is None else r6(hi)} {line.get('unit', '')}".strip()
    return "HELD blank"


def ledger_form(length=None, low=None, high=None):
    """rule 2 -> (form, length, low, high)."""
    if length is not None:
        if low is not None or high is not None:
            raise BeadStateError("a ledger row carries a length AND a bound")
        if float(length) <= 0:
            raise BeadStateError(f"a measured bead length must be > 0, got {length}")
        return MEASURED, r6(length), None, None
    if low is not None or high is not None:
        if low is None or high is None:
            raise BeadStateError("a held bead bound needs both ends")
        if float(high) <= 0 or float(high) < float(low) or float(low) < 0:
            raise BeadStateError(f"bad held bead bound {low} .. {high}")
        return HELD_BOUND, None, r6(low), r6(high)
    return HELD_BLANK, None, None, None


def bead_state(form, length, low, high, hstate, *, own_cause="", host_cause=""):
    """rule 2 state table -> dict(state, value, low, high, ledger_ref, cause)."""
    out = {"state": None, "value": None, "low": None, "high": None, "ledger_ref": "", "cause": ""}
    if hstate not in (RELEASED, BOUNDED, BLANK):
        raise BeadStateError(f"unknown host state {hstate!r}")
    if form == HELD_BLANK:
        out.update(state=HELD_BLANK, cause=own_cause if hstate == RELEASED else _both(own_cause, host_cause))
    elif hstate == RELEASED and form == MEASURED:
        out.update(state=RELEASED, value=length, cause="released together with its host")
    elif hstate == RELEASED:
        out.update(state=HELD_BOUND, low=low, high=high, cause=own_cause)
    elif hstate == BOUNDED and form == MEASURED:
        out.update(state=HELD_BOUND, low=length, high=length, cause=_both("", host_cause))
    elif hstate == BOUNDED:
        out.update(state=HELD_BOUND, low=low, high=high, cause=_both(own_cause, host_cause))
    else:  # host BLANK, ledger MEASURED / HELD_BOUND
        ref = f"{length}" if form == MEASURED else f"{low} .. {high}"
        out.update(state=HELD_BLANK, ledger_ref=f"ledger {ref} m (reference text, not a quantity)",
                   cause=_both(own_cause if form == HELD_BOUND else "", host_cause))
    check_one(out)
    return out


def _both(own, host):
    parts = []
    if own:
        parts.append(f"bead: {own}")
    if host:
        parts.append(f"host: {host}")
    return " || ".join(parts)


def check_one(b):
    """rule 6 on one after-state."""
    s = b["state"]
    if s == RELEASED:
        if b["value"] is None or b["value"] <= 0:
            raise BeadStateError("RELEASED bead without a non-zero length")
    elif s == HELD_BOUND:
        if b["low"] is None or b["high"] is None or b["high"] <= 0 or b["high"] < b["low"]:
            raise BeadStateError(f"bad HELD bound {b['low']} .. {b['high']}")
        if b["value"] is not None:
            raise BeadStateError("a HELD bead carries a released value")
    elif s == HELD_BLANK:
        if any(b[k] is not None for k in ("value", "low", "high")):
            raise BeadStateError("a HELD_BLANK bead carries a number")
    else:
        raise BeadStateError(f"unknown bead state {s!r}")


def check_rows(rows):
    """rules 4 - 6 over a restated ledger: one arris once, one host, owner named, never released on a held host."""
    seen = {}
    for r in rows:
        eid = r["edge_id"]
        if eid in seen:
            raise BeadStateError(f"arris {eid} restated twice (hosts {seen[eid]} / {r['host_line']})")
        seen[eid] = r["host_line"]
        if r.get("owner_trade") != OWNER_TRADE:
            raise BeadStateError(f"{eid}: owner trade not named as {OWNER_TRADE}")
        if r["bead_state"] == RELEASED and r["host_state"] != RELEASED:
            raise BeadStateError(f"{eid}: bead RELEASED on a {r['host_state']} host")
        check_one({"state": r["bead_state"], "value": r.get("value"), "low": r.get("low"), "high": r.get("high")})
    return len(seen)
