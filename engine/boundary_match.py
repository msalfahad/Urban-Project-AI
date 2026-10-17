"""E91 — the central mechanism: raster finds the room, vector measures it.

A topology region's traced outline is a SEARCH GUIDE and nothing more. For
each run of that outline this module looks LOCALLY for real source geometry
that could be the finish face there, chooses one, and records why. The final
polygon is then built from the chosen vector objects.

The distinction that makes the round work:

    RASTER IDENTIFIES TOPOLOGY.   VECTOR RECONSTRUCTS MEASUREMENT.

So the raster polygon is never scaled, warped, offset or smoothed into
place. Where no vector object can be found for a run, that run stays
UNRESOLVED and the candidate is PARTIAL — it does not fall back to the pixel
coordinate, because a pixel coordinate in a released polygon is exactly what
§3 forbids.

Selection is LOCAL and PRIORITY-LED, never global-nearest. Choosing the
nearest line globally is a failure this project has already had: the nearest
line to a room's north wall can be the south face of the wall above it, or a
dimension line, and picking it produces a polygon that looks plausible and
measures the wrong thing. So a candidate must be on the run's own axis,
within a stated window, and overlap the run — and among those, the
established wall face beats the diagnostic one even if the diagnostic one is
nearer.

Every interval carries its whole decision (§10): candidates seen, the one
chosen, distance, orientation difference, support length, and every
alternative with the reason it lost. There is no black-box "snapped
successfully".
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from engine.space_objects import (
    BoundaryInterval, MeasuredSpaceCandidate, SOURCE_PRIORITY,
    SRC_DIAGNOSTIC_VECTOR, SRC_RASTER_ONLY, SRC_RECOVERED_FRAGMENT,
    SRC_UNRESOLVED, SRC_VECTOR_EXTERNAL_BOUNDARY, SRC_VECTOR_OPENING_JAMB,
    SRC_VECTOR_WALL_FACE)

# How far from the traced run a candidate face may sit. The traced boundary
# follows the INK edge, so it should already be within a pixel or two of the
# drawn finish face: the pixel pitch here is 10.8 mm, and the ink edge plus
# the tracer's half-pixel quantisation put the guide within ~3 px. The window
# is set from that, not from what makes the most matches — and `sensitivity`
# reports what other windows would have done.
SEARCH_WINDOW_MM = 60.0
# A candidate must share this much of the run to be measuring the same wall.
MIN_SUPPORT_MM = 80.0
MIN_SUPPORT_FRACTION = 0.25
# Axis-aligned architecture: a candidate on the other axis is not a
# near-miss, it is a different wall.
MAX_ORIENTATION_DIFF_DEG = 0.0

# Why a candidate lost.
REJ_AXIS = "WRONG_AXIS"
REJ_WINDOW = "OUTSIDE_THE_LOCAL_SEARCH_WINDOW"
REJ_SUPPORT = "TOO_LITTLE_SHARED_EXTENT_TO_BE_THE_SAME_WALL"
REJ_PRIORITY = "A_HIGHER_AUTHORITY_SOURCE_COVERS_THIS_RUN"
REJ_FARTHER = "SAME_SOURCE_CLASS_BUT_LESS_SUPPORT_OR_FARTHER"


@dataclass(frozen=True)
class VectorCandidate:
    """One drawn line that could be a finish face, and what licenses it."""

    object_id: str
    axis: str
    fixed_mm: float
    start_mm: float
    end_mm: float
    source_type: str = SRC_VECTOR_WALL_FACE
    validation_class: str = "ESTABLISHED"

    @property
    def length_mm(self) -> float:
        return abs(self.end_mm - self.start_mm)


@dataclass
class MatchReport:
    candidates: list = field(default_factory=list)
    notes: dict = field(default_factory=dict)

    def record(self, *, limit: int = 60) -> dict:
        rows = [c.record() for c in self.candidates[:limit]]
        by_status = Counter(c.measurement_status for c in self.candidates)
        all_iv = [i for c in self.candidates for i in c.intervals]
        return {
            "regions_matched": len(self.candidates),
            "by_measurement_status": dict(by_status),
            "boundary_intervals": len(all_iv),
            "intervals_by_source": dict(Counter(
                i.source_type for i in all_iv)),
            "length_by_source_m": {
                s: round(sum(i.length_mm for i in all_iv
                             if i.source_type == s) / 1000, 2)
                for s in sorted({i.source_type for i in all_iv})},
            "candidate_rows": rows,
            "selection_rule": (
                "LOCAL and PRIORITY-LED. A candidate must be on the run's "
                "own axis, within the search window, and share enough "
                "extent to be the same wall; among those the higher "
                "authority source wins even when a lower one is nearer. "
                "NOT global-nearest: the nearest line to a room's north "
                "wall can be the south face of the wall above it"),
            "polygon_rule": (
                "built from the chosen vector objects only. A run with no "
                "match stays UNRESOLVED and leaves the candidate PARTIAL — "
                "it does not fall back to the pixel coordinate, and the "
                "raster outline is never scaled, warped, offset or "
                "smoothed into place"),
            "notes": dict(self.notes),
        }


def match_region(region_id: str, runs, candidates, *,
                 search_window_mm: float = SEARCH_WINDOW_MM,
                 min_support_mm: float = MIN_SUPPORT_MM,
                 candidate_id: str = "",
                 bridge_fixture_detours: bool = True,
                 basis: str = "CLEAR_INTERNAL_FINISH_FACE"
                 ) -> MeasuredSpaceCandidate:
    """Match one region's traced ring to source geometry, then rebuild it."""
    by_axis: dict = {}
    for c in candidates:
        by_axis.setdefault(c.axis, []).append(c)

    intervals, chosen_fixed = [], []
    for run in runs:
        iv, fixed = _match_run(
            run, by_axis.get(run.axis, ()), region_id=region_id,
            search_window_mm=search_window_mm,
            min_support_mm=min_support_mm)
        intervals.append(iv)
        chosen_fixed.append(fixed)

    # Fixture detours in the traced outline are collapsed onto the drawn
    # line that already spans them, before the ring is rebuilt.
    if bridge_fixture_detours:
        runs, intervals = bridge_indentations(runs, intervals,
                                              candidates)
        chosen_fixed = [i.fixed_mm if i.is_measured else None
                        for i in intervals]

    ring, closed = _rebuild(runs, chosen_fixed)
    area = perimeter = None
    wkt = ""
    geom_hash = ""
    if closed and ring is not None:
        area = abs(ring.area) / 1e6
        perimeter = ring.length / 1000.0
        wkt = ring.wkt
        import hashlib
        geom_hash = hashlib.sha256(wkt.encode()).hexdigest()[:24]

    unresolved = sum(1 for i in intervals if not i.is_measured)
    why = ("every run of the traced outline matched drawn source geometry, "
           "and the polygon is built from those objects"
           if closed else
           f"{unresolved} of {len(intervals)} boundary run(s) found no "
           "source geometry in the local window, so no polygon was built: "
           "a polygon completed with pixel coordinates would carry raster "
           "millimetres into a measurement")

    return MeasuredSpaceCandidate(
        candidate_id=candidate_id or f"MSC-{region_id}",
        region_id=region_id, intervals=tuple(intervals),
        polygon_wkt=wkt, area_m2=area, perimeter_m=perimeter,
        measurement_basis=basis if closed else "",
        geometry_hash=geom_hash, polygon_closed=closed, why=why)


