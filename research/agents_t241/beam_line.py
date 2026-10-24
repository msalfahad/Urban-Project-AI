"""BEAM_LINE_V1 (T-241, unwired, stdlib only; rollback: delete the folder).

Whole-line closure rules for CONC.BEAM (suspended beams of the roof-slab plans): every beam run once, the slab / beam
partition with the slab ledger, each intersection once. ERS s.2 (define, reconstruct, reconcile), s.3 (geometric scope
before numbers; one element, several geometries), s.4 (quantity + rule + test). Rules applied: R-CONC-OWN-1 (T-189:
each intersection volume once, precedence column > beam > slab on the route G basis), R-BEAM-CONT-1 (T-229: a beam is
cut only at a member that SUPPORTS it), R-SLAB-T-1 (T-234, proposed: slab / beam convention stated before comparing),
the T-217 lesson (four sources apart: a difference confirmed by two printed / drawn sources is a CONFLICT carried as a
range, never its larger end), the T-230 lesson (a member ends only at an element it physically meets in 3-D), the T-200
lesson (a finished level never feeds a concrete dimension), owner Q-16 / Q-61 C (unlabelled or contradicted members
HELD with a candidate, never 0, never the bigger reading).

Physical element. One beam RUN = the solid between the faces of the members that support it, at the full printed depth
D below the slab top, width b, under convention C1 (T-234: the slab panel stops at the beam faces, the beam is billed
at full depth; the band area x t is the beam's). A run is billed by exactly one line; its plan footprint shares no area
with a slab panel (C1) and no area with a column footprint that the column line bills (precedence column > beam).

Statuses (WORKFLOW_CONTROLS s.5): CALCULATED / DRAWING-CONFIRMED (one value), CONFLICT (two printed / drawn values:
low .. high, both kept), HELD (a dimension not printed: volume None or a candidate range, never 0).
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "agents_t229"))
from beam_support import area, inter_area, rect  # noqa: E402  (T-229 merged geometry helpers, convex polygons)

SCHEMA = "BEAM_LINE_V1"
CONVENTIONS = ("C1_PANEL_BETWEEN_BEAM_FACES", "C2_PLATE_OVER_BEAMS")
UNIT_TO_M = {"m": 1.0, "cm": 0.01, "mm": 0.001}
WIDTH_TOL_M = 0.005      # drawn vs schedule width: below this they agree (drafting / fit), above it a CONFLICT
TOL_M2 = 1e-4
TOL_M3 = 1e-4
STATUSES = ("CALCULATED", "DRAWING-CONFIRMED", "CONFLICT", "HELD", "VERIFIED")
MEASURED = ("CALCULATED", "DRAWING-CONFIRMED", "VERIFIED")
DATUM_KINDS = ("STRUCTURAL", "FINISHED")


class Refused(ValueError):
    """A request the rules refuse (the message names the rule)."""


def to_m(v, unit="m"):
    if v is None:
        return None
    if unit not in UNIT_TO_M:
        raise Refused("unit %r unknown" % unit)
    return float(v) * UNIT_TO_M[unit]


def run_row(run_id, storey, mark, length, b_schedule=None, b_drawn=None, depth=None, unit="m", candidates=None,
            reason=None, sources=()):
    """One beam run. length = axis length between the faces of its supports (plan, drawn edges);
    b_schedule / b_drawn the two width sources (either may be None = not printed / not drawn); depth = printed D.

    - both widths given and different by more than WIDTH_TOL_M -> CONFLICT, m3 low .. high (both kept, never collapsed);
    - no width or no depth printed -> HELD, m3 None or the candidate range given (Q-16 / Q-61 C), never 0;
    - else CALCULATED b x D x L."""
    L, bs, bd, D = to_m(length, unit), to_m(b_schedule, unit), to_m(b_drawn, unit), to_m(depth, unit)
    if L is None or L <= 0:
        raise Refused("run %s: no length between support faces" % run_id)
    row = dict(run=run_id, storey=storey, mark=mark, length_m=round(L, 4), b_schedule_m=bs, b_drawn_m=bd, depth_m=D,
               sources=list(sources), reason=reason)
    widths = [w for w in (bs, bd) if w is not None]
    if D is None or not widths:
        lo, hi = (candidates or (None, None))
        row.update(status="HELD", m3=None, m3_low=lo, m3_high=hi,
                   reason=reason or ("depth not printed" if D is None else "width not printed or drawn"))
        return row
    if len(widths) == 2 and abs(bs - bd) > WIDTH_TOL_M:
        v = sorted((bs * D * L, bd * D * L))
        row.update(status="CONFLICT", m3=None, m3_low=round(v[0], 6), m3_high=round(v[1], 6),
                   reason=reason or "schedule width %.3f vs drawn %.3f (T-217 lesson: both kept)" % (bs, bd))
        return row
    b = bd if bd is not None else bs
    m3 = b * D * L
    row.update(status="CALCULATED", m3=round(m3, 6), m3_low=round(m3, 6), m3_high=round(m3, 6))
    return row


def check_claim(row, claimed_m3, tol=TOL_M3):
    """Refuse a single figure for a CONFLICT (its larger or smaller end picked) or a HELD run released / zeroed."""
    if row["status"] == "CONFLICT":
        raise Refused("run %s is a CONFLICT %.4f .. %.4f: a single figure (%.4f) collapses the range (T-217 lesson, "
                      "Q-61 C(1): never the larger reading)" % (row["run"], row["m3_low"], row["m3_high"], claimed_m3))
    if row["status"] == "HELD":
        raise Refused("run %s is HELD (%s): never released, never 0" % (row["run"], row["reason"]))
    if claimed_m3 is None or abs(claimed_m3 - row["m3"]) > tol:
        raise Refused("run %s: claimed %r != measured %.6f" % (row["run"], claimed_m3, row["m3"]))
    return True


def check_end(run_id, member_kind, member_bottom, member_top, beam_soffit, beam_top):
    """A beam end is owned by (stops at the face of) a member only if the member physically meets the beam in 3-D:
    its vertical extent overlaps the beam's [soffit, top] (T-230 lesson). A plan outline at another level (a footing
    or neck top below the soffit, a member starting above the beam top) is refused as the end."""
    if None in (member_bottom, member_top, beam_soffit, beam_top):
        raise Refused("run %s: end at %s with a level not printed: HELD, not an end" % (run_id, member_kind))
    if member_top < beam_soffit - 1e-6 or member_bottom > beam_top + 1e-6:
        raise Refused("run %s: %s [%.3f, %.3f] does not meet the beam [%.3f, %.3f] in 3-D: a plan outline at "
                      "another level is never an end (T-230)" % (run_id, member_kind, member_bottom, member_top,
                                                                 beam_soffit, beam_top))
    return True


def depth_from_levels(run_id, top_level, top_kind, soffit_level, soffit_kind):
    """Depth from two levels only when both are STRUCTURAL datums (T-200 lesson: a finished level never feeds a
    concrete dimension)."""
    for k in (top_kind, soffit_kind):
        if k not in DATUM_KINDS:
            raise Refused("run %s: datum kind %r unknown" % (run_id, k))
        if k == "FINISHED":
            raise Refused("run %s: a finished level is never a structural top / soffit (T-200, UP-LEVEL-DATUM-001)"
                          % run_id)
    d = top_level - soffit_level
    if d <= 0:
        raise Refused("run %s: top below soffit" % run_id)
    return round(d, 6)


def line_total(rows):
    """CONC.BEAM totals per storey: measured (one value) apart from the CONFLICT range and the HELD runs (never 0)."""
    seen = set()
    out = {}
    for r in rows:
        if r["run"] in seen:
            raise Refused("run %s billed twice in the line (every run once)" % r["run"])
        seen.add(r["run"])
        s = out.setdefault(r["storey"], dict(n=0, measured_m3=0.0, conflict_low=0.0, conflict_high=0.0,
                                             conflict_n=0, held_n=0, held_low=0.0, held_high=0.0, held_no_value=[]))
        s["n"] += 1
        if r["status"] in MEASURED:
            s["measured_m3"] += r["m3"]
        elif r["status"] == "CONFLICT":
            s["conflict_n"] += 1
            s["conflict_low"] += r["m3_low"]
            s["conflict_high"] += r["m3_high"]
        elif r["status"] == "HELD":
            s["held_n"] += 1
            if r["m3_low"] is None:
                s["held_no_value"].append(r["run"])
            else:
                s["held_low"] += r["m3_low"]
                s["held_high"] += r["m3_high"]
        else:
            raise Refused("run %s: status %r unknown" % (r["run"], r["status"]))
    for s in out.values():
        for k in ("measured_m3", "conflict_low", "conflict_high", "held_low", "held_high"):
            s[k] = round(s[k], 6)
    return out


def convention(c, beam_c1_m3, band_area_by_t):
    """Beam total under convention c from the C1 total: C2 (slab plate over the beams) moves band area x t out of the
    beam line (and into the slab line); slab + beam unchanged."""
    if c not in CONVENTIONS:
        raise Refused("convention %r unknown: state C1 or C2 before comparing (R-SLAB-T-1)" % c)
    if c == CONVENTIONS[0]:
        return round(beam_c1_m3, 6)
    return round(beam_c1_m3 - sum(a * t for a, t in band_area_by_t), 6)


def partition(slab_panels, beam_pieces, column_footprints, tol=TOL_M2):
    """Plan partition of one slab sheet: each beam piece (convex polygon, id, line) against every slab panel and every
    column footprint that the COLUMN line bills. Returns the overlaps; any beam / slab overlap above tol is DOUBLE
    (the band would be in both lines under C1); a beam / column overlap is DOUBLE (precedence column > beam: the beam
    line must deduct it)."""
    double = []
    for b in beam_pieces:
        for s in slab_panels:
            a = inter_area(b["poly"], s["poly"])
            if a > tol:
                double.append(("BEAM/SLAB", b["id"], s["id"], round(a, 6)))
        for c in column_footprints:
            a = inter_area(b["poly"], c["poly"])
            if a > tol:
                double.append(("BEAM/COLUMN", b["id"], c["id"], round(a, 6)))
    return dict(status="PASS" if not double else "FAIL", double=double)


def gaps(region_area, billed_areas, tol=TOL_M2):
    """A concrete region (drawn beam face) less what the lines bill: the unbilled rest is a GAP (never closed by 0)."""
    rest = region_area - sum(billed_areas)
    if rest < -tol:
        raise Refused("region billed %.6f m2 more than drawn: DOUBLE" % -rest)
    return round(max(rest, 0.0), 6)


def reconcile(a_m3, b_m3, components, tol=1e-3):
    """a - b = sum of named components + residual; the residual is NAMED, never hidden (ERS s.2.4)."""
    diff = a_m3 - b_m3
    explained = sum(v for _n, v in components)
    resid = diff - explained
    return dict(diff=round(diff, 6), explained=round(explained, 6), residual=round(resid, 6),
                closed=abs(resid) <= tol, components=[(n, round(v, 6)) for n, v in components])


__all__ = ["SCHEMA", "Refused", "run_row", "check_claim", "check_end", "depth_from_levels", "line_total",
           "convention", "partition", "gaps", "reconcile", "rect", "area", "inter_area", "to_m"]
