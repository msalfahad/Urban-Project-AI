"""A stair is not a room-floor polygon, and its treads are not tiles.

Round 6C found a stair tread carrying 1.2 m2 of "floor" and refused to
release it. Refusing is not measuring. On P7757 the stair finish is
MARBLE while the floor around it is PORCELAIN — **a project rule, not a
universal one** — and marble is bought by the piece:

    TREAD_M2     every tread, measured from its own polygon
    RISER_M2     every riser, width by height
    LANDING_M2   the landing polygon
    NOSING_LM    the exposed front edges
    SKIRTING_LM  separately again, where the drawing establishes it

Four numbers and a fifth, and none of them is added to another: square
metres and linear metres are different quantities and a stair that
reports one number has already lost the argument.

WHAT A STAIR LOOKS LIKE IN PLAN

A run of parallel lines at a near-constant pitch, spanning a common
interval, inside one enclosure. That is a stair — and it is also a
louvre, a grating and a run of shelving, so this module says STAIR only
where the drawing gives it a stair's own evidence, and NOT_ESTABLISHED
otherwise. Decorative parallel lines are refused.

WHAT A PLAN CANNOT SAY

A plan does not carry a riser height. Without section evidence the riser
quantity is `RISER_QUANTITY_NOT_ESTABLISHED` — never a default, never a
standard rise, never treads-minus-one arithmetic dressed up as geometry.
The same for a tread nobody drew: `TREAD_QUANTITY_NOT_ESTABLISHED`.

    DO NOT ASSUME treads = risers, OR treads = risers - 1

CURVED AND WINDER STAIRS

Every tread is measured from ITS OWN polygon. No constant width times a
constant going times a count: a winder's treads are wedges of different
sizes and the marble is cut to each of them.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from engine import cad_profile as cprofile
from engine import space_enclosure as enc

MODEL = "STAIR_ASSEMBLY_TREADS_RISERS_LANDINGS_V2"

# --- what a stair is made of --------------------------------------------
STAIR_ASSEMBLY = "STAIR_ASSEMBLY"
STAIR_FLIGHT = "STAIR_FLIGHT"
STAIR_TREAD = "STAIR_TREAD"
STAIR_RISER = "STAIR_RISER"
STAIR_LANDING = "STAIR_LANDING"
PARTS = (STAIR_ASSEMBLY, STAIR_FLIGHT, STAIR_TREAD, STAIR_RISER,
         STAIR_LANDING)

# --- §11 what the drawing SHOWS, before anything is reconstructed -------
OBS_PARALLEL_RUN = "A_RUN_OF_PARALLEL_LINES_AT_A_TREAD_GOING"
OBS_ARC_RING = "CONCENTRIC_ARCS_WITH_LINES_POINTING_AT_THEIR_CENTRE"
OBS_STAIR_LABEL = "A_STAIR_LABEL"
OBSERVATION_KINDS = (OBS_PARALLEL_RUN, OBS_ARC_RING, OBS_STAIR_LABEL)

MAPPED = "MAPPED_TO_STAIR_ASSEMBLY"
UNRESOLVED_OBSERVATION = "STAIR_OBSERVATION_UNRESOLVED"
# A run the drawing shows and the evidence REFUSES is resolved, not
# unresolved: hatching in the corner of a plate is not a staircase
# nobody reconstructed, it is not a staircase.
NOT_A_STAIR_ON_EVIDENCE = "NOT_A_STAIR_ON_EVIDENCE"
OBSERVATION_STATES = (MAPPED, UNRESOLVED_OBSERVATION,
                      NOT_A_STAIR_ON_EVIDENCE)

# --- §9 what KIND of stair it is ----------------------------------------
MAIN_INTERIOR_STAIR = "MAIN_INTERIOR_STAIR"
SECONDARY_INTERIOR_STAIR = "SECONDARY_INTERIOR_STAIR"
SERVICE_STAIR = "SERVICE_STAIR"
EXTERIOR_STEPS = "EXTERIOR_STEPS"
LANDSCAPE_STEPS = "LANDSCAPE_STEPS"
STAIR_ROLE_UNKNOWN = "STAIR_ROLE_UNKNOWN"
STAIR_ROLES = (MAIN_INTERIOR_STAIR, SECONDARY_INTERIOR_STAIR,
               SERVICE_STAIR, EXTERIOR_STEPS, LANDSCAPE_STEPS,
               STAIR_ROLE_UNKNOWN)

# §16. A stair is not marble because it is a stair.
FINISH_NOT_CONFIRMED = "STAIR_FINISH_NOT_CONFIRMED"

# --- how it runs ---------------------------------------------------------
STRAIGHT = "STRAIGHT"
L_SHAPED = "L_SHAPED"
U_SHAPED = "U_SHAPED"
WINDER = "WINDER"
CURVED = "CURVED"
SPIRAL = "SPIRAL"
CONFIGURATION_NOT_ESTABLISHED = "STAIR_CONFIGURATION_NOT_ESTABLISHED"

# --- what a plan cannot answer -------------------------------------------
RISER_NOT_ESTABLISHED = "RISER_QUANTITY_NOT_ESTABLISHED"
TREAD_NOT_ESTABLISHED = "TREAD_QUANTITY_NOT_ESTABLISHED"
FLIGHTS_OVERLAP = "FLIGHTS_OF_ONE_STAIR_OVERLAP_EACH_OTHER"
LANDING_NOT_ESTABLISHED = "LANDING_QUANTITY_NOT_ESTABLISHED"
SKIRTING_NOT_ESTABLISHED = "STAIR_SKIRTING_NOT_ESTABLISHED"
FLOOR_TO_FLOOR_NOT_ESTABLISHED = "FLOOR_TO_FLOOR_HEIGHT_NOT_ESTABLISHED"
PLAN_AND_SECTION_DISAGREE = "PLAN_AND_SECTION_DISAGREE"
NOT_A_STAIR = "PARALLEL_LINES_WITH_NO_STAIR_EVIDENCE"

# --- the evidence a run of lines has to have -----------------------------
EV_CONSTANT_PITCH = "PARALLEL_LINES_AT_A_CONSTANT_PITCH"
EV_SPAN_TOGETHER = "THEY_SPAN_THE_SAME_INTERVAL"
EV_INSIDE_ONE_CELL = "THEY_LIE_INSIDE_ONE_ENCLOSED_CELL"
EV_STAIR_LABEL = "A_STAIR_LABEL_STANDS_IN_THAT_CELL"
EV_GOING_IS_A_STAIR_GOING = "THE_PITCH_IS_A_TREAD_GOING"
EVIDENCE = (EV_CONSTANT_PITCH, EV_SPAN_TOGETHER, EV_INSIDE_ONE_CELL,
            EV_STAIR_LABEL, EV_GOING_IS_A_STAIR_GOING)

# A stair has at least this many treads drawn before a run of lines is a
# flight rather than two lines that happen to be parallel.
MIN_TREADS = 3

# A tread's going, in millimetres. NOT a rule about what a going should
# be — a bound on what a drawn pitch may be and still be read as one.
# Below the first figure the lines are hatching; above the second they
# are not treads of a stair anybody walks up.
MIN_GOING_MM = 150.0
MAX_GOING_MM = 450.0

# Two pitches are the same pitch within this. The enclosure's own join.
SAME_PITCH_MM = enc.COLLINEAR_JOIN_MM * 10.0

# A cell inside the footprint deeper than the largest going is a landing
# rather than a tread.
LANDING_MIN_MM = MAX_GOING_MM

# --- §13 what a piece of floor BETWEEN the flights actually is ----------
#
# A staircase turns on a LANDING. It does not turn on the floor plate it
# arrives at, on the void its flights wind around, or on the circulation
# the room keeps beside it. Round 6D took every piece left between the
# flights for a landing, and one of them was 11.93 m2 — a floor plate
# wearing a landing's name, and, had a finish been confirmed, marble
# billed over porcelain on the same square metre (§16).
FLOOR_PLATE = "FLOOR_PLATE"
OPEN_VOID = "OPEN_VOID"
CIRCULATION_FLOOR = "CIRCULATION_FLOOR"
LANDING_ROLE_UNRESOLVED = "WHAT_THIS_PIECE_IS_IS_NOT_ESTABLISHED"
BETWEEN_FLIGHT_ROLES = (STAIR_LANDING, FLOOR_PLATE, OPEN_VOID,
                        CIRCULATION_FLOOR, LANDING_ROLE_UNRESOLVED)
NOT_A_STAIR_LANDING = "NOT_A_STAIR_LANDING"

# A landing is a piece of the STAIR: about as wide as the flights it
# joins and no longer than a couple of them. Larger than that and the
# stair stands on it rather than turns on it. A multiple of the drawn
# flight width, never an area: the drawing decides the scale.
LANDING_MAX_WIDTHS = 2.5

# Two pieces touch when they come this close together.
CONTACT_MM = SAME_PITCH_MM

# A stair is at least this wide, or it is a ladder in a shaft. The
# project's own thinnest wall, doubled: nothing new is chosen.
MIN_WIDTH_MM = cprofile.MIN_WALL_THICKNESS_MM * 2.0

# A STAIR FILLS ITS CELL. A run of hatching in the corner of a room is
# parallel, pitched and inside an enclosure too — and it covers a few
# per cent of it. A share, never an area: the cell decides the scale.
STAIR_CELL_SHARE = 0.25
NOT_ENOUGH_OF_THE_CELL = "THE_RUN_COVERS_TOO_LITTLE_OF_THE_CELL_IT_IS_IN"


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "PARTS": list(PARTS),
        "MIN_TREADS": MIN_TREADS,
        "MIN_GOING_MM": MIN_GOING_MM,
        "MAX_GOING_MM": MAX_GOING_MM,
        "SAME_PITCH_MM": SAME_PITCH_MM,
        "LANDING_MIN_MM": LANDING_MIN_MM,
        "MIN_WIDTH_MM": MIN_WIDTH_MM,
        "STAIR_CELL_SHARE": STAIR_CELL_SHARE,
        "LANDING_MAX_WIDTHS": LANDING_MAX_WIDTHS,
        "CONTACT_MM": CONTACT_MM,
        "BETWEEN_FLIGHT_ROLES": list(BETWEEN_FLIGHT_ROLES),
        "STAIR_ROLES": list(STAIR_ROLES),
        "why": {
            "a_landing_is_a_piece_of_the_stair": (
                "a stair turns on a landing, arrives at a floor plate, "
                "winds around a void and stands beside circulation. "
                "Only the first is stair finish, and calling the other "
                "three landings bills marble over porcelain"),
            "a_kind_of_stair_is_not_a_width": (
                "the widest run in a drawing is not the main stair of a "
                "building. What a main stair does is carry a storey, and "
                "where nothing says which storeys a run connects, its "
                "kind is UNKNOWN rather than guessed"),
            "a_stair_fills_its_cell": (
                "a run of hatching is parallel, pitched and inside an "
                "enclosure as well. What a stair also does is take up "
                "its cell, and a share says so at any scale"),
            "a_riser_needs_a_section": (
                "a plan carries no height. Without section evidence the "
                "riser quantity is NOT ESTABLISHED, and no standard rise "
                "is borrowed from anywhere"),
            "counts_are_not_arithmetic": (
                "treads = risers and treads = risers - 1 are both true of "
                "some stairs and neither is derived here. Each is counted "
                "from what is drawn"),
            "each_tread_from_its_own_polygon": (
                "a winder's treads are wedges of different sizes. A "
                "constant width times a constant going times a count is "
                "the wrong quantity for every one of them"),
            "m2_and_lm_are_not_added": (
                "TREAD_M2, RISER_M2 and LANDING_M2 are areas; NOSING_LM "
                "and SKIRTING_LM are lengths. They are reported apart"),
            "no_waste_here": (
                "this is the MEASURED NET quantity. A waste factor and a "
                "procurement quantity are separate numbers, applied "
                "later, by an owner-approved rule"),
        },
    }


def model_hash() -> str:
    parts = ([MODEL] + list(PARTS) + list(EVIDENCE)
             + list(OBSERVATION_KINDS) + list(STAIR_ROLES)
             + list(OBSERVATION_STATES) + list(BETWEEN_FLIGHT_ROLES)
             + [FINISH_NOT_CONFIRMED, NOT_A_STAIR_LANDING]
             + [STRAIGHT, L_SHAPED, U_SHAPED, WINDER, CURVED, SPIRAL,
                CONFIGURATION_NOT_ESTABLISHED, RISER_NOT_ESTABLISHED,
                TREAD_NOT_ESTABLISHED, LANDING_NOT_ESTABLISHED,
                SKIRTING_NOT_ESTABLISHED, PLAN_AND_SECTION_DISAGREE,
                NOT_A_STAIR]
             + [str(v) for v in (MIN_TREADS, MIN_GOING_MM, MAX_GOING_MM,
                                 SAME_PITCH_MM, LANDING_MIN_MM,
                                 MIN_WIDTH_MM, STAIR_CELL_SHARE,
                                 LANDING_MAX_WIDTHS, CONTACT_MM)]
             + [NOT_ENOUGH_OF_THE_CELL, FLIGHTS_OVERLAP])
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


# ------------------------------------------------------------- the objects

@dataclass
class Observation:
    """One stair-like thing the drawing shows. Not yet a staircase."""

    observation_id: str = ""
    region_id: str = ""
    kind: str = ""
    at_mm: tuple = ()
    extent_mm: tuple = ()
    lines: int = 0
    evidence: tuple = ()
    status: str = UNRESOLVED_OBSERVATION
    stair_id: str = ""
    why: str = ""

    def record(self) -> dict:
        return {
            "stair_observation_id": self.observation_id,
            "drawing_region_id": self.region_id,
            "observation_kind": self.kind,
            "at_mm": [round(v, 1) for v in self.at_mm],
            "extent_mm": [round(v, 1) for v in self.extent_mm],
            "lines": self.lines,
            "evidence": list(self.evidence),
            "status": self.status,
            "stair_id": self.stair_id,
            "why": self.why,
        }


@dataclass
class Tread:
    """One tread, measured from its own polygon."""

    tread_id: str = ""
    index: int = 0
    polygon_wkt: str = ""
    area_m2: float = 0.0
    going_mm: float = 0.0          # front edge to back edge
    width_mm: float = 0.0          # the walking width
    nosing_length_mm: float = 0.0  # the exposed front edge
    front_edge_wkt: str = ""
    back_edge_wkt: str = ""
    inner_edge_wkt: str = ""
    outer_edge_wkt: str = ""
    rectangular: bool = True
    cad_provenance: tuple = ()
    status: str = "TREAD_MEASURED"

    def record(self) -> dict:
        return {
            "tread_id": self.tread_id,
            "index": self.index,
            "tread_area_m2": round(self.area_m2, 4),
            "going_mm": round(self.going_mm, 1),
            "width_mm": round(self.width_mm, 1),
            "nosing_length_mm": round(self.nosing_length_mm, 1),
            "rectangular": self.rectangular,
            "front_edge_wkt": self.front_edge_wkt,
            "back_edge_wkt": self.back_edge_wkt,
            "inner_edge_wkt": self.inner_edge_wkt,
            "outer_edge_wkt": self.outer_edge_wkt,
            "polygon_wkt_mm": self.polygon_wkt,
            "cad_provenance": list(self.cad_provenance),
            "status": self.status,
        }


@dataclass
class Riser:
    """One riser. Its face area needs a height a plan does not carry."""

    riser_id: str = ""
    index: int = 0
    width_mm: float = 0.0
    height_mm: float | None = None
    area_m2: float | None = None
    height_source: str = RISER_NOT_ESTABLISHED
    edge_wkt: str = ""
    status: str = RISER_NOT_ESTABLISHED

    def record(self) -> dict:
        return {
            "riser_id": self.riser_id,
            "index": self.index,
            "riser_width_mm": round(self.width_mm, 1),
            "riser_height_mm": (None if self.height_mm is None
                                else round(self.height_mm, 1)),
            "riser_face_area_m2": (None if self.area_m2 is None
                                   else round(self.area_m2, 4)),
            "height_source": self.height_source,
            "edge_wkt": self.edge_wkt,
            "status": self.status,
        }


@dataclass
class Landing:
    """A piece of floor between the flights, and what it IS (§13)."""

    landing_id: str = ""
    polygon_wkt: str = ""
    area_m2: float = 0.0
    length_mm: float = 0.0
    width_mm: float = 0.0
    role: str = LANDING_ROLE_UNRESOLVED
    touches_flight_ends: int = 0
    touches_flight_sides: int = 0
    role_evidence: tuple = ()
    status: str = NOT_A_STAIR_LANDING

    @property
    def is_stair_landing(self) -> bool:
        return self.role == STAIR_LANDING

    def record(self) -> dict:
        return {
            "landing_id": self.landing_id,
            "role": self.role,
            "piece_area_m2": round(self.area_m2, 4),
            # THE AREA IS ONLY A LANDING AREA WHEN THE PIECE IS ONE.
            # A floor plate reported as landing_area_m2 is marble over
            # porcelain on the same square metre.
            "landing_area_m2": (round(self.area_m2, 4)
                                if self.is_stair_landing else None),
            "landing_length_mm": round(self.length_mm, 1),
            "landing_width_mm": round(self.width_mm, 1),
            "touches_flight_ends": self.touches_flight_ends,
            "touches_flight_sides": self.touches_flight_sides,
            "role_evidence": list(self.role_evidence),
            "polygon_wkt_mm": self.polygon_wkt,
            "status": self.status,
        }


@dataclass
class Flight:
    flight_id: str = ""
    axis: str = ""                 # the axis the treads are drawn on
    direction_mm: tuple = ()       # the interval the flight climbs over
    width_mm: float = 0.0
    treads: list = field(default_factory=list)
    risers: list = field(default_factory=list)
    configuration: str = CONFIGURATION_NOT_ESTABLISHED
    evidence: tuple = ()
    centre_mm: tuple = ()      # the ring's centre, or the flight's own
    span_mm: tuple = ()        # inner/outer radius, or the drawn extent

    @property
    def tread_area_m2(self) -> float:
        return sum(t.area_m2 for t in self.treads)

    @property
    def nosing_lm(self) -> float:
        return sum(t.nosing_length_mm for t in self.treads) / 1000.0

    def record(self) -> dict:
        return {
            "flight_id": self.flight_id,
            "axis": self.axis,
            "climbs_over_mm": [round(v, 1) for v in self.direction_mm],
            "stair_width_m": round(self.width_mm / 1000.0, 3),
            "number_of_treads": len(self.treads),
            "number_of_risers": len(self.risers),
            "TREAD_M2": round(self.tread_area_m2, 4),
            # NO RISERS IS NOT ZERO RISERS. An empty sum reads as a
            # measured nothing, and nothing here has been measured.
            "RISER_M2": (None if not self.risers
                         or any(r.area_m2 is None for r in self.risers)
                         else round(sum(r.area_m2 or 0.0
                                        for r in self.risers), 4)),
            "NOSING_LM": round(self.nosing_lm, 3),
            "configuration": self.configuration,
            "evidence": list(self.evidence),
            "centre_mm": [round(v, 1) for v in self.centre_mm],
            "span_mm": [round(v, 1) for v in self.span_mm],
            "treads": [t.record() for t in self.treads],
            "risers": [r.record() for r in self.risers],
            "counts_are_not_derived_from_each_other": (
                "treads and risers are each counted from what is drawn. "
                "Neither is the other plus or minus one here"),
        }


@dataclass
class Assembly:
    stair_id: str = ""
    region_id: str = ""
    floor_from: str = ""
    floor_to: str = ""
    space_id: str = ""
    footprint_wkt: str = ""
    footprint_area_m2: float = 0.0
    containing_space_area_m2: float | None = None
    flights: list = field(default_factory=list)
    landings: list = field(default_factory=list)
    configuration: str = CONFIGURATION_NOT_ESTABLISHED
    stair_role: str = STAIR_ROLE_UNKNOWN
    role_evidence: tuple = ()
    interior_exterior: str = ""
    finish: str = FINISH_NOT_CONFIRMED
    finish_source: str = "OWNER_RULE_REQUEST"
    physical_stair_id: str = ""
    finish_rule: str = ""
    skirting_lm: float | None = None
    skirting_status: str = SKIRTING_NOT_ESTABLISHED
    exceptions: tuple = ()
    evidence: tuple = ()

    @property
    def tread_m2(self) -> float:
        return sum(f.tread_area_m2 for f in self.flights)

    @property
    def landing_m2(self) -> float:
        # ONLY the pieces this stair turns on. The floor it lands on is
        # floor, and it is measured by the floor, once (§13, §16).
        return sum(x.area_m2 for x in self.landings if x.is_stair_landing)

    @property
    def not_stair_landing_m2(self) -> float:
        return sum(x.area_m2 for x in self.landings
                   if not x.is_stair_landing)

    @property
    def nosing_lm(self) -> float:
        return sum(f.nosing_lm for f in self.flights)

    @property
    def riser_m2(self):
        vals = [r.area_m2 for f in self.flights for r in f.risers]
        if not vals or any(v is None for v in vals):
            return None          # not established is not zero
        return sum(vals)

    def record(self) -> dict:
        return {
            "stair_id": self.stair_id,
            "drawing_region_id": self.region_id,
            "floor_from": self.floor_from or FLOOR_TO_FLOOR_NOT_ESTABLISHED,
            "floor_to": self.floor_to or FLOOR_TO_FLOOR_NOT_ESTABLISHED,
            "physical_space_id": self.space_id,
            "configuration": self.configuration,
            "stair_role": self.stair_role,
            "role_evidence": list(self.role_evidence),
            "interior_exterior": self.interior_exterior,
            "finish": self.finish,
            "finish_source": self.finish_source,
            "physical_stair_id": self.physical_stair_id,
            "flight_count": len(self.flights),
            "footprint_area_m2": round(self.footprint_area_m2, 4),
            "containing_space_area_m2": (
                None if self.containing_space_area_m2 is None
                else round(self.containing_space_area_m2, 4)),
            "footprint_wkt_mm": self.footprint_wkt,
            "MEASURED_NET": {
                # A stair whose flights overlap cannot have both their
                # treads, and neither can be chosen: the quantity is NOT
                # ESTABLISHED rather than the larger of two readings.
                "TREAD_M2": (None if TREAD_NOT_ESTABLISHED
                             in self.exceptions
                             else round(self.tread_m2, 4)),
                "RISER_M2": (None if self.riser_m2 is None
                             else round(self.riser_m2, 4)),
                "LANDING_M2": round(self.landing_m2, 4),
                "NOSING_LM": round(self.nosing_lm, 3),
                "STAIR_SKIRTING_LM": self.skirting_lm,
                "this_is": ("the measured net quantity. No waste factor "
                            "and no procurement quantity are applied "
                            "here, and no price exists"),
            },
            "skirting_status": self.skirting_status,
            "finish_rule": self.finish_rule or "NO_PROJECT_FINISH_RULE",
            "flights": [f.record() for f in self.flights],
            "landings": [x.record() for x in self.landings
                         if x.is_stair_landing],
            # EVERY piece between the flights, including the ones that
            # are not landings and the floor they belong to instead.
            "pieces_between_the_flights": [x.record()
                                           for x in self.landings],
            "not_stair_landing_m2": round(self.not_stair_landing_m2, 4),
            "exceptions": list(self.exceptions),
            "evidence": list(self.evidence),
            "floor_finish_owner": (
                "this footprint belongs to the stair. Its area may not "
                "appear again in any floor-finish quantity"),
        }


@dataclass
class StairReport:
    region_id: str = ""
    assemblies: list = field(default_factory=list)
    observations: list = field(default_factory=list)
    refused: list = field(default_factory=list)
    notes: dict = field(default_factory=dict)

    def counts(self) -> dict:
        return {
            "stair_assemblies": len(self.assemblies),
            "flights": sum(len(a.flights) for a in self.assemblies),
            "treads": sum(len(f.treads) for a in self.assemblies
                          for f in a.flights),
            "risers": sum(len(f.risers) for a in self.assemblies
                          for f in a.flights),
            "stair_landings": sum(1 for a in self.assemblies
                                  for x in a.landings
                                  if x.is_stair_landing),
            "pieces_between_flights": sum(len(a.landings)
                                          for a in self.assemblies),
            "pieces_that_are_floor_not_stair": sum(
                1 for a in self.assemblies for x in a.landings
                if x.role in (FLOOR_PLATE, CIRCULATION_FLOOR)),
            "pieces_that_are_void": sum(
                1 for a in self.assemblies for x in a.landings
                if x.role == OPEN_VOID),
            "stair_observations": len(self.observations),
            "observations_mapped": sum(1 for o in self.observations
                                       if o.status == MAPPED),
            "observations_refused_as_not_a_stair": sum(
                1 for o in self.observations
                if o.status == NOT_A_STAIR_ON_EVIDENCE),
            "observations_unresolved": sum(
                1 for o in self.observations
                if o.status == UNRESOLVED_OBSERVATION),
            "runs_refused": len(self.refused),
            "riser_quantity_established": sum(
                1 for a in self.assemblies if a.riser_m2 is not None),
        }

    def record(self) -> dict:
        return {
            "model": MODEL,
            "STAIR_ASSEMBLY_HASH": model_hash(),
            "drawing_region_id": self.region_id,
            "counts": self.counts(),
            "frozen_parameters": frozen_parameters(),
            "assemblies": [a.record() for a in self.assemblies],
            "observations": [o.record() for o in self.observations],
            "refused": list(self.refused),
            "notes": dict(self.notes),
        }


# ------------------------------------------------------------ the detector

def _runs(lines, axis: str) -> list:
    """Parallel drawn lines on one axis, grouped into pitched runs.

    A run is three or more lines, each a tread's going from the last and
    overlapping it along its length. SEVERAL RUNS MAY BE OPEN AT ONCE:
    two flights side by side share their tread positions, and a walk
    that can only follow one of them finds neither.

    A CONSTANT pitch is not required — a winder's goings differ from
    tread to tread, and requiring one would cut every winder into pieces
    and then measure none of them. Constant pitch is recorded as
    evidence where it is true.

    This is also what a louvre, a grating and a run of shelving look
    like, which is why the caller still has to find stair evidence
    around the run.
    """
    rows = []
    for c in lines:
        if getattr(c, "axis", "") != axis:
            continue
        lo, hi = sorted((c.start_mm, c.end_mm))
        rows.append((c.fixed_mm, lo, hi, c))
    rows.sort(key=lambda r: (r[0], r[1], r[2]))
    # TWO LINES LESS THAN A GOING APART ARE ONE STEP'S EDGE. A stair is
    # often drawn with a nosing line just in front of each riser line,
    # and read as two tracks it becomes two overlapping flights that
    # measure the same marble twice.
    merged = []
    for row in rows:
        if merged and row[0] - merged[-1][0] < MIN_GOING_MM \
                and min(merged[-1][2], row[2]) \
                - max(merged[-1][1], row[1]) > MIN_WIDTH_MM:
            prev = merged[-1]
            merged[-1] = (prev[0], min(prev[1], row[1]),
                          max(prev[2], row[2]), prev[3])
            continue
        merged.append(row)
    rows = merged
    open_runs: list = []
    done: list = []
    for row in rows:
        best, best_gap = None, None
        for run in open_runs:
            last = run[-1]
            gap = row[0] - last[0]
            span = min(last[2], row[2]) - max(last[1], row[1])
            if MIN_GOING_MM <= gap <= MAX_GOING_MM and span > MIN_WIDTH_MM:
                if best is None or gap < best_gap:
                    best, best_gap = run, gap
        if best is not None:
            best.append(row)
            continue
        open_runs.append([row])
    for run in open_runs:
        done.extend(_cut(run))
    return done


def _cut(run) -> list:
    """Split a walk where the lines stop being treads of one flight.

    A flight's treads reach nearly as far as each other — a winder's
    shrink from one end to the other, but gradually. A room's own wall
    runs the width of the ROOM and happens to sit a going away from the
    first tread, so it joins the walk; and it gives itself away by
    reaching past its neighbour by more than a tread's going, which is
    the module's own figure and not a new one.
    """
    out, cur = [], []
    for row in run:
        if cur and abs((row[2] - row[1]) - (cur[-1][2] - cur[-1][1])) \
                > MAX_GOING_MM:
            out.append(cur)
            cur = [row]
            continue
        cur.append(row)
    out.append(cur)
    return [r for r in out if len(r) >= MIN_TREADS]


def _polygon(axis: str, f0: float, f1: float, lo: float, hi: float):
    from shapely.geometry import box

    if axis == "H":
        return box(lo, f0, hi, f1)
    return box(f0, lo, f1, hi)


def _edge(axis: str, fixed: float, lo: float, hi: float) -> str:
    from shapely.geometry import LineString

    pts = ([(lo, fixed), (hi, fixed)] if axis == "H"
           else [(fixed, lo), (fixed, hi)])
    return LineString(pts).wkt


def assess(lines, *, region_id: str = "DR-001", spaces=(), labels=(),
           floor_from: str = "", floor_to: str = "", sections=None,
           finish_rule: str = "", skirting_rule=None,
           arcs=(), primitives=()) -> StairReport:
    """Find the stairs in one region and measure what is drawn.

    `spaces` are the region's measured spaces (each with a polygon and an
    identity), `labels` their authored text. `sections` is optional
    section evidence: {stair or region key: {"riser_height_mm": ...,
    "risers": ..., "treads": ...}} — a plan alone never produces a riser
    height, and nothing here invents one.

    Runs that stand in the SAME cell are flights of ONE stair: two
    flights and a landing are one staircase, not two staircases.
    """
    from shapely.wkt import loads

    rep = StairReport(region_id=region_id)
    poly_of = {}
    for sp in spaces or ():
        wkt = getattr(sp, "polygon_wkt", "") or ""
        if not wkt:
            continue
        try:
            poly_of[getattr(sp, "space_id", "")] = loads(wkt)
        except Exception:      # noqa: BLE001
            continue
    stair_points = [(getattr(o, "x", 0.0), getattr(o, "y", 0.0))
                    for o in (labels or ())
                    if "STAIR" in (getattr(o, "text", "") or "").upper()]

    # ---- every run, with the cell it stands in ------------------------
    found = []
    n = 0
    for axis in ("H", "V"):
        for run in _runs(lines, axis):
            n += 1
            goings = [run[i + 1][0] - run[i][0] for i in range(len(run) - 1)]
            ev = [EV_SPAN_TOGETHER]
            if goings and max(goings) - min(goings) <= SAME_PITCH_MM:
                ev.append(EV_CONSTANT_PITCH)
            if goings and all(MIN_GOING_MM <= g <= MAX_GOING_MM
                              for g in goings):
                ev.append(EV_GOING_IS_A_STAIR_GOING)
            f_lo, f_hi = run[0][0], run[-1][0]
            lo = min(r[1] for r in run)
            hi = max(r[2] for r in run)
            foot = _polygon(axis, f_lo, f_hi, lo, hi)
            space_id, cell = "", None
            for sid, g in sorted(poly_of.items()):
                try:
                    if g.intersection(foot).area > foot.area * 0.5:
                        space_id, cell = sid, g
                        break
                except Exception:      # noqa: BLE001
                    continue
            if cell is not None:
                ev.append(EV_INSIDE_ONE_CELL)
            labelled = any(foot.contains(_pt(x, y)) for x, y in stair_points)
            if labelled:
                ev.append(EV_STAIR_LABEL)
            if cell is None and not labelled:
                rep.refused.append({
                    "run_id": f"RUN-{region_id}-{n:03d}",
                    "axis": axis, "lines": len(run),
                    "pitch_mm": round(goings[0], 1) if goings else None,
                    "why": NOT_A_STAIR,
                    "what_would_settle_it": (
                        "an enclosure around it, or a stair label in it")})
                continue
            found.append({"axis": axis, "run": run, "foot": foot,
                          "space_id": space_id, "cell": cell,
                          "ev": ev, "n": n})

    # ---- §12 the curved and winder flights ---------------------------
    #
    # Radial treads about a common centre. A detector that knows only
    # parallel lines does not see a curved stair at all, and silence is
    # the one answer a stair register may not give.
    curved = curved_flights(arcs, primitives, region_id=region_id,
                            sections=sections)
    for ring, flight in curved:
        from shapely.wkt import loads as _loads

        foot = None
        for t in flight.treads:
            g = _loads(t.polygon_wkt)
            foot = g if foot is None else foot.union(g)
        if foot is None:
            continue
        space_id, cell = "", None
        for sid, g in sorted(poly_of.items()):
            try:
                if g.intersection(foot).area > foot.area * 0.5:
                    space_id, cell = sid, g
                    break
            except Exception:      # noqa: BLE001
                continue
        n += 1
        found.append({"axis": "RADIAL", "run": [], "foot": foot,
                      "space_id": space_id, "cell": cell, "n": n,
                      "flight": flight, "ring": ring,
                      "ev": list(flight.evidence)
                      + ([EV_INSIDE_ONE_CELL] if cell is not None else [])})

    # ---- runs in one cell are flights of one stair --------------------
    groups: dict = {}
    for item in found:
        groups.setdefault(item["space_id"] or f"RUN-{item['n']}",
                          []).append(item)

    for k, (key, items) in enumerate(sorted(groups.items()), 1):
        cell = next((it["cell"] for it in items if it["cell"] is not None),
                    None)
        foot = items[0]["foot"]
        for it in items[1:]:
            foot = foot.union(it["foot"])
        labelled = any(EV_STAIR_LABEL in it["ev"] for it in items)
        radial = any(it["axis"] == "RADIAL" for it in items)
        if cell is not None and not labelled and not radial and \
                foot.area < cell.area * STAIR_CELL_SHARE:
            rep.refused.append({
                "run_id": f"RUN-{region_id}-{items[0]['n']:03d}",
                "axis": items[0]["axis"],
                "lines": sum(len(it["run"]) for it in items),
                "pitch_mm": None,
                "why": NOT_ENOUGH_OF_THE_CELL,
                "what_would_settle_it": (
                    f"it covers {round(100 * foot.area / cell.area, 1)}% "
                    "of the cell it stands in, and no stair label stands "
                    "there")})
            continue
        asm = Assembly(
            stair_id=f"SA-{region_id}-{k:03d}", region_id=region_id,
            floor_from=floor_from, floor_to=floor_to,
            space_id=items[0]["space_id"],
            # THE STAIR'S OWN FOOTPRINT, not the room it stands in. The
            # cell's area is reported beside it and never as the stair.
            footprint_wkt=foot.wkt,
            footprint_area_m2=foot.area / 1e6,
            containing_space_area_m2=(None if cell is None
                                      else cell.area / 1e6),
            finish_rule=finish_rule,
            skirting_lm=(skirting_rule or {}).get("skirting_lm"),
            skirting_status=(
                SKIRTING_NOT_ESTABLISHED
                if not (skirting_rule or {}).get("skirting_lm")
                else "FROM_A_PROJECT_RULE"),
            evidence=tuple(sorted({e for it in items for e in it["ev"]})))

        exceptions = []
        for j, it in enumerate(items, 1):
            flight = (it["flight"] if it.get("flight") is not None
                      else _flight(it, region_id, k, j, cell, sections))
            # §13 asks what lies between the FLIGHTS, so the flights have
            # to be on the items before the pieces between them are read.
            it["flight"] = flight
            asm.flights.append(flight)
            if any(r.status == RISER_NOT_ESTABLISHED for r in flight.risers):
                exceptions.append(RISER_NOT_ESTABLISHED)
            if not flight.treads:
                exceptions.append(TREAD_NOT_ESTABLISHED)
            sec = _section_for(sections, flight.flight_id, region_id)
            told = sec.get("treads")
            if told and int(told) != len(flight.treads):
                exceptions.append(PLAN_AND_SECTION_DISAGREE)

        asm.landings.extend(_landings(cell, items, region_id, k))
        axes = {it["axis"] for it in items}
        if len(items) >= 2 and len(axes) > 1:
            asm.configuration = L_SHAPED
        elif len(items) >= 2:
            asm.configuration = U_SHAPED
        elif asm.flights:
            asm.configuration = asm.flights[0].configuration
        # Do two flights of this stair cover the same ground? Then their
        # tread polygons cannot both be marble, and nothing here picks.
        feet = [it["foot"] for it in items]
        for i, fa in enumerate(feet):
            for fb in feet[i + 1:]:
                try:
                    if fa.intersection(fb).area > 1000.0:
                        exceptions.extend([FLIGHTS_OVERLAP,
                                           TREAD_NOT_ESTABLISHED])
                except Exception:      # noqa: BLE001
                    continue
        asm.exceptions = tuple(sorted(set(exceptions)))
        if TREAD_NOT_ESTABLISHED in asm.exceptions:
            for f in asm.flights:
                for t in f.treads:
                    t.status = TREAD_NOT_ESTABLISHED
        rep.assemblies.append(asm)

    # ---- §11 every stair-like thing the drawing shows ----------------
    mapped_ids = {it["n"]: a.stair_id
                  for a in rep.assemblies
                  for it in found
                  if a.footprint_wkt and it["foot"] is not None
                  and it["foot"].intersects(_loads_safe(a.footprint_wkt))}
    for it in found:
        g = it["foot"]
        x0, y0, x1, y1 = (g.bounds if g is not None else (0, 0, 0, 0))
        sid = mapped_ids.get(it["n"], "")
        rep.observations.append(Observation(
            observation_id=f"SO-{region_id}-{it['n']:03d}",
            region_id=region_id,
            kind=(OBS_ARC_RING if it["axis"] == "RADIAL"
                  else OBS_PARALLEL_RUN),
            at_mm=((x0 + x1) / 2.0, (y0 + y1) / 2.0),
            extent_mm=(x0, y0, x1, y1),
            lines=len(it["run"]) or len(it.get("flight").treads) + 1,
            evidence=tuple(it["ev"]),
            status=MAPPED if sid else UNRESOLVED_OBSERVATION,
            stair_id=sid,
            why=("reconstructed as part of this assembly" if sid else
                 "the drawing shows it and this round did not "
                 "reconstruct a stair from it")))
    for x in rep.refused:
        rep.observations.append(Observation(
            observation_id=x["run_id"].replace("RUN-", "SO-"),
            region_id=region_id, kind=OBS_PARALLEL_RUN,
            lines=x.get("lines", 0), evidence=(),
            status=NOT_A_STAIR_ON_EVIDENCE,
            why=f"{x['why']}: {x.get('what_would_settle_it', '')}"))
    for o in (labels or ()):
        text = (getattr(o, "text", "") or "").upper()
        if "STAIR" not in text:
            continue
        x, y = getattr(o, "x", 0.0), getattr(o, "y", 0.0)
        hit = ""
        for a in rep.assemblies:
            try:
                if _loads_safe(a.footprint_wkt).buffer(
                        MAX_GOING_MM * 4).contains(_pt(x, y)):
                    hit = a.stair_id
                    break
            except Exception:      # noqa: BLE001
                continue
        rep.observations.append(Observation(
            observation_id=f"SO-{region_id}-L{abs(hash((x, y))) % 997:03d}",
            region_id=region_id, kind=OBS_STAIR_LABEL, at_mm=(x, y),
            evidence=(EV_STAIR_LABEL,),
            status=MAPPED if hit else UNRESOLVED_OBSERVATION,
            stair_id=hit,
            why=("a stair assembly stands where this label does" if hit
                 else "a stair is named here and none was reconstructed")))

    rep.notes["a_plan_carries_no_height"] = (
        "every riser here is NOT ESTABLISHED unless section evidence was "
        "supplied. No standard rise is assumed")
    rep.notes["no_double_count"] = (
        "a stair's footprint belongs to the stair. Its area may not "
        "appear in any floor-finish quantity as well")
    rep.notes["runs_in_one_cell_are_one_stair"] = (
        "two flights and a landing are one staircase. Counting them as "
        "two would count the landing twice and the stair not at all")
    return rep


def _section_for(sections, flight_id: str, region_id: str) -> dict:
    src = sections or {}
    return dict(src.get(flight_id) or src.get(region_id) or {})


def _flight(item, region_id: str, k: int, j: int, cell, sections) -> Flight:
    """One run of treads, each measured from its own polygon."""
    axis, run = item["axis"], item["run"]
    lo = min(r[1] for r in run)
    hi = max(r[2] for r in run)
    x0, y0, x1, y1 = item["foot"].bounds
    flight = Flight(
        flight_id=f"SF-{region_id}-{k:03d}-{j:02d}", axis=axis,
        direction_mm=(run[0][0], run[-1][0]), width_mm=hi - lo,
        centre_mm=((x0 + x1) / 2.0, (y0 + y1) / 2.0),
        span_mm=(run[0][0], run[-1][0]),
        evidence=tuple(item["ev"]))
    for i in range(len(run) - 1):
        a, b = run[i], run[i + 1]
        # A WINDER'S TREAD IS NOT THE OVERLAP OF TWO LINES. Take the
        # stretch both lines reach over, clipped to the cell the stair
        # stands in, so a wedge is measured as the wedge it is.
        g = _polygon(axis, a[0], b[0], min(a[1], b[1]), max(a[2], b[2]))
        # Clipped to THIS FLIGHT's own footprint, and then to the cell.
        # Two flights side by side share their tread positions, and a
        # tread clipped only to the cell would cover its neighbour's
        # treads as well — a stair measuring more marble than it has.
        for clip in (item["foot"], cell):
            if clip is None:
                continue
            try:
                g = g.intersection(clip)
            except Exception:      # noqa: BLE001
                pass
        if g.is_empty or g.area <= 0:
            continue
        x0, y0, x1, y1 = g.bounds
        width = (x1 - x0) if axis == "H" else (y1 - y0)
        flight.treads.append(Tread(
            tread_id=f"ST-{region_id}-{k:03d}-{j:02d}-{i + 1:02d}",
            index=i + 1, polygon_wkt=g.wkt, area_m2=g.area / 1e6,
            going_mm=b[0] - a[0], width_mm=width,
            nosing_length_mm=a[2] - a[1],
            front_edge_wkt=_edge(axis, a[0], a[1], a[2]),
            back_edge_wkt=_edge(axis, b[0], b[1], b[2]),
            inner_edge_wkt=_edge("V" if axis == "H" else "H",
                                 min(a[1], b[1]), a[0], b[0]),
            outer_edge_wkt=_edge("V" if axis == "H" else "H",
                                 max(a[2], b[2]), a[0], b[0]),
            rectangular=abs((a[2] - a[1]) - (b[2] - b[1])) <= SAME_PITCH_MM,
            cad_provenance=(getattr(a[3], "object_id", ""),
                            getattr(b[3], "object_id", ""))))

    sec = _section_for(sections, flight.flight_id, region_id)
    rise = sec.get("riser_height_mm")
    told = sec.get("risers")
    n_risers = int(told) if told else len(flight.treads)
    for i in range(n_risers):
        w = (flight.treads[min(i, len(flight.treads) - 1)].width_mm
             if flight.treads else flight.width_mm)
        flight.risers.append(Riser(
            riser_id=f"SR-{region_id}-{k:03d}-{j:02d}-{i + 1:02d}",
            index=i + 1, width_mm=w,
            height_mm=(None if rise is None else float(rise)),
            area_m2=(None if rise is None else w * float(rise) / 1e6),
            height_source=(RISER_NOT_ESTABLISHED if rise is None
                           else "SECTION_EVIDENCE"),
            status=(RISER_NOT_ESTABLISHED if rise is None
                    else "RISER_MEASURED")))

    widths = {round(t.width_mm, 1) for t in flight.treads}
    goings = {round(t.going_mm, 1) for t in flight.treads}
    flight.configuration = (STRAIGHT if len(widths) == 1 and len(goings) == 1
                            else WINDER)
    return flight


def _loads_safe(wkt: str):
    from shapely.geometry import Polygon
    from shapely.wkt import loads

    try:
        return loads(wkt)
    except Exception:      # noqa: BLE001
        return Polygon()


def _pt(x: float, y: float):
    from shapely.geometry import Point

    return Point(x, y)


def _climb(flight, foot) -> tuple:
    """The direction this flight climbs in, as a unit vector.

    A flight's treads are drawn across its climb, so the axis the run
    was found on gives the climb directly. A curved flight climbs ROUND
    its ring: at any point that is the tangent, across the radius.
    """
    axis = getattr(flight, "axis", "")
    if axis == "H":
        return (0.0, 1.0)
    if axis == "V":
        return (1.0, 0.0)
    centre = tuple(getattr(flight, "centre_mm", ()) or ())
    if axis == "RADIAL" and len(centre) == 2:
        rx = foot.centroid.x - centre[0]
        ry = foot.centroid.y - centre[1]
        nrm = (rx * rx + ry * ry) ** 0.5
        if nrm > 0:
            return (-ry / nrm, rx / nrm)
    return (0.0, 0.0)


def _at_the_end(g, foot, flight) -> bool:
    """Is this piece off the END of the flight, or beside its SIDE?

    A stair turns on a piece at the end of a flight. The gap a pair of
    parallel flights leaves BETWEEN them is beside both of their sides,
    and it is the stairwell void, not a landing anybody walks on.
    """
    ux, uy = _climb(flight, foot)
    if ux == 0.0 and uy == 0.0:
        return False
    dx = g.centroid.x - foot.centroid.x
    dy = g.centroid.y - foot.centroid.y
    return abs(dx * ux + dy * uy) > abs(dx * -uy + dy * ux)


def _landings(cell, items, region_id: str, n: int) -> list:
    """What the flights of one stair leave BETWEEN them, and what it is.

    Two questions, and Round 6D answered only the first. WHERE the
    leftover pieces are: between the flights, never the rest of the room
    the stair stands in — taking the flights out of the space around
    them made a 1,229 m2 "landing" out of a floor plate on the first run
    of this module. And WHAT each piece is (§13): a stair turns on a
    landing, arrives at a floor plate, winds around a void and stands
    beside circulation, and only the first of those four is stair.
    """
    from shapely.geometry import box

    out = []
    feet = [it["foot"] for it in items]
    if len(feet) < 2:
        return out
    x0 = min(f.bounds[0] for f in feet)
    y0 = min(f.bounds[1] for f in feet)
    x1 = max(f.bounds[2] for f in feet)
    y1 = max(f.bounds[3] for f in feet)
    rest = box(x0, y0, x1, y1)
    for f in feet:
        rest = rest.difference(f)
    if cell is not None:
        try:
            rest = rest.intersection(cell)
        except Exception:      # noqa: BLE001
            pass
    if rest.is_empty:
        return out
    edge = None
    if cell is not None:
        try:
            edge = cell.exterior
        except Exception:      # noqa: BLE001
            edge = None

    for i, g in enumerate(getattr(rest, "geoms", [rest]), 1):
        if g.is_empty or g.area <= 0:
            continue
        bx0, by0, bx1, by1 = g.bounds
        long_mm = max(bx1 - bx0, by1 - by0)
        short_mm = min(bx1 - bx0, by1 - by0)

        ends, sides, widths, ev = 0, 0, [], []
        near = g.buffer(CONTACT_MM)
        for it in items:
            foot, flight = it["foot"], it.get("flight")
            try:
                if not near.intersects(foot):
                    continue
            except Exception:      # noqa: BLE001
                continue
            widths.append(getattr(flight, "width_mm", 0.0) or 0.0)
            if flight is not None and _at_the_end(g, foot, flight):
                ends += 1
            else:
                sides += 1
        width = max(widths) if widths else 0.0
        fits = bool(width) and long_mm <= width * LANDING_MAX_WIDTHS \
            and short_mm >= MIN_GOING_MM
        try:
            reaches_the_room = bool(edge is not None
                                    and near.intersects(edge))
        except Exception:      # noqa: BLE001
            reaches_the_room = False

        # SIZE FIRST. A piece bigger than the flights it lies among is
        # not something a staircase turns on and not a well it winds
        # around: it is floor, and the floor measures it. The 11.93 m2
        # Round 6D called a landing is 7.0 m long beside a 1.25 m
        # flight — a plate of floor between two runs of a stair.
        if not fits and ends >= 2:
            role = LANDING_ROLE_UNRESOLVED
            ev.append("IT_JOINS_THE_ENDS_OF_TWO_FLIGHTS")
            ev.append("AND_IT_IS_FAR_LARGER_THAN_THE_FLIGHTS_IT_JOINS")
        elif not fits:
            role = CIRCULATION_FLOOR if reaches_the_room else FLOOR_PLATE
            ev.append("IT_IS_LARGER_THAN_THE_FLIGHTS_BESIDE_IT")
            if reaches_the_room:
                ev.append("THE_ROOM_AROUND_THE_STAIR_REACHES_IT")
        elif ends >= 2:
            role = STAIR_LANDING
            ev.append("IT_JOINS_THE_ENDS_OF_TWO_FLIGHTS")
            ev.append("IT_IS_NO_LARGER_THAN_THE_FLIGHTS_IT_JOINS")
        elif ends == 1 and not reaches_the_room:
            role = STAIR_LANDING
            ev.append("IT_LIES_AT_THE_END_OF_A_FLIGHT")
            ev.append("THE_ROOM_DOES_NOT_REACH_IT")
        elif ends == 0 and sides >= 2 and not reaches_the_room:
            role = OPEN_VOID
            ev.append("IT_LIES_BESIDE_TWO_FLIGHTS_AND_AT_THE_END_OF_NONE")
        elif reaches_the_room:
            role = CIRCULATION_FLOOR
            ev.append("THE_ROOM_AROUND_THE_STAIR_REACHES_IT")
        else:
            role = LANDING_ROLE_UNRESOLVED
            ev.append("NOTHING_DRAWN_SAYS_WHICH_OF_THE_FOUR_IT_IS")

        out.append(Landing(
            landing_id=f"SL-{region_id}-{n:03d}-{i:02d}",
            polygon_wkt=g.wkt, area_m2=g.area / 1e6,
            length_mm=long_mm, width_mm=short_mm,
            role=role, touches_flight_ends=ends, touches_flight_sides=sides,
            role_evidence=tuple(ev),
            status=("LANDING_MEASURED" if role == STAIR_LANDING
                    else NOT_A_STAIR_LANDING)))
    return out


# ------------------------------------------------- §12 the curved stair

# Two arcs are drawn about the same centre when their centres are this
# close. The enclosure's own junction reach, a hundred times over: a
# drawn arc's centre is a computed point, not a snapped one.
ARC_CENTRE_MM = enc.JUNCTION_REACH_MM * 100.0

# A radial line points AT the centre when the perpendicular distance
# from the centre to its infinite line is under this. Same figure.
RADIAL_MM = ARC_CENTRE_MM

RADIAL_RUN = "RADIAL_TREADS_ABOUT_A_COMMON_CENTRE"
EV_CONCENTRIC_ARCS = "CONCENTRIC_ARCS_SHARE_A_CENTRE"
EV_RADIAL_LINES = "LINES_POINT_AT_THAT_CENTRE"
EV_TREADS_IN_SEQUENCE = "THE_RADIAL_LINES_FOLLOW_EACH_OTHER_ROUND"


@dataclass(frozen=True)
class ArcRing:
    """Concentric arcs about one centre: a stair's inner and outer string."""

    cx: float
    cy: float
    radii: tuple
    arc_ids: tuple

    @property
    def inner_mm(self) -> float:
        return min(self.radii)

    @property
    def outer_mm(self) -> float:
        return max(self.radii)

    def record(self) -> dict:
        return {"centre_mm": [round(self.cx, 1), round(self.cy, 1)],
                "radii_mm": [round(r, 1) for r in self.radii],
                "inner_mm": round(self.inner_mm, 1),
                "outer_mm": round(self.outer_mm, 1),
                "arcs": len(self.radii),
                "cad_provenance": list(self.arc_ids)}


