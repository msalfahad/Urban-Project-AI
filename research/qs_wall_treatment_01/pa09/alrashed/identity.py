"""Project identity and floor inventory for the Al Rashed villa, read from the supplied drawings only.

Everything here comes off the two files the owner attributed.  The title block is in a legacy Arabic CAD font whose
bytes are not Unicode, so the Arabic field LABELS are transliterated rather than decoded - but the values that
matter for a takeoff (plot, block, area, levels, sheet names) are Latin on the sheet and are read as drawn.
"""

from __future__ import annotations

import collections
import hashlib
import json
import re
import subprocess
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR
from research.qs_wall_treatment_01.pa09.alrashed import geometry as G

OUT = Path(PR.OUT_DIR) / "pa09_alrashed"
PDF = "/root/.claude/uploads/93607c01-16a4-590f-af7c-1c2701c3b240/507baa5b-16-11-2025.pdf"

# Read from the sheet.  The Arabic labels transliterate as: wfhP HBpl] Hgs:kdM = Sabah Al Ahmad residential;
# Hpl] uf]HggI ugD HgvHa] = Ahmad Abdullah Ali Al Rashed; r'uM = block; rsdlM = plot; lshpM = area; s:K oHW =
# private residence; lo'' jv:d> HgfkHu = building permit drawing.
IDENTITY = {
    "PROJECT_ID": "ALRASHED_SABAH_AL_AHMAD",
    "OWNER_ON_DRAWING": "Ahmad Abdullah Ali Al Rashed",
    "LOCATION": "Sabah Al Ahmad Residential City, Kuwait",
    "BLOCK": "D4",
    "PLOT": "247",
    "PLOT_AREA_M2": 600.00,
    "PLOT_DIMENSIONS": "22.00 m street frontage x 27.28 m depth",
    "USE": "private residence (villa)",
    "PERMIT_APPLICATION": "BLD 0245232024",
    "CONSULTANT": "EWAN - Sanam Tower 1, Floor 12, Fahad Al Salem Street, Kuwait City, Qibla Block 11",
    "DRAWN_BY": "BILAL HAIDER", "CHECKED_BY": "HOMAM SHAMI", "SHEET_YEAR": "2024",
    "DRAWING_SCALE": "1:100",
    "NEIGHBOURS": "plots 245, 247, 248, 249 on the location plan",
    "ARITHMETIC_CHECK": "22.00 x 27.28 = 600.16 m2, against the 600.00 m2 the schedule states",
}

# The three storeys the supplied set draws, with the level each plan carries.
FLOORS = [
    {"FLOOR": "BASEMENT", "PDF_PAGE": 1, "LEVEL_M": 65.04, "SHEET_TITLE": "BASEMENT FLOOR PLAN",
     "ROOMS_LABELLED": ["DEWANIYA", "HALL", "MUGALLAT", "CAR PARKING", "DRIVER", "STORE",
                        "PANTRY", "PANTRY", "BATH", "BATH"],
     "HAS_STAIR": True, "HAS_LIFT": True},
    {"FLOOR": "GROUND", "PDF_PAGE": 2, "LEVEL_M": 69.04, "SHEET_TITLE": "GROUND FLOOR PLAN",
     "OTHER_LEVELS_ON_SHEET": [67.79, 67.84, 67.90],
     "ROOMS_LABELLED": ["HALL", "HALL", "M.BED ROOM", "M.BED ROOM", "BED ROOM", "BED ROOM", "BED ROOM",
                        "KITCHEN", "DRESS", "WASH", "WASH", "BATH", "BATH", "BATH", "BATH", "BATH", "BATH",
                        "BALCONY", "BALCONY", "ROOF"],
     "HAS_STAIR": True, "HAS_LIFT": True},
    {"FLOOR": "FIRST", "PDF_PAGE": 3, "LEVEL_M": 73.04, "SHEET_TITLE": "FIRST FLOOR PLAN",
     "ROOMS_LABELLED": ["STORE", "MECH.ROOM", "HEATERS", "ROOF"],
     "HAS_STAIR": True, "HAS_LIFT": False,
     "NOTE": "mostly open roof at 73.04 with a small penthouse block; there is no separate roof plan sheet"},
]

# What the sheet's own area schedule states, as drawn.  Which figure belongs to which floor is NOT stated in words
# beside it, so it is recorded as read and carried into the owner questions rather than assigned.
AREA_SCHEDULE_AS_DRAWN = {
    "FIGURES_M2": [69.66, 382.16, 451.82, 494.62, 600.00],
    "PERCENTAGES_OF_PLOT": {"69.66": "11.61%", "382.16": "63.69%", "494.62": "82.43%", "600.00": "100.00%"},
    "ARITHMETIC_ON_THE_SHEET": "451.82 = 382.16 + 69.66",
    "NOT_ESTABLISHED": "the schedule does not say in words which storey each figure measures, and 494.62 is not "
                       "451.82, so at least one figure covers something the other two do not",
    "USE": "an independent check on the recovered floor areas once the assignment is settled; not an input",
}

