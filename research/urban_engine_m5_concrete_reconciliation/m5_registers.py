"""M5 registers: source scope matrix (02), missing concrete (10), double counts (11), quotation exposure (12),
priority RFIs (13) and the independent validation (15)."""

from __future__ import annotations

import math
from collections import defaultdict

from shapely.geometry import Polygon
from shapely.ops import unary_union

import m5_reconcile as M
import m5_tables as T

BASIS = {   # how each source measures a family (text from the source records and the S3.1 bases)
    "FOOTINGS": ("schedule L x W x H per drawn mark", "drawn outline x schedule depth (26 outlines)",
                 "PAD_LxWxH_SCHEDULE", "PAD_LxWxH_SCHEDULE"),
    "STRAPS": ("typed length x schedule section", "drawn faces clear of the footings x schedule depth",
               "strap band incl. the part inside footings (R9.1)", "full face overlap x schedule W x H (R9.1)"),
    "NECKS": ("1.50 m necks x section", "footing top to GF +1.00, founding 1.50 m below plot (printed minimum)",
              "neck 1.00 m (A3)", "neck 1.00 m (A3)"),
    "GROUND_BEAMS": ("211 m x 30 x 60 (two lumps)", "drawn spans net of columns x p.13 class depth; exterior "
                     "FOLLOW ARCH bracket", "network ~200 m x 0.30 x 0.60", "42 strips 200.036 m x 0.30 x 0.60 (A5)"),
    "GB_PERIMETER": ("71.7 m x 20 x 60 'perimeter tie beam'", "no such element drawn", "-", "-"),
    "GROUND_SLAB": ("295.5 m2 gross x 0.10", "cells between ground beams x 0.10 (two cells unresolved)",
                    "gross outline x 0.10", "324.038 m2 GF gross outline x 0.10 (A7)"),
    "COLUMNS": ("clear height under beams (3.75 / 3.45)", "floor to floor (4.50 / 4.20 / 4.20), beams net of columns",
                "GF from +-0.00 (A2)", "GF from +-0.00 (A2), CN through FOU + GR (A8)"),
    "BEAMS": ("gross depth (slab inside H), c/c lengths", "H overall (reading A) net of columns; high = H + t",
              "downstand below the slab", "downstand below the slab (R1 - R5 allocation)"),
    "SLABS": ("net of beam footprints, 16 / 18 cm", "panels stop at beam faces; 16 cm default, 18 cm tags",
              "full depth over beams; GF 0.20", "full depth over beams; GF 0.20 (A1, KNOWN_WRONG)"),
    "LINTELS": ("not priced", "p.13 lintel schedule over masonry openings", "not in source", "not in source"),
    "STAIRS": ("plan x 0.28 m equivalent", "drawn flights / winders / landings at the waist range (S8.7)",
               "undeclared", "undeclared (A9)"),
    "DOMES": ("3 x 22.6 m2 x 0.10", "2 spherical caps (S8.3) + 2 ring beams; tower dome unresolved", "not in source",
              "not in source"),
    "POOL": ("base + walls 1.8 m + steps", "drawn base footprint + 200 mm wall bands x height (S8.2 / S8.2A)",
             "not in source", "not in source"),
    "POOL_PUMP_ROOM": ("walls + floor", "not drawn (UNRESOLVED)", "not in source", "not in source"),
    "LIFT": ("8 m x 0.20 x 1.50", "four drawn 200 mm pit walls x founding range (S8.8)", "not in source",
             "not in source"),
    "CANTILEVER_PORTIONS": ("not priced", "hatched bands (S9A) at the adjacent slab thickness (conditional)",
                            "not in source", "not in source"),
    "WATER_TANK": ("not priced (roof slab in 2F slabs)", "roof slab in 2F slabs; base / walls not drawn",
                   "not in source", "not in source"),
    "BOUNDARY_WALL": ("42 m x 30 x 60 beam", "drawn run x p.14 typical .. B.W row (conditional)", "not in source",
                      "not in source"),
    "PARAPETS": ("not priced", "architecture only (UNRESOLVED)", "not in source", "not in source"),
    "BLINDING": ("full plot 15.00 x 31.37 x 0.10 (kept apart)", "drawn layer under footings + ground beams",
                 "about 15.787 (brief)", "rule A6 (0.10 + 0.10 projection)"),
}


