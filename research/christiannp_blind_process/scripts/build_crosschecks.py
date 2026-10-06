"""christiannp blind-run forensic handoff - Urban-side cross-checks (process diagnostic only).

The sealed christiannp-autocad blind run was executed outside this environment. Its tool-call log, AutoLISP, local
scripts, raw extractions and per-object lists are NOT held here (see ../process_log/EVIDENCE_INVENTORY.json). What this
script can do honestly is:

  1. record every christiannp figure the owner relayed, with where it was relayed (RELAYED);
  2. derive what those figures arithmetically imply (INFERRED - never a donor record);
  3. set them against Urban's frozen registers (URBAN_FROZEN) - population, geometry and section by object.

It changes nothing: no sealed donor result, no Urban production code, no frozen Urban register. It reads
  research/coverage_recovery_round/QUANTITY_SCENARIOS.json, WALL_FACE_PAIR_EXTRACT.json
  tests/alsenan/registers_v3b/BOQ_LINES_V3B.json
and writes the JSON deliverables of research/christiannp_blind_process/.

    python research/christiannp_blind_process/scripts/build_crosschecks.py
"""

from __future__ import annotations

import hashlib
import itertools
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
ROOT = PKG.parents[1]
sys.path.insert(0, str(ROOT))

from engine.source import wall_band_reconciliation as WB  # noqa: E402  (read-only use of the generic classifier)

CR = ROOT / "research" / "coverage_recovery_round"
V3B = ROOT / "tests" / "alsenan" / "registers_v3b" / "BOQ_LINES_V3B.json"

# ---- christiannp figures as RELAYED by the owner (no donor file is held) ------------------------------------------
S31 = "OWNER_BRIEF_S3.1_SECTION_16"            # 'CURRENT INDEPENDENT MCP REFERENCES' (post-freeze only)
CRB = "OWNER_BRIEF_COVERAGE_RECOVERY_SECTION_5_6"
FHB = "OWNER_BRIEF_CHRISTIANNP_FORENSIC_HANDOFF"
RELAYED = {
    "BUA_m2": (598.708, S31), "NET_SLAB_GF_m2": (290.555, S31), "NET_SLAB_1F_m2": (179.325, S31),
    "NET_SLAB_2F_m2": (55.275, S31), "NET_SLAB_TOTAL_m2": (525.155, CRB), "TOTAL_RC_m3": (333.173, S31),
    "FOOTINGS_m3": (65.669, S31), "STRAPS_m3": (6.053, S31), "GROUND_BEAMS_m3": (36.006, S31),
    "GROUND_BEAM_LENGTH_m": (200.036, FHB), "GROUND_BEAM_STRIPS": (42, FHB), "GROUND_BEAM_DEPTH_A5_m": (0.60, FHB),
    "GROUND_SLAB_m3": (32.404, S31), "GROUND_SLAB_AREA_m2": (324.038, FHB), "GROUND_SLAB_T_m": (0.10, FHB),
    "COL_FOU_m3": (6.150, S31), "COL_GF_m3": (26.235, S31), "COL_1F_m3": (8.888, S31), "COL_2F_m3": (3.377, S31),
    "BEAMS_GF_m3": (25.206, S31), "BEAMS_1F_m3": (18.562, S31), "BEAMS_2F_m3": (2.823, S31),
    "SLABS_GF_m3": (58.111, S31), "SLABS_1F_m3": (28.692, S31), "SLABS_2F_m3": (9.950, S31),
    "STAIRS_m3": (5.048, S31), "NET_REBAR_t_KNOWN_INCOMPLETE": (22.916, S31), "BLOCK_150_m": (79.971, CRB),
    "BLOCK_200_m": (183.497, CRB), "WALL_FACES_GROSS_m2": (2364.7, CRB), "RASTER_CELL_mm": (50, FHB),
}
RELAYED_TEXT = {
    "RASTER_METHOD": ("50 mm raster; layer-1 lines + arcs; exterior flood fill", FHB),
    "BEAM_RULES": ("rules R1-R5 exist in the report; the rule texts are not held", FHB),
    "A1": ("GF slab thickness 0.20", FHB), "A5": ("ground-beam depth 0.60", FHB),
    "A7": ("ground slab area = GF gross outline", FHB), "A8": ("CN columns continue FOU + GR", FHB),
    "WELL": ("direct AutoCAD/LISP entity extraction; raw LINE/ARC/POLYLINE reading; schedule/member extraction; "
             "independent area calculation; wall-face pairing; kept LOW-confidence measurable quantities", CRB),
    "WEAK": ("manual engineering allocation; not fully automatic; assumed wall/finish heights; windows and room "
             "areas unresolved; structural assumptions in concrete", CRB),
    "MISSING_REBAR": ("CB support/MID bars, top hangers, slab top bars, slab diagonal bars, unlabelled slab "
                      "directions, ground-beam steel, stair steel, BOXED footing bars, CN steel, laps, starters, "
                      "hooks", CRB),
}


