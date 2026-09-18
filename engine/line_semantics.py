"""E1.4 — what a drawn line MEANS, before anything asks it to bound a room.

THE DEFECT THIS REPLACES

Three cold reviewers independently reported the same thing about frozen
E1.3: stretches of boundary chain lying exactly along DASHED outlines -
the nested outlines of a stair above, of a slab edge below the cut plane -
carrying the role MATERIAL_WALL_FACE, and in one case a 4.55 m "column"
face. A dashed line drawn to show what is overhead had become visible
material because the chain needed something there and it was there.

A line that continues a chain is not thereby a wall. What a line MEANS is
established from evidence about the line, before any question about
boundaries is asked of it.

WHAT THIS DOES

One classifier, one status per stretch, from the evidence the drawing
actually offers: its linetype and dash pattern where the CAD exposes one,
its layer, whether it repeats, whether it runs with a stair, whether it
pairs with another face at a wall thickness, whether it is continuous, and
its entity type.

Positive evidence is required to call something visible material. Absence
of evidence is UNRESOLVED, and UNRESOLVED never bounds anything.
"""

from __future__ import annotations

import hashlib

MODEL = "WHAT_A_LINE_MEANS_IS_ESTABLISHED_BEFORE_IT_IS_ASKED_TO_BOUND_V1"

VISIBLE_MATERIAL_FACE = "VISIBLE_MATERIAL_FACE"
OVERHEAD_GEOMETRY = "OVERHEAD_GEOMETRY"
BELOW_CUT_PLANE_GEOMETRY = "BELOW_CUT_PLANE_GEOMETRY"
STAIR_PROJECTION = "STAIR_PROJECTION"
CENTERLINE = "CENTERLINE"
DIMENSION_OR_WITNESS = "DIMENSION_OR_WITNESS"
ANNOTATION = "ANNOTATION"
UNRESOLVED = "UNRESOLVED"

STATUSES = (VISIBLE_MATERIAL_FACE, OVERHEAD_GEOMETRY,
            BELOW_CUT_PLANE_GEOMETRY, STAIR_PROJECTION, CENTERLINE,
            DIMENSION_OR_WITNESS, ANNOTATION, UNRESOLVED)

# Only this status may be asked to bound anything.
MAY_BE_ASKED_TO_BOUND = (VISIBLE_MATERIAL_FACE,)

# --- evidence ------------------------------------------------------------
LINETYPE_IS_DASHED = "THE_LINETYPE_OR_DASH_PATTERN_IS_NOT_CONTINUOUS"
LINETYPE_IS_CONTINUOUS = "THE_LINETYPE_IS_CONTINUOUS"
LINETYPE_NOT_EXPOSED = "THE_CAD_DOES_NOT_EXPOSE_A_LINETYPE_FOR_THIS_ENTITY"
PAIRED_AT_A_WALL_THICKNESS = "IT_PAIRS_WITH_ANOTHER_FACE_AT_A_WALL_THICKNESS"
RUNS_WITH_A_STAIR = "IT_RUNS_WITH_DRAWN_STAIR_GEOMETRY"
LAYER_SAYS_OVERHEAD = "ITS_LAYER_NAMES_GEOMETRY_ABOVE_OR_BELOW_THE_CUT"
LAYER_SAYS_DIMENSION = "ITS_LAYER_IS_A_DIMENSION_OR_WITNESS_LAYER"
LAYER_SAYS_ANNOTATION = "ITS_LAYER_IS_AN_ANNOTATION_LAYER"
LAYER_SAYS_CENTERLINE = "ITS_LAYER_IS_A_CENTRELINE_LAYER"
REPEATS_AS_A_FAMILY = "THE_SAME_FIGURE_REPEATS_ACROSS_THE_DRAWING"
IS_INSIDE_A_WALL_BAND = "IT_LIES_INSIDE_AN_ESTABLISHED_WALL_BAND"
RASTER_SHOWS_A_SOLID_STROKE = "THE_SOURCE_RASTER_SHOWS_A_SOLID_STROKE_HERE"
RASTER_SHOWS_A_BROKEN_STROKE = "THE_SOURCE_RASTER_SHOWS_A_BROKEN_STROKE_HERE"

# Evidence that, on its own, positively establishes visible material.
POSITIVE_FOR_VISIBLE_MATERIAL = (PAIRED_AT_A_WALL_THICKNESS,
                                 IS_INSIDE_A_WALL_BAND,
                                 RASTER_SHOWS_A_SOLID_STROKE)

# Evidence that positively establishes the line is not in the cut plane.
POSITIVE_FOR_NOT_IN_THE_CUT_PLANE = (LINETYPE_IS_DASHED,
                                     LAYER_SAYS_OVERHEAD,
                                     RASTER_SHOWS_A_BROKEN_STROKE)

# A layer's linetype and the printed sheet can disagree. When they do,
# neither is silently preferred.
THE_LAYER_AND_THE_SHEET_DISAGREE = (
    "the layer this stretch is on carries a broken linetype, and the "
    "printed sheet shows a solid stroke along it. A layer's linetype is "
    "what was intended and the sheet is what was issued. Nobody here can "
    "say which governs, so what this line means is UNRESOLVED - it bounds "
    "nothing, and it is not asserted to be overhead either")

