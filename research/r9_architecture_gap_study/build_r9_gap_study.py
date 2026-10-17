"""R9 READ-ONLY ARCHITECTURE GAP STUDY - current Urban engine (HEAD) vs the research-pack ideas.

v1 (a75b845): built before the pack arrived, from the ideas the owner's R9 brief names, mapped against the Urban code at HEAD (files / functions / tests that
exist and were read), and against the two donors held locally at their DONORS.lock commits (U-C4N, OpenTakeoff) and
the christiannp forensic package. v2: pack_v2.py overlays the delivered pack and the pinned-commit verification of
RoomGraph / aec-qto / Rebar-Takeoff; no PACK_NOT_HELD value survives (apply_pack refuses one). Nothing here changes production code; nothing is installed or copied.

    python research/r9_architecture_gap_study/build_r9_gap_study.py
"""

from __future__ import annotations

import csv
import io
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PACK = "PACK_NOT_HELD"
COLS = ["RECOMMENDATION_ID", "RESEARCH_IDEA", "DONOR_SOURCE", "CURRENT_URBAN_EQUIVALENT", "FILES", "CLASSES",
        "FUNCTIONS", "TESTS", "STATUS", "WHAT_URBAN_ALREADY_DOES", "WHAT_RESEARCH_ADDS", "WHAT_RESEARCH_LOSES_VS_URBAN",
        "EXPECTED_ACCURACY_BENEFIT", "EXPECTED_COVERAGE_BENEFIT", "AUDITABILITY_BENEFIT", "IMPLEMENTATION_RISK",
        "REGRESSION_RISK", "LICENCE_IMPACT", "DEPENDENCY_IMPACT", "RECOMMENDATION", "BENCHMARK_REQUIRED",
        "TESTS_REQUIRED", "PRIORITY"]
STATUS = {"ALREADY_PRESENT", "PARTIAL", "MISSING", "CONFLICT", "URBAN_STRONGER", "NOT_APPLICABLE"}
RECO = {"KEEP_URBAN", "ADOPT", "ADAPT", "CHALLENGER_ONLY", "REJECT", "DEFER"}


def R(i, idea, donor, equiv, files, classes, funcs, tests, status, does, adds, loses, acc, cov, aud, irisk, rrisk,
      lic, dep, reco, bench, treq, prio):
    assert status in STATUS and reco in RECO, i
    return dict(zip(COLS, [i, idea, donor, equiv, files, classes, funcs, tests, status, does, adds, loses, acc, cov,
                           aud, irisk, rrisk, lic, dep, reco, bench, treq, prio]))


