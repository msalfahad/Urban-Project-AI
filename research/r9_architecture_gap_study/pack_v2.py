"""R9 gap study v2 - evidence from the delivered research pack and the donor repositories it names.

Pack: Urban_BOQ_Research_Pack_2026-10-07.zip (sha256 below), read in full (15 docs, 3 clean-room reference files, 5
machine-readable files). RoomGraph, aec-platform/qto and Rebar-Takeoff were checked at a pinned commit by a blob-less,
no-checkout git fetch: LICENSE, README, docs and the dependency manifest were READ; no source file was copied or run,
nothing was installed. Other pack-only donors (cad-ai-agent, ConMCP, tianzheng-dwg-parse, FreeCAD-Reinforcement,
Plansight ...) were NOT fetched: their rows say PACK_CLAIM_ONLY.

v1 rows stay as written; OVERRIDES replace fields the pack / verification changed (each changed row lists them in
CHANGED_BY_PACK), PACK_ROWS add recommendations v1 did not cover.
"""

from __future__ import annotations

PACK_SHA256 = "166a7341ebd9dc2d258d1c97e422ec67880782d86303c89cf76111d82d9e5331"
PACK_FILES = 23

VERIFIED = {
    "ROOMGRAPH": {"repo": "aec-platform/roomgraph", "commit": "772f0954a33d7930c5a9c5e3a48335831cc06ba7",
                  "commit_date": "2026-08-10", "licence_file": "MIT (Copyright (c) 2026 Nguyen Thu Thuy)",
                  "pack_says": "MIT", "licence_verified": True, "runtime_dependencies": "none (stdlib only)",
                  "features_confirmed": ["vector-PDF content-stream reader (own lexer)", "scale: dimension strings > "
                                         "title block > door widths, with confidence; --scale exact",
                                         "line clustering -> face pairing 60-420 mm", "corner repair: bridged "
                                         "length becomes a bridged opening (provenance kept)",
                                         "planar arrangement: split at crossings / T, half-edge minimal cycles",
                                         "symbol library (doors, windows, curtain wall, stairs, sanitary ...)",
                                         "room adjacency + walkability graph", "--strict fails on uncertainty",
                                         "printed room area vs measured (> 3 % warns); scale bar / dimension "
                                         "chain / door schedule as independent witnesses"],
                  "limitations_confirmed": ["scans out of scope", "single-line walls unsupported",
                                            "walls > 420 mm unsupported", "CURVED WALLS UNSUPPORTED (clustered as "
                                            "short lines, do not pair)", "door drawn over a continuous wall not "
                                            "found; accidental drafting gap reported as an opening",
                                            "scale inferred; error enters areas squared"]},
    "AEC_QTO": {"repo": "aec-platform/qto", "commit": "82c1001658b2310c576c7fc39d721695e4382f2f",
                "commit_date": "2026-08-09", "licence_file": "MIT (Copyright (c) 2026 Nguyen Thu Thuy)",
                "pack_says": "MIT", "licence_verified": True,
                "runtime_dependencies": "ifc-spf>=0.1 (same author; its licence NOT verified here)",
                "features_confirmed": ["IFC element -> cost-code CLASSIFICATION (not measurement)",
                                       "TOML [meta] + [[rule]] mappings, no Python per standard",
                                       "specificity with integer priority override",
                                       "quantity names in preference order; no-quantity status, never dropped",
                                       "mapping lint: qto validate", "golden CSV per standard (tests/golden)",
                                       "meta.status draft/reviewed/deprecated + declared gaps"],
                "limitations_confirmed": ["all shipped mappings status=draft", "IFC only", "reads authored Qto_* "
                                          "quantities; no geometry kernel"]},
    "REBAR_TAKEOFF": {"repo": "tolga-ileri/Rebar-Takeoff", "commit": "54641dd850291a9a8d8aac6119562a8a5f2099f7",
                      "commit_date": "2026-09-09", "licence_file": "MIT (Copyright (c) 2026 Tolga Ileri)",
                      "pack_says": "MIT (re-verify at commit)", "licence_verified": True,
                      "runtime_dependencies": "ezdxf, scipy, openpyxl, pandas; UI nicegui, pywebview; build "
                                              "pyinstaller, pillow; DWG needs ODA File Converter (not "
                                              "redistributable)",
                      "features_confirmed": ["scans placed TEXT / MTEXT / INSERT / ATTRIB",
                                             "layer discovery by name keywords + label content",
                                             "label grammar: '16[16/20', '16O16/20', '%%c', '2x19[10/10', "
                                             "'L=400', 'BOY=400', 'UZUNLUK=400' (Turkish practice)",
                                             "quantity/diameter label matched to the NEARBY length label",
                                             "unit mass from diameter and 7850 kg/m3",
                                             "unresolved rows stay out of the total and are listed",
                                             "match-rate vs included-in-totals metrics"],
                      "limitations_confirmed": ["self-described APPROXIMATE", "not a geometric rebar verifier",
                                                "hooks / laps only if in the labels", "range labels low confidence",
                                                "grammar is Turkish-convention, not the ST7757 ('5O10/m', "
                                                "'8 O 12', schedule ATTRIB) convention"]},
}

