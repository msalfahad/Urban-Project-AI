"""T-689 rules (project-agnostic; scope: every villa whose column / beam concrete lines are HELD as bounded ranges).
Research only, unwired. Built on R-T678-2 (t678_rules, slab-top lower bound from a drawn head under a printed beam on
one plane) and R-T669-2 (printed opening top + printed slab thickness); neither file is edited.

R-T689-1 1.0.0  JOINT TRANSFER OF A SLAB-TOP LOWER BOUND TO THE SUPPORTING COLUMNS (no plane premise).
    Provenance: UP-CONC-JOINT-001 (a column runs to the slab top; the beam-column joint is one node), R-T678-2 (the
    beam bound s >= head - tol + D_b), ERS s.2.1 / s.2.3 (physical element, first principles).
    A drawn (DRAWING-CONFIRMED, tolerance tol) or printed opening head directly under a DOWN-STAND beam of printed
    total depth D_b, inside the beam's clear span between its two supporting column faces, bounds that beam's top:
        top_b >= head - tol + D_b.
    The beam's top at each support is the top of the supporting column (the column runs to the slab top at the
    joint), so for each SUPPORT column of that span:  h_col_lo = top_b_lo - base, without any one-plane premise.
    A column that does not support that span receives the bound only through R-T678-2 (one plane: one outline, no
    step, no level or thickness printed inside it); when R-T678-2 refuses, the column keeps its previous lower bound
    and the refusal is named. Refused: an ASSUMED head (owner door fallback), a beam with no printed depth or a depth
    conflict, a beam whose up / down-stand is an open designer item, an opening outside the span, s_lo above the
    printed finished mark (drawing contradiction -> FLAGGED).

R-T689-2 1.0.0  A HELD RANGE MOVES ONLY TOWARDS A DRAWN DATUM (narrowing discipline for every held m3 line).
    after.low >= before.low and after.high <= before.high (never widened by a narrowing task); a bound end moves only
    with a named drawn / printed source; a midpoint, the freelancer's figure, a typical detail, a scaled section on a
    sheet marked not to scale, or 'the larger / more conservative end' is refused as a source; a line whose datum is
    missing stays HELD with its designer item named (D-nn), never 0, never closed to one end. A range closes
    (DRAWING-CONFIRMED) only when low == high from such a source.

R-T689-3 1.0.0  EVERY HELD LINE IN THE TOP SHARE OF THE WIDTH NAMES ITS DESIGNER ITEM PER CAUSE.
    A held bounded line can carry two independent causes (section CONFLICT and height datum); each cause needs its own
    register item. A cause with no register number is a finding (a register gap), never silently folded into the
    other item.
"""
from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agents_t678"))
import t678_rules as R78  # noqa: E402

D = R78.D
q6 = R78.q6
Refused = R78.Refused

HEAD_OK = ("PRINTED", "DRAWING-CONFIRMED", "VERIFIED")
BAD_SOURCES = ("MIDPOINT", "FREELANCER", "TYPICAL_DETAIL", "SCALED_NTS", "LARGER_END", "CONSERVATIVE")


# ---------------------------------------------------------------------------------------------------- R-T689-1
def beam_top_lower_bound(*, beam, heads, finished_mark=None):
    """beam: {id, depth (printed, m), stand: 'DOWN' | 'UP' | 'OPEN', span: (a, b) clear span positions m}.
    heads: [{id, head_abs, tol, status, at: (a, b) jamb positions along the same axis}]."""
    if beam.get("depth") is None:
        raise Refused(f"{beam.get('id')}: beam depth not printed: no transfer")
    if beam.get("stand") != "DOWN":
        raise Refused(f"{beam.get('id')}: up / down-stand {beam.get('stand')!r} not settled (designer item): no transfer")
    sa, sb = (D(v, "span") for v in beam["span"])
    usable = []
    for h in heads:
        if h.get("status") not in HEAD_OK:
            raise Refused(f"{h.get('id')}: head status {h.get('status')!r} cannot bound a beam top")
        ja, jb = (D(v, "jamb") for v in h["at"])
        if ja < sa or jb > sb:
            raise Refused(f"{h['id']}: opening {ja} .. {jb} not inside the clear span {sa} .. {sb}")
        usable.append({"id": h["id"], "head_abs": h["head_abs"], "tol": h.get("tol") or 0, "status": h["status"],
                       "beam_depth": beam["depth"]})
    res = R78.slab_top_lower_bound(heads=usable, one_plane=True, finished_ceiling=finished_mark)
    res["beam"] = beam["id"]
    return res


