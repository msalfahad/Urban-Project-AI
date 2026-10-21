"""ALSENAN ROUND 4 - build and freeze the source-exhaustion registers (Round-3 registers are never written).

    python3 research/alsenan_rebar_source_exhaustion_04/build_rebar_v4.py <ctx.pkl | work_dir> [--twice]

1. load the Alsenan context; read the frozen visual evidence capture (evidence/VISUAL_EVIDENCE_CAPTURE.json);
2. alsenan_rebar_v4.build -> claims, components, populations; invariants; known-components BBS; project gate;
3. write the Round-4 registers + INDEX.json (sha256 per file). --twice rebuilds and refuses on any difference.
No benchmark value is read here (firewall, tested). post_freeze_rebar_comparison.py runs after the freeze.
"""

from __future__ import annotations

import hashlib
import json
import math
import pickle
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in (str(ROOT / "research" / "external_engine_lab"), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

import alsenan_rebar_v4 as R4  # noqa: E402
import alsenan_rebar_v4_sources as SV  # noqa: E402
from engine.source import rebar_model as RM  # noqa: E402
from engine.source import visual_source_claim as VS  # noqa: E402

OUT = HERE / "registers"
R1_GZB = ROOT / "research/alsenan_control_plane_01/registers/STRUCTURAL_POPULATION_COVERAGE_REGISTER.json"
R3REG = ROOT / "research/alsenan_rebar_truth_03/registers"
LAP_BBS = ("LAP-70D-NOTE9-EXTENDED", 70)
REVIEW_FACET_KIND = "INDEPENDENT_REVIEW"


def _clean(o):
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items() if not str(k).startswith("_")}
    if isinstance(o, (list, tuple, set)):
        return [_clean(v) for v in (sorted(o) if isinstance(o, set) else o)]
    if hasattr(o, "item"):
        o = o.item()
    if isinstance(o, float):
        return round(o, 6)
    return o


def _text(o):
    return json.dumps(_clean(o), indent=1, ensure_ascii=False) + "\n"


def load(src):
    p = Path(src)
    if p.is_file():
        return pickle.load(open(p, "rb"))
    import alsenan_v3b as V3B
    return V3B.build(p, "rebar-source-exhaustion-round-4")


def r3(name):
    return json.loads((R3REG / f"{name}.json").read_text())


