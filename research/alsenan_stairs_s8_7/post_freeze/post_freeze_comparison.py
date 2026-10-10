"""S8.7 post-freeze comparison: the frozen stair package against the earlier figures, after the freeze.

    python3 -I research/alsenan_stairs_s8_7/post_freeze/post_freeze_comparison.py

Reads the frozen S8.7 package (verified before and after; never written) and the earlier figures:
  * the old Urban V3b lines for stairs: C-STAIR (concrete), R-STAIRS-GF (bars), S-GOING / S-TREAD / S-RISER /
    S-NOSING / S-RAIL (finishes) and its STAIRS bar population;
  * the PRE-S8 concrete-state column, the 03 / 04 coverage-matrix columns and the 06 candidate register for the
    stair family (firewalled until now);
  * the R5 architectural stair register (its tread runs).
Every difference is classified (NO_DIFFERENCE, AUTHORITY, SCOPE, METHOD, MISSED_OBJECT, NEW_RELEASE, NOT_COMPARABLE)
and explained. Nothing here changes a frozen quantity or chooses an interpretation.
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
V3B_POP = ROOT / "tests/alsenan/registers_v3b/REBAR_POPULATION_REGISTER.json"
R5_STAIRS = R / "alsenan_arch_truth_05/registers/STAIR_ARCHITECTURAL_REGISTER.json"
PRE_S8 = R / "pre_s8_structural_completeness"
MANIFEST = PKG / "17_S8_7_FREEZE_MANIFEST.json"
OUT = ["01_POST_FREEZE_COMPARISON.csv", "02_S8_7_CONDITIONAL_TOTALS.csv", "03_POST_FREEZE_SUMMARY.json",
       "00_POST_FREEZE_README.md"]
STAIR_CODES = re.compile(r"STAIR|TREAD|RISER|NOSING|GOING|S-RAIL")


def _rows(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _r(v, nd=6):
    return None if v is None else round(float(v) + 0.0, nd) + 0.0


def _cell(v):
    if v is None:
        return ""
    if isinstance(v, float):
        s = f"{v:.6f}".rstrip("0").rstrip(".")
        return "0" if s in ("-0", "") else s
    if isinstance(v, (list, dict)):
        return json.dumps(v, ensure_ascii=False, sort_keys=True)
    return str(v)


def _csv(name, rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0]), lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: _cell(v) for k, v in r.items()})
    (HERE / name).write_text(buf.getvalue(), encoding="utf-8")


def conditional_totals(conc):
    """S8.7 released m3 per stair plus the sensitivity readings of the blocked parts (never a release)."""
    out = []
    for stair in ("ST-A", "ST-B", "ST-C", "ST-D"):
        rs = [r for r in conc if r["STAIR_ID"] == stair]
        rel = math.fsum(float(r["CONCRETE_M3"]) for r in rs if r["CONCRETE_M3"])
        lo = hi = 0.0
        missing = []
        for r in rs:
            if r["CONCRETE_M3"]:
                continue
            sv = [float(x["m3_flight_only"]) for x in json.loads(r["SENSITIVITY_ONLY"] or "[]")
                  if x.get("m3_flight_only") is not None]
            if sv:
                lo += min(sv)
                hi += max(sv)
            else:
                missing.append(r["ELEMENT_ID"])
        out.append({"STAIR_ID": stair, "RELEASED_M3": _r(rel), "SENSITIVITY_LOW_M3": _r(lo),
                    "SENSITIVITY_HIGH_M3": _r(hi), "RELEASED_PLUS_SENSITIVITY_LOW": _r(rel + lo),
                    "RELEASED_PLUS_SENSITIVITY_HIGH": _r(rel + hi), "NOT_COMPUTED": missing,
                    "NOTE": "sensitivity is context for the comparison only; it is never a quantity"})
    return out


def compare():
    pre = DR.verify_frozen(MANIFEST, ROOT)
    s = json.loads((PKG / "16_S8_7_SUMMARY.json").read_text(encoding="utf-8"))
    conc = _rows(PKG / "07_CONCRETE_QTO.csv")
    geo = {r["ELEMENT_ID"]: r for r in _rows(PKG / "06_PLAN_AND_INCLINED_GEOMETRY.csv")}
    tot = conditional_totals(conc)
    lines = [l for l in json.loads(V3B_LINES.read_text(encoding="utf-8"))["lines"] if STAIR_CODES.search(l["code"])]
    rows = []
    rel = s["released"]
    a_lo = sum(t["RELEASED_PLUS_SENSITIVITY_LOW"] for t in tot)
    a_hi = sum(t["RELEASED_PLUS_SENSITIVITY_HIGH"] for t in tot)
    for l in lines:
        tech, com = l["release"]["technical"], l["release"]["commercial"]
        code = l["code"]
        if code == "C-STAIR":
            cls = "AUTHORITY + SCOPE"
            s87 = f"released {rel['concrete_m3']} m3 (three plates); blocked parts' sensitivity puts the stairs " \
                  f"with every computable part at {_r(a_lo)} - {_r(a_hi)} m3 before the winder turns, the curved " \
                  f"flight and the step flights (not computed)"
            why = ("V3b released nothing technically (BLOCKED) and carried a commercial provisional figure built by a "
                   "code method: risers ceil(H / 0.175), waist 16 cm, width 1.15 m, a W x W landing per turn. S8.7 "
                   "found the riser counts drawn (and in conflict between the plans on GF -> 1F), the 1.20 m printed "
                   "width, three plates with authority and no authority for the flights. V3b's single line also "
                   "carries no stair-by-stair scope: S8.7 has two staircases and two step flights.")
        elif code.startswith("R-STAIRS"):
            cls = "NEW_RELEASE"
            s87 = f"released {rel['kg']} kg (Ø16, 8Ø16/m landing bottom bars by rate density)"
            why = ("V3b found no stair callout bound. S8.7 binds the nine plan callouts 8%%C16/m with their bar "
                   "lines and releases the bars only over the three plates whose concrete is released")
        elif code == "S-GOING":
            cls = "NO_DIFFERENCE"
            s87 = "300 mm (drawn pitch of every tread set on both drawings; p.16 '30')"
            why = "same going"
        elif code in ("S-TREAD", "S-RISER", "S-NOSING", "S-RAIL", "F-STAIR"):
            cls = "NOT_COMPARABLE"
            est = {k: geo[k]["FINISHING_TREAD_AREA_M2"] for k in geo if geo[k]["FINISHING_TREAD_AREA_M2"]}
            s87 = f"finishes are not S8.7 scope; established tread areas only: {est}"
            why = "architectural finishes are a later family; V3b's commercial figure rests on risers from the 2R + G band"
        else:
            cls, s87, why = "NOT_COMPARABLE", "", ""
        rows.append({"REFERENCE": f"V3b {l['line_id']} {code} ({l['level']})", "UNIT": l["unit"],
                     "REFERENCE_TECHNICAL": f"{tech['class']} {tech['qty']}",
                     "REFERENCE_COMMERCIAL": f"{com['class']} {com['qty']}"
                                             + (f" ({com.get('low')} - {com.get('high')})" if com.get('low') else ""),
                     "REFERENCE_METHOD": com.get("method") or l.get("formula"), "S8_7": s87, "CLASS": cls,
                     "EXPLANATION": why})
    pop = [r for r in json.loads(V3B_POP.read_text(encoding="utf-8"))["rows"] if r.get("population") == "STAIRS"]
    for r in pop:
        rows.append({"REFERENCE": "V3b rebar population STAIRS", "UNIT": "kg",
                     "REFERENCE_TECHNICAL": f"{r['classes']} {r['technical_kg']}", "REFERENCE_COMMERCIAL": "",
                     "REFERENCE_METHOD": "", "S8_7": f"{rel['kg']} kg", "CLASS": "NEW_RELEASE",
                     "EXPLANATION": "as R-STAIRS-GF"})
    with open(PRE_S8 / "02_STRUCTURAL_ELEMENT_CENSUS.csv", encoding="utf-8", newline="") as fh:
        census = [r for r in csv.DictReader(fh) if r["ELEMENT_FAMILY"].startswith(("STAIR", "STAIR_AND"))
                  or r["ELEMENT_ID"].startswith("SPC-STAIR-SP")]
    states = sorted({r["CONCRETE_QUANTITY_STATE"] for r in census if "C-STAIR" in r["CONCRETE_QUANTITY_STATE"]})
    rows.append({"REFERENCE": "PRE-S8 02 CONCRETE_QUANTITY_STATE (10 stair rows)", "UNIT": "m3",
                 "REFERENCE_TECHNICAL": "; ".join(states), "REFERENCE_COMMERCIAL": "",
                 "REFERENCE_METHOD": "the V3b line bound to every stair zone", "S8_7": "see C-STAIR",
                 "CLASS": "SCOPE", "EXPLANATION": "one V3b figure is quoted against five zones that are two "
                                                  "staircases and one repeated view"})
    with open(PRE_S8 / "03_CONCRETE_COVERAGE_MATRIX.csv", encoding="utf-8", newline="") as fh:
        cov = [r for r in csv.DictReader(fh) if r["FAMILY"] == "STAIR_AND_LANDING"]
    rows.append({"REFERENCE": "PRE-S8 03 concrete coverage (STAIR_AND_LANDING)", "UNIT": "m3",
                 "REFERENCE_TECHNICAL": sorted({r["V3B_LINE_TECHNICAL_M3_SHARED"] for r in cov}),
                 "REFERENCE_COMMERCIAL": sorted({r["V3B_LINE_COMMERCIAL_PROVISIONAL_M3_SHARED"] for r in cov}),
                 "REFERENCE_METHOD": "CR (contractor register) columns empty for stairs",
                 "S8_7": f"released {rel['concrete_m3']} m3", "CLASS": "AUTHORITY",
                 "EXPLANATION": "no contractor-register stair figure exists; the only earlier figure is V3b's "
                                "commercial provisional one"})
    with open(PRE_S8 / "06_S8_CANDIDATE_REGISTER.csv", encoding="utf-8", newline="") as fh:
        cand = [r for r in csv.DictReader(fh) if r["S8_FAMILY"] == "STAIR_AND_LANDING"]
    rows.append({"REFERENCE": "PRE-S8 06 CONCRETE_STATES (stair family; the cell seen by the survey read)",
                 "UNIT": "m3", "REFERENCE_TECHNICAL": cand[0]["CONCRETE_STATES"], "REFERENCE_COMMERCIAL": "",
                 "REFERENCE_METHOD": "", "S8_7": "not read by any S8.7 quantity (recorded exposure)",
                 "CLASS": "AUTHORITY", "EXPLANATION": "same V3b figure as C-STAIR"})
    r5 = json.loads(R5_STAIRS.read_text(encoding="utf-8"))
    for run in r5["runs"]:
        rows.append({"REFERENCE": f"R5 stair run {run['floor']}-{run['run']} (layer {run['layer']})", "UNIT": "lines",
                     "REFERENCE_TECHNICAL": f"{run['tread_lines']} tread lines, risers {run['riser_count_candidate']}",
                     "REFERENCE_COMMERCIAL": f"width {run['flight_width_m']} m, finish {run['tread_finish_m2']} m2",
                     "REFERENCE_METHOD": run["why"][:120], "S8_7": "02_TREAD_RUN_CENSUS",
                     "CLASS": "METHOD",
                     "EXPLANATION": "R5 counts lines as treads (risers = lines + 1) and splits sets at drafting "
                                    "breaks; S8.7 counts lines as risers, pairs nosing / riser lines, and assigns "
                                    "every set to one element"})
    rows.append({"REFERENCE": "R5 stair register coverage", "UNIT": "", "REFERENCE_TECHNICAL":
                 f"{len(r5['runs'])} runs on GF / 1F; no 2F run; no radial (curved / winder) line",
                 "REFERENCE_COMMERCIAL": "", "REFERENCE_METHOD": "",
                 "S8_7": "main stair 1F -> 2F (12 + 11 risers), both winder turns and the 12 radial risers of the "
                         "light-well flight", "CLASS": "MISSED_OBJECT",
                 "EXPLANATION": "R5 found the straight sets only"})
    _csv(OUT[0], rows)
    _csv(OUT[1], tot)
    summ = {"round": "S8_7_POST_FREEZE", "frozen_manifest_sha256": pre["manifest_sha256"],
            "s8_7_released": rel, "rows": len(rows),
            "classes": {k: sum(1 for r in rows if r["CLASS"] == k) for k in sorted({r["CLASS"] for r in rows})},
            "v3b_c_stair_commercial_m3": next(l["release"]["commercial"]["qty"] for l in lines if l["code"] == "C-STAIR"),
            "s8_7_released_plus_sensitivity_m3": [_r(a_lo), _r(a_hi)],
            "rule": "explains differences only; no frozen S8.7 quantity is changed or chosen here"}
    (HERE / OUT[2]).write_text(json.dumps(summ, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    (HERE / OUT[3]).write_text(readme(summ, tot), encoding="utf-8")
    post = DR.verify_frozen(MANIFEST, ROOT)
    assert post["manifest_sha256"] == pre["manifest_sha256"]
    return summ


def readme(s, tot):
    t = "\n".join(f"| {x['STAIR_ID']} | {_cell(x['RELEASED_M3'])} | {_cell(x['RELEASED_PLUS_SENSITIVITY_LOW'])} - "
                  f"{_cell(x['RELEASED_PLUS_SENSITIVITY_HIGH'])} | {', '.join(x['NOT_COMPUTED']) or '-'} |" for x in tot)
    return f"""# S8.7 post-freeze comparison