def arc_rings(arcs) -> list:
    """Arcs grouped by the centre they are drawn about."""
    groups: dict = {}
    for a in arcs or ():
        key = (round(a.cx / ARC_CENTRE_MM), round(a.cy / ARC_CENTRE_MM))
        groups.setdefault(key, []).append(a)
    out = []
    for _k, members in groups.items():
        if len(members) < 2:
            continue
        radii = sorted(m.radius for m in members)
        if radii[-1] - radii[0] < MIN_WIDTH_MM:
            continue          # one string drawn twice is not a stair
        out.append(ArcRing(
            cx=members[0].cx, cy=members[0].cy, radii=tuple(radii),
            arc_ids=tuple(getattr(m, "object_id", "") for m in members)))
    return out


def _radials(ring: ArcRing, segments) -> list:
    """Drawn lines that point at the ring's centre, by angle."""
    import math

    out = []
    for s in segments or ():
        x1, y1, x2, y2 = s.x1, s.y1, s.x2, s.y2
        dx, dy = x2 - x1, y2 - y1
        length = math.hypot(dx, dy)
        if length < MIN_WIDTH_MM:
            continue
        # perpendicular distance from the centre to this line
        d = abs(dy * (ring.cx - x1) - dx * (ring.cy - y1)) / length
        if d > RADIAL_MM:
            continue
        r1 = math.hypot(x1 - ring.cx, y1 - ring.cy)
        r2 = math.hypot(x2 - ring.cx, y2 - ring.cy)
        lo, hi = min(r1, r2), max(r1, r2)
        # A TREAD EDGE SPANS THE FLIGHT, from the inner string to the
        # outer one. A line that merely points at the centre from
        # somewhere else in the plan — a dimension, a wall on a radius,
        # a hatch — crosses the band and keeps going, and it is not a
        # tread. The slack is a tread's own smallest going.
        if abs(lo - ring.inner_mm) > MIN_GOING_MM:
            continue
        if abs(hi - ring.outer_mm) > MIN_GOING_MM:
            continue
        mx, my = (x1 + x2) / 2.0, (y1 + y2) / 2.0
        ang = math.atan2(my - ring.cy, mx - ring.cx)
        out.append({"angle": ang, "lo": lo, "hi": hi,
                    "object_id": getattr(s, "object_id", "")})
    out.sort(key=lambda r: r["angle"])
    return out


