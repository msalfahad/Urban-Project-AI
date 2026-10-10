"""S8.7B post-freeze comparison: the frozen owner-scenario layer against the earlier figures, after the freeze.

    python3 -I research/alsenan_stairs_s8_7b/post_freeze/post_freeze_comparison.py

Reads the frozen S8.7B layer (and the S8.7 / S8.7A manifests; all verified before and after, never written), then the
earlier figures S8.7B did not read before its freeze:
  * the old Urban V3b stair lines (C-STAIR, S-RISER, S-TREAD, S-NOSING, S-RAIL, S-GOING) and their code method,
    reproduced here from the stated inputs;
  * the PRE-S8 stair rows (02 CONCRETE_QUANTITY_STATE / MISSING_INFORMATION);
  * the R5 architectural stair register (its riser method);
  * the S8.7 and S8.7A post-freeze ranges.
Every difference is classified (NO_DIFFERENCE, AUTHORITY, SCOPE, METHOD, MISSED_OBJECT, NOT_COMPARABLE) and
explained. Nothing here changes a frozen quantity, chooses a riser count or releases anything.
"""

from __future__ import annotations

import csv
import io
import json
import math
import re
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
MANIFEST = PKG / "16_S8_7B_FREEZE_MANIFEST.json"
OTHER = [R / "alsenan_stairs_s8_7/17_S8_7_FREEZE_MANIFEST.json",
         R / "alsenan_stairs_s8_7a/15_S8_7A_CORRECTION_MANIFEST.json"]
OUT = ["01_POST_FREEZE_COMPARISON.csv", "02_V3B_VS_OWNER_SCENARIO.csv", "03_POST_FREEZE_SUMMARY.json",
       "00_POST_FREEZE_README.md"]
STAIR_CODES = re.compile(r"STAIR|TREAD|RISER|NOSING|GOING|S-RAIL")
V3B_RISE_M = {"A1": 4.50, "A2": 4.20}
V3B_LANDINGS = {"A1": 2, "A2": 1}


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
        s = f"{v:.6f}"
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
        out[run] = {"risers": n, "riser_mm": R_ * 1000, "concrete_m3": round(conc, 4), "treads": n - 1,
                    "riser_face_m2": round(n * R_ * 1.15, 3), "nosing_lm": round((n - 1) * 1.15, 3)}
    return out


