"""M5 comparison tables: the element-by-element crosswalk (03 + membership), the family totals of the four sources
(02), and the freelancer -> Urban bridge (04). RECONCILIATION phase: explains differences, chooses nothing."""

from __future__ import annotations

from collections import defaultdict

import m5_reconcile as M

COUNTED = "KEEP"


def contrib(u):
    """How one Urban item enters the reference: measured (low / base / high), conditional (low / high) or neither."""
    out = {"ML": 0.0, "MB": 0.0, "MH": 0.0, "CL": 0.0, "CH": 0.0, "STATE": u["M5"]}
    st = u["M5"]
    if st in ("EXCLUDED_SAME_AS_M4", "REALLOCATED_TO_DOMES", "NOT_SLAB_DOME_OPENING", "SUPERSEDED_BY_CANTILEVER"):
        out["STATE"] = "EXCLUDED (" + st + ")"
        return out
    if u["CATEGORY"] == "PROVISIONAL" and st == COUNTED:
        out.update(ML=u["LOW"] or 0.0, MB=u["BASE"] or 0.0, MH=u["HIGH"] or 0.0, STATE="MEASURED")
    elif st == "CONDITIONAL_DECOMPOSED":
        t = (u["DIMS"] or {}).get("t_m") or 0.0
        out.update(CL=u.get("M5_SLAB_M2", 0.0) * t, CH=u.get("M5_SLAB_HIGH_M2", 0.0) * t, STATE="CONDITIONAL")
    elif u["CATEGORY"] == "PROVISIONAL" and st == "CONDITIONAL":
        out.update(CL=u["LOW"] or 0.0, CH=u["HIGH"] or 0.0, STATE="CONDITIONAL")
    elif u["EXP_HIGH"] is not None:
        out.update(CL=u["EXP_LOW"] or 0.0, CH=u["EXP_HIGH"] or 0.0, STATE="CONDITIONAL")
    else:
        out["STATE"] = "UNMEASURABLE"
    return out


# ------------------------------------------------------------------ crosswalk keys
STAIR_OF_FL = {("STAIRS_AND_DOME", 20): "ST-A", ("STAIRS_AND_DOME", 21): "ST-A", ("STAIRS_AND_DOME", 11): "ST-D",
               ("STAIRS_AND_DOME", 12): "ST-C"}
POOL_OF_FL = {11: "BASE", 12: "WALLS", 14: "STEPS", 13: "PUMP_ROOM", 15: "PUMP_ROOM"}


def fl_key(r):
    f, fl, mk = r["FAMILY"], r["FLOOR"], r["MARK"]
    if f in ("FOOTINGS",):
        return ("FOOTINGS", "FOUNDATION", "F+F10" if mk in ("F", "F10") else mk)
    if f in ("STRAPS", "NECKS"):
        return (f, "FOUNDATION", mk)
    if f == "COLUMNS" and mk.startswith("PC"):
        return ("COLUMNS", fl, "P.C")
    if f in ("COLUMNS", "BEAMS"):
        return (f, fl, mk)
    if f == "SLABS":
        return ("SLABS", fl, f"t {r['D']:.2f}")
    if f == "STAIRS":
        return ("STAIRS", "ALL", STAIR_OF_FL.get((r["CATEGORY"], r["ROW"]), "UNMAPPED"))
    if f == "DOMES":
        return ("DOMES", "ROOF", "SHELLS")
    if f in ("POOL", "POOL_PUMP_ROOM"):
        return ("POOL" if f == "POOL" else "POOL_PUMP_ROOM", "GROUND", POOL_OF_FL.get(r["ROW"], "OTHER"))
    if f == "GROUND_BEAMS":
        return ("GROUND_BEAMS", "GROUND", "NETWORK")
    if f == "GROUND_SLAB":
        return ("GROUND_SLAB", "GROUND", "SLAB_ON_GRADE")
    if f == "LIFT":
        return ("LIFT", "FOUNDATION", "PIT_WALLS")
    if f == "BOUNDARY_WALL":
        return ("BOUNDARY_WALL", "SITE", "BEAM")
    if f == "GB_PERIMETER":
        return ("GB_PERIMETER", "GROUND", "PERIMETER")
    if f == "BLINDING":
        return ("BLINDING", "FOUNDATION", "PLAIN")
    return (f, fl, mk or "ALL")


