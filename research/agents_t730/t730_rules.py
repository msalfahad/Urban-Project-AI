"""R-T730-1 WIRING READINESS ROUND 5 (T-730, research; every villa). Extends R-T723-1 1.0.0 (applied unchanged through
`t723_rules`, itself on R-T705-1 1.0.0 and R-T698-1 1.1.0) with what a map restated AFTER Gate B packages merged needs:
rows those packages wired, conflicts between merged pieces that only a pending row can settle, the capped-blank form,
derived-element ledgers restated arris by arris, and one blocker list per row. No quantity is produced, changed or wired.

  1. WIRED. A restated row whose after-state the candidate now carries is WIRED: VALUE / BOUND / EXCLUDED equal on the
     line index (6 dp); ONE_SIDED equal (side and value, 6 dp) in the beside register rebuilt from the merged packages;
     a BLANK-with-cause (TEXT) row only when a merged package's named record lists the line (the index cannot show a
     cause). A WIRED row moves nothing, is counted once and is never wired again. A row that only stated its line
     (NO_PROPOSAL) or was KEEP before stays what it was (never WIRED: it proposed nothing).
  2. CONFLICT CARRIED. Two merged pieces stating different after-states for one line with no supersession declared:
     R-T723-1 rule 4 fails the build, EXCEPT for a line listed in the declared conflict register with its decider (a
     named board row or the Lead): then every row on that line is CONFLICT, none is LIVE, the line moves in no package
     and the decider is the row's blocker. The map never picks a number; an unlisted conflict still fails.
  3. FORM RESTATE. A ONE_SIDED AT_MOST after-state on a line whose index carries a two-ended range with a low of exactly
     0 is a CHANGE (the 0 .. x form becomes a blank line with x beside as its cap) only when a merged rule declares that
     a 0 low is no floor for that line (named in `form_rules`); otherwise R-T723-1 rule 1 FORM_CONFLICT stands.
  4. CAP. A BLANK_NAMED ledger row with a cap is ONE_SIDED AT_MOST (the cap beside a blank line): never a range from 0,
     never 0, never summed; a BLANK_NAMED row without a cap is BLANK. A cap of exactly 0 is refused as a cap (it
     would state the quantity as 0): the row is BLANK and flagged CAP_ZERO for its hub to settle (ZERO_BY_GEOMETRY
     with evidence that the face does not exist, or a re-measure); never carried as 0.
  5. ARRIS RESTATEMENT. A derived-element ledger restated under a ruling (bead lm on its host) supersedes the earlier
     ledger arris by arris: every earlier ADD row has exactly one restating row with the same arris id AND the same host
     line, and the restating ledger adds no arris of its own; otherwise the build fails (no arris lost or added
     silently, none moved to another host).
  6. BLOCKERS. Every row that is neither WIRED nor moving-free names its blockers: PENDING_ON <READY package>, WAITS
     <TODO / QUEUED row>, DESIGNER <item>, RULING <id>, CONFLICT <decider>. A designer item under a row that is added or
     kept HELD blank is its cause (held_on), not a blocker: the HELD line is exactly what the package wires. A hub is
     buildable in one run when its LIVE moving rows carry no blocker other than its own package or packages earlier in
     the hub order.
  7. IDS. A cited id resolves only as a full id or a unique prefix of >= 8 hex digits (R-T705-1 rule 1). An absent id is
     STALE and fails the build; it is never re-mapped to a neighbour (same element id on another line, the next line of
     the same code, the nearest geometry or another storey's line).

Scope: every villa (no project data in this module). Provenance: T-730 (lane I, 2026-11-12), Lead row T-730; rulings
cited by the rows they govern (CORNER BEAD HEIGHT STATE 2026-11-11 16:25 via R-T728-1; R-T724-3 capped blank).
"""
from __future__ import annotations

import sys
from pathlib import Path

_T723 = Path(__file__).resolve().parents[1] / "agents_t723"
if str(_T723) not in sys.path:
    sys.path.insert(0, str(_T723))
import t723_rules as R723  # noqa: E402

R705, R698 = R723.R705, R723.R698
RULE_ID, RULE_VERSION = "R-T730-1", "1.0.0"
BASE_RULES = ((R723.RULE_ID, R723.RULE_VERSION), (R705.RULE_ID, R705.RULE_VERSION), (R698.RULE_ID, R698.RULE_VERSION))
ReadinessError = R723.ReadinessError
r6 = R723.r6
after, after_text = R723.after, R723.after_text

WIRED, CONFLICT, FORM_RESTATE = "WIRED", "CONFLICT", "FORM_RESTATE"
KEEP, CHANGE, ADD, NONE, TEXT = R723.KEEP, R723.CHANGE, R723.ADD, R723.NONE, R723.TEXT
BESIDE, RESTATE_BESIDE, FORM_CONFLICT = R723.BESIDE, R723.RESTATE_BESIDE, R723.FORM_CONFLICT
MOVING = R723.MOVING
LIVE, DUPLICATE, SUPERSEDED, STATEMENT = R723.LIVE, R723.DUPLICATE, R723.SUPERSEDED, R723.STATEMENT
BLOCKER_KINDS = ("PENDING_ON", "WAITS", "DESIGNER", "RULING", "CONFLICT")


def resolve(cited, target):
    """rule 7 -> full line id; raises on an absent or ambiguous id (never a neighbour)."""
    full, cls, why = R705.resolve_id(cited, target)
    if full is None:
        raise ReadinessError(f"{cited}: {cls} ({why}); never re-mapped to a neighbour")
    return full


