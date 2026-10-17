"""PA08_QORTUBA_BLIND_01 step 1: acceptance + the frozen engine AS-IS on the Qortuba sources, in the audited subprocess.

No engine change, no owner parameter, no height, no label, no storey name: the sources and the generic rules only.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR
from research.qs_wall_treatment_01.pa08 import blind_run as BR, source_acceptance as SA

UP = "/root/.claude/uploads/93607c01-16a4-590f-af7c-1c2701c3b240/"
DWG = UP + "b634a91b-qurtoba1.dwg"
PDF = UP + "55d20e2d-BLOCK__1__PLOT_449-rfa1.pdf"
DECODE = "data/runs/cad_convert/QORTUBA_ARCHITECTURAL.json"
OUT = Path(PR.OUT_DIR) / "pa08_qortuba"
BLIND = OUT / "blind"
REGISTRY = {"_REGISTRY_ID": "QORTUBA_BLIND_NO_OWNER_PARAMETERS", "NORMAL_INTERNAL_PLASTER_HEIGHT": {"VALUE": None, "SOURCE_TYPE": "UNKNOWN"}, "DOOR_HEIGHT": {"VALUE": None, "SOURCE_TYPE": "UNKNOWN"},
            "DOOR_REVEAL_DEPTH": {"VALUE": None, "SOURCE_TYPE": "UNKNOWN"}, "TARTUSHA_HEIGHT": {"VALUE": None, "SOURCE_TYPE": "UNKNOWN"}, "WALL_TILE_HEIGHT": {"VALUE": None, "SOURCE_TYPE": "UNKNOWN"},
            "NOTE": "blind test: no P7757 value is a Qortuba rule; every vertical parameter is UNKNOWN until the owner declares it for this project"}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def decoder_record():
    exe = "/tmp/ldwg/programs/dwgread"
    ver = subprocess.run([exe, "--version"], capture_output=True, text=True).stdout.strip() if Path(exe).exists() else None
    return {"DECODER": "GNU LibreDWG dwgread -O JSON", "VERSION": ver, "PATH": exe, "EPHEMERAL_BUILD": True, "DWG_SHA256": sha(DWG), "DECODE_SHA256": sha(DECODE), "DECODE_BYTES": Path(DECODE).stat().st_size,
            "NOTE": "the decode is a lossless-as-possible JSON of the DWG; the engine reads the decode, never the DWG bytes"}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    acc = SA.accept("QORTUBA", [DWG, DECODE, PDF], {DWG: "ARCHITECTURAL", DECODE: "ARCHITECTURAL", PDF: "ARCHITECTURAL"}, declared_exposure=None)
    acc["DECODER"] = decoder_record()
    acc["OWNER_DECLARATION"] = "the owner holds withheld contractor quantity information for this project; it was not requested, opened or inferred"
    (OUT / "PA08_SOURCE_ACCEPTANCE.json").write_text(json.dumps(acc, indent=1), "utf-8")
    print("ACCEPTANCE", acc["INDEPENDENT_VALIDATION_STATUS"], acc["HAS_THIS_PROJECT_BEEN_USED_TO_DEVELOP_THE_ENGINE"], acc["UNIT_STATUS"])
    if acc["INDEPENDENT_VALIDATION_STATUS"] != "ACCEPTED":
        raise SystemExit("not accepted")
    cfg = BR.config_for(acc, REGISTRY, trades=("NORMAL_INTERNAL_PLASTER", "WET_ROOM_SPLATTER", "COLUMN_BONDING"), rule_version="URBAN_RULES_PA08_QORTUBA_BLIND")
    cfg["PROJECT_ID"] = "QORTUBA"; cfg["DRAWING_FAMILY"] = "VILLA_APARTMENT_SECOND_FLOOR"
    (OUT / "PA08_BLIND_CONFIG.json").write_text(json.dumps(cfg, indent=1), "utf-8")
    blind = BR.launch(cfg, [DECODE, PDF], out_dir=BLIND)
    (OUT / "PA08_BLIND_RESULT.json").write_text(json.dumps(blind, indent=1), "utf-8")
    print("BLIND", blind["STATUS"], "violations", blind["VIOLATIONS"], "files", len(blind["FILES_OPENED"]))
    if blind["STATUS"] != "COMPLETED":
        print(blind["STDERR_TAIL"])


if __name__ == "__main__":
    main()
