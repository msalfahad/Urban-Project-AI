"""T-233: whole-line closure of an isolated-footing concrete line and its blinding line (research piece, not wired).

Pure functions, no I/O, any villa. Inputs are VALUES only: a footing schedule (type -> L, W, H in metres, printed) and
the drawn footing outlines of one foundation plan (each outline once, with the type tags printed in or at it, its drawn
plan size and area in metres). Nothing here reads a drawing; the Alsenan runner `t233_alsenan_check.py` builds the
inputs from the DXF and states every source.

Physical elements (ERS s.2.1):
- FOOTING: the reinforced-concrete solid of one drawn outline: plan = the drawn outline (two sources: the schedule row
  L x W and the drawn outline, either orientation), depth H from the schedule (one printed source; the typical details
  print 'D' / 'AS PER SCHEDULE'). A drawn outline clipped where it meets a neighbour (a notch exactly where another
  footing's outline lies) is the designer's own one-owner drawing of that intersection (R-CONC-OWN-1): the clipped
  area x H is used and the clip is reported; the neighbour keeps the piece at its own depth.
- BLINDING: the plain-concrete layer under each footing: plan = the footing outline grown by the printed projection
  on every side, thickness printed; where two footings' blinding overlaps in plan it is ONE layer (union). The
  underlay between blinding and footing (screed, membrane) is another trade: refused in either concrete line.

Statuses: AGREE (drawn = schedule), CLIPPED (drawn = schedule less a neighbour's piece), CONFLICT (two printed
sources disagree: both volumes carried as a range, never one end picked), HELD (no type, two types on one outline,
a type with no schedule row, no printed projection / thickness). HELD is never 0 and never inside a measured total.
"""

from __future__ import annotations

from dataclasses import dataclass, field

TOL_M = 0.005          # drawn vs printed size tolerance (5 mm)
TOL_M2 = 1e-4

UNDERLAY_CLASSES = {"SCREED", "MEMBRANE", "WATERPROOFING", "PROTECTION_BOARD", "INSULATION"}


class RefusedError(ValueError):
    """An input that would put a wrong or invented quantity into the line."""


@dataclass(frozen=True)
class ScheduleRow:
    type: str
    L: float
    W: float
    H: float


@dataclass(frozen=True)
class Outline:
    id: str                     # drawing entity id (handle) or fixture id
    tags: tuple                 # footing type tags printed in / at the outline (each tag bound to ONE outline)
    a: float                    # drawn plan extent 1 (m)
    b: float                    # drawn plan extent 2 (m)
    area: float                 # drawn plan area (m2); < a*b when clipped
    clipped_by: tuple = ()      # outline ids whose drawn outline occupies the missing piece (one-owner clip)
    blind_m2: float | None = None            # blinding plan of this outline alone (outline grown by the projection)
    blind_outside_m2: float = 0.0            # part of blind_m2 beyond a boundary the layer cannot cross (plot line)
    element_class: str = "FOOTING"


@dataclass
class FootingRow:
    outline: str
    type: str | None
    status: str
    m3: float | None
    m3_range: tuple | None
    basis: str
    plan_m2: float | None = None
    H: float | None = None


@dataclass
class LineResult:
    rows: list
    measured_m3: float
    held: list = field(default_factory=list)          # (id, reason, range or None)
    by_type: dict = field(default_factory=dict)       # type -> (count, m3)

    @property
    def closable(self) -> bool:
        return not self.held


def _same_size(a, b, L, W, tol=TOL_M):
    return (abs(a - L) <= tol and abs(b - W) <= tol) or (abs(a - W) <= tol and abs(b - L) <= tol)


