"""S8.6 post-freeze comparison: the frozen lintel package against the earlier figures, at equal scope, after the
freeze.

    python3 -I research/alsenan_lintels_s8_6/post_freeze/post_freeze_comparison.py

Reads the frozen S8.6 package (verified before and after; never written) and the earlier figures:
  * the old Urban V3b lines C-LINT-GF / 1F / 2F (per-opening details) and R-LINTELS-GF / 1F / 2F_ROOF, and its
    LINTELS rebar population;
  * the R5 opening register's lintel_depth_m (the depth V3b used per opening);
  * the PRE-S8 census quantity column and the 03 coverage-matrix columns for the lintel family.
Every difference is classified (NO_DIFFERENCE, GEOMETRY, SUPPORT_IDENTITY, DOUBLE_COUNT, MISSED_OBJECT,
NOT_COMPARABLE) and explained. Nothing here changes a frozen quantity or chooses an interpretation.
"""

from __future__ import annotations

import csv
import io
import json
import sys
from collections import Counter, defaultdict
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
R5 = R / "alsenan_arch_truth_05/registers/OPENING_EVIDENCE_REGISTER_V3.json"
PRE_S8 = R / "pre_s8_structural_completeness"
MANIFEST = PKG / "15_S8_6_FREEZE_MANIFEST.json"
OUT = ["01_POST_FREEZE_COMPARISON.csv", "02_FLOOR_TOTALS.csv", "03_POST_FREEZE_SUMMARY.json",
       "00_POST_FREEZE_README.md"]
FLOOR_OF = {"GF": "GF", "1F": "1F", "2F_ROOF": "2F"}


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


def _csv(name, rows, fields):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: _cell(r.get(k)) for k in fields})
    (HERE / name).write_text(buf.getvalue(), encoding="utf-8")


def v3b():
    d = json.loads(V3B_LINES.read_text(encoding="utf-8"))
    lines = d.get("rows") or d.get("lines") or next(v for v in d.values() if isinstance(v, list))
    conc = {l["code"]: l for l in lines if l.get("code", "").startswith("C-LINT-")}
    reb = {l["code"]: l for l in lines if l.get("code", "").startswith("R-LINTELS-")}
    pop = [p for p in json.loads(V3B_POP.read_text(encoding="utf-8"))["rows"] if p.get("population") == "LINTELS"] \
        if isinstance(json.loads(V3B_POP.read_text(encoding="utf-8")), dict) and \
        "rows" in json.loads(V3B_POP.read_text(encoding="utf-8")) else []
    return conc, reb, pop


