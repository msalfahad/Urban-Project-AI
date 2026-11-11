"""R-T705-1 WIRING READINESS ROUND 3 (T-705, research; every villa). Extends the mapping rule R-T698-1 1.1.0 (applied
unchanged through `t698_rules.classify`) with what a hub package needs to be built in one run from several merged pieces
at once. No quantity is produced, changed or wired here.

  1. SHORT IDS. A ledger may cite a host by an id prefix ('L-b1529955'). It resolves only when exactly one target line id
     starts with it (>= 8 hex digits after 'L-'); none -> STALE_ABSENT, more than one -> AMBIGUOUS_HOST. Never by guess.
  2. MULTI-HOST. A row naming two hosts ('L-a | L-b') is AMBIGUOUS_HOST (R-T698-1 6b): split by carrier before wiring.
  3. AFTER-STATE. Each row states the after-state the ledger proposes for its line: VALUE v, BOUND lo .. hi (hi None =
     OPEN / AT_LEAST), BLANK (held, no number) or KEEP (no proposal). The wire action is KEEP when the after-state equals
     the target line (value / bounds to 6 dp), CHANGE when it differs, ADD for a line the target lacks (a MISSING item or a
     split), NONE for a row that yields no line of the family (not an element of it, or owned by another trade's line).
     A HELD / BLANK after-state never carries 0 (R-T698-1 rule 9); an after-state of 0 is allowed only when the ledger
     states it as a calculated geometric zero (ZERO_BY_GEOMETRY), never for a missing value.
  4. CROSS-PIECE ORDER. When one piece of the round changes a line that another piece's rows rest on, those rows are
     MAPPED_PENDING_CHANGE on the first piece (R-T698-1 rule 5): wired after it, restated on its after-state.
  5. ONE OWNER. Every row names the owner trade of its element (register ruling); one element id claimed by two families
     fails; a pending stage that carries a length the register gives to another family fails (arris once: B4-09 owns the
     arris lm, B4-04 / T-314 carries face m2 only).
  6. PACKAGE SIZE. A package's changed-line count = distinct target line ids with CHANGE + lines ADDed; KEEP and NONE
     rows move nothing and are not counted.

Scope: every villa (no project data in this module). Provenance: T-705 (lane I, 2026-11-11), Lead row T-705 and the
register rulings 2026-11-11 04:20 (B4-09 corner beads) / 08:25 (arris once); lesson 08:25 'derived maps carry HELD'.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

_T698 = Path(__file__).resolve().parents[1] / "agents_t698"
if str(_T698) not in sys.path:
    sys.path.insert(0, str(_T698))
import t698_rules as R698  # noqa: E402

RULE_ID, RULE_VERSION = "R-T705-1", "1.0.0"
BASE_RULE = (R698.RULE_ID, R698.RULE_VERSION)
KEEP, CHANGE, ADD, NONE = "KEEP", "CHANGE", "ADD", "NONE"
ACTIONS = (KEEP, CHANGE, ADD, NONE)
VALUE, BOUND, BLANK, NOPROP, ZERO = "VALUE", "BOUND", "BLANK", "NO_PROPOSAL", "ZERO_BY_GEOMETRY"
ReadinessError = R698.ReadinessError
_SHORT = re.compile(r"^L-[0-9a-f]{8,20}$")


def resolve_id(cited, target):
    """rule 1 -> (full id or None, class or None, reason)."""
    if cited in target:
        return cited, None, "full id"
    if not _SHORT.match(str(cited or "")):
        return None, R698.STALE, f"{cited!r} is not a line id or a prefix of >= 8 hex digits"
    hits = sorted(k for k in target if k.startswith(cited))
    if len(hits) == 1:
        return hits[0], None, f"prefix {cited} -> {hits[0]} (unique)"
    if not hits:
        return None, R698.STALE, f"prefix {cited} matches no target line"
    return None, R698.AMBIGUOUS, f"prefix {cited} matches {len(hits)} lines {hits[:3]}"


def split_hosts(cited):
    return [h.strip() for h in str(cited or "").split("|") if h.strip()]


def r6(x):
    return None if x is None else round(float(x), 6)


def after(kind, value=None, lo=None, hi=None, note=""):
    """a ledger's proposed after-state (rule 3)."""
    if kind not in (VALUE, BOUND, BLANK, NOPROP, ZERO):
        raise ReadinessError(f"unknown after-state kind {kind}")
    a = {"kind": kind, "value": r6(value), "low": r6(lo), "high": r6(hi), "note": note}
    if kind == VALUE and a["value"] is None:
        raise ReadinessError("VALUE after-state without a value")
    if kind == VALUE and a["value"] == 0:
        raise ReadinessError("a 0 value must be stated as ZERO_BY_GEOMETRY (rule 3)")
    if kind == BOUND and a["low"] is None:
        raise ReadinessError("BOUND after-state without its low end")
    if kind == BOUND and a["high"] is not None and a["high"] < a["low"]:
        raise ReadinessError(f"BOUND high {a['high']} below low {a['low']}")
    if kind == BLANK and (a["value"] is not None or a["low"] is not None or a["high"] is not None):
        raise ReadinessError("BLANK after-state carries a number")
    if kind == ZERO:
        a["value"] = 0.0
    return a


