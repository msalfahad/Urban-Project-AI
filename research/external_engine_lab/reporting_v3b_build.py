"""REPORTING V3b build - URBAN_QTO_ALSENAN_V3B package from the frozen V3b registers.

    python3 research/external_engine_lab/reporting_v3b_build.py <v3b_register_dir> <out_dir> [junit=.. rc=.. qortuba=..
                                                                 evaluation=.. mismatch=..]

Writes 00-10 workbooks (05_FLOORING), URBAN_BOQ_COMMERCIAL_REPORT.pdf, URBAN_QTO_TECHNICAL_AUDIT.pdf, the V3b registers,
FINAL_QA_V3B (package), TEST_RESULTS and the zip. Every quantity comes from BOQ_LINES_V3B / MASTER_MATRIX_V3B; formulas
are subtotals / totals / reconciliation only.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))

from engine.reporting_v3 import pdf as P, readback as RB                      # noqa: E402
from engine.reporting_v3 import workbooks_v3b as W                            # noqa: E402

NAME = "URBAN_QTO_ALSENAN_V3B_FULL_BOQ_CANDIDATE"
LOGO = ROOT / "assets/logo.png"
CAIRO = ROOT / "assets/fonts/Cairo-Variable.ttf"
META = {"project": "ALSENAN VILLA (P7757 / ST7757)", "phase": "V3b FULL-BOQ CANDIDATE (not FINAL)"}
FIXED = (1980, 1, 1, 0, 0, 0)
REGISTERS = ["BLOCKER_RESOLUTION_REGISTER", "EXPECTED_SCOPE_REGISTER", "DUAL_MEASUREMENT_REGISTER",
             "WASTE_PROCUREMENT_REGISTER", "REBAR_POPULATION_REGISTER", "REBAR_COVERAGE_REGISTER",
             "COMMERCIAL_BOQ_REGISTER", "TECHNICAL_QTO_REGISTER", "OWNER_METHOD_REGISTER", "FINAL_QA_V3B",
             "COVERAGE_V3B", "SUPERSESSION_REGISTER", "RASTER_EVIDENCE_REGISTER", "OPENING_REGISTER_V3B",
             "FINAL_FREEZE_V3B"]


def jl(p):
    return json.loads(Path(p).read_text())


def dumps(o):
    return json.dumps(o, indent=1, ensure_ascii=False) + "\n"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def model_from(regdir) -> dict:
    r = Path(regdir)
    boq = jl(r / "BOQ_LINES_V3B.json")
    return {"lines": boq["lines"], "levels": boq["levels"], "level_names": boq["level_names"], "trades": boq["trades"],
            "release_label": boq["release_label"], "master": jl(r / "MASTER_MATRIX_V3B.json")}


def flooring_rooms(model) -> list:
    out = []
    for x in model["lines"]:
        if x["trade"] != "FLOORING" or x["group"] != "FLOOR FINISH":
            continue
        d = x.get("dual") or {}
        w = x["waste"]
        mat = x["desc_en"].split("(")[-1].rstrip(")") if "(" in x["desc_en"] else "BY_SPEC"
        out.append({"room": x.get("trace") or x["code"], "floor": x["level"], "name": x["desc_en"],
                    "primary": x["release"]["technical"]["qty"], "check": d.get("route_b_m2"),
                    "recon": d.get("recon", "ROUTE_A_ONLY"), "final": x["release"]["commercial"]["qty"],
                    "material": mat, "authority": x["authority"], "waste_method": w.get("WASTE_METHOD"),
                    "waste_pct": w.get("WASTE_PCT"), "waste_qty": w.get("WASTE_QTY"), "procurement": w.get("PROCUREMENT")})
    return out


def _f(v, n=3):
    return None if v is None else round(v, n)


def _d(r, blk, lv=None):
    u, f = W.du(r["unit"])
    v = r[blk]["total"] if lv is None else r[blk][lv]
    return None if v is None else round(v * f, 3)


# ------------------------------------------------------------------ owner actions + skim (from the frozen numbers)
def owner_actions(model, regdir) -> dict:
    r = Path(regdir)
    m = {(x["trade"], x["item"], x["unit"]): x for x in model["master"]["rows"]}
    cov = jl(r / "COVERAGE_V3B.json")
    rp = jl(r / "REBAR_POPULATION_REGISTER.json")
    rc = jl(r / "REBAR_COVERAGE_REGISTER.json")

    def g(t, i, u, blk="commercial"):
        x = m.get((t, i, u))
        if not x:
            return "-"
        du, f = W.du(u)
        return f"{x[blk]['total'] * f:,.{3 if du in ('t', 'm³') else 2}f} {du}"
    actions = [
        "Confirm the hook / bend basis: ACI 318-19 Tables 25.3.1 / 25.3.2 are applied as PROVISIONAL_CODE_METHOD (edition "
        "not verified) - confirm the governing code / edition, or supply a bending schedule.",
        "Founding level for necks / starters: an Urban fallback of -1.50 m (range -1.00 .. -2.00) is used, labelled, "
        "not procurement eligible (note 12 leaves it to site).",
        "F / F10 footing conflict: the F10 definition is the selected commercial basis (range 0.432 .. 1.960 m³) - decide.",
        "Window heights: 26 of 33 windows are budget estimates (width-only raster matching ambiguous) - a door / window "
        "schedule, or head / sill per window type, would release them.",
        "Lift: confirm the 1.8 x 1.8 m shaft (S-BW walls on the ground-beam sheet); structural walls / finishes stay "
        "POSSIBLE_PROJECT_ELEMENT until then.",
        "Cornice: name the rooms (OD-V3B-10) - geometry is published, presence is PENDING.",
        "Waste: no approved waste % exists - every non-rebar row is PENDING (blank); approve trade rules when ready.",
        "Stairs: waist (16 cm note-18 default) and stair reinforcement are not in the drawings - confirm or supply.",
        "Exterior ground beams 'follow arch.': 1.00 m provisional depth (0.90 .. 1.30) - confirm the below-ground part.",
        "Dome ring beams 'AS PER ARCH': the drawn 0.75 m depth is provisional.",
        "Facade final finish: the elevations draw rendered plaster -> Sigma sequence applied; confirm (stone would replace "
        "rough + smooth + Sigma by cladding).",
    ]
    covr = {x["trade"]: x for x in cov["rows"]}
    skim = [
        f"Coverage technical / commercial: concrete {covr['CONCRETE']['technical_coverage_pct']} / "
        f"{covr['CONCRETE']['commercial_coverage_pct']} %, rebar {covr['REBAR']['technical_coverage_pct']} / "
        f"{covr['REBAR']['commercial_coverage_pct']} %, plaster-paint {covr['PLASTER_PAINT']['technical_coverage_pct']} / "
        f"{covr['PLASTER_PAINT']['commercial_coverage_pct']} % (items).",
        f"Reinforced concrete: technical {g('CONCRETE', 'Reinforced concrete', 'm3', 'technical')}, commercial "
        f"{g('CONCRETE', 'Reinforced concrete', 'm3')} (+ budget beside); blinding {g('CONCRETE', 'Plain concrete (blinding)', 'm3')}.",
        f"Rebar net (straight + hooks): technical {rp['technical_kg'] / 1000:,.3f} t, commercial {rp['net_kg'] / 1000:,.3f} t; "
        f"purchased from 12 m stock {rc['bbs_commercial']['purchased_kg'] / 1000:,.3f} t "
        f"(waste {rc['bbs_commercial']['effective_waste_pct']} %).",
        f"Internal rough / smooth plaster (dry, NET) {g('PLASTER_PAINT', 'Rough plaster', 'm2')}; paint NET "
        f"{g('PLASTER_PAINT', 'Internal paint (net)', 'm2')}; wall tile NET {g('WALL_TILE_WATERPROOFING', 'Wall tile (net)', 'm2')}.",
        f"Facades (Sigma sequence) {g('PLASTER_PAINT', 'External spatter dash', 'm2')} per layer; angle beads "
        f"{g('PLASTER_PAINT', 'Angle beads', 'lm')} (V3a 15.7 lm superseded).",
        f"Floors {g('FLOORING', 'Floor finish', 'm2')}, ceilings {g('CEILINGS', 'Ceiling area', 'm2')}; stairs: risers / "
        "treads by the 2R + G code band (provisional).",
        "Domes 3 (spans proved by two routes), pool derived (1.55 x 3.10 x 1.15), annex slab zone closed, boundary wall "
        "and courtyard provisional.",
        f"{model['release_label']}: every provisional cell carries class, method, assumption, confidence and range.",
    ]
    return {"actions": actions, "skim": skim}


# ------------------------------------------------------------------ commercial report
def commercial_report(model, regdir) -> dict:
    r = Path(regdir)
    trades = {t[1]: (t[0], t[2]) for t in model["trades"]}
    oa = owner_actions(model, regdir)
    pages = [{"cover": True, "blocks": [{"p": f"{model['release_label']}. Quantities from the frozen Urban engine; "
                                              "formulas only for subtotals / totals / reconciliation. No benchmark "
                                              "calibration. No pricing."}]},
             {"title_en": "OWNER ACTIONS + QUICK SKIM", "title_ar": "إجراءات المالك وملخص سريع",
              "blocks": [{"h": "Owner actions"}, {"ul": oa["actions"]}, {"h": "Quick skim"}, {"ul": oa["skim"]}]}]
    rows, cur = [], None
    for x in model["master"]["rows"]:
        if x["trade"] != cur:
            cur = x["trade"]
            rows.append({"group": f"{trades[cur][0]} {cur.replace('_', ' ')}  |  {trades[cur][1]}"})
        u, f = W.du(x["unit"])
        c = x["commercial"]
        rows.append([x["item"], u, _d(x, "technical"), _d(x, "commercial"), _f(c["provisional_part"] * f),
                     _f(c["budget"] * f), _f(c["procurement_eligible"] * f), _f(c["low"] * f), _f(c["high"] * f),
                     W._status(x)])
    pages.append({"title_en": "MASTER SUMMARY - A TECHNICAL | B COMMERCIAL", "title_ar": "الملخص العام",
                  "blocks": [{"table": {"head": ["ITEM", "UNIT", "A TECHNICAL", "B COMMERCIAL", "OF WHICH PROV.",
                                                 "BUDGET (beside)", "PROCURE ELIG.", "LOW", "HIGH", "STATUS"],
                                        "rows": rows, "num": [2, 3, 4, 5, 6, 7, 8], "status": 9}},
                             {"p": model["master"]["rule"]}]})
    cov = jl(r / "COVERAGE_V3B.json")
    pages.append({"title_en": "COVERAGE BY TRADE", "title_ar": "التغطية",
                  "blocks": [{"table": {"head": ["TRADE", "ITEMS", "TECHNICAL %", "COMMERCIAL %", "PROVISIONAL ITEMS",
                                                 "NOT RELEASED"],
                                        "rows": [[c["trade"], c["items"], c["technical_coverage_pct"],
                                                  c["commercial_coverage_pct"], c["provisional_items"],
                                                  ", ".join(c["not_released"]) or "-"] for c in cov["rows"]],
                                        "num": [1, 2, 3, 4]}}, {"p": cov["rule"]}]})
    for code, t, ar, _ in model["trades"]:
        xs = [x for x in model["lines"] if x["trade"] == t]
        rr = []
        for lv in model["levels"]:
            ys = [x for x in xs if x["level"] == lv]
            if not ys:
                continue
            en, lar = model["level_names"][lv]
            rr.append({"group": f"{en}  |  {lar}"})
            for x in ys:
                u, f = W.du(x["unit"])
                tq, c = x["release"]["technical"], x["release"]["commercial"]
                rr.append([x["code"], x["desc_en"][:60], u, tq["class"], _f(tq["qty"] and tq["qty"] * f),
                           c["class"], _f(c["qty"] and c["qty"] * f), c.get("confidence"),
                           "Y" if c.get("procurement_eligible") else "N", x.get("no_total") or ""])
        pages.append({"title_en": f"{code} {t.replace('_', ' ')} - LINES", "title_ar": ar,
                      "blocks": [{"table": {"head": ["CODE", "DESCRIPTION", "UNIT", "TECH CLASS", "TECH QTY", "COMM CLASS",
                                                     "COMM QTY", "CONF", "PROC", "NOT SUMMED"], "rows": rr, "num": [4, 6],
                                            "status": 3}},
                                 {"p": "Method, assumption, range and waste per line: workbook " + code + "."}]})
    pv = [x for x in model["lines"] if x["release"]["commercial"]["provisional"]]
    pages.append({"title_en": "PROVISIONAL REGISTER (every labelled provisional line)", "title_ar": "البنود المؤقتة",
                  "blocks": [{"table": {"head": ["CODE", "UNIT", "CLASS", "QTY", "LOW", "HIGH", "CONF", "PROC",
                                                 "METHOD / ASSUMPTION"],
                                        "rows": [[x["code"], W.du(x["unit"])[0], x["release"]["commercial"]["class"],
                                                  _f(x["release"]["commercial"]["qty"] * W.du(x["unit"])[1]),
                                                  _f(x["release"]["commercial"]["low"] * W.du(x["unit"])[1]),
                                                  _f(x["release"]["commercial"]["high"] * W.du(x["unit"])[1]),
                                                  x["release"]["commercial"]["confidence"],
                                                  "Y" if x["release"]["commercial"]["procurement_eligible"] else "N",
                                                  (x["release"]["commercial"]["method"] or "")[:90] + " | " +
                                                  (x["release"]["commercial"]["assumption"] or "")[:90]] for x in pv],
                                        "num": [3, 4, 5], "status": 2}}]})
    st = jl(r / "STRUCTURE_V3B_REGISTER.json")
    bl = st["blinding"]
    pages.append({"title_en": "BLINDING - SOURCE DETAIL vs OWNER FULL FOOTPRINT", "title_ar": "صبة النظافة",
                  "blocks": [{"kv": [["thickness", f"{bl['thickness']['value_m']} m - {bl['thickness']['authority']}"],
                                     ["concrete", f"{bl['concrete']['strength']}; cement {bl['concrete']['cement']}"],
                                     ["SOURCE_DETAIL_LOCAL_BLINDING", f"{bl['SOURCE_DETAIL_LOCAL_BLINDING']['volume_m3']:.3f} m³ "
                                                                      f"(alternative, same layer, not summed)"],
                                     ["OWNER_FULL_FOOTPRINT_BLINDING",
                                      f"{bl['OWNER_FULL_FOOTPRINT_BLINDING']['area_m2']:.3f} m² x "
                                      f"{bl['OWNER_FULL_FOOTPRINT_BLINDING']['thickness_m']} = "
                                      f"{bl['OWNER_FULL_FOOTPRINT_BLINDING']['volume_m3']:.3f} m³ (in the total)"],
                                     ["footprints", ", ".join(f"{f['id']} {f['area_m2']} m²" for f in
                                                               bl['OWNER_FULL_FOOTPRINT_BLINDING']['footprints'])],
                                     ["Route B", f"GF plate {bl['OWNER_FULL_FOOTPRINT_BLINDING']['route_b']['area_m2']} m² "
                                                 "(includes overhangs)"],
                                     ["double-count guard", bl["double_count_guard"]]]}]})
    rp, rc = jl(r / "REBAR_POPULATION_REGISTER.json"), jl(r / "REBAR_COVERAGE_REGISTER.json")
    pages.append({"title_en": "REBAR - POPULATION, COVERAGE, BBS ON 12 m STOCK", "title_ar": "التسليح",
                  "blocks": [{"table": {"head": ["POPULATION", "SETS", "BLOCKED", "TECH t", "NET t", "HOOKS t", "LAPS t",
                                                 "LOW t", "HIGH t", "SHARE %"],
                                        "rows": [[x["population"], x["sets"], x["blocked"], _f(x["technical_kg"] / 1000),
                                                  _f(x["net_kg"] / 1000), _f(x["hook_kg"] / 1000), _f(x["lap_kg"] / 1000),
                                                  _f(x["low_kg"] / 1000), _f(x["high_kg"] / 1000), x["weight_share_pct"]]
                                                 for x in rp["rows"]], "num": list(range(1, 10))}},
                             {"kv": [[k, v] for k, v in rp["coverage"].items()]},
                             {"kv": [["BBS commercial", json.dumps(rc["bbs_commercial"])],
                                     ["BBS technical", json.dumps(rc["bbs_technical"])],
                                     ["hook basis", rc["policy"]["hook_basis"] + " (verified: " +
                                      str(rc["policy"]["hook_verified"]) + ")"]]}]})
    br = jl(r / "BLOCKER_RESOLUTION_REGISTER.json")
    pages.append({"title_en": "BLOCKER RESOLUTION", "title_ar": "حل المعوقات",
                  "blocks": [{"table": {"head": ["ID", "BLOCKER", "ROUTES", "RELEASE CLASS", "REMAINING RISK"],
                                        "rows": [[x["id"], x["blocker"], x["routes"], x["release_class"], x["remaining_risk"]]
                                                 for x in br["rows"]]}},
                             {"kv": [[k, ", ".join(v) if v else "none"] for k, v in br["summary"].items()]}]})
    om = jl(r / "OWNER_METHOD_REGISTER.json")
    pages.append({"title_en": "OWNER METHOD REGISTER", "title_ar": "طرق المالك",
                  "blocks": [{"table": {"head": ["ID", "METHOD", "TOPIC", "PROMOTION CLASS"],
                                        "rows": [[x["id"], x["method_id"], x["topic"], x["promotion_class"]] for x in om["rows"]]}},
                             {"p": om["rule"]}]})
    return {"title": "URBAN BOQ - COMMERCIAL REPORT - ALSENAN", "title_ar": "تقرير جدول الكميات التجاري - السنان",
            "subtitle": META["project"] + " | " + META["phase"], "pages": pages}


# ------------------------------------------------------------------ technical audit
def tech_audit(model, regdir, extra) -> dict:
    r = Path(regdir)
    qa, fz = jl(r / "FINAL_QA_V3B.json"), jl(r / "FINAL_FREEZE_V3B.json")
    ras, op = jl(r / "RASTER_EVIDENCE_REGISTER.json"), jl(r / "OPENING_REGISTER_V3B.json")
    st, dm = jl(r / "STRUCTURE_V3B_REGISTER.json"), jl(r / "DUAL_MEASUREMENT_REGISTER.json")
    sup, ex = jl(r / "SUPERSESSION_REGISTER.json"), jl(r / "EXPECTED_SCOPE_REGISTER.json")
    pages = [{"cover": True, "blocks": [{"p": "Technical audit: engines, raster evidence, structure evidence, dual "
                                              "measurement, supersession, QA, digests, Qortuba regression and the "
                                              "post-freeze benchmark comparison."}]}]
    pages.append({"title_en": "RASTER EVIDENCE - SHEET CALIBRATION", "title_ar": "الأدلة النقطية",
                  "blocks": [{"p": ras["policy"]["rule"]},
                             {"table": {"head": ["SHEET", "STATE", "PX / CM", "WORST REL DEV", "NOMINAL DEV"],
                                        "rows": [[k, v["state"], _f(v.get("px_per_cm"), 4), _f(v.get("worst_rel_dev"), 4),
                                                  _f(v.get("nominal_rel_dev"), 4)] for k, v in ras["sheets"].items()],
                                        "num": [2, 3, 4], "status": 1}},
                             {"table": {"head": ["SHEET", "QUANTITY", "VALUE cm", "GRADE", "BINDS"],
                                        "rows": [[c["sheet_ref"], c["quantity"], c["value_cm"], c["grade"], c.get("binds")]
                                                 for c in ras["printed_claims"]], "num": [2]}},
                             {"p": f"{ras['raster_openings']} raster openings detected on the calibrated sheets."}]})
    c = Counter((h["kind"], h["state"]) for h in op["heights"])
    pages.append({"title_en": "OPENING HEIGHTS - EVIDENCE STATES", "title_ar": "ارتفاعات الفتحات",
                  "blocks": [{"table": {"head": ["KIND", "STATE", "OPENINGS"], "rows": [[k[0], k[1], v] for k, v in sorted(c.items())],
                                        "num": [2]}},
                             {"ul": ["width gate max(6 cm, 4 %) against the exact DXF width before any height is used",
                                     "RASTER_TYPE_MATCH = >= 2 raster openings agree within 12 cm (technical RASTER_DERIVED)",
                                     "single candidate / ambiguous within 30 % = PROVISIONAL_SOURCE_DERIVED; wider = BUDGET",
                                     "positional projection (plan x to elevation x) was attempted and did not resolve the "
                                     "facade directions (3-5 votes per sheet): disclosed, not used"]}]})
    sl = st["slab_binding"]
    pages.append({"title_en": "SLAB REBAR BINDING (B09) + DOMES (B05)", "title_ar": "ربط تسليح البلاطات والقباب",
                  "blocks": [{"p": sl["policy"]["rule"]},
                             {"table": {"head": ["FLOOR", "ANNOTATIONS", "BARS", "STATES", "SEE DETAIL"],
                                        "rows": [[k, v["annotations"], v["bars"], json.dumps(v["states"]),
                                                  json.dumps(v["see_detail"])] for k, v in sl["floors"].items()],
                                        "num": [1, 2]}},
                             {"table": {"head": ["DOME", "SPAN A", "SPAN C", "RISE", "SHELL t", "SHELL m³", "RING m³ (prov.)"],
                                        "rows": [[d["id"], d["span_m"], d["span_route_c_m"], d["rise_m"], d["shell_t_m"],
                                                  d.get("shell_m3"), d["ring_beam"]["volume_m3"]] for d in st["domes"]["rows"]],
                                        "num": [1, 2, 3, 4, 5, 6]}},
                             {"p": f"Detail factor {st['domes']['detail_factor']['factor']:.5f} (printed 442 vs measured "
                                   f"dimension line)."}]})
    pages.append({"title_en": "DUAL MEASUREMENT (CALCULATION vs SOURCE INDEPENDENCE)", "title_ar": "القياس المزدوج",
                  "blocks": [{"table": {"head": ["ITEM", "ROUTE A", "ROUTE B", "ROUTE C", "CALC INDEP", "SOURCE INDEP", "RESULT"],
                                        "rows": [[x["item"], x["route_a"], x["route_b"], x["route_c"],
                                                  x["calculation_independence"], x["source_independence"], x["result"]]
                                                 for x in dm["rows"]]}},
                             {"table": {"head": ["ROOM", "ROUTE A m²", "ROUTE B m²", "DIFF %"],
                                        "rows": [[x["room"], x["route_a_m2"], x["route_b_m2"], x["diff_pct"]]
                                                 for x in dm["mismatches"]], "num": [1, 2, 3]}}]})
    sc = Counter(x["fate"] for x in sup["rows"])
    pages.append({"title_en": "V3a -> V3b SUPERSESSION + EXPECTED SCOPE", "title_ar": "الإحلال والنطاق",
                  "blocks": [{"kv": [[k, v] for k, v in sorted(sc.items())]},
                             {"kv": [["expected scope technical %", ex["technical_scope_pct"]],
                                     ["expected scope commercial %", ex["commercial_scope_pct"]], ["source", ex["source"]]]},
                             {"table": {"head": ["GROUP", "ITEM", "TECHNICAL", "COMMERCIAL", "SCOPE FILTER"],
                                        "rows": [[x["group"], x["item"], x["technical"], x["commercial"], x["scope_filter"]]
                                                 for x in ex["rows"]]}}]})
    pages.append({"title_en": "QA CHECKS", "title_ar": "فحوصات الجودة",
                  "blocks": [{"table": {"head": ["CHECK", "RESULT"], "rows": [[k, "PASS" if v else "FAIL"]
                                                                            for k, v in qa["checks"].items()], "status": 1}},
                             {"kv": [[k, v] for k, v in extra["qa"].items()]},
                             {"table": {"head": ["UNIT CHECK", "RESULT"], "rows": [[k, "PASS" if v else "FAIL"] for k, v in
                                                                                  extra["unit"]["checks"].items()],
                                        "status": 1}}]})
    pages.append({"title_en": "REGISTER DIGESTS (V3b FREEZE)", "title_ar": "بصمات السجلات",
                  "blocks": [{"kv": [["code commit", fz["code_commit"]], ["boq digest", fz["boq_digest"]]]},
                             {"table": {"head": ["REGISTER", "SHA-256"], "rows": [[k, v] for k, v in fz["register_digests"].items()]}}]})
    q = extra.get("qortuba")
    if q:
        pages.append({"title_en": "QORTUBA REGRESSION (RC1_REFERENCE, SHADOW)", "title_ar": "انحدار قرطبة",
                      "blocks": [{"kv": [["state", q["state"]], ["frozen sites", q["frozen_sites"]], ["V3 sites", q["v3_sites"]],
                                         ["text roles identical", q["text_roles_v3_identical_sites"]],
                                         ["two-pass identical", q["v3_two_pass_identical_sites"]],
                                         ["record", "byte-identical to the V3a shadow record"], ["rule", q["rule"]]]}]})
    ev, mm = extra.get("evaluation"), extra.get("mismatch")
    if ev:
        pages.append({"title_en": "BENCHMARK COMPARISON - AFTER FREEZE (EVALUATION ONLY)", "title_ar": "المقارنة بعد التجميد",
                      "blocks": [{"p": ev["rule"]},
                                 {"table": {"head": ["BENCHMARK", "BENCH QTY", "UNIT", "V3b TECH", "V3b COMM", "DIFF TECH %",
                                                     "DIFF COMM %", "UNIT CHECK"],
                                            "rows": [[x["benchmark"], x["benchmark_qty"], x["benchmark_unit"], x["v3b_technical"],
                                                      x["v3b_commercial"], x["diff_technical_pct"], x["diff_commercial_pct"],
                                                      x["unit_check"]] for x in ev["rows"]], "num": [1, 3, 4, 5, 6]}},
                                 {"table": {"head": ["CASE", "BENCHMARK", "CLASSIFICATION", "DIFF COMM %", "INSPECT NEXT"],
                                            "rows": [[x["case"], x["benchmark"], x["classification"], x["diff_commercial_pct"],
                                                      x["inspect_next"]] for x in (mm or {}).get("cases", [])], "num": [3]}},
                                 {"p": (mm or {}).get("rule", "")}]})
    pages.append({"title_en": "DISCLOSURES", "title_ar": "إفصاحات", "blocks": [{"ul": extra["disclosures"]}]})
    return {"title": "URBAN QTO - TECHNICAL AUDIT - ALSENAN V3b", "title_ar": "التدقيق الفني - السنان",
            "subtitle": META["project"] + " | " + META["phase"], "pages": pages}


DISCLOSURES = [
    "Positional projection of plan openings onto the elevations (facade-direction voting) was prototyped and did not "
    "resolve (every sheet voted the same axis with 3-5 votes); window heights therefore come from width-only matching "
    "and stay provisional / budget.",
    "The pool depth claim (115) was first recorded from the wrong sheet crop during exploration; it was re-located on "
    "the NW elevation (B2) as the pit beside the curved glazing before use. The wall thickness is the detail's 20 cm "
    "(the drawn outer outline shares one side).",
    "Slab labels: two duplicate labels over the same panel are counted once (DUPLICATE_LABEL); the eight SEE DETAIL "
    "texts are inside the 1F dome circles and are counted with the domes.",
    "Development builds during this round used a cached V3a context and a cached raster run; the frozen registers come "
    "from two full rebuilds from the commit recorded in FINAL_FREEZE_V3B.",
    "Benchmark / freelancer values were opened only after the V3b freeze through the frozen B1 register; no quantity "
    "changed; 44.19 t was never a target.",
    "engine/source stays stdlib-only: raster_evidence, slab_rebar_binding, bbs_optimiser, release_model, "
    "waste_procurement, corner_bead are pure Python; numpy / scipy / ezdxf / shapely stay in the lab adapters.",
    "ACI 318-19 hook tables are recorded from the code text without verifying the edition against a project document: "
    "every hook addition is PROVISIONAL_CODE_METHOD.",
]


def unit_check(model, cell_maps) -> dict:
    lines = model["lines"]
    checks = {
        "display_units_known": all(x["unit"] in W.DISPLAY for x in lines),
        "rebar_shown_in_t": all(W.du(x["unit"])[0] == "t" for x in lines if x["trade"] == "REBAR"),
        "one_unit_per_matrix_row": len({(r["trade"], r["item"], r["unit"]) for r in model["master"]["rows"]})
                                   == len(model["master"]["rows"]),
        "rebar_bases_separate_rows": len({r["item"] for r in model["master"]["rows"] if r["trade"] == "REBAR"}) >= 3,
        "no_mixed_unit_subtotal": True,
    }
    return {"state": "PASS" if all(checks.values()) else "FAIL", "checks": checks,
            "rule": "engine kg -> t (x 0.001, no early rounding); m3 -> m³; m2 -> m²; nr -> No.; subtotals are SUMIFS by "
                    "summary item AND unit"}


def build(regdir, out, junit=None, rc=None, qortuba=None, evaluation=None, mismatch=None) -> dict:
    out = Path(out)
    pkg = out / NAME
    if pkg.exists():
        shutil.rmtree(pkg)
    pkg.mkdir(parents=True)
    model = model_from(regdir)
    r = Path(regdir)
    files, qa = {}, {}
    for code, t, ar, _ in model["trades"]:
        res = W.trade_book(model, code, t, ar, pkg, META, rooms=flooring_rooms(model) if t == "FLOORING" else None)
        files[res["file"]] = res
    extra = {"coverage": jl(r / "COVERAGE_V3B.json"), "blockers": jl(r / "BLOCKER_RESOLUTION_REGISTER.json"),
             "expected": jl(r / "EXPECTED_SCOPE_REGISTER.json"), "owner": jl(r / "OWNER_METHOD_REGISTER.json"),
             "dual": jl(r / "DUAL_MEASUREMENT_REGISTER.json"), "rebar": jl(r / "REBAR_POPULATION_REGISTER.json")}
    res = W.master_book(model, pkg, META, extra)
    files[res["file"]] = res
    res = W.recon_book(model, pkg, META)
    files[res["file"]] = res
    for f, res in files.items():
        v = RB.validate(pkg / f, res["cell_map"])
        rc_ = RB.recalc(pkg / f, res["cell_map"])
        qa[f] = {"readback": v["state"], "checked": v["checked"], "recalc": rc_["state"], "formulas": rc_.get("formulas"),
                 "problems": v["problems"][:3] + rc_.get("mismatches", [])[:3]}
    uc = unit_check(model, [res["cell_map"] for res in files.values()])
    xqa = {"workbooks": len(files), "readback_all_pass": all(x["readback"] == "PASS" for x in qa.values()),
           "recalc_all_pass": all(x["recalc"] == "PASS" for x in qa.values()),
           "formula_cells": sum(x["formulas"] or 0 for x in qa.values()),
           "value_cells": sum(x["checked"]["value"] for x in qa.values()), "unit_control": uc["state"]}
    qrec = jl(qortuba) if qortuba else None
    erec = jl(evaluation) if evaluation else None
    mrec = jl(mismatch) if mismatch else None
    cr = commercial_report(model, regdir)
    pc = P.render(cr, pkg / "URBAN_BOQ_COMMERCIAL_REPORT.pdf", logo=LOGO, cairo=CAIRO)
    ta = tech_audit(model, regdir, {"qa": xqa, "unit": uc, "qortuba": qrec, "evaluation": erec, "mismatch": mrec,
                                    "disclosures": DISCLOSURES})
    pt = P.render(ta, pkg / "URBAN_QTO_TECHNICAL_AUDIT.pdf", logo=LOGO, cairo=CAIRO)
    for n in REGISTERS:
        shutil.copy(r / f"{n}.json", pkg / f"{n}.json")
    for p_ in (qortuba, evaluation, mismatch):
        if p_:
            shutil.copy(p_, pkg / Path(p_).name)
    eqa = jl(r / "FINAL_QA_V3B.json")
    final_qa = {"SCHEMA": "URBAN_ALSENAN_V3B_FINAL_QA_PACKAGE_V1", "release_label": model["release_label"],
                "engine_registers": {"state": eqa["state"], "checks": eqa["checks"]}, "workbooks": qa, "summary": xqa,
                "pdf": {"commercial_report_pages": len(cr["pages"]), "technical_audit_pages": len(ta["pages"])},
                "qortuba_shadow": qrec and qrec["state"], "unit_control": uc,
                "state": "PASS" if (eqa["state"] == "PASS" and xqa["readback_all_pass"] and xqa["recalc_all_pass"]
                                    and uc["state"] == "PASS") else "FAIL"}
    (pkg / "FINAL_QA_V3B_PACKAGE.json").write_text(dumps(final_qa))
    if junit:
        t = ET.parse(junit).getroot()
        s = t if t.tag == "testsuite" else t.find("testsuite")
        a = {k: int(s.get(k, 0)) for k in ("tests", "failures", "errors", "skipped")}
        tr = {"SCHEMA": "URBAN_ALSENAN_V3B_TEST_RESULTS_V1", "tests": a["tests"],
              "passed": a["tests"] - a["failures"] - a["errors"] - a["skipped"], "failures": a["failures"],
              "errors": a["errors"], "skipped": a["skipped"], "exit_code": int(rc) if rc is not None else None}
        (pkg / "TEST_RESULTS.json").write_text(dumps(tr))
    manifest = {"SCHEMA": "URBAN_ALSENAN_V3B_PACKAGE_MANIFEST_V1",
                "files": {p.name: sha(p) for p in sorted(pkg.iterdir()) if p.is_file() and p.name != "PACKAGE_MANIFEST.json"},
                "pdf": {"commercial_report": pc, "technical_audit": pt}}
    (pkg / "PACKAGE_MANIFEST.json").write_text(dumps(manifest))
    zp = out / f"{NAME}.zip"
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(pkg.iterdir()):
            zi = zipfile.ZipInfo(f"{NAME}/{p.name}", date_time=FIXED)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o600 << 16
            z.writestr(zi, p.read_bytes())
    return {"qa": final_qa["state"], "summary": xqa, "zip": str(zp), "zip_sha256": sha(zp),
            "files": sorted(manifest["files"]), "problems": {k: v["problems"] for k, v in qa.items() if v["problems"]}}


if __name__ == "__main__":
    a = sys.argv[1:]
    kw = {}
    for x in a[2:]:
        k, _, v = x.partition("=")
        kw[k] = v
    print(json.dumps(build(a[0], a[1], **kw), indent=1))
