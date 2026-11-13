"""T-735 rules (project-agnostic; scope: every villa). Research only, unwired. Built on R-T732-1 (column formwork from the
member's own held dimensions, face by face), R-T714-1 (a held formwork line takes its member's bound face by face),
R-T730-1 (an undeclared conflict is carried with a named decider; a cap of 0 is refused as a cap), R-CONC-OWN-1,
UP-FW-001, R-T696-1 (directed rounding) and UP-QTY-STATUS-001; none of them edited.

R-T735-1 1.0.0  A FORMWORK LINE STATED IN TWO FORMS BY TWO MERGED PIECES GETS ONE LIVE FORM, AND EVERY EARLIER FORM IS
                SUPERSEDED BY NAME.
    A decider re-derives the line from the member's own held dimensions under the current method (R-T732-1 for a
    column, R-T735-2 for a held-depth beam face) and records, for EVERY earlier form on the line, why it is not the
    live one. Accepted supersession causes:
      UPPER_BOUND_METHOD_NOT_A_FLOOR   a 'low' computed P x (h - t) (UP-FW-001) contains the faces the framing members
                                       cover; it can sit above the true quantity (F-T732-1), so it is no floor;
      ENVELOPE_NOT_LINE_HIGH           a 'high' P_max x (h_hi - t) bounds the perimeter faces only; it leaves out the
                                       slab-edge band outside the column, so it is no line high;
      BLANK_WITH_POSITIVE_FLOOR        a BLANK 'no positive floor' where the re-derived shaft floor is > 0 for every
                                       reading of the member;
      CAP_ZERO_FROM_HELD_DEPTH         a 0 .. 0 'cap' that is the walk's held-depth convention, not a measured 0
                                       (R-T735-2);
      RESTATED_SAME_FORM               the earlier form equals the live form (kept, named).
    The live form is BOUNDED, AT_LEAST or BLANK_NAMED (never 0, never a range from 0). Refused: a decision that leaves
    an earlier form without a supersession entry; a later BLANK that would win without a declared cause (order of
    merging decides nothing); a 0 entered as a cap; a live high below its live low.

R-T735-2 1.0.0  A WALK FACE OF 0 m2 RECORDED UNDER A HELD DEPTH IS NOT A MEASURED ZERO.
    Physical element: a beam side below the slab = contact length beside a slab panel x (D - t), D the TOTAL beam depth
    (schedule depth from the slab top), t the neighbouring panel's thickness. When the walk holds the member's depth
    (D unknown to the walk) it books 0 m2 and puts the length in a held-length record. That 0 is restated:
      (a) D is settled when every candidate concrete line of the member decomposes as width x D x length with the SAME
          D (only the width differs): then side = L_held x (D - t), INDEPENDENT of the width when every contact edge
          of the held length runs ALONG the member (verified by edge direction on the drawing); an edge across the
          member would scale with the width and is refused here (SCALED, not settled by this rule);
      (b) ZERO_BY_GEOMETRY only with drawing evidence: no held length beside a slab on that face AND no other contact,
          or D <= t (no downstand);
      (c) otherwise BLANK_NAMED with the cause; never 0, never a cap of 0.
    Refused: a held length <= 0 offered as a figure, D <= t with a positive side, a depth that differs between the
    candidates, a t missing (a missing thickness is never the general note unless the panel ledger states it).
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "agents_t696"))
import bound_rounding_v1 as BR  # noqa: E402

D = BR.D
RULES = {"R-T735-1": "1.0.0", "R-T735-2": "1.0.0"}
CAUSES = ("UPPER_BOUND_METHOD_NOT_A_FLOOR", "ENVELOPE_NOT_LINE_HIGH", "BLANK_WITH_POSITIVE_FLOOR",
          "CAP_ZERO_FROM_HELD_DEPTH", "RESTATED_SAME_FORM")
LIVE = ("BOUNDED", "AT_LEAST", "BLANK_NAMED")
MAX_M = D("100")
DEPTH_TOL = D("0.005")   # ledger m3 at 4 dp and lengths to the mm: implied depth within 5 mm


class Refused(ValueError):
    pass


def decide(line_id, live, earlier):
    """R-T735-1. live = {'cls', 'low', 'high'}; earlier = [{'piece', 'form', 'cause'}, ...] (every merged form)."""
    if live["cls"] not in LIVE:
        raise Refused(f"{line_id}: live class {live['cls']!r} unknown")
    lo, hi = live.get("low"), live.get("high")
    if live["cls"] == "BOUNDED":
        if lo is None or hi is None or D(lo) <= 0 or D(hi) < D(lo):
            raise Refused(f"{line_id}: BOUNDED needs 0 < low <= high ({lo} .. {hi})")
    elif live["cls"] == "AT_LEAST":
        if lo is None or D(lo) <= 0 or hi is not None:
            raise Refused(f"{line_id}: AT_LEAST needs a positive low and no high")
    else:
        if lo is not None or hi is not None:
            raise Refused(f"{line_id}: BLANK_NAMED carries no figure")
        if not live.get("cause"):
            raise Refused(f"{line_id}: BLANK_NAMED without a named cause")
    if live.get("cap") is not None and D(live["cap"]) == 0:
        raise Refused(f"{line_id}: a cap of 0 reads as a quantity of 0 (R-T730-1): refused as a cap")
    if not earlier:
        raise Refused(f"{line_id}: no earlier form: nothing to decide")
    seen = set()
    for e in earlier:
        if e.get("cause") not in CAUSES:
            raise Refused(f"{line_id}: earlier form of {e.get('piece')} has no accepted supersession cause "
                          f"({e.get('cause')!r}): a later piece never wins by merge order")
        if e["piece"] in seen:
            raise Refused(f"{line_id}: two entries for {e['piece']}")
        seen.add(e["piece"])
        f = e["form"]
        if e["cause"] == "RESTATED_SAME_FORM" and (f.get("cls"), f.get("low"), f.get("high")) != (
                live["cls"], live.get("low"), live.get("high")):
            raise Refused(f"{line_id}: {e['piece']} called the same form but differs")
        if e["cause"] == "CAP_ZERO_FROM_HELD_DEPTH" and not (f.get("cap") is not None and D(f["cap"]) == 0):
            raise Refused(f"{line_id}: CAP_ZERO cause on a form without a 0 cap")
        if e["cause"] == "BLANK_WITH_POSITIVE_FLOOR" and (f.get("cls") != "BLANK_NAMED" or live["cls"] == "BLANK_NAMED"):
            raise Refused(f"{line_id}: BLANK_WITH_POSITIVE_FLOOR needs a blank earlier form and a live floor")
    return {"line_id": line_id, "live": live, "superseded": earlier, "rule": "R-T735-1 1.0.0"}


def held_depth_side(*, held_len, edges_along, candidates, t, cap_contacts=()):
    """R-T735-2 (a): held_len m beside slab panels; edges_along: [bool] per contact edge of that length (True = along the
    member); candidates: [(width, printed depth, length, m3), ...] of the member's concrete lines; t: neighbour panel thickness.
    Returns dict(dep, low, high, d, cls)."""
    L = D(held_len)
    if L <= 0:
        raise Refused("held length <= 0: R-T735-2 (b) applies (zero only with drawing evidence), not a figure")
    if L > MAX_M:
        raise Refused(f"held length {L} m: unit error")
    if t is None:
        raise Refused("neighbour panel thickness missing: HELD, never a default")
    tt = D(t)
    depths = set()
    for w, d, ln, m3 in candidates:
        wd, dd, lnd = D(w), D(d), D(ln)
        implied = D(m3) / (wd * lnd)
        if abs(implied - dd) > DEPTH_TOL:
            raise Refused(f"candidate {m3} m3 / ({w} x {ln}) = depth {implied:.4f}, not {d}: does not decompose")
        depths.add(dd)
    if len(depths) != 1:
        raise Refused(f"depth differs between candidates {sorted(depths)}: not settled (BLANK_NAMED)")
    dd = depths.pop()
    if dd <= tt:
        raise Refused(f"D {dd} <= t {tt}: no downstand; ZERO_BY_GEOMETRY needs the drawing evidence, not this rule")
    if not edges_along or not all(edges_along):
        raise Refused("a contact edge runs across the member: the side scales with the width (SCALED), not settled")
    side = BR.mul(L, dd - tt)
    lo, hi = BR.bound(side, side)
    return {"dep": "INDEPENDENT", "cls": "BOUNDED", "low": lo, "high": hi, "d": dd, "t": tt, "exact": side,
            "named_beside": list(cap_contacts)}
