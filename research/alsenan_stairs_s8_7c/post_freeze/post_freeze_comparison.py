"""S8.7C post-freeze comparison: the frozen design resolution study against the earlier figures, after the freeze.

    python3 -I research/alsenan_stairs_s8_7c/post_freeze/post_freeze_comparison.py

Reads the frozen S8.7C study (and the S8.7 / S8.7A / S8.7B manifests; all verified before and after, never written),
then the earlier figures S8.7C did not read before its freeze:
  * the old Urban V3b C-STAIR line and its code method, reproduced here from the stated inputs;
  * the S8.7B post-freeze owner-scenario main-stair figures;
  * the PRE-S8 stair rows (02 CONCRETE_QUANTITY_STATE / MISSING_INFORMATION);
  * the R5 architectural stair register (its riser method);
  * the S8.7 and S8.7A post-freeze ranges.
Every difference is classified (NO_DIFFERENCE, AUTHORITY, SCOPE, METHOD, MISSED_OBJECT, NOT_COMPARABLE) and
explained. Nothing here changes a frozen quantity, chooses an arrangement or releases anything.
"""

from __future__ import annotations

import csv
import io
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
ROOT = PKG.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import delta_release as DR  # noqa: E402

R = ROOT / "research"
V3B_LINES = ROOT / "tests/alsenan/registers_v3b/BOQ_LINES_V3B.json"
R5_STAIRS = R / "alsenan_arch_truth_05/registers/STAIR_ARCHITECTURAL_REGISTER.json"
PRE_S8 = R / "pre_s8_structural_completeness"
S87_PF = R / "alsenan_stairs_s8_7/post_freeze/03_POST_FREEZE_SUMMARY.json"
S87A_PF = R / "alsenan_stairs_s8_7a/post_freeze/03_POST_FREEZE_SUMMARY.json"
S87B_PF = R / "alsenan_stairs_s8_7b/post_freeze/03_POST_FREEZE_SUMMARY.json"
S87B_SUMMARY = R / "alsenan_stairs_s8_7b/14_RELEASE_SUMMARY.json"
MANIFEST = PKG / "13_S8_7C_FREEZE_MANIFEST.json"
OTHER = [R / "alsenan_stairs_s8_7/17_S8_7_FREEZE_MANIFEST.json",
         R / "alsenan_stairs_s8_7a/15_S8_7A_CORRECTION_MANIFEST.json",
         R / "alsenan_stairs_s8_7b/16_S8_7B_FREEZE_MANIFEST.json"]
OUT = ["01_POST_FREEZE_COMPARISON.csv", "02_CANDIDATES_VS_EARLIER_FIGURES.csv", "03_POST_FREEZE_SUMMARY.json",
       "00_POST_FREEZE_README.md"]
WAISTS = ("150", "160", "175", "200")
V3B_RISE_M = {"A1": 4.50, "A2": 4.20}
V3B_LANDINGS = {"A1": 2, "A2": 1}
OWNER_28_KEY = "main stair GF -> 1F (OWNER-28)"


def _rows(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _r(v, nd=6):
    return None if v is None else round(float(v) + 0.0, nd) + 0.0


def _cell(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, float):
        s = f"{v:.9f}"
        s = s.rstrip("0").rstrip(".") if "." in s else s
        return "0" if s in ("-0", "") else s
    if isinstance(v, (list, dict)):
        return json.dumps(v, ensure_ascii=False, sort_keys=True)
    return str(v)


def _csv(name, rows):
    keys = list(dict.fromkeys(k for r in rows for k in r))
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=keys, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: _cell(r.get(k)) for k in keys})
    (HERE / name).write_text(buf.getvalue(), encoding="utf-8")


def v3b_method():
    """V3b's code method per storey (from its stated inputs): n = ceil(H / 0.175), one slope of (n - 1) goings of
    0.30, width 1.15, waist 0.16, flat W x W quarters (two on GF -> 1F, one on 1F -> 2F)."""
    out = {}
    for run, H in V3B_RISE_M.items():
        n = math.ceil(H / 0.175 - 1e-9)
        R_ = H / n
        slope = math.hypot((n - 1) * 0.30, H)
        conc = slope * 1.15 * 0.16 + n * R_ * 0.30 / 2 * 1.15 + 1.15 * 1.15 * V3B_LANDINGS[run] * 0.16
        out[run] = {"risers": n, "riser_mm": R_ * 1000, "concrete_m3": round(conc, 4)}
    return out


