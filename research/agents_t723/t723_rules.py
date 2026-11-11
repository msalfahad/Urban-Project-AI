"""R-T723-1 WIRING READINESS ROUND 4 (T-723, research; every villa). Extends R-T705-1 1.0.0 (applied unchanged through
`t705_rules`) and R-T698-1 1.1.0 with what the next hub packages need once one-sided figures, text-only restatements,
superseding ledgers and a previous map restated on a new candidate meet in one round. No quantity is produced, changed
or wired here.

  1. ONE-SIDED BESIDE. A ledger figure bounded on one side only (AT_LEAST / AT_MOST, or CONDITIONAL on a payable form) is
     an after-state of its own kind, ONE_SIDED: it is wired BESIDE a HELD line (the line keeps no measured_net and no
     range; never summed; never a range; never 0). Against the line's current beside record the action is KEEP (same
     side and value to 6 dp), RESTATE_BESIDE (another figure already beside: the package replaces it and says why) or
     BESIDE (none yet). A ONE_SIDED after-state on a line that already carries a released value or a two-ended range is
     FORM_CONFLICT: not wireable as stated (the ledger narrows nothing; the Lead / Checker decides which form governs).
  2. TEXT. A BLANK after-state that names its cause on a line that is already blank moves no number: action TEXT (the
     record's cause / question changes; Gate B still lists it, because 'every other line byte-identical' counts it).
     The same BLANK on a line that carries a number is a CHANGE (a downgrade), never TEXT.
  3. EXCLUDED. A NOT_APPLICABLE after-state (the surface or member is no element of the family, its owner named) carries
     no quantity and is never stated as 0: CHANGE when the line still carries a figure or a range, KEEP when it is
     already excluded.
  4. ONE LIVE ROW PER LINE. Several merged pieces may restate the same line. Rows with the same after-state are one
     statement: the earliest merge is LIVE, later ones DUPLICATE (counted once). Different after-states: the later merge
     is LIVE and the earlier SUPERSEDED only when the later ledger declares that it restates the earlier one for that
     line; otherwise CONFLICT (fails the build: the Lead decides, the map never picks a number). A row that only states
     the line (NO_PROPOSAL) is a STATEMENT: it proposes nothing, so it never conflicts and is never counted.
  5. ONE LINE PER ROW. A ledger row (piece + row key) maps to at most one target line; a row mapped to two lines fails
     (split by carrier first, R-T698-1 6b).
  6. RESTATED MAP. A previous round's row is re-classified on the new candidate: its host absent -> STALE (fails);
     its index entry (class, value, range) or its beside record changed between the two candidates -> HOST_CHANGED with
     the cause; a host a READY (unmerged) package changes -> PENDING_CHANGE on that package; otherwise MAPPED as before.
     Its after-state is re-tested against the new line (rule 1 .. 3 and R-T705-1 rule 3).
  7. RULING RESTATE. A row whose after-state rests on a register reading the Lead has since replaced carries the flag
     RULING_RESTATE (its class stays the R-T698-1 class): the ledger must be restated under the new ruling before
     wiring; the map carries it, never re-derives it, and its package is not buildable until then.
  8. PACKAGE SIZE (extends R-T705-1 rule 6). changed = distinct lines with CHANGE / BESIDE / RESTATE_BESIDE; text =
     distinct lines with TEXT only; added = lines ADDed. KEEP, NONE, DUPLICATE and SUPERSEDED rows move nothing.

Scope: every villa (no project data in this module). Provenance: T-723 (lane I, 2026-11-11), Lead row T-723 and the
register rulings 2026-11-11 16:25 (CORNER BEAD HEIGHT STATE; STAIRS concrete vs finish faces) and 20:25 (VOIDS B2-05).
"""
from __future__ import annotations

import sys
from pathlib import Path

_T705 = Path(__file__).resolve().parents[1] / "agents_t705"
if str(_T705) not in sys.path:
    sys.path.insert(0, str(_T705))
import t705_rules as R705  # noqa: E402

R698 = R705.R698
RULE_ID, RULE_VERSION = "R-T723-1", "1.0.0"
BASE_RULES = ((R705.RULE_ID, R705.RULE_VERSION), (R698.RULE_ID, R698.RULE_VERSION))
ReadinessError = R705.ReadinessError
r6 = R705.r6