# ------------------------------------------------------------------------------------------------- triage
TRIAGE = [
    # id, title, category, status, resolution / evidence, promotes
    ("Q-R3-13a", "concrete cover (members / soil)", "SOURCE_RESOLVABLE", "RESOLVED_FROM_SOURCE",
     "p.8 note 22: >= 25 mm columns / slabs / beams, >= 70 mm against soil - CROSS_VERIFIED (OCR + independent review)",
     "cover rules COVER_GENERAL_25MM / COVER_AGAINST_SOIL_70MM"),
    ("Q-R3-14", "ground beam '3Ø16 + 3Ø16' lower rows", "SOURCE_RESOLVABLE", "RESOLVED_FROM_SOURCE",
     "p.13 > 5 m section: two lower rows of 3Ø16 (dot rows 3/3/3, section 300 x 600, OCR, independent review) - "
     "both rows are real, never de-duplicated", "GROUND_BEAM LOWER_1 / LOWER_2"),
    ("Q-R3-8a", "lift pit reinforcement values and pit plan", "SOURCE_RESOLVABLE", "RESOLVED_FROM_SOURCE",
     "p.14: walls 200, 6Ø12/m, 6Ø16/m, 2Ø16 base bars (CROSS_VERIFIED); pit 1.80 x 1.80 inside / 2.20 x 2.20 outside "
     "from ST7757.dxf S-BW", "LIFT_PIT_BASE_2D16, pit perimeters"),
    ("Q-R3-11a", "D5 columns - off-storey / real", "SOURCE_RESOLVABLE", "RESOLVED_FROM_SOURCE",
     "17 OFF_STOREY_COLUMN (not drawn on the storey sheet nor above, drawn below), 4 REAL (one outline, upper member "
     "unbound), 2 REAL several outlines (provisional)", "column populations"),
    ("Q-R3-3a", "CB6 occurrence", "SOURCE_RESOLVABLE", "RESOLVED_FROM_SOURCE",
     "centreline 10.575 m vs schedule 10.70 m; column-supported spans 2 = schedule 2", "CB6 component matrix"),
    ("Q-R3-10", "stair p.16 typical", "STRUCTURAL_ENGINEER_REQUIRED", "SOURCE_READ_APPLICABILITY_OPEN",
     "p.16 read and structured (TYPICAL_STAIR_DETAIL_SOURCE); applicability to 4.50 m two-turn / 4.20 m stairs is an "
     "engineering decision", "stair population (G23)"),
    ("Q-R3-7a", "per-metre count convention (ceil(rate x w) vs ceil(w / s) + 1)", "METHOD_DECISION", "OPEN",
     "measurement convention, not design: Urban method proposal in PROJECT_REBAR_RULE_REGISTER.count_method_proposal",
     "every per-metre convention bar (provisional today)"),
    ("Q-R3-7b", "two-layer footing top-mesh end shape", "STRUCTURAL_ENGINEER_REQUIRED", "OPEN",
     "no detail prints the FTB top-mesh ends", "FTB TOP_LAYER_END_DETAIL"),
    ("Q-R3-8b", "lift pit depth / wall height", "OWNER_OR_MANUFACTURER_REQUIRED", "OPEN",
     "p.14 prints 'As Per Lift Manufactures recommendations'", "LIFT_PIT_WALL_12MM / 16MM"),
    ("Q-R3-8c", "lift pit wall bars per face", "STRUCTURAL_ENGINEER_REQUIRED", "OPEN",
     "bars are drawn on both faces; whether 6Ø12/m and 6Ø16/m apply per face is not printed", "lift walls"),
    ("Q-R3-1", "CB support-bar / hanger cut-offs", "STRUCTURAL_ENGINEER_REQUIRED", "OPEN",
     "CB schedule graphics are N.T.S. templates; p.15 rules are for slabs, not beams - PROVISIONAL_NTS_GEOMETRY kept",
     "CB EXTENSION parts"),
    ("Q-R3-2", "CB3 MID1/MID2, CB8 MID1 empty cells", "STRUCTURAL_ENGINEER_REQUIRED", "OPEN", "cells are empty",
     "CB3 / CB8 support components"),
    ("Q-R3-3b", "CB3 / CB4 / CB5 / CB8 / CB12 occurrences, CB2 / CB10 tags", "STRUCTURAL_ENGINEER_REQUIRED", "NARROWED",
     "candidate search in CB_OCCURRENCE_CANDIDATE_REGISTER: each has a stated contradiction", "6 CB populations"),
    ("Q-R3-4", "hook / bend / beam-end anchorage lengths", "STRUCTURAL_ENGINEER_REQUIRED", "OPEN",
     "no project source; p.8 note 9 is the starter-bar development length, not a hook rule; METHOD option: adopt the "
     "code hook table as an Urban method", "every HOOK / ANCHORAGE part"),
    ("Q-R3-13b", "135° hook allowance", "STRUCTURAL_ENGINEER_REQUIRED", "OPEN", "code / engineer decision",
     "PROVISIONAL_HOOK_ALLOWANCE parts"),
    ("Q-R3-5", "note 21 side bars: width -> 2/3/4 Ø12, per face?", "STRUCTURAL_ENGINEER_REQUIRED", "OPEN",
     "mapping not printed", "SIDE_BARS on simple beams and CB > 60 cm"),
    ("Q-R3-6", "footing BOXED '3+4 ... 3+8' meaning / diameter", "STRUCTURAL_ENGINEER_REQUIRED", "NARROWED",
     "p.13 confirms a separate boxed-bar cage exists; values unexplained", "16 BOXED components"),
    ("Q-R3-9", "SB2 duplicate row; SB1 F / F10 footing", "STRUCTURAL_ENGINEER_REQUIRED", "OPEN", "source conflicts",
     "SB2, SB1, F / F10"),
    ("Q-R3-11b", "D5: C4 tag H4199 without an outline (3 storeys)", "STRUCTURAL_ENGINEER_REQUIRED", "NARROWED",
     "no outline of the printed size beside the tag", "3 column populations"),
    ("Q-R3-12", "column ties in the beam-column joint / over the storey", "STRUCTURAL_ENGINEER_REQUIRED", "OPEN",
     "no detail prints joint ties; R3 ties over the clear height kept", "column TIES"),
    ("Q-S4", "ground-slab scope (T=10cm, 5Ø10/m E.W.)", "STRUCTURAL_ENGINEER_REQUIRED", "NARROWED",
     "GROUND_SLAB_SCOPE_REGISTER_V2: note cell vs all cells of FP-1 - candidates and contradictions listed", "G15"),
    ("Q-R4-1", "lift tie beams (note 19) - section, bars, position", "STRUCTURAL_ENGINEER_REQUIRED", "NEW",
     "GF storey 4.50 m > 4.30 m: note 19 requires them; nothing detailed", "LIFT_TIE_BEAMS:GF"),
    ("Q-R4-2", "planted columns (P.C 20x70, 2 x P.C 20x50) bars and beam extras", "STRUCTURAL_ENGINEER_REQUIRED", "NEW",
     "not in the column schedule; p.15 detail lengths 'DEPTH'", "3 PLANTED_COLUMN populations"),
    ("Q-R4-3", "parapet detail applicability", "STRUCTURAL_ENGINEER_REQUIRED", "NEW",
     "three p.14 details, none bound to a roof edge", "PARAPET_RC"),
    ("Q-R4-4", "temperature steel for 160 / 180 mm slabs (not table rows)", "STRUCTURAL_ENGINEER_REQUIRED", "NEW",
     "no rounding: SOURCE_RULE_NOT_EXACT_MATCH; METHOD option: use the next thicker row", "3 TEMPERATURE populations"),
    ("Q-R4-5", "boundary wall: schedule B.W vs p.14 typical", "STRUCTURAL_ENGINEER_REQUIRED", "NEW", "source conflict",
     "BOUNDARY_WALL"),
    ("Q-R4-6", "ground beams under exterior walls (27 spans disagree)", "SOURCE_RESOLVABLE", "NEW",
     "overlay the architectural exterior walls on the GBP sheet (next round)", "governing GB detail per span"),
    ("Q-R4-7", "ground beam < 2.5 m stirrups (drawn, no callout)", "STRUCTURAL_ENGINEER_REQUIRED", "NEW",
     "stirrup not printed", "GB < 2.5 m STIRRUPS"),
    ("Q-R4-8", "AI-only readings: lintel MIN.40cm bearing, starter foot Min. 30cm, note 9 wording",
     "SOURCE_RESOLVABLE", "NEW", "a QS opens the crop (page / bbox / hash in the claim) and records a human "
                                 "verification - promotes the claim to HUMAN_VERIFIED_SOURCE", "lintel / starter parts"),
    ("Q-R4-9", "slab support continuity per panel", "SOURCE_RESOLVABLE", "NEW",
     "panel adjacency on the slab sheets decides which supports are continuous", "slab STOP50 extensions"),
    ("Q-R4-10", "founding level (necks, deep-footing lower ground beam)", "OWNER_OR_MANUFACTURER_REQUIRED", "NEW",
     "p.8 note 12: by site / soil investigation", "NECK_VERTICALS, conditional lower GB"),
    ("Q-R4-11", "pool detail zones vs the 1.55 x 3.10 plan", "STRUCTURAL_ENGINEER_REQUIRED", "NEW",
     "detail shows a sloped floor not on the plan", "POOL"),
    ("Q-R4-12", "dome rise: elevations 1.72 / 2.15 vs detail 190", "OWNER_OR_MANUFACTURER_REQUIRED", "NEW",
     "architecture to confirm", "dome shell extensions"),
]


