"""T-615: Q-80 answered A -> the 0.15 m black-block module 40 x 20 (12.5 / m2) as UPC-BLACK-BLOCK-001 1.1.0
(rules/rulebook/URBAN_COMPANY_RULEBOOK_1.1.0.json), and the quantities T-533 / T-539 held on that one datum restated.

Physical element: the 0.15 m solid black (cement) block as laid, 39 x 19 face + 10 mm bed and head joint = 40 x 20
installed module (owner Q-80 2026-11-07, Q-75 2026-11-02 for the 0.20 m block; joint owner 2026-10-29), its joint
mortar (panel R-T533-1 / R-T367-1 identity, perimeter increment R-T520-1), the mortar materials (UPC-BLACK-MORTAR-001,
Q-78 A) and the Q-77 accessories (sharmat ties one per 3 courses at a wall-to-column junction, bed-joint strip every
3 courses) on the same course (0.19 + 0.010 = 0.200 m).

Method (no new arithmetic rule; the merged rules re-run with the new register entry):
  * register = UPC-BLACK-BLOCK-001 1.1.0 confirmed_modules_m (0.15 and 0.20: 40 x 20), joint 10 mm -> BM.ModuleEntry
  * units / panel mortar per wall: block_module_v1.quantities on the T-506 material base (RC lintel faces out); the
    low end takes the HELD D-1F-09 lintel face (0 .. 0.34 m2) out as T-533 did
  * perimeter mortar: t520_alsenan.build() with MODULE from the register (kappa and course height both follow it)
  * ties / strip: t539_alsenan.build() with the T-533 register reading the 1.1.0 rulebook; T-539 asserts inside that
    every restated count equals T-355 PRIMARY (the same 0.200 m course), so nothing is scaled or copied
Rounding: the rulebook keeps the theoretical count unrounded (company_rulebook_v1.black_blocks rounds to 1e-9 only);
the procurement count is ceil(theoretical x (1 + sourced waste)) and waste is not sourced -> procurement HELD. Cement
bags are 'rounded up at the purchasing group' (UPC-BLACK-MORTAR-001): the group is the whole black-block mortar line,
so the 0.15 m share is stated unrounded.
Writes research/agents_t615/out/: WALLS_015_T615.csv, ACCESSORIES_015_T615.csv, SUMMARY_T615.json.
    python3 -I research/agents_t615/t615_alsenan.py [--check]
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for p in ("agents_t533", "agents_t520", "agents_t539"):
    sys.path.insert(0, str(ROOT / "research" / p))
import block_module_v1 as BM  # noqa: E402
import t520_alsenan as A  # noqa: E402
import t533_alsenan as T533  # noqa: E402
import t539_alsenan as T539  # noqa: E402
import accessory_ledger_v2 as V  # noqa: E402

OUT = HERE / "out"
RULEBOOK_NEW = "rules/rulebook/URBAN_COMPANY_RULEBOOK_1.1.0.json"
RULEBOOK_OLD = "rules/rulebook/URBAN_COMPANY_RULEBOOK_1.0.0.json"
INPUTS = [RULEBOOK_NEW, RULEBOOK_OLD,
          "research/agents_t520/out/PERIMETER_BY_WALL_T520.csv",
          "research/agents_t506/out/MORTAR_RECONCILIATION_T506.csv",
          "research/agents_t533/out/SUMMARY_T533.json",
          "research/agents_t539/out/TIES_V2_T539.csv",
          "research/agents_t539/out/STRIP_V2_T539.csv",
          "research/agents_t539/out/SUMMARY_T539.json"]
RULE_ID, RULE_VERSION = "UPC-BLACK-BLOCK-001", "1.1.0"
MODULE_STATUS = "ASSUMED - OWNER-APPROVED"     # owner company rule (Q-80), not printed on the drawings
STATUS_RANK = ["VERIFIED", "DRAWING-CONFIRMED", "ASSUMED - OWNER-APPROVED"]
D39_TOP_2F = T539.D39_TOP_RANGE_2F             # 2F block top 3.75 .. 3.85 m (D-39, T-488 / T-520)

# Owner condition of Q-80: 'tell me if the drawings show otherwise'. Search of 2026-11-08 (this run) over the
# structural DXF (ST7757 dxf.dxf: 2,553 text / mtext / attribute / dimension strings incl. the Arabic notes written in
# the xarb keyboard-mapped font, layers, hatch patterns, block names), the architectural DXF (P7757_DXF_COMPRESSED.zip:
# 675 strings, layers, hatches, blocks) and the text layer of ST7757.pdf / sanitary-7757.pdf. Handles and geometry only
# (no drawing text is copied): what the drawings say about the black block, and whether a 15 cm face is printed.
DRAWING_SEARCH = [
    {"drawing": "ST7757 dxf.dxf", "handle": "B8", "layer": "S-NOTE", "kind": "general note (Arabic)",
     "finding": "names black (cement) block walls built from foundation level at the neighbour-side perimeter; prints "
                "no block size, face, thickness or joint", "verdict": "NO FACE PRINTED"},
    {"drawing": "ST7757 dxf.dxf", "handle": "7D", "layer": "S-NOTE", "kind": "general note (Arabic)",
     "finding": "slab thickness 16 cm unless stated otherwise (a slab, not a block)", "verdict": "NOT A BLOCK"},
    {"drawing": "ST7757 dxf.dxf", "handle": "7FD", "layer": "S-HAT.BAT", "kind": "HATCH AR-B816C, scale 15",
     "finding": "U-shaped strip 200 mm wide (boundary 31.370 x 8.300 m, 8 vertices) on the ground-level column plan: "
                "a 0.20 m black-block wall in plan (the B8 neighbour-side walls); the AutoCAD library pattern draws a "
                "240 x 120 mm cell at scale 15 (graphic, not a unit size)", "verdict": "0.20 m WALL, NO FACE"},
    {"drawing": "ST7757 dxf.dxf", "handle": "7FB", "layer": "S-HAT.BAT", "kind": "HATCH AR-B816C, scale 15",
     "finding": "strip 200 x 1,150 mm on the same plan", "verdict": "0.20 m WALL, NO FACE"},
    {"drawing": "ST7757 dxf.dxf", "handle": "80F", "layer": "S-HAT.BAT", "kind": "HATCH AR-B816, scale 15",
     "finding": "strip 1,200 x 200 mm on the same plan", "verdict": "0.20 m WALL, NO FACE"},
    {"drawing": "ST7757 dxf.dxf", "handle": "537", "layer": "-", "kind": "INSERT of block '816'",
     "finding": "block '816' holds one slab-reinforcement label (8 bars of 16 mm per m), not a masonry unit",
     "verdict": "NOT A BLOCK"},
    {"drawing": "P7757 DXF (architectural)", "handle": "-", "layer": "all 19 layers",
     "kind": "texts, hatches (NET / ANGLE / LINE / AR-PARQ1 / SOLID), 47 block names",
     "finding": "no block product, size, face or joint text; no masonry hatch; '15.00' / '+0.15' are dimensions and "
                "levels", "verdict": "SILENT"},
    {"drawing": "ST7757.pdf, sanitary-7757.pdf", "handle": "-", "layer": "-", "kind": "PDF text layer",
     "finding": "no text layer beyond sheet dates and the sheet number (prints of the CAD sheets)", "verdict": "SILENT"},
]
DRAWING_RESULT = ("no drawing prints a 15 cm (or any) black-block face; the only masonry statements are the B8 note "
                  "(black block, no size) and three AR-B816 hatches on 0.20 m strips: nothing differs from 40 x 20, "
                  "so nothing is reported against Q-80 and the rule is applied as answered")
NOT_SEARCHED = ("architectural PDF sheets (Drive 'Alsenan chalet project', Alsenan_Architectural_P7757_Pages_* and "
                "p7757_arch_sheet03/04/09/10): prints of the architectural DXF searched above, not re-read in this run")


def _csv(p):
    return list(csv.DictReader((ROOT / p).open(encoding="utf-8")))


def _sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def rule_record(path=RULEBOOK_NEW):
    rb = json.loads((ROOT / path).read_text(encoding="utf-8"))
    return rb, next(r for r in rb["records"] if r["rule_id"] == RULE_ID)


def register(path=RULEBOOK_NEW):
    """T-533's register builder pointed at the 1.1.0 rulebook (one source of the module; nothing re-typed)."""
    keep = T533.INPUTS[2]
    try:
        T533.INPUTS[2] = path
        return T533.register()
    finally:
        T533.INPUTS[2] = keep