def _dedupe(radials, ring: ArcRing) -> list:
    """Two lines a hair apart are one tread edge drawn twice.

    'A hair' is the angle a tread's smallest going subtends at the
    ring's own mean radius — the module's own figure, at this stair's
    scale.
    """
    if not radials:
        return []
    mean_r = max((ring.inner_mm + ring.outer_mm) / 2.0, 1.0)
    min_angle = MIN_GOING_MM / mean_r
    out = [radials[0]]
    for r in radials[1:]:
        if r["angle"] - out[-1]["angle"] < min_angle:
            out[-1] = {**out[-1], "lo": min(out[-1]["lo"], r["lo"]),
                       "hi": max(out[-1]["hi"], r["hi"]),
                       "object_id": out[-1]["object_id"]}
            continue
        out.append(r)
    return out


def _sector(ring: ArcRing, a0: float, a1: float):
    """The wedge between two radial lines, from inner string to outer."""
    import math

    from shapely.geometry import Polygon

    steps = max(2, int(abs(a1 - a0) / math.radians(2.0)) + 1)
    pts = []
    for i in range(steps + 1):
        t = a0 + (a1 - a0) * i / steps
        pts.append((ring.cx + ring.outer_mm * math.cos(t),
                    ring.cy + ring.outer_mm * math.sin(t)))
    for i in range(steps, -1, -1):
        t = a0 + (a1 - a0) * i / steps
        pts.append((ring.cx + ring.inner_mm * math.cos(t),
                    ring.cy + ring.inner_mm * math.sin(t)))
    return Polygon(pts)


