"""Coverage-recovery round - POST-FREEZE diagnostic comparison (the only file that holds donor / reference figures).

Refuses to run unless every output of the blind build still matches COVERAGE_RECOVERY_FREEZE.json. Compares
population counts, lengths, areas and volumes against U-C4N, christiannp (blind MCP runs, recorded from the owner's
brief) and the freelancer QS reference, classifies every meaningful difference and writes the root-cause register.
Nothing here feeds back into a quantity.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

# ---- recorded from the owner's brief (COMPARISON ONLY) ------------------------------------------------------------
UC4N = {"BUA_m2": 590.362, "CONCRETE_m3": 337.812, "FOOTINGS_m3": 66.579, "GROUND_BEAMS_m3": 36.005, "STRAPS_m3": 6.122,
        "GROUND_SLAB_m3": 32.183, "COLUMNS_m3": 45.070, "COL_FOU_m3": 6.150, "COL_GF_m3": 26.235, "COL_1F_m3": 8.888,
        "COL_2F_m3": 3.797, "BEAMS_m3": 50.841, "SLABS_m3": 95.689, "STAIRS_m3": 5.325, "NET_SLAB_m2": 518.250,
        "BLOCK_150_m": 71.589, "BLOCK_200_m": 148.095, "NET_REBAR_t": 22.619}
CNP = {"BUA_m2": 598.708, "CONCRETE_m3": 333.173, "FOOTINGS_m3": 65.669, "GROUND_BEAMS_m3": 36.006, "STRAPS_m3": 6.053,
       "GROUND_SLAB_m3": 32.404, "COL_FOU_m3": 6.150, "COL_GF_m3": 26.235, "COL_1F_m3": 8.888, "COL_2F_m3": 3.377,
       "BEAMS_m3": 46.591, "SLABS_m3": 96.753, "STAIRS_m3": 5.048, "NET_SLAB_m2": 525.155, "BLOCK_150_m": 79.971,
       "BLOCK_200_m": 183.497, "WALL_FACES_m2": 2364.7, "NET_REBAR_t": 22.916}
FREELANCER = {"FOOTINGS_m3": 65.634, "GROUND_BEAMS_m3": 37.98, "BOUNDARY_BEAM_m3": 7.56, "PERIMETER_GB_IN_FOUNDATIONS_m3":
              8.604, "STRAPS_m3": 3.392, "GROUND_SLAB_m3": 29.55, "COL_NECK_m3": 8.805, "COL_GF_m3": 17.438,
              "COL_1F_m3": 7.728, "COL_2F_m3": 3.381, "BEAMS_GROSS_m3": 65.966, "SLABS_NET_m3": 59.817,
              "NET_SLAB_m2": 372.19, "STAIRS_m3": 15.053, "CONCRETE_m3": 352.436}


def sha(b):
    return hashlib.sha256(b).hexdigest()


def dumps(o):
    return json.dumps(o, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def check_freeze():
    fz = json.loads((HERE / "COVERAGE_RECOVERY_FREEZE.json").read_text(encoding="utf-8"))
    for k, h in fz["outputs"].items():
        if sha((HERE / k).read_bytes()) != h:
            raise SystemExit(f"freeze broken: {k} changed after the freeze")
    for k, h in fz["inputs"].items():
        p = ROOT / k
        if p.exists() and sha(p.read_bytes()) != h:
            raise SystemExit(f"freeze broken: input {k} changed")
    return fz


def J(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def row(trade, element, unit, urban, donors, basis, reason, urban_issue, donor_issue, review, note, counts=None):
    b = urban.get("best")
    diffs = {k: (None if v is None or b is None else round(b - v, 3)) for k, v in donors.items()}
    return {"trade": trade, "element": element, "unit": unit, "urban_official": urban.get("official"),
            "urban_lower_bound": urban.get("lower_bound"), "urban_best_provisional": b, "urban_low": urban.get("low"),
            "urban_high": urban.get("high"), "urban_counts": counts, "donors": donors,
            "best_minus_donor": diffs, "basis_match": basis, "reason_class": reason, "likely_urban_issue": urban_issue,
            "likely_donor_issue": donor_issue, "needs_source_review": review, "note": note}


def L(q):
    return {"official": q["VERIFIED_QUANTITY"], "lower_bound": q["LOWER_BOUND_QUANTITY"],
            "best": q["BEST_PROVISIONAL_QUANTITY"], "low": q["LOW_SCENARIO"], "high": q["HIGH_SCENARIO"]}


def build():
    fz = check_freeze()
    Q, B = J("QUANTITY_SCENARIOS.json"), J("COVERAGE_BASELINE.json")["concrete_by_trade"]
    gb, gs, col, bm, sl, wl = Q["ground_beams"], Q["ground_slab"], Q["columns"], Q["beams"], Q["slabs"], Q["walls"]
    ext = [s for s in gb["spans"] if s["kind"] == "EXTERIOR"]
    int_m3 = sum(s["part"]["best"] for s in gb["spans"] if s["kind"] == "INTERIOR")
    ext_len = sum(s["length_m"] for s in ext)
    implied_d = {k: round((v - int_m3) / (ext_len * 0.30), 3) for k, v in (("UC4N", UC4N["GROUND_BEAMS_m3"]),
                                                                           ("CHRISTIANNP", CNP["GROUND_BEAMS_m3"]))}
    gross_gf = sl["sheets"]["GF"]["gross_m2"]
    pf = col["per_floor"]
    walls200 = wl["length_by_thickness"]["200"]
    rec = wl["reconciliation"]
    b200 = {k: sum(rec[f"{fl}|200"]["method_b"].get(k, 0.0) for fl in ("GF", "1F", "2F"))
            for k in ("PAIRED_WALL", "COLUMN_OVERLAP_POLICY", "OPENING_SPAN", "DUPLICATE_FACE")}
    col_ov200 = sum(rec[f"{fl}|200"]["method_a"]["column_overlap_m"] for fl in ("GF", "1F", "2F"))
    rows = [
        row("BUA", "gross structural outline (sum of floors)", "m2",
            {"official": round(sum(sl["sheets"][f]["gross_m2"] for f in ("GF", "1F", "2F")), 3),
             "best": round(sum(sl["sheets"][f]["gross_m2"] for f in ("GF", "1F", "2F")), 3)},
            {"UC4N": UC4N["BUA_m2"], "CHRISTIANNP": CNP["BUA_m2"]}, "MATCH", "MEASUREMENT_CONVENTION", False, False,
            False, "within 1 %; no change to gross-area logic"),
        row("FOOTINGS", "isolated / combined footings", "m3", {"official": B["FOOTINGS"]["technical_m3"],
                                                               **{k: v for k, v in L(B["FOOTINGS"]["dual_layer"]).items()
                                                                  if k != "official"}},
            {"UC4N": UC4N["FOOTINGS_m3"], "CHRISTIANNP": CNP["FOOTINGS_m3"], "FREELANCER": FREELANCER["FOOTINGS_m3"]},
            "MATCH", "SOURCE_CONFLICT", False, False, True, "F / F10 outline conflict and the F3 count; architecture healthy"),
        row("GROUND_BEAMS", "interior + exterior + boundary beam", "m3", L(gb["volume"]),
            {"UC4N": UC4N["GROUND_BEAMS_m3"], "CHRISTIANNP": CNP["GROUND_BEAMS_m3"],
             "FREELANCER": FREELANCER["GROUND_BEAMS_m3"] + FREELANCER["BOUNDARY_BEAM_m3"]}, "PARTIAL",
            "SOURCE_CONFLICT", False, True, True,
            f"the population is complete in Urban (59 spans, {round(ext_len, 3)} m exterior). Exterior depth is "
            f"unprinted ('FOLLOW ARCH.'); Urban brackets it 0.90-1.30 m from the elevations; the donors' totals imply an "
            f"exterior depth of {implied_d} m. Urban's low was never 'lost geometry' but technical-only publication.",
            counts={"interior_spans": len(gb["spans"]) - len(ext), "exterior_spans": len(ext)}),
        row("STRAPS", "strap beams", "m3", {"official": B["STRAPS"]["technical_m3"], "best": B["STRAPS"]["technical_m3"]},
            {"UC4N": UC4N["STRAPS_m3"], "CHRISTIANNP": CNP["STRAPS_m3"], "FREELANCER": FREELANCER["STRAPS_m3"]},
            "PARTIAL", "DONOR_ASSUMPTION", False, True, True,
            "Urban = freelancer; both oracles ~6.1 m3 - likely band measured through the footings or a deeper section"),
        row("GROUND_SLAB", "slab on grade", "m3", L(gs["volume"]),
            {"UC4N": UC4N["GROUND_SLAB_m3"], "CHRISTIANNP": CNP["GROUND_SLAB_m3"], "FREELANCER": FREELANCER["GROUND_SLAB_m3"]},
            "PARTIAL", "URBAN_BLOCKING_LOSS", True, True, True,
            f"Urban lost the unlabelled cells (now recovered: {gs['area']['BEST_PROVISIONAL_QUANTITY']} m2 net of beams / "
            f"columns at 0.10). The oracles equal the GF gross slab outline {gross_gf} m2 x 0.10 = "
            f"{round(gross_gf * 0.10, 3)} m3 - i.e. they include the ground-beam footprint and openings."),
        row("COLUMNS", "FOUNDATION + GF + 1F + 2F (column + joint)", "m3", L(col["volume"]),
            {"UC4N": UC4N["COLUMNS_m3"], "CHRISTIANNP": round(CNP["COL_FOU_m3"] + CNP["COL_GF_m3"] + CNP["COL_1F_m3"] +
                                                               CNP["COL_2F_m3"], 3)}, "PARTIAL", "MEASUREMENT_CONVENTION",
            True, False, False,
            "totals within ~2 %; the FOUNDATION / GF split differs (Urban: footing top -> GF FFL; donors: footing -> "
            "ground beam / plinth). Urban's earlier low came from clear-height columns + 47 occurrences without a "
            "technical record (now 95 / 95).",
            counts={fl: pf[fl]["occurrences"] for fl in pf}),
        row("COLUMNS_FOU_PLUS_GF", "FOUNDATION + GF storey", "m3",
            {"best": round(pf["FOUNDATION"]["column_plus_joint"]["BEST_PROVISIONAL_QUANTITY"] +
                           pf["GF"]["column_plus_joint"]["BEST_PROVISIONAL_QUANTITY"], 3)},
            {"UC4N": UC4N["COL_FOU_m3"] + UC4N["COL_GF_m3"], "CHRISTIANNP": CNP["COL_FOU_m3"] + CNP["COL_GF_m3"]},
            "MATCH", "MEASUREMENT_CONVENTION", False, False, False, "the split, not the population, differs"),
        row("BEAMS", "downstands (clear length x B x (D - t)) + residue", "m3", L(bm["volume"]),
            {"UC4N": UC4N["BEAMS_m3"], "CHRISTIANNP": CNP["BEAMS_m3"]}, "PARTIAL", "OCCURRENCE_MISSING", True, False, True,
            f"{len(bm['residue_objects'])} residue objects ({sum(1 for o in bm['residue_objects'] if o['terminal'] == 'UNQUANTIFIED')} "
            "tags without a band - possibly repeats of measured beams); the remainder is occurrence interpretation"),
        row("SLABS", "net plate x thickness", "m3", L(sl["volume"]),
            {"UC4N": UC4N["SLABS_m3"], "CHRISTIANNP": CNP["SLABS_m3"]}, "PARTIAL", "DONOR_ASSUMPTION", False, True, True,
            f"implied donor thickness {round(UC4N['SLABS_m3'] / UC4N['NET_SLAB_m2'], 3)} / "
            f"{round(CNP['SLABS_m3'] / CNP['NET_SLAB_m2'], 3)} m vs printed 0.16 (GF, 1F) / 0.18 (2F); U-C4N assumed 0.20 "
            "for GF; the GF conflict void (T16 tag inside) is the remaining area question"),
        row("NET_SLAB_AREA", "gross outline - openings", "m2", L(sl["area"]),
            {"UC4N": UC4N["NET_SLAB_m2"], "CHRISTIANNP": CNP["NET_SLAB_m2"], "FREELANCER": FREELANCER["NET_SLAB_m2"]},
            "PARTIAL", "SOURCE_CONFLICT", False, False, True,
            "Urban high adds back the GF 'VOID' face that carries a T16 tag; every deduction has an opening id "
            "(SLAB_OPENING_RECONCILIATION). The freelancer excludes beam footprints (different basis)"),
        row("BLOCKWORK_200", "wall length", "m", L(walls200), {"UC4N": UC4N["BLOCK_200_m"], "CHRISTIANNP": CNP["BLOCK_200_m"]},
            "PARTIAL", "URBAN_BLOCKING_LOSS", True, True, True,
            f"Urban never measured {round(walls200['BEST_PROVISIONAL_QUANTITY'] - walls200['VERIFIED_QUANTITY'], 3)} m of "
            f"WALL_BAND_AMBIGUOUS bands; with the column-overlap convention (+{round(col_ov200, 3)} m) Urban is "
            f"{round(walls200['BEST_PROVISIONAL_QUANTITY'] + col_ov200, 3)} m. Method B raw pairs = paired wall "
            f"{round(b200['PAIRED_WALL'], 3)} + openings {round(b200['OPENING_SPAN'], 3)} + columns "
            f"{round(b200['COLUMN_OVERLAP_POLICY'], 3)} + duplicates {round(b200['DUPLICATE_FACE'], 3)} m - the larger "
            "donor figure measures through openings and columns"),
        row("BLOCKWORK_150", "wall length", "m", L(wl["length_by_thickness"]["150"]),
            {"UC4N": UC4N["BLOCK_150_m"], "CHRISTIANNP": CNP["BLOCK_150_m"]}, "MATCH", "MEASUREMENT_CONVENTION", False,
            False, False, "positive test - inside the donor range"),
        row("WALL_FACES", "physical wall-face area (finish-independent)", "m2",
            L(wl["physical_faces"]["physical_area"]), {"CHRISTIANNP": CNP["WALL_FACES_m2"]}, "PARTIAL",
            "SCOPE_DIFFERENCE", True, False, True,
            "Urban released only certified room faces before; physical faces now exist first. Urban bands are net of "
            "openings and exclude column / beam faces; the donor figure is gross"),
    ]
    root = [
        {"difference": "GROUND_BEAMS", "q1_urban_rule": "technical release requires a printed depth; 'FOLLOW ARCH.' -> "
         "BLOCKED -> technical 0 for 28 exterior spans (the commercial layer already held 33.09 m3)",
         "q2_objects_excluded": "28 exterior spans (110.299 m) + the boundary-wall beam run",
         "q3_handles": "V3 GROUND_STRUCTURE spans GB-* (bands H2000+H252 ...), C-BWALL S-BOUN run",
         "q4_donor_included_real_objects": "yes - the same spans", "q5_donor_overcount": "no; donors appear to assume a "
         "shallower exterior section (implied depth below Urban's elevation-derived low)",
         "q6_generic_fix": "yes - ground_beam_recovery: depth ladder, measured length / width always kept, BOUNDED scenario",
         "q7_code": "engine/source/ground_beam_recovery.py + evidence_ladder GROUND_BEAM_DEPTH; publish scenario layers",
         "q8_regression": "tests/coverage_recovery_engine::test_beam_with_missing_depth_survives, "
                          "::test_remediation_records_every_attempted_method",
         "q9_project_specific": "the exterior depth bracket 0.90-1.30 m (from the elevations) is project data, not code"},
        {"difference": "GROUND_SLAB", "q1_urban_rule": "a ground-slab region was released only where a 'T=' label sat "
         "inside it; unlabelled cells between ground beams were never measured",
         "q2_objects_excluded": "9 cells, about 101.7 m2 in footprint FP-1",
         "q3_handles": "ST7757 GROUND BEAMS PLAN texts H5782|5776 / H5782|5789 (T=10cm), layers 1 + 2 bands",
         "q4_donor_included_real_objects": "yes - the unlabelled cells", "q5_donor_overcount": "likely - the oracle "
         "figures equal the GF gross slab outline x 0.10, i.e. they also include the ground-beam footprint and openings",
         "q6_generic_fix": "yes - ground_slab_recovery: footprint - bands - columns = cells; label scope as a scenario",
         "q7_code": "engine/source/ground_slab_recovery.py; coverage_anomaly.ground_slab_vs_footprint",
         "q8_regression": "::test_unlabelled_slab_cell_contributes_candidate_area, "
                          "::test_ground_slab_decomposition_recovers_cells_between_beams",
         "q9_project_specific": "the 10 cm thickness and which cells are slab-on-grade"},
        {"difference": "COLUMNS", "q1_urban_rule": "column concrete waited for clear height below beams (beam depth per "
         "face) and the foundation storey waited for the founding level",
         "q2_objects_excluded": "47 of 95 occurrences had no technical concrete (36 foundation + 11 blocked residue)",
         "q3_handles": "S1 COLUMN_OCCURRENCE_REGISTER column_id / plan_source handles",
         "q4_donor_included_real_objects": "yes", "q5_donor_overcount": "no - convention split only",
         "q6_generic_fix": "yes - column_concrete_geometry: B x D x (interval - slab t), independent of rebar",
         "q7_code": "engine/source/column_concrete_geometry.py",
         "q8_regression": "::test_column_rebar_blocker_does_not_block_concrete, ::test_c4n_cn_propagation_error_does_not_happen",
         "q9_project_specific": "storey intervals, slab tags, founding-level range"},
        {"difference": "BEAMS", "q1_urban_rule": "V3a binding rules (NO_BAND_ADJACENT_TO_TAG, SPAN_COUNT_MISMATCH, "
         "BAND_TYPE_CONFLICT ...) blocked residue; GF / 1F residue only reached a BUDGET line outside the total",
         "q2_objects_excluded": "24 residue objects (+1 duplicate); 8 tags have no band at all",
         "q3_handles": "V3b residue ids (ALSENAN_ST7757_DXF|H... TEXT)", "q4_donor_included_real_objects": "partly",
         "q5_donor_overcount": "possible for U-C4N (tags may repeat measured beams)",
         "q6_generic_fix": "yes - beam_occurrence_recovery: every tag / band terminates; continuity + width routes",
         "q7_code": "engine/source/beam_occurrence_recovery.py; evidence_ladder MEMBER_BINDING",
         "q8_regression": "::test_unbound_beam_recovered_from_faces_and_continuity, ::test_source_conflict_emits_both_scenarios",
         "q9_project_specific": "which residue tags duplicate a measured beam"},
        {"difference": "SLABS / NET_SLAB_AREA", "q1_urban_rule": "openings deducted from evidence; one GF void face "
         "carries a T16 tag (conflict) and was deducted silently", "q2_objects_excluded": "GF:SITE-4e71d36d91b40e50 "
         "27.08 m2 (conflict); thickness differences are donor assumptions", "q3_handles": "B2A1 SLAB_REGION faces",
         "q4_donor_included_real_objects": "possibly the conflict face", "q5_donor_overcount": "volume: yes (0.20 m "
         "assumed thickness)", "q6_generic_fix": "yes - slab_opening_reconciliation: opening ids + conflict scenario",
         "q7_code": "engine/source/slab_opening_reconciliation.py",
         "q8_regression": "::test_every_slab_deduction_has_opening_provenance, "
                          "::test_c4n_slab_thickness_assumption_never_overrides_project_rule",
         "q9_project_specific": "whether that GF face is a void"},
        {"difference": "BLOCKWORK_200", "q1_urban_rule": "WALL_BAND_POLICY reports ambiguous bands but never measures "
         "them; column overlap is excluded", "q2_objects_excluded": "12 ambiguous bands (44.3 m of 200 mm)",
         "q3_handles": "A3 WALL_BAND_REGISTER band ids (WB-...)", "q4_donor_included_real_objects": "yes",
         "q5_donor_overcount": "christiannp - yes: through openings / columns / duplicate faces (Method B shows the "
                               "split)", "q6_generic_fix": "yes - ambiguous bands become CANDIDATE length; "
                               "wall_band_reconciliation explains every metre", "q7_code":
         "engine/source/wall_band_reconciliation.py", "q8_regression": "::test_wall_pair_false_positives_are_classified",
         "q9_project_specific": "which ambiguous bands are walls (vs kerbs / parapets)"},
        {"difference": "WALL_FACES / PLASTER", "q1_urban_rule": "faces were released only after room certification and "
         "finish assignment", "q2_objects_excluded": "all uncertified faces", "q3_handles": "V3 BLOCKWORK bands",
         "q4_donor_included_real_objects": "yes", "q5_donor_overcount": "gross basis (openings, column faces)",
         "q6_generic_fix": "yes - physical_wall_faces: face area first, finish after", "q7_code":
         "engine/source/physical_wall_faces.py", "q8_regression": "::test_material_and_paint_uncertainty_keep_physical_and_plaster_area",
         "q9_project_specific": "finish schedule"},
    ]
    return fz, {"POST_FREEZE_MCP_COMPARISON.json": {"difference_register": rows, "freeze_checked": True,
                                                    "donor_sources": {"UC4N": "blind MCP run (brief)",
                                                                      "CHRISTIANNP": "blind MCP run (brief)",
                                                                      "FREELANCER": "FREELANCER_QS_REFERENCE"}},
                "ROOT_CAUSE_REGISTER.json": {"rows": root}}


def main():
    fz, files = build()
    for k, v in files.items():
        (HERE / k).write_text(dumps(v), encoding="utf-8")
    outs = {k: sha((HERE / k).read_bytes()) for k in sorted(list(fz["outputs"]) + list(files))}
    idx = {"round": "COVERAGE_RECOVERY", "freeze": "COVERAGE_RECOVERY_FREEZE.json",
           "freeze_sha256": sha((HERE / "COVERAGE_RECOVERY_FREEZE.json").read_bytes()),
           "blind_outputs": sorted(fz["outputs"]), "post_freeze_outputs": sorted(files), "outputs": outs,
           "extracts": {k: sha((HERE / k).read_bytes()) for k in ("GROUND_SLAB_CELL_EXTRACT.json",
                                                                  "WALL_FACE_PAIR_EXTRACT.json")}}
    (HERE / "INDEX.json").write_text(dumps(idx), encoding="utf-8")
    for r in files["POST_FREEZE_MCP_COMPARISON.json"]["difference_register"]:
        print(f"{r['trade']:20s} best {r['urban_best_provisional']!s:>9} {r['donors']} {r['reason_class']}")


if __name__ == "__main__":
    main()