A_LINE_THAT_CONTINUES_A_CHAIN_IS_NOT_A_WALL = (
    "a chain needing something at a coordinate is not evidence that "
    "anything is built there. Dashed geometry is never promoted to visible "
    "material because it closes or continues a chain, and a status may not "
    "be revised by what a downstream pass would like it to be")

ABSENCE_OF_EVIDENCE_IS_UNRESOLVED = (
    "where the drawing offers nothing that settles what a line means, the "
    "answer is UNRESOLVED. UNRESOLVED bounds nothing, contributes nothing, "
    "and is reported rather than resolved by preference")


def model_hash() -> str:
    parts = [MODEL] + list(STATUSES) + list(POSITIVE_FOR_VISIBLE_MATERIAL) \
        + list(POSITIVE_FOR_NOT_IN_THE_CUT_PLANE)
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def classify(evidence) -> dict:
    """One stretch's line semantics, from the evidence offered about it."""
    ev = tuple(evidence or ())
    has = set(ev)

    def out(status, why, blocked=()):
        return {
            "LINE_SEMANTICS_STATUS": status,
            "MAY_BE_ASKED_TO_BOUND": status in MAY_BE_ASKED_TO_BOUND,
            "evidence": list(ev),
            "positive_evidence_for_visible_material": sorted(
                has & set(POSITIVE_FOR_VISIBLE_MATERIAL)),
            "positive_evidence_that_it_is_not_in_the_cut_plane": sorted(
                has & set(POSITIVE_FOR_NOT_IN_THE_CUT_PLANE)),
            "blocked_by": list(blocked),
            "why": why,
            "a_line_that_continues_a_chain_is_not_a_wall":
                A_LINE_THAT_CONTINUES_A_CHAIN_IS_NOT_A_WALL,
        }

    # Annotation, dimension and centreline work is what its layer says it
    # is, and no boundary question is asked of it.
    if LAYER_SAYS_DIMENSION in has:
        return out(DIMENSION_OR_WITNESS,
                   "a dimension or witness line measures the drawing and "
                   "builds nothing")
    if LAYER_SAYS_ANNOTATION in has:
        return out(ANNOTATION,
                   "annotation describes the drawing and builds nothing")
    if LAYER_SAYS_CENTERLINE in has:
        return out(CENTERLINE,
                   "a centreline locates something. It is not a face of it")

    not_cut = has & set(POSITIVE_FOR_NOT_IN_THE_CUT_PLANE)
    positive = has & set(POSITIVE_FOR_VISIBLE_MATERIAL)

    # The sheet is what was issued and the layer is what was intended. A
    # broken stroke on the sheet settles it; a solid stroke on the sheet
    # against a broken linetype on the layer settles nothing.
    if (RASTER_SHOWS_A_SOLID_STROKE in has
            and RASTER_SHOWS_A_BROKEN_STROKE not in has
            and not_cut and not_cut <= {LINETYPE_IS_DASHED}):
        row = out(UNRESOLVED, THE_LAYER_AND_THE_SHEET_DISAGREE,
                  blocked=sorted(not_cut | positive))
        row["CONFLICTING_EVIDENCE"] = sorted(not_cut | {
            RASTER_SHOWS_A_SOLID_STROKE})
        return row

    # Geometry positively shown to be outside the cut plane cannot be
    # visible material, however well it would have continued a chain.
    if not_cut:
        if RUNS_WITH_A_STAIR in has:
            return out(STAIR_PROJECTION,
                       "it is drawn outside the cut plane and runs with the "
                       "stair: it is the stair projected, not a wall",
                       blocked=sorted(positive))
        if LAYER_SAYS_OVERHEAD in has:
            return out(OVERHEAD_GEOMETRY,
                       "its layer says it is above or below the cut plane "
                       "and its linework agrees",
                       blocked=sorted(positive))
        return out(BELOW_CUT_PLANE_GEOMETRY,
                   "it is drawn broken, which is how this drawing shows "
                   "what the cut plane does not pass through. What it is "
                   "exactly is not settled; that it is not a visible face "
                   "is",
                   blocked=sorted(positive))

    if positive:
        return out(VISIBLE_MATERIAL_FACE,
                   "positive evidence places built material in the cut "
                   "plane along this stretch")

    if RUNS_WITH_A_STAIR in has:
        return out(STAIR_PROJECTION,
                   "it runs with drawn stair geometry and nothing "
                   "establishes it as a face of built fabric")

    return out(UNRESOLVED, ABSENCE_OF_EVIDENCE_IS_UNRESOLVED)


