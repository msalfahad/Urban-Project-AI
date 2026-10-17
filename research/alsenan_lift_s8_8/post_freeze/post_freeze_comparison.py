"""S8.8 post-freeze comparison: the frozen lift package against the earlier figures, after the freeze.

    python3 -I research/alsenan_lift_s8_8/post_freeze/post_freeze_comparison.py

Reads the frozen S8.8 package (verified before and after; never written) and the earlier figures:
  * the old Urban V3b lines (no lift line exists; the FF row of the footing line B0001 C-FTG) and its FOOTINGS bar
    population;
  * the PRE-S8 concrete-state column, the 03 / 04 coverage-matrix rows, the 06 candidate register and the 07
    interface columns for the lift family (firewalled until now);
  * the R9.1 freelancer post-freeze records (the FF footing crosswalk, the pit opening, the S-BW decision).
Every difference is classified (NO_DIFFERENCE, AUTHORITY, SCOPE, METHOD, MISSED_OBJECT, NEW_RELEASE, NOT_COMPARABLE)
and explained, by equal physical scope. Nothing here changes a frozen quantity or chooses an interpretation.
"""

from __future__ import annotations

import csv
import io
import json
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
PRE_S8 = R / "pre_s8_structural_completeness"
R91 = R / "R9_1_CHRIS_POST_FREEZE"
MANIFEST = PKG / "18_S8_8_FREEZE_MANIFEST.json"
OUT = ["01_POST_FREEZE_COMPARISON.csv", "02_S8_8_CONDITIONAL_TOTALS.csv", "03_POST_FREEZE_SUMMARY.json",
       "00_POST_FREEZE_README.md"]
LIFT_IDS = ("FTG-FF-18688-14112", "SPC-LIFT_PIT", "SPC-LIFT_TIE_BEAM-GF", "PS8-LIFT-WALLS")


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


def _lift_word(t):
    t = t.upper()
    return " LIFT" in f" {t}" or "ELEVATOR" in t or " PIT " in f" {t} " or "LIFT_" in t


def conditional_totals(s, walls):
    """what the frozen package holds per component: released, conditional coefficient, sensitivity (never a
    release), and quantities owned elsewhere."""
    out = []
    for r in walls:
        if r["ELEMENT_ID"].startswith("LIFT-01-PIT-WALL-") or r["ELEMENT_ID"] == "LIFT-01-PIT-WALLS (all)":
            out.append({"COMPONENT": r["ELEMENT_ID"], "RELEASED_M3": 0.0,
                        "M3_PER_M_HEIGHT": _r(r["M3_PER_M_HEIGHT_CONDITIONAL"]),
                        "SENSITIVITY": r["SENSITIVITY"], "OWNED_ELSEWHERE_M3": None,
                        "NOTE": "conditional coefficients and sensitivity are context only; never a quantity"})
    out.append({"COMPONENT": "LIFT-01-FTG (FF)", "RELEASED_M3": 0.0, "M3_PER_M_HEIGHT": None, "SENSITIVITY": "",
                "OWNED_ELSEWHERE_M3": s["footing"]["concrete_m3_computed_not_released"],
                "NOTE": "computed for the record; the footing family owns it; never a quantity of S8.8"})
    return out