ROWS = [
    # ---- states ------------------------------------------------------------------------------------------------
    R("R9-ST-01", "simple quantity states (verified / review_required / conflict / assumption)", "research pack examples",
      "three-axis state + scenario layers", "engine/source/physical_measurement_state.py; quantity_scenarios.py; "
      "release_model_v2.py", "-", "stamp, release_state, blocked_is_not_zero; part, combine, check",
      "tests/coverage_recovery_engine/test_coverage_recovery.py", "URBAN_STRONGER",
      "measurement / authority / release axes; release derived; VERIFIED<=LOWER_BOUND<=LOW<=BEST<=HIGH; UNQUANTIFIED "
      "listed; BLOCKED never zero; procurement only from official layer",
      "nothing beyond vocabulary", "would merge measurement and authority; 'review_required' hides whether the value "
                                   "is a bound, a candidate or blocked", "none", "none", "none", "-", "-", "-", "-",
      "KEEP_URBAN", "no", "keep test_blocked_measurable_object_is_not_zero", "-"),
    # ---- quantity fact core --------------------------------------------------------------------------------------
    R("R9-QF-01", "Evidence -> QuantityFact -> MeasurementProfile -> MeasuredQuantity", "research pack",
      "observations (neutral) -> CANONICAL_MEASUREMENT_INPUT -> methods -> evidence rows -> boq_canonical / "
      "boq_report; structural: S1 census -> structural_schedule rows -> V3b BOQ lines; coverage: scenario parts",
      "engine/source/observations.py; canonical_input.py; run_manifest.py; boq_canonical.py; boq_report.py; "
      "structural_census.py; quantity_scenarios.py", "CanonicalMeasurementInput",
      "canonical_input.check_requirements (fail closed); run_manifest.build; boq_report rows (copy-only)",
      "tests/r8_7, tests/r8_19, tests/rc1", "PARTIAL",
      "architecture path already has neutral observations, a fail-closed canonical input, a run manifest and a copy-only "
      "report layer; structural and coverage paths carry the same ideas in register form",
      "one named, typed contract shared by every trade (a QuantityFact shape) and an explicit profile step",
      "a new dataclass hierarchy would duplicate CanonicalMeasurementInput / scenario parts and lose the state axes",
      "low", "low", "high (one receipt shape across trades)", "medium (if rewrite) / low (if contract)", "medium",
      "none", "none", "ADAPT", "golden fixtures of V3b + coverage-round outputs",
      "contract validator over existing records: every BOQ-bearing record maps to the QuantityFact fields or fails",
      "P1"),
    R("R9-QF-02", "facts neutral of measurement convention", "research pack",
      "conventions live inside geometry modules", "engine/source/beam_occurrence_recovery.py (B x (D - t)); "
      "column_concrete_geometry.py (net of slab above); physical_wall_faces.py (interval - member, net of openings); "
      "ground_slab_recovery.py (cells net of beams); wall_faces_v2.py", "-", "_vol, record, faces, quantities",
      "tests/coverage_recovery_engine", "PARTIAL",
      "conventions are explicit and documented in each module, never hidden; dual-basis (contractor rulebook) exists "
      "for wall treatment (engine/contractor_measurement.py)",
      "a declared convention id on each output so a second profile can be computed from the same fact",
      "nothing if done as a stamp; a forced split would break frozen byte-identical outputs",
      "medium (comparisons stop mixing conventions)", "none", "high", "low", "low", "none", "none", "ADAPT",
      "no", "every quantity record names its CONVENTION_ID; two conventions from one fact reproduce", "P1"),
    R("R9-QF-03", "measured vs procurement quantity", "OpenTakeoff / research pack", "net BOQ vs waste layer",
      "engine/source/waste_procurement.py; release_model_v2.py", "-", "resolve, apply; procurement_eligible_v2",
      "tests (V3b waste)", "ALREADY_PRESENT", "net is the BOQ; waste/procurement a separate rule-driven layer with "
                                              "hierarchy; provisional never procurement-eligible", "-", "-", "none",
      "none", "none", "-", "-", "-", "-", "KEEP_URBAN", "no", "-", "-"),
    # ---- provenance --------------------------------------------------------------------------------------------
    R("R9-PR-01", "provenance receipt on every authoritative quantity", "research pack / OpenTakeoff provenance schema",
      "run manifest + report trace (architecture); census handles (structure); freeze hashes (rounds)",
      "engine/source/run_manifest.py; boq_report.py (TRACE); export_provenance.py; execution_provenance.py; "
      "freeze_manifest.py; research/*/INDEX.json", "-", "build (RUN_INPUT_DIGEST, CODE_BOUND_DIGEST), row_authority_digest",
      "tests/r8_11, tests/r8_19, tests/r8_6", "PARTIAL",
      "architectural rows carry run id, revision anchor sha, claims applied/rejected, policy digests, method contract, "
      "kernel versions; S1 rows carry drawing + handles + raw ATTRIBs",
      "the SAME receipt on structural V3b lines and coverage-round parts (today: free-text trace, no handles)",
      "a second provenance system would split the audit trail", "none", "none", "high", "low", "low", "none", "none",
      "ADAPT", "no", "test_every_authoritative_quantity_has_receipt (see PROVENANCE_FIELD_COVERAGE.csv)", "P0"),
    R("R9-PR-02", "numeric confidence + named factors", "OpenTakeoff confidence.ts", "authority levels / evidence tiers",
      "engine/source/structural_authority.py; evidence_ladder.py; evidence_tiers.py; role_authority.py", "-",
      "authority level per fact type; ladder levels", "tests/structural_review_engine", "URBAN_STRONGER",
      "authority is ordinal and per fact type; release derived from it, never from a score",
      "a transparent review-priority signal", "a score near 1.0 reads as 'verified' (OpenTakeoff itself warns of this)",
      "none", "none", "low", "low", "low", "Apache-2.0 idea only", "none", "CHALLENGER_ONLY", "no",
      "a score may order the review queue but never changes release", "DEFER"),
    R("R9-PR-03", "machine-original vs human-corrected geometry lineage", "OpenTakeoff proposed_verts_norm / edits",
      "claims never edit geometry; source-correction claims not implemented", "engine/source/owner_claims.py; "
      "project_claims.py; topology_closures.py (C = SOURCE CORRECTION CLAIM, not in R8.11)", "-", "-", "tests/r8_10",
      "PARTIAL", "source geometry immutable; human input is a scoped, versioned claim",
      "a lineage record for a corrected trace (machine ring kept, human ring added)",
      "editing geometry in place (Urban forbids it)", "low now", "low", "medium", "medium", "low", "Apache-2.0 idea only",
      "none", "DEFER", "no", "when a review UI exists: correction claim keeps the machine geometry byte-identical",
      "DEFER"),
    R("R9-PR-04", "actor separate from method", "OpenTakeoff protocol (method is not actor)",
      "frame evidence: human vs agent vs candidate; claims carry author / role; runs carry method id",
      "engine/source/frame.py; project_claims.py; rule_promotion.py; run_manifest.py", "-", "-", "tests/r8_4",
      "PARTIAL", "agent evidence is CANDIDATE-only; human confirmation bound to a source hash; promotion needs a "
                 "different reviewer", "one ACTOR field and one METHOD field on every quantity receipt",
      "-", "none", "none", "medium", "low", "low", "Apache-2.0 idea only", "none", "ADAPT", "no",
      "receipt rejects a quantity with no actor/method pair", "P1"),
    R("R9-PR-05", "version stamp on comparison values", "R9 brief section 8 (79 m vs 89.74 m)",
      "ENGINE_COMMIT / REGISTER_VERSION / DRAWING_SHA / CALCULATION_ROUND (research only)",
      "research/christiannp_blind_process/scripts/build_crosschecks.py (stamp)", "-", "stamp",
      "tests/christiannp_blind_process", "PARTIAL", "stamps exist in the donor package; not yet in comparison engines",
      "-", "-", "none", "none", "high", "low", "low", "none", "none", "ADOPT", "no",
      "comparison_scope / source_oracle_comparison rows require the four stamp fields", "P0"),
    R("R9-PR-06", "marked-up review export", "OpenTakeoff", "review workbooks, visual QA overlays, annotated images",
      "engine/boq_xlsx.py; boq_rc1_xlsx.py; research/*/review", "-", "-", "tests/reporting_v2", "PARTIAL",
      "per-round review XLSX with dashboards; overlays on original sources", "a standard marked-up drawing export",
      "-", "none", "none", "medium", "low", "low", "Apache-2.0 idea only", "none", "DEFER", "no", "-", "DEFER"),
    # ---- scale ------------------------------------------------------------------------------------------------
    R("R9-SC-01", "scale gate - DXF / DWG", "research pack / OpenTakeoff scaleConfirmed", "UNIT_CONTEXT frozen rule",
      "engine/source/frame.py; engine/source/cad/unit_evidence.py; cad_profile.py; region_candidates.py", "-",
      "UNIT_CONTEXT status (VERIFIED / CONFIRMED_BY_HUMAN / PROVISIONAL / UNCONFIRMED / CONFLICT / BLOCKED); "
      "DIMLFAC via act_measurement; REGION_MIXED_SCALE_NOTES", "tests/r8_3, tests/r8_4", "URBAN_STRONGER",
      "INSUNITS is a declaration, never truth; >= 2 independent kinds within 0.5 %; region transforms separate from "
      "native units", "-", "OpenTakeoff warns instead of blocking (rejected in DONORS.lock)", "none", "none", "none",
      "-", "-", "-", "-", "KEEP_URBAN", "no", "-", "-"),
    R("R9-SC-02", "scale gate - vector PDF", "research pack / OpenTakeoff", "page / raster frame transform + "
      "calibration objects; no UNIT_CONTEXT instance enforced for PDF pages at quantity time",
      "engine/frames.py; engine/pdf_vector_evidence.py; engine/vector_source.py; engine/source/calibration_v2.py",
      "-", "calibration_v2.uniform / xy / affine", "tests/test_document_reader.py, V3b raster tests", "PARTIAL",
      "page/raster transform proved; calibrations are named objects", "a hard gate: no PDF-derived length enters a "
                                                                      "quantity without a VERIFIED page UNIT_CONTEXT",
      "-", "high for PDF-only projects", "low", "high", "medium", "low", "none", "none", "ADAPT", "yes (PDF-only "
      "project)", "PDF quantity without a verified page frame -> BLOCKED", "P1"),
    R("R9-SC-03", "scale gate - raster PDF", "research pack", "raster_evidence.calibrate (>= 2 printed dimensions), "
      "calibration_v2", "engine/source/raster_evidence.py; calibration_v2.py", "-", "calibrate", "V3b raster tests",
      "ALREADY_PRESENT", "raster is evidence only after its scale is proved", "-", "-", "none", "none", "none", "-", "-",
      "-", "-", "KEEP_URBAN", "no", "-", "-"),
    R("R9-SC-04", "scale / units - IFC", "research pack", "none", "-", "-", "-", "-", "NOT_APPLICABLE",
      "no IFC source in any current project", "IFC route", "-", "n/a", "n/a", "n/a", "high", "low",
      "ifcopenshell LGPL-3.0 if ever used", "new dependency", "DEFER", "yes (an IFC project)", "-", "DEFER"),
    # ---- RoomGraph ---------------------------------------------------------------------------------------------
    R("R9-RG-01", "wall-line pairing before segment pairing", "RoomGraph (" + PACK + ")",
      "wall bands with interval matching and fragmented-mate resolver", "engine/source/wall_bands.py; "
      "fragment_recovery.py; wall_band_reconciliation.py", "-", "WALL_BAND_POLICY_V5; pair_parallel_faces; classify",
      "tests/r8_13, tests/r8_14, tests/coverage_recovery_engine", "ALREADY_PRESENT",
      "pairing over fragmented faces; per-metre classes (paired / opening / column / duplicate)", PACK,
      "-", "unknown", "unknown", "low", "-", "-", PACK, "-", "CHALLENGER_ONLY", "yes", "wall-pair fixtures A-W", "P2"),
    R("R9-RG-02", "corner bridge repair", "RoomGraph (" + PACK + ")", "junction recovery / patches / zero-material "
      "closures", "engine/junction_recovery.py; junction_patch.py; engine/source/topology_closures.py", "-",
      "TopologyClosure (reversible)", "tests/r8_11", "URBAN_STRONGER",
      "closures are reversible, zero-material and need physical evidence; snap tolerance judged by topology",
      PACK, "a silent bridge would merge rooms", "-", "-", "high", "-", "-", PACK, "-", "KEEP_URBAN", "no", "-", "-"),
    R("R9-RG-03", "T / crossing splitting + planar arrangement", "RoomGraph / OpenTakeoff arrangement.ts",
      "exact noding (TS01) + independent half-edge Route B + GEOS cross-check", "engine/source/topology.py; "
      "room_topology_v3.py; planar_shadow_topology.py; topology_crosscheck.py", "-", "-", "tests/r8_8, tests/r8_9",
      "ALREADY_PRESENT", "two independent planar routes compared region by region", "-", "-", "none", "none", "none",
      "-", "-", "-", "-", "KEEP_URBAN", "no", "-", "-"),
    R("R9-RG-04", "minimal-cycle room detection", "RoomGraph (" + PACK + ")", "planar faces = sites (TS01, Route B)",
      "engine/source/topology.py; planar_shadow_topology.py; engine/room_partition_graph.py", "-", "-",
      "tests/r8_8", "ALREADY_PRESENT", "geometry first, names afterwards", PACK, "-", "unknown", "unknown", "-", "-",
      "-", PACK, "-", "CHALLENGER_ONLY", "yes", "-", "P2"),
    R("R9-RG-05", "opening classification", "RoomGraph (" + PACK + ")", "opening evidence V3 + authority + completion",
      "engine/cad_openings.py; engine/source/opening_evidence.py; opening_authority.py; opening_completion.py; "
      "door_transition.py", "-", "-", "tests/r8_15, tests/r8_17", "URBAN_STRONGER",
      "existence separate from host; height ladder; side-aware host; door closures from positive evidence", PACK, "-",
      "-", "-", "high", "-", "-", PACK, "-", "KEEP_URBAN", "no", "-", "-"),
    R("R9-RG-06", "room adjacency graph", "RoomGraph (" + PACK + ")",
      "room matrix (view), side-aware window host; no adjacency graph object consumed by wall classification",
      "engine/source/room_matrix.py; semantic_zones.py; engine/room_partition_graph.py", "-", "-", "tests/rc1",
      "PARTIAL", "rooms add up; hosts resolved per opening", "an adjacency graph that wall reconciliation (Method C) "
                                                           "can use: which two rooms each wall face separates",
      "-", "medium (walls 200 mm, plaster sides)", "medium", "high", "medium", "low", PACK, "none", "ADAPT", "yes",
      "every wall face has 0/1/2 adjacent rooms; Method C vs Method A/B classes", "P1"),
    R("R9-RG-07", "multiple scale candidates", "RoomGraph (" + PACK + ")", "unit evidence families + frame CONFLICT",
      "engine/source/cad/unit_evidence.py; frame.py", "-", "-", "tests/r8_3", "ALREADY_PRESENT", "-", "-", "-", "none",
      "none", "none", "-", "-", "-", "-", "KEEP_URBAN", "no", "-", "-"),
    R("R9-RG-08", "strict / no-guess mode", "RoomGraph (" + PACK + ")", "fail-closed everywhere",
      "engine/source/canonical_input.py; frame.py; release_model_v2.py", "-", "-", "tests/r8_7", "URBAN_STRONGER",
      "unknown is never void; blocked never zero; candidate never verified", "-", "-", "none", "none", "none", "-", "-",
      "-", "-", "KEEP_URBAN", "no", "-", "-"),
    R("R9-RG-09", "RoomGraph as a vector-PDF room challenger route", "RoomGraph (" + PACK + ")",
      "CAD-first rooms; PDF rooms via raster topology / space enclosure (research-era)", "engine/raster_topology.py; "
      "engine/space_enclosure.py; engine/vector_source.py", "-", "-", "older E-series tests", "PARTIAL",
      "PDF route exists for evidence, not a maintained room route", "an independent vector-PDF room route for "
                                                                   "PDF-only projects", PACK, "medium on PDF-only",
      "medium", "medium", "medium", "low (challenger)", PACK, PACK, "CHALLENGER_ONLY", "yes (PDF-only project with "
                                                                                      "CAD truth)",
      "region-by-region comparison against TS01 on a project with both", "P2"),
    # ---- Rebar-Takeoff --------------------------------------------------------------------------------------------
    R("R9-RT-01", "placed TEXT / MTEXT / ATTRIB / INSERT reading", "Rebar-Takeoff (" + PACK + ")",
      "K2 kernel + neutral observations", "engine/source/cad/kernel_ezdxf.py; observations.py; cad/libredwg_map.py",
      "-", "-", "tests/r8_2", "ALREADY_PRESENT", "ATTRIB values with owner insert, tag and handle", "-", "-", "none",
      "none", "none", "-", "-", "-", "-", "KEEP_URBAN", "no", "-", "-"),
    R("R9-RT-02", "bar token parsing", "Rebar-Takeoff (" + PACK + ")", "THREE separate grammars",
      "engine/source/schedule_grammar.py (parse_bar); structural_schedule.py (bar_spec); slab_rebar_binding.py "
      "(parse)", "-", "parse_bar, bar_spec, parse", "tests/test_schedule.py, tests/alsenan_rebar_truth",
      "CONFLICT", "each parser is tested for its own consumer", "one grammar, one regression corpus",
      "-", "high (S4 reads footing bars; a token read differently by two parsers is a silent conflict)", "medium",
      "high", "low", "medium", PACK, "none", "ADAPT", "no",
      "corpus of every bar token in ST7757 parsed identically by one grammar; disagreements listed", "P0"),
    R("R9-RT-03", "member-mark parsing", "Rebar-Takeoff (" + PACK + ")", "exact '/'-token match; beam namespaces",
      "engine/source/structural_schedule.py (parse_mark); beam_binding.py (namespace, lookup)", "-", "-",
      "tests/alsenan_structural_census", "URBAN_STRONGER", "no fuzzy match; B / CB / SB namespaces", "-",
      "fuzzy marks", "none", "none", "none", "-", "-", "-", "-", "KEEP_URBAN", "no", "-", "-"),
    R("R9-RT-04", "nearby dimension matching", "Rebar-Takeoff (" + PACK + ")",
      "architectural dimension owner / roles; structural members bind by schedule, not by nearby dimensions",
      "engine/dimension_owner.py; dimension_roles.py; engine/source/beam_binding.py ('never nearest-text')", "-",
      "-", "tests/test_dimension_owner.py", "PARTIAL", "positive constraints only for members",
      "dimension evidence for bar extents (e.g. slab top bar length, BOXED)", "nearest-text binding (rejected)",
      "medium (slab top bars)", "medium", "medium", "medium", "medium", PACK, "none", "DEFER", "yes", "-", "DEFER"),
    R("R9-RT-05", "spatial / layer / block context, duplicates, ambiguity exclusion", "Rebar-Takeoff (" + PACK + ")",
      "region membership, text roles, terminal ledger, engineering flags", "engine/source/region_membership.py; "
      "text_role_v3.py; terminal_ledger.py; engineering_flags.py; structural_schedule.reconcile", "-", "-",
      "tests/r8_9, tests/alsenan_structural_census", "PARTIAL",
      "per element family", "a structure-wide ANNOTATION CENSUS: every bar-like token -> exactly one terminal state",
      "-", "high (S4)", "high", "high", "low", "low", PACK, "none", "ADAPT", "no",
      "token conservation: tokens_in == bound + definition_only + unbound + unreadable + duplicate", "P0"),
    R("R9-RT-06", "confidence per annotation", "Rebar-Takeoff (" + PACK + ")", "interpretation_state + authority",
      "engine/source/schedule_grammar.py; structural_authority.py", "-", "-", "-", "URBAN_STRONGER", "-", "-", "-",
      "none", "none", "none", "-", "-", "-", "-", "KEEP_URBAN", "no", "-", "-"),
    R("R9-RT-07", "source coordinates per annotation", "Rebar-Takeoff (" + PACK + ")", "schedule cell provenance",
      "engine/source/schedule_grammar.py (cell: block, handle, tag, raw, drawing, layer, position, page)", "-",
      "cell", "-", "ALREADY_PRESENT", "-", "-", "-", "none", "none", "none", "-", "-", "-", "-", "KEEP_URBAN", "no",
      "-", "-"),
    R("R9-RT-08", "Rebar-Takeoff as a whole", "Rebar-Takeoff (" + PACK + ")", "S1 + S2 + schedule readers + "
      "accurate_boq_rebar", "see RT-01..07", "-", "-", "-", "PARTIAL", "-", "test fixtures / token corpora", "-",
      "medium", "medium", "high", "low as fixtures", "low", PACK + " (licence decides fixture use)", "none",
      "CHALLENGER_ONLY", "yes", "use as TEST_FIXTURE_DONOR only after licence check", "P1"),
    # ---- OpenTakeoff contracts -------------------------------------------------------------------------------
    R("R9-OT-01", "shared deterministic math between UI and MCP", "OpenTakeoff", "'code calculates, agents never do'",
      "engine/units.py; engine/unit_guard.py; engine/source/boq_report.py (copy-only)", "-", "-", "-",
      "NOT_APPLICABLE", "no UI; agents never compute", "-", "-", "none", "none", "none", "-", "-", "Apache-2.0", "-",
      "KEEP_URBAN", "no", "-", "-"),
    # ---- rule engine -------------------------------------------------------------------------------------------
    R("R9-RE-01", "declarative rule profiles (aec-platform/qto)", "aec-qto (" + PACK + ")",
      "method registers as data + profiles JSON + rule register + promotion lifecycle; arithmetic in code",
      "engine/source/urban_methods.py; urban_methods_v3.py; waste_procurement.py; rule_promotion.py; "
      "engine/finishes_rules.py; engine/profiles/*.json; research/alsenan_structural_census_s1/"
      "STRUCTURAL_PROJECT_RULE_REGISTER.json", "-", "applies, resolve, apply", "tests/r8_19, tests/test_finance*",
      "PARTIAL", "methods are versioned, scoped and overrideable; precedence explicit; owner facts outrank fallbacks",
      "one declarative profile format for convention choices", "authority / state / provenance behaviour if the "
                                                               "declarative format cannot express precedence and "
                                                               "fail-closed blocking", "low", "none", "medium",
      "high", "high", PACK, "none", "DEFER", "yes: URBAN_KW_V1 golden fixture first",
      "golden fixture reproduces V3b + coverage outputs byte-for-byte before any migration", "P2"),
    R("R9-RE-02", "golden fixture before migration", "R9 brief section 10", "frozen registers + rebuild tests",
      "research/coverage_recovery_round (rebuild test); research/alsenan_multi_engine_comparison "
      "(s3_1 snapshot); freeze manifests", "-", "-", "tests/coverage_recovery_engine/test_alsenan_coverage_round.py",
      "PARTIAL", "byte-identical rebuilds exist per round", "a single URBAN_KW_V1 golden set across trades",
      "-", "none", "none", "high", "low", "low", "none", "none", "ADOPT", "no",
      "URBAN_KW_V1 golden: every released quantity + its receipt hashed", "P1"),
    # ---- geometry backend ------------------------------------------------------------------------------------
    R("R9-GB-01", "formal GeometryBackend (URBAN_NATIVE / SHAPELY / CLIPPER2 / CAD_ORACLE)", "research pack",
      "native kernels in engine/source; shapely imported directly by ~45 legacy engine/ modules; two declared "
      "engine/source exceptions; run manifest records loaded GEOS version", "engine/source/topology.py (native); "
      "topology_crosscheck.py, ground_slab_recovery.py (shapely, declared); engine/*.py (shapely, undeclared); "
      "run_manifest.loaded_geos_version", "-", "-", "tests/r8_1/test_r8_1_boundaries.py", "PARTIAL",
      "engine/source is stdlib-only by test, with named exceptions",
      "one registry: backend id + version per module, recorded in every run", "-", "low", "none", "high", "low",
      "low", "shapely BSD-3; Clipper2 BSL-1.0 (if ever)", "none now", "ADAPT", "no",
      "a register test: every geometry-library import is declared with its backend id; manifests carry the id",
      "P1"),
    R("R9-GB-02", "port legacy engine/ shapely modules to a backend interface", "research pack",
      "legacy architectural E-series modules", "engine/*.py", "-", "-", "older suites", "PARTIAL", "-", "-", "-",
      "none", "none", "low", "high", "high", "-", "-", "DEFER", "no", "-", "DEFER"),
]