def _match_run(run, pool, *, region_id: str, search_window_mm: float,
               min_support_mm: float):
    """Choose one candidate for one run, and record the whole decision."""
    iid = f"BI-{region_id}-{run.run_index:03d}"
    seen, rejected, live = [], [], []

    for c in pool:
        seen.append(c.object_id)
        dist = abs(c.fixed_mm - run.fixed_mm)
        if dist > search_window_mm:
            rejected.append((c.object_id, REJ_WINDOW))
            continue
        lo = max(min(run.start_mm, run.end_mm), min(c.start_mm, c.end_mm))
        hi = min(max(run.start_mm, run.end_mm), max(c.start_mm, c.end_mm))
        support = max(hi - lo, 0.0)
        need = min(min_support_mm,
                   max(run.length_mm * MIN_SUPPORT_FRACTION, 1.0))
        if support < need:
            rejected.append((c.object_id, REJ_SUPPORT))
            continue
        live.append((c, dist, support))

    if not live:
        return BoundaryInterval(
            interval_id=iid, axis=run.axis, fixed_mm=run.fixed_mm,
            start_mm=run.start_mm, end_mm=run.end_mm,
            source_type=SRC_UNRESOLVED,
            candidate_object_ids=tuple(seen),
            rejected=tuple(rejected),
            reason_chosen=(
                "no drawn source geometry on this axis lies within "
                f"{search_window_mm:.0f} mm of this run with enough shared "
                "extent to be the same wall. The run stays UNRESOLVED "
                "rather than taking its coordinate from the pixels")), None

    live.sort(key=lambda t: (SOURCE_PRIORITY.get(t[0].source_type, 99),
                             -t[2], t[1], t[0].object_id))
    best, dist, support = live[0]
    for c, d, s in live[1:]:
        reason = (REJ_PRIORITY
                  if SOURCE_PRIORITY.get(c.source_type, 99)
                  > SOURCE_PRIORITY.get(best.source_type, 99)
                  else REJ_FARTHER)
        rejected.append((c.object_id, reason))

    return BoundaryInterval(
        interval_id=iid, axis=run.axis, fixed_mm=best.fixed_mm,
        start_mm=max(min(run.start_mm, run.end_mm),
                     min(best.start_mm, best.end_mm)),
        end_mm=min(max(run.start_mm, run.end_mm),
                   max(best.start_mm, best.end_mm)),
        source_type=best.source_type, chosen_object_id=best.object_id,
        candidate_object_ids=tuple(seen), rejected=tuple(rejected),
        distance_mm=dist, orientation_difference_deg=0.0,
        support_length_mm=support, validation_class=best.validation_class,
        reason_chosen=(
            f"{best.source_type} on the same axis, {dist:.1f} mm from the "
            f"traced run, sharing {support:.0f} mm of its extent. "
            f"{len(live) - 1} other candidate(s) in the window lost on "
            "source authority, shared extent or distance")), best.fixed_mm