def bind_population(outlines):
    """Each outline once, each printed tag to one outline only. Refuses a tag (an outline id + type) listed twice and
    an outline id listed twice (a footing counted under two types or twice)."""
    seen = set()
    for o in outlines:
        if o.id in seen:
            raise RefusedError(f"outline {o.id} listed twice: one physical footing, one row")
        seen.add(o.id)
        if o.element_class != "FOOTING":
            raise RefusedError(f"{o.id}: {o.element_class} is not footing concrete")
        if max(o.a, o.b) > 30.0 or o.area > 900.0:
            raise RefusedError(f"{o.id}: plan {o.a} x {o.b} is not in metres (mm or cm input?)")
    return outlines


def footing_row(o: Outline, schedule: dict) -> FootingRow:
    if o.element_class in UNDERLAY_CLASSES:
        raise RefusedError(f"{o.id}: underlay ({o.element_class}) is another trade, never concrete")
    tags = tuple(dict.fromkeys(o.tags))
    if not tags:
        return FootingRow(o.id, None, "HELD", None, None, "no type printed at the outline")
    if len(tags) > 1:
        # one drawn outline carrying two types: a combined footing with no own schedule row. Readings shown, not chosen.
        sch = [schedule.get(t) for t in tags]
        if any(s is None for s in sch):
            return FootingRow(o.id, "+".join(tags), "HELD", None, None, "a type without a schedule row")
        # reading A: each schedule row as printed, separately; reading B: the drawn outline cast as one footing at
        # the deepest tagged depth (a shallower one-depth outline would leave the deeper type's printed depth unbuilt
        # under its own column, contradicting that type's schedule row, so it is not a reading)
        sep = sum(s.L * s.W * s.H for s in sch)
        drawn = o.area * max(s.H for s in sch)
        lo, hi = min(sep, drawn), max(sep, drawn)
        return FootingRow(o.id, "+".join(tags), "HELD", None, (round(lo, 6), round(hi, 6)),
                          "one outline, two types: (A) schedule rows separately %.4f; (B) drawn outline %.3f m2 x "
                          "H %.2f = %.4f" % (sep, o.area, max(s.H for s in sch), drawn), o.area, None)
    t = tags[0]
    s = schedule.get(t)
    if s is None:
        return FootingRow(o.id, t, "HELD", None, None, "type has no schedule row")
    if not _same_size(o.a, o.b, s.L, s.W):
        v_s, v_d = s.L * s.W * s.H, o.area * s.H
        return FootingRow(o.id, t, "CONFLICT", None, (round(min(v_s, v_d), 6), round(max(v_s, v_d), 6)),
                          "drawn %.3f x %.3f vs schedule %.2f x %.2f" % (o.a, o.b, s.L, s.W), o.area, s.H)
    full = s.L * s.W
    if o.area < full - TOL_M2:
        if not o.clipped_by:
            return FootingRow(o.id, t, "CONFLICT", None, (round(o.area * s.H, 6), round(full * s.H, 6)),
                              "outline smaller than its schedule row with no neighbour in the missing piece",
                              o.area, s.H)
        return FootingRow(o.id, t, "CLIPPED", round(o.area * s.H, 6), None,
                          "drawn area %.4f m2 (schedule %.2f x %.2f less the piece owned by %s) x H %.2f"
                          % (o.area, s.L, s.W, "/".join(o.clipped_by), s.H), o.area, s.H)
    return FootingRow(o.id, t, "AGREE", round(full * s.H, 6), None,
                      "L x W x H = %.2f x %.2f x %.2f (drawn outline agrees)" % (s.L, s.W, s.H), full, s.H)


def footing_line(outlines, schedule) -> LineResult:
    bind_population(outlines)
    rows = [footing_row(o, schedule) for o in outlines]
    measured = sum(r.m3 for r in rows if r.m3 is not None)
    held = [(r.outline, r.basis, r.m3_range) for r in rows if r.m3 is None]
    by_type = {}
    for r in rows:
        if r.m3 is not None:
            c, v = by_type.get(r.type, (0, 0.0))
            by_type[r.type] = (c + 1, round(v + r.m3, 6))
    return LineResult(rows, round(measured, 6), held, by_type)


