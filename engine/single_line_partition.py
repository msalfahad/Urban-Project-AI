"""A line the architect drew once, and the three different things it can mean.

Round 6A set aside every line that is a face of no wall and has floor on
both sides of it — 845 of them on P7757, 729 m in total. That was right
about a worktop and wrong about a partition: a 100 mm block wall drawn as
a single line is still a wall, and setting it aside merges the two rooms
it separates. Thirty-four of P7757's seventy polygons have no measurable
clear floor, and seventy of their unattributed sides are lines exactly
like that.

The mistake to avoid now is the opposite one. A single line that divides a
region is not a partition BECAUSE it divides a region — that is circular,
and it would turn every dimension line, every hatch boundary and every
worktop into blockwork. So this module asks for POSITIVE ARCHITECTURAL
EVIDENCE, and keeps three questions apart that a single line answers
differently:

    TOPOLOGY_AUTHORITY        are these two spaces separate?
    CLEAR_FACE_AUTHORITY      where exactly does each room's floor stop?
    MATERIAL_WALL_AUTHORITY   how much blockwork, plaster, paint is there?

**THESE ARE NOT EQUIVALENT.** A supported single-line partition can
establish that two rooms exist without establishing one millimetre of
wall thickness. It then carries:

    PARTITION_TOPOLOGY_ESTABLISHED
    CLEAR_FACE_NOT_ESTABLISHED       — unless the face is independently found
    MATERIAL_NOT_ESTABLISHED         — ALWAYS. §6, and it is mandatory.

A SECOND WALL FACE IS NEVER INVENTED. Where the thickness is unknown the
answer is that it is unknown; the centreline is not quietly substituted,
because half of an unknown number is still unknown.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass, field

from engine import cad_profile as cprofile
from engine import space_enclosure as enc

MODEL = "POSITIVE_EVIDENCE_SINGLE_LINE_PARTITION_V1"

# --- §1 the three authorities, kept apart --------------------------------
TOPOLOGY_ESTABLISHED = "PARTITION_TOPOLOGY_ESTABLISHED"
TOPOLOGY_UNRESOLVED = "PARTITION_TOPOLOGY_UNRESOLVED"
CLEAR_FACE_ESTABLISHED = "CLEAR_FACE_ESTABLISHED"
CLEAR_FACE_NOT_ESTABLISHED = "CLEAR_FACE_NOT_ESTABLISHED"
MATERIAL_ESTABLISHED = "MATERIAL_WALL_ESTABLISHED"
MATERIAL_NOT_ESTABLISHED = "MATERIAL_WALL_NOT_ESTABLISHED"

# --- §4 the three results, never collapsed -------------------------------
RESULT_A = "TOPOLOGY_AND_CLEAR_FACE_ESTABLISHED_MATERIAL_NOT"
RESULT_B = "TOPOLOGY_ESTABLISHED_CLEAR_FACE_AND_MATERIAL_NOT"
RESULT_C = "PARTITION_UNRESOLVED"

RESULTS = (RESULT_A, RESULT_B, RESULT_C)

WHAT_EACH_RESULT_IS = {
    RESULT_A: ("two separate physical spaces, and each one's floor stops "
               "at a face found independently of this line. The area may "
               "be released; the blockwork may not"),
    RESULT_B: ("two separate physical spaces, and nothing says where "
               "either floor stops. The topology may be released; the "
               "CLEAR AREA may not, and neither may any material"),
    RESULT_C: ("not established as a partition at all. It bounds nothing, "
               "and the spaces on either side of it are one space"),
}

# --- §3 positive architectural evidence ----------------------------------
EV_TERMINATES_AT_ESTABLISHED_WALLS = (
    "BOTH_ENDS_MEET_AN_ESTABLISHED_WALL_BAND")
EV_ONE_END_MEETS_A_WALL = "ONE_END_MEETS_AN_ESTABLISHED_WALL_BAND"
EV_T_OR_L_JUNCTION = "ANOTHER_DRAWN_LINE_MEETS_IT_AT_A_T_OR_L_JUNCTION"
EV_CONTINUES_AN_ALIGNMENT = (
    "IT_CONTINUES_THE_ALIGNMENT_OF_AN_ESTABLISHED_PARTITION")
EV_HOSTS_AN_OPENING = "AN_OPENING_IS_HOSTED_ON_IT_OR_ALIGNS_WITH_IT"
EV_REPEATED_ACROSS_PLANS = "THE_SAME_LINE_APPEARS_ON_ANOTHER_PLAN"
EV_AUTHORED_DIMENSION = "AN_AUTHORED_DIMENSION_ENDS_ON_IT"
EV_SEPARATES_OBSERVATIONS = (
    "IT_SEPARATES_TWO_INDEPENDENTLY_SUPPORTED_SPACE_OBSERVATIONS")

EVIDENCE = (EV_TERMINATES_AT_ESTABLISHED_WALLS, EV_ONE_END_MEETS_A_WALL,
            EV_T_OR_L_JUNCTION, EV_CONTINUES_AN_ALIGNMENT,
            EV_HOSTS_AN_OPENING, EV_REPEATED_ACROSS_PLANS,
            EV_AUTHORED_DIMENSION, EV_SEPARATES_OBSERVATIONS)

# A partition has to be ANCHORED in the fabric and then CORROBORATED. One
# strong token on its own is a coincidence waiting to happen; two
# independent statements about the same line are an architect's intent.
#
# RUNNING FROM WALL TO WALL IS NOT STRONG EVIDENCE. A worktop is fitted
# between two walls, a wardrobe is built between two walls, and a bath is
# set between two walls. On P7757 that token alone would have turned the
# kitchen counter back into a partition and undone round 6A. What a
# fitting does NOT have is a door through it, a twin on the floor above,
# a wall it continues, or a named room on each side of it.
STRONG = (EV_HOSTS_AN_OPENING, EV_REPEATED_ACROSS_PLANS,
          EV_CONTINUES_AN_ALIGNMENT, EV_SEPARATES_OBSERVATIONS)
SUPPORTING = (EV_TERMINATES_AT_ESTABLISHED_WALLS, EV_ONE_END_MEETS_A_WALL,
              EV_T_OR_L_JUNCTION, EV_AUTHORED_DIMENSION)
MIN_TOKENS = 2

# --- §5 where the clear face may come from -------------------------------
FACE_FROM_A_CONTINUING_BAND = (
    "THIS_LINE_IS_COLLINEAR_WITH_A_FACE_OF_AN_ESTABLISHED_BAND")
FACE_FROM_A_DIMENSION = "AN_AUTHORED_DIMENSION_GIVES_THE_FACE_POSITION"
FACE_FROM_A_JAMB = "A_JAMB_OR_REVEAL_ON_IT_GIVES_THE_FACE_POSITION"

FACE_EVIDENCE = (FACE_FROM_A_CONTINUING_BAND, FACE_FROM_A_DIMENSION,
                 FACE_FROM_A_JAMB)

# --- tolerances, all of them borrowed ------------------------------------
# An end "meets" something when the enclosure itself would treat the
# junction as a corner rather than a gap. `space_enclosure.JUNCTION_REACH_MM`
# is the only tolerance in this project that may close anything.
REACH_MM = enc.JUNCTION_REACH_MM
COLLINEAR_MM = enc.COLLINEAR_JOIN_MM

# A partition shorter than the thinnest thing this project calls a wall is
# not a partition. The profile's own figure.
MIN_LENGTH_MM = cprofile.MIN_WALL_THICKNESS_MM

# A dimension endpoint or an alignment is "on" the line within the same
# junction reach. Nothing new.
ALIGN_MM = REACH_MM


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "EVIDENCE": list(EVIDENCE),
        "STRONG": list(STRONG),
        "SUPPORTING": list(SUPPORTING),
        "MIN_TOKENS": MIN_TOKENS,
        "FACE_EVIDENCE": list(FACE_EVIDENCE),
        "REACH_MM": REACH_MM,
        "MIN_LENGTH_MM": MIN_LENGTH_MM,
        "why": {
            "no_new_number": (
                "the reach is the enclosure's junction reach, the "
                "collinearity is its collinear join, and the minimum "
                "length is the profile's thinnest wall. This module "
                "introduces no constant of its own"),
            "positive_evidence_only": (
                "dividing a region is not evidence of being a partition. "
                "Every dimension line, hatch boundary and worktop divides "
                "a region"),
            "one_strong_and_two_in_total": (
                "a partition is ANCHORED in the fabric and then "
                "CORROBORATED. One token is a coincidence; two "
                "independent statements about one line are intent"),
            "wall_to_wall_is_not_strong": (
                "a worktop, a wardrobe and a bath are all fitted between "
                "two walls. Spanning the room is what a fitting does"),
            "material_is_never_established_here": (
                "§6. A line has no thickness. Whatever this module "
                "concludes about topology, the blockwork, plaster, paint, "
                "wall ceramic and waterproofing it contributes is ZERO "
                "until a second face is found — and this module never "
                "invents one"),
            "no_room_size_rule": (
                "no candidate is accepted or refused for the size of the "
                "space on either side of it"),
        },
    }


def model_hash() -> str:
    parts = ([MODEL] + list(EVIDENCE) + list(FACE_EVIDENCE) + list(RESULTS)
             + [TOPOLOGY_ESTABLISHED, TOPOLOGY_UNRESOLVED,
                CLEAR_FACE_ESTABLISHED, CLEAR_FACE_NOT_ESTABLISHED,
                MATERIAL_ESTABLISHED, MATERIAL_NOT_ESTABLISHED,
                str(MIN_TOKENS), str(REACH_MM), str(MIN_LENGTH_MM)])
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


# ------------------------------------------------------------- the object

@dataclass
class Candidate:
    """§2. One drawn line, and everything asked of it."""

    candidate_id: str = ""
    region_id: str = ""
    source_entity_id: str = ""
    source_entity_ids: tuple = ()
    source_layer: str = ""
    axis: str = ""
    fixed_mm: float = 0.0
    start_mm: float = 0.0
    end_mm: float = 0.0
    evidence: tuple = ()
    face_evidence: tuple = ()
    topology_authority: str = TOPOLOGY_UNRESOLVED
    clear_face_authority: str = CLEAR_FACE_NOT_ESTABLISHED
    material_authority: str = MATERIAL_NOT_ESTABLISHED
    status: str = RESULT_C
    clear_face_mm: float = None
    clear_face_band_id: str = ""
    why: str = ""

    @property
    def length_mm(self) -> float:
        return abs(self.end_mm - self.start_mm)

    @property
    def establishes_topology(self) -> bool:
        return self.topology_authority == TOPOLOGY_ESTABLISHED

    @property
    def establishes_clear_face(self) -> bool:
        return self.clear_face_authority == CLEAR_FACE_ESTABLISHED

    def record(self) -> dict:
        return {
            "candidate_id": self.candidate_id,
            "drawing_region_id": self.region_id,
            "source_entity_id": self.source_entity_id,
            "source_entity_ids": list(self.source_entity_ids
                                      or (self.source_entity_id,)),
            "source_layer": self.source_layer,
            "geometry": {"axis": self.axis,
                         "fixed_mm": round(self.fixed_mm, 2),
                         "endpoints_mm": [round(self.start_mm, 2),
                                          round(self.end_mm, 2)],
                         "length_mm": round(self.length_mm, 1)},
            "evidence": list(self.evidence),
            "clear_face_evidence": list(self.face_evidence),
            "TOPOLOGY_AUTHORITY": self.topology_authority,
            "CLEAR_FACE_AUTHORITY": self.clear_face_authority,
            "MATERIAL_WALL_AUTHORITY": self.material_authority,
            "status": self.status,
            "what_that_status_is": WHAT_EACH_RESULT_IS[self.status],
            "clear_face_mm": (None if self.clear_face_mm is None
                              else round(self.clear_face_mm, 2)),
            "clear_face_from_band": self.clear_face_band_id,
            "why": self.why,
            "material_contribution_m": 0.0,
            "provenance": ("one drawn CAD entity. No second face was "
                           "created, and none is implied"),
        }


@dataclass
class PartitionReport:
    region_id: str = ""
    candidates: list = field(default_factory=list)
    notes: dict = field(default_factory=dict)

    def established(self) -> list:
        return [c for c in self.candidates if c.establishes_topology]

    def counts(self) -> dict:
        return {
            "candidates": len(self.candidates),
            "by_status": dict(Counter(c.status
                                      for c in self.candidates).most_common()),
            "topology_established": len(self.established()),
            "clear_face_established": sum(
                1 for c in self.candidates if c.establishes_clear_face),
            "material_established": sum(
                1 for c in self.candidates
                if c.material_authority == MATERIAL_ESTABLISHED),
            "topology_established_length_m": round(sum(
                c.length_mm for c in self.established()) / 1000.0, 1),
            "material_established_length_m": 0.0,
            "evidence_seen": dict(Counter(
                t for c in self.candidates for t in c.evidence).most_common()),
        }

    def record(self, *, limit: int = 30) -> dict:
        return {
            "model": MODEL,
            "SINGLE_LINE_PARTITION_HASH": model_hash(),
            "drawing_region_id": self.region_id,
            "counts": self.counts(),
            "frozen_parameters": frozen_parameters(),
            "candidates": [c.record() for c in self.candidates[:limit]],
            "the_mandatory_rule": (
                "a topology-only partition contributes 0 m of "
                "MATERIAL_ESTABLISHED_LENGTH. It may not create blockwork, "
                "plaster, paint, wall ceramic or waterproofing"),
            "notes": dict(self.notes),
        }


# --------------------------------------------------------------- evidence

def _iv(c):
    return tuple(sorted((c.start_mm, c.end_mm)))


@dataclass(frozen=True)
class _Run:
    """Collinear pieces the drawing means as one partition."""

    axis: str
    fixed_mm: float
    start_mm: float
    end_mm: float
    object_ids: tuple
    source_layer: str = ""


def _merge(lines, openings) -> list:
    """Join collinear pieces across a doorway, and across drafting noise.

    A partition with a door in it is drawn as two pieces. Asked
    separately, neither piece has a room on each side of it — the stamps
    are beside the DOOR, not beside the stub — and both are refused. The
    architect drew one wall, so one wall is what is assessed.

    A gap is joined only when an opening on this very line explains it,
    or when it is narrower than the enclosure's own junction reach. No
    other gap is bridged: §8 of round 5 forbids a general bridging rule
    and this is not one.
    """
    by_line: dict = {}
    for c in lines:
        if c.axis not in ("H", "V"):
            continue
        key = (c.axis, round(c.fixed_mm / COLLINEAR_MM))
        by_line.setdefault(key, []).append(c)
    out = []
    for (axis, _k), group in by_line.items():
        group.sort(key=lambda c: min(_iv(c)))
        fixed = group[0].fixed_mm
        cur = None
        for c in group:
            lo, hi = _iv(c)
            if cur is None:
                cur = [lo, hi, [c.object_id],
                       getattr(c, "source_layer", "")]
                continue
            gap = lo - cur[1]
            if gap <= REACH_MM or _opening_on(openings, axis, fixed,
                                              cur[1], lo):
                cur[1] = max(cur[1], hi)
                cur[2].append(c.object_id)
            else:
                out.append(_Run(axis, fixed, cur[0], cur[1],
                                tuple(cur[2]), cur[3]))
                cur = [lo, hi, [c.object_id],
                       getattr(c, "source_layer", "")]
        if cur is not None:
            out.append(_Run(axis, fixed, cur[0], cur[1], tuple(cur[2]),
                            cur[3]))
    return out


def _band_faces(walls) -> dict:
    """(axis, coord) -> the intervals an established band's face covers."""
    out: dict = {}
    for w in walls or ():
        if not getattr(w, "has_pairing_evidence", False):
            continue
        # Where the band IS a band — both faces drawn. A face whose
        # partner is missing over a stretch is exactly the single line
        # this module is asked about, and it cannot be its own evidence.
        for lo, hi in w.drawn_mm:
            if hi - lo <= COLLINEAR_MM:
                continue
            for fixed in (w.face_a_mm, w.face_b_mm):
                out.setdefault((w.axis, round(fixed, 1)),
                               []).append((lo, hi, w.wall_id))
    return out