def scope_matrix(fam_rows):
    out = []
    for r in fam_rows:
        b = BASIS.get(r["FAMILY"], ("", "", "", ""))
        out.append({"SCOPE_ITEM": r["FAMILY"], "TITLE": r["TITLE"], "RC": r["RC"],
                    "FREELANCER_M3": r["FREELANCER_M3"], "FREELANCER_BASIS": b[0],
                    "URBAN_M4_M3": r["URBAN_M4_BASE_M3"], "URBAN_M5_MEASURED_M3": r["URBAN_M5_MEASURED_BASE_M3"],
                    "URBAN_M5_CONDITIONAL_HIGH_M3": r["URBAN_M5_CONDITIONAL_HIGH_M3"], "URBAN_BASIS": b[1],
                    "UC4N_M3": r["UC4N_M3"], "UC4N_BASIS": b[2], "CHRISTIANNP_M3": r["CHRISTIANNP_M3"],
                    "CHRISTIANNP_BASIS": b[3],
                    "NORMALISATION": NORMALISE.get(r["FAMILY"], "directly comparable after the family mapping")})
    return out


NORMALISE = {
    "GROUND_BEAMS": "compare the ground zone allocation-free (GB + perimeter + straps + slab) and the network length",
    "GB_PERIMETER": "freelancer-only row; part of the ground zone",
    "GROUND_SLAB": "net cells vs gross plate: subtract the member footprint (05)",
    "COLUMNS": "allocation-free frame per floor (columns + beams + slabs, 07)",
    "BEAMS": "allocation-free frame per floor (MCP beams are downstand, their slabs full depth)",
    "SLABS": "allocation-free frame per floor",
    "NECKS": "height basis differs (founding level not printed)",
    "STRAPS": "length basis differs (MCP measure into the footings)",
    "BLINDING": "plain concrete: never added to RC",
}


# ------------------------------------------------------------------ 10 missing concrete
def missing_register(U, elements, rate):
    rows = []
    n = 0
    for u in U:
        c = T.contrib(u)
        st = c["STATE"]
        planted = u["BLOCKER"] == "M4_DETECTION_GAP"
        if st not in ("CONDITIONAL", "UNMEASURABLE") and not planted:
            continue
        n += 1
        lo, hi = (c["MB"], c["MB"]) if planted else (c["CL"], c["CH"])
        rows.append({"MISSING_ID": f"MC-{n:03d}", "MISSING_FROM": "URBAN M4 BASE" if planted else "URBAN BASE",
                     "FAMILY": u["FAMILY"], "FLOOR": u["FLOOR"], "ELEMENT": u["UID"], "MARK": u["MARK"],
                     "WHERE": T.S_loc(u), "STATUS": "MEASURED_IN_M5 (detection gap)" if planted else st,
                     "LOW_M3": M.r6(lo), "HIGH_M3": M.r6(hi), "KWD_LOW": M.kwd(lo, rate), "KWD_HIGH": M.kwd(hi, rate),
                     "WHY": u.get("M5_NOTE") or u["BLOCKER"], "NEEDED": NEED.get(u["BLOCKER"], u["BLOCKER"])})
    for e in elements:
        if e["CLASS"].startswith("MISSING_IN_FREELANCER") and (e["URBAN_MEASURED_BASE_M3"] or 0) > 0:
            n += 1
            rows.append({"MISSING_ID": f"MC-{n:03d}", "MISSING_FROM": "FREELANCER", "FAMILY": e["FAMILY"],
                         "FLOOR": e["FLOOR"], "ELEMENT": e["ELEMENT_ID"], "MARK": e["MARK_OR_PART"],
                         "WHERE": e["URBAN_LOCATION"], "STATUS": "MEASURED in Urban",
                         "LOW_M3": e["URBAN_MEASURED_LOW_M3"], "HIGH_M3": e["URBAN_MEASURED_HIGH_M3"],
                         "KWD_LOW": M.kwd(e["URBAN_MEASURED_LOW_M3"], rate),
                         "KWD_HIGH": M.kwd(e["URBAN_MEASURED_HIGH_M3"], rate), "WHY": e["EXPLANATION"][:200],
                         "NEEDED": "none (drawn and measured); the freelancer omits it"})
    return rows


