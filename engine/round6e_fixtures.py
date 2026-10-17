"""Round 6E — seventeen cases about identity, release, agreement, stairs.

The independent audit of the Round 6C and 6D bundles found four kinds of
defect, and each of them is a case here before it is a fix anywhere:

    an id that follows the enumeration rather than the space
        A  the same drawing, enumerated the other way round
        B  a wall refined by 30 mm
        C  one room split into two
        D  two rooms merged into one
        E  a room added, and a room gone
        F  the same room, renamed
        G  the same room, reclassified
        H  two rooms of exactly the same area, in different places
        Q  a candidate that matches two predecessors equally

    a release state that contradicts itself
        I  a register where everything released is releasable
        J  a DRAWING_ARTIFACT marked releasable
        K  a PARTIAL_SPACE marked releasable
        L  a parent released beside its own children

    a report number the export's own rows do not add up to
        M  a metric that IS the aggregation
        N  a metric that is not, which must be caught and NOT adjusted

    a stair read from its width and a floor read as a landing
        O  a wide four-tread run on one plan, and a stair on two plans
        P  a proper landing, and a floor plate far too large to be one

Cases J, K, L, N and Q exist to FAIL if the engine ever says otherwise:
they are the synthetic failures §3, §7 and §19 ask for. No coordinate in
this file comes from any real project.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field

from engine import round4_fixtures as r4
from engine import round6d_fixtures as r6d
from engine.cad_fixtures import Builder

W, D, G, TXT = r4.W, r4.D, r4.G, r4.TXT

LINEAGE = "LINEAGE"
RELEASE = "RELEASE"
CONSISTENCY = "CONSISTENCY"
STAIR = "STAIR"

# Two plans on one sheet stand this far apart, as in round 6C.
SHEET_STEP_MM = 200000.0


@dataclass(frozen=True)
class Case:
    name: str
    what_it_tests: str
    kind: str
    payload: dict = field(default_factory=dict)
    expect: dict = field(default_factory=dict)


# ------------------------------------------------------- the lineage kit

def _sp(space_id, box, *, region="DR-001", identity="", role="ROOM"):
    return {"space_id": space_id, "region_id": region, "box": box,
            "normalized_identity": identity, "candidate_role": role}


def _a():
    """The same rooms, enumerated the other way round."""
    prev = [_sp("PS-001", (0, 0, 4000, 3000), identity="BEDROOM"),
            _sp("PS-002", (5000, 0, 9000, 3000), identity="STORE")]
    now = [_sp("PS-101", (5000, 0, 9000, 3000), identity="STORE"),
           _sp("PS-102", (0, 0, 4000, 3000), identity="BEDROOM")]
    return Case(
        "A_THE_SAME_DRAWING_ENUMERATED_THE_OTHER_WAY_ROUND",
        "a stable id follows the space, not the order of the flood",
        LINEAGE, {"previous": prev, "now": now},
        expect={"lineage": {"PS-101": "UNCHANGED", "PS-102": "UNCHANGED"},
                "stable_ids": {"PS-101": "PS-002", "PS-102": "PS-001"}})


def _b():
    """A wall refined by 30 mm: the same room, reshaped."""
    prev = [_sp("PS-001", (0, 0, 4000, 3000), identity="BEDROOM")]
    now = [_sp("PS-101", (0, 0, 3970, 3000), identity="BEDROOM")]
    return Case(
        "B_A_WALL_REFINED_BY_30_MM",
        "ordinary geometry refinement never changes an identity",
        LINEAGE, {"previous": prev, "now": now},
        expect={"lineage": {"PS-101": "UNCHANGED"},
                "stable_ids": {"PS-101": "PS-001"}})


def _c():
    """One room becomes two. NEITHER child is the parent."""
    prev = [_sp("PS-001", (0, 0, 8000, 3000), identity="LIVING")]
    now = [_sp("PS-101", (0, 0, 3900, 3000), identity="LIVING"),
           _sp("PS-102", (4100, 0, 8000, 3000), identity="STUDY")]
    return Case(
        "C_ONE_ROOM_SPLIT_INTO_TWO",
        "whichever child is enumerated first is not the parent",
        LINEAGE, {"previous": prev, "now": now},
        expect={"lineage": {"PS-101": "SPLIT", "PS-102": "SPLIT"},
                "no_child_keeps": ["PS-001"],
                "predecessors": {"PS-101": ["PS-001"],
                                 "PS-102": ["PS-001"]}})


def _d():
    """Two rooms become one. Every predecessor is kept."""
    prev = [_sp("PS-001", (0, 0, 3900, 3000), identity="LIVING"),
            _sp("PS-002", (4100, 0, 8000, 3000), identity="STUDY")]
    now = [_sp("PS-101", (0, 0, 8000, 3000), identity="LIVING")]
    return Case(
        "D_TWO_ROOMS_MERGED_INTO_ONE",
        "a merged space is a new identity with both histories",
        LINEAGE, {"previous": prev, "now": now},
        expect={"lineage": {"PS-101": "MERGED"},
                "no_child_keeps": ["PS-001", "PS-002"],
                "predecessors": {"PS-101": ["PS-001", "PS-002"]}})


def _e():
    """A room added, and a room that is gone."""
    prev = [_sp("PS-001", (0, 0, 4000, 3000), identity="BEDROOM"),
            _sp("PS-002", (5000, 0, 9000, 3000), identity="STORE")]
    now = [_sp("PS-101", (0, 0, 4000, 3000), identity="BEDROOM"),
           _sp("PS-102", (10000, 0, 14000, 3000), identity="TERRACE")]
    return Case(
        "E_A_ROOM_ADDED_AND_A_ROOM_GONE",
        "NEW and REMOVED are stated, never inferred from a count",
        LINEAGE, {"previous": prev, "now": now},
        expect={"lineage": {"PS-101": "UNCHANGED", "PS-102": "NEW"},
                "removed": ["PS-002"]})


def _f():
    """The same room, renamed."""
    prev = [_sp("PS-001", (0, 0, 4000, 3000), identity="STORE")]
    now = [_sp("PS-101", (0, 0, 4000, 3000), identity="STUDY")]
    return Case(
        "F_THE_SAME_ROOM_RENAMED",
        "an identity change is a change, and keeps the stable id",
        LINEAGE, {"previous": prev, "now": now},
        expect={"lineage": {"PS-101": "IDENTITY_CHANGED"},
                "stable_ids": {"PS-101": "PS-001"}})


def _g():
    """The same polygon, reclassified."""
    prev = [_sp("PS-001", (0, 0, 4000, 3000), identity="STORE",
                role="UNRESOLVED")]
    now = [_sp("PS-101", (0, 0, 4000, 3000), identity="STORE",
               role="ROOM")]
    return Case(
        "G_THE_SAME_ROOM_RECLASSIFIED",
        "a role change is a change, and keeps the stable id",
        LINEAGE, {"previous": prev, "now": now},
        expect={"lineage": {"PS-101": "ROLE_CHANGED"},
                "stable_ids": {"PS-101": "PS-001"}})


def _h():
    """Two rooms of EXACTLY the same area, in different places."""
    prev = [_sp("PS-001", (0, 0, 4000, 3000), identity="BED_1"),
            _sp("PS-002", (6000, 0, 10000, 3000), identity="BED_2")]
    now = [_sp("PS-101", (6000, 0, 10000, 3000), identity="BED_2"),
           _sp("PS-102", (0, 0, 4000, 3000), identity="BED_1")]
    return Case(
        "H_TWO_ROOMS_OF_EXACTLY_THE_SAME_AREA",
        "area is the one evidence that cannot tell two rooms apart",
        LINEAGE, {"previous": prev, "now": now},
        expect={"stable_ids": {"PS-101": "PS-002", "PS-102": "PS-001"},
                "lineage": {"PS-101": "UNCHANGED", "PS-102": "UNCHANGED"}})


def _q():
    """A candidate that matches two predecessors equally well."""
    prev = [_sp("PS-001", (0, 0, 4000, 3000), identity=""),
            _sp("PS-002", (4000, 0, 8000, 3000), identity="")]
    now = [_sp("PS-101", (2000, 0, 6000, 3000), identity="")]
    return Case(
        "Q_A_CANDIDATE_THAT_MATCHES_TWO_PREDECESSORS_EQUALLY",
        "where the evidence does not settle it, the answer is an "
        "explicit unresolved exception and no id is carried",
        LINEAGE, {"previous": prev, "now": now},
        expect={"lineage": {"PS-101": "UNRESOLVED_LINEAGE"},
                "no_child_keeps": ["PS-001", "PS-002"],
                "unresolved_is_explicit": True})


# ------------------------------------------------------- the release kit

def _row(space_id, box, *, role, basis="CLEAR_INTERNAL_FACE_TO_FACE",
         label="", blockers=(), gate="RELEASE_ELIGIBLE_GEOMETRY"):
    """One candidate, with the MEASUREMENT layer's verdict on it.

    `gate` is what the measurement layer said about the polygon, before
    anybody asked what the polygon IS. It is open on every row of these
    cases on purpose: the failures are role failures, and one state has
    to catch them with the geometry perfectly fine.
    """
    return {"space_id": space_id, "region_id": "DR-001", "box": box,
            "candidate_role": role, "basis": basis, "raw_label": label,
            "release_status": gate, "blockers": tuple(blockers)}


def _i():
    """Two ordinary rooms. Everything released is releasable."""
    rows = [_row("PS-001", (0, 0, 4000, 3000), role="ROOM", label="BEDROOM"),
            _row("PS-002", (5000, 0, 9000, 3000), role="ROOM",
                 label="STORE")]
    return Case(
        "I_A_REGISTER_WHERE_EVERYTHING_RELEASED_IS_RELEASABLE",
        "the ordinary case: one state, and nothing contradicting it",
        RELEASE, {"rows": rows},
        expect={"contradictions": 0, "released_at_least": 1})


def _j():
    """A drawing artifact, which may never release a room quantity."""
    # A TITLE STRIP: 12 m long and 40 mm deep, thinner on the mean
    # measure than the thinnest wall this project recognises. Its
    # measurement gate is open, exactly as the failing case needs.
    rows = [_row("PS-001", (0, 0, 4000, 3000), role="ROOM", label="BEDROOM"),
            _row("PS-900", (0, 6000, 12000, 6040), role="DRAWING_ARTIFACT")]
    return Case(
        "J_A_DRAWING_ARTIFACT_MARKED_RELEASABLE",
        "a title strip is not a room, whatever the measurement gate "
        "says about its polygon",
        RELEASE, {"rows": rows},
        expect={"contradictions": 0, "never_released": ["PS-900"],
                "roles": {"PS-900": "DRAWING_ARTIFACT"}})


def _k():
    """Half a room is not a room."""
    # A piece of a room bounded by a partition whose thickness nobody
    # established: measured, and not a room.
    rows = [_row("PS-001", (0, 0, 4000, 3000), role="ROOM", label="BEDROOM"),
            _row("PS-800", (9000, 0, 11000, 1350), role="PARTIAL_SPACE",
                 basis="CLEAR_FACE_NOT_ESTABLISHED")]
    return Case(
        "K_A_PARTIAL_SPACE_MARKED_RELEASABLE",
        "a 2.70 m2 piece of a room is not the room, and releases nothing",
        RELEASE, {"rows": rows},
        expect={"contradictions": 0, "never_released": ["PS-800"],
                "roles": {"PS-800": "PARTIAL_SPACE"}})


def _l():
    """A plate and the rooms inside it. Only one of them may release."""
    rows = [_row("PS-700", (0, 0, 12000, 6000), role="ROOM",
                 label="FLOOR PLATE"),
            _row("PS-001", (200, 200, 5800, 5800), role="ROOM",
                 label="BEDROOM"),
            _row("PS-002", (6200, 200, 11800, 5800), role="ROOM",
                 label="STORE")]
    return Case(
        "L_A_PARENT_RELEASED_BESIDE_ITS_OWN_CHILDREN",
        "a parent and its children may never both release: the area "
        "would be counted twice",
        RELEASE, {"rows": rows},
        expect={"contradictions": 0, "never_released": ["PS-700"]})


# --------------------------------------------------- the consistency kit

_TABLE = [
    {"physical_space_id": "PS-001", "released": "true", "area_m2": "12.6"},
    {"physical_space_id": "PS-002", "released": "true", "area_m2": "8.4"},
    {"physical_space_id": "PS-003", "released": "false", "area_m2": "99.9"},
]


def _m():
    """A metric that IS the aggregation of the rows beneath it."""
    return Case(
        "M_A_REPORT_METRIC_THAT_IS_THE_AGGREGATION",
        "the ordinary case: the report adds up the export's own rows",
        CONSISTENCY,
        {"tables": {"SPACE_REGISTER": _TABLE},
         "metrics": [("RELEASE_ELIGIBLE_GEOMETRY_AREA_M2", "SPACE_REGISTER",
                      21.0, {"where": {"released": True},
                             "column": "area_m2"}),
                     ("RELEASE_ELIGIBLE_GEOMETRY", "SPACE_REGISTER", 2,
                      {"where": {"released": True}, "op": "count"})]},
        expect={"status": "REPORT_AND_EXPORT_AGREE", "disagreements": 0})


def _n():
    """A metric the rows do not add up to. Caught, and NOT adjusted."""
    return Case(
        "N_A_REPORT_METRIC_THE_EXPORT_DOES_NOT_ADD_UP_TO",
        "a disagreement is a defect in the run, and neither number is "
        "changed to make them agree",
        CONSISTENCY,
        {"tables": {"SPACE_REGISTER": _TABLE},
         "metrics": [("RELEASE_ELIGIBLE_GEOMETRY_AREA_M2", "SPACE_REGISTER",
                      26.3085, {"where": {"released": True},
                                "column": "area_m2"})]},
        expect={"status": "REPORT_AND_EXPORT_DISAGREE",
                "disagreements": 1,
                "report_value_unchanged": 26.3085,
                "export_value_unchanged": 21.0})


# -------------------------------------------------------- the stair kit

def _plan(b, ox, oy, title):
    r6d._shell(b, ox, oy, 12000, 9000)
    b.text(title, ox + 500, oy - 500, r6d.TITLE_H, TXT)


def _o():
    """A wide four-tread run on one plan; a stair drawn on two."""
    b = Builder()
    # GROUND: the staircase that carries the storey, and a short wide run
    _plan(b, 0, 0, "GROUND FLOOR PLAN")
    r4._partition_v(b, 4000, 0, 5000, t=200.0, gaps=[(3600, 4500)])
    r4._door(b, "DA", 4000, 3600, 900)
    r6d._treads(b, "H", 300.0, 9, 300.0, 200.0, 1400.0)
    r4._stamp(b, "S1", ["STAIR"], 800, 1500)
    # the short wide run, in its own cell, with its own label
    r4._partition_v(b, 8000, 5400, 9000, t=200.0)
    r4._partition_h(b, 5400, 8000, 12000, t=200.0, gaps=[(9000, 9900)])
    r4._door(b, "DB", 9000, 5400, 900)
    r6d._treads(b, "H", 5700.0, 5, 300.0, 8200.0, 11000.0)
    r4._stamp(b, "S2", ["STAIR"], 9600, 6600)
    # FIRST: the same staircase, at the same place in its own plan
    ox = SHEET_STEP_MM
    _plan(b, ox, 0, "FIRST FLOOR PLAN")
    r4._partition_v(b, ox + 4000, 0, 5000, t=200.0, gaps=[(3600, 4500)])
    r4._door(b, "DC", ox + 4000, 3600, 900)
    r6d._treads(b, "H", 300.0, 9, 300.0, ox + 200.0, ox + 1400.0)
    r4._stamp(b, "S3", ["STAIR"], ox + 800, 1500)
    return Case(
        "O_A_WIDE_RUN_ON_ONE_PLAN_IS_NOT_THE_MAIN_STAIR",
        "a main stair carries a storey. Width is not what makes one",
        STAIR, {"decode": b.build()},
        expect={"widest_is_not_main": True,
                "a_stair_on_two_floors_exists": True})


def _p():
    """A landing between two flight ends, and a floor plate too large."""
    b = Builder()
    r6d._shell(b, 0, 0, 10000, 8000)
    b.text("GROUND FLOOR PLAN", 500, -500, r6d.TITLE_H, TXT)
    # the stair's own cell, the way a stair hall is drawn
    r4._partition_v(b, 2200, 0, 8000, t=200.0, gaps=[(6800, 7700)])
    r4._door(b, "DA", 2200, 6800, 900)
    # two flights climbing in y, END TO END, with 1.5 m between their
    # ends: the piece between them is the landing the stair turns on
    r6d._treads(b, "H", 300.0, 9, 300.0, 400.0, 1600.0)
    r6d._treads(b, "H", 4200.0, 9, 300.0, 400.0, 1600.0)
    r4._stamp(b, "S1", ["STAIR"], 1000, 3400)
    r4._stamp(b, "S2", ["HALL"], 7000, 4000)
    return Case(
        "P_A_LANDING_BETWEEN_TWO_FLIGHT_ENDS",
        "a landing joins the ends of the flights and is no larger than "
        "them; anything larger is floor, and the floor measures it",
        STAIR, {"decode": b.build()},
        expect={"stair_landings_at_least": 1,
                # 1.20 m of flight width by the 1.50 m between the ends
                "landing_m2": 1.2 * 1.5,
                "no_piece_larger_than_the_flights_is_a_landing": True})


CASES = (_a, _b, _c, _d, _e, _f, _g, _h, _i, _j, _k, _l, _m, _n, _o, _p,
         _q)


def cases() -> list:
    return [fn() for fn in CASES]


def fixture_hash() -> str:
    """The cases, frozen: a changed expectation changes this."""
    parts = []
    for c in cases():
        parts.append(f"{c.name}|{c.kind}|{sorted(c.expect.items())}")
    return hashlib.sha256("|".join(map(str, parts)).encode(
        "utf-8")).hexdigest()[:24]
