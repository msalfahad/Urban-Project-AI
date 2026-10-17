"""The arithmetic of the QS rule pack, executable and tested — and idle.

The Urban Projects QS Rule Pack (Finishes V1) states how the finishes
trades are measured. This module is that arithmetic and nothing else: no
project is run through it, no drawing is read by it, and nothing here
starts a BOQ. It exists so that when a measurement round does begin, the
rules are already the owner's rather than something reinvented at the
keyboard.

Each function takes established geometry and returns a quantity WITH its
unit and its provenance, or refuses. None of them invents a dimension: a
missing height, a missing run or an unestablished opening comes back as
NOT ESTABLISHED, because a finishes quantity computed from a guess is a
quantity somebody orders.

    UP-CER-002/003   skirting is a run less its doors
    UP-CER-004       and it is ZERO where the wall tile runs full height
    UP-CER-005       wall ceramic is the eligible area less its openings
    UP-CER-006/007   an exposed edge takes ONE finish, not two
    UP-STAIR-010/011 a stair skirting follows the zigzag or the rake,
                     never the plan run
    UP-STAIR-012     a railing follows the open edge only
    UP-WP-002/003    the upturn is 0.15 m, and the membrane carries
                     through the doorway rather than stopping at it
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass

MODEL = "URBAN_PROJECTS_FINISHES_ARITHMETIC_V1"

UNIT_M2 = "m2"
UNIT_LM = "lm"
UNIT_PCS = "pcs"

NOT_ESTABLISHED = "NOT_ESTABLISHED"
MEASURED = "MEASURED_NET"

# UP-WP-002. The upturn the owner states, in metres. A project detail
# that states another replaces it; nothing here assumes a second one.
UPTURN_M = 0.15

FULL_WALL_TILE_TAKES_THE_SKIRTING = (
    "the wall ceramic runs full height, so it already reaches the floor. "
    "This zero is a RULE, not a quantity nobody measured")
ONE_EDGE_ONE_FINISH = (
    "an exposed edge takes a mitred 45-degree finish OR a steel profile. "
    "Counting it in both counts the same edge twice")
THROUGH_THE_DOORWAY = (
    "the membrane does not stop at the door line: it carries through so "
    "the room can be flood tested, and that piece is not deducted")


def model_hash() -> str:
    parts = [MODEL, UNIT_M2, UNIT_LM, UNIT_PCS, NOT_ESTABLISHED, MEASURED,
             str(UPTURN_M), FULL_WALL_TILE_TAKES_THE_SKIRTING,
             ONE_EDGE_ONE_FINISH, THROUGH_THE_DOORWAY,
             CURVE_FRACTION_NOT_ESTABLISHED]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


@dataclass
class Quantity:
    """A number that knows its unit, its rule and whether it is real."""

    item: str = ""
    value: float | None = None
    unit: str = ""
    rule_id: str = ""
    status: str = NOT_ESTABLISHED
    what_is_missing: tuple = ()
    why: str = ""

    def record(self) -> dict:
        return {
            "item": self.item,
            "value": (None if self.value is None else round(self.value, 4)),
            "unit": self.unit,
            "rule_id": self.rule_id,
            "status": self.status,
            "what_is_missing": list(self.what_is_missing),
            "why": self.why,
        }


def _need(item, unit, rule_id, missing, why=""):
    return Quantity(item=item, unit=unit, rule_id=rule_id,
                    status=NOT_ESTABLISHED, what_is_missing=tuple(missing),
                    why=why or "the geometry this rule needs is not "
                              "established, and no default stands in")


# --------------------------------------------- a curved intrusion

CURVE_FRACTION_NOT_ESTABLISHED = "THE_APPLICABLE_FRACTION_IS_NOT_ESTABLISHED"


def circular_segment_m2(radius_m=None, segment_height_m=None) -> Quantity:
    """The area a circle cuts out of a rectangle, from the chord in.

    A pool, a curved wall or a bay intrudes on a room as a CIRCULAR
    SEGMENT — the piece between a chord and the arc — and its area is

        R² · arccos((R − h)/R) − (R − h)·√(2Rh − h²)

    where h is how deep the arc reaches past the chord. Nothing about
    that is a rule of thumb, and nothing about it is half.
    """
    if radius_m is None or segment_height_m is None:
        return _need("CIRCULAR_SEGMENT", UNIT_M2, "GEOMETRY",
                     ["the radius", "the segment height"])
    r, h = float(radius_m), float(segment_height_m)
    if r <= 0 or h <= 0 or h > 2 * r:
        return _need("CIRCULAR_SEGMENT", UNIT_M2, "GEOMETRY",
                     ["a radius and a segment height that describe an arc"])
    area = (r * r * math.acos((r - h) / r)
            - (r - h) * math.sqrt(max(2 * r * h - h * h, 0.0)))
    return Quantity("CIRCULAR_SEGMENT", area, UNIT_M2, "GEOMETRY",
                    MEASURED,
                    why=f"a segment of radius {r} m reaching {h} m past "
                        "its chord")


def curved_intrusion_deduction(radius_m=None, segment_height_m=None, *,
                               applicable_fraction=None) -> Quantity:
    """How much of that segment this room actually loses.

    THE FRACTION IS EVIDENCE, NOT A HABIT. Half a segment is deducted
    when half of it falls inside the room, and which half that is comes
    from the drawing. A fraction nobody established is the reason a
    take-off and a benchmark differ by exactly one half-segment.
    """
    seg = circular_segment_m2(radius_m, segment_height_m)
    if seg.status != MEASURED:
        return seg
    if applicable_fraction is None:
        return _need("CURVED_INTRUSION_DEDUCTION", UNIT_M2, "GEOMETRY",
                     ["how much of the segment falls inside this room"],
                     "the segment is " + f"{seg.value:.4f} m2 and how "
                     "much of it this room loses is not established. "
                     + CURVE_FRACTION_NOT_ESTABLISHED)
    frac = float(applicable_fraction)
    return Quantity("CURVED_INTRUSION_DEDUCTION", seg.value * frac,
                    UNIT_M2, "GEOMETRY", MEASURED,
                    why=(f"{frac:g} of a {seg.value:.4f} m2 segment, as "
                         "the drawing gives it"))


# ------------------------------------------------------------- ceramic

def floor_ceramic(area_m2=None, *, deduct_m2=0.0) -> Quantity:
    """UP-CER-001. The room's floor, less anything another trade owns."""
    if area_m2 is None:
        return _need("DRY_FLOOR_CERAMIC", UNIT_M2, "UP-CER-001",
                     ["the released floor polygon"])
    return Quantity("DRY_FLOOR_CERAMIC", max(area_m2 - deduct_m2, 0.0),
                    UNIT_M2, "UP-CER-001", MEASURED,
                    why="the released floor area, less the area another "
                        "finish already owns")