def after_text(a):
    if a is None:
        return "-"
    k = a["kind"]
    if k in (VALUE, ZERO):
        return f"{k} {a['value']}"
    if k == BOUND:
        return f"BOUND {a['low']} .. {'OPEN' if a['high'] is None else a['high']}"
    return k


def line_matches(a, line):
    """does the target line already state the after-state? (6 dp)"""
    if line is None:
        return False
    v, lo, hi = r6(line.get("measured_net")), r6(line.get("held_low")), r6(line.get("held_high"))
    if a["kind"] == NOPROP:
        return True
    if a["kind"] in (VALUE, ZERO):
        return v == a["value"] and lo is None and hi is None
    if a["kind"] == BOUND:
        return v is None and lo == a["low"] and hi == a["high"]
    if a["kind"] == BLANK:
        return v is None and lo is None and hi is None
    return False


def wire_action(a, line, *, adds=False, yields_line=True):
    """rule 3 -> (action, reason)."""
    if not yields_line:
        return NONE, "the row yields no line of this family"
    if adds:
        return ADD, "the target has no line for it: the package adds one"
    if line is None:
        return NONE, "no target line"
    if line_matches(a, line):
        return KEEP, "the target line already states the after-state"
    return CHANGE, f"{R698.state_text(line)} -> {after_text(a)}"


def check_no_zero(rows):
    """rule 3 / R-T698-1 rule 9: a held or blank state is never 0; a 0 after-state only as ZERO_BY_GEOMETRY."""
    for r in rows:
        a = r.get("after")
        if a and a["kind"] in (BOUND, BLANK) and (a["value"] == 0):
            raise ReadinessError(f"row {r['row']}: held after-state carried as 0")
        if a and a["kind"] == VALUE and a["value"] == 0:
            raise ReadinessError(f"row {r['row']}: VALUE 0 not stated as ZERO_BY_GEOMETRY")
        if r.get("ledger_state") in ("HELD", "UNKNOWN") and r.get("qty") in (0, 0.0, "0"):
            raise ReadinessError(f"row {r['row']}: held / unknown ledger quantity carried as 0")
    return True


def check_one_owner(rows, key="element"):
    """rule 5: one element id, one owner family."""
    seen = {}
    for r in rows:
        e, fam = r.get(key), r.get("owner_family")
        if not e:
            continue
        if e in seen and seen[e] != fam:
            raise ReadinessError(f"element {e} claimed by {seen[e]} and {fam}")
        seen[e] = fam
    return True


def check_owner_named(rows):
    for r in rows:
        if not r.get("owner_family"):
            raise ReadinessError(f"row {r['row']}: no owner trade named")
    return True


def check_arris_once(stage_rows, *, forbidden_unit="lm", forbidden_words=("CORNER", "ARRIS", "BEAD")):
    """rule 5 on a pending face stage: it may carry face m2 only; any lm row or a corner / arris / bead element fails."""
    for s in stage_rows:
        txt = " ".join(str(s.get(k) or "") for k in ("element_id", "element", "line_key")).upper()
        if s.get("unit") == forbidden_unit or any(w in txt for w in forbidden_words):
            raise ReadinessError(f"stage row {s.get('line_id')} carries an arris length ({txt.strip()})")
    return True


def package_size(rows):
    """rule 6 -> (changed line count, added line count, ids)."""
    ch = sorted({r["host_line_id"] for r in rows if r.get("action") == CHANGE and r.get("host_line_id")})
    ad = sorted({r["new_line_key"] for r in rows if r.get("action") == ADD})
    return {"changed": len(ch), "added": len(ad), "changed_ids": ch, "added_keys": ad}