def run():
    DR.verify_frozen(MANIFEST, ROOT)
    cen = {r["OPENING_ID"]: r for r in _rows(PKG / "01_OPENING_CENSUS.csv") if r["RECORD"] == "OPENING"}
    bm = {r["OPENING_ID"]: r for r in _rows(PKG / "04_OPENING_LINTEL_BINDING_MATRIX.csv")}
    conc = {r["OPENING_ID"]: r for r in _rows(PKG / "06_LINTEL_CONCRETE_QTO.csv")}
    s86 = json.loads((PKG / "14_S8_6_SUMMARY.json").read_text(encoding="utf-8"))
    r5_of = {}
    for oid, r in cen.items():
        for x in json.loads(r["R5_IDS"] or "[]"):
            r5_of[x] = oid
    r5d = {r["id"]: r.get("lintel_depth_m") for r in json.loads(R5.read_text(encoding="utf-8"))["rows"]}
    vc, vr, vpop = v3b()
    out, seen = [], set()
    for code in sorted(vc):
        line = vc[code]
        fl = FLOOR_OF[line["level"]]
        for det in line["details"]:
            ref = det["ref"]
            oid = r5_of.get(ref)
            o = bm.get(oid) if oid else None
            c = conc.get(oid) if oid else None
            ours = float(c["M3"]) if c else None
            if oid is None:
                cls, why = "NOT_COMPARABLE", "the R5 row matches no S8.6 opening"
            elif oid in seen:
                cls, why = "DOUBLE_COUNT", (f"second R5 row for {oid} (R5 lists a door and a glazed-door candidate in "
                                            "one gap): V3b counts the lintel twice")
            elif o["DECISION"] == "SCHEDULE_BOUND_LINTEL":
                if abs(ours - det["qty"]) <= 0.0005:
                    cls, why = "NO_DIFFERENCE", "same opening, same row, full 400 mm bearing both sides"
                else:
                    shared = float(c["SHARED_CORNER_M3"] or 0)
                    cls, why = "GEOMETRY", (f"S8.6 bearing {float(c['BEARING_START_MM']):.1f} / "
                                            f"{float(c['BEARING_END_MM']):.1f} mm ({c['START_SUPPORT']} / "
                                            f"{c['END_SUPPORT']})" + (f", corner shared with another lintel "
                                                                      f"({shared:.6f} m3 counted there)"
                                                                      if shared else "") +
                                            "; V3b assumes 400 + 400 and no shared corner")
            else:
                cls, why = "SUPPORT_IDENTITY", (f"S8.6 {o['DECISION']}: {o['REASON'][:160]}; V3b adds a lintel "
                                                "regardless of the beam over the opening")
            if oid:
                seen.add(oid)
            out.append({"V3B_LINE": code, "FLOOR": fl, "V3B_REF": ref, "V3B_FORMULA": det["formula"],
                        "V3B_M3": det["qty"], "R5_LINTEL_DEPTH_M": r5d.get(ref), "S8_6_OPENING": oid,
                        "S8_6_DECISION": o["DECISION"] if o else None,
                        "S8_6_M3_RELEASED": ours if o and o["DECISION"] == "SCHEDULE_BOUND_LINTEL" else 0.0,
                        "S8_6_M3_SENSITIVITY": ours if c and c["LANE"] == "SENSITIVITY_ONLY" else None,
                        "CLASS": cls, "EXPLANATION": why})
    v3b_ops = {r["S8_6_OPENING"] for r in out if r["S8_6_OPENING"]}
    for oid, r in sorted(cen.items()):
        if oid in v3b_ops or r["KIND"] == "SLAB_OPENING":
            continue
        c = conc.get(oid)
        out.append({"V3B_LINE": None, "FLOOR": r["FLOOR"], "V3B_REF": None, "V3B_M3": 0.0, "S8_6_OPENING": oid,
                    "S8_6_DECISION": bm[oid]["DECISION"],
                    "S8_6_M3_RELEASED": float(c["M3"]) if c and c["LANE"] == "PROJECT_BASIS_QTO" else 0.0,
                    "S8_6_M3_SENSITIVITY": float(c["M3"]) if c and c["LANE"] == "SENSITIVITY_ONLY" else None,
                    "CLASS": "MISSED_OBJECT", "EXPLANATION": f"{r['TYPE']} found by S8.6, absent from R5 / V3b"})
    F = ["V3B_LINE", "FLOOR", "V3B_REF", "V3B_FORMULA", "V3B_M3", "R5_LINTEL_DEPTH_M", "S8_6_OPENING",
         "S8_6_DECISION", "S8_6_M3_RELEASED", "S8_6_M3_SENSITIVITY", "CLASS", "EXPLANATION"]
    _csv(OUT[0], out, F)
    tot = []
    for code in sorted(vc):
        fl = FLOOR_OF[vc[code]["level"]]
        det_sum = sum(d["qty"] for d in vc[code]["details"])
        tot.append({"FLOOR": fl, "ITEM": "CONCRETE_M3", "V3B_LINE": code, "V3B_QTY": vc[code]["qty"],
                    "V3B_DETAIL_SUM": _r(det_sum), "S8_6_RELEASED": s86["released"]["concrete_m3_by_floor"][fl],
                    "S8_6_SENSITIVITY": _r(sum(float(c["M3"]) for c in conc.values()
                                               if c["FLOOR"] == fl and c["LANE"] == "SENSITIVITY_ONLY")),
                    "DOUBLE_COUNT_M3": _r(sum(r["V3B_M3"] for r in out if r["FLOOR"] == fl and
                                              r["CLASS"] == "DOUBLE_COUNT"))})
    for code in sorted(vr):
        fl = FLOOR_OF[vr[code]["level"]]
        tot.append({"FLOOR": fl, "ITEM": "REBAR_KG", "V3B_LINE": code, "V3B_QTY": vr[code]["qty"],
                    "S8_6_RELEASED": _r(sum(s86["released"]["kg_by_floor_and_diameter"][fl].values())),
                    "NOTE": vr[code]["formula"]})
    _csv(OUT[1], tot, ["FLOOR", "ITEM", "V3B_LINE", "V3B_QTY", "V3B_DETAIL_SUM", "S8_6_RELEASED", "S8_6_SENSITIVITY",
                       "DOUBLE_COUNT_M3", "NOTE"])
    pre = [r for r in _rows(PRE_S8 / "02_STRUCTURAL_ELEMENT_CENSUS.csv") if r["ELEMENT_ID"] == "SPC-LINTELS"]
    cov = [r for r in _rows(PRE_S8 / "03_CONCRETE_COVERAGE_MATRIX.csv") if r["FAMILY"] == "LINTEL"]
    summ = {"round": "S8_6_POST_FREEZE", "frozen_manifest_sha256": DR.verify_frozen(MANIFEST, ROOT)["manifest_sha256"],
            "classes": dict(sorted(Counter(r["CLASS"] for r in out).items())),
            "v3b_concrete_m3": {FLOOR_OF[l["level"]]: l["qty"] for l in vc.values()},
            "v3b_concrete_total_m3": _r(sum(l["qty"] for l in vc.values())),
            "v3b_rebar_kg": {FLOOR_OF[l["level"]]: l["qty"] for l in vr.values()},
            "v3b_rebar_total_kg": _r(sum(l["qty"] for l in vr.values())),
            "v3b_population": vpop,
            "s8_6_released_m3": s86["released"]["concrete_m3"], "s8_6_released_kg": s86["released"]["kg"],
            "s8_6_sensitivity_m3": s86["sensitivity_not_released"]["m3"],
            "s8_6_sensitivity_kg": s86["sensitivity_not_released"]["kg"],
            "double_count_m3": _r(sum(r["V3B_M3"] for r in out if r["CLASS"] == "DOUBLE_COUNT")),
            "pre_s8_quantity_state": pre[0]["CONCRETE_QUANTITY_STATE"] if pre else None,
            "pre_s8_coverage": {k: cov[0][k] for k in ("URBAN_LINES", "V3B_LINE_TECHNICAL_M3_SHARED",
                                                       "COVERAGE_STATE")} if cov else None,
            "rule": "explains differences; never changes a frozen quantity"}
    (HERE / OUT[2]).write_text(json.dumps(summ, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    L = ["# S8.6 post-freeze comparison", "", "Frozen package verified before and after. Classes: " +
         ", ".join(f"{k} {v}" for k, v in summ["classes"].items()) + ".", "",
         f"- V3b lintel concrete {summ['v3b_concrete_total_m3']} m3 ({summ['v3b_concrete_m3']}); S8.6 releases "
         f"{summ['s8_6_released_m3']} m3 and holds {summ['s8_6_sensitivity_m3']} m3 as sensitivity.",
         f"- V3b counts {summ['double_count_m3']} m3 twice (four R5 door + glazed-door pairs).",
         f"- V3b lintel bars {summ['v3b_rebar_total_kg']} kg (hooks from ACI tables, a generic rule the project does "
         f"not state); S8.6 releases {summ['s8_6_released_kg']} kg, sensitivity {summ['s8_6_sensitivity_kg']} kg.",
         "- Main cause: V3b gives every opening a lintel; S8.6 blocks the openings with an S1 beam band over them "
         "until a head level is printed.", ""]
    (HERE / OUT[3]).write_text("\n".join(L) + "\n", encoding="utf-8")
    DR.verify_frozen(MANIFEST, ROOT)
    return summ


if __name__ == "__main__":
    print(json.dumps(run(), indent=1, ensure_ascii=False))
