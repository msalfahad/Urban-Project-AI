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

from engine import boundary_authority as authority
from engine import enclosure_role as roles
from engine import identity_reconcile as ident
from engine import semantic_seed as seeds_mod
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
    enclosure_role: str = roles.UNRESOLVED
    role_evidence: tuple = ()
    identity: object = None
    boundary_roles: tuple = ()
    closed_on_envelope: bool = False

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
    def physical_space_status(self) -> str:
        """Is this a physical space — separately from what it is called.

        §10: geometry, physical-space validity, identity and release are
        four different questions. A room whose name nobody can read is
        still a room.
        """
        if not self.is_complete:
            return "PHYSICAL_SPACE_NOT_ESTABLISHED"
        if self.enclosure_role != roles.RELEASABLE_ROLE:
            return f"NOT_A_PHYSICAL_ROOM_ROLE_IS_{self.enclosure_role}"
        return "PHYSICAL_SPACE_VALIDATED"

    @property
    def identity_status(self) -> str:
        """What it is CALLED. Never a precondition for the geometry."""
        if self.identity is None:
            return ident.IDENTITY_UNKNOWN
        return self.identity.identity_status

    @property
    def normalized_identity(self) -> str:
        return "" if self.identity is None else \
            self.identity.normalized_identity

    def record(self) -> dict:
        e = self.enclosure
        return {
            "space_id": self.space_id,
            "seed_mm": [round(v, 1) for v in self.seed_mm],
            "room_name_observations": list(self.label_observations),
            "label_block": self.label_block,
            "room_type": (self.normalized_identity or "NOT_ESTABLISHED"),
            "geometry_status": self.geometry_status,
            "physical_space_status": self.physical_space_status,
            "identity_status": self.identity_status,
            "normalized_identity": self.normalized_identity,
            "identity_evidence": (list(self.identity.evidence)
                                  if self.identity else []),
            "independent_identity_statements": (
                self.identity.supporting_observations
                if self.identity else 0),
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
            "enclosure_role": self.enclosure_role,
            "enclosure_role_evidence": list(self.role_evidence),
            "closed_using_building_envelope": self.closed_on_envelope,
            "boundary_segments": [dict(b) for b in self.boundary_roles],
            "boundary_segment_count": len(self.boundary_roles),
            "geometry_hash": (e.geometry_hash if e else ""),
            "release_status": self._release()["status"],
            "blocker": self._release()["blocker"],
        }

    def _release(self) -> dict:
        """Every condition, with the role test that round 1 did not have.

        Round 1 released a 443 m2 plot as a washroom because it asked only
        about completeness, identity and dimensions. All three were
        satisfied. The question it never asked was WHAT KIND OF ENCLOSURE
        this is, and that is now the first structural gate after geometry.

        FALSE RELEASE IS WORSE THAN ZERO RELEASE, so every branch below
        fails closed.
        """
        if not self.is_complete:
            return {"status": "DIAGNOSTIC_ONLY",
                    "blocker": (self.enclosure.leaks[0].reason
                                if self.enclosure and self.enclosure.leaks
                                else self.geometry_status)}
        if self.enclosure_role != roles.RELEASABLE_ROLE:
            return {"status": "DIAGNOSTIC_ONLY",
                    "blocker": f"ENCLOSURE_ROLE_IS_{self.enclosure_role}"}
        # Identity must be ESTABLISHED or explicitly UNKNOWN. Only a
        # CONTRADICTION blocks — round 2 blocked on "more than one string",
        # which stopped every bilingual stamp on the drawing.
        if self.identity_status == ident.IDENTITY_CONFLICT:
            return {"status": "DIAGNOSTIC_ONLY",
                    "blocker": "INCOMPATIBLE_SEMANTIC_OBSERVATIONS"}
        if not self.enclosure or not self.enclosure.edges:
            return {"status": "DIAGNOSTIC_ONLY",
                    "blocker": "BOUNDARY_PROVENANCE_NOT_SUPPORTED"}
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
    semantic: object = None
    roles: object = None
    authority: object = None
    identity: object = None
    all_candidate_lines: int = 0
    notes: dict = field(default_factory=dict)

    def counts(self) -> dict:
        complete = [r for r in self.rows if r.is_complete]
        partial = [r for r in self.rows
                   if r.enclosure and r.enclosure.verdict == enc.ENCLOSED
                   and not r.is_complete]
        unresolved = [r for r in self.rows if r not in complete
                      and r not in partial]
        established = [r for r in self.rows
                       if r.identity_status == ident.IDENTITY_ESTABLISHED]
        rel = [r for r in self.rows
               if r._release()["status"] == "RELEASE_ELIGIBLE_GEOMETRY"]
        checks = [d for r in self.rows for d in r.dimension_checks]
        return {
            "space_candidates": len(self.rows),
            "complete": len(complete),
            "partial": len(partial),
            "unresolved": len(unresolved),
            "identity_established": len(established),
            "release_eligible": len(rel),
            "by_enclosure_role": dict(Counter(
                r.enclosure_role for r in self.rows).most_common()),
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
            "wall_like_candidates": self.all_candidate_lines,
            "room_boundary_eligible_candidates": self.candidate_lines,
            "boundary_authority": (self.authority.record()
                                   if self.authority else None),
            "identity_reconciliation": (self.identity.record()
                                        if self.identity else None),
            "seeds_from_room_name_blocks": self.candidates,
            "counts": self.counts(),
            "semantic_seeds": (self.semantic.record() if self.semantic
                               else None),
            "enclosure_roles": (self.roles.record() if self.roles else None),
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


def seeds_from_labels(normalized, *, semantic=None) -> list:
    """Every qualified room-name stamp, and nothing else.

    Round 1 used "text carried by a placed block", and 27 of 48 candidates
    were not rooms — a street name, a neighbour, a view and a level mark are
    all text carried by placed blocks. The semantic classifier is now the
    gate, and only ROOM_LIKE observations pass.

    A label says WHERE a space might be and WHAT it might be called. It
    never says where that space's boundary runs.
    """
    rep = semantic if semantic is not None else seeds_mod.classify(
        normalized.texts)
    by_id = {t.provenance.object_id: t for t in normalized.texts}
    out = []
    for o in rep.seeds():
        src = by_id.get(o.provenance[0]) if o.provenance else None
        if src is None or not src.provenance.block_path:
            continue
        out.append({
            "block": src.provenance.block_path[-1],
            "value": o.text, "x": o.x, "y": o.y,
            "object_id": src.provenance.object_id,
        })
    return out


def _boundary_segments(enclosure, role_of) -> tuple:
    """Every side of the measured polygon, with its provenance and role.

    §14 asks for this per segment: which CAD entity drew it, what role the
    authority gave it, and whether material stands there or the boundary is
    virtual (a portal closing a doorway without pretending material exists).
    """
    if not enclosure or not enclosure.edges:
        return ()
    out = []
    for axis, fixed, lo, hi, object_id, src in enclosure.edges:
        out.append({
            "axis": axis, "fixed_mm": round(fixed, 2),
            "interval_mm": [round(lo, 2), round(hi, 2)],
            "length_mm": round(abs(hi - lo), 1),
            "cad_provenance": object_id,
            "boundary_roles": list(role_of.get(object_id, ())),
            "material": ("MATERIAL_PRESENT" if object_id else
                         "VIRTUAL_NO_MATERIAL"),
            "source_type": src,
        })
    return tuple(out)


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


def measure(normalized, profile, *, region=None, semantic=None) -> Report:
    """Classify, seed, flood, classify the role, then cross-check.

    The order matters and is the correction this round makes. Round 1 went
    seed -> flood -> release. It now goes:

        CLASSIFY THE OBSERVATION   is this string even about a space?
        SEED                       only from what survives
        FLOOD                      the frozen enclosure, unchanged
        CLASSIFY THE ENCLOSURE     what KIND of thing did we just close?
        RELEASE                    only a PHYSICAL_ROOM_CANDIDATE

    Every stage can only narrow what the next one sees.
    """
    wall_layers = tuple(profile.wall_like_layers())
    all_cands = wall_candidates(normalized, wall_layers)
    sem = semantic if semantic is not None else seeds_mod.classify(
        normalized.texts)
    seeds = seeds_from_labels(normalized, semantic=sem)
    if region is not None:
        seeds = [s for s in seeds if region.contains(s["x"], s["y"])]

    # ROUND 3's CORRECTION. A paired-face test proves a line is drawn like a
    # wall; it cannot tell a site boundary from a partition. The authority
    # stage measures how many walls lie between each side of a band and the
    # outside, and only bands reaching the depth at which rooms live may
    # close one. §6: a site line never completes a room polygon.
    auth = authority.classify(all_cands, sem.seeds())
    eligible_ids = {b.band_id for b in auth.eligible()}
    cands = [c for c in all_cands if c.object_id in eligible_ids]
    role_of = {b.band_id: b.roles for b in auth.bands}

    # §7's SMALLEST SUPPORTED ENCLOSING CYCLE, done by enclosing twice.
    #
    # The first pass offers only bands that divide the fabric. If a seed
    # closes on those, that is the nearest enclosing cycle and no outer
    # boundary was needed — which is also §6 satisfied, because a site line
    # can never appear in an enclosure that did not use one.
    #
    # Only when the inner pass fails is the outermost boundary offered, so
    # a corner room bounded on two sides by external wall still measures
    # (§5). "Smallest" here is topological, not an area comparison: it is
    # the nearest cycle the drawn partitions support.
    inner_cands = [c for c in cands
                   if authority.INTERNAL_PARTITION in role_of.get(
                       c.object_id, ())]

    rep = Report(candidates=len(seeds), wall_layers=wall_layers,
                 candidate_lines=len(cands))
    rep.semantic = sem
    rep.authority = auth
    rep.all_candidate_lines = len(all_cands)

    # Reconcile the labels at each place into ONE identity. Round 2 counted
    # strings and called every bilingual stamp a conflict; SALOON and صالون
    # are one identity stated twice.
    by_id = {t.provenance.object_id: t for t in normalized.texts}
    seed_texts = [by_id[s["object_id"]] for s in seeds
                  if s["object_id"] in by_id]
    id_rep = ident.reconcile(ident.observations_from(seed_texts))
    rep.identity = id_rep

    groups = [{"x": g.x, "y": g.y,
               "block": (g.observations[0].carrier_block
                         if g.observations else ""),
               "labels": [o.text for o in g.observations],
               "ids": [o.observation_id for o in g.observations],
               "identity": g}
              for g in id_rep.groups]

    for n, g in enumerate(sorted(groups, key=lambda r: (-r["y"], r["x"])), 1):
        sid = f"CADSP-{n:03d}"
        box = (g["x"] - SEED_NEIGHBOURHOOD_MM, g["y"] - SEED_NEIGHBOURHOOD_MM,
               g["x"] + SEED_NEIGHBOURHOOD_MM, g["y"] + SEED_NEIGHBOURHOOD_MM)
        e = enc.enclose(sid, (g["x"], g["y"]), inner_cands, extent=box,
                        enclosure_id=f"LSE-{sid}")
        used_envelope = False
        if not e.is_complete:
            wider = enc.enclose(sid, (g["x"], g["y"]), cands, extent=box,
                                enclosure_id=f"LSE-{sid}")
            if wider.is_complete:
                e, used_envelope = wider, True
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
            provenance=tuple(g["ids"]),
            identity=g.get("identity"),
            boundary_roles=_boundary_segments(e, role_of),
            closed_on_envelope=used_envelope))

    # WHAT KIND OF ENCLOSURE DID WE JUST CLOSE? Asked of every enclosure at
    # once, because the answer is containment and containment is a property
    # of the SET, not of one polygon.
    # Counted over RECONCILED IDENTITIES, not raw labels. A bilingual stamp
    # is two strings and one room; counting the strings made an ordinary
    # room look like two observations in one space, which the role
    # classifier then read as open plan and refused to call a room.
    role_rep = roles.classify(
        [(r.space_id, r.enclosure.polygon_wkt if r.enclosure else "")
         for r in rep.rows],
        id_rep.groups, cands)
    verdicts = {v.enclosure_id: v for v in role_rep.verdicts}
    rep.rows = [
        SpaceRow(**{**r.__dict__,
                    "enclosure_role": (verdicts[r.space_id].role
                                       if r.space_id in verdicts
                                       else roles.UNRESOLVED),
                    "role_evidence": (verdicts[r.space_id].evidence
                                      if r.space_id in verdicts else ())})
        for r in rep.rows]
    rep.roles = role_rep

    rep.notes["seeding"] = (
        "every seed is a room-name block the architect placed inside the "
        "room it names. Loose text was not used: a street name or a level "
        "mark would seed the wrong space")
    rep.notes["wall_layers_came_from"] = (
        "the source profile's geometric test, not from any layer name")
    return rep
