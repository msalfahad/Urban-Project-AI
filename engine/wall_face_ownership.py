"""Which FACE of a wall does a room actually stop at?

Round 6 made the wall bands honest: one line may not serve two walls over
the same stretch, and 3,272 phantom bands became 389. It left the next
question untouched, and that question is where the kitchen went.

P7757's kitchen measured 2.20 x 2.55 m. The supervised reference is
3.00 x 2.70. The missing 800 mm and 150 mm are not a tolerance and not a
trade-grouping question:

    CAD-311  x = -151839.9   a 500 mm deep COUNTER along the west wall
    CAD-310  x = -152339.9   the west wall's internal face
    CAD-284  y = -801093.5   a 500 mm deep COUNTER along the north wall
    CAD-283  y = -800593.5   the north wall's internal face

The flood stops at the FIRST line it meets, and the first line it meets is
the front of a kitchen counter. Between 2700 mm of clear floor and 2200 mm
of unobstructed floor sits a worktop, and only one of those two numbers is
a floor area.

So this module answers one question about every line in a drawing:

    IS THERE OPEN SPACE ON THE OTHER SIDE OF YOU?

and one question about every pair of lines:

    IS THERE OPEN SPACE OUTSIDE EACH OF YOU, AND NONE BETWEEN YOU?

A wall is where the spaces on both sides stop. That is not a heuristic
about layers, depths or names — it is what a wall IS, read off the
arrangement the drawing already draws. Three things fall out of it:

  * A COUNTER IS NOT A WALL. Open floor lies on BOTH sides of a counter
    front: the room, and the strip between it and the wall behind. A pair
    with space between its faces is not a band, and a line with space on
    both sides bounds nothing.

  * A GLAZING LINE IS NOT A FACE. The three inner lines of a window sit
    INSIDE the 200 mm band. Nothing outside them is space, so they cannot
    be where a room stops — and the pair that CAN is the 200 mm one, not
    the 120 mm one that happened to be nearer.

  * A ROOM AND ITS NEIGHBOUR TAKE OPPOSITE FACES. Ownership is the side
    the space is on. One wall therefore gives its low face to one room and
    its high face to the other, and no universal boundary is drawn down
    the middle of anything.

Nothing here changes the frozen enclosure. The flood still runs, still
leaks where the drawing leaks, and still reports what it reports. This
module states the MEASUREMENT BASIS of the polygon that is released, and
the basis is named on every space rather than switched silently.
"""

from __future__ import annotations

import bisect
import hashlib
from dataclasses import dataclass, field

from engine import cad_profile as cprofile
from engine import fitting_band as fitting
from engine import space_enclosure as enc

MODEL = "SPACE_STOPS_AT_THE_FACE_WALL_OWNERSHIP_V1"

# --- §4 the measurement bases, never silently switched -------------------
CLEAR_INTERNAL_FINISH_FACE = "CLEAR_INTERNAL_FINISH_FACE"
STRUCTURAL_FACE = "STRUCTURAL_FACE"
WALL_CENTERLINE = "WALL_CENTERLINE"
EXTERNAL_FACE = "EXTERNAL_FACE"
BASIS_NOT_ESTABLISHED = "MEASUREMENT_BASIS_NOT_ESTABLISHED"
# ROUND 6B §4/§5. A side held by a single-line partition whose topology is
# established and whose thickness is not. It is NOT the same state as "no
# face at all": the two spaces ARE separate, and only the position of the
# floor's edge is unknown. Collapsing the two would lose exactly the
# distinction round 6B exists to keep.
CLEAR_FACE_NOT_ESTABLISHED = "CLEAR_FACE_NOT_ESTABLISHED"

BASES = (CLEAR_INTERNAL_FINISH_FACE, STRUCTURAL_FACE, WALL_CENTERLINE,
         EXTERNAL_FACE, CLEAR_FACE_NOT_ESTABLISHED, BASIS_NOT_ESTABLISHED)

WHAT_EACH_BASIS_IS = {
    CLEAR_INTERNAL_FINISH_FACE: (
        "the finished face a room stops at, on the side facing that room. "
        "This is the floor-area basis and the only one round 6A releases"),
    STRUCTURAL_FACE: (
        "the face of the structural member behind the finish. Not measured "
        "here: nothing in this drawing separates render from block"),
    WALL_CENTERLINE: (
        "half way through the wall. Never a floor area, and never a "
        "substitute for one"),
    EXTERNAL_FACE: (
        "the face on the far side from the room. Used for external "
        "envelope quantities, never for an internal floor"),
    CLEAR_FACE_NOT_ESTABLISHED: (
        "a single-line partition separates this space from the next one, "
        "and nothing says how thick it is. The TOPOLOGY is established; "
        "the clear floor area is not, and the centreline is not "
        "substituted for the face"),
    BASIS_NOT_ESTABLISHED: (
        "the space is bounded somewhere this module cannot name a face "
        "for. No floor quantity may be taken from it"),
}

# --- what lies on one side of a line -------------------------------------
SIDE_SPACE = "OPEN_SPACE"
SIDE_MATERIAL = "INSIDE_A_WALL"
SIDE_OPEN = "OUTSIDE_THE_DRAWN_ARRANGEMENT"