def _meets_a_band(faces, axis, station, coord) -> str:
    """Does a wall band's face cross this line's end, perpendicular to it?"""
    other = "H" if axis == "V" else "V"
    for (ax, fixed), runs in faces.items():
        if ax != other or abs(fixed - station) > REACH_MM:
            continue
        for lo, hi, wall_id in runs:
            if lo - REACH_MM <= coord <= hi + REACH_MM:
                return wall_id
    return ""


def _crosses_here(candidates, axis, fixed, lo, hi) -> bool:
    """Is any perpendicular line drawn across this one, away from its ends?"""
    other = "H" if axis == "V" else "V"
    for c in candidates:
        if c.axis != other:
            continue
        c_lo, c_hi = _iv(c)
        if not (c_lo - REACH_MM <= fixed <= c_hi + REACH_MM):
            continue
        if lo + REACH_MM < c.fixed_mm < hi - REACH_MM:
            return True
    return False


def _aligned_band(faces, axis, fixed, lo, hi) -> tuple:
    """Is this line collinear with an established face that runs on past it?"""
    for (ax, f), runs in faces.items():
        if ax != axis or abs(f - fixed) > COLLINEAR_MM:
            continue
        for r_lo, r_hi, wall_id in runs:
            if min(hi, r_hi) - max(lo, r_lo) > REACH_MM:
                continue          # it IS that face, not a continuation
            if abs(r_hi - lo) <= REACH_MM or abs(r_lo - hi) <= REACH_MM:
                return (f, wall_id)
    return (None, "")