def cap_after(cap, note=""):
    """rule 4."""
    if cap is None:
        return after(R705.BLANK, note=note)
    if r6(cap) == 0:
        return after(R705.BLANK, note=("CAP_ZERO refused as a cap (rule 4): " + note)[:120])
    return after(R723.ONE_SIDED, side="AT_MOST", value=cap, note=("cap: " + note)[:120])


def carried(a, line, beside, named):
    """rule 1: does the candidate carry the after-state? (index / beside register / named record)"""
    if a is None or line is None:
        return False
    k = a["kind"]
    v, lo, hi = r6(line.get("measured_net")), r6(line.get("held_low")), r6(line.get("held_high"))
    if k == R723.ONE_SIDED:
        return bool(beside) and beside.get("side") == a["side"] and r6(beside.get("value")) == a["value"] \
            and v is None and not (lo is not None and hi is not None)
    if k == R723.EXCLUDED:
        return line.get("class") in ("EXCLUDED", "NOT_APPLICABLE") and v is None and lo is None and hi is None
    if k == R705.BLANK:
        return v is None and lo is None and hi is None and named
    if k in (R705.VALUE, R705.BOUND, R705.ZERO):
        return R705.line_matches(a, line)
    return False


def wire_action(a, line, beside=None, *, named=False, was=None, form_rule=None):
    """rules 1 / 3 on top of R-T723-1 wire_action -> (action, reason). `was` = the row's action on the previous map."""
    if line is not None and a is not None and was in MOVING + (TEXT,) and carried(a, line, beside, named):
        return WIRED, "the candidate carries the after-state (wired by a merged package)"
    if a is not None and a["kind"] == R723.ONE_SIDED and a["side"] == "AT_MOST" and line is not None:
        v, lo, hi = r6(line.get("measured_net")), r6(line.get("held_low")), r6(line.get("held_high"))
        if v is None and lo == 0 and hi is not None:
            if form_rule:
                return CHANGE, (f"{FORM_RESTATE} ({form_rule}): {R698.state_text(line)} -> blank, cap {a['value']} "
                                "beside (a 0 low is no floor)")
            return FORM_CONFLICT, f"{R698.state_text(line)}: a 0 .. x range against a cap; no form rule declared"
    return R723.wire_action(a, line, beside)


def resolve_live(rows, order, supersedes, conflicts):
    """rule 2 on top of R-T723-1 rule 4. `conflicts` = {line id: decider}. Rows on a listed line are all CONFLICT; a
    listed line without an actual conflict fails (the register must stay true)."""
    on = {}
    for r in rows:
        t = r.get("host_line_id") or r.get("new_line_key")
        if t in conflicts and r.get("action") != NONE and r.get("after") and r["after"]["kind"] != R705.NOPROP:
            on.setdefault(t, []).append(r)
    for t, dec in conflicts.items():
        rs = on.get(t, [])
        if len({after_text(r["after"]) for r in rs}) < 2 or len({r["piece"] for r in rs}) < 2:
            raise ReadinessError(f"conflict register lists {t} but its rows do not conflict")
        for r in rs:
            r["live"], r["action_reason"] = CONFLICT, f"CONFLICT on the line, decider {dec}: " + r.get("action_reason", "")
            r.setdefault("blockers", []).append(f"CONFLICT {dec}")
    rest = [r for r in rows if r.get("live") != CONFLICT]
    R723.resolve_live(rest, order, supersedes)
    return True


def arris_supersede(earlier, later, *, key="element", host="host_line_id"):
    """rule 5 -> {earlier row id: later row id}; raises on a lost / added / moved arris."""
    e = {}
    for r in earlier:
        e.setdefault(r[key], []).append(r)
    lt = {}
    for r in later:
        lt.setdefault(r[key], []).append(r)
    bad = [k for k, v in list(e.items()) + list(lt.items()) if len(v) != 1]
    if bad:
        raise ReadinessError(f"arris stated twice in one ledger: {sorted(set(bad))[:3]}")
    if set(e) != set(lt):
        raise ReadinessError(f"arris lost {sorted(set(e) - set(lt))[:3]} / added {sorted(set(lt) - set(e))[:3]}")
    out = {}
    for k, (r,) in e.items():
        (n,) = lt[k]
        if r[host] != n[host]:
            raise ReadinessError(f"arris {k} moved from host {r[host]} to {n[host]}")
        out[r["row"]] = n["row"]
    return out


def check_blockers(rows):
    """rule 6: every blocker is of a known kind and names its object."""
    for r in rows:
        for b in r.get("blockers", []):
            kind, _, obj = b.partition(" ")
            if kind not in BLOCKER_KINDS or not obj.strip():
                raise ReadinessError(f"row {r['row']}: blocker {b!r}")
    return True


def buildable(rows, earlier_hubs=()):
    """rule 6: a hub is buildable when its live moving rows carry no blocker other than its own / earlier hubs' packages
    (`earlier_hubs` includes the hub itself)."""
    ok = tuple(f"PENDING_ON {h}" for h in earlier_hubs)
    open_ = sorted({b for r in rows if r.get("live") in (LIVE, None, CONFLICT) and r.get("action") not in (NONE, KEEP, WIRED)
                    for b in r.get("blockers", []) if not b.startswith(ok)})
    return not open_, open_


def package_size(rows):
    """R-T723-1 rule 8; WIRED / CONFLICT rows move nothing."""
    return R723.package_size([r for r in rows if r.get("live") != CONFLICT and r.get("action") != WIRED])