def module_015(reg):
    r = BM.resolve(reg, "BLACK", 0.15)
    if r["status"] != "RESOLVED":
        raise BM.ModuleError(f"0.15 m module not resolved from {RULEBOOK_NEW}: {r['held']}")
    e = r["entry"]
    if (round(e.face_w_m + e.head_joint_m, 6), round(e.face_h_m + e.bed_joint_m, 6)) != (0.40, 0.20):
        raise BM.ModuleError(f"0.15 m module {e} is not the Q-80 40 x 20 module")
    return e


def weakest(*st):
    return max(st, key=lambda s: STATUS_RANK.index(s))


def perimeter(module):
    keep = A.MODULE
    try:
        A.MODULE = module
        rows, _ = A.build()
    finally:
        A.MODULE = keep
    return {r["wall_id"]: r for r in rows}


def walls_restated():
    reg, _ng = register()
    e = module_015(reg)
    mod = (e.face_w_m, e.face_h_m, round(e.face_w_m + e.head_joint_m, 6), round(e.face_h_m + e.bed_joint_m, 6))
    if mod != A.MODULE:
        raise BM.ModuleError(f"register module {mod} differs from the T-520 module {A.MODULE}")
    per = perimeter(mod)
    rows, tot = [], dict.fromkeys(("contract_m2", "material_base_m2", "material_base_low_m2", "units_nr",
                                   "units_nr_low", "panel_m3", "panel_m3_low", "panel_contract_m3", "per_fig_m3",
                                   "per_low_m3", "per_high_m3"), 0.0)
    for w, m in T533.walls():
        wid = w["wall_id"]
        mb = float(m["material_base_m2"])
        mb_low = mb - float(m["held_face_max_m2"] or 0.0)
        q = BM.quantities(mb, reg, "BLACK", 0.15, T533.CEMENT_BAGS, T533.SAND_M3, T533.MIX_SOURCE)
        ql = BM.quantities(mb_low, reg, "BLACK", 0.15, T533.CEMENT_BAGS, T533.SAND_M3, T533.MIX_SOURCE)
        qc = BM.quantities(float(w["established_m2"]), reg, "BLACK", 0.15, T533.CEMENT_BAGS, T533.SAND_M3,
                           T533.MIX_SOURCE)
        if q["status"] != "RESOLVED" or q["units_nr"] is None:
            raise BM.ModuleError(f"{wid}: not restated ({q['held']})")
        p = per[wid]
        fig, lo, hi = (float(p[k]) for k in ("perimeter_figure_m3", "perimeter_low_m3", "perimeter_high_m3"))
        held_bands = int(p["held_bands"] or 0)
        status = weakest(w["area_status"], MODULE_STATUS)
        rows.append({
            "floor": w["floor"], "wall_id": wid, "line_id": w["line_id"], "area_status": w["area_status"],
            "contract_m2": w["established_m2"], "material_base_m2": m["material_base_m2"],
            "material_base_low_m2": f"{mb_low:.4f}", "required_lintels": m["required_lintels"],
            "units_nr": f"{q['units_nr']:.4f}", "units_nr_low": f"{ql['units_nr']:.4f}",
            "panel_mortar_m3": f"{q['mortar_m3']:.6f}", "panel_mortar_m3_low": f"{ql['mortar_m3']:.6f}",
            "panel_contract_m3": f"{qc['mortar_m3']:.6f}", "panel_t367_m3": w["panel_t367_m3"],
            "perimeter_figure_m3": f"{fig:.6f}", "perimeter_low_m3": f"{lo:.6f}", "perimeter_high_m3": f"{hi:.6f}",
            "perimeter_held_bands": held_bands, "perimeter_held_pieces": p["held_pieces"],
            "cement_bags": f"{(q['mortar_m3'] + fig) * T533.CEMENT_BAGS:.4f}",
            "sand_m3": f"{(q['mortar_m3'] + fig) * T533.SAND_M3:.6f}",
            "status": status, "basis": f"{RULE_ID} {RULE_VERSION} (Q-80) + area {w['area_status']}",
            "was": "HELD (T-533: 0.15 m module not stated)",
            "residual_held": (f"perimeter: {held_bands} band(s) HELD by name in T-520 ({p['held_pieces'][:80]})"
                              if held_bands and p["held_pieces"] else
                              (f"perimeter: {held_bands} band(s) closed as RANGE in T-520" if held_bands else ""))})
        for k, v in (("contract_m2", float(w["established_m2"])), ("material_base_m2", mb),
                     ("material_base_low_m2", mb_low), ("units_nr", q["units_nr"]), ("units_nr_low", ql["units_nr"]),
                     ("panel_m3", q["mortar_m3"]), ("panel_m3_low", ql["mortar_m3"]),
                     ("panel_contract_m3", qc["mortar_m3"]), ("per_fig_m3", fig), ("per_low_m3", lo),
                     ("per_high_m3", hi)):
            tot[k] += v
    return rows, tot, e


