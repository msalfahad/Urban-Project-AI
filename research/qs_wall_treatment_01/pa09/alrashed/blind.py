"""FULL_VILLA_BLIND_VALIDATION step 1: accept the Al Rashed sources and run the frozen engine on them.

No engine change, no Qortuba value, no owner parameter, no label, no storey name: the two supplied drawings and the
generic rules only.  Every file the run opens is audited in a subprocess, so a read outside the accepted set makes
the run VALIDATION_INVALID instead of quietly contaminating the blind.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR
from research.qs_wall_treatment_01.pa08 import blind_run as BR, source_acceptance as SA

UP = "/root/.claude/uploads/93607c01-16a4-590f-af7c-1c2701c3b240/"
DWG = UP + "a0f821ff-16-11-2025.dwg"
PDF = UP + "507baa5b-16-11-2025.pdf"
DECODE = "data/runs/cad_convert/ALRASHED_ARCHITECTURAL.json"
OUT = Path(PR.OUT_DIR) / "pa09_alrashed"
BLIND = OUT / "blind"

# Every vertical parameter is UNKNOWN.  Qortuba's 3.00 m wall, 2.20 m door and 1.50 m window are measurements of one
# flat in another building and are not defaults here; where this project needs a height it is read or asked.
REGISTRY = {"_REGISTRY_ID": "ALRASHED_BLIND_NO_OWNER_PARAMETERS",
            "NORMAL_INTERNAL_PLASTER_HEIGHT": {"VALUE": None, "SOURCE_TYPE": "UNKNOWN"},
            "DOOR_HEIGHT": {"VALUE": None, "SOURCE_TYPE": "UNKNOWN"},
            "DOOR_REVEAL_DEPTH": {"VALUE": None, "SOURCE_TYPE": "UNKNOWN"},
            "TARTUSHA_HEIGHT": {"VALUE": None, "SOURCE_TYPE": "UNKNOWN"},
            "WALL_TILE_HEIGHT": {"VALUE": None, "SOURCE_TYPE": "UNKNOWN"},
            "NOTE": "blind test: no Qortuba or P7757 value is an Al Rashed rule"}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def decoder_record():
    exe = "/tmp/ldwg/programs/dwgread"
    ver = subprocess.run([exe, "--version"], capture_output=True, text=True).stdout.strip() if Path(exe).exists() else None
    return {"DECODER": "GNU LibreDWG dwgread -O JSON", "VERSION": ver, "PATH": exe,
            "DWG_SHA256": sha(DWG), "DECODE_SHA256": sha(DECODE), "DECODE_BYTES": Path(DECODE).stat().st_size,
            "DECODE_NORMALISED_TO_UTF8": True,
            "NORMALISATION": "the decoder emits the drawing's legacy Arabic font bytes verbatim, so the JSON is not "
                             "valid UTF-8; 40 undecodable bytes were replaced before the engine read it.  This is "
                             "part of decoding, not an engine change: no geometry, dimension or coordinate is "
                             "touched, and the affected bytes are all inside Arabic label text",
            "NOTE": "the engine reads the decode, never the DWG bytes"}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    acc = SA.accept("ALRASHED_SABAH_AL_AHMAD", [DWG, DECODE, PDF],
                    {DWG: "ARCHITECTURAL", DECODE: "ARCHITECTURAL", PDF: "ARCHITECTURAL"}, declared_exposure=None)
    acc["DECODER"] = decoder_record()
    acc["DECLARED_UNIT"] = {
        "SOURCE": DECODE, "UNIT": "m",
        "EVIDENCE": ["title text on every sheet: S.STREET 22.00 m / NEIGHBOR 27.28 M, and the plan geometry spans "
                     "about 22 x 23 drawing units",
                     "the modal paired-wall separation is 0.20 and 0.15 drawing units - 200 and 150 mm, a wall, "
                     "only if a drawing unit is a metre",
                     "362 of 507 authored dimensions display exactly 100 x their own geometry: metres drawn, "
                     "centimetres shown"],
        "FILE_SAYS": "INSUNITS = 1 (inches), which the drawing contradicts",
        "HOW_IT_IS_APPLIED": "the declaration is offered to the engine, which accepts it only after checking that "
                             "it puts the drawing's wall pairs inside the plausible wall band and that INSUNITS "
                             "does not.  The engine is not told what the answer is"}
    acc["OWNER_DECLARATION"] = ("the owner holds a historical Excel for this project; it was not requested, opened "
                                "or inferred, and it stays sealed until the blind takeoff is frozen")
    (OUT / "ALRASHED_SOURCE_ACCEPTANCE.json").write_text(json.dumps(acc, indent=1, default=str), "utf-8")
    print("ACCEPTANCE", acc["INDEPENDENT_VALIDATION_STATUS"], acc["HAS_THIS_PROJECT_BEEN_USED_TO_DEVELOP_THE_ENGINE"], acc["UNIT_STATUS"])
    if acc["INDEPENDENT_VALIDATION_STATUS"] != "ACCEPTED":
        raise SystemExit("not accepted")
    cfg = BR.config_for(acc, REGISTRY, trades=("NORMAL_INTERNAL_PLASTER", "WET_ROOM_SPLATTER", "COLUMN_BONDING"),
                        rule_version="URBAN_RULES_PA09_ALRASHED_BLIND")
    cfg["PROJECT_ID"] = "ALRASHED"; cfg["DRAWING_FAMILY"] = "VILLA_THREE_STOREY"
    # The file's INSUNITS says inches.  The building says otherwise, three ways, all of them on the drawing:
    # the plot is written on the sheet as 22.00 m x 27.28 m and the plan geometry spans about 22 x 23 units; the
    # walls are drawn 0.20 and 0.15 units apart, which is a wall only if a unit is a metre; and the dimensions
    # display exactly 100 x their own geometry, which is centimetres from metres.  Declaring the unit is reading
    # the drawing, not assuming it - and the engine still checks the declaration against the wall band before it
    # will overrule the file.
    cfg["DECLARED_UNITS"] = {DECODE: "m"}
    (OUT / "ALRASHED_BLIND_CONFIG.json").write_text(json.dumps(cfg, indent=1, default=str), "utf-8")
    blind = BR.launch(cfg, [DECODE, PDF], out_dir=BLIND)
    (OUT / "ALRASHED_BLIND_RESULT.json").write_text(json.dumps(blind, indent=1, default=str), "utf-8")
    print("BLIND", blind["STATUS"], "violations", blind["VIOLATIONS"], "files", len(blind["FILES_OPENED"]))
    if blind["STATUS"] != "COMPLETED":
        print(blind["STDERR_TAIL"])
    return blind


if __name__ == "__main__":
    main()
