"""URBAN_WINDOW_SIZE_GUIDE_V1 - the owner's approved fallback window sizes, and the priority that governs them.

The guide is a FALLBACK.  It never overrides a dimension the project states or a dimension the project geometry
yields; it supplies a height, by room use, only where the project is silent.  Its widths rank below anything
measurable, and a width taken from it is marked as an estimate rather than presented as measured geometry.
"""

from __future__ import annotations

RULE_ID = "US-19"
VERSION = "URBAN_WINDOW_SIZE_GUIDE_V1"
KIND = "URBAN_STANDARD"
TRAVELS = True

PROVENANCE = {
    "APPROVED_BY": "project owner, in writing, as an Urban standard for future projects",
    "SOURCE_DOCUMENT": "Urban_Projects_Kuwait_Window_Size_Guide(1).pdf",
    "DOCUMENT_RECEIVED": False,
    "WHAT_WAS_INGESTED": "the guide's size table as transcribed in full in the owner's instruction; the PDF "
                         "itself did not arrive in this session",
    "WHY_IT_STILL_STANDS": "the table is the substance and the owner set it out completely.  If the PDF is sent "
                           "later it should be checked against this table rather than replacing it silently",
}

# The order is absolute.  A lower rank is never consulted while a higher one can answer.
PRIORITY = [
    (1, "SOURCE_STATED_DIMENSION", "a dimension written on the project drawing"),
    (2, "MEASURED_FROM_PROJECT_GEOMETRY", "measured from the project PDF or DWG"),
    (3, "EXPLICIT_PROJECT_OWNER_OVERRIDE", "a value the owner gave for this project"),
    (4, "URBAN_WINDOW_SIZE_GUIDE_V1", "this guide, by room use"),
    (5, "ASK_THE_OWNER", "nothing above answers"),
]

# WIDTH x HEIGHT as the guide states them.  Only the HEIGHT is normally taken: the width comes from the project.
TABLE = {
    "SMALL_BEDROOM":        {"W": 1.50, "H": 1.50, "AREA_BAND_M2": (10, 14)},
    "MASTER_LARGE_BEDROOM": {"W": 1.80, "H": 1.50, "AREA_BAND_M2": (16, 25)},
    "BEDROOM_BALCONY_DOOR": {"W": 1.80, "H": 2.20, "AREA_BAND_M2": None},
    "LIVING_ROOM":          {"W": 2.40, "H": 1.80, "AREA_BAND_M2": (20, 35)},
    "LARGE_HALL":           {"W": 1.80, "H": 2.20, "AREA_BAND_M2": (35, 60),
                             "NOTE": "the guide suggests two units; the plan decides count and width"},
    "DEWANIYA":             {"W": 2.40, "H": 1.80, "AREA_BAND_M2": None},
    "DINING_ROOM":          {"W": 1.80, "H": 1.50, "AREA_BAND_M2": None},
    "KITCHEN":              {"W": 1.20, "H": 1.20, "AREA_BAND_M2": None},
    "BATHROOM":             {"W": 0.90, "H": 0.60, "AREA_BAND_M2": None},
    "GUEST_WASH":           {"W": 0.90, "H": 0.90, "AREA_BAND_M2": None},
    "MAID_DRIVER_ROOM":     {"W": 1.50, "H": 1.20, "AREA_BAND_M2": None},
    "DRESSING_ROOM":        {"W": 0.90, "H": 0.90, "AREA_BAND_M2": None},
    "LAUNDRY_STORE":        {"W": 0.90, "H": 0.90, "AREA_BAND_M2": None},
    "STAIR_WINDOW":         {"W": 1.20, "H": 1.50, "AREA_BAND_M2": None},
}

LABEL_MAP = {
    "M.BED ROOM": "MASTER_LARGE_BEDROOM",
    "KITCHEN": "KITCHEN",
    "BATH": "BATHROOM",
    "WASH": "GUEST_WASH",
    "DRIVER": "MAID_DRIVER_ROOM",
    "MAID": "MAID_DRIVER_ROOM",
    "STORE": "LAUNDRY_STORE",
    "LAUNDRY": "LAUNDRY_STORE",
    "DRESS": "DRESSING_ROOM",
    "DEWANIYA": "DEWANIYA",
    "DINNING": "DINING_ROOM",
    "W.C": "BATHROOM",
    "TOILET": "BATHROOM",
}

# The guide's own design advice on orientation, window-to-wall ratio and daylight is DESIGN GUIDANCE.  It does not
# touch a takeoff: a window that was built 2.00 m wide is 2.00 m wide whichever way it faces.
NOT_APPLIED_TO_TAKEOFF = {
    "SOLAR_ORIENTATION_RESIZING": "DESIGN_REVIEW_ONLY",
    "WINDOW_TO_WALL_RATIO_TARGETS": "DESIGN_REVIEW_ONLY",
    "DAYLIGHT_AND_VENTILATION_TARGETS": "DESIGN_REVIEW_ONLY",
    "WHY": "an existing building is measured as built.  Resizing a measured opening to satisfy a design target "
           "would put a recommendation into a quantity",
}

SUPERSEDES = {
    "SUPERSEDED": "the illustrative 2.00 m window height given earlier in this project",
    "BY": VERSION,
    "SCOPE": "windows with no source height",
    "WHY": "the 2.00 m was offered as an example before the guide existed, and applying one height to every "
           "window ignores what the room is",
    "EFFECT_ON_THIS_PROJECT": "no window keeps 2.00 m; each takes the height its room's category gives",
}


def category_for(label, area_m2):
    """The guide category for a room, or None where the use is not clear enough to pick one."""
    if label in LABEL_MAP:
        return LABEL_MAP[label], "EXPLICIT_LABEL_MAP"
    if label == "BED ROOM":
        if area_m2 is None:
            return None, "AREA_UNKNOWN"
        if area_m2 <= 14:
            return "SMALL_BEDROOM", "BEDROOM_SELECTED_BY_AREA"
        return "MASTER_LARGE_BEDROOM", "BEDROOM_SELECTED_BY_AREA"
    if label == "HALL":
        if area_m2 is None:
            return None, "AREA_UNKNOWN"
        if area_m2 <= 35:
            return "LIVING_ROOM", "HALL_SELECTED_BY_AREA"
        return "LARGE_HALL", "HALL_SELECTED_BY_AREA"
    return None, "NO_CLEAR_CATEGORY"


def height_for(label, area_m2):
    cat, how = category_for(label, area_m2)
    if not cat:
        return None, cat, how
    return TABLE[cat]["H"], cat, how