DONOR_COLS = ["TECHNIQUE", "URBAN", "U_C4N", "CHRISTIANNP", "ROOMGRAPH", "OPENTAKEOFF", "REBAR_TAKEOFF",
              "BEST_CURRENT_METHOD", "WHY", "KNOWN_DEFECT", "DECISION", "NEXT_TEST"]


def D(t, urban, uc4n, cnp, rg, ot, rt, best, why, defect, dec, nxt):
    return dict(zip(DONOR_COLS, [t, urban, uc4n, cnp, rg, ot, rt, best, why, defect, dec, nxt]))


NH = "NOT_HELD (pack)"
DONORS = [
    D("ATTRIB schedule extraction", "S1 schedule_table + schedule_grammar (handles, raw ATTRIBs)", "direct ATTRIB",
      "schedule ATTRIB (report)", NH, "scheduleParse.ts (silent row drop rejected)", NH, "URBAN",
      "drawn column wins over tag; raw kept; conflicts recorded", "BOXED semantics unresolved", "PRODUCTION",
      "BOXED interpretation stays BLOCKED until a source/claim"),
    D("source handles", "on census, bands, faces, pairs", "yes", "not delivered", NH, "shape ids", NH, "URBAN",
      "handle + block path identity", "V3b BOQ lines carry no handles", "PRODUCTION", "receipt test on V3b lines"),
    D("physical occurrence census", "S1 + population_conservation", "independent census", "yes", NH, "-", NH,
      "URBAN", "terminal state per object", "-", "PRODUCTION", "-"),
    D("footing outline / tag dual route", "structural_schedule.footing_occurrences (marks + candidates)", "partial",
      "outlines + tags", NH, "-", NH, "URBAN (needs explicit dual-route reconcile)", "-", "F3 / F-F10 / FN",
      "PRODUCTION", "test_footing_outline_two_tags_is_source_conflict"),
    D("beam face pairing", "structural_schedule.beam_bands, wall_band_reconciliation", "beam-face pairing",
      "parallel strips (R1-R5)", NH, "-", NH, "URBAN", "positive constraints", "8 unbound tags", "PRODUCTION", "-"),
    D("beam tag binding", "beam_binding (namespaces, never nearest-text)", "yes", "R1-R5 (R5 rejected)", NH, "-", NH,
      "URBAN", "-", "-", "PRODUCTION", "width gate test (R4 idea)"),
    D("collinear continuation", "beam_occurrence_recovery continuity route", "-", "R2", NH, "-", NH,
      "URBAN + R2 idea as CANDIDATE", "-", "-", "PRODUCTION (candidate only)",
      "test_continuation_stops_at_support_with_new_tag"),
    D("width-to-schedule validation", "drawn_vs_schedule on columns; partial on beams", "-", "R4 (60 mm)", NH, "-", NH,
      "URBAN + R4 as gate", "-", "-", "PRODUCTION", "test_width_mismatch_flags_binding"),
    D("region intersection", "cad_guards.segment_intersects_region", "start-point clipping (defect)", "-", NH, "-",
      NH, "URBAN", "true intersection", "-", "PRODUCTION", "-"),
    D("slab polygon extraction", "B2A1 slab regions + slab_opening_reconciliation", "-", "raster", NH, "-", NH,
      "URBAN", "vector + ids per opening", "GF conflict void", "PRODUCTION", "-"),
    D("raster / flood-fill slab oracle", "raster_topology (arch, research-era)", "-", "50 mm, 5 classes", NH,
      "rastermask.ts / oneclick", NH, "independent Urban rebuild", "independent route", "edge cells, leaks",
      "CHALLENGER", "convergence 100/50/25/10 mm"),
    D("opening reconstruction", "opening_evidence V3 / completion / reveals", "-", "-", NH, "doorseal.ts", NH,
      "URBAN", "-", "-", "PRODUCTION", "-"),
    D("wall-face pairing", "wall_band_reconciliation Method B", "face pairing", "raw pairs", NH, "-", NH, "URBAN",
      "per-metre classes", "finish-line pairs", "PRODUCTION (cross-route)", "finish-line rejection fixture"),
    D("room-cycle extraction", "TS01 + Route B + GEOS cross-check", "hand-rolled planar kernel (rejected)", "-", NH,
      "arrangement.ts (weld/split/faces)", NH, "URBAN", "two independent routes", "-", "PRODUCTION", "-"),
    D("room adjacency", "room_matrix view; no graph object", "-", "-", NH, "-", NH, "MISSING graph",
      "needed for wall Method C", "-", "PRODUCTION (P1)", "every face -> 0/1/2 rooms"),
    D("physical wall-face extraction", "physical_wall_faces (coverage round), wall_faces_v2", "-",
      "gross faces (A10)", NH, "-", NH, "URBAN", "interval - member, per face", "-", "PRODUCTION", "-"),
    D("scale calibration", "frame UNIT_CONTEXT, raster calibration, calibration_v2", "unit_of default mm (rejected)",
      "-", NH, "scaleConfirmed warn-not-block (rejected)", NH, "URBAN", "frozen rule", "PDF page gate soft",
      "PRODUCTION", "PDF quantity without verified frame -> BLOCKED"),
    D("provenance receipt", "run_manifest + boq_report TRACE (arch)", "handles", "-", NH, "provenance.schema.json",
      NH, "URBAN arch path", "digest-bound", "structural lines weak", "PRODUCTION", "receipt coverage test"),
    D("human correction lineage", "claims, never edits", "-", "-", NH, "proposed_verts_norm + edits", NH,
      "OpenTakeoff idea (for a future UI)", "-", "-", "DEFER", "-"),
    D("rule profiles", "method registers + profiles JSON", "-", "-", NH, "rules.ts", NH, "URBAN for now", "-",
      "conventions inside modules", "DEFER (golden first)", "URBAN_KW_V1 golden"),
    D("rebar annotation parsing", "3 parsers (schedule_grammar, bar_spec, slab_rebar_binding.parse)", "partial",
      "partial (unresolved list)", NH, "-", NH, "URBAN, unified", "-", "parser duplication", "PRODUCTION (P0)",
      "single-grammar token corpus"),
    D("BBS model", "rebar_model + accurate_boq_rebar + bbs_optimiser", "simplified ties (rejected)",
      "incomplete (22.916 t)", NH, "-", NH, "URBAN", "RF.1 firewall", "-", "PRODUCTION", "S4"),
    D("revision diff", "source revisions, revision delta, source_anchor", "snapshot diff", "-", NH,
      "snapshotDiff.js", NH, "URBAN", "-", "-", "PRODUCTION", "-"),
    D("scenario quantities", "quantity_scenarios", "-", "-", NH, "-", NH, "URBAN", "unique to Urban", "-",
      "PRODUCTION", "-"),
]

