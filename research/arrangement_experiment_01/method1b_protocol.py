"""METHOD 1B - the atomic planar arrangement. The rules, written first.

WHY THERE IS A METHOD 1B AT ALL

Method 1A built the arrangement out of exactly the edge set frozen E1.4
admits to bound a CLEAR ROOM FACE. It produced two faces and 0.125 m2 of
enclosed area on a whole floor. That is a real result and it stands:

    E1.4 CLEAR-ROOM-BOUNDARY admission is insufficient as the separator
    set for a global planar arrangement.

It is not, however, a test of the arrangement REPRESENTATION. It is a test
of one admission gate. The experiment exposed a conflation that had been
carried since E1.2:

    CAN_OWN_CLEAR_ROOM_FACE   is not   CAN_PARTITION_THE_PLANAR_DOMAIN

A wall face that a room's finish does not follow still divides the plane.
A column standing behind a plastered face still occupies space. The edge
of a pool still separates walkable floor from water. None of those is a
clear room face, and every one of them partitions the drawing.

WHAT THIS MODULE IS

The complete rule set for Method 1b, written and hashed BEFORE the method
is constructed and before any cell result is seen. Nothing in it names a
room, a candidate, a project or an expected quantity. No rule anywhere
below consults face area, closure gain, candidate identity or benchmark
agreement to decide whether an edge enters the arrangement.

If Method 1b fails under these rules, it fails. There is no Method 1c.

THE ONE ADMISSION PRINCIPLE

    An interval enters the atomic arrangement when the source evidence
    establishes that SOMETHING PHYSICAL IS THERE, whatever it is.

    WHAT it is decides which PLANAR_PARTITION_CAPABILITY it carries. When
    what-it-is is not settled, the capability is UNRESOLVED and every cell
    whose closure depends on it says so in its own record.

    An interval whose evidence establishes that nothing physical is there
    - a dimension string, a witness line, a centre line, an annotation, a
    door leaf, a swing arc, furniture, a cabinet front, a counter edge, a
    line above or below the cut plane - does not enter.

That principle is the whole difference from Method 1A, which asked instead
whether the interval could be the surface a surveyor measures to.
"""

from __future__ import annotations

import hashlib

from engine import interval_role as ir
from engine import line_semantics as ls
from engine import column_validation as cv
from engine import curve_semantics as cs
from engine import cad_entity_role as cer
from research.arrangement_experiment_01 import protocol as P

METHOD = "METHOD_1B_ATOMIC_PLANAR_ARRANGEMENT"
MODEL = "AN_EDGE_CAN_PARTITION_THE_PLANE_WITHOUT_BEING_A_WALL_V1"

THE_LESSON_THIS_METHOD_EXISTS_TO_RECORD = (
    "E1_4_CLEAR_ROOM_BOUNDARY_CAPABILITY != PLANAR_PARTITION_CAPABILITY")

WHAT_METHOD_1A_ESTABLISHED = (
    "E1.4 CLEAR-ROOM-BOUNDARY admission is insufficient as the separator "
    "set for a global planar arrangement. Method 1A is preserved exactly "
    "as run and is not reframed, re-scored or overwritten by this method")

THE_B_C_D_MEASUREMENTS_ARE_NOT_A_METHOD = (
    "DEVELOPMENT_DIAGNOSTIC_ONLY. The four-set widening measurement "
    "located the cause of the Method 1A starvation and motivated this "
    "method. Set C and set D are NOT Method 1b and are not promoted into "
    "it. Method 1b admits by capability, not by widening a gate")

# =====================================================================
# 1. THE NEW CAPABILITY DIMENSION
# =====================================================================

CAPABILITY = "PLANAR_PARTITION_CAPABILITY"

HARD_PHYSICAL_SEPARATOR = "HARD_PHYSICAL_SEPARATOR"
OBSTACLE_BOUNDARY = "OBSTACLE_BOUNDARY"
NON_FLOOR_REGION_BOUNDARY = "NON_FLOOR_REGION_BOUNDARY"
SOFT_SEMANTIC_BOUNDARY = "SOFT_SEMANTIC_BOUNDARY"
PORTAL_BREAK = "PORTAL_BREAK"
COMPUTATIONAL_DOMAIN_BOUNDARY = "COMPUTATIONAL_DOMAIN_BOUNDARY"
NON_SEPARATOR = "NON_SEPARATOR"
UNRESOLVED = "UNRESOLVED"

PLANAR_PARTITION_CAPABILITIES = (
    HARD_PHYSICAL_SEPARATOR, OBSTACLE_BOUNDARY, NON_FLOOR_REGION_BOUNDARY,
    SOFT_SEMANTIC_BOUNDARY, PORTAL_BREAK, COMPUTATIONAL_DOMAIN_BOUNDARY,
    NON_SEPARATOR, UNRESOLVED,
)

# The capabilities this one is NOT. Each of these answers a different
# engineering question and none of them may be read off this one.
THIS_IS_INDEPENDENT_OF = (
    "MATERIAL_PRESENT",
    "CAN_OWN_CLEAR_FINISH_FACE",
    "CAN_CONTRIBUTE_WALL_LENGTH",
    "CAN_CONTRIBUTE_MATERIAL_LENGTH",
    "CAN_BOUND_CLEAR_FLOOR_REGION",
)

