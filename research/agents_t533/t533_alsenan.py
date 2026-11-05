"""T-533 training-villa builder: the block module of the 15 carried 0.15 m black walls (B9-04 panel + perimeter joint
mortar, block units) on R-T533-1 (block_module_v1.py).

Inputs (merged, read only; numbers and ids only, no drawing content):
  research/agents_t520/out/PERIMETER_BY_WALL_T520.csv    the 24 walls / pieces of T-367 / T-506 with the T-520 figures
  research/agents_t506/out/MORTAR_RECONCILIATION_T506.csv material base m2 (laid block, RC lintel faces taken out)
  rules/rulebook/URBAN_COMPANY_RULEBOOK_1.0.0.json        UPC-BLACK-BLOCK-001 (confirmed modules by thickness)
Result: the register has no sourced 0.15 m module -> every 0.15 m unit / mortar / cement / sand quantity stays HELD by
name (never 0, never the 0.20 m module). The scenario table re-runs the T-520 perimeter method and the panel identity
for the three modules the board already names (Q-75 options, supplier clarification list row 1): FIGURES BESIDE, NOT
QUANTITIES, so the HELD value drops in the moment a source states the module.
Writes research/agents_t533/out/: WALLS_015_T533.csv, SCENARIOS_015_T533.csv, SUMMARY_T533.json.
    python3 -I research/agents_t533/t533_alsenan.py [--check]
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
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "research" / "agents_t520"))
import block_module_v1 as BM  # noqa: E402
import t520_alsenan as A  # noqa: E402

OUT = HERE / "out"
INPUTS = ["research/agents_t520/out/PERIMETER_BY_WALL_T520.csv",
          "research/agents_t506/out/MORTAR_RECONCILIATION_T506.csv",
          "rules/rulebook/URBAN_COMPANY_RULEBOOK_1.0.0.json"]
J = 0.010                                       # owner session 2026-10-29: provisional 10 mm joint, mortared blocks
CEMENT_BAGS, SAND_M3 = 8.0, 1.1                 # UPC-BLACK-MORTAR-001 / Q-78 A (owner 2026-11-02), per m3 mortar
MIX_SOURCE = "UPC-BLACK-MORTAR-001 1.0.0 (Q-78 A owner 2026-11-02): 1:4, 8 bags 50 kg + 1.1 m3 loose sand per m3"
# the 15 carried 0.15 m walls of T-520 (beside: module HELD); GF-W22 (D-27) and 2F-W08 (D-39) are held on other causes
EXCLUDED = {"GF-W22": "D-27 area conflict on its parent (T-488), own HELD", "2F-W08": "D-39 2F storey (T-488), own HELD"}
# modules already named on the board for this datum (no new value): Q-75 option A / supplier list row 1 alternative /
# Q-75 option B. Face (w, h) and module (W, H) in m; every one is a WHAT-IF, none is a source for the 0.15 m block.
SCENARIOS = [
    ("S-A", "39 x 19 face + 10 mm = 40 x 20 module (the 0.20 m block's owner module, Q-75 option A)", (0.39, 0.19, 0.40, 0.20)),
    ("S-B", "40 x 20 actual face + 10 mm = 41 x 21 module (supplier clarification list 2026-10-23 row 1)", (0.40, 0.20, 0.41, 0.21)),
    ("S-C", "39 x 24 face + 10 mm = 40 x 25 module (Q-75 option '40x25 -> 10 per m2')", (0.39, 0.24, 0.40, 0.25)),
]
# where the 0.15 m module was looked for (ERS s.2.2 order), what each says; kept with the result for the Checker
SOURCES = [
    ("1 drawings", "architectural plans / sections / notes, structural notes p.1 note 2, p.8 notes 18-20",
     "no block product, size, joint or mix printed (T-091 printed-notes census, T-107, T-143, T-176)", "SILENT"),
    ("2 specification", "Kuwait General Specification 1990, section 04220 (Drive Engineering Sources / 01 Kuwait References)",
     "re-read 2026-11-05: read_file_content stops inside 02230 (TOC lists 04220); the 11.8 MB file is over the "
     "connector's download limit (T-489 refusal text 'File too large for download, over limit of 10 MB')", "NOT READABLE"),
    ("3 owner rule", "Q-75 answer 2026-11-02 / UPC-BLACK-BLOCK-001 1.0.0",
     "physical 40 x 19 x 19 (the 20 cm block); 12.5 per m2 only where the installed module is confirmed 40 x 20; "
     "rulebook not_given: 'the 15 cm black block installed module'", "0.20 ONLY"),
    ("3 owner data", "CLARIFICATIONS_SUPPLIER_2026-10-23.md row 1",
     "the 15 / 20 cm dimensions are the open question itself (DRAFT list, no answer recorded)", "OPEN"),
    ("4 reference", "Bayt Al-Omr, Kuwait Society of Engineers 2023 (Drive 01 Kuwait References), full text",
     "black cement block named (solid units advised at least for the first two courses); no unit size", "NO SIZE"),
    ("6 interpretation", "owner's stored takeoff notes (quantity-takeoff-rules s.2.1)",
     "'39 x 19 + 1 cm = 40 x 20 ... for 15 cm and 20 cm' is not labelled CONFIRMED; when the same text was put to the "
     "owner (Q-75 option A) the answer named the 40 x 19 x 19 block only", "NOT A SOURCE"),
]


def _csv(p):
    return list(csv.DictReader((ROOT / p).open(encoding="utf-8")))


def _sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def register():
    """the sourced module register from the company rulebook: only thicknesses the owner confirmed."""
    rb = json.loads((ROOT / INPUTS[2]).read_text(encoding="utf-8"))
    rule = next(r for r in rb["records"] if r["rule_id"] == "UPC-BLACK-BLOCK-001")
    reg = []
    for t, (W, H) in rule["params"]["confirmed_modules_m"]["value"].items():
        reg.append(BM.ModuleEntry("BLACK", float(t), round(W - J, 6), round(H - J, 6), J, J,
                                  f"UPC-BLACK-BLOCK-001 {rule['version']} ({rule['source'].split(';')[0]}); "
                                  "10 mm joint owner 2026-10-29", "OWNER_CONFIRMED"))
    return reg, rule.get("not_given", [])


def walls():
    t520 = {r["wall_id"]: r for r in _csv(INPUTS[0])}
    t506 = {r["wall_id"]: r for r in _csv(INPUTS[1])}
    ws = [r for r in t520.values() if r["t_m"] == "0.15" and r["wall_id"] not in EXCLUDED]
    if len(ws) != 15:
        raise BM.ModuleError(f"expected the 15 carried 0.15 m walls, found {len(ws)}")
    for r in ws:
        if t506[r["wall_id"]]["bucket"] != "HELD-0.15-MODULE":
            raise BM.ModuleError(f"{r['wall_id']}: T-506 bucket {t506[r['wall_id']]['bucket']}")
    return [(r, t506[r["wall_id"]]) for r in sorted(ws, key=lambda r: (["GF", "1F"].index(r["floor"]), r["wall_id"]))]


def perimeter_by_module(module):
    """T-520 R-T520-1 re-run with another module (kappa and course height both follow it); 15 walls only."""
    keep = A.MODULE
    try:
        A.MODULE = module
        rows, _ = A.build()
    finally:
        A.MODULE = keep
    ids = {w["wall_id"] for w, _ in walls()}
    sel = {r["wall_id"]: r for r in rows if r["wall_id"] in ids}
    return {k: (float(v["perimeter_figure_m3"]), float(v["perimeter_low_m3"]), float(v["perimeter_high_m3"]))
            for k, v in sel.items()}


def build():
    reg, not_given = register()
    W = walls()
    rows, tot = [], {"contract_m2": 0.0, "material_base_m2": 0.0, "material_base_low_m2": 0.0, "panel_t367_m3": 0.0}
    for w, m in W:
        q = BM.quantities(float(m["material_base_m2"]), reg, "BLACK", 0.15, CEMENT_BAGS, SAND_M3, MIX_SOURCE)
        if q["status"] != "HELD" or q["units_nr"] is not None:
            raise BM.ModuleError(f"{w['wall_id']}: 0.15 m module resolved from {q['citation']}: re-check the source")
        tot["contract_m2"] += float(w["established_m2"])
        tot["material_base_m2"] += float(m["material_base_m2"])
        # a HELD lintel (T-506: 1F-W13 D-1F-09, face 0 .. 0.34 m2) may take laid block out: low end of the base
        tot["material_base_low_m2"] += float(m["material_base_m2"]) - float(m["held_face_max_m2"] or 0.0)
        tot["panel_t367_m3"] += float(w["panel_t367_m3"])
        rows.append({"floor": w["floor"], "wall_id": w["wall_id"], "line_id": w["line_id"],
                     "area_status": w["area_status"], "contract_m2": w["established_m2"],
                     "material_base_m2": m["material_base_m2"], "required_lintels": m["required_lintels"],
                     "units_nr": "", "panel_mortar_m3": "", "perimeter_mortar_m3": "", "cement_bags": "", "sand_m3": "",
                     "status": "HELD", "held": q["held"]})
    scen = []
    for sid, label, mod in SCENARIOS:
        e = BM.ModuleEntry("BLACK", 0.15, mod[0], mod[1], round(mod[2] - mod[0], 6), round(mod[3] - mod[1], 6),
                           "WHAT-IF " + sid, "SUPPLIER_RECORD")
        p = BM.per_m2(e)
        per = perimeter_by_module(mod)
        fig, lo, hi = (sum(v[i] for v in per.values()) for i in range(3))
        panel_c = tot["contract_m2"] * p["mortar_m3_per_m2"]
        panel_b = tot["material_base_m2"] * p["mortar_m3_per_m2"]
        scen.append({"scenario": sid, "module": label, "units_per_m2": f"{p['units_per_m2']:.6f}",
                     "kappa": f"{p['kappa']:.6f}", "mortar_m3_per_m2": f"{p['mortar_m3_per_m2']:.7f}",
                     "units_nr_material_base": f"{tot['material_base_low_m2'] * p['units_per_m2']:.2f} .. {tot['material_base_m2'] * p['units_per_m2']:.2f}",
                     "panel_m3_contract_basis": f"{panel_c:.6f}",
                     "panel_m3_material_base": f"{tot['material_base_low_m2'] * p['mortar_m3_per_m2']:.6f} .. {panel_b:.6f}",
                     "perimeter_m3_figure": f"{fig:.6f}", "perimeter_m3_low": f"{lo:.6f}", "perimeter_m3_high": f"{hi:.6f}",
                     "cement_bags_panel_mb_plus_perimeter": f"{(panel_b + fig) * CEMENT_BAGS:.4f} .. {(panel_b + hi) * CEMENT_BAGS:.4f}",
                     "sand_m3_panel_mb_plus_perimeter": f"{(panel_b + fig) * SAND_M3:.6f} .. {(panel_b + hi) * SAND_M3:.6f}",
                     "label": "FIGURE BESIDE, NOT A QUANTITY (0.15 m module not sourced)"})
    return rows, scen, tot, not_given


def texts():
    rows, scen, tot, not_given = build()
    def csvtext(rs):
        s = io.StringIO()
        w = csv.DictWriter(s, fieldnames=list(rs[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rs)
        return s.getvalue()
    sa = scen[0]
    summary = {
        "rule": BM.RULE, "task": "T-533", "walls": len(rows), "excluded": EXCLUDED,
        "result": "HELD", "missing_datum": BM.MISSING_015, "rulebook_not_given": not_given,
        "contract_m2": round(tot["contract_m2"], 4), "material_base_m2": round(tot["material_base_m2"], 4), "material_base_low_m2": round(tot["material_base_low_m2"], 4),
        "lintel_faces_m2": round(tot["contract_m2"] - tot["material_base_m2"], 4),
        "panel_t367_m3_pinned": round(tot["panel_t367_m3"], 6),
        "s_a_reproduces_t520": {"panel_contract_m3": sa["panel_m3_contract_basis"], "perimeter_figure_m3": sa["perimeter_m3_figure"],
                                "perimeter_high_m3": sa["perimeter_m3_high"]},
        "scenarios": {s["scenario"]: {k: s[k] for k in ("units_per_m2", "units_nr_material_base", "panel_m3_material_base",
                                                       "perimeter_m3_figure", "perimeter_m3_high")} for s in scen},
        "sources_searched": [dict(zip(("level", "source", "finding", "verdict"), s)) for s in SOURCES],
        "mix_source": MIX_SOURCE,
        "sha256_inputs": {p: _sha(p) for p in INPUTS},
    }
    return {"WALLS_015_T533.csv": csvtext(rows), "SCENARIOS_015_T533.csv": csvtext(scen),
            "SUMMARY_T533.json": json.dumps(summary, indent=1, ensure_ascii=False) + "\n"}


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
    print(T["SUMMARY_T533.json"][:3000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
