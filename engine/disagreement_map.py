"""E71 — where the vector polygon and the raster region disagree, and why.

BED-01 is the first frozen control. Its vector geometry and the raster
reference differ by 14.64% of area, and a single percentage is useless: it
does not say whether the engine is wrong, the reference is wrong, or the two
are measuring different things. So the disagreement is decomposed.

    RASTER IS NOT GROUND TRUTH.

The raster region is a segmentation output. Its boundary sits wherever the
pixels fell, which is somewhere inside the wall it abuts, quantised to
10.8 mm. It is a SECOND SIGNAL — good enough to say WHERE to look, never to
supply a millimetre. So nothing here corrects the vector geometry, and
nothing here is tuned to make the number smaller. The output is a map of
seven causes, and several of them are the reference's error rather than the
engine's.

BED-01 IS NOT TUNED. If this map says the engine is wrong, the fix is in the
engine and it gets measured again from scratch.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Why a piece of one shape is not in the other.
CAUSE_WALL_BASIS = "A_MEASUREMENT_BASIS_DIFFERS_RASTER_BOUNDARY_IN_THE_WALL"
CAUSE_DOORWAY = "B_DOORWAY_THRESHOLD_CLOSED_DIFFERENTLY"
CAUSE_QUANTISATION = "C_RASTER_BOUNDARY_QUANTISATION"
CAUSE_FIXTURE = "D_SEGMENTATION_CARVED_AROUND_A_FIXTURE"
CAUSE_VECTOR_LEAK = "E_VECTOR_LEAKED_PAST_A_MISSING_SEPARATOR"
CAUSE_RASTER_OVERREACH = "F_RASTER_REGION_CLAIMS_FLOOR_THE_VECTOR_DOES_NOT"
CAUSE_UNEXPLAINED = "G_UNEXPLAINED"

CAUSES = (CAUSE_WALL_BASIS, CAUSE_DOORWAY, CAUSE_QUANTISATION,
          CAUSE_FIXTURE, CAUSE_VECTOR_LEAK, CAUSE_RASTER_OVERREACH,
          CAUSE_UNEXPLAINED)

# Causes that are the REFERENCE's error, not the engine's. Naming them is the
# point: a disagreement driven by where the segmentation put its boundary is
# not evidence that the measurement is wrong.
REFERENCE_SIDE_CAUSES = (CAUSE_WALL_BASIS, CAUSE_QUANTISATION,
                         CAUSE_FIXTURE, CAUSE_RASTER_OVERREACH)
ENGINE_SIDE_CAUSES = (CAUSE_VECTOR_LEAK,)

# A piece smaller than this is not a finding. One square centimetre.
MIN_PIECE_MM2 = 10_000.0
# Within this of the shared boundary, and no wider, a piece is the raster's
# own stair-stepping: 1.5 pixels at 10.813 mm/px.
QUANTISATION_MM = 16.5
# A piece is "in the wall" if this much of it lies inside the wall solid.
IN_WALL_SHARE = 0.5
# A strip hugging the wall solid and narrower than a wall is thick is the
# segmentation boundary sitting short of the finish face — the same basis
# difference, measured on the room side instead of inside the masonry. The
# width ceiling is the drawing's own thickest wall, passed in by the caller.
WALL_ADJACENCY_MM = 1.0
# A barrier only explains a piece if it accounts for a real share of it, and
# a doorway threshold is door-sized. A 3.8 m2 lobe that merely touches a
# barrier is a segmentation that grew through the door, not a threshold.
BARRIER_SHARE = 0.3
MAX_DOORWAY_PIECE_M2 = 1.0
# How much of a vector-only piece must lie in OTHER labelled rooms before
# the vector space is judged to have leaked past a missing separator, and
# how much of it one room must hold to be named.
OTHER_ROOM_SHARE = 0.3
OTHER_ROOM_PIECE_MM2 = 1_000_000.0


@dataclass(frozen=True)
class Piece:
    """One connected region present in exactly one of the two shapes."""

    piece_id: str
    side: str                      # VECTOR_ONLY or RASTER_ONLY
    area_m2: float
    cause: str
    max_width_mm: float = 0.0
    share_inside_wall_solid: float = 0.0
    barrier_ids: tuple[str, ...] = ()
    other_space_ids: tuple[str, ...] = ()
    centroid_mm: tuple = ()
    why: str = ""

    @property
    def blame(self) -> str:
        if self.cause in REFERENCE_SIDE_CAUSES:
            return "THE_REFERENCE"
        if self.cause in ENGINE_SIDE_CAUSES:
            return "THE_ENGINE"
        return "NOT_ATTRIBUTED"

    def record(self) -> dict:
        return {"piece_id": self.piece_id, "side": self.side,
                "area_m2": round(self.area_m2, 4),
                "cause": self.cause, "blame": self.blame,
                "max_width_mm": round(self.max_width_mm, 1),
                "share_inside_wall_solid": round(
                    self.share_inside_wall_solid, 3),
                "barrier_ids": list(self.barrier_ids),
                "other_space_ids": list(self.other_space_ids),
                "centroid_mm": [round(v, 1) for v in self.centroid_mm],
                "why": self.why}


@dataclass
class DisagreementMap:
    space_id: str = ""
    vector_area_m2: float = 0.0
    raster_area_m2: float = 0.0
    intersection_m2: float = 0.0
    union_m2: float = 0.0
    pieces: list = field(default_factory=list)
    notes: dict = field(default_factory=dict)

    @property
    def iou(self) -> float:
        return 0.0 if not self.union_m2 else self.intersection_m2 / self.union_m2

    @property
    def area_delta_pct(self) -> float:
        if not self.raster_area_m2:
            return 0.0
        return 100.0 * (self.vector_area_m2 - self.raster_area_m2) / \
            self.raster_area_m2

    def record(self) -> dict:
        by_cause: dict = {}
        for p in self.pieces:
            d = by_cause.setdefault(p.cause, {"pieces": 0, "area_m2": 0.0})
            d["pieces"] += 1
            d["area_m2"] = round(d["area_m2"] + p.area_m2, 4)
        blamed: dict = {}
        for p in self.pieces:
            blamed[p.blame] = round(blamed.get(p.blame, 0.0) + p.area_m2, 4)
        return {
            "space_id": self.space_id,
            "vector_area_m2": round(self.vector_area_m2, 4),
            "raster_reference_area_m2": round(self.raster_area_m2, 4),
            "area_delta_pct": round(self.area_delta_pct, 2),
            "intersection_m2": round(self.intersection_m2, 4),
            "union_m2": round(self.union_m2, 4),
            "iou": round(self.iou, 4),
            "vector_only_m2": round(sum(
                p.area_m2 for p in self.pieces
                if p.side == "VECTOR_ONLY"), 4),
            "raster_only_m2": round(sum(
                p.area_m2 for p in self.pieces
                if p.side == "RASTER_ONLY"), 4),
            "by_cause": dict(sorted(by_cause.items(),
                                    key=lambda kv: -kv[1]["area_m2"])),
            "disagreement_area_by_blame": blamed,
            "pieces": [p.record() for p in sorted(
                self.pieces, key=lambda p: -p.area_m2)][:40],
            "minimum_piece_mm2": MIN_PIECE_MM2,
            "notes": dict(self.notes),
            "raster_is_not_ground_truth": (
                "the raster region is a segmentation output whose boundary "
                "sits somewhere inside the wall it abuts, quantised to one "
                "pixel. Several causes below are the REFERENCE's error. An "
                "area delta is not an error rate until it is decomposed"),
            "this_control_is_not_tuned": (
                "nothing here corrects the vector geometry and nothing is "
                "adjusted to make the delta smaller. If the map shows the "
                "engine is wrong, the engine is fixed and the control is "
                "measured again from scratch"),
        }


def polygon_from_mask(mask, *, px_mm: float, to_vector):
    """A raster region as a polygon in VECTOR millimetres.

    Built from row runs rather than pixel squares: a 3.5 x 4 m room is some
    120,000 pixels but only a few hundred runs, and the union of runs is the
    same shape.
    """
    import numpy as np
    from shapely.geometry import box
    from shapely.ops import unary_union

    boxes = []
    for y in range(mask.shape[0]):
        row = mask[y]
        if not row.any():
            continue
        idx = np.nonzero(row)[0]
        breaks = np.nonzero(np.diff(idx) > 1)[0]
        starts = np.concatenate(([0], breaks + 1))
        ends = np.concatenate((breaks, [idx.size - 1]))
        for s, e in zip(starts, ends):
            x0 = float(idx[s]) * px_mm
            x1 = float(idx[e] + 1) * px_mm
            y0, y1 = float(y) * px_mm, float(y + 1) * px_mm
            p0, p1 = to_vector(x0, y0), to_vector(x1, y1)
            boxes.append(box(min(p0[0], p1[0]), min(p0[1], p1[1]),
                             max(p0[0], p1[0]), max(p0[1], p1[1])))
    if not boxes:
        return None
    return unary_union(boxes)


def build(space_id: str, vector_geom, raster_geom, *, solid=None,
          barriers=(), other_regions=None, min_piece_mm2=MIN_PIECE_MM2,
          max_wall_thickness_mm: float = 500.0) -> DisagreementMap:
    """Decompose the disagreement into causes. Corrects nothing."""
    from engine.free_space import BARRIER_ACCEPTED
    from shapely.geometry import Polygon

    rep = DisagreementMap(space_id=space_id)
    if vector_geom is None or raster_geom is None:
        rep.notes["status"] = "NOT_COMPARABLE"
        rep.notes["why"] = (
            "one of the two shapes does not exist, so there is no "
            "disagreement to decompose. A missing shape is not agreement")
        return rep

    rep.vector_area_m2 = vector_geom.area / 1e6
    rep.raster_area_m2 = raster_geom.area / 1e6
    rep.intersection_m2 = vector_geom.intersection(raster_geom).area / 1e6
    rep.union_m2 = vector_geom.union(raster_geom).area / 1e6

    bars = [(b.portal_id, Polygon(list(b.ring))) for b in barriers
            if b.status == BARRIER_ACCEPTED and b.ring]
    solid_geom = getattr(solid, "geometry", None)

    # The raster region with its holes filled. A segmentation carves holes
    # around fixtures, text and hatching, and a vector-only piece sitting in
    # one of them is cause D — not an unexplained disagreement. The earlier
    # test for D asked whether the piece touched the intersection's
    # BOUNDARY, which includes every hole ring, so it never fired.
    filled = _filled(raster_geom)
    holes_m2 = (filled.area - raster_geom.area) / 1e6
    rep.notes["raster_reference_holes"] = {
        "holes": _hole_count(raster_geom),
        "hole_area_m2": round(holes_m2, 4),
        "raster_area_with_holes_filled_m2": round(filled.area / 1e6, 4),
        "why_it_matters": (
            "two raster-derived reference areas for the same room differ by "
            "this much purely on whether the carved holes count as floor. "
            "A fixture standing on a floor does not remove floor area, so "
            "the comparison here uses the region AS SEGMENTED and reports "
            "the filled figure beside it rather than choosing silently"),
    }

    n = 0
    for side, diff in (("VECTOR_ONLY", vector_geom.difference(raster_geom)),
                       ("RASTER_ONLY", raster_geom.difference(vector_geom))):
        parts = ([g for g in diff.geoms]
                 if diff.geom_type.startswith("Multi")
                 else ([diff] if not diff.is_empty else []))
        for g in parts:
            if g.area < min_piece_mm2:
                continue
            n += 1
            in_wall = 0.0
            if solid_geom is not None and g.area:
                in_wall = g.intersection(solid_geom).area / g.area
            hit, bar_share = (), 0.0
            touching = [(i, poly) for i, poly in bars if g.intersects(poly)]
            if touching and g.area:
                hit = tuple(sorted(i for i, _ in touching))
                from shapely.ops import unary_union
                bar_share = g.intersection(
                    unary_union([poly for _, poly in touching])).area / g.area
            # How much of this piece belongs to OTHER labelled rooms. The
            # test used to ask whether one other region covered half the
            # piece, which missed the case that matters most: a merged blob
            # spanning twenty-one rooms overlaps each of them by a few per
            # cent and was reported as unexplained.
            # Each hit carries its OWN polygon rather than a key to look
            # the polygon up again. The repository's ORDER IS NEVER IDENTITY
            # check objects to the re-lookup shape, and it is right to: a
            # join written that way is one refactor away from indexing the
            # wrong collection. There is nothing to join here — the polygon
            # is already in hand.
            others, other_share = (), 0.0
            hits = [(sid, poly, g.intersection(poly).area)
                    for sid, poly in (other_regions or {}).items()
                    if sid != space_id and poly is not None
                    and g.intersects(poly)]
            if hits and g.area:
                from shapely.ops import unary_union
                other_share = g.intersection(unary_union(
                    [poly for _, poly, _ in hits])).area / g.area
                others = tuple(
                    sid for sid, _, area in sorted(
                        hits, key=lambda h: -h[2])
                    if area >= OTHER_ROOM_PIECE_MM2
                    or area >= 0.05 * g.area)
            width = _max_width(g)
            near_wall = (solid_geom is not None
                         and g.distance(solid_geom) <= WALL_ADJACENCY_MM)
            cause, why = _cause(side=side, area=g.area, width=width,
                                in_wall=in_wall, barriers=hit,
                                bar_share=bar_share, others=others,
                                other_share=other_share,
                                in_a_raster_hole=(side == "VECTOR_ONLY"
                                                  and filled.covers(g)),
                                geom=g, near_wall=near_wall,
                                max_wall_mm=max_wall_thickness_mm)
            c = g.representative_point()
            rep.pieces.append(Piece(
                piece_id=f"DG-{n:04d}", side=side, area_m2=g.area / 1e6,
                cause=cause, max_width_mm=width,
                share_inside_wall_solid=in_wall, barrier_ids=hit,
                other_space_ids=others, centroid_mm=(c.x, c.y), why=why))

    rep.notes["status"] = "DECOMPOSED"
    rep.notes["pieces_below_the_floor_ignored"] = (
        f"pieces under {min_piece_mm2:.0f} mm2 are not reported: at one "
        "square centimetre they are boundary arithmetic, not findings")
    return rep


def _filled(geom):
    """The shape with its holes filled: outer rings only."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    parts = (list(geom.geoms) if geom.geom_type.startswith("Multi")
             else [geom])
    return unary_union([Polygon(g.exterior) for g in parts
                        if g.geom_type == "Polygon"])


