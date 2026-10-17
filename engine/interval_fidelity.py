"""E70 — does a wall polygon span only what was actually drawn?

A wall band is reduced to a start and an end, and a polygon is built across
that whole span. But the two drawn faces need not occupy all of it. Face A
may run [0, 3000] while face B runs [0, 1000] and [2000, 3000], and the
1000 mm between is a doorway. A polygon spanning [0, 3000] puts material
across that doorway, and then two things in the run contradict each other:
the wall solid says masonry, the portal barrier says opening.

Worse, it is silent. The polygon is valid, the union is valid, the area
conserves, and every invariant holds — because none of them knows what the
source drew. So the intervals are audited against the ring directly.

Three states per millimetre of a band's span:

    BOTH FACES DRAWN    material is defensible
    ONE FACE DRAWN      the other side is unknown; NEVER INVENT THE
                        MISSING HALF
    NEITHER FACE DRAWN  the ring spans something nobody drew

Only the third is a bridge, and a bridge is acceptable ONLY if something
accounts for it: a recorded extension with provenance, or a portal whose
existence is established. Anything else is an UNEXPLAINED BRIDGE and the run
must say so rather than let the geometry assert it.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

# A discontinuity below this is the numerical join between two collinear
# segments, not an opening. It is the same floor the leak map uses for an
# aperture, for the same reason: below it, nothing gets through.
MIN_BRIDGE_MM = 50.0

BRIDGE_EXPLAINED_BY_PORTAL = "EXPLAINED_BY_AN_ESTABLISHED_PORTAL"
BRIDGE_EXPLAINED_BY_EXTENSION = "EXPLAINED_BY_A_RECORDED_EXTENSION"
BRIDGE_UNEXPLAINED = "UNEXPLAINED_BRIDGE"
# Where only one face was drawn, the second face's position is extrapolated
# from where it WAS drawn. The band engine already records why it extended,
# and those reasons are not equivalent.
ONE_FACE_SUPPORTED = "ONE_FACE_WITH_A_CAP_OR_JUNCTION_TO_SUPPORT_IT"
ONE_FACE_UNSUPPORTED = "ONE_FACE_WITH_AN_UNRESOLVED_EXTENSION"
ONE_FACE_UNDECLARED = "ONE_FACE_WITH_NO_EXTENSION_RECORD_AT_ALL"

# Extension reasons the band engine itself treats as establishing material.
SUPPORTED_EXTENSION_REASONS = ("END_CAP_SUPPORTED", "JUNCTION_OVERHANG")

BRIDGE_CLASSES = (BRIDGE_EXPLAINED_BY_PORTAL, BRIDGE_EXPLAINED_BY_EXTENSION,
                  BRIDGE_UNEXPLAINED, ONE_FACE_SUPPORTED,
                  ONE_FACE_UNSUPPORTED, ONE_FACE_UNDECLARED)

# Classes where the polygon asserts material the source does not establish.
DEFECT_CLASSES = (BRIDGE_UNEXPLAINED, ONE_FACE_UNSUPPORTED,
                  ONE_FACE_UNDECLARED)


class IntervalFidelityError(RuntimeError):
    """A wall polygon spans drawing that does not exist."""


@dataclass(frozen=True)
class Bridge:
    """One stretch of a polygon's span that the faces do not account for."""

    wall_band_id: str
    axis: str
    fixed_mm: float
    start_mm: float
    end_mm: float
    bridge_class: str
    portal_ids: tuple[str, ...] = ()
    why: str = ""

    @property
    def length_mm(self) -> float:
        return self.end_mm - self.start_mm

    extension_reason: str = ""

    @property
    def is_a_defect(self) -> bool:
        return self.bridge_class in DEFECT_CLASSES

    def record(self) -> dict:
        return {"wall_band_id": self.wall_band_id, "axis": self.axis,
                "fixed_mm": round(self.fixed_mm, 1),
                "from_mm": round(self.start_mm, 1),
                "to_mm": round(self.end_mm, 1),
                "length_mm": round(self.length_mm, 1),
                "bridge_class": self.bridge_class,
                "extension_reason": self.extension_reason,
                "portal_ids": list(self.portal_ids),
                "is_a_defect": self.is_a_defect,
                "why": self.why}


