"""SOURCE DOCUMENT INVENTORY (§25) - what exists, what is NOT PROVIDED.

Registers every project document present in the repository and in the
session upload area by name, size and hash; classifies it; and marks each
document type the readers or the trade rules require as PRESENT,
PRESENT_NOT_DECODED, PRESENT_SEALED or SOURCE_NOT_PROVIDED.

Policy on the upload area:
  * spreadsheets are hashed, never opened (they may be the human
    benchmark; the benchmark stays sealed until A22 is frozen)
  * credential files are listed by name only, never read or hashed
  * nothing here is copied into the repository

    python3 -m research.qs_wall_treatment_01.source_inventory
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as P

REPO_SOURCES = [
    ("data/golden/7757/inputs/P7757_SCAN_20260506.pdf", "RASTER_SCAN_SET", "the 12-page scan"),
    ("data/golden/7757/inputs/P7757_DRAWINGS.pdf", "ARCHITECTURAL_DRAWINGS_PDF",
     "the 10 drawing pages split from the scan"),
    ("data/golden/7757/original/P7757_ORIGINAL_pages_01-06.pdf", "ORIGINAL_PDF_PART", ""),
    ("data/golden/7757/original/P7757_ORIGINAL_pages_07-12.pdf", "ORIGINAL_PDF_PART", ""),
    ("data/golden/7757/source_c/P7757_ARCHITECTURAL.dwg", "ARCHITECTURAL_DWG", "DESIGN_ARCHITECTURAL"),
    ("data/golden/7757/source_b/P7757_ARCHITECTURAL_20260506.dwf", "ARCHITECTURAL_DWF",
     "no W2D reader in this project"),
    ("data/golden/7757/sealed/P7757_area_takeoff_benchmark.pdf", "SEALED_AREA_TAKEOFF",
     "architect's floor-area take-off; SEALED; not a wall-treatment benchmark"),
    ("data/runs/cad_convert/P7757_ARCHITECTURAL.json", "ARCHITECTURAL_DWG_DECODE", "LibreDWG JSON"),
    ("data/registry/P7757_PROJECT_RULES.json", "PROJECT_RULES", ""),
    ("data/trade_rules/URBAN_PROJECTS_RULE_LIBRARY.json", "RULE_LIBRARY", ""),
]

UPLOAD_DIR = Path("/root/.claude/uploads/93607c01-16a4-590f-af7c-1c2701c3b240")

# document types the trace readers and the trade rules asked for
REQUIRED_TYPES = {
    "FINISHES_SPECIFICATION": "which faces are plaster / tartusha / stone; heights",
    "DOOR_AND_WINDOW_SCHEDULE": "opening sizes replacing the temporary defaults",
    "OPENING_JAMB_SILL_HEAD_DETAIL": "actual reveal depths (§16)",
    "STAIR_SECTION_DETAIL": "stair-well plaster height, underside",
    "STAIR_SETTING_OUT_PLAN": "stair wall face lengths",
    "PARAPET_COPING_DETAIL": "capping / band construction",
    "ROOF_BUILD_UP_OR_PARAPET_BASE_DETAIL": "kerb height above slab",
    "ROOF_PLAN_AT_+13.90": "tower parapet plan lengths",
    "REFLECTED_CEILING_PLAN": "ceiling heights per room (floors are not ceilings, §28)",
    "SECTION_THROUGH_RECEPTION_VOID": "double-height plaster height",
    "COLUMN_SCHEDULE": "column faces for bonding + plaster (§19)",
    "STRUCTURAL_DRAWINGS": "beams (not plaster), column positions",
    "SANITARY_DRAWINGS": "wet rooms for tartusha scope (§18)",
    "ELECTRICAL_DRAWINGS": "not required for wall treatment",
    "CONTROL_JOINT_DETAIL": "control-joint spacing (§24)",
    "EXTERNAL_FINISHES_SCHEDULE": "which facade faces are plastered (§21)",
}
# what the repository / uploads can satisfy, by rule
TYPE_SATISFIED_BY = {
    "STRUCTURAL_DRAWINGS": ("UPLOAD_STRUCTURAL_DWG", "PRESENT_NOT_DECODED"),
    "SANITARY_DRAWINGS": ("REGISTERED_DESIGN_SANITARY", "PRESENT_REGISTERED"),
}


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _classify_upload(name: str) -> tuple:
    n = name.lower()
    if "firebase" in n or "urbanprojectsmanager" in n or n.endswith(".json"):
        return "CREDENTIAL_OR_CONFIG_FILE", "NEVER_READ_NEVER_HASHED"
    if n.endswith((".xlsx", ".xls", ".xlsm")):
        return "SPREADSHEET", "SEALED_HASHED_NOT_OPENED"
    if n.endswith(".dwg"):
        if "st7757" in n or "str" in n:
            return "STRUCTURAL_DWG", "PRESENT_NOT_DECODED"
        return "ARCHITECTURAL_DWG_UPLOAD", "PRESENT"
    if n.endswith(".dwf"):
        return "DWF_PACKAGE", "PRESENT_NO_READER"
    if "sanitary" in n:
        return "SANITARY_PDF", "PRESENT_REGISTERED"
    if "st7757" in n and n.endswith(".pdf"):
        return "STRUCTURAL_PDF", "PRESENT_NOT_READ"
    if n.endswith(".pdf"):
        return "PDF", "PRESENT_NOT_CLASSIFIED"
    if n.endswith((".png", ".jpg", ".jpeg")):
        return "IMAGE", "PRESENT_NOT_CLASSIFIED"
    return "OTHER", "PRESENT_NOT_CLASSIFIED"


def run() -> dict:
    repo = []
    for rel, kind, note in REPO_SOURCES:
        p = Path(rel)
        repo.append({"PATH": rel, "KIND": kind, "NOTE": note,
                     "PRESENT": p.exists(),
                     "SIZE": p.stat().st_size if p.exists() else None,
                     "SHA256": _sha(p) if p.exists() else None})
    uploads = []
    if UPLOAD_DIR.exists():
        for f in sorted(UPLOAD_DIR.iterdir()):
            kind, status = _classify_upload(f.name)
            rec = {"NAME": f.name, "KIND": kind, "STATUS": status,
                   "SIZE": f.stat().st_size}
            if status != "NEVER_READ_NEVER_HASHED":
                rec["SHA256"] = _sha(f)
            uploads.append(rec)
    up_kinds = {u["KIND"] for u in uploads}
    rules = json.loads(Path("data/registry/P7757_PROJECT_RULES.json").read_text("utf-8"))
    sanitary = (rules.get("sources") or {}).get("DESIGN_SANITARY")
    sanitary_present = any(u["KIND"] == "SANITARY_PDF" for u in uploads)
    required = {}
    for t, why in REQUIRED_TYPES.items():
        st = "SOURCE_NOT_PROVIDED"
        by = None
        if t == "STRUCTURAL_DRAWINGS" and ("STRUCTURAL_DWG" in up_kinds or "STRUCTURAL_PDF" in up_kinds):
            st, by = "PRESENT_NOT_DECODED", "upload: structural DWG/PDF"
        if t == "SANITARY_DRAWINGS" and (sanitary or sanitary_present):
            st, by = "PRESENT_REGISTERED", "DESIGN_SANITARY in P7757_PROJECT_RULES"
        required[t] = {"NEEDED_FOR": why, "STATUS": st, "SATISFIED_BY": by}
    spreadsheets = [u for u in uploads if u["KIND"] == "SPREADSHEET"]
    body = {
        "PHASE_ID": P.PHASE_ID, "ARTIFACT": "SOURCE_INVENTORY",
        "REPOSITORY_SOURCES": repo,
        "UPLOAD_AREA": str(UPLOAD_DIR),
        "UPLOAD_AREA_FILES": uploads,
        "SPREADSHEETS_SEALED": [{"NAME": s["NAME"], "SHA256": s["SHA256"], "SIZE": s["SIZE"]}
                                for s in spreadsheets],
        "BENCHMARK_EXCEL_IDENTITY": ("NOT_ESTABLISHED_WITHOUT_OPENING; "
                                     f"{len(spreadsheets)} spreadsheet candidates, all sealed"),
        "REQUIRED_DOCUMENT_TYPES": required,
        "SOURCE_NOT_PROVIDED": sorted(t for t, r in required.items()
                                      if r["STATUS"] == "SOURCE_NOT_PROVIDED"),
        "POLICY": ("present documents are registered by hash; absent ones are "
                   "SOURCE_NOT_PROVIDED and nothing is assumed in their place"),
    }
    p = Path(P.OUT_DIR) / "SOURCE_INVENTORY.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"SOURCE_INVENTORY_SHA256": _sha(p),
            "SOURCE_NOT_PROVIDED": body["SOURCE_NOT_PROVIDED"],
            "SPREADSHEETS_SEALED": len(spreadsheets),
            "UPLOADS": len(uploads)}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
