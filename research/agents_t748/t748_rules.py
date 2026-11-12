"""R-T748-1 WIRING READINESS ROUND 6 (T-748, research; every villa on the engine's line-index scheme).

Restates a merged wiring-readiness map (R-T730-1 rows) on a NEWER candidate after Gate B packages merged, and maps the
pieces merged since that map to their hubs by line id. Pure functions; no drawing, no candidate, no quantity is
produced, changed or wired. Builds on R-T730-1 1.0.0 (ids: full id or unique >= 8-hex prefix, never a neighbour).

  1. RESTATE. Every mapped row is re-read on the newer index: a cited host absent there is STALE and fails the build
     (never re-mapped). A host whose index entry is byte-equal on the map's candidate and on the newer one is
     UNCHANGED; otherwise HOST_CHANGED with the package(s) that moved it, and the row must be re-derived by its hub
     (its old 'before' is never wired).
  2. MERGED HUB. A row of a hub whose package has merged is WIRED when the package's row set names the host line
     (WIRED_SAME when the index now carries the row's after-state, WIRED_RESTATED when the package's Gate B carried
     another, Checker-verified state: the package record governs, the row moves nothing). A moving LIVE row of a
     merged hub that the package did not name is UNWIRED_AFTER_MERGE (a finding, listed by id, never dropped).
  3. BLOCKERS. A blocker naming a board row that is now MERGED is CLEARED (kept in the row with the merge); a READY row
     stays PENDING_ON; QUEUED / TODO stays WAITS; a RULING stays until the ruling id is answered.
  4. RELEASED UNCHANGED. A restatement whose after-state differs from a RELEASED line by no more than the piece's own
     named ledger rounding (|d| <= 0.0005 in the line's unit, cause named by the piece) is KEEP_RELEASED; a larger
     difference on a released line is CHANGE_RELEASED and is flagged for the package's Gate B (a released figure is
     only moved by a Checker record or a Gate B package, never by a map).
  5. DOWNGRADE RECORD. An issued Checker downgrade record maps as DOWNGRADE on each of its lines to the hub of the
     line's family. It is APPLIED only when the index's own downgrade input lists it; otherwise NOT_APPLIED_IN_INDEX
     (the statement keeps the index state and prints the record beside). The record file's downgrade_id is the
     identity; a different id cited in board text is a finding, never a second record.
  6. ONE HUB PER TARGET. Every moving target (a line id, or a new-line key for an ADD) belongs to exactly one hub;
     a target in two hubs fails the build unless the line is in the declared conflict register with its decider.
  7. NO-LINE PIECES. A merged census whose family has no candidate line maps to ADD_FAMILY rows keyed
     '<family>@<scope>', HELD where the piece holds it (never 0), with a hub or NO_PACKAGE_ROW (never dropped).

Scope: every villa (no project data here). Provenance: T-748 (lane I, 2026-11-12), Lead row T-748; R-T730-1 1.0.0.
"""
from __future__ import annotations

import re
from decimal import Decimal

RULE_ID, RULE_VERSION = "R-T748-1", "1.0.0"
BASE_RULES = (("R-T730-1", "1.0.0"), ("R-T739-1", "1.0.0"))
FULL = re.compile(r"^L-[0-9a-f]{20}$")
PREFIX = re.compile(r"^L-[0-9a-f]{8,19}$")
MOVING = ("CHANGE", "ADD", "BESIDE", "RESTATE_BESIDE", "TEXT", "DOWNGRADE", "ADD_FAMILY", "CHANGE_RELEASED")
ROUNDING = Decimal("0.0005")
BOARD_STATES = ("MERGED", "READY", "CLAIMED", "TODO", "QUEUED", "BLOCKED", "REJECTED")


class ReadinessError(Exception):
    pass


def resolve(cited, index_ids):
    """rule 7 of R-T730-1: full id or unique >= 8-hex prefix; absent / ambiguous fails (never a neighbour)."""
    if not isinstance(cited, str):
        raise ReadinessError(f"{cited!r}: not a line id")
    if FULL.match(cited):
        if cited in index_ids:
            return cited
        raise ReadinessError(f"{cited}: STALE (absent on the newer index); never re-mapped to a neighbour")
    if not PREFIX.match(cited):
        raise ReadinessError(f"{cited}: too short or malformed for a line id")
    hits = [i for i in index_ids if i.startswith(cited)]
    if len(hits) != 1:
        raise ReadinessError(f"{cited}: {'absent' if not hits else 'ambiguous'} on the newer index")
    return hits[0]