@dataclass
class Report:
    bridges: list = field(default_factory=list)
    checked: dict = field(default_factory=dict)

    @property
    def defects(self) -> list:
        return [b for b in self.bridges if b.is_a_defect]

    @property
    def holds(self) -> bool:
        return not self.defects

    def record(self) -> dict:
        return {
            "holds": self.holds,
            "invariant": "NO_WALL_POLYGON_SILENTLY_BRIDGES_AN_UNDRAWN_GAP",
            "bridges": len(self.bridges),
            "polygons_asserting_unestablished_material": len(self.defects),
            "defect_classes": list(DEFECT_CLASSES),
            "by_class": dict(Counter(b.bridge_class for b in self.bridges)),
            "length_mm_by_class": {
                k: round(v, 1) for k, v in sorted(
                    _by_class_length(self.bridges).items())},
            "minimum_bridge_mm": MIN_BRIDGE_MM,
            "checked": dict(self.checked),
            "detail": [b.record() for b in sorted(
                self.bridges, key=lambda b: (not b.is_a_defect,
                                             -b.length_mm))[:40]],
            "what_a_bridge_is": (
                "a stretch of a band's span where NEITHER drawn face is "
                "present, so the polygon's ring crosses something nobody "
                "drew. Every geometric invariant can hold while this is "
                "happening, because none of them knows what the source drew"),
            "what_makes_one_acceptable": (
                "a recorded extension with provenance, or a portal whose "
                "existence is established. Nothing else — and a bridge no "
                "portal explains means the wall solid asserts masonry where "
                "the drawing is silent"),
        }


def _by_class_length(bridges) -> dict:
    out: dict = {}
    for b in bridges:
        out[b.bridge_class] = out.get(b.bridge_class, 0.0) + b.length_mm
    return out


def _union(spans) -> list:
    out = []
    for a, b in spans:
        a, b = (a, b) if a <= b else (b, a)
        if b > a:
            out.append((a, b))
    if not out:
        return []
    out.sort()
    merged = [list(out[0])]
    for s, e in out[1:]:
        if s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    return [(s, e) for s, e in merged]


def _intersect(a_runs, b_runs) -> list:
    out = []
    for a0, a1 in a_runs:
        for b0, b1 in b_runs:
            s, e = max(a0, b0), min(a1, b1)
            if e > s:
                out.append((s, e))
    return _union(out)


def _complement(runs, lo: float, hi: float) -> list:
    out, cur = [], lo
    for s, e in runs:
        s, e = max(s, lo), min(e, hi)
        if s > cur:
            out.append((cur, s))
        cur = max(cur, e)
    if cur < hi:
        out.append((cur, hi))
    return out


def _measure(runs) -> float:
    return sum(e - s for s, e in runs)