PROV_FIELDS = ["project", "drawing hash", "revision", "sheet/layout/page", "source handles / bbox", "raw text",
               "geometry method", "unit context / scale", "rule/profile id", "formula", "inputs", "measurement state",
               "authority state", "release state", "scenario bounds", "confidence factors", "conflicts",
               "remediation attempts", "machine-original geometry", "human-reviewed geometry", "validation results",
               "version stamp"]
FAM = ["ARCH_R8_RUN_AND_REPORT_ROW", "STRUCTURAL_S1_CENSUS_ROW", "STRUCTURAL_V3B_BOQ_LINE", "COVERAGE_SCENARIO_PART"]
PROV = {   # field -> (arch, s1, v3b, coverage) ; YES / PARTIAL / NO with where
    "project": ("YES run manifest (revision bound)", "YES register header", "YES file schema", "YES round"),
    "drawing hash": ("YES source_anchor_sha256", "PARTIAL drawing name, sha in INDEX", "NO", "YES freeze input / "
                                                                                          "extract sha"),
    "revision": ("YES source_revision_id", "PARTIAL", "NO", "NO"),
    "sheet/layout/page": ("YES region_id / frame_id", "YES sheets / page", "NO", "PARTIAL (extract)"),
    "source handles / bbox": ("YES sites / surface ids", "YES handles", "NO (free-text trace)", "PARTIAL (part ids; "
                                                                                              "pairs have handles)"),
    "raw text": ("YES texts in canonical input", "YES raw_attributes", "NO", "NO"),
    "geometry method": ("YES method id + contract version", "PARTIAL", "PARTIAL formula text", "YES module"),
    "unit context / scale": ("YES unit_claim_id + native_to_mm", "PARTIAL (umm)", "NO", "NO"),
    "rule/profile id": ("YES rule_ids + policy digests", "YES rule register ids", "PARTIAL authority text",
                        "PARTIAL (why)"),
    "formula": ("YES (method)", "PARTIAL", "YES formula", "PARTIAL"),
    "inputs": ("YES canonical_input_digest", "YES", "PARTIAL details", "YES freeze inputs"),
    "measurement state": ("PARTIAL (release status)", "PARTIAL (terminal_state)", "PARTIAL status",
                          "YES measurement_state"),
    "authority state": ("YES authority_digest", "YES type_authority", "PARTIAL authority", "YES authority_state"),
    "release state": ("YES release_state", "NO", "YES release (technical / commercial)", "YES derived"),
    "scenario bounds": ("NO", "NO", "PARTIAL commercial low / high", "YES"),
    "confidence factors": ("NO (by design: authority levels)", "NO", "PARTIAL confidence letter", "NO"),
    "conflicts": ("YES blockers / root questions", "YES conflict states", "PARTIAL status", "YES SOURCE_CONFLICT"),
    "remediation attempts": ("PARTIAL owner queue", "PARTIAL review queue", "NO", "YES remediation records"),
    "machine-original geometry": ("YES source immutable", "YES", "n/a", "YES"),
    "human-reviewed geometry": ("NO (claims only, by design)", "NO", "NO", "NO"),
    "validation results": ("YES gates / cross-checks", "YES conservation", "PARTIAL", "YES anomalies"),
    "version stamp": ("YES code_commit + CODE_BOUND_DIGEST", "PARTIAL (INDEX)", "NO", "PARTIAL (freeze)"),
}

