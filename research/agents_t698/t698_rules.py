"""R-T698-1 WIRING READINESS MAPPING (T-698, research; every villa). Maps the rows of a merged, Checker-verified ledger
to the line ids of a candidate line index, BEFORE any wiring, so a lane I package can be built in one run.

The rule (no quantity is produced, changed or wired here):

  1. A ledger row names its host: a candidate line id, a pending-package line (a stage that is not yet the candidate),
     or a crosswalk key (a wall -> its blockwork line, a flight -> its stair line) resolved by a merged crosswalk.
  2. A host line id that is ABSENT from the target index is STALE_ABSENT: named with the row, never mapped by guess.
  3. A host whose item code is not one the family may attach to is WRONG_HOST (e.g. a mesh row on a plaster line):
     refused, named.
  4. A present host is compared with its state in the REFERENCE index (the oldest committed index that carries it; the
     ledger's own base where one is committed): any change of class, measured value or held bound -> HOST_CHANGED
     (the ledger row must be restated on the new host before wiring; the change is quoted, not re-derived);
     no change -> MAPPED.
  5. A present host that a PENDING package changes (the package the wiring must follow) -> MAPPED_PENDING_CHANGE: the
     wiring waits for that package and restates on its after-state.
  6. A host that exists only in a pending stage -> MAPPED_PENDING_LINE (exists only after that package is merged).
  6b. A crosswalk key that resolves to more than one target line -> AMBIGUOUS_HOST: the row must be split by carrier
     before wiring (never assigned to one of them by guess).
  7. A row with no host by construction (an item with no candidate line and no stage line) -> NO_HOST, named.
  8. Every ledger row lands in exactly one class: rows in == sum of classes (reconciled by count, by family).
  9. HELD stays HELD and blank stays blank: a ledger row's quantity is copied as the ledger states it, never 0.
  9b. (1.1.0) A row whose ledger names HELD PARTS (e.g. held joints counted by name beside a measured length) carries
     them (`held_parts`) and the HELD marker (`held` True, `qty` None): a row of 0 m with held parts is never a plain 0.
  9c. (1.1.0) A ledger that states two unchosen bands (owner method vs drawing-derived method) maps as a HELD BAND PAIR:
     `qty` None, `lo` = owner band, `hi` = drawing band, `band_pair` True; a census never sums one band as
     determinate (it states the pair and the class split, with a class whose split is unresolved kept HELD).

Scope: every villa (no project data in this module). Provenance: T-698 (lane I, 2026-11-11), from T-692 F-T692-1
('the gap is wiring, not measuring') and the Lead row's acceptance (a test fails when a mapped host id is absent).
"""
from __future__ import annotations

from collections import Counter

RULE_ID, RULE_VERSION = "R-T698-1", "1.1.0"   # 1.1.0: rules 9b / 9c (T-698 r2, Gate A defects)
MAPPED, HOST_CHANGED, PENDING_CHANGE = "MAPPED", "HOST_CHANGED", "MAPPED_PENDING_CHANGE"
PENDING_LINE, STALE, WRONG, NO_HOST = "MAPPED_PENDING_LINE", "STALE_ABSENT", "WRONG_HOST", "NO_HOST"
AMBIGUOUS = "AMBIGUOUS_HOST"
CLASSES = (MAPPED, HOST_CHANGED, PENDING_CHANGE, PENDING_LINE, STALE, WRONG, NO_HOST, AMBIGUOUS)
READY = {MAPPED, PENDING_LINE}       # can be wired as the ledger states it (pending line: after its package)


class ReadinessError(ValueError):
    pass


def state_key(line):
    """the fields whose change means the host moved: class, measured value, held bounds (unit and item must not move)."""
    if line is None:
        return None
    return (line.get("item_code"), line.get("unit"), line.get("class"), line.get("measured_net"),
            line.get("held_low"), line.get("held_high"))


def state_text(line):
    if line is None:
        return "absent"
    c, v, lo, hi = line.get("class"), line.get("measured_net"), line.get("held_low"), line.get("held_high")
    if v is not None:
        return f"{c} {v}"
    if lo is not None or hi is not None:
        return f"{c} {lo} .. {'OPEN' if hi is None else hi}"
    return f"{c} blank"