def ur_key(u):
    f, fl, mk = u["FAMILY"], u["FLOOR"], u["MARK"]
    if f == "FOOTINGS":
        return ("FOOTINGS", "FOUNDATION", "F+F10" if mk in ("F", "F10", "F/F10") else mk)
    if f in ("STRAPS", "NECKS"):
        return (f, "FOUNDATION", mk or "UNMARKED")
    if f == "COLUMNS":
        return ("COLUMNS", fl, mk or "UNMARKED")
    if f == "BEAMS":
        return ("BEAMS", fl, mk or "UNLABELLED")
    if f == "SLABS":
        t = (u["DIMS"] or {}).get("t_m") if isinstance(u["DIMS"], dict) else None
        return ("SLABS", fl, f"t {t:.2f}" if t else "STAIR_OR_UNRESOLVED")
    if f == "STAIRS":
        return ("STAIRS", "ALL", "ST-" + mk.split("-")[0][0])
    if f == "DOMES":
        part = "SHELLS" if mk.endswith("-SHELL") and "TOWER" not in mk else \
            ("RINGS" if mk.endswith("-RING") else ("TOWER" if "TOWER" in mk else "DRUMS"))
        return ("DOMES", "ROOF", part)
    if f == "POOL":
        return ("POOL", "GROUND", "BASE" if "BASE" in mk else "WALLS")
    if f == "LIFT":
        return ("LIFT", "FOUNDATION", "PIT_WALLS" if "PIT-WALL" in mk else mk.replace("LIFT-01-", ""))
    if f == "GROUND_BEAMS":
        return ("GROUND_BEAMS", "GROUND", "NETWORK")
    if f == "GROUND_SLAB":
        return ("GROUND_SLAB", "GROUND", "SLAB_ON_GRADE")
    if f == "BLINDING":
        return ("BLINDING", "FOUNDATION", "PLAIN")
    if f == "BOUNDARY_WALL":
        return ("BOUNDARY_WALL", "SITE", "BEAM")
    return (f, fl, mk or "ALL")


def _dims_text(rows):
    out = []
    for r in rows:
        dims = "x".join(f"{x:g}" for x in (r["B"], r["C"], r["D"]) if isinstance(x, (int, float)))
        cnt = r["COUNT"] if r["COUNT"] not in (None, 1) else ""
        out.append(f"{r['FL_ID']} {r['DESCRIPTION']} {cnt + ' x ' if isinstance(cnt, str) and cnt else ''}"
                   f"{(str(cnt) + ' x ') if isinstance(cnt, (int, float)) else ''}{dims} = {r['VALUE_M3']:.3f}")
    return "; ".join(out)


def _fl_len(rows, idx="D"):
    return sum((r["COUNT"] if isinstance(r["COUNT"], (int, float)) else 1) * (r[idx] or 0) for r in rows)


def _ur_len(us):
    out = 0.0
    for u in us:
        d = u["DIMS"] if isinstance(u["DIMS"], dict) else {}
        out += d.get("length_m") or d.get("clear_length_m") or 0.0
    return out


