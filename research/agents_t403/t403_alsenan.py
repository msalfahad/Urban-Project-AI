"""T-403 development villa: the plot boundary wall below N.G., run by run (values only; no coordinates, no names).

    python3 -I research/agents_t403/t403_alsenan.py          # print and compare with summary_t403.json
    python3 -I research/agents_t403/t403_alsenan.py --write  # rebuild summary_t403.json

Inputs: ALSENAN_T403_INPUT.json (t403_extract.py on the Drive copy of 'ST7757 dxf.dxf') and the printed facts below,
each with its sheet. Nothing is taken from the freelancer or the engine; the freelancer rows are compared afterwards.
"""

from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import t403_rules as R  # noqa: E402

INP = json.load(open(os.path.join(HERE, "ALSENAN_T403_INPUT.json"), encoding="utf-8"))
OUT = os.path.join(HERE, "summary_t403.json")

# Printed facts (ST7757.pdf; read at 300 dpi this run)
TYPICAL = {
    "ref": "ST p.14 TYPICAL BOUNDARY WALL section A-A + plan; p.3 legend 'Typical Boundary Wall' (hatch S-HAT.BAT "
           "AR-B816C 7FD / 7FB, AR-B816 80F fill exactly the S-BOUN bands 7FE / 7FC / 810)",
    "upper_b": 0.20, "upper_d": 0.40,            # A-A: '20' width, '40' depth of the upper G.B, top at 'N.G. LEVEL'
    "lower_b": 0.20,                             # A-A: lower G.B the wall's width; foundation plan band 0.20 (1658 / 1659)
    "lower_d_readings": [0.40, 0.60],            # depth NOT written in A-A: p.14 plan 'GROUND BEAM (20x40)' vs p.10 'B.W 20 x 60'
    "blinding_t": 0.10,                          # A-A '10' plain concrete under the pad and the beam
    "pad": [1.30, 0.80, 0.30],                   # A-A / plan '(130x80x30)', '80' includes the beam's 20, '30'
    "pad_share_owner": None,                     # not printed (T-356 R-T356-4)
    "column_w": 0.30, "column_t": 0.20,          # '(20x30) R.C COLUMNS 4d14', 0.20 = the wall thickness
    "formation": {"at_least": 1.50, "source": "PRINTED_GENERAL_MINIMUM"},  # p.9 note 1 (excavation >= 1.5 m below the
    # existing plot level); A-A ties the brick to 'AS PER EXCAVATION DEPTH BELOW N.G. LEVEL'; Q-21 C: a minimum, not the level
}

RUNS = INP["runs"]
FE = RUNS["FENCE_7FE"]
X = {k: dict(v["footing_crossings_m"]) for k, v in RUNS.items()}
# T-253 / T-396 run allocation (corner squares once, in the north run): 7FE = north 31.37 + street 8.10 + sea-N 2.25
NORTH = 31.37
STREET = 8.10
SEA_N = round(FE["lower_band_axis_m"] - NORTH - STREET, 4)
FENCE_RUNS = [
    {"id": "F-NORTH", "class": "FENCE", "axis_m": NORTH, "crossing_m": 0.0, "section_ref": "TYP", "columns": None},
    {"id": "F-STREET", "class": "FENCE", "axis_m": STREET, "crossing_m": X["FENCE_7FE"].get("F:1668", 0.0),
     "section_ref": "TYP", "columns": None},
    {"id": "F-SEA-N", "class": "FENCE", "axis_m": SEA_N, "crossing_m": 0.0, "section_ref": "TYP", "columns": None},
    {"id": "F-SEA-S", "class": "FENCE", "axis_m": RUNS["FENCE_7FC"]["lower_band_axis_m"],
     "crossing_m": sum(X["FENCE_7FC"].values()), "section_ref": "TYP", "columns": None},
    {"id": "F-PASSAGE", "class": "FENCE", "axis_m": RUNS["FENCE_810"]["lower_band_axis_m"],
     "crossing_m": sum(X["FENCE_810"].values()), "section_ref": "TYP", "columns": None},
]
OTHER = [{"id": k, "class": v["class"], "axis_m": v["lower_band_axis_m"], "crossing_m": round(sum(dict(v["footing_crossings_m"]).values()), 4)}
         for k, v in sorted(RUNS.items()) if v["class"] != "FENCE"]