def _rebuild(runs, chosen_fixed):
    """Build the polygon from the chosen faces. All or nothing.

    Vertices are the intersections of consecutive runs: the ring alternates
    axes, so run i supplies one coordinate of the corner and run i+1 the
    other. Order is what makes this possible, which is why the tracer
    returns an ordered ring rather than a bag of segments.
    """
    from shapely.geometry import Polygon

    if len(runs) < 4 or any(f is None for f in chosen_fixed):
        return None, False

    pts = []
    n = len(runs)
    for i in range(n):
        a, b = runs[i], runs[(i + 1) % n]
        fa, fb = chosen_fixed[i], chosen_fixed[(i + 1) % n]
        if a.axis == b.axis:
            return None, False          # not an alternating ring
        if a.axis == "H":
            pts.append((fb, fa))        # x from the V run, y from the H run
        else:
            pts.append((fa, fb))

    try:
        poly = Polygon(pts)
        if not poly.is_valid:
            poly = poly.buffer(0)
        if poly.is_empty or poly.area <= 0:
            return None, False
        return poly, True
    except Exception:                    # noqa: BLE001
        return None, False


# ------------------------------------------------ building the candidates

def candidates_from_walls(wall_polys, *, classify=None) -> list:
    """Every DRAWN wall face, as a candidate finish face.

    Both faces of every band, each over the intervals where that face was
    actually drawn — not over the band's full length. A face is only a
    measurement where the draughtsman drew it, which is the same rule the
    wall authority applies to material.
    """
    out = []
    for wp in wall_polys:
        for side, fixed, ivs in (
                ("A", wp.face_a_mm, getattr(wp, "face_a_intervals", ())),
                ("B", wp.face_b_mm, getattr(wp, "face_b_intervals", ()))):
            if fixed is None:
                continue
            spans = list(ivs) or [(wp.start_mm, wp.end_mm)]
            for k, (lo, hi) in enumerate(spans, 1):
                src, val = (classify(wp, side, lo, hi) if classify
                            else (SRC_VECTOR_WALL_FACE, "ESTABLISHED"))
                if src is None:
                    continue
                out.append(VectorCandidate(
                    object_id=f"{wp.wall_band_id}-{side}{k:02d}",
                    axis=wp.axis, fixed_mm=float(fixed),
                    start_mm=float(min(lo, hi)), end_mm=float(max(lo, hi)),
                    source_type=src, validation_class=val))
    return out


