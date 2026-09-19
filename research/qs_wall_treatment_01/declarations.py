"""Controller declarations for the P7757 overlap audit and owner resolution.

These are the only semantic inputs the audit takes beyond the frozen
register, and they are recorded verbatim in the output so a reviewer can
see every place a human (the controller) said "these traces are one
object" or "this trace is a capping band, not a wall face". Each entry
cites the trace evidence it rests on. Nothing here edits a trace.
"""

from __future__ import annotations

# Physical objects - membership by trace id, per case
OBJECT_MAP = {
    "CASE-6-ROOF-PARAPET": {
        # the +9.70 terrace SE-edge parapet assembly, by physical part
        "PO-SE-PARAPET-PLAN-BODY": ["PAR-01", "SEG-01", "SEG-02"],
        "PO-SE-PARAPET-KERB": ["PAR-11", "PAR-04"],
        "PO-SE-PARAPET-SOLID-WALL": ["PAR-12", "SEG-05"],
        "PO-SE-BALUSTRADE": ["BAL-03", "BAL-02"],
        "PO-SE-CAPPING": ["PAR-13", "PAR-05"],
        "PO-SE-END-PIER": ["SEG-04"],
        "PO-SW-PARAPET": ["PAR-02"],
        "PO-NE-PARAPET": ["PAR-03", "PAR-07"],
        "PO-TOWER-PARAPET-1390": ["PAR-10", "PAR-06", "PAR-08", "PAR-09"],
        "PO-NW-ROOF-EDGE-ELEMENT": ["UNK-04", "UNK-06", "SEG-03"],
    },
    "CASE-3-DOOR-AND-WINDOW": {
        "PO-SALOON-SEA-VIEW-LINE": ["SEG-01", "UNK-07"],
        "PO-SALOON-SEA-VIEW-GLAZING": ["GLZ-01", "GLZ-01S", "GLZ-01N"],
        "PO-SALOON-CORNER-PIER-TOP": ["COL-01", "COL-01N"],
        "PO-SALOON-CORNER-PIER-BOTTOM": ["COL-02", "COL-02N"],
        "PO-POOL-CURVED-WALL": ["GLZ-02", "GLZ-02S", "GLZ-02N"],
    },
    "CASE-4-STAIR": {
        "PO-MAIN-CURVED-STAIR": ["STR-01", "STR-02", "STR-03"],
        "PO-SERVICE-STAIR": ["STR-04", "STR-05", "STR-06"],
    },
    "CASE-1-NORMAL-PLASTER": {
        "PO-MAIN-CURVED-STAIR": ["STR-01", "STR-02"],
        "PO-RECEPTION-VOID": ["UNK-01", "UNK-02"],
    },
}

# Material-role overrides, with the trace evidence each rests on
ROLE_OVERRIDES = {
    "CASE-6-ROOF-PARAPET": {
        "PAR-13": {"MATERIAL_ROLE": "CAPPING_BAND",
                   "REASON": "traced as the top rail / capping band over the "
                             "lattice and the solid wall (SE elevation), "
                             "20 band per DIM-20; not a wall face"},
        "PAR-05": {"MATERIAL_ROLE": "CAPPING_BAND",
                   "REASON": "traced as the cap element spanning the full "
                             "wall width on top of the B-B cut"},
        "SEG-04": {"MATERIAL_ROLE": "PIER_FACE",
                   "REASON": "traced as the end pier/post at the rounded "
                             "corner of the SE parapet"},
        "SEG-05": {"MATERIAL_ROLE": "PARAPET_SOLID_FACE",
                   "REASON": "traced as the right-end vertical edge of the "
                             "SE parapet itself"},
        "SEG-01": {"MATERIAL_ROLE": "PARAPET_SOLID_FACE",
                   "REASON": "traced as the external (SE) face LINE of the "
                             "parapet PAR-01 in plan: a parapet face, not a "
                             "room wall"},
        "SEG-02": {"MATERIAL_ROLE": "PARAPET_SOLID_FACE",
                   "REASON": "traced as the roof-side face LINE of PAR-01 in "
                             "plan"},
    },
    "CASE-3-DOOR-AND-WINDOW": {
        "SEG-06": {"MATERIAL_ROLE": "UNRESOLVED",
                   "REASON": "traced as a low wall / planter edge; whether it "
                             "is a plasterable wall face is not established"},
    },
}

# §4 - an open balustrade and the solid base under it, where traced
SOLID_BASE_OF = {
    "CASE-6-ROOF-PARAPET": {"BAL-03": "PAR-11", "BAL-02": "PAR-04"},
}

