"""Measure spaces from authored CAD, through the SAME frozen enclosure.

Nothing here is a new measurement algorithm. The enclosure that measured
AR-00 — `SUPPORTED_LINE_ARRANGEMENT_FLOOD_FILL_V1`, freeze hash
`01ff128e7ffdab820805dce1` — is used unchanged, and this module only does
the two things a CAD source changes:

    WHERE TO FLOOD FROM   AR-00 needed a raster region to say "there is a
                          space here". A CAD drawing says it directly: a
                          room-name stamp is a block the architect placed
                          INSIDE the room it names. That is a better seed
                          than a pixel blob and it needs no rasterising.

    WHICH LINES SUPPORT    AR-00 had to guess wall faces from pen weight.
                          Here they come from the layers the source profile
                          proposed on geometric evidence, and each candidate
                          keeps its DWG handle.

Everything after that — the flood, the leak map, the corner construction,
the five scores — is the frozen algorithm, so a CAD result and a PDF result
are comparable rather than merely both present.

    NO RASTERISATION. NO PEN WEIGHT. NO PROJECT-1 CONSTANT.

THE DIMENSION CROSS-CHECK IS DONE AFTERWARDS, NEVER DURING

Geometry is measured first and compared second. The authored dimensions are
a separate observation with their own unit (see DIMLFAC), and a
disagreement raises an exception rather than adjusting anything — the same
rule that kept AR-00's printed dimensions from becoming a correction
factor.
"""

from __future__ import annotations

import hashlib
import math
from collections import Counter
from dataclasses import dataclass, field

from engine import space_enclosure as enc
from engine.boundary_match import VectorCandidate
from engine.space_objects import SRC_VECTOR_WALL_FACE

MEASURE = "CAD_SEEDED_FROZEN_ENCLOSURE_V1"

# How far from a room stamp to look for its walls. The enclosure's own
# neighbourhood margin governs the wall search; this is only the box the
# flood may not escape, and it is set from the largest room anybody builds
# in a villa rather than from this drawing. A space larger than this is
# reported as ESCAPED, which is the honest answer for an unbounded area.
SEED_NEIGHBOURHOOD_MM = 20000.0

# Dimension cross-check verdicts, and the tolerance for AGREE. Authored CAD
# coordinates are exact, so a real agreement is exact to within the rounding
# the dimension's own display precision imposes; 1 mm is far looser than
# that and still far tighter than any drafting error worth accepting.
AGREE_TOL_MM = 1.0
AGREE = "AGREE"
DISAGREE = "DISAGREE"
AMBIGUOUS = "AMBIGUOUS"
NOT_PRESENT = "NOT_PRESENT"