def _sequence(radials, ring: ArcRing) -> list:
    """Put the tread edges in order round the ring, and cut the run.

    TWO THINGS THE ANGLES DO THAT A SORT DOES NOT SURVIVE. A flight that
    crosses the -180/+180 line looks like a full circle when its angles
    are simply sorted — the first version of this measured a 95-degree
    flight as 352 degrees of marble. And a ring may carry lines that are
    not treads of this flight at all.

    So the sequence starts after the LARGEST gap round the circle — the
    open side of the flight — and is cut wherever the step from one edge
    to the next is not a tread's going at this ring's mean radius.
    """
    import math

    if len(radials) < 2:
        return []
    mean_r = max((ring.inner_mm + ring.outer_mm) / 2.0, 1.0)
    angles = [r["angle"] for r in radials]
    gaps = [(angles[(i + 1) % len(angles)] - angles[i]) % (2 * math.pi)
            for i in range(len(angles))]
    start = (gaps.index(max(gaps)) + 1) % len(angles)
    order, ang = [], []
    for k in range(len(radials)):
        i = (start + k) % len(radials)
        a = angles[i]
        if ang and a < ang[-1]:
            a += 2 * math.pi * math.ceil((ang[-1] - a) / (2 * math.pi))
        ang.append(a)
        order.append({**radials[i], "angle": a})
    runs, cur = [], [order[0]]
    for prev, nxt in zip(order, order[1:]):
        going = (nxt["angle"] - prev["angle"]) * mean_r
        if MIN_GOING_MM <= going <= MAX_GOING_MM:
            cur.append(nxt)
            continue
        runs.append(cur)
        cur = [nxt]
    runs.append(cur)
    runs = [r for r in runs if len(r) >= MIN_TREADS + 1]
    return max(runs, key=len) if runs else []


