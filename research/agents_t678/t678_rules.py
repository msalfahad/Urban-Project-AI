"""T-678 rules (project-agnostic; scope: every villa with a printed RC lintel schedule, drawn / printed opening heads and
a slab plan whose beams carry printed depths). Research only, unwired. Built on R-T673-1 / -3 (t673_rules), not edited.

R-T678-1 1.0.0  LINTEL EXISTENCE FROM A BOUNDED SOFFIT (the fill state is not the physical question).
    Provenance: R-T453-4 / R-T673-1 (a lintel is REQUIRED where masonry is built above the head: head + D + bed under
    the soffit), ERS s.2.1 (physical element first). New here, two points:
    (a) The test needs a LOWER BOUND of the clear height over the opening, not a measured wall area. A host wall whose
        net area is HELD (another opening's width not drawn, a datum open) still decides existence when the lower
        bound of every soffit over the opening leaves room:  spare = c_lo - (head + tol) - (D + bed) >= 0 -> REQUIRED;
        c_hi - (head - tol) < D -> FLAGGED (the member serves the opening); otherwise HELD_BY_NAME with the threshold
        that would decide it.
    (b) The soffits are those of the pieces OVER THE OPENING'S OWN EXTENT (position-resolved along the run) when the
        run pieces carry positions; otherwise min over every piece of the host wall (R-T673-1, safe side).
    Head sources: PRINTED, DRAWING-CONFIRMED (with its read tolerance) or ASSUMED - OWNER-APPROVED (the owner door-height
    fallback Q-55 C, tolerance 0, label carried into the result); a head with no source -> HELD, never 0.
    Refused: c / head not in metres, a soffit bound from a member whose depth is not printed (unsized / unlabelled),
    a missing FFL for the opening's floor.

R-T678-2 1.0.0  SLAB-TOP LOWER BOUND FROM A DRAWN HEAD UNDER A PRINTED BEAM (extends R-T669-2: printed opening top +
    printed slab thickness). Where a slab top level is not printed (finished mark only), and an opening's head is drawn
    (DRAWING-CONFIRMED, tolerance tol) directly under a beam of printed depth D_b on ONE slab plane (one outline, no
    step, no level or thickness printed inside it):  s_lo = max over such openings (head - tol) + D_b.
    The bound holds for every member under that plane: a beam of printed depth d over another wall has its soffit
    >= s_lo - d; a slab-only piece has its soffit >= s_lo - D_max, D_max = the deepest printed down-stand beam drawn on
    the plane (a drawn down-stand beam is deeper than the slab it hangs from). Refused: two planes, an unprinted D_b,
    a head that is not drawn, s_lo above the printed finished ceiling (drawing contradiction, FLAGGED).

R-T678-3 1.0.0  A LINTEL END WITH NO RECORDED STOPPER (crossing wall, unrecorded neighbour) is OPEN: the lower bound
    counts only the bounded ends' b_min (MIN-BEARING lower bound, R-T524-1), the upper bound is OPEN; never a ceiling
    invented for that end and never 0.
"""
from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "agents_t673"))
import t673_rules as R73  # noqa: E402

D = R73.D
q6 = R73.q6
Refused = R73.Refused
B_MIN = R73.B_MIN
REQUIRED, FLAGGED, HELD_BY_NAME, HELD = R73.REQUIRED, R73.FLAGGED, R73.HELD_BY_NAME, R73.HELD
HEAD_SOURCES = ("PRINTED", "DRAWING-CONFIRMED", "VERIFIED", "ASSUMED - OWNER-APPROVED")


# ---------------------------------------------------------------------------------------------------- R-T678-2
def slab_top_lower_bound(*, heads, one_plane, finished_ceiling=None):
    """heads: [{id, head_abs, tol, status, beam_depth}] each drawn directly under a beam of printed depth."""
    if not one_plane:
        raise Refused("R-T678-2: the slab is not one plane (step / level / thickness inside): no transfer")
    if not heads:
        raise Refused("R-T678-2: no drawn head under a printed beam")
    best = None
    for h in heads:
        if h.get("status") not in ("DRAWING-CONFIRMED", "PRINTED", "VERIFIED"):
            raise Refused(f"{h.get('id')}: head status {h.get('status')!r} cannot bound a slab")
        if h.get("beam_depth") is None:
            raise Refused(f"{h.get('id')}: the beam over the head has no printed depth")
        hd, t, db = D(h["head_abs"], "head"), D(h.get("tol") or 0, "tol"), D(h["beam_depth"], "beam depth")
        if t > Decimal("0.10") or not (Decimal("0.10") <= db <= Decimal("2.0")):
            raise Refused(f"{h['id']}: tol / beam depth not in metres")
        v = hd - t + db
        if best is None or v > best[0]:
            best = (v, h["id"])
    if finished_ceiling is not None and best[0] > D(finished_ceiling, "ceiling"):
        return {"state": FLAGGED, "s_lo": q6(best[0]), "governing": best[1],
                "why": "lower bound above the printed finished mark: drawing contradiction"}
    return {"state": "BOUNDED", "s_lo": q6(best[0]), "governing": best[1]}


