"""T-694 rules (research only; every villa). Version 1.0.0 each. Built on R-T679-1 / R-T683-1 (not edited).

R-T694-1 PARTITION. Every line of the trade on the candidate index sits in exactly one class bucket: RELEASED, HELD
    BOUNDED (both ends), HELD BLANK (no end in the index) or EXCLUDED. A line in no bucket (unknown class, one end only,
    a HELD line carrying a released number) or in two (the same line id twice, a RELEASED line carrying a bound) is
    refused. The buckets are printed side by side and never summed together.

R-T694-2 PROPOSED OVERLAY. A merged-but-unwired ledger is shown beside the candidate as a PROPOSED column, never as the
    candidate: each move names its line, its 'before' must equal the index to the digit, a move never touches a
    RELEASED line, never releases a HELD line, never turns a bound into a blank and never widens a range (low may only
    rise, high may only fall; blank -> bounded is allowed: an OPEN end closed). Lines without a move are carried as
    they are. The overlay's totals re-add from its lines.

R-T694-3 LEADER ASSOCIATION. A member text (mark + section) that carries a leader belongs to the outline its leader's
    far end reaches (nearest outline within the arrow gap tolerance, and no second outline within that tolerance), not
    to the outline nearest the text. A text with no leader belongs to the nearest outline only when no second outline
    lies within the tolerance; otherwise the association is UNRESOLVED (never the nearest by default).

R-T694-4 CAUSE REGISTER. A HELD line's cause of kind SECTION is valid only when its two section readings differ (the
    bound uses both); a SECTION cause on a line whose readings agree is refused (a spurious cause hides the real one).
    Every cause item that names a designer register entry must list the line's member in that entry; a missing member is
    a register gap (reported, never silently accepted).
"""
from __future__ import annotations

import math
from collections import OrderedDict
from decimal import Decimal

RELEASED, HELD, EXCLUDED = "RELEASED", "HELD", "EXCLUDED"
BUCKETS = ("RELEASED", "HELD_BOUNDED", "HELD_BLANK", "EXCLUDED")


class Refused(ValueError):
    pass


def D(x) -> Decimal:
    if x is None:
        raise Refused("missing number (never 0)")
    if isinstance(x, float):
        return Decimal(repr(x))
    return Decimal(str(x))


def s6(x: Decimal) -> str:
    return f"{x.quantize(Decimal('0.000001')):f}"


# ------------------------------------------------------------------------------------------------ R-T694-1
def bucket_of(ln: dict) -> list[str]:
    """All buckets a line satisfies (exactly one is required)."""
    cls, lo, hi, net = ln.get("class"), ln.get("held_low"), ln.get("held_high"), ln.get("measured_net")
    out = []
    if cls == RELEASED and net is not None:
        out.append("RELEASED")
    if cls == RELEASED and (lo is not None or hi is not None):
        out.append("HELD_BOUNDED")  # a released line carrying a bound sits in two buckets
    if cls == HELD and net is None and lo is not None and hi is not None:
        out.append("HELD_BOUNDED")
    if cls == HELD and net is None and lo is None and hi is None:
        out.append("HELD_BLANK")
    if cls == EXCLUDED and net is None and lo is None and hi is None:
        out.append("EXCLUDED")
    return out


def partition(lines: list[dict], *, prefix: str, unit: str) -> OrderedDict:
    parts: OrderedDict = OrderedDict((b, []) for b in BUCKETS)
    seen = set()
    for ln in lines:
        if not ln.get("item_code", "").startswith(prefix):
            continue
        lid = ln.get("line_id")
        if lid in seen:
            raise Refused(f"R-T694-1: {lid} listed twice (in two buckets)")
        seen.add(lid)
        if ln.get("unit") != unit:
            raise Refused(f"R-T694-1: {lid} unit {ln.get('unit')!r} != {unit!r}")
        b = bucket_of(ln)
        if len(b) == 0:
            raise Refused(f"R-T694-1: {lid} ({ln.get('class')}, {ln.get('held_low')} .. {ln.get('held_high')}, net "
                          f"{ln.get('measured_net')}) is in no bucket")
        if len(b) > 1:
            raise Refused(f"R-T694-1: {lid} is in two buckets {b}")
        parts[b[0]].append(ln)
    return parts


def totals(parts: OrderedDict) -> OrderedDict:
    rel = sum((D(x["measured_net"]) for x in parts["RELEASED"]), Decimal(0))
    lo = sum((D(x["held_low"]) for x in parts["HELD_BOUNDED"]), Decimal(0))
    hi = sum((D(x["held_high"]) for x in parts["HELD_BOUNDED"]), Decimal(0))
    return OrderedDict(released=OrderedDict(lines=len(parts["RELEASED"]), m3=s6(rel)),
                       held_bounded=OrderedDict(lines=len(parts["HELD_BOUNDED"]), low=s6(lo), high=s6(hi)),
                       held_blank=OrderedDict(lines=len(parts["HELD_BLANK"]), high="OPEN"),
                       excluded=OrderedDict(lines=len(parts["EXCLUDED"])),
                       engine_range=[s6(rel + lo), "OPEN" if parts["HELD_BLANK"] else s6(rel + hi)])