# pairs the controller declares as two objects at different depths
# projecting onto one drawing area (elevations / sections only)
SAME_PROJECTION_PAIRS = {
    "CASE-6-ROOF-PARAPET": [],
}


# ==================================================================
# FACE SET PLAN - which traced faces form which measurement set, for
# which zone, floor and trade. A measurement decision, declared and
# recorded, never tuned. Faces not listed here are not estimated.
# ==================================================================
FACE_SET_PLAN = [
    {"SET_ID": "GF-SALOON-NORMAL-PLASTER", "CASE": "CASE-3-DOOR-AND-WINDOW",
     "SHEET": "GROUND_FLOOR_PLAN", "FLOOR": "GROUND", "ZONE": "SALOON",
     "TRADE": "NORMAL_INTERNAL_PLASTER", "BASIS": "WALL_FACE_SET", "SIDE": "INTERNAL",
     "FACES": ["SEG-01", "SEG-02", "SEG-03", "SEG-04", "SEG-05", "SEG-06", "GLZ-02", "OE-01"],
     "OPENINGS": ["GLZ-01", "D-01", "UNK-01"],
     "DOUBLE_HEIGHT_STATUS": "NOT_INDICATED_ON_TRACED_SHEETS",
     "OPEN_PLAN_NOTE": "the west boundary OE-01 toward RECEPTION is an open edge: "
                       "no material, no plaster, and it is not bridged"},
    {"SET_ID": "GF-SALOON-COLUMN-BONDING", "CASE": "CASE-3-DOOR-AND-WINDOW",
     "SHEET": "GROUND_FLOOR_PLAN", "FLOOR": "GROUND", "ZONE": "SALOON",
     "TRADE": "COLUMN_BONDING_PLUS_PLASTER", "BASIS": "WALL_FACE_SET", "SIDE": "INTERNAL",
     "FACES": ["COL-01", "COL-02", "COL-03", "COL-04"], "OPENINGS": []},
    {"SET_ID": "GF-RECEPTION-DOUBLE-HEIGHT", "CASE": "CASE-1-NORMAL-PLASTER",
     "SHEET": "GROUND_FLOOR_PLAN", "FLOOR": "GROUND", "ZONE": "RECEPTION",
     "TRADE": "DOUBLE_HEIGHT_PLASTER", "BASIS": "WALL_FACE_SET", "SIDE": "INTERNAL",
     "FACES": ["SEG-01", "SEG-02", "SEG-03", "SEG-04", "SEG-05", "SEG-06",
               "OPEN-01", "OPEN-02", "W-01"],
     "OPENINGS": ["D-01"],
     "DOUBLE_HEIGHT_STATUS": "ESTABLISHED (VOID above, UNK-01/UNK-02): the normal "
                             "3.20 height is NOT applied (§8)"},
    {"SET_ID": "GF-RECEPTION-COLUMN-BONDING", "CASE": "CASE-1-NORMAL-PLASTER",
     "SHEET": "GROUND_FLOOR_PLAN", "FLOOR": "GROUND", "ZONE": "RECEPTION",
     "TRADE": "COLUMN_BONDING_PLUS_PLASTER", "BASIS": "WALL_FACE_SET", "SIDE": "INTERNAL",
     "FACES": ["COL-01", "COL-02", "COL-03", "COL-04", "COL-05"], "OPENINGS": [],
     "HEIGHT_NOTE": "columns in the double-height zone: NORMAL height not applied",
     "HEIGHT_PARAMETER": "DOUBLE_HEIGHT_PLASTER_HEIGHT"},
    {"SET_ID": "GF-SERVICE-STAIR-WALLS", "CASE": "CASE-4-STAIR",
     "SHEET": "GROUND_FLOOR_PLAN", "FLOOR": "GROUND", "ZONE": "SERVICE_STAIR_CORE",
     "TRADE": "STAIR_WALL_PLASTER", "BASIS": "LINEAR_SURFACE_RUN", "SIDE": "INTERNAL",
     "FACES": ["SEG-05", "SEG-06", "SEG-07"], "OPENINGS": []},
    {"SET_ID": "GF-MAIN-STAIR-WALLS", "CASE": "CASE-4-STAIR",
     "SHEET": "GROUND_FLOOR_PLAN", "FLOOR": "GROUND", "ZONE": "MAIN_STAIR",
     "TRADE": "STAIR_WALL_PLASTER", "BASIS": "LINEAR_SURFACE_RUN", "SIDE": "INTERNAL",
     "FACES": ["SEG-01", "SEG-02", "SEG-03"], "OPENINGS": []},
    {"SET_ID": "FF-MAIN-STAIR-WALL", "CASE": "CASE-4-STAIR",
     "SHEET": "FIRST_FLOOR_PLAN", "FLOOR": "FIRST", "ZONE": "MAIN_STAIR",
     "TRADE": "STAIR_WALL_PLASTER", "BASIS": "LINEAR_SURFACE_RUN", "SIDE": "INTERNAL",
     "FACES": ["SEG-04"], "OPENINGS": []},
    {"SET_ID": "GF-NW-FACADE-EXTERNAL", "CASE": "CASE-3-DOOR-AND-WINDOW",
     "SHEET": "GROUND_FLOOR_PLAN", "FLOOR": "GROUND", "ZONE": "NW_SEA_VIEW_FACADE",
     "TRADE": "EXTERNAL_PLASTER", "BASIS": "LINEAR_SURFACE_RUN", "SIDE": "EXTERNAL",
     "FACES": ["GLZ-01", "COL-01", "COL-02"], "OPENINGS": [],
     "UNRESOLVED_FACES": {
         "COL-01": "external plastered exposure not established: the pier is seen "
                   "hatched (cut) on the NW elevation sheet, its outer face is not seen",
         "COL-02": "external plastered exposure not established: same as COL-01"},
     "EXTERNAL_EXPOSURE_NOTE": "the piers are seen hatched (cut) on the NW elevation "
                               "sheet; their external plastered exposure is not "
                               "established, so they are UNRESOLVED here"},
    {"SET_ID": "ROOF-SE-PARAPET-EXTERNAL", "CASE": "CASE-6-ROOF-PARAPET",
     "SHEET": "SOUTH_EAST_ELEVATION", "FLOOR": "ROOF_+9.70", "ZONE": "SE_TERRACE_PARAPET",
     "TRADE": "ROOF_PARAPET_EXTERNAL_FACE", "BASIS": "LINEAR_SURFACE_RUN", "SIDE": "EXTERNAL",
     "FACES": ["PAR-11", "PAR-12", "SEG-04", "BAL-03", "PAR-13"], "OPENINGS": []},
    {"SET_ID": "ROOF-SE-PARAPET-CAPPING", "CASE": "CASE-6-ROOF-PARAPET",
     "SHEET": "SOUTH_EAST_ELEVATION", "FLOOR": "ROOF_+9.70", "ZONE": "SE_TERRACE_PARAPET",
     "TRADE": "ROOF_PARAPET_CAPPING", "BASIS": "LINEAR_SURFACE_RUN", "SIDE": "TOP",
     "FACES": ["PAR-13"], "OPENINGS": []},
    {"SET_ID": "ROOF-SE-PARAPET-INTERNAL", "CASE": "CASE-6-ROOF-PARAPET",
     "SHEET": "SECOND_FLOOR_ROOF_PLAN", "FLOOR": "ROOF_+9.70", "ZONE": "SE_TERRACE_PARAPET",
     "TRADE": "ROOF_PARAPET_INTERNAL_FACE", "BASIS": "LINEAR_SURFACE_RUN", "SIDE": "ROOF_SIDE",
     "FACES": ["SEG-02"], "OPENINGS": [],
     "NOTE": "roof-side face height is not traced on any sheet"},
    {"SET_ID": "ROOF-TOWER-PARAPET-1390-EXTERNAL", "CASE": "CASE-6-ROOF-PARAPET",
     "SHEET": "SOUTH_EAST_ELEVATION", "FLOOR": "ROOF_+13.90", "ZONE": "TOWER_PARAPET",
     "TRADE": "ROOF_PARAPET_EXTERNAL_FACE", "BASIS": "LINEAR_SURFACE_RUN", "SIDE": "EXTERNAL",
     "FACES": ["PAR-10"], "OPENINGS": []},
]