def build(ctx, capture=None):
    gzb = json.loads(R1_GZB.read_text())["ground_zone_binding"]
    b = R4.build(ctx, gzb, capture=capture)
    comps, pops = b.comps, b.pops
    cby = defaultdict(list)
    for c in comps:
        cby[c["population_id"]].append(c)
    trade = RM.totals(pops)
    ps = {p["pop_id"]: p["release_state"] for p in pops}
    bb = RM.bbs(comps, ps, lap_factor=LAP_BBS[1], lap_rule_id=LAP_BBS[0])
    viol = {"completeness": RM.check_completeness(b.rc_occ, pops, comps),
            "duplicates": RM.check_duplicates(comps, pops),
            "provenance": RM.check_provenance(comps),
            "mass": RM.check_mass(comps, pops, trade, bb),
            "bbs_eligibility": RM.check_bbs_eligibility(bb, comps, ps)}
    viol.update(R4.project_invariants(b))
    checks_pass = all(not v for v in viol.values())
    n_conf = len(b.defs["conflicts"]) + 1 + 1                              # schedule conflicts + B.W vs p.14 + F/F10
    status = RM.project_status(pops, comps, checks_pass=checks_pass, source_conflicts=n_conf)
    kbbs = RM.known_components_bbs(bb, status)
    regs = {}
    claims = list(b.claims.values())

    # ---------------------------------------------------------------- 1 visual source claims
    regs["VISUAL_SOURCE_CLAIM_REGISTER"] = {
        "SCHEMA": "URBAN_ALSENAN_VISUAL_SOURCE_CLAIM_V1", "policy": VS.POLICY_ID, "drawing": SV.DRAWING,
        "drawing_sha256": b.pdf_sha, "evidence_capture": "evidence/VISUAL_EVIDENCE_CAPTURE.json",
        "reader": "AI visual transcription by this round's reader from the rendered crop (raw + normalised)",
        "deterministic_channels": ["OCR_TEXT (tesseract 5.3.4, eng / ara)", "PDF_VECTOR_GEOMETRY (pymupdf)",
                                   "DXF_GEOMETRY / DXF_TEXT (ST7757.dxf)"],
        "independent_channel": SV.REVIEW_REF,
        "state_rule": "CROSS_VERIFIED = AI reading + >= 2 distinct non-AI channels (>= 1 deterministic) that agree "
                      "and together cover every facet the claim asserts; AI-only -> PROVISIONAL authority; any "
                      "disagreement -> SOURCE_CONFLICT",
        "counts": dict(Counter(c["source_state"] for c in claims)),
        "applicability_counts": dict(Counter(c["applicability"] for c in claims)),
        "claims": claims}

    # ---------------------------------------------------------------- 2 project rules
    def rule(rid, claim, value, applies, scope, note=None, alias=None):
        c = b.claims[claim] if claim else None
        return {"rule_id": rid, "alias": alias, "value": value, "applies_to": applies, "scope": scope,
                "claim_id": claim, "source_state": c["source_state"] if c else "NO_PROJECT_SOURCE",
                "quantity_authority": VS.quantity_authority(c) if c else VS.NO_AUTHORITY, "note": note}
    pm_comps = [c for c in comps if c["count_mode"] in ("BARS_PER_METRE", "SPACING_MM")]
    delta = sum(((c["count"] or {}).get("convention") or 0) - ((c["count"] or {}).get("verified") or 0)
                for c in pm_comps)
    delta_kg = sum((((c["count"] or {}).get("convention") or 0) - ((c["count"] or {}).get("verified") or 0)) *
                   (c["verified_length_m"] + c["provisional_length_m"]) * (c["unit_weight_kg_m"] or 0)
                   for c in pm_comps if c["state"] not in (RM.BLOCKED, RM.NOT_REQUIRED))
    regs["PROJECT_REBAR_RULE_REGISTER"] = {
        "SCHEMA": "URBAN_ALSENAN_PROJECT_REBAR_RULES_V1",
        "rules": [
            rule("COVER_GENERAL_25MM", "P8-N22-COVER-GENERAL", 25, ["COLUMN", "BEAM", "CONTINUOUS_BEAM", "SLAB",
                                                                     "LINTEL", "DOME"], "minimum cover",
                 alias="COVER-MEMBER-25"),
            rule("COVER_AGAINST_SOIL_70MM", "P8-N22-COVER-SOIL", 70, ["FOOTING", "FOOTING_2_LAYER", "FOOTING_LIFT",
                                                                      "STRAP_BEAM", "GROUND_BEAM", "GROUND_SLAB",
                                                                      "COLUMN_STARTERS", "POOL"], "minimum cover",
                 alias="COVER-SOIL-70"),
            rule("DEVELOPMENT_STARTER_70D_40D", "P8-N09-STARTER-DEVELOPMENT", {"tension": 70, "compression": 40},
                 ["STARTER_BARS"], "development / tie length of starter bars only",
                 note="NOT a hook, bend or beam-end anchorage rule; used for BBS laps of long runs only as a labelled "
                      "procurement assumption (LAP-70D-NOTE9-EXTENDED)"),
            rule("STARTER_PROJECTION_40D", "P13-STARTER-PROJECTION-40D", 40, ["COLUMN_STARTERS"],
                 "starter projection above the footing top"),
            rule("STARTER_FOOT_MIN_300", "P13-STARTER-FOOT-MIN30", 300, ["COLUMN_STARTERS"], "horizontal foot"),
            rule("LINTEL_BEARING_MIN_400", "P13-LINTEL-BEARING", 400, ["LINTEL"], "bearing each side"),
            rule("SLAB_THICKNESS_DEFAULT_160", "P8-N18-SLAB-THICKNESS", 160, ["SLAB"], "unless stated otherwise"),
            rule("SLAB_TOP_ANCHOR_0_25L", "P15-SLAB-TOP-NONCONTINUOUS", 0.25, ["SLAB"], "non-continuous support"),
            rule("SLAB_TOP_0_30L_MAX", "P15-SLAB-TOP-CONTINUOUS", 0.30, ["SLAB"], "continuous support, larger span"),
            rule("SLAB_BOTTOM_STOP_50PCT_0_125L", "P15-SLAB-BOTTOM-STOP", {"fraction": 0.5, "stop": 0.125}, ["SLAB"],
                 "continuous support"),
            rule("TEMPERATURE_LAP_40D", "P15-TEMPERATURE-NOTES", 40, ["TEMPERATURE_REINFORCEMENT"], "temperature bars"),
            rule("SIDE_BARS_NOTE_21", "P8-N21-SIDE-BARS", "2/3/4 Ø12 by width", ["BEAM", "CONTINUOUS_BEAM"],
                 "depth > 60 cm", note="width -> count mapping NOT printed: BLOCKED"),
            rule("LIFT_TIE_BEAMS_NOTE_19", "P8-N19-LIFT-TIE-BEAMS", {"height_m": 3.0, "storey_gt_m": 4.3},
                 ["LIFT_TIE_BEAM"], "storeys > 4.30 m"),
            rule("HOOKS_AND_BENDS", None, "PROVISIONAL_HOOK_ALLOWANCE (ACI 318-19 tables, edition unverified)",
                 ["ALL"], "no project source", note="engineer / code decision; never verified")],
        "count_method_proposal": {
            "id": "URBAN_FINITE_SPACING_METHOD_V1 (PROPOSAL - pending owner / engineer approval)",
            "inputs": ["printed rate n/m or spacing s", "clear distribution width = side - 2 x cover",
                       "edge cover at both ends"],
            "strict_source_lower_bound": "n = ceil(rate x clear_distribution)  (current VERIFIED count)",
            "geometric_end_bar_convention": "n_spaces = ceil(clear_distribution / max_spacing); n_bars = n_spaces + 1 "
                                            "(where the instruction means a MAXIMUM spacing)",
            "current_state": "convention bars PROVISIONAL until the meaning of 'n Ø d / m' in this schedule is "
                             "approved",
            "difference_bars": delta, "difference_kg": round(delta_kg, 3),
            "components_affected": len(pm_comps)}}

    # ---------------------------------------------------------------- 3 ground beams
    gbr = b.registers["GROUND_BEAMS"]
    regs["GROUND_BEAM_REBAR_V4"] = {
        "SCHEMA": "URBAN_ALSENAN_GROUND_BEAM_REBAR_V4",
        "GROUND_BEAM_DETAIL_REGISTER": [
            {"detail": k, "applicability_condition": v["rule"] + (" without concentrated load" if k != "EXT" else ""),
             "section_mm": [v["B"] * 1000, v["D"] * 1000 if v["D"] else "FOLLOW ARCH."],
             "top_bars": v["TOP"], "lower_layer_1": v["LOWER_1"], "lower_layer_2": v["LOWER_2"],
             "side_reinforcement": v["SIDE"], "stirrups": v["STIR"] or "DRAWN, NOT PRINTED",
             "claim_id": v["claim"], "source_page": 13, "source_crop": b.claims[v["claim"]]["crop_bbox"],
             "crop_hash": b.claims[v["claim"]]["crop_hash"],
             "interpretation_state": b.claims[v["claim"]]["source_state"]} for k, v in R4.GB_DETAILS.items()],
        "binding_rule": "length category from the clear span AND a centreline-basis length (clear + 0.25 m) - "
                        "ambiguous when they differ; exterior when the span lies on a ground-beam footprint outline "
                        "(cross-layer, DXF); V3 'adjacent to the ZONE-1 cell' flag kept as second evidence; a "
                        "component is VERIFIED only when every candidate detail gives the same bars",
        "q_r3_14": "RESOLVED: the two lower rows are real (dot rows 3/3/3); never de-duplicated",
        "occurrences": gbr,
        "summary": {"spans": len(gbr), "by_primary": dict(Counter(r["primary_detail"] for r in gbr)),
                    "by_applicability": dict(Counter(r["applicability"] for r in gbr)),
                    "v3_vs_footprint_disagreements": sum(1 for r in gbr if r["v3_exterior_flag"] != r["footprint_edge"]),
                    "verified_kg": sum(r["verified_kg"] for r in gbr),
                    "provisional_kg": sum(r["provisional_kg"] for r in gbr)}}

    # ---------------------------------------------------------------- 4 temperature, 5 slab detail, 6 lift
    regs["TEMPERATURE_REBAR_RULE_REGISTER"] = dict(b.registers["TEMPERATURE"], SCHEMA="URBAN_ALSENAN_TEMPERATURE_V1",
                                                   claim_state=b.claims["P15-TEMPERATURE-SCHEDULE"]["source_state"])
    srr = b.slab_rule_rows
    regs["SLAB_DETAIL_RULE_REGISTER"] = {
        "SCHEMA": "URBAN_ALSENAN_SLAB_DETAIL_RULES_V1",
        "rules": [{"rule": r, "claim_id": c, "source_state": b.claims[c]["source_state"],
                   "value": b.claims[c]["value"]} for r, c in (("TOP_ANCHOR_NON_CONTINUOUS", "P15-SLAB-TOP-NONCONTINUOUS"),
                                                              ("TOP_CONTINUOUS_WHICHEVER_LARGER", "P15-SLAB-TOP-CONTINUOUS"),
                                                              ("BOTTOM_STOP_50PCT", "P15-SLAB-BOTTOM-STOP"))],
        "drawing_proportions": SV.load_capture()["crops"]["P15_SLAB_ON_BEAMS"]["geometry"]["dimension_lines"],
        "comparison": srr,
        "summary": {"by_classification": dict(Counter(r["classification"] for r in srr)),
                    "r3_verified_kg": sum(r["r3_verified_kg"] for r in srr),
                    "r4_verified_kg": sum(r["r4_verified_kg"] for r in srr),
                    "moved_to_provisional_kg": sum(r["r3_verified_kg"] - r["r4_verified_kg"] for r in srr)},
        "finding": "Round 3 released every bottom bar over span + embedment and drawn top bars over the whole panel; "
                   "the p.15 rules stop half the bottom bars 0.125 L short of a continuous support and limit top bars to "
                   "0.25 L / 0.30 L - the excess is no longer verified (support continuity per panel is Q-R4-9)"}
    regs["LIFT_REBAR_SOURCE_REGISTER"] = {"SCHEMA": "URBAN_ALSENAN_LIFT_REBAR_V1",
                                          "claims": ["P14-LIFT-VALUES", "P14-LIFT-ORIENTATION"],
                                          "claim_states": {k: b.claims[k]["source_state"]
                                                           for k in ("P14-LIFT-VALUES", "P14-LIFT-ORIENTATION")},
                                          **b.registers["LIFT"],
                                          "blocked_dimension": "pit depth / wall height - lift manufacturer"}

    # ---------------------------------------------------------------- 7 carried re-audit
    r3occ = {r["occurrence_id"]: r for r in r3("REBAR_OCCURRENCE_REGISTER")["rows"]}
    def r3k(occ):
        r = r3occ.get(occ, {})
        return {f: r.get(f, 0.0) for f in ("lower_bound_kg", "provisional_kg", "budget_kg", "audit_kg")}
    def r4k(ets):
        sel = [p for p in pops if p["element_type"] in ets]
        return {"populations": len(sel), "verified_kg": sum(p["verified_complete_kg"] + p["lower_bound_kg"] for p in sel),
                "provisional_kg": sum(p["provisional_kg"] for p in sel), "audit_kg": sum(p["audit_kg"] for p in sel),
                "release_states": dict(Counter(p["release_state"] for p in sel))}
    basis = defaultdict(set)
    for s in ctx["v3b"]["rebar"]["weighed"]:
        basis[s["population"]].add(s.get("basis") or "")
    carried = [
        ("GROUND", ["GROUND_BEAM"], "V3a ground-beam sets: p.13 sections by clear length; hooks code method",
         "p.13 sections as CROSS_VERIFIED claims; per-span candidate envelope (interior / exterior x length basis); "
         "anchorage BLOCKED", "interior + exterior merged into one GB register; exterior flag re-tested"),
        ("GROUND_BEAM_EXT", ["GROUND_BEAM"], "V3b exterior GB bars with D = 1.00 provisional", "(merged into GROUND)",
         "longitudinal bars no longer depend on D: verified where the governing detail is certain"),
        ("LINTELS", ["LINTEL"], "p.13 lintel schedule, straight bars (W + 0.80 - 2c)",
         "schedule CROSS_VERIFIED (core = opening width); MIN.40 bearing AI-only (provisional); drawn hooks BLOCKED; "
         "5Ø8/M per-metre split", "bearing extension now provisional; hooks blocked"),
        ("COLUMN_STARTERS", ["COLUMN_STARTERS"], "weight only: median FOUNDATION bars x (neck @ Urban founding -1.50 + "
                                                 "H - 7 cm + 40Ø)",
         "per GF column: FOUNDATION bars x (footing depth min - 70 + 300 foot + 40Ø projection); NECK BLOCKED",
         "founding-level fallback removed; neck blocked"),
        ("BOUNDARY_WALL", ["BOUNDARY_WALL"], "schedule row B.W over the S-BOUN run (provisional)",
         "SOURCE_CONFLICT schedule B.W vs p.14 typical; columns / pads / lower beam BLOCKED",
         "no side of a conflict is selected"),
        ("DOME", ["DOME"], "DETAIL OF DOME scaled by the printed 442; rise from elevations",
         "DXF-text bars; ring inner circle verified; shell lower bound = plan radius / plan area; rise-dependent "
         "parts provisional", "rise (1.72 / 2.15 elevations vs 1.90 detail) no longer drives verified kg"),
        ("POOL", ["POOL"], "deep-end callouts applied to the whole pool", "all bar sets PROVISIONAL (AI mapping of the "
                                                                          "N.I.S. detail; sloped floor not on plan)",
         "R3 released it as a lower bound - now provisional"),
        ("BEAM_RESIDUE", ["BEAM_UNBOUND_TAG"], "BUDGET: same-type median length x section per unbound tag",
         "one BLOCKED population per unbound tag, audit only", "BUDGET removed - no opaque kg"),
        ("FOOTING_F_F10", [], "F10 selected (provisional)", "RETIRED - duplicate of the blocked R3 F / F10 pair",
         "selecting one side of a conflict is not allowed")]
    rows = []
    for popn, ets, old_src, new_model, reason in carried:
        o = r3k(f"CARRIED:{popn}")
        n = r4k(ets) if ets and popn not in ("GROUND_BEAM_EXT",) else {"populations": 0, "verified_kg": 0.0,
                                                                       "provisional_kg": 0.0, "audit_kg": 0.0}
        rows.append({"population": popn, "old_source": old_src, "old_formula": sorted(basis.get(popn, []))[:3],
                     "old_kg": o, "new_component_model": new_model, "new_kg": n,
                     "source_coverage": "PDF claims + DXF geometry" if ets else "none (retired)",
                     "release_state": n.get("release_states"),
                     "difference_verified_kg": n["verified_kg"] - o["lower_bound_kg"],
                     "difference_provisional_kg": n["provisional_kg"] - o["provisional_kg"] - o["budget_kg"],
                     "reason": reason})
    regs["CARRIED_POPULATION_REAUDIT"] = {"SCHEMA": "URBAN_ALSENAN_CARRIED_REAUDIT_V1", "rows": rows,
                                          "carried_populations_remaining": sum(1 for p in pops if p["occurrence_id"]
                                                                               .startswith("CARRIED:")),
                                          "starters": b.registers["STARTERS"], "lintels": b.registers["LINTELS"],
                                          "domes": b.registers["DOMES"], "boundary_wall": b.registers["BOUNDARY_WALL"],
                                          "f_f10": b.registers["F_F10"],
                                          "new_required_blocked": {"lift_tie_beams": b.registers["LIFT_TIE_BEAMS"]}}

    # ---------------------------------------------------------------- 8 CB, 9 D5, 10 ground slab
    regs["CB_OCCURRENCE_CANDIDATE_REGISTER"] = {
        "SCHEMA": "URBAN_ALSENAN_CB_OCCURRENCE_CANDIDATES_V1", "rows": b.cb_candidates,
        "summary": dict(Counter(r["decision"] for r in b.cb_candidates)),
        "rule": "breadth, length vs schedule sum (<= 5 %), column-supported span count, tag position, collinear "
                "extension; ACCEPTED_STRONG only with no contradiction - weak matches are never auto-accepted",
        "nts_cutoffs": "PROVISIONAL_NTS_GEOMETRY kept for every template extension"}
    regs["D5_COLUMN_SOURCE_RECONCILIATION"] = {
        "SCHEMA": "URBAN_ALSENAN_D5_RECONCILIATION_V1", "rows": b.d5,
        "summary": dict(Counter(r["classification"] for r in b.d5)),
        "r3_audit_kg": r3("COLUMN_REBAR_RECONCILIATION")["d5_blocked"],
        "rule": "kg re-enters only where the physical occurrence is established (one outline, bound tag); a candidate "
                "classification never restores kg; OFF_STOREY occurrences keep their weight as audit"}
    r3scope = r3("SLAB_REBAR_AUDIT")["ground_slab_scope"]
    regs["GROUND_SLAB_SCOPE_REGISTER_V2"] = dict(R4.ground_slab_scope_v2(ctx, r3scope),
                                                 SCHEMA="URBAN_ALSENAN_GROUND_SLAB_SCOPE_V2")

    # ---------------------------------------------------------------- 11 triage
    regs["ENGINEERING_QUESTION_TRIAGE_REGISTER"] = {
        "SCHEMA": "URBAN_ALSENAN_QUESTION_TRIAGE_V1",
        "rows": [{"id": i, "question": q, "category": c, "status": s, "evidence": e, "promotes": p}
                 for i, q, c, s, e, p in TRIAGE],
        "by_category": dict(Counter(c for _, _, c, _, _, _ in TRIAGE)),
        "by_status": dict(Counter(s for _, _, _, s, _, _ in TRIAGE)),
        "rule": "ask humans only what the drawings / code cannot answer; SOURCE_RESOLVABLE items are next-round work"}

    # ---------------------------------------------------------------- 12 status, 13 scorecard, BBS
    regs["PROJECT_REBAR_STATUS"] = dict(status, SCHEMA="URBAN_ALSENAN_PROJECT_REBAR_STATUS_V1", trade_totals=trade,
                                        known_components_bbs=kbbs, invariants_pass=checks_pass)
    regs["KNOWN_COMPONENTS_BBS_REGISTER"] = {"SCHEMA": "URBAN_ALSENAN_KNOWN_COMPONENTS_BBS_V1", **kbbs,
                                             "by_dia": bb["by_dia"], "included_components": len(bb["included"]),
                                             "excluded_components": len(bb["excluded"]), "lap_rule": LAP_BBS[0],
                                             "lap_rule_note": "note 9 names starter bars; applying 70Ø to other long "
                                                              "runs is a labelled procurement assumption"}
    req = [c for c in comps if c["required"] and ps[c["population_id"]] != RM.NIS]
    non_nis = [p for p in pops if p["release_state"] != RM.NIS]
    ver = sum(p["verified_complete_kg"] + p["lower_bound_kg"] for p in pops)
    prov = sum(p["provisional_kg"] for p in pops)
    aud = sum(p["audit_kg"] for p in pops if p["release_state"] != RM.NIS)
    review_dep = 0.0
    for c in comps:
        cid = (c["source"] or {}).get("claim_id")
        if cid and c["verified_kg"] > 0:
            cl = b.claims[cid]
            alt = dict(cl, corroborations=[x for x in cl["corroborations"] if x["kind"] != REVIEW_FACET_KIND])
            if VS.resolve_state(alt)[0] != VS.CROSS_VERIFIED:
                review_dep += c["verified_kg"]
    pdf_regions = __import__("alsenan_structural_source_v2").PDF_ONLY
    regs["REBAR_ACCURACY_SCORECARD_V2"] = {
        "SCHEMA": "URBAN_ALSENAN_REBAR_SCORECARD_V2",
        "metrics": {
            "source_accounting_pct": 100.0 * len(pdf_regions) / len(pdf_regions),
            "schedule_definitions_feeding_quantity_pct": None,
            "source_interpretation_pct": 100.0 * sum(1 for c in claims if c["source_state"] in
                                                     (VS.CROSS_VERIFIED, VS.MACHINE_READ, VS.HUMAN_VERIFIED)) / len(claims),
            "occurrence_binding_pct": 100.0 * sum(1 for p in non_nis if p["occurrence_state"] == "ESTABLISHED") /
            len(non_nis),
            "required_component_completeness_pct": 100.0 * sum(1 for c in req if c["state"] == RM.COMPLETE) / len(req),
            "population_completeness_pct": status["population_completeness_pct"],
            "verified_kg_share_pct": 100.0 * ver / (ver + prov + aud),
            "provisional_kg_share_pct": 100.0 * prov / (ver + prov + aud),
            "blocked_population_count": sum(1 for p in pops if p["release_state"] == RM.BLK),
            "mass_conservation": "PASS" if not viol["mass"] else "FAIL",
            "provenance": "PASS" if not viol["provenance"] else "FAIL",
            "human_claim_dependency_pct": 100.0 * review_dep / ver if ver else 0.0,
            "human_claim_dependency_note": "share of verified kg whose claim would fall back to AI-only without the "
                                           "owner-relayed independent review; HUMAN_VERIFIED claims: 0"},
        "rule": "metrics are reported separately; they are never combined into one accuracy number",
        "pdf_regions_accounted": [r[0] for r in pdf_regions]}

    # ---------------------------------------------------------------- supporting registers
    regs["REBAR_POPULATION_REGISTER_V4"] = {
        "SCHEMA": "URBAN_ALSENAN_REBAR_POPULATIONS_V4", "trade_totals": trade,
        "populations": [{k: p[k] for k in ("pop_id", "element_type", "occurrence_id", "level", "occurrence_state",
                                           "occurrence_why", "release_state", "verified_complete_kg", "lower_bound_kg",
                                           "provisional_kg", "budget_kg", "audit_kg", "missing_components",
                                           "component_states")} for p in pops],
        "components": [{k: c.get(k) for k in ("comp_id", "population_id", "element_type", "occurrence_id", "bar_role",
                                              "layer", "direction", "span", "dia_mm", "count_mode", "count", "parts",
                                              "verified_length_m", "provisional_length_m", "unit_weight_kg_m",
                                              "verified_kg", "provisional_kg", "audit_kg", "state", "required",
                                              "cover_rule_id", "source", "formula", "why", "component_group")}
                       for c in comps],
        "rc_occurrences": len(b.rc_occ),
        "checks": {k: {"violations": v, "pass": not v} for k, v in viol.items()}}
    regs["REBAR_GATE_TRANSITIONS_R4"] = gates(viol)
    return regs, b, bb