def R(k):
    return RELAYED[k][0]


def J(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def r3(x):
    return None if x is None else round(x, 3)


# ---- 1. ground beams ---------------------------------------------------------------------------------------------
def ground_beams(Q):
    gb = Q["ground_beams"]
    groups = defaultdict(lambda: {"spans": 0, "length_m": 0.0, "urban_m3": 0.0})
    for s in gb["spans"]:
        g = groups[(s["kind"], s["B_m"], s["depth_m"], s["depth_level"])]
        g["spans"] += 1
        g["length_m"] += s["length_m"]
        g["urban_m3"] += s["part"]["best"]
    rows = []
    for (kind, b, d, lvl), g in sorted(groups.items()):
        rows.append({"kind": kind, "B_m": b, "urban_depth_m": d, "urban_depth_level": lvl, "spans": g["spans"],
                     "length_m": r3(g["length_m"]), "urban_best_m3": r3(g["urban_m3"]),
                     "at_donor_section_0.30x0.60_m3": r3(g["length_m"] * 0.30 * R("GROUND_BEAM_DEPTH_A5_m")),
                     "donor_minus_urban_m3": r3(g["length_m"] * 0.30 * R("GROUND_BEAM_DEPTH_A5_m") - g["urban_m3"])})
    L_u = gb["length_m"]
    L_d = R("GROUND_BEAM_LENGTH_m")
    return {
        "relayed": {"volume_m3": R("GROUND_BEAMS_m3"), "length_m": L_d, "strips": R("GROUND_BEAM_STRIPS"),
                    "depth_m_A5": R("GROUND_BEAM_DEPTH_A5_m")},
        "inferred_section_m2": r3(R("GROUND_BEAMS_m3") / L_d),
        "inferred_reproduction": {"formula": "200.036 m x 0.30 m x 0.60 m", "value_m3": round(L_d * 0.30 * 0.60, 4),
                                  "matches_relayed": abs(L_d * 0.30 * 0.60 - R("GROUND_BEAMS_m3")) < 0.001,
                                  "reading": "one uniform 0.30 x 0.60 section over every strip; width 0.30 is the "
                                             "drawn band width, depth 0.60 is assumption A5"},
        "urban_population": {"spans": len(gb["spans"]), "length_m": L_u, "conservation_ok": gb["conservation"]["ok"],
                             "boundary_beam_line": gb["boundary_beam_line"]},
        "length_difference_m": r3(L_d - L_u),
        "length_difference_pct": round(100 * (L_d - L_u) / L_u, 2),
        "by_section_class": rows,
        "finding": "POPULATION_EQUIVALENT: the donor found no ground-beam length Urban lacks (+%.3f m, %.2f%%). The "
                   "volume gap is section, not population: donor applies 0.60 m to all strips; Urban's p.13 details "
                   "give 0.30/0.40/0.60 m on interior spans and the exterior depth is unprinted ('FOLLOW ARCH.')."
                   % (L_d - L_u, 100 * (L_d - L_u) / L_u),
    }


# ---- 2. slabs: thickness, net area, opening hypotheses -----------------------------------------------------------
def slabs(Q):
    sheets = Q["slabs"]["sheets"]
    out = {}
    own_gross = {"GF": (R("GROUND_SLAB_AREA_m2"), "donor ground-slab area = donor GF gross outline (A7)")}
    for fl in ("GF", "1F", "2F"):
        s = sheets[fl]
        net_d, vol_d = R(f"NET_SLAB_{fl}_m2"), R(f"SLABS_{fl}_m3")
        gross_d, gross_basis = own_gross.get(fl, (s["gross_m2"], "Urban gross (donor gross for this floor not relayed)"))
        ded_d = gross_d - net_d
        ops = [(o["opening_id"], o["area_m2"], o["role"], o["state"]) for o in s["openings"]]
        cands = []
        for k in range(0, len(ops) + 1):
            for combo in itertools.combinations(ops, k):
                a = sum(c[1] for c in combo)
                cands.append({"deducted": [c[0] for c in combo], "roles": sorted({c[2] for c in combo}),
                              "sum_m2": r3(a), "residual_m2": r3(ded_d - a)})
        cands.sort(key=lambda c: abs(c["residual_m2"]))
        top = cands[:4]
        unique = len(top) < 2 or (abs(top[1]["residual_m2"]) - abs(top[0]["residual_m2"]) > 1.0
                                  and abs(top[0]["residual_m2"]) < 1.0)
        out[fl] = {"relayed_net_m2": net_d, "relayed_volume_m3": vol_d,
                   "inferred_thickness_m": round(vol_d / net_d, 4),
                   "urban_gross_m2": s["gross_m2"], "urban_openings_m2": r3(sum(o[1] for o in ops)),
                   "urban_net_m2": r3(s["gross_m2"] - sum(o[1] for o in ops)),
                   "donor_gross_used_m2": gross_d, "donor_gross_basis": gross_basis,
                   "inferred_donor_deductions_m2": r3(ded_d),
                   "urban_openings": [{"opening_id": o[0], "area_m2": o[1], "role": o[2], "state": o[3]} for o in ops],
                   "deduction_hypotheses_ranked": top,
                   "hypothesis_status": "UNIQUE" if unique else "NON_UNIQUE (raster edge allocation of +/- 1-2 m2 "
                                                                 "cannot be separated without the donor cell map)"}
    t = {fl: out[fl]["inferred_thickness_m"] for fl in out}
    return {"floors": out, "inferred_thicknesses_m": t,
            "A1_effect_m3": r3(R("SLABS_GF_m3") - R("NET_SLAB_GF_m2") * 0.16),
            "pattern": "best-ranked hypotheses on GF and 1F both deduct the VOID openings and keep the STAIR well "
                       "(10.725 m2 each floor) in the slab; residuals are within raster edge tolerance. HYPOTHESIS "
                       "ONLY - confirm against the donor cell map."}


# ---- 3. columns ---------------------------------------------------------------------------------------------------
def columns(Q):
    A, G, N, n = defaultdict(float), defaultdict(float), defaultdict(float), Counter()
    for x in Q["columns"]["records"]:
        A[x["floor"]] += x["A_m2"]
        G[x["floor"]] += x["gross_m3"]
        N[x["floor"]] += x["net_of_slab_m3"] or 0.0
        n[x["floor"]] += 1
    keymap = {"FOUNDATION": "COL_FOU_m3", "GF": "COL_GF_m3", "1F": "COL_1F_m3", "2F": "COL_2F_m3"}
    rows = {}
    for fl, k in keymap.items():
        rows[fl] = {"urban_occurrences": n[fl], "urban_section_sum_m2": r3(A[fl]), "urban_gross_m3": r3(G[fl]),
                    "urban_net_of_slab_m3": r3(N[fl]), "urban_mean_height_m": r3(G[fl] / A[fl]),
                    "relayed_donor_m3": R(k),
                    "inferred_donor_height_if_same_population_m": r3(R(k) / A[fl]),
                    "donor_minus_urban_net_m3": r3(R(k) - N[fl])}
    fou_gf_u = N["FOUNDATION"] + N["GF"]
    fou_gf_d = R("COL_FOU_m3") + R("COL_GF_m3")
    return {"floors": rows, "FOU_plus_GF": {"urban_m3": r3(fou_gf_u), "donor_m3": r3(fou_gf_d),
                                            "difference_m3": r3(fou_gf_d - fou_gf_u)},
            "readings": [
                "GF donor 26.235 m3 over Urban's GF section sum 4.50 m2 implies 5.83 m - above the 4.50 m storey, so "
                "the donor GF row carries column volume Urban books under FOUNDATION (FOU+GF agree within 0.23 m3).",
                "1F and 2F donor values imply ~3.6 m on Urban's sections (storey 4.20 m): consistent with columns "
                "measured clear of beam depth, i.e. the joint volume is not in the donor column rows.",
                "FOU 6.150 / GF 26.235 / 1F 8.888 are identical in both blind runs (U-C4N and christiannp); only 2F "
                "differs (3.797 vs 3.377). Identity across two 'independent' runs needs explaining before either is "
                "used as corroboration.",
            ]}


# ---- 4. footings: occurrence by occurrence -----------------------------------------------------------------------
def footings():
    lines = {r["code"]: r for r in J(V3B)["lines"]}
    ftg, ff10 = lines["C-FTG"], lines["C-FTG-FF10"]
    occ = [{"seq": i + 1, "type": d["ref"], "formula": d["formula"], "urban_m3": d["qty"], "status": d["status"],
            "donor_m3": "NOT_HELD"} for i, d in enumerate(ftg["details"])]
    by_type = Counter(o["type"] for o in occ if o["urban_m3"] is not None)
    vol = {o["type"]: o["urban_m3"] for o in occ if o["urban_m3"] is not None}
    urban = ftg["qty"]
    diff = R("FOOTINGS_m3") - urban
    options = []
    ff = {"F/F10 excluded (Urban technical)": 0.0, "F/F10 as 2 x F": 0.432, "F/F10 as 1 x F10": 1.960}
    for fname, fv in ff.items():
        for k in (0, 1, 2):
            for combo in itertools.combinations_with_replacement(sorted(vol), k):
                add = sum(vol[t] for t in combo)
                options.append({"f_f10": fname, "extra_occurrences": list(combo), "added_m3": r3(fv + add),
                                "residual_m3": r3(diff - fv - add)})
    options.sort(key=lambda o: abs(o["residual_m3"]))
    return {"urban_released_m3": urban, "urban_occurrences": len([o for o in occ if o["urban_m3"] is not None]),
            "urban_blocked_outlines": [o["type"] for o in occ if o["urban_m3"] is None],
            "urban_type_counts": dict(sorted(by_type.items())), "urban_occurrences_table": occ,
            "f_f10_scenarios": ff10["formula"], "relayed_donor_m3": R("FOOTINGS_m3"), "difference_m3": r3(diff),
            "candidate_decompositions_ranked": options[:8],
            "status": "NON_UNIQUE - the donor occurrence list is not held, so the 1.323 m3 cannot be assigned "
                      "occurrence by occurrence; the ranked decompositions are arithmetic candidates only."}


# ---- 5. beams / 6. plaster --------------------------------------------------------------------------------------
def beams():
    lines = {r["code"]: r for r in J(V3B)["lines"]}
    rows = {}
    for fl, tech, res, extra in (("GF", "C-BEAM-GF", "C-BEAM-GF-RES", ()), ("1F", "C-BEAM-1F", "C-BEAM-1F-RES",
                                 ("C-DOME-RING-12EB", "C-DOME-RING-2F33")), ("2F", "C-BEAM-2F", None,
                                                                             ("C-DOME-RING-1300",))):
        t = lines[tech]["qty"] or 0.0
        rq = (lines[res]["release"]["commercial"].get("qty") or 0.0) if res else 0.0
        ex = sum(lines[e]["release"]["commercial"].get("qty") or 0.0 for e in extra)
        d = R(f"BEAMS_{fl}_m3")
        rows[fl] = {"urban_technical_m3": r3(t), "urban_residue_commercial_m3": r3(rq),
                    "urban_dome_ring_commercial_m3": r3(ex), "relayed_donor_m3": d,
                    "donor_minus_urban_technical_m3": r3(d - t),
                    "donor_minus_urban_technical_plus_residue_m3": r3(d - t - rq)}
    return {"floors": rows, "note": "dome ring beams are listed separately because their inclusion in the donor "
                                    "beam rows is unknown; donor per-strip lists are not held"}


def plaster(Q):
    L = R("BLOCK_150_m") + R("BLOCK_200_m")
    pf = Q["walls"]["physical_faces"]
    return {"relayed_donor_gross_faces_m2": R("WALL_FACES_GROSS_m2"), "donor_wall_length_m": r3(L),
            "inferred_height_if_two_faces_no_deductions_m": r3(R("WALL_FACES_GROSS_m2") / (2 * L)),
            "reading": "2364.7 / (2 x 263.468 m) = 4.488 m: equal to the GF storey height applied to every wall on "
                       "every floor, both faces, no opening deduction - INFERRED, not a donor record",
            "urban_physical_faces": {"basis": pf["basis"], "faces": pf["faces"],
                                     "verified_m2": pf["physical_area"]["VERIFIED_QUANTITY"],
                                     "best_m2": pf["physical_area"]["BEST_PROVISIONAL_QUANTITY"],
                                     "by_floor_role_m2": pf["by_floor_role"]}}


# ---- 7. wall pairing diagnostic (Urban Method B reconstruction; donor pairs not preserved) -----------------------
def wall_pairing(W):
    rows, tot = [], defaultdict(lambda: defaultdict(float))
    for fl in sorted(W["floors"]):
        f = W["floors"][fl]
        for w, ivs in sorted(f["pairs"].items()):
            ivs2 = [dict(iv, length=iv["length"]) for iv in ivs]
            cl = WB.classify(ivs2, column_boxes=[tuple(c) for c in f["column_boxes"]],
                             opening_boxes=[tuple(c) for c in f["opening_boxes"]])
            for iv in cl:
                parts = iv["parts"]
                L = iv["length"]
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
        "christiannp_pairs": "NOT_PRESERVED_IN_THIS_ENVIRONMENT - the sealed run's pair list (handles, widths, "
                             "overlaps, acceptance reasons) was never delivered to Urban; no row below is a donor row",
        "christiannp_parameters": {k: "NOT_HELD" for k in (
            "source_layers", "line_types", "parallel_tolerance", "width_buckets", "overlap_threshold",
            "nearest_pair_rule", "de_duplication", "intersections", "t_junctions", "columns", "openings",
            "short_segments", "curved_walls", "finish_lines", "false_positive_prevention")},
        "urban_method_b": {"rule": W["rule"], "wall_layer": W["layer"], "column_layer": W["column_layer"],
                           "opening_layers": W["opening_layers"], "source_dxf_sha256": W["source"],
                           "classifier": "engine.source.wall_band_reconciliation.classify (unchanged)"},
        "urban_method_b_totals_m": totals,
        "urban_method_b_gross_m": gross,
        "relayed_donor_m": {"150": R("BLOCK_150_m"), "200": R("BLOCK_200_m")},
        "donor_minus_method_b_gross_m": {w: r3(R(f"BLOCK_{w}_m") - gross[w]) for w in ("150", "200")},
        "reading": "christiannp's 200 mm length sits within %.1f m of Urban's UNCLASSIFIED Method-B gross "
                   "(paired + openings + column overlap + duplicate faces). INFERENCE: the donor total is raw parallel "
                   "pairing before classification." % abs(R("BLOCK_200_m") - gross["200"]),
        "rows": rows,
    }