@dataclass(frozen=True)
class SpaceRow:
    """One measured space candidate, with its provenance and status."""

    space_id: str
    seed_mm: tuple
    label_observations: tuple
    label_block: str
    enclosure: object
    scores: dict
    openings: tuple = ()
    wall_thicknesses_mm: tuple = ()
    principal_dims_mm: tuple = ()
    dimension_checks: tuple = ()
    provenance: tuple = ()

    @property
    def is_complete(self) -> bool:
        return bool(self.enclosure and self.enclosure.is_complete)

    @property
    def geometry_status(self) -> str:
        if not self.enclosure:
            return "NO_ENCLOSURE_ATTEMPTED"
        if self.enclosure.is_complete:
            return "MEASUREMENT_COMPLETE"
        if self.enclosure.verdict == enc.ENCLOSED:
            return "ENCLOSED_WITH_UNSUPPORTED_BOUNDARY"
        return self.enclosure.verdict

    @property
    def identity_status(self) -> str:
        if not self.label_observations:
            return "IDENTITY_NOT_ESTABLISHED_NO_LABEL"
        if len(set(self.label_observations)) > 1:
            return "IDENTITY_AMBIGUOUS_MULTIPLE_LABELS"
        return "LABEL_OBSERVED_FROM_AUTHORED_TEXT"

    def record(self) -> dict:
        e = self.enclosure
        return {
            "space_id": self.space_id,
            "seed_mm": [round(v, 1) for v in self.seed_mm],
            "room_name_observations": list(self.label_observations),
            "label_block": self.label_block,
            "room_type": "NOT_ESTABLISHED",
            "geometry_status": self.geometry_status,
            "identity_status": self.identity_status,
            "clear_internal_polygon_wkt": (e.polygon_wkt if e else ""),
            "clear_area_m2": (None if not e or e.area_m2 is None
                              else round(e.area_m2, 3)),
            "clear_internal_perimeter_m": (
                None if not e or e.perimeter_m is None
                else round(e.perimeter_m, 3)),
            "principal_clear_dimensions_mm": [
                round(v, 1) for v in self.principal_dims_mm],
            "vector_boundary_support_pct": (e.vector_support_pct if e else 0.0),
            "openings": [dict(o) for o in self.openings],
            "wall_thickness_observations_mm": [
                round(v, 1) for v in self.wall_thicknesses_mm],
            "unsupported_boundary": [lk.record() for lk in (e.leaks if e
                                                            else ())],
            "dimension_cross_check": [dict(d) for d in self.dimension_checks],
            "cad_provenance": list(self.provenance),
            "geometry_hash": (e.geometry_hash if e else ""),
            "release_status": self._release()["status"],
            "blocker": self._release()["blocker"],
        }

    def _release(self) -> dict:
        if not self.is_complete:
            return {"status": "DIAGNOSTIC_ONLY",
                    "blocker": (self.enclosure.leaks[0].reason
                                if self.enclosure and self.enclosure.leaks
                                else self.geometry_status)}
        if self.identity_status.startswith("IDENTITY_NOT_ESTABLISHED"):
            return {"status": "DIAGNOSTIC_ONLY",
                    "blocker": "IDENTITY_NOT_ESTABLISHED"}
        bad = [d for d in self.dimension_checks
               if d.get("verdict") == DISAGREE]
        if bad:
            return {"status": "DIAGNOSTIC_ONLY",
                    "blocker": "AUTHORED_DIMENSION_DISAGREES_WITH_GEOMETRY"}
        return {"status": "RELEASE_ELIGIBLE_GEOMETRY", "blocker": ""}


@dataclass
class Report:
    rows: list = field(default_factory=list)
    candidates: int = 0
    wall_layers: tuple = ()
    candidate_lines: int = 0
    notes: dict = field(default_factory=dict)

    def counts(self) -> dict:
        complete = [r for r in self.rows if r.is_complete]
        partial = [r for r in self.rows
                   if r.enclosure and r.enclosure.verdict == enc.ENCLOSED
                   and not r.is_complete]
        unresolved = [r for r in self.rows if r not in complete
                      and r not in partial]
        ident = [r for r in self.rows
                 if r.identity_status == "LABEL_OBSERVED_FROM_AUTHORED_TEXT"]
        rel = [r for r in self.rows
               if r._release()["status"] == "RELEASE_ELIGIBLE_GEOMETRY"]
        checks = [d for r in self.rows for d in r.dimension_checks]
        return {
            "space_candidates": len(self.rows),
            "complete": len(complete),
            "partial": len(partial),
            "unresolved": len(unresolved),
            "identity_established": len(ident),
            "release_eligible": len(rel),
            "dimension_checks": len(checks),
            "dimension_agree": sum(1 for d in checks
                                   if d["verdict"] == AGREE),
            "dimension_disagree": sum(1 for d in checks
                                      if d["verdict"] == DISAGREE),
            "dimension_ambiguous": sum(1 for d in checks
                                       if d["verdict"] == AMBIGUOUS),
            "dimension_not_present": sum(1 for d in checks
                                         if d["verdict"] == NOT_PRESENT),
        }

    def baseline_hash(self) -> str:
        """One hash over every measured geometry and identity."""
        rows = sorted(
            f"{r.space_id}|{r.geometry_status}|{r.identity_status}|"
            f"{'' if not r.enclosure else r.enclosure.geometry_hash}|"
            f"{'' if not r.enclosure or r.enclosure.area_m2 is None else round(r.enclosure.area_m2, 4)}"
            for r in self.rows)
        return hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest()[:24]

    def record(self) -> dict:
        return {
            "measure": MEASURE,
            "enclosure_algorithm": enc.ALGORITHM,
            "enclosure_freeze_hash": enc.freeze_hash(),
            "wall_layers_used": list(self.wall_layers),
            "wall_face_candidates": self.candidate_lines,
            "seeds_from_room_name_blocks": self.candidates,
            "counts": self.counts(),
            "spaces": [r.record() for r in self.rows],
            "notes": dict(self.notes),
            "authority": (
                "CAD coordinates measured by the frozen enclosure. No "
                "raster, no pen weight, no project-1 scale constant"),
        }