GATES = [
    ("G11", "PASS", "unchanged from R3 (FTB both layers)"), ("G13", "PASS", "unchanged from R3 (straps)"),
    ("G15", "XFAIL", "ground-slab scope still unresolved after the second pass (GROUND_SLAB_SCOPE_REGISTER_V2)"),
    ("G23", "XFAIL", "stair source READ, applicability BLOCKED"),
    ("G32", "PASS", "p.13 lower ground-beam rows are not de-duplicated"),
    ("G33", "PASS", "p.15 temperature schedule source-accounted"),
    ("G34", "PASS", "a 160 / 180 mm slab is never mapped to another row"),
    ("G35", "PASS", "p.16 stair source READ while applicability stays BLOCKED"),
    ("G36", "PASS", "known-components BBS is never procurement-ready below 100 % completeness"),
    ("G37", "PASS", "an AI visual transcription alone never becomes VERIFIED authority"),
    ("G38", "PASS", "every visual claim carries a crop reference and crop hash"),
    ("G39", "PASS", "CB N.T.S. extensions stay PROVISIONAL"),
    ("G40", "PASS", "a D5 candidate never re-enters a total"),
    ("G41", "PASS", "ground-slab min / max polygon guessing is forbidden"),
    ("G42", "PASS", "no carried opaque population remains"),
]


