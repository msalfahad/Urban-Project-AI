"""A band standing on another band is a fitting, and a fitting is not a wall.

A kitchen counter, a run of units, a wardrobe, a duct casing and a bath
panel are all drawn with two parallel lines a wall's thickness apart, and
nothing about those two lines says furniture. What gives a fitting away
is where it stands:

    IT SHARES A FACE LINE WITH ANOTHER ESTABLISHED BAND, over stretches
    that overlap, with its other face on the OPPOSITE side of that line

A wall does not have a second wall glued to it along part of its length.
Of two bands stacked that way the one that RUNS FURTHER is the wall — a
lining is fitted along part of a wall, never the other way round.

A fitting has two faces and they do not mean the same thing:

    the SHARED face  is where it meets the wall. A space on that side is
                     bounded by the WALL BEHIND, which draws that line
                     itself and owns it
    the FRONT face   stands out into the room. A space that stops there
                     has stopped at furniture

**A FITTING NEVER DEFINES A ROOM'S CLEAR INTERNAL FINISH FACE.** The room
a fitting stands in is measured to the wall behind it, which is where the
tiles, the plaster and the blockwork actually are. That is why this
module exists at the geometry layer and not only in the register: by the
time a polygon has stopped at a counter front, the wrong room has already
been measured.

What this module does NOT decide: whether the fitting is a kitchen unit,
a wardrobe or a bath panel. It says only that it stands on a wall.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from engine import space_enclosure as enc

MODEL = "A_BAND_STANDING_ON_A_WALL_IS_A_FITTING_V1"

# Two faces are the same line when the enclosure itself would not tell
# them apart. Nothing new is chosen here.
SAME_PLACE_MM = enc.COLLINEAR_JOIN_MM

FITTING_STANDS_ON_A_WALL = "IT_STANDS_ON_A_BAND_THAT_RUNS_FURTHER"
SHARED_FACE = "SHARED_FACE_THE_WALL_BEHIND_OWNS_IT"
FRONT_FACE = "FRONT_FACE_OF_A_FITTING_NO_ROOM_ENDS_HERE"


@dataclass(frozen=True)
class StackedBand:
    """One band fitted along another: which face is which, and on what."""

    lining_id: str
    wall_id: str
    axis: str
    shared_face_mm: float
    far_face_mm: float
    lining_length_mm: float = 0.0
    wall_length_mm: float = 0.0

    @property
    def front_face_mm(self) -> float:
        return self.far_face_mm

    def face_role(self, fixed_mm: float) -> str:
        if abs(fixed_mm - self.far_face_mm) <= SAME_PLACE_MM:
            return FRONT_FACE
        return SHARED_FACE

    def record(self) -> dict:
        return {
            "fitting_band_id": self.lining_id,
            "stands_on_wall_band_id": self.wall_id,
            "axis": self.axis,
            "shared_face_mm": round(self.shared_face_mm, 2),
            "front_face_mm": round(self.far_face_mm, 2),
            "fitting_runs_mm": round(self.lining_length_mm, 1),
            "wall_runs_mm": round(self.wall_length_mm, 1),
            "evidence": FITTING_STANDS_ON_A_WALL,
            "what_it_means": (
                "no room's clear internal finish face is at the front "
                "face. The room this fitting stands in is measured to the "
                "wall behind it"),
        }


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "SAME_PLACE_MM": SAME_PLACE_MM,
        "why": {
            "the_longer_one_is_the_wall": (
                "a lining is fitted along part of a wall and never the "
                "other way round. Where both run the same length neither "
                "is called a fitting, because nothing says which"),
            "only_the_front_face_is_refused": (
                "the shared face is the wall's own line. Refusing it too "
                "would take the room the fitting stands in with it"),
            "nothing_about_furniture": (
                "this module says a band stands on a wall. It does not "
                "say whether it is a counter, a wardrobe or a casing"),
        },
    }


def model_hash() -> str:
    parts = [MODEL, FITTING_STANDS_ON_A_WALL, SHARED_FACE, FRONT_FACE,
             str(SAME_PLACE_MM)]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


@dataclass
class FittingReport:
    """One region's fittings, and what the engine did about them."""

    region_id: str = ""
    fittings: dict = None

    def record(self) -> dict:
        return {
            "drawing_region_id": self.region_id,
            "model": MODEL,
            "FITTING_BAND_HASH": model_hash(),
            "fittings": [st.record()
                         for _k, st in sorted((self.fittings or {}).items())],
            "what_a_fitting_does_not_do": (
                "it does not bound a room, it does not give a clear "
                "internal finish face, and the strip between its two "
                "faces is not the inside of a wall"),
        }