# ------------------------------------------------------------------------------------------------ R-T694-2
def overlay(lines: list[dict], moves: list[dict]) -> tuple[list[dict], list[OrderedDict]]:
    """moves: [{line_id, before: [lo, hi] | None, after: [lo, hi], source}] -> (lines', applied rows)."""
    by = {ln["line_id"]: ln for ln in lines}
    out = {k: dict(v) for k, v in by.items()}
    rows = []
    done = set()
    for m in moves:
        lid = m["line_id"]
        if lid in done:
            raise Refused(f"R-T694-2: {lid} moved twice")
        done.add(lid)
        ln = by.get(lid)
        if ln is None:
            raise Refused(f"R-T694-2: {lid} not on the candidate index")
        if ln["class"] != HELD:
            raise Refused(f"R-T694-2: {lid} is {ln['class']}: an overlay moves HELD lines only")
        if not m.get("source"):
            raise Refused(f"R-T694-2: {lid} move names no source")
        cur = None if ln["held_low"] is None else [D(ln["held_low"]), D(ln["held_high"])]
        bef = None if m["before"] is None else [D(m["before"][0]), D(m["before"][1])]
        if cur != bef:
            raise Refused(f"R-T694-2: {lid} before {m['before']} != index {ln['held_low']} .. {ln['held_high']}")
        if m.get("after") is None:
            raise Refused(f"R-T694-2: {lid} turned into a blank / released (an overlay never does)")
        lo, hi = D(m["after"][0]), D(m["after"][1])
        if lo < 0 or lo > hi:
            raise Refused(f"R-T694-2: {lid} after {lo} .. {hi} not ordered")
        if cur is not None and (lo < cur[0] or hi > cur[1]):
            raise Refused(f"R-T694-2: {lid} widened {cur[0]} .. {cur[1]} -> {lo} .. {hi}")
        out[lid]["held_low"], out[lid]["held_high"] = float(lo), float(hi)
        rows.append(OrderedDict(line_id=lid, element_id=ln["element_id"],
                                before="blank (OPEN)" if cur is None else [s6(cur[0]), s6(cur[1])],
                                after=[s6(lo), s6(hi)], source=m["source"]))
    return [out[ln["line_id"]] for ln in lines], rows


# ------------------------------------------------------------------------------------------------ R-T694-3
def _dist(p, b):
    return math.hypot(max(b[0] - p[0], 0, p[0] - b[2]), max(b[1] - p[1], 0, p[1] - b[3]))


def nearest(at, outlines: dict[str, tuple]) -> list:
    """[handle, mm] of the outline nearest a point (reported beside an association, never used as one)."""
    d, h = min((_dist(at, b), h) for h, b in outlines.items())
    return [h, round(d)]


def associate(text: dict, outlines: dict[str, tuple], tol: float) -> OrderedDict:
    """text: {handle, at: (x, y), leader_far: (x, y) | None}; outlines: handle -> (x0, y0, x1, y1) (mm)."""
    dist = _dist
    p = text["leader_far"] if text.get("leader_far") is not None else text["at"]
    ds = sorted((dist(p, b), h) for h, b in outlines.items())
    basis = "LEADER" if text.get("leader_far") is not None else "NEAREST"
    if not ds or ds[0][0] > tol:
        return OrderedDict(text=text["handle"], outline=None, basis=basis, status="UNRESOLVED", why="none within tol")
    if len(ds) > 1 and ds[1][0] <= tol:
        return OrderedDict(text=text["handle"], outline=None, basis=basis, status="UNRESOLVED",
                           why=f"two outlines within {tol}: {ds[0][1]} / {ds[1][1]}")
    return OrderedDict(text=text["handle"], outline=ds[0][1], basis=basis, status="ASSOCIATED",
                       gap_mm=round(ds[0][0]), next_mm=round(ds[1][0]) if len(ds) > 1 else None)


# ------------------------------------------------------------------------------------------------ R-T694-4
def check_causes(rows: list[dict], register: dict[str, set]) -> tuple[list[OrderedDict], list[OrderedDict]]:
    """rows: [{line_id, member_ref, causes: [{item, kind}], readings: [a, b] | None}] -> (spurious, gaps)."""
    spurious, gaps = [], []
    for r in rows:
        for c in r["causes"]:
            if c["kind"] == "SECTION":
                rd = r.get("readings")
                if rd is not None and D(rd[0]) == D(rd[1]):
                    spurious.append(OrderedDict(line_id=r["line_id"], item=c["item"], readings=[str(x) for x in rd],
                                                why="SECTION cause on a line whose readings agree"))
                    continue
            it = c["item"]
            if it is None:
                gaps.append(OrderedDict(line_id=r["line_id"], item=None, member=r["member_ref"], kind=c["kind"],
                                        why="cause with no designer item"))
            elif it in register and r["member_ref"] not in register[it]:
                gaps.append(OrderedDict(line_id=r["line_id"], item=it, member=r["member_ref"], kind=c["kind"],
                                        why=f"member not in {it}'s registered list"))
    return spurious, gaps