def classify(host, *, allowed_codes, target, reference=None, pending_changed=None, pending_lines=None,
             pending_name="pending package"):
    """-> (class, host_line_id or None, reason). `target` / `reference`: {line_id: line}; `pending_changed`: {line_id:
    text of the change}; `pending_lines`: {key or id: line id of the stage line}."""
    pending_changed = pending_changed or {}
    pending_lines = pending_lines or {}
    if host is None or host == "":
        return NO_HOST, None, "the ledger row names no host line"
    if host in pending_lines:
        return PENDING_LINE, pending_lines[host], f"exists only in the {pending_name} stage"
    if not str(host).startswith("L-"):
        return NO_HOST, None, f"host {host!r} is neither a candidate line nor a {pending_name} stage line"
    ln = target.get(host)
    if ln is None:
        return STALE, None, "host line id absent from the target index"
    if ln.get("item_code") not in allowed_codes:
        return WRONG, host, f"host item {ln.get('item_code')} is not one of {sorted(allowed_codes)}"
    if host in pending_changed:
        return PENDING_CHANGE, host, f"{pending_name} changes the host: {pending_changed[host]}"
    ref = (reference or {}).get(host)
    if ref is not None and state_key(ref) != state_key(ln):
        return HOST_CHANGED, host, f"host moved since the reference index: {state_text(ref)} -> {state_text(ln)}"
    return MAPPED, host, "host present, same state as the reference index" if ref is not None else \
        "host present (not in the reference index: no earlier state to compare)"


def reconcile(rows, expected_n, family):
    """rule 8: every row in exactly one class; the count equals the ledger's row count."""
    c = Counter(r["class"] for r in rows)
    bad = set(c) - set(CLASSES)
    if bad:
        raise ReadinessError(f"{family}: unknown classes {sorted(bad)}")
    if len(rows) != expected_n or sum(c.values()) != expected_n:
        raise ReadinessError(f"{family}: {len(rows)} rows mapped, ledger has {expected_n}")
    keys = [r["row"] for r in rows]
    if len(set(keys)) != len(keys):
        raise ReadinessError(f"{family}: a ledger row is mapped twice")
    return {k: c.get(k, 0) for k in CLASSES}


def check_hosts_present(rows, target):
    """the acceptance guard: every row classed as resting on a target line must name a line present in the index."""
    for r in rows:
        if r["class"] in (MAPPED, HOST_CHANGED, PENDING_CHANGE, WRONG) and r["host_line_id"] not in target:
            raise ReadinessError(f"row {r['row']}: mapped host {r['host_line_id']} is absent from the target index")
    return True


def check_no_zero_for_held(rows):
    """rule 9: a held or blank ledger quantity is never carried as 0."""
    for r in rows:
        if r.get("ledger_state") in ("HELD", "UNKNOWN") and r.get("qty") in (0, 0.0, "0"):
            raise ReadinessError(f"row {r['row']}: held / unknown quantity carried as 0")
    return True


def check_held_parts(rows):
    """rule 9b: a row with held parts (> 0) is HELD (marker set, quantity None), never a plain number or 0."""
    for r in rows:
        hp = r.get("held_parts") or {}
        if any((v or 0) > 0 for v in hp.values()) and (not r.get("held") or r.get("qty") is not None):
            raise ReadinessError(f"row {r['row']}: {hp} held parts but the row is not HELD (qty {r.get('qty')!r})")
    return True


def check_band_pair(rows):
    """rule 9c: a band-pair row is never determinate (qty None, held marker, both bands carried)."""
    for r in rows:
        if r.get("band_pair") and (r.get("qty") is not None or not r.get("held") or r.get("lo") is None
                                   or r.get("hi") is None):
            raise ReadinessError(f"row {r['row']}: an unchosen band pair stated as determinate or without its bands")
    return True


def check_census_not_determinate(census_entry):
    """rule 9c on a census: a band-pair ledger's census entry carries status HELD BAND PAIR and no 'determinate' key
    (anywhere in it); summing one band as determinate fails."""
    def walk(o, path):
        if isinstance(o, dict):
            for k, v in o.items():
                if "determinate" in str(k):
                    raise ReadinessError(f"band-pair census states a determinate quantity at {path}/{k}")
                walk(v, f"{path}/{k}")
    if census_entry.get("status") != "HELD BAND PAIR":
        raise ReadinessError("band-pair census entry is not labelled HELD BAND PAIR")
    walk(census_entry, "")
    return True


def membership_check(members, carried, line):
    """a wall -> blockwork line crosswalk is CONFIRMED on a line only when the sum of its walls' carried m2 equals the
    line's measured value (6 dp). Returns (status, residual or None)."""
    if line is None:
        return "ABSENT", None
    v = line.get("measured_net")
    if v is None:
        return "NOT_CHECKABLE (host not valued)", None
    s = round(sum(carried[m] for m in members), 6)
    res = round(v - s, 6)
    return ("CONFIRMED" if abs(res) <= 1e-6 else "RESIDUAL"), res
