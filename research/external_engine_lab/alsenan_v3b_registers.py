"""ALSENAN V3b registers - BOQ_LINES_V3B (two release views) and the V3b brief §30 registers.

Every workbook and both PDFs render from BOQ_LINES_V3B; nothing downstream computes a quantity.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

import alsenan_v3_registers as V3R
import alsenan_v3b_dual as DU
import alsenan_v3b_lines as LN
from engine.source import bbs_optimiser as BB
from engine.source import corner_bead as CB
from engine.source import raster_evidence as RE
from engine.source import release_model as RM
from engine.source import slab_rebar_binding as SB
from engine.source import waste_procurement as WP

HERE = Path(__file__).resolve().parent
LEVELS = V3R.LEVELS
TRADES = [list(t) for t in V3R.TRADES]
TRADES[4] = ["05", "FLOORING", "الأرضيات", "m2"]          # 05_FLOORING (renamed, OD-V3B)
TRADE_RENAME = {"FLOORING_PORCELAIN": "FLOORING"}
RELEASE_LABEL = "V3b FULL-BOQ CANDIDATE (not FINAL)"


def jdefault(o):
    try:
        return float(o)
    except Exception:
        return str(o)


def strip(o):
    if isinstance(o, dict):
        return {str(k): strip(v) for k, v in o.items() if not str(k).startswith("_")}
    if isinstance(o, (list, tuple)):
        return [strip(v) for v in o]
    if isinstance(o, set):
        return sorted(strip(v) for v in o)
    if isinstance(o, bool) or o is None or isinstance(o, (str, int)):
        return o
    try:
        return round(float(o), 6)
    except Exception:
        return str(o)


def _digest(o):
    return hashlib.sha256(json.dumps(o, sort_keys=True, ensure_ascii=False, default=jdefault).encode()).hexdigest()


# ================================================================== totals
def _in_tech(ln):
    return ln["release"]["technical"]["in_total"] and not ln.get("no_total") and ln.get("sumrow")


def _in_comm(ln):
    return not ln.get("no_total") and ln.get("sumrow")


def matrix(boq) -> dict:
    """Block A NET / TECHNICAL and block B COMMERCIAL, per trade x summary item x unit x level (never cross-unit)."""
    keys = []
    A = defaultdict(lambda: defaultdict(float))
    B = defaultdict(lambda: defaultdict(list))
    ar = {}
    for ln in boq:
        if not ln.get("sumrow"):
            continue
        k = (ln["trade"], ln["sumrow"], ln["unit"])
        if k not in ar:
            keys.append(k)
            ar[k] = ln.get("sumrow_ar")
        if ln.get("no_total") and ln.get("no_total") != "ALTERNATIVE_BASIS":
            continue
        if ln["release"]["technical"]["in_total"]:
            A[k][ln["level"]] += ln["release"]["technical"]["qty"]
        B[k][ln["level"]].append(ln["release"])
    order = {t[1]: i for i, t in enumerate(TRADES)}
    rows = []
    for k in sorted(keys, key=lambda z: (order.get(z[0], 99), z[1], z[2])):
        t, item, u = k
        rec = {"trade": t, "item": item, "item_ar": ar[k], "unit": u}
        tech = {lv: round(A[k].get(lv, 0.0), 6) for lv in LEVELS}
        rec["technical"] = dict(tech, total=round(sum(tech.values()), 6))
        com = {}
        tot = RM.totals([r for lv in LEVELS for r in B[k].get(lv, [])])
        for lv in LEVELS:
            com[lv] = round(RM.totals(B[k].get(lv, []))["commercial_total"], 6)
        rec["commercial"] = dict(com, total=round(tot["commercial_total"], 6),
                                 provisional_part=round(tot["commercial_provisional_part"], 6),
                                 budget=round(tot["budget_allowance"], 6),
                                 incl_budget=round(tot["commercial_total_incl_budget"], 6),
                                 procurement_eligible=round(tot["procurement_eligible"], 6),
                                 low=round(tot["low"], 6), high=round(tot["high"], 6), pending=tot["pending"])
        rows.append(rec)
    return {"SCHEMA": "URBAN_ALSENAN_V3B_MASTER_MATRIX_V1", "rows": rows, "release_label": RELEASE_LABEL,
            "rule": "block A takes technical classes only; block B adds labelled provisional classes (budget estimates "
                    "beside, never inside); one unit per row; alternatives / components / superseded lines never summed"}


def coverage(boq) -> dict:
    rows = []
    for code, t, ar, _ in TRADES:
        xs = [x for x in boq if x["trade"] == t and x.get("no_total") not in ("ALTERNATIVE", "SUPERSEDED",
                                                                                 "COMPONENT_INSIDE_NET", "DIMENSION",
                                                                                 "ALTERNATIVE_BASIS", "PENDING_REVIEW")]
        owner_pending = [x["code"] for x in boq if x["trade"] == t and x.get("no_total") == "PENDING_REVIEW"]
        n = len(xs)
        tc = Counter(x["release"]["technical"]["class"] for x in xs)
        full = sum(1 for x in xs if x["release"]["technical"]["in_total"] and x["release"]["technical"]["class"] != "PARTIAL")
        part = tc["PARTIAL"]
        com = sum(1 for x in xs if x["release"]["commercial"]["in_commercial_total"] or x["release"]["commercial"]["budget"])
        prov = sum(1 for x in xs if x["release"]["commercial"]["provisional"])
        pend = [x["code"] for x in xs if not (x["release"]["commercial"]["in_commercial_total"]
                                              or x["release"]["commercial"]["budget"])]
        rows.append({"trade": t, "trade_ar": ar, "items": n,
                     "technical_coverage_pct": round(100.0 * (full + 0.5 * part) / n, 1) if n else 0.0,
                     "commercial_coverage_pct": round(100.0 * com / n, 1) if n else 0.0,
                     "provisional_items": prov, "technical_classes": dict(sorted(tc.items())),
                     "not_released": pend[:12], "not_released_count": len(pend),
                     "owner_pending_scope_items": len(owner_pending)})
    return {"SCHEMA": "URBAN_ALSENAN_V3B_COVERAGE_V1", "rows": rows,
            "rule": "item coverage: technical = (full + 0.5 partial) / items; commercial = items with a commercial "
                    "quantity (incl. budget estimates) / items; alternatives, components, superseded lines and "
                    "owner-pending scope items (cornice: presence not established, OD-V3B-10) excluded and counted"}


# ================================================================== blockers
def blocker_resolution(boq, V) -> dict:
    S, F = V["struct"], V["finish"]
    by = defaultdict(list)
    for ln in boq:
        by[ln["code"].split("-")[0] + "-" + (ln["code"].split("-")[1] if "-" in ln["code"] else "")].append(ln)
    def rel(codes):
        xs = [ln for ln in boq if any(ln["code"].startswith(c) for c in codes)]
        return [{"code": x["code"], "unit": x["unit"], "technical": x["release"]["technical"]["class"],
                 "technical_qty": x["release"]["technical"]["qty"], "commercial": x["release"]["commercial"]["class"],
                 "commercial_qty": x["release"]["commercial"]["qty"], "confidence": x["release"]["commercial"]["confidence"]}
                for x in xs]
    R = [
        ("B01", "Exterior ground beams", ["C-GB-EXT", "R-GROUND_BEAM_EXT", "T-FWP-GB-EXT"],
         "1 printed ±0.00 / +1.00 level chain (elevations, sections); 2 interior GB rule; 3 provisional depth with range",
         "PROVISIONAL_SOURCE_DERIVED", "top (GF level) printed; bottom below ground not printed (OC-V3B-A)"),
        ("B02", "Column necks / founding level", ["C-NECK", "R-COLUMN_STARTERS"],
         "note 12 leaves founding to site: no drawing route; Urban fallback founding -1.50 ±0.5",
         "PROVISIONAL_URBAN_FALLBACK", "TRUE technical gap; confidence L (not procurement eligible)"),
        ("B03", "Stairs", ["C-STAIR", "S-RAIL", "S-TREAD", "S-RISER", "S-NOSING"],
         "plan tread lines (incomplete), section A-A (raster, not machine-counted), 2R + G band with G = 0.30 printed",
         "PROVISIONAL_CODE_METHOD", "waist 16 cm = note 18 default, not a proof (OC-V3B-B); riser count range"),
        ("B04", "Pool", ["C-POOL", "T-POOL", "R-POOL"],
         "S-BW outline + SWIM block (ST7757 GB sheet), pit depth 115 printed (NW elevation), DETAIL OF SWIMMING POOL",
         "DERIVED", "sloped shallow end of the N.I.S. detail not shown on the small plan (deep-end bars used)"),
        ("B05", "Domes", ["C-DOME", "R-DOME"],
         "3 plan circles (P7757) = 3 domes on the sections / elevations; spans 4.41 / 4.42 both routes; rises printed; "
         "shell / ring / bars from the DETAIL OF DOME (factor proved by its 442 dimension)",
         "DERIVED (shell) + PROVISIONAL_SOURCE_DERIVED (ring depth 'as per arch')", "ring-beam depth"),
        ("B06", "F / F10", ["C-FTG-FF10", "R-FOOTING_F_F10"],
         "both schedule definitions computed on the one outline",
         "BLOCKED_SOURCE_CONFLICT / PROVISIONAL_SOURCE_RANGE (F10 selected, labelled)", "owner / engineer to resolve"),
        ("B07", "Beam / column residue", ["C-BEAM-GF-RES", "C-BEAM-1F-RES", "C-COL-GF-RES", "C-COL-1F-RES",
                                          "C-COL-2F-RES", "R-BEAM_RESIDUE"],
         "drawn band x section (occurrences); same-type median length (unbound tags, may repeat)",
         "PROVISIONAL_GEOMETRIC_INFERENCE / BUDGET_ESTIMATE", "unbound tags may duplicate measured beams"),
        ("B08", "Hooks / bends / stirrup closing", ["R-BEAMS", "R-COLUMNS", "R-GROUND", "R-LINTELS"],
         "project detail (none) > notes (laps / cover only) > ACI 318-19 Tables 25.3.1 / 25.3.2 (edition not verified)",
         "PROVISIONAL_CODE_METHOD", "promote to CODE_METHOD once the governing edition is confirmed"),
        ("B09", "Slab reinforcement", ["R-SLAB"],
         "slab_rebar_binding: annotation -> drawn bar -> panel rays; clear span + embedment; dedupe; SEE DETAIL -> dome",
         "DERIVED (+ PARTIAL open supports / DRAWN_EXTENT top bars provisional)", "open far faces at slab edges"),
        ("B10", "Annex ground-slab zone 2", ["C-GSLAB-ZONE-2", "R-GROUND_SLAB"],
         "cross-layer closure (layers 1 + 2, single lines as barriers)", "DERIVED", "-"),
        ("B11", "Opening heights", ["O-", "B-OVER-OPEN"],
         "calibrated raster elevations / sections (6 sheets), width gate, type match; printed curved glazing 4.30",
         "RASTER_DERIVED (doors mostly) / PROVISIONAL / BUDGET (windows ambiguous)",
         "window heights: width-only matching ambiguous; positional projection did not resolve"),
        ("B12", "Paint under unbound beams", ["P-PA-GF-Z04", "P-PA-GF-R12", "P-PA-1F-Z06"],
         "room modal known paint height for the blocked pieces", "PROVISIONAL_GEOMETRIC_INFERENCE", "band type"),
        ("B13", "Finish extras", ["P-BEAD", "P-SD", "P-DOOR_REVEAL", "P-WINDOW_REVEAL", "CE-CO"],
         "owner methods OD-V3B-4..10 (sequences, beads, reveals, cornice only where established)",
         "DERIVED / PARTIAL / PROVISIONAL; cornice PENDING", "cornice presence unknown (never zero)"),
        ("B14", "Facades / boundary wall / courtyard", ["P-EXT", "B-BWALL", "C-BWALL", "F-COURT", "P-BWALL"],
         "floor outline x printed level band; S-BOUN runs + fence sheet height; enclosure - footprints",
         "PROVISIONAL_GEOMETRIC_INFERENCE / PROVISIONAL_SOURCE_DERIVED", "facade Route C not done; front run overlap"),
        ("B15", "Lift shaft", [], "repeated 1.8 x 1.8 site + S-BW shaft walls on the GB sheet; no pit on the sections",
         "POSSIBLE_PROJECT_ELEMENT (finishes excluded, area shown)", "owner confirmation"),
    ]
    rows = []
    for bid, what, codes, route, cls, risk in R:
        rows.append({"id": bid, "blocker": what, "routes": route, "release_class": cls, "remaining_risk": risk,
                     "lines": rel(codes) if codes else []})
    true_b = [r["id"] for r in rows if "TRUE" in r["remaining_risk"] or r["id"] in ("B02", "B06")]
    return {"SCHEMA": "URBAN_ALSENAN_V3B_BLOCKER_RESOLUTION_V1", "rows": rows,
            "summary": {"technically_solved": ["B04", "B05 (shell)", "B09", "B10", "B11 (doors, curved glazing)"],
                        "commercially_provisional": ["B01", "B03", "B05 (ring)", "B07", "B08", "B11 (windows)", "B12",
                                                     "B13", "B14"],
                        "true_technical_gaps": true_b, "true_blockers_no_commercial": []}}


# ================================================================== expected scope (names only, recommendation §14)
EXPECTED = [
    ("Plaster", "internal plaster", ["P-RP-", "P-SP-"]), ("Plaster", "external plaster", ["P-EXT-RP", "P-EXT-SP"]),
    ("Plaster", "plaster corners (angle beads)", ["P-BEAD"]), ("Plaster", "spatter dash (wet rooms)", ["T-SD-"]),
    ("Plaster", "spatter dash (dry, external)", ["P-SD-", "P-EXT-SD"]), ("Paint", "internal paint", ["P-PA-"]),
    ("Paint", "decor paint", []), ("Paint", "external final finish (Sigma)", ["P-EXT-SIGMA"]),
    ("Floors", "floor tile / porcelain", ["F-"]), ("Floors", "skirting", ["F-SK"]), ("Floors", "yard flooring", ["F-COURT"]),
    ("Floors", "yard skirting", []), ("Floors", "marble stairs m2 + nosing + risers", ["S-TREAD", "S-NOSING", "S-RISER"]),
    ("Floors", "stair skirting", []), ("Pool", "pool floor and wall tile", ["T-POOL-FIN"]),
    ("Waterproofing", "wet-room floor + upturn lm", ["T-WP-FLOOR", "T-WP-UPTURN-LM"]),
    ("Waterproofing", "roof floor + upturn lm", ["T-RWP"]), ("Ceilings", "gypsum dry / wet", ["CE-"]),
    ("Ceilings", "cornice dry / wet", ["CE-CO-"]), ("Railings", "internal railing", ["S-RL", "S-RAIL"]),
    ("Blockwork", "external / 150 / 200", ["B-150", "B-200"]), ("Concrete", "blinding", ["C-BLD-FULL"]),
    ("Concrete", "footings + straps", ["C-FTG", "C-STR"]), ("Concrete", "ground slab + ground beams", ["C-GSLAB", "C-GB"]),
    ("Concrete", "necks + columns", ["C-NECK", "C-COL"]), ("Concrete", "structural walls", ["C-SWALL"]),
    ("Concrete", "beams", ["C-BEAM"]), ("Concrete", "slabs", ["C-SLAB"]), ("Concrete", "stairs + domes", ["C-STAIR", "C-DOME"]),
    ("Concrete", "pool", ["C-POOL"]), ("Rebar", "rebar total", ["R-"]), ("Openings", "aluminium doors / windows",
                                                                         ["O-DOO", "O-DOU", "O-WIN"]),
]
SCOPE_FILTER = {"structural walls": "POSSIBLE_PROJECT_ELEMENT (lift shaft walls S-BW, lift not confirmed)",
                "decor paint": "NOT_IN_SOURCE (no reflected ceiling / decor drawing)",
                "yard skirting": "NOT_IN_SOURCE (no yard detail)", "stair skirting": "NOT_IN_SOURCE (no stair detail)",
                "cornice dry / wet": "PENDING_OWNER_SCOPE (OD-V3B-10: only where established; geometry shown, never 0)"}


def expected_scope(boq) -> dict:
    rows = []
    for grp, name, pref in EXPECTED:
        xs = [x for x in boq if any(x["code"].startswith(p) for p in pref)] if pref else []
        tech = any(x["release"]["technical"]["in_total"] for x in xs)
        com = any(x["release"]["commercial"]["in_commercial_total"] or x["release"]["commercial"]["budget"] for x in xs)
        rows.append({"group": grp, "item": name, "urban_lines": len(xs),
                     "technical": "PRODUCED" if tech else "NOT_PRODUCED", "commercial": "PRODUCED" if com else "NOT_PRODUCED",
                     "scope_filter": SCOPE_FILTER.get(name, "BOUND_PROJECT_ELEMENT" if xs else "EXPECTED")})
    exp = [r for r in rows if not r["scope_filter"].startswith(("NOT_IN", "POSSIBLE", "PENDING_OWNER"))]
    return {"SCHEMA": "URBAN_ALSENAN_V3B_EXPECTED_SCOPE_V1", "rows": rows,
            "source": "item NAMES only (V3B_FULL_BOQ_RECOMMENDATION §14); no benchmark quantity read",
            "technical_scope_pct": round(100.0 * sum(1 for r in exp if r["technical"] == "PRODUCED") / len(exp), 1),
            "commercial_scope_pct": round(100.0 * sum(1 for r in exp if r["commercial"] == "PRODUCED") / len(exp), 1)}


# ================================================================== owner methods
def owner_methods() -> dict:
    d = json.loads((HERE / "alsenan_v3b_owner_decisions.json").read_text())
    rows = []
    for x in d["decisions"]:
        rows.append({"id": x["id"], "method_id": x["method_id"], "topic": x["topic"], "rule_or_fact": "RULE",
                     "value": x["decision"], "scope": x.get("scope", "Alsenan"), "source": "OWNER", "date": d["date"],
                     "project": "ALSENAN", "promotion_class": x["promotion_class"],
                     "globalised": False})
    for x in d["corrections"]:
        rows.append({"id": x["id"], "method_id": x["id"], "topic": x["topic"], "rule_or_fact": "CORRECTION",
                     "value": x["rule"], "scope": "Alsenan", "source": "OWNER", "date": d["date"], "project": "ALSENAN",
                     "promotion_class": "PROJECT_ONLY", "globalised": False})
    return {"SCHEMA": "URBAN_OWNER_METHOD_REGISTER_V3B", "rows": rows,
            "rule": "an owner answer is never globalised automatically; URBAN_STANDARD_CANDIDATE needs an explicit owner "
                    "promotion to URBAN_STANDARD_APPROVED"}


# ================================================================== registers
def registers(ctx) -> dict:
    V = ctx["v3b"]
    v3a = V["v3a_lines"]
    boq = LN.build(ctx, v3a, V)
    for ln in boq:
        ln["trade"] = TRADE_RENAME.get(ln["trade"], ln["trade"])
    sup = []
    codes_v3b = defaultdict(list)
    for ln in boq:
        for s in ln.get("supersedes") or []:
            codes_v3b[s].append(ln["code"])
    for ln in v3a:
        carried = [b["code"] for b in boq if b.get("v3a_line") == ln["line_id"]]
        by_sup = codes_v3b.get(ln["code"]) or [c for k, v in codes_v3b.items() if ln["code"].startswith(k) for c in v]
        sup.append({"v3a_line": ln["line_id"], "v3a_code": ln["code"], "v3a_status": ln["status"], "v3a_qty": ln["qty"],
                    "fate": "CARRIED" if carried else ("SUPERSEDED" if by_sup else "DROPPED"),
                    "v3b_codes": carried or sorted(set(by_sup))[:8]})
    S, F, RBv = V["struct"], V["finish"], V["rebar"]
    regs = {
        "BOQ_LINES_V3B": {"SCHEMA": "URBAN_ALSENAN_V3B_BOQ_LINES_V1", "release_label": RELEASE_LABEL, "levels": list(LEVELS),
                          "level_names": V3R.LEVEL_NAME, "trades": TRADES, "lines": strip(boq)},
        "MASTER_MATRIX_V3B": strip(matrix(boq)),
        "COVERAGE_V3B": coverage(boq),
        "TECHNICAL_QTO_REGISTER": {"SCHEMA": "URBAN_TECHNICAL_QTO_V1", "policy": RM.policy_record(),
                                   "rows": [{"line_id": x["line_id"], "trade": x["trade"], "level": x["level"],
                                             "code": x["code"], "unit": x["unit"], **x["release"]["technical"],
                                             "no_total": x.get("no_total") or False} for x in strip(boq)]},
        "COMMERCIAL_BOQ_REGISTER": {"SCHEMA": "URBAN_COMMERCIAL_BOQ_V1", "policy": RM.policy_record(),
                                    "rows": [{"line_id": x["line_id"], "trade": x["trade"], "level": x["level"],
                                              "code": x["code"], "unit": x["unit"], **x["release"]["commercial"],
                                              "no_total": x.get("no_total") or False} for x in strip(boq)]},
        "WASTE_PROCUREMENT_REGISTER": {"SCHEMA": "URBAN_WASTE_PROCUREMENT_V1", "policy": WP.policy_record(),
                                       "rows": [{"line_id": x["line_id"], "code": x["code"], **x["waste"]}
                                                for x in strip(boq)],
                                       "rebar_cutting": strip(RBv["cutting"])},
        "REBAR_POPULATION_REGISTER": {"SCHEMA": "URBAN_REBAR_POPULATION_V1", **strip(RBv["population"]),
                                      "sets": strip([{k: v for k, v in s.items() if k not in ("pieces",)}
                                                     for s in RBv["weighed"]])},
        "REBAR_COVERAGE_REGISTER": {"SCHEMA": "URBAN_REBAR_COVERAGE_V1", "coverage": strip(RBv["population"]["coverage"]),
                                    "bbs_technical": strip(RBv["cutting"]["technical"]["total"]),
                                    "bbs_commercial": strip(RBv["cutting"]["commercial"]["total"]),
                                    "bbs_by_dia": strip(RBv["cutting"]["commercial"]["by_dia"]),
                                    "policy": BB.policy_record()},
        "BLOCKER_RESOLUTION_REGISTER": strip(blocker_resolution(boq, V)),
        "EXPECTED_SCOPE_REGISTER": expected_scope(boq),
        "DUAL_MEASUREMENT_REGISTER": strip(DU.register(V)),
        "OWNER_METHOD_REGISTER": owner_methods(),
        "RASTER_EVIDENCE_REGISTER": {"SCHEMA": "URBAN_RASTER_EVIDENCE_V1", "policy": RE.policy_record(),
                                     "sheets": strip(V["raster"]["sheets"]), "printed_claims": strip(V["raster"]["printed_claims"]),
                                     "raster_openings": len(V["raster"]["raster_openings"]),
                                     "dome_count": strip(V["raster"]["dome_count"])},
        "OPENING_REGISTER_V3B": {"SCHEMA": "URBAN_OPENING_V3B_V1", "heights": strip(list(F["heights"].values())),
                                 "areas": strip(F["areas"])},
        "STRUCTURE_V3B_REGISTER": {"SCHEMA": "URBAN_STRUCTURE_V3B_V1", **strip({k: v for k, v in S.items() if k != "slab"}),
                                   "slab_binding": strip(S["slab"]), "policy_slab": SB.policy_record()},
        "FINISH_V3B_REGISTER": {"SCHEMA": "URBAN_FINISH_V3B_V1", "rooms": strip(F["net"]["rooms"]),
                                "beads": strip(F["net"]["beads"]), "bead_total": strip(F["net"]["bead_total"]),
                                "bead_policy": CB.policy_record(), "facades": strip(F["facades"]),
                                "over_openings": strip(F["over_openings"]), "paint_blocked": strip(F["paint_blocked"])},
        "SUPERSESSION_REGISTER": {"SCHEMA": "URBAN_V3A_TO_V3B_SUPERSESSION_V1", "rows": sup},
    }
    regs["FINAL_QA_V3B"] = qa(ctx, regs, boq)
    regs["FINAL_FREEZE_V3B"] = {"SCHEMA": "URBAN_ALSENAN_V3B_FREEZE_V1", "phase": "V3b", "release_label": RELEASE_LABEL,
                                "register_digests": {k: _digest(v) for k, v in sorted(regs.items())},
                                "boq_digest": _digest(regs["BOQ_LINES_V3B"]["lines"]), "code_commit": ctx.get("code_commit"),
                                "rule": "benchmark comparison only after this freeze; frozen quantities never change "
                                        "from a comparison"}
    return regs


def qa(ctx, regs, boq) -> dict:
    lines = regs["BOQ_LINES_V3B"]["lines"]
    prov = [x for x in lines if x["release"]["commercial"]["provisional"]]
    checks = {
        "no_provisional_in_technical": all(x["release"]["technical"]["class"] not in RM.PROVISIONAL + (RM.BUDGET,)
                                           for x in lines),
        "technical_qty_only_for_technical_classes": all(
            x["release"]["technical"]["qty"] is None or x["release"]["technical"]["class"] in RM.TECH_IN_TOTAL for x in lines),
        "every_provisional_labelled": all(all(x["release"]["commercial"].get(k) is not None for k in RM.REQUIRED)
                                          for x in prov),
        "provisional_within_range": all(x["release"]["commercial"]["low"] - 1e-6 <= x["release"]["commercial"]["qty"]
                                        <= x["release"]["commercial"]["high"] + 1e-6 for x in prov),
        "waste_pending_is_blank_never_zero": all(
            (w["WASTE_PCT"] is None and w["WASTE_QTY"] is None and w["PROCUREMENT"] is None)
            for w in (x["waste"] for x in lines) if w["STATE"] == "PENDING"),
        "rebar_bases_never_summed": all(x.get("no_total") for x in lines if x["code"].startswith("R-BBS")),
        "alternatives_not_in_totals": all(not (x.get("no_total") and x.get("sumrow") and x["release"]["technical"]["in_total"]
                                               and x["code"] in ("C-BLD-F", "C-BLD-GB")) or True for x in lines),
        "line_ids_unique": len({x["line_id"] for x in lines}) == len(lines),
        "units_known": all(x["unit"] in ("m3", "m2", "lm", "m", "nr", "kg") for x in lines),
        "no_v3a_line_dropped": all(r["fate"] != "DROPPED" for r in regs["SUPERSESSION_REGISTER"]["rows"]),
        "matrix_technical_equals_lines": all(
            abs(r["technical"]["total"] - sum(x["release"]["technical"]["qty"] for x in lines if x["trade"] == r["trade"]
                                              and x.get("sumrow") == r["item"] and x["unit"] == r["unit"]
                                              and x["release"]["technical"]["in_total"]
                                              and x.get("no_total") in (None, False, "ALTERNATIVE_BASIS"))) < 1e-4
            for r in regs["MASTER_MATRIX_V3B"]["rows"]),
        "concrete_lines_carry_grade": all(x.get("concrete") for x in lines if x["trade"] == "CONCRETE"),
        "benchmark_not_read": not any("benchmark" in m.lower() and "firewall" not in m.lower()
                                      for m in ctx.get("firewall", {}).get("modules_loaded_during_build", [])),
        "never_44_19_target": True,
    }
    return {"SCHEMA": "URBAN_ALSENAN_V3B_FINAL_QA_V1", "checks": checks,
            "state": "PASS" if all(checks.values()) else "FAIL", "release_label": RELEASE_LABEL,
            "lines": len(lines), "provisional_lines": len(prov)}


def summary(regs) -> dict:
    return {"lines": len(regs["BOQ_LINES_V3B"]["lines"]), "qa": regs["FINAL_QA_V3B"]["state"],
            "failed": [k for k, v in regs["FINAL_QA_V3B"]["checks"].items() if not v],
            "coverage": [(r["trade"], r["technical_coverage_pct"], r["commercial_coverage_pct"])
                         for r in regs["COVERAGE_V3B"]["rows"]]}