def _jamb_face(openings, axis, fixed, lo, hi):
    """Does an opening ON this line name a second face, and so a thickness?

    §5. A door in a partition is drawn with its reveals, and the reveals
    are where the two faces are. That is the partition's own construction
    stated by the architect — not an inference from this line, and not a
    thickness borrowed from somewhere else in the drawing.
    """
    for o in openings or ():
        if o.axis != axis:
            continue
        faces = tuple(o.wall_faces_mm or ())
        if len(faces) < 2:
            continue
        if not any(abs(v - fixed) <= REACH_MM for v in faces):
            continue
        o_lo, o_hi = sorted((o.start_mm, o.end_mm))
        if min(hi, o_hi) - max(lo, o_lo) <= REACH_MM:
            continue
        near = min(faces, key=lambda v: abs(v - fixed))
        return near
    return None


def _opening_on(openings, axis, fixed, lo, hi) -> bool:
    for o in openings or ():
        if o.axis != axis:
            continue
        faces = o.wall_faces_mm or (o.fixed_mm,)
        if not any(abs(v - fixed) <= REACH_MM for v in faces):
            continue
        o_lo, o_hi = sorted((o.start_mm, o.end_mm))
        if min(hi, o_hi) - max(lo, o_lo) > REACH_MM:
            return True
    return False


