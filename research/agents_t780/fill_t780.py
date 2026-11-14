"""T-780 (DELIVERY MODE fix-row set): roof layers of ARCH_TAKEOFF_V3.0.82 restated on ONE area per roof surface
(t780_rules.ROOF_LAYER_AREA_V1: the face inside the parapet / wall faces, beam tops included, less closed-upstand
footprints), and roof membrane / finish vs the freelancer split into named causes.

Reads committed, Checker-merged files only (no drawings, no client data):
  research/agents_t770/out/LINE_INDEX_V3_0_82.json   candidate of record (line ids, before-state)
  research/agents_t626/T626_DRAWN.json               roof faces by DXF handle (T-626 / T-321, merged)
  research/agents_t541/t541_inputs.py                the freelancer's one roof row (285.00 m2 / 194.00 lm, numbers only)
The +13.90 top roof inner sides 7.70 x 6.45 were re-read this run from the architectural DXF (Drive 'Alsenan chalet
project' P7757_DXF_COMPRESSED.zip, decoded into .work/private only): 2F wall inner-face lines 12B7 / 1292 (x) and
1283 / 1279 (y), outer 1288 / 1291 / 1281 / 1274 = 8.10 x 6.80 (south wall 0.15, others 0.20); dome circle 1300
r 2.205 on the 2F plan. Only the dimensions are used here.

    python3 -I research/agents_t780/fill_t780.py [--write]
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import t780_rules as R  # noqa: E402

IDX = os.path.join(ROOT, "research/agents_t770/out/LINE_INDEX_V3_0_82.json")
DRAWN = os.path.join(ROOT, "research/agents_t626/T626_DRAWN.json")
FREELANCER_ROOF_M2 = 285.00     # his one roof row (t541_inputs.FREELANCER_MEMBRANE_M2), used for membrane and finish
FREELANCER_UPTURN_LM = 194.00   # t541_inputs.FREELANCER_UPTURN_LM

# line ids per roof surface (V3.0.82): membrane, finish, insulation, protection, screed, upturn, rolls
LINES = {
    "ROOF-430": {"FIN.WP.ROOF": "L-d57d2dc2fafac8bc72d8", "FIN.ROOF.FINISH": "L-702487d5998861c463c1",
                 "FIN.ROOF.INSULATION": "L-8a5192a5ee3e40b61b08", "FIN.ROOF.PROTECTION": "L-0cb71da74613f446eee9",
                 "FIN.ROOF.SCREED": "L-bec94500648a90fb2f2a"},
    "TERRACE-550": {"FIN.WP.ROOF": "L-2f7502be6f501baf49b1", "FIN.ROOF.FINISH": "L-a6ce29981d037284ec84",
                    "FIN.ROOF.INSULATION": "L-940b7a65d7e79bc0ec33", "FIN.ROOF.PROTECTION": "L-f9e6d4f8c099f6a6cc8e",
                    "FIN.ROOF.SCREED": "L-5f018cfc13aaa9ae2210"},
    "ROOF-970": {"FIN.WP.ROOF": "L-636fd3ff1784a12e653b", "FIN.ROOF.FINISH": "L-e005eb9041acb08d8b87",
                 "FIN.ROOF.INSULATION": "L-122cbab32ca719527de8", "FIN.ROOF.PROTECTION": "L-e0dc4455bc0c6ee4fa9b",
                 "FIN.ROOF.SCREED": "L-f4ae7151a6e2b93dd7ad"},
    "ROOF-1390": {"FIN.WP.ROOF": "L-3e8fe55da71851816dd4", "FIN.ROOF.FINISH": "L-ab79aa46b9647f63b54a",
                  "FIN.ROOF.INSULATION": "L-19912fbc18556b65ccf6", "FIN.ROOF.PROTECTION": "L-c5c48bba5d23fa70e9ad",
                  "FIN.ROOF.SCREED": "L-b016c961ddf9e530e3c1", "FIN.WP.ROOF_UPTURN": "L-aac1f35e08f85b643692",
                  "FIN.WP.MEMBRANE_ROLLS": "L-90b40877c8c3da54ba1b"},
}
POOLCOURT_MEMBRANE = ("L-eff54f96bfcfcf175d58", "L-2361d6ec13c952bd2ae3")   # open-sky slab + ledge (membrane only)
T764_LINES = ("L-636fd3ff1784a12e653b", "L-aac1f35e08f85b643692", "L-90b40877c8c3da54ba1b")
TOP_INNER = (7.70, 6.45)          # DXF 12B7..1292 = 7700 mm, 1283..1279 = 6450 mm (this run)
TOP_OUTER = (8.10, 6.80)          # DXF 1288..1291, 1281..1274 (Q-34 floor plate 55.08 m2)
ROLL_RATIO = (8.0, 55.559)        # T-764 method: rolls per m2 of roof 1F-AT220 (released)


def r6(x):
    return round(x, 6)


def surfaces(drawn, byid):
    """the layer area of each roof surface by ROOF_LAYER_AREA_V1, with its basis text and label"""
    out = {}
    # +4.30 annex, +5.50 strips, +9.70 roof: the face is already the engine's membrane line (outline to the parapet /
    # wall faces, T-321 handles; +9.70 net of its two dome openings + the drawn band, T-764). The finish hatch is not
    # an area basis (R.roof_surface refuses it): layers move up to the membrane line.
    for z, why in (("ROOF-430", "annex +4.30 face to wall face B3A (T-321 handles, exact arc 55.560332; engine arc 55.559 "
                                "kept); finish hatch D1F + B2A stopped 0.640 m2 short on the D band B3C at the wall foot"),
                   ("TERRACE-550", "+5.50 strips face (T-321 handles AE3 / B25 / B33 / B5D / BDB / CED); finish hatch "
                                   "AE0 + D1A + 1252 leaves 1.078 m2 of symbol frames / door-swing gaps"),
                   ("ROOF-970", "+9.70 face 146.532 less the two dome openings 2 x 15.359 (B4 rings, Q-44 A) + drawn band "
                                "0.1575 = membrane line (T-764, merged); finish hatch 2F21 + gaps stopped on the band")):
        a = byid[LINES[z]["FIN.WP.ROOF"]]["measured_net"]
        s = R.roof_surface(a)
        s.update(basis=why, label="DRAWING-READ")
        out[z] = s
    dome3 = float(drawn["roof"]["ROOF-1390"]["circles"]["DOME-3"]["r"])
    face = R.rect_face(*TOP_INNER)
    assert abs(face - float(drawn["roof"]["ROOF-1390"]["area"])) < 1e-9
    s = R.roof_surface(face, (dome3,), parapet_inner_lm=2 * sum(TOP_INNER))
    s.update(label="ESTIMATE",
             basis=f"+13.90 top roof inside the parapet = 2F wall inner faces {TOP_INNER[0]:.2f} x {TOP_INNER[1]:.2f} = "
                   f"{face:.3f} m2 (DXF 12B7 / 1292 / 1283 / 1279, beam tops included; was slab panels 7.4543 / 0.16 = "
                   f"46.589, F-V770-1) less DOME-3 base r {dome3:.3f} = {s['footprints_m2']:.3f} m2 (S0 concrete dome "
                   f"L-d5401fa8 stands on the slab; layers stop at its base with an upturn, as at the +9.70 domes, Q-24 / "
                   f"Q-29) = {s['layer_m2']:.3f} m2; outline from the 2F walls, no roof plan: Q-34 stays with the owner")
    out["ROOF-1390"] = s
    return out


def main(write=False):
    idx = json.load(open(IDX))
    byid = {l["line_id"]: l for l in idx["lines"]}
    drawn = json.load(open(DRAWN))
    surf = surfaces(drawn, byid)
    rows = []

    def row(lid, code, unit, after, label, basis):
        l = byid[lid]
        assert l["item_code"] == code and l["unit"] == unit and l["class"] == "RELEASED", (lid, l["item_code"])
        before = l["measured_net"]
        if abs(before - after) < 5e-7:
            return
        rows.append({"line_id": lid, "item_code": code, "unit": unit, "element_id": l["element_id"],
                     "before": {"class": l["class"], "net": before, "label": l.get("method_label")},
                     "after": {"class": "RELEASED", "net": r6(after)}, "label": label, "basis": basis,
                     "restates_t764": lid in T764_LINES})

    for z, s in surf.items():
        for code, q in R.layers_for(s).items():
            unit = "m3" if code == "FIN.ROOF.SCREED" else "m2"
            b = s["basis"] if code != "FIN.ROOF.SCREED" else f"{s['layer_m2']:.3f} m2 x screed 0.075 avg (company default); " + s["basis"]
            row(LINES[z][code], code, unit, q, s["label"], b)
    top = surf["ROOF-1390"]
    row(LINES["ROOF-1390"]["FIN.WP.ROOF_UPTURN"], "FIN.WP.ROOF_UPTURN", "lm", top["upturn_lm"], "ESTIMATE",
        f"parapet inner faces 2 x ({TOP_INNER[0]:.2f} + {TOP_INNER[1]:.2f}) = {2 * sum(TOP_INNER):.2f} + DOME-3 base ring "
        f"{top['upturn_lm'] - 2 * sum(TOP_INNER):.3f} = {top['upturn_lm']:.3f} lm (was the 2F facade run 29.8 = outer "
        f"faces 2 x (8.10 + 6.80): the upturn rises on the inner face)")
    rolls = -(-top["layer_m2"] * ROLL_RATIO[0] // ROLL_RATIO[1])
    row(LINES["ROOF-1390"]["FIN.WP.MEMBRANE_ROLLS"], "FIN.WP.MEMBRANE_ROLLS", "pcs", rolls, "ESTIMATE",
        f"top roof {top['layer_m2']:.3f} m2 x 8 rolls / 55.559 m2 of roof 1F-AT220 (T-764 method kept) = "
        f"{top['layer_m2'] * ROLL_RATIO[0] / ROLL_RATIO[1]:.2f} -> {int(rolls)} rolls")

    # ---- before / after per trade and the freelancer split ------------------------------------------------------
    after = {r["line_id"]: r["after"]["net"] for r in rows}

    def tot(code, unit="m2"):
        ls = [l for l in idx["lines"] if l["item_code"] == code and l["unit"] == unit and l["class"] != "EXCLUDED"]
        blank = sum(1 for l in ls if l["measured_net"] is None and l["line_id"] not in after)
        b = sum(l["measured_net"] or 0 for l in ls)
        a = sum(after.get(l["line_id"], l["measured_net"] or 0) for l in ls)
        return b, a, blank

    face = {z: float(drawn["roof"][z]["area"]) for z in drawn["roof"]}
    domes_970 = sum(float(c["area"]) for c in drawn["roof"]["ROOF-970"]["circles"].values())
    dome_3 = top["footprints_m2"]
    pool = sum(byid[i]["measured_net"] for i in POOLCOURT_MEMBRANE)
    his_residual = FREELANCER_ROOF_M2 - sum(face.values())     # T-626: his row = the four gross faces + 0.52
    fb, fa, fblank = tot("FIN.ROOF.FINISH")
    mb, ma, mblank = tot("FIN.WP.ROOF")
    ub, ua, ublank = tot("FIN.WP.ROOF_UPTURN", "lm")
    band_970 = surf["ROOF-970"]["layer_m2"] - (face["ROOF-970"] - domes_970)
    arc_430 = face["ROOF-430"] - surf["ROOF-430"]["layer_m2"]
    fin_causes = {"RULE_DIFFERENCE dome footprints +9.70 (2 openings, B4 rings) : his row gross": domes_970,
                  "RULE_DIFFERENCE DOME-3 footprint +13.90 (S0 shell on the slab) : his row gross": dome_3,
                  "TOLERANCE +9.70 membrane line vs face less exact dome discs (band 0.1575 = arc gain)": -band_970,
                  "TOLERANCE annex corner arc discretisation (55.559 vs exact 55.560)": arc_430,
                  "UNRESOLVED residual of his row (T-626, below 1 %)": his_residual}
    mem_causes = dict(fin_causes)
    mem_causes["ENGINE_RIGHT pool-court open-sky slab + ledge +5.50 (membrane, not in his row)"] = -pool
    for name, causes, a in (("finish", fin_causes, fa), ("membrane", mem_causes, ma)):
        assert abs(FREELANCER_ROOF_M2 - a - sum(causes.values())) < 1e-4, (name, FREELANCER_ROOF_M2 - a, sum(causes.values()))
    summary = {
        "rows": len(rows), "restated_t764_lines": [r["line_id"] for r in rows if r["restates_t764"]],
        "blank_roof_lines_before": fblank + mblank + ublank, "blank_roof_lines_after": 0,
        "roof_finish_m2": {"before": r6(fb), "after": r6(fa), "freelancer": FREELANCER_ROOF_M2,
                           "after_vs_freelancer_pct": round(100 * (fa - FREELANCER_ROOF_M2) / FREELANCER_ROOF_M2, 1),
                           "causes_m2_his_minus_ours": {k: r6(v) for k, v in fin_causes.items()}},
        "roof_membrane_m2": {"before": r6(mb), "after": r6(ma), "freelancer": FREELANCER_ROOF_M2,
                             "after_vs_freelancer_pct": round(100 * (ma - FREELANCER_ROOF_M2) / FREELANCER_ROOF_M2, 1),
                             "causes_m2_his_minus_ours": {k: r6(v) for k, v in mem_causes.items()}},
        "roof_upturn_lm": {"before": r6(ub), "after": r6(ua), "freelancer": FREELANCER_UPTURN_LM,
                           "after_vs_freelancer_pct": round(100 * (ua - FREELANCER_UPTURN_LM) / FREELANCER_UPTURN_LM, 1),
                           "dome_ring_upturns_lm": r6(2 * 13.892698 + (top["upturn_lm"] - 2 * sum(TOP_INNER))),
                           "after_without_dome_rings_lm": r6(ua - 2 * 13.892698 - (top["upturn_lm"] - 2 * sum(TOP_INNER))),
                           "note": "his row's length basis is not printed; without the 3 dome-ring upturns ours is within "
                                   "1.4 % of his 194.00 (consistent with his gross-dome area): proposal, not a split"},
        "annex_membrane_line": "the annex +4.30 roof HAS a membrane line: L-d57d2dc2 1F-ROOF-AT220 55.559 m2 (= ROOF-430, "
                               "T-321 / T-702); the 13 Nov owner table note 'annex has no membrane line' is a label "
                               "mismatch (AT220 is the 1F-plan name of ROOF-430), not a missing quantity",
    }
    beside = {
        "alternative_top_roof_gross_m2": {"value": r6(top["face_m2"]), "when": "the designer's roof plan shows the dome "
                                          "membrane running under DOME-3 (no base upturn): +15.275 m2 per layer, "
                                          "-13.855 lm upturn; designer item D-62 (no roof plan)"},
        "annex_finish_on_d_band_m2": {"value": 54.9203, "when": "the D band at the annex wall foot is a built plinth on "
                                      "the slab (finish only, -0.639 m2 = 0.27 % of the roof finish trade)"},
        "missing_item_dome_extrados": "3 concrete dome shells (S0) have no outer-surface waterproofing / finish line; "
                                      "spherical cap pi (a^2 + h^2): 2 x pi (2.21^2 + 1.90^2) = 53.38 m2 + pi (2.205^2 + "
                                      "2.15^2) = 29.80 m2, about 83.2 m2 BESIDE only (no company default, no printed "
                                      "spec): Lead to route as a MISSING family / designer item, never folded into the "
                                      "roof membrane",
        "pool_court_layers": "the +5.50 pool-court open-sky slab has a membrane line (4.907 + ledge 0.640) but no "
                             "screed / insulation / protection / finish lines: its floor finish belongs to the pool-court "
                             "outdoor floor family (T-769), not added here",
    }
    out = {"schema": "DELIVERY_FIX_ROWS_V1", "task": "T-780", "candidate_version": idx["candidate_version"],
           "rule": "ROOF_LAYER_AREA_V1 (proposed, research/agents_t780/t780_rules.py)",
           "inputs": {"index": "LINE_INDEX_V3_0_82.json", "drawn": "T626_DRAWN.json (T-626 / T-321 merged)",
                      "dxf_reread": "Drive 'Alsenan chalet project' P7757_DXF_COMPRESSED.zip handles 12B7 1292 1283 1279 "
                                    "1288 1291 1281 1274 1300 (dimensions only)"},
           "summary": summary, "beside": beside,
           "surfaces": {z: {k: (r6(v) if isinstance(v, float) else v) for k, v in s.items()} for z, s in surf.items()},
           "rows": rows}
    print(json.dumps(summary, indent=1))
    if write:
        d = os.path.join(HERE, "out")
        os.makedirs(d, exist_ok=True)
        json.dump(out, open(os.path.join(d, "FIX_ROWS.json"), "w"), indent=1)
        md = [f"# T-780 fix rows on {out['candidate_version']}: roof layers on one area per roof surface", "",
              "Rule: " + out["rule"], "", "## Summary", "", "```", json.dumps(summary, indent=1), "```", "",
              "## Beside (not in any line)", ""] + [f"- {k}: {json.dumps(v)}" for k, v in beside.items()] + [
              "", "## Rows", "", "| line | item | unit | before | after | label | T-764 line | basis |",
              "|---|---|---|---|---|---|---|---|"]
        for r in rows:
            md.append(f"| {r['line_id']} | {r['item_code']} | {r['unit']} | {r['before']['net']:.3f} | "
                      f"{r['after']['net']:.3f} | {r['label']} | {'yes' if r['restates_t764'] else ''} | {r['basis']} |")
        open(os.path.join(d, "FIX_ROWS.md"), "w").write("\n".join(md) + "\n")
    return out


if __name__ == "__main__":
    main("--write" in sys.argv)
