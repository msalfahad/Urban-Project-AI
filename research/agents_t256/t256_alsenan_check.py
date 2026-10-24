"""T-256 Alsenan check: the 15 CONFLICT columns and the 5 NOT_DRAWN upper lines of CONC.COLUMN, per-member evidence.

Inputs (committed, values only): ALSENAN_T256_EVIDENCE.json (t256_extract.py on the Drive copies), the T-248 ledger
(research/agents_t248/LEDGER_T248.csv: members, heights, ranges). Writes LEDGER_T256.csv and summary.json.
Nothing is applied to any engine, candidate or released line (lane I decides after the Checker).

    python3 -I research/agents_t256/t256_alsenan_check.py [--write]
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import column_evidence as CE  # noqa: E402

PLATE_T = {"GF": 0.16, "1F": 0.16}   # one 0.16 plate on ST p.4 (GF roof) and p.5 (1F roof): T-220 / T-248 (merged)
SHEET = {"GF": "GFRS", "1F": "FFRS", "2F": "SFRS"}
PAGE = {"GF": 4, "1F": 5, "2F": 6}


def load():
    ev = json.load(open(HERE / "ALSENAN_T256_EVIDENCE.json", encoding="utf-8"))
    led = {r["member"]: r for r in csv.DictReader(open(ROOT / "research/agents_t248/LEDGER_T248.csv", encoding="utf-8"))}
    return ev, led


def sources_for(m):
    s = m["storey"]
    plan = f"ST dxf: {SHEET[s]} slab plan (PDF p.{PAGE[s]})"
    src = [CE.Source("SCHEDULE", *m["schedule_cm"], "cm", "ST dxf: column schedule (PDF p.9)",
                     ref=f"CGT {m['schedule_handle']} band {m['schedule_band']}"),
           CE.Source("DRAWN", *m["drawn_mm"], "mm", plan, ref=m["member"])]
    if m["pdf_plot_mm"]:
        src.append(CE.Source("DRAWN", *m["pdf_plot_mm"], "mm", f"ST pdf p.{PAGE[s]} plot", copy_of=plan,
                             ref="vector fill"))
    for c in m["arch_outline_copies"]:
        src.append(CE.Source("DRAWN", c["W_mm"], c["D_mm"], "mm", f"ARCH dxf: {s} plan, layer S-COL.BON", copy_of=plan,
                             ref=c["handle"]))
    for d in m["arch_dims_both_points_on_faces"]:
        if d["face_to_face"]:
            raise SystemExit(f"{m['member']}: an architectural face-to-face dimension exists ({d}); classify it first")
    if m["gr_band_cm"] and m["schedule_band"] != "GR":
        src.append(CE.Source("SCHEDULE", *m["gr_band_cm"], "cm", "ST dxf: column schedule (PDF p.9)", member_specific=False,
                             ref="GR band of the same type: the storey below, context only"))
    for w, d, h in m["foundation_cap_text_cm"]:
        src.append(CE.Source("TEXT", w, d, "cm", "ST dxf: CAP column & axis plan (PDF p.1)", member_specific=False,
                             ref=f"text {h} at the neck of the same stack: the FOUNDATION member, context only"))
    if m["kind"] == "TURNED":
        src.append(CE.Source("DRAWN", 200, 1000, "mm", "ST pdf p.15 typical detail of twisted column",
                             member_specific=False, ref="typical: column in first drawn narrower than the 25 column in ground, unprinted"))
    return src


def diagnose(m):
    dr = sorted(m["drawn_mm"])
    sc = sorted(x * 10 for x in m["schedule_cm"])
    gr = sorted(x * 10 for x in m["gr_band_cm"]) if m["gr_band_cm"] else None
    which = [n for n, a, b in (("short side", dr[0], sc[0]), ("long side", dr[1], sc[1])) if abs(a - b) > 5]
    walls = m["arch_wall_lines_through_member_mm_from_face"]
    return {"differs_in": which, "drawn_equals_gr_band": gr is not None and dr == gr and m["schedule_band"] != "GR",
            "arch_wall_faces_through_member_mm": [f"{a}{b}" for a, b in walls]}


def build():
    ev, led = load()
    rows, recs = [], []
    for m in ev["members"]:
        L = led[m["member"]]
        rec = CE.classify(m["member"], sources_for(m))
        h = float(L["h_lo"])
        lo, hi = rec.m3(h)
        drawn_a = round(m["drawn_mm"][0] * m["drawn_mm"][1] / 1e6, 6)
        sched_a = round(m["schedule_cm"][0] * m["schedule_cm"][1] / 1e4, 6)
        tr = CE.plate_transfer(drawn_a, sched_a, PLATE_T[m["storey"]])
        dg = diagnose(m)
        rows.append({
            "member": m["member"], "storey": m["storey"], "mark": m["mark"], "kind": m["kind"], "neck": m["neck"],
            "drawn_mm": "x".join(map(str, m["drawn_mm"])), "schedule_cm": f"{m['schedule_band']} " + "x".join(map(str, m["schedule_cm"])),
            "pdf_plot_mm": "x".join(map(str, m["pdf_plot_mm"])) if m["pdf_plot_mm"] else "",
            "pdf_same_as_dxf": m["pdf_agrees_with_dxf"],
            "arch_copy_same_as_dxf": all(c["same_size"] for c in m["arch_outline_copies"]) and bool(m["arch_outline_copies"]),
            "arch_face_to_face_dims": sum(1 for d in m["arch_dims_both_points_on_faces"] if d["face_to_face"]),
            "slab_plan_print_at_member": m["slab_plan_text_or_dim_at_member"],
            "third_independent_printed": len(rec.third),
            "status": rec.status, "basis": rec.basis, "differs_in": "+".join(dg["differs_in"]),
            "drawn_equals_gr_band": dg["drawn_equals_gr_band"],
            "a_lo": rec.range_m2[0], "a_hi": rec.range_m2[1], "h": h, "m3_lo": lo, "m3_hi": hi,
            "t248_m3_lo": float(L["m3_lo"]), "t248_m3_hi": float(L["m3_hi"]),
            "plate_transfer_schedule_reading_m3": tr["m3"], "plate_transfer_kind": tr["kind"],
            "designer_item": "D-16" if m["mark"] == "C8" else "NEW (T-217 'D-64' label collides with D-64 opening)",
        })
        recs.append(rec)
    ex = []
    for a in ev["not_drawn_lines"]:
        s = a["storey"]
        below = {"1F": "GFRS", "2F": "FFRS"}[s]
        searched = {
            "storey structural plan": a["searched"][f"ST dxf {SHEET[s]} (column layers + texts, 0.6 m)"],
            "plot of the storey plan": a["searched"][f"ST pdf p.{PAGE[s]} (filled outlines, 0.6 m)"],
            "architectural plan of the storey": a["searched"][f"architectural dxf {s} plan (S-COL.BON, 0.6 m)"],
            "structural plan below (start / stop symbol)": "FOUND" if a[f"start_symbol_on_{below}"] else "ABSENT",
        }
        mt = ev["schedule_type_table"][a["mark"]]
        band_key = "band_2ND_printed" if s == "2F" else "band_1ST_printed"
        r = CE.existence(a["line"], searched, member_specific_print=a[f"texts_within_0.6m_on_{SHEET[s]}"] > 0,
                         type_band_only=mt[band_key])
        r.update({"storey": s, "mark": a["mark"], "neck": a["neck"], "route_g_m3": a["route_g_m3"], "searched": searched,
                  "column_below": a[f"column_below_on_{below}"]})
        ex.append(r)
    return ev, rows, recs, ex


def summarise(ev, rows, ex):
    def tot(rs, k):
        return round(sum(r[k] for r in rs), 6)
    by = {}
    for s in ("GF", "1F"):
        rs = [r for r in rows if r["storey"] == s]
        by[s] = {"n": len(rs), "m3": [tot(rs, "m3_lo"), tot(rs, "m3_hi")],
                 "plate_transfer_schedule_reading_m3": tot(rs, "plate_transfer_schedule_reading_m3")}
    tt = ev["schedule_type_table"]
    return {
        "method": CE.METHOD, "rule": CE.RULE,
        "conflict_members": len(rows),
        "status_count": {k: sum(1 for r in rows if r["status"] == k) for k in ("AGREE", "SETTLED", "CONFLICT", "HELD")},
        "basis_count": {k: sum(1 for r in rows if r["basis"] == k) for k in sorted({r["basis"] for r in rows})},
        "conflict_m3": [tot(rows, "m3_lo"), tot(rows, "m3_hi")],
        "equals_t248": all(abs(r["m3_lo"] - r["t248_m3_lo"]) < 1e-9 and abs(r["m3_hi"] - r["t248_m3_hi"]) < 1e-9 for r in rows),
        "by_storey": by,
        "differs_in": {k: sum(1 for r in rows if r["differs_in"] == k) for k in sorted({r["differs_in"] for r in rows})},
        "drawn_equals_gr_band_1F": sum(1 for r in rows if r["storey"] == "1F" and r["drawn_equals_gr_band"]),
        "independence": {
            "pdf_plot_same_as_dxf_on_all_15": all(r["pdf_same_as_dxf"] for r in rows),
            "pdf_storeys": {s: {k: v for k, v in d.items() if k != "rows"} for s, d in ev["pdf"]["storeys"].items()},
            "arch_column_layers": ev["arch_column_layers"], "arch_column_outlines_total": ev["arch_column_outlines_total"],
            "arch_vs_structural": ev["arch_vs_structural_column_layer"],
            "arch_copy_same_on_all_15": all(r["arch_copy_same_as_dxf"] for r in rows),
            "arch_face_to_face_dims_on_the_15": sum(r["arch_face_to_face_dims"] for r in rows),
            "slab_plan_prints_at_the_15": sum(r["slab_plan_print_at_member"] for r in rows),
        },
        "existence": {
            "lines": [{k: v for k, v in r.items()} for r in ex],
            "status_count": {k: sum(1 for r in ex if r["status"] == k) for k in ("EXISTS", "UNKNOWN", "NOT_PRESENT")},
            "route_g_m3_on_them": round(sum(r["route_g_m3"] for r in ex), 6),
            "type_table_2ND_band_types_without_a_2F_member": sorted(m for m, v in tt.items()
                                                                     if v["band_2ND_printed"] and v["drawn_2F"] == 0),
        },
    }


def main(argv):
    ev, rows, recs, ex = build()
    summ = summarise(ev, rows, ex)
    if "--write" in argv:
        with open(HERE / "LEDGER_T256.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        (HERE / "summary.json").write_text(json.dumps(summ, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: summ[k] for k in ("status_count", "basis_count", "conflict_m3", "equals_t248", "by_storey",
                                             "differs_in", "drawn_equals_gr_band_1F")}, indent=1))
    print(json.dumps(summ["existence"]["status_count"]), summ["existence"]["route_g_m3_on_them"],
          summ["existence"]["type_table_2ND_band_types_without_a_2F_member"])


if __name__ == "__main__":
    main(sys.argv)