def accessories_restated():
    """T-539 V2 re-run on the 1.1.0 register vs its published outputs: the rows that leave HELD."""
    keep = T533.INPUTS[2]
    try:
        T533.INPUTS[2] = RULEBOOK_NEW
        B = T539.build()
        S = T539.summarise(B)
        reg = T539.register()
    finally:
        T533.INPUTS[2] = keep
    old_t = {(r["population"], r["wall_id"], r["column_at"], r["face"]): r for r in _csv(INPUTS[5])}
    old_s = {r["wall_id"]: r for r in _csv(INPUTS[6])}
    rows = []
    for t in B["ties"]:
        k = (t["population"], t["wall_id"], t["column_at"], t["face"])
        o = old_t[k]
        if o["state"] != t["state"]:
            if not (o["state"] == "HELD" and t["state"] == "MEASURED" and o["t_m"] == "0.15"):
                raise V.LedgerV2Error(f"unexpected tie move {k}: {o['state']} -> {t['state']}")
            sa = int(o["figures"].split()[0].split("=")[1])
            if t["ties"] != sa:
                raise V.LedgerV2Error(f"{k}: restated {t['ties']} vs T-539 S-A figure {sa}")
            rows.append({"item": "MAS.TIE.SHARMAT", "population": t["population"], "wall_id": t["wall_id"],
                         "floor": t["floor"], "where": f"{t['column_at']} {t['face']}", "top_m": f"{float(t['top']):.3f}",
                         "unit": "pcs", "was": "HELD (R-T533-1)", "now": t["ties"], "status": MODULE_STATUS,
                         "note": t.get("bound") or ""})
    for s in B["strip"]:
        o = old_s[s["wall_id"]]
        if (o["net_m"] or None) is None and s["net_m"] is not None:
            if o["t_m"] != "0.15":
                raise V.LedgerV2Error(f"unexpected strip move {s['wall_id']}")
            rows.append({"item": "MAS.MESH.BED_JOINT", "population": "WALL", "wall_id": s["wall_id"],
                         "floor": s["floor"], "where": s["group"], "top_m": "", "unit": "m.l", "was": "HELD (R-T533-1)",
                         "now": f"{float(s['net_m']):.4f}", "status": MODULE_STATUS, "note": ""})
    c015, held = T539.wall_course(reg, "BLACK", 0.15)
    if held:
        raise V.LedgerV2Error(f"0.15 m course not resolved: {held}")
    d39_2f08 = list(V.tie_range(c015, *D39_TOP_2F))
    return rows, S, d39_2f08


