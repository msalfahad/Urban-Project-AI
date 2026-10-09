"""S8.3 post-freeze comparison: the frozen dome / ring QTO against earlier figures, at equal scope, after the freeze.

    python3 -I research/alsenan_dome_ring_s8_3/post_freeze/post_freeze_comparison.py

Reads the frozen S8.3 package (verified before and after; never written) and the earlier figures:
  * old Urban register lines (control plane 2: C-DOME-SHELL-*, C-DOME-RING-*, R-DOME-*), and the old builder's dome
    formula, re-evaluated here only to explain its figures;
  * the freelancer QS lineage (row 'القبه' = dome) and the multi-engine concrete comparison;
  * the christiannp / Urban slab-opening crosswalk (an interface, not an S8.3 quantity).
Every difference is classified (POPULATION, SCOPE, GEOMETRY_INPUT, NTS_BASIS, SURFACE_BASIS, NOT_COMPARABLE,
NO_DIFFERENCE) and explained. Nothing here changes a frozen quantity or chooses an interpretation.
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
OLD_V2 = R / "alsenan_control_plane_02/registers/ALSENAN_CONTROL_V2_CANDIDATE.json"
LINEAGE = R / "alsenan_multi_engine_comparison/FREELANCER_CATEGORY_LINEAGE.json"
MULTI = R / "alsenan_multi_engine_comparison/MULTI_ENGINE_CONCRETE_COMPARISON.json"
GAPS = R / "R9_1_CHRIS_POST_FREEZE/02_OBJECT_GAP_REGISTER.csv"
MANIFEST = PKG / "16_S8_3_FREEZE_MANIFEST.json"
OUT = ["01_POST_FREEZE_COMPARISON.csv", "02_OLD_FORMULA_RECONSTRUCTION.csv", "03_POST_FREEZE_SUMMARY.json",
       "00_POST_FREEZE_README.md"]
KG12 = 12 * 12 / 162.0


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


def old_lines():
    out = {}

    def walk(o):
        if isinstance(o, dict):
            c = o.get("code", "")
            if c.startswith(("C-DOME", "R-DOME")):
                q = o.get("v2_qty") or {}
                out[c] = {"desc": o.get("desc_en"), "old_technical": o.get("old_v3b_technical_qty"),
                          "release": o.get("new_release_state"),
                          "value": next((q[k] for k in ("verified", "lower_bound", "provisional") if q.get(k) is not None), None)}
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(json.loads(OLD_V2.read_text(encoding="utf-8")))
    return out


def freelancer_dome():
    d = json.loads(LINEAGE.read_text(encoding="utf-8"))
    found = []

    def walk(o):
        if isinstance(o, dict):
            if o.get("physical_kind") == "DOME" and o.get("kind") == "LEAF_ROW":
                found.append(o)
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(d)
    assert len(found) == 1, "one freelancer dome row"
    f = found[0]
    return {"count": f["count"], "factor": f["B"], "area_m2": f["C"], "t_m": f["D"], "value": f["value"], "cell": f["cell"]}


def multi_dome():
    d = json.loads(MULTI.read_text(encoding="utf-8"))
    hit = []

    def walk(o):
        if isinstance(o, dict):
            if o.get("category") == "DOME" and "FREELANCER_QS" in o:
                hit.append(o)
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(d)
    return hit[0]


def opening_refs():
    out = []
    for r in _rows(GAPS):
        txt = " ".join(r.values())
        m = re.search(r"Urban ([\d.]+) / christiannp ([\d.]+) m2", txt)
        if m and "radial fan (dome)" in txt:
            out.append((float(m.group(1)), float(m.group(2))))
    return out


def old_shell(a, h, t):
    """the old builder's shell: mid-surface area 2 pi (R - t/2)(h - t/2) x t, R from the plan radius and the rise."""
    Rr = (a * a + h * h) / (2 * h)
    area_mid = 2 * math.pi * (Rr - t / 2) * (h - t / 2)
    return {"R": Rr, "area_mid": area_mid, "m3": area_mid * t, "mesh_kg": area_mid * 2 / 0.15 * KG12}