# --- §3 side ownership ----------------------------------------------------
SPACE_LEFT = "SPACE_LEFT"          # the lower coordinate on this axis
SPACE_RIGHT = "SPACE_RIGHT"        # the higher coordinate on this axis
OWNER_INTERIOR = "INTERIOR"
OWNER_EXTERIOR = "EXTERIOR"
OWNER_UNKNOWN = "UNKNOWN"

OWNERSHIP = (SPACE_LEFT, SPACE_RIGHT, OWNER_INTERIOR, OWNER_EXTERIOR,
             OWNER_UNKNOWN)

# --- why a line may or may not bound a room ------------------------------
BOUNDS_WALL_FACE = "A_FACE_OF_AN_ESTABLISHED_WALL_BAND"
BOUNDS_PORTAL = "A_PORTAL_CLOSING_AN_OPENING_WITH_NO_MATERIAL"
BOUNDS_RECOVERED = "A_RECOVERED_PARTITION_SPAN"
NOT_BOUNDING_INSIDE_A_SPACE = "OPEN_SPACE_LIES_ON_BOTH_SIDES_OF_THIS_LINE"
NOT_BOUNDING_INSIDE_A_WALL = "IT_LIES_INSIDE_A_WALL_BAND_AND_BOUNDS_NOTHING"
NOT_BOUNDING_NO_PAIRING = "ITS_BAND_IS_PAIRED_ON_NOTHING_BUT_PROXIMITY"

# A shared edge shorter than the enclosure's own collinear join is a
# hairline artefact of the arrangement, not a piece of wall. This is the
# enclosure's tolerance, unchanged; nothing new is introduced.
HAIRLINE_MM = enc.COLLINEAR_JOIN_MM

# Two faces closer than the thinnest thing this project calls a wall are
# not two faces. The profile's own figures, unchanged.
MIN_WALL_MM = cprofile.MIN_WALL_THICKNESS_MM

# A strip WIDER than the thickest wall this project recognises is not the
# inside of a wall — it is somewhere a person stands. This is the profile's
# own ceiling, the same number the graph's material test uses, and it lets
# "is there space here" be answered from the drawn coordinates alone
# instead of from a polygon that a two-millimetre drafting gap can leak
# through. On P7757 that leak is why the kitchen's own 200 mm south wall
# was read as open floor.
MAX_WALL_MM = cprofile.MAX_WALL_THICKNESS_MM

# Where a face is probed along the stretch it shares with its partner.
# Three stations rather than one, so a doorway at the middle of a wall does
# not decide what the whole wall is. These are FRACTIONS of the shared
# stretch, not distances, so no millimetre figure enters here.
PROBE_STATIONS = (0.25, 0.5, 0.75)


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "BASES": list(BASES),
        "PROBE_STATIONS": list(PROBE_STATIONS),
        "HAIRLINE_MM": HAIRLINE_MM,
        "MIN_WALL_MM": MIN_WALL_MM,
        "MAX_WALL_MM": MAX_WALL_MM,
        "why": {
            "no_new_number": (
                "the hairline is the enclosure's own collinear join and the "
                "wall minimum is the profile's. The probe stations are "
                "fractions of a stretch the drawing itself sets"),
            "a_wall_is_where_the_spaces_stop": (
                "open space outside each face and none between them. This "
                "is read off the arrangement, not off a layer name, a "
                "depth, or a list of what furniture is called"),
            "no_layer_rule": (
                "no layer is trusted or distrusted. The counter and the "
                "wall it stands against are on the same layers as each "
                "other elsewhere in this drawing"),
            "probe_is_evidence": (
                "what lies beyond a face is read at three stations along "
                "the stretch the two faces share. It is evidence about a "
                "pair, ranked with the rest, and it admits nothing on its "
                "own"),
        },
    }


def model_hash() -> str:
    parts = [MODEL] + list(BASES) + list(OWNERSHIP) + [
        BOUNDS_WALL_FACE, BOUNDS_PORTAL, BOUNDS_RECOVERED,
        NOT_BOUNDING_INSIDE_A_SPACE, NOT_BOUNDING_INSIDE_A_WALL,
        NOT_BOUNDING_NO_PAIRING, SIDE_SPACE, SIDE_MATERIAL, SIDE_OPEN,
        str(PROBE_STATIONS), str(HAIRLINE_MM), str(MIN_WALL_MM),
        str(MAX_WALL_MM)]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


# ------------------------------------------------------------ arrangement

def _segment(c):
    from shapely.geometry import LineString

    lo, hi = sorted((c.start_mm, c.end_mm))
    if hi - lo <= 0:
        return None
    if c.axis == "H":
        return LineString([(lo, c.fixed_mm), (hi, c.fixed_mm)])
    if c.axis == "V":
        return LineString([(c.fixed_mm, lo), (c.fixed_mm, hi)])
    return None


def _mean_thickness_mm(face) -> float:
    """Twice area over perimeter — the same measure the graph uses."""
    per = face.length
    return 0.0 if per <= 0 else 2.0 * face.area / per