AN_EDGE_CAN_PARTITION_WITHOUT_BEING_A_WALL = (
    "partitioning the plane and being a wall are different claims. An "
    "obstacle footprint partitions and builds no wall. A pool edge "
    "partitions and is not masonry. A portal break partitions the face "
    "graph and carries no material across the opening. Nothing downstream "
    "may read a material quantity off this capability, and nothing may "
    "read this capability off a material quantity")

# Which capabilities actually cut the plane when the faces are formed.
CUTS_THE_PLANE = (HARD_PHYSICAL_SEPARATOR, OBSTACLE_BOUNDARY,
                  NON_FLOOR_REGION_BOUNDARY, SOFT_SEMANTIC_BOUNDARY,
                  PORTAL_BREAK, COMPUTATIONAL_DOMAIN_BOUNDARY, UNRESOLVED)
DOES_NOT_ENTER_THE_ARRANGEMENT = (NON_SEPARATOR,)

# Which of them assert physical separation of free space.
PHYSICALLY_SEPARATES = (HARD_PHYSICAL_SEPARATOR, OBSTACLE_BOUNDARY,
                        NON_FLOOR_REGION_BOUNDARY)
EXPLICITLY_DOES_NOT_SEPARATE = (PORTAL_BREAK, SOFT_SEMANTIC_BOUNDARY,
                                COMPUTATIONAL_DOMAIN_BOUNDARY)
SEPARATION_NOT_SETTLED = (UNRESOLVED,)

# Which of them may ever carry material, wall length, or a finish face.
MAY_CARRY_MATERIAL = (HARD_PHYSICAL_SEPARATOR, OBSTACLE_BOUNDARY)
MAY_CARRY_WALL_LENGTH = (HARD_PHYSICAL_SEPARATOR,)
NEVER_CARRIES_ANYTHING_MEASURABLE = (
    NON_FLOOR_REGION_BOUNDARY, SOFT_SEMANTIC_BOUNDARY, PORTAL_BREAK,
    COMPUTATIONAL_DOMAIN_BOUNDARY)

A_SOFT_PARTITION_IS_NEVER_A_WALL = P.A_SOFT_PARTITION_IS_NEVER_A_WALL

# =====================================================================
# 2. THE ADMISSION TABLE - semantic role to partition capability
# =====================================================================
#
# Read a row as: what an interval carrying this established semantic role
# contributes to the PARTITION question. It says nothing about material,
# wall length or finish face, each of which is asked elsewhere.

BY_ROLE = {
    # ---- something physical is there, and what it is is established ----
    ir.MATERIAL_WALL_FACE: HARD_PHYSICAL_SEPARATOR,
    ir.GLAZING: HARD_PHYSICAL_SEPARATOR,
    # a column is admitted through the structural-object channel as one
    # closed footprint, never as its constituent intervals - see §4
    ir.COLUMN: OBSTACLE_BOUNDARY,
    # a non-floor contour divides walkable floor from what is not floor
    ir.POOL_CONTOUR: NON_FLOOR_REGION_BOUNDARY,

    # ---- something physical is there and what it is is NOT settled ----
    ir.COLUMN_CANDIDATE_UNRESOLVED: UNRESOLVED,
    ir.AMBIGUOUS_PAIRED_BAND: UNRESOLVED,

    # ---- the evidence establishes that nothing separating is there ----
    ir.POOL_INTERNAL_GEOMETRY: NON_SEPARATOR,
    ir.CASEWORK: NON_SEPARATOR,
    ir.CABINET_FRONT: NON_SEPARATOR,
    ir.COUNTER_EDGE: NON_SEPARATOR,
    ir.FIXTURE: NON_SEPARATOR,
    ir.FURNITURE: NON_SEPARATOR,
    ir.STAIR_GEOMETRY: NON_SEPARATOR,
    ir.DIMENSION_LINE: NON_SEPARATOR,
    ir.DIMENSION_WITNESS: NON_SEPARATOR,
    ir.CONSTRUCTION_LINE: NON_SEPARATOR,
    ir.DOOR: NON_SEPARATOR,
    ir.ANNOTATION: NON_SEPARATOR,
    ir.LEVEL_OR_GRID_ANNOTATION: NON_SEPARATOR,

    # ---- no role established at all ----
    # UNKNOWN is not the same as UNRESOLVED. UNRESOLVED means the drawing
    # establishes that something built is there and not which thing.
    # UNKNOWN means no positive evidence of anything was found. Admitting
    # every UNKNOWN stroke as a separator would let unclassified linework
    # carve the floor, which is the failure this whole line of work
    # exists to prevent.
    ir.UNKNOWN: NON_SEPARATOR,
}

WHY_UNKNOWN_IS_NOT_UNRESOLVED = (
    "UNRESOLVED is a claim: something built stands here and the drawing "
    "does not say which thing. UNKNOWN is the absence of a claim. An "
    "arrangement that admits absence of evidence as a separator is an "
    "arrangement that will cut a room in half along a stray stroke, and "
    "no downstream pass could tell that it had")

WHY_A_STAIR_TREAD_DOES_NOT_PARTITION = (
    "a tread, a riser line and a nosing describe how a floor changes "
    "level. They are drawn on the floor, not built across it. A stair "
    "assembly may sit inside a physical space and it does not divide one "
    "space into fourteen")