# Lengths that are not a single printed dimension but a declared chain of
# printed dimensions; PROVISIONAL by rule (length_basis = DERIVED_CHAIN)
DERIVED_LENGTHS = {
    ("CASE-6-ROOF-PARAPET", "PAR-13"): {
        "length_m": 7.10, "length_basis": "DERIVED_CHAIN",
        "FORMULA": "DIM-02 1.29 + 2 x DIM-04 R2.21 + DIM-03 1.39 (roof-side length "
                   "of the SE run in plan, PAR-01 chain)",
        "supporting_dimensions": ["DIM-02", "DIM-04", "DIM-03"],
        "WHY_PROVISIONAL": "the chain closes through a dome radius doubled, a "
                           "reader composition rather than one printed length"},
}

# Traced heights / widths bound to faces, with the dimension trace and
# what the owner resolution said about it
FACE_DIMENSIONS = {
    ("CASE-3-DOOR-AND-WINDOW", "SEG-02"): {
        "supporting_dimensions": ["DIM-05"],
        "NOTE": "printed 515 runs from the open-edge tick (x~1520) to the sea-view "
                "wall LINE; the internal face length may differ by the corner pier "
                "COL-02's extent along the wall. Kept as printed, flagged"},
    ("CASE-3-DOOR-AND-WINDOW", "SEG-03"): {
        "supporting_dimensions": ["DIM-07", "DIM-09"],
        "NOTE": "printed 200 with ticks at x~1682 and x~1796: full run of the return "
                "wall including the black block COL-03; the plastered face length "
                "between COL-03 and the sea-view line may be shorter. Kept as printed, flagged"},
    ("CASE-6-ROOF-PARAPET", "PAR-10"): {
        "height_m": 0.50, "height_source": "DRAWING_PRINTED_DIMENSION",
        "supporting_dimensions": ["DIM-14"],
        "NOTE": "DIM-14 lower end is the dashed +13.90 datum line"},
    ("CASE-6-ROOF-PARAPET", "PAR-13"): {
        "width_m": 0.20, "width_source": "DRAWING_PRINTED_DIMENSION",
        "supporting_dimensions": ["DIM-20", "DIM-01"],
        "NOTE": "band thickness 20 (DIM-20) and parapet wall thickness 20 (DIM-01)"},
    ("CASE-6-ROOF-PARAPET", "PAR-12"): {
        "height_m": None, "height_source": None,
        "supporting_dimensions": ["DIM-21", "DIM-20", "DIM-15"],
        "NOTE": "face height AMBIGUOUS: 1.22 m to the band or 1.42 m with it; "
                "NOT_ESTABLISHED until resolved"},
}