@dataclass
class Arrangement:
    """What this region's own lines enclose, and which of it is material.

    The faces are the graph's faces and the material test is the graph's
    test. Nothing is re-derived: this is the same arrangement, indexed so
    that a question can be asked of a POINT rather than of a polygon.
    """

    region_id: str = ""
    space_faces: list = field(default_factory=list)
    material_faces: list = field(default_factory=list)
    coords: dict = field(default_factory=dict)   # axis -> sorted [(c, runs)]
    _keys: dict = field(default_factory=dict)    # axis -> sorted coords
    _tree: object = None
    _flat: list = field(default_factory=list)
    _kind: list = field(default_factory=list)

    def at(self, x: float, y: float) -> str:
        """Is this point open space, inside a wall, or outside everything?"""
        from shapely.geometry import Point

        if self._tree is None:
            return SIDE_OPEN
        pt = Point(x, y)
        for idx in self._tree.query(pt):
            if self._flat[int(idx)].contains(pt):
                return self._kind[int(idx)]
        return SIDE_OPEN

    def next_coord(self, axis: str, coord: float, lo: float, hi: float,
                   direction: int):
        """The next parallel line beyond `coord` that overlaps [lo, hi]."""
        rows = self.coords.get(axis)
        if not rows:
            return None
        keys = self._keys.get(axis) or []
        i = bisect.bisect_left(keys, coord)
        rng = range(i, len(rows)) if direction > 0 else range(i - 1, -1, -1)
        for j in rng:
            c, runs = rows[j]
            if direction > 0 and c <= coord + HAIRLINE_MM:
                continue
            if direction < 0 and c >= coord - HAIRLINE_MM:
                continue
            if any(min(hi, r1) - max(lo, r0) > HAIRLINE_MM for r0, r1 in runs):
                return c
        return None

    def beyond(self, axis: str, coord: float, lo: float, hi: float,
               direction: int, station: float) -> str:
        """What lies immediately beyond this face, at this station."""
        nxt = self.next_coord(axis, coord, lo, hi, direction)
        if nxt is None:
            return SIDE_OPEN
        mid = (coord + nxt) / 2.0
        along = lo + (hi - lo) * station
        return self.at(mid, along) if axis == "V" else self.at(along, mid)

    def both_sides(self, axis: str, coord: float, lo: float,
                   hi: float) -> tuple:
        """What lies on each side of one line, over one stretch."""
        seen = []
        for direction in (-1, +1):
            vals = [self.beyond(axis, coord, lo, hi, direction, st)
                    for st in PROBE_STATIONS]
            for want in (SIDE_SPACE, SIDE_OPEN, SIDE_MATERIAL):
                if want in vals:
                    seen.append(want)
                    break
            else:
                seen.append(SIDE_MATERIAL)
        return tuple(seen)

    def width_beyond(self, axis: str, coord: float, lo: float, hi: float,
                     direction: int) -> str:
        """What lies beyond this face, read from the drawn coordinates.

        There is no polygon here on purpose. A wall's interior is a closed
        cell only if every line around it meets every other, and drawings
        are not drawn that way; one 50 mm slot at a window turns the
        inside of a wall into the whole floor plate. The distance to the
        next parallel line does not care.
        """
        nxt = self.next_coord(axis, coord, lo, hi, direction)
        if nxt is None:
            return SIDE_OPEN
        return (SIDE_SPACE if abs(nxt - coord) > MAX_WALL_MM
                else SIDE_MATERIAL)

    def widths_between(self, axis: str, f_lo: float, f_hi: float,
                       lo: float, hi: float) -> list:
        """The width of every strip strictly between two faces."""
        rows = self.coords.get(axis) or []
        keys = self._keys.get(axis) or []
        i = bisect.bisect_right(keys, f_lo)
        j = bisect.bisect_left(keys, f_hi)
        stops = [f_lo] + [
            c for c, runs in rows[i:j]
            if f_lo + HAIRLINE_MM < c < f_hi - HAIRLINE_MM
            and any(min(hi, r1) - max(lo, r0) > HAIRLINE_MM
                    for r0, r1 in runs)] + [f_hi]
        return [b - a for a, b in zip(stops, stops[1:])]

    def cells_between(self, axis: str, f_lo: float, f_hi: float,
                      lo: float, hi: float, station: float) -> list:
        """Every strip strictly between two faces, said at one station."""
        rows = self.coords.get(axis) or []
        keys = self._keys.get(axis) or []
        i = bisect.bisect_right(keys, f_lo)
        j = bisect.bisect_left(keys, f_hi)
        stops = [f_lo] + [
            c for c, runs in rows[i:j]
            if f_lo + HAIRLINE_MM < c < f_hi - HAIRLINE_MM
            and any(min(hi, r1) - max(lo, r0) > HAIRLINE_MM
                    for r0, r1 in runs)] + [f_hi]
        along = lo + (hi - lo) * station
        out = []
        for a, b in zip(stops, stops[1:]):
            mid = (a + b) / 2.0
            out.append(self.at(mid, along) if axis == "V"
                       else self.at(along, mid))
        return out