WHY_A_DOOR_LEAF_DOES_NOT_PARTITION = (
    "the leaf and its swing arc are evidence that an opening exists. The "
    "opening is represented by a PORTAL_BREAK on the wall it interrupts, "
    "which connects the cells either side. The leaf itself bounds nothing "
    "and a swing arc that partitioned the plane would cut a quarter "
    "circle out of every room with a door")

# =====================================================================
# 3. THE LINE-SEMANTICS VETO - §6, hidden and overhead geometry
# =====================================================================
#
# E1.4's repair stands. Geometry the drawing establishes as being outside
# the cut plane does not enter the arrangement, and it does not re-enter
# because polygonisation improves. Closure gain is not semantic evidence.
#
# The veto needs POSITIVE evidence. A line whose linetype the CAD does not
# expose is classified UNRESOLVED by line semantics, and that status
# answers "is this in the cut plane" with silence, not with no. The ROLE
# pass has independently established what the thing is; line semantics may
# only veto on evidence that it is not in the cut plane.

VETOED_BY_LINE_SEMANTICS = (
    ls.OVERHEAD_GEOMETRY,
    ls.BELOW_CUT_PLANE_GEOMETRY,
    ls.STAIR_PROJECTION,
    ls.CENTERLINE,
    ls.DIMENSION_OR_WITNESS,
    ls.ANNOTATION,
)
NOT_VETOED_BY_LINE_SEMANTICS = (ls.VISIBLE_MATERIAL_FACE, ls.UNRESOLVED)

A_VETO_NEEDS_POSITIVE_EVIDENCE = (
    "Method 1A required LINE_SEMANTICS_STATUS to be VISIBLE_MATERIAL_FACE "
    "before an interval could bound anything, so every interval whose "
    "linetype the CAD does not expose was refused on the absence of "
    "evidence. Here the veto list is stated explicitly and an UNRESOLVED "
    "line-semantics status vetoes nothing. How many intervals enter on "
    "that status is counted and reported, so the effect of this decision "
    "is visible rather than buried")

CLOSURE_GAIN_IS_NOT_SEMANTIC_EVIDENCE = (
    "no interval, layer or class of geometry is admitted, restored or "
    "re-read because admitting it closes more faces or encloses more "
    "area. The admission rules were written and hashed before the first "
    "face of this method existed")

# =====================================================================
# 4. CLEAR-FACE OWNERSHIP DOES NOT GATE ADMISSION
# =====================================================================

CLEAR_FACE_OWNERSHIP_IS_NOT_ASKED_HERE = (
    "E1.4 holds an object's outline back from a room's boundary when the "
    "architectural face owns the clear face at that location, or when "
    "ownership there is not settled. That is the correct answer to the "
    "question E1.4 asks, and it is the wrong question here. A column "
    "behind a plastered face does not stop occupying space because the "
    "plaster is what a surveyor measures to. Ownership decides what a "
    "room's finish follows; it does not decide what exists in the plane. "
    "Method 1b therefore does not consult CLEAR_FACE_OWNERSHIP_STATUS "
    "when admitting an edge, and records each edge's ownership status "
    "beside its partition capability so the two stay visibly separate")

A_BURIED_OBJECT_MAKES_NO_FREE_SPACE = (
    "a structural object buried inside a wall solid still enters the "
    "arrangement, and the faces it creates lie inside material. They are "
    "classified as material or obstacle before anything is grouped, so a "
    "buried object creates no new free-space segmentation. That follows "
    "from classifying the cells honestly and needs no special case")

# =====================================================================
# 5. STRUCTURAL OBJECTS - §4, existence is not boundary relevance
# =====================================================================

STRUCTURAL_EXISTENCE = "STRUCTURAL_EXISTENCE"
ARRANGEMENT_BOUNDARY_RELEVANCE = "ARRANGEMENT_BOUNDARY_RELEVANCE"

EXISTENCE_IS_NOT_BOUNDARY_RELEVANCE = (
    "that a structural object exists is one finding. That a particular "
    "stroke of its linework should cut the plane is another. A confirmed "
    "column contributes ONE closed outer footprint. Its centre lines, its "
    "internal hatching, the stretches where its sides are parts of longer "
    "wall lines, and every construction fragment around it contribute "
    "nothing. Adding all held-back structural linework would polygonise "
    "the drawing beautifully and would mean nothing")

# The channel a structural object enters by, and the only geometry it may
# offer: one closed ring per object, derived from the object's own loop.
STRUCTURAL_OBJECT_FOOTPRINT = "STRUCTURAL_OBJECT_FOOTPRINT"

STRUCTURAL_ADMISSION = {
    # existence status -> what the object's closed outer footprint carries
    cv.STRUCTURAL_COLUMN_CONFIRMED: OBSTACLE_BOUNDARY,
    cv.STRUCTURAL_COLUMN_UNRESOLVED: UNRESOLVED,
    cv.NOT_A_STRUCTURAL_COLUMN: None,   # not admitted through this channel
}