PACK_ONLY = {   # named by the pack, not fetched: claims only
    "cad-ai-agent": "Apache-2.0 (pack claim)", "ConMCP": "MIT (pack claim)", "tianzheng-dwg-parse": "MIT (pack claim)",
    "FreeCAD-Reinforcement": "LGPL-2+ (pack claim)", "Plansight": "MIT code, AGPL-dependency caution (pack claim)",
    "IfcOpenShell / ifc5d / ifcopenshell-mcp": "LGPL-3+ (pack claim)", "Clipper2": "BSL-1.0 (pack claim)",
    "Manifold / build123d / CadQuery / OR-Tools": "Apache-2.0 (pack claim)",
    "pypdfium2 / pdfplumber / PDF.js / PaddleOCR / Tesseract": "permissive (pack claim)",
    "PyMuPDF": "AGPL-3.0 or commercial (pack claim; consistent with the package metadata installed here)",
}

RG = VERIFIED["ROOMGRAPH"]
QT = VERIFIED["AEC_QTO"]
RT = VERIFIED["REBAR_TAKEOFF"]
RG_SRC = f"RoomGraph {RG['repo']}@{RG['commit'][:8]} (MIT verified)"
RT_SRC = f"Rebar-Takeoff {RT['repo']}@{RT['commit'][:8]} (MIT verified)"
QT_SRC = f"aec-qto {QT['repo']}@{QT['commit'][:8]} (MIT verified)"

