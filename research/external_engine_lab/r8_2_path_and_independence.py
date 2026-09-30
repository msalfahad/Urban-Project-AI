"""R8.2 §3 / §9 / §24 — ACTIVE PATH MAP and DECODER INDEPENDENCE MATRIX (research lab, data only).

Every CURRENT_ACTIVE entry names the runner file and the stack modules it
imports, and a check below verifies those files exist and that the imports
claimed are really in the runner's source, so the map cannot drift silently.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

STACKS = {
    "CAD_ADAPTER": {"modules": ["engine/cad_adapter.py"], "role": "LibreDWG JSON -> NormalizedDrawing primitives (frozen)"},
    "LEGACY_CAD_ROUNDS": {"modules": ["engine/cad_profile.py", "engine/cad_measure.py", "engine/cad_geometry.py",
                                      "engine/cad_regions.py", "engine/cad_openings.py"],
                          "role": "Project-2 rounds 2-6E and E1 geometry (P7757)"},
    "INGEST_PIPELINE7": {"modules": ["engine/ingest/harness.py", "engine/ingest/pipeline7.py"],
                         "role": "generic ingest over cad_adapter primitives (PA05-PA08)"},
    "QS_CORE": {"modules": ["engine/qs_core/pipeline.py", "engine/qs_core/quantities.py"],
                "role": "evidence, admission, publication contract (R5-R7)"},
    "PROJECT_READER_ALRASHED": {"modules": ["research/qs_wall_treatment_01/pa09/alrashed/geometry.py"],
                                "role": "project-specific reader of the LibreDWG JSON; top-level entities only; no block expansion"},
    "PDF_STACK_ALRASHED": {"modules": ["research/qs_wall_treatment_01/pa09/alrashed/labels.py",
                                       "research/qs_wall_treatment_01/pa09/alrashed/final_takeoff.py"],
                           "role": "labels, dimensions and glazed openings read from the issued PDF (pymupdf)"},
    "SOURCE_K1_K2": {"modules": ["engine/source/cad/kernel.py", "engine/source/cad/kernel_ezdxf.py",
                                 "engine/source/reconcile.py", "engine/source/cad/census.py"],
                     "role": "canonical source engine (R8.1-R8.2); SHADOW only, no production consumer"},
    "EXTERNAL_ENGINE_LAB": {"modules": ["research/external_engine_lab/r8_2_shadow_impact.py"],
                            "role": "research, never imported by engine/"},
}

PATHS = [
    {"project": "ALRASHED", "run": "R7 generic-engine validation + frozen FULL_VILLA takeoff (published R7 BOQ basis)",
     "status": "CURRENT_ACTIVE",
     "runner": "research/qs_wall_treatment_01/pa09/alrashed/regression_r7.py",
     "expected_imports": ["engine.qs_core", "research.qs_wall_treatment_01.pa09.alrashed"],
     "chain": ["SOURCE 16-11-2025.dwg + 16-11-2025.pdf",
               "decoder LibreDWG dwgread -> data/runs/cad_convert/ALRASHED_ARCHITECTURAL.json",
               "adapter PROJECT_READER_ALRASHED (geometry.load: entities outside BLOCK..ENDBLK spans; no INSERT expansion)",
               "geometry exact rectilinear grid rooms (geometry.grid / rooms), jamb gaps, INSERT insertion points on DOOR/WIN layers",
               "evidence PDF_STACK_ALRASHED labels + glazed openings; qs_core admission / hosting / masonry identity",
               "publication qs_core quantities -> ALRASHED_DETAILED_QUANTITY_EXPORT (FINAL / BLOCKED rows)"],
     "uses_cad_adapter": False},
    {"project": "QORTUBA", "run": "PA08_QORTUBA_ROOM_BY_ROOM_QS_01 (published room-by-room takeoff)",
     "status": "CURRENT_ACTIVE",
     "runner": "research/qs_wall_treatment_01/pa08/qortuba/qs01/takeoff.py",
     "expected_imports": ["engine.ingest", "research.qs_wall_treatment_01.pa08.qortuba"],
     "chain": ["SOURCE Qortuba DWG (not in this environment)",
               "decoder LibreDWG dwgread -> data/runs/cad_convert/QORTUBA_ARCHITECTURAL.json",
               "adapter CAD_ADAPTER (engine/ingest/harness.py calls cad_adapter.normalize)",
               "geometry INGEST_PIPELINE7 bands / faces / spaces / measurement regions",
               "evidence pipeline7 semantic attachment + qs01 room inventory",
               "publication qs01 floor / skirting / block-wall / blue-element / ceiling rows"],
     "uses_cad_adapter": True},
    {"project": "P7757", "run": "PA07 supervised regression", "status": "CURRENT_ACTIVE (regression; releases no quantity: BRIDGE_ALLOWED = 0)",
     "runner": "research/qs_wall_treatment_01/pa07/run.py",
     "expected_imports": ["engine.ingest"],
     "chain": ["SOURCE data/golden/7757/source_c/P7757_ARCHITECTURAL.dwg",
               "decoder LibreDWG dwgread -> data/runs/cad_convert/P7757_ARCHITECTURAL.json",
               "adapter CAD_ADAPTER", "geometry INGEST_PIPELINE7",
               "evidence pipeline7 quantity safety gates", "publication NONE (every quantity line blocked by a gate)"],
     "uses_cad_adapter": True},
    {"project": "P7757", "run": "WT01 / PA01-PA02 wall-treatment estimate", "status": "LEGACY",
     "runner": "research/qs_wall_treatment_01/cad_links.py", "expected_imports": ["engine.cad_adapter"],
     "chain": ["decoder LibreDWG JSON", "adapter CAD_ADAPTER", "geometry E1.4 registers + research modules",
               "publication research estimate (frozen)"], "uses_cad_adapter": True},
    {"project": "P7757", "run": "Project-2 rounds 2-6E, E1-E1.4", "status": "LEGACY",
     "runner": "tools/run_round6e.py", "expected_imports": ["engine.cad_adapter"],
     "chain": ["decoder LibreDWG JSON", "adapter CAD_ADAPTER", "geometry LEGACY_CAD_ROUNDS", "publication frozen round exports"],
     "uses_cad_adapter": True},
    {"project": "ALL", "run": "R8 source engine (K1 D1 / K2 D2 / reconcile / census)", "status": "TARGET_CANONICAL (SHADOW)",
     "runner": "research/external_engine_lab/r8_2_shadow_impact.py", "expected_imports": ["engine.source"],
     "chain": ["decoder D1 LibreDWG JSON / D2 DXF", "adapter engine/source/cad/libredwg_map.py, kernel_ezdxf.py",
               "geometry K1 / K2", "reconciliation engine/source/reconcile.py", "publication NONE (shadow)"],
     "uses_cad_adapter": False},
    {"project": "ALL", "run": "tests/r8_0, tests/r8_1, tests/r8_2", "status": "TEST_ONLY", "runner": "tests/r8_2/test_r8_2_reconcile.py",
     "expected_imports": ["engine.source"], "chain": [], "uses_cad_adapter": True},
]

INDEPENDENCE = {
    "D1_K1": {"route": "D1_LIBREDWG_JSON", "source_bytes": "DWG", "parser_lineage": "LIBREDWG 0.13.3 dwgread",
              "conversion_chain": ["DWG", "dwgread -O JSON"], "representation_mapper": "engine/source/cad/libredwg_map.py",
              "transform_kernel_lineage": "URBAN_K1 (kernel.py + kernel_ocs.py + affine.py)",
              "decoder_pin": "dwgread sha256 fe49cf28... REGISTERED; the real decodes pre-date this session: NOT_ESTABLISHED"},
    "D2_K2": {"route": "D2_DXF_EZDXF", "source_bytes": "DXF", "parser_lineage": "EZDXF 1.4.4 DXF reader (for the DXF text); "
              "the DXF itself is produced by whatever exported it", "conversion_chain": ["DWG", "<exporter> -> DXF", "ezdxf.readfile"],
              "representation_mapper": "engine/source/cad/kernel_ezdxf.py",
              "transform_kernel_lineage": "EZDXF (Insert.matrix44, multi_insert, entity.transform, OCS, bulge_to_arc)",
              "decoder_pin": "ezdxf package 1.4.4 REGISTERED (package identity)"},
    "CAD_ADAPTER": {"route": "LEGACY", "source_bytes": "DWG", "parser_lineage": "LIBREDWG 0.13.3 dwgread",
                    "transform_kernel_lineage": "cad_adapter Transform2D", "decoder_pin": "none"},
}

FAILURE_DOMAINS = [
    # domain, D1/K1 vs D2/K2 independence, why
    ("DWG byte parsing", "NOT_INDEPENDENT when the DXF is exported by LibreDWG dwg2dxf (shared parser); INDEPENDENT only with an AutoCAD / ODA export",
     "both representations originate in the same parser"),
    ("Handle identity (3-byte truncation)", "INDEPENDENT with a non-LibreDWG DXF; the truncation is in LibreDWG's JSON writer, DXF handles are hex text",
     "D1 identity = (byte size, value); D2 identity = full hex handle"),
    ("Field mapping (which key means what)", "INDEPENDENT", "libredwg_map vs ezdxf's own DXF group-code parser"),
    ("OCS / Arbitrary Axis", "INDEPENDENT", "K1 clean Urban AAA vs ezdxf.math.OCS"),
    ("Block placement / composition", "INDEPENDENT", "K1 composed Affine2 vs ezdxf Insert.matrix44 + entity.transform"),
    ("Curve orientation under reflection", "INDEPENDENT", "K1 sign(det(full)) + point cross-check vs K2 extrusion sign after ezdxf re-encodes the entity"),
    ("Bulge arcs", "INDEPENDENT", "K1 chord/sagitta construction vs ezdxf.math.bulge_to_arc"),
    ("Non-uniform scale", "INDEPENDENT", "K1 affine image of the circle vs ezdxf Ellipse.from_arc + transform"),
    ("MINSERT grid", "INDEPENDENT but K2 has EZDXF-L01/L02", "K1 rotated offsets vs ezdxf multi_insert (spacing not transformed under reflection)"),
    ("XREF", "NOT_EXERCISED: neither route resolves xrefs", "both report findings; zero children is never proof"),
    ("Visibility", "INDEPENDENT", "D1 'invisible' key vs DXF group 60"),
    ("Units", "NOT_INDEPENDENT: both carry INSUNITS raw; neither applies it", "UNIT_CONTEXT is R8.3"),
    ("Reconciliation arithmetic", "SHARED (one engine/source/reconcile.py)", "a comparison contract, not a route"),
    ("Realised output schema", "SHARED (engine/source/realised.py)", "records only; no placement code"),
]


def verify():
    problems = []
    for s, v in STACKS.items():
        for m in v["modules"]:
            if not (ROOT / m).exists():
                problems.append(f"stack {s}: missing {m}")
    for p in PATHS:
        src = (ROOT / p["runner"]).read_text() if (ROOT / p["runner"]).exists() else ""
        if not src:
            problems.append(f"runner missing {p['runner']}")
        for imp in p["expected_imports"]:
            pkg, _, leaf = imp.rpartition(".")
            spelled = [rf"(from|import)\s+{re.escape(imp)}\b"] + ([rf"from\s+{re.escape(pkg)}\s+import\s+[^\n]*\b{re.escape(leaf)}\b"] if pkg else [])
            if not any(re.search(x, src) for x in spelled):
                problems.append(f"{p['runner']}: does not import {imp}")
        if "uses_cad_adapter" in p and p["status"].startswith("CURRENT_ACTIVE") and p["project"] != "ALL":
            chain_uses = any("CAD_ADAPTER" in c for c in p["chain"])
            if chain_uses != p["uses_cad_adapter"]:
                problems.append(f"{p['runner']}: chain/cad_adapter flag disagree")
    # Al Rashed: the project reader must not import cad_adapter (else the map is wrong)
    ar = (ROOT / "research/qs_wall_treatment_01/pa09/alrashed").rglob("*.py")
    if any("cad_adapter" in f.read_text() for f in ar):
        problems.append("an Al Rashed pa09 module imports cad_adapter: the ALRASHED path claim is wrong")
    h = (ROOT / "engine/ingest/harness.py").read_text()
    if "CA.normalize(" not in h:
        problems.append("engine/ingest/harness.py no longer calls cad_adapter.normalize")
    return problems


def build():
    return {"ACTIVE_PATH_MAP": {"SCHEMA": "URBAN_R8_2_ACTIVE_PATH_MAP_V1", "stacks": STACKS, "paths": PATHS,
                                "verification_problems": verify(),
                                "note": "'the engine' is not one path: four stacks are live or frozen; only the rows marked "
                                        "CURRENT_ACTIVE feed an output today"},
            "DECODER_INDEPENDENCE_MATRIX": {"SCHEMA": "URBAN_R8_2_DECODER_INDEPENDENCE_V1", "routes": INDEPENDENCE,
                                            "failure_domains": [{"domain": d, "independence": i, "why": w} for d, i, w in FAILURE_DOMAINS],
                                            "rule": "never call two routes independent without naming the failure domain"}}


if __name__ == "__main__":
    print(json.dumps(build(), indent=1))