# ------------------------------------------------------------------ explanation rules per family
def explain(key, fr, us, c, ctx):
    """(class, explanation, treatment, confidence, release) for one crosswalk group."""
    fam, floor, mk = key
    fl = sum(r["VALUE_M3"] for r in fr)
    ub = c["MB"]
    has_exp = c["CH"] > 0
    base = M.classify(fl, ub, has_exp)
    if fam == "GB_PERIMETER":
        return ("SOURCE_CONFLICT", "No 20 cm perimeter beam is drawn: every ground beam on SH08 is a 300 mm band "
                "and the p.13 exterior detail is 30 x FOLLOW ARCH. The freelancer's 211 m of 30 x 60 already runs "
                "the whole network including the exterior lines (Urban network 194.3 m net / ~199 m gross), so this "
                "row repeats the perimeter (likely double count) or prices a beam no plan shows. Its 20 x 60 equals "
                "the unbound schedule row B.W (boundary wall beam); p.1 note B (neighbour-side upper + lower beam) is "
                "a CANDIDATE reading.", "not in the measured base; RFI (neighbour-side note B / B.W row)",
                "MEDIUM", "NOT_RELEASED")
    if fam == "BOUNDARY_WALL":
        return ("SCOPE_DIFFERENCE", "Boundary wall: the GB plan draws its run on layer S-BOUN (centreline "
                f"{ctx['boundary']['length_m']:.2f} m by ezdxf); p.14 prints a typical (GB "
                f"{ctx['boundary']['gb_w'] * 100:.0f} x {ctx['boundary']['gb_h'] * 100:.0f}, pads, columns) that "
                "conflicts with schedule row B.W; pad / column spacing not printed. The freelancer prices the beam "
                "only, at 30 x 60.", "CONDITIONAL allowance (beam at p.14 typical .. B.W row); pads and columns "
                "UNRESOLVED; confirm whether the boundary wall is in the contract", "MEDIUM", "CONDITIONAL")
    if fam == "GROUND_SLAB":
        return ("SCOPE_DIFFERENCE + BEAM_SLAB_OVERLAP + MISSING_IN_URBAN_BASE", "The freelancer's 295.5 m2 is a "
                "gross plate that includes the ground-beam and column footprints (the beams are already measured "
                "full depth) and the two cells Urban holds unresolved; see 05 for the area bridge.",
                "measured cells in the base; the lift / stair cell split by S8.1A as CONDITIONAL; RFI on the T=10 "
                "cm note scope", "HIGH", "PARTLY_MEASURED")
    if fam == "GROUND_BEAMS":
        return ("THICKNESS_OR_DEPTH_DIFFERENCE + GEOMETRY_DIFFERENCE", "Same physical network (three independent "
                "extractions: Urban, christiannp, U-C4N within 3 %). The freelancer applies 30 x 60 to every run "
                "and 211 m of length; Urban uses the printed p.13 classes (30 x 30 / 30 x 40 / 30 x 60) by span and "
                "the FOLLOW ARCH exterior bracket, net of columns. See 05.", "measured (class depths); RFI-A05 "
                "length basis and exterior depth", "HIGH", "MEASURED_PROVISIONAL")
    if fam == "POOL_PUMP_ROOM":
        return ("SCOPE_DIFFERENCE", "No pump room is drawn on any structural or architectural sheet (S8.2 source "
                "search p.3, p.7, architectural GF). A pool needs plant space somewhere, so it is not assumed "
                "absent: it is UNRESOLVED with no measurable geometry.", "RFI: location and structure of the pool "
                "plant room; not in the base", "MEDIUM", "UNRESOLVED")
    if fam == "POOL" and mk == "STEPS":
        return ("SCOPE_DIFFERENCE", "No pool step or bench is drawn (S8.2 PL-STEPS NOT_SHOWN).",
                "not in the base; covered by the pool RFI", "MEDIUM", "UNRESOLVED")
    if fam == "POOL" and mk == "BASE":
        return (base or "GEOMETRY_DIFFERENCE", "Same base: the drawn structural footprint x the stated 40 cm (S8.2); "
                "the slope between the deep and shallow ends is ignored on both sides.", "measured", "HIGH",
                "MEASURED_PROVISIONAL")
    if fam == "POOL" and mk == "WALLS":
        return ("HEIGHT_OR_LEVEL_DIFFERENCE", "Wall plan bands agree in kind; the freelancer takes 12 m x 1.8 m "
                "high, Urban the drawn 200 mm bands x the height above the base. The pool floor profile is a "
                "PROFILE_CONFLICT (architectural flat floor vs structural deep end / slope / shallow end).",
                "measured with the S8.2A depth range; RFI on the pool depth", "MEDIUM", "MEASURED_PROVISIONAL")
    if fam == "DOMES":
        if mk == "SHELLS":
            return ("GEOMETRY_DIFFERENCE + SCOPE_DIFFERENCE", "The freelancer prices three shells of 22.6 m2 x 0.10 "
                    "(22.6 is close to 2 pi x 1.9^2, a hemisphere on the 1.90 m rise); Urban measures the two drawn "
                    "domes A and B as spherical caps on the printed 4.42 m chord and 1.90 m rise (S8.3), and holds "
                    "the tower dome as UNRESOLVED (architecture only).", "shells measured; tower dome conditional",
                    "HIGH", "MEASURED_PROVISIONAL")
        if mk == "TOWER":
            return ("UNRESOLVED_REQUIRES_ENGINEER", "Tower dome: drawn in the architecture only, no structural shell "
                    "(S8.3); held as an exposure, never assumed absent.", "CONDITIONAL; RFI-M5-07", "LOW",
                    "CONDITIONAL")
        if mk == "DRUMS":
            return ("UNRESOLVED_REQUIRES_ENGINEER", "The architecture draws a 1.30 m drum under each dome; whether it "
                    "is the RC ring itself or a wall under it is not stated (S8.3).", "UNRESOLVED; RFI-M5-07", "LOW",
                    "UNRESOLVED")
        if mk == "RINGS":
            return ("MISSING_IN_FREELANCER", "Ring beams under both domes (S8.3); depth 'AS PER ARCH' gives the "
                    "range. The arcs of ring A that M4 bound to B4 are moved here (D-02).", "measured base with "
                    "range; RFI on the ring depth", "MEDIUM", "MEASURED_PROVISIONAL")
    if fam == "STAIRS":
        if mk == "ST-B":
            return ("MISSING_IN_FREELANCER", "Lobby steps (4 risers +1.00 -> +0.30) found by S8.7 inside the "
                    "S8.1A bay; no freelancer row.", "measured with the waist range", "MEDIUM", "MEASURED_PROVISIONAL")
        return ("ASSUMPTION_DIFFERENCE", "The freelancer multiplies plan length x width by a 0.28 m 'steps + "
                "waist' equivalent; Urban integrates the drawn flights, winders and landings at the waist range "
                "(S8.7 / S8.7C), and keeps riser-count scenarios as research, never as an approved quantity.",
                "measured with the waist range; RFI on waist and riser arrangement", "MEDIUM",
                "MEASURED_PROVISIONAL")
    if fam == "LIFT":
        return (base or "GEOMETRY_DIFFERENCE", "Same pit walls (200 mm). The freelancer takes 8 m x 1.5 m; S8.8 "
                "measures the four drawn wall pieces between the lift columns, from the FF top to the GF level "
                "with the founding range.", "measured with the founding range", "HIGH", "MEASURED_PROVISIONAL")
    if fam == "LINTELS":
        return ("MISSING_IN_FREELANCER", "Cast lintels over masonry openings (p.13 lintel schedule) are not in the "
                "freelancer's RC; 46 openings under a beam stay UNRESOLVED (lintel only if the head is below the "
                "soffit).", "measured (openings not under a beam); conditional for the rest", "MEDIUM",
                "MEASURED_PROVISIONAL")
    if fam == "CANTILEVER_PORTIONS":
        return ("MISSING_IN_FREELANCER", "Hatched cantilever portions (S9A legend match); thickness not printed, "
                "valued at the adjacent slab thickness.", "CONDITIONAL; RFI-A08", "MEDIUM", "CONDITIONAL")
    if fam in ("WATER_TANK", "PARAPETS"):
        return ("UNRESOLVED_REQUIRES_ENGINEER", "Not drawn as structure (architecture only / not in source); no "
                "freelancer row either.", "UNRESOLVED; RFI", "LOW", "UNRESOLVED")
    if fam == "BLINDING":
        return ("SCOPE_DIFFERENCE (NOT RC)", "Plain concrete, never mixed with RC. The freelancer takes the full "
                "plot 15.00 x 31.37 m (both printed on SH08) x 0.10; Urban the drawn layer under footings and "
                "ground beams (10 cm, 10 cm projection, p.13), overlaps counted once. See 09.",
                "separate line; alternatives priced in 12", "HIGH", "MEASURED_PROVISIONAL")
    if fam == "NECKS":
        return (base or "HEIGHT_OR_LEVEL_DIFFERENCE", "Neck height: the freelancer uses 1.50 m; Urban runs the "
                "neck from the footing top to the GF level +1.00 with the founding level at the printed minimum "
                "1.50 m below plot level (range to 2.00 m, RFI-A03).", "measured with the founding range",
                "MEDIUM", "MEASURED_PROVISIONAL")
    if fam == "COLUMNS":
        if base:
            why = {"MATCHED_WITHIN_TOLERANCE": "same population and section",
                   "MISSING_IN_FREELANCER": "column occurrence drawn and scheduled for this storey (column plan and "
                                            "the storey's slab plan); no freelancer row for it",
                   }.get(base.split(" ")[0], "no Urban column of this mark on this storey; check the floor's "
                                             "unresolved columns (CN type not in the schedule)")
            return (base, why, "measured" if c["MB"] else "conditional / RFI", "MEDIUM", "MEASURED_PROVISIONAL")
        return ("HEIGHT_OR_LEVEL_DIFFERENCE", "Column height basis: the freelancer takes the clear height under "
                "the beams (3.75 m GF, 3.45 m 1F / 2F) because its beams are measured gross through the joints; "
                "Urban takes floor to floor (4.50 / 4.20 / 4.20) and measures beams net of the columns. Compare "
                "the allocation-free frame per floor (07).", "measured", "HIGH", "MEASURED_PROVISIONAL")
    if fam == "BEAMS":
        if mk == "UNLABELLED":
            return ("MISSING_IN_URBAN_BASE (held as unresolved exposure)" if fr else "UNRESOLVED_REQUIRES_ENGINEER",
                    "Drawn spans no tag binds (or an AMBIGUOUS tag, e.g. CB10 on 1F); M4 holds them with the "
                    "neighbour section as exposure (alignment alone never carries a section).", "CONDITIONAL; "
                    "RFI-M4-03", "MEDIUM", "CONDITIONAL")
        if base:
            why = {"MATCHED_WITHIN_TOLERANCE": "same length and section on both sides",
                   "MISSING_IN_FREELANCER": "drawn band bound to this tag on the slab sheet; no freelancer row for "
                                            "this mark on this floor",
                   }.get(base.split(" ")[0],
                         "no M4 span is bound to this mark on this floor: its tags are AMBIGUOUS between bands of "
                         "other widths (e.g. CB10 on the 1F sheet, two tags between a 200 and a 300 band), so the "
                         "spans sit in the floor's unlabelled-span exposure (UNLABELLED row)")
            return (base, why, "measured" if c["MB"] else "conditional / RFI-M5-04", "MEDIUM",
                    "MEASURED_PROVISIONAL" if c["MB"] else "CONDITIONAL")
        fl_l, ur_l = _fl_len(fr), _ur_len(us)
        fb = {(r["B"], r["C"]) for r in fr}
        ub = {((u["DIMS"] or {}).get("width_m"), (u["DIMS"] or {}).get("depth_m")) for u in us
              if isinstance(u["DIMS"], dict)}
        why = f"length {fl_l:.2f} m (freelancer) vs {ur_l:.2f} m (Urban, net of columns)"
        cls = "GEOMETRY_DIFFERENCE"
        if fb and ub and not fb & ub and {b[1] for b in fb} != {b[1] for b in ub}:
            cls = "THICKNESS_OR_DEPTH_DIFFERENCE"
            why += f"; section {sorted(fb)} vs {sorted(ub)}"
        return (cls, why + ". The freelancer measures gross depth through the joints (same depth reading as M4 "
                "base); length differences come from c/c vs net-of-column lengths and from spans counted on one "
                "side only.", "measured", "MEDIUM", "MEASURED_PROVISIONAL")
    if fam == "FOOTINGS":
        if base:
            return (base, "same schedule dimensions and count" if base.startswith("MATCHED") else
                    "outline drawn on the foundation plan; see 07", "measured", "HIGH", "MEASURED_PROVISIONAL")
        nf = sum((r["COUNT"] if isinstance(r["COUNT"], (int, float)) else 1) for r in fr)
        return ("GEOMETRY_DIFFERENCE", f"population: {nf} in the freelancer vs {len(us)} drawn outlines in Urban "
                "(same schedule size)" + ("; the FN outline overlapping F9 is deducted by Urban" if mk == "FN"
                                          else ""), "measured", "HIGH", "MEASURED_PROVISIONAL")
    if fam == "STRAPS":
        return (base or "GEOMETRY_DIFFERENCE", "Strap length: Urban measures the drawn faces clear of the footings "
                "(the footing owns its prism); the freelancer types its own length. SB2 has two schedule rows "
                "(1.0 / 0.8 wide): Urban takes the drawn width, the other row is the range.", "measured", "HIGH",
                "MEASURED_PROVISIONAL")
    if fam == "SLABS":
        return (base or "GEOMETRY_DIFFERENCE", "Net slab panels stop at the beam faces on both sides (beams gross "
                "depth); small area differences per floor. See 06.", "measured", "HIGH", "MEASURED_PROVISIONAL")
    return (base or "ASSUMPTION_DIFFERENCE", f"freelancer {fl:.3f} m3 vs Urban measured {ub:.3f} m3 (conditional up "
            f"to {c['CH']:.3f}); see the family audit", "", "MEDIUM", "")