# ---- 8. gap register / 9. assumption forensics ------------------------------------------------------------------
def gap_register(Q, gb, sl, col, ftg, bm, pl, wp):
    cov = {r["trade"]: r for r in J(CR / "QUANTITY_COVERAGE_DASHBOARD.json")["rows"]}

    def u(trade):
        r = cov[trade]
        return {"official_before": r["official_before"], "verified": r["verified"], "best": r["best_provisional"],
                "low": r["low"], "high": r["high"], "release": r["release"]}

    rows = [
        dict(trade="GROUND_BEAMS", element="interior + exterior ground beams",
             urban=u("GROUND_BEAMS"), donor={"m3": R("GROUND_BEAMS_m3"), "length_m": R("GROUND_BEAM_LENGTH_m"),
                                             "strips": R("GROUND_BEAM_STRIPS")},
             same_basis="NO - same population (length within %.2f%%), different section" % gb["length_difference_pct"],
             donor_objects=f"{R('GROUND_BEAM_STRIPS')} strips, {R('GROUND_BEAM_LENGTH_m')} m",
             urban_objects=f"{gb['urban_population']['spans']} spans, {gb['urban_population']['length_m']} m",
             donor_method="paired band strips x one uniform section 0.30 x 0.60", donor_assumptions=["A5"],
             urban_blocker="exterior depth 'FOLLOW ARCH.' unprinted -> technical BLOCKED (now a BOUNDED scenario)",
             root_cause="publication (technical-only) + unsourced exterior depth; NOT extraction",
             donor_likely_correct="NO for section (0.60 contradicts the p.13 details on 27 of 31 interior spans)",
             urban_likely_correct="YES on population and interior sections; exterior depth needs the consultant",
             classification="B", generic_lesson="a measured population must survive a missing depth",
             production_change="none new (ground_beam_recovery already does this); publish scenario layers",
             regression_test="test: uniform-depth fill never overrides a DETAIL depth on the same span",
             must_not_hardcode=["0.60 m depth", "0.30 m width", "200.036 m", "42 strips"]),
        dict(trade="GROUND_SLAB", element="slab on grade", urban=u("GROUND_SLAB"),
             donor={"m3": R("GROUND_SLAB_m3"), "area_m2": R("GROUND_SLAB_AREA_m2"), "t_m": R("GROUND_SLAB_T_m")},
             same_basis="NO - donor area = GF gross slab outline (A7); Urban = founded cells between ground beams",
             donor_objects="one outline", urban_objects="23 cells (14 labelled zones + 9 recovered unlabelled)",
             donor_method="raster gross outline x T=10 cm", donor_assumptions=["A7"],
             urban_blocker="label-scoped release (fixed in the coverage round: 9 cells, 101.7 m2 as CANDIDATE)",
             root_cause="area authority: donor uses the suspended GF slab outline, which includes ground-beam and "
                        "column footprints and openings; Urban measures cells net of beams",
             donor_likely_correct="NO as verified scope; YES that unlabelled cells exist",
             urban_likely_correct="cells are the physical slab; scope of T=10 note still a consultant question",
             classification="B", generic_lesson="thickness authority and area authority are separate facts",
             production_change="keep ground_slab_recovery; never substitute a floor outline for slab-on-grade",
             regression_test="test: ground-slab area excludes ground-beam footprint and column footprints",
             must_not_hardcode=["324.038 m2", "0.10 m for all panels"]),
        dict(trade="COLUMN_CONCRETE", element="columns + joints per storey", urban=u("COLUMNS_AND_JOINTS"),
             donor={k: R(k) for k in ("COL_FOU_m3", "COL_GF_m3", "COL_1F_m3", "COL_2F_m3")},
             same_basis="NO - storey split and joint convention differ (FOU+GF agree within %.3f m3)"
                        % abs(col["FOU_plus_GF"]["difference_m3"]),
             donor_objects="NOT_HELD", urban_objects="95 occurrences (S1 chains)",
             donor_method="outline + nearest label per floor; continuation logic not held", donor_assumptions=["A8"],
             urban_blocker="none after the coverage round (95/95 quantified)",
             root_cause="convention (FOU/GF split, joints) + CN continuation assumption",
             donor_likely_correct="UNKNOWN per floor; A8 conflicts with Urban/human review",
             urban_likely_correct="YES on census; founding level still a range", classification="C",
             generic_lesson="column concrete never waits for rebar or clear height",
             production_change="none", regression_test="existing: CN propagation does not happen",
             must_not_hardcode=["per-floor donor volumes"]),
        dict(trade="BEAMS", element="downstands per floor", urban=u("BEAMS"),
             donor={f: R(f"BEAMS_{f}_m3") for f in ("GF", "1F", "2F")},
             same_basis="PARTLY - downstand convention stated as Urban's; allocation of residue and dome rings unknown",
             donor_objects="NOT_HELD (rules R1-R5)", urban_objects="tagged occurrences + 16 recovered residues + 8 "
                                                                   "unquantified tags",
             donor_method="parallel-face strips + label matching + schedule-span capping (R1-R5, texts not held)",
             donor_assumptions=["NOT_HELD"], urban_blocker="8 tags without a measurable band; CB8 span count",
             root_cause="occurrence binding + residue release", donor_likely_correct="UNKNOWN",
             urban_likely_correct="lower bound is safe; best 45.537 m3", classification="E",
             generic_lesson="unbound tags become candidate occurrences, never drops",
             production_change="beam binding ladder (already P1)", regression_test="tag without band stays "
                                                                                   "UNQUANTIFIED with identity",
             must_not_hardcode=["per-floor donor volumes"]),
        dict(trade="SLAB_NET_AREA", element="net slab plate per floor", urban={"net_m2": {
             fl: sl["floors"][fl]["urban_net_m2"] for fl in sl["floors"]}},
             donor={fl: R(f"NET_SLAB_{fl}_m2") for fl in ("GF", "1F", "2F")},
             same_basis="MOSTLY - both gross outline minus openings; donor via 50 mm raster",
             donor_objects="raster regions (map not held)", urban_objects="vector outline + per-id openings",
             donor_method="raster + exterior flood fill", donor_assumptions=["opening classification - NOT_HELD"],
             urban_blocker="none (GF conflict void carried as SOURCE_CONFLICT)",
             root_cause="opening classification: best hypothesis = donor keeps stair wells in the slab",
             donor_likely_correct="NO if stair wells are open (Urban shows stair line work inside)",
             urban_likely_correct="YES for VOID/STAIR deductions; GF T16 void open/closed is a consultant question",
             classification="C", generic_lesson="every deduction carries an opening id and a role",
             production_change="none", regression_test="existing: every deduction has an opening id",
             must_not_hardcode=["290.555", "179.325", "55.275"]),
        dict(trade="SLAB_OPENINGS", element="voids / stair wells / conflict voids",
             urban={fl: sl["floors"][fl]["urban_openings_m2"] for fl in sl["floors"]},
             donor={fl: sl["floors"][fl]["inferred_donor_deductions_m2"] for fl in sl["floors"]},
             same_basis="NO (inferred)", donor_objects="NOT_HELD", urban_objects="8 openings with ids",
             donor_method="raster classes (opening / unresolved-enclosed) - parameters not held",
             donor_assumptions=["NOT_HELD"], urban_blocker="GF void carries a T16 tag (conflict)",
             root_cause="see SLAB_NET_AREA hypotheses", donor_likely_correct="UNKNOWN",
             urban_likely_correct="UNKNOWN for the GF conflict void", classification="E",
             generic_lesson="a tagged face inside an opening is a conflict, not a silent deduction",
             production_change="none", regression_test="existing OPENING_CONFLICT test",
             must_not_hardcode=["opening areas"]),
        dict(trade="WALLS_150", element="150 mm blockwork length", urban=u("BLOCKWORK_150_LENGTH"),
             donor={"m": R("BLOCK_150_m")}, same_basis="CLOSE", donor_objects="NOT_HELD",
             urban_objects="established bands", donor_method="parallel-face pairing",
             donor_assumptions=["NOT_HELD"], urban_blocker="none material",
             root_cause="donor gross pairing vs Urban classified bands (see wall diagnostic)",
             donor_likely_correct="close", urban_likely_correct="close", classification="C",
             generic_lesson="positive control for any pairing route", production_change="none",
             regression_test="150 mm Method B vs Method A within the explained classes",
             must_not_hardcode=["79.971 m"]),
        dict(trade="WALLS_200", element="200 mm blockwork length", urban=u("BLOCKWORK_200_LENGTH"),
             donor={"m": R("BLOCK_200_m")}, same_basis="NO - donor = raw pairs before classification (inferred)",
             donor_objects="NOT_HELD", urban_objects="established + 12 ambiguous bands; Method B pairs with handles",
             donor_method="parallel-face pairing", donor_assumptions=["NOT_HELD"],
             urban_blocker="12 ambiguous bands were never measured (now CANDIDATE)",
             root_cause="Urban: ambiguous bands + column-overlap convention; donor: openings, column faces and "
                        "duplicate faces counted as wall",
             donor_likely_correct="NO - includes non-wall length", urban_likely_correct="best 134.076 m is "
                                                                                          "physical; exact split pending",
             classification="D", generic_lesson="pair, then classify every metre before calling it wall",
             production_change="wall_band_reconciliation as a required cross-route",
             regression_test="pairs across a door opening classify as OPENING_SPAN",
             must_not_hardcode=["183.497 m"]),
        dict(trade="PLASTER", element="wall face area", urban={"physical_faces_verified_m2": pl[
             "urban_physical_faces"]["verified_m2"], "physical_faces_best_m2": pl["urban_physical_faces"]["best_m2"]},
             donor={"gross_faces_m2": R("WALL_FACES_GROSS_m2")},
             same_basis="NO - donor gross (both faces, ~4.49 m inferred height, no deductions)",
             donor_objects="NOT_HELD", urban_objects="266 faces with handles", donor_method="length x 2 x height",
             donor_assumptions=["wall heights assumed (relayed weakness)"],
             urban_blocker="finish certification (fixed: physical faces now measured)",
             root_cause="Urban released only certified room faces; donor used gross length x assumed height",
             donor_likely_correct="NO as a finish quantity", urban_likely_correct="physical faces yes; finishes pending",
             classification="B", generic_lesson="PHYSICAL_WALL_FACE_AREA before finish semantics",
             production_change="physical_wall_faces feeding plaster/paint (P1)",
             regression_test="face area = length x (interval - member) - openings, per face",
             must_not_hardcode=["2364.7 m2", "4.49 m"]),
        dict(trade="FOOTINGS", element="isolated / combined footings", urban={"released_m3": ftg["urban_released_m3"],
             "occurrences": ftg["urban_occurrences"], "blocked": ftg["urban_blocked_outlines"]},
             donor={"m3": R("FOOTINGS_m3")}, same_basis="YES (L x W x H per schedule)",
             donor_objects="NOT_HELD", urban_objects="25 occurrences + 1 F/F10 outline (2 handles) blocked",
             donor_method="closed outlines + nearest tag + schedule ATTRIB (relayed)", donor_assumptions=["NOT_HELD"],
             urban_blocker="F / F10 source conflict", root_cause="F3 count / F-F10 / FN classification (owner); "
                                                                 "decomposition NON_UNIQUE",
             donor_likely_correct="UNKNOWN", urban_likely_correct="YES for 25 released occurrences",
             classification="E", generic_lesson="outline route and tag route must agree occurrence by occurrence",
             production_change="footing dual route (P2)", regression_test="every outline has exactly one tag or a "
                                                                          "conflict record",
             must_not_hardcode=["65.669 m3"]),
        dict(trade="STAIRS", element="stair concrete", urban={"status": "see V3b stair lines"},
             donor={"m3": R("STAIRS_m3")}, same_basis="UNKNOWN", donor_objects="NOT_HELD",
             urban_objects="V3b stair register", donor_method="NOT_HELD", donor_assumptions=["NOT_HELD"],
             urban_blocker="see V3b", root_cause="not investigable without the donor stair breakdown",
             donor_likely_correct="UNKNOWN", urban_likely_correct="UNKNOWN", classification="E",
             generic_lesson="stair flights, landings and waists need separate records",
             production_change="none", regression_test="none until the donor breakdown is held",
             must_not_hardcode=["5.048 m3"]),
    ]
    return {"classification_key": {"A": "MORE COMPLETE AND SOURCE-SUPPORTED",
                                   "B": "MORE COMPLETE BUT ASSUMPTION-DEPENDENT", "C": "DIFFERENT MEASUREMENT BASIS",
                                   "D": "DONOR ERROR", "E": "UNKNOWN"},
            "rule": "donor values are RELAYED by the owner; every donor per-object field is NOT_HELD; Urban values "
                    "from the frozen coverage-recovery round", "rows": rows}


