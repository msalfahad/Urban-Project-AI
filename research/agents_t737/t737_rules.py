"""R-T737-1 1.0.0 (every villa): readiness census of a QUEUED exterior-face integration stage against a newer
candidate, and the re-binding of the exterior corner-bead rows onto the stage's face lines.

No quantity is measured or wired here. The rule only classifies and re-binds, from merged or pinned records.

 1. STAGE LINE CENSUS (per stage line, by line id; never by a neighbour):
      CHANGE row (an existing host id):  host absent from the target index        -> GONE (never mapped by guess)
                                          host present, same state as the stage's before-state -> LIVE
                                          host present, state / value / bound moved -> STALE (before and now quoted)
      ADD row (a new element id):         element id free in the target index      -> LIVE_NEW
                                          element id already a line in the target -> COLLISION (stale: re-key first)
    The stage before-state BLOCKED_RFI with no value / bound reads as index class HELD with no value and no bound.
 2. SOURCE CENSUS: every merged source the stage read is compared by git blob id (stage commit vs target tree):
    SAME / CHANGED / ABSENT. A CHANGED or ABSENT source makes every face it feeds STALE_SOURCE; SAME keeps them LIVE
    only when no later merged record restates one of its faces or holes (rule 3).
 3. SUPERSESSION: a later merged record that restates a face, hole or level the stage carries, with a different
    figure or state, makes that row STALE with the moved figure; a record that AGREES is cited, never silently dropped.
    A cross-ledger CONFLICT (two merged ledgers carrying one physical dimension in two states) is carried as CONFLICT
    with its decider named; it is never resolved by picking either figure (R-T730-1).
 4. BEAD RE-BINDING (after the stage): a vertical arris [bottom, top] is cut at the level breakpoints of the face
    stack that holds the most of its span on one of its two sides; each segment takes the line of the face that
    holds that height. Rings around an opening take the line of the face that holds the hole. The segments of an
    arris sum to its span exactly (arris once); a part no face holds is a NO_HOST segment (named, never a
    neighbour's line); two equally holding stacks that assign different lines make the arris AMBIGUOUS (not split).
 5. POST-STAGE HOST STATE: a stage line valued in a quantity state (MEASURED / SOURCE_DERIVED / PROVISIONAL) is
    RELEASED in the line index (T-469 line_class); a bounded line is BOUNDED; a blank line is BLANK. The bead state
    then follows R-T728-1 (research/agents_t728/t728_rules.bead_state) unchanged.
 6. NEVER 0: a HELD or blank figure is never written as 0; a split never invents a level that no face prints.
"""
from __future__ import annotations

import hashlib

RULE = "R-T737-1"
VERSION = "1.0.0"
QUANTITY_STATES = ("MEASURED", "SOURCE_DERIVED", "PROVISIONAL")   # = research/agents_t469 line_class
LIVE, LIVE_NEW, STALE, GONE, COLLISION = "LIVE", "LIVE_NEW", "STALE", "GONE", "COLLISION"
SAME, CHANGED, ABSENT = "SAME", "CHANGED", "ABSENT"
RELEASED, BOUNDED, BLANK = "RELEASED", "BOUNDED", "BLANK"
EPS = 1e-6


class CensusError(ValueError):
    pass


def r6(x):
    return None if x is None else round(float(x), 6)


