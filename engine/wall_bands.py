"""E25V2 — a wall is a BAND, and it is not always two parallel strokes.

Two findings drove this rewrite, both measured on AR-00 rather than reasoned
about.

THE ROOT CAUSE OF ZERO ROOM FACES. Every side of every control room DOES have
its two heavy-pen faces, ~150 mm apart. Pairing rejected them anyway, because
`wall_pairs` ranks candidate mates BY GAP ALONE:

    gap 105 mm, overlap  100 mm   <- a scrap of fixture linework, and it won
    gap 151 mm, overlap 2400 mm   <- the actual other face of the wall

The scrap is 46 mm nearer and has one twenty-fourth of the overlap. "Nearest
parallel line" is a proxy for "the other face of this wall" and on a drawing
full of fixtures it is a bad one. A mate is now scored by how much of the face
it actually runs ALONGSIDE, with distance as a tiebreak.

THE MODEL WAS ALSO TOO NARROW. `two parallel strokes -> wall` is one drawing
convention among several. Another architect's plan will use filled bands or
single lines, and must not fail for it. So representation is an OBSERVATION
with a named type, and a band may be supported by faces, caps, fills or raster
evidence in combination.

    DO NOT PROMOTE A PROXY INTO PHYSICAL TRUTH.
    A heavy pen is not a wall. A fill is not a wall. Nearest is not paired.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

# How the architect drew this wall. Observations, never automatic walls.
DOUBLE_FACE_WALL = "DOUBLE_FACE_WALL"
SINGLE_LINE_WALL = "SINGLE_LINE_WALL"
FILLED_WALL_BAND = "FILLED_WALL_BAND"
RECTANGULAR_WALL_OBJECT = "RECTANGULAR_WALL_OBJECT"
COMPOSITE_WALL_GEOMETRY = "COMPOSITE_WALL_GEOMETRY"
CURVED_WALL = "CURVED_WALL"
UNKNOWN_WALL_REPRESENTATION = "UNKNOWN_WALL_REPRESENTATION"

REPRESENTATIONS = (DOUBLE_FACE_WALL, SINGLE_LINE_WALL, FILLED_WALL_BAND,
                   RECTANGULAR_WALL_OBJECT, COMPOSITE_WALL_GEOMETRY,
                   CURVED_WALL, UNKNOWN_WALL_REPRESENTATION)

# WHY A BAND EXTENDS BEYOND WHERE BOTH FACES RUN TOGETHER. Taking the union of
# the faces was necessary — at an L corner the inner face stops a wall
# thickness early because the perpendicular wall occupies that corner — but an
# unexamined union can bridge a real opening, which is exactly the thing this
# engine exists to find.
JUNCTION_OVERHANG = "JUNCTION_OVERHANG"
END_CAP_SUPPORTED = "END_CAP_SUPPORTED"
FRAGMENTED_MATE_EXTENSION = "FRAGMENTED_MATE"
UNRESOLVED_EXTENSION = "UNRESOLVED_EXTENSION"

EXTENSION_REASONS = (JUNCTION_OVERHANG, END_CAP_SUPPORTED,
                     FRAGMENTED_MATE_EXTENSION, UNRESOLVED_EXTENSION)

# An overhang no longer than this is explained by the wall it meets: a
# centreline runs to the far face of the perpendicular wall and stops.
MAX_JUNCTION_OVERHANG_MM = 450.0

VALIDATED = "VALIDATED"
PROBABLE = "PROBABLE"
AMBIGUOUS = "AMBIGUOUS"
REJECTED = "REJECTED"

# Why a face found no mate. Reported per PROBABLE WALL FACE, so the histogram
# is about walls rather than about thousands of glyph strokes.
NO_PARALLEL_FACE = "NO_PARALLEL_FACE"
INSUFFICIENT_OVERLAP = "INSUFFICIENT_OVERLAP"
SEPARATION_INCONSISTENT = "SEPARATION_INCONSISTENT"
FRAGMENTED_MATE = "FRAGMENTED_MATE"
MATE_DIFFERENT_OBJECT_TYPE = "MATE_EXISTS_DIFFERENT_OBJECT_TYPE"
END_CAP_INTERRUPTION = "END_CAP_INTERRUPTION"
JUNCTION_INTERRUPTION = "JUNCTION_INTERRUPTION"
PAIRED_OK = "PAIRED"
OTHER = "OTHER"
REJECT_UNRESOLVED = "UNRESOLVED"

# Evidence families. Two independent ones before a band is VALIDATED.
FAMILY_FACE = "FACE_GEOMETRY"
FAMILY_CLOSURE = "CLOSURE"
FAMILY_RASTER = "RASTER"
FAMILY_STYLE = "SOURCE_STYLE"

E_TWO_FACES = "TWO_PARALLEL_FACES"
E_STRONG_OVERLAP = "FACES_OVERLAP_MOST_OF_THEIR_LENGTH"
E_END_CAP = "END_CAP_CLOSES_THE_BAND"
E_RASTER_BAND = "RASTER_WALL_MASK_SUPPORTS_THE_BAND"
E_WALL_PEN = "DRAWN_WITH_THE_SHEET_WALL_PEN"

EVIDENCE_FAMILY = {
    E_TWO_FACES: FAMILY_FACE,
    E_STRONG_OVERLAP: FAMILY_FACE,
    E_END_CAP: FAMILY_CLOSURE,
    E_RASTER_BAND: FAMILY_RASTER,
    E_WALL_PEN: FAMILY_STYLE,
}
MIN_FAMILIES_FOR_VALIDATED = 2

# A mate must run alongside at least this share of the shorter face. This is
# the test that replaces "nearest": it asks whether the two lines are the two
# sides of one wall, which is a question about company, not about distance.
MIN_OVERLAP_RATIO = 0.5
# And an absolute floor, so two 40 mm scraps cannot pair with each other.
MIN_OVERLAP_MM = 200.0
# The separation window a wall may have. Wide on purpose: thickness is
# evidence, never a classification.
MIN_SEPARATION_MM = 60.0
MAX_SEPARATION_MM = 450.0
# A face shorter than this is not a wall face on any drawing at this scale.
MIN_FACE_MM = 300.0


class WallBandError(RuntimeError):
    """A band was asserted without the evidence to carry it."""


@dataclass(frozen=True)
class WallBandCandidate:
    """One wall, however the architect drew it."""

    wall_band_id: str
    representation_type: str
    axis: str
    centreline_mm: float
    start_mm: float
    end_mm: float
    face_a_ids: tuple[str, ...] = ()
    face_b_ids: tuple[str, ...] = ()
    # The two faces' own constant coordinates, so ownership can name a real
    # drawn face rather than "centreline plus half the thickness".
    face_a_mm: float | None = None
    face_b_mm: float | None = None
    cap_ids: tuple[str, ...] = ()
    source_object_ids: tuple[str, ...] = ()
    wall_face_separation_mm: float | None = None
    separation_basis: str = ""
    supporting_evidence: tuple[str, ...] = ()
    conflicting_evidence: tuple[str, ...] = ()
    raster_support_ratio: float | None = None
    validation_status: str = AMBIGUOUS
    why: str = ""
    # The intervals each face actually occupies, so a union can be audited.
    # Reducing face A [0,3000] and face B [0,1000]+[2000,3000] to a band
    # [0,3000] without recording the 1000 mm discontinuity is how a union
    # silently bridges an opening.
    face_a_intervals: tuple[tuple[float, float], ...] = ()
    face_b_intervals: tuple[tuple[float, float], ...] = ()
    both_faces_interval: tuple[float, float] | None = None
    extensions: tuple[dict, ...] = ()

    @property
    def length_mm(self) -> float:
        return abs(self.end_mm - self.start_mm)

    @property
    def families(self) -> set:
        return {EVIDENCE_FAMILY[e] for e in self.supporting_evidence
                if e in EVIDENCE_FAMILY}

    def record(self) -> dict:
        return {"wall_band_id": self.wall_band_id,
                "representation_type": self.representation_type,
                "axis": self.axis,
                "centreline_mm": round(self.centreline_mm, 1),
                "length_mm": round(self.length_mm, 1),
                "face_a_ids": list(self.face_a_ids),
                "face_b_ids": list(self.face_b_ids),
                "face_a_mm": (None if self.face_a_mm is None
                              else round(self.face_a_mm, 1)),
                "face_b_mm": (None if self.face_b_mm is None
                              else round(self.face_b_mm, 1)),
                "cap_ids": list(self.cap_ids),
                "wall_face_separation_mm": (
                    None if self.wall_face_separation_mm is None
                    else round(self.wall_face_separation_mm, 1)),
                "separation_basis": self.separation_basis,
                "supporting_evidence": list(self.supporting_evidence),
                "conflicting_evidence": list(self.conflicting_evidence),
                "families": sorted(self.families),
                "raster_support_ratio": (
                    None if self.raster_support_ratio is None
                    else round(self.raster_support_ratio, 3)),
                "face_a_intervals": [list(i) for i in self.face_a_intervals],
                "face_b_intervals": [list(i) for i in self.face_b_intervals],
                "both_faces_interval": (list(self.both_faces_interval)
                                        if self.both_faces_interval else None),
                "extensions": [dict(e) for e in self.extensions],
                "validation_status": self.validation_status, "why": self.why}


@dataclass(frozen=True)
class FaceRejection:
    """Why one PROBABLE wall face found no mate."""

    segment_id: str
    axis: str
    fixed_mm: float
    length_mm: float
    reason: str
    best_gap_mm: float | None = None
    best_overlap_mm: float | None = None
    candidates_in_window: int = 0

    def record(self) -> dict:
        return {"segment_id": self.segment_id, "axis": self.axis,
                "length_mm": round(self.length_mm, 1), "reason": self.reason,
                "best_gap_mm": (None if self.best_gap_mm is None
                                else round(self.best_gap_mm, 1)),
                "best_overlap_mm": (None if self.best_overlap_mm is None
                                    else round(self.best_overlap_mm, 1)),
                "candidates_in_window": self.candidates_in_window}


def _extent(s):
    return min(s.start_mm, s.end_mm), max(s.start_mm, s.end_mm)


def mate_score(a, b) -> tuple[float, float, float]:
    """How much of the shorter face this candidate runs alongside.

    Returns (overlap_mm, overlap_ratio, gap_mm). The RATIO is what ranks
    mates — a wall's two faces run together for most of their length, and a
    fixture line that happens to be nearer does not.
    """
    a_lo, a_hi = _extent(a)
    b_lo, b_hi = _extent(b)
    overlap = min(a_hi, b_hi) - max(a_lo, b_lo)
    shorter = min(a_hi - a_lo, b_hi - b_lo)
    ratio = (overlap / shorter) if shorter > 0 else 0.0
    return overlap, ratio, abs(a.fixed_mm - b.fixed_mm)


def build_bands(faces, *, caps=(), wall_pen: float | None = None,
                raster_support=None) -> tuple[list, list]:
    """Pair faces into bands by COMPANY, not by proximity.

    `faces` should be the probable wall-face population. `raster_support` is an
    optional callable (axis, centreline, start, end) -> ratio in 0..1; it is
    ONE evidence family and can never validate a band alone.
    """
    by_axis: dict[str, list] = {}
    for s in faces:
        if s.length_mm < MIN_FACE_MM:
            continue
        by_axis.setdefault(s.axis, []).append(s)

    caps_by_axis: dict[str, list] = {}
    for c in caps:
        caps_by_axis.setdefault(c.axis, []).append(c)

    bands: list[WallBandCandidate] = []
    rejections: list[FaceRejection] = []
    used: set = set()
    n = 0

    for axis, group in by_axis.items():
        group.sort(key=lambda s: (s.fixed_mm, _extent(s)[0]))

        # GLOBAL GREEDY, not mutual-best. Requiring each face's favourite to
        # favour it back discarded 402 faces on AR-00: where A's best is B and
        # B's best is C, A was dropped even though a perfectly good mate was
        # still free. Every acceptable pairing is scored, the best are taken
        # first, and each face is used once.
        scored = []
        in_window: dict[str, int] = {}
        best_seen: dict[str, tuple] = {}
        for i, a in enumerate(group):
            for b in group[i + 1:]:
                gap = abs(b.fixed_mm - a.fixed_mm)
                if gap < MIN_SEPARATION_MM:
                    continue
                if gap > MAX_SEPARATION_MM:
                    break          # sorted by fixed: nothing further can fit
                in_window[a.segment_id] = in_window.get(a.segment_id, 0) + 1
                in_window[b.segment_id] = in_window.get(b.segment_id, 0) + 1
                overlap, ratio, _ = mate_score(a, b)
                for sid in (a.segment_id, b.segment_id):
                    prev = best_seen.get(sid)
                    if prev is None or overlap > prev[1]:
                        best_seen[sid] = (gap, overlap)
                if overlap < MIN_OVERLAP_MM or ratio < MIN_OVERLAP_RATIO:
                    continue
                # RANKED BY COMPANY: how much of the shorter face this mate
                # runs alongside. Distance only breaks a tie. Ranking by gap is
                # what let a 100 mm scrap beat a 2400 mm wall face.
                scored.append((-ratio, -overlap, gap, a, b))
        scored.sort(key=lambda t: (t[0], t[1], t[2]))

        caps_other = caps_by_axis.get("V" if axis == "H" else "H", ())
        for _, _, gap, a, b in scored:
            if a.segment_id in used or b.segment_id in used:
                continue
            used.add(a.segment_id)
            used.add(b.segment_id)
            overlap, ratio, _ = mate_score(a, b)

            a_lo, a_hi = _extent(a)
            b_lo, b_hi = _extent(b)
            # THE BAND SPANS THE UNION OF ITS FACES, not their intersection.
            # At an L corner the outer face runs past the inner one by a wall
            # thickness — the inner face stops early precisely because the
            # perpendicular wall occupies that corner. Taking the intersection
            # made every band stop short of every junction, so two
            # perpendicular bands never met and the graph stayed in pieces:
            # 184 termini and 7 bounded faces from 243 clean bands.
            lo, hi = min(a_lo, b_lo), max(a_hi, b_hi)
            overlap_lo, overlap_hi = max(a_lo, b_lo), min(a_hi, b_hi)
            centre = (a.fixed_mm + b.fixed_mm) / 2

            ev = [E_TWO_FACES]
            if ratio >= 0.8:
                ev.append(E_STRONG_OVERLAP)
            if wall_pen is not None and abs(a.stroke_width_pt - wall_pen) < 1e-6:
                ev.append(E_WALL_PEN)
            cap_ids = tuple(
                c.cap_id for c in caps_other
                if overlap_lo - 200 <= c.at_mm <= overlap_hi + 200
                and abs(min(c.span_mm) - min(a.fixed_mm, b.fixed_mm)) < 250)
            if cap_ids:
                ev.append(E_END_CAP)
            ratio_r = None
            if raster_support is not None:
                ratio_r = raster_support(axis, centre, overlap_lo, overlap_hi)
                if ratio_r is not None and ratio_r >= 0.6:
                    ev.append(E_RASTER_BAND)

            fams = {EVIDENCE_FAMILY[e] for e in ev}
            if len(fams) >= MIN_FAMILIES_FOR_VALIDATED:
                status = VALIDATED
                why = (f"two faces running together over {ratio * 100:.0f}% of "
                       f"their length, and {len(fams)} independent evidence "
                       "families agree")
            else:
                status = PROBABLE
                why = ("two faces pair cleanly but only one evidence family "
                       "supports the band")
            # THE UNION AUDIT. Each end beyond the both-faces interval is an
            # extension, and each one must say why it is there.
            exts = []
            for label, at, other_end in (("start", lo, overlap_lo),
                                         ("end", hi, overlap_hi)):
                run = abs(other_end - at)
                if run < 1.0:
                    continue
                if run <= MAX_JUNCTION_OVERHANG_MM:
                    reason = JUNCTION_OVERHANG
                    note = (f"{run:.0f} mm is within one wall thickness: the "
                            "longer face runs to the far side of the wall it "
                            "meets")
                elif cap_ids:
                    reason = END_CAP_SUPPORTED
                    note = "an end cap closes the band over this extension"
                else:
                    reason = UNRESOLVED_EXTENSION
                    note = (f"{run:.0f} mm of single-face extension with no "
                            "junction or cap to explain it. This band's extent "
                            "beyond the paired interval is NOT established "
                            "material")
                exts.append({"end": label, "length_mm": round(run, 1),
                             "extension_reason": reason, "note": note})

            n += 1
            bands.append(WallBandCandidate(
                wall_band_id=f"WB-{n:05d}",
                representation_type=DOUBLE_FACE_WALL, axis=axis,
                centreline_mm=centre, start_mm=lo, end_mm=hi,
                face_a_ids=(a.segment_id,), face_b_ids=(b.segment_id,),
                face_a_mm=a.fixed_mm, face_b_mm=b.fixed_mm,
                cap_ids=cap_ids,
                source_object_ids=(a.path_id, b.path_id),
                wall_face_separation_mm=gap,
                separation_basis="MEASURED_BETWEEN_TWO_DRAWN_FACES",
                supporting_evidence=tuple(ev),
                raster_support_ratio=ratio_r,
                face_a_intervals=((a_lo, a_hi),),
                face_b_intervals=((b_lo, b_hi),),
                both_faces_interval=(overlap_lo, overlap_hi),
                extensions=tuple(exts),
                validation_status=status, why=why))

        for a in group:
            if a.segment_id in used:
                continue
            seen = best_seen.get(a.segment_id)
            n_win = in_window.get(a.segment_id, 0)
            if n_win == 0:
                reason = NO_PARALLEL_FACE
            elif seen and seen[1] < MIN_OVERLAP_MM:
                reason = INSUFFICIENT_OVERLAP
            else:
                reason = FRAGMENTED_MATE
            rejections.append(FaceRejection(
                a.segment_id, axis, a.fixed_mm, a.length_mm, reason,
                seen[0] if seen else None, seen[1] if seen else None, n_win))
    return bands, rejections


def single_face_candidates(rejections, faces, *, caps=(),
                           raster_support=None) -> list[WallBandCandidate]:
    """Faces with no mate, kept as SINGLE_FACE candidates — never mirrored.

    DO NOT INVENT THE SECOND WALL FACE. Mirroring a lone face by an assumed
    thickness manufactures a wall the drawing does not contain, and every
    quantity downstream inherits it. A single face may join a topology
    hypothesis only when an INDEPENDENT source supports the missing side, and
    even then it stays PROBABLE.
    """
    by_id = {s.segment_id: s for s in faces}
    out: list[WallBandCandidate] = []
    n = 0
    for r in rejections:
        s = by_id.get(r.segment_id)
        if s is None or r.reason != NO_PARALLEL_FACE:
            continue
        lo, hi = _extent(s)
        ratio = (raster_support(s.axis, s.fixed_mm, lo, hi)
                 if raster_support else None)
        ev = []
        if ratio is not None and ratio >= 0.6:
            ev.append(E_RASTER_BAND)
        n += 1
        out.append(WallBandCandidate(
            wall_band_id=f"WBS-{n:05d}",
            representation_type=SINGLE_LINE_WALL, axis=s.axis,
            centreline_mm=s.fixed_mm, start_mm=lo, end_mm=hi,
            face_a_ids=(s.segment_id,), face_b_ids=(),
            face_a_mm=s.fixed_mm, face_b_mm=None,
            source_object_ids=(s.path_id,),
            wall_face_separation_mm=None,
            separation_basis="NOT_ESTABLISHED — only one face is drawn",
            supporting_evidence=tuple(ev),
            conflicting_evidence=("no second face exists in the drawing",),
            raster_support_ratio=ratio,
            validation_status=PROBABLE if ev else AMBIGUOUS,
            why=("one face only. Its centreline and thickness are NOT "
                 "established and were not assumed; mirroring it would "
                 "manufacture a wall the drawing does not contain")))
    return out


def summary(bands, rejections) -> dict:
    return {
        "bands": len(bands),
        "by_representation": dict(Counter(b.representation_type
                                          for b in bands)),
        "by_status": dict(Counter(b.validation_status for b in bands)),
        "total_length_m": round(sum(b.length_mm for b in bands) / 1000, 1),
        "separation_bands_mm": dict(Counter(
            ("<60" if (b.wall_face_separation_mm or 0) < 60 else
             "60-120" if b.wall_face_separation_mm < 120 else
             "120-180" if b.wall_face_separation_mm < 180 else
             "180-260" if b.wall_face_separation_mm < 260 else
             "260-400" if b.wall_face_separation_mm <= 400 else ">400")
            for b in bands if b.wall_face_separation_mm is not None)),
        "evidence_histogram": dict(Counter(
            e for b in bands for e in b.supporting_evidence)),
        "rejections": len(rejections),
        "rejection_reasons": dict(Counter(r.reason for r in rejections)),
    }


def audit_extensions(bands, portals=()) -> dict:
    """Does any band extension bridge a supported opening?

    THE HARD INVARIANT: a union extension may not cross a PORTAL_PROBABLE or
    PORTAL_VALIDATED interval unless it is represented as a host-wall opening
    with zero material present. A band that quietly spans a doorway puts
    blockwork and plaster where there is a door.
    """
    from collections import Counter
    crossing = []
    supported = [p for p in portals
                 if getattr(p, "status", "") in ("PORTAL_PROBABLE",
                                                 "PORTAL_VALIDATED")]
    for b in bands:
        for e in b.extensions:
            lo, hi = ((b.start_mm, b.both_faces_interval[0])
                      if e["end"] == "start"
                      else (b.both_faces_interval[1], b.end_mm)) \
                if b.both_faces_interval else (b.start_mm, b.end_mm)
            for p in supported:
                if p.axis != b.axis:
                    continue
                if abs(p.fixed_mm - b.centreline_mm) > 400:
                    continue
                if min(hi, max(p.start_mm, p.end_mm)) - max(
                        lo, min(p.start_mm, p.end_mm)) > 50:
                    crossing.append({
                        "wall_band_id": b.wall_band_id,
                        "portal_id": p.portal_id,
                        "extension_reason": e["extension_reason"],
                        "extension_mm": e["length_mm"],
                        "why": ("this band's single-face extension spans a "
                                "supported opening. It must be represented as "
                                "a host-wall opening with zero material "
                                "present, not as continuous wall")})
    return {
        "bands_with_extensions": sum(1 for b in bands if b.extensions),
        "extensions": sum(len(b.extensions) for b in bands),
        "by_reason": dict(Counter(e["extension_reason"] for b in bands
                                  for e in b.extensions)),
        "extensions_crossing_a_supported_portal": crossing,
        "invariant_holds": not crossing,
        "invariant": ("no union extension may cross a PORTAL_PROBABLE or "
                      "PORTAL_VALIDATED interval as continuous material"),
    }