def _dimension_on(dimensions, axis, fixed, lo, hi) -> bool:
    """Does an authored dimension END on this line?

    A dimension whose extension line lands on a partition is the
    architect stating where that partition is. It is read as EVIDENCE
    about the line's position; no value is taken from it here.
    """
    for d in dimensions or ():
        for x, y in _dim_points(d):
            v = x if axis == "V" else y
            along = y if axis == "V" else x
            if abs(v - fixed) <= ALIGN_MM and lo - ALIGN_MM <= along <= \
                    hi + ALIGN_MM:
                return True
    return False


def _dim_points(d) -> list:
    out = []
    for name in ("defpoints", "points", "extension_points"):
        pts = getattr(d, name, None)
        if pts:
            for p in pts:
                try:
                    out.append((float(p[0]), float(p[1])))
                except Exception:      # noqa: BLE001
                    continue
    for a, b in (("x1", "y1"), ("x2", "y2"), ("x", "y")):
        if hasattr(d, a) and hasattr(d, b):
            try:
                out.append((float(getattr(d, a)), float(getattr(d, b))))
            except Exception:      # noqa: BLE001
                continue
    return out


def _separates_observations(observations, axis, fixed, lo, hi,
                            arr=None) -> bool:
    """Is there a named space in the strip on EACH side of this line?

    THE STRIP, not the half-plane. The first version of this asked
    whether any observation lay anywhere to the west and anywhere to the
    east, which is true of every line in a building — including the front
    of P7757's kitchen counter, whose west "side" is 500 mm of worktop
    with the whole rest of the villa behind it.

    Each side now reaches only as far as the next parallel line the
    drawing puts there. A worktop has nothing named in its 500 mm; two
    rooms either side of a partition each have their own stamp.
    """
    edges = [None, None]
    if arr is not None:
        edges[0] = arr.next_coord(axis, fixed, lo, hi, -1)
        edges[1] = arr.next_coord(axis, fixed, lo, hi, +1)
    low, high = False, False
    for o in observations or ():
        along = o.y if axis == "V" else o.x
        across = o.x if axis == "V" else o.y
        if not (lo <= along <= hi):
            continue
        if across < fixed:
            if edges[0] is None or across > edges[0]:
                low = True
        elif across > fixed:
            if edges[1] is None or across < edges[1]:
                high = True
    return low and high