def support_column_height_lo(*, top_lo, base, supports, column):
    """R-T689-1: a column that supports the bounded span takes h_lo = top_lo - base; any other column is refused."""
    if column not in supports:
        raise Refused(f"{column}: not a support of the bounded span: joint transfer refused (R-T678-2 plane only)")
    h = D(top_lo, "top") - D(base, "base")
    if h <= 0:
        raise Refused("non-positive column height")
    return q6(h)


def plate_transfer(*, top_lo, base, one_plane, why_not=None):
    """R-T678-2 plate transfer to a non-support column: only on one plane; else the refusal is returned by name."""
    if not one_plane:
        return {"state": "REFUSED", "why": why_not or "not one plane (R-T678-2)"}
    return {"state": "BOUNDED", "h_lo": q6(D(top_lo) - D(base))}


# ---------------------------------------------------------------------------------------------------- R-T689-2
def narrow(*, before, after, source):
    """before / after: (low, high) Decimal-able or None for an open end; source: {kind, ref}. Returns the after bound
    with its status; refuses widening, an unnamed source, a refused source kind, or a 0 / missing replacing a bound."""
    if not source or not source.get("ref"):
        raise Refused("R-T689-2: a bound end moves only with a named drawn / printed source")
    if source.get("kind") in BAD_SOURCES:
        raise Refused(f"R-T689-2: source kind {source.get('kind')} is not a drawing datum")
    bl, bh = before
    al, ah = after
    if al is None or ah is None:
        if (bl is not None and al is None) or (bh is not None and ah is None):
            raise Refused("R-T689-2: a known bound end cannot be dropped (missing never replaces a value)")
    if al is not None and D(al, "low") <= 0:
        raise Refused("R-T689-2: a held member is never 0")
    if bl is not None and al is not None and D(al) < D(bl):
        raise Refused("R-T689-2: low end moved down (widening)")
    if bh is not None and ah is not None and D(ah) > D(bh):
        raise Refused("R-T689-2: high end moved up (widening)")
    if al is not None and ah is not None and D(al) > D(ah):
        raise Refused("R-T689-2: low above high")
    state = "CLOSED" if (al is not None and ah is not None and D(al) == D(ah)) else "HELD"
    return {"state": state, "low": None if al is None else q6(D(al)), "high": None if ah is None else q6(D(ah)),
            "source": source}


def keep(before, item):
    """A line whose datum is missing stays HELD with its item named; never 0, never one end."""
    if not item:
        raise Refused("R-T689-2: a held line keeps a named designer item")
    lo, hi = before
    if lo is not None and D(lo) == 0 and hi is not None and D(hi) == 0:
        raise Refused("a held member is never 0")
    return {"state": "HELD", "low": None if lo is None else q6(D(lo)), "high": None if hi is None else q6(D(hi)),
            "item": item}


def conflict_bound(*, areas, height, item):
    """A blank column line whose section is a CONFLICT pair (both readings known) and whose height is bounded gets
    a_min x h_lo .. a_max x h_hi (R-COL-SECTION-CONFLICT-1, as the bounded conflict lines); one reading is never
    chosen. A missing height end or a missing reading keeps the line blank, HELD by name, never 0."""
    if len(areas) != 2 or any(a is None for a in areas):
        return keep((None, None), item or "section reading missing")
    if height is None or height[0] is None or height[1] is None:
        return keep((None, None), item or "height datum missing")
    a1, a2 = sorted(D(a, "area") for a in areas)
    hl, hh = D(height[0], "h_lo"), D(height[1], "h_hi")
    if a1 <= 0 or hl <= 0 or hl > hh:
        raise Refused("conflict bound: non-positive area / height or h_lo above h_hi")
    return {"state": "HELD", "low": q6(a1 * hl), "high": q6(a2 * hh), "item": item}


# ---------------------------------------------------------------------------------------------------- R-T689-3
def register_gaps(lines, register):
    """lines: [{line_id, causes: [{kind, item}]}]; register: set of D-nn present in the designer register.
    Returns the (line_id, cause kind) pairs whose item is missing or not in the register."""
    gaps = []
    for ln in lines:
        if not ln.get("causes"):
            gaps.append((ln["line_id"], "NO_CAUSE"))
        for c in ln.get("causes", []):
            if not c.get("item") or c["item"] not in register:
                gaps.append((ln["line_id"], c["kind"]))
    return gaps


def width_share(lines, share=Decimal("0.80")):
    """Rank held bounded lines by width (m3) and return the smallest prefix whose width reaches `share` of the total."""
    ws = sorted(((D(l["high"]) - D(l["low"]), l["line_id"]) for l in lines), key=lambda r: (-r[0], r[1]))
    tot = sum((w for w, _ in ws), Decimal(0))
    if tot <= 0:
        return [], Decimal(0)
    cum, out = Decimal(0), []
    for w, lid in ws:
        out.append(lid)
        cum += w
        if cum >= share * tot:
            break
    return out, q6(tot)