def arrangement(candidates, *, region_id: str = "") -> Arrangement:
    """Build the region's arrangement once, for everything below."""
    from shapely.ops import polygonize, unary_union
    from shapely.strtree import STRtree

    segs = [s for s in (_segment(c) for c in candidates) if s is not None]
    arr = Arrangement(region_id=region_id)
    if not segs:
        return arr
    for f in polygonize(unary_union(segs)):
        if _mean_thickness_mm(f) <= cprofile.MAX_WALL_THICKNESS_MM:
            arr.material_faces.append(f)
        else:
            arr.space_faces.append(f)
    arr._flat = list(arr.space_faces) + list(arr.material_faces)
    arr._kind = ([SIDE_SPACE] * len(arr.space_faces)
                 + [SIDE_MATERIAL] * len(arr.material_faces))
    if arr._flat:
        arr._tree = STRtree(arr._flat)

    by_axis: dict = {}
    for c in candidates:
        if c.axis not in ("H", "V"):
            continue
        lo, hi = sorted((c.start_mm, c.end_mm))
        if hi - lo <= 0:
            continue
        key = round(c.fixed_mm / HAIRLINE_MM)
        by_axis.setdefault(c.axis, {}).setdefault(
            key, [c.fixed_mm, []])[1].append((lo, hi))
    for axis, rows in by_axis.items():
        arr.coords[axis] = sorted(
            (fixed, tuple(sorted(runs))) for fixed, runs in rows.values())
        arr._keys[axis] = [c for c, _ in arr.coords[axis]]
    return arr


# ------------------------------------- §2 is this pair where spaces stop?

@dataclass(frozen=True)
class PairTopology:
    """What the arrangement says about one candidate pair of faces."""

    spaces_stop_at_both: bool
    space_between: bool
    outside_low: str
    outside_high: str

    def record(self) -> dict:
        return {"OPEN_SPACE_OUTSIDE_EACH_FACE_AND_NONE_BETWEEN":
                self.spaces_stop_at_both,
                "open_space_lies_between_the_faces": self.space_between,
                "beyond_the_low_face": self.outside_low,
                "beyond_the_high_face": self.outside_high}


def pair_topology(arr: Arrangement, axis: str, fa: float, fb: float,
                  interval) -> PairTopology:
    """Is this pair two faces of one wall, as the drawing's own spaces say?

    Two conditions, both structural, and both read off the DRAWN
    COORDINATES rather than off a polygon:

        no strip between the faces is wider than a wall can be
        beyond each face there is either a strip wider than a wall can be,
            or nothing drawn at all

    The first is what refuses a pair straddling a room. The second is what
    refuses a window's inner glazing line, whose far side is thirty
    millimetres of the same wall — and it is why the 200 mm band wins over
    the 120 mm one that happened to be nearer.

    "Nothing drawn at all" is how an external wall qualifies: beyond its
    outer face the region draws nothing. Demanding a space there would
    make every perimeter wall unpairable.
    """
    lo, hi = interval
    f_lo, f_hi = (fa, fb) if fa <= fb else (fb, fa)
    if hi - lo <= HAIRLINE_MM or f_hi - f_lo < MIN_WALL_MM:
        return PairTopology(False, False, SIDE_OPEN, SIDE_OPEN)

    widths = arr.widths_between(axis, f_lo, f_hi, lo, hi)
    between = any(w > MAX_WALL_MM for w in widths)
    b_lo = arr.width_beyond(axis, f_lo, lo, hi, -1)
    b_hi = arr.width_beyond(axis, f_hi, lo, hi, +1)
    stops = (not between and b_lo in (SIDE_SPACE, SIDE_OPEN)
             and b_hi in (SIDE_SPACE, SIDE_OPEN))
    return PairTopology(stops, between, b_lo, b_hi)


# --------------------------------------------------- §3 side ownership

@dataclass
class FaceOwnership:
    """One face of one wall band, and which space it faces."""

    wall_id: str
    region_id: str
    axis: str
    face: str                    # "A" or "B"
    fixed_mm: float
    interval_mm: tuple
    side: str                    # SPACE_LEFT / SPACE_RIGHT
    beyond: str                  # SIDE_SPACE / SIDE_MATERIAL / SIDE_OPEN
    interior_exterior: str = OWNER_UNKNOWN
    owner_space_id: str = ""
    cad_provenance: tuple = ()

    @property
    def face_id(self) -> str:
        return f"{self.wall_id}-FACE-{self.face}"

    def record(self) -> dict:
        return {
            "face_id": self.face_id,
            "wall_band_id": self.wall_id,
            "axis": self.axis,
            "fixed_mm": round(self.fixed_mm, 2),
            "interval_mm": [round(v, 2) for v in self.interval_mm],
            "side": self.side,
            "what_lies_beyond_it": self.beyond,
            "interior_exterior": self.interior_exterior,
            "owning_physical_space": self.owner_space_id,
            "cad_provenance": list(self.cad_provenance),
        }


def _face_runs(wall, which):
    return wall.face_a if which == "A" else wall.face_b