def _hole_count(geom) -> int:
    parts = (list(geom.geoms) if geom.geom_type.startswith("Multi")
             else [geom])
    return sum(len(g.interiors) for g in parts if g.geom_type == "Polygon")


def _max_width(geom) -> float:
    """Roughly how thick a piece is: twice its largest inscribed radius."""
    try:
        from shapely import maximum_inscribed_circle
        line = maximum_inscribed_circle(geom)
        return 2.0 * line.length
    except Exception:
        x0, y0, x1, y1 = geom.bounds
        return min(x1 - x0, y1 - y0)


def _cause(*, side: str, area: float, width: float, in_wall: float,
           barriers: tuple, bar_share: float, others: tuple,
           other_share: float, in_a_raster_hole: bool, geom,
           near_wall: bool, max_wall_mm: float) -> tuple[str, str]:
    """Read in order of decisiveness, most specific evidence first.

    Order matters and an earlier version got it wrong: testing the barrier
    first put 3.8 m2 of segmentation that had grown out through a doorway
    into "doorway threshold closed differently", which reads as a harmless
    basis difference. It is not — it is the reference claiming a corridor.
    """
    if (side == "VECTOR_ONLY" and others
            and other_share >= OTHER_ROOM_SHARE):
        named = ", ".join(others[:8])
        more = ("" if len(others) <= 8
                else f" and {len(others) - 8} more")
        return CAUSE_VECTOR_LEAK, (
            f"{other_share * 100:.0f}% of this {area / 1e6:.4f} m2 lies "
            f"inside the raster region(s) for {named}{more}. The vector "
            "space reached past separators that are missing from the wall "
            "solid, so this piece belongs to other rooms. THIS ONE IS THE "
            "ENGINE")
    if in_a_raster_hole and in_wall < IN_WALL_SHARE:
        return CAUSE_FIXTURE, (
            f"{area / 1e6:.4f} m2 inside the raster region's outer ring and "
            "carved out of it: the segmentation split around something "
            "standing on the floor — a fixture, a hatch, a block of text. A "
            "fixture does not remove floor area, so the vector polygon is "
            "right to include it")
    if in_wall >= IN_WALL_SHARE:
        return CAUSE_WALL_BASIS, (
            f"{in_wall * 100:.0f}% of this {area / 1e6:.4f} m2 lies INSIDE "
            "the wall solid. The two shapes are on different measurement "
            "bases: the vector polygon stops at the clear internal finish "
            "face, the segmentation boundary sits within the masonry. That "
            "is the reference's basis, not an engine error")
    if near_wall and width <= max_wall_mm:
        return CAUSE_WALL_BASIS, (
            f"a {width:.0f} mm strip against the wall solid, "
            f"{area / 1e6:.4f} m2, narrower than the drawing's thickest "
            f"wall ({max_wall_mm:.0f} mm). The segmentation boundary stopped "
            "short of the finish face by about this much — the same basis "
            "difference as material overlap, measured on the room side of "
            "the wall instead of inside it")
    if width <= QUANTISATION_MM:
        return CAUSE_QUANTISATION, (
            f"a {width:.1f} mm sliver. At 10.813 mm per pixel the "
            "segmentation boundary stair-steps by about this much, so the "
            "disagreement is the raster's own resolution")
    if (barriers and bar_share >= BARRIER_SHARE
            and area / 1e6 <= MAX_DOORWAY_PIECE_M2):
        return CAUSE_DOORWAY, (
            f"{area / 1e6:.4f} m2, {bar_share * 100:.0f}% of it on an "
            f"accepted portal barrier ({', '.join(barriers)}) and no larger "
            "than a doorway. The two shapes close the threshold at different "
            "places: the vector boundary runs along the host wall's drawn "
            "faces, the segmentation stops where the pixels did")
    if side == "RASTER_ONLY":
        extra = ("" if not barriers else
                 f" It touches {', '.join(barriers)}, which is how it got "
                 "out — through the doorway, not across a threshold.")
        return CAUSE_RASTER_OVERREACH, (
            f"{area / 1e6:.4f} m2 the raster region claims and the vector "
            f"polygon does not, {width:.0f} mm across at its widest and not "
            f"inside the wall solid.{extra} The segmentation grew past this "
            "room's boundary, which is what region growing does at a gap")
    return CAUSE_UNEXPLAINED, (
        f"{area / 1e6:.4f} m2, {width:.0f} mm across, "
        f"{in_wall * 100:.0f}% inside the wall solid, "
        f"{'touching' if near_wall else 'away from'} the wall solid, not in "
        "a carved hole, no barrier and no other labelled region. Nothing "
        "available explains it, and a guess here would become a correction")