def wall_candidates(normalized, wall_layers) -> list:
    """Axis-aligned segments on the proposed wall layers, as candidates.

    The candidate type is the one the enclosure already consumes, so the
    frozen algorithm sees exactly what it saw on AR-00 — only sourced from
    an authored layer instead of a pen weight.
    """
    keep = set(wall_layers)
    out = []
    for p in normalized.segments():
        if p.provenance.layer not in keep or p.axis not in ("H", "V"):
            continue
        if p.axis == "H":
            fixed, lo, hi = p.y1, min(p.x1, p.x2), max(p.x1, p.x2)
        else:
            fixed, lo, hi = p.x1, min(p.y1, p.y2), max(p.y1, p.y2)
        out.append(VectorCandidate(
            object_id=p.object_id, axis=p.axis, fixed_mm=fixed,
            start_mm=lo, end_mm=hi, source_type=SRC_VECTOR_WALL_FACE,
            validation_class="ESTABLISHED"))
    return out


def seeds_from_labels(normalized) -> list:
    """Every room-name stamp: a point the architect put inside a room.

    Only text that arrived through a BLOCK INSTANCE counts. Text drawn
    loose on the sheet is as likely to be a note, a street name or a level
    mark, and a seed in the wrong place measures the wrong space.
    """
    out = []
    for t in normalized.texts:
        if not t.provenance.block_path:
            continue
        out.append({
            "block": t.provenance.block_path[-1],
            "value": t.value,
            "x": t.x, "y": t.y,
            "object_id": t.provenance.object_id,
        })
    return out


def _principal(polygon_wkt: str) -> tuple:
    """The clear span across the space on each axis, from its own polygon."""
    if not polygon_wkt:
        return ()
    from shapely.wkt import loads

    poly = loads(polygon_wkt)
    x0, y0, x1, y1 = poly.bounds
    return (round(x1 - x0, 1), round(y1 - y0, 1))


def _dimension_checks(enclosure, dimensions, *, dimlfac: float) -> list:
    """Compare the measured span against authored dimensions nearby.

    Geometry is measured first. A dimension is matched to a span only when
    its extension lines bracket the same interval on the same axis, and the
    three values stay separate throughout.
    """
    if not enclosure or not enclosure.polygon_wkt:
        return []
    from shapely.wkt import loads

    poly = loads(enclosure.polygon_wkt)
    x0, y0, x1, y1 = poly.bounds
    spans = (("X", x1 - x0, x0, x1, (y0 + y1) / 2),
             ("Y", y1 - y0, y0, y1, (x0 + x1) / 2))
    out = []
    for axis, span, lo, hi, mid in spans:
        best, best_gap = None, None
        for d in dimensions:
            if axis == "X":
                if abs(d.y1 - d.y2) > AGREE_TOL_MM:
                    continue
                dlo, dhi = sorted((d.x1, d.x2))
                off = abs(d.y1 - mid)
            else:
                if abs(d.x1 - d.x2) > AGREE_TOL_MM:
                    continue
                dlo, dhi = sorted((d.y1, d.y2))
                off = abs(d.x1 - mid)
            # The dimension must bracket the same interval, and lie near
            # the space rather than anywhere on the sheet.
            if abs(dlo - lo) > 50.0 or abs(dhi - hi) > 50.0:
                continue
            if off > SEED_NEIGHBOURHOOD_MM:
                continue
            if best is None or off < best_gap:
                best, best_gap = d, off
        if best is None:
            out.append({
                "axis": axis,
                "GEOMETRY_MEASURED_VALUE_MM": round(span, 2),
                "DIMENSION_DISPLAY_VALUE": None,
                "DIMENSION_NORMALIZED_VALUE_MM": None,
                "residual_mm": None, "verdict": NOT_PRESENT,
                "why": "no authored dimension brackets this span"})
            continue
        norm = best.normalized_mm
        if norm is None or best.is_overridden:
            verdict, resid = AMBIGUOUS, None
            why = ("the author typed over the measurement, so the printed "
                   "text is not a reading of the geometry")
        else:
            resid = span - norm
            verdict = AGREE if abs(resid) <= AGREE_TOL_MM else DISAGREE
            why = ("authored CAD coordinates are exact, so agreement is "
                   "expected to within display rounding")
        out.append({
            "axis": axis,
            "GEOMETRY_MEASURED_VALUE_MM": round(span, 2),
            "DIMENSION_DISPLAY_VALUE": best.display_value,
            "DIMENSION_NORMALIZED_VALUE_MM": (None if norm is None
                                              else round(norm, 2)),
            "dimlfac_applied": dimlfac,
            "residual_mm": (None if resid is None else round(resid, 3)),
            "verdict": verdict, "why": why,
            "dimension_provenance": best.provenance.object_id,
            "never": "these values are never averaged"})
    return out