def compare():
    pre = DR.verify_frozen(MANIFEST, ROOT)
    pre_o = [DR.verify_frozen(m, ROOT)["manifest_sha256"] for m in OTHER]
    s = json.loads((PKG / "14_RELEASE_SUMMARY.json").read_text(encoding="utf-8"))
    conc = _rows(PKG / "08_WAIST_THICKNESS_CONCRETE_SENSITIVITY.csv")
    tot = s["concrete_sensitivity_m3_by_waist"]
    plates = {r["ELEMENT_ID"]: float(r["GROSS_M3"]) for r in conc if r["ALREADY_RELEASED_BY_S8_7"] == "True"
              and r["WAIST_MM"] == "160"}
    v3 = v3b_method()
    lines = {l["code"]: l for l in json.loads(V3B_LINES.read_text(encoding="utf-8"))["lines"]
             if STAIR_CODES.search(l["code"])}
    c = lines["C-STAIR"]["release"]["commercial"]
    v3_sum = round(sum(x["concrete_m3"] for x in v3.values()), 4)
    main_keys = ("main stair GF -> 1F (OWNER-28)", "main stair 1F -> 2F (OWNER-27)")
    main = {w: round(sum(tot[k][w]["gross"] for k in main_keys) + plates["A1-L1"] + plates["A2-T1"], 6)
            for w in ("150", "160", "175", "200")}
    rep = []
    for run, own_n, k in (("A1", 28, main_keys[0]), ("A2", 27, main_keys[1])):
        x = v3[run]
        rep.append({"STOREY_RUN": run, "V3B_RISERS": x["risers"], "V3B_RISER_MM": _r(x["riser_mm"]),
                    "OWNER_RISERS": own_n, "OWNER_RISER_MM": _r(V3B_RISE_M[run] * 1000 / own_n),
                    "V3B_CONCRETE_M3": x["concrete_m3"],
                    "S8_7B_NEW_GROSS_M3_BY_WAIST": {w: tot[k][w]["gross"] for w in ("150", "160", "175", "200")},
                    "S8_7_PLATE_M3": plates["A1-L1"] if run == "A1" else plates["A2-T1"],
                    "V3B_WIDTH_M": 1.15, "S8_7B_WIDTH_M": 1.20,
                    "V3B_LANDINGS": f"{V3B_LANDINGS[run]} flat W x W quarter(s)",
                    "S8_7B_TURN": "one winder quarter (4 risers) + one flat quarter (landing)"})
    _csv(OUT[1], rep)
    rows = []
    rows.append({"REFERENCE": "V3b C-STAIR (GF)", "UNIT": "m3",
                 "REFERENCE_VALUE": f"technical {lines['C-STAIR']['release']['technical']['class']}; commercial "
                                    f"{c['class']} {c['qty']} ({c['low']} - {c['high']})",
                 "REFERENCE_METHOD": c["method"],
                 "S8_7B": f"V3b method reproduced: {v3_sum} m3; owner scenario main stair (new gross + S8.7 plates) "
                          f"{main['150']} / {main['160']} / {main['175']} / {main['200']} m3 at 150 / 160 / 175 / 200",
                 "CLASS": "METHOD + SCOPE",
                 "EXPLANATION": "V3b's figure sits near the owner scenario at a 160 mm waist only by compensation: fewer "
                                "risers (26 / 24 against 28 / 27), one straight slope per storey, 1.15 m width "
                                "(drawn 1.20), flat quarters where one quarter is drawn as winders, and no round "
                                "stair or steps on grade. It is a code-method estimate, not a reading of the drawings."})
    for run in ("A1", "A2"):
        x = v3[run]
        own = 28 if run == "A1" else 27
        rows.append({"REFERENCE": f"V3b riser count {run}", "UNIT": "risers",
                     "REFERENCE_VALUE": f"{x['risers']} ({_r(x['riser_mm'], 3)} mm)",
                     "REFERENCE_METHOD": "ceil(H / 0.175); section A-A not machine-counted",
                     "S8_7B": f"owner {own}; section A-A measured {27 if run == 'A1' else 25}",
                     "CLASS": "METHOD",
                     "EXPLANATION": ("V3b's 26 is neither drawn nor the owner's; the section, which V3b did not count, "
                                     "draws 27 to the printed +3.50") if run == "A1" else
                                    ("V3b's 24 equals the structural sheet only through the 175 mm cap (4.20 / 0.175); "
                                     "the owner's 27 needs the architectural winders; the section draws 25")})
    for code, s87b in (("S-RISER", "riser face area is H x W for any count of equal risers; the owner's counts do not "
                                    "change it, the width (1.20 drawn) and the winder risers (longer than W) do"),
                       ("S-NOSING", "V3b counts 25 + 23 = 48 treads; the owner's 28 / 27 risers give more nosings; "
                                    "finishes are not S8.7B scope"),
                       ("S-TREAD", "finish areas are not S8.7B scope; they follow the confirmed counts"),
                       ("S-RAIL", "handrails are not S8.7B scope"),
                       ("S-GOING", "300 mm on every primary flight; S8.7B uses the drawn 300")):
        l = lines[code]
        com = l["release"]["commercial"]
        rows.append({"REFERENCE": f"V3b {code}", "UNIT": l["unit"],
                     "REFERENCE_VALUE": f"technical {l['release']['technical']['class']}; commercial {com['class']} "
                                        f"{com['qty']}", "REFERENCE_METHOD": com.get("method") or l.get("formula"),
                     "S8_7B": s87b, "CLASS": "NO_DIFFERENCE" if code == "S-GOING" else (
                         "METHOD" if code in ("S-RISER", "S-NOSING") else "NOT_COMPARABLE"),
                     "EXPLANATION": "V3b's finish lines rest on its own riser counts and 1.15 m width"})
    census = [r for r in _rows(PRE_S8 / "02_STRUCTURAL_ELEMENT_CENSUS.csv")
              if r["ELEMENT_ID"].startswith("SPC-STAIR-SP")]
    miss = sorted({r["MISSING_INFORMATION"] for r in census})
    rows.append({"REFERENCE": f"PRE-S8 02 stair rows ({len(census)})", "UNIT": "-",
                 "REFERENCE_VALUE": sorted({r["CONCRETE_QUANTITY_STATE"][:60] for r in census}),
                 "REFERENCE_METHOD": f"missing: {miss}",
                 "S8_7B": "riser height: owner provisional, in conflict with the printed +3.50 (GF -> 1F) and the "
                          "structural winders (1F -> 2F); landing levels: GF -> 1F printed, the others inferred; "
                          "waist: still UNKNOWN",
                 "CLASS": "AUTHORITY", "EXPLANATION": "the three missing items remain engineer / architect decisions"})
    r5 = json.loads(R5_STAIRS.read_text(encoding="utf-8"))
    rows.append({"REFERENCE": "R5 stair register", "UNIT": "risers",
                 "REFERENCE_VALUE": f"{len(r5['runs'])} runs; risers = tread lines + 1; riser height "
                                    f"{r5['riser_height']['state']}", "REFERENCE_METHOD": "straight tread sets only",
                 "S8_7B": "plans paired line by line (nosing + riser face = one riser), turn and curved risers read; "
                          "section A-A measured on its own riser grid",
                 "CLASS": "METHOD + MISSED_OBJECT",
                 "EXPLANATION": "R5 over-counts each run whose landing edge is drawn and misses every winder and curved "
                                "riser and the section"})
    for p, ref, key in ((S87_PF, "S8.7 post-freeze released + sensitivity (all four stairs; winder turns and the "
                                 "curved flight not computed)", "s8_7_released_plus_sensitivity_m3"),
                        (S87A_PF, "S8.7A post-freeze main-stair whole-stair range (drawn counts)",
                         "s8_7a_main_stair_whole_m3_range")):
        x = json.loads(p.read_text(encoding="utf-8"))
        val = x[key]
        rows.append({"REFERENCE": ref, "UNIT": "m3", "REFERENCE_VALUE": val,
                     "REFERENCE_METHOD": "context only (never a quantity)",
                     "S8_7B": f"owner scenario at 160: {main['160']} m3 (new gross + S8.7 plates)",
                     "CLASS": "METHOD",
                     "EXPLANATION": "S8.7B evaluates the owner's arrangement only, with the winders on their own "
                                    "walking line and the beam zones apart; all are research context, none released"})
    _csv(OUT[0], rows)
    summ = {"round": "S8_7B_POST_FREEZE", "frozen_manifest_sha256": pre["manifest_sha256"],
            "other_manifests_sha256": pre_o, "rows": len(rows),
            "classes": {k: sum(1 for r in rows if r["CLASS"] == k) for k in sorted({r["CLASS"] for r in rows})},
            "v3b_c_stair_commercial_m3": c["qty"], "v3b_method_reproduced_m3": v3_sum,
            "v3b_reproduced_exactly": abs(v3_sum - c["qty"]) < 5e-5, "v3b_risers": {k: v["risers"] for k, v in v3.items()},
            "owner_scenario_main_stair_m3_by_waist": main, "release_delta": s["release_delta"],
            "rule": "explains differences only; no frozen quantity is changed, no riser count is chosen, nothing is "
                    "released"}
    (HERE / OUT[2]).write_text(json.dumps(summ, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    (HERE / OUT[3]).write_text(readme(summ), encoding="utf-8")
    post = DR.verify_frozen(MANIFEST, ROOT)
    assert post["manifest_sha256"] == pre["manifest_sha256"]
    assert [DR.verify_frozen(m, ROOT)["manifest_sha256"] for m in OTHER] == pre_o
    return summ


def readme(s):
    m = s["owner_scenario_main_stair_m3_by_waist"]
    return f"""# S8.7B post-freeze comparison

This comparison ran after the S8.7B freeze. The S8.7B, S8.7 and S8.7A manifests were verified before and after, and
nothing frozen was written. Classes: {json.dumps(s['classes'])}.

## V3b C-STAIR

V3b's commercial provisional figure, {s['v3b_c_stair_commercial_m3']} m3, reproduces from its stated method as
{s['v3b_method_reproduced_m3']} m3. The method uses {s['v3b_risers']['A1']} / {s['v3b_risers']['A2']} risers, one
slope per storey, a 1.15 m width, a 0.16 waist and flat quarters.

The owner scenario's main stair is {m['150']} / {m['160']} / {m['175']} / {m['200']} m3 at a 150 / 160 / 175 / 200
mm waist. That is S8.7B's new gross plus the S8.7 plates, as research context only. V3b lands near the 160 mm case
only because its differences compensate:
- fewer risers;
- a single slope per storey;
- a narrower width;
- no winder geometry.

V3b also omits the round stair and the steps on grade.

## Riser counts

- V3b never counted section A-A. Measured in S8.7B, it draws 27 risers (GF -> 1F) and 25 (1F -> 2F).
- V3b's 26 is drawn nowhere and is not the owner's.
- V3b's 24 is the structural sheet's flat-quarter arrangement, reached only through the 175 mm cap.

## Other references

- **PRE-S8:** the stair rows' missing information (waist, riser height, landing levels) stays with the engineer and
  architect.
- **R5:** its lines + 1 method and its missed winder and curved risers are unchanged findings.

Nothing here is released. The release delta stays 0 m3 and 0 kg.
"""


if __name__ == "__main__":
    print(json.dumps(compare(), indent=1))