OVERRIDES = {
    "R9-ST-01": {"DONOR_SOURCE": "pack 03 section F / 14 B (verified / auto_pass / review_required / conflict / "
                                 "assumption / rejected + factorised confidence)",
                 "WHAT_RESEARCH_ADDS": "AUTO_PASS (machine pass with no authority) and factorised confidence "
                                       "scores - neither should enter Urban release"},
    "R9-QF-01": {"DONOR_SOURCE": "pack 01 #1, 03 C-D, 14 A, cleanroom_reference/quantity_contracts.py",
                 "WHAT_RESEARCH_ADDS": "EvidenceRef / ScaleCalibration / QuantityFact / MeasuredQuantity shapes "
                                       "(Decimal values, fact_ids, profile + rule_ids, review_state)",
                 "WHAT_RESEARCH_LOSES_VS_URBAN": "a single review_state string replaces measurement / authority / "
                                                 "release axes and scenario bounds; Decimal vs Urban floats would "
                                                 "break byte-identical frozen outputs"},
    "R9-QF-02": {"DONOR_SOURCE": "pack 01 #1, 03 C, 09 (raw opening stored once; profile applies rules)"},
    "R9-PR-01": {"DONOR_SOURCE": "pack 01 #2, machine_readable/provenance_schema.json, OpenTakeoff",
                 "WHAT_RESEARCH_ADDS": "a JSON-schema receipt shape (quantity_id, evidence[file_hash, revision, "
                                       "sheet, layout, entity_handle, bbox, raw_text], scale, method, formula, "
                                       "inputs, confidence, machine/reviewed geometry refs, validations, warnings, "
                                       "review_state) usable as an EXPORT view of the Urban receipt"},
    "R9-SC-02": {"DONOR_SOURCE": "pack 01 #3, 10 E, 14 C; RoomGraph scale.py (verified)",
                 "WHAT_RESEARCH_ADDS": "scale states unknown / candidate / auto_verified / human_verified / "
                                       "conflicted; second-dimension check; RoomGraph's independent witnesses "
                                       "(scale bar, dimension chains, printed room area)",
                 "WHAT_RESEARCH_LOSES_VS_URBAN": "RoomGraph's last-resort scale from DOOR WIDTHS is a design-"
                                                 "variable quantity, not evidence (reject as an evidence kind); "
                                                 "Urban needs >= 2 independent kinds, the pack only one"},
    "R9-SC-04": {"LICENCE_IMPACT": "IfcOpenShell / ifc5d LGPL-3+ (pack claim): adapter boundary + legal review",
                 "DONOR_SOURCE": "pack 01 #10, 04 R10.0"},
    "R9-RG-01": {"DONOR_SOURCE": RG_SRC, "WHAT_RESEARCH_ADDS": "line clustering BEFORE segment pairing (faces "
                                                                "60-420 mm) so a doorway does not split a wall",
                 "EXPECTED_ACCURACY_BENEFIT": "none on CAD (Urban pairs fragmented faces); possible on vector PDF",
                 "LICENCE_IMPACT": "MIT verified", "DEPENDENCY_IMPACT": "none (RoomGraph is stdlib-only)",
                 "WHAT_RESEARCH_LOSES_VS_URBAN": "curved walls and walls > 420 mm do not pair (RoomGraph "
                                                 "LIMITATIONS) - Alsenan has arches / curved glazing"},
    "R9-RG-02": {"DONOR_SOURCE": RG_SRC, "WHAT_RESEARCH_ADDS": "bridged length recorded as a bridged opening",
                 "LICENCE_IMPACT": "MIT verified"},
    "R9-RG-04": {"DONOR_SOURCE": RG_SRC, "WHAT_RESEARCH_ADDS": "nothing beyond Urban's two planar routes",
                 "EXPECTED_ACCURACY_BENEFIT": "none on CAD", "EXPECTED_COVERAGE_BENEFIT": "PDF-only projects",
                 "LICENCE_IMPACT": "MIT verified"},
    "R9-RG-05": {"DONOR_SOURCE": RG_SRC, "WHAT_RESEARCH_ADDS": "a wider symbol library (revolving, roller, "
                                                                "curtain wall by mullion rhythm)",
                 "WHAT_RESEARCH_LOSES_VS_URBAN": "a door drawn over a continuous wall is missed; an accidental "
                                                 "drafting gap becomes an opening (Urban: positive evidence only)",
                 "LICENCE_IMPACT": "MIT verified"},
    "R9-RG-06": {"DONOR_SOURCE": RG_SRC, "WHAT_RESEARCH_ADDS": "shared wall = adjacent, opening on it = walkable; "
                                                                "graph connectivity and entrances",
                 "LICENCE_IMPACT": "MIT verified (idea; Urban builds its own graph over TS01 sites)"},
    "R9-RG-07": {"DONOR_SOURCE": RG_SRC},
    "R9-RG-08": {"DONOR_SOURCE": RG_SRC + " --strict"},
    "R9-RG-09": {"DONOR_SOURCE": RG_SRC, "WHAT_RESEARCH_ADDS": "an independent, dependency-free vector-PDF room "
                                                                "route with an adjacency graph",
                 "WHAT_RESEARCH_LOSES_VS_URBAN": "no curves, no single-line or > 420 mm walls, no scans; scale "
                                                 "can fall back to door widths",
                 "LICENCE_IMPACT": "MIT verified at 772f0954", "DEPENDENCY_IMPACT": "none (stdlib only)",
                 "BENCHMARK_REQUIRED": "yes: a project with CAD truth AND a clean vector PDF, without curved walls "
                                       "(Alsenan's arches fall outside RoomGraph's scope)"},
    "R9-RT-01": {"DONOR_SOURCE": RT_SRC},
    "R9-RT-02": {"DONOR_SOURCE": RT_SRC + "; pack 08",
                 "WHAT_RESEARCH_ADDS": "nothing usable for the grammar itself: Rebar-Takeoff's grammar is "
                                       "Turkish-convention ('16[16/20', 'L=400', 'BOY='); the gap is Urban's own "
                                       "three parsers", "LICENCE_IMPACT": "MIT verified; nothing reused"},
    "R9-RT-03": {"DONOR_SOURCE": RT_SRC},
    "R9-RT-04": {"DONOR_SOURCE": RT_SRC + " (nearby length label)", "STATUS": "CONFLICT",
                 "WHAT_RESEARCH_ADDS": "length from the NEAREST length label",
                 "WHAT_RESEARCH_LOSES_VS_URBAN": "nearest-text binding is exactly what Urban beam_binding forbids "
                                                 "(positive constraints only)",
                 "RECOMMENDATION": "REJECT", "LICENCE_IMPACT": "MIT verified"},
    "R9-RT-05": {"DONOR_SOURCE": RT_SRC + "; pack 04 R9.5, 08",
                 "WHAT_RESEARCH_ADDS": "two metrics worth keeping: automatic match rate and included-in-totals "
                                       "rate; unresolved rows listed, not totalled (Urban already does the latter)",
                 "LICENCE_IMPACT": "MIT verified (idea only)"},
    "R9-RT-06": {"DONOR_SOURCE": RT_SRC},
    "R9-RT-07": {"DONOR_SOURCE": RT_SRC},
    "R9-RT-08": {"DONOR_SOURCE": RT_SRC, "STATUS": "URBAN_STRONGER",
                 "WHAT_RESEARCH_ADDS": "annotation-first pattern + match-rate metrics; no reusable grammar or "
                                       "fixtures (Turkish label convention, synthetic DXFs)",
                 "WHAT_RESEARCH_LOSES_VS_URBAN": "approximate by design: nearest-label lengths, no geometry, laps "
                                                 "only from labels",
                 "RECOMMENDATION": "REJECT", "LICENCE_IMPACT": "MIT verified at 54641dd8",
                 "DEPENDENCY_IMPACT": "scipy, pandas, nicegui, pywebview, pyinstaller, ODA converter - none needed",
                 "BENCHMARK_REQUIRED": "no", "TESTS_REQUIRED": "-", "PRIORITY": "-"},
    "R9-OT-01": {"DONOR_SOURCE": "OpenTakeoff; pack 01 #12, 03 G, mcp_tool_surface.json"},
    "R9-RE-01": {"DONOR_SOURCE": QT_SRC + "; pack 01 #8, 04 R9.4, 09",
                 "WHAT_RESEARCH_ADDS": "TOML [[rule]] with specificity + priority override, a lint (qto "
                                       "validate), golden CSV per mapping, status draft/reviewed, declared gaps",
                 "WHAT_RESEARCH_LOSES_VS_URBAN": "qto CLASSIFIES authored IFC quantities; it has no measurement, "
                                                 "authority precedence, fail-closed blocking or scenario layers - "
                                                 "the pattern covers Urban's mapping step only",
                 "LICENCE_IMPACT": "MIT verified at 82c10016 (pattern only)",
                 "DEPENDENCY_IMPACT": "none adopted (qto depends on ifc-spf, licence unverified)"},
    "R9-RE-02": {"DONOR_SOURCE": QT_SRC + " tests/golden/*.csv; pack 09 golden tests"},
    "R9-GB-01": {"DONOR_SOURCE": "pack 01 #4, 04 R9.2, 05 #11",
                 "WHAT_RESEARCH_ADDS": "Clipper2 integer offsets (skirting / upturn paths)",
                 "WHAT_RESEARCH_LOSES_VS_URBAN": "pack proposes ADDING Shapely: Urban already depends on it "
                                                 "(~45 engine modules); Urban's skirting path engine is native"},
}

