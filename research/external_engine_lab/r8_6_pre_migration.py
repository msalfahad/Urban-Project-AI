"""R8.6 — PRE-MIGRATION PROOF REGISTERS (design and evidence only; nothing is migrated).

Builds, from the R8.6 round-1 proof (r8_6_canonical_rebuild.py) and the committed R8.5 registers:

  OWNER_ACTION_REGISTER         every open owner / external action, none marked resolved without owner input
  QORTUBA_DEPENDENCY_GRAPH      SOURCE -> ... -> QUANTITY ROW per round-1 row, node status and what blocks what
  QORTUBA_BLOCKER_REGISTER      every non-migratable Qortuba row: what is missing and what kind of missing it is
  LEGACY_LOGIC_AUDIT            every dependency of the six rows, classified GENERIC / ADAPTER FACT / LEGACY / BENCHMARK
  ROUND1_CAPABILITY_SIGNATURES  the exact signatures round 1 needs, by dimension, QUALIFIED = NO
  INDEPENDENT_PARSER_TEST_PLAN  the scoped future test for an admitted Qortuba export
  ACTIVE_PATH_DEFECT_REGISTER   the Al Rashed closed-bit defect, versioned, geometry question separate from trade
  MIGRATION_TRANSACTION         the round-1 transaction, its abort conditions and rollback (design)
  R8_6_DECISION_REGISTER        what R8.6 decided and why

    python3 research/external_engine_lab/r8_6_pre_migration.py [register_dir]
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))

from engine.source import independent_export as IX                                     # noqa: E402
from engine.source import qualification as Q                                            # noqa: E402

REG = ROOT / "tests/r8_6/registers"
R85 = ROOT / "tests/r8_5/registers"
R85_OUT = ROOT / "research/external_engine_lab/outputs/r8_5"
APPROVED = ROOT / "data/experiments/P7757_WALL_TREATMENT_ESTIMATE_01/pa08_qortuba_boq/APPROVED_QUANTITIES.json"
QORTUBA_SHA = "2ec3a9c8b66eb2e129275b87010f4a8d79d7e5bdcc31c1897c14fd7e5647d355"
P7757_SHA = "7f61f3acdd62d62dc745f8b522f8136cb41c575df36ec6d9f27c2fe48fea41e3"
ALRASHED_SHA = "299c61b1df7660384e027d44c0a29d8b64c92995843c0517cea05d485974660c"
STATES = ("READY", "BLOCKED", "PENDING_OWNER", "PENDING_EXTERNAL", "NOT_MIGRATED")
MISSING_KINDS = ("ENGINE_MISSING", "RULE_MISSING", "SOURCE_EVIDENCE_MISSING", "OWNER_DECISION_REQUIRED",
                 "EXTERNAL_PARSER_REQUIRED")
AUDIT_CLASSES = ("GENERIC_URBAN_METHOD", "PROJECT_ADAPTER_FACT", "LEGACY_PROJECT_LOGIC", "BENCHMARK_ONLY")


def jl(p):
    return json.loads(Path(p).read_text())


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


# ====================================================================== owner actions (§21)
def owner_actions():
    A = []

    def add(aid, project, q, why, src, choices, blocked, urgency):
        A.append({"action_id": aid, "project": project, "question": q, "why_needed": why, "exact_source_hash": src,
                  "choices": choices, "what_is_blocked": blocked, "urgency": urgency, "status": "OPEN",
                  "resolved_only_by": "explicit owner input recorded as an authorised claim (release V3)"})
    add("CONFIRM_QORTUBA_NATIVE_UNIT", "QORTUBA",
        "What is the native drawing unit of this exact DWG (one drawing unit = how many millimetres)?",
        "every round-1 area scales with the square of the unit; the active path read cm from INSUNITS, which the "
        "canonical policy does not accept as confirmation. The room method also uses mm thresholds, so the unit "
        "affects which rooms exist, not only their scale", QORTUBA_SHA, ["mm", "cm", "m", "other (state it)"],
        ["unit context", "measurement frame", "physical value of Q-03, Q-03P, Q-11, Q-12, Q-13, Q-14"], "HIGH")
    add("REVIEW_QORTUBA_SECOND_FLOOR_PLAN_DESIGNATION", "QORTUBA",
        "Is region RC:MODEL_SPACE:4267:540:1649 (title text handle 428 'SECOND FLOOR PLAN') the second-floor plan "
        "these rows are measured in?", "a detected label is a candidate; only a reviewer with authority makes it a "
        "designation", QORTUBA_SHA, ["ACCEPT", "REJECT", "ACCEPT_WITH_CHANGED_EXTENT"],
        ["region status", "measurement frame", "all round-1 rows"], "HIGH")
    add("APPROVE_QORTUBA_ROUND1_BASELINE_ROWS", "QORTUBA",
        "Are the current six rows (Q-03, Q-03P, Q-11, Q-12, Q-13, Q-14) the approved baseline that a migration "
        "would supersede?", "all six rows are STATUS FINAL but APPROVAL_STATUS DRAFT; a migration supersedes an "
        "approved version and never an unreviewed draft", QORTUBA_SHA, ["APPROVE_AS_BASELINE", "REVIEW_FIRST"],
        ["migration transaction step 1 (baseline selection)"], "MEDIUM")
    add("CONFIRM_Q14_CEILING_HAS_NO_VOID_OR_OPENING", "QORTUBA",
        "In the ten apartment rooms, is there any void, stair opening, shaft or open-to-above condition in the "
        "ceiling?", "Q-14 sets ceiling area = floor region; the method records VOID / STAIR_OPENING / SHAFT / "
        "OPEN_TO_ABOVE = False without testing them (no reflected ceiling plan exists)", QORTUBA_SHA,
        ["NONE", "YES (name the rooms)"], ["Q-14 release"], "MEDIUM")
    add("SUPPLY_INDEPENDENT_QORTUBA_DXF", "QORTUBA",
        "Please export the exact Qortuba DWG to DXF with AutoCAD (2018 DXF, AC1032) or the ODA File Converter, "
        "without editing, exploding, purging, auditing, rescaling or cleaning, and state the tool, version and settings.",
        "round 1 needs its 10 capability signatures exercised by an independent parser; the P7757 export does not "
        "cover Qortuba", QORTUBA_SHA, None, ["decoder qualification for round 1", "all round-1 rows"], "HIGH")
    add("SUPPLY_INDEPENDENT_P7757_DXF", "P7757",
        "Please export the exact P7757 DWG (AutoCAD 2018 DXF, AC1032, or ODA) with no edits, explodes, purges, audits, "
        "rescale or cleanup, and state tool, version and settings.",
        "INDEPENDENT_REAL_RECONCILIATION is BLOCKED_EXTERNAL_INPUT; the two supplied DXFs are ezdxf conversions "
        "(DIAGNOSTIC_NONQUALIFYING_CONVERSION)", P7757_SHA, None, ["P7757 independent reconciliation"], "MEDIUM")
    add("DECIDE_COLUMN_DEDUCTION_METHOD", "ALRASHED",
        "Are column footprints inside a room deducted from the floor-finish quantity?",
        "the closed-polyline defect fix would change BA-092 from 146.97 to 146.7697 m2 (column-net); neither value "
        "may be chosen until the trade rule is decided", ALRASHED_SHA,
        ["DEDUCT_ALL_COLUMN_FOOTPRINTS", "DO_NOT_DEDUCT", "DEDUCT_ABOVE_A_STATED_AREA"],
        ["Al Rashed floor-finish rows", "applying the closed-bit fix"], "MEDIUM")
    add("CONFIRM_P7757_NATIVE_UNIT", "P7757", "What is the native drawing unit of this exact DWG?",
        "P7757 unit context is UNCONFIRMED", P7757_SHA, ["mm", "cm", "m", "other"], ["P7757 physical values"], "LOW")
    add("RESOLVE_ALRASHED_UNIT_CONFLICT", "ALRASHED", "Which unit governs this DWG (the evidence conflicts)?",
        "Al Rashed unit context is CONFLICT: every value is VALUE_NOT_COMPUTABLE", ALRASHED_SHA,
        ["mm", "cm", "m", "other"], ["all Al Rashed physical values"], "LOW")
    add("REVIEW_ALRASHED_ADAPTER_WINDOWS", "ALRASHED", "Are the adapter's three floor windows the plan regions?",
        "the windows are adapter constants, PENDING_REVIEW", ALRASHED_SHA, ["ACCEPT", "REJECT", "CHANGE"],
        ["Al Rashed region designation"], "LOW")
    return {"SCHEMA": "URBAN_R8_6_OWNER_ACTION_REGISTER_V1",
            "rule": "no action is marked resolved without explicit owner input; nothing in this register is inferred",
            "actions": A, "open": len(A), "resolved": 0}


# ====================================================================== legacy logic audit (§10)
def legacy_audit(proof):
    rows = [
        ("pipeline7 ingest (bands, faces, sites, grids, planar faces)", "engine/ingest/pipeline7.py",
         "GENERIC_URBAN_METHOD", "engine package with no-project-constant tests (PA05-PA07)", "ALL"),
        ("unit selection: INSUNITS first, accepted SOURCE_ESTABLISHED", "engine/ingest/source_units.py",
         "LEGACY_PROJECT_LOGIC",
         "legacy active-path policy, not project-specific: INSUNITS 5 -> cm accepted although the method's own secondary "
         "check failed (modal wall pair 714.5 mm, outside 50-600 mm). Superseded by the canonical unit policy "
         "(UNCONFIRMED); the round may not use it", "ALL"),
        ("method thresholds in millimetres (snap 2 mm, shaft 600 mm, terrace 3.0 m2, guard 0.9 m2, raster cell)",
         "r3/floor_regions.py, qs01/takeoff.py", "GENERIC_URBAN_METHOD",
         "generic heuristics, but they make the method NOT scale-invariant: the unit decides which cells are rooms",
         "ALL"),
        ("cell classes, stair / roof tokens incl. Arabic 'سطح'", "r2/cells.py", "GENERIC_URBAN_METHOD",
         "generic vocabulary; located in a project folder, needs promotion", "ALL"),
        ("room inventory: layer names 'STAIR' and 'lift' exclude a cell from the apartment", "qs01/takeoff.py",
         "PROJECT_ADAPTER_FACT", "exact layer names of this drawing; must become adapter facts, not method code", "ALL"),
        ("room inventory: labelled cell = apartment room; unlabelled cell with an apartment door = room",
         "qs01/takeoff.py", "GENERIC_URBAN_METHOD", "generic rule; depends on labels (canonical) and door sites", "ALL"),
        ("wet classes BATHROOM, WC, KITCHEN, LAUNDRY, WASHROOM", "qs01/takeoff.py, r2/cells.py",
         "GENERIC_URBAN_METHOD", "generic semantic classes", "Q-03, Q-11, Q-13"),
        ("STOREY constant 'SECOND_FLOOR (title block ...)'", "qs01/takeoff.py", "PROJECT_ADAPTER_FACT",
         "label only, never enters a value; it is the designation still PENDING_REVIEW", "ALL (metadata)"),
        ("CERAMIC_ROOM_NAMES = ('BATH', 'PAINTRY')", "boq/owner_rules.py", "PROJECT_ADAPTER_FACT",
         "owner-approved project rule QP-07 (the pantry is a ceramic service room), keyed on the drawing's spelling "
         "'PAINTRY'; it decides membership of Q-03P, Q-12 and Q-13", "Q-03P, Q-12, Q-13"),
        ("Q-03 / Q-11 rooms=['BATH','BATH','BATH'] and 'the three bathroom floor polygons'", "boq/owner_rules.py",
         "LEGACY_PROJECT_LOGIC",
         "hardcoded room list and wording; does not enter the value (the value sums the WET floors), but would be "
         "wrong metadata if the room set changed. Replace by computed membership before migration", "Q-03, Q-11"),
        ("Q-14 extra CEILING_PERIMETER_NOT_A_PAYABLE_ITEM_LM = 153.125", "boq/owner_rules.py", "LEGACY_PROJECT_LOGIC",
         "hardcoded number in row metadata; not in the value", "Q-14"),
        ("ceiling area = floor region; VOID / STAIR_OPENING / SHAFT / OPEN_TO_ABOVE all False", "qs01/takeoff.py",
         "LEGACY_PROJECT_LOGIC",
         "asserted, not tested: the conditions are constants. Q-14 rests on it (owner action "
         "CONFIRM_Q14_CEILING_HAS_NO_VOID_OR_OPENING)", "Q-14"),
        ("row expressions for the six rows (sum of floor polygons by class)", "boq/owner_rules.py",
         "GENERIC_URBAN_METHOD", "proven by ablation to need only the floors (all other inputs passed empty)", "ALL"),
        ("benchmark / pricing / contractor registers", "boq/benchmark_seal.py, pricing/*", "BENCHMARK_ONLY",
         "not in the import closure of the six rows (verified)", "NONE"),
    ]
    out = [{"dependency": d, "where": w, "class": c, "evidence": e, "rows_affected": r} for d, w, c, e, r in rows]
    blocking = [x for x in out if x["class"] == "LEGACY_PROJECT_LOGIC" and "value" in x["evidence"]
                and "not in the value" not in x["evidence"] and "does not enter the value" not in x["evidence"]]
    return {"SCHEMA": "URBAN_R8_6_LEGACY_LOGIC_AUDIT_V1", "classes": list(AUDIT_CLASSES),
            "searched_for": ["project name checks", "hardcoded coordinates", "room ids", "manual totals",
                             "project-specific constants", "special-case dimensions", "benchmark-derived values"],
            "search_result": {"hardcoded_coordinates": 0, "hardcoded_room_ids": 0, "manual_totals_in_value_path": 0,
                              "benchmark_imports": 0},
            "dependencies": out, "by_class": dict(Counter(x["class"] for x in out)),
            "legacy_logic_in_value_path": [x["dependency"] for x in out if x["class"] == "LEGACY_PROJECT_LOGIC"
                                           and x["dependency"].startswith(("unit selection", "ceiling area"))],
            "verdict": ("the six values are produced by generic method code plus two project adapter facts (layer "
                        "names, QP-07 membership); two LEGACY items reach values - the INSUNITS unit (blocked: unit "
                        "UNCONFIRMED) and the untested ceiling conditions (Q-14 only) - and two LEGACY items are "
                        "metadata only. The method itself lives in a project research folder and is NOT_MIGRATED"),
            "unused": len(blocking)}


# ====================================================================== capability signatures (§11)
def dims(sig):
    return dict(p.split("=", 1) for p in sig.split("|") if "=" in p)


def round1_signatures(proof):
    sys.path.insert(0, str(ROOT / "research/external_engine_lab"))
    import r8_6_canonical_rebuild as R
    can = R.Canonical()
    allsig = Q.capability_signatures(can.doc)
    need = {}
    for r in proof["rows"]:
        for s in r["source_capability_signatures"]:
            need.setdefault(s, set()).add(r["row_id"].split("|")[0])
    r1_obs = {o for r in proof["rows"] for o in r["source_observations"]}
    r1_occ = {(o, tuple(pth)) for r in proof["rows"] for o, pth in r["source_occurrences"]}
    in_block = {}
    for b in can.doc.blocks.values():
        for o in b.entities:
            in_block[o.obs_id] = b.name
    curve = {"LINE": "STRAIGHT_SEGMENT", "LWPOLYLINE_STRAIGHT": "POLYLINE_STRAIGHT_SPANS",
             "LWPOLYLINE_BULGE": "POLYLINE_WITH_BULGE_ARCS", "ARC": "CIRCULAR_ARC"}
    out = []
    for s in sorted(need):
        d = dims(s)
        occ = allsig.get(s, [])
        r1 = sorted({(k[0], tuple(k[1])) for k in occ if (k[0], tuple(k[1])) in r1_occ},
                    key=lambda x: (int(x[0].split(":")[1].split("+")[0]), x[1]))
        out.append({"signature": s, "entity_kind": d.get("KIND"), "curve_class": curve.get(d.get("KIND"), d.get("KIND")),
                    "transform_chain": d.get("CHAIN"), "reflection_orientation": d.get("NET"),
                    "block_depth": int(d.get("DEPTH", 0)), "ocs_extrusion": d.get("EXT"), "context": d.get("CTX"),
                    "visibility": d.get("VIS"), "handle_representation": d.get("HANDLE"),
                    "source_count": len(occ), "round1_occurrence_count": len(r1),
                    "round1_occurrences": [[o, list(pth)] for o, pth in r1],
                    "blocks": sorted({in_block[o] for o, _ in r1 if o in in_block}),
                    "rows_using_it": sorted(need[s]), "QUALIFIED": "NO",
                    "qualified_when": "EXERCISED_AND_PASS on every compared occurrence against an ADMITTED independent "
                                      "export; no equivalence rule admitted (EQUIVALENCE_RULES = ())"})
    others = sorted(set(allsig) - set(need))
    return {"SCHEMA": "URBAN_R8_6_ROUND1_CAPABILITY_SIGNATURES_V1", "source_sha256": QORTUBA_SHA,
            "required": out, "required_count": len(out), "source_signature_count": len(allsig),
            "round1_observations": len(r1_obs), "round1_occurrences": len(r1_occ),
            "occurrences_inside_block_instances": sum(1 for _, pth in r1_occ if pth),
            "distinct_block_observations": sum(1 for o in r1_obs if o in in_block),
            "net_reflected_occurrences": sum(x["round1_occurrence_count"] for x in out
                                              if x["reflection_orientation"] == "NET_REFLECTED"),
            "not_required_for_round1": [{"signature": s, "source_count": len(allsig[s])} for s in others],
            "qualified": 0, "rule": "no flat-set shortcut: each signature is qualified on its own"}


# ====================================================================== independent parser plan (§12)
def parser_plan(sigs):
    every = {"Q-03", "Q-03P", "Q-11", "Q-12", "Q-13", "Q-14"}
    req = []
    for s in sigs["required"]:
        whole = set(s["rows_using_it"]) == every
        req.append({"signature": s["signature"], "must": "PASS", "occurrences_to_compare": s["round1_occurrence_count"],
                    "failure_blocks": "ENTIRE_ROUND" if whole else "ROWS_ONLY",
                    "rows_blocked_on_failure": s["rows_using_it"]})
    blocks = sorted({b for s in sigs["required"] for b in s["blocks"]})
    return {"SCHEMA": "URBAN_R8_6_INDEPENDENT_PARSER_TEST_PLAN_V1", "source_sha256": QORTUBA_SHA,
            "status": "PLANNED_NOT_RUN", "INDEPENDENT_REAL_RECONCILIATION": "BLOCKED_EXTERNAL_INPUT",
            "step_1_admission": {"function": "engine.source.independent_export.admission",
                                 "tools": list(IX.INDEPENDENT_TOOLS), "requested_format": "AUTOCAD_2018_DXF",
                                 "required_acadver": IX.ACADVER["AUTOCAD_2018_DXF"],
                                 "forbidden_operations": list(IX.FORBIDDEN_OPERATIONS),
                                 "intake_record_fields": ["source DWG sha256", "DXF sha256", "converter product",
                                                          "converter version", "conversion settings", "target DXF version",
                                                          "audit enabled (must be no)", "purge / edit / explode / cleanup "
                                                          "(must be none)", "operator / source statement"],
                                 "failure_blocks": "ENTIRE_ROUND"},
            "step_2_verification": {
                "HANDLE_IDENTITY": {"must": "VERIFIED for every round-1 observation handle",
                                    "why": "every required signature is handle-keyed; ODA is NOT assumed to preserve handles",
                                    "failure_blocks": "ENTIRE_ROUND"},
                "ENTITY_CENSUS": {"must": "equal per (space, type, layer) for the layers and kinds the round-1 observations use, "
                                          "inside region RC:MODEL_SPACE:4267:540:1649",
                                  "failure_blocks": "ENTIRE_ROUND", "outside_scope": "recorded, not blocking"},
                "BLOCK_LINEAGE": {"must": "equal for the blocks round-1 observations sit in", "blocks": blocks,
                                  "failure_blocks": "ROWS_ONLY (rows whose observations sit in the failing block)"},
                "CUSTOM_CLASSES": {"must": "present when used inside the row region",
                                   "note": "the source's unsupported entities (REGION, SPLINE, unknown 518) are outside "
                                           "the six rows; V-CAD-5 is PASS in the row region",
                                   "failure_blocks": "ENTIRE_ROUND only if a custom object appears inside the region"},
                "GEOMETRY": {"must": "K1 vs K2 reconciliation PASS per handle and instance path for every required "
                                     "signature occurrence", "failure_blocks": "per signature (below)"}},
            "step_3_signatures": req,
            "irrelevant_to_round1": [s["signature"] for s in sigs["not_required_for_round1"]],
            "result_rule": "qualification is scoped: a failure outside the ten signatures blocks nothing in round 1; "
                           "a failure inside them blocks exactly the rows listed, or the whole round where every row "
                           "depends on it"}


# ====================================================================== blocker breakdown (§9)
def blocker_register():
    diff = jl(R85_OUT / "SHADOW_VALUE_DIFF.json")["QORTUBA"]["rows"]
    M = {
        "HIDDEN_SKIRTING": [("OPENING_IDENTITY", "ENGINE_MISSING"), ("OPENING_WIDTH", "ENGINE_MISSING"),
                            ("WALL_PERIMETER_METHOD", "ENGINE_MISSING")],
        "HIDDEN_PROFILE_ABOVE_SKIRTING": [("OPENING_IDENTITY", "ENGINE_MISSING"), ("OPENING_WIDTH", "ENGINE_MISSING"),
                                          ("WALL_PERIMETER_METHOD", "ENGINE_MISSING")],
        "WET_AREA_WATERPROOFING_UPTURN": [("WALL_PERIMETER_METHOD", "ENGINE_MISSING"),
                                          ("WATERPROOFING_RULE (classified wall-boundary path)", "ENGINE_MISSING")],
        "PANTRY_WATERPROOFING_UPTURN": [("WALL_PERIMETER_METHOD", "ENGINE_MISSING"),
                                        ("WATERPROOFING_RULE (classified wall-boundary path)", "ENGINE_MISSING")],
        "PANTRY_UPTURN_VERTICAL_AREA_REFERENCE": [("derived from Q-04P", "ENGINE_MISSING")],
        "WET_AREA_UPTURN_VERTICAL_AREA_REFERENCE": [("derived from Q-04", "ENGINE_MISSING")],
        "WALL_CERAMIC_BATHROOMS": [("OPENING_IDENTITY", "ENGINE_MISSING"), ("OPENING_WIDTH", "ENGINE_MISSING"),
                                   ("WALL_PERIMETER_METHOD", "ENGINE_MISSING")],
        "WALL_CERAMIC_SERVICE_ROOM": [("OPENING_IDENTITY", "ENGINE_MISSING"), ("OPENING_WIDTH", "ENGINE_MISSING"),
                                      ("OPENING HOST SIDE (2.750 m HALL/PAINTRY opening)", "OWNER_DECISION_REQUIRED")],
        "BLOCKWORK_200": [("MASONRY_MATERIAL_IDENTITY", "ENGINE_MISSING"), ("HEIGHT (openings without height)",
                                                                          "SOURCE_EVIDENCE_MISSING")],
        "BLOCKWORK_150": [("MASONRY_MATERIAL_IDENTITY", "ENGINE_MISSING"), ("HEIGHT (openings without height)",
                                                                          "SOURCE_EVIDENCE_MISSING")],
        "INTERNAL_PLASTER": [("OPENING_IDENTITY", "ENGINE_MISSING"), ("REVEAL_METHOD", "RULE_MISSING"),
                             ("WALL_PERIMETER_METHOD", "ENGINE_MISSING")],
        "WALL_PAINT": [("OPENING_IDENTITY", "ENGINE_MISSING"), ("REVEAL_METHOD", "RULE_MISSING"),
                       ("WALL_PERIMETER_METHOD", "ENGINE_MISSING")],
        "TILE_PREPARATION_TARTUSHA": [("OPENING_IDENTITY", "ENGINE_MISSING"), ("WALL_PERIMETER_METHOD", "ENGINE_MISSING")],
        "ALUMINIUM_EXTERNAL_WINDOWS": [("OPENING_IDENTITY", "ENGINE_MISSING"), ("OPENING_WIDTH", "ENGINE_MISSING"),
                                       ("GLAZING_RULE", "RULE_MISSING")],
        "PVC_INTERNAL_DOORS": [("OPENING_IDENTITY", "ENGINE_MISSING"), ("OPENING_WIDTH", "ENGINE_MISSING"),
                               ("PRICING BASIS (per door / set / m2, O-09)", "OWNER_DECISION_REQUIRED")],
        "INTERNAL_GLAZED_OPENING": [("GLAZING_RULE (trade classification, O-10)", "OWNER_DECISION_REQUIRED")],
    }
    out = []
    for r in diff:
        if r["value_class"] == "VALUE_EXACT_MATCH":
            continue
        item = r["row_id"].split("|")[1]
        if r["value_class"] == "VALUE_NOT_COMPUTABLE":
            missing = [("no quantity exists at this thickness (NOT_APPLICABLE row)", "SOURCE_EVIDENCE_MISSING")]
        else:
            missing = M[item]
        common = [("UNIT_AUTHORITY", "OWNER_DECISION_REQUIRED"), ("REGION_AUTHORITY", "OWNER_DECISION_REQUIRED"),
                  ("SOURCE_CAPABILITY (independent parser)", "EXTERNAL_PARSER_REQUIRED")]
        out.append({"row_id": r["row_id"], "r8_5_class": r["value_class"], "current_status": r["current_status"],
                    "current_value": r["current_value"], "unit": r["unit"], "rules": r["rules"],
                    "row_specific_missing": [{"what": w, "kind": k} for w, k in missing],
                    "shared_missing": [{"what": w, "kind": k} for w, k in common]})
    kinds = Counter(m["kind"] for x in out for m in x["row_specific_missing"])
    what = Counter(m["what"].split(" (")[0] for x in out for m in x["row_specific_missing"])
    return {"SCHEMA": "URBAN_R8_6_QORTUBA_BLOCKER_REGISTER_V1", "kinds": list(MISSING_KINDS), "rows": out,
            "count": len(out), "row_specific_by_kind": dict(kinds), "row_specific_by_what": dict(what),
            "planning_note": "R9 planning: OPENING_IDENTITY / OPENING_WIDTH (an opening register on canonical geometry) "
                             "and WALL_PERIMETER_METHOD unblock 11 rows; masonry identity 2; reveal and glazing rules are "
                             "rule work; three rows wait on an owner decision"}


# ====================================================================== dependency graph (§8)
def dependency_graph(proof, sigs):
    N = [
        ("SOURCE_FILE", "READY", "source DWG sha256 " + QORTUBA_SHA[:16] + "... matches the pinned decode", []),
        ("SOURCE_OBSERVATIONS", "READY", f"D1 decode; {sigs['round1_observations']} observations bound the ten rooms",
         ["SOURCE_FILE"]),
        ("CAPABILITY_SIGNATURES", "PENDING_EXTERNAL",
         f"{sigs['required_count']} required, 0 qualified; needs an admitted Qortuba AutoCAD/ODA export",
         ["SOURCE_OBSERVATIONS"]),
        ("PHYSICAL_GEOMETRY", "READY", "K1 realisation; the canonical rebuild reproduces every room exactly (shadow)",
         ["SOURCE_OBSERVATIONS"]),
        ("METHOD_INPUT_CONTRACT", "NOT_MIGRATED",
         "block names, part identity, texts and dimensions mapped from D1/K1 in the R8.6 lab; not yet an engine/source "
         "capability", ["PHYSICAL_GEOMETRY"]),
        ("REGION_DESIGNATION", "PENDING_OWNER", "candidate RC:MODEL_SPACE:4267:540:1649, PENDING_REVIEW",
         ["SOURCE_OBSERVATIONS"]),
        ("UNIT_CONTEXT", "PENDING_OWNER", "UNCONFIRMED; active INSUNITS reading not accepted", ["SOURCE_FILE"]),
        ("MEASUREMENT_FRAME", "BLOCKED", "UNCONFIRMED until unit and region are authorised",
         ["UNIT_CONTEXT", "REGION_DESIGNATION"]),
        ("ROOM_METHOD", "NOT_MIGRATED", "QS01 Method A on pipeline7, research code in a project folder",
         ["PHYSICAL_GEOMETRY", "METHOD_INPUT_CONTRACT", "MEASUREMENT_FRAME"]),
        ("ROOM_IDENTITY", "READY", "labels from D1 (61 of 61 equal), wet/dry classes generic, QP-07 approved",
         ["SOURCE_OBSERVATIONS", "ROOM_METHOD"]),
        ("TRADE_METHOD", "NOT_MIGRATED", "owner_rules row expressions (generic sums), project code",
         ["ROOM_METHOD", "ROOM_IDENTITY"]),
        ("CEILING_CONDITIONS", "PENDING_OWNER", "void / stair / shaft / open-to-above asserted False, not tested",
         ["ROOM_METHOD"]),
        ("BASELINE_APPROVAL", "PENDING_OWNER", "current rows are FINAL but approval DRAFT", []),
    ]
    nodes = [{"node": n, "status": s, "evidence": e, "depends_on": d} for n, s, e, d in N]
    rows = []
    for r in proof["rows"]:
        qid = r["row_id"].split("|")[0]
        deps = ["CAPABILITY_SIGNATURES", "TRADE_METHOD", "MEASUREMENT_FRAME", "BASELINE_APPROVAL"]
        if qid == "Q-14":
            deps.append("CEILING_CONDITIONS")
        rows.append({"node": f"QUANTITY_ROW:{qid}", "status": "BLOCKED", "depends_on": deps,
                     "item": r["item"], "value_state": "PREVIEW (shadow)"})
    by = {n["node"]: n for n in nodes}

    def closure(n, seen=None):
        seen = seen if seen is not None else set()
        for d in by.get(n, {}).get("depends_on", ()):
            if d not in seen:
                seen.add(d)
                closure(d, seen)
        return seen
    for r in rows:
        r["blocking_ancestors"] = sorted(d for d in set(r["depends_on"]) | {x for d in r["depends_on"] for x in closure(d)}
                                         if by.get(d, {}).get("status") not in (None, "READY"))
    single = {}
    for n in nodes:
        if n["status"] != "READY":
            single[n["node"]] = sorted(r["node"] for r in rows if n["node"] in r["blocking_ancestors"])
    return {"SCHEMA": "URBAN_R8_6_QORTUBA_DEPENDENCY_GRAPH_V1", "states": list(STATES),
            "chain": "SOURCE_FILE -> SOURCE_OBSERVATIONS -> CAPABILITY_SIGNATURES -> PHYSICAL_GEOMETRY -> "
                     "REGION_DESIGNATION -> UNIT_CONTEXT -> MEASUREMENT_FRAME -> TRADE_METHOD -> QUANTITY_ROW",
            "nodes": nodes, "rows": rows, "what_one_missing_fact_blocks": single}


# ====================================================================== active-path defect (§3, §4)
def defect_register():
    d = jl(R85 / "R8_ADAPTER_DEFECT_CLOSED_FLAG.json")
    xr = d["r8_5_cross_reference"]
    changed_area = [x for x in d["defect_only_counterfactual"]["changed"] if x["state"] == "AREA_CHANGED"]
    return {"SCHEMA": "URBAN_R8_6_ACTIVE_PATH_DEFECT_REGISTER_V1", "defects": [{
        "defect_kind": "ACTIVE_PATH_DEFECT", "defect_id": d["defect_id"], "version": 2,
        "supersedes_version": {"version": 1, "register": "tests/r8_5/registers/R8_ADAPTER_DEFECT_CLOSED_FLAG.json"},
        "affected_source_hash": ALRASHED_SHA,
        "code_location": d["location"], "reference_reading": d["reference_reading"],
        "current_code_sha256": sha(d["location"]["file"]),
        "code_sha256_when_measured": d["no_change_attestation"]["geometry_py_sha256_before"],
        "code_unchanged_since_measured": sha(d["location"]["file"]) == d["no_change_attestation"]["geometry_py_sha256_before"],
        "source_evidence": {"closed_outlines_bit_512": d["affected_closed_outlines"],
                            "dropped_closing_edges": d["dropped_closing_edges_in_floor_windows"],
                            "dropped_closing_edges_total": d["dropped_closing_edges_total"]},
        "geometry_effect": "each closed col.str outline loses its closing edge; the reader's grid merges or splits cells "
                           "across the missing edge",
        "affected_rooms": {"explained_by_defect_alone": xr["explained_by_defect_alone"],
                           "by_r8_5_class": {k: v for k, v in xr["native_checks"].items() if k.startswith("CHANGED")},
                           "rooms": [x["room_ref"] for x in xr["changed_rooms"]]},
        "quantity_effect": [{"room": x["adapter_room_ref"], "name": x["name"], "adapter_area_m2": x["adapter_area_m2"],
                             "with_closed_bit_m2": x["corrected_area_m2"], "delta_m2": x["delta_m2"]}
                            for x in changed_area],
        "trade_rule_interaction": {"room": "BA-092", "values": [146.97, 146.7697], "chosen": None,
                                   "status": "TRADE_DEDUCTION_RULE_UNDECIDED"},
        "questions": {
            "SOURCE_GEOMETRY": {"question": "is the column physically a closed polygon?", "answer": "YES",
                                "basis": "LWPOLYLINE flag bit 512 set (175 outlines); the canonical reader and "
                                         "cad_adapter both read 0x200"},
            "TRADE_METHOD": {"question": "is the column footprint deducted from floor-finish billing?",
                             "answer": "UNDECIDED", "owner_action": "DECIDE_COLUMN_DEDUCTION_METHOD"}},
        "separation_rule": ("a future geometry fix must emit the column footprint inside a room as its own quantity "
                            "(gross room area and column footprint area, both carried), so that the trade rule - not "
                            "the fix - decides whether it is deducted"),
        "fix_status": "NOT_APPLIED", "active_reader_changed": False}]}


# ====================================================================== migration transaction (§17, §18)
ABORTS = [
    ("SOURCE_HASH_CHANGED", "source DWG sha256 differs from the frozen value", "sha256 of the source file"),
    ("DECODE_CHANGED", "D1 decode sha256 differs from the frozen value", "sha256 of the decode"),
    ("DECODER_CHANGED_OR_UNQUALIFIED", "decoder binary differs from the pin, or its V2 qualification is absent / withdrawn",
     "decoder pin + qualification record"),
    ("SIGNATURE_OUTSIDE_QUALIFICATION", "a round-1 observation carries a signature not EXERCISED_AND_PASS",
     "capability_signatures(doc) vs qualification"),
    ("REGION_CHANGED", "designation id, extent or review status differs from the frozen accepted designation",
     "designation record"),
    ("FRAME_EVIDENCE_CHANGED", "frame evidence digest differs from the frozen one", "measurement_frame().evidence_digest"),
    ("UNIT_CHANGED", "unit claim id / value differs, or the claim was superseded", "unit claim (release V3)"),
    ("METHOD_REVISION_CHANGED", "any file of the frozen calculation path changed", "method_code_sha256"),
    ("METHOD_INPUT_CONTRACT_BROKEN", "a canonical input the contract requires is missing (block names, part ids, texts, "
     "dimensions) or differs from the frozen check", "contract ablation + text/dimension equality"),
    ("SOURCE_BLOCKER_APPEARED", "any BLOCKING finding in the row region (V-CAD-5 or source exception)", "source exceptions"),
    ("VALUE_DELTA_OUTSIDE_TOLERANCE", "canonical value rounded to the published precision differs from the approved "
     "value (tolerance 0; no widening)", "per-row comparison"),
    ("ROW_PROVENANCE_MISSING", "a row lacks observation ids, geometry ids, frame id, evidence version, method id, "
     "formula, inputs or qualification id", "provenance check"),
    ("UNEXPECTED_ROW_SET", "a row added, removed or renamed relative to the frozen round-1 scope", "row-id set equality"),
    ("ROOM_SET_CHANGED", "a room added, removed, renamed or re-classified wet/dry relative to the frozen proof",
     "rooms digest"),
    ("OWNER_ACTION_REOPENED", "an owner action this round depends on is not RESOLVED by an authorised claim",
     "owner action register"),
    ("BASELINE_NOT_APPROVED", "the version being superseded is not APPROVED", "row approval status"),
]


def transaction():
    steps = [
        (1, "CREATE_RUN", "create a new QTO run/version id; record the frozen inputs (source, decode, decoder pin, "
                          "qualification id, unit claim id, designation id, frame id, evidence version, method hashes, "
                          "baseline row versions)", ["SOURCE_HASH_CHANGED", "BASELINE_NOT_APPROVED"]),
        (2, "RUN_CANONICAL_SOURCE", "D1 -> K1 -> method-input contract", ["DECODE_CHANGED", "DECODER_CHANGED_OR_UNQUALIFIED",
                                                                         "SIGNATURE_OUTSIDE_QUALIFICATION",
                                                                         "METHOD_INPUT_CONTRACT_BROKEN"]),
        (3, "APPLY_APPROVED_REGION_AND_FRAME", "accepted designation + confirmed unit -> measurement frame (V3)",
         ["REGION_CHANGED", "UNIT_CHANGED", "FRAME_EVIDENCE_CHANGED", "SOURCE_BLOCKER_APPEARED"]),
        (4, "RUN_SIX_APPROVED_METHODS", "rooms (Method A) then the six row expressions",
         ["METHOD_REVISION_CHANGED", "ROOM_SET_CHANGED", "ROW_PROVENANCE_MISSING"]),
        (5, "COMPARE_OLD_VS_NEW", "every row: canonical (rounded to published precision) vs approved baseline",
         ["VALUE_DELTA_OUTSIDE_TOLERANCE", "UNEXPECTED_ROW_SET"]),
        (6, "ABORT_ON_ANY_NON_APPROVED_DIFFERENCE", "any abort condition -> the run is closed ABORTED, nothing published",
         [a[0] for a in ABORTS]),
        (7, "HUMAN_REVIEW", "owner reviews the before/after table and provenance; approval is recorded as a claim",
         ["OWNER_ACTION_REOPENED"]),
        (8, "PUBLISH_NEW_VERSION", "new row versions with supersession records pointing to the baseline versions", []),
        (9, "KEEP_OLD_VERSION_UNTOUCHED", "baseline versions stay byte-identical (hash recorded before and after)", []),
        (10, "ROLLBACK_BY_SELECTING_PREVIOUS_VERSION", "rollback = a further supersession selecting the previous version, "
                                                      "with author and reason; never a delete or an in-place edit", []),
    ]
    return {"SCHEMA": "URBAN_R8_6_MIGRATION_TRANSACTION_V1", "status": "DESIGN_ONLY_NOT_EXECUTED",
            "scope": ["Q-03", "Q-03P", "Q-11", "Q-12", "Q-13", "Q-14"],
            "steps": [{"step": n, "name": a, "does": b, "abort_checks": c} for n, a, b, c in steps],
            "abort_conditions": [{"code": c, "condition": w, "measured_by": m, "on_trigger": "ABORT_FAIL_CLOSED"}
                                 for c, w, m in ABORTS],
            "fail_closed": "an abort check that cannot be evaluated (missing evidence, error) counts as triggered",
            "never": ["overwrite an approved quantity in place", "publish a partial round", "widen a tolerance",
                      "switch the active pipeline", "modify cad_adapter or geometry.py", "begin R9"],
            "rollback": {"how": "supersession selecting the previous version", "who": "an authorised reviewer",
                         "triggers": ["unit claim superseded", "designation rejected", "qualification withdrawn",
                                      "V-CAD-5 regression in the row region", "owner request"],
                         "per_row": True},
            "PRODUCTION_MIGRATION": "NO", "MIGRATION_EXECUTION_READY": "NO"}


# ====================================================================== decisions
def decisions(proof):
    D = [
        ("R86-D01", "The R8.5 six-row 'exact match' is not accepted as proof (it snapped current cut lines). Replaced by "
                    "the full-substitution canonical rebuild.", "DECIDED"),
        ("R86-D02", "Round-1 proof inputs: curves from K1, texts and dimensions from D1 placed through K1 instance paths; "
                    "the remaining active-reader inputs are proven non-dependencies by ablation.", "DECIDED"),
        ("R86-D03", "The session-upload PDF is removed from the canonical runs (proven non-dependency); tests never read "
                    "session uploads.", "DECIDED"),
        ("R86-D04", "Session determinism guard: any write under data/ or tests/ fails the session.", "DECIDED"),
        ("R86-D05", "Villa-inventory test narrowed: no write; artifact self-consistency + in-memory determinism; upload "
                    "drift reported by a separate status step.", "DECIDED"),
        ("R86-D06", "Round-1 scope unchanged: six rows. Q-14 additionally waits on the ceiling-condition owner action.",
         "DECIDED"),
        ("R86-D07", "No gate lowered: unit UNCONFIRMED, designation PENDING_REVIEW, INDEPENDENT_REAL_RECONCILIATION "
                    "BLOCKED_EXTERNAL_INPUT, qualification 0/10.", "DECIDED"),
        ("R86-D08", "The closed-bit defect stays NOT_APPLIED; fix only after the column-deduction rule, and the fix must "
                    "carry the column footprint as its own quantity.", "DECIDED"),
        ("R86-D09", "MIGRATION_PLANNING_READY = YES; MIGRATION_EXECUTION_READY = NO; PRODUCTION_MIGRATION = NO.", "DECIDED"),
    ]
    return {"SCHEMA": "URBAN_R8_6_DECISION_REGISTER_V1",
            "decisions": [{"id": i, "decision": t, "status": s} for i, t, s in D],
            "gates": {"PRODUCTION_MIGRATION": "NO", "MIGRATION_PLANNING_READY": "YES", "MIGRATION_EXECUTION_READY": "NO",
                      "INDEPENDENT_REAL_RECONCILIATION": "BLOCKED_EXTERNAL_INPUT",
                      "QORTUBA_UNIT_CONTEXT": proof["canonical_context"]["unit"],
                      "QORTUBA_REGION": proof["canonical_context"]["region"],
                      "ALRASHED_COLUMN_RULE": "TRADE_DEDUCTION_RULE_UNDECIDED"}}


def main(out: Path = REG):
    out.mkdir(parents=True, exist_ok=True)
    proof = jl(out / "QORTUBA_ROUND1_PROOF.json")
    sigs = round1_signatures(proof)
    regs = {
        "OWNER_ACTION_REGISTER": owner_actions(),
        "QORTUBA_DEPENDENCY_GRAPH": dependency_graph(proof, sigs),
        "QORTUBA_BLOCKER_REGISTER": blocker_register(),
        "LEGACY_LOGIC_AUDIT": legacy_audit(proof),
        "ROUND1_CAPABILITY_SIGNATURES": sigs,
        "INDEPENDENT_PARSER_TEST_PLAN": parser_plan(sigs),
        "ACTIVE_PATH_DEFECT_REGISTER": defect_register(),
        "MIGRATION_TRANSACTION": transaction(),
        "R8_6_DECISION_REGISTER": decisions(proof),
    }
    for name, obj in regs.items():
        (out / f"{name}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False) + "\n")
    s = regs["ROUND1_CAPABILITY_SIGNATURES"]
    print("signatures", s["required_count"], "of", s["source_signature_count"], "obs", s["round1_observations"],
          "occ", s["round1_occurrences"], "in blocks", s["occurrences_inside_block_instances"],
          "block obs", s["distinct_block_observations"], "reflected", s["net_reflected_occurrences"])
    for x in s["required"]:
        print("  ", x["round1_occurrence_count"], x["source_count"], x["blocks"], x["rows_using_it"], x["signature"][:70])
    print("blockers", regs["QORTUBA_BLOCKER_REGISTER"]["row_specific_by_kind"])
    print("one fact blocks", {k: len(v) for k, v in regs["QORTUBA_DEPENDENCY_GRAPH"]["what_one_missing_fact_blocks"].items()})
    print("plan", [(x["signature"][:40], x["failure_blocks"]) for x in regs["INDEPENDENT_PARSER_TEST_PLAN"]["step_3_signatures"]])
    return regs


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else REG)