def elements(F, U, ctx, rate):
    """One row per crosswalk group (family, floor, mark), and the membership of every record."""
    groups = defaultdict(lambda: {"fl": [], "ur": []})
    for r in F["rows"]:
        if r["VALUE_M3"] or r["RECOMPUTED_M3"]:
            groups[fl_key(r)]["fl"].append(r)
    for u in U:
        groups[ur_key(u)]["ur"].append(u)
    rows, members = [], []
    order = {f: i for i, f in enumerate(M.FAMILY_ORDER + ("BLINDING",))}
    for n, key in enumerate(sorted(groups, key=lambda k: (order.get(k[0], 99), k[1], k[2])), 1):
        fr, us = groups[key]["fl"], groups[key]["ur"]
        c = {"ML": 0.0, "MB": 0.0, "MH": 0.0, "CL": 0.0, "CH": 0.0}
        states = defaultdict(int)
        for u in us:
            cu = contrib(u)
            for k in c:
                c[k] += cu[k]
            states[cu["STATE"]] += 1
        fl = sum(r["VALUE_M3"] for r in fr)
        cls, why, treat, conf, rel = explain(key, fr, us, c, ctx)
        eid = f"M5-{key[0]}-{key[1]}-{key[2]}".replace(" ", "").replace("/", "_")
        loc = sorted({(u["SOURCE"].split(" ")[1] if u["ORIGIN"] == "M4" and " SH" in u["SOURCE"] else
                       u["ORIGIN"]) for u in us})
        rows.append({"ELEMENT_ID": eid, "FAMILY": key[0], "FLOOR": key[1], "MARK_OR_PART": key[2],
                     "N_FREELANCER_ROWS": len(fr), "N_URBAN_ITEMS": len(us),
                     "URBAN_STATES": "; ".join(f"{k} {v}" for k, v in sorted(states.items())),
                     "FREELANCER_M3": M.r6(fl), "URBAN_MEASURED_LOW_M3": M.r6(c["ML"]),
                     "URBAN_MEASURED_BASE_M3": M.r6(c["MB"]), "URBAN_MEASURED_HIGH_M3": M.r6(c["MH"]),
                     "URBAN_CONDITIONAL_LOW_M3": M.r6(c["CL"]), "URBAN_CONDITIONAL_HIGH_M3": M.r6(c["CH"]),
                     "UC4N_M3": "NOT_HELD (category level only; see TOT rows)",
                     "CHRISTIANNP_M3": "NOT_HELD (category level only; see TOT rows)",
                     "DIFF_FREELANCER_MINUS_URBAN_BASE_M3": M.r6(fl - c["MB"]),
                     "COST_KWD": M.kwd(fl - c["MB"], rate), "CLASS": cls, "EXPLANATION": why,
                     "FREELANCER_DETAIL": _dims_text(fr), "URBAN_LOCATION": ", ".join(loc),
                     "TREATMENT": treat, "CONFIDENCE": conf, "RELEASE_STATUS": rel})
        for r in fr:
            members.append({"ELEMENT_ID": eid, "SOURCE": "FREELANCER (S3.1 lineage, derived)", "RECORD_ID": r["FL_ID"],
                            "FAMILY": r["FAMILY"], "FLOOR": r["FLOOR"], "MARK": r["MARK"],
                            "DESCRIPTION": r["DESCRIPTION"], "STATE": "PRICED", "LOW_M3": "",
                            "BASE_M3": M.r6(r["VALUE_M3"]), "HIGH_M3": "", "EXPOSURE_LOW_M3": "",
                            "EXPOSURE_HIGH_M3": "", "LOCATION": f"worksheet {r['WORKSHEET']} cell {r['CELL']}",
                            "M5_NOTE": ""})
        for u in us:
            cu = contrib(u)
            members.append({"ELEMENT_ID": eid, "SOURCE": "URBAN " + u["ORIGIN"], "RECORD_ID": u["UID"],
                            "FAMILY": u["FAMILY"], "FLOOR": u["FLOOR"], "MARK": u["MARK"],
                            "DESCRIPTION": (u["FORMULA"] or u["BLOCKER"])[:120], "STATE": cu["STATE"],
                            "LOW_M3": M.r6(u["LOW"]), "BASE_M3": M.r6(u["BASE"]), "HIGH_M3": M.r6(u["HIGH"]),
                            "EXPOSURE_LOW_M3": M.r6(u["EXP_LOW"]), "EXPOSURE_HIGH_M3": M.r6(u["EXP_HIGH"]),
                            "LOCATION": S_loc(u), "M5_NOTE": u.get("M5_NOTE", "")})
    return rows, members


