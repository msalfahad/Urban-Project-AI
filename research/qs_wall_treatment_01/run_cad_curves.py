"""P7757 curve register from the architectural DWG decode.

Anchors are the authored room labels the CAD census already established
as real identity (SALOON, RECEPTION, swimming pool). The curved faces the
A21 readers could describe but not measure are named as PROPOSED
correspondences only.

    python3 -m research.qs_wall_treatment_01.run_cad_curves
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from engine import cad_adapter as CA
from engine import cad_curve_register as CR
from research.qs_wall_treatment_01 import protocol as P

DECODE = "data/runs/cad_convert/P7757_ARCHITECTURAL.json"
DWG = "data/golden/7757/source_c/P7757_ARCHITECTURAL.dwg"

ANCHORS = {
    "POOL": {"LABEL": "swimming pool",
             "PROPOSED_A21": ["CASE-3-DOOR-AND-WINDOW/GLZ-02 (curved band, "
                              "lower-left quadrant of the swimming pool)"],
             "RADIUS_BAND_MM": (1000.0, 3000.0), "LAYERS": ("5", "2", "4")},
    "RECEPTION": {"LABEL": "RECEPTION",
                  "PROPOSED_A21": ["CASE-4-STAIR/STR-01, CASE-1-NORMAL-PLASTER/STR-01 "
                                   "(curved main stair)"],
                  "RADIUS_BAND_MM": (1000.0, 3000.0), "LAYERS": ("5",)},
    "SALOON": {"LABEL": "SALOON",
               "PROPOSED_A21": ["CASE-3-DOOR-AND-WINDOW/GLZ-02"],
               "RADIUS_BAND_MM": (1000.0, 3000.0), "LAYERS": ("5", "2", "4")},
}

NOT_LOCATED_BY_DESIGN = [
    {"A21": "CASE-6-ROOF-PARAPET/PAR-01 rounded corner (SE parapet, roof plan)",
     "STATUS": "NOT_LOCATED",
     "WHY": "the roof plan frame is not identified in the CAD model (floor "
            "identity is NOT_ESTABLISHED_FROM_CAD); no anchor label exists "
            "on that sheet in the decode"},
]


def run() -> dict:
    d = json.loads(Path(DECODE).read_text("utf-8"))
    n = CA.normalize(d, source_file=Path(DWG).name)
    reg = CR.curve_register(n, anchors=ANCHORS)
    body = {"PHASE_ID": P.PHASE_ID, "ARTIFACT": "CAD_CURVE_REGISTER",
            "DECODE_SHA256": hashlib.sha256(Path(DECODE).read_bytes()).hexdigest(),
            "DWG_SHA256": hashlib.sha256(Path(DWG).read_bytes()).hexdigest(),
            "NORMALIZATION_HASH": (n.normalization_hash() if callable(n.normalization_hash) else n.normalization_hash),
            "ANCHORS": ANCHORS, "NOT_LOCATED_BY_DESIGN": NOT_LOCATED_BY_DESIGN,
            **reg}
    p = Path(P.OUT_DIR) / "CAD_CURVE_REGISTER.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"CAD_CURVE_REGISTER_SHA256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "CURVE_SETS": [(s["CURVE_SET_ID"], s["FRAME_ID"], s["CENTER_MM"],
                            s["RADII_MM"], s["DISTANCE_CENTER_TO_ANCHOR_M"])
                           for s in body["CURVE_SETS"]],
            "FRAMES": len(body["FRAMES"])}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