def soffit_lower_bound(s_lo, member_depth=None, slab_only=False, d_max=None):
    if slab_only:
        if d_max is None:
            raise Refused("slab-only piece needs the deepest printed down-stand beam of the plane")
        return q6(D(s_lo) - D(d_max))
    if member_depth is None:
        raise Refused("a member with no printed depth cannot give a soffit bound")
    return q6(D(s_lo) - D(member_depth))


# ---------------------------------------------------------------------------------------------------- R-T678-1
def existence_bounded(*, head, tol, head_status, c_lo, c_hi, d, bed):
    if head is None:
        return HELD, None, "head not established: existence HELD, never 0"
    if head_status not in HEAD_SOURCES:
        raise Refused(f"head status {head_status!r} cannot decide existence")
    h, t = D(head, "head"), D(tol or 0, "tol")
    if t > Decimal("0.10"):
        raise Refused("tolerance not a drawn-read tolerance (mm passed as m?)")
    if head_status in ("PRINTED", "ASSUMED - OWNER-APPROVED"):
        t = Decimal(0)
    if c_lo is None:
        return HELD, None, "no lower bound of the soffit over the opening"
    lo = D(c_lo, "clear lo")
    hi = None if c_hi is None else D(c_hi, "clear hi")
    if lo <= 0 or lo > 10 or (hi is not None and (hi < lo or hi > 10)):
        raise Refused("clear height not in metres")
    dd, bb = D(d, "D"), D(bed, "bed")
    spare = lo - (h + t) - (dd + bb)
    label = " (head ASSUMED - OWNER-APPROVED)" if head_status == "ASSUMED - OWNER-APPROVED" else ""
    if spare >= 0:
        return REQUIRED, q6(spare), "masonry above the head under the lowest soffit bound" + label
    if hi is not None and hi - (h - t) < dd:
        return FLAGGED, q6(spare), "no soffit leaves room for the band depth: the member serves the opening"
    need = q6((h + t) + dd + bb - lo)
    return HELD_BY_NAME, q6(spare), f"decided only if the soffit rises {need} m above its lower bound" + label


def pieces_over(pieces, x0, x1, eps=Decimal("0.0005")):
    """pieces: [(from_m, to_m, kind, depth)] along the run; returns those overlapping [x0, x1] (kind BEAM / SLAB /
    COLUMN / FACE); a HELD (unsized) beam over the extent is returned too, so the caller refuses it."""
    a, b = D(x0, "x0"), D(x1, "x1")
    if b <= a:
        raise Refused("opening extent empty")
    out = []
    for f, t, kind, dep in pieces:
        f, t = D(f, "from"), D(t, "to")
        if t - f <= eps:
            continue
        if min(t, b) - max(f, a) > eps and kind not in ("COLUMN", "FACE"):
            out.append((f, t, kind, dep))
    return out


# ---------------------------------------------------------------------------------------------------- R-T678-3
def lintel_m3_open_end(lintel):
    """one end with no recorded stopper: lo = B D (w + bounded ends' b_min), hi OPEN."""
    w, B, Dd = D(lintel["width_m"], "width"), D(lintel["B"], "B"), D(lintel["D"], "D")
    if w <= 0 or w > 10:
        raise Refused("width not in metres")
    bounded = 0
    for e in lintel["ends"]:
        if e.get("stopper") in ("COLUMN", "END_OF_MASONRY", "END", "SEARCH_LIMIT"):
            st, _ = R73.bearing_state(e["a"])
            if st == R73.BOUNDED:
                bounded += 1
    lo = q6(B * Dd * (w + bounded * B_MIN))
    if lo <= 0:
        raise Refused("lo <= 0")
    return {"id": lintel["id"], "convention": "MIN_BEARING (one end OPEN)", "state": "HELD_BY_NAME", "lo_m3": lo,
            "hi_m3": None}


def column_m3(section_lo, section_hi, base, top_lo, top_hi, joint_depth=Decimal(0)):
    """a column from its base to top (top = slab top, or the soffit of a member billed through it: joint_depth)."""
    a0, a1 = D(section_lo, "area"), D(section_hi, "area")
    b, t0, t1, j = D(base, "base"), D(top_lo, "top lo"), D(top_hi, "top hi"), D(joint_depth, "joint")
    if a0 > a1 or a0 <= 0 or a1 > 2:
        raise Refused("section area not in m2")
    h0, h1 = t0 - j - b, t1 - j - b
    if h0 <= 0 or h1 < h0 or h1 > 10:
        raise Refused(f"height {h0} .. {h1} not a storey in metres")
    return {"h_lo": q6(h0), "h_hi": q6(h1), "lo_m3": q6(a0 * h0), "hi_m3": q6(a1 * h1)}