_D = dict(EXPECTED_ACCURACY_BENEFIT="-", EXPECTED_COVERAGE_BENEFIT="-", AUDITABILITY_BENEFIT="-",
          IMPLEMENTATION_RISK="-", REGRESSION_RISK="-", LICENCE_IMPACT="-", DEPENDENCY_IMPACT="-",
          BENCHMARK_REQUIRED="no", TESTS_REQUIRED="-", CLASSES="-", FUNCTIONS="-", TESTS="-")


def P(i, idea, donor, equiv, files, status, does, adds, loses, reco, prio, **kw):
    r = dict(_D, RECOMMENDATION_ID=i, RESEARCH_IDEA=idea, DONOR_SOURCE=donor, CURRENT_URBAN_EQUIVALENT=equiv,
             FILES=files, STATUS=status, WHAT_URBAN_ALREADY_DOES=does, WHAT_RESEARCH_ADDS=adds,
             WHAT_RESEARCH_LOSES_VS_URBAN=loses, RECOMMENDATION=reco, PRIORITY=prio, CHANGED_BY_PACK=["NEW_ROW"])
    r.update(kw)
    return r


PACK_ROWS = [
    P("R9-LIC-01", "avoid PyMuPDF (AGPL-3.0 or commercial) in a proprietary distribution", "pack 01 #9, 06",
      "PyMuPDF is imported by production engine modules", "engine/pdf_vector_evidence.py; engine/vector_source.py; "
      "engine/geometry.py; engine/glyph_text.py; engine/sanitary_source.py; engine/ingest/harness.py "
      "(+ research and tests); requirements.txt lists it only as an optional 'tools' comment", "CONFLICT",
      "PDF vector / text evidence lane works", "the licence fact: a closed commercial distribution of these modules "
                                               "carries AGPL obligations unless a commercial licence is bought",
      "-", "ADAPT", "P1", LICENCE_IMPACT="HIGH: AGPL-3.0 runtime dependency, undeclared in DONORS.lock / "
                                         "THIRD_PARTY_PROVENANCE",
      DEPENDENCY_IMPACT="replace with pypdfium2 (render) + pdfplumber (vector/text), or buy a PyMuPDF licence",
      IMPLEMENTATION_RISK="medium (PDF evidence lane rewrite behind the same outputs)", REGRESSION_RISK="medium",
      BENCHMARK_REQUIRED="yes: PDF evidence registers reproduce under the replacement",
      TESTS_REQUIRED="engine import test fails on an AGPL import unless a licence record exists",
      DECISION="OWNER DECISION NOW (licence strategy); migration after S4 - S4 reads DXF only"),
    P("R9-LIC-02", "third-party manifest + CI licence gate (fail on unapproved runtime dependency)", "pack 06",
      "engine/source dependency register enforced by test; DONORS.lock for donors", "tests/r8_1/test_r8_1_boundaries.py "
      "(NOT_IN_DEPENDENCY_REGISTER); research/external_engine_lab/DONORS.lock, THIRD_PARTY_PROVENANCE.json",
      "PARTIAL", "engine/source imports are register-checked", "one manifest covering ALL runtime imports "
                                                              "(engine/ legacy too) with licence + approval",
      "-", "ADOPT", "P1", AUDITABILITY_BENEFIT="high", IMPLEMENTATION_RISK="low", LICENCE_IMPACT="prevents R9-LIC-01 "
                                                                                                  "recurring",
      TESTS_REQUIRED="every third-party import in engine/ appears in the manifest with an approved licence"),
    P("R9-PDF-01", "permissive PDF / OCR stack (pypdfium2, pdfplumber, PDF.js, PaddleOCR / Tesseract) + page router",
      "pack 01 #9, 04 R9.8, 10 C-D", "PyMuPDF render / vector / text; tesseract as an optional external binary",
      "engine/pdf_vector_evidence.py (ocr via tesseract binary); engine/document_reader.py", "PARTIAL",
      "three-channel crop evidence (render, OCR, vector)", "licence-clean replacements; a page router",
      "-", "DEFER", "P2", DEPENDENCY_IMPACT="new deps (pypdfium2, pdfplumber)", BENCHMARK_REQUIRED="yes",
      DECISION="follows R9-LIC-01"),
    P("R9-SV-01", "document / drawing survey before takeoff (tianzheng-dwg-parse pattern)", "pack 05 #9, 10 A "
      "(tianzheng: PACK_CLAIM_ONLY)", "capability census, per-entity census, region candidates, repeated-geometry and "
      "storey copy-family detection", "engine/source/capability.py; cad/census.py; region_candidates.py; "
      "engine/drawing_region.py; engine/drawing_role.py", "ALREADY_PRESENT",
      "placed instances counted, not definitions; repeated panels detected", "-", "-", "KEEP_URBAN", "-"),
    P("R9-REV-01", "revision + cross-sheet identity (SourceEntityKey, CrossSheetLink, match-line continuation)",
      "pack 01 #11, 04 R9.7; cad-ai-agent (PACK_CLAIM_ONLY)", "source identity (handle + block path), source "
      "revisions, revision delta, source anchor; no match-line continuation object",
      "engine/source/source_anchor.py; observations.py; R8.7 revision delta", "PARTIAL",
      "a line item survives a revision with its source identity", "match-line / continuation links across partial "
                                                                  "sheets", "-", "DEFER", "P2",
      EXPECTED_COVERAGE_BENEFIT="multi-sheet plans", BENCHMARK_REQUIRED="yes (a split-sheet project)"),
    P("R9-EX-01", "explain_quantity(quantity_id) as pure structured data", "pack 01 #16, 14 E, mcp_tool_surface.json",
      "boq_report trace + room_matrix breakdown + run manifest", "engine/source/boq_report.py; room_matrix.py; "
      "run_manifest.py", "PARTIAL", "every report row is traceable", "one function over the receipt "
                                                                    "(depends on R9-PR-01)", "-", "ADAPT", "P1",
      AUDITABILITY_BENEFIT="high", TESTS_REQUIRED="explain(q) reproduces q from its receipt without re-reading the "
                                                  "drawing"),
    P("R9-RV-01", "review queue ordered by expected quantity impact", "pack 14 F",
      "owner decision queue / root questions deduplicated from dependency impacts", "engine/source/question_helper.py; "
      "R6.5 root questions", "PARTIAL", "questions deduplicated and scoped", "impact x uncertainty ordering", "-",
      "DEFER", "DEFER"),
    P("R9-BM-01", "per-family accuracy metrics, error taxonomy, blind protocol", "pack 07",
      "blind input contract, benchmark firewall, predeclared blind gates, scorecards, freeze-then-compare",
      "engine/blind_input_contract.py; engine/source/benchmark_firewall.py; engine/benchmark_protection.py; "
      "engine/supervised_benchmark.py", "PARTIAL", "blind protocol and freeze-before-compare are enforced",
      "one metrics registry per quantity family (incl. bar-level rebar metrics) and a primary-cause taxonomy",
      "a single aggregate accuracy figure (pack itself rejects it)", "ADAPT", "P1",
      TESTS_REQUIRED="S4 emits bar-level records so bar-mark recall / diameter / count / length / mass error can "
                     "be scored"),
    P("R9-RB-01", "rebar evidence priority ladder (BBS > member schedule > callout > detail > geometry > assumption)",
      "pack 01 #6, 08, 14 D", "authority levels per fact type; schedule-first census",
      "engine/source/structural_authority.py; structural_census.py; evidence_ladder.py", "ALREADY_PRESENT",
      "lower sources challenge, never overwrite (conflict records)", "-", "-", "KEEP_URBAN", "-"),
    P("R9-RB-02", "canonical rebar objects (BarSpec / BarShape / BarSet / BarLengthBreakdown / BBSRow)",
      "pack 04 R9.6, 08, cleanroom_reference/rebar_contracts.py; FreeCAD-Reinforcement (PACK_CLAIM_ONLY, LGPL-2+)",
      "rebar_model + column_rebar + accurate_boq_rebar (hooks, laps as BBS length, never net)",
      "engine/source/rebar_model.py (lap_parts); bbs_optimiser.py (hook_addition, split_run, cut); "
      "accurate_boq_rebar.py; column_rebar.py", "ALREADY_PRESENT", "length components kept separate; laps BLOCKED "
                                                                   "without a lap authority",
      "named dataclass shapes", "-", "KEEP_URBAN", "-"),
    P("R9-RB-03", "OR-Tools cutting-stock optimisation", "pack 01 #13, 04 R10.2",
      "native BBS cutting optimiser", "engine/source/bbs_optimiser.py", "ALREADY_PRESENT",
      "procurement layer separate from net", "an external solver", "-", "REJECT", "-",
      DEPENDENCY_IMPACT="avoids OR-Tools"),
    P("R9-FW-01", "formwork as contact surfaces (build123d / CadQuery / Manifold)", "pack 01 #14, 04 R10.1",
      "no formwork trade yet", "-", "MISSING", "-", "contact-face formwork", "-", "DEFER", "DEFER",
      DEPENDENCY_IMPACT="3D kernels (Apache-2.0, pack claim)"),
    P("R9-AG-01", "typed agent operations, whole-changeset rejection, audit, sandbox (cad-ai-agent / ConMCP)",
      "pack 05 #4-#5 (PACK_CLAIM_ONLY)", "agent sandbox, audit log, blind input contract; agents give CANDIDATE "
      "evidence only", "engine/agent_sandbox.py; engine/audit_log.py; engine/blind_input_contract.py; "
      "engine/source/frame.py", "PARTIAL", "agents cannot set status or compute quantities",
      "whole-changeset rejection of a proposed fact group", "-", "DEFER", "DEFER"),
    P("R9-MCP-01", "high-level deterministic MCP surface over the core", "pack 03 G, 04 R10.3, mcp_tool_surface.json",
      "CAD oracle interface (consumer side only)", "engine/source/cad_oracle.py", "NOT_APPLICABLE",
      "-", "Urban as an MCP server", "-", "DEFER", "DEFER"),
    P("R9-RE-03", "rule lint for dead / shadowed / conflicting rules", QT_SRC + " (qto validate); pack 09",
      "method precedence explicit; no lint", "engine/source/urban_methods.py; urban_methods_v3.py", "MISSING",
      "-", "lint over Urban method registers", "-", "ADAPT", "P2", TESTS_REQUIRED="two methods applying to the "
                                                                                    "same kind at the same "
                                                                                    "precedence fail the lint"),
    P("R9-PR-07", "provenance JSON-schema export view", "pack machine_readable/provenance_schema.json",
      "Urban receipts (R9-PR-01)", "engine/source/run_manifest.py; boq_report.py", "PARTIAL",
      "-", "an export adapter mapping Urban receipts onto the schema (review_state derived from release state)",
      "using the schema as the internal model would drop Urban's state axes", "ADAPT", "P2"),
]

