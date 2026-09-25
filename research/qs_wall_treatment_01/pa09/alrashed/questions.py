"""The consolidated owner-question batch for the Al Rashed villa, after the complete read of the supplied set.

Only questions whose answer changes a quantity.  Each one says what the drawing does give, what it does not, and
what it blocks - in the words an owner can answer without opening a CAD file.  No ids, no hashes, no layer names.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR

OUT = Path(PR.OUT_DIR) / "pa09_alrashed"

QUESTIONS = [
    {"NO": "AR-01", "SUBJECT": "Floor-to-floor height",
     "DRAWING_GIVES": "the level of each floor: basement 65.04, ground 69.04, first 73.04. So floor to floor is "
                      "4.00 m basement to ground and 4.00 m ground to first.",
     "DRAWING_DOES_NOT_GIVE": "the slab thickness, so not the CLEAR height from finished floor to ceiling.",
     "ASK": "What clear wall height should I use for each floor? If the slab is 20 cm, clear height would be "
            "3.80 m - please confirm or give the right figure.",
     "BLOCKS": ["blockwork", "internal plaster", "external plaster", "internal paint", "external paint",
                "wall tiling in the wet rooms", "ceiling"],
     "WHY": "every wall quantity is length x height. The lengths are measured; the height is the only thing "
            "missing, and it multiplies all of them."},

    {"NO": "AR-02", "SUBJECT": "Door heights",
     "DRAWING_GIVES": "every door position and clear width on all three floors.",
     "DRAWING_DOES_NOT_GIVE": "any door height - there is no door schedule and no section in the supplied set.",
     "ASK": "What height are the internal doors, and is the main entrance door a different height?",
     "BLOCKS": ["PVC / internal doors", "the opening deductions from plaster, paint and blockwork"],
     "WHY": "a door that is not deducted leaves wall material in the quantity that was never built."},

    {"NO": "AR-03", "SUBJECT": "Window heights",
     "DRAWING_GIVES": "every window position and width.",
     "DRAWING_DOES_NOT_GIVE": "window height or sill height.",
     "ASK": "What height are the windows, and at what sill height? If they vary by room, which rooms differ?",
     "BLOCKS": ["aluminium", "the opening deductions from external plaster and paint"],
     "WHY": "aluminium is priced by area, and the deduction changes the plaster and paint on every external wall."},

    {"NO": "AR-04", "SUBJECT": "The area schedule on the sheet",
     "DRAWING_GIVES": "an area schedule reading 69.66 m2 (11.61%), 382.16 m2 (63.69%), 494.62 m2 (82.43%) and "
                      "600.00 m2 (100%), with 451.82 = 382.16 + 69.66 written on the sheet.",
     "DRAWING_DOES_NOT_GIVE": "which storey each figure measures. 494.62 is not 451.82, so one figure covers "
                              "something the other two do not.",
     "ASK": "Which floor is 382.16 m2 and which is 69.66 m2, and what does 494.62 m2 include that they do not?",
     "BLOCKS": [],
     "WHY": "nothing is calculated from these figures - they are the independent check on my own measured areas, "
            "and I cannot check a floor against a figure until I know which floor it is."},

    {"NO": "AR-05", "SUBJECT": "Which floors are finished, and in what",
     "DRAWING_GIVES": "room names on every floor: dewaniya, hall, mugallat, car parking, driver, store, pantries "
                      "and baths in the basement; halls, bedrooms, master bedrooms, kitchen, dress, wash rooms, "
                      "baths and balconies on the ground floor; store, machine room and heaters on the first.",
     "DRAWING_DOES_NOT_GIVE": "any finishes schedule or specification.",
     "ASK": "Which rooms take porcelain and which take ceramic, and is the car parking finished or left as "
            "power-floated concrete?",
     "BLOCKS": ["porcelain", "ceramic", "skirting / profile"],
     "WHY": "the floor areas are the same either way, but they are different BOQ items at different rates."},

    {"NO": "AR-06", "SUBJECT": "The roof at first floor level",
     "DRAWING_GIVES": "the first floor is almost entirely open roof at level 73.04, with a small block containing "
                      "a store, a machine room and the heaters. There is no separate roof plan sheet.",
     "DRAWING_DOES_NOT_GIVE": "the parapet height, or whether the roof is tiled, screeded or left bare.",
     "ASK": "How high is the roof parapet, and what finish goes on the roof?",
     "BLOCKS": ["waterproofing", "roof finish", "parapet blockwork, plaster and paint"],
     "WHY": "the roof is the largest single horizontal area in the villa and the parapet runs right around it."},

    {"NO": "AR-07", "SUBJECT": "Structural and MEP drawings",
     "DRAWING_GIVES": "architectural floor plans only.",
     "DRAWING_DOES_NOT_GIVE": "any structural, sanitary, electrical or mechanical drawing.",
     "ASK": "Do you want concrete, reinforcement, sanitary and electrical in this takeoff? If so those drawings "
            "are needed; if not I will leave those trades out rather than estimate them.",
     "BLOCKS": ["concrete / reinforcement", "sanitary", "electrical"],
     "WHY": "a quantity is not invented for a discipline that was not supplied."},

    {"NO": "AR-08", "SUBJECT": "Scope of the basement external areas",
     "DRAWING_GIVES": "a car parking area and open areas inside the plot at basement level.",
     "DRAWING_DOES_NOT_GIVE": "whether these are inside the contract.",
     "ASK": "Is the car parking area and the open yard part of the finishing scope, or is the contract the "
            "building only?",
     "BLOCKS": ["external floor finish", "external plaster and paint to boundary walls"],
     "WHY": "it is a large area and including or excluding it moves the external trades significantly."},
]


def build():
    rec = {"ARTIFACT": "ALRASHED_OWNER_QUESTIONS_BATCH_01",
           "PROJECT_ID": "ALRASHED_SABAH_AL_AHMAD",
           "PHASE_ID": "FULL_VILLA_BLIND_VALIDATION_01",
           "BATCH": 1, "COUNT": len(QUESTIONS), "QUESTIONS": QUESTIONS,
           "NUMBERING": "AR-nn is this project's own namespace; Qortuba's numbers are sealed with Qortuba",
           "RULE": "asked once, as one batch, after the complete read of the supplied set",
           "NOT_ASKED": "nothing the drawings already answer. The drawing unit, the wall thicknesses, the room "
                        "names, the levels, the plot and the current revision were all read from the source"}
    rec["DIGEST"] = hashlib.sha256(json.dumps(QUESTIONS, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]
    return rec


def finish():
    rec = build()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "ALRASHED_OWNER_QUESTIONS_BATCH_01.json").write_text(
        json.dumps(rec, indent=1, ensure_ascii=False), "utf-8")
    return rec


if __name__ == "__main__":
    r = finish()
    print(f"{r['COUNT']} questions  |  digest {r['DIGEST']}")
    for q in r["QUESTIONS"]:
        print(f"  {q['NO']}  {q['SUBJECT']}")