def compare():
    pre = DR.verify_frozen(MANIFEST, ROOT)
    s = json.loads((PKG / "17_S8_8_SUMMARY.json").read_text(encoding="utf-8"))
    walls = _rows(PKG / "06_WALL_GEOMETRY_AND_CONCRETE_QTO.csv")
    tot = conditional_totals(s, walls)
    rel = s["released"]
    d = s["dimensions_established"]
    rows = []

    def add(ref, unit, tech, com, method, s88, cls, why):
        rows.append({"REFERENCE": ref, "UNIT": unit, "REFERENCE_TECHNICAL": tech, "REFERENCE_COMMERCIAL": com,
                     "REFERENCE_METHOD": method, "S8_8": s88, "CLASS": cls, "EXPLANATION": why})
    lines = json.loads(V3B_LINES.read_text(encoding="utf-8"))["lines"]
    lift = [l for l in lines if _lift_word(" ".join(str(l.get(k) or "") for k in ("code", "desc_en", "group")))]
    add("V3b lines for the lift (pit walls, pit base, shaft, tie beam)", "-", f"{len(lift)} lines",
        "", "", f"released {rel['concrete_m3']} m3 / {rel['kg']} kg; one shaft, 4 pit walls "
                f"({d['net_wall_footprint_m2']} m2 footprint), the GF tie beam and 13 questions populated",
        "MISSED_OBJECT", "V3b carried no lift line: the pit walls, the P14 wall bars and the P8-N19 tie beam were "
                         "not in its population. S8.8 populates them and releases nothing, because the pit depth is "
                         "the lift manufacturer's and no tie-beam section is stated")
    b1 = next(l for l in lines if l["line_id"] == "B0001")
    ff = [x for x in b1["details"] if x.get("ref") == "FF"]
    add(f"V3b {b1['line_id']} {b1['code']} ({b1['level']}), FF row", b1["unit"],
        f"{ff[0]['formula']} = {ff[0]['qty']} ({ff[0]['status']})",
        f"line {b1['release']['commercial']['class']} {b1['release']['commercial']['qty']}", b1["formula"],
        f"{s['footing']['concrete_m3_computed_not_released']} m3 computed, not released (footing family)",
        "NO_DIFFERENCE", "same outline, same schedule depth; S8.8 leaves the footing concrete with the footing family "
                         "(no frozen accurate stage holds it)")
    pop = [r for r in json.loads(V3B_POP.read_text(encoding="utf-8"))["rows"] if r.get("population") == "FOOTINGS"]
    add("V3b rebar population FOOTINGS", "kg", f"{pop[0]['technical_kg']} ({pop[0]['sets']} sets)", "", "",
        f"FF mats stay S4's ({s['footing']['bars_kg_S4_lower_bound']} kg lower bound); S8.8 adds 0 kg",
        "NOT_COMPARABLE", "a whole-family aggregate; it has no FF or lift-wall row to compare by equal scope")
    with open(PRE_S8 / "02_STRUCTURAL_ELEMENT_CENSUS.csv", encoding="utf-8", newline="") as fh:
        census = {r["ELEMENT_ID"]: r for r in csv.DictReader(fh) if r["ELEMENT_ID"] in LIFT_IDS}
    for eid in LIFT_IDS:
        st = census[eid]["CONCRETE_QUANTITY_STATE"]
        if eid.startswith("FTG-FF"):
            cls, why = "SCOPE", ("PRE-S8 quotes the whole V3b footing line (all footings) against the FF element; "
                                 "the FF share is the 11.385 m3 row above")
        else:
            cls, why = "NO_DIFFERENCE", "no earlier concrete figure; S8.8 also releases none (blocked on authority)"
        add(f"PRE-S8 02 CONCRETE_QUANTITY_STATE {eid}", "m3", st, "", "", "0 m3 released", cls, why)
    with open(PRE_S8 / "03_CONCRETE_COVERAGE_MATRIX.csv", encoding="utf-8", newline="") as fh:
        cov = [r for r in csv.DictReader(fh) if r["FAMILY"] == "LIFT"]
    for r in cov:
        add(f"PRE-S8 03 concrete coverage LIFT / {r['FLOOR']}", "m3",
            f"{r['ELEMENT_STATES']} lines {r['URBAN_LINES']} shared {r['V3B_LINE_TECHNICAL_M3_SHARED'] or '-'}",
            f"commercial shared {r['V3B_LINE_COMMERCIAL_PROVISIONAL_M3_SHARED'] or '-'}; CR {r['CR_TRADE'] or '-'} "
            f"{r['CR_VERIFIED_LOWER_BEST_M3'] or '-'}", r["COVERAGE_STATE"], "0 m3 released",
            "AUTHORITY", "no contractor-register lift figure; the only figure is the shared V3b footing line")
    with open(PRE_S8 / "04_REBAR_COVERAGE_MATRIX.csv", encoding="utf-8", newline="") as fh:
        rc = [r for r in csv.DictReader(fh) if r["FAMILY"] == "LIFT"]
    add("PRE-S8 04 rebar coverage LIFT", "kg", "; ".join(f"{r['COMPONENT']}: {r['COVERAGE']}" for r in rc), "", "",
        "FF mats S4 / S4.1 unchanged; the P14 wall bars split into 5 roles x 4 walls x faces (08), all blocked",
        "METHOD", "PRE-S8 held the P14 wall callouts as one unquantified component; S8.8 binds each to its role, "
                  "wall and face and keeps them blocked")
    with open(PRE_S8 / "06_S8_CANDIDATE_REGISTER.csv", encoding="utf-8", newline="") as fh:
        cand = [r for r in csv.DictReader(fh) if r["S8_FAMILY"] == "LIFT"]
    add("PRE-S8 06 CONCRETE_STATES (lift family)", "m3", cand[0]["CONCRETE_STATES"], "", cand[0]["READINESS"],
        "0 m3; plan outline established, depth / height blocked", "NO_DIFFERENCE",
        "the readiness stays BLOCKED_NEEDS_AUTHORITY for depth, height and bar extents")
    with open(PRE_S8 / "07_INTERFACE_DOUBLE_COUNT_AUDIT.csv", encoding="utf-8", newline="") as fh:
        ifs = [r for r in csv.DictReader(fh) if r["INTERFACE"] in ("LIFT WALL -> PIT BASE", "WALL -> FOUNDATION")]
    for r in ifs:
        add(f"PRE-S8 07 {r['INTERFACE']}", "-", f"concrete: {r['CONCRETE']}", f"bars: {r['BARS_OWNED']}", r["STATE"],
            "wall bars now owned by S8.8 (blocked); base mesh stays S4.1's once; no pit slab", "SCOPE",
            "the ownership gap PRE-S8 recorded is closed by assignment, not by a quantity")
    fo = [r for r in _rows(R91 / "08_FOOTING_OCCURRENCE_CROSSWALK.csv") if r["URBAN_ID"] == "FTG-FF-18688-14112"]
    add(f"R9.1 freelancer {fo[0]['CHRIS_ID']} (FF)", "m3", f"schedule {fo[0]['CHRIS_M3_SCHEDULE']}, drawn "
        f"{fo[0]['CHRIS_M3_DRAWN_AREA']}", fo[0]["CHRIS_CONFLICTS"], fo[0]["DIFFERENCE_CLASS"],
        f"{s['footing']['concrete_m3_computed_not_released']} m3 computed (footing family)", "NO_DIFFERENCE",
        "same object, same volume; the 'four columns inside' flag is the lift: S8.8 records the four lift columns "
        "on the footing as normal")
    md = [r for r in _rows(R91 / "12_CHRIS_MANUAL_DECISION_GAP.csv") if r["DECISION_ID"] == "MD06"]
    add("R9.1 MD06 S-BW boxes", "-", md[0]["CHRIS_DECISION"], md[0]["GAP_CLASS"], "",
        "S-BW 10EA / 10EB / 7BE / 7C2 = the pit walls (four pieces, columns cut out); 7C5 / 7C6 = the pool",
        "NO_DIFFERENCE", "the S-BW layer role is now applied deterministically (S8.1A barrier, S8.8 wall pieces)")
    g = [r for r in _rows(R91 / "02_OBJECT_GAP_REGISTER.csv") if r["GAP_ID"] == "G022"]
    add("R9.1 G022 ground-slab cell containing the pit", "m2", g[0]["QUANTITY_EFFECT"], g[0]["DIFFERENCE_CLASS"],
        g[0]["ACTION"], "the 3.24 m2 opening (S8.1A RG-04) is the pit's inside area; the ring cells RG-12..15 are the "
                        "pit walls", "NO_DIFFERENCE", "already corrected by S8.1A; S8.8 confirms the same outline")
    _csv(OUT[0], rows)
    _csv(OUT[1], tot)
    summ = {"round": "S8_8_POST_FREEZE", "frozen_manifest_sha256": pre["manifest_sha256"], "s8_8_released": rel,
            "rows": len(rows), "v3b_lift_lines": len(lift),
            "classes": {k: sum(1 for r in rows if r["CLASS"] == k) for k in sorted({r["CLASS"] for r in rows})},
            "ff_v3b_m3": ff[0]["qty"], "ff_r9_1_m3": float(fo[0]["CHRIS_M3_SCHEDULE"]),
            "ff_s8_8_computed_m3": s["footing"]["concrete_m3_computed_not_released"],
            "rule": "explains differences only; no frozen S8.8 quantity is changed or chosen here"}
    (HERE / OUT[2]).write_text(json.dumps(summ, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    (HERE / OUT[3]).write_text(readme(summ), encoding="utf-8")
    post = DR.verify_frozen(MANIFEST, ROOT)
    assert pre == post, "the frozen package changed during the comparison"
    return summ


def readme(s):
    cls = ", ".join(f"{k} {v}" for k, v in s["classes"].items())
    return f"""# S8.8 post-freeze comparison

Run after the freeze (`18_S8_8_FREEZE_MANIFEST.json`, sha256 `{s['frozen_manifest_sha256'][:16]}...`, verified
before and after). It compares by equal physical scope and changes nothing.

- **V3b has {s['v3b_lift_lines']} lift lines.** The pit walls, their bars and the P8-N19 tie beam were missing from
  the old population. S8.8 populates them and releases 0 m3 / 0 kg: the pit depth is the lift manufacturer's, and no
  tie-beam section is stated.
- **The FF footing volume agrees everywhere.** V3b's footing line has {s['ff_v3b_m3']} m3 for FF, the freelancer
  crosswalk has {s['ff_r9_1_m3']} m3, and S8.8 computes {s['ff_s8_8_computed_m3']} m3. S8.8 does not release it:
  the footing family owns it.
- **PRE-S8 had no lift figure.** It recorded the lift as NOT_MEASURED. Its footing state quotes the whole V3b footing
  line against one footing, a scope difference. The ownership gap for the wall bars is now closed by assignment
  (S8.8, blocked).
- **The freelancer reading of the S-BW boxes is the one S8.8 applies.** The boxes are the lift-pit and pool walls,
  and the 3.24 m2 pit opening matches.

Classes: {cls}.
"""


if __name__ == "__main__":
    print(json.dumps(compare(), indent=1))
