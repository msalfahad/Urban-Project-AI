"""A pantry is not always a room, and a counter is not a wall.

Round 6C measured physical spaces and refused to release a 900 x 2500
strip a PANTRY label was sitting in. The owner's correction is that the
strip was the wrong answer for a second reason as well: **a pantry need
not be a closed room at all.**

    CLOSED_PANTRY            four walls and a door, a physical space
    OPEN_AMERICAN_PANTRY     open to the dining, saloon, living or
                             reception space it serves
    PANTRY_OPENNESS_UNKNOWN  the drawing does not say. Nobody guesses

So this module builds the layer between a physical space and a trade
quantity:

    PHYSICAL_SPACE  ->  FUNCTIONAL_ZONE  ->  TRADE_MEASUREMENT_ZONE
                                             (a later round. Not here)

A FUNCTIONAL ZONE IS NOT A ROOM AND CREATES NO WALLS. One large open
space may hold a saloon zone, a dining zone, an American pantry zone and
a circulation zone with nothing physical between them, and none of those
boundaries may ever become blockwork, plaster or a room polygon.

WALL TILE ON AN OPEN PANTRY

An open pantry still has tiled walls — the ones that are actually there.
Wall tile is measured on the host wall segments serving the zone, and the
OPEN EDGE toward the dining or living space contributes ZERO: there is no
wall there and the zone is never closed virtually to make one.

    ONE_WALL   one host segment
    L_SHAPE    two
    U_SHAPE    three
    CLOSED     four

**Tile height is not assumed.** No 3.00 m, no 2.40 m, no project's habit
borrowed for another. Without an owner rule the height, and therefore
every area that depends on it, is an OWNER_RULE_REQUEST.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

MODEL = "FUNCTIONAL_ZONE_AND_PANTRY_OPENNESS_V1"

# --- §1 the three answers ------------------------------------------------
CLOSED_PANTRY = "CLOSED_PANTRY"
OPEN_AMERICAN_PANTRY = "OPEN_AMERICAN_PANTRY"
OPENNESS_UNKNOWN = "PANTRY_OPENNESS_UNKNOWN"
OPENNESS = (CLOSED_PANTRY, OPEN_AMERICAN_PANTRY, OPENNESS_UNKNOWN)

OWNER_RULE_REQUEST = "OWNER_RULE_REQUEST"

# --- §5 the shape of the tiled walls -------------------------------------
ONE_WALL = "ONE_WALL"
L_SHAPE = "L_SHAPE"
U_SHAPE = "U_SHAPE"
CLOSED_ON_FOUR_SIDES = "CLOSED_ON_FOUR_SIDES"
SHAPE_NOT_ESTABLISHED = "WALL_TILE_SHAPE_NOT_ESTABLISHED"

# Concepts that an American pantry opens ONTO. The ontology's own words,
# not new vocabulary: a pantry open to one of these is the American case
# the owner described.
OPEN_PLAN_CONCEPTS = ("DINING", "DINING_ZONE", "SALOON", "LIVING",
                      "RECEPTION", "HALL")

# The English term this project reads for a pantry. A term in another
# language belongs in the ontology, where it can be reviewed — never
# guessed at here. An unrecognised word stays UNKNOWN_TERM and this
# module says nothing about it.
PANTRY_TERMS = ("PANTRY",)

# --- what a zone's extent may rest on ------------------------------------
EV_LABEL_INSIDE_A_SPACE = "THE_LABEL_SITS_IN_THIS_PHYSICAL_SPACE"
EV_FITTING_RUN = "A_RUN_OF_FITTINGS_STANDS_ALONG_THESE_WALLS"
EV_HOST_WALLS = "THE_HOST_WALL_SEGMENTS_ARE_ESTABLISHED"
EV_OPEN_EDGE = "A_SIDE_OF_THIS_SPACE_HAS_NO_WALL_ON_IT"
EV_SHARES_A_SPACE = "ANOTHER_OPEN_PLAN_LABEL_SHARES_THIS_SPACE"
EV_FULLY_BOUNDED = "EVERY_SIDE_OF_THIS_SPACE_IS_AN_ESTABLISHED_WALL_FACE"
EV_SOLE_LABEL = "NO_OTHER_ROOM_LABEL_IS_IN_THIS_SPACE"

EXTENT_NOT_ESTABLISHED = "FUNCTIONAL_ZONE_EXTENT_NOT_ESTABLISHED"
EXTENT_FROM_FITTINGS = "FROM_THE_FITTINGS_AND_THE_WALLS_THEY_STAND_ON"
EXTENT_IS_THE_SPACE = "THE_WHOLE_OF_THE_PHYSICAL_SPACE_IT_IS_IN"


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "OPENNESS": list(OPENNESS),
        "WALL_TILE_SHAPES": [ONE_WALL, L_SHAPE, U_SHAPE,
                             CLOSED_ON_FOUR_SIDES, SHAPE_NOT_ESTABLISHED],
        "OPEN_PLAN_CONCEPTS": list(OPEN_PLAN_CONCEPTS),
        "PANTRY_TERMS": list(PANTRY_TERMS),
        "why": {
            "a_zone_creates_no_walls": (
                "a saloon zone and a dining zone in one open space are two "
                "zones and one space. Nothing between them is ever "
                "blockwork, plaster or a room boundary"),
            "an_open_edge_tiles_nothing": (
                "the side of a pantry that opens to the dining room has no "
                "wall on it, so its wall-tile length is zero. The zone is "
                "never closed virtually to produce one"),
            "height_is_never_assumed": (
                "no default tile height exists in this engine. Without a "
                "project rule the height and every area resting on it are "
                "an OWNER_RULE_REQUEST"),
            "openness_is_evidence_not_a_word": (
                "the label PANTRY says nothing about whether it is closed. "
                "Where the geometry does not say, the answer is UNKNOWN"),
        },
    }


def model_hash() -> str:
    parts = ([MODEL] + list(OPENNESS) + list(OPEN_PLAN_CONCEPTS)
             + list(PANTRY_TERMS)
             + [ONE_WALL, L_SHAPE, U_SHAPE, CLOSED_ON_FOUR_SIDES,
                SHAPE_NOT_ESTABLISHED, OWNER_RULE_REQUEST])
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


# ------------------------------------------------------------- the objects

@dataclass
class Zone:
    """One functional zone inside one physical space."""

    zone_id: str = ""
    region_id: str = ""
    floor_level: str = ""
    space_id: str = ""
    zone_kind: str = ""
    label_raw: str = ""
    at_mm: tuple = ()
    extent_basis: str = EXTENT_NOT_ESTABLISHED
    extent_area_m2: float | None = None
    evidence: tuple = ()
    why: str = ""

    def record(self) -> dict:
        return {
            "functional_zone_id": self.zone_id,
            "drawing_region_id": self.region_id,
            "floor": self.floor_level,
            "physical_space_id": self.space_id,
            "zone_kind": self.zone_kind,
            "raw_label": self.label_raw,
            "at_mm": [round(v, 1) for v in self.at_mm],
            "extent_basis": self.extent_basis,
            "extent_area_m2": (None if self.extent_area_m2 is None
                               else round(self.extent_area_m2, 4)),
            "evidence": list(self.evidence),
            "creates_no_wall": True,
            "why": self.why,
        }


@dataclass
class PantryAnalysis:
    """§5. What a pantry is, and what of it can be tiled."""

    pantry_zone_id: str = ""
    space_id: str = ""
    region_id: str = ""
    floor_level: str = ""
    openness: str = OPENNESS_UNKNOWN
    openness_evidence: tuple = ()
    host_wall_segment_ids: tuple = ()
    open_edge_ids: tuple = ()
    wall_tile_shape: str = SHAPE_NOT_ESTABLISHED
    wall_tile_length_m: float = 0.0
    open_edge_length_m: float = 0.0
    wall_tile_height_m: float | None = None
    gross_wall_tile_area_m2: float | None = None
    opening_deductions_m2: float | None = None
    net_wall_tile_area_m2: float | None = None
    height_source: str = OWNER_RULE_REQUEST
    rule_source: str = OWNER_RULE_REQUEST
    exceptions: tuple = ()

    def record(self) -> dict:
        return {
            "pantry_zone_id": self.pantry_zone_id,
            "physical_space_id": self.space_id,
            "drawing_region_id": self.region_id,
            "floor": self.floor_level,
            "pantry_openness": self.openness,
            "openness_evidence": list(self.openness_evidence),
            "host_wall_segment_ids": list(self.host_wall_segment_ids),
            "open_edge_ids": list(self.open_edge_ids),
            "wall_tile_shape": self.wall_tile_shape,
            "wall_tile_length_m": round(self.wall_tile_length_m, 3),
            "open_edge_length_m": round(self.open_edge_length_m, 3),
            "wall_tile_height_m": self.wall_tile_height_m,
            "gross_wall_tile_area_m2": self.gross_wall_tile_area_m2,
            "opening_deductions_m2": self.opening_deductions_m2,
            "net_wall_tile_area_m2": self.net_wall_tile_area_m2,
            "height_source": self.height_source,
            "rule_source": self.rule_source,
            "exceptions": list(self.exceptions),
            "the_open_edge_tiles_nothing": (
                "an open edge contributes zero wall-tile length. This zone "
                "is not closed virtually to produce a fourth wall"),
        }


@dataclass
class ZoneReport:
    zones: list = field(default_factory=list)
    pantries: list = field(default_factory=list)
    notes: dict = field(default_factory=dict)

    def counts(self) -> dict:
        from collections import Counter

        return {
            "functional_zones": len(self.zones),
            "by_kind": dict(Counter(z.zone_kind
                                    for z in self.zones).most_common()),
            "pantries": len(self.pantries),
            "by_openness": dict(Counter(p.openness
                                        for p in self.pantries).most_common()),
            "owner_rule_requests": sum(
                1 for p in self.pantries
                if p.height_source == OWNER_RULE_REQUEST),
        }

    def record(self) -> dict:
        return {
            "model": MODEL,
            "FUNCTIONAL_ZONE_HASH": model_hash(),
            "counts": self.counts(),
            "frozen_parameters": frozen_parameters(),
            "zones": [z.record() for z in self.zones],
            "pantry_analysis": [p.record() for p in self.pantries],
            "notes": dict(self.notes),
            "what_this_is_not": (
                "no TradeMeasurementZone, no ceramic quantity, no waste "
                "and no price. A zone is where a thing happens, not a "
                "quantity of anything"),
        }


# --------------------------------------------------------------- the rules

def _is_pantry(raw: str, concept: str) -> bool:
    up = (raw or "").strip().upper()
    return any(term in up for term in PANTRY_TERMS)


def _wall_faces(row) -> list:
    """The boundary faces of a space that are established WALL faces."""
    return [f for f in (row.get("boundary_faces") or ())
            if f.get("wall_band_id") and f.get("basis", "").startswith(
                "CLEAR_INTERNAL")]


def _open_faces(row) -> list:
    """The sides of a space that no wall band accounts for."""
    return [f for f in (row.get("boundary_faces") or ())
            if not f.get("wall_band_id")]


def _shape_of(n: int) -> str:
    return {1: ONE_WALL, 2: L_SHAPE, 3: U_SHAPE,
            4: CLOSED_ON_FOUR_SIDES}.get(n, SHAPE_NOT_ESTABLISHED)


def assess(rows, labels, *, floor_of=None, fittings=None,
           tile_rules=None) -> ZoneReport:
    """One functional-zone candidate per authored label, and no walls.

    `rows` are the register's rows, each with `boundary_faces` as plain
    dicts. `labels` are the reconciled label verdicts. `tile_rules` is an
    optional mapping of project rules — a height, a specification — and
    where it does not answer, the answer is an OWNER_RULE_REQUEST.
    """
    from engine import architectural_ontology as onto

    rep = ZoneReport()
    floor = dict(floor_of or {})
    by_id = {r["space_id"]: r for r in rows}
    rules = dict(tile_rules or {})

    # every label that resolved to a space, grouped by that space
    in_space: dict = {}
    for v in labels:
        sid = getattr(v, "space_id", "")
        if sid and sid in by_id:
            in_space.setdefault(sid, []).append(v)

    n = 0
    for v in labels:
        sid = getattr(v, "space_id", "")
        row = by_id.get(sid)
        if row is None:
            continue
        n += 1
        raw = getattr(v, "text", "")
        look = onto.classify_term(raw)
        kind = (look.concept if look.is_known else "UNKNOWN_TERM")
        siblings = [x for x in in_space.get(sid, ()) if x is not v]
        ev = [EV_LABEL_INSIDE_A_SPACE]
        if siblings:
            ev.append(EV_SHARES_A_SPACE)
        zone = Zone(
            zone_id=f"FZ-{row['region_id']}-{n:04d}",
            region_id=row["region_id"],
            floor_level=floor.get(row["region_id"], ""),
            space_id=sid, zone_kind=kind, label_raw=raw,
            at_mm=(getattr(v, "x", 0.0), getattr(v, "y", 0.0)),
            extent_basis=(EXTENT_IS_THE_SPACE if not siblings
                          else EXTENT_NOT_ESTABLISHED),
            extent_area_m2=(row.get("area_m2") if not siblings else None),
            evidence=tuple(ev),
            why=("this zone is the whole of the space it names"
                 if not siblings else
                 "several zones share one open space, and no line in the "
                 "drawing divides them. Their separate extents are not "
                 "established, and nothing here invents one"))
        rep.zones.append(zone)

        if not _is_pantry(raw, kind):
            continue

        walls = _wall_faces(row)
        opens = _open_faces(row)
        sides = {round(f["fixed_mm"], 1) for f in walls}
        shape = _shape_of(len(sides))
        tile_m = sum(f.get("length_mm", 0.0) for f in walls) / 1000.0
        open_m = sum(f.get("length_mm", 0.0) for f in opens) / 1000.0

        ov = []
        if siblings and any(
                onto.classify_term(getattr(s, "text", "")).concept
                in OPEN_PLAN_CONCEPTS for s in siblings):
            openness = OPEN_AMERICAN_PANTRY
            ov.append(EV_SHARES_A_SPACE)
        elif opens:
            openness = OPEN_AMERICAN_PANTRY
            ov.append(EV_OPEN_EDGE)
        elif walls and not opens and len(sides) >= 4:
            openness = CLOSED_PANTRY
            ov.extend([EV_FULLY_BOUNDED, EV_SOLE_LABEL])
        else:
            openness = OPENNESS_UNKNOWN
        if walls:
            ov.append(EV_HOST_WALLS)

        height = rules.get("wall_tile_height_m")
        src = rules.get("rule_source", OWNER_RULE_REQUEST)
        gross = None if height is None else round(tile_m * height, 4)
        rep.pantries.append(PantryAnalysis(
            pantry_zone_id=zone.zone_id, space_id=sid,
            region_id=row["region_id"],
            floor_level=floor.get(row["region_id"], ""),
            openness=openness, openness_evidence=tuple(ov),
            host_wall_segment_ids=tuple(sorted(
                {f["wall_band_id"] for f in walls})),
            open_edge_ids=tuple(sorted(
                {f.get("face_id") or "UNNAMED_SIDE" for f in opens})),
            wall_tile_shape=shape, wall_tile_length_m=tile_m,
            open_edge_length_m=open_m,
            wall_tile_height_m=height,
            gross_wall_tile_area_m2=gross,
            opening_deductions_m2=(None if height is None else 0.0),
            net_wall_tile_area_m2=gross,
            height_source=(OWNER_RULE_REQUEST if height is None
                           else rules.get("height_source", "PROJECT_RULE")),
            rule_source=src,
            exceptions=(() if openness != OPENNESS_UNKNOWN
                        else (OWNER_RULE_REQUEST,))))

    rep.notes["a_zone_is_not_a_room"] = (
        "a functional zone never creates a wall, a room polygon or a "
        "quantity. It says where something happens")
    rep.notes["closed_and_open_are_not_one_rule"] = (
        "a closed pantry is an ordinary physical space. An American "
        "pantry is a zone of a larger one, and they are not merged")
    return rep
