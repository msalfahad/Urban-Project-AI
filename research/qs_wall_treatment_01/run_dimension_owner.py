"""DIMENSION_OWNER_STATUS over the four frozen cases, and the independent
CASE-6 height re-check the owner ordered (§5).

Two records per CASE-6 height dimension, kept apart:

  * the DETERMINISTIC owner resolution from traced extension lines against
    traced element geometry (engine.dimension_owner), with an ink check on
    the processed sheet;
  * the ORCHESTRATOR_VISUAL_RECHECK - a fresh reading of the source crops
    at the traced extension lines, recorded in the orchestrator's own words
    and marked as such. It is a review, not a reader output, and it changes
    nothing in the frozen register.

    python3 -m research.qs_wall_treatment_01.run_dimension_owner
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image

from engine import dimension_owner as DO
from research.qs_wall_treatment_01 import declarations as D
from research.qs_wall_treatment_01 import protocol as P

# The orchestrator's independent re-check of every CASE-6 height dimension,
# from the source crops at the traced extension lines (not from prose).
ORCHESTRATOR_VISUAL_RECHECK = {
    "RECHECK_BY": "ORCHESTRATOR_VISUAL_RECHECK",
    "METHOD": "crops of the processed sheets at the traced EXTENSION_LINE_A/B "
              "and DIMENSION_LINE_TRACE coordinates, viewed at 2x-12x; each end "
              "described by what the extension line lands on",
    "DIMENSIONS": {
        "DIM-16": {"SHEET": "SOUTH_EAST_ELEVATION", "TEXT": "155",
                   "END_A": "tower top line y=432 (+14.40)",
                   "END_B": "horizontal extension line at y=540 meeting the tower "
                            "wall: the DOME APEX level, not a parapet element",
                   "OWNER": "tower top to dome apex",
                   "AGREES_WITH_READER_PROSE": False,
                   "DISCREPANCY": "the reader's prose called 155 the 'first link "
                                  "down to the parapet rail'; the rail is the end "
                                  "of 193, not of 155. The chain values and their "
                                  "sum are unaffected; only the prose owner of "
                                  "155 was wrong"},
        "DIM-17": {"SHEET": "SOUTH_EAST_ELEVATION", "TEXT": "193",
                   "END_A": "dome apex level y=540", "END_B": "handrail top y=673",
                   "OWNER": "dome apex to handrail top", "AGREES_WITH_READER_PROSE": True},
        "DIM-18": {"SHEET": "SOUTH_EAST_ELEVATION", "TEXT": "104",
                   "END_A": "handrail top y=673",
                   "END_B": "terrace parapet base line y=745",
                   "OWNER": "composite: kerb above base line + X-lattice + rail; "
                            "the text sits inside the lattice zone",
                   "AGREES_WITH_READER_PROSE": True,
                   "NOTE": "104 is NOT the height of any solid plasterable face"},
        "DIM-19": {"SHEET": "SOUTH_EAST_ELEVATION", "TEXT": "139",
                   "END_A": "parapet base line y=745", "END_B": "window head y=841",
                   "OWNER": "base line to window head (not a parapet dimension)",
                   "AGREES_WITH_READER_PROSE": True},
        "DIM-20": {"SHEET": "SOUTH_EAST_ELEVATION", "TEXT": "20",
                   "END_A": "upper line of the top band y=650",
                   "END_B": "lower line of the top band y=662, over the solid wall",
                   "OWNER": "capping band thickness (PAR-13)", "AGREES_WITH_READER_PROSE": True},
        "DIM-21": {"SHEET": "SOUTH_EAST_ELEVATION", "TEXT": "680",
                   "END_A": "lower line of the band y=662 = top of the solid wall face",
                   "END_B": "+4.30 annex roof slab (hatched) y=1138",
                   "OWNER": "solid wall top (PAR-12) to +4.30 slab",
                   "AGREES_WITH_READER_PROSE": True},
        "DIM-13": {"SHEET": "SOUTH_EAST_ELEVATION", "TEXT": "1440",
                   "END_A": "tower top y=432", "END_B": "ground line ±0.00 y=1432",
                   "OWNER": "overall height", "AGREES_WITH_READER_PROSE": True},
        "DIM-14": {"SHEET": "SOUTH_EAST_ELEVATION", "TEXT": "50",
                   "END_A": "tower top line y=432",
                   "END_B": "DASHED +13.90 level line y=465 (a datum line, not a "
                            "drawn slab edge)",
                   "OWNER": "tower parapet PAR-10 height above the +13.90 datum",
                   "AGREES_WITH_READER_PROSE": True},
        "DIM-15": {"SHEET": "SOUTH_EAST_ELEVATION", "TEXT": "420",
                   "END_A": "dashed +13.90 line y=465", "END_B": "dashed +9.70 line y=760",
                   "OWNER": "storey datum to datum", "AGREES_WITH_READER_PROSE": True},
        "DIM-07": {"SHEET": "SECTION_B_B", "TEXT": "130",
                   "END_A": "extension line at y=490 landing on the top of the "
                            "un-hatched outer NW roof-edge element (x~1624-1656)",
                   "END_B": "slab top +9.70 y=557",
                   "OWNER": "NW (sea-view) roof-edge element UNK-06 - identity "
                            "unresolved; the hatched wall beside it is only ~10 cm "
                            "above the slab",
                   "AGREES_WITH_READER_PROSE": True,
                   "NOTE": "130 is NOT a dimension of the SE parapet"},
        "DIM-08": {"SHEET": "SECTION_B_B", "TEXT": "50",
                   "END_A": "tower block top y=315", "END_B": "dashed +13.90 line y=341",
                   "OWNER": "tower parapet PAR-06 above the +13.90 datum",
                   "AGREES_WITH_READER_PROSE": True},
        "DIM-09": {"SHEET": "SECTION_B_B", "TEXT": "420",
                   "END_A": "dashed +13.90 y=341", "END_B": "slab top +9.70 y=557",
                   "OWNER": "storey datum to slab", "AGREES_WITH_READER_PROSE": True},
        "DIM-10": {"SHEET": "SECTION_A_A", "TEXT": "50",
                   "END_A": "parapet top line y=412 (hatched cut parapet at left)",
                   "END_B": "slab top line y=445",
                   "OWNER": "tower parapet PAR-08", "AGREES_WITH_READER_PROSE": True},
        "DIM-11": {"SHEET": "SECTION_A_A", "TEXT": "50",
                   "END_A": "parapet top line y=412", "END_B": "dashed level line y=445",
                   "OWNER": "tower parapet PAR-09 above the +13.90 datum",
                   "AGREES_WITH_READER_PROSE": True},
    },
    "CROSS_SHEET_CONSISTENCY": {
        "SE_PARAPET_STACK_AT_B_B_CUT": (
            "B-B at 1.944 cm/px (420 cm = 216 px): hatched kerb 557->529 = 0.54 m, "
            "lattice 529->502 = 0.52 m, cap 502->493 = 0.17 m; total 1.24 m above "
            "+9.70 -> cap top ~ +10.94. SE elevation chain: 14.40-1.55-1.93 = +10.92 "
            "rail top. CONSISTENT within one pixel. The elevation's base line at "
            "+9.88 is ~0.18 m above the slab: the kerb continues below it"),
        "SE_SOLID_WALL_FACE_HEIGHT": (
            "+4.30+6.80 = +11.10 solid wall top, +11.30 band top; base line +9.88: "
            "face 1.22 m without the band, 1.42 m with it. AMBIGUOUS stands"),
    },
    "CHANGES_TO_THE_FROZEN_REGISTER": "none",
}


def _images(cid: str) -> dict:
    d = Path(P.CASE_SANDBOX) / cid
    out = {}
    for f in d.glob("*.jpeg"):
        out[f.stem] = Image.open(f).convert("L")
    return out


def run() -> dict:
    reg = json.loads(Path(P.TRACE_REGISTER).read_text("utf-8"))
    out = {"PHASE_ID": P.PHASE_ID, "ARTIFACT": "DIMENSION_OWNER_REGISTER",
           "TRACE_REGISTER_SHA256": hashlib.sha256(
               Path(P.TRACE_REGISTER).read_bytes()).hexdigest(),
           "STATUSES": DO.OWNER_STATUSES,
           "OWNER_IS_SEPARATE_FROM_TEXT_READ": True,
           "PER_CASE": {}, "SUMMARY": {}}
    for cid in P.CASES:
        traces = [t for t in reg["TRACES"] if t["CASE_ID"] == cid]
        recs = DO.resolve(traces, object_map=D.OBJECT_MAP.get(cid),
                          role_overrides=D.ROLE_OVERRIDES.get(cid),
                          images=_images(cid))
        out["PER_CASE"][cid] = recs
        out["SUMMARY"][cid] = DO.summary(recs)
    out["ORCHESTRATOR_VISUAL_RECHECK_CASE_6"] = ORCHESTRATOR_VISUAL_RECHECK
    # agreement between the deterministic resolution and the visual re-check
    det = {r["TRACE_ID"]: r for r in out["PER_CASE"]["CASE-6-ROOF-PARAPET"]}
    agree = {}
    for did, v in ORCHESTRATOR_VISUAL_RECHECK["DIMENSIONS"].items():
        r = det.get(did)
        agree[did] = {"DETERMINISTIC": r["DIMENSION_OWNER_STATUS"] if r else None,
                      "DETERMINISTIC_OWNER_OBJECTS": r["OWNER_OBJECTS"] if r else None,
                      "VISUAL_OWNER": v["OWNER"],
                      "PROSE_AGREEMENT": v["AGREES_WITH_READER_PROSE"]}
    out["CASE_6_RECHECK_VS_DETERMINISTIC"] = agree
    p = Path(P.OUT_DIR) / "DIMENSION_OWNER_REGISTER.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"DIMENSION_OWNER_REGISTER_SHA256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "SUMMARY": out["SUMMARY"]}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