STRUCTURAL_FOOTPRINT_RULES = (
    "the ring is the object's own LOOP_RING, derived from its members. "
    "Where LOOP_RING_ESTABLISHED is false the object offers no footprint "
    "and that is recorded, not patched",
    "the ring enters as ONE closed edge chain with one EDGE_ID, not as a "
    "set of side intervals",
    "a candidate the validation withdrew (NOT_A_STRUCTURAL_COLUMN) offers "
    "no obstacle footprint; its member intervals stand or fall on their "
    "own established interval roles like any other linework",
    "no interval whose role is COLUMN is admitted individually. It is "
    "represented by its object's footprint. Intervals carrying that role "
    "with no validated object behind them are counted and reported, and "
    "they do not enter",
    "an obstacle footprint creates an obstacle cell. It creates no wall "
    "quantity, no finish face and no wall length",
)

# =====================================================================
# 6. NON-FLOOR REGIONS - §5, general, no project rule
# =====================================================================

WATER_EDGE = "WATER_EDGE"
COPING_EDGE = "COPING_EDGE"
DECORATIVE_ARC = "DECORATIVE_ARC"
OTHER_NON_FLOOR_SUBROLE = "OTHER"
NON_FLOOR_SUBROLE_UNRESOLVED = "NON_FLOOR_SUBROLE_UNRESOLVED"

# A non-floor contour is established ONLY where the source evidence
# establishes the region's identity independently of its shape, and the
# curve's own semantic places it on the region's outline. E1.4's curve
# semantics already answer both: a round object becomes a water body only
# when a label group beside it says so, and each ring carries its own
# curve semantic with a confidence.
NON_FLOOR_CONTOUR_SEMANTICS = (cs.POOL_OUTER_CONSTRUCTION, cs.POOL_WALL_FACE)
NON_FLOOR_MIN_CONFIDENCE = (cer.HIGH, cer.MEDIUM)

NON_FLOOR_ADMISSION_RULE = (
    "an interval enters as NON_FLOOR_REGION_BOUNDARY when (a) its "
    "established semantic role is a non-floor contour role, (b) the "
    "region it outlines was identified by source evidence that is not "
    "its own shape - a label group naming the region - and (c) its curve "
    "semantic is one of the region's outline semantics at HIGH or MEDIUM "
    "confidence. If any of the three is missing the interval enters as "
    "UNRESOLVED and the cells that depend on it are UNRESOLVED_CELL")

NON_FLOOR_EDGES_CARRY = {
    "MATERIAL_WALL": False,
    "WALL_LENGTH_CONTRIBUTION_MM": 0.0,
    "CLEAR_ROOM_FACE": False,
    "PHYSICAL_ROOM_WALL": False,
}

THE_SUBROLE_IS_RECORDED_SEPARATELY = (
    "whether a given non-floor contour is the water edge, the coping "
    "edge, a decorative arc or something else is a finer question than "
    "the one this method asks. E1.4 does not answer it and Method 1b "
    "does not invent an answer: NON_FLOOR_SUBROLE is recorded as "
    "UNRESOLVED on every such edge. The arrangement may create a "
    "non-floor cell without claiming the edge is masonry and without "
    "claiming which kind of non-floor edge it is")

DO_NOT_CHOOSE_THE_READING_THAT_CLOSES_THE_FACE = (
    "four non-floor intervals changed the diagnostic's enclosed area by "
    "207.8 m2. That is evidence that this semantic class matters "
    "topologically. It is not evidence that those arcs are correct, and "
    "no rule here resolves a role towards the reading that closes a "
    "larger face. The rule above was written before this method was "
    "built and does not mention area")

# =====================================================================
# 7. PORTALS - §7, adjacency not fake closure
# =====================================================================

PORTAL_RULES = (
    "a door opening does not become a separator chord in order to close "
    "cells. The wall it interrupts is the separating construction; the "
    "opening is one PORTAL_BREAK edge lying in the line of that wall",
    "a PORTAL_BREAK carries MATERIAL_PRESENT = false, "
    "WALL_LENGTH_CONTRIBUTION = 0 and PHYSICAL_SEPARATION = false",
    "the cell adjacency register records the cells either side of a "
    "PORTAL_BREAK as CONNECTED_THROUGH_A_PORTAL. Adjacency through the "
    "opening is preserved and is the point of the edge existing",
    "no fake material edge is drawn across an opening, and no pass may "
    "read wall length, finish face or material off a portal break",
)

# A gap the drawing leaves that no portal evidence explains is not a
# portal and is not a wall. It closes the topology and says so.
UNRESOLVED_GAP_RULE = (
    "a gap in the fabric with no established portal evidence enters as "
    "UNRESOLVED. It holds the topology together and every cell whose "
    "closure depends on it is UNRESOLVED_CELL")

# =====================================================================
# 8. THE EXTERIOR - §9, no computational frame unless forced
# =====================================================================

EXTERIOR_RULE = (
    "the arrangement library supports an unbounded exterior face "
    "naturally: the complement of the union of the bounded faces. That "
    "face is used. No computational bounding frame is introduced, so no "
    "frame edge exists to be mistaken for a wall and the earlier failure "
    "where a window became a room boundary cannot repeat",
    "if a frame ever becomes technically necessary, every frame edge is "
    "labelled COMPUTATIONAL_DOMAIN_BOUNDARY with PHYSICAL = false and "
    "MEASUREMENT_CONTRIBUTION = 0, and no physical space or quantity may "
    "inherit it. The count of such edges is reported either way",
)

OUTSIDE_CELL_ID = "C-OUTSIDE"

# =====================================================================
# 9. CELL CLASSES AND THE ORDER THEY ARE DECIDED IN - §8
# =====================================================================