def build():
    before = DR.verify_frozen(MANIFEST, ROOT)
    s = json.loads((PKG / "15_S8_3_SUMMARY.json").read_text(encoding="utf-8"))
    g = {r["ROW_ID"]: r for r in _rows(PKG / "04_RING_GEOMETRY.csv")}
    sens = {r["CASE_ID"]: float(r["VALUE"]) for r in _rows(PKG / "12_SENSITIVITY_CASES.csv")}
    old = old_lines()
    fr = freelancer_dome()
    multi = multi_dome()
    opens = opening_refs()
    a = float(g["DOME-A-OPENING"]["R2_MM"]) / 1000.0
    shell_one = s["shell"]["volume"]
    released_m3, released_kg = s["released"]["concrete_m3"], s["released"]["reinforcement_kg"]

    # ------------------------------------------------------------ old formula re-evaluated (explanation only)
    rec = []
    for rise, why in ((1.72, "the NW elevation '172': railing top to apex, not springing to apex"),
                      (1.90, "the p.7 rise '190' (springing to the outer apex)")):
        o = old_shell(a, rise, 0.10)
        rec.append({"CASE": f"old shell formula, plan radius {a:.4f} m, rise {rise:.2f} m", "WHY": why,
                    "R_M": o["R"], "MID_AREA_M2": o["area_mid"], "SHELL_M3": o["m3"], "MESH_KG_ONE_MESH": o["mesh_kg"]})
    tw = old_shell(2.205, 2.15, 0.10)
    rec.append({"CASE": "old shell formula, tower: plan radius 2.205 m, rise 2.15 m", "WHY": "architectural tower "
                "circle and the elevations' '215'", "R_M": tw["R"], "MID_AREA_M2": tw["area_mid"], "SHELL_M3": tw["m3"],
                "MESH_KG_ONE_MESH": tw["mesh_kg"]})
    cl_detail = 2 * float(g["DOME-A-RING-DETAIL"]["R1_MM"]) / 1000.0 + 0.2
    ring_old = math.pi * cl_detail * 0.20 * 0.75
    rec.append({"CASE": f"old ring: pi x {cl_detail:.4f} m centreline x 0.20 x 0.75", "WHY": "detail-reading "
                "centreline with the drawn N.I.S depth 0.75 m", "R_M": cl_detail / 2, "MID_AREA_M2": None,
                "SHELL_M3": ring_old, "MESH_KG_ONE_MESH": None})
    ring_bars_old = math.pi * cl_detail * (3 * 16 ** 2 + 3 * 18 ** 2 + 4 * 14 ** 2) / 162.0
    rec.append({"CASE": "old ring bars: 3T16 + 3T18 + 4T14 as closed circles on the detail centreline", "WHY": "before "
                "links and laps", "R_M": cl_detail / 2, "MID_AREA_M2": None, "SHELL_M3": None,
                "MESH_KG_ONE_MESH": ring_bars_old})

    # ------------------------------------------------------------ comparison rows
    rows = []

    def C(i, item, s83, lane, ref_name, ref, same, cls, why):
        d = None if s83 is None or ref is None else s83 - ref
        rows.append({"ROW_ID": i, "ITEM": item, "S8_3_VALUE": s83, "S8_3_LANE": lane, "REFERENCE": ref_name,
                     "REFERENCE_VALUE": ref, "SAME_SCOPE": same, "DIFFERENCE": d,
                     "DIFFERENCE_PCT": None if d is None or not ref else 100 * d / ref, "CLASS": cls, "EXPLANATION": why})
    old_terr = old["C-DOME-SHELL-12EB"]["value"] + old["C-DOME-SHELL-2F33"]["value"]
    C("PF-01", "concrete: two terrace dome shells (m3)", released_m3, "PROJECT_BASIS_QTO", "old Urban C-DOME-SHELL-12EB "
      "+ -2F33", old_terr, True, "GEOMETRY_INPUT",
      f"the old formula with rise 1.72 m reproduces {rec[0]['SHELL_M3']:.3f} per shell; with the p.7 rise 1.90 it gives "
      f"{rec[1]['SHELL_M3']:.3f}, within {abs(rec[1]['SHELL_M3'] - shell_one) * 1000:.1f} litres of S8.3's exact "
      f"{shell_one:.6f}: the difference is the rise reading, not the formula")
    C("PF-02", "concrete: two terrace dome shells (m3)", released_m3, "PROJECT_BASIS_QTO",
      f"freelancer QS '{fr['cell']}' two of {fr['count']} domes", 2 * fr["value"] / fr["count"], True, "SURFACE_BASIS",
      f"freelancer {fr['factor']} x {fr['area_m2']} m2 x {fr['t_m']} m per dome (surface basis not stated); S8.3 "
      f"mid-surface {s['shell']['area_mid']:.4f} m2 x 0.10 equivalent, exact concentric caps")
    C("PF-03", "concrete: tower dome shell (m3)", None, "SOURCE_CONFLICT (not quantified)", "old Urban C-DOME-SHELL-1300",
      old["C-DOME-SHELL-1300"]["value"], False, "POPULATION",
      f"old Urban counts the architectural-only tower dome as RC ({old['C-DOME-SHELL-1300']['release']}); S8.3 does not "
      f"(no structural occurrence, section A-A draws none). S8.3's sensitivity with the terrace thickness, "
      f"{sens['SA-TOWER-SHELL']:.6f}, matches the old {old['C-DOME-SHELL-1300']['value']} (old formula "
      f"{tw['m3']:.3f}): same arithmetic, different population decision")
    C("PF-04", "concrete: tower dome shell (m3)", None, "SOURCE_CONFLICT (not quantified)",
      f"freelancer QS (one of {fr['count']})", fr["value"] / fr["count"], False, "POPULATION",
      "the freelancer counts three domes; S8.3 counts two structural")
    for k, t in (("C-DOME-RING-12EB", "DOME-A"), ("C-DOME-RING-2F33", "DOME-B"), ("C-DOME-RING-1300", "DOME-TOWER")):
        C(f"PF-05-{t}", f"concrete: ring beam {t} (m3)", None, "SOURCE_CONFLICT", f"old Urban {k}", old[k]["value"], False,
          "NTS_BASIS" if t != "DOME-TOWER" else "POPULATION",
          f"old: pi x {cl_detail:.4f} x 0.20 x 0.75 = {ring_old:.3f}: the drawn N.I.S depth, which the source dimensions "
          f"'AS PER ARCH'; S8.3 keeps the depth and the plan position open (sensitivity "
          f"{sens['SA-DOME-A-RING-PLAN-50']:.3f}-{sens['SA-DOME-B-RING-DETAIL-130']:.3f} m3 per terrace ring)"
          if t != "DOME-TOWER" else "a ring under an architectural-only dome")
    C("PF-06", "concrete: all dome lines (m3)", released_m3, "PROJECT_BASIS_QTO", "old Urban domes, verified layer",
      multi["URBAN"], False, "POPULATION", "old 7.523 = two terrace shells + the tower shell; its best layer 13.49 adds "
      "three provisional rings")
    C("PF-07", "concrete: all dome lines (m3)", released_m3, "PROJECT_BASIS_QTO", "freelancer QS domes", fr["value"],
      False, "POPULATION", "three domes in the freelancer, two in S8.3")
    C("PF-08", "reinforcement: two terrace domes (kg)", released_kg, "PROJECT_BASIS_QTO", "old Urban R-DOME-1F",
      old["R-DOME-1F"]["value"], False, "SCOPE",
      f"old = shell mesh at rise 1.72 ({2 * rec[0]['MESH_KG_ONE_MESH']:.3f} kg for two) + ring bars on the detail "
      f"centreline ({2 * ring_bars_old:.3f} kg for two) + links at the N.I.S depth and laps (the rest); S8.3 releases "
      f"only the mesh at rise 1.90 ({2 * rec[1]['MESH_KG_ONE_MESH']:.3f} kg old formula vs {released_kg:.3f})")
    C("PF-09", "reinforcement: tower dome (kg)", None, "SOURCE_CONFLICT (not quantified)", "old Urban R-DOME-2F_ROOF",
      old["R-DOME-2F_ROOF"]["value"], False, "POPULATION", "architectural-only dome")
    C("PF-10", "reinforcement: domes (kg)", released_kg, "PROJECT_BASIS_QTO", "freelancer QS", None, False,
      "NOT_COMPARABLE", "the freelancer gives one steel figure for stairs and dome together")
    for i, (u, c) in enumerate(sorted(opens), 1):
        t = "DOME-A" if i == 1 else "DOME-B"
        ours = float(g[f"{t}-OPENING"]["PLAN_AREA_M2"]) + float(g[f"{t}-RING-PLAN"]["PLAN_AREA_M2"])
        bay = (float(g[f"{t}-FACE+x"]["R1_MM"]) - float(g[f"{t}-FACE-x"]["R1_MM"])) * \
            (float(g[f"{t}-FACE+y"]["R1_MM"]) - float(g[f"{t}-FACE-y"]["R1_MM"])) / 1e6
        C(f"PF-11-{t}", f"interface: slab region under {t} (m2, matched by area)", ours, "geometry (no S8.3 quantity)",
          "old Urban radial-fan void", u, True, "NO_DIFFERENCE" if abs(ours - u) < 0.01 else "GEOMETRY_INPUT",
          "S8.3 opening + plan-reading ring inside the bay; old Urban deducted this as a void")
        C(f"PF-12-{t}", f"interface: slab region under {t} (m2, matched by area)", bay, "geometry (no S8.3 quantity)",
          "christiannp kept as slab", c, True, "NO_DIFFERENCE" if abs(bay - c) < 0.01 else "GEOMETRY_INPUT",
          "christiannp keeps the whole bay rectangle as slab (not deducted); S7 excludes the dome-zone faces")
    C("PF-13", "ownership: S6 dome ring arcs (kg)", 0.0, "TRANSFERRED_OUT", "S6 / S6.1 (frozen)", 0.0, True,
      "NO_DIFFERENCE", "eight segments move to S8.3 with no quantity")
    C("PF-14", "S7 top-support steel at the dome bays (kg)", s["s7_dome_adjacent_kg"]["total"], "STAYS_WITH_S7",
      "S7 / S7A (frozen)", s["s7_dome_adjacent_kg"]["total"], True, "NO_DIFFERENCE", "neither added nor subtracted")
    after = DR.verify_frozen(MANIFEST, ROOT)
    assert before["manifest_sha256"] == after["manifest_sha256"], "the frozen package changed"
    for o in OUT:
        if (HERE / o).exists():
            (HERE / o).unlink()
    _csv(OUT[0], rows)
    _csv(OUT[1], rec)
    summary = {"round": "S8_3_POST_FREEZE", "frozen_manifest_sha256": after["manifest_sha256"],
               "frozen_quantities_unchanged": True, "rows": len(rows),
               "classes": {c: sum(1 for r in rows if r["CLASS"] == c) for c in sorted({r["CLASS"] for r in rows})},
               "references": [str(p.relative_to(ROOT)) for p in (OLD_V2, LINEAGE, MULTI, GAPS)],
               "headline": {"s8_3_concrete_m3": released_m3, "s8_3_reinforcement_kg": released_kg,
                            "old_urban_terrace_shells_m3": _r(old_terr, 6), "old_urban_all_dome_m3": multi["URBAN"],
                            "freelancer_all_dome_m3": _r(fr["value"], 6), "old_urban_terrace_rebar_kg": old["R-DOME-1F"]["value"],
                            "old_urban_tower_rebar_kg": old["R-DOME-2F_ROOF"]["value"]}}
    (HERE / OUT[2]).write_text(json.dumps(summary, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    L = ["# S8.3 post-freeze comparison", "",
         f"Run after the freeze (`{MANIFEST.name}` {after['manifest_sha256'][:12]}…, verified before and after; nothing "
         "frozen changes).", "", "| row | item | S8.3 | reference | value | same scope | class |", "|---|---|---|---|---|---|---|"]
    L += [f"| {r['ROW_ID']} | {r['ITEM']} | {_cell(_r(r['S8_3_VALUE'], 3)) or '-'} | {r['REFERENCE']} | "
          f"{_cell(_r(r['REFERENCE_VALUE'], 3)) or '-'} | {r['SAME_SCOPE']} | {r['CLASS']} |" for r in rows]
    L += ["", "## Why they differ", ""] + [f"- **{r['ROW_ID']}**: {r['EXPLANATION']}." for r in rows]
    (HERE / OUT[3]).write_text("\n".join(L) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), indent=1, sort_keys=True, ensure_ascii=False))