def S_loc(u):
    s = u["SOURCE"] or ""
    if u["ORIGIN"] == "M4":
        s = s.split(".dxf ", 1)[-1]
    return s[:160]


# ------------------------------------------------------------------ family totals: four sources + the Urban reference
def family_totals(F, U, MC, fam):
    """Family totals of every source on the M5 canonical families (RC; blinding kept apart)."""
    fl = defaultdict(float)
    for r in F["rows"]:
        fl[r["FAMILY"]] += r["VALUE_M3"]
    m4 = defaultdict(float)
    for u in U:
        if u["ORIGIN"] == "M4" and u["CATEGORY"] == "PROVISIONAL":
            m4[u["FAMILY"]] += u["BASE"] or 0.0
    mcp = {"UC4N": defaultdict(lambda: None), "CHRISTIANNP": defaultdict(lambda: None)}
    pick = {("FOUNDATIONS", None): "FOOTINGS", ("STRAP_BEAMS", None): "STRAPS", ("GROUND_BEAMS", None): "GROUND_BEAMS",
            ("GROUND_SLAB", None): "GROUND_SLAB", ("COLUMNS_NECKS", "FOUNDATION"): "NECKS",
            ("COLUMNS_NECKS", "GF"): "COLUMNS", ("COLUMNS_NECKS", "1F"): "COLUMNS", ("COLUMNS_NECKS", "2F"): "COLUMNS",
            ("BEAMS", "all floors"): "BEAMS", ("SLABS", "all floors"): "SLABS", ("STAIRS", None): "STAIRS",
            ("DOME", None): "DOMES", ("POOL", None): "POOL"}
    for r in MC["rows"]:
        k = (r["category"], r["subcategory"] if r["category"] in ("COLUMNS_NECKS", "BEAMS", "SLABS") else None)
        fam_ = pick.get(k)
        if not fam_:
            continue
        for src in ("UC4N", "CHRISTIANNP"):
            v = r[src]
            if v is not None:
                mcp[src][fam_] = (mcp[src][fam_] or 0.0) + v
    rows = []
    for f in M.FAMILY_ORDER + ("BLINDING",):
        R = fam.get(f, {})
        rows.append({"FAMILY": f, "TITLE": M.FAMILY_TITLE.get(f, f), "RC": "NO" if f == "BLINDING" else "YES",
                     "FREELANCER_M3": M.r6(fl.get(f, 0.0)), "URBAN_M4_BASE_M3": M.r6(m4.get(f, 0.0)),
                     "URBAN_M5_MEASURED_LOW_M3": M.r6(R.get("MEAS_LOW", 0.0)),
                     "URBAN_M5_MEASURED_BASE_M3": M.r6(R.get("MEAS_BASE", 0.0)),
                     "URBAN_M5_MEASURED_HIGH_M3": M.r6(R.get("MEAS_HIGH", 0.0)),
                     "URBAN_M5_CONDITIONAL_LOW_M3": M.r6(R.get("COND_LOW", 0.0)),
                     "URBAN_M5_CONDITIONAL_HIGH_M3": M.r6(R.get("COND_HIGH", 0.0)),
                     "URBAN_N_UNMEASURABLE": R.get("N_UNMEASURABLE", 0),
                     "UC4N_M3": M.r6(mcp["UC4N"][f]) if mcp["UC4N"][f] is not None else "NOT_IN_SOURCE",
                     "CHRISTIANNP_M3": M.r6(mcp["CHRISTIANNP"][f]) if mcp["CHRISTIANNP"][f] is not None
                     else "NOT_IN_SOURCE"})
    return rows