Run after the freeze; the frozen package is verified before and after and is never written. Classes:
{json.dumps(s['classes'])}.

- **V3b C-STAIR** released no technical quantity. It carried a commercial provisional
  {s['v3b_c_stair_commercial_m3']} m3 from a code method: risers from H / 0.175, waist 16 cm, width 1.15 m, one
  landing per turn.
- **S8.7** releases {s['s8_7_released']['concrete_m3']} m3 (three plates with authority). With the sensitivity of
  every blocked part it can compute, the total is {s['s8_7_released_plus_sensitivity_m3'][0]} -
  {s['s8_7_released_plus_sensitivity_m3'][1]} m3. That range is context only, never a quantity, and it excludes
  the winder turns, the curved flight and the steps on grade.

| Stair | Released m3 | Released + sensitivity m3 | Not computed |
|---|---|---|---|
{t}

- **Bars**: V3b had no stair bars ("no stair reinforcement callout bound"). S8.7 binds the nine plan 8Ø16/m
  callouts and releases {s['s8_7_released']['kg']} kg over the released plates only.
- **R5**: the architectural stair register found straight tread sets only. It counts lines as treads and missed
  the 1F -> 2F main stair, both winder turns and the curved flight.
"""


if __name__ == "__main__":
    print(json.dumps(compare(), indent=1))
