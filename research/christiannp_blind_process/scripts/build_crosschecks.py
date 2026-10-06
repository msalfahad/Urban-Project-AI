"""christiannp blind-run forensic handoff - evidence register and Urban-side cross-checks (process diagnostic only).

Evidence classes (one per statement):
  REPORT_EXPLICIT       stated in the sealed report CHRISTIANNP_ALSENAN_BLIND_FULL_BOQ.md. The report file itself is
                        not yet in this environment: every REPORT_EXPLICIT item is imported from the owner's quotation
                        of it and carries report_file_check = PENDING until scripts/verify_report_quotes.py has run
                        against the delivered file.
  URBAN_FROZEN          Urban's own frozen registers, version-stamped (ENGINE_COMMIT / REGISTER_VERSION / DRAWING_SHA /
                        CALCULATION_ROUND).
  ARITHMETIC_INFERENCE  arithmetic on the two classes above; never a donor record.
  NOT_HELD              the chronological MCP transcript, raw LISP, scripts, raw dumps and per-object lists.

It changes nothing: no sealed donor result, no Urban production code, no frozen Urban register.

    python research/christiannp_blind_process/scripts/build_crosschecks.py
"""

from __future__ import annotations

import hashlib
import itertools
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
ROOT = PKG.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

from engine.source import wall_band_reconciliation as WB  # noqa: E402  (read-only use of the generic classifier)

CR = ROOT / "research" / "coverage_recovery_round"
V3B = ROOT / "tests" / "alsenan" / "registers_v3b" / "BOQ_LINES_V3B.json"
V3G = ROOT / "tests" / "alsenan" / "registers_v3" / "GROUND_STRUCTURE_REGISTER.json"
S1L = ROOT / "research" / "alsenan_structural_census_s1" / "STRUCTURAL_LEVEL_REGISTER.json"
OPN = ROOT / "research" / "alsenan_arch_truth_05" / "registers" / "OPENING_EVIDENCE_REGISTER_V3.json"
REPORT_NAME = "CHRISTIANNP_ALSENAN_BLIND_FULL_BOQ.md"
PENDING = "PENDING (report file not yet delivered; imported from the owner's quotation)"

# ---- REPORT_EXPLICIT: figures and statements of the sealed report (via the owner's quotations) ------------------
Q_S31, Q_CR, Q_FH, Q_EC = ("owner brief S3.1 section 16", "owner brief coverage-recovery sections 5-6",
                           "owner brief forensic handoff", "owner brief evidence correction")
REPORT = {
    "BUA_m2": (598.708, Q_S31), "NET_SLAB_GF_m2": (290.555, Q_S31), "NET_SLAB_1F_m2": (179.325, Q_S31),
    "NET_SLAB_2F_m2": (55.275, Q_S31), "NET_SLAB_TOTAL_m2": (525.155, Q_CR), "TOTAL_RC_m3": (333.173, Q_S31),
    "FOOTINGS_m3": (65.669, Q_S31), "STRAPS_m3": (6.053, Q_S31), "GROUND_BEAMS_m3": (36.006, Q_EC),
    "GBP_RAW_LINES": (85, Q_EC), "GBP_PAIRED_STRIPS": (42, Q_EC), "GBP_LENGTH_m": (200.036, Q_EC),
    "GBP_STRIP_WIDTH_mm": (300, Q_EC), "GB_DEPTH_A5_m": (0.60, Q_EC),
    "GROUND_SLAB_m3": (32.404, Q_S31), "GROUND_SLAB_AREA_m2": (324.038, Q_FH), "GROUND_SLAB_T_m": (0.10, Q_FH),
    "COL_FOU_m3": (6.150, Q_S31), "COL_GF_m3": (26.235, Q_S31), "COL_1F_m3": (8.888, Q_S31), "COL_2F_m3": (3.377, Q_S31),
    "BEAMS_GF_m3": (25.206, Q_S31), "BEAMS_1F_m3": (18.562, Q_S31), "BEAMS_2F_m3": (2.823, Q_S31),
    "SLABS_GF_m3": (58.111, Q_S31), "SLABS_1F_m3": (28.692, Q_S31), "SLABS_2F_m3": (9.950, Q_S31),
    "STAIRS_m3": (5.048, Q_S31), "NET_REBAR_t": (22.916, Q_S31), "BLOCK_150_m": (79.971, Q_CR),
    "BLOCK_200_m": (183.497, Q_CR), "WALL_FACES_GROSS_m2": (2364.7, Q_CR), "RASTER_CELL_mm": (50, Q_EC),
}
ASSUMPTIONS = {   # A1-A15 as quoted by the owner from the report
    "A1": "GF slab t = 0.20", "A2": "GF column base +/-0.00", "A3": "foundation neck height 1.00",
    "A4": "2F roof top +13.90", "A5": "ground-beam depth 0.60", "A6": "blinding 0.10 + 0.10 projection",
    "A7": "ground slab = GF gross outline", "A8": "CN continued through FOU + GR",
    "A9": "stair waist / landing assumptions", "A10": "wall height = floor-to-floor - slab thickness",
    "A11": "ceiling = net slab above", "A12": "structural levels = architectural FFL", "A13": "door leaf height 2.10",
    "A14": "floor / ceiling area from slab net area", "A15": "roof waterproofing = SFRS slab only, no upturns",
}
BEAM_RULES = {
    "R1": "continuous beam allocated once per plan, capped at schedule total span; width match preferred, then length",
    "R2": "CB may continue collinearly into an adjacent unlabeled strip",
    "R3": "same-mark labels < 2 m apart are merged",
    "R4": "if schedule width differs from drawn strip width by > 60 mm, the strip is assigned to the matching-width "
          "label instead",
    "R5": "remaining strip length is shared equally among simple labels",
}
RASTER_REPORT = {"cell_mm": 50, "primitives": "layer-1 lines + arcs", "outside": "exterior flood fill",
                 "classes": ["SLAB_LABELLED", "BEAM_INTERIOR", "OPENING", "UNRESOLVED_ENCLOSED", "EDGE_LINE_CELLS"]}