ONE_SIDED, EXCLUDED = "ONE_SIDED", "EXCLUDED"
SIDES = ("AT_LEAST", "AT_MOST", "CONDITIONAL")
KEEP, CHANGE, ADD, NONE = R705.KEEP, R705.CHANGE, R705.ADD, R705.NONE
BESIDE, RESTATE_BESIDE, TEXT, FORM_CONFLICT = "BESIDE", "RESTATE_BESIDE", "TEXT", "FORM_CONFLICT"
MOVING = (CHANGE, BESIDE, RESTATE_BESIDE)
LIVE, DUPLICATE, SUPERSEDED, STATEMENT = "LIVE", "DUPLICATE", "SUPERSEDED", "STATEMENT"
HOST_CHANGED, PENDING, RULING_RESTATE = R698.HOST_CHANGED, R698.PENDING_CHANGE, "RULING_RESTATE"


def after(kind, value=None, lo=None, hi=None, note="", side=None):
    """R-T705-1 after-states plus ONE_SIDED (rule 1) and EXCLUDED (rule 3)."""
    if kind == ONE_SIDED:
        if side not in SIDES:
            raise ReadinessError(f"ONE_SIDED side {side!r}")
        v = r6(value)
        if v is None:
            raise ReadinessError("ONE_SIDED without its figure")
        if v <= 0 and side == "AT_LEAST":
            raise ReadinessError("an AT_LEAST figure of 0 says nothing: state BLANK with the cause")
        if v < 0 or (v == 0 and side != "AT_LEAST"):
            raise ReadinessError(f"ONE_SIDED {side} figure {v} (never 0, never negative)")
        if lo is not None or hi is not None:
            raise ReadinessError("ONE_SIDED is never a range")
        return {"kind": ONE_SIDED, "side": side, "value": v, "low": None, "high": None, "note": note}
    if kind == EXCLUDED:
        if value is not None or lo is not None or hi is not None:
            raise ReadinessError("EXCLUDED carries no number (never 0)")
        return {"kind": EXCLUDED, "value": None, "low": None, "high": None, "note": note}
    return R705.after(kind, value=value, lo=lo, hi=hi, note=note)


def after_text(a):
    if a is None:
        return "-"
    if a["kind"] == ONE_SIDED:
        return f"ONE_SIDED {a['side']} {a['value']}"
    if a["kind"] == EXCLUDED:
        return EXCLUDED
    return R705.after_text(a)


def _numbers(line):
    return r6(line.get("measured_net")), r6(line.get("held_low")), r6(line.get("held_high"))


def wire_action(a, line, beside=None, *, adds=False, yields_line=True):
    """rules 1 .. 3 (and R-T705-1 rule 3) -> (action, reason). `beside` = {side, value} already beside the line."""
    if not yields_line:
        return NONE, "the row yields no line of this family"
    if adds:
        return ADD, "the target has no line for it: the package adds one"
    if line is None:
        return NONE, "no target line"
    v, lo, hi = _numbers(line)
    if a["kind"] == ONE_SIDED:
        if v is not None or (lo is not None and hi is not None):
            return FORM_CONFLICT, (f"{R698.state_text(line)} already carries a figure / range; a one-sided "
                                   f"{a['side']} {a['value']} narrows nothing (rule 1)")
        if beside and beside.get("side") == a["side"] and r6(beside.get("value")) == a["value"]:
            return KEEP, f"already beside: {a['side']} {a['value']}"
        if beside:
            return RESTATE_BESIDE, f"beside {beside.get('side')} {beside.get('value')} -> {a['side']} {a['value']}"
        return BESIDE, f"{R698.state_text(line)}: {a['side']} {a['value']} beside, never in the line"
    if a["kind"] == EXCLUDED:
        if line.get("class") in ("EXCLUDED", "NOT_APPLICABLE") and v is None and lo is None and hi is None:
            return KEEP, "already excluded"
        return CHANGE, f"{R698.state_text(line)} -> EXCLUDED (no quantity, never 0)"
    if a["kind"] == R705.BLANK and v is None and lo is None and hi is None:
        return TEXT, "blank stays blank: the record names the cause (no number moves)"
    return R705.wire_action(a, line)