def ownership(walls, arr: Arrangement, *, region_id: str = "",
              envelope=None, fittings=None) -> list:
    """Every established face, with the side it faces and what is there.

    A face is owned by the space on ITS side. The same wall therefore
    yields one face to the room on the low side and the opposite face to
    the room on the high side, and no boundary is ever drawn down the
    middle of a wall to be shared between them.
    """
    from engine import interior_exterior as ie

    out = []
    for w in walls:
        if not w.has_pairing_evidence:
            continue
        for which in ("A", "B"):
            fixed = w.face_a_mm if which == "A" else w.face_b_mm
            other = w.face_b_mm if which == "A" else w.face_a_mm
            # ROUND 6D: a fitting's front face owns no space. The room
            # it stands in is measured to the wall behind it.
            if fitting.is_front_face(fittings, w.wall_id, fixed):
                continue
            for iv in (w.face_stretches(which) or ((0.0, 0.0),)):
                direction = -1 if fixed < other else +1
                side = SPACE_LEFT if direction < 0 else SPACE_RIGHT
                beyond = SIDE_OPEN
                for st in PROBE_STATIONS:
                    seen = arr.beyond(w.axis, fixed, iv[0], iv[1], direction, st)
                    if seen == SIDE_SPACE:
                        beyond = seen
                        break
                    if seen == SIDE_OPEN:
                        beyond = seen
                ix = OWNER_UNKNOWN
                if envelope is not None:
                    nxt = arr.next_coord(w.axis, fixed, iv[0], iv[1], direction)
                    step = (fixed + nxt) / 2.0 if nxt is not None else (
                        fixed + direction * max(MIN_WALL_MM, 1.0))
                    along = (iv[0] + iv[1]) / 2.0
                    px, py = ((step, along) if w.axis == "V" else (along, step))
                    verdict = ie.classify_point(envelope, px, py)
                    ix = {ie.INTERIOR: OWNER_INTERIOR,
                          ie.EXTERIOR: OWNER_EXTERIOR}.get(
                              verdict.verdict, OWNER_UNKNOWN)
                out.append(FaceOwnership(
                    wall_id=w.wall_id, region_id=region_id or w.region_id,
                    axis=w.axis, face=which, fixed_mm=fixed,
                    interval_mm=(iv[0], iv[1]), side=side, beyond=beyond,
                    interior_exterior=ix,
                    cad_provenance=tuple(
                        oid for r in _face_runs(w, which)
                        for oid in r.object_ids)))
    return out


# ------------------------------- what may bound a clear-internal polygon

def bounding_geometry(walls, *, closures=(), recovered=(), fittings=None):
    """The lines a room is allowed to STOP at, as one geometry.

    Three kinds and no others: a face of a wall band that earned its
    pairing, a portal closing an opening, and a partition span round 5
    recovered. A counter front, a glazing line, a door leaf, a level mark
    and a piece of furniture are none of those, and a room does not end at
    any of them.
    """
    from shapely.geometry import LineString
    from shapely.ops import unary_union

    segs = []
    for w in walls:
        if not w.has_pairing_evidence:
            continue
        for which in ("A", "B"):
            fixed = w.face_a_mm if which == "A" else w.face_b_mm
            # ROUND 6D: the front of a fitting is not where a room ends.
            # Its shared face is the wall's own line and the wall puts it
            # there itself.
            if fitting.is_front_face(fittings, w.wall_id, fixed):
                continue
            for lo, hi in w.face_stretches(which):
                if hi - lo <= HAIRLINE_MM:
                    continue
                if w.axis == "V":
                    segs.append(LineString([(fixed, lo), (fixed, hi)]))
                else:
                    segs.append(LineString([(lo, fixed), (hi, fixed)]))
    for c in list(closures) + list(recovered):
        s = _segment(c)
        if s is not None:
            segs.append(s)
    return unary_union(segs) if segs else None


def _shared_edge(f1, f2):
    """The edge two arrangement faces have in common.

    The WHOLE boundary of each, not just its outer ring. A room sitting in
    the middle of a floor plate is a HOLE in the face around it, and
    comparing outer rings alone reports no neighbour at all — which is how
    the first version of this module absorbed nothing on P7757.
    """
    try:
        return f1.boundary.intersection(f2.boundary)
    except Exception:       # noqa: BLE001
        return None


@dataclass(frozen=True)
class DroppedLine:
    """A line that stands INSIDE a space rather than bounding one."""

    object_id: str
    axis: str
    fixed_mm: float
    interval_mm: tuple
    why: str

    def record(self) -> dict:
        return {"cad_provenance": self.object_id, "axis": self.axis,
                "fixed_mm": round(self.fixed_mm, 2),
                "interval_mm": [round(v, 2) for v in self.interval_mm],
                "length_mm": round(abs(self.interval_mm[1]
                                       - self.interval_mm[0]), 1),
                "why_it_does_not_bound_a_room": self.why}


def _face_cover(walls, fittings=None) -> dict:
    """Where an established band actually puts a face, per line.

    The FRONT face of a fitting is not one. A counter that stands against
    a wall is drawn exactly like a wall, and a line kept because a band
    has a face there is a line a room may stop at — which is how a room
    comes to be measured to a run of units.
    """
    out: dict = {}
    for w in walls or ():
        if not w.has_pairing_evidence:
            continue
        # Where the band IS a band — both of its faces drawn. A face
        # running on past its partner is the single line round 6B asks
        # about, and it does not get to keep a room's boundary on its own
        # say-so just because a band starts somewhere along it.
        for lo, hi in w.drawn_mm:
            if hi - lo <= HAIRLINE_MM:
                continue
            for fixed in (w.face_a_mm, w.face_b_mm):
                if fitting.is_front_face(fittings, w.wall_id, fixed):
                    continue
                out.setdefault((w.axis, round(fixed / HAIRLINE_MM)),
                               []).append((lo, hi))
    return out


def _band_pairs(walls, fittings=None) -> dict:
    """Which two coordinates are the two faces of ONE established band.

    A fitting is left out: the strip between a counter's back and its
    front is furniture standing on the floor, not the inside of a wall.
    """
    out: dict = {}
    for w in walls or ():
        if not w.has_pairing_evidence:
            continue
        if (fittings or {}).get(w.wall_id) is not None:
            continue
        a, b = sorted((w.face_a_mm, w.face_b_mm))
        for lo, hi in w.drawn_mm:
            if hi - lo <= HAIRLINE_MM:
                continue
            out.setdefault((w.axis, round(a / HAIRLINE_MM),
                            round(b / HAIRLINE_MM)), []).append((lo, hi))
    return out


