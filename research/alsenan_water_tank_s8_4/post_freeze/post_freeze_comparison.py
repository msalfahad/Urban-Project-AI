"""S8.4 post-freeze comparison: the frozen water-tank QTO against earlier figures, at equal scope, after the freeze.

    python3 -I research/alsenan_water_tank_s8_4/post_freeze/post_freeze_comparison.py

Reads the frozen S8.4 package (verified before and after; never written) and the earlier figures:
  * the old Urban V3b register: its bar sets for the four tank callouts (the only earlier figure at the same scope),
    its 2F slab concrete line and its 2F slab steel line, and the control-plane states of those lines;
  * the freelancer QS lineage and the multi-engine concrete comparison (2F slab rows);
  * the PRE-S8 coverage states and the coverage-recovery dashboard.
Every difference is classified (LAYER, RUN_BASIS, COUNT_BASIS, STOP_ZONE, SCOPE, THICKNESS_BASIS, PLATE_BASIS,
NOT_COMPARABLE, NO_DIFFERENCE) and explained. Nothing here changes a frozen quantity or chooses an interpretation.
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
V3B = ROOT / "tests/alsenan/registers_v3b"
OLD_V2 = R / "alsenan_control_plane_02/registers/ALSENAN_CONTROL_V2_CANDIDATE.json"
LINEAGE = R / "alsenan_multi_engine_comparison/FREELANCER_CATEGORY_LINEAGE.json"
MULTI = R / "alsenan_multi_engine_comparison/MULTI_ENGINE_CONCRETE_COMPARISON.json"
CR = R / "coverage_recovery_round/QUANTITY_COVERAGE_DASHBOARD.json"
PRE_S8 = R / "pre_s8_structural_completeness"
S7_PANELS = R / "alsenan_slab_rebar_s7/05_S7_PANEL_SUMMARY.csv"
MANIFEST = PKG / "15_S8_4_FREEZE_MANIFEST.json"
OUT = ["01_POST_FREEZE_COMPARISON.csv", "02_OLD_FORMULA_RECONSTRUCTION.csv", "03_POST_FREEZE_SUMMARY.json",
       "00_POST_FREEZE_README.md"]
CALLOUTS = {"7A7": ("SP-2F_ROOF_SLAB-01", "X"), "7A8": ("SP-2F_ROOF_SLAB-01", "Y"),
            "798": ("SP-2F_ROOF_SLAB-02", "X"), "796": ("SP-2F_ROOF_SLAB-02", "Y")}


def kg_m(d):
    return d * d / 162.0


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
        s = f"{v:.9f}".rstrip("0").rstrip(".")
        return "0" if s in ("-0", "") else s
    if isinstance(v, (list, dict)):
        return json.dumps(v, ensure_ascii=False, sort_keys=True)
    return str(v)


def _csv(name, rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(rows[0]), lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: _cell(r.get(k)) for k in rows[0]})
    (HERE / name).write_text(buf.getvalue(), encoding="utf-8")


def v3b_lines():
    d = json.loads((V3B / "BOQ_LINES_V3B.json").read_text(encoding="utf-8"))
    return {ln["code"]: ln for ln in d["lines"]}


def v3b_tank_sets():
    sets = json.loads((V3B / "REBAR_POPULATION_REGISTER.json").read_text(encoding="utf-8"))["sets"]
    out = {}
    for s in sets:
        for h in CALLOUTS:
            if s.get("population") == "SLAB" and s.get("level") == "2F_ROOF" and s.get("ref", "").endswith(f"[{h}]"):
                out[h] = s
    binding = {r["annotation"]: r for r in json.loads((V3B / "STRUCTURE_V3B_REGISTER.json").read_text(
        encoding="utf-8"))["slab_binding"]["rows"] if r["annotation"] in CALLOUTS}
    return out, binding


def main():
    before = DR.verify_frozen(MANIFEST, ROOT)
    s = json.loads((PKG / "14_S8_4_SUMMARY.json").read_text(encoding="utf-8"))
    fam = {r["ITEM_ID"]: r for r in _rows(PKG / "05_REINFORCEMENT_QTO.csv")}
    conc = {r["PANEL_ID"]: r for r in _rows(PKG / "04_CONCRETE_QTO.csv") if r["RELEASED"] == "True"}
    lines = v3b_lines()
    sets, binding = v3b_tank_sets()
    assert sorted(sets) == sorted(CALLOUTS), sorted(sets)

    # ------------------------------------------------------------ the four V3b sets, by their own formula
    recon = []
    steps = {"V3B": 0.0, "NO_EMBEDMENT": 0.0, "S8_4_ONE_FACE": 0.0, "S8_4_TWO_FACES": 0.0, "S8_4_RELEASED": 0.0}
    for h, (pid, d) in CALLOUTS.items():
        st, b = sets[h], binding[h]
        dia = int(st["dia_mm"])
        own = st["count"] * st["bar_m"] * kg_m(dia)
        assert abs(own - st["tech_kg"]) < 1e-6, h                         # V3b's figure = its own formula
        clear = b["clear_span_mm"] / 1000.0
        embed = sum(b["embed_mm"]) / 1000.0
        assert abs(clear + embed - st["bar_m"]) < 1e-9 and not b["top"]
        no_emb = st["count"] * clear * kg_m(dia)
        bottom, top = fam[f"S8.4-R-{pid[-2:]}-{d}-B"], fam[f"S8.4-R-{pid[-2:]}-{d}-T"]
        one = float(top["FULL_LENGTH_M"]) * kg_m(dia)
        two = one + float(bottom["FULL_LENGTH_M"]) * kg_m(dia)
        rel = float(top["RELEASED_KG"]) + float(bottom["RELEASED_KG"])
        n = float(b["n"])
        recon.append({"CALLOUT": h, "PANEL": pid, "DIRECTION": d, "DIA_MM": dia, "RATE_PER_M": n,
                      "V3B_COUNT": st["count"], "V3B_COUNT_RULE": f"floor({n:g} x {b['width_mm'] / 1000:g}) + 1 = "
                                                                  f"{math.floor(n * b['width_mm'] / 1000 + 1e-9) + 1}",
                      "V3B_BAR_M": st["bar_m"], "V3B_RUN": f"clear {clear:g} + embedment {b['embed_mm']}",
                      "V3B_FACES": "ONE (top false; the (T&B) is not read)", "V3B_KG": _r(st["tech_kg"]),
                      "V3B_KG_BY_OWN_FORMULA": _r(own), "V3B_WITHOUT_EMBEDMENT_KG": _r(no_emb),
                      "S8_4_EQUIVALENT_COUNT": _r(float(top["EQUIVALENT_COUNT_UNROUNDED"])),
                      "S8_4_ONE_FACE_FULL_KG": _r(one), "S8_4_TWO_FACES_FULL_KG": _r(two), "S8_4_RELEASED_KG": _r(rel),
                      "S8_4_FAMILIES": [bottom["ITEM_ID"], top["ITEM_ID"]]})
        steps["V3B"] += st["tech_kg"]
        steps["NO_EMBEDMENT"] += no_emb
        steps["S8_4_ONE_FACE"] += one
        steps["S8_4_TWO_FACES"] += two
        steps["S8_4_RELEASED"] += rel
    assert abs(steps["S8_4_RELEASED"] - s["released"]["reinforcement_kg"]) < 1e-6
    bridge = [("V3B four tank sets (one face each)", steps["V3B"]),
              ("RUN_BASIS: less V3b's 2 x 175 mm embedment beyond the faces (S8.4 blocks anchorage)",
               steps["NO_EMBEDMENT"] - steps["V3B"]),
              ("COUNT_BASIS: whole bars floor(n W) + 1 on the rectangle -> unrounded rate x area (panel 01's notch)",
               steps["S8_4_ONE_FACE"] - steps["NO_EMBEDMENT"]),
              ("LAYER: add the second face each callout's (T&B) states", steps["S8_4_TWO_FACES"] - steps["S8_4_ONE_FACE"]),
              ("STOP_ZONE: less the bottom stop zones S8.4 blocks", steps["S8_4_RELEASED"] - steps["S8_4_TWO_FACES"])]
    assert abs(math.fsum(v for _, v in bridge) - steps["S8_4_RELEASED"]) < 1e-6

    # ------------------------------------------------------------ comparison rows
    rows = []

    def C(rid, source, line, scope, ref, unit, s84, cls, why):
        rows.append({"ROW_ID": rid, "SOURCE": source, "LINE": line, "SCOPE": scope, "REFERENCE_QTY": _r(ref),
                     "UNIT": unit, "S8_4_EQUAL_SCOPE_QTY": _r(s84),
                     "DIFFERENCE": _r(s84 - ref) if (ref is not None and s84 is not None) else None,
                     "DIFFERENCE_CLASS": cls, "EXPLANATION": why})
    C("PF-01", "Urban V3b (REBAR_POPULATION_REGISTER)", "R-SLAB-2F_ROOF sets [7A7] [7A8] [796] [798]",
      "EQUAL (the same four callouts in the same two panels)", steps["V3B"], "kg", steps["S8_4_RELEASED"],
      "LAYER + RUN_BASIS + COUNT_BASIS + STOP_ZONE",
      "; ".join(f"{t} {v:+.3f}" for t, v in bridge[1:]) + " (02)")
    r_line = lines["R-SLAB-2F_ROOF"]
    C("PF-02", "Urban V3b (BOQ_LINES_V3B)", "R-SLAB-2F_ROOF (whole 2F roof, 16 bar sets)", "WIDER (whole floor)",
      r_line["qty"], "kg", None, "SCOPE",
      f"the four tank sets ({steps['V3B']:.3f} kg) sit inside this line with the other panels' sets; the line misses "
      f"the (T&B) top faces of the tank panels ({steps['S8_4_TWO_FACES'] - steps['S8_4_ONE_FACE']:.3f} kg at "
      "S8.4's basis); the control plane marks it VERIFIED_PARTIAL_LOWER_BOUND")
    c_line = lines["C-SLAB-2F"]
    a_tank = math.fsum(float(c["NET_AREA_M2"]) for c in conc.values())
    plate = float(c_line["formula"].split("net plate ")[1].split(" m2")[0])
    t_v3b = round(c_line["qty"] / plate, 3)              # V3b rounds its line to 0.001 m3; its thickness is 0.180
    C("PF-03", "Urban V3b (BOQ_LINES_V3B)", "C-SLAB-2F (net plate x t)", "WIDER (whole 2F plate)", c_line["qty"], "m3",
      None, "SCOPE + PLATE_BASIS + THICKNESS_BASIS",
      f"V3b: {plate:g} m2 x {t_v3b:.3f} m for the whole floor (beam strips inside the plate, full depth); the tank "
      f"panels are not itemised (PRE-S8 NOT_ITEMISED). V3b's own rule on the two tank faces gives {a_tank * t_v3b:.4f} "
      f"m3 = S8.4 {s['released']['concrete_m3']:.4f} m3 (NO_DIFFERENCE in thickness there); outside them the source "
      "says 160 mm (P8-N18), V3b uses 180 (PRE-S7 C-05)")
    C("PF-04", "S8.4 rule applied to V3b's tank scope", "two panel faces x 0.180", "EQUAL", a_tank * t_v3b, "m3",
      s["released"]["concrete_m3"], "NO_DIFFERENCE", "same thickness, same faces")
    lin = json.loads(LINEAGE.read_text(encoding="utf-8"))
    slab_cat = [c for c in lin["categories"] if c["category_id"] == "SLABS"][0]
    fq = slab_cat["quantity_by_physical_kind"]["SLAB_NET_2F"]
    s7p = [r for r in _rows(S7_PANELS) if r["FLOOR"] == "2F_ROOF_SLAB" and r["S7_SCOPE"] == "IN_SCOPE_S7"]
    other = math.fsum(float(r["AREA_M2"]) * float(r["THICKNESS_MM"]) / 1000.0 for r in s7p)
    floor_face = other + s["released"]["concrete_m3"]
    C("PF-05", "freelancer QS (lineage)", "SLABS / SLAB_NET_2F (net of beams)", "WIDER (whole 2F slab, net of beams)",
      fq, "m3", None, "SCOPE",
      f"not itemised per panel. Explanation only: the same face-to-face basis over the whole 2F roof (S7's "
      f"{len(s7p)} panels at their 160 mm, {other:.4f} m3, plus S8.4's {s['released']['concrete_m3']:.4f} m3) gives "
      f"{floor_face:.4f} m3, {fq - floor_face:+.4f} m3 from the freelancer net; never a release")
    multi = json.loads(MULTI.read_text(encoding="utf-8"))
    mrow = [r for r in multi["rows"] if r.get("category") == "SLABS" and r.get("subcategory") == "2F"][0]
    C("PF-06", "multi-engine comparison", "SLABS 2F (oracle)", "WIDER (whole 2F slab, full depth)",
      mrow["CHRISTIANNP"], "m3", None, "NOT_COMPARABLE",
      f"the oracle agrees with V3b's full-depth plate ({mrow['URBAN']} m3); no per-panel figure")
    C("PF-07", "freelancer QS (lineage)", "SLABS steel (all floors)", "WIDER (all slabs, all floors)",
      slab_cat.get("steel_value_t"), "t", None, "NOT_COMPARABLE", "one steel tonnage for every slab of the building")
    v2 = json.loads(OLD_V2.read_text(encoding="utf-8"))
    v2s = {ln["code"]: ln for ln in v2["lines"] if ln.get("code") in ("C-SLAB-2F", "R-SLAB-2F_ROOF")}
    C("PF-08", "control plane V2", "C-SLAB-2F / R-SLAB-2F_ROOF states", "WIDER", None, "", None, "NOT_COMPARABLE",
      f"C-SLAB-2F {v2s['C-SLAB-2F']['new_release_state']}; R-SLAB-2F_ROOF {v2s['R-SLAB-2F_ROOF']['new_release_state']}; "
      "neither itemises the tank")
    cov = [r for r in _rows(PRE_S8 / "03_CONCRETE_COVERAGE_MATRIX.csv") if r["FAMILY"] == "WATER_TANK"]
    C("PF-09", "PRE-S8 coverage", "WATER_TANK 2F_ROOF_SLAB", "EQUAL", None, "", s["released"]["concrete_m3"],
      "NOT_COMPARABLE", f"PRE-S8 coverage {cov[0]['COVERAGE_STATE']} / faces {cov[0]['FACE_STATES']}: no earlier "
                        "Urban figure for the tank; S8.4 is the first itemised measure")
    crd = json.loads(CR.read_text(encoding="utf-8"))
    sl = [r for r in crd["rows"] if r.get("trade") == "SLABS"]
    C("PF-10", "coverage-recovery dashboard", "SLABS (all floors)", "WIDER", sl[0]["official_before"] if sl else None,
      "m3", None, "NOT_COMPARABLE", "one slab total for the building; no per-panel figure")
    rows.sort(key=lambda r: r["ROW_ID"])
    _csv(OUT[0], rows)
    _csv(OUT[1], recon)
    after = DR.verify_frozen(MANIFEST, ROOT)
    assert before == after
    summ = {"round": "S8_4_POST_FREEZE", "frozen_manifest_sha256": before["manifest_sha256"],
            "frozen_unchanged": before == after,
            "equal_scope": {"v3b_tank_sets_kg": _r(steps["V3B"]), "s8_4_released_kg": _r(steps["S8_4_RELEASED"]),
                            "bridge": [{"step": t, "kg": _r(v)} for t, v in bridge],
                            "concrete_v3b_rule_on_tank_faces_m3": _r(a_tank * t_v3b),
                            "s8_4_concrete_m3": s["released"]["concrete_m3"]},
            "finding": "the earlier Urban steel for the tank panels counts each (T&B) callout once: the top faces are "
                       "missing; its concrete applies 180 mm to the whole 2F plate where the source says 160 outside "
                       "the two tank panels",
            "rows": {r["ROW_ID"]: r["DIFFERENCE_CLASS"] for r in rows},
            "rule": "explains, never changes a frozen quantity or chooses an interpretation"}
    (HERE / OUT[2]).write_text(json.dumps(summ, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    md = ["# S8.4 post-freeze comparison", "",
          f"Run after the freeze (`15_S8_4_FREEZE_MANIFEST.json`, sha `{before['manifest_sha256'][:12]}…`), verified "
          "before and after; no frozen quantity changes.", "",
          "## Equal scope: the four tank callouts", "",
          f"The old Urban V3b register has one bar set per tank callout, **{steps['V3B']:.3f} kg**, against S8.4's "
          f"**{steps['S8_4_RELEASED']:.3f} kg**. V3b's figure is reproduced by its own formula (count x bar length x "
          "D^2/162) and bridged step by step:", "",
          "| step | kg |", "|---|---|"]
    md += [f"| {t} | {v:+.3f} |" if i else f"| {t} | {v:.3f} |" for i, (t, v) in enumerate(bridge)]
    md += [f"| S8.4 released | {steps['S8_4_RELEASED']:.3f} |", "",
           "- The largest difference is the layer: V3b reads each callout once and never applies its (T&B).",
           "- V3b adds 175 mm embedment at each end and counts whole bars as floor(n W) + 1; S8.4 measures face to "
           "face, blocks anchorage and keeps the count unrounded.", "",
           "## Concrete", "",
           f"- No earlier figure itemises the tank panels. V3b's C-SLAB-2F is the whole plate, {plate:g} m2 x "
           f"{t_v3b:.3f} m = {c_line['qty']} m3; its own thickness on the two tank faces gives "
           f"{a_tank * t_v3b:.4f} m3, the same as S8.4.",
           "- V3b's 180 mm over the whole floor disagrees with the source (160 mm outside the tank panels): PRE-S7 "
           "C-05, outside S8.4's scope.", "",
           "## Other references", ""]
    md += [f"- {r['ROW_ID']} {r['SOURCE']} ({r['LINE']}): {r['DIFFERENCE_CLASS']}. {r['EXPLANATION']}" for r in rows
           if r["ROW_ID"] not in ("PF-01", "PF-04")]
    (HERE / OUT[3]).write_text("\n".join(md) + "\n", encoding="utf-8")
    return summ


if __name__ == "__main__":
    print(json.dumps(main()["equal_scope"], indent=1))