def skirting(run_lm=None, *, door_widths_lm=(), full_wall_ceramic=None,
             ) -> Quantity:
    """UP-CER-002/003/004. A run less its doors — or zero, by rule."""
    if full_wall_ceramic is None:
        return _need("FLOOR_SKIRTING", UNIT_LM, "UP-CER-004",
                     ["whether this room's wall ceramic is full height"],
                     "a wet room with full wall ceramic takes no floor "
                     "skirting, and whether this one does is not known")
    if full_wall_ceramic:
        return Quantity("FLOOR_SKIRTING", 0.0, UNIT_LM, "UP-CER-004",
                        MEASURED, why=FULL_WALL_TILE_TAKES_THE_SKIRTING)
    if run_lm is None:
        return _need("FLOOR_SKIRTING", UNIT_LM, "UP-CER-002",
                     ["the room's wall base run"])
    if door_widths_lm is None:
        return _need("FLOOR_SKIRTING", UNIT_LM, "UP-CER-003",
                     ["the width of each door opening in the run"])
    doors = sum(door_widths_lm)
    return Quantity("FLOOR_SKIRTING", max(run_lm - doors, 0.0), UNIT_LM,
                    "UP-CER-003", MEASURED,
                    why=f"{run_lm} lm of wall base less {doors} lm of "
                        "door openings")


def wall_ceramic(gross_m2=None, *, openings_m2=None) -> Quantity:
    """UP-CER-005. Gross eligible wall area less its openings."""
    if gross_m2 is None:
        return _need("WALL_CERAMIC", UNIT_M2, "UP-CER-005",
                     ["the eligible wall faces", "the tile height"])
    if openings_m2 is None:
        return _need("WALL_CERAMIC", UNIT_M2, "UP-CER-005",
                     ["every opening in those faces"])
    return Quantity("WALL_CERAMIC", max(gross_m2 - openings_m2, 0.0),
                    UNIT_M2, "UP-CER-005", MEASURED,
                    why="the eligible wall area less what is cut out of it")


