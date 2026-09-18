"""E1.2 §10 — a note about the site is not a room.

E1.1 counted 24 functional identities on the ground floor. Four of them
were NEIGHBOUR, NEIGHBOUR, STREET and SEA VIEW: notes telling a reader
what lies beyond the plot. They are not spaces, they have no boundary to
find, and counting them made the completeness denominator wrong and the
withheld list longer than it should be.

So every label gets a class before anything asks it for a boundary:

    PHYSICAL_SPACE_LABEL      names a space the drawing encloses
    FUNCTIONAL_ZONE_LABEL     names a use spanning several spaces
    SITE_CONTEXT_ANNOTATION   names what is OUTSIDE the plot
    LEVEL_ANNOTATION          a level or datum
    SECTION_MARK              a section or detail reference
    DIMENSION_TEXT            a number the dimension style printed
    OTHER_ANNOTATION          writing about the drawing
    UNRESOLVED_TEXT           glyphs nobody here can read

None of those four words is in this module. The class comes from where
the stamp sits relative to the plot, how big it is set beside the room
stamps, how it is turned relative to the plot edge, and whether the
glyphs read at all - so the same code classifies the next drawing's
"BEACH", "MAIN ROAD" or "ADJACENT PLOT" without being told.
"""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass

from engine import label_grouping as lg

MODEL = "A_NOTE_ABOUT_THE_SITE_IS_NOT_A_ROOM_V1"

PHYSICAL_SPACE_LABEL = "PHYSICAL_SPACE_LABEL"
FUNCTIONAL_ZONE_LABEL = "FUNCTIONAL_ZONE_LABEL"
SITE_CONTEXT_ANNOTATION = "SITE_CONTEXT_ANNOTATION"
LEVEL_ANNOTATION = "LEVEL_ANNOTATION"
SECTION_MARK = "SECTION_MARK"
DIMENSION_TEXT = "DIMENSION_TEXT"
OTHER_ANNOTATION = "OTHER_ANNOTATION"
UNRESOLVED_TEXT = "UNRESOLVED_TEXT"

LABEL_CLASSES = (PHYSICAL_SPACE_LABEL, FUNCTIONAL_ZONE_LABEL,
                 SITE_CONTEXT_ANNOTATION, LEVEL_ANNOTATION, SECTION_MARK,
                 DIMENSION_TEXT, OTHER_ANNOTATION, UNRESOLVED_TEXT)

# Only these two are spaces the floor is expected to account for.
IN_THE_COMPLETENESS_DENOMINATOR = (PHYSICAL_SPACE_LABEL,
                                   FUNCTIONAL_ZONE_LABEL)

SITE_CONTEXT_IS_NOT_A_SPACE = (
    "a note naming what lies beyond the plot has no boundary to find. "
    "Counting it as a physical space makes the denominator wrong and puts "
    "a permanent withheld row in the register for a thing that was never "
    "a room")

NO_WORD_LIST_DECIDES_THIS = (
    "no token is matched against a list of site words anywhere in this "
    "module. The class comes from placement relative to the plot, "
    "typography beside the room stamps, orientation and readability")

# --- evidence -----------------------------------------------------------
EV_OUTSIDE_THE_PLOT = "ITS_VISIBLE_CENTROID_LIES_OUTSIDE_THE_PLOT_FACE"
EV_NEAR_THE_SHEET_EDGE = "IT_SITS_IN_THE_OUTER_MARGIN_OF_THE_DRAWING"
EV_LARGER_THAN_ROOM_STAMPS = "SET_LARGER_THAN_THE_ROOM_STAMPS"
EV_RUNS_ALONG_A_PLOT_EDGE = "TURNED_TO_RUN_ALONG_A_PLOT_EDGE"
EV_INSIDE_THE_PLOT = "ITS_VISIBLE_CENTROID_LIES_INSIDE_THE_PLOT_FACE"
EV_READS_AS_A_LEVEL = "READS_AS_A_LEVEL_OR_DATUM"
EV_READS_AS_A_NUMBER = "READS_AS_A_NUMBER_ONLY"
EV_SHORT_TOKEN_NEAR_A_CIRCLE = "A_ONE_OR_TWO_GLYPH_TOKEN_INSIDE_A_CIRCLE"
EV_A18_ZONE_ONLY = "THE_FROZEN_READING_TIES_IT_TO_A_ZONE_NOT_A_SPACE"
EV_NO_READABLE_GLYPHS = "NO_READABLE_GLYPHS"
EVIDENCE = (EV_OUTSIDE_THE_PLOT, EV_NEAR_THE_SHEET_EDGE,
            EV_LARGER_THAN_ROOM_STAMPS, EV_RUNS_ALONG_A_PLOT_EDGE,
            EV_INSIDE_THE_PLOT, EV_READS_AS_A_LEVEL, EV_READS_AS_A_NUMBER,
            EV_SHORT_TOKEN_NEAR_A_CIRCLE, EV_A18_ZONE_ONLY,
            EV_NO_READABLE_GLYPHS)