def _thicknesses(enclosure, candidates) -> tuple:
    """Separations between the enclosure's edges and the next parallel face."""
    if not enclosure or not enclosure.edges:
        return ()
    out = Counter()
    for axis, fixed, lo, hi, _oid, _src in enclosure.edges:
        for c in candidates:
            if c.axis != axis:
                continue
            gap = abs(c.fixed_mm - fixed)
            if gap < 1.0 or gap > 600.0:
                continue
            if min(hi, c.end_mm) - max(lo, c.start_mm) < 500.0:
                continue
            out[round(gap, 1)] += 1
    return tuple(t for t, _ in out.most_common(6))


def measure(normalized, profile, *, region=None) -> Report:
    """Seed from room stamps, flood the authored lines, then cross-check."""
    wall_layers = tuple(profile.wall_like_layers())
    cands = wall_candidates(normalized, wall_layers)
    seeds = seeds_from_labels(normalized)
    if region is not None:
        seeds = [s for s in seeds if region.contains(s["x"], s["y"])]

    rep = Report(candidates=len(seeds), wall_layers=wall_layers,
                 candidate_lines=len(cands))

    # Group stamps that sit within one room: a block carries its English and
    # its Arabic label as two text entities at nearby points, and they are
    # one room, not two.
    groups: list = []
    for s in sorted(seeds, key=lambda r: (r["x"], r["y"])):
        for g in groups:
            if (abs(g["x"] - s["x"]) < 2000.0
                    and abs(g["y"] - s["y"]) < 2000.0
                    and g["block"] == s["block"]):
                g["labels"].append(s["value"])
                g["ids"].append(s["object_id"])
                break
        else:
            groups.append({"x": s["x"], "y": s["y"], "block": s["block"],
                           "labels": [s["value"]], "ids": [s["object_id"]]})

    for n, g in enumerate(sorted(groups, key=lambda r: (-r["y"], r["x"])), 1):
        sid = f"CADSP-{n:03d}"
        box = (g["x"] - SEED_NEIGHBOURHOOD_MM, g["y"] - SEED_NEIGHBOURHOOD_MM,
               g["x"] + SEED_NEIGHBOURHOOD_MM, g["y"] + SEED_NEIGHBOURHOOD_MM)
        e = enc.enclose(sid, (g["x"], g["y"]), cands, extent=box,
                        enclosure_id=f"LSE-{sid}")
        scores = enc.score(e, seed_mm=(g["x"], g["y"]))
        checks = _dimension_checks(e, normalized.dimensions,
                                   dimlfac=normalized.dimlfac)
        rep.rows.append(SpaceRow(
            space_id=sid, seed_mm=(g["x"], g["y"]),
            label_observations=tuple(g["labels"]), label_block=g["block"],
            enclosure=e, scores=scores,
            principal_dims_mm=_principal(e.polygon_wkt),
            wall_thicknesses_mm=_thicknesses(e, cands),
            dimension_checks=tuple(checks),
            provenance=tuple(g["ids"])))

    rep.notes["seeding"] = (
        "every seed is a room-name block the architect placed inside the "
        "room it names. Loose text was not used: a street name or a level "
        "mark would seed the wrong space")
    rep.notes["wall_layers_came_from"] = (
        "the source profile's geometric test, not from any layer name")
    return rep