def _repeated(cross_plan, axis, fixed, lo, hi, region_id) -> bool:
    """Does a line at the same place in ANOTHER region look like this one?"""
    key = (axis, round(fixed, 1), round(lo, 1), round(hi, 1))
    return len(cross_plan.get(key, set()) - {region_id}) > 0


def cross_plan_index(by_region) -> dict:
    """Lines keyed by their REGION-LOCAL geometry, across every region.

    A villa's first floor repeats its ground floor's risers, shafts and
    party walls at the same place relative to the drawing's own origin.
    That repetition is evidence; the absolute coordinates are not.
    """
    out: dict = {}
    for region_id, (origin, lines) in by_region.items():
        ox, oy = origin
        for c in lines:
            lo, hi = _iv(c)
            if c.axis == "V":
                key = ("V", round(c.fixed_mm - ox, 1),
                       round(lo - oy, 1), round(hi - oy, 1))
            elif c.axis == "H":
                key = ("H", round(c.fixed_mm - oy, 1),
                       round(lo - ox, 1), round(hi - ox, 1))
            else:
                continue
            out.setdefault(key, set()).add(region_id)
    return out


# ----------------------------------------------------------------- assess

def _fitting_fronts(walls, fittings) -> dict:
    """(axis, coord) -> the stretches that are the FRONT of a fitting."""
    out: dict = {}
    lin = dict(fittings or {})
    if not lin:
        return out
    for w in walls or ():
        st = lin.get(w.wall_id)
        if st is None:
            continue
        for which in ("A", "B"):
            fixed = w.face_a_mm if which == "A" else w.face_b_mm
            if abs(fixed - st.far_face_mm) > COLLINEAR_MM:
                continue
            for lo, hi in w.face_stretches(which):
                out.setdefault((w.axis, round(fixed, 1)),
                               []).append((lo, hi))
    return out