FREE_SPACE_CELL = "FREE_SPACE_CELL"
MATERIAL_SOLID_CELL = "MATERIAL_SOLID_CELL"
OBSTACLE_CELL = "OBSTACLE_CELL"
NON_FLOOR_CELL = "NON_FLOOR_CELL"
OUTSIDE_OR_UNBOUNDED_CELL = "OUTSIDE_OR_UNBOUNDED_CELL"
UNRESOLVED_CELL = "UNRESOLVED_CELL"

CELL_CLASSES = (FREE_SPACE_CELL, MATERIAL_SOLID_CELL, OBSTACLE_CELL,
                NON_FLOOR_CELL, OUTSIDE_OR_UNBOUNDED_CELL, UNRESOLVED_CELL)

# The tests are applied in this order and the first that answers wins.
# Every test is stated here before the method runs.
CELL_CLASSIFICATION_ORDER = (
    ("1_SLIVER",
     "smaller than the sliver threshold. A junction artefact of noding, "
     "not a space. Recorded as MATERIAL_SOLID_CELL and counted separately"),
    ("2_INSIDE_ONE_PAIRED_WALL_BODY",
     "bounded only by edges carrying material, thin, and its bounding "
     "faces belong to one paired wall body. This is the inside of a wall "
     "and it is not floor"),
    ("3_INSIDE_A_STRUCTURAL_FOOTPRINT",
     "its representative point lies inside the closed footprint of a "
     "structural object admitted as OBSTACLE_BOUNDARY"),
    ("4_THIN_AND_ALL_MATERIAL_BUT_UNPAIRED",
     "bounded only by material and thin, with no pairing to establish it "
     "as one wall body. An obstacle, and what kind is not settled here"),
    ("5_INSIDE_AN_ESTABLISHED_NON_FLOOR_REGION",
     "its representative point lies inside a region closed by "
     "NON_FLOOR_REGION_BOUNDARY edges"),
    ("6_CLOSURE_DEPENDS_ON_UNRESOLVED_EDGES",
     "the cell does not survive the unresolved-edge counterfactual: with "
     "every UNRESOLVED edge withdrawn, no face of the arrangement covers "
     "its representative point. The cell exists only because of geometry "
     "whose meaning is not settled, so it is UNRESOLVED_CELL"),
    ("7_OTHERWISE", "bounded, not a sliver, not the inside of a wall, not "
     "an obstacle, not non-floor, and it survives without any unresolved "
     "edge. FREE_SPACE_CELL"),
)

THE_UNRESOLVED_COUNTERFACTUAL = (
    "a cell touching an unresolved edge is not automatically unresolved. "
    "What matters is whether the unresolved geometry is load-bearing for "
    "its closure, and that is measured rather than assumed: the faces are "
    "formed a second time from the admitted edges MINUS every UNRESOLVED "
    "edge, and a cell whose representative point lands in no face of that "
    "second arrangement had its closure from geometry nobody has "
    "identified. This is a counterfactual, not a threshold, and it needs "
    "no tuned number")

COUNT_THE_MATERIAL_CELLS_SEPARATELY = (
    "walls and columns generate many small material and obstacle cells. "
    "A large face count is not a result. Every class is counted on its "
    "own line and the thing this experiment goes on to group is "
    "FREE_SPACE_CELL")

SLIVER_AREA_MM2 = 10_000.0          # unchanged from Method 1A
WALL_FACE_MAX_THICKNESS_MM = 600.0  # unchanged from Method 1A
NODE_SNAP_MM = 1.0                  # unchanged from Method 1A

THE_THRESHOLDS_ARE_INHERITED_NOT_TUNED = (
    "the sliver area, the wall-face thickness limit and the node snap are "
    "carried across from Method 1A unchanged. Method 1b changes what is "
    "ADMITTED, not how faces are measured, and moving a threshold between "
    "the two methods would make the comparison meaningless")

# =====================================================================
# 10. CURVES - §10
# =====================================================================

ARC_TOPOLOGY_TOLERANCE_MM = 2.0

CURVE_RULES = (
    "the analytical source arc is preserved exactly in provenance: its "
    "entity, its kind, its centre, its radius and its angles",
    "the topology may linearise an arc, and every linearised edge records "
    "SOURCE_CURVE_ID, SOURCE_CURVE_TYPE, TOPOLOGY_APPROXIMATION and "
    "MAX_APPROXIMATION_ERROR measured from the analytical arc",
    "no measurement anywhere may treat a chord as the source arc. A "
    "length or an area that matters is taken from the analytical source",
)

A_CHORD_IS_NEVER_AN_ARC = (
    "a linearisation exists so that a topology library can node a curve. "
    "It is not the geometry, it is never written back over the source, "
    "and its deviation from the source is recorded on the edge itself")

# =====================================================================
# 11. WHAT EVERY EDGE RECORDS - §12
# =====================================================================

EDGE_FIELDS = (
    "EDGE_ID",
    "SOURCE_ENTITY_IDS",
    "SOURCE_INTERVAL_IDS",
    "SEMANTIC_ROLE",
    "PLANAR_PARTITION_CAPABILITY",
    "MATERIAL_PRESENT",
    "PHYSICAL_SEPARATION",
    "CAN_OWN_CLEAR_FINISH_FACE",
    "WALL_LENGTH_CONTRIBUTION_ALLOWED",
    "ADJACENT_CELL_IDS",
    "PROVENANCE",
)