def audit(wall_polys, *, portals=(), established=None,
          min_bridge_mm: float = MIN_BRIDGE_MM) -> Report:
    """Compare every resolved polygon's span against what its faces drew.

    `established(portal)` decides whether a portal's EXISTENCE is settled
    enough to account for a gap. A portal whose existence is unresolved
    explains nothing: that is the whole point of splitting portal existence
    from portal geometry.
    """
    if established is None:
        def established(p):
            return True

    rep = Report()
    by_axis: dict = {}
    for p in portals:
        if established(p):
            by_axis.setdefault(p.axis, []).append(p)

    spans = both = one = neither = 0.0
    resolved = 0
    for wp in wall_polys:
        if not wp.is_resolved:
            continue
        resolved += 1
        lo, hi = min(wp.start_mm, wp.end_mm), max(wp.start_mm, wp.end_mm)
        if hi <= lo:
            continue
        a = _union(wp.face_a_intervals)
        b = _union(wp.face_b_intervals)
        if not a and not b:
            # No interval provenance at all: the audit cannot run on this
            # band, and saying nothing would read as a pass.
            rep.bridges.append(Bridge(
                wall_band_id=wp.wall_band_id, axis=wp.axis,
                fixed_mm=(wp.face_a_mm if wp.face_a_mm is not None else 0.0),
                start_mm=lo, end_mm=hi,
                bridge_class=BRIDGE_UNEXPLAINED, why=(
                    "this polygon records no face intervals, so there is no "
                    "evidence that its ring spans drawn geometry. An audit "
                    "that cannot run is not a pass")))
            continue

        both_runs = _intersect(a, b)
        either = _union(list(a) + list(b))
        spans += hi - lo
        both += _measure(both_runs)
        one += _measure(either) - _measure(both_runs)
        gaps = _complement(either, lo, hi)
        neither += _measure(gaps)

        # One face only. The polygon spans it and the second face's position
        # there is an extrapolation, so what matters is whether the band
        # engine recorded a reason and whether that reason establishes
        # material. Its own UNRESOLVED_EXTENSION note says it does not.
        for s, e in _complement(both_runs, lo, hi):
            if e - s < min_bridge_mm:
                continue
            if _measure(_intersect([(s, e)], either)) <= 0.0:
                continue
            reason = _covering_extension(wp, s, e, lo, hi)
            if reason in SUPPORTED_EXTENSION_REASONS:
                cls, why = ONE_FACE_SUPPORTED, (
                    f"{e - s:.0f} mm where only one face was drawn, and the "
                    f"band records {reason} for it. The second face's "
                    "position is an extrapolation, but a cap or a junction "
                    "closes the band over it")
            elif reason:
                cls, why = ONE_FACE_UNSUPPORTED, (
                    f"{e - s:.0f} mm where only one face was drawn and the "
                    f"band records {reason}: by the band engine's own note, "
                    "this extent beyond the paired interval is NOT "
                    "established material. The polygon carries it anyway, so "
                    "the wall solid is asserting masonry the source does not "
                    "establish")
            else:
                cls, why = ONE_FACE_UNDECLARED, (
                    f"{e - s:.0f} mm where only one face was drawn and NO "
                    "extension record covers it. The polygon extends over "
                    "length the drawing does not support and says nothing "
                    "about why")
            rep.bridges.append(Bridge(
                wall_band_id=wp.wall_band_id, axis=wp.axis,
                fixed_mm=(wp.face_a_mm if wp.face_a_mm is not None else 0.0),
                start_mm=s, end_mm=e, bridge_class=cls,
                extension_reason=reason, why=why))

        for s, e in gaps:
            if e - s < min_bridge_mm:
                continue
            hit = tuple(sorted(
                p.portal_id for p in by_axis.get(wp.axis, ())
                if min(p.start_mm, p.end_mm) < e
                and max(p.start_mm, p.end_mm) > s))
            ext = _explained_by_extension(wp, s, e, lo, hi)
            if hit:
                cls, why = BRIDGE_EXPLAINED_BY_PORTAL, (
                    f"{e - s:.0f} mm where neither face was drawn, and "
                    f"{len(hit)} established portal(s) sit there. The gap is "
                    "a doorway — but note the polygon still spans it, so the "
                    "wall solid carries material across the opening and the "
                    "barrier is doing the work twice")
            elif ext:
                cls, why = BRIDGE_EXPLAINED_BY_EXTENSION, (
                    f"{e - s:.0f} mm accounted for by a recorded extension: "
                    f"{ext}")
            else:
                cls, why = BRIDGE_UNEXPLAINED, (
                    f"{e - s:.0f} mm where NEITHER face was drawn and "
                    "nothing accounts for it — no established portal, no "
                    "recorded extension. The ring spans drawing that does "
                    "not exist, and the wall solid asserts masonry where the "
                    "source is silent")
            rep.bridges.append(Bridge(
                wall_band_id=wp.wall_band_id, axis=wp.axis,
                fixed_mm=(wp.face_a_mm if wp.face_a_mm is not None else 0.0),
                start_mm=s, end_mm=e, bridge_class=cls, portal_ids=hit,
                why=why))

    rep.checked.update({
        "resolved_wall_polygons": resolved,
        "total_span_mm": round(spans, 1),
        "both_faces_drawn_mm": round(both, 1),
        "one_face_drawn_mm": round(one, 1),
        "neither_face_drawn_mm": round(neither, 1),
        "established_portals_considered": sum(
            len(v) for v in by_axis.values()),
        "fidelity": ("the three lengths add to the total span. A band whose "
                     "span is all BOTH FACES drew exactly what the polygon "
                     "claims"),
    })
    return rep


def _covering_extension(wp, s: float, e: float, lo: float,
                        hi: float) -> str:
    """Which recorded extension covers [s, e], by the end it extends from."""
    for ext in wp.extensions:
        run = float(ext.get("length_mm") or 0.0)
        if run <= 0.0:
            continue
        end = str(ext.get("end", "")).lower()
        tol = 1.0
        if end in ("start", "lo", "a"):
            if s >= lo - tol and e <= lo + run + tol:
                return str(ext.get("extension_reason") or end)
        elif s >= hi - run - tol and e <= hi + tol:
            return str(ext.get("extension_reason") or end)
    return ""


def _explained_by_extension(wp, s: float, e: float, lo: float,
                            hi: float) -> str:
    """Does a recorded extension cover this undrawn gap?"""
    return _covering_extension(wp, s, e, lo, hi)


def assert_no_silent_bridge(wall_polys, *, portals=(), established=None
                            ) -> None:
    rep = audit(wall_polys, portals=portals, established=established)
    if not rep.holds:
        worst = sorted(rep.defects, key=lambda b: -b.length_mm)[:5]
        raise IntervalFidelityError(
            f"{len(rep.defects)} wall polygon(s) span drawing that does not "
            "exist:\n  - " + "\n  - ".join(
                f"{b.wall_band_id} {b.length_mm:.0f} mm — {b.why}"
                for b in worst))