def state(ln):
    """the comparable state of an index line."""
    return {"class": ln["class"], "value": ln["measured_net"], "low": ln["held_low"], "high": ln["held_high"],
            "unit": ln["unit"], "item_code": ln["item_code"]}


def host_status(lid, old, new, movers):
    """rule 1 -> (status, packages)."""
    if lid not in new:
        raise ReadinessError(f"{lid}: STALE on the newer index")
    if lid not in old:
        return "HOST_ADDED", sorted(movers.get(lid, ()))
    if old[lid] == new[lid]:
        return "UNCHANGED", []
    who = sorted(movers.get(lid, ()))
    if not who:
        raise ReadinessError(f"{lid}: index entry moved with no package naming it")
    return "HOST_CHANGED", who


def refresh_blockers(blockers, board):
    """rule 3 -> (open, cleared). board: {row id: state}."""
    open_, cleared = [], []
    for b in blockers:
        m = re.match(r"^(PENDING_ON|WAITS|CONFLICT)\s+(T-\d{3})\b", b)
        if m:
            st = board.get(m.group(2))
            if st is None:
                raise ReadinessError(f"{b}: blocker names a row absent from the board table")
            if st == "MERGED":
                cleared.append(f"{b} -> CLEARED ({m.group(2)} MERGED)")
                continue
            kind = "PENDING_ON" if st == "READY" else "WAITS"
            open_.append(f"{kind} {m.group(2)} ({st})" + b[m.end():])
            continue
        open_.append(b)
    return open_, cleared


def released_action(line_value, after_value, rounding_named):
    """rule 4 for a restatement on a RELEASED line."""
    d = abs(Decimal(str(after_value)) - Decimal(str(line_value)))
    if d == 0:
        return "KEEP", "0"
    if d <= ROUNDING and rounding_named:
        return "KEEP_RELEASED", format(d, "f")
    return "CHANGE_RELEASED", format(d, "f")


def downgrade_rows(records, index, applied_ids, cited_ids=()):
    """rule 5 -> (rows, findings)."""
    rows, findings = [], []
    for r in records:
        st = "APPLIED" if r["downgrade_id"] in applied_ids else "NOT_APPLIED_IN_INDEX"
        for lid in r["line_ids"]:
            ln = index.get(lid)
            if ln is None:
                raise ReadinessError(f"{r['downgrade_id']}: {lid} absent")
            rows.append({"line_id": lid, "downgrade_id": r["downgrade_id"], "status": st, "state": r["state"],
                         "index_class": ln["class"], "unit": ln["unit"], "engine_qty": r["engine_qty"]})
    have = {r["downgrade_id"] for r in records}
    for c in cited_ids:
        if c not in have and not any(h.startswith(c) for h in have):
            findings.append(f"{c}: cited on the board, no record with this id (record ids: {', '.join(sorted(have))})")
    return rows, findings


def one_hub_per_target(rows, conflicts=None):
    """rule 6 -> {target: hub}; raises on a target in two hubs that is not declared."""
    conflicts = conflicts or {}
    own = {}
    for r in rows:
        if r["action"] not in MOVING or r.get("live", "LIVE") != "LIVE":
            continue
        t = r["target"]
        if t in own and own[t] != r["hub"] and t not in conflicts:
            raise ReadinessError(f"{t}: moved by two hubs ({own[t]}, {r['hub']}) with no declared decider")
        own.setdefault(t, r["hub"])
    return own


def add_family(family, scope, hub, held, low=None, high=None):
    """rule 7."""
    if held and low is not None and high is not None and Decimal(str(high)) == 0:
        raise ReadinessError(f"{family}@{scope}: a held family line is never carried as 0 .. 0")
    if low is not None and high is not None and Decimal(str(low)) > Decimal(str(high)):
        raise ReadinessError(f"{family}@{scope}: low above high")
    return {"target": f"{family}@{scope}", "action": "ADD_FAMILY", "hub": hub or "NO_PACKAGE_ROW",
            "held": held, "low": low, "high": high, "live": "LIVE"}