def detect(walls) -> dict:
    """Which of this region's bands stand on another band.

    Returns {fitting band id: StackedBand}. A band that stands on a band
    which itself stands on something is still just a fitting here.
    """
    out: dict = {}
    good = [w for w in (walls or ())
            if getattr(w, "has_pairing_evidence", False)]
    for a in good:
        for b in good:
            if a is b or a.axis != b.axis:
                continue
            shared = None
            for fa in (a.face_a_mm, a.face_b_mm):
                for fb in (b.face_a_mm, b.face_b_mm):
                    if abs(fa - fb) <= SAME_PLACE_MM:
                        shared = fa
            if shared is None:
                continue
            a_far = (a.face_b_mm if abs(a.face_a_mm - shared)
                     <= SAME_PLACE_MM else a.face_a_mm)
            b_far = (b.face_b_mm if abs(b.face_a_mm - shared)
                     <= SAME_PLACE_MM else b.face_a_mm)
            if (a_far - shared) * (b_far - shared) >= 0:
                continue          # same side of the shared line: not stacked
            # Do they run ALONGSIDE each other at all? Their extents,
            # not their claims on the shared line: of two bands drawn on
            # one line only one of them ends up owning any given stretch
            # of it, and a fitting that has given its share to the wall
            # it stands on is still standing on it.
            a_lo, a_hi = a.drawn_extent_mm
            b_lo, b_hi = b.drawn_extent_mm
            if min(a_hi, b_hi) - max(a_lo, b_lo) <= SAME_PLACE_MM:
                continue          # they never meet along their length
            # HOW FAR EACH ONE IS DRAWN, not how much of the shared line
            # each ended up owning: of two bands drawn on one line only
            # one of them owns any given stretch of it, and that says
            # nothing about which is the wall.
            a_run, b_run = a.drawn_run_mm, b.drawn_run_mm
            if a_run < b_run:
                out[a.wall_id] = StackedBand(
                    lining_id=a.wall_id, wall_id=b.wall_id, axis=a.axis,
                    shared_face_mm=shared, far_face_mm=a_far,
                    lining_length_mm=a_run, wall_length_mm=b_run)
            elif b_run < a_run:
                out[b.wall_id] = StackedBand(
                    lining_id=b.wall_id, wall_id=a.wall_id, axis=b.axis,
                    shared_face_mm=shared, far_face_mm=b_far,
                    lining_length_mm=b_run, wall_length_mm=a_run)
    return out


def detect_by_region(walls_by_region) -> dict:
    out: dict = {}
    for _region, walls in (walls_by_region or {}).items():
        out.update(detect(walls))
    return out


def is_front_face(fittings, wall_id: str, fixed_mm: float) -> bool:
    """Is this line the FRONT of a fitting — the side no room ends at?"""
    st = (fittings or {}).get(wall_id)
    return st is not None and st.face_role(fixed_mm) == FRONT_FACE


def stops_at_a_fitting(row, fittings) -> tuple:
    """The fittings whose FRONT face bounds this candidate.

    `row["face_contacts"]` is (wall_band_id, face_mm) for every boundary
    face. A contact at a fitting's shared face is a contact with the wall
    behind it and is not returned.
    """
    lin = dict(fittings or {})
    if not lin:
        return ()
    hit = {}
    for band_id, face_mm in row.get("face_contacts", ()):
        st = lin.get(band_id)
        if st is None or face_mm is None:
            continue
        if abs(float(face_mm) - st.far_face_mm) <= SAME_PLACE_MM:
            hit[band_id] = st
    return tuple(hit[k] for k in sorted(hit))