def build():
    rb, rec = rule_record()
    _rb0, rec0 = rule_record(RULEBOOK_OLD)
    W, tot, e = walls_restated()
    acc, S539, d39 = accessories_restated()
    ties = [r for r in acc if r["item"] == "MAS.TIE.SHARMAT"]
    strip = [r for r in acc if r["item"] == "MAS.MESH.BED_JOINT"]
    t533 = json.loads((ROOT / INPUTS[4]).read_text(encoding="utf-8"))
    s539_old = json.loads((ROOT / INPUTS[7]).read_text(encoding="utf-8"))
    upm = 1.0 / ((e.face_w_m + e.head_joint_m) * (e.face_h_m + e.bed_joint_m))
    cement = ((tot["panel_m3_low"] + tot["per_low_m3"]) * T533.CEMENT_BAGS,
              (tot["panel_m3"] + tot["per_fig_m3"]) * T533.CEMENT_BAGS,
              (tot["panel_m3"] + tot["per_high_m3"]) * T533.CEMENT_BAGS)
    sand = tuple(c / T533.CEMENT_BAGS * T533.SAND_M3 for c in cement)
    r6 = lambda v: round(v, 6)
    summary = {
        "task": "T-615", "rule": f"{RULE_ID} {rec['version']} (supersedes {rec0['version']})",
        "rulebook": {"file": RULEBOOK_NEW, "version": rb["version"], "supersedes": rb["supersedes"],
                     "changed_records": [RULE_ID], "default_reader": "engine/source/company_rulebook_v1.py stays on 1.0.0"},
        "module_015": {"face_m": [e.face_w_m, e.face_h_m], "joint_m": e.head_joint_m,
                       "installed_m": [round(e.face_w_m + e.head_joint_m, 6), round(e.face_h_m + e.bed_joint_m, 6)],
                       "units_per_m2": r6(upm), "status": MODULE_STATUS,
                       "citation": f"{RULE_ID} {rec['version']} params.confirmed_modules_m['0.15'] = {rec['params']['confirmed_modules_m']['value']['0.15']} (Q-80, owner 2026-11-07); 10 mm joint owner 2026-10-29",
                       "register_entry_citation": e.citation},
        "walls": len(W), "excluded": T533.EXCLUDED,
        "area_m2": {"contract": round(tot["contract_m2"], 4), "material_base": round(tot["material_base_m2"], 4),
                    "material_base_low": round(tot["material_base_low_m2"], 4)},
        "units_nr": {"theoretical": round(tot["units_nr"], 4), "low": round(tot["units_nr_low"], 4),
                     "procurement": "HELD: waste not sourced (UPC-BLACK-BLOCK-001 'waste separate, evidence-based')",
                     "rounding": "theoretical count kept unrounded (rulebook method; company_rulebook_v1 rounds to "
                                 "1e-9); whole units only at procurement = ceil(theoretical x (1 + sourced waste))",
                     "board_2198_75": "the board's 2,198.75 = 175.9 (rounded area) x 12.5; on the unrounded material "
                                      f"base {tot['material_base_m2']:.3f} m2 it is {tot['units_nr']:.4f} "
                                      f"({tot['units_nr'] - 2198.75:+.4f} nr = rounding of the area only)"},
        "panel_mortar_m3": {"material_base": r6(tot["panel_m3"]), "low": r6(tot["panel_m3_low"]),
                            "contract_basis": r6(tot["panel_contract_m3"]),
                            "t367_pinned_contract": t533["panel_t367_m3_pinned"]},
        "perimeter_mortar_m3": {"low": r6(tot["per_low_m3"]), "figure": r6(tot["per_fig_m3"]),
                                "high": r6(tot["per_high_m3"]),
                                "range_cause": "R-T520-1: a block-to-block junction is butt-jointed or bonded (drawings "
                                               "print no junction detail) and dome-opening pieces HELD by name"},
        "cement_bags_50kg": {"low": round(cement[0], 4), "figure": round(cement[1], 4), "high": round(cement[2], 4),
                             "rounding": "up at the purchasing group (the whole black-block mortar line), not here",
                             "waste": "HELD (not sourced)"},
        "sand_m3_loose": {"low": r6(sand[0]), "figure": r6(sand[1]), "high": r6(sand[2])},
        "ties_pcs": {"end_restated": sum(r["now"] for r in ties if r["population"] == "END"),
                     "end_walls": sorted({r["wall_id"] for r in ties if r["population"] == "END"}),
                     "interior_restated": sum(r["now"] for r in ties if r["population"] == "INTERIOR"),
                     "interior_junctions": sum(1 for r in ties if r["population"] == "INTERIOR"),
                     "ledger_measured_before": s539_old["ties_v2"]["ties_measured"], "ledger_measured_after": S539["ties_v2"]["ties_measured"],
                     "still_held_junctions": S539["ties_v2"]["held_junctions"],
                     "still_held_by_cause": S539["ties_v2"]["by_held_cause"],
                     "d39_2f_w08_tie_range": d39},
        "bed_joint_strip_ml": {"restated": round(sum(float(r["now"]) for r in strip), 4), "walls": len(strip),
                               "ledger_measured_before": s539_old["strip_v2"]["v2_measured_net_m"],
                               "ledger_measured_after": S539["strip_v2"]["v2_measured_net_m"]},
        "reproduces": {"t533_s_a_units": t533["scenarios"]["S-A"]["units_nr_material_base"],
                       "t533_s_a_panel": t533["scenarios"]["S-A"]["panel_m3_material_base"],
                       "t533_s_a_perimeter": [t533["scenarios"]["S-A"]["perimeter_m3_figure"],
                                              t533["scenarios"]["S-A"]["perimeter_m3_high"]],
                       "t533_s_a_panel_contract": t533["s_a_reproduces_t520"]["panel_contract_m3"]},
        "drawing_search": DRAWING_SEARCH, "drawing_result": DRAWING_RESULT, "not_searched": NOT_SEARCHED,
        "freelancer": "prices blockwork in m2 only (T-176): no units, mortar, ties or strip to compare; verdict UNRESOLVED "
                      "(no comparison possible)",
        "fix_rows": fix_rows(tot, cement, sand, ties, strip, S539),
        "sha256_inputs": {p: _sha(p) for p in INPUTS},
    }
    return W, acc, summary


