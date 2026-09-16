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
from engine import cad_openings as openings_mod
from engine import drawing_region as dregion
from engine import enclosure_role as roles
from engine import face_subdivision as fsub
from engine import junction_recovery as jrec
from engine import partition_continuity as pcont
from engine import physical_wall as pwall
from engine import identity_reconcile as ident
from engine import portal_match as pmatch
from engine import room_partition_graph as rpg
from engine import semantic_seed as seeds_mod
from engine import space_enclosure as enc
from engine import space_topologies as topo
from engine.boundary_match import VectorCandidate
from engine.space_objects import SRC_VECTOR_WALL_FACE

MEASURE = "CAD_REGION_LOCAL_CONTINUITY_RECOVERED_MEASUREMENT_V1"

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
# §17. A span that is not a SIDE of the polygon cannot be cross-checked
# against a dimension at all, and calling that NOT_PRESENT overstated what
# had been looked for. An L-shaped room has no single edge spanning its
# bounding box, so no authored dimension could bracket one.
NOT_APPLICABLE = "NOT_APPLICABLE"


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
    region_id: str = ""
    zones: tuple = ()
    boundary_openings: tuple = ()
    relations: tuple = ()
    quantities: dict = field(default_factory=dict)
    recovered_boundary: tuple = ()

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
        if self.enclosure_role == roles.RELEASABLE_ROLE:
            return "PHYSICAL_SPACE_VALIDATED"
        if self.enclosure_role == roles.VOID_OR_SHAFT:
            # §11. A bounded face with no readable label is still a bounded
            # face. It may not RELEASE as a room — round 2's safety is
            # untouched — but refusing to admit it exists was the thing
            # that made measurement hostage to the text layer.
            return "PHYSICAL_SPACE_VALIDATED_IDENTITY_UNKNOWN"
        return f"NOT_A_PHYSICAL_ROOM_ROLE_IS_{self.enclosure_role}"

    @property
    def is_physical_space(self) -> bool:
        return self.physical_space_status.startswith(
            "PHYSICAL_SPACE_VALIDATED")

    @property
    def weakest_topology_authority(self) -> str:
        """The weakest authority anything on this boundary carries.

        A polygon is only as releasable as the flimsiest thing holding it
        shut. A drawn wall carries VALIDATED; a recovered span carries what
        `partition_continuity` gave it and no more.
        """
        if any(r["TOPOLOGY_AUTHORITY"] == pcont.TOPOLOGY_SUPPORTED
               for r in self.recovered_boundary):
            return pcont.TOPOLOGY_SUPPORTED
        return pcont.TOPOLOGY_VALIDATED

    @property
    def material_authority(self) -> str:
        """Whether blockwork may be taken from this room's own boundary."""
        if any(r["MATERIAL_AUTHORITY"] != pcont.MATERIAL_ESTABLISHED
               for r in self.recovered_boundary):
            return pcont.MATERIAL_CANDIDATE
        return pcont.MATERIAL_ESTABLISHED

    @property
    def unresolved_relations(self) -> tuple:
        """Openings on this boundary that settle neither one room nor two."""
        return tuple(
            r for r in self.relations
            if r.get("ROOM_PARTITION_RELATION") == topo.REL_UNRESOLVED)

    @property
    def identity_status(self) -> str:
        """What it is CALLED. Never a precondition for the geometry."""
        if len(self.zones) > 1:
            # §8. Several identities inside one face is not a conflict and
            # not an unknown — it is one space used for several things.
            return "IDENTITY_IS_SEVERAL_FUNCTIONAL_ZONES"
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
            "drawing_region_id": self.region_id,
            "functional_zones": [z.record() for z in self.zones],
            "functional_zone_count": len(self.zones),
            "boundary_openings": [dict(o) for o in self.boundary_openings],
            "room_partition_relations": [dict(r) for r in self.relations],
            "unresolved_room_partition_relations": len(
                self.unresolved_relations),
            "quantity_ontology": dict(self.quantities),
            "recovered_boundary_spans": [dict(r)
                                         for r in self.recovered_boundary],
            "TOPOLOGY_AUTHORITY": self.weakest_topology_authority,
            "MATERIAL_AUTHORITY": self.material_authority,
            "material_boq_status": (
                "MATERIAL_RELEASE_BLOCKED" if self.material_authority
                != pcont.MATERIAL_ESTABLISHED else "MATERIAL_MEASURABLE"),
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
        # ROUND 4. An opening on this boundary that nobody could match to
        # a host, and an opening that settles neither one room nor two,
        # both stop the release. Neither invents anything: the polygon is
        # measured and reported, it simply may not be quantified from.
        amb = [o for o in self.boundary_openings
               if o.get("host_status") not in ("", "HOST_ESTABLISHED")]
        if amb:
            return {"status": "DIAGNOSTIC_ONLY",
                    "blocker": amb[0].get("host_status",
                                          "PORTAL_HOST_AMBIGUOUS")}
        if self.unresolved_relations:
            return {"status": "DIAGNOSTIC_ONLY",
                    "blocker": topo.REL_UNRESOLVED}
        # ROUND 5, §18. A recovered span may be strong enough to SUBDIVIDE
        # and not strong enough to RELEASE. Material authority is tracked
        # separately and blocks the BOQ, not the geometry.
        if self.weakest_topology_authority != pcont.TOPOLOGY_VALIDATED:
            return {"status": "DIAGNOSTIC_ONLY",
                    "blocker": "RECOVERED_SPAN_TOPOLOGY_AUTHORITY_IS_"
                               + self.weakest_topology_authority}
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
    regions: object = None
    openings: object = None
    matches: object = None
    graphs: list = field(default_factory=list)
    walls: list = field(default_factory=list)
    continuity: list = field(default_factory=list)
    junctions: list = field(default_factory=list)
    subdivisions: list = field(default_factory=list)
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
            "identity_unknown": sum(
                1 for r in self.rows
                if r.identity_status == ident.IDENTITY_UNKNOWN),
            "physical_spaces_validated": sum(
                1 for r in self.rows if r.is_physical_space),
            "validated_geometry_unknown_identity": sum(
                1 for r in self.rows if r.is_physical_space
                and r.identity_status == ident.IDENTITY_UNKNOWN),
            "functional_zone_groups": sum(1 for r in self.rows
                                          if len(r.zones) > 1),
            "spaces_with_an_unresolved_relation": sum(
                1 for r in self.rows if r.unresolved_relations),
            "spaces_closed_with_a_recovered_span": sum(
                1 for r in self.rows if r.recovered_boundary),
            "spaces_with_material_authority": sum(
                1 for r in self.rows
                if r.material_authority == pcont.MATERIAL_ESTABLISHED),
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
            "dimension_not_applicable": sum(
                1 for d in checks if d["verdict"] == NOT_APPLICABLE),
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
            "drawing_regions": (self.regions.record()
                                if self.regions else None),
            "openings": (self.openings.record() if self.openings else None),
            "portal_matching": (self.matches.record()
                                if self.matches else None),
            "room_partition_graphs": [g.record() for g in self.graphs],
            "physical_walls": [w.record() for w in self.walls],
            "partition_continuity": [c.record() for c in self.continuity],
            "junction_recovery": [j.record() for j in self.junctions],
            "face_subdivision": [d.record() for d in self.subdivisions],
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


