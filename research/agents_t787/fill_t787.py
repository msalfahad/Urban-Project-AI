"""T-787 (DELIVERY MODE fix-row set, Checker flag F-V780-1): the missing DOME EXTRADOS lines.

Three concrete dome shells have a concrete line but no outer-surface line: DOME-A / DOME-B over the +9.70 roof (plan
circles DOME-W / DOME-E, B4 rings) and DOME-3 on the +13.90 top roof. This set ADDS, per dome, the membrane and the
protection on its extrados (DOME_EXTRADOS_V1, t787_rules.py) plus one rolls line; it changes no existing line (the flat
roof lines of T-780 already stop at the dome bases: footprints deducted, base upturns counted).

Evidence (read this run; dimensions only, no client data copied):
  ST7757.pdf p.7 'DETAIL OF DOME' (Drive 'Alsenan chalet project'): outer chord 442 on the springing line at the ring
    beam top, vertical 190 from that line to the OUTER crown, shell 10 -> the two +9.70 domes (ST p.5 'SEE DETAIL').
  Architectural DXF (P7757_DXF_COMPRESSED.zip): level lines 23EC / 23ED / 23EE = +5.50 / +9.70 / +13.90 (4.20 apart,
    text 2887 '+5.50'); DOME-3 elevation outline = 24 layer-5 lines, best-fit circle r 2.2044 (residual <= 4.5 mm),
    width dimension 2C86 4410 on the parapet-top line 23A6 (+14.40), height 2149 from +14.40 to the crown +16.55; the
    +9.70 dome on the other elevation is the SAME outline (every vertex 4140.0 lower), height 2CF9 1716 above its
    parapet line 279F (+10.69). So: the 2.15 / 1.72 heights are the parts visible above the parapets (not rises), and
    the architect draws all three domes as one type -> DOME-3 takes the only printed dome section (as its concrete line
    L-d5401fa8 does, T-761 DEFAULT, D-21).

    python3 -I research/agents_t787/fill_t787.py [--write]
"""
from __future__ import annotations

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import t787_rules as R  # noqa: E402

IDX = os.path.join(ROOT, "research/agents_t770/out/LINE_INDEX_V3_0_84.json")
T780 = os.path.join(ROOT, "research/agents_t780/out/FIX_ROWS.json")
FREELANCER_ROOF_M2 = 285.00          # his one roof row (t541_inputs), gross faces incl. the dome footprints
ROLL_RATIO = (8.0, 55.559)           # T-764 / T-780 method: rolls per m2 of membrane
ST_CHORD, ST_RISE, ST_T = 4.42, 1.90, 0.10   # ST p.7 DETAIL OF DOME (outer chord, rise to outer crown, shell)
ARCH_R = 2.205                       # architectural plan / elevation circle r (DXF 1300 r 2.2050; fit 2.2044)

DOMES = {
    # dome: (concrete line, plan circle, label, basis of the shell geometry)
    "DOME-A": ("L-8ea34765d16b54898140", "DOME-W (12EB, +9.70 roof)", "DRAWING-READ",
               "ST p.7 DETAIL OF DOME printed for this dome (ST p.5 SEE DETAIL): outer chord 4.42 at the ring-beam top, "
               "rise 1.90 to the outer crown"),
    "DOME-B": ("L-fffa895ed96b9d6a682c", "DOME-E (2F33, +9.70 roof)", "DRAWING-READ",
               "ST p.7 DETAIL OF DOME printed for this dome (ST p.5 SEE DETAIL): outer chord 4.42 at the ring-beam top, "
               "rise 1.90 to the outer crown"),
    "DOME-3": ("L-d5401fa8986900c66c37", "DOME-3 (1300, +13.90 top roof)", "DEFAULT",
               "no structural section for the 2F dome (D-21); the architect draws it with the identical outline as the "
               "+9.70 domes (elevation polyline 4140.0 apart, same 4.41 width), so the only printed shell 4.42 / 1.90 "
               "applies, as on its concrete line L-d5401fa8 (T-761); the elevation 2.15 is the part above the +14.40 "
               "parapet top, not the rise (T-780 beside read it as a rise: 29.80 refused)"),
}