def assumptions(gb, sl, col):
    known = {
        "A1": dict(assumption="GF slab thickness 0.20 m", categories=["SLABS"], physical="GF slab volume",
                   semantic="slab thickness tag scope", why="NOT_HELD",
                   search="NOT_HELD", alternatives="0.16 (project default unless noted - later Urban reading)",
                   sensitivity_m3=sl["A1_effect_m3"],
                   later_review="INCORRECT as a default: Urban source reading = 0.16 unless locally noted",
                   generic_fallback="NO", adopt="NO",
                   why_not="a general note outranks an assumed value; the evidence ladder takes PROJECT_GENERAL_RULE"),
        "A5": dict(assumption="ground-beam depth 0.60 m", categories=["GROUND_BEAMS", "GB rebar", "waterproofing"],
                   physical="all %d strips" % R("GROUND_BEAM_STRIPS"), semantic="exterior 'FOLLOW ARCH.' depth",
                   why="exterior depth unprinted", search="NOT_HELD", alternatives="NOT_HELD",
                   sensitivity_m3=round(R("GROUND_BEAM_LENGTH_m") * 0.30 * 0.10, 3),
                   later_review="NOT ESTABLISHED: contradicts p.13 interior details on 27 of 31 interior spans; "
                                "exterior bracket from elevations 0.90-1.30 m",
                   generic_fallback="NO", adopt="NO", why_not="an assumed depth over-rides measured details; "
                                                              "Urban keeps a BOUNDED scenario instead"),
        "A7": dict(assumption="ground slab area = GF gross outline", categories=["GROUND_SLAB"],
                   physical="slab-on-grade extent", semantic="which panels are slab-on-grade", why="NOT_HELD",
                   search="NOT_HELD", alternatives="cells between ground beams (Urban)",
                   sensitivity_m3=round((R("GROUND_SLAB_AREA_m2") - 322.413) * 0.10, 3),
                   later_review="CANDIDATE physical scope, not verified: includes beam/column footprints",
                   generic_fallback="as a HIGH scenario only", adopt="NO as verified",
                   why_not="a suspended-slab outline is not slab-on-grade evidence"),
        "A8": dict(assumption="CN columns continue FOU + GR", categories=["COLUMN_CONCRETE", "column rebar"],
                   physical="CN occurrences", semantic="column continuation", why="NOT_HELD", search="NOT_HELD",
                   alternatives="CN per S1 chains", sensitivity_m3="NOT_DERIVABLE (CN list not held)",
                   later_review="CONFLICTS with later Urban / human review", generic_fallback="NO", adopt="NO",
                   why_not="continuation must come from each storey's own plan occurrence"),
    }
    rows = []
    for i in range(1, 16):
        k = f"A{i}"
        if k in known:
            rows.append(dict(id=k, text_status="RELAYED", **known[k]))
        else:
            rows.append({"id": k, "text_status": "NOT_HELD", "assumption": None,
                         "note": "the A1-A15 list exists in the sealed report; only A1, A5, A7 and A8 were relayed"})
    return {"rows": rows}


