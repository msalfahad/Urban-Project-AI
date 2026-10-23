"""T-233 Alsenan check: CONC.FOOTING and CONC.BLINDING as whole reference lines, from committed inputs only.

    python3 -I research/agents_t233/t233_alsenan_check.py          # writes LEDGER_T233.csv + summary.json here

Inputs: ALSENAN_FOOTING_INPUT.json (t233_extract.py on Drive "Alsenan chalet project" / "ST7757 dxf.dxf", sha 9f9d1179;
values only); the freelancer's own cells from tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json (RC workbook, sheets
'ورقة1' rows 15 / 17 and the footings sheet rows 11-32); strap and band components quoted with their merged source
(T-230 MERGED 17ed6f92; T-065 / owner Q-28 A PROVISIONAL); engine figures from the run named in ENGINE (own runs this
task, outside the repository). Nothing here is released; integration is a lane I package after the Checker's verdict.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import footing_line as FL  # noqa: E402

# Engine figures (own runs, Python 3.11.17, Drive copies P7757.dxf ab54dd55 / ST7757 dxf 9f9d1179, head 17ed6f92):
ENGINE = {
    "A": {  # released ARCH_TAKEOFF_V2.9 + route G, tools/release_baseline.py V29_ROUTEG_NO_PROFILE: REPRODUCED,
            # 1,455 lines, BOQ_LINES.csv b96185d4
        "footings_measured": 64.304, "footing_F10_provisional": (0.216, 1.96),
        "straps_measured": 2.6494, "strap_provisional": (0.9052, 1.1315), "band": 7.2204,
        "blinding": None, "blinding_bounded": (7.2755, 16.887),   # BOUNDED_EXPOSURE 'BLINDING_THICKNESS_NOT_PRINTED'
    },
    "V3.0.7": {  # candidate ARCH_TAKEOFF_V3.0.7 (research/agents_t167/v304_run.py + research/agents_t193/v307_run.py):
                 # V3_0_7_BOQ_LINES.csv 197c5599 REPRODUCED
        "footings_measured": 64.304, "footing_F10_provisional": (0.216, 1.96),
        "straps_measured": 2.244035, "strap_provisional": (1.146382, 1.146382),
        "strap_bounded_inside_open_outlines": ((0.0, 0.402518), (0.0, 1.406176)), "band": 7.2204,
        "blinding": 15.179437,                                    # PROVISIONAL: union under the released footings
        "blinding_bounded": ((4.949374, 9.422514), (0.48, 0.59), (0.377803, 0.771877)),
    },
    "V3.0.8": {  # candidate ARCH_TAKEOFF_V3.0.8 (T-231 MERGED 3b042470; research/agents_t231/v308_run.py,
                 # own run: V3_0_8_BOQ_LINES.csv 57fe219a REPRODUCED)
        "footings_measured": 64.304, "footing_F10_provisional": (0.216, 1.96),
        "straps_measured": 3.3905, "strap_held": ((0.0295, 0.1181), (0.0, 0.385)), "band": 7.2204,
        "blinding": 15.179437,
    },
}

# Strap component (T-230 MERGED 17ed6f92, research/agents_t230: owner method = drawing-derived at e = 0)
STRAPS = {"measured": 3.3905,
          "held": [("SB3/F3 strap excess", "strap soffit level not printed (D-15 narrowed, T-230)", (0.0295, 0.2683)),
                   ("SB1/F10+F end", "end ownership waits on F10 + F (Q-31 C): A_in 0.770 m2 x [0 .. D 0.50] "
                    "(V3.0.8 bound, T-231 MERGED 3b042470)", (0.0, 0.385))]}
# Foundation-level boundary band (T-065, owner Q-28 A PROVISIONAL, NOT RELEASED: section C1 20x60 vs 20x40 and the
# band / footing levels at each crossing unproven); 91.94 m drawn, 21.45 m inside footings
BAND = {"measured": 0.0,
        "held": [("band B.W", "Q-28 A provisional 8.459 (net, 0.20 x 0.60); section C1 and crossing levels open",
                  (5.639, 11.033))]}
# Ground-beam and strap blinding (T-100 hand, not re-measured here; see T-233 report s.4)
GB_BLIND = {"measured": 0.0,
            "held": [("ground-beam blinding", "T-100: R 9.691 / L 5.534; L refuted in 3-D by T-230 levels for the "
                      "drawn beams; detail selection (two-beam detail) waits on the formation (Q-21 C)",
                      (9.691, 9.691)),
                     ("strap blinding", "D-15: none printed under straps", (0.0, 0.913))]}


def freelancer():
    d = json.loads((ROOT / "tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json").read_text(encoding="utf-8"))
    rows = {}
    for r in d["rows"]:
        if r["file"] == "RC" and r["sheet"] == "القواعد":
            rows[r["row"]] = {k[0]: c["v"] for k, c in r["cells"].items()}
        if r["file"] == "RC" and r["sheet"] == "ورقة1" and r["row"] in (15, 17):
            rows["S%d" % r["row"]] = {k[0]: c["v"] for k, c in r["cells"].items()}
    iso = {rows[i]["A"]: (rows[i]["B"], rows[i]["C"], rows[i]["D"], rows[i]["F"], rows[i]["I"]) for i in range(13, 29)}
    straps = sum(rows[i]["I"] for i in (29, 30, 31))
    band = rows[32]["I"]
    return dict(isolated=iso, isolated_m3=round(sum(v[4] for v in iso.values()), 6), straps_m3=round(straps, 6),
                band_m3=round(band, 6), band_len_m=rows[32]["D"], footing_line_m3=round(rows["S17"]["E"], 6),
                blinding_m3=round(rows["S15"]["E"], 6), blinding_basis=(rows[11]["B"], rows[11]["C"], rows[11]["D"]))


def main(write=True):
    inp = json.loads((HERE / "ALSENAN_FOOTING_INPUT.json").read_text(encoding="utf-8"))
    sched = {t: FL.ScheduleRow(t, v["L"], v["W"], v["H"]) for t, v in inp["schedule"].items()}
    outl = [FL.Outline(o["id"], tuple(o["tags"]), o["a"], o["b"], o["area"], tuple(o["clipped_by"]), o["blind_m2"],
                       o["blind_outside_m2"]) for o in inp["outlines"]]
    fres = FL.footing_line(outl, sched)
    bres = FL.blinding_line(outl, fres, projection_m=inp["source"]["projection_m"],
                            thickness_m=inp["source"]["thickness_m"],
                            union_m2_measured=inp["blinding_union_measured_m2"], schedule=sched)
    drawn_types = {r.type for r in fres.rows}
    not_drawn = sorted(t for t in sched if t not in drawn_types and not any(t in (r.type or "").split("+")
                                                                            for r in fres.rows))
    foot_line = FL.keyed_line({"isolated footings": (fres.measured_m3, fres.held),
                               "straps": (STRAPS["measured"], STRAPS["held"]),
                               "boundary band": (BAND["measured"], BAND["held"])})
    blind_line = FL.keyed_line({"footing blinding": (bres.measured_m3, bres.held),
                                "ground-beam / strap blinding": (GB_BLIND["measured"], GB_BLIND["held"])})
    fr = freelancer()
    # reconciliation, freelancer isolated footings vs drawing (units, m3)
    f10_sched = sched["F10"].L * sched["F10"].W * sched["F10"].H
    f3 = sched["F3"].L * sched["F3"].W * sched["F3"].H
    fn_clip = (sched["FN"].L * sched["FN"].W - next(o.area for o in outl if o.clipped_by)) * sched["FN"].H
    rec_iso = round(fr["isolated_m3"] - fres.measured_m3, 6)
    explained = round(f10_sched - f3 * (2 - fr["isolated"]["F3"][3]) + fn_clip, 6)
    eng = ENGINE["A"]
    summary = dict(
        footing_rows=len(fres.rows), by_type={k: list(v) for k, v in sorted(fres.by_type.items())},
        not_drawn_types=not_drawn, footings_measured_m3=fres.measured_m3,
        footings_held=[list(h) for h in fres.held],
        blinding=dict(measured_m3=bres.measured_m3, **bres.by_type, held=[list(h) for h in bres.held]),
        conc_footing=dict(measured_m3=foot_line[0], held=[list(h) for h in foot_line[1]], verdict=foot_line[2]),
        conc_blinding=dict(measured_m3=blind_line[0], held=[list(h) for h in blind_line[1]], verdict=blind_line[2]),
        freelancer=dict(isolated_m3=fr["isolated_m3"], straps_m3=fr["straps_m3"], band_m3=fr["band_m3"],
                        line_m3=fr["footing_line_m3"], blinding_m3=fr["blinding_m3"],
                        blinding_basis=list(fr["blinding_basis"])),
        reconcile_isolated=dict(diff_m3=rec_iso, F10_at_schedule=round(f10_sched, 6),
                                F3_second_outline=round(-f3, 6), FN_clip_counted_twice=round(fn_clip, 6),
                                explained_m3=explained, residual_m3=round(rec_iso - explained, 6)),
        engine_A=dict(footings_measured=eng["footings_measured"],
                      footings_diff_m3=round(eng["footings_measured"] - fres.measured_m3, 6),
                      straps_total=round(eng["straps_measured"] + eng["strap_provisional"][1], 6),
                      straps_diff_m3=round(eng["straps_measured"] + eng["strap_provisional"][1] - STRAPS["measured"], 6),
                      band=eng["band"], F10_provisional=list(eng["footing_F10_provisional"]),
                      line_total=round(eng["footings_measured"] + eng["footing_F10_provisional"][1]
                                       + eng["straps_measured"] + eng["strap_provisional"][1] + eng["band"], 4),
                      blinding_bounded=list(eng["blinding_bounded"])),
        engine_V307=dict(
            line_total=round(64.304 + 1.96 + 2.244035 + 1.146382 + 7.2204, 6),
            blinding_footing=ENGINE["V3.0.7"]["blinding"],
            blinding_footing_minus_ours_m3=round(ENGINE["V3.0.7"]["blinding"] - bres.measured_m3, 6),
            strap_inside_F10_outline_high=0.402518),
        engine_V308=dict(
            line_measured_plus_provisional=round(64.304 + 1.96 + 3.3905 + 7.2204, 6),
            sb3_high_end=ENGINE["V3.0.8"]["strap_held"][0][1], sb3_high_end_T230=STRAPS["held"][0][2][1]),
    )
    if write:
        with open(HERE / "LEDGER_T233.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["line", "outline", "type", "status", "m3", "range_m3", "basis"])
            for r in fres.rows:
                w.writerow(["CONC.FOOTING", r.outline, r.type, r.status, r.m3, r.m3_range, r.basis])
            for r in bres.rows:
                w.writerow(["CONC.BLINDING", r.outline, r.type, r.status, r.m3, r.m3_range, r.basis])
            for name, why, rng in bres.held:
                if name == "BLINDING-OUTSIDE-BOUNDARY":
                    w.writerow(["CONC.BLINDING", name, "", "HELD", "", rng, why])
        (HERE / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return fres, bres, summary


if __name__ == "__main__":
    _, _, s = main(write=True)
    print(json.dumps({k: s[k] for k in ("footings_measured_m3", "conc_footing", "conc_blinding", "reconcile_isolated",
                                        "engine_A")}, indent=1, ensure_ascii=False))