MATRIX_DONOR_UPDATES = {   # DONOR_TECHNIQUE_MATRIX: technique -> {column: value}
    "room-cycle extraction": {"ROOMGRAPH": "line clustering -> face pairing -> corner repair -> half-edge minimal "
                                           "cycles (verified; no curved walls)"},
    "room adjacency": {"ROOMGRAPH": "shared wall = adjacent; opening = walkable (verified)",
                       "BEST_CURRENT_METHOD": "RoomGraph idea over Urban TS01 sites"},
    "wall-face pairing": {"ROOMGRAPH": "line-first pairing 60-420 mm (verified)"},
    "opening reconstruction": {"ROOMGRAPH": "gap where both faces stop + symbol library (verified; misses doors "
                                            "drawn over continuous walls)"},
    "scale calibration": {"ROOMGRAPH": "dimension strings > title block > door widths + independent witnesses "
                                       "(verified; door-width fallback rejected)",
                          "REBAR_TAKEOFF": "none: lengths are read from label values (L=400 as cm)"},
    "rebar annotation parsing": {"REBAR_TAKEOFF": "Turkish label grammar + nearest length label (verified; "
                                                  "approximate)", "ROOMGRAPH": "-"},
    "rule profiles": {"ROOMGRAPH": "-", "REBAR_TAKEOFF": "-"},
    "provenance receipt": {"ROOMGRAPH": "per-run warnings + scale source/confidence", "REBAR_TAKEOFF":
                           "Excel audit sheets; source text kept"},
    "BBS model": {"REBAR_TAKEOFF": "count x length x unit mass only"},
    "source handles": {"REBAR_TAKEOFF": "not stated in README"},
    "ATTRIB schedule extraction": {"REBAR_TAKEOFF": "reads placed ATTRIB / TEXT labels; no schedule-grid reading"},
    "physical wall-face extraction": {"ROOMGRAPH": "wall centre / faces for rooms; no face-area output"},
    "slab polygon extraction": {"ROOMGRAPH": "room polygons only (gross / net m2)"},
}
DONOR_NEW_COLUMN = "AEC_QTO"
DONOR_NEW_COLUMN_VALUES = {"rule profiles": "TOML rules, specificity + priority, lint, golden CSV (verified; "
                                            "classification only)",
                           "scenario quantities": "-", "provenance receipt": "quantity_name per row (verified)"}