def dumps(o):
    return json.dumps(o, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def main():
    Q = J(CR / "QUANTITY_SCENARIOS.json")
    W = J(CR / "WALL_FACE_PAIR_EXTRACT.json")
    gb, sl, col, ftg, bm, pl = ground_beams(Q), slabs(Q), columns(Q), footings(), beams(), plaster(Q)
    wp = wall_pairing(W)
    inputs = {str(p.relative_to(ROOT)): sha(p) for p in (CR / "QUANTITY_SCENARIOS.json",
                                                          CR / "WALL_FACE_PAIR_EXTRACT.json",
                                                          CR / "QUANTITY_COVERAGE_DASHBOARD.json", V3B)}
    files = {
        "process_log/EVIDENCE_INVENTORY.json": {
            "held": {"relayed_values": {k: {"value": v, "source": s} for k, (v, s) in sorted(RELAYED.items())},
                     "relayed_text": {k: {"text": v, "source": s} for k, (v, s) in sorted(RELAYED_TEXT.items())}},
            "not_held": ["tool-call log", "MCP tool names and arguments", "active AutoCAD document per step",
                         "AutoLISP expressions / scripts", "PowerShell / local scripts", "raw extraction dumps",
                         "intermediate geometry (strips, raster cells, pairs)", "assumption texts A2-A4, A6, A9-A15",
                         "beam rule texts R1-R5", "per-object handle lists", "failed attempts / retries"],
            "searched": ["this repository (all tracked files)", "the session upload folder (file names only; "
                         "credential and do-not-open files were not opened)", "this session's own transcript",
                         "the account's cloud sessions (list only)"],
            "repository_record": "research/external_engine_lab/DONORS.lock: christiannp/autocad = "
                                 "UNRESOLVED_EXTERNAL_REPOSITORY"},
        "intermediate_geometry/URBAN_CROSSCHECKS.json": {"inputs_sha256": inputs, "ground_beams": gb, "slabs": sl,
                                                         "columns": col, "footings": ftg, "beams": bm,
                                                         "plaster": pl},
        "CHRISTIANNP_WALL_PAIRING_DIAGNOSTIC.json": dict(wp, inputs_sha256=inputs),
        "CHRISTIANNP_VS_URBAN_GAP_REGISTER.json": gap_register(Q, gb, sl, col, ftg, bm, pl, wp),
        "CHRISTIANNP_ASSUMPTION_FORENSICS.json": assumptions(gb, sl, col),
    }
    for name, obj in files.items():
        (PKG / name).write_text(dumps(obj), encoding="utf-8")
    return files


if __name__ == "__main__":
    f = main()
    x = f["intermediate_geometry/URBAN_CROSSCHECKS.json"]
    print("GB", x["ground_beams"]["inferred_reproduction"], x["ground_beams"]["length_difference_m"])
    for r in x["ground_beams"]["by_section_class"]:
        print("  ", r)
    print("SLAB t", x["slabs"]["inferred_thicknesses_m"], "A1", x["slabs"]["A1_effect_m3"])
    for fl, s in x["slabs"]["floors"].items():
        print("  ", fl, s["inferred_donor_deductions_m2"], s["hypothesis_status"][:9], s["deduction_hypotheses_ranked"][:2])
    print("COL", json.dumps(x["columns"]["floors"]), x["columns"]["FOU_plus_GF"])
    print("FTG", x["footings"]["difference_m3"], x["footings"]["candidate_decompositions_ranked"][:4])
    print("BEAMS", json.dumps(x["beams"]["floors"]))
    print("PLASTER", x["plaster"]["inferred_height_if_two_faces_no_deductions_m"])
    w = f["CHRISTIANNP_WALL_PAIRING_DIAGNOSTIC.json"]
    print("WALLS", w["urban_method_b_gross_m"], w["donor_minus_method_b_gross_m"], w["urban_method_b_totals_m"].get("ALL|200"),
          len(w["rows"]))