def fix_rows(tot, cement, sand, ties, strip, S539):
    S539_OLD = json.loads((ROOT / INPUTS[7]).read_text(encoding="utf-8"))
    end = sum(r["now"] for r in ties if r["population"] == "END")
    inn = sum(r["now"] for r in ties if r["population"] == "INTERIOR")
    return [
        {"id": "FR-T615-1", "family": "B9-01 blockwork 0.15 m black (units)", "unit": "nr",
         "was": "HELD (T-533)", "now": f"{tot['units_nr_low']:.2f} .. {tot['units_nr']:.2f} theoretical",
         "status": MODULE_STATUS, "basis": "UPC-BLACK-BLOCK-001 1.1.0 x T-506 material base; procurement HELD (waste)"},
        {"id": "FR-T615-2", "family": "B9-04 joint mortar, panel, 0.15 m walls", "unit": "m3",
         "was": "HELD (T-533)", "now": f"{tot['panel_m3_low']:.6f} .. {tot['panel_m3']:.6f}", "status": MODULE_STATUS,
         "basis": "R-T533-1 identity on 40 x 20 / 39 x 19 x 0.15"},
        {"id": "FR-T615-3", "family": "B9-04 joint mortar, perimeter, 0.15 m walls", "unit": "m3",
         "was": "HELD (T-520 / T-533)", "now": f"{tot['per_low_m3']:.6f} .. {tot['per_high_m3']:.6f} "
                                               f"(figure {tot['per_fig_m3']:.6f})",
         "status": MODULE_STATUS, "basis": "R-T520-1 re-run on the register module"},
        {"id": "FR-T615-4", "family": "B9-04 mortar materials, 0.15 m walls", "unit": "bags 50 kg / m3 loose sand",
         "was": "HELD", "now": f"cement {cement[0]:.2f} .. {cement[2]:.2f}; sand {sand[0]:.3f} .. {sand[2]:.3f}",
         "status": MODULE_STATUS, "basis": "UPC-BLACK-MORTAR-001 (8 bags + 1.1 m3 per m3); waste HELD"},
        {"id": "FR-T615-5", "family": "B9-06 MAS.TIE.SHARMAT (proposed)", "unit": "pcs",
         "was": f"{S539_OLD['ties_v2']['ties_measured']} measured + 0.15 m junctions HELD", "now": f"+{end} end + {inn} interior = "
                                                                f"{S539['ties_v2']['ties_measured']} measured",
         "status": MODULE_STATUS, "basis": "T-539 V2 re-run on the 1.1.0 register (= T-355 PRIMARY course, asserted)"},
        {"id": "FR-T615-6", "family": "B9-07 MAS.MESH.BED_JOINT (proposed)", "unit": "m.l",
         "was": f"{S539_OLD['strip_v2']['v2_measured_net_m']} measured + {len(strip)} 0.15 m walls HELD",
         "now": f"+{sum(float(r['now']) for r in strip):.4f} = {S539['strip_v2']['v2_measured_net_m']:.4f} measured",
         "status": MODULE_STATUS, "basis": "T-539 V2 re-run on the 1.1.0 register"},
        {"id": "FR-T615-7", "family": "drawing check (Q-80 condition)", "unit": "-", "was": "-",
         "now": "no 15 cm block face printed on any drawing searched; nothing to report against Q-80",
         "status": "DRAWING-CONFIRMED (silence)", "basis": "DRAWING_SEARCH in SUMMARY_T615.json"},
    ]


def texts():
    W, acc, summary = build()

    def csvtext(rs):
        s = io.StringIO()
        w = csv.DictWriter(s, fieldnames=list(rs[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rs)
        return s.getvalue()
    return {"WALLS_015_T615.csv": csvtext(W), "ACCESSORIES_015_T615.csv": csvtext(acc),
            "SUMMARY_T615.json": json.dumps(summary, indent=1, ensure_ascii=False) + "\n"}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    T = texts()
    if "--check" in argv:
        bad = [k for k, v in T.items() if not (OUT / k).exists() or (OUT / k).read_text(encoding="utf-8") != v]
        print("reproduce:", "OK" if not bad else f"DIFFER {bad}")
        return 1 if bad else 0
    OUT.mkdir(exist_ok=True)
    for k, v in T.items():
        (OUT / k).write_text(v, encoding="utf-8")
    print(T["SUMMARY_T615.json"][:6000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
