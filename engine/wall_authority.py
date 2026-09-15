"""E74 — two wall solids, because material presence is not one question.

The wall solid was one object and every quantity was measured against it.
But 55.9 m of its span rests on extensions the band engine itself records as
`UNRESOLVED_EXTENSION` — *"this band's extent beyond the paired interval is
NOT established material"*. A single solid cannot hold both that and the
446 m where two faces were actually drawn, because a reader cannot tell
which part a number came from.

So there are two, and every wall polygon INTERVAL says which it may enter:

    ESTABLISHED_WALL_SOLID
        only intervals whose physical material presence is established:
        both drawn faces present, or a single-face extension a cap or
        junction closes, or a validated junction patch. Production geometry
        may depend on this and nothing else.

    DIAGNOSTIC_AUGMENTED_WALL_SOLID
        the established solid PLUS unresolved extensions, unvalidated
        patches and any other hypothesis geometry, each with provenance.
        Useful for finding what is missing. No quantity may depend on it.

The admission decision is per INTERVAL, not per polygon. A band is usually
part established and part not — face A runs the whole span, face B stops
short, and a cap explains one end but nothing explains the other. Admitting
or refusing the whole polygon would either discard 24 m of real wall or
admit 14 m of invention.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

ESTABLISHED = "ESTABLISHED_WALL_SOLID"
DIAGNOSTIC = "DIAGNOSTIC_AUGMENTED_WALL_SOLID"
SOLIDS = (ESTABLISHED, DIAGNOSTIC)

# Why an interval is established.
BOTH_FACES_DRAWN = "BOTH_FACES_DRAWN"
ONE_FACE_CAP_CLOSED = "ONE_FACE_WITH_AN_END_CAP"
ONE_FACE_JUNCTION_CLOSED = "ONE_FACE_WITH_A_JUNCTION_OVERHANG"
VALIDATED_JUNCTION_PATCH = "VALIDATED_JUNCTION_PATCH"

# Why an interval is diagnostic only.
UNRESOLVED_EXTENSION = "UNRESOLVED_SINGLE_FACE_EXTENSION"
UNDECLARED_EXTENSION = "SINGLE_FACE_WITH_NO_EXTENSION_RECORD"
NO_FACE_INTERVALS = "NO_FACE_INTERVAL_PROVENANCE"
UNVALIDATED_PATCH = "UNVALIDATED_JUNCTION_PATCH"

ESTABLISHED_GROUNDS = (BOTH_FACES_DRAWN, ONE_FACE_CAP_CLOSED,
                       ONE_FACE_JUNCTION_CLOSED, VALIDATED_JUNCTION_PATCH)
DIAGNOSTIC_GROUNDS = (UNRESOLVED_EXTENSION, UNDECLARED_EXTENSION,
                      NO_FACE_INTERVALS, UNVALIDATED_PATCH)

# Extension reasons the band engine treats as establishing material.
CAP_REASONS = {"END_CAP_SUPPORTED": ONE_FACE_CAP_CLOSED,
               "JUNCTION_OVERHANG": ONE_FACE_JUNCTION_CLOSED}

# An interval shorter than this is a numerical join between two collinear
# stretches, not a decision. Same floor as the leak map's aperture.
MIN_INTERVAL_MM = 50.0


class WallAuthorityError(RuntimeError):
    """Production geometry was asked to depend on the diagnostic solid."""


@dataclass(frozen=True)
class Admission:
    """One interval of one wall polygon, and which solid it may enter."""

    wall_band_id: str
    axis: str
    fixed_mm: float
    start_mm: float
    end_mm: float
    grounds: str
    solids: tuple[str, ...]
    source_face_ids: tuple[str, ...] = ()
    patch_id: str = ""
    why: str = ""

    @property
    def length_mm(self) -> float:
        return self.end_mm - self.start_mm

    @property
    def is_established(self) -> bool:
        return ESTABLISHED in self.solids

    def record(self) -> dict:
        return {"wall_band_id": self.wall_band_id, "axis": self.axis,
                "from_mm": round(self.start_mm, 1),
                "to_mm": round(self.end_mm, 1),
                "length_mm": round(self.length_mm, 1),
                "grounds": self.grounds,
                "may_enter": list(self.solids),
                "established": self.is_established,
                "source_face_ids": list(self.source_face_ids),
                "junction_patch_id": self.patch_id,
                "why": self.why}


@dataclass
class AuthorityReport:
    admissions: list = field(default_factory=list)
    notes: dict = field(default_factory=dict)

    @property
    def established(self) -> list:
        return [a for a in self.admissions if a.is_established]

    @property
    def diagnostic_only(self) -> list:
        return [a for a in self.admissions if not a.is_established]

    def _m(self, items) -> float:
        return round(sum(a.length_mm for a in items) / 1000, 3)

    def record(self) -> dict:
        return {
            "solids": list(SOLIDS),
            "intervals": len(self.admissions),
            "established_intervals": len(self.established),
            "diagnostic_only_intervals": len(self.diagnostic_only),
            "established_length_m": self._m(self.established),
            "diagnostic_only_length_m": self._m(self.diagnostic_only),
            "total_length_m": self._m(self.admissions),
            "by_grounds_m": {
                k: round(v / 1000, 3) for k, v in sorted(
                    _by_grounds(self.admissions).items())},
            "by_grounds_count": dict(Counter(
                a.grounds for a in self.admissions)),
            "diagnostic_only_detail": [
                a.record() for a in sorted(
                    self.diagnostic_only, key=lambda a: -a.length_mm)][:40],
            "the_rule": (
                "admission is per INTERVAL, not per polygon. A band is "
                "usually part established and part not, and deciding whole "
                "polygons would either discard real wall or admit "
                "invention"),
            "what_may_depend_on_each": {
                ESTABLISHED: ("production room geometry, released "
                              "quantities, frozen controls"),
                DIAGNOSTIC: ("finding what is missing. NO quantity and NO "
                             "production room geometry"),
            },
            "notes": dict(self.notes),
        }


def _by_grounds(admissions) -> dict:
    out: dict = {}
    for a in admissions:
        out[a.grounds] = out.get(a.grounds, 0.0) + a.length_mm
    return out


def _union(spans) -> list:
    out = [(min(a, b), max(a, b)) for a, b in spans if max(a, b) > min(a, b)]
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


def _covering_extension(wp, s: float, e: float, lo: float,
                        hi: float) -> str:
    """Which recorded extension covers [s, e]. Shared with the fidelity
    audit deliberately: the two must agree about what the band declared."""
    from engine.interval_fidelity import _covering_extension as shared
    return shared(wp, s, e, lo, hi)


def classify_intervals(wall_polys, *, patches=(),
                       min_interval_mm: float = MIN_INTERVAL_MM
                       ) -> AuthorityReport:
    """Decide, per interval, which solid it may enter. Repairs nothing."""
    rep = AuthorityReport()
    by_patch = {p.patch_id: p for p in patches}

    for wp in wall_polys:
        if not wp.is_resolved:
            continue
        lo = min(wp.start_mm, wp.end_mm)
        hi = max(wp.start_mm, wp.end_mm)
        if hi <= lo:
            continue
        fixed = wp.face_a_mm if wp.face_a_mm is not None else 0.0
        faces = tuple(wp.source_face_ids)
        a = _union(list(getattr(wp, "face_a_intervals", ()) or ()))
        b = _union(list(getattr(wp, "face_b_intervals", ()) or ()))

        def add(s, e, grounds, solids, why, patch_id=""):
            if e - s < min_interval_mm:
                return
            rep.admissions.append(Admission(
                wall_band_id=wp.wall_band_id, axis=wp.axis, fixed_mm=fixed,
                start_mm=s, end_mm=e, grounds=grounds, solids=solids,
                source_face_ids=faces, patch_id=patch_id, why=why))

        if not a and not b:
            # No provenance at all. It cannot be shown established, so it
            # is not — the absence of evidence is not evidence.
            add(lo, hi, NO_FACE_INTERVALS, (DIAGNOSTIC,),
                "this polygon records no face intervals, so no part of it "
                "can be shown to rest on drawn geometry. An interval that "
                "cannot be established is not established")
            continue

        both = _intersect(a, b)
        for s, e in both:
            add(s, e, BOTH_FACES_DRAWN, (ESTABLISHED, DIAGNOSTIC),
                f"{e - s:.0f} mm with BOTH faces drawn: material presence "
                "is established by the drawing itself")

        for s, e in _complement(both, lo, hi):
            reason = _covering_extension(wp, s, e, lo, hi)
            ground = CAP_REASONS.get(reason)
            if ground:
                add(s, e, ground, (ESTABLISHED, DIAGNOSTIC),
                    f"{e - s:.0f} mm with one face drawn and the band "
                    f"recording {reason}. The second face's position is an "
                    "extrapolation, but a physical cap or junction closes "
                    "the band over it")
            elif reason:
                add(s, e, UNRESOLVED_EXTENSION, (DIAGNOSTIC,),
                    f"{e - s:.0f} mm the band itself records as {reason}: "
                    "by its own note this extent beyond the paired interval "
                    "is NOT established material. It is refused from the "
                    "established solid and kept here with provenance")
            else:
                add(s, e, UNDECLARED_EXTENSION, (DIAGNOSTIC,),
                    f"{e - s:.0f} mm with one face drawn and NO extension "
                    "record covering it. Nothing says why the polygon "
                    "extends here")

    for p in patches:
        solids = ((ESTABLISHED, DIAGNOSTIC) if p.is_validated
                  else (DIAGNOSTIC,))
        grounds = (VALIDATED_JUNCTION_PATCH if p.is_validated
                   else UNVALIDATED_PATCH)
        rep.admissions.append(Admission(
            wall_band_id=",".join(p.wall_band_ids), axis=p.axis,
            fixed_mm=0.0, start_mm=0.0, end_mm=p.extension_mm,
            grounds=grounds, solids=solids,
            source_face_ids=tuple(p.source_face_ids), patch_id=p.patch_id,
            why=p.why))
    rep.notes["junction_patches"] = len(by_patch)
    rep.notes["validated_junction_patches"] = sum(
        1 for p in patches if p.is_validated)
    return rep


def build(wall_polys, *, patches=(), solid=ESTABLISHED, snap_grid_mm=None,
          report=None):
    """Build one of the two solids from the intervals admitted to it.

    A polygon is CLIPPED to its admitted intervals rather than included or
    dropped whole, which is what makes the two solids differ by exactly the
    material whose presence is or is not established.
    """
    from shapely.geometry import Polygon, box
    from shapely.ops import unary_union

    if solid not in SOLIDS:
        raise WallAuthorityError(f"unknown solid {solid!r}; expected one of "
                                 f"{SOLIDS}")
    rep = report if report is not None else classify_intervals(
        wall_polys, patches=patches)
    admitted: dict = {}
    for a in rep.admissions:
        if solid in a.solids and not a.patch_id:
            admitted.setdefault(a.wall_band_id, []).append(
                (a.start_mm, a.end_mm))

    shapes = []
    for wp in wall_polys:
        runs = _union(admitted.get(wp.wall_band_id, []))
        if not runs or not wp.is_resolved:
            continue
        p = Polygon(list(wp.ring))
        if not p.is_valid:
            p = p.buffer(0)
        x0, y0, x1, y1 = p.bounds
        for s, e in runs:
            clip = (box(s, y0, e, y1) if wp.axis == "H"
                    else box(x0, s, x1, e))
            piece = p.intersection(clip)
            if not piece.is_empty and piece.area > 0.0:
                shapes.append(piece)

    # Validated patches are material in the established solid; every patch
    # is material in the diagnostic one.
    for patch in patches:
        if solid == ESTABLISHED and not patch.is_validated:
            continue
        if patch.polygon is not None and not patch.polygon.is_empty:
            shapes.append(patch.polygon)

    if not shapes:
        return None
    geom = unary_union(shapes)
    if snap_grid_mm:
        from shapely import set_precision
        geom = set_precision(geom, snap_grid_mm)
        if not geom.is_valid:
            geom = geom.buffer(0)
    return geom


# How close a diagnostic-only interval must lie to a space's boundary to
# count as holding that boundary up.
BOUNDARY_REACH_MM = 1.0


def unestablished_dependency(candidate, admissions, wall_polys, *,
                             reach_mm: float = BOUNDARY_REACH_MM) -> dict:
    """Does this space's boundary rest on material that is not established?

    A polygon can be geometrically perfect and still exist only because a
    hypothesis was treated as masonry. That is the difference between a
    diagnostic space and a releasable one, and it is not visible from the
    polygon.
    """
    from shapely.geometry import Polygon, box

    geom = getattr(candidate, "geometry", None)
    if geom is None:
        return {"depends_on_unestablished_material": None,
                "why": "no geometry to test"}
    edge = geom.boundary
    by_band = {wp.wall_band_id: wp for wp in wall_polys if wp.is_resolved}

    touching, length = [], 0.0
    for a in admissions:
        if a.is_established or a.patch_id:
            continue
        wp = by_band.get(a.wall_band_id)
        if wp is None:
            continue
        p = Polygon(list(wp.ring))
        if not p.is_valid:
            p = p.buffer(0)
        x0, y0, x1, y1 = p.bounds
        clip = (box(a.start_mm, y0, a.end_mm, y1) if a.axis == "H"
                else box(x0, a.start_mm, x1, a.end_mm))
        piece = p.intersection(clip)
        if piece.is_empty:
            continue
        if piece.distance(edge) <= reach_mm:
            touching.append(a)
            length += a.length_mm

    return {
        "depends_on_unestablished_material": bool(touching),
        "unestablished_intervals_on_its_boundary": len(touching),
        "unestablished_boundary_length_m": round(length / 1000, 3),
        "intervals": [a.record() for a in sorted(
            touching, key=lambda x: -x.length_mm)][:12],
        "why": (
            "this space's boundary runs along material whose physical "
            "presence is not established, so the space exists as drawn only "
            "because a hypothesis was treated as masonry"
            if touching else
            "every stretch of this space's boundary rests on material whose "
            "presence is established"),
    }


def compare(established, diagnostic) -> dict:
    """What the diagnostic solid adds, in area and in material."""
    e_area = 0.0 if established is None else established.area
    d_area = 0.0 if diagnostic is None else diagnostic.area
    extra = None
    if established is not None and diagnostic is not None:
        extra = diagnostic.difference(established)
    return {
        "established_area_m2": round(e_area / 1e6, 4),
        "diagnostic_augmented_area_m2": round(d_area / 1e6, 4),
        "added_by_hypothesis_m2": round(
            0.0 if extra is None else extra.area / 1e6, 4),
        "added_share_of_diagnostic_pct": (
            None if d_area <= 0.0 else
            round(100.0 * (d_area - e_area) / d_area, 2)),
        "established_components": _components(established),
        "diagnostic_components": _components(diagnostic),
        "why_components_are_not_a_target": (
            "a disconnected wall component is not automatically defective. "
            "The target is correct SPACE PARTITIONING, and component count "
            "is reported only so the two solids can be told apart"),
    }


def _components(geom) -> int | None:
    if geom is None:
        return None
    return (len(geom.geoms) if geom.geom_type.startswith("Multi") else 1)