NEW_DONOR_ROWS = [
    {"TECHNIQUE": "licence / dependency gate", "URBAN": "engine/source register test + DONORS.lock (PyMuPDF "
                                                        "undeclared)", "U_C4N": "-", "CHRISTIANNP": "-",
     "ROOMGRAPH": "stdlib only", "OPENTAKEOFF": "NOTICE file", "REBAR_TAKEOFF": "-", "AEC_QTO": "-",
     "BEST_CURRENT_METHOD": "pack third_party_manifest + CI gate", "WHY": "AGPL slipped into engine/",
     "KNOWN_DEFECT": "PyMuPDF in 6 engine modules", "DECISION": "PRODUCTION (P1)", "NEXT_TEST": "manifest test"},
    {"TECHNIQUE": "golden regression fixtures", "URBAN": "per-round freezes + byte-identical rebuild tests",
     "U_C4N": "-", "CHRISTIANNP": "-", "ROOMGRAPH": "generated fixtures", "OPENTAKEOFF": "evals corpus",
     "REBAR_TAKEOFF": "synthetic DXF tests", "AEC_QTO": "tests/golden/*.csv per mapping",
     "BEST_CURRENT_METHOD": "URBAN + qto per-profile golden", "WHY": "golden tied to a profile version",
     "KNOWN_DEFECT": "no cross-trade URBAN_KW_V1 golden", "DECISION": "PRODUCTION (P1)",
     "NEXT_TEST": "URBAN_KW_V1 golden"},
    {"TECHNIQUE": "ambiguity excluded from totals", "URBAN": "release model: BLOCKED / candidate never official",
     "U_C4N": "kept measuring", "CHRISTIANNP": "assumptions filled", "ROOMGRAPH": "--strict",
     "OPENTAKEOFF": "review state", "REBAR_TAKEOFF": "unresolved rows out of total", "AEC_QTO": "no-quantity rows",
     "BEST_CURRENT_METHOD": "URBAN (with scenario layers)", "WHY": "uncertainty neither zero nor official",
     "KNOWN_DEFECT": "-", "DECISION": "PRODUCTION", "NEXT_TEST": "-"},
]