def compare():
    pre = DR.verify_frozen(MANIFEST, ROOT)
    pre_o = [DR.verify_frozen(m, ROOT)["manifest_sha256"] for m in OTHER]
    s = json.loads((PKG / "11_RELEASE_SUMMARY.json").read_text(encoding="utf-8"))
    gf = {r["SCENARIO"]: r for r in _rows(PKG / "02_GF_1F_27_VS_28_GEOMETRY.csv")}
    conc = _rows(PKG / "07_CONDITIONAL_CONCRETE_COMPARISON.csv")
    a1l1 = {w: float(next(r["GROSS_M3"] for r in conc if r["SCENARIO"] == "A-28" and r["WAIST_MM"] == w
                          and r["COMPONENT"].startswith("landing A1-L1"))) for w in WAISTS}
    tot = s["concrete_m3_by_waist"]
    v3 = v3b_method()
    v3_lines = {l["code"]: l for l in json.loads(V3B_LINES.read_text(encoding="utf-8"))["lines"]}
    c = v3_lines["C-STAIR"]["release"]["commercial"]
    v3_sum = round(sum(x["concrete_m3"] for x in v3.values()), 4)
    s87b = json.loads(S87B_SUMMARY.read_text(encoding="utf-8"))["concrete_sensitivity_m3_by_waist"]
    s87b_pf = json.loads(S87B_PF.read_text(encoding="utf-8"))
    # 02: each GF -> 1F candidate as a whole flight-to-floor stair (new gross + the S8.7 landing plate) against V3b's
    # GF -> 1F share and S8.7B's frozen owner-28
    cand = []
    for sid in ("A-28", "B-27-S", "B-27-SM", "REF-25"):
        for w in WAISTS:
            whole = tot[sid][w]["gross"] + a1l1[w]
            cand.append({"SCENARIO": sid, "WAIST_MM": int(w), "RISERS": int(gf[sid]["TOTAL_RISERS"]),
                         "STATUS": gf[sid]["STATUS"], "S8_7C_NEW_GROSS_M3": tot[sid][w]["gross"],
                         "S8_7C_NEW_NET_M3": tot[sid][w]["net"], "S8_7_A1_L1_PLATE_M3": _r(a1l1[w], 9),
                         "WHOLE_GF_1F_GROSS_M3": _r(whole, 9),
                         "V3B_GF_1F_METHOD_M3": v3["A1"]["concrete_m3"],
                         "MINUS_V3B_M3": _r(whole - v3["A1"]["concrete_m3"], 6),
                         "S8_7B_OWNER_28_GROSS_M3": s87b[OWNER_28_KEY][w]["gross"],
                         "MINUS_S8_7B_OWNER_28_M3": _r(tot[sid][w]["gross"] - s87b[OWNER_28_KEY][w]["gross"], 9),
                         "LANE": "RESEARCH_SENSITIVITY_NOT_RELEASED"})
    _csv(OUT[1], cand)
    get = {(x["SCENARIO"], str(x["WAIST_MM"])): x for x in cand}
    same = max(abs(get[("A-28", w)]["MINUS_S8_7B_OWNER_28_M3"]) for w in WAISTS)
    main_b = {w: _r(s87b_pf["owner_scenario_main_stair_m3_by_waist"][w] - tot["A-28"][w]["gross"]
                    + tot["B-27-S"][w]["gross"], 6) for w in WAISTS}
    rows = []
    rows.append({"REFERENCE": "V3b riser count GF -> 1F", "UNIT": "risers",
                 "REFERENCE_VALUE": f"{v3['A1']['risers']} ({_r(v3['A1']['riser_mm'], 3)} mm)",
                 "REFERENCE_METHOD": "ceil(H / 0.175); no drawing counted",
                 "S8_7C": "drawn: 28 (structural sheet), 27 (section A-A), 25 (architectural plan); most consistent: "
                          "27 (B-27-S)",
                 "CLASS": "METHOD",
                 "EXPLANATION": f"{v3['A1']['risers']} is drawn nowhere. With {v3['A1']['risers']} equal risers the "
                                f"printed +3.50 would need {_r(2500 / v3['A1']['riser_mm'], 2)} risers, so V3b's count "
                                "cannot reach the printed half-landing either"})
    rows.append({"REFERENCE": "V3b C-STAIR, GF -> 1F share (method reproduced)", "UNIT": "m3",
                 "REFERENCE_VALUE": f"{v3['A1']['concrete_m3']} of {c['qty']} (commercial {c['class']})",
                 "REFERENCE_METHOD": c["method"],
                 "S8_7C": "whole GF -> 1F at 160 (new gross + S8.7 plate): A-28 "
                          f"{get[('A-28', '160')]['WHOLE_GF_1F_GROSS_M3']}, B-27-S "
                          f"{get[('B-27-S', '160')]['WHOLE_GF_1F_GROSS_M3']}, B-27-SM "
                          f"{get[('B-27-SM', '160')]['WHOLE_GF_1F_GROSS_M3']}",
                 "CLASS": "METHOD + SCOPE",
                 "EXPLANATION": "V3b uses one straight slope of 25 goings, a 1.15 m width and two flat 1.15 x 1.15 "
                                "quarters; S8.7C uses the drawn two flights, the winder turn on its walking line, a "
                                "1.20 m width and the S8.7 landing, with the beam and column zones kept apart"})
    rows.append({"REFERENCE": "S8.7B frozen owner-28 GF -> 1F (new gross / NET by waist)", "UNIT": "m3",
                 "REFERENCE_VALUE": {w: s87b[OWNER_28_KEY][w] for w in WAISTS},
                 "REFERENCE_METHOD": "S8.7B section integral, winder plane-equivalent, outline-intersected cut-out",
                 "S8_7C": {w: tot["A-28"][w] for w in WAISTS},
                 "CLASS": "NO_DIFFERENCE",
                 "EXPLANATION": f"A-28 reproduces S8.7B within {_r(same * 1e6, 3)} x 1e-6 m3: S8.7B publishes its "
                                "winder tread areas to 1e-6 m2, and S8.7C cuts column 36B by its read rectangle rather "
                                "than by the outline intersection"})
    rows.append({"REFERENCE": "S8.7B post-freeze owner-scenario main stair (both storeys, new gross + plates)",
                 "UNIT": "m3", "REFERENCE_VALUE": s87b_pf["owner_scenario_main_stair_m3_by_waist"],
                 "REFERENCE_METHOD": "OWNER-28 (GF -> 1F) + OWNER-27 (1F -> 2F) + the S8.7 plates",
                 "S8_7C": f"with section A-A's 27 (B-27-S) for GF -> 1F instead: {main_b}",
                 "CLASS": "SCOPE",
                 "EXPLANATION": "the 1F -> 2F owner 27 is unchanged; replacing GF -> 1F 28 by the section's 27 "
                                f"changes the main stair by {_r(main_b['160'] - s87b_pf['owner_scenario_main_stair_m3_by_waist']['160'], 6)} "
                                "m3 at 160 (two fewer lower risers, one more winder)"})
    census = [r for r in _rows(PRE_S8 / "02_STRUCTURAL_ELEMENT_CENSUS.csv") if r["ELEMENT_ID"].startswith("SPC-STAIR-SP")]
    miss = sorted({r["MISSING_INFORMATION"] for r in census})
    rows.append({"REFERENCE": f"PRE-S8 02 stair rows ({len(census)})", "UNIT": "-",
                 "REFERENCE_VALUE": sorted({r["CONCRETE_QUANTITY_STATE"][:60] for r in census}),
                 "REFERENCE_METHOD": f"missing: {miss}",
                 "S8_7C": "riser height: GF -> 1F narrowed to the section's 27 (printed +3.50) against the structural "
                          "sheet's 28, each needing stated drawing changes; landing levels: GF -> 1F printed, 1F -> 2F "
                          "+7.989 with 27 (not printed; the section scales +7.69); waist: still UNKNOWN",
                 "CLASS": "AUTHORITY",
                 "EXPLANATION": "the missing items remain engineer / architect decisions; S8.7C reduces the choice, it "
                                "does not make it"})
    r5 = json.loads(R5_STAIRS.read_text(encoding="utf-8"))
    rows.append({"REFERENCE": "R5 stair register", "UNIT": "risers",
                 "REFERENCE_VALUE": f"{len(r5['runs'])} straight tread sets; riser_count_candidate = tread lines + 1; "
                                    f"riser height {r5['riser_height']['state']}",
                 "REFERENCE_METHOD": "plan tread lines only",
                 "S8_7C": "every riser line read by handle (S8.7B 12), the winder radials and their fan centre, section "
                          "A-A's turn treads measured",
                 "CLASS": "METHOD + MISSED_OBJECT",
                 "EXPLANATION": "R5 misses the winder and curved risers and the section, which is where the 27 / 28 "
                                "question is decided"})
    for p, ref, key in ((S87_PF, "S8.7 post-freeze released + sensitivity (all four stairs)",
                         "s8_7_released_plus_sensitivity_m3"),
                        (S87A_PF, "S8.7A post-freeze main-stair whole-stair range (drawn counts)",
                         "s8_7a_main_stair_whole_m3_range")):
        x = json.loads(p.read_text(encoding="utf-8"))
        rows.append({"REFERENCE": ref, "UNIT": "m3", "REFERENCE_VALUE": x[key],
                     "REFERENCE_METHOD": "context only (never a quantity)",
                     "S8_7C": f"GF -> 1F only, whole at 160: A-28 {get[('A-28', '160')]['WHOLE_GF_1F_GROSS_M3']} / "
                              f"B-27-S {get[('B-27-S', '160')]['WHOLE_GF_1F_GROSS_M3']}",
                     "CLASS": "NOT_COMPARABLE",
                     "EXPLANATION": "different scope (S8.7C compares GF -> 1F arrangements only); all research "
                                    "context, none released"})
    _csv(OUT[0], rows)
    summ = {"round": "S8_7C_POST_FREEZE", "frozen_manifest_sha256": pre["manifest_sha256"],
            "other_manifests_sha256": pre_o, "rows": len(rows),
            "classes": {k: sum(1 for r in rows if r["CLASS"] == k) for k in sorted({r["CLASS"] for r in rows})},
            "v3b_c_stair_commercial_m3": c["qty"], "v3b_method_reproduced_m3": v3_sum,
            "v3b_reproduced_exactly": abs(v3_sum - c["qty"]) < 5e-5,
            "v3b_risers": {k: v["risers"] for k, v in v3.items()},
            "v3b_gf_1f_method_m3": v3["A1"]["concrete_m3"],
            "a_28_minus_s8_7b_owner_28_max_m3": _r(same, 9),
            "whole_gf_1f_gross_m3_at_160": {sid: get[(sid, "160")]["WHOLE_GF_1F_GROSS_M3"]
                                            for sid in ("A-28", "B-27-S", "B-27-SM", "REF-25")},
            "main_stair_with_b_27_s_m3_by_waist": main_b,
            "most_consistent_gf_1f": s["most_consistent_gf_1f"]["scenario"],
            "release_delta": s["release_delta"],
            "rule": "explains differences only; no frozen quantity is changed, no arrangement is chosen, nothing is "
                    "released"}
    (HERE / OUT[2]).write_text(json.dumps(summ, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    (HERE / OUT[3]).write_text(readme(summ), encoding="utf-8")
    post = DR.verify_frozen(MANIFEST, ROOT)
    assert post["manifest_sha256"] == pre["manifest_sha256"]
    assert [DR.verify_frozen(m, ROOT)["manifest_sha256"] for m in OTHER] == pre_o
    return summ


def readme(s):
    w = s["whole_gf_1f_gross_m3_at_160"]
    mb = " / ".join(f"{s['main_stair_with_b_27_s_m3_by_waist'][k]:.3f}" for k in WAISTS)
    return f"""# S8.7C post-freeze comparison

This comparison ran after the S8.7C freeze. The S8.7C, S8.7, S8.7A and S8.7B manifests were verified before and after,
and nothing frozen was written. Classes: {json.dumps(s['classes'])}.

## V3b

V3b's commercial C-STAIR figure, {s['v3b_c_stair_commercial_m3']} m3, reproduces from its stated method as
{s['v3b_method_reproduced_m3']} m3. Its GF -> 1F share is {s['v3b_gf_1f_method_m3']} m3, from
{s['v3b_risers']['A1']} risers.

- **V3b's {s['v3b_risers']['A1']} risers are drawn nowhere.** The drawings show 28 (structural sheet), 27 (section
  A-A) and 25 (architectural plan). Like 28, V3b's count cannot reach the printed +3.50 with equal risers.
- **The whole GF -> 1F stair at a 160 mm waist** (new gross plus the S8.7 landing plate) is:
  - A-28: {w['A-28']:.3f} m3;
  - B-27-S: {w['B-27-S']:.3f} m3;
  - B-27-SM: {w['B-27-SM']:.3f} m3;
  - REF-25: {w['REF-25']:.3f} m3.
- **The difference is method and scope.** V3b uses one straight slope, a 1.15 m width and two flat quarters, where
  the drawings show two flights, a winder turn and a 1.20 m width.

## S8.7B

- **A-28 reproduces S8.7B's frozen owner-28 GF -> 1F** within {s['a_28_minus_s8_7b_owner_28_max_m3']:.1e} m3. The
  difference comes from S8.7B's tread areas being published to 1e-6 m2 and from the column cut-out method.
- **Replacing GF -> 1F 28 with section A-A's 27** changes S8.7B's main-stair research figure to {mb} m3 at a
  150 / 160 / 175 / 200 mm waist. The 1F -> 2F owner 27 is unchanged.

## Other references

- **PRE-S8:** the stair rows' missing information remains with the engineer and architect. S8.7C narrows the GF ->
  1F riser question to {s['most_consistent_gf_1f']} (section A-A) against the structural sheet's 28. It does not
  decide it.
- **R5:** its tread-lines + 1 method misses the winders, the curved risers and the section.

Nothing here is released. The release delta stays 0 m3 and 0 kg.
"""


if __name__ == "__main__":
    print(json.dumps(compare(), indent=1))