# --------------------------------------------------- what the sheet shows
# A stroke is read as printed along at least this many sample stations.
MIN_INK_SAMPLES = 12
# Solid: nearly every station has ink and the ink is not interrupted.
SOLID_MIN_INK_SHARE = 0.9
SOLID_MAX_BLANK_RUNS = 1
# Broken: ink and blank alternate more than once, with real blank in it.
BROKEN_MIN_BLANK_RUNS = 2
BROKEN_MIN_BLANK_SHARE = 0.15
BROKEN_MIN_INK_SHARE = 0.2


def raster_stroke_evidence(samples) -> dict:
    """Read a printed stroke as solid, broken, or neither, from ink samples.

    `samples` is the ink at evenly spaced stations along the stretch, in
    order: True where the sheet is dark. A dash pattern shows up as ink
    and blank alternating along the line; a solid stroke shows up as ink
    nearly everywhere with at most one interruption.

    Where the sheet does not settle it - too few stations, too little
    ink, one long blank because the crop ran off the sheet - this returns
    no evidence rather than a guess.
    """
    ink = [bool(v) for v in samples or ()]
    n = len(ink)
    if n < MIN_INK_SAMPLES:
        return {"EVIDENCE": None, "samples": n,
                "why": ("too few stations along this stretch for the sheet "
                        "to say anything about its stroke")}
    dark = sum(1 for v in ink if v)
    share = dark / n
    blank_runs, run = 0, False
    for v in ink:
        if not v and not run:
            blank_runs += 1
            run = True
        elif v:
            run = False
    blank_share = 1.0 - share
    base = {"samples": n, "ink_share": round(share, 4),
            "blank_runs": blank_runs}
    if share >= SOLID_MIN_INK_SHARE and blank_runs <= SOLID_MAX_BLANK_RUNS:
        return {**base, "EVIDENCE": RASTER_SHOWS_A_SOLID_STROKE,
                "why": "the sheet is inked along nearly all of this stretch"}
    if (blank_runs >= BROKEN_MIN_BLANK_RUNS
            and blank_share >= BROKEN_MIN_BLANK_SHARE
            and share >= BROKEN_MIN_INK_SHARE):
        return {**base, "EVIDENCE": RASTER_SHOWS_A_BROKEN_STROKE,
                "why": ("the sheet alternates ink and blank along this "
                        "stretch, which is how a dash pattern prints")}
    return {**base, "EVIDENCE": None,
            "why": ("the sheet neither shows a solid stroke here nor a "
                    "dash pattern. It says nothing about this stretch")}


# --------------------------------------- the drawing's own linetype table
A_LINETYPE_IS_READ_FROM_THE_DRAWING = (
    "which layers are drawn broken is read from the drawing's own LTYPE "
    "table and its layer records, not from a list of layer names anybody "
    "chose. A layer whose linetype has a dash pattern is drawn broken in "
    "this drawing, whatever it is called")

DASH_MARKS = ("_", "-", ".")


def linetype_table(objects) -> dict:
    """layer name -> what the drawing's own tables say its linetype is."""
    ltypes = {}
    for o in objects or ():
        if o.get("object") != "LTYPE":
            continue
        h = o.get("handle") or []
        key = h[-1] if h else None
        desc = str(o.get("description") or "")
        pattern = float(o.get("pattern_len") or 0.0)
        ltypes[key] = {
            "LINETYPE": o.get("name"),
            "PATTERN_LENGTH": pattern,
            "DESCRIPTION": desc,
            "IS_DASHED": bool(
                pattern > 0.0 or any(m * 2 in desc for m in DASH_MARKS)),
        }
    out = {}
    for o in objects or ():
        if o.get("object") != "LAYER":
            continue
        ref = o.get("ltype") or []
        row = ltypes.get(ref[-1] if ref else None)
        out[str(o.get("name"))] = {
            **(row or {"LINETYPE": None, "PATTERN_LENGTH": None,
                       "DESCRIPTION": "", "IS_DASHED": None}),
            "LINETYPE_WAS_EXPOSED": row is not None,
            "why": A_LINETYPE_IS_READ_FROM_THE_DRAWING,
        }
    return out


def layer_linetype_evidence(layer, table) -> str:
    """The one piece of linetype evidence the drawing offers about a layer."""
    row = (table or {}).get(str(layer))
    if not row or row.get("IS_DASHED") is None:
        return LINETYPE_NOT_EXPOSED
    return LINETYPE_IS_DASHED if row["IS_DASHED"] else LINETYPE_IS_CONTINUOUS


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "STATUSES": list(STATUSES),
        "MAY_BE_ASKED_TO_BOUND": list(MAY_BE_ASKED_TO_BOUND),
        "POSITIVE_FOR_VISIBLE_MATERIAL": list(POSITIVE_FOR_VISIBLE_MATERIAL),
        "POSITIVE_FOR_NOT_IN_THE_CUT_PLANE":
            list(POSITIVE_FOR_NOT_IN_THE_CUT_PLANE),
        "why": {
            "a_line_that_continues_a_chain_is_not_a_wall":
                A_LINE_THAT_CONTINUES_A_CHAIN_IS_NOT_A_WALL,
            "absence_of_evidence_is_unresolved":
                ABSENCE_OF_EVIDENCE_IS_UNRESOLVED,
        },
    }
