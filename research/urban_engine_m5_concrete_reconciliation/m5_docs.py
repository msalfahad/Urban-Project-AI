"""M5 narrative documents (00, 01, 05 - 09, 15, 17), written from the computed package so every number in the text is
the number in the tables. RECONCILIATION phase: external figures appear here only as compared positions."""

from __future__ import annotations

import m5_reconcile as M


def f(x, n=2):
    if x is None or x == "":
        return "-"
    if isinstance(x, str):
        return x
    return f"{x:,.{n}f}"


def k(x):
    return "-" if x is None else f"{x:,.0f}"


def table(rows, cols, heads=None, fmt=None):
    heads = heads or cols
    fmt = fmt or {}
    out = ["| " + " | ".join(heads) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for r in rows:
        cells = []
        for c in cols:
            v = r.get(c) if isinstance(r, dict) else r[cols.index(c)]
            cells.append(fmt[c](v) if c in fmt else (f(v) if isinstance(v, float) else ("-" if v in (None, "")
                                                                                          else str(v))))
        out.append("| " + " | ".join(c.replace("|", "/") for c in cells) + " |")
    return "\n".join(out)


def _el(P, fam, part=None, floor=None):
    return [e for e in P["elements"] if e["FAMILY"] == fam and (part is None or e["MARK_OR_PART"] == part)
            and (floor is None or e["FLOOR"] == floor)]


def documents(P):
    n = P["numbers"]
    u = n["urban_m5"]
    rate = P["rate"]
    fl = n["freelancer_rc_m3"]
    d = {}
    gap_mixed = fl - n["m4_total_incl_plain_m3"]
    gap_rc = fl - n["m4_rc_m3"]
    gap_m5 = fl - u["MEAS_BASE"]
    s_by = {s["STEP_ID"]: s for s in P["bridge"]["steps"]}
    top = sorted([e for e in P["elements"] if e["FAMILY"] != "BLINDING"],
                 key=lambda e: -abs(e["DIFF_FREELANCER_MINUS_URBAN_BASE_M3"] or 0))
    fam = P["fam"]
    ec = P["engine_change"]
    rfi = P["rfi"]

    # ---------------------------------------------------------------- 01 executive
    scen = {s["SCENARIO"][:2]: s for s in P["scen"]}
    lines = [
        "# M5: quotation-critical concrete reconciliation (ST7757)",
        "",
        "> **Status: NOT QUOTATION-READY as a fixed-price lump sum.** This is a planning reconciliation, not "
        "engineering approval. Nothing here is VERIFIED by a person, and the project gate stays INCOMPLETE. "
        f"Concrete is priced at the brief's rate of {rate} KWD/m3. Plain concrete (blinding) is kept apart from "
        "reinforced concrete (RC) everywhere.",
        "",
        "**Phase: RECONCILIATION.** The Urban engine was run first, at its frozen M4 state (commit "
        f"`35c0587`, V3 conventions); its register was hashed (`{n['freeze']['CANDIDATE_GEOMETRY_HASH']}`) before "
        "any external figure was read. The freelancer and MCP figures are read from their own records at build "
        "time. They explain differences only; no Urban quantity was chosen or tuned to meet them.",
        "",
        "## The answer in one table",
        "",
        table([
            {"Q": "Freelancer RC (excl. its 47.055 m3 plain concrete)", "M3": fl, "KWD": fl * rate},
            {"Q": "Urban M4 headline (the brief's 312.05) = RC + plain", "M3": n["m4_total_incl_plain_m3"],
             "KWD": n["m4_total_incl_plain_m3"] * rate},
            {"Q": "  of which Urban M4 RC", "M3": n["m4_rc_m3"], "KWD": n["m4_rc_m3"] * rate},
            {"Q": "  of which plain concrete (blinding), not RC", "M3": n["m4_plain_m3"], "KWD": n["m4_plain_m3"] * rate},
            {"Q": "**Urban M5 RC, drawing-supported measured base**", "M3": u["MEAS_BASE"], "KWD": u["MEAS_BASE"] * rate},
            {"Q": "  measured range (every convention low .. high)", "M3": f"{u['MEAS_LOW']:.2f} - {u['MEAS_HIGH']:.2f}",
             "KWD": f"{u['MEAS_LOW'] * rate:,.0f} - {u['MEAS_HIGH'] * rate:,.0f}"},
            {"Q": "  conditional allowances (drawn, need an answer)", "M3": f"{u['COND_LOW']:.2f} - {u['COND_HIGH']:.2f}",
             "KWD": f"{u['COND_LOW'] * rate:,.0f} - {u['COND_HIGH'] * rate:,.0f}"},
            {"Q": "  unmeasurable items (not drawn; listed, never zero)", "M3": f"{int(u['N_UNMEASURABLE'])} items",
             "KWD": "-"},
            {"Q": "Measured base + conditional high", "M3": scen["S5"]["RC_M3"], "KWD": scen["S5"]["KWD"]},
            {"Q": "Upper planning bound (measured high + conditional high)", "M3": scen["S6"]["RC_M3"],
             "KWD": scen["S6"]["KWD"]},
        ], ["Q", "M3", "KWD"], ["Quantity", "m3", "KWD"], {"KWD": lambda v: k(v) if isinstance(v, float) else str(v)}),
        "",
        "## A. Findings",
        "",
        "### Why the difference is not 40.39 m3",
        "",
        f"- **The 40.39 m3 compares unlike things.** {fl:.3f} - {n['m4_total_incl_plain_m3']:.3f} = {gap_mixed:.2f} m3. "
        f"The Urban figure includes {n['m4_plain_m3']:.3f} m3 of blinding; the freelancer's does not (its "
        f"{n['freelancer_plain_m3']:.3f} m3 of plain concrete is a separate row).",
        f"- **RC against RC, the M4 gap is {gap_rc:.2f} m3** ({gap_rc * rate:,.0f} KWD).",
        "- **M4's generic route does not measure four families** that the frozen S-stages measure: stairs, domes, the "
        f"pool and the lift-pit walls ({fam['STAIRS']['MEAS_BASE'] + fam['DOMES']['MEAS_BASE'] + fam['POOL']['MEAS_BASE'] + fam['LIFT']['MEAS_BASE']:.2f} m3).",
        f"- **With them, after the M5 ownership decisions** (no double count, 11A), Urban's measured RC is "
        f"{u['MEAS_BASE']:.3f} m3. The freelancer prices **{gap_m5:.2f} m3 more ({gap_m5 * rate:,.0f} KWD)**.",
        "",
        "### The difference, cause by cause",
        "",
        "Each step is Urban minus freelancer; the steps close exactly (IV-08). The full table with evidence is 04.",
        "",
        table(P["bridge"]["steps"], ["STEP_ID", "STEP", "M3", "KWD", "CLASS"],
              ["Step", "Cause", "m3", "KWD", "Class"], {"KWD": k, "M3": lambda v: f"{v:+.3f}"}),
        "",
        f"Start {P['bridge']['start']:.3f} m3 (freelancer RC) -> end {P['bridge']['end']:.3f} m3 (Urban measured base).",
        "",
        "**How to read the bridge:**",
        "",
        f"- **Freelancer items with no drawing behind them, or counted twice: {-(s_by['B01']['M3'] + s_by['B02']['M3'] + s_by['B03']['M3'] + s_by['B04']['M3'] + s_by['B05']['M3']):.2f} m3.**",
        "  - the boundary-wall beam (scope, B01);",
        "  - the 20 x 60 'perimeter tie beam' (B02): no such beam is drawn, and the 211 m of ground beam already runs the "
        "exterior lines;",
        "  - the pool pump room and steps (B03, B04): not drawn;",
        "  - the ground slab poured over the ground-beam and column footprint (B05): those beams are already full depth.",
        f"- **Different conventions: ground-beam depths and lengths, {-(s_by['B08']['M3'] + s_by['B09']['M3'] + s_by['B10']['M3']):.2f} m3 net.** "
        "The freelancer uses 30 x 60 everywhere; the drawings print 30 x 30 / 30 x 40 / 30 x 60 by span (p.13).",
        f"- **Urban is higher on the frame** (columns {s_by['B14']['M3']:+.2f}, slabs {s_by['B16']['M3']:+.2f}). "
        f"The beams net {s_by['B15']['M3']:+.2f} m3 because of **compensating errors**:",
        "  - the freelancer misses whole beams that are drawn (B27, B19, B25, B5, part of B6 / B4) and some column "
        "occurrences (1F C6, 2F C8);",
        "  - it measures other beams centre to centre.",
        "  - Per floor, allocation-free: GF agrees within 1 %, but the freelancer is "
        f"{-next(r for r in P['frame'] if r['FLOOR'] == '1F')['DIFF_FL_MINUS_URBAN_FRAME']:.2f} m3 short on 1F (07).",
        f"- **Stairs ({s_by['B18']['M3']:+.2f}) and the pool walls ({s_by['B20']['M3']:+.2f}) are assumption-driven.** The "
        "freelancer uses a 0.28 m slab equivalent on the stairs and 1.8 m pool walls. Urban integrates the drawn "
        "flights at the waist range (S8.7) and the drawn wall bands (S8.2A).",
        "",
        "### Largest items",
        "",
        table(top[:12], ["ELEMENT_ID", "FREELANCER_M3", "URBAN_MEASURED_BASE_M3", "URBAN_CONDITIONAL_HIGH_M3",
                         "COST_KWD", "CLASS"],
              ["Element", "Freelancer m3", "Urban base m3", "Urban cond. high m3", "KWD (FL - U)", "Class"],
              {"COST_KWD": k}),
        "",
        "**Missing:**",
        "",
        "- **In Urban's M4 base:**",
        "  - three planted columns (fixed in V4, B);",
        "  - the ground-slab cells under the lift lobby and the light-well stair (conditional);",
        "  - 17 drawn beam spans no tag binds, incl. CB10 on 1F (conditional);",
        "  - 46 lintels under beams (conditional).",
        "- **In the freelancer's BOQ:**",
        "  - the beams B27, B19, B25, B5 and B28 (and CA);",
        "  - a second F3 footing;",
        "  - the lobby steps ST-B;",
        "  - the dome ring beams;",
        "  - the lintels;",
        "  - the cantilever portions.",
        "",
        "**Double counted:**",
        "",
        "- **In the freelancer's BOQ:**",
        f"  - the ground slab over {P['gs']['members_inside_m2']:.1f} m2 of beams and columns ({P['gs']['members_inside_m2'] * 0.1:.2f} m3);",
        "  - the perimeter beam (probable, 8.60 m3).",
        "- **Avoided in M5:**",
        "  - the water-tank roof slabs held by two registers;",
        "  - the dome-A ring read by M4 as beams;",
        "  - the dome-B opening read by M4 as a stair zone;",
        "  - cantilever hatches read by M4 as unlabelled beams (11A).",
        "",
        "### Top 5 risks",
        "",
    ]
    for r in rfi[:5]:
        lines.append(f"{r['PRIORITY']}. **{r['RFI_ID']}**: {r['QUESTION']}")
        lines.append(f"   - Swing {r['SWING_M3']:.2f} m3 ({k(r['SWING_KWD'])} KWD); {r['SCOPE']}.")
    lines += [
        "",
        "## B. What changed",
        "",
        "### Engine fix (Phase 8)",
        "",
        "One confirmed defect is fixed: **planted columns labelled on a slab plan were not read.** The generic route "
        "read columns from the column plan only, so the three 'P.C 20x70' and 'P.C 20x50' labels on the GF and 1F slab "
        "sheets produced no column.",
        "",
        "The fix is gated on the new conventions set `engine/profiles/URBAN_M5_GENERIC_CONVENTIONS_V4.json`. That set is "
        "V3 plus `PLANTED_COLUMN_LABELS`. The CLI default stays V3, so the frozen M4 package still reproduces byte "
        "for byte.",
        "",
        table([{"RUN": "before: V3 (frozen M4)", "RC": ec["v3_rc"]}, {"RUN": "after: V4 (M5)", "RC": ec["v4_rc"]},
               {"RUN": "difference", "RC": ec["v4_rc"] - ec["v3_rc"]}], ["RUN", "RC"], ["Engine run", "RC m3"],
              {"RC": lambda v: f"{v:.3f}"}),
        "",
        f"KWD impact: +{(ec['v4_rc'] - ec['v3_rc']) * rate:,.1f}. The items are in 18; the bars stay MISSING_DATA (no ratio).",
        "",
        "### M5 ownership decisions",
        "",
        "They decide which register owns an element that two registers hold, and record what the frozen M4 run "
        "missed (11A). The M4 base changes only by D-02 (ring arcs reallocated to the domes) and D-06 (planted "
        "columns added):",
        "",
        table(P["decisions"], ["DECISION_ID", "KIND", "ACTION", "BASE_M3_MOVED", "EXPOSURE_HIGH_M3_DROPPED"],
              ["Id", "Kind", "Action", "Base m3", "Exposure m3 dropped"]),
        "",
        "### Classification of every candidate defect",
        "",
        table(ENGINE_CANDIDATES, ["ID", "FINDING", "CLASS", "ACTION"], ["Id", "Finding", "Class", "Action"]),
        "",
        "### New unresolved or conditional items",
        "",
        f"- **Boundary wall:** a drawn run of {P['boundary']['length_m']:.2f} m on layer S-BOUN, valued "
        f"{fam['BOUNDARY_WALL']['COND_LOW']:.2f} - {fam['BOUNDARY_WALL']['COND_HIGH']:.2f} m3 for the beam only. Pads "
        "and columns: spacing not printed.",
        f"- **The p.1 note B neighbour-side beam:** 0 - {next(x for x in P['U'] if x['UID'] == 'M5:NEIGHBOUR-SIDE-UPPER-BEAM')['EXP_HIGH']:.2f} m3.",
        "- **The lift / lobby ground-slab cell, split by S8.1A:** slab candidates "
        f"{P['ctx']['decomposition'][0][0]['M5_SLAB_M2']:.2f} m2.",
        "",
        "## C. What is still unanswered (minimum questions)",
        "",
        table(rfi, ["PRIORITY", "RFI_ID", "TO", "QUESTION", "QUANTITY_LOW_M3", "QUANTITY_HIGH_M3", "SWING_KWD", "NOTE"],
              ["#", "RFI", "To", "Question", "Low m3", "High m3", "Swing KWD", "Note"], {"SWING_KWD": k}),
        "",
        "## D. Recommendation",
        "",
        "**NOT QUOTATION-READY for a fixed price.** The blockers are:",
        "",
        f"1. **RFI-M5-01, the beam depth reading:** {fam['BEAMS']['MEAS_HIGH'] - fam['BEAMS']['MEAS_BASE']:.2f} m3.",
        "2. **The ground-slab extent and the exterior ground-beam depth (RFI-M5-02, -03)**, plus the unlabelled spans "
        "(RFI-M5-04).",
        "3. **Elements with no drawing:** the pump room, the water-tank base and walls, the parapets, the boundary-wall "
        "pads and columns, and the tower dome / drum.",
        "",
        "**Closest defensible schedule:**",
        "",
        f"- **Quote the measured base, {u['MEAS_BASE']:.2f} m3 RC, as provisional quantities** (remeasurable), with the "
        f"conditional allowances {u['COND_LOW']:.2f} - {u['COND_HIGH']:.2f} m3 as separately listed items.",
        f"- **Add the blinding as its own line:** {n['m4_plain_m3']:.2f} m3 drawn, or the full-plot alternative.",
        "- **List the unmeasurable items as exclusions or provisional sums.** Never price them at zero.",
        "- **Use a variation mechanism** for the RFI outcomes. The 12 workbook gives every line at "
        f"{rate} KWD/m3.",
        "",
        "Do not take the freelancer's total as a target. It contains items with no drawing behind them and a probable "
        "double count. It also misses drawn beams, some column occurrences, the dome rings and the lintels.",
        "",
    ]
    d["01_EXECUTIVE_CONCRETE_RECONCILIATION.md"] = "\n".join(lines) + "\n"
    d["00_README.md"] = readme(P)
    d["05_GROUND_BEAM_AND_SLAB_AUDIT.md"] = doc05(P)
    d["06_SUSPENDED_SLAB_AUDIT.md"] = doc06(P)
    d["07_FOUNDATIONS_COLUMNS_BEAMS_AUDIT.md"] = doc07(P)
    d["08_STAIRS_DOMES_POOL_AUDIT.md"] = doc08(P)
    d["09_BLINDING_CONCRETE_AUDIT.md"] = doc09(P)
    d["15_INDEPENDENT_VALIDATION.md"] = doc15(P)
    d["17_CHATGPT_HANDOFF.md"] = doc17(P)
    return d


ENGINE_CANDIDATES = [
    {"ID": "E-01", "FINDING": "planted columns labelled on slab plans ('P.C 20x70') are not read",
     "CLASS": "MISSING_DETECTION (confirmed: printed label, S8.5 population, freelancer rows)",
     "ACTION": "FIXED in V4 (PLANTED_COLUMN_LABELS); +3 columns"},
    {"ID": "E-02", "FINDING": "the dome-A ring arcs on the 1F sheet are bound to the straight-beam tag B4",
     "CLASS": "UNRESOLVED_INTERPRETATION (the ring depth is 'AS PER ARCH')",
     "ACTION": "M5 decision D-02 (S8.3 owns the ring); no generic rule"},
    {"ID": "E-03", "FINDING": "dome-B radial lines read as winder treads (stair zone)",
     "CLASS": "INCORRECT_CLASSIFICATION, fail-safe (unresolved, not in the base)",
     "ACTION": "M5 decision D-03; not fixed generically (a spiral stair fans the same way)"},
    {"ID": "E-04", "FINDING": "the S-BW lift-pit outlines are not used as ground-slab face edges",
     "CLASS": "MISSING_DETECTION (exposure only: the cell is unresolved)",
     "ACTION": "M5 decision D-05; RFI-M5-02 decides the cell"},
    {"ID": "E-05", "FINDING": "cantilever hatches read as unlabelled beams",
     "CLASS": "UNRESOLVED_INTERPRETATION (exposure only)", "ACTION": "M5 decision D-04"},
    {"ID": "E-06", "FINDING": "the M4 headline concrete total adds plain concrete to RC",
     "CLASS": "REPORTING_ONLY (the summary keeps concrete_rc separately)",
     "ACTION": "M5 reports RC and plain apart; the frozen M4 text is not edited"},
    {"ID": "E-07", "FINDING": "two registers hold the water-tank roof slabs", "CLASS": "REPORTING_ONLY",
     "ACTION": "M5 decision D-01"},
]


def readme(P):
    n = P["numbers"]
    files = [
        ("00_NUMBERS.json", "Every headline number, the freeze block, the check count"),
        ("01_EXECUTIVE_CONCRETE_RECONCILIATION.md", "Findings, what changed, the questions, the recommendation"),
        ("02_SOURCE_SCOPE_MATRIX.csv", "Scope item x source: quantity and measurement basis"),
        ("02A_SOURCE_INVENTORY.csv", "Every file read, sha256, recorded-hash check; missing sources with location"),
        ("02B_FOUR_SOURCE_BASELINE.csv", "The four totals reproduced from their records"),
        ("02C_FAMILY_TOTALS.csv", "Family totals of the four sources and of the Urban reference"),
        ("03_ELEMENT_BY_ELEMENT_COMPARISON.csv", "One row per element group (family, floor, mark): four sources, class, "
                                                 "cost, location, treatment"),
        ("03A_ELEMENT_MEMBERSHIP.csv", "Every freelancer row and Urban item, with its group and state (nothing dropped)"),
        ("04_FREELANCER_VS_URBAN_BRIDGE.csv", "Ordered causes from the freelancer RC to the Urban measured base"),
        ("05_GROUND_BEAM_AND_SLAB_AUDIT.md", "+ 05A (cells), 05B (beam classes)"),
        ("06_SUSPENDED_SLAB_AUDIT.md", "+ 06A (panels), 06B (floors)"),
        ("07_FOUNDATIONS_COLUMNS_BEAMS_AUDIT.md", "+ 07A (mark crosswalk), 07B (frame per floor)"),
        ("08_STAIRS_DOMES_POOL_AUDIT.md", "Stairs, domes, pool, lift and specials"),
        ("09_BLINDING_CONCRETE_AUDIT.md", "+ 09A (blinding options); plain concrete only"),
        ("10_MISSING_CONCRETE_REGISTER.csv", "Missing in Urban's base or in the freelancer's, located"),
        ("11_DOUBLE_COUNT_REGISTER.csv", "+ 11A (the M5 ownership decisions)"),
        ("12_QUOTATION_COST_EXPOSURE.xlsx", "Generated, git-ignored; CSV twins 12 / 12A committed"),
        ("13_PRIORITY_RFIS.csv", "The minimum questions, ranked by KWD swing"),
        ("14_VISUAL_CONCRETE_QA.pdf", "Generated, git-ignored; the HTML and the SVGs (visual/) are committed"),
        ("15_INDEPENDENT_VALIDATION.md", "+ 15A (the checks)"),
        ("16_TEST_RESULTS.md", "Tests on this commit"),
        ("17_CHATGPT_HANDOFF.md", "What worked, what did not, what to do next"),
        ("18_ENGINE_CHANGE_V3_TO_V4.csv", "Before / after of the Phase 8 engine fix"),
        ("M5_CONCRETE_RECONCILIATION_WORKBOOK.xlsx", "Consolidated workbook (generated, git-ignored)"),
    ]
    return "\n".join([
        "# M5: quotation-critical concrete reconciliation and independent quantity audit (ST7757)",
        "",
        "Planning reconciliation, not engineering approval. The gate stays INCOMPLETE.",
        "",
        f"- **Phase:** RECONCILIATION. The Urban engine is frozen at M4 `35c0587`; candidate hash "
        f"`{n['freeze']['CANDIDATE_GEOMETRY_HASH']}`.",
        "- **External figures:** read from their records at build time. They never reach the engine and no quantity "
        "was tuned to them.",
        "- **Freelancer source:** the original workbook is not in this environment. The hash-pinned S3.1 lineage, which "
        "traced every leaf row from the workbook's formulas, is used and cited as DERIVED (02A).",
        "- **MCP sources:**",
        "  - U-C4N is held at category level only;",
        "  - christiannp has report-explicit per-floor and per-stage values;",
        "  - neither sealed report is in the repository (02A records where they were expected).",
        "",
        "**Rebuild** (the private drawings in `data/inputs/by_sha256/`):",
        "",
        "```",
        "python3 -I research/urban_engine_m5_concrete_reconciliation/build_m5_package.py --cache CACHE_DIR",
        "```",
        "",
        "**Paths:** `{P}` in printed paths stands for the project folder prefix of the stage folders (not reproduced).",
        "",
        table([{"F": a, "W": b} for a, b in files], ["F", "W"], ["File", "What it holds"]),
        "",
    ]) + "\n"


def doc05(P):
    s_by = {s["STEP_ID"]: s for s in P["bridge"]["steps"]}
    gs = P["gs"]
    n = P["numbers"]
    b = P["boundary"]
    fam = P["fam"]
    flr = {r["FL_ID"]: r for r in P["F"]["rows"]}
    gbfl = [r for r in P["F"]["rows"] if r["FAMILY"] in ("GROUND_BEAMS", "GB_PERIMETER", "BOUNDARY_WALL")]
    dec = P["ctx"]["decomposition"]
    parts = dec[0][2] if dec else {}
    ce = P["MC"]["christiannp_explicit"]
    gz_fl = sum(r["VALUE_M3"] for r in P["F"]["rows"] if r["FAMILY"] in ("GROUND_SLAB", "GROUND_BEAMS", "GB_PERIMETER",
                                                                         "BOUNDARY_WALL", "STRAPS"))
    gz_u = sum(fam[x]["MEAS_BASE"] for x in ("GROUND_SLAB", "GROUND_BEAMS", "STRAPS"))
    return "\n".join([
        "# 05 Ground beams + ground slab (investigation A)",
        "",
        "## The ground zone, allocation-free",
        "",
        f"The freelancer's ground zone is {gz_fl:.3f} m3: its 'ground beams + ground slab' category, plus the "
        "perimeter beam and straps it files under foundations, plus the boundary-wall beam. Urban measures "
        f"{gz_u:.3f} m3 (ground slab + ground beams + straps), with conditional cells "
        f"{fam['GROUND_SLAB']['COND_LOW']:.2f} - {fam['GROUND_SLAB']['COND_HIGH']:.2f} m3 and a conditional "
        f"boundary-wall beam {fam['BOUNDARY_WALL']['COND_LOW']:.2f} - {fam['BOUNDARY_WALL']['COND_HIGH']:.2f} m3.",
        "",
        "The brief's '75.09 vs 51.24' compares the freelancer's category with M4's ground beams + slab. That "
        "category already holds the boundary-wall beam; the perimeter beam and straps sit in its foundations "
        "category.",
        "",
        "## Ground slab: where the freelancer's 295.5 m2 goes",
        "",
        table([
            {"A": "freelancer plate (one typed area, no outline)", "M2": gs["fl_area_m2"], "M3": gs["fl_m3"]},
            {"A": "drawn ground-floor plate (union of all SH08 faces: cells, beam strips, columns)", "M2": gs["footprint_m2"],
             "M3": None},
            {"A": "  cells Urban measures (20 cells, 0.10)", "M2": gs["measured_m2"], "M3": fam["GROUND_SLAB"]["MEAS_BASE"]},
            {"A": "  cells Urban holds (lift / lobby cell, light-well stair cell)", "M2": gs["unresolved_m2"],
             "M3": None},
            {"A": "  ground beams and columns inside the plate (already full depth)", "M2": gs["members_inside_m2"],
             "M3": None},
            {"A": "freelancer area beyond the drawn plate (cannot be located)", "M2": gs["fl_area_m2"] - gs["footprint_m2"],
             "M3": None},
            {"A": "christiannp (A7: GF gross outline)", "M2": gs["christiannp_area_m2"],
             "M3": ce.get("GROUND_SLAB_m3")},
        ], ["A", "M2", "M3"], ["", "m2", "m3"]),
        "",
        "Two parts of the 295.5 m2 can be located, and one cannot:",
        "",
        f"- **{gs['members_inside_m2']:.2f} m2 of the plate is ground beams and columns.** The freelancer prices them "
        f"again at full depth, so {gs['members_inside_m2'] * 0.1:.2f} m3 is double counted (BEAM_SLAB_OVERLAP).",
        f"- **{gs['unresolved_m2']:.2f} m2 is the two cells Urban holds.**",
        f"- **{gs['fl_area_m2'] - gs['footprint_m2']:.2f} m2 lies beyond the drawn plate and cannot be located.** A "
        "single typed area cannot be placed. The 1.2 m passage between the two blocks (S-BOUN strip, +0.15) is a "
        "candidate.",
        "",
        "### The held cells",
        "",
        "The M4 face of the lift / lobby cell is split by the S8.1A recovered regions. Those polygons are in the same "
        "sheet frame plus the SH08 origin, and they were intersected exactly:",
        "",
        table([{"K": f"{kk[1]} ({kk[2]})", "A": a} for kk, a in sorted(parts.items(), key=lambda kv: -kv[1])],
              ["K", "A"], ["Region inside the M4 cell", "m2"], {"A": lambda v: f"{v:.3f}"}),
        "",
        "How the cell is treated:",
        "",
        "- **M4 already deducted the four ground-beam bands that cross it.** The lift void and the 200 mm pit walls "
        "are still inside the face: the S-BW pit outlines are not face edges.",
        "- **M4's exposure of the face (4.49 m3) therefore overstates the slab** by the void and the walls.",
        f"- **M5 carries the slab candidates as CONDITIONAL ground slab:** {parts and sum(a for kk, a in parts.items() if kk[0] == 'GROUND_SLAB_CANDIDATE'):.2f} m2 x 0.10 "
        "(low). The high end adds the lobby / stair region.",
        "- **The TT1 note's scope is not established (S8.1A).** That is RFI-M5-02.",
        "",
        "## Ground beams",
        "",
        table(P["gb_rows"], ["CLASS", "WIDTH_M", "DEPTH_BASE_M", "DEPTH_LOW_M", "DEPTH_HIGH_M", "ARCH_FLOOR_LEVEL",
                             "N_SPANS", "LENGTH_M", "BASE_M3", "BLOCKER"],
              ["Class", "W", "H base", "H low", "H high", "Level inside", "Spans", "Length m", "Base m3", "Blocker"]),
        "",
        "### The freelancer's rows",
        "",
        table(gbfl, ["FL_ID", "DESCRIPTION", "B", "C", "D", "VALUE_M3"], ["Row", "What", "B", "C", "D", "m3"]),
        "",
        "B, C and D are as typed in the workbook: width, length, depth on the ground-beam rows; width, depth, length "
        "on the perimeter row.",
        "",
        "**Same network, different depth and length.** Three independent extractions agree on the drawn network:",
        "",
        "- Urban's spans: 194.29 m net of columns;",
        f"- christiannp: {ce.get('GBP_PAIRED_STRIPS')} strips, {ce.get('GBP_LENGTH_m')} m gross;",
        "- U-C4N: about 200 m (36.005 / 0.18).",
        "",
        "The freelancer's 211 m is that network measured through the columns and junctions, with about 12 m more.",
        "",
        "**Depth:**",
        "",
        "- **Interior.** The freelancer's 0.60 everywhere replaces the printed p.13 classes: 30 x 30 under 2.5 m, "
        f"30 x 40 under 5 m, 30 x 60 over 5 m ({s_by['B09']['M3']:+.2f} m3). Which length selects the "
        "class (centre to centre or clear) is RFI-A05; Urban takes the base reading and shows the range.",
        f"- **Exterior.** The detail is 30 x 'FOLLOW ARCH.' Urban brackets it at 0.9 - 1.0 m where the plan prints "
        f"+1.00 inside, and keeps the class section where the inside level is +0.30 / +0.15 (annex, court) "
        f"({s_by['B10']['M3']:+.2f} m3).",
        "",
        "**The perimeter tie beam (71.7 m x 20 x 60, 8.604 m3) is not a drawn element:**",
        "",
        "- every ground beam on SH08 is a 300 mm band;",
        "- the 20 x 60 section is the schedule row B.W (boundary-wall beam), which binds to no plan occurrence;",
        "- p.1 note B describes an upper and a lower beam over a black-brick wall on the neighbour side (CANDIDATE).",
        "",
        f"Urban holds note B as UNRESOLVED (0 - {next(x for x in P['U'] if x['UID'] == 'M5:NEIGHBOUR-SIDE-UPPER-BEAM')['EXP_HIGH']:.2f} m3 "
        f"over {b['neighbour_m']:.2f} m of neighbour-side exterior beam), RFI-M5-08.",
        "",
        "### The boundary wall",
        "",
        "Layer S-BOUN on SH08 draws the wall strips, 200 mm thick:",
        "",
        f"- the main run along the neighbour, street and sea sides: {P['runs'][0]['centreline_m']:.2f} m;",
        "- two short pieces: " + ", ".join("%.2f m" % r["centreline_m"] for r in P["runs"][1:]) + ".",
        "",
        f"The freelancer's 42 m follows the main run. p.14 prints a typical: {b['typical_text']}. It conflicts with "
        f"the B.W row (20 x 60), and the spacing of pads and columns is not printed. The beam is a CONDITIONAL "
        f"{fam['BOUNDARY_WALL']['COND_LOW']:.2f} - {fam['BOUNDARY_WALL']['COND_HIGH']:.2f} m3; pads and columns are "
        "UNRESOLVED. Whether the boundary wall is in the contract at all is the client's call (RFI-M5-09).",
        "",
        "## Map",
        "",
        "`visual/01_GROUND_ZONE_FOOTPRINT.svg` (annotated), `visual/09d_UNRESOLVED_SH08.svg`.",
        "",
    ]) + "\n"


def doc06(P):
    fl = P["slab_floors"]
    tot_u = sum(r["URBAN_M3"] for r in fl)
    tot_f = sum(r["FREELANCER_M3"] for r in fl)
    cn = sum(r["CHRISTIANNP_M3"] for r in fl)
    rows18 = [r for r in P["slab_rows"] if r["THICKNESS_M"] == 0.18]
    per_cm = sum(r["SENSITIVITY_PER_CM_M3"] for r in fl)
    fr = {r["FLOOR"]: r for r in P["frame"]}
    return "\n".join([
        "# 06 Suspended slabs (investigation B)",
        "",
        "## Per floor",
        "",
        table(fl, ["FLOOR", "URBAN_PANELS", "URBAN_NET_AREA_M2", "URBAN_M3", "FREELANCER_AREA_M2", "FREELANCER_M3",
                   "AREA_DIFF_FL_MINUS_URBAN_M2", "CHRISTIANNP_NET_AREA_M2", "CHRISTIANNP_M3", "CHRISTIANNP_IMPLIED_T_M"],
              ["Floor", "Panels", "Urban net m2", "Urban m3", "FL m2", "FL m3", "FL - U m2", "christiannp m2",
               "christiannp m3", "christiannp t"]),
        "",
        f"Urban has {tot_u:.3f} m3 and the freelancer {tot_f:.3f} m3: they agree within {abs(tot_u - tot_f):.2f} m3.",
        "",
        "- **Both use the same convention.** Panels are net of the beam footprints, and the beams are measured full "
        "depth (06A shows the overlap Urban deducts per panel).",
        f"- **The MCPs reach {cn:.1f} m3 (christiannp; U-C4N 95.689) for two reasons:**",
        "  - they run the slab over the beams (net areas 290.6 / 179.3 / 55.3 m2, against Urban's beam-net panels) and "
        "measure the beams as downstands only;",
        "  - christiannp's GF volume implies 0.20 m (assumption A1, against the printed 16 cm).",
        "- **Allocation-free frame per floor** (07B):",
        f"  - GF: freelancer {fr['GF']['FL_FRAME']:.2f}, Urban {fr['GF']['URBAN_FRAME']:.2f}, christiannp {f(fr['GF']['CHRISTIANNP_FRAME'])};",
        f"  - 1F: freelancer {fr['1F']['FL_FRAME']:.2f}, Urban {fr['1F']['URBAN_FRAME']:.2f}, christiannp {f(fr['1F']['CHRISTIANNP_FRAME'])};",
        f"  - 2F: freelancer {fr['2F']['FL_FRAME']:.2f}, Urban {fr['2F']['URBAN_FRAME']:.2f}, christiannp {f(fr['2F']['CHRISTIANNP_FRAME'])}.",
        "",
        "## The 16 cm default and the 18 cm panels",
        "",
        "**The 16 cm default is printed, but no person has read it yet.** Panels without their own tag take 16 cm, "
        "which is printed twice:",
        "",
        "- the p.8 general note N18;",
        "- p.1 note A.",
        "",
        "Both are Arabic vector glyphs, read by machine (S1 census, M4 OCR). The freelancer's own label 'S.S 16 CM' "
        "uses the same value, but agreement between machine readings is not human verification.",
        "",
        f"**Sensitivity:** each 1 cm on the default panels is {per_cm:.2f} m3 ({per_cm * P['rate']:,.0f} KWD), RFI-M5-16.",
        "",
        "**The two 18 cm panels** (" + ", ".join("%s %.3f m2" % (r["PANEL_ID"], r["NET_AREA_M2"]) for r in rows18) +
        ") carry "
        "a printed 'T 18' tag. They are the water-tank roof (S8.4 measures the same two panels: decision D-01, counted "
        "once).",
        "",
        "## Faces that are not slab",
        "",
        "The 1F face M4 held as a stair zone (17.13 m2, 2.74 m3 exposure) contains the dome-B centre. The dome's "
        "radial lines were read as winder treads. S8.3 records no slab inside the dome circle, so the exposure is "
        "dropped (D-03). The dome-A interior is a beam-strip face and was never counted.",
        "",
        "Panel table: 06A (Panel ID | floor | gross | openings | beam / column overlap | net | t | volume | source). "
        "Maps: `visual/03a-c_SLAB_MAP_*.svg`.",
        "",
    ]) + "\n"


def doc07(P):
    fr = P["frame"]
    rows = [e for e in P["elements"] if e["FAMILY"] == "BEAMS" and e["CLASS"] != "MATCHED_WITHIN_TOLERANCE"]
    rows.sort(key=lambda e: -abs(e["DIFF_FREELANCER_MINUS_URBAN_BASE_M3"] or 0))
    ft = [e for e in P["elements"] if e["FAMILY"] in ("FOOTINGS", "STRAPS", "NECKS")]
    col = [e for e in P["elements"] if e["FAMILY"] == "COLUMNS"]
    fam = P["fam"]
    return "\n".join([
        "# 07 Foundations, columns and beams (investigations C + D)",
        "",
        "## Frame per floor (allocation-free)",
        "",
        table(fr, ["FLOOR", "FL_COLUMNS", "FL_BEAMS", "FL_SLABS", "FL_FRAME", "URBAN_COLUMNS", "URBAN_BEAMS", "URBAN_SLABS",
                   "URBAN_FRAME", "URBAN_CONDITIONAL_HIGH", "CHRISTIANNP_FRAME", "DIFF_FL_MINUS_URBAN_FRAME"],
              ["Floor", "FL col", "FL beams", "FL slabs", "FL frame", "U col", "U beams", "U slabs", "U frame",
               "U cond. high", "christiannp frame", "FL - U"]),
        "",
        "**The near-equal beam totals hide compensating errors.** Per floor, the GF frames agree; the freelancer "
        "is short on 1F and close on 2F.",
        "",
        "Columns differ by convention: the freelancer takes clear height under the beams and measures the beams "
        "through the joints. Urban takes floor to floor and measures the beams net of the columns. The joint is "
        "counted once either way, so only the frame per floor compares.",
        "",
        "## Beams by floor and mark (largest differences)",
        "",
        table(rows[:30], ["FLOOR", "MARK_OR_PART", "FREELANCER_M3", "URBAN_MEASURED_BASE_M3", "URBAN_CONDITIONAL_HIGH_M3",
                          "DIFF_FREELANCER_MINUS_URBAN_BASE_M3", "CLASS"],
              ["Floor", "Mark", "FL m3", "U base m3", "U cond. high", "FL - U", "Class"]),
        "",
        "**What the mark crosswalk shows** (07A has every mark):",
        "",
        "- **Many marks match to the litre** (GF B22, B29, B3, B5, B8, B11, B14, B16; 1F B18, B1, B11, B3; 2F B7). "
        "Same geometry, same depth reading.",
        "- **Missing in the freelancer's BOQ, though drawn and bound:**",
        "  - GF B27 (90 x 85, 3.27 m);",
        "  - 1F B19, B25 and B5;",
        "  - most of the 1F B6 length (21.4 m drawn against 4.37 m priced);",
        "  - GF B28 and CA.",
        "- **Missing in Urban's base:**",
        "  - 1F CB10: two tags sit between a 200 band and a 300 band, so it is AMBIGUOUS and held in the 1F "
        "unlabelled-span exposure;",
        "  - the unlabelled spans in general: CONDITIONAL, RFI-M5-04.",
        "- **Length differences on continuous beams** (CB1 - CB8, CB9 - CB13): the freelancer measures centre to "
        "centre or the scheduled total; Urban measures the drawn spans net of the supports.",
        "- **Depth reading (RFI-M5-01).** Urban's base takes H as the overall depth (slab inside); the high end, "
        f"{fam['BEAMS']['MEAS_HIGH']:.2f} m3, takes H below the slab. The freelancer uses the base reading.",
        "- **The two dome-A ring arcs** that M4 bound to B4 are moved to the dome ring (D-02).",
        "",
        "## Footings, straps and necks",
        "",
        table(ft, ["FAMILY", "MARK_OR_PART", "FREELANCER_M3", "URBAN_MEASURED_BASE_M3", "URBAN_CONDITIONAL_HIGH_M3",
                   "DIFF_FREELANCER_MINUS_URBAN_BASE_M3", "CLASS"],
              ["Family", "Mark", "FL m3", "U base m3", "U cond. high", "FL - U", "Class"]),
        "",
        "**Footings agree mark for mark** (same schedule sizes), with two exceptions:",
        "",
        "- SH10 draws two F3 outlines, and the freelancer prices one;",
        "- one FN outline overlaps F9, and Urban deducts the overlap.",
        "",
        "**The F/F10 conflict outline:** both sources price it as F10.",
        "",
        "**Necks:** the freelancer's 1.50 m against Urban's footing top to +1.00. The founding level is printed only "
        "as a minimum (1.50 m below plot level), so it is RFI-M5-05.",
        "",
        "**Straps:** Urban measures clear of the footings; the MCPs measure into them (11, X-01).",
        "",
        "## Columns",
        "",
        table(col, ["FLOOR", "MARK_OR_PART", "FREELANCER_M3", "URBAN_MEASURED_BASE_M3", "URBAN_CONDITIONAL_HIGH_M3",
                    "CLASS"], ["Floor", "Mark", "FL m3", "U base m3", "U cond. high", "Class"]),
        "",
        "**Planted columns (P.C, 1F and 2F):** the freelancer prices them (PC1, PC2, PC) and M4 missed them. The engine "
        "fix (V4) and M5 decision D-06 add them.",
        "",
        "**CN columns:** their type is not in the schedule (RFI-M5-12).",
        "",
        "**Lift-pit walls:** see 08.",
        "",
    ]) + "\n"


def doc08(P):
    st = [e for e in P["elements"] if e["FAMILY"] in ("STAIRS",)]
    dm = [e for e in P["elements"] if e["FAMILY"] == "DOMES"]
    pl = [e for e in P["elements"] if e["FAMILY"] in ("POOL", "POOL_PUMP_ROOM", "LIFT", "CANTILEVER_PORTIONS",
                                                      "WATER_TANK", "PARAPETS", "BOUNDARY_WALL", "GB_PERIMETER",
                                                      "LINTELS")]
    cols = ["FAMILY", "FLOOR", "MARK_OR_PART", "FREELANCER_M3", "URBAN_MEASURED_LOW_M3", "URBAN_MEASURED_BASE_M3",
            "URBAN_MEASURED_HIGH_M3", "URBAN_CONDITIONAL_HIGH_M3", "CLASS"]
    heads = ["Family", "Floor", "Part", "FL m3", "U low", "U base", "U high", "U cond. high", "Class"]
    fam = P["fam"]
    return "\n".join([
        "# 08 Stairs, domes, pool and specials (investigations E + F)",
        "",
        "## Stairs",
        "",
        table(st, cols, heads),
        "",
        "There are four drawn stairs (S8.7):",
        "",
        "- **ST-A main stair:** GF -> 1F -> 2F; two flights, a winder turn and a half-landing per storey.",
        "- **ST-B lobby steps:** 4 risers, +1.00 -> +0.30.",
        "- **ST-C light-well stair:** curved flight, straight flight, corner landing, short flight.",
        "- **ST-D entrance steps:** 5 risers, +0.15 -> +1.00.",
        "",
        "How the freelancer's rows map:",
        "",
        "- its main stair (4 flights x 5.3 m + 3 landings) is ST-A;",
        "- its 'entrance stair' is ST-D;",
        "- its 'stair 2' (16.4 m x 1.2 m) is ST-C;",
        "- ST-B has no row.",
        "",
        "Every freelancer row uses a 0.28 m 'steps + waist slab' equivalent over the plan length.",
        "",
        f"Urban integrates each drawn flight, winder and landing at the waist range: {fam['STAIRS']['MEAS_LOW']:.2f} "
        f"- {fam['STAIRS']['MEAS_HIGH']:.2f} m3, base {fam['STAIRS']['MEAS_BASE']:.2f}. The waist is not printed "
        "(p.16 'THICK' has no value), so it is RFI-M5-06. The GF -> 1F riser arrangements of S8.7A-C stay research "
        "only; none is an approved quantity.",
        "",
        "## Domes",
        "",
        table(dm, cols, heads),
        "",
        "**Different components, near-equal totals.** The numeric closeness is not agreement.",
        "",
        "- **The freelancer** prices three shells of 22.6 m2 x 0.10, about a hemisphere on the 1.90 m rise.",
        "- **Urban** measures the two drawn domes as spherical caps (printed 4.42 m chord, 1.90 m rise, 0.10 thick: "
        "S8.3) and their ring beams (depth 'AS PER ARCH': range).",
        "- **Held as UNRESOLVED by Urban:**",
        "  - the tower dome (architecture only);",
        "  - the 1.30 m drums.",
        "",
        "## Pool, lift, specials",
        "",
        table(pl, cols, heads),
        "",
        "- **Pool:**",
        "  - the base matches;",
        "  - the walls differ by height, because the floor profile is a PROFILE_CONFLICT between the architectural "
        "flat floor and the structural deep end / slope;",
        "  - the steps and the pump room are not drawn on any sheet (S8.2 source search), so they are UNRESOLVED and "
        "never assumed absent;",
        "  - the curved ground beam around the pool (R 2250 +) is a separate element from the pool wall (R 1550 / "
        "1750, 500 mm gap; S8.2A) and is counted once.",
        "- **Lift:**",
        "  - the four 200 mm pit walls (S8.8) are the freelancer's 'lift walls';",
        "  - Urban measures the drawn pieces to the founding range;",
        "  - the GF tie beam and the overrun are not drawn;",
        "  - the lift footing FF is a footing (07).",
        "- **Water tank:**",
        "  - the roof slabs are in the 2F slabs (D-01);",
        "  - the base and walls are not drawn.",
        "- **Cantilever portions:** the hatched bands of S9A, at the adjacent slab thickness, CONDITIONAL (D-04).",
        "- **Parapets:** architecture only.",
        "",
        "Figures: `visual/05_STAIRS_DOMES.svg`, `visual/06_POOL_SPECIAL_SCOPE.svg`.",
        "",
    ]) + "\n"


def doc09(P):
    bo = P["blind_overlap"]
    rows = P["blind_rows"]
    return "\n".join([
        "# 09 Blinding (plain concrete, investigation G)",
        "",
        "**Plain concrete is never added to RC.** Every option below is plain concrete only.",
        "",
        table(rows, ["OPTION", "AREA_M2", "M3", "BASIS", "STATUS"], ["Option", "m2", "m3", "Basis", "Status"]),
        "",
        "The p.13 typical details draw a 10 cm plain-concrete layer, with a 10 cm projection, under:",
        "",
        "- both footing details;",
        "- every typical ground-beam section.",
        "",
        "**Overlaps counted once:**",
        "",
        f"- footing layer {bo['footings_m2']:.2f} m2;",
        f"- beam strips {bo['beams_m2']:.2f} m2;",
        f"- beam strip on footing layer {bo['footing_beam_overlap_m2']:.2f} m2;",
        f"- strip on strip {bo['strip_strip_m2']:.2f} m2;",
        f"- footing on footing {bo['footing_footing_m2']:.2f} m2.",
        "",
        f"The union of the placed outlines is {bo['placed_union_m2']:.2f} m2 (registration {bo['state']}, "
        f"{bo['matched']} footings matched).",
        "",
        "**The freelancer's 47.055 m3 is the whole plot** (15.00 x 31.37 m, both printed on SH08) x 0.10, under "
        "court, garden and building alike. No sheet draws such a layer, so it is a CONDITIONAL alternative, if the "
        "specification asks for it.",
        "",
        "**The MCP figure (about 15.787 m3, stated in the brief)** is close to the footing layer alone. christiannp's "
        "A6 states the same rule; no file holds the quantity.",
        "",
        "These layer readings were made by machine and not reviewed by a person (M4 OCR P13N01 / P13N02).",
        "",
        "Map: `visual/07_BLINDING_OVERLAP.svg`.",
        "",
    ]) + "\n"


def doc15(P):
    ch = P["checks"]
    ok = sum(c["RESULT"] == "PASS" for c in ch)
    return "\n".join([
        "# 15 Independent validation",
        "",
        f"**{ok} / {len(ch)} checks pass.**",
        "",
        "The checks combine:",
        "",
        "- a second geometric method (shapely on the M4 polygons);",
        "- direct reads of the DXF with ezdxf (boundary wall, plot frame, dome circles), independent of the engine's "
        "intake;",
        "- arithmetic recomputation of every freelancer row;",
        "- cross-source agreement;",
        "- conservation: every record in exactly one group and one lane, and the bridge closes.",
        "",
        "Code shared with the engine is disclosed per check.",
        "",
        table(ch, ["CHECK_ID", "WHAT", "METHOD", "VALUE", "EXPECTED", "RESULT", "SHARED_CODE"],
              ["Id", "What", "Method", "Value", "Expected", "Result", "Shared code"]),
        "",
        "**Not validated:**",
        "",
        "- **The stair, dome, pool and lift quantities** come from the frozen S-stage registers (through M1). They were "
        "checked there, not re-measured here.",
        "- **Arc-bounded slab faces** are skipped by IV-10, because their stored ring is a chord polygon.",
        "- **No person has confirmed** any machine-read printed value (16 cm default, blinding layer, p.13 classes).",
        "",
    ]) + "\n"


def doc17(P):
    n = P["numbers"]
    u = n["urban_m5"]
    fam = P["fam"]
    rfi = P["rfi"]
    return "\n".join([
        "# Notes for ChatGPT: what worked, what is not working, what to do next (M5)",
        "",
        "## What worked",
        "",
        "**Reproducing the four sources from their records.** The freelancer total comes from the 149 traced leaf "
        "rows; U-C4N and christiannp from their categories; M4 from its summary. Every brief figure is reproduced "
        "(IV-04, IV-05).",
        "",
        f"**Finding the real gap.** The brief's 40.39 m3 mixes {n['m4_plain_m3']:.2f} m3 of blinding into Urban's figure. "
        f"Like for like, Urban's drawing-supported RC is {u['MEAS_BASE']:.2f} m3 against the freelancer's "
        f"{n['freelancer_rc_m3']:.2f}, a gap of {n['freelancer_rc_m3'] - u['MEAS_BASE']:.2f} m3. Each part of that gap is "
        "located and classified (04).",
        "",
        "**An element crosswalk with nothing dropped.** Every freelancer row and Urban item sits in exactly one group "
        "(IV-07). Beams compare per floor and mark; footings and columns per mark; stairs per stair; domes and the "
        "pool per component.",
        "",
        "**Exact geometric crosswalks between registers**, through the sheet origins:",
        "",
        "- the S8.1A regions decompose M4's lift / lobby cell exactly;",
        "- the dome circles (S-BOUN) locate the ring arcs and the dome opening;",
        "- the S9A hatches locate the cantilever portions.",
        "",
        "**One real engine defect, fixed.** Planted columns labelled on slab plans were missed. The fix is gated in V4 "
        "and changes nothing else (IV-19).",
        "",
        "## What is not working / not done",
        "",
        "**Sources not in this environment.** The freelancer's original workbook and both sealed MCP reports are "
        "missing. U-C4N is only comparable at category level.",
        "",
        "**Engine behaviour left as it is, because it is fail-safe:**",
        "",
        "- the dome's radial lines read as winders;",
        "- the dome ring arcs bound to B4;",
        "- the pit outlines not used as face edges.",
        "",
        "These are corrected by M5 ownership decisions for this project only (no generic rule). A generic rule "
        "needs a held-out set with domes and spiral stairs.",
        "",
        "**Stairs, domes, pool and lift come from the frozen S-stages.** The generic route does not measure them yet.",
        "",
        f"**The quotation is not ready.** The beam depth reading alone swings "
        f"{fam['BEAMS']['MEAS_HIGH'] - fam['BEAMS']['MEAS_BASE']:.2f} m3. Five element types have no drawing.",
        "",
        "## Recommended next steps (in order)",
        "",
        "1. **Get the minimum answers** (13): " + ", ".join(r["RFI_ID"] for r in rfi[:6]) + ".",
        "   - The person review loop (M4 next step 1) turns each answer into MANUALLY_CONFIRMED.",
        "2. **Upload the freelancer's original workbook and both MCP reports**, then rebuild 03 against their item "
        "tables.",
        "3. **Bring stairs, domes, pool and lift into the generic route** (S8.x engines as modules), so that one run "
        "measures the whole RC scope.",
        "4. **A held-out synthetic set with domes, spiral stairs and lift pits**, before any generic rule for E-02 to "
        "E-04.",
        "5. **Quote on provisional quantities with a variation mechanism:**",
        f"   - measured {u['MEAS_BASE']:.2f} m3;",
        f"   - conditional allowances {u['COND_LOW']:.2f} - {u['COND_HIGH']:.2f} m3;",
        "   - exclusions for the undrawn items;",
        "   - blinding as its own line.",
        "",
    ]) + "\n"