# =====================================================================
# 12. WHAT COUNTS AS A MEANINGFUL REPRESENTATION - §13
# =====================================================================
#
# Three named tests, none of which consults an area, a benchmark, or how
# close a cell is to anything.

MEANINGFUL_ATOMIC_CELL_REPRESENTATION = "MEANINGFUL_ATOMIC_CELL_REPRESENTATION"
NO_MEANINGFUL_CELL_REPRESENTATION = "NO_MEANINGFUL_CELL_REPRESENTATION"

REPRESENTATION_TESTS = (
    ("ANCHOR_LANDS_IN_A_BOUNDED_CELL",
     "the case's frozen E1.4 label seed anchor - a point the source "
     "establishes, not an area - lies inside a bounded face of the "
     "arrangement rather than in the unbounded exterior"),
    ("THE_CELL_IS_NOT_MATERIAL_OR_SLIVER",
     "the face the anchor lands in is not classified MATERIAL_SOLID_CELL "
     "and is not a noding sliver. A label anchor inside a wall means the "
     "arrangement did not represent that space at all"),
    ("NO_HARD_SEPARATOR_RUNS_THROUGH_THE_CELL",
     "no admitted HARD_PHYSICAL_SEPARATOR edge lies in the interior of "
     "that face. A face that swallows a wall is a face that failed to "
     "partition, however plausible its outline looks"),
)

REPRESENTATION_VERDICT_RULE = (
    "a case has a MEANINGFUL_ATOMIC_CELL_REPRESENTATION when all three "
    "tests pass. Otherwise NO_MEANINGFUL_CELL_REPRESENTATION, with the "
    "failing test named. Where the representation is legitimately several "
    "adjacent cells - an open-plan cluster, a space entered through a "
    "portal - the cells reachable from the anchor cell through "
    "PORTAL_BREAK adjacency alone are reported beside the verdict. That "
    "set is reported, not scored")

AREA_CLOSENESS_IS_NOT_A_TEST = (
    "no verdict above compares a cell's area to anything. Area closeness "
    "would be reconciliation to an expected geometry, and no expected "
    "geometry, manual take-off or benchmark quantity is opened anywhere "
    "in this experiment")

# =====================================================================
# 13. THE POOL / NON-FLOOR AUDIT - §14
# =====================================================================

NON_FLOOR_AUDIT_QUESTIONS = (
    "which source curves each NON_FLOOR_REGION_BOUNDARY edge derives "
    "from, by entity id, kind, centre and radius",
    "which cells each of those edges borders",
    "whether one side of each is classified NON_FLOOR_CELL",
    "whether the edges close a loop that is otherwise unbounded, measured "
    "by withdrawing them and re-forming the faces",
    "whether the local overlay shows a sensible topology",
)

THE_LARGE_AREA_EFFECT_IS_NEITHER_PROOF_NOR_DISPROOF = (
    "that these edges change enclosed area by a large amount is a "
    "topological fact about closure, not a semantic argument that they "
    "are correct. The audit reports what they do and does not argue from "
    "how much they do it")

# =====================================================================
# 14. SURVIVAL - §15
# =====================================================================

SURVIVAL_CRITERIA = (
    "each of the seven selected cases has a meaningful atomic cell "
    "representation, or a clearly explainable representation consisting "
    "of multiple adjacent cells",
    "the open-plan cluster is representable without inserting a fake "
    "physical wall",
    "Pantry can remain open while still participating in cell topology",
    "the E1.4 closed W.C and Kitchen are not destroyed by the arrangement",
    "portal and opening relations appear as adjacency, not fake closure",
    "curves remain traceable to analytical source geometry",
)

IF_IT_FAILS_IT_FAILS = (
    "if Method 1b fails these representation criteria the experiment "
    "stops and reports the arrangement hypothesis as failing. It is not "
    "rescued again. There is no Method 1c, 1d or 1e, and no rule in this "
    "protocol may be changed after the first cell result is seen")

NOTHING_IS_SCORED_YET = (
    "no Excel, no manual area, no known expected m2, no corrected "
    "polygon. Methods 1b, 2, 3 and A20 are frozen first and independent "
    "scoring happens later")