def curved_flights(arcs, segments, *, region_id: str = "DR-001",
                   sections=None) -> list:
    """Every curved or winder flight this region draws, as Flights.

    A winder's treads are wedges of different sizes and each is measured
    from its OWN sector: no average tread, no constant going, and no
    rectangle substituted for a shape the drawing gives exactly.
    """
    import math

    out = []
    for n, ring in enumerate(arc_rings(arcs), 1):
        radials = _sequence(_dedupe(_radials(ring, segments), ring), ring)
        if len(radials) < MIN_TREADS + 1:
            continue
        flight = Flight(
            flight_id=f"SF-{region_id}-C{n:02d}", axis="RADIAL",
            direction_mm=(round(math.degrees(radials[0]["angle"]), 2),
                          round(math.degrees(radials[-1]["angle"]), 2)),
            width_mm=ring.outer_mm - ring.inner_mm,
            configuration=WINDER,
            centre_mm=(ring.cx, ring.cy),
            span_mm=(ring.inner_mm, ring.outer_mm),
            evidence=(EV_CONCENTRIC_ARCS, EV_RADIAL_LINES,
                      EV_TREADS_IN_SEQUENCE, EV_GOING_IS_A_STAIR_GOING))
        for i in range(len(radials) - 1):
            a0, a1 = radials[i]["angle"], radials[i + 1]["angle"]
            sweep = a1 - a0
            g = _sector(ring, a0, a1)
            mean_r = (ring.inner_mm + ring.outer_mm) / 2.0
            flight.treads.append(Tread(
                tread_id=f"ST-{region_id}-C{n:02d}-{i + 1:02d}",
                index=i + 1, polygon_wkt=g.wkt,
                # the exact annulus sector, not the sampled polygon
                area_m2=0.5 * (ring.outer_mm ** 2 - ring.inner_mm ** 2)
                * abs(sweep) / 1e6,
                going_mm=abs(sweep) * mean_r,
                width_mm=ring.outer_mm - ring.inner_mm,
                nosing_length_mm=abs(sweep) * ring.outer_mm,
                front_edge_wkt=_ray(ring, a0), back_edge_wkt=_ray(ring, a1),
                inner_edge_wkt=_arc_wkt(ring, ring.inner_mm, a0, a1),
                outer_edge_wkt=_arc_wkt(ring, ring.outer_mm, a0, a1),
                rectangular=False,
                cad_provenance=(radials[i]["object_id"],
                                radials[i + 1]["object_id"])))
        sec = _section_for(sections, flight.flight_id, region_id)
        rise = sec.get("riser_height_mm")
        for i, t in enumerate(flight.treads, 1):
            flight.risers.append(Riser(
                riser_id=f"SR-{region_id}-C{n:02d}-{i:02d}",
                index=i, width_mm=t.width_mm,
                height_mm=(None if rise is None else float(rise)),
                area_m2=(None if rise is None
                         else t.width_mm * float(rise) / 1e6),
                height_source=(RISER_NOT_ESTABLISHED if rise is None
                               else "SECTION_EVIDENCE"),
                status=(RISER_NOT_ESTABLISHED if rise is None
                        else "RISER_MEASURED")))
        out.append((ring, flight))
    return out


