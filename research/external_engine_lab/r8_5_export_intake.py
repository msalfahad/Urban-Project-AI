"""Independent-export intake (R8.5 follow-up): admission + measured verification of every supplied DXF.

Writes tests/r8_5/registers/R8_INDEPENDENT_EXPORT_INTAKE.json (committed record). Files are read, hashed and
never modified, repaired or normalised. A DIAGNOSTIC_NONQUALIFYING_CONVERSION is never used to qualify.

    python3 research/external_engine_lab/r8_5_export_intake.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import ezdxf

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

from engine.source import independent_export as IX                        # noqa: E402
from engine.source.cad import libredwg_map as L                             # noqa: E402
from r8_4_qualification import load                                         # noqa: E402

U = Path("/root/.claude/uploads/93607c01-16a4-590f-af7c-1c2701c3b240")
OUT = ROOT / "tests/r8_5/registers/R8_INDEPENDENT_EXPORT_INTAKE.json"
P7757_SHA = "7f61f3acdd62d62dc745f8b522f8136cb41c575df36ec6d9f27c2fe48fea41e3"
ST7757_SHA = "3f7a556c69786834c16c355504437b5abcd1f5aa3a9625b33a2c5b14213f0227"
RECEIVED = [  # (file, role, source dwg sha, declared provenance as stated by the owner)
    ("cfff361a-P77573.dxf", "ARCHITECTURAL", P7757_SHA,
     {"tool": "AI_CONVERSION (undocumented DWG reader, written with ezdxf)", "tool_version": None,
      "requested_format": None, "exported_from_sha256": P7757_SHA,
      "operations": None, "exported_by": "owner-supplied; converted by an AI tool, not AutoCAD",
      "owner_statement": "kept units in millimetres, matched source CAD version, validated with no audit errors, "
                         "DIMENSION entities kept editable"}),
    ("9ce6e188-ST77573.dxf", "STRUCTURAL", ST7757_SHA,
     {"tool": "AI_CONVERSION (undocumented DWG reader, written with ezdxf)", "tool_version": None,
      "requested_format": None, "exported_from_sha256": ST7757_SHA, "operations": None,
      "exported_by": "owner-supplied; converted by an AI tool, not AutoCAD"}),
]
SOURCES = [("b5a96463-P77572.dwg", "ARCHITECTURAL_SOURCE", P7757_SHA), ("1926bdd8-ST77572.dwg", "STRUCTURAL_SOURCE", ST7757_SHA),
           ("73763f3d-p7757_part_1_pages_1-6.pdf", "SUPPORTING_VISUAL_EVIDENCE", None),
           ("4028d553-p7757_part_2_pages_7-12.pdf", "SUPPORTING_VISUAL_EVIDENCE", None),
           ("cbbbed0b-sanitary-7757.pdf", "SUPPORTING_VISUAL_EVIDENCE", None),
           ("811667aa-ST7757.pdf", "SUPPORTING_VISUAL_EVIDENCE", None)]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def d1_view(decode):
    doc = L.to_document(decode)
    raw = {str(L.handle_id(o.get("handle"))): o for o in decode["OBJECTS"] if isinstance(o.get("handle"), list)}
    ents = []
    for o in doc.entities:
        r = raw.get(str(o.source_handle)) or {}
        h = str(o.source_handle).split("+")[0]
        ents.append({"handle": format(int(h), "X") if h.isdigit() else h, "type": r.get("entity") or o.kind,
                     "layer": o.layer, "space": "MODEL"})
    blocks = {b.name: len(b.entities) for b in doc.blocks.values() if b.name}
    used = {o.get("type") for o in decode["OBJECTS"] if isinstance(o.get("type"), int) and o["type"] >= 500}
    classes = sorted({c["dxfname"] for c in decode.get("CLASSES", []) if c.get("number") in used and c.get("dxfname")})
    return ents, blocks, classes


def dxf_view(x):
    ents = [{"handle": e.dxf.handle, "type": e.dxftype(), "layer": e.dxf.layer, "space": "MODEL"} for e in x.modelspace()]
    blocks = {b.name: len(b) for b in x.blocks if not b.name.lower().startswith(("*model_space", "*paper_space"))}
    classes = sorted({c.dxf.name for c in x.classes})
    return ents, blocks, classes


def main():
    rec = {"SCHEMA": "URBAN_R8_INDEPENDENT_EXPORT_INTAKE_V1",
           "INDEPENDENT_REAL_RECONCILIATION": "BLOCKED_EXTERNAL_INPUT",
           "requirements_for_the_real_route": {
               "tool": list(IX.INDEPENDENT_TOOLS),
               "exported_from_sha256": P7757_SHA,
               "forbidden_operations": list(IX.FORBIDDEN_OPERATIONS),
               "autocad_2018_dxf_requires": IX.ACADVER["AUTOCAD_2018_DXF"],
               "verification_before_qualification": list(IX.DOMAINS),
               "oda_note": "ODA is parser-independent but is NOT assumed to preserve source handles: handle identity, "
                           "entity census, block lineage, custom classes and geometry are verified from the file"},
           "sources": [], "exports": []}
    for f, role, expect in SOURCES:
        p = U / f
        h = sha(p)
        rec["sources"].append({"file": f, "role": role, "sha256": h, "bytes": p.stat().st_size,
                               "matches_expected_sha256": (h == expect) if expect else None,
                               "use": "primary source" if role == "ARCHITECTURAL_SOURCE" else
                               "corroborating structural evidence only" if role == "STRUCTURAL_SOURCE" else
                               "supporting visual / document evidence only; never a substitute for the CAD parser route"})
    d1 = d1_view(load("data/runs/cad_convert/P7757_ARCHITECTURAL.json"))
    for f, role, src, declared in RECEIVED:
        p = U / f
        x = ezdxf.readfile(str(p))
        header = {k: x.header.get(k) for k in ("$ACADVER", "$LASTSAVEDBY", "$INSUNITS", "$HANDSEED")}
        adm = IX.admission(sha(p), header, None, declared, src)
        entry = {"file": f, "role": role, "bytes": p.stat().st_size, "header": header, "admission": adm,
                 "classification": adm["status"], "modified": False, "repaired": False, "normalised": False}
        if role == "ARCHITECTURAL":
            ents, blocks, classes = dxf_view(x)
            ver = IX.verify(d1[0], ents, d1[1], blocks, d1[2], classes)
            entry["diagnostic_verification_against_D1"] = ver
            entry["diagnostic_counts"] = {"d1_model_entities": len(d1[0]), "dxf_model_entities": len(ents),
                                          "dxf_model_types": dict(Counter(e["type"] for e in ents).most_common(12))}
        rec["exports"].append(entry)
        print(f, adm["status"], [r[:70] for r in adm["reasons"]])
        if role == "ARCHITECTURAL":
            print({k: v["verdict"] for k, v in ver.items() if isinstance(v, dict)})
    OUT.write_text(json.dumps(rec, indent=1, ensure_ascii=False, default=str) + "\n")


if __name__ == "__main__":
    main()
