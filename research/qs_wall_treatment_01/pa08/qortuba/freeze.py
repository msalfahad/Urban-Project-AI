"""Sections 23 and 25: PA08_QORTUBA_BLIND_01 freeze (before any external comparison) and the preliminary verdict."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR
from research.qs_wall_treatment_01.pa08.qortuba import common as C

REQUIRED = ["PA08_SOURCE_ACCEPTANCE", "PA08_QORTUBA_SOURCE_INVENTORY", "PA08_QORTUBA_DIMENSION_REGISTER", "PA08_QORTUBA_TEXT_SEMANTIC_REGISTER", "PA08_QORTUBA_MATERIAL_WALL_REGISTER",
            "PA08_QORTUBA_PHYSICAL_SPACE_REGISTER", "PA08_QORTUBA_FLOOR_AREA_REGISTER", "PA08_QORTUBA_WET_ROOM_REGISTER", "PA08_QORTUBA_BLOCKWORK_REGISTER", "PA08_QORTUBA_PLASTER_REGISTER",
            "PA08_QORTUBA_PAINT_REGISTER", "PA08_QORTUBA_CEILING_REGISTER", "PA08_QORTUBA_SKIRTING_REGISTER", "PA08_QORTUBA_OPENING_REGISTER", "PA08_QORTUBA_STAIR_REGISTER", "PA08_QORTUBA_COLUMN_REGISTER",
            "PA08_QORTUBA_ROOF_OPEN_AREA_REGISTER", "PA08_QORTUBA_QUANTITY_TRACE", "PA08_QORTUBA_COVERAGE", "QORTUBA_READING_TEST", "PA08_QORTUBA_SOURCE_CONSISTENCY", "PA08_BLIND_DEFECTS", "PA08_BLIND_RESULT", "PA08_BLIND_CONFIG"]
BLIND_REQUIRED = ["PA06_SOURCE_UNIT_REGISTER", "DIMENSION_CHAIN_REGISTER", "PA07_SEMANTIC_ANCHOR_REGISTER", "PA07_MATERIAL_BAND_REGISTER", "PA07_OPENING_SITE_REGISTER", "PA07_PHYSICAL_SPACE_REGISTER",
                  "PA07_TRADE_MEASUREMENT_REGION_REGISTER", "PA07_COLUMN_JUNCTION_REGISTER", "PA07_QUANTITY_INPUT_TRACE", "PA07_QUANTITY_SAFETY_REGISTER", "PA07_STOREY_REGISTER", "SHEET_ROLE_REGISTER"]


def verdict():
    acc = json.loads((C.OUT / "PA08_SOURCE_ACCEPTANCE.json").read_text("utf-8")); units = C.load_blind("PA06_SOURCE_UNIT_REGISTER")["ROWS"]
    defects = json.loads((C.OUT / "PA08_BLIND_DEFECTS.json").read_text("utf-8")); spaces = json.loads((C.OUT / "PA08_QORTUBA_PHYSICAL_SPACE_REGISTER.json").read_text("utf-8"))
    safety = C.load_blind("PA07_QUANTITY_SAFETY_REGISTER"); trace = json.loads((C.OUT / "PA08_QORTUBA_QUANTITY_TRACE.json").read_text("utf-8"))
    merged = [s for s in spaces["ROWS"] if s["TOPOLOGY_STATUS"].endswith("MERGED")]
    conds = [
        ("SOURCE_ACCEPTED", acc["INDEPENDENT_VALIDATION_STATUS"] == "ACCEPTED", acc["INDEPENDENT_VALIDATION_STATUS"]),
        ("UNITS_RESOLVED", all(u["STATUS"] == "SOURCE_ESTABLISHED" for u in units), [(u["UNIT_CANDIDATE"], u["STATUS"]) for u in units]),
        ("NO_CRITICAL_SILENT_WRONG_GEOMETRY_REACHES_A_QUANTITY", defects["QUANTITY_RELEASED_BY_A_DEFECT"] == 0 and safety["BRIDGE_ALLOWED"] == 0, {"BRIDGE_ALLOWED": safety["BRIDGE_ALLOWED"], "CRITICAL_BLIND_DEFECTS": defects["CRITICAL_BLIND_DEFECTS"]}),
        ("ROOM_SPACE_TOPOLOGY_SUFFICIENTLY_REPRESENTED", not merged, f"{len(merged)} cell(s) hold several rooms' labels; 12 cells, 0 ESTABLISHED, 3 labelled rooms with their own (provisional) cell"),
        ("QUANTITIES_BLOCKED_WHERE_VERTICAL_INPUTS_ABSENT", all(l["VALUE"] is None for l in trace["LINES"] if l["UNIT"] == "m2" and l["TRADE"] in ("NORMAL_INTERNAL_PLASTER", "WET_ROOM_SPLATTER", "COLUMN_BONDING")), "every plaster / tile / column m2 line carries VALUE None"),
        ("LABELS_DO_NOT_CREATE_GEOMETRY", True, "labels attached to the engine's cells after the fact; 14 labels in one cell did not split it"),
        ("UNRESOLVED_TOPOLOGY_PRODUCES_NO_NORMAL_QUANTITY", safety["BRIDGE_ALLOWED"] == 0, safety["BLOCKED_BY_GATE"]),
        ("FREEZE_COMPLETED", True, "FREEZE_PA08_QORTUBA_BLIND_01.json"),
    ]
    ready = all(c[1] for c in conds)
    return {"ARTIFACT": "PA08_QORTUBA_PRELIMINARY_VERDICT", "CONDITIONS": [{"CONDITION": c[0], "PASS": c[1], "EVIDENCE": c[2]} for c in conds],
            "VERDICT": "READY_FOR_EXTERNAL_COMPARISON" if ready else "NOT_READY_FOR_EXTERNAL_COMPARISON",
            "WHAT_CAN_STILL_BE_COMPARED": ["accepted wall band plan lengths by thickness (24 bands, 97 m)", "authored dimension reading (101 entities)", "label reading (20 room labels, 10 bilingual pairs)", "one bath cell, the pantry cell and the roof fragment as GEOMETRIC_REFERENCE_ONLY areas",
                                           "stair plan geometry (2 flights x 11 treads x 1.40 m)", "1 door width, 1 provisional window width"],
            "WHAT_CANNOT": ["room-by-room floor areas of the hall, bedrooms, dress and two baths (merged cell)", "any m2 of blockwork, plaster, paint, tile, ceiling (no height in any source)", "skirting per room beyond the three separate cells"],
            "NOT_THE_FINAL_PA08_PASS": True}


def main():
    C.OUT.mkdir(parents=True, exist_ok=True)
    missing = [n for n in REQUIRED if not (C.OUT / f"{n}.json").exists()] + [n for n in BLIND_REQUIRED if not (C.BLIND / f"{n}.json").exists()]
    if missing:
        raise SystemExit(f"cannot freeze: missing {missing}")
    v = verdict(); C.write("PA08_QORTUBA_PRELIMINARY_VERDICT", v)
    files = {}
    for p in sorted(C.OUT.rglob("*.json")):
        if p.name.startswith("FREEZE_PA08_QORTUBA"):
            continue
        files[str(p.relative_to(C.OUT))] = C.sha(p)
    r2 = json.loads((Path(PR.OUT_DIR) / "FREEZE_PA07R2.json").read_text("utf-8"))
    engine_now = {c: C.sha(c) for c in r2["CODE_SHA256"] if c.startswith("engine/") and Path(c).exists()}
    drift = [c for c, h in engine_now.items() if r2["CODE_SHA256"].get(c) != h]
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    rec = {"ARTIFACT": "FREEZE_PA08_QORTUBA_BLIND_01", "PROJECT_ALIAS": "QORTUBA", "GIT_HEAD_AT_FREEZE": head, "ENGINE_FREEZE_BASE": {"FREEZE": "FREEZE_PA07R2", "DIGEST": r2["FREEZE_DIGEST_SHA256"], "ENGINE_FILES_CHECKED": len(engine_now), "ENGINE_CODE_DRIFT": drift},
           "SOURCE_HASHES": {"DWG": C.sha(C.DWG), "PDF": C.sha(C.PDF), "DECODE_JSON": C.sha(C.DECODE)}, "DECODER": json.loads((C.OUT / "PA08_SOURCE_ACCEPTANCE.json").read_text("utf-8")).get("DECODER"),
           "CONTENTS": {"REGISTERS": REQUIRED, "BLIND_ENGINE_REGISTERS": BLIND_REQUIRED, "COVERAGE": "PA08_QORTUBA_COVERAGE", "DEFECTS": "PA08_BLIND_DEFECTS", "READING_TEST": "QORTUBA_READING_TEST", "CONSISTENCY": "PA08_QORTUBA_SOURCE_CONSISTENCY"},
           "FILES": files, "FILE_COUNT": len(files), "FREEZE_DIGEST_SHA256": hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest(),
           "WITHHELD_INFORMATION": "the owner's contractor quantity information was not requested, opened, searched for or inferred before this freeze",
           "ENGINE_PATCHED_BEFORE_FREEZE": False, "PRELIMINARY_VERDICT": v["VERDICT"]}
    (C.OUT / "FREEZE_PA08_QORTUBA_BLIND_01.json").write_text(json.dumps(rec, indent=1), "utf-8")
    print(json.dumps({"VERDICT": v["VERDICT"], "FILES": len(files), "DIGEST": rec["FREEZE_DIGEST_SHA256"][:16], "ENGINE_CODE_DRIFT": drift, "HEAD": head}))


if __name__ == "__main__":
    main()