VILLA = {"unit": "m", "band_axis_m": INP["lower_band"]["axis_m"], "sections": {"TYP": TYPICAL},
         "runs": FENCE_RUNS, "other_runs": OTHER}

# Freelancer rows (quantities only; RC workbook sheets 'القواعد' r32 and 'الشناجات' r15, blockwork 'الكميات' r150)
FREELANCER = {"lower_band": (71.7, 0.20, 0.60), "upper_gb": (42.0, 0.30, 0.60), "fence_above_ng_m2": 74.40}


def build():
    res = R.takeoff(VILLA)
    fence_axis = round(sum(r["axis_m"] for r in FENCE_RUNS), 4)
    fence_x = round(sum(r["crossing_m"] for r in FENCE_RUNS), 4)
    # whole lower band (line L-6290a9f3) split by owner class: free x 0.20 x 0.40 .. drawn x 0.20 x 0.60
    split = {}
    for name, ax, xx in [("FENCE", fence_axis, fence_x)] + [(o["id"], o["axis_m"], o["crossing_m"]) for o in OTHER]:
        split[name] = {"axis_m": round(ax, 4), "crossing_m": round(xx, 4), "free_m": round(ax - xx, 4),
                       "solid_low_m3": round((ax - xx) * 0.2 * 0.4, 6), "solid_high_m3": round(ax * 0.2 * 0.6, 6),
                       "owner_method_A_m3": round((ax - xx) * 0.2 * 0.6, 6)}
    tot = {k: round(sum(v[k] for v in split.values()), 6) for k in ("axis_m", "crossing_m", "free_m", "solid_low_m3",
                                                                     "solid_high_m3", "owner_method_A_m3")}
    # freelancer
    fl, fu = FREELANCER["lower_band"], FREELANCER["upper_gb"]
    his_lo, his_up = fl[0] * fl[1] * fl[2], fu[0] * fu[1] * fu[2]
    up_gross = res["totals"]["UPPER_GB_at_most_m3"]
    L_up = fence_axis
    up_causes = {"length (44.07 vs 42.0) at his section": round((L_up - fu[0]) * fu[1] * fu[2], 6),
                 "width (printed 0.20 vs his 0.30)": round(L_up * (0.20 - fu[1]) * fu[2], 6),
                 "depth (printed 0.40 vs his 0.60)": round(L_up * 0.20 * (0.40 - fu[2]), 6)}
    up_causes["residual"] = round(up_gross - his_up - sum(up_causes.values()), 6)
    out = {
        "schema": "URBAN_T403_SUMMARY_V1",
        "input_sha_note": INP["source"]["sha256"][:8],
        "fence_band": {"axis_m": fence_axis, "crossing_m": fence_x, "free_m": round(fence_axis - fence_x, 4),
                       "upper_gb_len_by_area_m": INP["upper_gb_total_len_by_area_m"]},
        "takeoff": res,
        "lower_band_split_L6290a9f3": {"by_class": split, "total": tot},
        "freelancer": {
            "upper_gb": {"his_m3": round(his_up, 6), "ours_gross_m3": up_gross, "diff_m3": round(up_gross - his_up, 6),
                         "diff_pct_of_his": round(100 * (up_gross - his_up) / his_up, 2), "causes": up_causes},
            "lower_band_whole": {"his_m3": round(his_lo, 6), "ours_range_m3": [tot["solid_low_m3"], tot["solid_high_m3"]],
                                 "owner_A_m3": tot["owner_method_A_m3"],
                                 "owner_A_minus_his_m3": round(tot["owner_method_A_m3"] - his_lo, 6),
                                 "length_cause_m": round(tot["free_m"] - fl[0], 4)},
            "masonry_below_ng": {"his_m2": None, "ours_plane_at_least_m2": res["totals"]["MASONRY_plane_at_least_m2"]},
        },
        "guards": INP["guards"],
    }
    return out


if __name__ == "__main__":
    text = json.dumps(build(), indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    if "--write" in sys.argv:
        open(OUT, "w", encoding="utf-8").write(text)
        print(OUT)
    else:
        print(text)
        same = os.path.exists(OUT) and open(OUT, encoding="utf-8").read() == text
        print("summary reproduced:", same)
        sys.exit(0 if same else 1)