IDENTIFYING_CLASSES = (seeds_mod.ROOM_LIKE, seeds_mod.ZONE_LIKE)


def seeds_from_labels(normalized, *, semantic=None, classes=None) -> list:
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
    want = tuple(classes) if classes else (seeds_mod.ROOM_LIKE,)
    by_id = {t.provenance.object_id: t for t in normalized.texts}
    out = []
    for o in [x for x in rep.observations if x.semantic_class in want]:
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
            "material": ("VIRTUAL_NO_MATERIAL"
                         if (not object_id
                             or object_id.startswith("PORTAL-"))
                         else "MATERIAL_PRESENT"),
            "opening_evidence": (object_id[len("PORTAL-"):]
                                 if object_id.startswith("PORTAL-") else ""),
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
    rectangular = len(poly.exterior.coords) - 1 == 4 and not list(
        getattr(poly, "interiors", ()) or ())
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
                "residual_mm": None,
                "verdict": NOT_PRESENT if rectangular else NOT_APPLICABLE,
                "why": ("no authored dimension brackets this span"
                        if rectangular else
                        "this polygon is not rectangular on this axis, so "
                        "its bounding span is not a SIDE anything could "
                        "have dimensioned")})
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


def _identity_label(node) -> tuple:
    """Every label inside one face, in order, without discarding any."""
    return tuple(t for z in node.zones for t in z.label_observations)


