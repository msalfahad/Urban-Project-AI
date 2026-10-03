"""E79 — sample the single-line population blind, and report its evidence.

434.8 m is a large claim to rest on one classifier. Either the drawing uses
a single-line wall convention, or a proxy has overreached — and the
classifier cannot answer that about itself.

So a DETERMINISTIC sample is drawn across strata that would expose an
overreach in different ways, and each member is reported with its raw
evidence rather than a verdict. Determinism matters twice: the sample is
reproducible, and it cannot be re-drawn until it looks better.

    BLIND means the manual expected-wall list is NOT consulted, here or
    anywhere in the sampling or the evidence. Classifying a sample against
    the answers would measure agreement with a list, not whether the
    convention is real.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

LONG = "LONG_RUN"
MEDIUM = "MEDIUM_RUN"
SHORT = "SHORT_RUN"
JUNCTION_CONNECTED = "JUNCTION_CONNECTED"
ISOLATED = "ISOLATED"
NEAR_ROOM_BOUNDARY = "NEAR_A_LABELLED_ROOM_BOUNDARY"

STRATA = (LONG, MEDIUM, SHORT, JUNCTION_CONNECTED, ISOLATED,
          NEAR_ROOM_BOUNDARY)

LONG_MM = 3000.0
SHORT_MM = 800.0
# Within this of an accepted band's end, a stroke is junction-connected.
JUNCTION_REACH_MM = 200.0
# Within this of a labelled region's centroid-to-centroid midline, a stroke
# sits where a separation between two named rooms would be.
ROOM_REACH_MM = 1500.0

PER_STRATUM = 3


@dataclass(frozen=True)
class SampledStroke:
    """One member of the sample, with what is known about it and no verdict."""

    stroke_id: str
    stratum: str
    axis: str
    fixed_mm: float
    start_mm: float
    end_mm: float
    stroke_class: str
    stroke_width_pt: float | None = None
    raster_support: float | None = None
    collinear_neighbours: int = 0
    nearest_band_id: str = ""
    nearest_band_gap_mm: float | None = None
    junction_band_ids: tuple[str, ...] = ()
    continuity_gaps: int = 0
    parallel_face_within_mm: float | None = None
    fixture_conflict: bool = False
    labelled_rooms_either_side: tuple[str, ...] = ()
    evidence: tuple[str, ...] = ()

    @property
    def length_mm(self) -> float:
        return self.end_mm - self.start_mm

    def record(self) -> dict:
        return {
            "stroke_id": self.stroke_id, "stratum": self.stratum,
            "axis": self.axis, "fixed_mm": round(self.fixed_mm, 1),
            "length_mm": round(self.length_mm, 1),
            "stroke_class": self.stroke_class,
            "pen_width_pt": self.stroke_width_pt,
            "raster_wall_support": self.raster_support,
            "collinear_neighbours_on_this_line": self.collinear_neighbours,
            "nearest_accepted_band": self.nearest_band_id,
            "nearest_accepted_band_gap_mm": (
                None if self.nearest_band_gap_mm is None
                else round(self.nearest_band_gap_mm, 1)),
            "junction_connected_to": list(self.junction_band_ids),
            "parallel_face_within_mm": (
                None if self.parallel_face_within_mm is None
                else round(self.parallel_face_within_mm, 1)),
            "fixture_or_symbol_conflict": self.fixture_conflict,
            "labelled_rooms_either_side": list(
                self.labelled_rooms_either_side),
            "evidence": list(self.evidence),
            "verdict": "NOT_ADJUDICATED_HERE",
            "why_no_verdict": (
                "this row reports what is known about the stroke. Deciding "
                "whether it is a wall from these fields is a separate act, "
                "and doing it here against a manual list would measure "
                "agreement with the list rather than whether the drawing "
                "uses a single-line convention"),
        }


@dataclass
class Sample:
    population: str = ""
    population_strokes: int = 0
    population_length_m: float = 0.0
    seed: str = ""
    members: list = field(default_factory=list)
    strata_sizes: dict = field(default_factory=dict)
    notes: dict = field(default_factory=dict)

    def record(self) -> dict:
        from collections import Counter
        return {
            "population": self.population,
            "population_strokes": self.population_strokes,
            "population_length_m": round(self.population_length_m, 1),
            "sampling": "DETERMINISTIC_STRATIFIED",
            "seed": self.seed,
            "blind": True,
            "what_blind_means": (
                "the manual expected-wall list is not consulted in the "
                "sampling or in any evidence field. Classifying a sample "
                "against the answers would measure agreement with a list"),
            "strata": list(STRATA),
            "stratum_population_sizes": dict(self.strata_sizes),
            "per_stratum_sampled": PER_STRATUM,
            "sampled": len(self.members),
            "by_stratum": dict(Counter(m.stratum for m in self.members)),
            "members": [m.record() for m in self.members],
            "the_question": (
                "does 434.8 m represent a real single-line wall convention, "
                "or has a proxy overreached? The evidence fields are here "
                "to answer that; the classifier cannot answer it about "
                "itself"),
            "notes": dict(self.notes),
        }


def _key(stroke_id: str, seed: str) -> str:
    return hashlib.sha256(f"{seed}/{stroke_id}".encode()).hexdigest()


def _stratum(s, junction_ids, near_rooms) -> str:
    """One stratum each, in a fixed order so membership is reproducible."""
    if near_rooms:
        return NEAR_ROOM_BOUNDARY
    if junction_ids:
        return JUNCTION_CONNECTED
    length = s.end_mm - s.start_mm
    if length >= LONG_MM:
        return LONG
    if length <= SHORT_MM:
        return SHORT
    if s.collinear_neighbours == 0 and (s.nearest_band_gap_mm is None
                                        or s.nearest_band_gap_mm > 1000.0):
        return ISOLATED
    return MEDIUM


def draw(strokes, *, population_class, bands=(), faces=(), regions=None,
         seed: str = "AR-00", per_stratum: int = PER_STRATUM) -> Sample:
    """A reproducible stratified sample of one stroke class, with evidence."""
    pop = [s for s in strokes if s.stroke_class == population_class]
    sample = Sample(
        population=population_class, population_strokes=len(pop),
        population_length_m=sum(s.length_mm for s in pop) / 1000, seed=seed)

    band_ends: dict = {}
    for b in bands:
        band_ends.setdefault(b.axis, []).append(
            (b.wall_band_id, min(b.start_mm, b.end_mm),
             max(b.start_mm, b.end_mm), b.centreline_mm))

    face_lines: dict = {}
    for f in faces:
        fid = getattr(f, "segment_id", "")
        face_lines.setdefault(f.axis, []).append((fid, f.fixed_mm,
                                                  f.start_mm, f.end_mm))

    rooms = [(r["space_id"], r["centroid_mm"]) for r in
             (regions or {}).values() if r.get("space_id")]

    staged = []
    for s in pop:
        junction = tuple(sorted(
            bid for bid, blo, bhi, bc in band_ends.get(s.axis, ())
            if abs(bc - s.fixed_mm) <= JUNCTION_REACH_MM
            and (abs(bhi - s.start_mm) <= JUNCTION_REACH_MM
                 or abs(blo - s.end_mm) <= JUNCTION_REACH_MM)))
        near_rooms = tuple(sorted(
            sid for sid, (cx, cy) in rooms
            if abs((cy if s.axis == "H" else cx) - s.fixed_mm)
            <= ROOM_REACH_MM
            and s.start_mm <= (cx if s.axis == "H" else cy) <= s.end_mm))
        # Nearest PARALLEL face on the same axis but a different line: the
        # absence of one is what makes a stroke single-line at all.
        par = None
        for fid, ffixed, flo, fhi in face_lines.get(s.axis, ()):
            if fid == s.stroke_id:
                continue
            d = abs(ffixed - s.fixed_mm)
            if d < 1e-6 or fhi < s.start_mm or flo > s.end_mm:
                continue
            if par is None or d < par:
                par = d
        staged.append((s, junction, near_rooms[:4], par))

    by_stratum: dict = {}
    for s, junction, near_rooms, par in staged:
        st = _stratum(s, junction, near_rooms)
        by_stratum.setdefault(st, []).append((s, junction, near_rooms, par))
    sample.strata_sizes = {k: len(v) for k, v in sorted(by_stratum.items())}

    for st in STRATA:
        members = sorted(by_stratum.get(st, ()),
                         key=lambda t: _key(t[0].stroke_id, seed))
        for s, junction, near_rooms, par in members[:per_stratum]:
            ev = list(s.evidence)
            if par is not None and par <= 1000.0:
                ev.append(f"A_PARALLEL_FACE_LIES_{par:.0f}_MM_AWAY")
            else:
                ev.append("NO_PARALLEL_FACE_ANYWHERE_ALONG_THIS_RUN")
            sample.members.append(SampledStroke(
                stroke_id=s.stroke_id, stratum=st, axis=s.axis,
                fixed_mm=s.fixed_mm, start_mm=s.start_mm, end_mm=s.end_mm,
                stroke_class=s.stroke_class,
                stroke_width_pt=s.stroke_width_pt,
                raster_support=s.raster_support,
                collinear_neighbours=s.collinear_neighbours,
                nearest_band_id=s.nearest_band_id,
                nearest_band_gap_mm=s.nearest_band_gap_mm,
                junction_band_ids=junction,
                parallel_face_within_mm=par,
                labelled_rooms_either_side=tuple(near_rooms),
                evidence=tuple(ev)))
    sample.notes["strata_with_no_members"] = [
        st for st in STRATA if not by_stratum.get(st)]
    return sample