def _ray(ring: ArcRing, angle: float) -> str:
    import math

    from shapely.geometry import LineString

    return LineString([
        (ring.cx + ring.inner_mm * math.cos(angle),
         ring.cy + ring.inner_mm * math.sin(angle)),
        (ring.cx + ring.outer_mm * math.cos(angle),
         ring.cy + ring.outer_mm * math.sin(angle))]).wkt


def _arc_wkt(ring: ArcRing, radius: float, a0: float, a1: float) -> str:
    import math

    from shapely.geometry import LineString

    steps = max(2, int(abs(a1 - a0) / math.radians(2.0)) + 1)
    return LineString([
        (ring.cx + radius * math.cos(a0 + (a1 - a0) * i / steps),
         ring.cy + radius * math.sin(a0 + (a1 - a0) * i / steps))
        for i in range(steps + 1)]).wkt


# ------------------------------- §10 one staircase, drawn on three plans

# A staircase drawn on the ground-floor plan and again on the first-floor
# plan is ONE staircase. The two drawings put it at the same place
# relative to their OWN region, which is how the sheet repeats anything.
SAME_PLACE_MM = 250.0

# The floors this project can order. A stair connects the ones its plans
# are drawn on, and where a floor is not established it connects nothing.
FLOOR_ORDER = ("BASEMENT", "GROUND", "MEZZANINE", "FIRST", "SECOND",
               "ROOF")
FLOOR_NOT_ESTABLISHED = "FLOOR_LEVEL_NOT_ESTABLISHED"

# --- §8, §11 what the stair coverage of a floor is ----------------------
#
# Round 6D exported one stair and said nothing about the rest. A plan
# that draws a stair the engine did not reconstruct has FAILED coverage,
# not complete coverage of one stair, and a large curved stair left
# unresolved is never left silent.
COVERAGE_COMPLETE = "STAIR_COVERAGE_COMPLETE"
COVERAGE_INCOMPLETE = "STAIR_COVERAGE_INCOMPLETE"
COVERAGE_FAILED = "STAIR_COVERAGE_FAILED"
NO_STAIR_OBSERVED = "NO_STAIR_LIKE_GEOMETRY_ON_THIS_FLOOR"
COVERAGE_STATES = (COVERAGE_COMPLETE, COVERAGE_INCOMPLETE,
                   COVERAGE_FAILED, NO_STAIR_OBSERVED)
LARGE_UNRESOLVED = "A_LARGE_STAIR_OBSERVATION_IS_UNRESOLVED"

# An unresolved observation is LARGE when it reaches this share of the
# largest staircase the same drawings did reconstruct. A share, never a
# size: the drawing sets the scale of its own stairs.
LARGE_SHARE = STAIR_CELL_SHARE

PHYSICAL_STAIR = "PHYSICAL_STAIR_ASSEMBLY"
PLAN_INSTANCE = "STAIR_PLAN_INSTANCE"
FLOORS_NOT_ESTABLISHED = "THE_FLOORS_THIS_STAIR_CONNECTS_ARE_NOT_ESTABLISHED"


@dataclass
class PhysicalStair:
    """One staircase of the building, however many plans draw it."""

    physical_stair_id: str = ""
    instances: tuple = ()          # (region_id, stair_id)
    floors: tuple = ()
    floor_from: str = ""
    floor_to: str = ""
    stair_role: str = STAIR_ROLE_UNKNOWN
    role_evidence: tuple = ()
    finish: str = FINISH_NOT_CONFIRMED
    finish_source: str = "OWNER_RULE_REQUEST"
    configuration: str = CONFIGURATION_NOT_ESTABLISHED
    width_m: float = 0.0
    tread_m2: float | None = None
    riser_m2: float | None = None
    landing_m2: float = 0.0
    floor_not_stair_m2: float = 0.0
    nosing_lm: float = 0.0
    skirting_lm: float | None = None
    exceptions: tuple = ()
    why: str = ""

    def record(self) -> dict:
        return {
            "physical_stair_id": self.physical_stair_id,
            "object": PHYSICAL_STAIR,
            "plan_instances": [{"drawing_region_id": r, "stair_id": s}
                               for r, s in self.instances],
            "floors_it_is_drawn_on": list(self.floors),
            "floor_from": self.floor_from or FLOORS_NOT_ESTABLISHED,
            "floor_to": self.floor_to or FLOORS_NOT_ESTABLISHED,
            "stair_role": self.stair_role,
            "role_evidence": list(self.role_evidence),
            "finish": self.finish,
            "finish_source": self.finish_source,
            "configuration": self.configuration,
            "stair_width_m": round(self.width_m, 3),
            "MEASURED_NET": {
                "TREAD_M2": (None if self.tread_m2 is None
                             else round(self.tread_m2, 4)),
                "RISER_M2": (None if self.riser_m2 is None
                             else round(self.riser_m2, 4)),
                "LANDING_M2": round(self.landing_m2, 4),
                "NOSING_LM": round(self.nosing_lm, 3),
                "STAIR_SKIRTING_LM": self.skirting_lm,
                # NOT stair quantity. The floor plate, void and
                # circulation this stair stands among, reported so that
                # the floor may measure them and the stair may not.
                "FLOOR_BETWEEN_THE_FLIGHTS_NOT_STAIR_M2": round(
                    self.floor_not_stair_m2, 4),
                "this_is": ("ONE staircase, measured once. The same stair "
                            "drawn on two plans is not two quantities"),
            },
            "exceptions": list(self.exceptions),
            "why": self.why,
        }


def _flight_keys(a: Assembly, origin) -> set:
    """What each flight of this stair looks like, relative to its region.

    The assembly's own centroid is not enough: the ground-floor plan may
    draw a curved flight AND the straight one beside it while the first
    floor draws only the curve, and two centroids that differ do not
    make two staircases. A FLIGHT is the thing that repeats.
    """
    ox, oy = origin
    out = set()
    for f in a.flights:
        cx, cy = (f.centre_mm or (0.0, 0.0))
        out.add((round((cx - ox) / SAME_PLACE_MM),
                 round((cy - oy) / SAME_PLACE_MM),
                 round(f.width_mm / SAME_PLACE_MM),
                 len(f.treads)))
    return out