def _side(arr: Arrangement, pairs: dict, axis: str, coord: float,
          lo: float, hi: float, direction: int) -> str:
    """Is what lies beyond this line a WALL, a space, or nothing drawn?

    A strip is the inside of a wall only when the two lines bounding it
    are the two faces of one established band. That is the whole test, and
    it is what separates a 200 mm wall from the 500 mm gap between a
    worktop and the wall behind it: both are narrow, and only one of them
    has a wall's two faces around it.
    """
    nxt = arr.next_coord(axis, coord, lo, hi, direction)
    if nxt is None:
        return SIDE_OPEN
    a, b = sorted((coord, nxt))
    key = (axis, round(a / HAIRLINE_MM), round(b / HAIRLINE_MM))
    for p_lo, p_hi in pairs.get(key, ()):
        if min(hi, p_hi) - max(lo, p_lo) > HAIRLINE_MM:
            return SIDE_MATERIAL
    return SIDE_SPACE


def clear_candidates(candidates, walls, arr: Arrangement, *, closures=(),
                     recovered=(), fittings=None) -> tuple:
    """Split a region's lines into what bounds a room and what stands in one.

    A line is KEPT when it is a face of an established wall band over this
    stretch, when it is a portal or a recovered span, or when the drawing
    gives no clear answer. It is DROPPED only on positive evidence that it
    bounds nothing:

        OPEN SPACE LIES ON BOTH SIDES OF IT

    That is true of a counter front, a door leaf, a wardrobe, a threshold
    and a hatch outline, and false of every wall face — a wall has
    material on one side, by definition. Where it is true and the line is
    a face of no band, the line is not where a room ends.

    A one-line partition nobody paired is dropped by the same rule, and
    that is not hidden: the two rooms it separated become one space whose
    boundary cannot be fully attributed, so its measurement basis is NOT
    ESTABLISHED and no floor quantity may be taken from it.
    """
    cover = _face_cover(walls, fittings)
    pairs = _band_pairs(walls, fittings)
    keep_ids = {getattr(c, "object_id", "")
                for c in list(closures) + list(recovered)}
    kept, dropped = [], []
    for c in candidates:
        if c.axis not in ("H", "V") or c.object_id in keep_ids:
            kept.append(c)
            continue
        lo, hi = sorted((c.start_mm, c.end_mm))
        key = (c.axis, round(c.fixed_mm / HAIRLINE_MM))
        if any(min(hi, b) - max(lo, a) > HAIRLINE_MM
               for a, b in cover.get(key, ())):
            kept.append(c)
            continue
        low = _side(arr, pairs, c.axis, c.fixed_mm, lo, hi, -1)
        high = _side(arr, pairs, c.axis, c.fixed_mm, lo, hi, +1)
        if low == SIDE_SPACE and high == SIDE_SPACE:
            dropped.append(DroppedLine(
                object_id=c.object_id, axis=c.axis, fixed_mm=c.fixed_mm,
                interval_mm=(lo, hi), why=NOT_BOUNDING_INSIDE_A_SPACE))
            continue
        kept.append(c)
    return kept, dropped


# ------------------------------------------- §4 what the polygon reports

@dataclass
class BoundaryFace:
    """One side of a released polygon, and why it is where it is."""

    axis: str
    fixed_mm: float
    interval_mm: tuple
    length_mm: float
    basis: str
    wall_band_id: str = ""
    face_id: str = ""
    cad_provenance: tuple = ()
    why: str = ""

    def record(self) -> dict:
        return {"axis": self.axis, "fixed_mm": round(self.fixed_mm, 2),
                "interval_mm": [round(v, 2) for v in self.interval_mm],
                "length_mm": round(self.length_mm, 1),
                "measurement_basis": self.basis,
                "wall_band_id": self.wall_band_id,
                "boundary_face_id": self.face_id,
                "cad_provenance": list(self.cad_provenance),
                "why_this_face_was_selected": self.why}


def _edges_of(polygon) -> list:
    out = []
    rings = [polygon.exterior] + list(polygon.interiors)
    for ring in rings:
        pts = list(ring.coords)
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            if abs(y1 - y0) <= HAIRLINE_MM and abs(x1 - x0) > HAIRLINE_MM:
                out.append(("H", y0, tuple(sorted((x0, x1)))))
            elif abs(x1 - x0) <= HAIRLINE_MM and abs(y1 - y0) > HAIRLINE_MM:
                out.append(("V", x0, tuple(sorted((y0, y1)))))
    return out


def _junction_return(axis, fixed, lo, hi, faces, attributed) -> object:
    """Is this short side the corner return of a band already on this ring?

    A wall's two faces do not always meet at the corner: one run stops 50
    or 150 mm short of the other, and the ring then carries a stub that no
    face covers. It is not an unaccounted side — it is where the wall
    turns. It is claimed only when the stub is no longer than the thinnest
    wall this project recognises AND a face of the SAME band is already on
    this ring, so nothing new is asserted about the geometry.
    """
    if hi - lo > MIN_WALL_MM + HAIRLINE_MM:
        return None
    for f in faces:
        if f.wall_id not in attributed or f.axis != axis:
            continue
        if abs(f.fixed_mm - fixed) <= MIN_WALL_MM + HAIRLINE_MM:
            return f
    return None