def edge_finish(mitred_lm=None, steel_lm=None, *, shared_lm=0.0) -> dict:
    """UP-CER-006/007. Two finishes for one edge, and never both."""
    out = {
        "MITRED_45_DEGREE_EDGE": Quantity(
            "MITRED_45_DEGREE_EDGE", mitred_lm, UNIT_LM, "UP-CER-006",
            MEASURED if mitred_lm is not None else NOT_ESTABLISHED),
        "STEEL_EDGE_PROFILE": Quantity(
            "STEEL_EDGE_PROFILE", steel_lm, UNIT_LM, "UP-CER-007",
            MEASURED if steel_lm is not None else NOT_ESTABLISHED),
        "both_on_the_same_edge_lm": round(shared_lm, 4),
        "status": ("DOUBLE_COUNTED_EDGE" if shared_lm > 0.0
                   else "ONE_EDGE_ONE_FINISH"),
        "why": ONE_EDGE_ONE_FINISH,
    }
    return out


def floor_drains(count=None) -> Quantity:
    """UP-CER-008. A count, in pieces."""
    if count is None:
        return _need("FLOOR_DRAIN", UNIT_PCS, "UP-CER-008",
                     ["the drains the drawing shows"])
    return Quantity("FLOOR_DRAIN", float(count), UNIT_PCS, "UP-CER-008",
                    MEASURED, why="counted, never measured by area")


# -------------------------------------------------------------- stairs

def zigzag_skirting(goings_mm=(), rises_mm=()) -> Quantity:
    """UP-STAIR-010. The path that follows every nose and every riser."""
    if not goings_mm or not rises_mm:
        return _need("STAIR_SKIRTING_ZIGZAG", UNIT_LM, "UP-STAIR-010",
                     ["each step's going", "each step's rise"])
    lm = (sum(goings_mm) + sum(rises_mm)) / 1000.0
    return Quantity("STAIR_SKIRTING_ZIGZAG", lm, UNIT_LM, "UP-STAIR-010",
                    MEASURED,
                    why=(f"{len(goings_mm)} goings and {len(rises_mm)} "
                         "rises, followed as they are cut"))


def sloped_skirting(plan_run_mm=None, total_rise_mm=None) -> Quantity:
    """UP-STAIR-011. The rake, which is longer than the plan run."""
    if plan_run_mm is None or total_rise_mm is None:
        return _need("STAIR_SKIRTING_SLOPED", UNIT_LM, "UP-STAIR-011",
                     ["the flight's plan run", "the flight's total rise"])
    return Quantity("STAIR_SKIRTING_SLOPED",
                    math.hypot(plan_run_mm, total_rise_mm) / 1000.0,
                    UNIT_LM, "UP-STAIR-011", MEASURED,
                    why="the inclined path, not its shadow on the plan")


def railing(open_edge_paths_mm=None) -> Quantity:
    """UP-STAIR-012. The open edge only: a wall side takes none."""
    if open_edge_paths_mm is None:
        return _need("STAIR_RAILING", UNIT_LM, "UP-STAIR-012",
                     ["which side of each flight is open",
                      "the path along that side"])
    return Quantity("STAIR_RAILING", sum(open_edge_paths_mm) / 1000.0,
                    UNIT_LM, "UP-STAIR-012", MEASURED,
                    why=("the open-edge path. A side against a wall "
                         "receives no railing"))


# ------------------------------------------------------- waterproofing

def wet_floor(area_m2=None, *, doorway_m2=0.0) -> Quantity:
    """UP-WP-001/003. The floor, and the doorway it carries through."""
    if area_m2 is None:
        return _need("WATERPROOFING_FLOOR", UNIT_M2, "UP-WP-001",
                     ["the wet room's floor polygon"])
    return Quantity("WATERPROOFING_FLOOR", area_m2 + doorway_m2, UNIT_M2,
                    "UP-WP-003", MEASURED, why=THROUGH_THE_DOORWAY)


def upturn(wall_run_lm=None, *, openings_lm=0.0, height_m=UPTURN_M,
           ) -> Quantity:
    """UP-WP-002. The run times 0.15 m, less what interrupts it."""
    if wall_run_lm is None:
        return _need("WATERPROOFING_UPTURN", UNIT_M2, "UP-WP-002",
                     ["the wet room's wall run"])
    run = max(wall_run_lm - openings_lm, 0.0)
    return Quantity("WATERPROOFING_UPTURN", run * height_m, UNIT_M2,
                    "UP-WP-002", MEASURED,
                    why=f"{run} lm of wall at {height_m} m of upturn")