UNRESOLVED_REBAR = ["continuous-beam T/M fields", "BOXED footing bars", "ground-beam reinforcement",
                    "missing slab direction", "slab top bars without extent", "CN reinforcement", "CB MID/support bars",
                    "top hangers", "stair reinforcement"]
UNRESOLVED_REBAR_NOTE = "the owner's quotation ends in 'etc.': the full list is in the report and is imported " \
                        "completely only when the file is delivered"
UC4N_REPORTED = {"COL_FOU_m3": 6.150, "COL_GF_m3": 26.235, "COL_1F_m3": 8.888, "COL_2F_m3": 3.797,
                 "GROUND_BEAMS_m3": 36.005, "GROUND_SLAB_m3": 32.183, "SLABS_m3": 95.689, "STAIRS_m3": 5.325,
                 "NET_SLAB_GF_m2": 291.425, "NET_SLAB_1F_m2": 171.235, "NET_SLAB_2F_m2": 55.590, "BUA_m2": 590.362,
                 "FOOTINGS_m3": 66.579, "GF_SLAB_T_ASSUMED_m": 0.20}   # owner briefs (S3.1 s16, coverage s4)


def R(k):
    return REPORT[k][0]


def J(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def r3(x):
    return None if x is None else round(x, 3)


def git_commit(p):
    out = subprocess.run(["git", "log", "-1", "--format=%h", "--", str(p.relative_to(ROOT))], cwd=ROOT,
                         capture_output=True, text=True).stdout.strip()
    return out or "UNCOMMITTED"


def stamp(p, rnd, drawing):
    return {"ENGINE_COMMIT": git_commit(p), "REGISTER_VERSION": f"{p.relative_to(ROOT)}@{sha(p)[:16]}",
            "DRAWING_SHA": drawing, "CALCULATION_ROUND": rnd}


# ---- ground beams --------------------------------------------------------------------------------------------------
def ground_beams(Q, G, V):
    gb = Q["ground_beams"]
    groups = defaultdict(lambda: {"spans": 0, "length_m": 0.0, "urban_m3": 0.0})
    for s in gb["spans"]:
        g = groups[(s["kind"], s["B_m"], s["depth_m"], s["depth_level"])]
        g["spans"] += 1
        g["length_m"] += s["length_m"]
        g["urban_m3"] += s["part"]["best"]
    rows = [{"kind": k, "B_m": b, "urban_depth_m": d, "urban_depth_level": lvl, "spans": g["spans"],
             "length_m": r3(g["length_m"]), "urban_best_m3": r3(g["urban_m3"]),
             "at_report_section_m3": r3(g["length_m"] * 0.30 * R("GB_DEPTH_A5_m")),
             "report_section_minus_urban_m3": r3(g["length_m"] * 0.30 * R("GB_DEPTH_A5_m") - g["urban_m3"])}
            for (k, b, d, lvl), g in sorted(groups.items())]
    L_u, L_d = gb["length_m"], R("GBP_LENGTH_m")
    return {
        "REPORT_EXPLICIT": {"geometry": {"raw_lines": R("GBP_RAW_LINES"), "paired_strips": R("GBP_PAIRED_STRIPS"),
                                         "length_m": L_d, "strip_width_mm": R("GBP_STRIP_WIDTH_mm")},
                            "depth": {"value_m": R("GB_DEPTH_A5_m"), "status": "ASSUMPTION A5"},
                            "volume": {"value_m3": R("GROUND_BEAMS_m3"),
                                       "basis": "drawn width x 0.60 assumed depth (A5) x total length",
                                       "status": "ASSUMPTION-DEPENDENT - not a source-measured volume"},
                            "report_file_check": PENDING},
        "ARITHMETIC_INFERENCE": {
            "check": f"{L_d} x 0.30 x 0.60 = {round(L_d * 0.30 * 0.60, 4)}",
            "matches_report": abs(L_d * 0.30 * 0.60 - R("GROUND_BEAMS_m3")) < 0.001,
            "raw_lines_vs_strips": f"{R('GBP_RAW_LINES')} raw lines for {R('GBP_PAIRED_STRIPS')} pairs: "
                                   f"{R('GBP_RAW_LINES') - 2 * R('GBP_PAIRED_STRIPS')} line(s) left unpaired or one "
                                   "face shared/split (which, NOT_HELD)"},
        "URBAN_FROZEN": {"bands": G["ground"]["bands"], "spans": G["ground"]["spans"],
                         "columns_on_sheet": G["ground"]["columns_on_sheet"], "band_source": G["ground"]["source"],
                         "length_m": L_u, "conservation_ok": gb["conservation"]["ok"],
                         "boundary_beam_line": gb["boundary_beam_line"], "by_section_class": rows,
                         "version": {"spans_and_sections": V["CR"], "bands": V["V3G"]}},
        "length_difference_m": r3(L_d - L_u), "length_difference_pct": round(100 * (L_d - L_u) / L_u, 2),
        "segmentation": {"report_paired_strips": R("GBP_PAIRED_STRIPS"), "urban_paired_bands": G["ground"]["bands"],
                         "urban_spans": G["ground"]["spans"],
                         "reading": "at the band level the two reconstructions nearly coincide (42 vs 43 paired "
                                    "bands); Urban's 59 is the same network split at supports (36 columns on the "
                                    "sheet). Node connectivity cannot be compared: the report's strip end points are "
                                    "NOT_HELD and Urban's frozen register keeps lengths, not band coordinates.",
                         "future_test": "compare TOTAL NETWORK LENGTH, NODE CONNECTIVITY (end / T / L / X nodes, "
                                        "components) and SEGMENTATION (bands vs spans) - never span counts alone"},
        "finding": "INDEPENDENT_EXTRACTION_AGREEMENT on length (+%.3f m, %.2f%%); the volume difference is section "
                   "(A5) and release, not population" % (L_d - L_u, 100 * (L_d - L_u) / L_u),
    }


# ---- slabs ----------------------------------------------------------------------------------------------------------
def slabs(Q):
    sheets = Q["slabs"]["sheets"]
    out = {}
    for fl in ("GF", "1F", "2F"):
        s = sheets[fl]
        net_d, vol_d = R(f"NET_SLAB_{fl}_m2"), R(f"SLABS_{fl}_m3")
        if fl == "GF":
            gross_d, basis = R("GROUND_SLAB_AREA_m2"), "report ground-slab area = report GF gross outline (A7)"
        else:
            gross_d, basis = s["gross_m2"], "Urban gross (report gross for this floor not imported)"
        ded = gross_d - net_d
        ops = [(o["opening_id"], o["area_m2"], o["role"], o["state"]) for o in s["openings"]]
        cands = []
        for k in range(len(ops) + 1):
            for combo in itertools.combinations(ops, k):
                a = sum(c[1] for c in combo)
                cands.append({"deducted": [c[0] for c in combo], "roles": sorted({c[2] for c in combo}),
                              "sum_m2": r3(a), "residual_m2": r3(ded - a)})
        cands.sort(key=lambda c: abs(c["residual_m2"]))
        out[fl] = {"report_net_m2": net_d, "report_volume_m3": vol_d,
                   "inferred_thickness_m": round(vol_d / net_d, 4), "urban_gross_m2": s["gross_m2"],
                   "urban_openings_m2": r3(sum(o[1] for o in ops)),
                   "urban_net_m2": r3(s["gross_m2"] - sum(o[1] for o in ops)), "gross_used_m2": gross_d,
                   "gross_basis": basis, "inferred_report_deductions_m2": r3(ded),
                   "urban_openings": [{"opening_id": o[0], "area_m2": o[1], "role": o[2], "state": o[3]} for o in ops],
                   "deduction_hypotheses_ranked": cands[:4],
                   "hypothesis_status": "UNIQUE" if len(ops) == 0 else
                   "NON_UNIQUE until the report's per-class raster areas (OPENING / UNRESOLVED_ENCLOSED / "
                   "EDGE_LINE_CELLS) are imported"}
    return {"floors": out, "inferred_thicknesses_m": {f: out[f]["inferred_thickness_m"] for f in out},
            "A1_effect_m3": r3(R("SLABS_GF_m3") - R("NET_SLAB_GF_m2") * 0.16),
            "pattern": "best fits on GF and 1F deduct the VOID openings and keep the 10.725 m2 stair well; the "
                       "report's own OPENING / UNRESOLVED_ENCLOSED class areas will confirm or refute this"}


# ---- columns ----------------------------------------------------------------------------------------------------
def columns(Q, L):
    A, N, n = defaultdict(float), defaultdict(float), Counter()
    for x in Q["columns"]["records"]:
        A[x["floor"]] += x["A_m2"]
        N[x["floor"]] += x["net_of_slab_m3"] or 0.0
        n[x["floor"]] += 1
    ffl = {iv["storey"]: (iv.get("lower_ffl_m"), iv.get("upper_ffl_m")) for iv in L["intervals"]}
    # the report's own vertical model: FOU = neck 1.00 (A3); GF base +/-0.00 (A2); levels = FFL (A12); roof +13.90 (A4)
    model = {"FOUNDATION": {"full": 1.00, "to_soffit": 1.00},
             "GF": {"full": ffl["GF"][1] - 0.0, "to_soffit": ffl["GF"][1] - 0.0 - 0.20},       # A1 0.20 above GF
             "1F": {"full": ffl["1F"][1] - ffl["1F"][0], "to_soffit": ffl["1F"][1] - ffl["1F"][0] - 0.16},
             "2F": {"full": 13.90 - ffl["2F"][0], "to_soffit": 13.90 - ffl["2F"][0] - 0.18}}
    key = {"FOUNDATION": "COL_FOU_m3", "GF": "COL_GF_m3", "1F": "COL_1F_m3", "2F": "COL_2F_m3"}
    rows = {}
    for fl, k in key.items():
        h = model[fl]
        rows[fl] = {"urban_occurrences": n[fl], "urban_section_sum_m2": r3(A[fl]), "urban_net_m3": r3(N[fl]),
                    "report_m3": R(k), "uc4n_reported_m3": UC4N_REPORTED[k],
                    "report_model_height_m": {kk: r3(v) for kk, v in h.items()},
                    "implied_report_section_sum_m2": {kk: r3(R(k) / v) for kk, v in h.items()},
                    "implied_minus_urban_section_m2": {kk: r3(R(k) / v - A[fl]) for kk, v in h.items()}}
    return {
        "floors": rows,
        "FOU_plus_GF": {"urban_m3": r3(N["FOUNDATION"] + N["GF"]), "report_m3": r3(R("COL_FOU_m3") + R("COL_GF_m3"))},
        "urban_levels": {"version": "see stamps", "GF_FFL_m": ffl["GF"][0], "1F_FFL_m": ffl["1F"][0],
                         "2F_FFL_m": ffl["2F"][0], "floor_to_floor_status": "PRINTED (P7757 VE-AA-09)",
                         "founding_level": "not printed (>= 1.5 m below plot level)",
                         "slab_top_vs_ffl": "structural slab top = FFL - build-up (build-up not printed)"},
        "readings": [
            "FOU/GF split explained by A2 + A3: the report's FOU is the 1.00 m neck only (6.150 / 1.00 = 6.15 m2 of "
            "section vs Urban 6.24 m2); its GF starts at +/-0.00, 1.00 m below the printed GF FFL +1.00 where Urban's "
            "GF starts. FOU + GF totals agree within 0.23 m3.",
            "1F / 2F: under the report's own level model the implied section sums are 0.24-0.33 m2 (1F) and "
            "0.10-0.14 m2 (2F) smaller than Urban's, whichever column top is used - a population or section "
            "difference, not a height convention. (The earlier package's 'clear of beams' hypothesis is withdrawn.)",
            "GF: implied 4.77-4.95 m2 vs Urban 4.50 m2 - consistent with A8 (CN carried through GR) adding sections.",
        ]}


# ---- footings / beams --------------------------------------------------------------------------------------------
def footings():
    lines = {r["code"]: r for r in J(V3B)["lines"]}
    ftg, ff10 = lines["C-FTG"], lines["C-FTG-FF10"]
    occ = [{"seq": i + 1, "type": d["ref"], "formula": d["formula"], "urban_m3": d["qty"], "status": d["status"],
            "report_m3": "NOT_HELD (per-occurrence list not imported)"} for i, d in enumerate(ftg["details"])]
    vol = {o["type"]: o["urban_m3"] for o in occ if o["urban_m3"] is not None}
    diff = R("FOOTINGS_m3") - ftg["qty"]
    opts = []
    for fname, fv in {"F/F10 excluded (Urban technical)": 0.0, "F/F10 as 2 x F": 0.432,
                      "F/F10 as 1 x F10": 1.960}.items():
        for k in (0, 1, 2):
            for combo in itertools.combinations_with_replacement(sorted(vol), k):
                add = sum(vol[t] for t in combo)
                opts.append({"f_f10": fname, "extra_occurrences": list(combo), "added_m3": r3(fv + add),
                             "residual_m3": r3(diff - fv - add)})
    opts.sort(key=lambda o: abs(o["residual_m3"]))
    return {"urban_released_m3": ftg["qty"], "urban_occurrences": len([o for o in occ if o["urban_m3"] is not None]),
            "urban_blocked_outlines": [o["type"] for o in occ if o["urban_m3"] is None],
            "urban_type_counts": dict(sorted(Counter(o["type"] for o in occ if o["urban_m3"] is not None).items())),
            "urban_occurrences_table": occ, "f_f10_scenarios": ff10["formula"], "report_m3": R("FOOTINGS_m3"),
            "difference_m3": r3(diff), "candidate_decompositions_ranked": opts[:8],
            "status": "NON_UNIQUE until the report's footing occurrence table is imported"}


def beams():
    lines = {r["code"]: r for r in J(V3B)["lines"]}
    rows = {}
    for fl, tech, res, extra in (("GF", "C-BEAM-GF", "C-BEAM-GF-RES", ()),
                                 ("1F", "C-BEAM-1F", "C-BEAM-1F-RES", ("C-DOME-RING-12EB", "C-DOME-RING-2F33")),
                                 ("2F", "C-BEAM-2F", None, ("C-DOME-RING-1300",))):
        t = lines[tech]["qty"] or 0.0
        rq = (lines[res]["release"]["commercial"].get("qty") or 0.0) if res else 0.0
        ex = sum(lines[e]["release"]["commercial"].get("qty") or 0.0 for e in extra)
        rows[fl] = {"urban_technical_m3": r3(t), "urban_residue_commercial_m3": r3(rq),
                    "urban_dome_ring_commercial_m3": r3(ex), "report_m3": R(f"BEAMS_{fl}_m3"),
                    "report_minus_urban_technical_m3": r3(R(f"BEAMS_{fl}_m3") - t),
                    "report_minus_urban_technical_plus_residue_m3": r3(R(f"BEAMS_{fl}_m3") - t - rq)}
    return {"floors": rows, "rules": "R1-R5 (REPORT_EXPLICIT); per-strip allocations NOT_HELD"}


# ---- plaster (corrected) -----------------------------------------------------------------------------------------
def plaster(Q, L):
    Lw = R("BLOCK_150_m") + R("BLOCK_200_m")
    gf = [iv for iv in L["intervals"] if iv["storey"] == "GF"][0]["floor_to_floor_m"]
    hmax = gf - 0.20                       # A10 with A1: the tallest wall the report's own rule can produce
    pf = Q["walls"]["physical_faces"]
    return {"report_gross_faces_m2": R("WALL_FACES_GROSS_m2"), "report_wall_pair_length_m": r3(Lw),
            "report_height_rule": "A10 wall height = floor-to-floor - slab thickness; A13 door leaf 2.10",
            "ARITHMETIC_INFERENCE": {
                "max_two_faces_at_A10_GF_height_m2": r3(2 * Lw * hmax),
                "excess_over_that_bound_m2": r3(R("WALL_FACES_GROSS_m2") - 2 * Lw * hmax),
                "reading": "even with every wall at the GF A10 height (4.30 m), both faces and no deduction, the "
                           "wall-pair lengths give at most %.1f m2 < 2364.7 m2: the plaster figure contains faces "
                           "beyond the paired wall lengths (columns, exterior / parapet faces or other surfaces). "
                           "The earlier package's 'uniform 4.49 m, no deductions' reading is WITHDRAWN; the "
                           "composition is in the report and is imported when the file is delivered."
                           % (2 * Lw * hmax)},
            "urban_physical_faces": {"basis": pf["basis"], "faces": pf["faces"],
                                     "verified_m2": pf["physical_area"]["VERIFIED_QUANTITY"],
                                     "best_m2": pf["physical_area"]["BEST_PROVISIONAL_QUANTITY"],
                                     "by_floor_role_m2": pf["by_floor_role"]}}


# ---- wall pairing diagnostic ------------------------------------------------------------------------------------
def wall_pairing(W):
    rows, tot = [], defaultdict(lambda: defaultdict(float))
    for fl in sorted(W["floors"]):
        f = W["floors"][fl]
        for w, ivs in sorted(f["pairs"].items()):
            cl = WB.classify([dict(iv) for iv in ivs], column_boxes=[tuple(c) for c in f["column_boxes"]],
                             opening_boxes=[tuple(c) for c in f["opening_boxes"]])
            for iv in cl:
                parts, L = iv["parts"], iv["length"]
                main = max(parts, key=parts.get) if parts else "EMPTY"
                share = parts.get("PAIRED_WALL", 0.0) / L if L else 0.0
                conf = ("REJECT" if "DUPLICATE_FACE" in parts else "HIGH" if share >= 0.9 else
                        "MEDIUM" if share >= 0.5 else "LOW")
                rows.append({"floor": fl, "width_mm": iv["width"], "face_handle_a": iv["a"], "face_handle_b": iv["b"],
                             "overlap_length_m": round(L / 1000.0, 3),
                             "parts_m": {k: round(v / 1000.0, 3) for k, v in sorted(parts.items())},
                             "accepted_reason": main, "confidence": conf})
                for k, v in parts.items():
                    tot[f"{fl}|{w}"][k] += v / 1000.0
                    tot[f"ALL|{w}"][k] += v / 1000.0
    totals = {k: {c: round(v, 3) for c, v in sorted(d.items())} for k, d in sorted(tot.items())}
    gross = {w: round(sum(totals[f"ALL|{w}"].values()), 3) for w in ("150", "200")}
    return {
        "christiannp_pairs": "NOT_PRESERVED_IN_THIS_ENVIRONMENT - the sealed run's raw pair list is not in the "
                             "report as quoted and no raw output was delivered; no row below is a donor row",
        "christiannp_parameters": {k: "NOT_HELD" for k in (
            "source_layers", "line_types", "parallel_tolerance", "width_buckets", "overlap_threshold",
            "nearest_pair_rule", "de_duplication", "intersections", "t_junctions", "columns", "openings",
            "short_segments", "curved_walls", "finish_lines", "false_positive_prevention")},
        "urban_method_b": {"rule": W["rule"], "wall_layer": W["layer"], "column_layer": W["column_layer"],
                           "opening_layers": W["opening_layers"], "source_dxf_sha256": W["source"],
                           "classifier": "engine.source.wall_band_reconciliation.classify (unchanged)"},
        "urban_method_b_totals_m": totals, "urban_method_b_gross_m": gross,
        "report_m": {"150": R("BLOCK_150_m"), "200": R("BLOCK_200_m")},
        "report_minus_method_b_gross_m": {w: r3(R(f"BLOCK_{w}_m") - gross[w]) for w in ("150", "200")},
        "reading": "the report's 200 mm length sits within %.1f m of Urban's UNCLASSIFIED Method-B gross: "
                   "ARITHMETIC_INFERENCE that the donor total is raw pairing before classification"
                   % abs(R("BLOCK_200_m") - gross["200"]),
        "rows": rows,
    }


# ---- donor agreement ---------------------------------------------------------------------------------------------
def agreement(col, sl, gb):
    return {"classes": ["INDEPENDENT_EXTRACTION_AGREEMENT", "SHARED_SOURCE_AGREEMENT", "SHARED_ASSUMPTION_AGREEMENT",
                        "CORRELATED_REASONING", "UNDETERMINED"],
            "rule": "agreement raises confidence only when the routes are INDEPENDENT_EXTRACTION_AGREEMENT; both "
                    "donor runs were agent sessions working from the same owner brief, so donor-donor agreement is "
                    "CORRELATED_REASONING unless shown otherwise",
            "rows": [
                {"element": "COLUMNS", "pair": "christiannp vs U-C4N",
                 "values": {k: [R(k), UC4N_REPORTED[k]] for k in ("COL_FOU_m3", "COL_GF_m3", "COL_1F_m3", "COL_2F_m3")},
                 "class": "SHARED_ASSUMPTION_AGREEMENT",
                 "why": "three floors identical to the litre; christiannp's FOU and GF rest on A2 + A3 (and A8); "
                        "identical values from a different route would need the same height model and population. "
                        "U-C4N's own assumptions are not in this environment."},
                {"element": "COLUMNS (FOU+GF total)", "pair": "christiannp vs Urban",
                 "values": col["FOU_plus_GF"], "class": "INDEPENDENT_EXTRACTION_AGREEMENT",
                 "why": "different routes (S1 census vs donor outlines) agree on the total within 0.23 m3; the split "
                        "differs by convention"},
                {"element": "SLABS (volume)", "pair": "christiannp vs U-C4N",
                 "values": {"christiannp_m3": r3(R("SLABS_GF_m3") + R("SLABS_1F_m3") + R("SLABS_2F_m3")),
                            "uc4n_m3": UC4N_REPORTED["SLABS_m3"]},
                 "class": "SHARED_ASSUMPTION_AGREEMENT",
                 "why": "both assumed GF t = 0.20 (christiannp A1; U-C4N per the coverage brief); A1 alone is "
                        "+%.3f m3" % sl["A1_effect_m3"]},
                {"element": "SLAB NET AREA", "pair": "christiannp vs U-C4N vs Urban",
                 "values": {fl: {"christiannp": R(f"NET_SLAB_{fl}_m2"), "uc4n": UC4N_REPORTED[f"NET_SLAB_{fl}_m2"],
                                 "urban": sl["floors"][fl]["urban_net_m2"]} for fl in ("GF", "1F", "2F")},
                 "class": "INDEPENDENT_EXTRACTION_AGREEMENT on GF / 2F donor-donor (raster vs vector); "
                          "UNDETERMINED on 1F (8.1 m2 apart) and on Urban vs donors (opening classification)",
                 "why": "areas come from geometry, not from a shared constant"},
                {"element": "GROUND BEAMS (volume)", "pair": "christiannp vs U-C4N",
                 "values": {"christiannp_m3": R("GROUND_BEAMS_m3"), "uc4n_m3": UC4N_REPORTED["GROUND_BEAMS_m3"]},
                 "class": "SHARED_ASSUMPTION_AGREEMENT",
                 "why": "christiannp = length x 0.30 x 0.60 (A5); U-C4N 36.005 / 0.18 = %.3f m - the same depth "
                        "assumption on the same length" % (UC4N_REPORTED["GROUND_BEAMS_m3"] / 0.18)},
                {"element": "GROUND BEAMS (length)", "pair": "christiannp vs Urban",
                 "values": {"christiannp_m": R("GBP_LENGTH_m"), "urban_m": gb["URBAN_FROZEN"]["length_m"],
                            "christiannp_strips": R("GBP_PAIRED_STRIPS"), "urban_bands": gb["URBAN_FROZEN"]["bands"]},
                 "class": "INDEPENDENT_EXTRACTION_AGREEMENT", "why": "two pairing implementations, +0.62 %"},
                {"element": "GROUND SLAB", "pair": "christiannp vs U-C4N",
                 "values": {"christiannp_m3": R("GROUND_SLAB_m3"), "uc4n_m3": UC4N_REPORTED["GROUND_SLAB_m3"]},
                 "class": "SHARED_SOURCE_AGREEMENT (thickness: the T=10 cm text) + SHARED_ASSUMPTION_AGREEMENT "
                          "(area: GF gross outline, A7)",
                 "why": "thickness and area authorities are separate; only the thickness is source"},
                {"element": "STAIRS", "pair": "christiannp vs U-C4N",
                 "values": {"christiannp_m3": R("STAIRS_m3"), "uc4n_m3": UC4N_REPORTED["STAIRS_m3"]},
                 "class": "UNDETERMINED", "why": "both assumption-dependent (christiannp A9); 5 % apart; the stair "
                                                 "breakdown is in the report but not imported"},
                {"element": "FOOTINGS", "pair": "all three",
                 "values": {"christiannp": R("FOOTINGS_m3"), "uc4n": UC4N_REPORTED["FOOTINGS_m3"], "urban": 64.346},
                 "class": "SHARED_SOURCE_AGREEMENT", "why": "same schedule L x W x H; differences are occurrence "
                                                            "counts (F3, F / F10, FN)"},
                {"element": "BUA", "pair": "all three",
                 "values": {"christiannp": R("BUA_m2"), "uc4n": UC4N_REPORTED["BUA_m2"], "urban": 595.092},
                 "class": "INDEPENDENT_EXTRACTION_AGREEMENT", "why": "within 1.4 % across three geometry routes"},
            ]}


# ---- assumptions A1-A15 / beam rules / raster / rebar ---------------------------------------------------------
def assumptions(sl, col, opn):
    door = Counter((r["height"]["m"], r["height"].get("authority")) for r in opn["rows"]
                   if "DOOR" in r["type"] and r["height"]["m"] is not None)
    C = {
        "A1": ("ASSUMPTION", "KNOWN_WRONG_AFTER_URBAN_REVIEW", "REJECT_FOR_PRODUCTION",
               "project default 0.16 unless locally noted (S1 STRUCTURAL_LEVEL_REGISTER: PROJECT_DEFAULT p.8 n.18)",
               f"+{sl['A1_effect_m3']} m3 on GF slabs"),
        "A2": ("ASSUMPTION", "PLAUSIBLE_BUT_UNVERIFIED", "REJECT_FOR_PRODUCTION",
               "a storey-boundary convention: printed GF FFL is +1.00; moving the base to +/-0.00 shifts ~1 m of "
               "column into GF without changing the FOU+GF total", "moves volume between FOU and GF; total neutral"),
        "A3": ("ASSUMPTION", "PLAUSIBLE_BUT_UNVERIFIED", "REJECT_FOR_PRODUCTION",
               "founding level not printed (>= 1.5 m below plot level); a constant 1.00 m neck under-reaches "
               "shallow footings (0.30 m deep footings would found at -1.30)", "FOU = section sum x 1.00"),
        "A4": ("DERIVED", "SOURCE_SUPPORTED", "ACCEPT_AS_DERIVED_LEVEL",
               "+9.70 + 4.20 printed floor-to-floor = +13.90; Urban also reads +13.90 at the tower-roof dome ring",
               "none against Urban"),
        "A5": ("ASSUMPTION", "KNOWN_WRONG_AFTER_URBAN_REVIEW", "REJECT_FOR_PRODUCTION",
               "p.13 details give 0.30 / 0.40 m on 27 of 31 interior spans; exterior depth unprinted (elevation "
               "bracket 0.90-1.30 m)", "about 6.0 m3 per 0.10 m of depth over 200 m"),
        "A6": ("ASSUMPTION", "SOURCE_SUPPORTED", "ACCEPT_WHERE_DETAIL_APPLIES",
               "Urban V3b reads the local blinding detail (10 cm, 10 cm beyond) - SOURCE_DETAIL_LOCAL_BLINDING",
               "none against Urban"),
        "A7": ("ASSUMPTION", "PLAUSIBLE_BUT_UNVERIFIED", "REJECT_FOR_PRODUCTION",
               "candidate physical scope only: the suspended GF outline includes ground-beam and column footprints",
               "about 10.7 m3 above Urban's best cells"),
        "A8": ("ASSUMPTION", "KNOWN_WRONG_AFTER_URBAN_REVIEW", "REJECT_FOR_PRODUCTION",
               "conflicts with S1 chains and the human review", "adds GF section (implied +0.27-0.45 m2)"),
        "A9": ("ASSUMPTION", "PLAUSIBLE_BUT_UNVERIFIED", "REJECT_FOR_PRODUCTION",
               "stair waist / landing values not cross-checked here", "stairs 5.048 m3 depends on it"),
        "A10": ("DERIVED", "PLAUSIBLE_BUT_UNVERIFIED", "REJECT_FOR_PRODUCTION",
                "ignores beams over walls (Urban: interval - terminating member) and uses A1 0.20 on GF",
                "overstates every wall that stops under a beam"),
        "A11": ("DERIVED", "PLAUSIBLE_BUT_UNVERIFIED", "REJECT_FOR_PRODUCTION",
                "slab net area is not a room ceiling: beam soffits and sides and room boundaries differ",
                "ceiling area"),
        "A12": ("ASSUMPTION", "PLAUSIBLE_BUT_UNVERIFIED", "REJECT_FOR_PRODUCTION",
                "Urban: structural slab top = FFL - floor build-up, build-up not printed", "every vertical interval"),
        "A13": ("ASSUMPTION", "PLAUSIBLE_BUT_UNVERIFIED", "REJECT_FOR_PRODUCTION",
                "Urban opening evidence: most internal doors 2.117 m (cross-verified) - close; but repeated 2.607 m "
                "types and one 3.65 m glazed door exist: %s" % dict(sorted(door.items(), key=lambda kv: -kv[1])[:5]),
                "door deductions on walls / plaster"),
        "A14": ("ASSUMPTION", "KNOWN_WRONG_AFTER_URBAN_REVIEW", "REJECT_FOR_PRODUCTION",
                "slab net area includes wall footprints and non-room areas; Urban measures floors and ceilings per "
                "room", "floor and ceiling finishes"),
        "A15": ("ASSUMPTION", "KNOWN_WRONG_AFTER_URBAN_REVIEW", "REJECT_FOR_PRODUCTION",
                "omits waterproofing upturns and any other exposed roof / terrace than SFRS",
                "roof waterproofing under-measured"),
    }
    rows = []
    for k, text in ASSUMPTIONS.items():
        nature, review, prod, basis, sens = C[k]
        rows.append({"id": k, "assumption": text, "evidence": "REPORT_EXPLICIT", "report_file_check": PENDING,
                     "nature": nature, "urban_review": review, "production": prod, "urban_basis": basis,
                     "sensitivity": sens, "should_urban_adopt": prod.startswith("ACCEPT"),
                     "generic_fallback_candidate": k in ("A4", "A6")})
    return {"classification_values": ["SOURCE_SUPPORTED", "DERIVED", "ASSUMPTION", "KNOWN_WRONG_AFTER_URBAN_REVIEW",
                                      "PLAUSIBLE_BUT_UNVERIFIED", "REJECT_FOR_PRODUCTION"],
            "fields": "nature = what the report did; urban_review = status after Urban's source reading; production "
                      "= Urban decision", "rows": rows}


def beam_rules():
    A = {
        "R1": dict(useful_generic_idea="yes: a continuous beam is one occurrence per plan, bounded by its schedule",
                   unsafe_heuristic="capping hides a missing support or a span-count conflict",
                   oracle_only=False, production_candidate="partly: occurrence-once + width-first ranking; the "
                   "cap becomes a SPAN_LENGTH_CONFLICT check, never a truncation",
                   failure_modes=["drawn spans longer than the schedule are silently cut",
                                  "two CBs of one mark on one plan collapse to one",
                                  "width tie broken by length picks the wrong strip"],
                   tests=["test_cb_allocated_once_per_plan", "test_cb_span_excess_is_conflict_not_truncation",
                          "test_cb_width_match_ranks_before_length"]),
        "R2": dict(useful_generic_idea="yes: collinear continuation is real evidence of one member",
                   unsafe_heuristic="an unlabelled collinear strip may be a different beam (lintel, edge beam)",
                   oracle_only=False, production_candidate="as CANDIDATE continuity with a width check and an end "
                   "condition (support / column) - never VERIFIED",
                   failure_modes=["continuation through a column into a different member",
                                  "collinear but offset strips merged"],
                   tests=["test_collinear_continuation_requires_same_width",
                          "test_continuation_stops_at_support_with_new_tag",
                          "test_continuation_is_candidate_not_verified"]),
        "R3": dict(useful_generic_idea="partly: repeated tags of one member exist",
                   unsafe_heuristic="a fixed 2 m distance is drawing-scale dependent and merges two short beams",
                   oracle_only=True, production_candidate="no; de-duplicate by shared strip geometry, not distance",
                   failure_modes=["two real 1.5 m beams with the same mark merged",
                                  "the same tag 2.1 m apart counted twice"],
                   tests=["test_same_mark_on_same_strip_is_one_occurrence",
                          "test_same_mark_on_different_strips_is_two_occurrences_regardless_of_distance"]),
        "R4": dict(useful_generic_idea="yes: drawn width vs schedule width is strong binding evidence",
                   unsafe_heuristic="silently re-assigning to another label can bind a strip to a label that is "
                                    "elsewhere; 60 mm is a fixed tolerance",
                   oracle_only=False, production_candidate="yes as a gate: WIDTH_MISMATCH recorded on the binding, "
                   "re-assignment only to a label that is also geometrically adjacent, tolerance from drawing units",
                   failure_modes=["finish lines at beam width pass the gate",
                                  "re-assignment across the plan to a distant same-width label"],
                   tests=["test_width_mismatch_flags_binding", "test_reassignment_requires_adjacency",
                          "test_width_tolerance_scales_with_units"]),
        "R5": dict(useful_generic_idea="no",
                   unsafe_heuristic="arithmetic allocation: assigns length to labels without geometry; any error "
                                    "is spread invisibly across members",
                   oracle_only=True, production_candidate="NO - reject for production; unallocated length stays a "
                   "CANDIDATE residue with identity (Urban beam_occurrence_recovery)",
                   failure_modes=["a missing strip is hidden by stretching others",
                                  "labels of different sections share one strip's length",
                                  "rebar inherits the wrong length"],
                   tests=["test_unallocated_strip_length_is_residue_not_shared",
                          "test_no_label_receives_length_without_geometry"]),
    }
    return {"rows": [dict(id=k, rule=BEAM_RULES[k], evidence="REPORT_EXPLICIT", report_file_check=PENDING, **A[k])
                     for k in BEAM_RULES]}


def raster_spec():
    return {
        "REPORT_EXPLICIT": dict(RASTER_REPORT, report_file_check=PENDING,
                                output_class_areas="present in the report per the owner; values not yet imported"),
        "NOT_HELD": ["exact grid origin", "bounding region", "line / arc rasterisation implementation",
                     "stroke thickness", "flood-fill seed and code", "class assignment rules", "edge-cell allocation",
                     "exact cell list", "tolerances", "raw script"],
        "recommendation": "rebuild an INDEPENDENT Urban raster oracle; do not copy unseen donor code",
        "urban_oracle_design": {
            "input": "layer-filtered K2 primitives of one slab sheet (lines + arcs), region frame from the sheet "
                     "register",
            "grid": "axis-aligned to the sheet frame; run at 100 / 50 / 25 / 10 mm and at two origins (0, half a cell)",
            "stroke": "Bresenham + arc sampling at <= cell/2 chord error; stroke width = 1 cell (recorded)",
            "classes": RASTER_REPORT["classes"] + ["OUTSIDE"],
            "outside": "4-connected flood fill from the frame border",
            "area": "cells x cell^2 per class; EDGE_LINE_CELLS reported separately, never silently allocated",
            "outputs": "per class: area, perimeter, connected components, per resolution and origin",
            "authority": "ORACLE_ONLY - compared with Urban vector areas; never a production quantity"},
        "convergence_tests": ["test_raster_area_converges_25_to_10mm (< 0.5 % per class)",
                              "test_component_count_stable_from_50mm",
                              "test_origin_shift_within_edge_band (perimeter x cell / 2)",
                              "test_flood_fill_leak_through_one_cell_gap_detected",
                              "test_thin_void_below_cell_size_reported_unresolved",
                              "test_edge_line_cells_reported_not_allocated"],
        "risks": ["edge cells: about +/- perimeter x cell/2 per boundary (1.7 m2 on 70 m at 50 mm)",
                  "gaps under one cell close; thin voids vanish", "arc quantisation",
                  "single-pixel leaks flood rooms", "text / hatch strokes become walls unless layer-filtered",
                  "grid-origin dependence"]}


def rebar_record():
    return {"report_net_rebar_t": R("NET_REBAR_t"), "label": "KNOWN_INCOMPLETE_NET_DRAWING_REBAR",
            "unresolved_items": [{"item": x, "evidence": "REPORT_EXPLICIT", "report_file_check": PENDING}
                                 for x in UNRESOLVED_REBAR],
            "unresolved_note": UNRESOLVED_REBAR_NOTE,
            "comparison_rule": "never compared with Urban ACCURATE_BOQ_REBAR as if both were complete; a comparison "
                               "is only per component that both sides hold as resolved"}


def dumps(o):
    return json.dumps(o, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def main():
    Q, W, G, L, opn = J(CR / "QUANTITY_SCENARIOS.json"), J(CR / "WALL_FACE_PAIR_EXTRACT.json"), J(V3G), J(S1L), J(OPN)
    dsha = {k: v for k, v in W["source"].items()}
    V = {"CR": stamp(CR / "QUANTITY_SCENARIOS.json", "COVERAGE_RECOVERY (CR.3)", dsha),
         "CR_WALLS": stamp(CR / "WALL_FACE_PAIR_EXTRACT.json", "COVERAGE_RECOVERY (CR.3)", dsha),
         "CR_DASH": stamp(CR / "QUANTITY_COVERAGE_DASHBOARD.json", "COVERAGE_RECOVERY (CR.3)", dsha),
         "V3B": stamp(V3B, "V3b", {"ST7757.dxf": dsha["ST7757.dxf"]}),
         "V3G": stamp(V3G, "V3", {"ST7757.dxf": dsha["ST7757.dxf"]}),
         "S1L": stamp(S1L, "S1", {"ST7757.dxf": dsha["ST7757.dxf"], "P7757.dxf": dsha["P7757.dxf"]}),
         "OPN": stamp(OPN, "R5 (arch truth 05)", {"P7757.dxf": dsha["P7757.dxf"]})}
    gb, sl, col = ground_beams(Q, G, V), slabs(Q), columns(Q, L)
    ftg, bm, pl, wp = footings(), beams(), plaster(Q, L), wall_pairing(W)
    agr = agreement(col, sl, gb)
    import gap_register as GR  # noqa: E402  (sibling module: the trade-by-trade register text)
    files = {
        "process_log/EVIDENCE_INVENTORY.json": {
            "classes": ["REPORT_EXPLICIT", "URBAN_FROZEN", "ARITHMETIC_INFERENCE", "NOT_HELD"],
            "report_file": {"name": REPORT_NAME, "status": "NOT YET IN THIS ENVIRONMENT - REPORT_EXPLICIT items "
                                                           "are imported from the owner's quotations; "
                                                           "scripts/verify_report_quotes.py checks them when the file "
                                                           "is placed in process_log/"},
            "REPORT_EXPLICIT": {"values": {k: {"value": v, "quoted_in": s} for k, (v, s) in sorted(REPORT.items())},
                                "assumptions": ASSUMPTIONS, "beam_rules": BEAM_RULES, "raster": RASTER_REPORT,
                                "unresolved_rebar": UNRESOLVED_REBAR},
            "NOT_HELD": ["chronological MCP session / tool-call transcript", "MCP tool names and arguments per step",
                         "active AutoCAD document per step", "raw LISP history", "local scripts",
                         "raw entity dumps", "raw wall pairs", "raw raster cells", "raw beam allocations",
                         "per-object handle lists", "failed attempts / retries"],
            "AWAITING_REPORT_FILE": ["raster output class areas", "full unresolved-rebar list (quoted with 'etc.')",
                                     "footing occurrence table", "stair breakdown (A9 values)",
                                     "plaster / wall-face composition", "column occurrence lists per floor"],
            "urban_versions": V},
        "intermediate_geometry/URBAN_CROSSCHECKS.json": {"versions": V, "ground_beams": gb, "slabs": sl,
                                                         "columns": col, "footings": ftg, "beams": bm,
                                                         "plaster": pl},
        "CHRISTIANNP_WALL_PAIRING_DIAGNOSTIC.json": dict(wp, urban_version=V["CR_WALLS"]),
        "CHRISTIANNP_VS_URBAN_GAP_REGISTER.json": GR.register(R, V, gb, sl, col, ftg, bm, pl, wp, agr),
        "CHRISTIANNP_ASSUMPTION_FORENSICS.json": assumptions(sl, col, opn),
        "CHRISTIANNP_BEAM_RULES_R1_R5.json": beam_rules(),
        "CHRISTIANNP_RASTER_METHOD_SPEC.json": raster_spec(),
        "CHRISTIANNP_DONOR_AGREEMENT.json": agr,
        "CHRISTIANNP_UNRESOLVED_REBAR.json": rebar_record(),
    }
    for name, obj in files.items():
        (PKG / name).write_text(dumps(obj), encoding="utf-8")
    return files


if __name__ == "__main__":
    f = main()
    x = f["intermediate_geometry/URBAN_CROSSCHECKS.json"]
    print("GB", x["ground_beams"]["ARITHMETIC_INFERENCE"], x["ground_beams"]["segmentation"]["urban_paired_bands"])
    print("COL", json.dumps({k: v["implied_minus_urban_section_m2"] for k, v in x["columns"]["floors"].items()}))
    print("PL", x["plaster"]["ARITHMETIC_INFERENCE"]["max_two_faces_at_A10_GF_height_m2"])
    for r in f["CHRISTIANNP_ASSUMPTION_FORENSICS.json"]["rows"]:
        print(r["id"], r["nature"], r["urban_review"], r["production"])