def attribute(polygon, faces, *, closures=(), recovered=(),
              partitions=None) -> list:
    """Name every side of the polygon: which face, which band, which entity.

    §4 asks this of every physical-space polygon, and the answer is not
    optional: a side nobody can attribute is reported with
    MEASUREMENT_BASIS_NOT_ESTABLISHED rather than assumed to be a wall.
    """
    by_axis: dict = {}
    for f in faces:
        by_axis.setdefault(f.axis, []).append(f)
    closure_by_axis: dict = {}
    for c in list(closures) + list(recovered):
        if c.axis in ("H", "V"):
            closure_by_axis.setdefault(c.axis, []).append(c)

    part_by_line = dict(partitions or {})
    out = []
    attributed = set()
    for axis, fixed, (lo, hi) in _edges_of(polygon):
        hit = None
        for f in by_axis.get(axis, ()):
            if abs(f.fixed_mm - fixed) > HAIRLINE_MM:
                continue
            if min(hi, f.interval_mm[1]) - max(lo, f.interval_mm[0]) <= \
                    HAIRLINE_MM:
                continue
            hit = f
            break
        if hit is not None:
            attributed.add(hit.wall_id)
            out.append(BoundaryFace(
                axis=axis, fixed_mm=fixed, interval_mm=(lo, hi),
                length_mm=hi - lo, basis=CLEAR_INTERNAL_FINISH_FACE,
                wall_band_id=hit.wall_id, face_id=hit.face_id,
                cad_provenance=hit.cad_provenance,
                why=("this face of the band is the one facing this space, "
                     f"and open space stops at it ({hit.side})")))
            continue
        cl = None
        for c in closure_by_axis.get(axis, ()):
            if abs(c.fixed_mm - fixed) > HAIRLINE_MM:
                continue
            c_lo, c_hi = sorted((c.start_mm, c.end_mm))
            if min(hi, c_hi) - max(lo, c_lo) <= HAIRLINE_MM:
                continue
            cl = c
            break
        if cl is not None:
            rec = str(cl.object_id).startswith("RECOVERED")
            out.append(BoundaryFace(
                axis=axis, fixed_mm=fixed, interval_mm=(lo, hi),
                length_mm=hi - lo, basis=CLEAR_INTERNAL_FINISH_FACE,
                cad_provenance=(cl.object_id,),
                why=(BOUNDS_RECOVERED if rec else BOUNDS_PORTAL)))
            continue
        part = None
        for oid, row in part_by_line.items():
            p_axis, p_fixed, p_lo, p_hi = row["geometry"]
            if p_axis != axis or abs(p_fixed - fixed) > HAIRLINE_MM:
                continue
            if min(hi, p_hi) - max(lo, p_lo) <= HAIRLINE_MM:
                continue
            part = (oid, row)
            break
        if part is not None:
            oid, row = part
            established = row["clear_face_established"]
            out.append(BoundaryFace(
                axis=axis, fixed_mm=fixed, interval_mm=(lo, hi),
                length_mm=hi - lo,
                basis=(CLEAR_INTERNAL_FINISH_FACE if established
                       else CLEAR_FACE_NOT_ESTABLISHED),
                wall_band_id=row.get("band_id", ""),
                face_id=row.get("candidate_id", ""),
                cad_provenance=tuple(row.get("entities", (oid,))),
                why=row.get("why", "")))
            continue
        out.append(BoundaryFace(
            axis=axis, fixed_mm=fixed, interval_mm=(lo, hi),
            length_mm=hi - lo, basis=BASIS_NOT_ESTABLISHED,
            why=("no established wall face, portal, recovered span or "
                 "single-line partition covers this side")))

    # ---- second pass: the corners the wall turns at -------------------
    #
    # Asked only once every side that HAS a face has one, because a stub
    # is claimed by a band already on this ring and the ring is not
    # traversed in any particular order.
    for i, f in enumerate(out):
        if f.basis != BASIS_NOT_ESTABLISHED:
            continue
        ret = _junction_return(f.axis, f.fixed_mm, f.interval_mm[0],
                               f.interval_mm[1], faces, attributed)
        if ret is None:
            continue
        out[i] = BoundaryFace(
            axis=f.axis, fixed_mm=f.fixed_mm, interval_mm=f.interval_mm,
            length_mm=f.length_mm, basis=CLEAR_INTERNAL_FINISH_FACE,
            wall_band_id=ret.wall_id, face_id=ret.face_id,
            cad_provenance=ret.cad_provenance,
            why=("the corner return of a band already bounding this "
                 "space. No new geometry is asserted"))
    return out