SCALE = {
    "DXF_DWG": {"physical_units": "UNIT_CONTEXT from >= 2 independent evidence kinds (frame.py frozen rule); "
                                  "INSUNITS is a DECLARATION only",
                "drawing_scale": "REGION_MEASUREMENT_TRANSFORM per region (enlarged details are region scales)",
                "dimlfac_unit_conflicts": "act_measurement / defpoint ratio families (unit_evidence); CONFLICT on "
                                          "> 0.5 % disagreement",
                "page_scale": "scale notes recorded as observations, never model-space truth",
                "known_dimension_calibration": "checked-dimension residual census",
                "verification_status": "VERIFIED / CONFIRMED_BY_HUMAN / PROVISIONAL / UNCONFIRMED / CONFLICT / BLOCKED",
                "true_gate": "YES (canonical_input fail-closed + frame status)", "gap": "none"},
    "VECTOR_PDF": {"physical_units": "page units -> calibration object (calibration_v2: UNIFORM / XY / AFFINE)",
                   "drawing_scale": "per-sheet calibration; vector/raster frame transform proved (frames.py)",
                   "dimlfac_unit_conflicts": "n/a", "page_scale": "printed scale as evidence",
                   "known_dimension_calibration": "printed dimensions measured on the page",
                   "verification_status": "calibration object state; NOT an enforced UNIT_CONTEXT at quantity time",
                   "true_gate": "PARTIAL", "gap": "no hard rule that a PDF-derived length needs a VERIFIED page frame "
                                                  "before it enters a quantity (R9-SC-02)"},
    "RASTER_PDF": {"physical_units": "raster_evidence.calibrate from >= 2 printed dimensions",
                   "drawing_scale": "per sheet / crop", "dimlfac_unit_conflicts": "n/a",
                   "page_scale": "nominal scale only as a check", "known_dimension_calibration": "yes",
                   "verification_status": "measurement grades + cross-sheet checks", "true_gate": "YES (evidence lane)",
                   "gap": "raster claims enter only as evidence / claims; keep"},
    "IFC": {"physical_units": "not supported", "drawing_scale": "n/a", "dimlfac_unit_conflicts": "n/a",
            "page_scale": "n/a", "known_dimension_calibration": "n/a", "verification_status": "n/a",
            "true_gate": "NO (no IFC route)", "gap": "only when an IFC project arrives (DEFER)"},
}