def candidates_from_caps(caps) -> list:
    """Wall END CAPS: the drawn line that closes a wall across its thickness.

    Measured on AR-00 and easy to miss. A room's outline steps in and out
    where walls of different thickness meet and where a doorway is recessed,
    and those 130-150 mm jogs run along a wall's END, not along either of
    its faces. With only faces in the pool the nearest candidate for such a
    jog was 5 metres away, so a 98%-matched room could not close.

    A cap is drawn vector geometry with its own evidence in
    `engine.connectivity`, so this adds a CLASS OF DRAWN LINE that was
    omitted — it does not widen any tolerance.
    """
    out = []
    for c in caps:
        axis = getattr(c, "axis", "")
        span = getattr(c, "span_mm", None)
        at = getattr(c, "at_mm", None)
        if not axis or span is None or at is None:
            continue
        # A cap segment lies ALONG `axis` at `at_mm`, spanning `span_mm`.
        out.append(VectorCandidate(
            object_id=str(getattr(c, "cap_id", "")
                          or getattr(c, "segment_id", "")),
            axis=axis, fixed_mm=float(at),
            start_mm=float(min(span)), end_mm=float(max(span)),
            source_type=SRC_VECTOR_WALL_FACE,
            validation_class="ESTABLISHED_END_CAP"))
    return out


def candidates_from_portals(barriers) -> list:
    """Opening jambs: the sides of an accepted portal barrier."""
    out = []
    for b in barriers:
        poly = getattr(b, "polygon", None)
        if poly is None or getattr(poly, "is_empty", True):
            continue
        minx, miny, maxx, maxy = poly.bounds
        axis = getattr(b, "axis", "")
        pid = getattr(b, "portal_id", "PT")
        if axis == "H":
            pairs = ((miny, minx, maxx), (maxy, minx, maxx))
        else:
            pairs = ((minx, miny, maxy), (maxx, miny, maxy))
        for k, (fixed, lo, hi) in enumerate(pairs, 1):
            out.append(VectorCandidate(
                object_id=f"{pid}-J{k}", axis=axis, fixed_mm=float(fixed),
                start_mm=float(lo), end_mm=float(hi),
                source_type=SRC_VECTOR_OPENING_JAMB,
                validation_class=getattr(b, "geometry_status", "")))
    return out


# Why a run could not be measured. The distinction that decides whether
# more engineering would help: a run with NO drawn line covering it at any
# distance is a hole in the drawing (or a doorway), while a run with a
# covering line just outside the window is a tolerance question.
UNRES_NOTHING_DRAWN = "NO_DRAWN_LINE_COVERS_THIS_SPAN_AT_ANY_DISTANCE"
UNRES_TOO_FAR = "A_COVERING_LINE_EXISTS_BUT_LIES_OUTSIDE_THE_WINDOW"
UNRES_TOO_SHORT = "THE_RUN_IS_SHORTER_THAN_THE_MINIMUM_SHARED_EXTENT"


# Two drawn intervals belong to the same finish-face LINE when they share
# an axis and a fixed coordinate to within this much. A face is routinely
# drawn as several pieces, so requiring the same object id would refuse to
# recognise the line it is a piece of.
SAME_LINE_TOLERANCE_MM = 1.0


def _line_covers(candidates, axis: str, fixed_mm: float, lo: float,
                 hi: float, *, tolerance_mm: float = SAME_LINE_TOLERANCE_MM
                 ) -> bool:
    """Is [lo, hi] continuously DRAWN on this line?

    The discriminator between a fixture detour and a doorway. A wall face
    runs straight past a bathtub, so the line is drawn across it; at a
    doorway the face STOPS, so the drawn intervals leave a gap. Bridging
    the first measures along drawn geometry; bridging the second would
    close an opening.
    """
    spans = sorted(
        (min(c.start_mm, c.end_mm), max(c.start_mm, c.end_mm))
        for c in candidates
        if c.axis == axis and abs(c.fixed_mm - fixed_mm) <= tolerance_mm)
    reach = lo
    for a, b in spans:
        if a > reach + 1e-6:
            break
        reach = max(reach, b)
        if reach >= hi - 1e-6:
            return True
    return reach >= hi - 1e-6