def _on_a_fitting_front(fronts, axis, fixed_mm, lo, hi) -> bool:
    for a, b in fronts.get((axis, round(fixed_mm, 1)), ()):
        if min(hi, b) - max(lo, a) > COLLINEAR_MM:
            return True
    return False


def assess(lines, *, region_id="DR-001", walls=(), candidates=(),
           openings=(), dimensions=(), observations=(), cross_plan=None,
           origin=(0.0, 0.0), arrangement=None,
           fittings=None) -> PartitionReport:
    """Ask every set-aside line what evidence it actually has.

    `lines` are round 6A's set-aside lines — a face of no wall, with floor
    on both sides. `candidates` is the region's whole drawn set, so a
    junction can be seen. Nothing here looks at how big the spaces on
    either side are.
    """
    rep = PartitionReport(region_id=region_id)
    faces = _band_faces(walls)
    fronts = _fitting_fronts(walls, fittings)
    xplan = cross_plan or {}
    ox, oy = origin

    runs = _merge(lines, openings)
    for n, line in enumerate(sorted(
            runs, key=lambda c: (c.axis, c.fixed_mm, min(_iv(c)))), 1):
        lo, hi = _iv(line)
        cand = Candidate(
            candidate_id=f"SLP-{region_id}-{n:04d}",
            region_id=region_id,
            source_entity_id=line.object_ids[0],
            source_entity_ids=tuple(line.object_ids),
            source_layer=line.source_layer,
            axis=line.axis, fixed_mm=line.fixed_mm,
            start_mm=lo, end_mm=hi)

        if cand.length_mm < MIN_LENGTH_MM:
            cand.why = ("shorter than the thinnest wall this project "
                        "recognises, so it is not a partition")
            rep.candidates.append(cand)
            continue

        # ROUND 6D. A line that IS the front of a fitting is furniture,
        # however much evidence it collects. A counter runs wall to wall,
        # continues an alignment and often has an opening beside it —
        # every one of those tokens is true of it and none of them makes
        # it a partition.
        if _on_a_fitting_front(fronts, line.axis, line.fixed_mm, lo, hi):
            cand.why = ("this line is the front face of a band standing "
                        "on a wall — a fitting, not a partition")
            rep.candidates.append(cand)
            continue

        ev = []
        a = _meets_a_band(faces, line.axis, lo, line.fixed_mm)
        b = _meets_a_band(faces, line.axis, hi, line.fixed_mm)
        if a and b:
            ev.append(EV_TERMINATES_AT_ESTABLISHED_WALLS)
        elif a or b:
            ev.append(EV_ONE_END_MEETS_A_WALL)
        if _crosses_here(candidates, line.axis, line.fixed_mm, lo, hi):
            ev.append(EV_T_OR_L_JUNCTION)
        face_mm, band_id = _aligned_band(faces, line.axis, line.fixed_mm,
                                         lo, hi)
        if band_id:
            ev.append(EV_CONTINUES_AN_ALIGNMENT)
        if _opening_on(openings, line.axis, line.fixed_mm, lo, hi):
            ev.append(EV_HOSTS_AN_OPENING)
        if line.axis == "V":
            key = ("V", round(line.fixed_mm - ox, 1),
                   round(lo - oy, 1), round(hi - oy, 1))
        else:
            key = ("H", round(line.fixed_mm - oy, 1),
                   round(lo - ox, 1), round(hi - ox, 1))
        if len(xplan.get(key, set()) - {region_id}) > 0:
            ev.append(EV_REPEATED_ACROSS_PLANS)
        if _dimension_on(dimensions, line.axis, line.fixed_mm, lo, hi):
            ev.append(EV_AUTHORED_DIMENSION)
        if _separates_observations(observations, line.axis, line.fixed_mm,
                                   lo, hi, arrangement):
            ev.append(EV_SEPARATES_OBSERVATIONS)

        cand.evidence = tuple(ev)
        strong = [t for t in ev if t in STRONG]
        if strong and len(ev) >= MIN_TOKENS:
            cand.topology_authority = TOPOLOGY_ESTABLISHED
            cand.status = RESULT_B
            cand.why = (f"anchored by {strong[0]} and corroborated by "
                        f"{len(ev)} statements in total")
        else:
            cand.why = ("no strong architectural evidence, or only one "
                        "statement about it. Dividing a region is not "
                        "evidence of being a partition")
            rep.candidates.append(cand)
            continue

        # ---- §5: where does the floor actually stop? ------------------
        fev = []
        if band_id:
            fev.append(FACE_FROM_A_CONTINUING_BAND)
            cand.clear_face_mm = face_mm
            cand.clear_face_band_id = band_id
        if _dimension_on(dimensions, line.axis, line.fixed_mm, lo, hi):
            fev.append(FACE_FROM_A_DIMENSION)
        jamb = _jamb_face(openings, line.axis, line.fixed_mm, lo, hi)
        if jamb is not None and FACE_FROM_A_CONTINUING_BAND not in fev:
            fev.append(FACE_FROM_A_JAMB)
            cand.clear_face_mm = jamb
        cand.face_evidence = tuple(fev)
        if FACE_FROM_A_CONTINUING_BAND in fev or FACE_FROM_A_JAMB in fev:
            cand.clear_face_authority = CLEAR_FACE_ESTABLISHED
            cand.status = RESULT_A
            cand.why += (
                ". Its face position comes from the established band "
                f"{band_id} it continues, not from itself"
                if band_id else
                ". Its face position comes from the reveals of an opening "
                "drawn in it, not from itself")
        else:
            cand.why += (". Nothing says where its faces are, so the "
                         "topology is released and the clear area is not")
        rep.candidates.append(cand)

    rep.notes["material_is_zero_by_construction"] = (
        "every candidate here carries MATERIAL_WALL_NOT_ESTABLISHED. §6 is "
        "not a threshold that could be crossed; it is what a line is")
    return rep