def check_after(rows):
    """rule 1 / 3 / R-T705-1 rule 3 on every row: no held / one-sided / excluded state carried as 0."""
    for r in rows:
        a = r.get("after")
        if not a:
            continue
        if a["kind"] in (EXCLUDED, R705.BLANK) and a.get("value") is not None:
            raise ReadinessError(f"row {r['row']}: {a['kind']} carries {a['value']}")
        if a["kind"] == ONE_SIDED and not a["value"]:
            raise ReadinessError(f"row {r['row']}: one-sided figure 0")
    R705.check_no_zero([r for r in rows if r.get("after") and r["after"]["kind"] not in (ONE_SIDED, EXCLUDED)])
    return True


def check_one_line_per_row(rows):
    """rule 5: a ledger row maps to one line at most."""
    seen = {}
    for r in rows:
        key = (r["piece"], r["row"])
        tgt = r.get("host_line_id") or r.get("new_line_key")
        if tgt is None:
            continue
        if key in seen and seen[key] != tgt:
            raise ReadinessError(f"row {key} mapped to two lines {seen[key]} and {tgt}")
        seen[key] = tgt
    return True


def resolve_live(rows, order, supersedes):
    """rule 4. `order` = pieces in merge order; `supersedes` = {(later, earlier): set(line ids)} declared by the later
    ledger. Sets r['live'] on every row naming a target; raises on an undeclared conflict."""
    rank = {p: i for i, p in enumerate(order)}
    by = {}
    for r in rows:
        tgt = r.get("host_line_id") or r.get("new_line_key")
        if tgt is None or r["action"] == NONE:
            r["live"] = None
            continue
        if r.get("after") and r["after"]["kind"] == R705.NOPROP:
            r["live"] = STATEMENT          # states the line, proposes nothing: never a conflict, never counted
            continue
        by.setdefault(tgt, []).append(r)
    for tgt, rs in by.items():
        rs.sort(key=lambda r: (rank[r["piece"]], r["row"]))
        first = rs[0]
        first["live"] = LIVE
        for r in rs[1:]:
            if after_text(r["after"]) == after_text(first["after"]):
                r["live"] = DUPLICATE
                r["live_of"] = first["row"]
                continue
            if tgt in supersedes.get((r["piece"], first["piece"]), set()):
                first["live"], first["live_of"] = SUPERSEDED, r["row"]
                r["live"] = LIVE
                first = r
                continue
            raise ReadinessError(f"CONFLICT on {tgt}: {first['row']} {after_text(first['after'])} vs {r['row']} "
                                 f"{after_text(r['after'])} (no supersession declared)")
    return True


def restate_class(host, old_index, new_index, old_beside, new_beside, pending):
    """rule 6 -> (class, reason)."""
    if host not in new_index:
        return R698.STALE, f"{host} absent from the new candidate"
    if host in pending:
        return PENDING, f"{pending[host]} changes {host}"
    if R698.state_key(old_index.get(host)) != R698.state_key(new_index[host]):
        return HOST_CHANGED, f"index entry changed: {R698.state_text(old_index.get(host))} -> {R698.state_text(new_index[host])}"
    if (old_beside or {}).get(host) != (new_beside or {}).get(host):
        return HOST_CHANGED, f"beside record changed: {(old_beside or {}).get(host)} -> {(new_beside or {}).get(host)}"
    return R698.MAPPED, "host present, same index entry and beside record on both candidates"


def package_size(rows):
    """rule 8 -> counts over LIVE rows."""
    live = [r for r in rows if r.get("live") in (LIVE, None)]
    ch = sorted({r["host_line_id"] for r in live if r.get("action") in MOVING and r.get("host_line_id")})
    tx = sorted({r["host_line_id"] for r in live if r.get("action") == TEXT and r.get("host_line_id")} - set(ch))
    ad = sorted({r["new_line_key"] for r in live if r.get("action") == ADD})
    return {"changed": len(ch), "text_only": len(tx), "added": len(ad), "changed_ids": ch, "text_ids": tx,
            "added_keys": ad}