# ==================================================================
# CAD-derived lengths (§15): used only with a CAD_TRACE_LINK_STATUS read
# from CAD_TRACE_LINKS.json at build time; ESTABLISHED -> established
# face, PROVISIONAL -> provisional face, otherwise unresolved. The A21
# printed values these replace are recorded as DIMENSION_OWNERSHIP_DIFFERENCE.
# ==================================================================
CAD_LENGTHS = {
    ("CASE-3-DOOR-AND-WINDOW", "COL-02"): {
        "length_m": 0.700, "length_basis": "CAD_GEOMETRY", "LINK_ID": "L4X",
        "WHAT": "exposed pier face inside the SALOON: neighbour-wall inner face to glazing start",
        "REPLACES": "printed DIM-03 '90' = pier BODY incl. 0.20 wall thickness",
        "DIFFERENCE_CLASS": "DIMENSION_OWNERSHIP_DIFFERENCE"},
    ("CASE-3-DOOR-AND-WINDOW", "COL-01"): {
        "length_m": 0.468, "length_basis": "CAD_GEOMETRY", "LINK_ID": "L5X",
        "WHAT": "exposed pier face inside the SALOON: glazing end to return-wall inner face",
        "REPLACES": "printed DIM-02 '90' whose ownership is NOT_ESTABLISHED (authored body 0.668)",
        "DIFFERENCE_CLASS": "DIMENSION_OWNERSHIP_DIFFERENCE"},
}

# Wall thicknesses established from printed dimensions - the owner's reveal
# rule is ACTUAL WALL THICKNESS FIRST (§6); a default applies only where the
# host wall's thickness is not established
WALL_THICKNESS_M = {
    ("CASE-3-DOOR-AND-WINDOW", "SEG-02"): {"value": 0.20, "source": "DIM-06 '20'"},
    ("CASE-3-DOOR-AND-WINDOW", "SEG-03"): {"value": 0.20, "source": "DIM-09 '20'"},
    ("CASE-1-NORMAL-PLASTER", "SEG-01"): {"value": 0.15, "source": "DIM-10 '15'"},
    ("CASE-1-NORMAL-PLASTER", "SEG-02"): {"value": 0.15, "source": "DIM-10 '15'"},
    ("CASE-4-STAIR", "SEG-04"): {"value": 0.15, "source": "DIM-20 '15'"},
}
REVEAL_DEPTH_RULE = ("ENGINEERING: an opening's reveal depth is its host wall's established "
                     "thickness; the TEMPORARY_DEFAULT applies only when that thickness is "
                     "not established. CONTRACTOR: 0.20 as the site record used")