# --- GENERAL thresholds -------------------------------------------------
MARGIN_SHARE = 0.06            # of the drawing region's short side
LARGER_THAN_ROOM_STAMPS = 1.25  # times the median room-stamp height
PLOT_EDGE_ALIGN_DEG = 12.0
SECTION_MARK_MAX_GLYPHS = 2

_LEVEL = re.compile(r"^\s*(%%[a-zA-Z]|[+\-±])?\s*\d+(\.\d+)?\s*$")
_NUMERIC = re.compile(r"^\s*[\d.,+\-±%]+\s*$")


def model_hash() -> str:
    parts = [MODEL] + list(LABEL_CLASSES) + list(EVIDENCE) + [
        f"{MARGIN_SHARE}", f"{LARGER_THAN_ROOM_STAMPS}"]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


@dataclass
class LabelRow:
    label_id: str = ""
    text: str = ""
    label_class: str = UNRESOLVED_TEXT
    evidence: tuple = ()
    at_mm: tuple = (0.0, 0.0)
    height_mm: float = 0.0
    group_id: str = ""
    in_denominator: bool = False
    why: str = ""

    def record(self) -> dict:
        return {
            "LABEL_ID": self.label_id,
            "text": self.text,
            "LABEL_CLASS": self.label_class,
            "EVIDENCE": list(self.evidence),
            "visible_centroid_mm": [round(self.at_mm[0], 2),
                                    round(self.at_mm[1], 2)],
            "text_height_mm": round(self.height_mm, 2),
            "LABEL_GROUP": self.group_id,
            "IN_PHYSICAL_SPACE_DENOMINATOR": self.in_denominator,
            "why": self.why,
            "site_context_is_not_a_space": SITE_CONTEXT_IS_NOT_A_SPACE,
        }


PLOT_FACE_MIN_SHARE = 0.25
PLOT_BASIS_LARGEST_FACE = "THE_LARGEST_FACE_THE_BUILT_LINEWORK_CLOSES"
PLOT_BASIS_HULL = "THE_OUTLINE_THE_BUILT_LINEWORK_REACHES"


def plot_face(material_segments, *, region=None):
    """The drawing's own outline, used ONLY to ask inside-or-outside.

    The built linework of a real floor rarely closes the plot: every
    opening breaks it. So the largest closed face is used when it is a
    substantial part of the drawing, and otherwise the outline the
    linework REACHES - its convex hull - stands in for the plot. Which
    basis was used is recorded, and no measurement comes from either.
    """
    try:
        from shapely.geometry import LineString
        from shapely.ops import polygonize, unary_union
    except Exception:
        return None, ""
    lines = []
    for s in material_segments:
        pts = s.points(tol_mm=2.0) if hasattr(s, "points") else None
        if pts and len(pts) >= 2:
            lines.append(LineString(pts))
    if not lines:
        return None, ""
    merged = unary_union(lines)
    try:
        faces = list(polygonize(merged))
    except Exception:
        faces = []
    hull = merged.convex_hull
    if faces:
        big = max(faces, key=lambda f: f.area)
        if hull.area and big.area / hull.area >= PLOT_FACE_MIN_SHARE:
            return big, PLOT_BASIS_LARGEST_FACE
    return hull, PLOT_BASIS_HULL