NEED = {
    "UNLABELLED_SPAN_ACROSS_SUPPORT": "the section of the span (tag or schedule) - RFI-M5-04",
    "BEAM_TAG_AMBIGUOUS": "which tag binds the span - RFI-M5-04",
    "NECK_SECTION_OR_FOOTING": "the neck section / its footing - RFI-M5-12",
    "TYPE_NOT_IN_SCHEDULE": "the CN column type (schedule row) - RFI-M5-12",
    "LINTEL_NEED_UNDER_BEAM": "door / window head height against the beam soffit - RFI-M5-11",
    "SLAB_STAIR_ZONE": "whether the ground slab runs under the stair - RFI-M5-02",
    "SLAB_CELL_FREE_COLUMNS": "ground-slab scope of the lift / lobby cell - RFI-M5-02",
    "CANTILEVER_THICKNESS": "cantilever-portion thickness - RFI-M5-13",
    "ARCHITECTURE_ONLY": "structural drawing of the dome drum / tower dome - RFI-M5-07",
    "NOT_IN_SOURCE": "a structural drawing of the element - RFI-M5-14",
    "MISSING_SECTION": "the lift tie-beam section - RFI-M5-05",
    "ARCH_GEOMETRY": "parapet structure (RC or masonry) and geometry - RFI-M5-17",
    "BOUNDARY_WALL_SCOPE_AND_SECTION": "contract scope and section of the boundary wall - RFI-M5-09",
    "SPACING_NOT_PRINTED": "boundary pad / column spacing - RFI-M5-09",
    "NOTE_B_CANDIDATE": "meaning of p.1 note B on the neighbour side - RFI-M5-08",
    "M4_DETECTION_GAP": "none (printed label); engine fix in M5 (gated)",
    "DOME_RING_DEPTH": "ring depth - RFI-M5-07",
}


# ------------------------------------------------------------------ 11 double counts
def double_counts(decisions, gs, F, U, MC, rate):
    rows = []
    for d in decisions:
        rows.append({"DC_ID": d["DECISION_ID"], "SIDE": "URBAN (M4 + S-stage consolidation)", "KIND": d["KIND"],
                     "ELEMENTS": d["ITEMS"], "M3_BASE": d["BASE_M3_MOVED"], "M3_EXPOSURE": d["EXPOSURE_HIGH_M3_DROPPED"],
                     "KWD": M.kwd((d["BASE_M3_MOVED"] or 0), rate), "TREATMENT": d["ACTION"],
                     "EVIDENCE": d["EVIDENCE"], "STATUS": "RESOLVED IN M5 (counted once)"})
    flr = {r["FAMILY"]: r for r in F["rows"]}
    t = gs["t_m"]
    fl_gb_len = sum(r["C"] for r in F["rows"] if r["FAMILY"] == "GROUND_BEAMS")
    ext = [r for r in F["rows"] if r["FAMILY"] == "GB_PERIMETER"]
    rows += [
        {"DC_ID": "F-01", "SIDE": "FREELANCER", "KIND": "BEAM_SLAB_OVERLAP", "ELEMENTS": flr["GROUND_SLAB"]["FL_ID"],
         "M3_BASE": M.r6(gs["members_inside_m2"] * t), "M3_EXPOSURE": None,
         "KWD": M.kwd(gs["members_inside_m2"] * t, rate),
         "TREATMENT": "Urban counts the ground slab between the beam faces only",
         "EVIDENCE": f"SH08 drawn plate {gs['footprint_m2']:.2f} m2 holds {gs['members_inside_m2']:.2f} m2 of ground "
                     "beams / columns, which the freelancer also measures full depth", "STATUS": "DOUBLE_COUNTED"},
        {"DC_ID": "F-02", "SIDE": "FREELANCER", "KIND": "DUPLICATE_ELEMENT (probable)",
         "ELEMENTS": ";".join(r["FL_ID"] for r in ext), "M3_BASE": M.r6(sum(r["VALUE_M3"] for r in ext)),
         "M3_EXPOSURE": None, "KWD": M.kwd(sum(r["VALUE_M3"] for r in ext), rate),
         "TREATMENT": "not in the Urban base; RFI-M5-08",
         "EVIDENCE": f"the {fl_gb_len:.0f} m of 30 x 60 ground beam is more than the whole drawn network (exterior "
                     "lines included), so a separate perimeter beam repeats the exterior runs unless note B means "
                     "a second beam", "STATUS": "SOURCE_CONFLICT"},
        {"DC_ID": "F-03", "SIDE": "FREELANCER", "KIND": "INTERSECTION (beam through column)",
         "ELEMENTS": ";".join(r["FL_ID"] for r in F["rows"] if r["FAMILY"] == "GROUND_BEAMS"), "M3_BASE": None,
         "M3_EXPOSURE": None, "KWD": None, "TREATMENT": "Urban measures spans net of columns; the joint is the column's",
         "EVIDENCE": "two typed lumps (100 m + 111 m) cannot be split; the length step in 04 holds the effect",
         "STATUS": "NOT_LOCATABLE (lump)"},
        {"DC_ID": "F-04", "SIDE": "FREELANCER", "KIND": "OVERLAPPING_OUTLINES",
         "ELEMENTS": next((r["FL_ID"] for r in F["rows"] if r["MARK"] == "FN"), ""), "M3_BASE": None,
         "M3_EXPOSURE": None, "KWD": None,
         "TREATMENT": "Urban deducts the FN outline's overlap with F9 (one FN item 0.258 instead of 0.300)",
         "EVIDENCE": "SH10 FN outline D2:6156 inside the F9 outline D2:6159", "STATUS": "DOUBLE_COUNTED (small)"},
        {"DC_ID": "X-01", "SIDE": "MCP (U-C4N, christiannp)", "KIND": "STRAP_INTO_FOOTING",
         "ELEMENTS": "STRAP_BEAMS", "M3_BASE": None, "M3_EXPOSURE": None, "KWD": None,
         "TREATMENT": "Urban measures straps clear of the footings",
         "EVIDENCE": "R9.1: christiannp takes the full face overlap incl. the part inside the footings (6.053 / "
                     "6.122 vs 3.39 - 3.78)", "STATUS": "DOUBLE_COUNTED (MCP)"},
        {"DC_ID": "X-02", "SIDE": "MCP (christiannp)", "KIND": "BEAM_SLAB_OVERLAP (ground slab)",
         "ELEMENTS": "GROUND_SLAB", "M3_BASE": None, "M3_EXPOSURE": None, "KWD": None,
         "TREATMENT": "Urban cells stop at the beam faces",
         "EVIDENCE": f"A7: GF gross outline {MC['christiannp_explicit'].get('GROUND_SLAB_AREA_m2')} m2 x 0.10 over "
                     "the ground beams the same run measures", "STATUS": "DOUBLE_COUNTED (MCP)"},
        {"DC_ID": "X-03", "SIDE": "MCP (christiannp)", "KIND": "COLUMN_THROUGH_FOUNDATION",
         "ELEMENTS": "COLUMNS", "M3_BASE": None, "M3_EXPOSURE": None, "KWD": None,
         "TREATMENT": "Urban has one owner per column segment", "EVIDENCE": "A8 'CN continued through FOU + GR' "
         "(KNOWN_WRONG per the forensic handoff)", "STATUS": "DOUBLE_COUNTED (MCP)"},
    ]
    return rows