# ------------------------------------------------------------------ freelancer -> Urban bridge (waterfall)
def gb_split(U):
    """M4 ground-beam spans (not straps): exterior (architectural exterior wall) vs interior; length, width, base."""
    out = {"EXT": [0.0, 0.0, set()], "INT": [0.0, 0.0, set()]}
    for u in U:
        if u["ORIGIN"] != "M4" or u["FAMILY"] != "GROUND_BEAMS" or u["CATEGORY"] != "PROVISIONAL":
            continue
        d = u["DIMS"]
        k = "EXT" if d.get("arch_class") == "EXTERIOR_WALL" else "INT"
        out[k][0] += d.get("length_m") or 0.0
        out[k][1] += u["BASE"] or 0.0
        out[k][2].add(d.get("width_m"))
    return out


def bridge(F, U, fam, gs, rate):
    """Ordered steps from the freelancer RC total to the Urban M5 measured base. Each step = Urban - freelancer."""
    fl = defaultdict(float)
    for r in F["rows"]:
        fl[r["FAMILY"]] += r["VALUE_M3"]
    flrow = {(r["CATEGORY"], r["ROW"]): r for r in F["rows"]}
    meas = {f: fam[f]["MEAS_BASE"] for f in fam}
    steps, raw = [], []

    def step(group, sid, title, value, cls, evidence, status):
        raw.append(value)
        steps.append({"STEP_GROUP": group, "STEP_ID": sid, "STEP": title, "M3": M.r6(value),
                      "KWD": M.kwd(value, rate), "CLASS": cls, "EVIDENCE": evidence, "STATUS": status})

    start = F["total_rc"]
    pump = fl["POOL_PUMP_ROOM"]
    steps_r = flrow.get(("SWIMMING_POOL", 14))
    step("A scope / not drawn", "B01", "Boundary-wall ground beam (freelancer 42 m x 30 x 60)",
         -fl["BOUNDARY_WALL"], "SCOPE_DIFFERENCE", "S-BOUN run on SH08 (boundary wall); p.14 typical; outside the "
         "building structure; Urban keeps a CONDITIONAL allowance (10)", "CONDITIONAL in Urban")
    step("A scope / not drawn", "B02", "Perimeter tie beam (freelancer 71.7 m x 20 x 60)", -fl["GB_PERIMETER"],
         "SOURCE_CONFLICT (likely DOUBLE_COUNTED)", "no 200 mm perimeter band on SH08; the 211 m of 30 x 60 "
         "already covers the exterior lines; section = unbound schedule row B.W", "RFI (note B / B.W)")
    step("A scope / not drawn", "B03", "Pool pump room walls and floor", -pump, "SCOPE_DIFFERENCE (not drawn)",
         "S8.2 PL-PUMP-ROOM NOT_SHOWN on p.3, p.7, architectural GF", "UNRESOLVED (RFI)")
    if steps_r:
        step("A scope / not drawn", "B04", "Pool steps", -steps_r["VALUE_M3"], "SCOPE_DIFFERENCE (not drawn)",
             "S8.2 PL-STEPS NOT_SHOWN", "UNRESOLVED (RFI)")
    t = gs["t_m"]
    step("B ground slab", "B05", "Ground slab over the ground-beam and column footprint (inside the drawn plate)",
         -gs["members_inside_m2"] * t, "DOUBLE_COUNTED (BEAM_SLAB_OVERLAP)",
         f"SH08 plate {gs['footprint_m2']:.2f} m2 minus the slab cells; the beams are measured full depth", "FIXED")
    step("B ground slab", "B06", "Ground-slab cells Urban holds unresolved (lift / stair cell, stair-zone cell)",
         -gs["unresolved_m2"] * t, "MISSING_IN_URBAN_BASE", "M4 UNRESOLVED cells; S8.1A decomposition (05)",
         "CONDITIONAL in Urban")
    step("B ground slab", "B07", "Freelancer plate area beyond the drawn ground-floor footprint",
         -(gs["fl_area_m2"] - gs["footprint_m2"]) * t, "GEOMETRY_DIFFERENCE (cannot be located)",
         "one typed area (no outline in the workbook) vs the drawn plate; the 1.2 m passage between the two blocks "
         "is a candidate", "UNLOCATED")
    resid = meas.get("GROUND_SLAB", 0.0) - (gs["fl_m3"] - gs["members_inside_m2"] * t - gs["unresolved_m2"] * t -
                                            (gs["fl_area_m2"] - gs["footprint_m2"]) * t)
    step("B ground slab", "B07a", "Member overlap deducted inside measured cells, and rounding", resid,
         "GEOMETRY_DIFFERENCE (small)", "M4 deducts band / column overlaps inside cells; cell areas kept to 4 dp",
         "MEASURED")
    G = gb_split(U)
    W = 0.3
    fl_len = sum(r["C"] for r in F["rows"] if r["FAMILY"] == "GROUND_BEAMS")
    fl_h = {r["D"] for r in F["rows"] if r["FAMILY"] == "GROUND_BEAMS"}
    fl_w = {r["B"] for r in F["rows"] if r["FAMILY"] == "GROUND_BEAMS"}
    H = fl_h.pop() if len(fl_h) == 1 else None
    Wf = fl_w.pop() if len(fl_w) == 1 else None
    L_ur = G["EXT"][0] + G["INT"][0]
    step("C ground beams", "B08", "Ground-beam length: freelancer total vs Urban net of columns",
         -(fl_len - L_ur) * Wf * H, "GEOMETRY_DIFFERENCE", f"{fl_len:.1f} m typed in two lumps vs {L_ur:.2f} m of "
         "drawn spans net of columns (column / neck owns the joint); christiannp 200.04 m gross, U-C4N ~200 m",
         "MEASURED")
    step("C ground beams", "B09", "Interior ground-beam depth: 0.60 everywhere vs the printed p.13 classes",
         G["INT"][1] - G["INT"][0] * Wf * H, "THICKNESS_OR_DEPTH_DIFFERENCE", "p.13 typical sections 30 x 30 "
         "(< 2.5 m), 30 x 40 (< 5 m), 30 x 60 (> 5 m); the class basis (c/c or clear) is RFI-A05", "MEASURED")
    step("C ground beams", "B10", "Exterior ground-beam depth: 0.60 vs the FOLLOW ARCH bracket",
         G["EXT"][1] - G["EXT"][0] * Wf * H, "THICKNESS_OR_DEPTH_DIFFERENCE", "p.13 exterior detail 30 x FOLLOW "
         "ARCH from the GF slab level (+1.00) to the outer ground level; base 0.9 - 1.0 where the plan prints +1.00, "
         "the class section at +0.30 / +0.15 (source conflict, RFI-M4-06)", "MEASURED (range)")
    for f, sid, title, cls, ev in (
            ("STRAPS", "B11", "Strap beams", "GEOMETRY_DIFFERENCE", "drawn faces clear of the footings; SB2 two rows"),
            ("FOOTINGS", "B12", "Footings", "MISSING_IN_FREELANCER", "a second F3 outline drawn on SH10; the FN "
             "outline overlapping F9 deducted"),
            ("NECKS", "B13", "Foundation necks", "HEIGHT_OR_LEVEL_DIFFERENCE", "neck to +1.00 from a founding level "
             "1.50 m below plot level (printed minimum) vs 1.50 m necks"),
            ("COLUMNS", "B14", "Columns GF - 2F", "HEIGHT_OR_LEVEL_DIFFERENCE", "floor to floor vs clear under "
             "beams (the joint is re-allocated, compare frame per floor in 07)"),
            ("BEAMS", "B15", "Suspended beams", "GEOMETRY_DIFFERENCE + MISSING_IN_FREELANCER", "per-mark crosswalk "
             "(07): B27, B19, B25, B5 and B6 / B4 lengths missing in the freelancer; c/c vs net lengths; dome-A ring "
             "arcs moved to domes"),
            ("SLABS", "B16", "Suspended slabs", "GEOMETRY_DIFFERENCE", "net panels per floor within 2 - 4 %; same "
             "16 cm default and 18 cm water-tank panels"),
            ("LINTELS", "B17", "Lintels", "MISSING_IN_FREELANCER", "p.13 lintel schedule over masonry openings"),
            ("STAIRS", "B18", "Stairs", "ASSUMPTION_DIFFERENCE", "0.28 m slab-equivalent vs drawn flights, winders and "
             "landings at the waist range; ST-B missing in the freelancer"),
            ("DOMES", "B19", "Domes", "GEOMETRY_DIFFERENCE + SCOPE_DIFFERENCE", "3 hemispheres vs 2 caps + 2 rings "
             "(tower dome conditional)"),
            ):
        step("D frame / foundations / specials", sid, title, meas.get(f, 0.0) - fl[f], cls, ev, "MEASURED")
    pool_fl = fl["POOL"] - (steps_r["VALUE_M3"] if steps_r else 0.0)
    step("D frame / foundations / specials", "B20", "Pool base and walls", meas.get("POOL", 0.0) - pool_fl,
         "HEIGHT_OR_LEVEL_DIFFERENCE", "wall height 1.8 m vs drawn bands x height above the base (profile "
         "conflict)", "MEASURED (range)")
    step("D frame / foundations / specials", "B21", "Lift pit walls", meas.get("LIFT", 0.0) - fl["LIFT"],
         "GEOMETRY_DIFFERENCE", "8 m x 1.5 m vs four drawn pieces x founding range", "MEASURED")
    end = sum(fam[f]["MEAS_BASE"] for f in fam if f != "BLINDING")
    total = start + sum(raw)
    return {"start": start, "end": end, "steps": steps, "closure_m3": total - end}