def measure(normalized, profile, *, semantic=None) -> Report:
    """Isolate the drawings, then measure each one on its own terms.

    ROUND 4 CHANGES THE ORDER AGAIN, AND FOR THE SAME REASON AS ROUND 3.

        ISOLATE      one model space can hold twelve unrelated drawings.
                     No relationship may cross between them (§1)
        AUTHORITY    which of this region's bands may close a room
        OPENINGS     what the holes in those bands actually are (§2-§5)
        MATCH        which wall each opening pierces, locally (§12)
        GRAPH        the region's faces ARE the physical spaces (§11)
        MEASURE      the frozen enclosure, unchanged, on each face
        IDENTIFY     names attached last, and never required (§11)
        ROLE         what KIND of enclosure each face is (round 2)
        RELEASE      only a physical room, with no unresolved opening

    Round 3 ran the authority, the containment and the enclosure across
    all twelve drawings at once and reported the cost itself: zero site
    bands found, because the outermost boundary of EVERYTHING spans the
    whole 808 m strip. Every one of those tests is now local.
    """
    wall_layers = tuple(profile.wall_like_layers())
    all_cands = wall_candidates(normalized, wall_layers)
    sem = semantic if semantic is not None else seeds_mod.classify(
        normalized.texts)
    # §8 needs the ZONE labels as well as the room ones. A dining area
    # inside an open-plan face is a functional zone, and round 3's
    # room-only filter silently threw it away — after which the face
    # released as a KITCHEN, which is exactly the merge §8 forbids.
    # Street names and level marks are still excluded: they name nothing
    # here.
    seeds = seeds_from_labels(normalized, semantic=sem,
                              classes=IDENTIFYING_CLASSES)

    regions = dregion.isolate(normalized)
    rep = Report(candidates=len(seeds), wall_layers=wall_layers)
    rep.semantic = sem
    rep.regions = regions
    rep.all_candidate_lines = len(all_cands)

    # Identity is reconciled ONCE, from the labels that qualified as seeds,
    # and then handed to each region. Grouping is spatial and by block
    # lineage, so it never reaches across a drawing anyway — but the
    # regions are what actually enforce it below.
    by_id = {t.provenance.object_id: t for t in normalized.texts}
    seed_texts = [by_id[s["object_id"]] for s in seeds
                  if s["object_id"] in by_id]
    id_rep = ident.reconcile(ident.observations_from(seed_texts))
    rep.identity = id_rep

    agg_auth = authority.AuthorityReport()
    agg_open = openings_mod.OpeningReport()
    agg_match = pmatch.MatchReport()
    role_of: dict = {}
    eligible_count = 0
    rows: list = []

    for reg in regions.regions:
        scoped = dregion.scope(reg, normalized)
        region_cands = dregion.scope_candidates(reg, all_cands)
        if not region_cands:
            continue
        obs = [o for o in sem.seeds() if reg.contains(o.x, o.y)]
        groups = [g for g in id_rep.groups if reg.contains(g.x, g.y)]

        # ---- what the holes are, BEFORE the authority runs -------------
        #
        # The order here is forced by a real failure. A plot wall with a
        # gate in it does not close, so the authority never saw an outer
        # ring, so no band was ever a site boundary — and the gate was free
        # to become a room's side. The openings are therefore classified
        # first, their closures let the authority see the rings that
        # actually exist, and the authority's verdict is then put back onto
        # the openings.
        opens = openings_mod.classify(
            region_cands, primitives=scoped["primitives"],
            instances=scoped["instances"], dimensions=scoped["dimensions"],
            region_id=reg.region_id)
        ring_closures = rpg.closure_candidates(
            opens.openings,
            {o.opening_id: "HOST_ESTABLISHED" for o in opens.openings})

        # ---- which bands may close a room, IN THIS DRAWING -------------
        #
        # Where a region carries no readable room stamp at all, the
        # authority's question has no anchor and every band came back
        # UNRESOLVED — which made a whole drawing unmeasurable because its
        # text was in an SHX font. The faces of its own arrangement answer
        # the same question without a string. This can release nothing on
        # its own: a face with no label is never a PHYSICAL_ROOM_CANDIDATE.
        anchors = obs or rpg.interior_anchors(region_cands + ring_closures)
        auth = authority.classify(region_cands + ring_closures, anchors)
        agg_auth.bands.extend(auth.bands)
        if auth.room_depth is not None:
            agg_auth.room_depth = auth.room_depth
        agg_auth.notes.update(auth.notes)
        role_of.update({b.band_id: b.roles for b in auth.bands})
        eligible_ids = {b.band_id for b in auth.eligible()}
        eligible = [c for c in region_cands if c.object_id in eligible_ids]
        eligible_count += len(eligible)

        # ---- and which wall each hole belongs to -----------------------
        opens = openings_mod.apply_band_roles(opens, role_of)
        agg_open.openings.extend(opens.openings)
        agg_open.interruptions.extend(opens.interruptions)
        agg_open.unmatched_symbols.extend(opens.unmatched_symbols)
        agg_open.notes.update(opens.notes)

        matched = pmatch.match(opens.openings, region_cands, region=reg,
                               region_report=regions,
                               eligible_bands=eligible_ids)
        agg_match.matches.extend(matched.matches)
        agg_match.portals.extend(matched.portals)
        agg_match.notes.update(matched.notes)
        status = matched.status_of()

        # ---- ROUND 5: is the partition there where nobody drew it? -----
        #
        # The chain is kept whole. Faces become BANDS become PHYSICAL WALLS
        # before anything asks whether a stretch of one is continuous, and
        # the answer carries two authorities so that closing a room never
        # quietly creates blockwork.
        walls = pwall.build(eligible, region_id=reg.region_id)
        cont = pcont.assess(walls.walls, openings=opens.openings,
                            region_id=reg.region_id)
        jct = jrec.recover(walls.walls, region_id=reg.region_id,
                           candidates=eligible, openings=opens.openings)
        recovered = (pcont.recovered_candidates(cont)
                     + jrec.recovered_candidates(jct))
        recovered_authority = {**pcont.recovered_authorities(cont),
                               **jrec.recovered_authorities(jct)}
        rep.walls.append(walls)
        rep.continuity.append(cont)
        rep.junctions.append(jct)

        # ---- the region's faces ARE the physical-space candidates ------
        #
        # Built TWICE on purpose: once from what is drawn, once with the
        # recovered spans. The difference is the only honest evidence that
        # a recovery subdivided anything, and §9 needs it to say so.
        before = rpg.build(region_id=reg.region_id, candidates=eligible,
                           openings=opens.openings, host_status=status,
                           identity_groups=groups)
        graph = rpg.build(region_id=reg.region_id, candidates=eligible,
                          openings=opens.openings, host_status=status,
                          identity_groups=groups, recovered=recovered)
        rep.graphs.append(graph)
        rep.subdivisions.append(fsub.diagnose(
            before.spaces, graph.spaces, continuity=cont,
            region_id=reg.region_id))

        open_by_id = {o.opening_id: o for o in opens.openings}
        rel_by_opening: dict = {}
        for r in graph.relations:
            rel_by_opening[r.get("opening_id", "")] = r

        region_rows = []
        for node in graph.spaces:
            e = node.enclosure
            bnd = []
            rels = []
            for oid in node.boundary_openings:
                o = open_by_id.get(oid)
                if o is None:
                    continue
                row = o.record()
                row["host_status"] = status.get(oid, pmatch.HOST_NOT_FOUND)
                bnd.append(row)
                if oid in rel_by_opening:
                    rels.append(rel_by_opening[oid])
            checks = _dimension_checks(e, scoped["dimensions"],
                                       dimlfac=normalized.dimlfac)
            segs = _boundary_segments(e, role_of)
            # Which recovered spans hold THIS face shut, asked of the
            # geometry. The frozen enclosure names one drawn piece per
            # side, so reading it off the edges would miss every recovery
            # that shares a side with a longer drawn run.
            recovered_here = [
                {**recovered_authority[oid], "cad_provenance": oid}
                for oid in node.recovered_on_boundary
                if oid in recovered_authority]
            region_rows.append(SpaceRow(
                space_id=node.node_id, seed_mm=node.seed_mm,
                label_observations=_identity_label(node),
                label_block="", enclosure=e,
                scores=enc.score(e, seed_mm=node.seed_mm),
                principal_dims_mm=_principal(e.polygon_wkt if e else ""),
                wall_thicknesses_mm=_thicknesses(e, eligible),
                dimension_checks=tuple(checks),
                provenance=tuple(o.observation_id for z in node.zones
                                 for o in z.identity.observations),
                identity=node.identity,
                boundary_roles=segs,
                recovered_boundary=tuple(recovered_here),
                region_id=reg.region_id,
                zones=node.zones,
                boundary_openings=tuple(bnd),
                relations=tuple(rels),
                quantities=graph.quantities.get(node.node_id, {})))

        # ---- WHAT KIND OF ENCLOSURE, asked WITHIN THIS DRAWING ----------
        #
        # Containment is a property of a SET, and round 3's set was every
        # drawing at once. A plan's outline contained a section's label
        # and nothing was ever a site boundary. The set is now one drawing.
        role_rep = roles.classify(
            [(r.space_id, r.enclosure.polygon_wkt if r.enclosure else "")
             for r in region_rows], groups, eligible)
        verdicts = {v.enclosure_id: v for v in role_rep.verdicts}
        rows.extend(
            SpaceRow(**{**r.__dict__,
                        "enclosure_role": (verdicts[r.space_id].role
                                           if r.space_id in verdicts
                                           else roles.UNRESOLVED),
                        "role_evidence": (verdicts[r.space_id].evidence
                                          if r.space_id in verdicts else ())})
            for r in region_rows)
        if rep.roles is None:
            rep.roles = role_rep
        else:
            rep.roles.verdicts.extend(role_rep.verdicts)

    rep.rows = rows
    rep.authority = agg_auth
    rep.openings = agg_open
    rep.matches = agg_match
    rep.candidate_lines = eligible_count

    rep.notes["order"] = (
        "isolate the drawings, then classify their openings, then build "
        "each region's own arrangement, then measure its faces with the "
        "frozen enclosure, then attach identity. Geometry does not wait "
        "for a name")
    rep.notes["seeding"] = (
        "a physical space no longer needs a room-name block to exist. "
        "Labels localise and NAME; the faces of the region's arrangement "
        "are what is measured. Loose text still never seeds anything: a "
        "street name or a level mark would name the wrong space")
    rep.notes["wall_layers_came_from"] = (
        "the source profile's geometric test, not from any layer name")
    rep.notes["openings"] = (
        "no gap was bridged. An opening closes a boundary only when its "
        "evidence grade and its matched host both allow it, and a grade-D "
        "wall gap allows nothing")
    return rep