def classify(groups, *, plot=None, region=None, a18_zone_tokens=(),
             material_segments=()) -> dict:
    """A class for every label group, from placement and typography."""
    from shapely.geometry import Point
    basis = ""
    if plot is None and material_segments:
        plot, basis = plot_face(material_segments, region=region)

    room_heights = [m.height for g in groups for m in g.members
                    if m.stamp_class == lg.ENGLISH_ROOM_STAMP and m.height]
    median_h = (sorted(room_heights)[len(room_heights) // 2]
                if room_heights else 0.0)
    if region is not None:
        x0, y0, x1, y1 = region.x0, region.y0, region.x1, region.y1
        margin = MARGIN_SHARE * min(x1 - x0, y1 - y0)
    else:
        x0 = y0 = x1 = y1 = margin = None

    rows = []
    for n, g in enumerate(groups, start=1):
        anchor = next((m for m in g.members
                       if m.stamp_class == lg.ENGLISH_ROOM_STAMP),
                      g.members[0])
        cx, cy = anchor.visible_centroid
        ev = []
        inside = None
        if plot is not None:
            inside = plot.contains(Point(cx, cy))
            ev.append(EV_INSIDE_THE_PLOT if inside else EV_OUTSIDE_THE_PLOT)
        if margin is not None and (cx < x0 + margin or cx > x1 - margin
                                   or cy < y0 + margin or cy > y1 - margin):
            ev.append(EV_NEAR_THE_SHEET_EDGE)
        if median_h and anchor.height > LARGER_THAN_ROOM_STAMPS * median_h:
            ev.append(EV_LARGER_THAN_ROOM_STAMPS)
        if abs(anchor.rotation) > 1e-6:
            deg = abs(math.degrees(anchor.rotation)) % 180.0
            if min(abs(deg - 0.0), abs(deg - 90.0), abs(deg - 180.0)) \
                    <= PLOT_EDGE_ALIGN_DEG and (
                        EV_NEAR_THE_SHEET_EDGE in ev
                        or EV_OUTSIDE_THE_PLOT in ev):
                ev.append(EV_RUNS_ALONG_A_PLOT_EDGE)

        text = anchor.text
        cls, why = UNRESOLVED_TEXT, ""
        if _LEVEL.match(text) or text.strip().startswith("%%"):
            cls = LEVEL_ANNOTATION
            ev.append(EV_READS_AS_A_LEVEL)
            why = "a level or datum, not a space"
        elif _NUMERIC.match(text):
            cls = DIMENSION_TEXT
            ev.append(EV_READS_AS_A_NUMBER)
            why = "a printed number"
        elif len(re.findall(r"[A-Za-z]", text)) <= SECTION_MARK_MAX_GLYPHS \
                and anchor.stamp_class != lg.ENGLISH_ROOM_STAMP:
            cls = SECTION_MARK
            ev.append(EV_SHORT_TOKEN_NEAR_A_CIRCLE)
            why = "one or two glyphs: a section or detail reference"
        elif EV_OUTSIDE_THE_PLOT in ev or (
                EV_NEAR_THE_SHEET_EDGE in ev
                and EV_LARGER_THAN_ROOM_STAMPS in ev):
            cls = SITE_CONTEXT_ANNOTATION
            why = ("it sits outside the drawing's own plot outline, or in "
                   "the outer margin set larger than the room stamps. It "
                   "names what is beyond the plot")
        elif g.english_token and g.english_token in {
                t.upper() for t in a18_zone_tokens}:
            cls = FUNCTIONAL_ZONE_LABEL
            ev.append(EV_A18_ZONE_ONLY)
            why = "the frozen reading ties this identity to a zone"
        elif anchor.stamp_class == lg.ENGLISH_ROOM_STAMP:
            cls = PHYSICAL_SPACE_LABEL
            why = "a readable room stamp inside the plot"
        elif anchor.stamp_class in (lg.ARABIC_ROOM_STAMP,
                                    lg.UNRESOLVED_SHX_TEXT):
            cls = UNRESOLVED_TEXT
            ev.append(EV_NO_READABLE_GLYPHS)
            why = ("no readable glyphs and no English stamp grouped with "
                   "it, so what it names is not established")
        else:
            cls = OTHER_ANNOTATION
            why = "writing about the drawing"

        rows.append(LabelRow(
            label_id=f"LBL-{n:03d}", text=text, label_class=cls,
            evidence=tuple(ev), at_mm=(cx, cy), height_mm=anchor.height,
            group_id=g.group_id,
            in_denominator=cls in IN_THE_COMPLETENESS_DENOMINATOR, why=why))

    counts = {c: sum(1 for r in rows if r.label_class == c)
              for c in LABEL_CLASSES}
    return {
        "rows": rows,
        "counts": counts,
        "physical_and_functional_candidates":
            sum(1 for r in rows if r.in_denominator),
        "site_context": counts[SITE_CONTEXT_ANNOTATION],
        "other_annotations": (counts[LEVEL_ANNOTATION]
                              + counts[SECTION_MARK]
                              + counts[DIMENSION_TEXT]
                              + counts[OTHER_ANNOTATION]),
        "unresolved": counts[UNRESOLVED_TEXT],
        "median_room_stamp_height_mm": round(median_h, 2),
        "plot_outline_basis": basis or "SUPPLIED_BY_THE_CALLER",
        "site_context_is_not_a_space": SITE_CONTEXT_IS_NOT_A_SPACE,
        "no_word_list_decides_this": NO_WORD_LIST_DECIDES_THIS,
    }


def frozen_parameters() -> dict:
    return {
        "MODEL": MODEL,
        "LABEL_CLASSES": list(LABEL_CLASSES),
        "IN_THE_COMPLETENESS_DENOMINATOR":
            list(IN_THE_COMPLETENESS_DENOMINATOR),
        "EVIDENCE": list(EVIDENCE),
        "MARGIN_SHARE": MARGIN_SHARE,
        "LARGER_THAN_ROOM_STAMPS": LARGER_THAN_ROOM_STAMPS,
        "PLOT_EDGE_ALIGN_DEG": PLOT_EDGE_ALIGN_DEG,
        "SECTION_MARK_MAX_GLYPHS": SECTION_MARK_MAX_GLYPHS,
        "PLOT_FACE_MIN_SHARE": PLOT_FACE_MIN_SHARE,
        "why": {"site_context_is_not_a_space": SITE_CONTEXT_IS_NOT_A_SPACE,
                "no_word_list_decides_this": NO_WORD_LIST_DECIDES_THIS},
    }