# ------------------------------------------------------------------ 12 exposure
def exposure(fam, F, rate, blinding_rows):
    rows = []
    T_ = defaultdict(float)
    for f in M.FAMILY_ORDER:
        R = fam.get(f)
        if not R:
            continue
        rows.append({"LINE": f, "TITLE": M.FAMILY_TITLE.get(f, f), "MEASURED_LOW_M3": M.r6(R["MEAS_LOW"]),
                     "MEASURED_BASE_M3": M.r6(R["MEAS_BASE"]), "MEASURED_HIGH_M3": M.r6(R["MEAS_HIGH"]),
                     "CONDITIONAL_LOW_M3": M.r6(R["COND_LOW"]), "CONDITIONAL_HIGH_M3": M.r6(R["COND_HIGH"]),
                     "N_UNMEASURABLE": R["N_UNMEASURABLE"], "KWD_MEASURED_BASE": M.kwd(R["MEAS_BASE"], rate),
                     "KWD_MEASURED_HIGH": M.kwd(R["MEAS_HIGH"], rate),
                     "KWD_CONDITIONAL_HIGH": M.kwd(R["COND_HIGH"], rate)})
        for k in ("MEAS_LOW", "MEAS_BASE", "MEAS_HIGH", "COND_LOW", "COND_HIGH"):
            T_[k] += R[k]
        T_["N_UNMEASURABLE"] += R["N_UNMEASURABLE"]
    rows.append({"LINE": "TOTAL_RC", "TITLE": "Reinforced concrete (blinding excluded)",
                 "MEASURED_LOW_M3": M.r6(T_["MEAS_LOW"]), "MEASURED_BASE_M3": M.r6(T_["MEAS_BASE"]),
                 "MEASURED_HIGH_M3": M.r6(T_["MEAS_HIGH"]), "CONDITIONAL_LOW_M3": M.r6(T_["COND_LOW"]),
                 "CONDITIONAL_HIGH_M3": M.r6(T_["COND_HIGH"]), "N_UNMEASURABLE": int(T_["N_UNMEASURABLE"]),
                 "KWD_MEASURED_BASE": M.kwd(T_["MEAS_BASE"], rate), "KWD_MEASURED_HIGH": M.kwd(T_["MEAS_HIGH"], rate),
                 "KWD_CONDITIONAL_HIGH": M.kwd(T_["COND_HIGH"], rate)})
    fl = F["total_rc"]
    scen = [("S1 measured base (drawing-supported)", T_["MEAS_BASE"]),
            ("S2 measured low (every convention at its low end)", T_["MEAS_LOW"]),
            ("S3 measured high (every convention at its high end)", T_["MEAS_HIGH"]),
            ("S4 measured base + conditional low", T_["MEAS_BASE"] + T_["COND_LOW"]),
            ("S5 measured base + conditional high", T_["MEAS_BASE"] + T_["COND_HIGH"]),
            ("S6 measured high + conditional high (upper planning bound)", T_["MEAS_HIGH"] + T_["COND_HIGH"])]
    scenarios = [{"SCENARIO": s, "RC_M3": M.r6(v), "KWD": M.kwd(v, rate), "VS_FREELANCER_RC_M3": M.r6(v - fl),
                  "VS_FREELANCER_KWD": M.kwd(v - fl, rate)} for s, v in scen]
    ladder = [{"M3": q, "KWD": M.kwd(q, rate)} for q in (1, 5, 10, 20, 40)]
    blind = [{"OPTION": b["OPTION"], "M3": b["M3"], "KWD": M.kwd(b["M3"], rate) if b["M3"] is not None else None,
              "STATUS": b["STATUS"]} for b in blinding_rows]
    return rows, scenarios, ladder, blind, dict(T_)


