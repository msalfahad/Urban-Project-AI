"""OWNER_DECISION_QUEUE, REVISION/SUPERSESSION ledger, SOURCE_COVERAGE and the
benchmark leakage guard (directive §22, §23, §24, §28).

    python3 -m research.qs_wall_treatment_01.decision_queue_v4
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from engine import benchmark_protection as BP
from engine import owner_decision_queue as ODQ
from engine import supersession_ledger as SL
from research.qs_wall_treatment_01 import protocol as P

OUT = Path(P.OUT_DIR)
UPLOADS = Path("/root/.claude/uploads/93607c01-16a4-590f-af7c-1c2701c3b240")
GEOMETRY_ARTIFACTS = ["ROOF_EDGE_PLAN_TO_ELEVATION_LINK_REGISTER.json", "STRUCTURAL_SOURCE_CHECK.json",
                      "PARAPET_ASSEMBLY_REGISTER.json", "FACE_MEASUREMENT_REGISTER.json",
                      "QS_MEASUREMENT_REGION_REGISTER.json", "OPENING_REGISTER_v4.json", "PLASTER_QUANTITY_TRACE.json"]
# figures that exist only in the contractor record (site record); none may appear in a geometry artifact
BENCHMARK_FIGURES = (1151.1375, 1469.9675, 82.399, 48.47, 96.94, 12.9, 116.495, 58.2475, 19.88, 25.34, 19.04, 113.76, 69.0)


def _num_scan(obj, hits, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            _num_scan(v, hits, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _num_scan(v, hits, f"{path}[{i}]")
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        for b in BENCHMARK_FIGURES:
            if abs(float(obj) - b) < 1e-6:
                hits.append({"AT": path, "VALUE": obj})


def run() -> dict:
    asm = json.loads((OUT / "PARAPET_ASSEMBLY_REGISTER.json").read_text("utf-8"))
    tr = json.loads((OUT / "PLASTER_QUANTITY_TRACE.json").read_text("utf-8"))
    st = json.loads((OUT / "STRUCTURAL_SOURCE_CHECK.json").read_text("utf-8"))
    d1 = asm["D1"]
    ne_ref = next((u.get("REFERENCE_GROSS_M2_IF_ELIGIBLE") for u in tr["UNRESOLVED_SCOPE"] if u.get("FACE_ID") == "F-NE-SOLID-EXT"), None)
    Q = []
    Q.append(ODQ.item(DECISION_ID="D1-SE-ROOFSIDE-BOTTOM", LOCATION="roof +9.70, SE edge, solid portion, roof-side face", TRADE="ROOF_SIDE_PARAPET plaster",
                      QUESTION="Is the roof-side plaster face measured from the structural slab (+9.70) or from the drawn finish level line (+9.88)?",
                      WHY_SOURCE_HIERARCHY_FAILED=d1["EXACT_MISSING_RELATIONSHIP"],
                      AVAILABLE_EVIDENCE=["DIM-21 +11.10 top", "LVL +9.70 slab", "base line +9.88 on raster and DWG elevation", "no section through the solid portion"],
                      OPTION_A="physical face from the slab: 1.40 m (technical default; plaster precedes roof finishes)",
                      OPTION_B="from the finish level line: 1.22 m", OPTION_C_IF_REQUIRED=None,
                      QUANTITY_IMPACT_IF_KNOWN={"m2": d1["QUANTITY_IMPACT_M2"]["ROOF_SIDE_A_MINUS_B"], "per_metre_run": d1["QUANTITY_IMPACT_M2"]["PER_METRE_RUN"]},
                      BLOCKS_WHAT="nothing: the line is carried as PROVISIONAL on option A", CAN_OTHER_WORK_CONTINUE=True,
                      VISUAL_CARD="decision_cards/D1_SE_PARAPET_SOURCE_CARD.png + visual_qa/SE_ELEVATION_FACES.png",
                      PRIORITY="QUANTITY_AFFECTING_SMALL", TECHNICAL_RECOMMENDATION="A"))
    Q.append(ODQ.item(DECISION_ID="D3-BENCHMARK-IDENTITY", LOCATION="contractor workbook (uploads b324a3e7 / c495ff6e)", TRADE="reconciliation only",
                      QUESTION="Is the contractor statement of executed plaster works (invoice No. 5) the P7757 site record?",
                      WHY_SOURCE_HIERARCHY_FAILED="no project identifier inside the workbook; consistent evidence only (rooms, levels, 12.90 stair well)",
                      AVAILABLE_EVIDENCE=["BENCHMARK_RECONCILIATION.json", "DUAL_BASIS_v3.json BENCHMARK_IDENTITY"],
                      OPTION_A="confirm identity -> reconciliation outputs become unconditional", OPTION_B="deny -> reconciliation withdrawn, geometry unaffected",
                      OPTION_C_IF_REQUIRED=None, QUANTITY_IMPACT_IF_KNOWN="none on engineering geometry", BLOCKS_WHAT="unconditional A22 only",
                      CAN_OTHER_WORK_CONTINUE=True, VISUAL_CARD="decision_cards (none: identity question)", PRIORITY="CLASSIFICATION_ONLY"))
    Q.append(ODQ.item(DECISION_ID="NE-PARAPET-EXTERNAL-FINISH", LOCATION="roof +9.70, NE (neighbour) edge parapet, outer face, 18.27 m", TRADE="SOLID_PARAPET external plaster",
                      QUESTION="Is the neighbour-facing outer face of the NE parapet plastered (boundary condition)?",
                      WHY_SOURCE_HIERARCHY_FAILED="no elevation shows the neighbour side; finishes specification SOURCE_NOT_PROVIDED",
                      AVAILABLE_EVIDENCE=["A-A hatched cut PAR-07 1.65 m above the slab", "DWG outer line 18.27 m"],
                      OPTION_A="plastered like the roof side", OPTION_B="not finished (party/boundary condition)", OPTION_C_IF_REQUIRED="rendered by another trade",
                      QUANTITY_IMPACT_IF_KNOWN={"m2_if_eligible": ne_ref}, BLOCKS_WHAT="one external parapet line", CAN_OTHER_WORK_CONTINUE=True,
                      VISUAL_CARD="visual_qa/ROOF_PLAN_EDGES.png", PRIORITY="QUANTITY_AFFECTING_SMALL"))
    Q.append(ODQ.item(DECISION_ID="EXTERNAL-FINISH-SYSTEM", LOCATION="all external faces (facades, parapet outer skins UNK-05)", TRADE="EXTERNAL_FACADE plaster",
                      QUESTION="Are the external faces plastered, or clad (stone / GRC / other) over the outer skin drawn on B-B (UNK-05)?",
                      WHY_SOURCE_HIERARCHY_FAILED="FINISHES_SPECIFICATION is SOURCE_NOT_PROVIDED; B-B draws an un-hatched 10 cm outer layer",
                      AVAILABLE_EVIDENCE=["UNK-05 on B-B", "SE facade gross 40.5 m2 (openings untraced)"],
                      OPTION_A="plaster (external plaster category applies)", OPTION_B="cladding over plaster base (base coat only)", OPTION_C_IF_REQUIRED="cladding without plaster",
                      QUANTITY_IMPACT_IF_KNOWN="whole EXTERNAL_FACADE category (not yet measured net)", BLOCKS_WHAT="EXTERNAL_FACADE net lines", CAN_OTHER_WORK_CONTINUE=True,
                      VISUAL_CARD="decision_cards/D1_SE_PARAPET_SOURCE_CARD.png (B-B inset)", PRIORITY="CLASSIFICATION_ONLY"))
    Q.append(ODQ.item(DECISION_ID="NW-THIN-EDGE-ELEMENT", LOCATION="roof +9.70, NW (sea-view) edge, 10 cm x 1.30 element (UNK-04, DIM-06/07)", TRADE="ROOF parapet",
                      QUESTION="What is the 10 cm thick, 1.30 m high sea-view roof-edge element: RC upstand, glass screen, metal screen?",
                      WHY_SOURCE_HIERARCHY_FAILED="drawn dashed / thin on the plan, un-hatched on B-B; no material note",
                      AVAILABLE_EVIDENCE=["UNK-04 plan", "DIM-07 130 on B-B (OWNER_PROVISIONAL)", "structural note: parapet per architectural detail"],
                      OPTION_A="solid RC/masonry upstand (plasterable both faces)", OPTION_B="glass / metal screen (zero plaster)", OPTION_C_IF_REQUIRED=None,
                      QUANTITY_IMPACT_IF_KNOWN="NOT_ESTABLISHED (length not yet measured from the DWG)", BLOCKS_WHAT="one roof-edge line", CAN_OTHER_WORK_CONTINUE=True,
                      VISUAL_CARD="visual_qa/ROOF_PLAN_EDGES.png", PRIORITY="QUANTITY_AFFECTING_SMALL"))
    Q.append(ODQ.item(DECISION_ID="SW-PARAPET-HEIGHT", LOCATION="roof +9.70, SW edge parapet 4.33 m (PAR-02)", TRADE="ROOF_SIDE_PARAPET plaster",
                      QUESTION="Height of the SW-edge parapet (no section cuts it; no elevation dimension)?",
                      WHY_SOURCE_HIERARCHY_FAILED="no source; continuity with the SE solid parapet is not proven (the SE corner is the lattice/kerb end)",
                      AVAILABLE_EVIDENCE=["DWG lines 4.325 / 4.125", "DIM-05 thickness 20"],
                      OPTION_A="site measurement supplied by the owner", OPTION_B="adopt the NE parapet height 1.65 by drawing convention (PROVISIONAL)",
                      OPTION_C_IF_REQUIRED="leave NOT_ESTABLISHED", QUANTITY_IMPACT_IF_KNOWN="4.13 lm x height (roof side)", BLOCKS_WHAT="one parapet line",
                      CAN_OTHER_WORK_CONTINUE=True, VISUAL_CARD="visual_qa/ROOF_PLAN_EDGES.png", PRIORITY="QUANTITY_AFFECTING_SMALL"))
    gate = ODQ.stop_gate(Q)
    technical = [{"ID": "T-DOUBLE-HEIGHT", "WHAT": "trace the RECEPTION double-height wall on A-A/B-B and set DOUBLE_HEIGHT_PLASTER_HEIGHT from the section", "OWNER": False},
                 {"ID": "T-STAIR-WELL", "WHAT": "component-based stair-well faces from the sections (never the 12.90 site record)", "OWNER": False},
                 {"ID": "T-COLUMN-GIRTH", "WHAT": "resolve 1.80 (structural 30x60) vs 1.70 (architectural 25x60 loop) for LOOP-059", "OWNER": False},
                 {"ID": "T-SE-FACADE-OPENINGS", "WHAT": "trace the arched windows below the SE parapet to net the 40.5 m2 gross", "OWNER": False},
                 {"ID": "T-KERB-PROFILE", "WHAT": "author the kerb ogee profile from the native elevation (now a raster polygon, PROVISIONAL)", "OWNER": False},
                 {"ID": "T-ROOF-PLAN-REGISTRATION", "WHAT": "register the roof-plan raster sheet to the DWG with declared pairs (now proportional, QA only)", "OWNER": False},
                 {"ID": "T-ST7757-DWG", "WHAT": "decode ST7757.dwg when a LibreDWG build is reachable", "OWNER": False}]
    # ---- supersession ledger ----------------------------------------------
    L = []
    def led(i, prev, art, mark, by, ev):
        L.append(SL.entry(ledger_id=i, previous_statement=prev, previous_artifact=art, mark=mark, replaced_by=by, evidence=ev, date="2026-09-19"))
    led("L-01", "D1 quantity impact 1.22 x 7.10 = 8.66 / 1.42 x 7.10 = 10.08 m2", "DECISION_CARDS.json / OWNER_REVIEW_V2.md", "WITHDRAWN",
        "assembly faces F-SE-SOLID-* on the solid portion only", "SE_ELEVATION_SOURCE_AUDIT.json D1.OLD_QUANTITY_IMPACT_WITHDRAWN")
    led("L-02", "SE parapet solid portion length NOT_ESTABLISHED", "SE_ELEVATION_SOURCE_AUDIT.json D1.RESIDUAL.LENGTH_STATUS", "SUPERSEDED",
        "3.683 m outer / 3.483 m roof-side from the DWG roof copy (PROPOSED split at CAD-4808)", "ROOF_EDGE_PLAN_TO_ELEVATION_LINK_REGISTER.json")
    led("L-03", "E1.4 LOOP-059: NOT_EXPOSED_TO_ROOM", "E1.4 COLUMN_EXISTENCE register (frozen)", "SUPERSEDED_IN_PART",
        "COLUMN_EXPOSED_TO_ROOM ESTABLISHED_PROVISIONAL (free-standing, beams not walls); the 'does not own the clear face' part stands",
        "STRUCTURAL_SOURCE_CHECK.json D2")
    led("L-04", "D2: EDGE_LEVEL_LINE / structural outline: no plasterable face", "SE_ELEVATION_SOURCE_AUDIT.json D2", "SUPERSEDED",
        "D2 RESOLVED_PROVISIONAL_BY_STRUCTURAL_SOURCE: exposed 30x60 column, girth 1.80 lm, column bonding line PROVISIONAL", "STRUCTURAL_SOURCE_CHECK.json D2")
    led("L-05", "ROOF-SE-PARAPET-CAPPING: PAR-13 7.10 x 0.20 = 1.42 m2 PROVISIONAL", "P7757_WALL_TREATMENT_ESTIMATE_v3.json (frozen)", "SUPERSEDED",
        "coping faces over the solid portion only (F-SE-CAP-TOP 0.7367 + edges); the rail over the lattice is a HANDRAIL (zero)", "PARAPET_ASSEMBLY_REGISTER.json")
    led("L-06", "D1 OWNER_DECISION_REQUIRED: choose 1.40 / 1.22 / 1.10", "OWNER_REVIEW_V4.md D1 card", "SUPERSEDED",
        "D1 REDUCED_TO_A_FACE_BOTTOM_CONVENTION, technical default A, queued non-blocking (0.63 m2)", "PARAPET_ASSEMBLY_REGISTER.json D1")
    led("L-07", "tower parapet ring length NOT_ESTABLISHED (no roof plan at +13.90)", "SE_ELEVATION_SOURCE_AUDIT.json material audit", "SUPERSEDED",
        "29.794 m exterior ring from ST7757.pdf p6 (+13.90 slab outline), PROVISIONAL / PROPOSED_CORRESPONDENCE", "STRUCTURAL_SOURCE_CHECK.json TOWER_ROOF_13_90_OUTLINE_p6")
    frozen_ok = {}
    for fz in ("FREEZE_ESTIMATE", "FREEZE_A22", "FREEZE_FINAL", "FREEZE_DUAL", "FREEZE_OWNER_EVIDENCE", "FREEZE_SE_AUDIT"):
        fp = OUT / f"{fz}.json"
        if not fp.exists():
            continue
        rec = json.loads(fp.read_text("utf-8"))
        cur = {a: (hashlib.sha256((OUT / a).read_bytes()).hexdigest() if (OUT / a).exists() else None) for a in rec["ARTIFACT_SHA256"]}
        frozen_ok[fz] = SL.assert_frozen_unchanged(rec, cur)
    # ---- source coverage -----------------------------------------------------
    cov = {"ARCHITECTURAL_PDF_PAGES": {"1 GROUND_FLOOR_PLAN": "traced (SALOON, D2 location)", "2 FIRST_FLOOR_PLAN": "traced (stair) - not used this phase",
                                       "3 SECOND_FLOOR_ROOF_PLAN": "traced; QA overlay", "4 SOUTH_EAST_ELEVATION": "native audit + faces overlay",
                                       "6 NORTH_WEST_ELEVATION": "traced - not used", "7 NORTH_EAST_ELEVATION": "traced - not used",
                                       "8 SECTION_A_A": "PAR-07/08/09 heights + ring thickness", "9 SECTION_B_B": "kerb 0.54, cap, outer skin",
                                       "5, 10": "not in the frozen register"},
           "DWG_P7757_ARCHITECTURAL": {"GF plan copy": "column loops (30) for the structural registration", "ROOF plan copy": "SE edge lines, domes, NE/SW edges",
                                       "ELEVATION blob": "level chain, base line corroboration (mirrored, different annotation revision)", "FF plan copy": "not used"},
           "ST7757_PDF_16_SHEETS": {"p1 COLUMN & AXIS": "registered (30 inliers, <=55 mm)", "p3 GROUND BEAMS": "D2 beam", "p4 GF ROOF SLAB": "D2 ceiling beam",
                                    "p5 FIRST FLOOR ROOF SLAB": "SE edge 7.497 m, ticks, SECTION B-B upstand", "p6 SECOND FLOOR ROOF SLAB": "+13.90 outline 29.794 m",
                                    "p2, p7-p16": "not used (foundations, details, schedules)"},
           "NOT_READABLE": {"ST7757.dwg": "PRESENT_NOT_DECODED (no LibreDWG; GitHub blocked)", "DWF packages": "no reader"},
           "NOT_USED": {"sanitary PDF (4a9be682)": "not relevant to plaster", "upload images": "not classified", "spreadsheets other than the benchmark": "sealed"},
           "CATEGORY_COVERAGE": {c: v["COVERAGE_STATUS"] for c, v in tr["BY_CATEGORY"].items()}}
    # ---- leakage guard ----------------------------------------------------------
    leaks = {}
    for a in GEOMETRY_ARTIFACTS:
        obj = json.loads((OUT / a).read_text("utf-8"))
        hits = []
        _num_scan(obj, hits)
        leaks[a] = {"BENCHMARK_KEY_OR_PHRASE_HITS": BP.scan(obj), "BENCHMARK_FIGURE_HITS": hits}
    clean = all(not v["BENCHMARK_FIGURE_HITS"] for v in leaks.values())
    out = {"PHASE_ID": P.PHASE_ID, "ARTIFACT": "OWNER_DECISION_QUEUE", "QUEUE": Q, "STOP_GATE": gate, "TECHNICAL_FOLLOW_UPS_NOT_OWNER": technical,
           "PRODUCTION_BOUNDARY": ["no BOQ pricing", "no project total", "no Firebase write", "no Manager Agent write", "no procurement quantities",
                                   "no P7757-specific interpretation promoted to an Urban-wide rule"]}
    (OUT / "OWNER_DECISION_QUEUE.json").write_text(json.dumps(out, indent=2, default=str) + "\n", encoding="utf-8")
    ledger = {"PHASE_ID": P.PHASE_ID, "ARTIFACT": "REVISION_SUPERSESSION_LEDGER", "ENTRIES": L, "FROZEN_ARTIFACTS_UNCHANGED": frozen_ok}
    (OUT / "REVISION_SUPERSESSION_LEDGER.json").write_text(json.dumps(ledger, indent=2, default=str) + "\n", encoding="utf-8")
    (OUT / "SOURCE_COVERAGE.json").write_text(json.dumps({"PHASE_ID": P.PHASE_ID, "ARTIFACT": "SOURCE_COVERAGE", **cov}, indent=2) + "\n", encoding="utf-8")
    lg = {"PHASE_ID": P.PHASE_ID, "ARTIFACT": "BENCHMARK_LEAKAGE_GUARD", "SCANNED": leaks, "GEOMETRY_ARTIFACTS_CLEAN": clean,
          "RULE": "benchmark figures may appear only in DUAL_BASIS / A22 / BENCHMARK_* artifacts"}
    (OUT / "BENCHMARK_LEAKAGE_GUARD.json").write_text(json.dumps(lg, indent=2, default=str) + "\n", encoding="utf-8")
    return {"QUEUE": [(q["DECISION_ID"], q["PRIORITY"]) for q in Q], "STOP_GATE": gate, "LEDGER": len(L),
            "FROZEN_OK": {k: v["OK"] for k, v in frozen_ok.items()}, "LEAKAGE_CLEAN": clean,
            "KEY_HITS": {a: len(v["BENCHMARK_KEY_OR_PHRASE_HITS"]) for a, v in leaks.items()}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=1, default=str))