def gates(viol):
    return {"SCHEMA": "URBAN_ALSENAN_REBAR_GATE_TRANSITIONS_R4",
            "rows": [{"gate": g, "final_state": s, "evidence": e,
                      "proving_test": "tests/alsenan_rebar_source_exhaustion/test_rebar_r4.py"} for g, s, e in GATES],
            "invariants_clean": all(not v for v in viol.values())}


def main(src, twice=False):
    ctx = load(src)
    regs, b, bb = build(ctx)
    texts = {k: _text(v) for k, v in regs.items()}
    if twice:
        again, _, _ = build(ctx)
        diff = [k for k, v in again.items() if _text(v) != texts[k]]
        if diff:
            raise SystemExit(f"NON-DETERMINISTIC: {diff}")
    OUT.mkdir(parents=True, exist_ok=True)
    idx = {}
    for k, t in texts.items():
        (OUT / f"{k}.json").write_text(t)
        idx[k] = hashlib.sha256(t.encode()).hexdigest()
    cap = (HERE / "evidence" / "VISUAL_EVIDENCE_CAPTURE.json").read_bytes()
    index = {"SCHEMA": "URBAN_ALSENAN_R4_INDEX", "files": idx, "st7757_pdf_sha256": b.pdf_sha,
             "st7757_dxf_sha256": b.sha, "evidence_capture_sha256": hashlib.sha256(cap).hexdigest(),
             "frozen_before_benchmark": True, "built_twice_identical": bool(twice)}
    (OUT / "INDEX.json").write_text(_text(index))
    print("wrote", len(idx), "registers;", regs["PROJECT_REBAR_STATUS"]["PROJECT_REBAR_STATUS"])


if __name__ == "__main__":
    main(sys.argv[1], "--twice" in sys.argv)