@dataclass
class ClearSpace:
    """One physical space on the clear-internal-finish-face basis."""

    space_id: str = ""
    region_id: str = ""
    polygon_wkt: str = ""
    area_m2: float = 0.0
    principal_dims_mm: tuple = ()
    basis: str = BASIS_NOT_ESTABLISHED
    boundary_faces: tuple = ()
    absorbed_faces: int = 0
    absorbed_area_m2: float = 0.0
    obstructed_area_m2: float = 0.0
    notes: dict = field(default_factory=dict)

    @property
    def basis_established(self) -> bool:
        return self.basis == CLEAR_INTERNAL_FINISH_FACE

    @property
    def topology_established(self) -> bool:
        """Are this space's limits known, whatever its area basis is?

        §1: a supported single-line partition establishes TWO PHYSICAL
        SPACES without establishing one millimetre of wall thickness.
        """
        return self.basis in (CLEAR_INTERNAL_FINISH_FACE,
                              CLEAR_FACE_NOT_ESTABLISHED)

    def record(self, *, limit: int = 24) -> dict:
        return {
            "measurement_basis": self.basis,
            "what_that_basis_is": WHAT_EACH_BASIS_IS[self.basis],
            "clear_internal_area_m2": round(self.area_m2, 3),
            "principal_dims_mm": [round(v, 1)
                                  for v in self.principal_dims_mm],
            "polygon_wkt_mm": self.polygon_wkt,
            "boundary_face_ids": [f.face_id for f in self.boundary_faces
                                  if f.face_id],
            "wall_band_ids": sorted({f.wall_band_id
                                     for f in self.boundary_faces
                                     if f.wall_band_id}),
            "boundary_faces": [f.record()
                               for f in self.boundary_faces[:limit]],
            "sides_with_no_established_face": sum(
                1 for f in self.boundary_faces
                if f.basis == BASIS_NOT_ESTABLISHED),
            "sides_held_by_a_partition_of_unknown_thickness": sum(
                1 for f in self.boundary_faces
                if f.basis == CLEAR_FACE_NOT_ESTABLISHED),
            "TOPOLOGY_ESTABLISHED": self.topology_established,
            "arrangement_faces_absorbed": self.absorbed_faces,
            "obstructed_extent_m2": round(self.obstructed_area_m2, 3),
            "area_behind_fittings_m2": round(self.absorbed_area_m2, 3),
            "notes": dict(self.notes),
        }


def clear_space(space_id: str, region_id: str, polygon, faces, *,
                closures=(), recovered=(), absorbed=0,
                obstructed_m2: float = 0.0, complete: bool = True,
                partitions=None) -> ClearSpace:
    """Measure one space on the clear-internal-finish-face basis."""
    bf = tuple(attribute(polygon, faces, closures=closures,
                         recovered=recovered, partitions=partitions))
    x0, y0, x1, y1 = polygon.bounds
    established = bool(bf) and complete and all(
        f.basis == CLEAR_INTERNAL_FINISH_FACE for f in bf)
    partition_only = bool(bf) and complete and not established and all(
        f.basis in (CLEAR_INTERNAL_FINISH_FACE, CLEAR_FACE_NOT_ESTABLISHED)
        for f in bf)
    basis = (CLEAR_INTERNAL_FINISH_FACE if established
             else CLEAR_FACE_NOT_ESTABLISHED if partition_only
             else BASIS_NOT_ESTABLISHED)
    return ClearSpace(
        space_id=space_id, region_id=region_id, polygon_wkt=polygon.wkt,
        area_m2=polygon.area / 1e6,
        principal_dims_mm=(round(x1 - x0, 1), round(y1 - y0, 1)),
        basis=basis,
        boundary_faces=bf, absorbed_faces=absorbed,
        absorbed_area_m2=max(0.0, polygon.area / 1e6 - obstructed_m2),
        notes={} if established else {
            "why_not_released": (
                "a single-line partition bounds this space and its "
                "thickness is not established, so the TOPOLOGY holds and "
                "the clear area does not"
                if partition_only else
                "the clear-internal flood did not close, or a side of this "
                "polygon is not an established wall face, portal, "
                "recovered span or single-line partition")})


@dataclass
class OwnershipReport:
    region_id: str = ""
    faces: list = field(default_factory=list)
    spaces: list = field(default_factory=list)
    dropped: list = field(default_factory=list)
    pairs_with_space_between: int = 0
    notes: dict = field(default_factory=dict)

    def counts(self) -> dict:
        return {
            "established_wall_faces": len(self.faces),
            "faces_facing_open_space": sum(1 for f in self.faces
                                           if f.beyond == SIDE_SPACE),
            "faces_facing_outside_the_arrangement": sum(
                1 for f in self.faces if f.beyond == SIDE_OPEN),
            "faces_by_interior_exterior": {
                k: sum(1 for f in self.faces if f.interior_exterior == k)
                for k in (OWNER_INTERIOR, OWNER_EXTERIOR, OWNER_UNKNOWN)},
            "clear_internal_spaces": len(self.spaces),
            "spaces_with_an_established_basis": sum(
                1 for s in self.spaces if s.basis_established),
            "arrangement_faces_absorbed": sum(s.absorbed_faces
                                              for s in self.spaces),
            "lines_standing_inside_a_space": len(self.dropped),
            "length_of_those_lines_m": round(sum(
                abs(d.interval_mm[1] - d.interval_mm[0])
                for d in self.dropped) / 1000.0, 1),
        }

    def record(self, *, limit: int = 20) -> dict:
        return {
            "model": MODEL,
            "WALL_FACE_OWNERSHIP_HASH": model_hash(),
            "drawing_region_id": self.region_id,
            "counts": self.counts(),
            "frozen_parameters": frozen_parameters(),
            "faces": [f.record() for f in self.faces[:limit]],
            "spaces": [s.record() for s in self.spaces[:limit]],
            "lines_standing_inside_a_space": [
                d.record() for d in self.dropped[:limit]],
            "notes": dict(self.notes),
        }