REVISION_SETS_IN_THE_DWG = {
    "PLAN_WINDOWS_FOUND": 9,
    "LAYOUT": "three storeys across, three revision rows down",
    "CURRENT_ROW": "R3 (y 146-182)",
    "HOW_THE_CURRENT_ROW_WAS_IDENTIFIED":
        "every dimension each PDF page prints is present in the matching R3 window with the same multiplicity "
        "(containment score 1.000); no other row scores 1.000 for any page",
    "SUPERSEDED_ROWS_CARRY": ["OLD AREA", "NEW AREA", "CANCELED", "MODIFY", "EXISTING AREA"],
    "WINDOWS": G.WINDOWS,
}

DISCIPLINES = {
    "PRESENT": ["ARCHITECTURAL floor plans (basement, ground, first)"],
    "ABSENT": ["sections", "elevations", "structural", "MEP (sanitary, electrical, mechanical)",
               "door and window schedule", "finishes schedule or written specification"],
    "WHAT_THE_ABSENCE_COSTS": {
        "sections / elevations": "no floor-to-floor or clear wall height, so no wall AREA quantity - blockwork, "
                                 "plaster, paint and wall tiling are all length x height",
        "door and window schedule": "no door or window heights, so no opening deduction and no aluminium or PVC area",
        "finishes schedule": "no way to tell which floor takes porcelain and which takes ceramic from the drawing",
        "structural": "no concrete or reinforcement quantity",
        "MEP": "no sanitary or electrical quantity",
    },
    "RULE": "a quantity is not invented for a discipline that was not supplied",
}


def _git(*a):
    try:
        return subprocess.run(["git", *a], capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception:
        return ""


def build():
    ents = G.load()
    floors = []
    for f in FLOORS:
        w = G.WINDOWS[f["FLOOR"]]
        g = G.grid(ents, w)
        comps = G.rooms(g)
        floors.append(dict(f, GRID_CELLS=[len(g["XS"]) - 1, len(g["YS"]) - 1],
                           WALL_SEGMENTS=len(g["WALLS"]), COLUMN_SEGMENTS=len(g["COLUMNS"]),
                           VIRTUAL_CLOSURES=len(g["CLOSURES"]),
                           SPACE_COMPONENTS=len(comps),
                           SPACE_COMPONENTS_ABOVE_MIN=sum(1 for c in comps if c["AREA_M2"] >= G.MIN_ROOM_M2)))
    rec = {
        "ARTIFACT": "ALRASHED_PROJECT_IDENTITY_AND_FLOOR_INVENTORY",
        "PHASE_ID": "FULL_VILLA_BLIND_VALIDATION_01",
        "STEPS": "1 establish project identity; 2 inventory floors and drawings; 3 name the missing disciplines",
        "IDENTITY": IDENTITY,
        "FLOORS": floors, "FLOOR_COUNT": len(floors),
        "AREA_SCHEDULE_AS_DRAWN": AREA_SCHEDULE_AS_DRAWN,
        "REVISION_SETS_IN_THE_DWG": REVISION_SETS_IN_THE_DWG,
        "DISCIPLINES": DISCIPLINES,
        "SEALED": "the historical Excel for this project was not requested, opened or inferred",
        "GIT_HEAD": _git("rev-parse", "--short", "HEAD"),
    }
    rec["DIGEST"] = hashlib.sha256(
        json.dumps({k: v for k, v in rec.items() if k != "GIT_HEAD"},
                   sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()[:16]
    return rec


def finish():
    rec = build()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "ALRASHED_PROJECT_IDENTITY_AND_FLOOR_INVENTORY.json").write_text(
        json.dumps(rec, indent=1, ensure_ascii=False, default=str), "utf-8")
    return rec


if __name__ == "__main__":
    r = finish()
    i = r["IDENTITY"]
    print(f"{i['PROJECT_ID']}  |  digest {r['DIGEST']}")
    print(f"   {i['OWNER_ON_DRAWING']} - {i['LOCATION']}, block {i['BLOCK']} plot {i['PLOT']}, {i['PLOT_AREA_M2']} m2")
    for f in r["FLOORS"]:
        print(f"   {f['FLOOR']:9s} level {f['LEVEL_M']:6.2f}  grid {f['GRID_CELLS'][0]}x{f['GRID_CELLS'][1]}  "
              f"walls {f['WALL_SEGMENTS']:3d}  closures {f['VIRTUAL_CLOSURES']:3d}  "
              f"spaces {f['SPACE_COMPONENTS_ABOVE_MIN']:3d}")