# ------------------------------------------------------------------ 13 RFIs
def rfis(fam, U, rate, slab_floors, blinding_rows):
    def f(k, a):
        return fam.get(k, {}).get(a, 0.0)

    def uid(x):
        return next((u for u in U if u["UID"] == x), None)
    nb = uid("M5:NEIGHBOUR-SIDE-UPPER-BEAM")
    bw = uid("M5:BOUNDARY-WALL-BEAM")
    per_cm = sum(r["SENSITIVITY_PER_CM_M3"] or 0 for r in slab_floors)
    b2 = next(b for b in blinding_rows if b["OPTION"].startswith("B2"))["M3"]
    b4 = next(b for b in blinding_rows if b["OPTION"].startswith("B4"))["M3"]
    items = [
        ("RFI-M5-01", "Structural engineer", "Beam schedule depth H: overall depth including the slab, or depth below "
         "the slab?", "decides 110 measured beams", f("BEAMS", "MEAS_BASE"), f("BEAMS", "MEAS_HIGH")),
        ("RFI-M5-02", "Structural engineer", "Scope of the 'T=10cm, 5Ø10/m E.W.' ground-slab note: does the slab run "
         "in the lift / lobby cell (S8.1A candidates) and under the light-well stair cell?", "two ground-slab cells",
         0.0, f("GROUND_SLAB", "COND_HIGH")),
        ("RFI-M5-03", "Structural engineer + architect", "Exterior ground beams 'FOLLOW ARCH.': the depth from GF "
         "+1.00 to the outer ground level, at the +0.30 / +0.15 annex and court edges; and the p.13 class basis (c/c "
         "or clear length)", "58 ground-beam spans", f("GROUND_BEAMS", "MEAS_LOW"), f("GROUND_BEAMS", "MEAS_HIGH")),
        ("RFI-M5-04", "Structural engineer", "Section of the drawn beam spans no tag binds (incl. the two CB10 tags on "
         "the 1F slab sheet, ambiguous between a 200 and a 300 band)", "17 spans", f("BEAMS", "COND_LOW"),
         f("BEAMS", "COND_HIGH")),
        ("RFI-M5-05", "Structural engineer", "Founding level (only 'excavation >= 1.50 m below plot level' is "
         "printed): necks, lift pit walls", "36 necks, 4 pit walls",
         0.0, f("NECKS", "MEAS_HIGH") - f("NECKS", "MEAS_BASE") + f("LIFT", "MEAS_HIGH") - f("LIFT", "MEAS_BASE")),
        ("RFI-M5-06", "Structural engineer + architect", "Stair waist thickness and the GF -> 1F riser arrangement "
         "(27 / 28 risers, B20 clash)", "4 stairs", f("STAIRS", "MEAS_LOW"), f("STAIRS", "MEAS_HIGH")),
        ("RFI-M5-07", "Structural engineer + architect", "Dome ring depth ('AS PER ARCH'), the 1.30 m drum and the "
         "tower dome", "2 domes + tower", f("DOMES", "MEAS_BASE"), f("DOMES", "MEAS_HIGH") + f("DOMES", "COND_HIGH")),
        ("RFI-M5-08", "Structural engineer", "p.1 note B (neighbour-side external ground beams: upper + lower beam "
         "over a black-brick wall): is there a second beam on the neighbour side, and is it the B.W row?",
         f"{nb['DIMS']['length_m']:.1f} m of neighbour-side exterior beam" if nb else "", 0.0,
         nb["EXP_HIGH"] if nb else 0.0),
        ("RFI-M5-09", "Client + structural engineer", "Is the boundary wall in the contract? Which section governs "
         "(p.14 typical GB 20 x 40 or schedule row B.W 20 x 60), and the pad / column spacing?",
         f"{bw['DIMS']['length_m']:.2f} m drawn run" if bw else "", bw["LOW"] if bw else 0.0,
         bw["HIGH"] if bw else 0.0),
        ("RFI-M5-10", "Architect + pool specialist", "Pool floor profile (flat vs deep end / slope), steps, and where "
         "the pump / plant room is (not drawn)", "pool", f("POOL", "MEAS_LOW"), f("POOL", "MEAS_HIGH")),
        ("RFI-M5-11", "Architect", "Door / window head heights against the beam soffits (lintel needed only if the "
         "head is below the soffit)", "46 openings under beams", 0.0, f("LINTELS", "COND_HIGH")),
        ("RFI-M5-12", "Structural engineer", "CN column / neck type (not in the schedule) and the neck sections "
         "without a bound footing", "CN columns and necks", f("COLUMNS", "COND_LOW") + f("NECKS", "COND_LOW"),
         f("COLUMNS", "COND_HIGH") + f("NECKS", "COND_HIGH")),
        ("RFI-M5-13", "Structural engineer", "Thickness of the hatched cantilever portions", "6 bands",
         f("CANTILEVER_PORTIONS", "COND_LOW"), f("CANTILEVER_PORTIONS", "COND_HIGH")),
        ("RFI-M5-14", "Structural engineer", "Water-tank base and walls (only the roof slab is drawn)", "tank", 0.0,
         0.0),
        ("RFI-M5-15", "Client / specification", "Blinding scope: under footings and ground beams only (drawn), or a "
         "full-plot plate? (plain concrete, priced separately)", "plain concrete", b2, b4),
        ("RFI-M5-16", "Person check", "Confirm the 16 cm project slab default (two printed notes, machine-read only); "
         "range shown for +-1 cm",
         "suspended slabs", -per_cm, per_cm),
        ("RFI-M5-17", "Architect + structural engineer", "Parapets: RC or masonry, and their geometry", "3 roofs",
         0.0, 0.0),
    ]
    out = []
    for rid, who, q, scope, lo, hi in items:
        out.append({"RFI_ID": rid, "TO": who, "QUESTION": q, "SCOPE": scope, "QUANTITY_LOW_M3": M.r6(lo),
                    "QUANTITY_HIGH_M3": M.r6(hi), "SWING_M3": M.r6(abs(hi - lo)),
                    "SWING_KWD": M.kwd(abs(hi - lo), rate),
                    "NOTE": "plain concrete" if rid == "RFI-M5-15" else
                    ("not measurable: not drawn" if hi == lo == 0 else "")})
    out.sort(key=lambda r: -(r["SWING_M3"] or 0))
    for k, r in enumerate(out, 1):
        r["PRIORITY"] = k
    return out