def protocol_hash() -> str:
    parts = ([METHOD, MODEL, THE_LESSON_THIS_METHOD_EXISTS_TO_RECORD]
             + list(PLANAR_PARTITION_CAPABILITIES)
             + list(THIS_IS_INDEPENDENT_OF)
             + [f"{r}:{c}" for r, c in sorted(BY_ROLE.items())]
             + list(VETOED_BY_LINE_SEMANTICS)
             + [f"{k}:{v}" for k, v in sorted(
                 STRUCTURAL_ADMISSION.items(), key=lambda kv: kv[0])]
             + list(NON_FLOOR_CONTOUR_SEMANTICS)
             + list(NON_FLOOR_MIN_CONFIDENCE)
             + [NON_FLOOR_ADMISSION_RULE]
             + list(PORTAL_RULES)
             + list(EXTERIOR_RULE)
             + list(CELL_CLASSES)
             + [k for k, _ in CELL_CLASSIFICATION_ORDER]
             + [k for k, _ in REPRESENTATION_TESTS]
             + [REPRESENTATION_VERDICT_RULE]
             + list(CURVE_RULES)
             + list(EDGE_FIELDS)
             + list(SURVIVAL_CRITERIA)
             + [f"SLIVER={SLIVER_AREA_MM2}",
                f"WALL_FACE={WALL_FACE_MAX_THICKNESS_MM}",
                f"SNAP={NODE_SNAP_MM}",
                f"ARC_TOL={ARC_TOPOLOGY_TOLERANCE_MM}"])
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def record() -> dict:
    """The whole rule set, as it is written to PROTOCOL.json and hashed."""
    return {
        "EXPERIMENT_ID": P.EXPERIMENT_ID,
        "METHOD": METHOD,
        "MODEL": MODEL,
        "EXPERIMENT_CLASS": P.EXPERIMENT_CLASS,
        "THIS_IS_NOT_E1_5_AND_NOT_PRODUCTION_E2": True,
        "E1_4_IS_NOT_MODIFIED": True,
        "E1_4_RUN_ID": P.E1_4_RUN_ID,
        "E1_4_RUN_HASH": P.E1_4_RUN_HASH,
        "EXPERIMENT_PROTOCOL_HASH": P.protocol_hash(),

        "THE_LESSON_THIS_METHOD_EXISTS_TO_RECORD":
            THE_LESSON_THIS_METHOD_EXISTS_TO_RECORD,
        "WHAT_METHOD_1A_ESTABLISHED": WHAT_METHOD_1A_ESTABLISHED,
        "METHOD_1A_IS_PRESERVED_EXACTLY_AS_RUN": True,
        "THE_B_C_D_MEASUREMENTS_ARE_NOT_A_METHOD":
            THE_B_C_D_MEASUREMENTS_ARE_NOT_A_METHOD,
        "SET_C_AND_SET_D_ARE_NOT_PROMOTED_INTO_THIS_METHOD": True,

        "THE_ADMISSION_PRINCIPLE": __doc__.split(
            "THE ONE ADMISSION PRINCIPLE")[1].strip(),

        "PLANAR_PARTITION_CAPABILITY": {
            "VALUES": list(PLANAR_PARTITION_CAPABILITIES),
            "THIS_IS_INDEPENDENT_OF": list(THIS_IS_INDEPENDENT_OF),
            "an_edge_can_partition_without_being_a_wall":
                AN_EDGE_CAN_PARTITION_WITHOUT_BEING_A_WALL,
            "CUTS_THE_PLANE": list(CUTS_THE_PLANE),
            "DOES_NOT_ENTER_THE_ARRANGEMENT":
                list(DOES_NOT_ENTER_THE_ARRANGEMENT),
            "PHYSICALLY_SEPARATES": list(PHYSICALLY_SEPARATES),
            "EXPLICITLY_DOES_NOT_SEPARATE":
                list(EXPLICITLY_DOES_NOT_SEPARATE),
            "SEPARATION_NOT_SETTLED": list(SEPARATION_NOT_SETTLED),
            "MAY_CARRY_MATERIAL": list(MAY_CARRY_MATERIAL),
            "MAY_CARRY_WALL_LENGTH": list(MAY_CARRY_WALL_LENGTH),
            "NEVER_CARRIES_ANYTHING_MEASURABLE":
                list(NEVER_CARRIES_ANYTHING_MEASURABLE),
            "a_soft_partition_is_never_a_wall":
                A_SOFT_PARTITION_IS_NEVER_A_WALL,
        },

        "ADMISSION_BY_SEMANTIC_ROLE": dict(sorted(BY_ROLE.items())),
        "why_unknown_is_not_unresolved": WHY_UNKNOWN_IS_NOT_UNRESOLVED,
        "why_a_stair_tread_does_not_partition":
            WHY_A_STAIR_TREAD_DOES_NOT_PARTITION,
        "why_a_door_leaf_does_not_partition":
            WHY_A_DOOR_LEAF_DOES_NOT_PARTITION,

        "LINE_SEMANTICS_VETO": {
            "VETOED": list(VETOED_BY_LINE_SEMANTICS),
            "NOT_VETOED": list(NOT_VETOED_BY_LINE_SEMANTICS),
            "a_veto_needs_positive_evidence": A_VETO_NEEDS_POSITIVE_EVIDENCE,
            "closure_gain_is_not_semantic_evidence":
                CLOSURE_GAIN_IS_NOT_SEMANTIC_EVIDENCE,
            "E1_4_HIDDEN_AND_OVERHEAD_REPAIR_IS_KEPT": True,
        },

        "CLEAR_FACE_OWNERSHIP": {
            "IS_CONSULTED_WHEN_ADMITTING_AN_EDGE": False,
            "IS_RECORDED_ON_EVERY_EDGE": True,
            "why": CLEAR_FACE_OWNERSHIP_IS_NOT_ASKED_HERE,
            "a_buried_object_makes_no_free_space":
                A_BURIED_OBJECT_MAKES_NO_FREE_SPACE,
        },

        "STRUCTURAL_OBJECT_TREATMENT": {
            "TWO_DIFFERENT_FINDINGS": [STRUCTURAL_EXISTENCE,
                                       ARRANGEMENT_BOUNDARY_RELEVANCE],
            "existence_is_not_boundary_relevance":
                EXISTENCE_IS_NOT_BOUNDARY_RELEVANCE,
            "ADMISSION_CHANNEL": STRUCTURAL_OBJECT_FOOTPRINT,
            "BY_EXISTENCE_STATUS": {k: v for k, v
                                    in STRUCTURAL_ADMISSION.items()},
            "RULES": list(STRUCTURAL_FOOTPRINT_RULES),
            "THE_HELD_BACK_INTERVALS_ARE_NOT_INSERTED_WHOLESALE": True,
        },

        "NON_FLOOR_REGION_TREATMENT": {
            "THIS_RULE_NAMES_NO_PROJECT_AND_NO_ROOM": True,
            "CONTOUR_SEMANTICS_THAT_QUALIFY":
                list(NON_FLOOR_CONTOUR_SEMANTICS),
            "MINIMUM_CONFIDENCE": list(NON_FLOOR_MIN_CONFIDENCE),
            "RULE": NON_FLOOR_ADMISSION_RULE,
            "EVERY_SUCH_EDGE_CARRIES": dict(NON_FLOOR_EDGES_CARRY),
            "SUBROLE_CANDIDATES": [WATER_EDGE, COPING_EDGE, DECORATIVE_ARC,
                                   OTHER_NON_FLOOR_SUBROLE],
            "SUBROLE_RECORDED_AS": NON_FLOOR_SUBROLE_UNRESOLVED,
            "the_subrole_is_recorded_separately":
                THE_SUBROLE_IS_RECORDED_SEPARATELY,
            "do_not_choose_the_reading_that_closes_the_face":
                DO_NOT_CHOOSE_THE_READING_THAT_CLOSES_THE_FACE,
        },

        "PORTAL_TREATMENT": {
            "RULES": list(PORTAL_RULES),
            "UNRESOLVED_GAP_RULE": UNRESOLVED_GAP_RULE,
            "NO_FAKE_MATERIAL_EDGE_ACROSS_AN_OPENING": True,
        },

        "COMPUTATIONAL_DOMAIN_TREATMENT": {
            "RULES": list(EXTERIOR_RULE),
            "A_BOUNDING_FRAME_IS_USED": False,
            "OUTSIDE_CELL_ID": OUTSIDE_CELL_ID,
        },

        "CELL_CLASSES": list(CELL_CLASSES),
        "CELL_CLASSIFICATION_ORDER": [
            {"TEST": k, "MEANS": v} for k, v in CELL_CLASSIFICATION_ORDER],
        "the_unresolved_counterfactual": THE_UNRESOLVED_COUNTERFACTUAL,
        "count_the_material_cells_separately":
            COUNT_THE_MATERIAL_CELLS_SEPARATELY,
        "wall_thickness_is_not_room": P.WALL_THICKNESS_IS_NOT_ROOM,
        "THRESHOLDS_INHERITED_FROM_METHOD_1A": {
            "SLIVER_AREA_MM2": SLIVER_AREA_MM2,
            "WALL_FACE_MAX_THICKNESS_MM": WALL_FACE_MAX_THICKNESS_MM,
            "NODE_SNAP_MM": NODE_SNAP_MM,
            "why": THE_THRESHOLDS_ARE_INHERITED_NOT_TUNED,
        },

        "CURVE_TREATMENT": {
            "RULES": list(CURVE_RULES),
            "ARC_TOPOLOGY_TOLERANCE_MM": ARC_TOPOLOGY_TOLERANCE_MM,
            "RECORDED_ON_EVERY_LINEARISED_EDGE": [
                "SOURCE_CURVE_ID", "SOURCE_CURVE_TYPE",
                "TOPOLOGY_APPROXIMATION", "MAX_APPROXIMATION_ERROR"],
            "a_chord_is_never_an_arc": A_CHORD_IS_NEVER_AN_ARC,
        },

        "EDGE_FIELDS": list(EDGE_FIELDS),

        "REPRESENTATION_VERDICT": {
            "VALUES": [MEANINGFUL_ATOMIC_CELL_REPRESENTATION,
                       NO_MEANINGFUL_CELL_REPRESENTATION],
            "TESTS": [{"TEST": k, "MEANS": v}
                      for k, v in REPRESENTATION_TESTS],
            "RULE": REPRESENTATION_VERDICT_RULE,
            "area_closeness_is_not_a_test": AREA_CLOSENESS_IS_NOT_A_TEST,
        },

        "NON_FLOOR_AUDIT_QUESTIONS": list(NON_FLOOR_AUDIT_QUESTIONS),
        "the_large_area_effect_is_neither_proof_nor_disproof":
            THE_LARGE_AREA_EFFECT_IS_NEITHER_PROOF_NOR_DISPROOF,

        "SURVIVAL_CRITERIA": list(SURVIVAL_CRITERIA),
        "if_it_fails_it_fails": IF_IT_FAILS_IT_FAILS,
        "nothing_is_scored_yet": NOTHING_IS_SCORED_YET,
        "no_benchmark_until_every_method_is_frozen":
            P.NO_BENCHMARK_UNTIL_EVERY_METHOD_IS_FROZEN,

        "NO_RULE_HERE_NAMES_A_ROOM_A_CANDIDATE_OR_A_PROJECT": True,
        "NO_RULE_HERE_CONSULTS_FACE_AREA_OR_CLOSURE_GAIN": True,

        "METHOD_1B_PROTOCOL_HASH": protocol_hash(),
    }