def head():
    return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def csv_text(rows, cols):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def dumps(o):
    return json.dumps(o, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def apply_pack():
    """v2: overlay the pack evidence on the v1 rows (v1 text kept where the pack changed nothing)."""
    import pack_v2 as PV
    rows = []
    for r in ROWS:
        r = dict(r)
        ov = PV.OVERRIDES.get(r["RECOMMENDATION_ID"], {})
        changed = sorted(k for k, v in ov.items() if r.get(k) != v)
        r.update(ov)
        for k, v in list(r.items()):
            if isinstance(v, str) and PACK in v:
                raise ValueError(f"{r['RECOMMENDATION_ID']}.{k} still says {PACK}")
        r["CHANGED_BY_PACK"] = changed
        rows.append(r)
    rows += PV.PACK_ROWS
    donors = []
    for d in DONORS:
        d = dict(d, **PV.MATRIX_DONOR_UPDATES.get(d["TECHNIQUE"], {}))
        d[PV.DONOR_NEW_COLUMN] = PV.DONOR_NEW_COLUMN_VALUES.get(d["TECHNIQUE"], "-")
        for k, v in list(d.items()):
            if v == NH:
                d[k] = "not applicable to this donor" if k in ("ROOMGRAPH", "REBAR_TAKEOFF") else v
        donors.append(d)
    donors += PV.NEW_DONOR_ROWS
    return PV, rows, donors


def main():
    PV, rows, donors = apply_pack()
    meta = {"pack": "Urban_BOQ_Research_Pack_2026-10-07.zip", "pack_sha256": PV.PACK_SHA256,
            "pack_status": f"DELIVERED and read in full ({PV.PACK_FILES} files)",
            "basis": "pack + Urban HEAD code + local donors at DONORS.lock commits (U-C4N cdb10638, OpenTakeoff "
                     "e6d2251c) + RoomGraph / aec-qto / Rebar-Takeoff verified at pinned commits (LICENSE, README, "
                     "docs, manifests read; no code copied) + christiannp forensic package",
            "v1_commit": "a75b845"}
    cols = COLS + ["CHANGED_BY_PACK", "DECISION"]
    dcols = DONOR_COLS[:7] + [PV.DONOR_NEW_COLUMN] + DONOR_COLS[7:]
    for r in rows:
        r.setdefault("DECISION", "-")
    prov_rows = [dict(FIELD=f, **dict(zip(FAM, PROV[f]))) for f in PROV_FIELDS]
    flat = lambda rs: [{k: ("; ".join(v) if isinstance(v, list) else v) for k, v in r.items()} for r in rs]  # noqa
    out = {
        "R9_ARCHITECTURE_GAP_MATRIX.json": dict(meta, columns=cols, rows=rows),
        "R9_ARCHITECTURE_GAP_MATRIX.csv": csv_text(flat(rows), cols),
        "DONOR_TECHNIQUE_MATRIX.json": dict(meta, columns=dcols, rows=donors),
        "DONOR_TECHNIQUE_MATRIX.csv": csv_text(donors, dcols),
        "PROVENANCE_FIELD_COVERAGE.csv": csv_text(prov_rows, ["FIELD", *FAM]),
        "SCALE_GATE_AUDIT.json": dict(meta, sources=SCALE, pack_scale_states_mapping={
            "unknown": "BLOCKED / no frame", "candidate": "UNCONFIRMED or PROVISIONAL",
            "auto_verified": "VERIFIED (Urban needs >= 2 independent evidence kinds)",
            "human_verified": "CONFIRMED_BY_HUMAN (bound to the source hash)", "conflicted": "CONFLICT"}),
        "R9_LICENCE_DEPENDENCY_REGISTER.json": dict(meta, verified_donors=PV.VERIFIED, pack_claim_only=PV.PACK_ONLY,
                                                    urban_runtime_imports=URBAN_IMPORTS),
        "PACK_RECOMMENDATION_MAP.json": dict(meta, rows=PACK_MAP),
    }
    for name, obj in out.items():
        (HERE / name).write_text(obj if isinstance(obj, str) else dumps(obj), encoding="utf-8")
    return out, rows


URBAN_IMPORTS = {   # third-party imports found in engine/ (grep at HEAD), with licence
    "shapely": "BSD-3-Clause; ~45 engine/ modules + 2 declared engine/source exceptions",
    "ezdxf": "MIT; K2 route (engine/source/cad/kernel_ezdxf.py)",
    "openpyxl": "MIT; workbook IO", "numpy": "BSD-3-Clause", "PIL (Pillow)": "HPND (permissive)",
    "scipy": "BSD-3-Clause (research / tests)",
    "pymupdf (fitz)": "AGPL-3.0 or commercial - 6 production engine/ modules; NOT in DONORS.lock / "
                      "THIRD_PARTY_PROVENANCE; requirements.txt only as an optional comment -> R9-LIC-01",
    "LibreDWG dwgread": "GPL-3.0, external binary producing JSON (not linked)",
    "tesseract": "Apache-2.0, optional external binary",
}

PACK_MAP = [   # every pack recommendation -> R9 row(s)
    {"pack_ref": "01 #1 facts vs rules", "rows": ["R9-QF-01", "R9-QF-02"]},
    {"pack_ref": "01 #2 provenance receipt", "rows": ["R9-PR-01", "R9-PR-07", "R9-EX-01"]},
    {"pack_ref": "01 #3 scale gate", "rows": ["R9-SC-01", "R9-SC-02", "R9-SC-03"]},
    {"pack_ref": "01 #4 Shapely / Clipper2 topology layer", "rows": ["R9-GB-01", "R9-GB-02"]},
    {"pack_ref": "01 #5 RoomGraph", "rows": ["R9-RG-01", "R9-RG-02", "R9-RG-03", "R9-RG-04", "R9-RG-05",
                                             "R9-RG-06", "R9-RG-07", "R9-RG-08", "R9-RG-09"]},
    {"pack_ref": "01 #6 rebar evidence ladder", "rows": ["R9-RB-01", "R9-RT-02", "R9-RT-05"]},
    {"pack_ref": "01 #7 ambiguity reduces totals", "rows": ["R9-ST-01"]},
    {"pack_ref": "01 #8 declarative profiles + golden", "rows": ["R9-RE-01", "R9-RE-02", "R9-RE-03"]},
    {"pack_ref": "01 #9 permissive PDF stack / PyMuPDF", "rows": ["R9-LIC-01", "R9-PDF-01"]},
    {"pack_ref": "01 #10 IFC adapter", "rows": ["R9-SC-04"]},
    {"pack_ref": "01 #11 revision / cross-sheet identity", "rows": ["R9-REV-01"]},
    {"pack_ref": "01 #12 one math library", "rows": ["R9-OT-01"]},
    {"pack_ref": "01 #13 rebar layers / OR-Tools", "rows": ["R9-RB-02", "R9-RB-03", "R9-QF-03"]},
    {"pack_ref": "01 #14 formwork contact", "rows": ["R9-FW-01"]},
    {"pack_ref": "01 #15 native AutoCAD challenger", "rows": ["(existing cad_oracle; no row)"]},
    {"pack_ref": "01 #16 explain quantity", "rows": ["R9-EX-01"]},
    {"pack_ref": "01 #17 multi-standard recomputation", "rows": ["R9-QF-02", "R9-RE-01"]},
    {"pack_ref": "01 #18 benchmark product", "rows": ["R9-BM-01"]},
    {"pack_ref": "03 F factorised confidence / statuses", "rows": ["R9-ST-01", "R9-PR-02"]},
    {"pack_ref": "04 R9.1-R9.8, R10.0-R10.3", "rows": ["R9-PR-01", "R9-SC-02", "R9-GB-01", "R9-RG-09", "R9-RE-01",
                                                      "R9-RT-05", "R9-RB-02", "R9-REV-01", "R9-PDF-01", "R9-SC-04",
                                                      "R9-FW-01", "R9-RB-03", "R9-MCP-01"]},
    {"pack_ref": "05 donors cad-ai-agent / ConMCP / tianzheng / Plansight", "rows": ["R9-AG-01", "R9-SV-01",
                                                                                      "R9-PDF-01"]},
    {"pack_ref": "06 licence gate", "rows": ["R9-LIC-01", "R9-LIC-02"]},
    {"pack_ref": "07 metrics / taxonomy / blind protocol", "rows": ["R9-BM-01"]},
    {"pack_ref": "14 F review priority", "rows": ["R9-RV-01"]},
    {"pack_ref": "14 G correction corpus", "rows": ["R9-PR-03"]},
]


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(HERE))
    o, rows = main()
    from collections import Counter
    print(len(rows), Counter(r["STATUS"] for r in rows), Counter(r["RECOMMENDATION"] for r in rows),
          Counter(r["PRIORITY"] for r in rows))
    print([r["RECOMMENDATION_ID"] for r in rows if r["CHANGED_BY_PACK"] and r["CHANGED_BY_PACK"] != ["NEW_ROW"]])