def r6(x):
    return round(x + 0.0, 6)


def main(write=False):
    idx = json.load(open(IDX))
    byid = {l["line_id"]: l for l in idx["lines"]}
    t780 = json.load(open(T780))
    shell = R.extrados(ST_CHORD, ST_RISE)
    # hand check: pi (2.21^2 + 1.90^2) = pi x 8.4941 = 26.6849
    assert abs(shell["area_m2"] - math.pi * (2.21 ** 2 + 1.90 ** 2)) < 1e-9
    arch_hemi = 2 * math.pi * ARCH_R ** 2
    new, surfaces = [], {}
    for d, (conc, circle, label, why) in DOMES.items():
        c = byid[conc]
        assert c["item_code"] == "STR.CONC.DOME" and c["class"] == "RELEASED", (d, c["item_code"], c["class"])
        # no existing line already covers this dome's outer face
        assert not any(("EXTRADOS" in str(l.get("element_id") or "").upper()) for l in idx["lines"])
        a = shell["area_m2"]
        surfaces[d] = {"concrete_line": conc, "plan_circle": circle, "chord_m": ST_CHORD, "rise_m": ST_RISE,
                       "R_m": r6(shell["R_m"]), "extrados_m2": r6(a), "label": label}
        lab_layer = "DEFAULT"   # company roof default build-up applied to a shell (no printed dome build-up, D-DOME)
        for code, q in R.dome_layers(a).items():
            what = "membrane" if code == "FIN.WP.ROOF" else "protection"
            el = f"DOME:{d}:EXTRADOS:{what.upper()}"
            new.append({"family": "B8-06" if code == "FIN.WP.ROOF" else "B13-01", "line_id": f"NEW:{el}",
                        "item_code": code, "unit": "m2", "element_id": el, "label": lab_layer,
                        "basis": f"{d} extrados {what} (company roof default on the shell; screed / insulation / tile "
                                 f"finish not printed on a shell, designer item D-DOME): pi (2.21^2 + 1.90^2) = "
                                 f"{a:.3f} m2 [{label}: {why}]; flat roof {circle} footprint already deducted with "
                                 f"its base upturn (T-780): no double count",
                        "net": r6(q)})
    total = sum(s["extrados_m2"] for s in surfaces.values())
    rolls = math.ceil(total * ROLL_RATIO[0] / ROLL_RATIO[1])
    new.append({"family": "B8-05", "line_id": "NEW:DOME:ALL:EXTRADOS:wp_rolls_to_buy",
                "item_code": "FIN.WP.MEMBRANE_ROLLS", "unit": "pcs",
                "element_id": "DOME:ALL:EXTRADOS:wp_rolls_to_buy", "label": "ESTIMATE",
                "basis": f"3 dome extrados {total:.3f} m2 x 8 rolls / 55.559 m2 (T-764 / T-780 method) = "
                         f"{total * ROLL_RATIO[0] / ROLL_RATIO[1]:.2f} -> {rolls} rolls",
                "net": float(rolls)})

    # ---- roof membrane vs the freelancer (T-780 after-state + these lines) ------------------------------------------
    mem = t780["summary"]["roof_membrane_m2"]
    fin = t780["summary"]["roof_finish_m2"]
    after_mem = mem["after"] + total
    causes = dict(mem["causes_m2_his_minus_ours"])
    causes["RULE_DIFFERENCE dome extrados (3 shells, curved area) : not in his row"] = -total
    assert abs(FREELANCER_ROOF_M2 - after_mem - sum(causes.values())) < 1e-4
    summary = {
        "new_lines": len(new), "changed_lines": 0, "domes": 3, "domes_without_extrados_line_before": 3,
        "domes_without_extrados_line_after": 0,
        "extrados_m2_per_dome": r6(shell["area_m2"]), "extrados_m2_total": r6(total),
        "t780_beside_estimate_m2": 83.18, "t780_beside_error": "DOME-3 rise 2.15 = elevation height above the +14.40 "
                                                            "parapet, not the rise: 29.80 -> 26.685 m2 (-3.11)",
        "roof_membrane_m2": {"before_t787": mem["after"], "after": r6(after_mem), "freelancer": FREELANCER_ROOF_M2,
                             "after_vs_freelancer_pct": round(100 * (after_mem - FREELANCER_ROOF_M2) /
                                                              FREELANCER_ROOF_M2, 1),
                             "causes_m2_his_minus_ours": {k: r6(v) for k, v in causes.items()},
                             "like_for_like_note": f"his 285 counts the dome footprints flat (45.99 m2 of plan); the "
                                                   f"curved shells are {total:.2f} m2: the +{total - 45.992784:.2f} m2 "
                                                   f"is the curvature, a RULE_DIFFERENCE, not an error either side"},
        "roof_finish_m2": {"unchanged": fin["after"], "why": "the flat-roof tile finish does not sit on a shell"},
        "rolls_pcs": rolls,
    }
    beside = {
        "arch_hemisphere_alternative_m2": {"per_dome": r6(arch_hemi), "total": r6(3 * arch_hemi),
                                           "when": "the designer confirms the domes are built to the architect's "
                                                   "hemisphere outline (r 2.205, rise = r) instead of the ST 4.42 / "
                                                   "1.90 section: +3.86 m2 per dome per layer (D-DOME)"},
        "intrados_check": "FIN.DOME.SOFFIT 24.150 m2 per dome (T-768, inner cap R - 0.10, h - 0.10) < extrados 26.685: "
                          "consistent shell, outer minus inner = 2.535 m2",
        "screed_insulation_on_shell": "not printed on any section; not added (company default stops at the flat roof); "
                                      "D-DOME asks the build-up",
        "ring_beam_outer_face": "the exposed ring / drum face between the roof and the springing is the base upturn "
                                "(lm) of T-780, not part of the extrados",
    }
    out = {"schema": "URBAN_FIX_ROWS_V1", "task": "T-787", "candidate_version": idx["candidate_version"],
           "rule": "DOME_EXTRADOS_V1 (proposed, research/agents_t787/t787_rules.py)",
           "inputs": {"index": "LINE_INDEX_V3_0_84.json", "t780": "research/agents_t780/out/FIX_ROWS.json (merged)",
                      "drawings": "Drive 'Alsenan chalet project' ST7757.pdf p.7; P7757_DXF_COMPRESSED.zip handles "
                                  "23EC 23ED 23EE 2887 23A6 2C86 279F 2CF9 1F95..1FAC 25C8..25DB (dimensions only)"},
           "summary": summary, "beside": beside, "surfaces": surfaces, "rows": [], "new_lines": new}
    print(json.dumps(summary, indent=1))
    if write:
        d = os.path.join(HERE, "out")
        os.makedirs(d, exist_ok=True)
        json.dump(out, open(os.path.join(d, "FIX_ROWS.json"), "w"), indent=1)
        md = [f"# T-787 fix rows on {out['candidate_version']}: dome extrados lines", "", "Rule: " + out["rule"], "",
              "## Summary", "", "```", json.dumps(summary, indent=1), "```", "", "## Beside (not in any line)", ""]
        md += [f"- {k}: {json.dumps(v)}" for k, v in beside.items()]
        md += ["", "## New lines", "", "| element | item | unit | figure | label | basis |", "|---|---|---|---|---|---|"]
        md += [f"| {n['element_id']} | {n['item_code']} | {n['unit']} | {n['net']:.3f} | {n['label']} | {n['basis']} |"
               for n in new]
        open(os.path.join(d, "FIX_ROWS.md"), "w").write("\n".join(md) + "\n")
    return out


if __name__ == "__main__":
    main("--write" in sys.argv)