def bridge_indentations(runs, intervals, candidates=()):
    """Collapse a fixture detour onto the drawn line that already spans it.

    Ink-based segmentation is what finds the rooms — a door leaf and a
    threshold close the gaps that leave the vector wall solid porous — but
    it also treats a drawn bathtub, kitchen unit or stair nosing as a
    barrier. The region outline therefore detours INTO the room around
    every fixture, and those detour runs have no wall anywhere near them:
    measured across AR-00, the median distance from an unmatched run to the
    nearest line covering it was 968 mm.

    A detour is recognised structurally, not by size: the matched runs on
    either side of it sit on the SAME drawn line, and that line is drawn
    CONTINUOUSLY across the whole detour. So the finish face there
    is that line — the draughtsman drew it straight past the bathtub — and
    collapsing the detour onto it measures along drawn geometry rather than
    inventing any.

    Where the two neighbours matched DIFFERENT objects the sequence is left
    alone: that is a doorway or a genuine step, and bridging it would be
    closing an opening.
    """
    n = len(runs)
    if n < 4:
        return list(runs), list(intervals)

    keep = [True] * n
    merged: dict = {}
    i = 0
    while i < n:
        if intervals[i].is_measured:
            i += 1
            continue
        # The maximal unmatched stretch [i, j)
        j = i
        while j < n and not intervals[j].is_measured:
            j += 1
        prev_i, next_i = (i - 1) % n, j % n
        if j - i >= n - 1 or prev_i == next_i:
            i = j
            continue
        a, b = intervals[prev_i], intervals[next_i]
        same_line = (a.is_measured and b.is_measured
                     and a.axis == b.axis
                     and abs(a.fixed_mm - b.fixed_mm)
                     <= SAME_LINE_TOLERANCE_MM)
        if same_line:
            lo = min(a.start_mm, a.end_mm, b.start_mm, b.end_mm)
            hi = max(a.start_mm, a.end_mm, b.start_mm, b.end_mm)
            if not _line_covers(candidates, a.axis, a.fixed_mm, lo, hi):
                i = j
                continue
            merged[prev_i] = (lo, hi)
            for k in range(i, j):
                keep[k] = False
            keep[next_i] = False
        i = j

    if not merged:
        return list(runs), list(intervals)

    out_runs, out_ivs = [], []
    for k in range(n):
        if not keep[k]:
            continue
        run, iv = runs[k], intervals[k]
        if k in merged:
            lo, hi = merged[k]
            run = type(run)(run.run_index, run.axis, run.fixed_mm, lo, hi,
                            run.pixel_length)
            iv = BoundaryInterval(
                interval_id=iv.interval_id, axis=iv.axis,
                fixed_mm=iv.fixed_mm, start_mm=lo, end_mm=hi,
                source_type=iv.source_type,
                chosen_object_id=iv.chosen_object_id,
                candidate_object_ids=iv.candidate_object_ids,
                rejected=iv.rejected, distance_mm=iv.distance_mm,
                orientation_difference_deg=iv.orientation_difference_deg,
                support_length_mm=hi - lo,
                validation_class=iv.validation_class,
                reason_chosen=(
                    iv.reason_chosen
                    + ". Extended across a fixture detour in the traced "
                      "outline: the runs on both sides of the detour chose "
                      "THIS object and its own drawn extent spans the gap, "
                      "so the finish face runs straight past the fitting"))
        out_runs.append(run)
        out_ivs.append(iv)
    return out_runs, out_ivs