# What the envelope calls a space, in the two words it uses for each
# side of the building line. A stair's kind starts with which side of it
# the stair stands on.
INTERIOR_WORDS = ("INTERIOR", "INSIDE_BUILDING")
EXTERIOR_WORDS = ("EXTERIOR", "OUTSIDE_BUILDING")

NOT_LANDSCAPE_OR_ENTRANCE = (
    "WHETHER_THESE_OUTSIDE_STEPS_ARE_LANDSCAPE_IS_NOT_ESTABLISHED")


def _role(*, interior, floors, width, widest, ties, hint, plans) -> tuple:
    """What KIND of stair this is, on what the drawings actually say.

    §9. A main stair carries a storey: it stands inside the building,
    it is drawn on the plans of two established floors, and no wider
    interior stair does the same. A run that climbs out of one plan into
    nothing established is not a main stair, however wide it is drawn,
    and its kind is UNKNOWN rather than guessed. SERVICE_STAIR and
    LANDSCAPE_STEPS need a rule or a label to say so: no arrangement of
    lines on a plan distinguishes them from the stair beside them.
    """
    if hint in STAIR_ROLES and hint != STAIR_ROLE_UNKNOWN:
        return hint, ("A_RULE_GIVEN_FOR_THIS_STAIR_SAYS_IT_IS_" + hint,)
    ev = []
    if interior:
        ev.append(f"THE_ENVELOPE_CALLS_ITS_SPACE_{interior}")
    carries = len(floors) >= 2
    if carries:
        ev.append("IT_IS_DRAWN_ON_THE_PLANS_OF_" + "_AND_".join(floors))
    else:
        ev.append("THE_FLOORS_IT_CONNECTS_ARE_NOT_ESTABLISHED")
    if plans > 1:
        ev.append(f"THE_SAME_STAIR_IS_DRAWN_ON_{plans}_PLANS")

    if interior in EXTERIOR_WORDS:
        ev.append(NOT_LANDSCAPE_OR_ENTRANCE)
        return EXTERIOR_STEPS, tuple(ev)
    if interior not in INTERIOR_WORDS:
        ev.append("NOTHING_SAYS_WHETHER_ITS_SPACE_IS_INSIDE")
        return STAIR_ROLE_UNKNOWN, tuple(ev)
    if not carries:
        # INSIDE, and climbing to nothing the drawings establish. It may
        # be the main stair of the building drawn once; it may be four
        # steps up to a terrace. Width does not tell the two apart.
        ev.append("IT_IS_NOT_ESTABLISHED_TO_CARRY_A_STOREY")
        return STAIR_ROLE_UNKNOWN, tuple(ev)
    if width >= widest - SAME_PLACE_MM:
        if ties > 1:
            ev.append("ANOTHER_INTERIOR_STAIR_CARRIES_A_STOREY_AS_WIDELY")
            return STAIR_ROLE_UNKNOWN, tuple(ev)
        ev.append("NO_WIDER_INTERIOR_STAIR_CARRIES_A_STOREY")
        return MAIN_INTERIOR_STAIR, tuple(ev)
    ev.append("A_WIDER_INTERIOR_STAIR_CARRIES_A_STOREY")
    return SECONDARY_INTERIOR_STAIR, tuple(ev)


# --- §15 the stair quantity, each figure in its own unit ----------------
#
# A stair is bought in four different kinds of number and they are never
# added: an area of marble, a length of nosing and skirting, a count of
# treads and risers, and a width. A single "stair quantity" is a wrong
# number in every unit at once.
UNIT_M2 = "m2"
UNIT_LM = "lm"
UNIT_PCS = "pcs"
UNIT_M = "m"
UNITS = (UNIT_M2, UNIT_LM, UNIT_PCS, UNIT_M)
NOT_ESTABLISHED_HERE = "NOT_ESTABLISHED"


def _q(value, unit: str, status: str = "") -> dict:
    return {"value": value, "unit": unit,
            "status": (status or (NOT_ESTABLISHED_HERE if value is None
                                  else "MEASURED_NET"))}


def quantities(physical_stairs, reports=()) -> dict:
    """§15. Every stair quantity, with its unit, and no sum across units."""
    counts = {}
    for rep in reports:
        for a in rep.assemblies:
            counts[a.stair_id] = {
                "treads": sum(len(f.treads) for f in a.flights),
                "risers": sum(1 for f in a.flights for r in f.risers
                              if r.height_mm is not None),
                "risers_drawn": sum(len(f.risers) for f in a.flights),
                "landings": sum(1 for x in a.landings if x.is_stair_landing),
            }
    rows = []
    for x in physical_stairs:
        c = {"treads": 0, "risers": 0, "risers_drawn": 0, "landings": 0}
        for _region, sid in x.instances:
            got = counts.get(sid)
            if got and got["treads"] >= c["treads"]:
                c = got
        unmeasured = TREAD_NOT_ESTABLISHED in x.exceptions
        rows.append({
            "physical_stair_id": x.physical_stair_id,
            "stair_role": x.stair_role,
            "finish": x.finish,
            "configuration": x.configuration,
            "floor_from": x.floor_from or FLOORS_NOT_ESTABLISHED,
            "floor_to": x.floor_to or FLOORS_NOT_ESTABLISHED,
            "STAIR_WIDTH": _q(round(x.width_m, 3) or None, UNIT_M),
            "TREADS": _q(c["treads"] or None, UNIT_PCS),
            "RISERS": _q(c["risers"] or None, UNIT_PCS,
                         "" if c["risers"] else RISER_NOT_ESTABLISHED),
            "RISERS_DRAWN_ON_PLAN": _q(c["risers_drawn"] or None, UNIT_PCS),
            "STAIR_LANDINGS": _q(c["landings"], UNIT_PCS),
            "TREAD_AREA": _q(None if unmeasured or x.tread_m2 is None
                             else round(x.tread_m2, 4), UNIT_M2),
            "RISER_FACE_AREA": _q(None if x.riser_m2 is None
                                  else round(x.riser_m2, 4), UNIT_M2,
                                  "" if x.riser_m2 is not None
                                  else RISER_NOT_ESTABLISHED),
            "LANDING_AREA": _q(round(x.landing_m2, 4), UNIT_M2),
            "NOSING_LENGTH": _q(round(x.nosing_lm, 3), UNIT_LM),
            "STAIR_SKIRTING": _q(x.skirting_lm, UNIT_LM,
                                 "" if x.skirting_lm is not None
                                 else SKIRTING_NOT_ESTABLISHED),
            "FLOOR_BETWEEN_THE_FLIGHTS_NOT_STAIR": _q(
                round(x.floor_not_stair_m2, 4), UNIT_M2,
                "NOT_STAIR_QUANTITY"),
            "exceptions": list(x.exceptions),
        })
    def _sum(key, unit):
        vals = [r[key]["value"] for r in rows]
        if any(v is None for v in vals):
            return {"value": None, "unit": unit,
                    "status": "NOT_ESTABLISHED_FOR_EVERY_STAIRCASE"}
        return {"value": round(sum(vals), 4), "unit": unit,
                "status": "MEASURED_NET"}
    return {
        "model": MODEL,
        "rows": rows,
        "totals": {
            "TREAD_AREA": _sum("TREAD_AREA", UNIT_M2),
            "RISER_FACE_AREA": _sum("RISER_FACE_AREA", UNIT_M2),
            "LANDING_AREA": _sum("LANDING_AREA", UNIT_M2),
            "NOSING_LENGTH": _sum("NOSING_LENGTH", UNIT_LM),
            "STAIR_SKIRTING": _sum("STAIR_SKIRTING", UNIT_LM),
            "TREADS": _sum("TREADS", UNIT_PCS),
            "RISERS": _sum("RISERS", UNIT_PCS),
        },
        "units_are_never_added": (
            "m2, lm and pcs are three different quantities of the same "
            "staircase. There is no total of them and none is written"),
    }


# --- §16 the same square metre is never two finishes --------------------
MARBLE_AND_PORCELAIN_CLASH = "A_SQUARE_METRE_IS_BOTH_STAIR_AND_FLOOR"
NO_CLASH = "NO_SQUARE_METRE_IS_BOTH_STAIR_AND_FLOOR"


def finish_clash(released, reports) -> dict:
    """§16. MARBLE n PORCELAIN = 0 m2, measured rather than asserted.

    `released` is what the register released as room floor — the
    porcelain candidates — as (space_id, polygon_wkt) in millimetres.
    Every stair footprint and every stair landing is taken out of it,
    and what remains in both is reported as an area, which has to be
    zero. Not a rule about what should happen: the intersection.
    """
    stair_parts = []
    for rep in reports:
        for a in rep.assemblies:
            if a.footprint_wkt:
                stair_parts.append((a.stair_id, _loads_safe(a.footprint_wkt)))
            for x in a.landings:
                if x.is_stair_landing and x.polygon_wkt:
                    stair_parts.append((x.landing_id, _loads_safe(x.polygon_wkt)))
    clashes, clash_m2 = [], 0.0
    for space_id, wkt in released:
        if not wkt:
            continue
        room = _loads_safe(wkt)
        if room.is_empty:
            continue
        for part_id, part in stair_parts:
            if part.is_empty:
                continue
            try:
                over = room.intersection(part)
            except Exception:      # noqa: BLE001
                continue
            if over.is_empty or over.area <= 0:
                continue
            clash_m2 += over.area / 1e6
            clashes.append({
                "physical_space_id": space_id,
                "stair_part_id": part_id,
                "overlap_m2": round(over.area / 1e6, 4),
                "what_it_would_mean": (
                    "this area would be billed as marble stair and as "
                    "porcelain floor, and it is one area"),
            })
    return {
        "model": MODEL,
        "released_room_polygons": len(list(released)),
        "stair_parts": len(stair_parts),
        "MARBLE_INTERSECT_PORCELAIN_M2": round(clash_m2, 4),
        "status": (NO_CLASH if clash_m2 <= 0.0001
                   else MARBLE_AND_PORCELAIN_CLASH),
        "clashes": clashes,
        "this_is": ("the measured intersection of the released room "
                    "floor with the stair, and not a promise about it"),
    }


def _extent_m2(o) -> float:
    """How much ground a stair-like observation covers, from its extent."""
    ex = tuple(o.extent_mm or ())
    if len(ex) == 4:
        return abs(ex[2] - ex[0]) * abs(ex[3] - ex[1]) / 1e6
    if len(ex) == 2:
        return abs(ex[0] * ex[1]) / 1e6
    return 0.0