def blinding_line(outlines, footing_result: LineResult, *, projection_m, thickness_m, union_m2_measured=None,
                  hold_outside=True, schedule=None) -> LineResult:
    """Blinding under the footings. projection / thickness must be PRINTED values (None = not printed -> HELD).
    A footing that is HELD or CONFLICT keeps its blinding HELD (it follows its footing). Overlap between the blinding
    of neighbouring footings is one layer: the caller passes the union area of the measured outlines' blinding
    (geometry), which must not exceed their sum. The part beyond a boundary the layer cannot cross (plot line) is HELD
    when hold_outside (a designer item), never silently kept or dropped."""
    if projection_m is None or thickness_m is None:
        return LineResult([], 0.0, [("BLINDING", "projection or thickness not printed", None)])
    status = {r.outline: r for r in footing_result.rows}
    rows, held = [], []
    s_meas = 0.0
    out_meas = 0.0
    for o in outlines:
        if o.blind_m2 is None:
            raise RefusedError(f"{o.id}: blinding plan not given")
        fr = status[o.id]
        expect = None
        if fr.status in ("AGREE",):
            expect = (o.a + 2 * projection_m) * (o.b + 2 * projection_m)
        if expect is not None and o.blind_m2 < expect - 1e-3:
            raise RefusedError(f"{o.id}: blinding {o.blind_m2:.4f} m2 smaller than the outline grown by the printed "
                               f"projection {expect:.4f} m2 (footing plan with no projection?)")
        if fr.m3 is None:
            lo = (o.blind_m2 - (o.blind_outside_m2 if hold_outside else 0)) * thickness_m
            hi = o.blind_m2 * thickness_m
            tags = tuple(dict.fromkeys(o.tags))
            if schedule and len(tags) > 1 and all(t in schedule for t in tags):
                sep = sum((schedule[t].L + 2 * projection_m) * (schedule[t].W + 2 * projection_m) for t in tags)
                hi = max(hi, sep * thickness_m)       # reading A: each row's own blinding, separately
            held.append((o.id, "follows its footing (%s)" % fr.status, (round(lo, 6), round(hi, 6))))
            rows.append(FootingRow(o.id, fr.type, "HELD", None, None, "footing " + fr.status))
            continue
        s_meas += o.blind_m2
        out_meas += o.blind_outside_m2
        rows.append(FootingRow(o.id, fr.type, fr.status, round(o.blind_m2 * thickness_m, 6), None,
                               "(outline + %.2f each side) x %.2f" % (projection_m, thickness_m), o.blind_m2,
                               thickness_m))
    union = s_meas if union_m2_measured is None else union_m2_measured
    if union > s_meas + 1e-6:
        raise RefusedError("union of the blinding plans exceeds their sum")
    overlap = s_meas - union
    net_m2 = union - (out_meas if hold_outside else 0.0)
    if hold_outside and out_meas > 0:
        held.append(("BLINDING-OUTSIDE-BOUNDARY", "projection beyond the plot line (designer item)",
                     (0.0, round(out_meas * thickness_m, 6))))
    res = LineResult(rows, round(net_m2 * thickness_m, 6), held)
    res.by_type = {"plan_sum_m2": round(s_meas, 6), "overlap_once_m2": round(overlap, 6),
                   "outside_m2": round(out_meas, 6), "net_m2": round(net_m2, 6)}
    return res


def keyed_line(components):
    """A BOQ reference line = several physical components (e.g. footings + straps + foundation band). Returns the
    measured sum, the held components and the closable verdict. A component given as None or with a held list is
    HELD, never 0; it is never added to the measured total."""
    measured, held = 0.0, []
    for name, comp in components.items():
        if comp is None:
            held.append((name, "not measured", None))
            continue
        m, h = comp
        measured += m
        held.extend((name + ":" + str(x[0]), x[1], x[2]) for x in h)
    verdict = "CLOSABLE NOW" if not held else "NOT CLOSABLE: " + "; ".join(sorted({x[0].split(':')[0] for x in held}))
    return round(measured, 6), held, verdict