def git_blob_id(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


# ---- rule 1 -------------------------------------------------------------------------------------------------------
def _index_state(ln):
    return {"class": ln.get("class"), "measured_net": r6(ln.get("measured_net")),
            "held_low": r6(ln.get("held_low")), "held_high": r6(ln.get("held_high")), "unit": ln.get("unit"),
            "item_code": ln.get("item_code"), "element_id": ln.get("element_id")}


def _before_matches(before, ln, item_code, unit):
    if ln.get("item_code") != item_code or ln.get("unit") != unit:
        return False
    st = (before or {}).get("state")
    val, lo, hi = (before or {}).get("value"), (before or {}).get("low"), (before or {}).get("high")
    if st == "BLOCKED_RFI" and val is None and lo is None and hi is None:
        return ln.get("class") == "HELD" and ln.get("measured_net") is None and ln.get("held_low") is None \
            and ln.get("held_high") is None
    if st in QUANTITY_STATES and val is not None:
        return ln.get("class") == "RELEASED" and abs((ln.get("measured_net") or 0) - val) <= EPS
    if lo is not None:
        return ln.get("class") == "HELD" and abs((ln.get("held_low") or -1) - lo) <= EPS and \
            ((hi is None and ln.get("held_high") is None) or abs((ln.get("held_high") or -1) - (hi or 0)) <= EPS)
    raise CensusError(f"before-state {before!r} cannot be compared")


def classify_stage_line(row, index_lines, *, item_code, unit):
    """row: a stage summary row (action CHANGE / ADD). index_lines: list of target line-index rows."""
    by_id = {ln["line_id"]: ln for ln in index_lines}
    by_el = {}
    for ln in index_lines:
        by_el.setdefault((ln.get("item_code"), ln.get("element_id")), []).append(ln)
    act = row.get("action")
    if act == "CHANGE":
        lid = row.get("line_id")
        if not lid:
            raise CensusError("CHANGE row without a line id")
        ln = by_id.get(lid)
        if ln is None:
            return {"census": GONE, "host_now": None, "why": f"{lid} absent from the target index: never mapped to a "
                                                              f"neighbour"}
        if ln.get("element_id") != row.get("element_id"):
            return {"census": STALE, "host_now": _index_state(ln),
                    "why": f"{lid} now carries element {ln.get('element_id')!r}, the stage {row.get('element_id')!r}"}
        if _before_matches(row.get("before"), ln, item_code, unit):
            return {"census": LIVE, "host_now": _index_state(ln), "why": "host present, same state as the stage base"}
        return {"census": STALE, "host_now": _index_state(ln),
                "why": f"host moved since the stage base: stage before {row.get('before')!r}, now {_index_state(ln)!r}"}
    if act == "ADD":
        hits = by_el.get((item_code, row.get("element_id"))) or []
        if row.get("line_id") and row["line_id"] in by_id:
            return {"census": COLLISION, "host_now": _index_state(by_id[row["line_id"]]),
                    "why": f"the stage's new line id {row['line_id']} is already taken in the target: re-key first"}
        if hits:
            return {"census": COLLISION, "host_now": _index_state(hits[0]),
                    "why": f"element id {row.get('element_id')!r} is already line {hits[0]['line_id']}: re-key first"}
        return {"census": LIVE_NEW, "host_now": None, "why": "element id free in the target index (line added at r3)"}
    raise CensusError(f"unknown stage action {act!r}")


# ---- rule 2 -------------------------------------------------------------------------------------------------------
def source_census(stage_blobs, target_blobs):
    """{path: blob} x {path: blob or None} -> {path: SAME / CHANGED / ABSENT}"""
    out = {}
    for p, b in stage_blobs.items():
        t = target_blobs.get(p)
        out[p] = ABSENT if t is None else (SAME if t == b else CHANGED)
    return out


# ---- rule 4 -------------------------------------------------------------------------------------------------------
def stacks_for_side(faces, floor, side):
    """faces: [{floor, side, portion, kind, bottom, top, line}] with levels. Returns a list of stacks (lists of
    level faces): faces of one portion form one stack; portions whose level intervals never overlap are one stack
    (a storey / parapet / over-lower-roof band set stacked on one side)."""
    groups = {}
    for f in faces:
        if f["floor"] != floor or f["side"] != side or f["bottom"] is None or f["top"] is None:
            continue
        groups.setdefault(f["portion"], []).append(f)
    stacks = []
    for g in groups.values():
        placed = False
        for s in stacks:
            if all(a["top"] <= b["bottom"] + EPS or b["top"] <= a["bottom"] + EPS for a in g for b in s):
                s.extend(g)
                placed = True
                break
        if not placed:
            stacks.append(list(g))
    for s in stacks:
        s.sort(key=lambda f: (f["bottom"], f["top"]))
    return stacks


def _segments(stack, lo, hi):
    segs = []
    for f in stack:
        a, b = max(lo, f["bottom"]), min(hi, f["top"])
        if b - a > EPS:
            segs.append((r6(a), r6(b), f["line"]))
    return segs


def _with_gaps(segs, lo, hi):
    """fill the uncovered parts of [lo, hi] with NO_HOST segments (line None); never a 0-length segment"""
    out, at = [], lo
    for a, b, line in sorted(segs):
        if a - at > EPS:
            out.append((r6(at), r6(a), None))
        out.append((a, b, line))
        at = max(at, b)
    if hi - at > EPS:
        out.append((r6(at), r6(hi), None))
    return out


def split_arris(arris, faces):
    """arris: {id, floor, sides: (A, B), bottom, top}. -> {state, segments [(lo, hi, line or None, m)], why}

    Candidate stacks: every face stack on either side that holds part of the span. The stack holding the most of the
    span is the arris's stack (the face the arris bounds); a tie between stacks that assign different lines is
    AMBIGUOUS (never split by guess). Parts no face holds are NO_HOST segments (named, never a neighbour's line)."""
    lo, hi = float(arris["bottom"]), float(arris["top"])
    if hi - lo <= EPS:
        raise CensusError(f"{arris.get('id')}: arris of no height")
    cands = []
    for s in arris["sides"]:
        for st in stacks_for_side(faces, arris["floor"], s):
            segs = _segments(st, lo, hi)
            if segs:
                cands.append((r6(sum(b - a for a, b, _ in segs)), segs))
    if not cands:
        return {"state": "NO_HOST", "segments": [(r6(lo), r6(hi), None, r6(hi - lo))],
                "why": "no face on either side holds any part of the arris"}
    best = max(c[0] for c in cands)
    top = [c[1] for c in cands if abs(c[0] - best) <= EPS]
    if any(t != top[0] for t in top[1:]):
        lines = sorted({x[2] for t in top for x in t})
        return {"state": "AMBIGUOUS", "segments": [], "why": f"equally covering stacks disagree: {lines}"}
    segs = [(a, b, l, r6(b - a)) for a, b, l in _with_gaps(top[0], lo, hi)]
    tot = sum(x[3] for x in segs)
    if abs(tot - (hi - lo)) > 1e-5:
        raise CensusError(f"{arris.get('id')}: segments {tot} != span {hi - lo}")
    hosts = {x[2] for x in segs}
    state = "PARTIAL" if None in hosts else ("SPLIT" if len(hosts) > 1 else "ONE_HOST")
    return {"state": state, "segments": segs, "why": ""}


def group_by_line(rows_segments):
    """[(line, m)] -> {line: m} rounded; never a 0 entry"""
    out = {}
    for line, m in rows_segments:
        if m is None or m <= 0:
            raise CensusError(f"segment of {m!r} m on {line}: never 0")
        out[line] = r6(out.get(line, 0.0) + m)
    return out


# ---- rule 5 -------------------------------------------------------------------------------------------------------
def post_stage_host_state(after):
    """stage row 'after' dict -> RELEASED / BOUNDED / BLANK"""
    st, val, lo, hi = after.get("state"), after.get("value"), after.get("low"), after.get("high")
    if st in QUANTITY_STATES and val is not None:
        if val <= 0:
            raise CensusError("a valued stage line of 0")
        return RELEASED
    if lo is not None:
        if hi is not None and hi < lo:
            raise CensusError("inverted stage bound")
        return BOUNDED
    if val is None and lo is None and hi is None:
        return BLANK
    raise CensusError(f"stage after-state {after!r} not classifiable")