def coverage(reports, physical_stairs=(), *, floor_of=None) -> dict:
    """§8, §11. What the drawings show against what was reconstructed.

    Per floor, because a building is climbed floor by floor and a stair
    reconstructed on the ground plan says nothing about the first. A
    floor whose plans draw stair-like geometry and yield no staircase
    has FAILED, not "one stair"; a floor with an unresolved observation
    or an unmeasured quantity is INCOMPLETE; and every unresolved
    observation is listed, largest first, so that a large curved stair
    is never quietly missing from a bill (§11).
    """
    floor = dict(floor_of or {})
    per: dict = {}
    for rep in reports:
        fl = floor.get(rep.region_id, "") or FLOOR_NOT_ESTABLISHED
        row = per.setdefault(fl, {
            "floor": fl, "plans": [], "observations": 0, "mapped": 0,
            "unresolved": 0, "refused_as_not_a_stair": 0,
            "runs_refused": 0, "stair_assemblies": 0,
            "unresolved_observations": [], "exceptions": set(),
            "tread_quantity_established": 0,
            "riser_quantity_established": 0,
            "landing_role_unresolved": 0})
        row["plans"].append(rep.region_id)
        row["runs_refused"] += len(rep.refused)
        row["stair_assemblies"] += len(rep.assemblies)
        for o in rep.observations:
            row["observations"] += 1
            if o.status == MAPPED:
                row["mapped"] += 1
            elif o.status == NOT_A_STAIR_ON_EVIDENCE:
                row["refused_as_not_a_stair"] += 1
            else:
                row["unresolved"] += 1
                row["unresolved_observations"].append(o)
        for a in rep.assemblies:
            row["exceptions"].update(a.exceptions)
            if TREAD_NOT_ESTABLISHED not in a.exceptions and a.flights:
                row["tread_quantity_established"] += 1
            if a.riser_m2 is not None:
                row["riser_quantity_established"] += 1
            row["landing_role_unresolved"] += sum(
                1 for x in a.landings if x.role == LANDING_ROLE_UNRESOLVED)

    biggest = max((a.footprint_area_m2 for rep in reports
                   for a in rep.assemblies), default=0.0)
    by_floor = {}
    for fl, row in per.items():
        large = [o for o in row["unresolved_observations"]
                 if biggest and _extent_m2(o) >= biggest * LARGE_SHARE]
        exceptions = sorted(row["exceptions"])
        if large:
            exceptions.append(LARGE_UNRESOLVED)
        if not row["observations"] and not row["stair_assemblies"]:
            status = NO_STAIR_OBSERVED
            why = "no run of lines on these plans reads as a stair"
        elif not row["stair_assemblies"]:
            status = COVERAGE_FAILED
            why = (f"{row['observations']} stair-like observations on "
                   "these plans and not one staircase reconstructed")
        elif row["unresolved"] or exceptions:
            status = COVERAGE_INCOMPLETE
            why = "; ".join(
                ([f"{row['unresolved']} observations unresolved"]
                 if row["unresolved"] else [])
                + ([", ".join(exceptions)] if exceptions else []))
        else:
            status = COVERAGE_COMPLETE
            why = "every stair-like observation is part of a staircase"
        by_floor[fl] = {
            "floor": fl,
            "drawing_regions": sorted(row["plans"]),
            "stair_observations": row["observations"],
            "mapped_to_a_staircase": row["mapped"],
            "unresolved": row["unresolved"],
            "refused_as_not_a_stair": row["refused_as_not_a_stair"],
            "runs_refused": row["runs_refused"],
            "stair_assemblies": row["stair_assemblies"],
            "tread_quantity_established": row["tread_quantity_established"],
            "riser_quantity_established": row["riser_quantity_established"],
            "pieces_between_flights_unresolved":
                row["landing_role_unresolved"],
            "coverage": status,
            "why": why,
            "exceptions": exceptions,
            # NEVER SILENTLY IGNORED. Every observation nobody turned
            # into a staircase, largest first, with what it covers.
            "unresolved_observations": [
                dict(o.record(),
                     covers_m2=round(_extent_m2(o), 4),
                     is_large=bool(biggest
                                   and _extent_m2(o) >= biggest * LARGE_SHARE))
                for o in sorted(row["unresolved_observations"],
                                key=_extent_m2, reverse=True)],
        }

    order = [f for f in FLOOR_ORDER if f in by_floor] + \
        sorted(f for f in by_floor if f not in FLOOR_ORDER)
    rows = [by_floor[f] for f in order]
    if any(r["coverage"] == COVERAGE_FAILED for r in rows):
        overall = COVERAGE_FAILED
    elif any(r["coverage"] == COVERAGE_INCOMPLETE for r in rows):
        overall = COVERAGE_INCOMPLETE
    elif not rows or all(r["coverage"] == NO_STAIR_OBSERVED for r in rows):
        overall = NO_STAIR_OBSERVED
    else:
        overall = COVERAGE_COMPLETE
    carry = sum(1 for x in physical_stairs
                if x.floor_from and x.floor_to
                and x.floor_from != x.floor_to)
    return {
        "model": MODEL,
        "stair_coverage": overall,
        "per_floor": rows,
        "physical_staircases": len(list(physical_stairs)),
        "staircases_that_carry_a_storey": carry,
        "unresolved_in_total": sum(r["unresolved"] for r in rows),
        "large_unresolved_in_total": sum(
            1 for r in rows for o in r["unresolved_observations"]
            if o["is_large"]),
        "this_is": (
            "what the drawings show against what was reconstructed. A "
            "floor that draws a stair and yields none has FAILED "
            "coverage, and one stair measured on one floor is not "
            "coverage of the building"),
    }


def reconcile(reports, *, regions=(), floor_of=None, interior_of=None,
              finish_rules=None, role_hints=None) -> dict:
    """Plan instances into physical staircases, with a role and a finish.

    §9 A stair's KIND comes from what it does — which storeys it
       carries — and not from how wide its widest run is drawn.
       role_hints carries what a rule or a label says about a space,
       {space_id: role}, and nothing else may name a SERVICE_STAIR or
       LANDSCAPE_STEPS: no arrangement of lines on a plan does.
    §10 The same staircase on two plans is one staircase.
    §16 No stair is marble because it is a stair: a finish is confirmed
        by the owner or by a document, and otherwise it is a request.
    """
    origin = {r.region_id: (r.x0, r.y0) for r in regions}
    floor = dict(floor_of or {})
    interior = dict(interior_of or {})
    rules = dict(finish_rules or {})
    hints = dict(role_hints or {})

    # ---- §10 the same stair on several plans -------------------------
    #
    # Grouped FIRST, because §9's question — what kind of stair is this —
    # is asked of a staircase and not of a drawing of one. Two plan
    # instances are one staircase when they draw a FLIGHT at the same
    # place relative to their own regions. Joined transitively: a stair
    # drawn on three plans is one stair, not three pairs.
    every = [a for rep in reports for a in rep.assemblies]
    keys = {id(a): _flight_keys(a, origin.get(a.region_id, (0.0, 0.0)))
            for a in every}
    parent = {id(a): id(a) for a in every}

    def _find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i, a in enumerate(every):
        for b in every[i + 1:]:
            if a.region_id == b.region_id:
                continue
            if keys[id(a)] & keys[id(b)]:
                parent[_find(id(a))] = _find(id(b))
    groups: dict = {}
    for a in every:
        groups.setdefault(_find(id(a)), []).append(a)

    # ---- §9 what KIND of stair each staircase is ---------------------
    #
    # NOT the widest run in the drawing. Round 6D asked only how wide a
    # run was, and made a four-tread run of 2.80 m the MAIN stair of the
    # building while the curved stair that carries the storey came out
    # SECONDARY. What a main stair does is carry a storey.
    facts = {}
    for root, members in groups.items():
        known = sorted({floor.get(a.region_id, "") for a in members}
                       & set(FLOOR_ORDER), key=FLOOR_ORDER.index)
        ix = ""
        for a in members:
            ix = interior.get(a.space_id, "") or ix
        facts[root] = {
            "known": known,
            "interior": ix,
            "width": max((f.width_mm for a in members for f in a.flights),
                         default=0.0),
            "hint": next((hints.get(a.space_id) for a in members
                          if hints.get(a.space_id)), ""),
        }
    carrying = [f["width"] for f in facts.values()
                if f["interior"] in INTERIOR_WORDS and len(f["known"]) >= 2]
    widest = max(carrying, default=0.0)
    ties = sum(1 for w in carrying if w >= widest - SAME_PLACE_MM)
    for root, f in facts.items():
        f["role"], f["evidence"] = _role(
            interior=f["interior"], floors=f["known"], width=f["width"],
            widest=widest, ties=ties, hint=f["hint"],
            plans=len(groups[root]))
    for root, members in groups.items():
        for a in members:
            a.stair_role = facts[root]["role"]
            a.role_evidence = facts[root]["evidence"]
            a.interior_exterior = facts[root]["interior"]

    out = []
    for k, (_root, members) in enumerate(sorted(
            groups.items(), key=lambda kv: kv[1][0].stair_id), 1):
        floors = [floor.get(a.region_id, "") for a in members]
        known = [f for f in floors if f in FLOOR_ORDER]
        known.sort(key=FLOOR_ORDER.index)
        first = members[0]
        exceptions = sorted({x for a in members for x in a.exceptions})
        tread = (None if any(a.record()["MEASURED_NET"]["TREAD_M2"] is None
                             for a in members)
                 else max(a.tread_m2 for a in members))
        riser = (None if any(a.riser_m2 is None for a in members)
                 else max(a.riser_m2 for a in members))
        role = first.stair_role
        rule = rules.get(role) or rules.get("ALL")
        stair = PhysicalStair(
            physical_stair_id=f"PS-STAIR-{k:03d}",
            instances=tuple((a.region_id, a.stair_id) for a in members),
            floors=tuple(floors), configuration=first.configuration,
            floor_from=(known[0] if len(known) >= 2 else ""),
            floor_to=(known[-1] if len(known) >= 2 else ""),
            stair_role=role,
            role_evidence=first.role_evidence,
            finish=(rule or FINISH_NOT_CONFIRMED),
            finish_source=("PROJECT_RULE_FOR_THIS_STAIR_ROLE" if rule
                           else "OWNER_RULE_REQUEST"),
            width_m=max((f.width_mm for a in members for f in a.flights),
                        default=0.0) / 1000.0,
            # MEASURED ONCE. The same stair drawn twice is one quantity,
            # and the fuller representation is the one that measures it.
            tread_m2=tread, riser_m2=riser,
            landing_m2=max((a.landing_m2 for a in members), default=0.0),
            floor_not_stair_m2=max((a.not_stair_landing_m2
                                    for a in members), default=0.0),
            nosing_lm=max((a.nosing_lm for a in members), default=0.0),
            exceptions=tuple(exceptions
                             + ([FLOORS_NOT_ESTABLISHED]
                                if len(known) < 2 else [])),
            why=("drawn on " + ", ".join(
                f"{a.region_id}({floor.get(a.region_id, 'no floor')})"
                for a in members)))
        for a in members:
            a.physical_stair_id = stair.physical_stair_id
            a.finish = stair.finish
            a.finish_source = stair.finish_source
        out.append(stair)

    return {
        "model": MODEL,
        "physical_stairs": out,
        "counts": {
            "physical_stair_assemblies": len(out),
            "plan_instances": sum(len(x.instances) for x in out),
            "connect_two_established_floors": sum(
                1 for x in out if x.floor_from and x.floor_to),
            "finish_confirmed": sum(
                1 for x in out if x.finish != FINISH_NOT_CONFIRMED),
        },
        "notes": {
            "one_stair_measured_once": (
                "a staircase drawn on the ground and first floor plans is "
                "one staircase. Adding both representations would buy the "
                "marble twice"),
            "no_finish_without_a_rule": (
                "a stair is not marble because it is a stair. Until the "
                "owner or a document says so, its finish is a request"),
        },
    }