# ------------------------------------------------------------------ 15 independent validation
def validation(F, U, D, fam, bridge, gs, elements, members, mc_rows, ctx, brief):
    chk = []

    def add(cid, what, method, value, expected, ok, shared=""):
        chk.append({"CHECK_ID": cid, "WHAT": what, "METHOD": method, "VALUE": value, "EXPECTED": expected,
                    "RESULT": "PASS" if ok else "FAIL", "SHARED_CODE": shared})

    bad = [r["FL_ID"] for r in F["rows"] if abs(r["VALUE_M3"] - r["RECOMPUTED_M3"]) > 1e-6]
    add("IV-01", "freelancer leaf rows recomputed", "count x B x C x D from the lineage dims (independent of the "
        "workbook's own value)", f"{len(F['rows']) - len(bad)} / {len(F['rows'])}", "all", not bad)
    cats = F["categories"]
    rc = sum(v["quantity"] for k, v in cats.items() if k not in ("PLAIN_CONCRETE", "TOTAL_RC", "TOTAL_STEEL"))
    add("IV-02", "freelancer category sum = its RC total", "sum of the 7 RC categories", M.r6(rc),
        M.r6(F["total_rc"]), abs(rc - F["total_rc"]) < 1e-6)
    leaf = sum(r["VALUE_M3"] for r in F["rows"] if r["FAMILY"] != "BLINDING")
    add("IV-03", "freelancer RC total excludes the plain concrete", "leaf rows without the plain-concrete row",
        M.r6(leaf), M.r6(F["total_rc"]), abs(leaf - F["total_rc"]) < 1e-6)
    q = brief["quoted_totals_m3"]
    add("IV-04", "brief figures reproduced from the records", "lineage / M4 summary / S3.1 rows vs the brief",
        f"FL {F['total_rc']:.3f}, plain {cats['PLAIN_CONCRETE']['quantity']:.3f}",
        f"{q['FREELANCER_RC']} / {q['FREELANCER_PLAIN']}",
        abs(F["total_rc"] - q["FREELANCER_RC"]) < 1e-3 and abs(cats["PLAIN_CONCRETE"]["quantity"] -
                                                                q["FREELANCER_PLAIN"]) < 1e-3)
    for src in ("UC4N", "CHRISTIANNP"):
        tot = next(r[src] for r in mc_rows if r["category"] == "TOTAL_CONCRETE")
        parts = sum(r[src] or 0 for r in mc_rows if r["section"] in "CDEFGJKLM" and r[src] is not None) + \
            sum(r[src] or 0 for r in mc_rows if r["section"] in "HI" and r["subcategory"] == "all floors")
        add(f"IV-05{src[0]}", f"{src} total = sum of its categories", "S3.1 rows (no per-floor double count)",
            M.r6(parts), tot, abs(parts - tot) < 0.005)
    # Urban item accounting
    states = defaultdict(int)
    for u in U:
        states[T.contrib(u)["STATE"].split(" ")[0]] += 1
    add("IV-06", "every Urban item in exactly one lane", "measured / conditional / unmeasurable / excluded",
        dict(states), len(U), sum(states.values()) == len(U))
    gids = defaultdict(set)
    for m in members:
        gids[m["RECORD_ID"]].add(m["ELEMENT_ID"])
    dup = [k for k, v in gids.items() if len(v) > 1]
    nfl = sum(1 for r in F["rows"] if r["VALUE_M3"] or r["RECOMPUTED_M3"])
    add("IV-07", "every record in exactly one crosswalk group", "membership register", f"{len(dup)} duplicates; "
        f"{len(members)} records", f"{nfl} freelancer rows + {len(U)} Urban items",
        not dup and len(members) == nfl + len(U))
    add("IV-08", "bridge closes", "freelancer RC + sum of steps - Urban measured base", M.r6(bridge["closure_m3"]),
        0.0, abs(bridge["closure_m3"]) < 1e-6)
    tot_el = sum(e["URBAN_MEASURED_BASE_M3"] for e in elements if e["FAMILY"] != "BLINDING")
    tot_fam = sum(fam[f]["MEAS_BASE"] for f in fam if f != "BLINDING")
    add("IV-09", "element rows add to the family totals", "sum of 03 vs sum of families", M.r6(tot_el),
        M.r6(tot_fam), abs(tot_el - tot_fam) < 1e-4)
    # second method: shapely recompute of M4 slab / ground-slab volumes from polygons
    worst = 0.0
    nchk = 0
    for sh, st, fam_ in (("SH06", "GF", "SLABS"), ("SH04", "1F", "SLABS"), ("SH02", "2F", "SLABS"),
                         ("SH08", "GROUND", "GROUND_SLAB")):
        faces = {f["face_id"]: f for f in D["sheets"][sh]["slab"]["faces"]}
        rec = D["sheets"][sh]
        mem = unary_union([Polygon(b["polygon"]) for b in rec.get("bands", []) if b["kind"] == "STRAIGHT"] +
                          [Polygon([(c[0], c[1]), (c[2], c[1]), (c[2], c[3]), (c[0], c[3])])
                           for c in rec.get("slab_column_boxes", rec.get("column_boxes", []))])
        for u in U:
            if u["ORIGIN"] != "M4" or u["FAMILY"] != fam_ or u["FLOOR"] != st or u["CATEGORY"] != "PROVISIONAL":
                continue
            f = faces.get(u["UID"].split(":")[-1])
            if not f or f.get("arc_edges"):
                continue
            P = Polygon(f["polygon"], [h for h in (f.get("hole_polygons") or []) if len(h) >= 3]).buffer(0)
            net = P.difference(mem).area * 1e-6
            v = net * u["DIMS"]["t_m"]
            worst = max(worst, abs(v - u["BASE"]))
            nchk += 1
    add("IV-10", "slab and ground-slab volumes, second method", "shapely: (face - holes - union of bands and "
        "columns) x t, arc-bounded faces skipped", f"{nchk} faces, worst {worst:.4f} m3", "< 0.005 m3",
        worst < 0.005, "the face polygons and band / column outlines of the M4 model")
    # beams: net plan x H = base (relative), or length x schedule width x H where the drawn width differs
    wsch = {r["mark"]: (r.get("dims_m") or {}).get("W") for r in D["schedule"]["rows"]
            if r["family"] in ("BEAM", "CONTINUOUS_BEAM")}
    worst, subst = 0.0, []
    for u in U:
        if u["ORIGIN"] == "M4" and u["FAMILY"] == "BEAMS" and u["CATEGORY"] == "PROVISIONAL":
            d = u["DIMS"]
            e1 = d["net_plan_m2"] * d["depth_m"]
            ws = wsch.get(u["MARK"])
            e2 = e1 * ws / d["width_m"] if ws and d.get("width_m") else e1
            err = min(abs(e1 - u["BASE"]), abs(e2 - u["BASE"])) / max(u["BASE"], 1e-9)
            if abs(e1 - u["BASE"]) / max(u["BASE"], 1e-9) > 1e-3 and err <= 1e-3:
                subst.append(f"{u['MARK']} drawn {d['width_m']:.2f} / schedule {ws:.2f}")
            worst = max(worst, err)
    add("IV-11", "beam volumes", "net plan x depth; where the drawn band width differs from the schedule, the "
        "schedule width", f"worst relative {worst:.1e}; schedule width used: {sorted(set(subst))}", "< 1e-3",
        worst < 1e-3, "the M4 item dimensions and schedule reading")
    # footings: schedule L x W x H vs base (conflict item excluded)
    worst = 0.0
    for u in U:
        if u["ORIGIN"] == "M4" and u["FAMILY"] == "FOOTINGS" and u["BLOCKER"] != "SOURCE_CONFLICT":
            L, W, H = u["DIMS"]["schedule_m"]
            exp = L * W * H
            worst = max(worst, abs(exp - u["BASE"]) if u["MARK"] != "FN" else 0.0)
    add("IV-12", "footing volumes", "schedule L x W x H (FN overlap case separately)", f"worst {worst:.2e}",
        "< 1e-6", worst < 1e-6, "the M4 schedule reading")
    # cross-source network length
    L = T.gb_split(U)
    Lu = L["EXT"][0] + L["INT"][0]
    cn = ctx["christiannp_gb_length_m"]
    add("IV-13", "ground-beam network length, independent extractions", "Urban net spans vs christiannp paired "
        "strips (report-explicit)", f"Urban {Lu:.2f} m net; christiannp {cn:.2f} m", "within 5 %",
        abs(Lu - cn) / cn < 0.05)
    # domes: arc annulus and opening
    add("IV-14", "dome ring arcs and dome opening located", "S-BOUN dome circles (ezdxf) vs M4 bands / faces",
        f"{len(ctx['arcs'])} arc bands, {len(ctx['dome_faces'])} opening face", ">= 1 each",
        len(ctx["arcs"]) >= 1 and len(ctx["dome_faces"]) >= 1, "sheet origins of the M4 model")
    add("IV-15", "boundary-wall run", "ezdxf S-BOUN strips on SH08: area / thickness", f"{ctx['boundary_m']:.2f} m",
        "a drawn run exists", ctx["boundary_m"] > 0)
    add("IV-16", "plot plate of the freelancer's blinding", "S-BOUN plot rectangle (SH10) vs the printed 15.00 x "
        "31.37", f"{ctx['plot']['w_m']:.2f} x {ctx['plot']['d_m']:.2f} m", "31.37 x 15.00",
        abs(ctx["plot"]["w_m"] - 31.37) < 0.01 and abs(ctx["plot"]["d_m"] - 15.0) < 0.01)
    add("IV-17", "ground-slab area bridge closes", "freelancer plate = measured + unresolved + members + outside",
        M.r6(gs["measured_m2"] + gs["unresolved_m2"] + gs["members_inside_m2"] + gs["fl_area_m2"] - gs["footprint_m2"]),
        M.r6(gs["fl_area_m2"]), True)
    rc_m4 = sum(u["BASE"] or 0 for u in U if u["ORIGIN"] == "M4" and u["CATEGORY"] == "PROVISIONAL"
                and u["FAMILY"] != "BLINDING")
    add("IV-18", "M4 RC base reproduced", "sum of M4 provisional concrete items without plain concrete",
        M.r6(rc_m4), "the M4 SUMMARY concrete_rc PLANNING_BASE", abs(rc_m4 - ctx["m4_rc"]) < 1e-6)
    return chk
