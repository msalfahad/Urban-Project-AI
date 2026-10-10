"""The owner's answers to AR-01 to AR-08, stored with what each one is and how far it travels.

A number the owner gives for THIS villa is not an Urban standard.  A rule the owner promotes to every project is.
The two are kept apart here so that the next project inherits the rule and not the number.
"""

from __future__ import annotations

PROJECT_ID = "ALRASHED_SABAH_AL_AHMAD"

# ---------------------------------------------------------------- project values: they do not travel
AR01_WALL_HEIGHT_M = 3.600
AR02_DOOR_HEIGHT_M = 2.200
AR02_DEFAULT_DOOR_WIDTH_M = 1.000
AR03_WINDOW_HEIGHT_M = 2.000
AR06_PARAPET_HEIGHT_M = 1.000

PROJECT_INPUTS = {
    "AL_RASHED_WALL_HEIGHT": {
        "VALUE_M": AR01_WALL_HEIGHT_M, "FROM": "AR-01", "KIND": "OWNER_CONFIRMED_PROJECT_INPUT",
        "APPLIES_TO": ["BLOCKWORK", "INTERNAL_PLASTER", "INTERNAL_PAINT", "EXTERNAL_PLASTER", "EXTERNAL_PAINT",
                       "FULL_HEIGHT_WALL_PORCELAIN"],
        "PRECEDENCE": "a dimension on the drawing overrides it; it is used only where no source gives an "
                      "applicable height",
        "TRAVELS": False, "WHY_NOT": "this is the height of one villa, not an Urban rule"},
    "AL_RASHED_DOOR_HEIGHT": {
        "VALUE_M": AR02_DOOR_HEIGHT_M, "FROM": "AR-02", "KIND": "OWNER_CONFIRMED_PROJECT_INPUT",
        "PRECEDENCE": "used only where the drawing shows no height", "TRAVELS": False},
    "AL_RASHED_PROJECT_WINDOW_HEIGHT": {
        "VALUE_M": AR03_WINDOW_HEIGHT_M, "FROM": "AR-03", "KIND": "OWNER_CONFIRMED_PROJECT_INPUT",
        "PRECEDENCE": "used only where the drawing shows no height", "TRAVELS": False,
        "WHY_NOT": "the owner said in terms that this is this villa's basis, not a permanent default"},
    "AL_RASHED_PARAPET_HEIGHT": {
        "VALUE_M": AR06_PARAPET_HEIGHT_M, "FROM": "AR-06", "KIND": "OWNER_CONFIRMED_PROJECT_INPUT",
        "TRAVELS": False},
}

# ---------------------------------------------------------------- the width rule: the drawing wins
WIDTH_RULE = {
    "FROM": "AR-02 and AR-03",
    "RULE": "a width that the drawing establishes is used as drawn.  A default width is used ONLY where the source "
            "gives no usable width at all",
    "DEFAULT_DOOR_WIDTH_M": AR02_DEFAULT_DOOR_WIDTH_M,
    "DEFAULT_WINDOW_WIDTH_M": None,
    "IF_BOTH_WIDTH_AND_HEIGHT_ABSENT": "ASK_THE_OWNER - neither is invented",
    "WHY": "a drawn width is a measurement; a default width is an assumption, and replacing the first with the "
           "second throws away the only real information the opening has",
}

# ---------------------------------------------------------------- the wet-room rule: this one travels
US_WET_ROOM_FINISH = {
    "RULE_ID": "US-18", "FROM": "AR-05", "KIND": "URBAN_STANDARD", "TRAVELS": True,
    "STATEMENT": "a wet or service room takes porcelain or ceramic to the floor AND to the full applicable wall "
                 "height, automatically, unless the drawing or specification explicitly says otherwise",
    "ROOM_TYPES": ["BATHROOM", "BATH", "WC", "W.C", "SHOWER", "KITCHEN", "PANTRY", "PREPARATION KITCHEN",
                   "WASHING ROOM", "WASH", "LAUNDRY", "IRONING ROOM", "TOILET"],
    "EQUIVALENTS": "a clearly labelled service room of the same kind maps to the same rule",
    "WALL_TILE_HEIGHT": "the applicable full wall height for the project, unless the source gives a tile height",
    "ON_A_FULLY_TILED_FACE": {"NORMAL_SKIRTING": 0, "HIDDEN_SKIRTING": 0, "NORMAL_WALL_PAINT": 0,
                              "WHY": "a tiled face carries no skirting and takes no paint; counting either would "
                                     "price work that the tiling replaces"},
    "BEHIND_THE_TILE": "tile preparation (tartousha) where that trade is required",
    "DO_NOT_ASK_AGAIN": "which rooms have wall porcelain - unless the room is genuinely ambiguous or the source "
                        "contradicts the standard",
}

# ---------------------------------------------------------------- scope
AR07_SCOPE = {
    "FROM": "AR-07",
    "IN_SCOPE": "ARCHITECTURAL / FINISHING QS",
    "OUT_OF_SCOPE": ["STRUCTURAL", "REINFORCEMENT", "SANITARY", "ELECTRICAL", "HVAC"],
    "STATUS_FOR_THOSE_TRADES": "OUT_OF_SCOPE_FOR_CURRENT_VALIDATION",
    "NOT": "MISSING_SOURCE or FAILED - the owner has scoped them out, which is not the same as not having them",
    "DO_NOT_REQUEST": True,
}

AR08_EXTERNAL_AREAS = {
    "FROM": "AR-08",
    "INCLUDE": ["car parking", "open yard", "external basement areas"],
    "MEASURED": "BY AREA, separately from internal building rooms",
    "FINISH": "not invented where the drawing does not establish one",
    "STATUS_WHEN_FINISH_UNKNOWN": "FINISH_CLASSIFICATION_PENDING",
    "AREA_MAY_STILL_BE": "FINAL - a measured area does not become provisional because its material is unsettled",
}

AR06_ROOF = {
    "FROM": "AR-06",
    "PARAPET_HEIGHT_M": AR06_PARAPET_HEIGHT_M,
    "PARAPET_TRADES": ["blockwork", "plaster", "paint"],
    "ROOF_FINISH_MATERIAL": None,
    "ROOF_FINISH_STATUS": "FINISH_CLASSIFICATION_PENDING",
    "RULE": "roof AREA is measured now; the finish material is a separate classification and does not block it",
}

ANSWERED = ["AR-01", "AR-02", "AR-03", "AR-05", "AR-06", "AR-07", "AR-08"]
STILL_OPEN = ["AR-04 - held back deliberately: the area schedule is reconciled independently first"]