def boundary_candidates(rep: PartitionReport, lines) -> list:
    """The set-aside lines that have earned the right to bound a space."""
    keep = set()
    for c in rep.established():
        keep |= set(c.source_entity_ids or (c.source_entity_id,))
    return [line for line in lines if line.object_id in keep]


def closure_candidates(rep: PartitionReport, lines):
    """Close the doorway in an established single-line partition.

    A partition with a door in it is two pieces with a hole between them.
    The pieces bound; the HOLE has to be closed too, or the flood walks
    through it and the two rooms the partition separates are measured as
    one. The closure carries ZERO material — its id says PORTAL, exactly
    as an opening's does — and it exists only inside a run this module
    has already established.
    """
    from engine.boundary_match import SRC_VECTOR_OPENING_JAMB
    from engine.boundary_match import VectorCandidate

    drawn: dict = {}
    for c in lines:
        if c.axis not in ("H", "V"):
            continue
        drawn.setdefault((c.axis, round(c.fixed_mm / COLLINEAR_MM)),
                         []).append(_iv(c))
    out = []
    for cand in rep.established():
        key = (cand.axis, round(cand.fixed_mm / COLLINEAR_MM))
        pieces = sorted(drawn.get(key, []))
        pos = cand.start_mm
        n = 0
        for lo, hi in pieces:
            if hi <= cand.start_mm or lo >= cand.end_mm:
                continue
            if lo - pos > REACH_MM:
                n += 1
                out.append(VectorCandidate(
                    object_id=f"PORTAL-{cand.candidate_id}-G{n}",
                    axis=cand.axis, fixed_mm=cand.fixed_mm,
                    start_mm=pos, end_mm=lo,
                    source_type=SRC_VECTOR_OPENING_JAMB,
                    validation_class="ESTABLISHED"))
            pos = max(pos, hi)
        if cand.end_mm - pos > REACH_MM:
            n += 1
            out.append(VectorCandidate(
                object_id=f"PORTAL-{cand.candidate_id}-G{n}",
                axis=cand.axis, fixed_mm=cand.fixed_mm,
                start_mm=pos, end_mm=cand.end_mm,
                source_type=SRC_VECTOR_OPENING_JAMB,
                validation_class="ESTABLISHED"))
    return out


def face_authority(rep: PartitionReport) -> dict:
    """object id -> whether its clear face is established, and from where."""
    out = {}
    for c in rep.established():
        for oid in (c.source_entity_ids or (c.source_entity_id,)):
            out[oid] = (c.clear_face_authority, c.clear_face_mm,
                        c.clear_face_band_id, c.candidate_id)
    return out