def diagnose_unresolved(runs, candidate, candidates, *,
                        search_window_mm: float = SEARCH_WINDOW_MM,
                        min_support_mm: float = MIN_SUPPORT_MM) -> list:
    """For each unmeasured run, say which of the three cases it is.

    Without this the report can only say "31% unresolved", which does not
    tell anybody whether to widen a window, draw a missing wall class, or
    accept that the drawing is open there.
    """
    out = []
    by_axis: dict = {}
    for c in candidates:
        by_axis.setdefault(c.axis, []).append(c)

    for iv, run in zip(candidate.intervals, runs):
        if iv.is_measured:
            continue
        lo = min(run.start_mm, run.end_mm)
        hi = max(run.start_mm, run.end_mm)
        covering = []
        for c in by_axis.get(run.axis, ()):
            a = max(lo, min(c.start_mm, c.end_mm))
            b = min(hi, max(c.start_mm, c.end_mm))
            need = min(min_support_mm,
                       max(run.length_mm * MIN_SUPPORT_FRACTION, 1.0))
            if b - a >= need:
                covering.append((abs(c.fixed_mm - run.fixed_mm),
                                 c.object_id, b - a))
        covering.sort()
        if not covering:
            reason = (UNRES_TOO_SHORT if run.length_mm < min_support_mm
                      else UNRES_NOTHING_DRAWN)
            nearest = None
        else:
            reason = UNRES_TOO_FAR
            nearest = covering[0]
        out.append({
            "interval_id": iv.interval_id,
            "axis": run.axis,
            "APPROXIMATE_length_mm": round(run.length_mm, 1),
            "reason": reason,
            "nearest_covering_line": (
                None if nearest is None else
                {"object_id": nearest[1],
                 "distance_mm": round(nearest[0], 1),
                 "shared_extent_mm": round(nearest[2], 1)}),
            "what_would_fix_it": (
                "nothing in this drawing: the span has no line covering it, "
                "so either it is an opening or the wall was never drawn"
                if reason == UNRES_NOTHING_DRAWN else
                "a wider search window would reach it — which is a "
                "tolerance decision, and a wider window also starts "
                "matching the wrong face"
                if reason == UNRES_TOO_FAR else
                "nothing: the run is a fragment shorter than the shared "
                "extent any candidate needs, and matching it would be "
                "matching noise"),
        })
    return out


def unresolved_summary(rows) -> dict:
    flat = [r for group in rows for r in group]
    by = Counter(r["reason"] for r in flat)
    return {
        "unresolved_runs": len(flat),
        "by_reason": dict(by),
        "length_by_reason_m": {
            k: round(sum(r["APPROXIMATE_length_mm"] for r in flat
                         if r["reason"] == k) / 1000, 2)
            for k in sorted(by)},
        "nearest_covering_distance_mm": sorted(
            {round(r["nearest_covering_line"]["distance_mm"])
             for r in flat if r["nearest_covering_line"]})[:20],
        "what_this_decides": (
            "whether more engineering would help. NOTHING_DRAWN means the "
            "drawing is open there — a doorway, or a wall nobody drew — and "
            "no tolerance reaches it. OUTSIDE_THE_WINDOW is the only class "
            "a tolerance change could convert, and widening the window "
            "also starts matching the wrong face"),
        "rows": flat[:200],
    }


def sensitivity(runs, candidates, *,
                windows=(20.0, 40.0, 60.0, 100.0, 200.0)) -> dict:
    """What other search windows would have matched.

    A window nobody measured cannot be wrong. This does not choose it — it
    shows what widening the window buys and what it starts to sweep in,
    which is the argument a reviewer needs.
    """
    rows = []
    for w in windows:
        got = match_region("SENS", runs, candidates, search_window_mm=w)
        rows.append({
            "search_window_mm": w,
            "matched_runs": sum(1 for i in got.intervals if i.is_measured),
            "unresolved_runs": len(got.unresolved_intervals),
            "polygon_closed": got.polygon_closed,
            "area_m2": (None if got.area_m2 is None
                        else round(got.area_m2, 3)),
        })
    return {
        "in_use_mm": SEARCH_WINDOW_MM,
        "rows": rows,
        "why_not_wider": (
            "a wider window starts matching the far face of the same wall, "
            "or the near face of the next room's wall. Both close the "
            "polygon and both measure the wrong room"),
    }
